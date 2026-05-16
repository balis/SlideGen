#!/usr/bin/env python3
"""Split outline.md into chunks at section boundaries.

Usage:
  python3 split_outline.py <outline.md>

Emits a JSON array to stdout. Each element describes one chunk:
  {"part": 0, "title": "Intro", "slide_range": [1, 4]}

slide_range is inclusive. Slides are identified by `## Slide N:` headers.

Section boundaries are detected in three tiers, in order of preference:

  1. Machine-readable HTML comment markers (preferred, deterministic):
       <!-- chunk-boundary: A | Imperative ETL Failures (LO1) -->
     The id (before `|`) is a stable chunk identifier; the title (after `|`)
     is human-readable and optional. The outline agent is required to emit
     these for new decks regardless of how run.md is phrased.

  2. Heading-pattern fallback for legacy outlines:
       ## SECTION A: ...    or    ## Block 1: ...   (case-insensitive)

  3. Fixed-size fallback for legacy unmarked outlines:
     - <= FALLBACK_THRESHOLD slides: single "Full deck" chunk (single-shot)
     - >  FALLBACK_THRESHOLD slides: fixed-size DEFAULT_CHUNK_SIZE chunks

Slides preceding the first marker become an "Intro" chunk.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SLIDE_RE = re.compile(r"^##\s+Slide\s+(\d+)\s*:", re.IGNORECASE)

# Primary: deterministic machine marker. Required for new outlines.
#   <!-- chunk-boundary: A | Imperative ETL (LO1) -->
# Title (after `|`) is optional; id (before `|`) is required.
CHUNK_RE = re.compile(
    r"^\s*<!--\s*chunk-boundary\s*:\s*(?P<id>[^|\s][^|]*?)\s*(?:\|\s*(?P<title>.*?))?\s*-->\s*$",
    re.IGNORECASE,
)

# Secondary: legacy heading-pattern fallback.
SECTION_RE = re.compile(
    r"^##\s+(?:SECTION|BLOCK)\s+[A-Z0-9]+\s*:?\s*(.*)$",
    re.IGNORECASE,
)

DEFAULT_CHUNK_SIZE = 10   # slides per chunk in fixed-size fallback
FALLBACK_THRESHOLD = 20   # below this, no chunking — single-shot is fine


def split(outline_text: str) -> list[dict]:
    lines = outline_text.splitlines()
    slides: list[tuple[int, int]] = []           # (line_idx, slide_num)
    markers: list[tuple[int, str]] = []          # (line_idx, title) from chunk-boundary comments
    legacy_sections: list[tuple[int, str]] = []  # (line_idx, title) from SECTION/BLOCK headings

    for i, line in enumerate(lines):
        if m := SLIDE_RE.match(line):
            slides.append((i, int(m.group(1))))
            continue
        if m := CHUNK_RE.match(line):
            chunk_id = m.group("id").strip()
            title = (m.group("title") or "").strip() or chunk_id
            markers.append((i, title))
            continue
        if m := SECTION_RE.match(line):
            legacy_sections.append((i, line.strip().lstrip("# ").strip()))

    # Prefer the deterministic marker. Fall back to legacy section headings only
    # if no markers exist anywhere in the document.
    sections = markers if markers else legacy_sections

    if not slides:
        return []

    first_slide_num = slides[0][1]
    last_slide_num = slides[-1][1]
    total_slides = last_slide_num - first_slide_num + 1

    if not sections:
        if total_slides <= FALLBACK_THRESHOLD:
            return [{
                "part": 0,
                "title": "Full deck",
                "slide_range": [first_slide_num, last_slide_num],
            }]
        # Fixed-size fallback for large unmarked outlines
        chunks: list[dict] = []
        for start in range(first_slide_num, last_slide_num + 1, DEFAULT_CHUNK_SIZE):
            end = min(start + DEFAULT_CHUNK_SIZE - 1, last_slide_num)
            chunks.append({
                "part": len(chunks),
                "title": f"Slides {start}-{end}",
                "slide_range": [start, end],
            })
        return chunks

    # Map each section to the slide number that starts it
    section_starts: list[tuple[int, str]] = []  # (start_slide_num, title)
    for sec_line, title in sections:
        nxt = next((s for s in slides if s[0] > sec_line), None)
        if nxt:
            section_starts.append((nxt[1], title))

    chunks: list[dict] = []

    # Intro chunk: slides before the first section
    first_sec_slide = section_starts[0][0]
    if first_slide_num < first_sec_slide:
        chunks.append({
            "part": 0,
            "title": "Intro",
            "slide_range": [first_slide_num, first_sec_slide - 1],
        })

    # Section chunks
    for i, (start, title) in enumerate(section_starts):
        end = section_starts[i + 1][0] - 1 if i + 1 < len(section_starts) else last_slide_num
        chunks.append({
            "part": len(chunks),
            "title": title,
            "slide_range": [start, end],
        })

    return chunks


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: split_outline.py <outline.md>", file=sys.stderr)
        return 1
    chunks = split(Path(sys.argv[1]).read_text())
    print(json.dumps(chunks, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
