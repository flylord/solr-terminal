import pathlib
import re

from solr_terminal.form_spec import SECTIONS, all_fields, defaults


def test_defaults_match_web_ui():
    d = defaults()
    assert d["q"] == "*:*" and d["q.op"] == "OR" and d["indent"] is True and d["defType"] == ""


def test_section_order():
    assert [s.key for s in SECTIONS] == ["common", "debugQuery", "dismax", "hl", "facet", "spatial", "spellcheck"]


def test_field_set_matches_reference_html():
    html = pathlib.Path("tests/fixtures/solr-query.html").read_text()
    models = set(re.findall(r"ng-model=\"val\['([^']+)'\]\"", html)) - {"json"}
    models = {"hl.usePhraseHighlighter" if m == "hl.usePhraseHighLighter" else m for m in models}
    assert {f.name for f in all_fields()} == models


def test_edismax_group_visibility():
    dismax = next(s for s in SECTIONS if s.key == "dismax")
    shared, edismax_only = dismax.groups
    assert shared.visible({"defType": "dismax"}) and not edismax_only.visible({"defType": "dismax"})
    assert edismax_only.visible({"defType": "edismax"})
    assert not shared.visible({"defType": "lucene"})


def test_hl_method_groups():
    hl = next(s for s in SECTIONS if s.key == "hl")
    names = lambda vals: {f.name for g in hl.groups if g.visible(vals) for f in g.fields}
    assert "hl.simple.pre" in names({"hl": True, "hl.method": "original"})
    assert "hl.simple.pre" not in names({"hl": True, "hl.method": "unified"})
    assert "hl.offsetSource" in names({"hl": True, "hl.method": "unified"})
    assert names({"hl": False}) == set()


def test_select_options():
    by = {f.name: f for f in all_fields()}
    assert by["wt"].options == ("", "json", "xml", "python", "ruby", "php", "csv")
    assert by["hl.bs.type"].options == ("", "SENTENCE", "SEPARATOR", "WORD", "CHARACTER", "LINE", "WHOLE")
