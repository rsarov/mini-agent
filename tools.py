from __future__ import annotations

from dataclasses import dataclass, asdict
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class _DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._current: dict[str, str] | None = None
        self._capture: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        class_names = attr.get("class", "").split()

        if tag == "a" and "result__a" in class_names:
            self._current = {"title": "", "url": _normalize_duckduckgo_url(attr.get("href", "")), "snippet": ""}
            self._capture = "title"
            self._parts = []
        elif self._current is not None and "result__snippet" in class_names:
            self._capture = "snippet"
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current is None or self._capture is None:
            return

        if tag == "a" and self._capture == "title":
            self._current["title"] = _clean_text(" ".join(self._parts))
            self._capture = None
            self._parts = []
        elif tag in {"a", "div"} and self._capture == "snippet":
            self._current["snippet"] = _clean_text(" ".join(self._parts))
            self.results.append(SearchResult(**self._current))
            self._current = None
            self._capture = None
            self._parts = []


def _clean_text(value: str) -> str:
    return " ".join(unescape(value).split())


def _normalize_duckduckgo_url(value: str) -> str:
    parsed = urlparse(unescape(value))
    query = parse_qs(parsed.query)
    return query.get("uddg", [value])[0]


def web_search(query: str, limit: int = 5, timeout: int = 10) -> dict[str, Any]:
    """Search the web and return a compact JSON-serializable result list."""
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")

    params = urlencode({"q": query.strip()})
    request = Request(
        f"https://duckduckgo.com/html/?{params}",
        headers={"User-Agent": "mini-agent/1.0 (+https://example.invalid)"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        return {
            "tool": "web_search",
            "arguments": {"query": query},
            "results": [],
            "error": str(exc),
        }

    parser = _DuckDuckGoHTMLParser()
    parser.feed(html)

    results = parser.results[:limit]
    return {
        "tool": "web_search",
        "arguments": {"query": query},
        "results": [asdict(result) for result in results],
    }


TOOLS = {
    "web_search": web_search,
}


def execute_tool(tool_call: dict[str, Any]) -> dict[str, Any]:
    tool_name = tool_call.get("tool")
    if tool_name == "none":
        return tool_call

    tool = TOOLS.get(tool_name)
    if tool is None:
        raise ValueError(f"unknown tool: {tool_name}")

    arguments = tool_call.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise ValueError("tool arguments must be an object")

    return tool(**arguments)
