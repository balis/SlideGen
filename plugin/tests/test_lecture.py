"""Tests for the lecture outline check on a synthetic two-lecture course."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sg import make_pptx, run, write  # noqa: E402


def _course(tmp_path) -> Path:
    root = tmp_path / "course"
    root.mkdir()
    make_pptx(root / "old.pptx", ["Intro", "Storage", "Hidden extra"], hidden={3})
    plan = write(root / "plan.yaml", yaml.safe_dump({
        "name": "Test course", "level": "bachelor", "lectures": {"count": 2, "hours": 1.5, "slides": [10, 12]},
        "decks": [{"id": "old", "path": "old.pptx"}]}))
    lecture = lambda n, topics: {"n": n, "title": f"L{n}", "summary": "s", "objectives": ["o"],
                                 "topics": [{"topic": t, "hours": h, "depth": "core"} for t, h in topics]}
    write(root / "plan" / "proposal.json", {
        "rationale": "r", "assumed_prerequisites": [], "dropped": [],
        "decisions": [{"id": "D01", "title": "t", "summary": "s", "lectures": [1]}],
        "lectures": [lecture(1, [("T1", 0.9), ("T2", 0.45)]), lecture(2, [("T3", 1.4)])]})
    return plan


def _outline(slides):
    """Slides as (topic, kind, extra) triples, numbered in order."""
    return {"lecture": 1, "slides": [{"n": i, "title": f"Slide {i}", "topic": t, "kind": k, **x}
                                     for i, (t, k, x) in enumerate(slides, 1)]}


GOOD = ([(None, "reuse", {"reuse": {"deck": "old", "slide": 1}})]
        + [("T1", "new", {})] * 5 + [("T1", "reuse", {"reuse": {"deck": "old", "slide": 3}})]
        + [("T2", "new", {})] * 3 + [("T3", "new", {"preview_of": 2})] + [(None, "new", {})])


def test_outline_check(tmp_path):
    plan = _course(tmp_path)
    out = tmp_path / "course" / "lectures" / "L01" / "outline.json"
    write(out, _outline(GOOD))
    r = run("lecture", "outline-check", "--plan", plan, "--lecture", "1")
    assert r["ok"] and r["slides"] == 12 and r["reused"] == 2 and r["previews"] == 1, r
    assert r["warnings"] and "hidden" in r["warnings"][0], r

    def fails(slides, expected):
        write(out, _outline(slides))
        r = run("lecture", "outline-check", "--plan", plan, "--lecture", "1")
        assert not r["ok"] and expected in r["error"], r

    fails(GOOD[:6], "6 slides; the author expects 10-12")
    fails([s if s[0] != "T2" else ("T1", "new", {}) for s in GOOD], "topic T2 is planned for this lecture but has no slide")
    fails(GOOD[:1] + [("T1", "new", {})] * 2 + [("T2", "new", {})] * 7 + GOOD[-2:], "topic T2: 7 slides")
    fails(GOOD[:-2] + [("T3", "new", {}), GOOD[-1]], "topic T3 is taught in lecture 2")
    fails(GOOD[:-1] + [(None, "reuse", {"reuse": {"deck": "old", "slide": 9}})], "deck old has 3 slides, not 9")
    fails(GOOD[:-1] + [(None, "reuse", {})], "kind reuse needs `reuse`")


def test_outline_matches_spec(tmp_path):
    """The deck specification must build the outline's slides and copy the template where the outline reuses it."""
    plan = _course(tmp_path)
    lec = tmp_path / "course" / "lectures" / "L01"
    write(lec / "outline.json", _outline(GOOD))
    built = lambda: [{"copy": 1}] + [{"layout": "Title Only", "title": f"s{i}"} for i in range(2, 13)]
    spec = built()
    spec[6] = {"copy": 3}                       # outline slide 7 reuses template slide 3
    write(lec / "deck.json", {"base": "../../old.pptx", "output": "l1.pptx", "slides": spec})
    r = run("lecture", "outline-check", "--plan", plan, "--lecture", "1", "--spec", lec / "deck.json")
    assert r["ok"], r
    write(lec / "deck.json", {"base": "../../old.pptx", "output": "l1.pptx", "slides": built()[:11]})
    r = run("lecture", "outline-check", "--plan", plan, "--lecture", "1", "--spec", lec / "deck.json")
    assert not r["ok"] and "the spec has 11 slides, the outline 12" in r["error"]
    assert "slide 7: the outline reuses old slide 3, but the spec builds a new slide" in r["error"], r
    spec[3] = {"copy": 2}                       # outline slide 4 is new
    write(lec / "deck.json", {"base": "../../old.pptx", "output": "l1.pptx", "slides": spec})
    r = run("lecture", "outline-check", "--plan", plan, "--lecture", "1", "--spec", lec / "deck.json")
    assert not r["ok"] and "slide 4: the outline says new, but the spec copies template slide 2" in r["error"], r
