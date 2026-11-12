from solr_terminal.form_spec import defaults
from solr_terminal.params import QueryInput, build_request, display_url


def qi(**kw):
    return QueryInput(values={**defaults(), **kw.pop("values", {})}, **kw)


def test_default_query():
    assert build_request("alteo", qi()) == ("alteo/select", [("q", "*:*"), ("q.op", "OR"), ("indent", "true")])


def test_dismax_fields_purged_unless_dismax():
    _, p = build_request("c", qi(values={"qf": "title_t"}))
    assert ("qf", "title_t") not in p
    _, p = build_request("c", qi(values={"defType": "edismax", "qf": "title_t", "pf2": "x"}))
    assert ("qf", "title_t") in p and ("pf2", "x") in p


def test_hl_method_purge():
    _, p = build_request("c", qi(values={"hl": True, "hl.method": "unified", "hl.simple.pre": "<b>", "hl.tag.pre": "<em>"}))
    assert ("hl", "true") in p and ("hl.tag.pre", "<em>") in p and ("hl.simple.pre", "<b>") not in p


def test_multiple_fq_and_raw():
    _, p = build_request("c", qi(fq=["a:1", "", "b:2"], raw=["x=1&y=2\nflag", "z=a=b"]))
    assert [v for k, v in p if k == "fq"] == ["a:1", "b:2"]
    assert ("x", "1") in p and ("y", "2") in p and ("flag", "") in p and ("z", "a=b") in p


def test_qt_handling():
    assert build_request("c", qi(qt="/query"))[0] == "c/query"
    path, p = build_request("c", qi(qt="legacy"))
    assert path == "c/select" and ("qt", "legacy") in p


def test_use_params_and_json():
    _, p = build_request("c", qi(use_params=["a", "b"], json='{"query":"*:*"}'))
    assert ("useParams", "a,b") in p and ("json", '{"query":"*:*"}') in p


def test_display_url_encodes_special_chars():
    url = display_url("http://h:8983/solr/", "c/select", [("q", 'title_t:"USB-C" AND p:[1 TO *] & #Računari')])
    assert url.startswith("http://h:8983/solr/c/select?q=")
    assert "&" not in url.split("?q=")[1] and "#" not in url and "Ra%C4%8Dunari" in url


def test_core_name_is_escaped():
    assert build_request("a#b", qi())[0] == "a%23b/select"
