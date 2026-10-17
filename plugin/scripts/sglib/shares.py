"""Whether a survey answer and its percentage are printed together on a stored page.

A survey table is trusted only if each answer's percentage is printed next to the answer's name. Finding the name
and the number anywhere on the page proves little: a page with fifty percentages contains most numbers a wrong table
could hold. So each stored page is split into rows by its layout:
- HTML: the text of every small element (table rows, list items, SVG chart groups, cards);
- PDF: the spans that share a baseline on one page, left to right;
- JSON: the scalar values of each object;
- text: each line, and each clause of the text joined across line breaks (prose such as "Prometheus reaches 77%
  production use").
A table row passes when some page row names the answer and prints its percentage as one of:
- any number in the row, if the row names no other answer of the table and holds at most three numbers (name,
  respondents and percent; a percent with its "evaluating" share);
- the number nearest to the name otherwise, the one after the name on a tie (tables and bar charts print the value
  after the label).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .sources import _normalize, _store_paths

MAX_ROW = 300          # characters; larger HTML elements hold several rows
BASELINE = 2.0         # points: spans this close vertically share a PDF row
OWN_ROW_NUMBERS = 3    # a row of one answer holds at most this many numbers
NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])")
CLAUSE = re.compile(r"[.;:!?]\s+|,\s+")


def _html_rows(raw: bytes) -> list[str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    rows = []
    for el in soup.find_all(True):
        text = el.get_text(" ", strip=True)
        if text and len(text) <= MAX_ROW:
            rows.append(text)
    return rows


def _pdf_rows(raw: bytes) -> list[str]:
    import fitz
    rows = []
    with fitz.open(stream=raw, filetype="pdf") as doc:
        for page in doc:
            spans = [(s["origin"][1], s["origin"][0], s["text"]) for b in page.get_text("dict")["blocks"]
                     for line in b.get("lines", []) for s in line["spans"] if s["text"].strip()]
            spans.sort()
            group, y0 = [], None
            for y, x, text in spans:
                if group and y - y0 > BASELINE:
                    rows.append(" ".join(t for _, t in sorted(group)))
                    group = []
                if not group:
                    y0 = y
                group.append((x, text))
            if group:
                rows.append(" ".join(t for _, t in sorted(group)))
    return rows


def _json_rows(raw: bytes) -> list[str]:
    rows = []

    def walk(x):
        if isinstance(x, dict):
            values = [str(v) for v in x.values() if isinstance(v, (str, int, float)) and not isinstance(v, bool)]
            if values:
                rows.append(" ".join(values))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(json.loads(raw.decode("utf-8", errors="replace")))
    return rows


def page_rows(store: Path, entry: dict) -> list[str]:
    """Rows of one stored page (its index entry), normalized for matching."""
    raw_path, text_path = _store_paths(store, entry["fetched"], entry["kind"])
    raw = raw_path.read_bytes() if raw_path.exists() else b""
    if entry["kind"] == "html" and raw:
        rows = _html_rows(raw)
    elif entry["kind"] == "pdf" and raw:
        rows = _pdf_rows(raw)
    elif entry["kind"] == "json" and raw:
        rows = _json_rows(raw)
    else:
        rows = []
    if text_path.exists():
        text = text_path.read_text(encoding="utf-8")
        rows += text.splitlines() + CLAUSE.split(re.sub(r"\s+", " ", text))
    return [r for r in (_normalize(x) for x in rows) if r]


def _value(token: str) -> float:
    return float(token.replace(",", "."))


def _name_pattern(name: str) -> re.Pattern | None:
    target = _normalize(name)
    return re.compile(r"(?<!\w)" + re.escape(target) + r"(?!\w)") if target else None


def paired(rows: list[str], name: str, percent: float, others: list[str] = ()) -> bool:
    """Whether some row prints `name` with `percent` (see the module docstring); `others` are the table's other
    answers."""
    pattern = _name_pattern(name)
    if pattern is None:
        return False
    rivals = [p for p in (_name_pattern(o) for o in others if _normalize(o) != _normalize(name)) if p]
    for row in rows:
        hits = list(pattern.finditer(row))
        if not hits:
            continue
        others_here = [r.span() for p in rivals for r in p.finditer(row)]
        # "Docker" inside "Docker / Docker Compose" names the longer answer, not this one
        hits = [h for h in hits if not any(a <= h.start() and h.end() <= b and b - a > h.end() - h.start()
                                           for a, b in others_here)]
        if not hits:
            continue
        numbers = [m for m in NUMBER.finditer(row)
                   if not any(m.start() < h.end() and m.end() > h.start() for h in hits)]   # not inside the name
        if not numbers:
            continue
        # another answer shares the row only where it is not part of this one's name
        shared = any(not any(a < h.end() and b > h.start() for h in hits) for a, b in others_here)
        if not shared and len(numbers) <= OWN_ROW_NUMBERS:
            if any(abs(_value(m.group()) - percent) < 1e-6 for m in numbers):
                return True
            continue
        for h in hits:
            def key(m):
                after = m.start() >= h.end()
                return (m.start() - h.end() if after else h.start() - m.end(), not after)
            if abs(_value(min(numbers, key=key).group()) - percent) < 1e-6:
                return True
    return False
