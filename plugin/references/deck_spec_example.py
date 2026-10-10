"""Example of a script that writes a deck specification for `sg pptx build` (schema deck_spec).

A lecture's slides are easier to write as code than as raw JSON: small helpers place boxes, arrows,
text and tables, and loops draw repeated shapes. This example shows each kind of slide once:
a reused slide of the template, a section divider, a bullet slide, a diagram and a table.

Run:
  python3 deck_spec_example.py --base TEMPLATE.pptx --out lecture/deck.json
  python3 <plugin>/scripts/sg.py pptx build --spec lecture/deck.json

The layout names used here ("Title Only", "Title and Content", "Section Header") must exist in the
template. Coordinates are in inches; keep shapes inside the template's slide size and below its title.
Bold and italic use **text** and *text*; write \\* for a literal asterisk (as in a path like orders/\\*.parquet).
"""
import argparse
import json
import os
from pathlib import Path

L, W = 0.7, 8.6            # left edge and width of the content area
TOP = 1.5                  # first line below the title


def text(x, y, w, h, lines, size=16, **kw):
    """A text box; lines are strings or {"text": ..., "level": n}; kw: bullets, bold, italic, color, align."""
    return {"type": "text", "x": x, "y": y, "w": w, "h": h, "text": lines, "size": size, **kw}


def box(x, y, w, h, label, fill="paleblue", size=12, **kw):
    """A filled shape with centred text; kw: shape (rect, rounded, ellipse, can, ...), dashed, line, bold."""
    return {"type": "box", "x": x, "y": y, "w": w, "h": h, "text": label, "fill": fill, "size": size, **kw}


def arrow(a, b, **kw):
    """An arrow from point a to point b; kw: label, color, dashed, width, head ("end", "both", "none")."""
    return {"type": "arrow", "from": list(a), "to": list(b), **kw}


def bullets(lines, w=4.2, size=16, y=TOP, h=3.0):
    return text(L, y, w, h, [{"text": s} for s in lines], size=size, bullets=True)


def takeaway(line, y=4.6):
    """The one-line message of a slide, under its content."""
    return text(L, y, W, 0.4, [line], size=14, italic=True, color="dark")


def build_slides():
    slides = []

    # 1. reuse the template's first slide; "edits" replace text in it, keeping its formatting
    slides.append({"copy": 1, "notes": "Reused from the template. Add edits: [{\"find\": ..., \"replace\": ...}]."})

    # 2. a section divider
    slides.append({"layout": "Section Header", "title": "Caching", "bullets": ["Keeping hot data close"],
                   "notes": None})

    # 3. bullets, with a second level and bold text
    slides.append({"layout": "Title and Content", "title": "Why cache?",
                   "bullets": ["Reading from memory is much faster than from disk or over the network",
                               {"text": "a **cache hit** avoids the slow read", "level": 1},
                               {"text": "a **cache miss** pays for it, and fills the cache", "level": 1},
                               "Every cache trades **freshness** for speed"],
                   "notes": "Speaker notes name the sources of every claim on the slide."})

    # 4. a diagram: bullets on the left, shapes on the right, a takeaway line at the bottom
    flow = [box(5.2, 1.6, 1.3, 0.55, "client", fill="palegrey"),
            box(7.4, 1.6, 1.6, 0.55, "cache", fill="palegold", shape="rounded"),
            box(7.4, 3.1, 1.6, 0.7, "database", fill="paleblue", shape="can"),
            arrow((6.5, 1.87), (7.4, 1.87), label="1. read"),
            arrow((8.2, 2.15), (8.2, 3.1), dashed=True),
            text(8.3, 2.45, 1.2, 0.3, ["2. on a miss"], size=10, color="dark")]
    slides.append({"layout": "Title Only", "title": "Read-through cache",
                   "shapes": [bullets(["The client asks the cache first",
                                       "On a miss, the cache reads the database and keeps the result",
                                       "Entries expire after a time to live (TTL)"])] + flow +
                             [takeaway("A longer TTL means more hits and staler data: a trade-off")],
                   "notes": None})

    # 5. a table; the first row is the header
    rows = [["Policy", "Evicts", "Good for"],
            ["LRU", "the least recently used entry", "recency-heavy access"],
            ["LFU", "the least frequently used entry", "stable popular items"],
            ["TTL", "entries older than a set age", "data that changes on a schedule"]]
    slides.append({"layout": "Title Only", "title": "Eviction policies",
                   "shapes": [{"type": "table", "x": L, "y": TOP, "w": W, "h": 2.0, "rows": rows, "size": 13,
                               "col_widths": [1.6, 3.6, 3.4]}],
                   "notes": None})
    return slides


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", required=True, help="template deck whose master and layouts are used")
    parser.add_argument("--out", required=True, help="deck specification to write (deck.json)")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    spec = {"base": os.path.relpath(Path(args.base).resolve(), out.parent),   # paths are relative to the spec
            "output": out.with_suffix(".pptx").name,
            "title": "Example lecture", "slides": build_slides()}
    out.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(spec['slides'])} slides -> {out}")


if __name__ == "__main__":
    main()
