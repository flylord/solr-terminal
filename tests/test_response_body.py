from solr_terminal.widgets.response_body import STYLES, _json_segments


def test_json_tokens_coloured():
    segs = _json_segments('  "title_t":["USB \\"C\\""], "n":-1.5e3, "ok":true')
    by_text = {s.text: s.style for s in segs}
    assert by_text['"title_t"'] == STYLES["key"]
    assert by_text['"USB \\"C\\""'] == STYLES["string"]
    assert by_text["-1.5e3"] == STYLES["number"]
    assert by_text["true"] == STYLES["literal"]
    assert "".join(s.text for s in segs) == '  "title_t":["USB \\"C\\""], "n":-1.5e3, "ok":true'
