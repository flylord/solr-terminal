"""Turn form input into a Solr request, following doQuery in the Solr Admin UI."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import quote, urlencode

from solr_terminal.form_spec import SECTIONS


@dataclass(frozen=True)
class QueryInput:
    values: Mapping[str, str | bool]
    fq: Sequence[str] = ()
    raw: Sequence[str] = ()
    qt: str = ""
    use_params: Sequence[str] = ()
    json: str = ""


def _visible_fields(values: Mapping[str, str | bool]) -> list[str]:
    names: list[str] = []
    for section in SECTIONS:
        if section.toggle:
            names.append(section.toggle.name)
        for group in section.groups:
            if group.visible(values):
                names.extend(f.name for f in group.fields)
    return names


def _encode(value: str | bool) -> str | None:
    if value is True:
        return "true"
    if isinstance(value, str) and value:
        return value
    return None


def build_request(core: str, q: QueryInput) -> tuple[str, list[tuple[str, str]]]:
    params: list[tuple[str, str]] = []
    for name in _visible_fields(q.values):
        encoded = _encode(q.values.get(name, ""))
        if encoded is not None:
            params.append((name, encoded))

    params.extend(("fq", f) for f in q.fq if f)

    for entry in q.raw:
        for part in re.split(r"[&\n]", entry):
            if not part:
                continue
            key, sep, value = part.partition("=")
            params.append((key, value if sep else ""))

    handler = "select"
    qt = q.qt.strip()
    if qt.startswith("/"):
        handler = qt[1:]
    elif qt:
        params.append(("qt", qt))

    if q.use_params:
        params.append(("useParams", ",".join(q.use_params)))
    if q.json:
        params.append(("json", q.json))

    return f"{quote(core, safe='')}/{handler}", params


def display_url(base_url: str, path: str, params: list[tuple[str, str]]) -> str:
    url = f"{base_url.rstrip('/')}/{path}"
    if params:
        url += "?" + urlencode(params, quote_via=quote)
    return url
