"""Scrollable read-only text that renders only the visible lines."""

import re
from functools import lru_cache

from rich.segment import Segment
from rich.style import Style
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip

JSON_TOKENS = re.compile(
    r'(?P<key>"(?:[^"\\]|\\.)*"(?=\s*:))'
    r'|(?P<string>"(?:[^"\\]|\\.)*")'
    r'|(?P<number>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
    r'|(?P<literal>\btrue\b|\bfalse\b|\bnull\b)'
)
STYLES = {
    "key": Style(color="#66d9ef", bold=True),
    "string": Style(color="#a6e22e"),
    "number": Style(color="#ae81ff"),
    "literal": Style(color="#f92672"),
}
PLAIN = Style()


@lru_cache(maxsize=4096)
def _json_segments(line: str) -> tuple[Segment, ...]:
    segments: list[Segment] = []
    pos = 0
    for match in JSON_TOKENS.finditer(line):
        if match.start() > pos:
            segments.append(Segment(line[pos:match.start()], PLAIN))
        segments.append(Segment(match.group(), STYLES[match.lastgroup]))
        pos = match.end()
    if pos < len(line):
        segments.append(Segment(line[pos:], PLAIN))
    return tuple(segments)


class ResponseBody(ScrollView, can_focus=True):
    def __init__(self, text: str = "", **kwargs):
        super().__init__(**kwargs)
        self.highlight_json = False
        self.lines: list[str] = []
        self.set_text(text)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def set_text(self, text: str, highlight_json: bool = False) -> None:
        self.lines = text.expandtabs(4).split("\n")
        self.highlight_json = highlight_json
        width = max((len(line) for line in self.lines), default=0)
        self.virtual_size = Size(width, len(self.lines))
        self.scroll_to(0, 0, animate=False)
        self.refresh()

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        index = scroll_y + y
        width = self.scrollable_content_region.width
        if index >= len(self.lines):
            return Strip.blank(width, self.rich_style)
        line = self.lines[index]
        segments = _json_segments(line) if self.highlight_json else (Segment(line, PLAIN),)
        return Strip(segments, len(line)).crop_extend(scroll_x, scroll_x + width, self.rich_style)
