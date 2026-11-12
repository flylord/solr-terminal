import httpx
import respx

from solr_terminal.app import Credentials, SolrTuiApp, resolve_credentials
from solr_terminal.screens.login import LoginScreen
from solr_terminal.screens.query import QueryScreen

BASE = "http://s/solr"


def test_flags_override_env():
    c = resolve_credentials(["--user", "f"], {"SOLR_USER": "e", "SOLR_PASSWORD": "p"})
    assert (c.url, c.user, c.password) == ("http://localhost:8983/solr", "f", "p")


def test_url_from_env():
    assert resolve_credentials([], {"SOLR_URL": "http://x/solr"}).url == "http://x/solr"


async def _login(app, pilot):
    await pilot.pause()
    app.screen.query_one("#user").value = "u"
    app.screen.query_one("#password").value = "bad"
    await pilot.click("#login")
    await app.workers.wait_for_complete()
    await pilot.pause()


def _error(app) -> str:
    return str(app.screen.query_one("#error").render())


@respx.mock
async def test_bad_password_stays_on_login():
    respx.get(f"{BASE}/admin/cores").respond(401)
    app = SolrTuiApp(Credentials(BASE, "", ""))
    async with app.run_test() as pilot:
        await _login(app, pilot)
        assert isinstance(app.screen, LoginScreen)
        assert "Authentication failed (401)" in _error(app)


@respx.mock
async def test_unreachable_server_message():
    respx.get(f"{BASE}/admin/cores").mock(side_effect=httpx.ConnectError("refused"))
    app = SolrTuiApp(Credentials(BASE, "", ""))
    async with app.run_test() as pilot:
        await _login(app, pilot)
        assert isinstance(app.screen, LoginScreen)
        assert "Cannot reach Solr at http://s/solr" in _error(app)


@respx.mock
async def test_env_credentials_skip_login():
    respx.get(f"{BASE}/admin/cores").respond(json={"status": {"alteo": {}}})
    respx.get(f"{BASE}/admin/info/system").respond(json={"lucene": {"solr-spec-version": "10.0.0"}})
    respx.get(f"{BASE}/alteo/config/params").respond(404)
    app = SolrTuiApp(Credentials(BASE, "u", "p"))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, QueryScreen)
