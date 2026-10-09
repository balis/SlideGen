"""Tests for stages 1 and 2 of field trends: items, classification, topic matching, and attention statistics."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sg import run, write  # noqa: E402

from sglib.attention import _visible, direction, log_ratio, random_effects  # noqa: E402
from sglib.harvest import compile_topics, topic_matches  # noqa: E402


def test_topic_matching():
    topics = [{"id": "iceberg", "aliases": ["Apache Iceberg", "Iceberg"], "exclude": ["iceberg lettuce"]},
              {"id": "rag", "aliases": ["RAG", "retrieval-augmented generation"]},
              {"id": "dbt", "aliases": ["dbt"]}]
    c = compile_topics(topics)
    assert topic_matches(c, "Migrating to Apache Icebergs at Acme") == ["iceberg"]          # plural allowed
    assert topic_matches(c, "Growing iceberg lettuce") == []                                # excluded phrase
    assert topic_matches(c, "Building RAG pipelines") == ["rag"]
    assert topic_matches(c, "a rag doll") == []                                             # ALL-CAPS alias is case-sensitive
    assert topic_matches(c, "Retrieval augmented generation on dbt models") == ["rag", "dbt"]
    assert topic_matches(c, "dbtcloud") == []                                               # whole words only


def test_statistics():
    y, v = log_ratio(20, 100, 10, 100)
    assert math.isclose(y, math.log(20.5 / 100.5) - math.log(10.5 / 100.5))
    one = random_effects([y], [v])
    assert math.isclose(one["log_ratio"], y) and one["low"] < y < one["high"]
    agree = random_effects([0.7, 0.69, 0.71], [0.01, 0.02, 0.01])
    assert direction(agree) == "up" and agree["tau2"] == 0
    split = random_effects([1.0, -1.0], [0.01, 0.01])   # disagreeing sources widen the interval
    assert split["tau2"] > 0 and direction(split) == "flat"
    assert direction(None) == "not measured"


def test_visibility():
    cfg = {"families": {"vendor_talks": {"role": "items", "quota": 1, "vendor": True},
                        "practitioner_talks": {"role": "items", "quota": 1}},
           "own_topics": {"vendor-summit": ["Apache Spark", "VendorDB"]},
           "sees_only": {"asf-con": {"text": "ASF projects", "foundation": "ASF"}}}
    vendor = {"key": "vendor-summit", "family": "vendor_talks", "organiser": "Vendor Inc"}
    asf = {"key": "asf-con", "family": "practitioner_talks", "organiser": "ASF"}
    t = lambda name, kind="tool", foundation=None, vend=None: {
        "name": name, "qualified": name, "aliases": [name], "kind": kind, "foundation": foundation, "vendor": vend}
    assert _visible(cfg, vendor, t("Apache Spark", foundation="ASF")) == (False, "own topic")
    assert _visible(cfg, vendor, t("Snowflake", vend="Snowflake")) == (False, "competitor's product")
    assert _visible(cfg, vendor, t("data contracts", kind="concept"))[0]
    assert _visible(cfg, asf, t("dbt"))[0] is False                       # not an ASF project
    assert _visible(cfg, asf, t("Apache Flink", foundation="ASF"))[0]
    assert _visible(cfg, asf, t("data mesh", kind="concept"))[0]


def test_items_classification_and_topics(tmp_path):
    root = tmp_path / "t"
    store = root / "sources"
    page = lambda name, text: run("fetch", "--file", write(tmp_path / name, text), "--store", store)["fetched"]
    titles26 = [f"Streaming lakehouse with Apache Iceberg part {i}" for i in range(15)] + \
               [f"Hiring great engineers, session {i}" for i in range(10)]
    titles25 = [f"Batch ETL with Apache Spark, case {i}" for i in range(20)] + ["Apache Iceberg intro day"]
    p26, p25 = page("p26.txt", "Programme 2026. " + " ".join(titles26)), page("p25.txt", "Programme 2025. " + " ".join(titles25))
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "data engineering", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                 "previous": ["2024-10-08", "2025-10-07"]}, "routes": {"lists": "x"},
        "families": {"practitioner_talks": {"role": "items", "quota": 1, "min_items": 5}},
        "anchors": [{"name": "Apache Iceberg"}]}))
    ws = root / "trends"
    row = {"key": "conf", "name": "Conf", "family": "practitioner_talks", "organiser": "Conf", "vendor": False,
           "single_technology": False, "selected": True,
           "verified": {"current": {"items": 25}, "previous": {"items": 21}}}
    write(ws / "sources_panel.json", {"sources": [row]})
    items = lambda titles: [{"id": f"i{n}", "title": t} for n, t in enumerate(titles)]
    write(ws / "items" / "conf.json", {"source": "conf", "parser": "x.py", "editions": {
        "current": {"pages": [p26], "note": None, "items": items(titles26)},
        "previous": {"pages": [p25], "note": None, "items": items(titles25 + ["A title that is not on the page", "Nor is this one at all"])}}})
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "2 of 23 titles not in the stored pages" in r["problems"][0]
    write(ws / "items" / "conf.json", {"source": "conf", "parser": "x.py", "editions": {
        "current": {"pages": [p26], "note": None, "items": items(titles26)},
        "previous": {"pages": [p25], "note": None, "items": items(titles25)}}})
    assert run("trends", "items-check", "--manifest", manifest)["ok"]
    prep = run("trends", "classify-prep", "--manifest", manifest)
    assert prep["sources"]["conf"] == {"items": 46, "batches": 1, "check": 46}   # editions smaller than the sample
    batch = json.loads((ws / "classify" / "conf" / "batch_01.json").read_text())
    assert all(set(i) == {"id", "title", "text", "presenter"} for i in batch["items"])   # no edition shown
    label = lambda i: {"id": i["id"], "in_scope": not i["title"].startswith("Hiring"), "sponsored": False}
    write(ws / "classify" / "conf" / "batch_01.labels.json",
          {"batch": batch["batch"], "labels": [label(i) for i in batch["items"]]})
    check = json.loads((ws / "classify" / "conf" / "check.json").read_text())
    write(ws / "classify" / "conf" / "check.labels.json",
          {"batch": check["batch"], "labels": [label(i) for i in check["items"]]})
    r = run("trends", "classify-join", "--manifest", manifest)
    assert r["ok"]
    cls = json.loads((ws / "classified" / "conf.json").read_text())
    assert len(cls["editions"]["current"]["measured"]) == 15 and len(cls["editions"]["previous"]["measured"]) == 21
    write(ws / "topics.json", {"topics": [
        {"id": "apache-iceberg", "name": "Apache Iceberg", "kind": "format", "aliases": ["Apache Iceberg", "Iceberg"],
         "foundation": "ASF", "vendor": None, "qualified": "Apache Iceberg"},
        {"id": "apache-spark", "name": "Apache Spark", "kind": "tool", "aliases": ["Apache Spark", "PySpark"],
         "foundation": "ASF", "vendor": None, "qualified": "Apache Spark"}]})
    r = run("trends", "topics-check", "--manifest", manifest)
    assert r["ok"]
    m = json.loads((ws / "matches.json").read_text())["matches"]
    assert len(m["apache-iceberg"]["conf"]["current"]) == 15 and len(m["apache-spark"]["conf"]["previous"]) == 20
    r = run("trends", "attention", "--manifest", manifest)
    att = json.loads((ws / "attention.json").read_text())["topics"]
    assert att["apache-iceberg"]["families"]["practitioner_talks"]["direction"] == "up"
    assert att["apache-spark"]["families"]["practitioner_talks"]["direction"] == "down"


def test_parse_job_board_table():
    from sglib.attention import _parse_itjw
    page = ("<table><tr><td>6 months to</td><td>8 Oct 2026</td><td>Same period 2025</td><td>Same period 2024</td></tr>"
            "<tr><td>Permanent jobs citing Apache Spark</td><td>1,272</td><td>240</td><td>288</td></tr>"
            "<tr><td>As % of all permanent jobs in the UK</td><td>0.23%</td><td>0.48%</td><td>0.39%</td></tr></table>")
    assert _parse_itjw(page) == {"current": 1272, "previous": 240, "share_current": 0.0023,
                                 "share_previous": 0.0048, "period": "8 Oct 2026"}
    assert _parse_itjw("<html>No such skill</html>") is None


def test_collectors_by_type(tmp_path):
    """Forum and adoption sources are measured by collector type, configured in the manifest or the verification."""
    from sglib.attention import COUNTERS, _adoption, collector_of
    from sglib.harvest import compile_topics  # noqa: F401  (patterns are built inside the counters)
    ws = tmp_path / "trends"
    raw = ws / "queries" / "raw" / "reddit-hpc"
    write(raw / "current.jsonl", "\n".join(json.dumps({"id": str(i), "title": t}) for i, t in
                                            enumerate(["Slurm job arrays", "MPI on GPUs", "Slurm vs PBS", "coffee"])))
    write(raw / "previous.jsonl", "\n".join(json.dumps({"id": str(i), "title": t}) for i, t in
                                             enumerate(["PBS scripts", "MPI tuning", "coffee", "tea"])))
    cfg = {"_ws": ws, "collectors": {"reddit-hpc": {"type": "reddit", "subreddit": "HPC"}}}
    topics = [{"id": "slurm", "name": "Slurm", "qualified": "Slurm", "aliases": ["Slurm"], "kind": "tool"},
              {"id": "mpi", "name": "MPI", "qualified": "MPI", "aliases": ["MPI"], "kind": "tool"}]
    col = collector_of(cfg, None, "reddit-hpc")
    n, k = COUNTERS[col["type"]](cfg, "reddit-hpc", col, topics)
    assert n == {"current": 4, "previous": 4} and k["slurm"] == {"current": 2, "previous": 0}
    verified_col = {"verified": {"collector": {"type": "survey_table"}}}
    assert collector_of({"_ws": ws}, verified_col, "hpc-survey") == {"type": "survey_table"}
    rows = lambda d: [{"name": k, "percent": v} for k, v in d.items()]
    write(ws / "queries" / "hpc-survey.json", {"source": "hpc-survey", "question": "Which schedulers do you use?",
                                               "editions": {"current": {"fetched": ["a"], "rows": rows({"Slurm": 61.0, "PBS": 20.0})},
                                                            "previous": {"fetched": ["b"], "rows": rows({"Slurm": 55.5, "PBS": 24.0})}}})
    t2 = [{**t, "survey_names": [t["name"]]} for t in topics]
    out = _adoption({"_ws": ws}, "hpc-survey", {"type": "survey_table"}, verified_col, t2, None)
    assert out == {"slurm": {"current": 61.0, "previous": 55.5, "delta_pp": 5.5, "direction": "up", "kind": "survey"}}


def test_manifest_schema(tmp_path):
    """A manifest without family roles or anchors is rejected before any work starts."""
    manifest = write(tmp_path / "t" / "trends.yaml", yaml.safe_dump({
        "field": "f", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                "previous": ["2024-10-08", "2025-10-07"]},
        "routes": {"lists": "x"}, "families": {"talks": {"quota": 2}}}))
    r = run("trends", "sources-merge", "--manifest", manifest)
    assert not r["ok"] and "'role' is a required property" in r["error"] and "'anchors' is a required" in r["error"]



def test_survey_check(tmp_path):
    """Every extracted answer and its percentage must appear in the edition's stored page."""
    root = tmp_path / "t"
    store = root / "sources"
    page = lambda name, text: run("fetch", "--file", write(tmp_path / name, text * 8), "--store", store)["fetched"]
    p26 = page("s26.txt", "Which schedulers do you use? Slurm 61% PBS Pro 20,0% LSF 7.5% ")
    p25 = page("s25.txt", "Which schedulers do you use? Slurm 55.5% PBS Pro 24% LSF 9% ")
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "f", "scope": "s", "windows": {"current": ["2025-10-09", "2026-10-09"],
                                                "previous": ["2024-10-09", "2025-10-08"]},
        "routes": {"lists": "x"}, "families": {"talks": {"role": "items", "quota": 1}}, "anchors": [{"name": "x"}]}))
    table = lambda cur: {"source": "hpc-survey", "question": "Which schedulers do you use?", "editions": {
        "current": {"fetched": [p26], "rows": [{"name": n, "percent": v} for n, v in cur]},
        "previous": {"fetched": [p25], "rows": [{"name": "Slurm", "percent": 55.5}, {"name": "PBS Pro", "percent": 24},
                                               {"name": "LSF", "percent": 9}]}}}
    write(root / "trends" / "queries" / "hpc-survey.json", table([("Slurm", 61), ("PBS Pro", 20.0), ("LSF", 7.5)]))
    assert run("trends", "survey-check", "--manifest", manifest, "--source", "hpc-survey")["ok"]
    write(root / "trends" / "queries" / "hpc-survey.json", table([("Slurm", 66), ("PBS Pro", 20.0), ("LSF", 7.5)]))
    r = run("trends", "survey-check", "--manifest", manifest, "--source", "hpc-survey")
    assert not r["ok"] and "1 of 3 rows not found" in r["problems"][0]
