"""Main screen: core picker and query form on the left, response on the right."""

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Label, Select

from solr_terminal.client import SolrClient, SolrError
from solr_terminal.params import build_request
from solr_terminal.widgets.query_form import QueryForm
from solr_terminal.widgets.response_view import ResponseView


class QueryScreen(Screen):
    BINDINGS = [
        Binding("f5", "execute", "Execute Query"),
        Binding("ctrl+enter", "execute", "Execute Query", show=False),
        Binding("f6", "toggle_pane", "Form/Response"),
        Binding("ctrl+q", "app.quit", "Quit"),
    ]

    def __init__(self, client: SolrClient, cores: list[str], version: str):
        super().__init__()
        self.client = client
        self.cores = cores
        self.version = version
        self._form_focus: Widget | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left"):
                yield Label(f"Solr {self.version}  {self.client.base_url}", id="server")
                yield Select(
                    [(c, c) for c in self.cores],
                    value=self.cores[0] if self.cores else Select.BLANK,
                    allow_blank=not self.cores,
                    prompt="No cores",
                    id="core",
                )
                yield QueryForm(id="form")
                yield Button("Execute Query", id="execute", variant="primary")
            yield ResponseView(id="response")
        yield Footer()

    @property
    def core(self) -> str | None:
        value = self.query_one("#core", Select).value
        return value if isinstance(value, str) else None

    def on_mount(self) -> None:
        self.load_paramsets()

    async def on_unmount(self) -> None:
        await self.client.aclose()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "core":
            self.load_paramsets()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "execute":
            self.action_execute()

    @work(exclusive=True, group="paramsets")
    async def load_paramsets(self) -> None:
        if self.core:
            self.query_one(QueryForm).set_paramsets(await self.client.paramsets(self.core))

    def action_toggle_pane(self) -> None:
        body = self.query_one(ResponseView).body
        if self.focused is body:
            target = self._form_focus if self._form_focus and self._form_focus.is_attached else self.query_one("#core")
            target.focus()
        else:
            self._form_focus = self.focused
            body.focus()

    def action_execute(self) -> None:
        view = self.query_one(ResponseView)
        if not self.core:
            view.show_error("No core selected.")
            return
        form = self.query_one(QueryForm)
        query = form.read()
        path, params = build_request(self.core, query)
        view.show_running()
        self.run_query(path, params, str(query.values.get("wt", "")))

    @work(exclusive=True, group="query")
    async def run_query(self, path: str, params: list[tuple[str, str]], wt: str) -> None:
        view = self.query_one(ResponseView)
        try:
            result = await self.client.query(path, params)
        except SolrError as exc:
            view.show_error(exc.message)
            return
        view.show(result, wt)
