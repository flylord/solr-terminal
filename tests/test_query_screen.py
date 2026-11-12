import respx

from solr_tui.client import SolrClient
from solr_tui.screens.query import QueryScreen
from solr_tui.widgets.response_view import ResponseView
from textual.app import App
from textual.widgets import Button, Input, Select, TextArea

BASE = "http://s/solr"
BODY = '{\n  "response":{"numFound":3}\n}'


class Host(App):
    def __init__(self):
        super().__init__()
        self.client = SolrClient(BASE, "u", "p")

    def on_mount(self) -> None:
        self.push_screen(QueryScreen(self.client, ["alteo", "other"], "10.0.0"))


def mock_solr(status=200, body=BODY):
    respx.get(url__regex=rf"{BASE}/\w+/config/params.*").respond(404)
    return respx.get(url__regex=rf"{BASE}/\w+/select.*").respond(status, text=body)


async def execute(app, pilot):
    await pilot.press("f5")
    await app.workers.wait_for_complete()
    await pilot.pause()


def url_text(app) -> str:
    return str(app.screen.query_one("#response-url").render())


@respx.mock
async def test_execute_default_query_shows_url_and_body():
    mock_solr()
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
        await execute(app, pilot)
        assert url_text(app) == "http://s/solr/alteo/select?q=%2A%3A%2A&q.op=OR&indent=true"
        assert '"numFound":3' in app.screen.query_one(ResponseView).result.body


@respx.mock
async def test_edismax_fields_appear_only_for_edismax():
    mock_solr()
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
        s = app.screen
        assert not _shown(s, "#qf")
        s.query_one("#defType", Select).value = "dismax"
        await pilot.pause()
        assert _shown(s, "#qf") and not _shown(s, "#pf2")
        s.query_one("#defType", Select).value = "edismax"
        await pilot.pause()
        assert _shown(s, "#pf2")


def _shown(screen, selector) -> bool:
    node = screen.query_one(selector)
    while node is not None and node is not screen:
        if not node.display:
            return False
        node = node.parent
    return True


@respx.mock
async def test_add_fq_rows_sent_in_order():
    route = mock_solr()
    app = Host()
    async with app.run_test(size=(160, 80)) as pilot:
        await pilot.pause()
        app.screen.query_one("#fq-add", Button).press()
        await pilot.pause()
        rows = app.screen.query("Input.fq")
        assert len(rows) == 2
        rows[0].value = "a:1"
        rows[1].value = "b:2"
        await execute(app, pilot)
        assert route.calls.last.request.url.params.get_list("fq") == ["a:1", "b:2"]


@respx.mock
async def test_core_switch_keeps_form_values():
    route = mock_solr()
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.screen.query_one("#q", TextArea).text = "title_t:usb"
        app.screen.query_one("#core", Select).value = "other"
        await pilot.pause()
        await execute(app, pilot)
        req = route.calls.last.request
        assert req.url.path == "/solr/other/select" and req.url.params["q"] == "title_t:usb"


@respx.mock
async def test_http_400_shows_status_and_body():
    mock_solr(400, '{"error":{"msg":"Cannot parse"}}')
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
        await execute(app, pilot)
        assert "HTTP 400" in str(app.screen.query_one("#response-status").render())
        assert "Cannot parse" in app.screen.query_one(ResponseView).result.body


@respx.mock
async def test_large_response_scrolls():
    mock_solr(body="\n".join(f'"line{i}":{i},' for i in range(5000)))
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
        await execute(app, pilot)
        body = app.screen.query_one(ResponseView).body
        assert body.max_scroll_y > 0
        body.focus()
        await pilot.press("end")
        await pilot.pause()
        assert body.scroll_y > 0


@respx.mock
async def test_huge_response_renders_fast():
    import time
    body = "{\n" + "\n".join(f'  "field{i}":"value number {i} with some text",' for i in range(100_000)) + "\n}"
    mock_solr(body=body)
    app = Host()
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        start = time.monotonic()
        await execute(app, pilot)
        assert time.monotonic() - start < 3
        assert app.screen.query_one(ResponseView).result.body == body


@respx.mock
async def test_quit_closes_client():
    mock_solr()
    app = Host()
    async with app.run_test() as pilot:
        await pilot.pause()
    assert app.client._http.is_closed
