"""Right pane: request URL, HTTP status and the raw response body."""

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from solr_tui.client import QueryResult

LEXERS = {"": "json", "json": "json", "xml": "xml", "python": "python", "ruby": "ruby", "php": "php", "csv": "text"}


class ResponseView(VerticalScroll):
    can_focus = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result: QueryResult | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="response-url")
        yield Static("", id="response-status")
        yield Static("Press F5 or Ctrl+Enter to execute the query.", id="response-body")

    def show_running(self) -> None:
        self.query_one("#response-status", Static).update("Running...")

    def show_error(self, message: str) -> None:
        self.query_one("#response-status", Static).update(message)

    def show(self, result: QueryResult, wt: str) -> None:
        self.result = result
        self.query_one("#response-url", Static).update(result.url)
        status = "" if result.status == 200 else f"HTTP {result.status}"
        self.query_one("#response-status", Static).update(status)
        lexer = LEXERS.get(wt, "text")
        self.query_one("#response-body", Static).update(
            Syntax(result.body, lexer, theme="monokai", word_wrap=True, background_color="default")
        )
        self.scroll_home(animate=False)
