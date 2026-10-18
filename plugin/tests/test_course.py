"""Tests for the course-plan commands of sg on a synthetic two-lecture course."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sg import run, write  # noqa: E402

SYLLABUS_A = """Data Engineering (Fall 2025)
Week 1: Distributed storage and object stores
Week 2: Columnar file formats and Parquet
Week 3: Stream processing with Kafka
"""
SYLLABUS_B = """Big Data Systems 2026
Lecture 1 - Distributed storage systems
Lecture 2 - Columnar file formats
Lecture 3 - LLM agents for data pipelines
"""
TEXTBOOK = """Contents
Chapter 1. Distributed storage
Chapter 2. Stream processing fundamentals
Chapter 3. Columnar storage formats
"""


def _ref(id_, kind, org, year, fetched, topics, vendor=False, level="bachelor"):
    return {"id": id_, "kind": kind, "title": id_, "url": f"file:{id_}", "org": org, "year": year,
            "level": level, "vendor": vendor, "fetched": fetched,
            "topics": [{"label": l, "quote": q, "weight": 1} for l, q in topics]}


def test_course_plan_flow(tmp_path):
    root = tmp_path / "course"
    plan = write(root / "plan.yaml", yaml.safe_dump({
        "name": "Test course", "level": "bachelor", "lectures": {"count": 2, "hours": 2},
        "current": [{"n": 1, "title": "Storage"}, {"n": 2, "title": "Formats"}],
        "references": {"syllabus": 2, "textbook": 1, "paper": 0, "professional": 0,
                       "recent_years": 3, "max_vendor_share": 0.5}}))
    store = root / "sources"
    ids = {}
    for name, text in (("a.txt", SYLLABUS_A), ("b.txt", SYLLABUS_B), ("book.txt", TEXTBOOK)):
        src = write(tmp_path / name, text * 4)   # long enough to count as a page
        ids[name] = run("fetch", "--file", src, "--store", store)["fetched"]
    ws = root / "plan"

    write(ws / "references" / "syllabus.json", {"kind": "syllabus", "searched": ["x"], "references": [
        _ref("uni-a-2025", "syllabus", "Uni A", 2025, ids["a.txt"], [
            ("storage", "Distributed storage and object stores"), ("formats", "Columnar file formats and Parquet"),
            ("streaming", "Stream processing with Kafka")]),
        _ref("uni-b-2026", "syllabus", "Uni B", 2026, ids["b.txt"], [
            ("storage", "Distributed storage systems"), ("formats", "Columnar file formats"),
            ("agents", "LLM agents for data pipelines")]),
        _ref("uni-a-again", "syllabus", "Uni A", 2025, ids["a.txt"], [
            ("storage", "Distributed storage and object stores"), ("formats", "Columnar file formats and Parquet"),
            ("streaming", "Stream processing with Kafka")]),
        _ref("uni-c-2015", "syllabus", "Uni C", 2015, ids["a.txt"], [
            ("storage", "Distributed storage and object stores"), ("formats", "Columnar file formats and Parquet"),
            ("streaming", "Stream processing with Kafka")])]})
    write(ws / "references" / "textbook.json", {"kind": "textbook", "searched": ["y"], "references": [
        _ref("book", "textbook", "Publisher", 2019, ids["book.txt"], [
            ("storage", "Distributed storage"), ("streaming", "Stream processing fundamentals"),
            ("formats", "Columnar storage formats"),
            ("invented", "A chapter that is not in the book")], level="general")]})

    r = run("course", "refs", "--plan", plan)
    assert r["ok"] and r["counts"] == {"syllabus": 2, "textbook": 1, "paper": 0, "professional": 0}, r
    reasons = {x["id"]: " ".join(x["reasons"]) for x in r["rejected"]}
    book = [a for a in json.loads((ws / "references_check.json").read_text())["accepted"] if a["id"] == "book"][0]
    assert [t["matched"] for t in book["topics"]] == [True, True, True, False]
    assert "second syllabus from Uni A" in reasons["uni-a-again"] and "older than" in reasons["uni-c-2015"]

    taxonomy = {"areas": [{"id": "A1", "title": "Systems"}], "topics": [
        {"id": "T1", "title": "Distributed storage", "area": "A1", "description": "d", "depends_on": []},
        {"id": "T2", "title": "File formats", "area": "A1", "description": "d", "depends_on": ["T1"]},
        {"id": "T3", "title": "Stream processing", "area": "A1", "description": "d", "depends_on": ["T1"]},
        {"id": "T4", "title": "LLM agents", "area": "A1", "description": "d", "depends_on": []}],
        "mapping": [{"ref": "uni-a-2025", "label": "storage", "topic": "T1"},
                    {"ref": "uni-a-2025", "label": "formats", "topic": "T2"},
                    {"ref": "uni-a-2025", "label": "streaming", "topic": "T3"},
                    {"ref": "uni-b-2026", "label": "storage", "topic": "T1"},
                    {"ref": "uni-b-2026", "label": "formats", "topic": "T2"},
                    {"ref": "book", "label": "storage", "topic": "T1"},
                    {"ref": "book", "label": "streaming", "topic": "T3"},
                    {"ref": "book", "label": "formats", "topic": "T2"},
                    {"ref": "book", "label": "invented", "topic": "T3"}]}
    write(ws / "taxonomy.json", taxonomy)
    r = run("course", "taxonomy", "--plan", plan)
    assert not r["ok"] and "not mapped" in r["error"] and "T4" in r["error"], r
    taxonomy["mapping"].append({"ref": "uni-b-2026", "label": "agents", "topic": "T4"})
    write(ws / "taxonomy.json", taxonomy)
    r = run("course", "taxonomy", "--plan", plan)
    assert r["ok"] and r["tiers"] == {"core": 3, "common": 1, "niche": 0}, r
    rows = {t["topic"]: t for t in json.loads((ws / "reference_curriculum.json").read_text())["topics"]}
    assert rows["T1"]["references"] == 3 and rows["T4"]["references"] == 1
    # a combined line may count for two topics
    taxonomy["mapping"].append({"ref": "uni-b-2026", "label": "formats", "topic": "T3"})
    write(ws / "taxonomy.json", taxonomy)
    assert run("course", "taxonomy", "--plan", plan)["ok"]
    rows = {t["topic"]: t for t in json.loads((ws / "reference_curriculum.json").read_text())["topics"]}
    assert rows["T3"]["references"] == 3 and rows["T2"]["references"] == 3

    write(ws / "mapping.json", {"lectures": [
        {"n": 1, "title": "Storage", "topics": [{"topic": "T1", "label": "HDFS", "hours": 1},
                                                {"topic": None, "label": "Hadoop hardware sizing", "hours": 1}]},
        {"n": 2, "title": "Formats", "topics": [{"topic": "T2", "label": "Parquet", "hours": 2}]}]})
    r = run("course", "gaps", "--plan", plan)
    assert r["ok"] and r["missing"] == 2 and r["current_only"] == 1, r   # T3 and T4 are not taught

    lecture = lambda n, topics, minutes=120, reuse=(): {"n": n, "title": f"L{n}", "summary": "s", "objectives": ["o"],
                                                        "topics": [{"topic": t, "hours": h, "depth": "core"} for t, h in topics],
                                                        "reuse": list(reuse),
                                                        "new_material": [{"what": "slides", "minutes": minutes}]}
    decisions = [{"id": f"D{i:02d}", "title": "t", "summary": "s", "lectures": [1]} for i in range(1, 14)]
    write(ws / "proposal.json", {"rationale": "r", "assumed_prerequisites": [], "dropped": [], "decisions": decisions,
                                 "lectures": [lecture(1, [("T2", 1), ("T3", 1)]), lecture(2, [("T1", 2)])]})
    r = run("course", "validate", "--plan", plan)
    assert not r["ok"] and "comes later" in r["error"] and "at most 12" in r["error"] and "T4" in r["error"], r
    assert "no lectures.slides" in r["error"], r
    cfg = yaml.safe_load(plan.read_text())
    cfg["lectures"]["slides"] = [40, 60]        # 50 slides per 120 minutes
    write(plan, yaml.safe_dump(cfg))
    write(ws / "proposal.json", {"rationale": "r", "assumed_prerequisites": [],
                                 "dropped": [{"topic": "T4", "reason": "too early for bachelors"}],
                                 "decisions": decisions[:2],
                                 "lectures": [lecture(1, [("T1", 1), ("T2", 1)]), lecture(2, [("T3", 2)], minutes=40)]})
    r = run("course", "validate", "--plan", plan)
    assert not r["ok"] and "lecture 2 has about 17 slides" in r["error"] and "96-120 min of material" in r["error"], r
    assert "lecture 2: its topics take 120 min but its material takes about 40 min" in r["error"], r
    assert "lecture 1" not in r["error"], r
    # the material fits the slot and agrees with the topic hours; a reused slide takes one slide's time at the pace
    cfg["decks"] = [{"id": "old", "path": "old.pptx"}]
    write(plan, yaml.safe_dump(cfg))
    reuse = [{"deck": "old", "slides": list(range(1, 26)), "note": "n"}]
    write(ws / "proposal.json", {"rationale": "r", "assumed_prerequisites": [],
                                 "dropped": [{"topic": "T4", "reason": "too early for bachelors"}],
                                 "decisions": decisions[:2],
                                 "lectures": [lecture(1, [("T1", 1), ("T2", 0.75)], minutes=60, reuse=reuse),
                                              lecture(2, [("T3", 2)], minutes=126)]})
    r = run("course", "validate", "--plan", plan)
    assert not r["ok"] and "has about" not in r["error"], r   # both slide estimates are within the range
    assert ("lecture 1: its topics take 105 min but its material takes about 120 min (25 reused slides + 60 min"
            in r["error"]), r
    assert "lecture 2: its material takes about 126 min" in r["error"] and "the slot is 120 min" in r["error"], r
    write(ws / "proposal.json", {"rationale": "r", "assumed_prerequisites": [],
                                 "dropped": [{"topic": "T4", "reason": "too early for bachelors"}],
                                 "decisions": decisions[:2],
                                 "lectures": [lecture(1, [("T1", 1), ("T2", 1)], minutes=60, reuse=reuse),
                                              lecture(2, [("T3", 2)])]})
    r = run("course", "validate", "--plan", plan)
    assert r["ok"] and r["core_placed"] == 3 and r["dropped"] == 1, r
    assert r["per_lecture_minutes"] == {"1": 120, "2": 120}, r
    r = run("course", "report", "--plan", plan)
    assert r["ok"] and r["per_lecture_slides"] == {"1": 50, "2": 50}, r
    assert "about 50" in (ws / "curriculum_proposal.md").read_text()
    decisions_md = (ws / "decisions.md").read_text()
    assert decisions_md.count("- [x] **D0") == 2
    assert "Gaps in the current curriculum" in (ws / "curriculum_proposal.md").read_text()


def test_course_trends(tmp_path):
    """Field trends link to course topics; a new topic for a growing trend must be decided by the proposal."""
    test_course_plan_flow(tmp_path)
    root = tmp_path / "course"
    plan = root / "plan.yaml"
    cfg = yaml.safe_load(plan.read_text())
    cfg["trends"] = "../trends"
    write(plan, yaml.safe_dump(cfg))
    ws = root / "plan"
    topic = lambda name, verdict, mentions=0: {"name": name, "kind": "concept", "verdict": verdict,
                                               "families": {"talks": {"mentions": mentions}}, "adoption": {}}
    write(tmp_path / "trends" / "attention.json", {"topics": {
        "iceberg": topic("Apache Iceberg", "steady", 5), "hadoop": topic("Apache Hadoop", "falling in one family"),
        "delta": topic("Delta Lake", "steady", 9), "hudi": topic("Apache Hudi", "steady", 7),
        "paimon": topic("Apache Paimon", "steady", 1), "lance": topic("Lance", "too little evidence"),
        "orc": topic("ORC", "rising in one family"),
        "semantic-layer": topic("Semantic layer", "growing"), "power-bi": topic("Power BI", "rising in one family")}})
    write(tmp_path / "trends" / "profiles.json", {"topics": [
        {"id": "semantic-layer", "status": "generally available", "organizations": ["A", "B"]}]})
    write(ws / "trend_map.json", {"links": [
        {"trend": "iceberg", "topic": "T2"}, {"trend": "hadoop", "topic": "T1"},
        {"trend": "delta", "topic": "T2"}, {"trend": "hudi", "topic": "T2"}, {"trend": "paimon", "topic": "T2"},
        {"trend": "lance", "topic": "T2"}, {"trend": "orc", "topic": "T2"},
        {"trend": "semantic-layer", "topic": "N01"}, {"trend": "power-bi", "topic": None}],
        "new_topics": [{"id": "N01", "title": "Semantic layer", "area": "A1", "depends_on": ["T2"], "why": "none"}]})
    gap_file = ws / "gap_analysis.json"
    gap_file.rename(ws / "gap_analysis.saved")
    r = run("course", "trends", "--plan", plan)
    assert r["ok"] and "gap_analysis.json is missing" in r["warnings"][0], r
    assert "**Warning:** gap_analysis.json is missing" in (ws / "trend_gaps.md").read_text()
    (ws / "gap_analysis.saved").rename(gap_file)
    r = run("course", "trends", "--plan", plan)
    assert r["ok"] and r["new_topics"] == 1 and r["must_decide"] == 1 and r["current_out_of_scope"] == 1, r
    assert r["warnings"] == [], r
    t = json.loads((ws / "trends.json").read_text())
    assert t["topics"]["T1"]["attention"] == "falling" and t["topics"]["N01"]["attention"] == "growing"
    gaps = (ws / "trend_gaps.md").read_text()
    assert "N01 Semantic layer" in gaps and "Power BI" in gaps and "Warning" not in gaps
    # one rising topic among several steady ones: the line counts them and names the most discussed steady ones
    assert ("- **T2 File formats**: rising; 6 linked trend topics; rising or falling: ORC (rising in one family); "
            "steady: 4 (Delta Lake, Apache Hudi, Apache Iceberg, …); too little evidence: 1") in gaps, gaps
    assert "- **T1 Distributed storage**: falling; 1 linked trend topic; rising or falling: Apache Hadoop" in gaps
    r = run("course", "validate", "--plan", plan)
    assert not r["ok"] and "new topic N01" in r["error"], r
    prop = json.loads((ws / "proposal.json").read_text())
    prop["lectures"][1]["topics"].append({"topic": "N01", "hours": 0.5, "depth": "overview"})
    prop["lectures"][1]["topics"][0]["hours"] = 1.5
    write(ws / "proposal.json", prop)
    assert run("course", "validate", "--plan", plan)["ok"]
    r = run("course", "report", "--plan", plan)
    assert r["ok"] and "| Attention now | Maturity |" in (ws / "curriculum_proposal.md").read_text()
