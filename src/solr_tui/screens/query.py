from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label

from solr_tui.client import SolrClient


class QueryScreen(Screen):
    def __init__(self, client: SolrClient, cores: list[str], version: str):
        super().__init__()
        self.client = client
        self.cores = cores
        self.version = version

    def compose(self) -> ComposeResult:
        yield Label(", ".join(self.cores))
