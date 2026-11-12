# solr_terminal

Terminal version of the Solr Admin Query screen, for standalone Solr 9 and 10.

## Run

```
uv sync
uv run solr_terminal --url http://localhost:8983/solr --user alteo
```

Login values come from flags or `SOLR_URL`, `SOLR_USER`, `SOLR_PASSWORD`. Anything missing is asked on the login screen.

## Keys

- `F5` or `Ctrl+Enter`: execute query
- `Tab` / `Shift+Tab`: move between fields
- `Ctrl+Q`: quit

## Tests

```
uv run pytest
```
