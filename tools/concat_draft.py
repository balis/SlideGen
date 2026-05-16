#!/usr/bin/env python3
"""Concatenate chunked draft files into a single Marp deck.

Usage:
  python3 concat_draft.py <output_path> <chunk_glob>

Reads chunk files matching <chunk_glob> in sorted order, prepends the Marp
frontmatter, joins chunks with `---` separators, writes the result to
<output_path>. Each chunk file is expected to contain raw slide content
(no frontmatter, no leading/trailing separators).
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

FRONTMATTER = """---
marp: true
theme: default
paginate: true
---
"""

SEPARATOR = "\n\n---\n\n"


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: concat_draft.py <output_path> <chunk_glob>", file=sys.stderr)
        return 1

    out_path = Path(sys.argv[1])
    chunk_paths = sorted(glob.glob(sys.argv[2]))
    if not chunk_paths:
        print(f"No chunk files matched: {sys.argv[2]}", file=sys.stderr)
        return 1

    parts: list[str] = []
    for cp in chunk_paths:
        text = Path(cp).read_text().strip()
        # Strip any leading/trailing slide separators a chunk may have left behind.
        while text.startswith("---"):
            text = text[3:].lstrip("\n")
        while text.endswith("---"):
            text = text[:-3].rstrip("\n")
        if text:
            parts.append(text)

    if not parts:
        print("All chunk files were empty.", file=sys.stderr)
        return 1

    body = SEPARATOR.join(parts)
    out_path.write_text(FRONTMATTER + "\n" + body + "\n")
    print(f"Wrote {out_path}: {len(parts)} chunks, {len(body)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
