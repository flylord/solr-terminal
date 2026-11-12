"""Query form definition transcribed from the Solr Admin UI (partials/query.html)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

FieldKind = Literal["text", "textarea", "checkbox", "select"]
Values = Mapping[str, str | bool]


@dataclass(frozen=True)
class Field:
    name: str
    kind: FieldKind
    label: str
    options: tuple[str, ...] = ()
    default: str | bool = ""


@dataclass(frozen=True)
class Group:
    key: str
    fields: tuple[Field, ...]
    visible: Callable[[Values], bool]


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    toggle: Field | None
    groups: tuple[Group, ...]


def _t(name: str) -> Field:
    return Field(name, "text", name)


def _c(name: str, default: bool = False) -> Field:
    return Field(name, "checkbox", name, default=default)


def _s(name: str, *options: str) -> Field:
    return Field(name, "select", name, ("", *options))


def _texts(*names: str) -> tuple[Field, ...]:
    return tuple(_t(n) for n in names)


def _always(_: Values) -> bool:
    return True


def _on(key: str) -> Callable[[Values], bool]:
    return lambda v: v.get(key) is True


def _hl_method(*methods: str) -> Callable[[Values], bool]:
    return lambda v: v.get("hl") is True and v.get("hl.method") in methods


SECTIONS: tuple[Section, ...] = (
    Section("common", "common", None, (
        Group("common", (
            Field("q", "textarea", "q", default="*:*"),
            Field("q.op", "select", "q.op", ("AND", "OR"), default="OR"),
            _t("sort"),
            _t("start"),
            _t("rows"),
            _t("fl"),
            _t("df"),
            _s("wt", "json", "xml", "python", "ruby", "php", "csv"),
            _c("indent", default=True),
        ), _always),
    )),
    Section("debugQuery", "debugQuery", _c("debugQuery"), (
        Group("debug", (_c("debug.explain.structured"),), _on("debugQuery")),
    )),
    Section("dismax", "defType", _s("defType", "lucene", "dismax", "edismax"), (
        Group("dismax", _texts("q.alt", "qf", "mm", "pf", "ps", "qs", "tie", "bq", "bf"),
              lambda v: v.get("defType") in ("dismax", "edismax")),
        Group("edismax", (*_texts("uf", "pf2", "pf3", "ps2", "ps3", "boost"),
                          _c("stopwords"), _c("lowercaseOperators")),
              lambda v: v.get("defType") == "edismax"),
    )),
    Section("hl", "hl", _c("hl"), (
        Group("hl", (_t("hl.fl"),), _on("hl")),
        Group("hl-original-tags", _texts("hl.simple.pre", "hl.simple.post"), _hl_method("original")),
        Group("hl-tags", _texts("hl.tag.pre", "hl.tag.post"), _hl_method("unified", "fastVector")),
        Group("hl-common", (
            _c("hl.requireFieldMatch"),
            _c("hl.usePhraseHighlighter"),
            _c("hl.highlightMultiTerm"),
            *_texts("hl.q", "hl.qparser", "hl.snippets", "hl.fragsize", "hl.encoder", "hl.maxAnalyzedChars"),
            _s("hl.method", "unified", "original", "fastVector"),
        ), _on("hl")),
        Group("hl-unified", (
            _s("hl.offsetSource", "ANALYSIS", "POSTINGS", "POSTINGS_WITH_TERM_VECTORS", "TERM_VECTORS"),
            _t("hl.fragAlignRatio"),
            _c("hl.fragsizeIsMinimum"),
            _t("hl.tag.ellipsis"),
            _c("hl.defaultSummary"),
            *_texts("hl.score.k1", "hl.score.b", "hl.score.pivot", "hl.bs.language", "hl.bs.country", "hl.bs.variant"),
            _s("hl.bs.type", "SENTENCE", "SEPARATOR", "WORD", "CHARACTER", "LINE", "WHOLE"),
            _t("hl.bs.separator"),
            _c("hl.weightMatches"),
        ), _hl_method("unified")),
        Group("hl-original", (
            _c("hl.mergeContiguous"),
            *_texts("hl.maxMultiValuedToExamine", "hl.maxMultiValuedToMatch"),
            _s("hl.formatter", "simple"),
            _s("hl.fragmenter", "gap", "regex"),
            *_texts("hl.regex.slop", "hl.regex.pattern", "hl.regex.maxAnalyzedChars"),
            _c("hl.preserveMulti"),
            _c("hl.payloads"),
        ), _hl_method("original")),
        Group("hl-alternate", (
            *_texts("hl.alternateField", "hl.maxAlternateFieldLength"),
            _c("hl.highlightAlternate"),
        ), _hl_method("original", "fastVector")),
        Group("hl-fastvector", _texts(
            "hl.fragListBuilder", "hl.fragmentsBuilder", "hl.boundaryScanner",
            "hl.phraseLimit", "hl.multiValuedSeparatorChar",
        ), _hl_method("fastVector")),
    )),
    Section("facet", "facet", _c("facet"), (
        Group("facet", (
            Field("facet.query", "textarea", "facet.query"),
            *_texts("facet.field", "facet.prefix", "facet.contains"),
            _c("facet.contains.ignoreCase"),
            *_texts("facet.limit", "facet.matches"),
            _s("facet.sort", "count", "index"),
            _t("facet.mincount"),
            _c("facet.missing"),
            Field("json.facet", "textarea", "json.facet"),
        ), _on("facet")),
    )),
    Section("spatial", "spatial", _c("spatial"), (
        Group("spatial", _texts("pt", "sfield", "d"), _on("spatial")),
    )),
    Section("spellcheck", "spellcheck", _c("spellcheck"), (
        Group("spellcheck", (
            _c("spellcheck.build"),
            _c("spellcheck.reload"),
            *_texts("spellcheck.q", "spellcheck.dictionary", "spellcheck.count"),
            _c("spellcheck.onlyMorePopular"),
            _c("spellcheck.extendedResults"),
            _c("spellcheck.collate"),
            *_texts("spellcheck.maxCollations", "spellcheck.maxCollationTries", "spellcheck.accuracy"),
        ), _on("spellcheck")),
    )),
)


def all_fields() -> list[Field]:
    fields: list[Field] = []
    for section in SECTIONS:
        if section.toggle:
            fields.append(section.toggle)
        for group in section.groups:
            fields.extend(group.fields)
    return fields


def defaults() -> dict[str, str | bool]:
    return {f.name: f.default for f in all_fields()}
