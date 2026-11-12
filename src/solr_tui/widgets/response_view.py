"""Right pane: request URL, HTTP status and the raw response body."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from solr_tui.client import QueryResult
from solr_tui.widgets.response_body import ResponseBody


class ResponseView(Vertical):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result: QueryResult | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="response-url")
        yield Static("", id="response-status")
        yield ResponseBody("Press F5 or Ctrl+Enter to execute the query.", id="response-body")

    @property
    def body(self) -> ResponseBody:
        return self.query_one("#response-body", ResponseBody)

    def show_running(self) -> None:
        self.query_one("#response-status", Static).update("Running...")

    def show_error(self, message: str) -> None:
        self.query_one("#response-status", Static).update(message)

    def show(self, result: QueryResult, wt: str) -> None:
        self.result = result
        self.query_one("#response-url", Static).update(result.url)
        self.query_one("#response-status", Static).update("" if result.status == 200 else f"HTTP {result.status}")
        self.body.set_text(result.body, highlight_json=wt in ("", "json"))
