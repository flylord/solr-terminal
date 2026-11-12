# solr_terminal

Terminal version of the Solr Admin Query screen, for standalone Solr 9 and 10.

![solr_terminal](docs/images/screenshot.png)

## Run

```
uv sync
uv run solr_terminal --url http://localhost:8983/solr --user alteo
```

Login values come from flags or `SOLR_URL`, `SOLR_USER`, `SOLR_PASSWORD`. Anything missing is asked on the login screen.

## Keys

- `F5` or `Ctrl+Enter`: execute query
- `F6`: switch between the form and the response
- `Tab` / `Shift+Tab`: move between fields
- `Ctrl+Q`: quit

## Tests

```
uv run pytest
```

## License

Copyright (C) 2026 Aleksandar Ilic

Released under the GNU General Public License v3.0 or later. See [LICENSE](LICENSE).
