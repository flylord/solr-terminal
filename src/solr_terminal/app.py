"""Application entry: credentials resolution and the Textual app."""

import argparse
from collections.abc import Mapping
from dataclasses import dataclass

from textual.app import App

DEFAULT_URL = "http://localhost:8983/solr"


@dataclass
class Credentials:
    url: str
    user: str
    password: str


def resolve_credentials(argv: list[str], env: Mapping[str, str]) -> Credentials:
    parser = argparse.ArgumentParser(prog="solr_terminal", description="Terminal Solr query screen")
    parser.add_argument("--url", help=f"Solr base URL (env SOLR_URL, default {DEFAULT_URL})")
    parser.add_argument("--user", help="username (env SOLR_USER)")
    parser.add_argument("--password", help="password (env SOLR_PASSWORD)")
    args = parser.parse_args(argv)
    return Credentials(
        url=args.url or env.get("SOLR_URL") or DEFAULT_URL,
        user=args.user or env.get("SOLR_USER", ""),
        password=args.password or env.get("SOLR_PASSWORD", ""),
    )


class SolrTuiApp(App):
    TITLE = "solr_terminal"
    CSS_PATH = "app.tcss"
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, creds: Credentials):
        super().__init__()
        self.creds = creds

    def on_mount(self) -> None:
        from solr_terminal.screens.login import LoginScreen

        self.push_screen(LoginScreen(self.creds, autoconnect=bool(self.creds.user and self.creds.password)))
