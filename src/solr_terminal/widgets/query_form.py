"""Left pane form generated from form_spec.SECTIONS."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Label, Select, SelectionList, TextArea

from solr_terminal.form_spec import SECTIONS, Field, all_fields, defaults
from solr_terminal.params import QueryInput


def widget_id(name: str) -> str:
    return name.replace(".", "-")


def _field_widget(field: Field) -> Widget:
    wid = widget_id(field.name)
    if field.kind == "checkbox":
        return Checkbox(field.label, bool(field.default), id=wid)
    if field.kind == "select":
        options = [("------" if o == "" else o, o) for o in field.options]
        return Select(options, value=field.default or field.options[0], allow_blank=False, id=wid)
    if field.kind == "textarea":
        return TextArea(str(field.default), id=wid, classes="textarea")
    placeholder = {"start": "0", "rows": "10"}.get(field.name, "")
    return Input(str(field.default), placeholder=placeholder, id=wid)


def _labelled(field: Field) -> list[Widget]:
    if field.kind == "checkbox":
        return [_field_widget(field)]
    return [Label(field.label, classes="field-label"), _field_widget(field)]


class _Row(Horizontal):
    def __init__(self, input_class: str, value: str = ""):
        super().__init__(classes="multi-row")
        self.input_class = input_class
        self.value = value

    def compose(self) -> ComposeResult:
        yield Input(self.value, classes=self.input_class)
        yield Button("-", classes="remove-row")


class QueryForm(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("Request-Handler (qt)", classes="field-label")
        yield Input(placeholder="/select", id="qt")
        for section in SECTIONS:
            with Vertical(classes="section", id=f"section-{section.key}"):
                if section.toggle:
                    yield from _labelled(section.toggle)
                for group in section.groups:
                    with Vertical(classes="group", id=f"group-{group.key}"):
                        for field in group.fields:
                            yield from _labelled(field)
                        if group.key == "common":
                            yield from self._common_extras()
        yield Label("Raw Query Parameters", classes="field-label")
        with Vertical(id="raw-list"):
            yield _Row("raw")
        yield Button("+", id="raw-add", classes="add-row")
        yield Label("JSON Query", classes="field-label")
        yield TextArea("", id="json", classes="textarea")

    def _common_extras(self) -> list[Widget]:
        return [
            Label("fq", classes="field-label"),
            Vertical(_Row("fq"), id="fq-list"),
            Button("+", id="fq-add", classes="add-row"),
            Label("paramset(s)", classes="field-label"),
            SelectionList[str](id="use-params"),
        ]

    def on_mount(self) -> None:
        self.refresh_visibility()

    def values(self) -> dict[str, str | bool]:
        result = defaults()
        for field in all_fields():
            widget = self.query_one(f"#{widget_id(field.name)}")
            if isinstance(widget, TextArea):
                result[field.name] = widget.text
            elif isinstance(widget, Checkbox):
                result[field.name] = widget.value
            else:
                value = widget.value
                result[field.name] = value if isinstance(value, str) else ""
        return result

    def refresh_visibility(self) -> None:
        values = self.values()
        for section in SECTIONS:
            for group in section.groups:
                self.query_one(f"#group-{group.key}").display = group.visible(values)

    def on_checkbox_changed(self) -> None:
        self.refresh_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "core":
            self.refresh_visibility()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fq-add":
            self.query_one("#fq-list").mount(_Row("fq"))
        elif event.button.id == "raw-add":
            self.query_one("#raw-list").mount(_Row("raw"))
        elif event.button.has_class("remove-row"):
            row = event.button.parent
            if len(row.parent.children) > 1:
                row.remove()
            else:
                row.query_one(Input).value = ""
        else:
            return
        event.stop()

    def set_paramsets(self, names: list[str]) -> None:
        selection = self.query_one("#use-params", SelectionList)
        selection.clear_options()
        selection.add_options([(n, n) for n in names])

    def read(self) -> QueryInput:
        return QueryInput(
            values=self.values(),
            fq=[i.value for i in self.query("Input.fq")],
            raw=[i.value for i in self.query("Input.raw")],
            qt=self.query_one("#qt", Input).value,
            use_params=list(self.query_one("#use-params", SelectionList).selected),
            json=self.query_one("#json", TextArea).text,
        )
