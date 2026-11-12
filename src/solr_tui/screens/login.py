"""Login screen: base URL, user and password."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label

from solr_tui.app import Credentials
from solr_tui.client import SolrClient, SolrError


class LoginScreen(Screen):
    def __init__(self, creds: Credentials, autoconnect: bool = False):
        super().__init__()
        self.creds = creds
        self.autoconnect = autoconnect

    def compose(self) -> ComposeResult:
        with Vertical(id="login-box"):
            yield Label("Solr URL")
            yield Input(self.creds.url, id="url")
            yield Label("Username")
            yield Input(self.creds.user, id="user")
            yield Label("Password")
            yield Input(self.creds.password, id="password", password=True)
            yield Button("Log in", id="login", variant="primary")
            yield Label("", id="error")
        yield Footer()

    def on_mount(self) -> None:
        if self.autoconnect:
            self.submit()

    def on_input_submitted(self) -> None:
        self.submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login":
            self.submit()

    def submit(self) -> None:
        self.query_one("#error", Label).update("Connecting...")
        self.connect(
            self.query_one("#url", Input).value.strip(),
            self.query_one("#user", Input).value,
            self.query_one("#password", Input).value,
        )

    @work(exclusive=True)
    async def connect(self, url: str, user: str, password: str) -> None:
        from solr_tui.screens.query import QueryScreen

        client = SolrClient(url, user, password)
        handed_over = False
        try:
            cores = await client.list_cores()
            version = await client.solr_version()
            self.app.switch_screen(QueryScreen(client, cores, version))
            handed_over = True
        except SolrError as exc:
            self.query_one("#error", Label).update(exc.message)
        finally:
            if not handed_over:
                await client.aclose()
