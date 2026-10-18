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


def test_items_parser_is_kept(tmp_path):
    """An items file names its parser inside the project with a hash; a changed, missing or outside parser fails."""
    import subprocess
    root = tmp_path / "t"
    store = root / "sources"
    titles = [f"Scaling Kubernetes clusters, part {i}" for i in range(6)]
    pid = run("fetch", "--file", write(tmp_path / "p.txt", "Programme. " + " ".join(titles)), "--store", store)["fetched"]
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "f", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                "previous": ["2024-10-08", "2025-10-07"]}, "routes": {"lists": "x"},
        "families": {"talks": {"role": "items", "quota": 1}}, "anchors": [{"name": "x"}]}))
    ws = root / "trends"
    write(ws / "sources_panel.json", {"sources": [{"key": "conf", "family": "talks", "selected": True,
                                                   "verified": {"current": {"items": 6}, "previous": {"items": 6}}}]})
    parser = write(ws / "parsers" / "conf.py", f'''import hashlib, json
from pathlib import Path
me = Path(__file__).resolve()
ROOT = me.parents[2]
items = [{{"id": str(i), "title": t}} for i, t in enumerate({titles!r})]
doc = {{"source": "conf", "parser": str(me.relative_to(ROOT)),
       "parser_sha256": hashlib.sha256(me.read_bytes()).hexdigest(),
       "editions": {{ed: {{"pages": ["{pid}"], "note": None, "items": items}} for ed in ("current", "previous")}}}}
(ROOT / "trends" / "items").mkdir(exist_ok=True)
(ROOT / "trends" / "items" / "conf.json").write_text(json.dumps(doc))
''')
    subprocess.run([sys.executable, str(parser)], check=True)
    r = run("trends", "items-check", "--manifest", manifest)
    assert r["ok"] and not [w for w in r["warnings"] if "parser" in w]
    assert "conf current: page" in r["warnings"][0] and "stored from a local file (p.txt)" in r["warnings"][0]
    parser.write_text(parser.read_text() + "# edited\n")
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "changed after it wrote the items" in r["problems"][0]
    parser.unlink()
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "is missing" in r["problems"][0]
    doc = json.loads((ws / "items" / "conf.json").read_text())
    write(ws / "items" / "conf.json", {**doc, "parser": str(tmp_path / "scratch" / "conf.py")})
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "outside the project" in r["problems"][0]
    del doc["parser_sha256"]
    write(ws / "items" / "conf.json", doc)   # written before parsers were kept: a warning only
    r = run("trends", "items-check", "--manifest", manifest)
    assert r["ok"] and "not recorded with its hash" in r["warnings"][0]


def test_parse_job_board_table():
    from sglib.attention import _parse_itjw
    page = ("<table><tr><td>6 months to</td><td>8 Oct 2026</td><td>Same period 2025</td><td>Same period 2024</td></tr>"
            "<tr><td>Permanent jobs citing Apache Spark</td><td>1,272</td><td>240</td><td>288</td></tr>"
            "<tr><td>As % of all permanent jobs in the UK</td><td>0.23%</td><td>0.48%</td><td>0.39%</td></tr></table>")
    assert _parse_itjw(page) == {"current": 1272, "previous": 240, "share_current": 0.0023,
                                 "share_previous": 0.0048, "period": "8 Oct 2026"}
    assert _parse_itjw("<html>No such skill</html>") is None


def test_job_board_failures_are_retried(tmp_path, monkeypatch):
    """A refused or failed request stops the collector without caching; a missing skill page is cached as empty."""
    import pytest
    import requests
    from sglib import attention
    from sglib.util import SgError

    class Reply:
        def __init__(self, status: int, text: str = ""):
            self.status_code, self.text = status, text

    replies = []

    def fake_get(url, **kw):
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(attention.time, "sleep", lambda s: None)
    monkeypatch.setattr(attention.requests, "get", fake_get)
    cache = tmp_path / "slurm.html"
    for reply in (requests.ConnectionError("proxy refused"), Reply(503)):
        replies.append(reply)
        with pytest.raises(SgError, match="run the collector again"):
            attention._itjw_page("Slurm", cache)
        assert not cache.exists()
    replies.append(Reply(404, "not found"))
    assert attention._itjw_page("Slurm", cache) == "" and cache.read_text() == ""
    page = tmp_path / "kubernetes.html"
    replies.append(Reply(200, "<html>page</html>"))
    assert attention._itjw_page("Kubernetes", page) == "<html>page</html>"
    assert attention._itjw_page("Kubernetes", page) == "<html>page</html>"   # served from the cache
    assert replies == []


def test_discourse_and_mailman_collectors(tmp_path, monkeypatch):
    """A Discourse forum yields the topics created in each window, read past pinned topics until activity predates
    the windows; a Mailman 3 list yields the messages that start a thread. Both are counted by title."""
    import gzip

    from sglib import attention

    cfg = {"_ws": tmp_path, "windows": {"current": ["2025-10-09", "2026-10-09"],
                                        "previous": ["2024-10-09", "2025-10-08"]}}
    topic = lambda i, title, created, bumped, pinned=False: {"id": i, "title": title, "created_at": created + "T10:00:00Z",
                                                             "bumped_at": bumped + "T10:00:00Z", "pinned": pinned}
    pages = [[topic(1, "Read the rules", "2019-10-28", "2024-07-30", pinned=True),
              topic(2, "Kubernetes scheduler and GPUs", "2026-01-05", "2026-02-01"),
              topic(3, "Helm chart upgrade fails", "2025-03-01", "2026-01-10")],
             [topic(4, "Kubernetes ingress timeouts", "2024-12-01", "2025-01-01"),
              topic(5, "Old question", "2023-05-01", "2024-01-01")],
             [topic(6, "Older question", "2022-05-01", "2023-01-01")]]
    requested = []

    def fake_get(url, params=None, pause=1.0, tries=8):
        requested.append(params["page"])
        return {"topic_list": {"topics": pages[params["page"]], "more_topics_url": "/latest?page=next"}}

    monkeypatch.setattr(attention, "_get", fake_get)
    out = tmp_path / "queries" / "raw" / "discuss-kubernetes"
    out.mkdir(parents=True)
    assert attention._collect_discourse(cfg, out, {"url": "https://discuss.example.org/"}) == {"current": 1, "previous": 2}
    assert requested == [0, 1, 2]
    assert [json.loads(line)["title"] for line in (out / "previous.jsonl").open()] == [
        "Kubernetes ingress timeouts", "Helm chart upgrade fails"]
    assert attention._collect_discourse(cfg, out, {"url": "https://discuss.example.org"}) == {"current": 1, "previous": 2}
    assert requested == [0, 1, 2]   # both windows are on disk: nothing is downloaded again

    mbox = "".join(f"From list@example.org Mon Jan  5 10:00:00 2026\n{headers}\n\nbody\n\n" for headers in [
        "Subject: [slurm-users] GPU sharing with MPS\nDate: Mon, 05 Jan 2026 10:00:00 +0000\nMessage-ID: <1@x>",
        "Subject: [slurm-users] Re: GPU sharing with MPS\nDate: Mon, 05 Jan 2026 12:00:00 +0000\nMessage-ID: <2@x>\n"
        "In-Reply-To: <1@x>",
        "Subject: =?utf-8?q?=5Bslurm-users=5D_Accounting_with_Slurm?=\nDate: Tue, 03 Dec 2024 09:00:00 +0100\n"
        "Message-ID: <3@x>",
        "Subject: [slurm-users] Slurm versions 26.05.4 and 25.11.8 are now\n available\n"
        "Date: Wed, 02 Sep 2026 21:38:59 +0000\nMessage-ID: <4@x>"])

    class Reply:
        status_code, content = 200, gzip.compress(mbox.encode())

    exports = []

    def fake_requests_get(url, params=None, headers=None, timeout=None):
        exports.append((url, params))
        return Reply()

    monkeypatch.setattr(attention.requests, "get", fake_requests_get)
    out = tmp_path / "queries" / "raw" / "slurm-users"
    out.mkdir(parents=True)
    archive = "https://lists.example.org/mailman3/hyperkitty/list/slurm-users@lists.example.org"
    assert attention._collect_mailman3(cfg, out, {"archive": archive}) == {"current": 2, "previous": 1}
    assert exports[0] == (archive + "/export/slurm-users.mbox.gz", {"start": "2025-10-09", "end": "2026-10-10"})
    assert [json.loads(line)["title"] for line in (out / "current.jsonl").open()] == [
        "GPU sharing with MPS", "Slurm versions 26.05.4 and 25.11.8 are now available"]

    topics = [{"id": "slurm", "name": "Slurm", "qualified": "Slurm", "aliases": ["Slurm"], "kind": "tool"},
              {"id": "kubernetes", "name": "Kubernetes", "qualified": "Kubernetes", "aliases": ["Kubernetes"],
               "kind": "platform"}]
    n, k = attention.COUNTERS["mailman3"](cfg, "slurm-users", {"type": "mailman3"}, topics)
    assert n == {"current": 2, "previous": 1} and k["slurm"] == {"current": 1, "previous": 1}
    n, k = attention.COUNTERS["discourse"](cfg, "discuss-kubernetes", {"type": "discourse"}, topics)
    assert n == {"current": 1, "previous": 2} and k["kubernetes"] == {"current": 1, "previous": 1}


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
    """Every extracted answer must be printed with its percentage on one row of the edition's stored page."""
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
    assert not r["ok"] and "1 of 3 answers are not printed with their percentage" in r["problems"][0]
    # a percentage printed on the page, but for another answer, is not a pair
    write(root / "trends" / "queries" / "hpc-survey.json", table([("Slurm", 20.0), ("PBS Pro", 20.0), ("LSF", 7.5)]))
    r = run("trends", "survey-check", "--manifest", manifest, "--source", "hpc-survey")
    assert not r["ok"] and "('Slurm', 20.0)" in r["problems"][0]


def test_share_pairs_by_layout(tmp_path):
    """Names and percentages are paired within a table row, a chart group, a PDF baseline, or a prose clause."""
    import fitz

    from sglib.shares import page_rows, paired
    store = tmp_path / "store"
    html = ("<html><body><p>Which cloud platforms did you use?</p><table>"
            "<tr><td>Docker / Docker Compose</td><td>6,440</td><td>59.1%</td></tr>"
            "<tr><td>Kubernetes</td><td>3,120</td><td>28.5%</td></tr></table>"
            "<svg><g role='listitem'><text>Helm</text><g><rect></rect><text>12.4%</text></g></g>"
            "<g role='listitem'><text>Docker</text><g><rect></rect><text>40.9%</text></g></g></svg>"
            "<p>Prometheus reaches 77% production use with 12% evaluating, CoreDNS achieves 76% with 5%.</p>"
            + "<p>filler text for the extractor</p>" * 20 + "</body></html>")
    hid = run("fetch", "--file", write(tmp_path / "chart.html", html), "--store", store)["fetched"]
    doc = fitz.open()
    pg = doc.new_page()
    for y, left, right in ((100, ("Kubernetes", "85"), ("Helm", "77")), (120, ("Prometheus", "73"), ("etcd", "70"))):
        for x, text in ((50, left[0]), (150, left[1]), (300, right[0]), (400, right[1])):
            pg.insert_text((x, y), text)
    for i in range(8):
        pg.insert_text((50, 200 + 15 * i), "Graduated CNCF projects used in production.")
    doc.save(tmp_path / "report.pdf")
    pid = run("fetch", "--file", tmp_path / "report.pdf", "--store", store)["fetched"]
    from sglib.trends import _entries
    entries = _entries(store)
    rows = page_rows(store, entries[hid])
    names = ["Docker / Docker Compose", "Kubernetes", "Helm", "Docker", "Prometheus", "CoreDNS"]
    for name, pct in (("Docker / Docker Compose", 59.1), ("Kubernetes", 28.5), ("Helm", 12.4), ("Docker", 40.9),
                      ("Prometheus", 77), ("CoreDNS", 76)):
        assert paired(rows, name, pct, names), name
    assert not paired(rows, "Kubernetes", 59.1, names) and not paired(rows, "Docker", 59.1, names)
    assert not paired(rows, "Prometheus", 76, names)
    rows = page_rows(store, entries[pid])
    names = ["Kubernetes", "Helm", "Prometheus", "etcd"]
    assert all(paired(rows, n, p, names) for n, p in (("Kubernetes", 85), ("Helm", 77), ("Prometheus", 73),
                                                       ("etcd", 70)))
    assert not paired(rows, "Kubernetes", 77, names) and not paired(rows, "Helm", 85, names)


def test_survey_skips_answers_missing_from_one_edition(tmp_path):
    """An answer printed in one edition only was added to or dropped from the survey; it is not a change to 0%."""
    from sglib.attention import _survey
    ws = tmp_path / "trends"
    rows = lambda d: [{"name": k, "percent": v} for k, v in d.items()]
    write(ws / "queries" / "s.json", {"source": "s", "question": "q", "editions": {
        "current": {"fetched": ["a"], "rows": rows({"Terraform": 30.0, "OpenTofu": 12.4})},
        "previous": {"fetched": ["b"], "rows": rows({"Terraform": 28.0, "Prometheus": 11.8})}}})
    topics = [{"id": "iac", "survey_names": ["Terraform", "OpenTofu"]}, {"id": "tofu", "survey_names": ["OpenTofu"]},
              {"id": "prom", "survey_names": ["Prometheus"]}]
    out = _survey({"_ws": ws}, "s", {"type": "survey_table"}, None, topics)
    assert out == {"iac": {"current": 30.0, "previous": 28.0, "delta_pp": 2.0, "direction": "up",
                           "skipped": ["OpenTofu"]}}


def _records_project(tmp_path, family: dict, collector: dict, editions: dict, verified_items: dict):
    """A field with one records source: its stored pages, panel row and items file. `editions` maps an edition
    to (page text, records)."""
    root = tmp_path / "t"
    store = root / "sources"
    ids = {ed: run("fetch", "--file", write(tmp_path / f"{ed}.txt", text), "--store", store)["fetched"]
           for ed, (text, _) in editions.items()}
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "f", "scope": "s", "windows": {"current": ["2025-10-09", "2026-10-09"],
                                                "previous": ["2024-10-09", "2025-10-08"]},
        "routes": {"lists": "x"}, "families": {"talks": {"role": "items", "quota": 1}, "src": family},
        "anchors": [{"name": "H100"}], "collectors": {"src-key": collector}}))
    ws = root / "trends"
    write(ws / "sources_panel.json", {"sources": [{"key": "src-key", "name": "Source", "family": "src",
                                                   "selected": True, "verified": {
                                                       ed: {"items": n} for ed, n in verified_items.items()}}]})
    write(ws / "items" / "src-key.json", {"source": "src-key", "parser": "trends/parsers/src-key.py", "editions": {
        ed: {"pages": [ids[ed]], "note": None, "items": records} for ed, (_, records) in editions.items()}})
    return manifest, ws


def test_ranked_list_records(tmp_path):
    """A ranked list is measured as records: every rank once, topics matched by alias, shares with a pp change."""
    from sglib.attention import adoption_cell
    systems = {"current": ["Cray EX, AMD EPYC 9654, NVIDIA H100 SXM5, Slingshot-11",
                           "ThinkSystem, Xeon Platinum 8480+, NVIDIA H200, Infiniband NDR",
                           "Cray EX, AMD EPYC 4th Gen, AMD Instinct MI300A, Slingshot-11",
                           "Eviden BullSequana, Grace 72C, NVIDIA GH200 Superchip, Infiniband NDR200"],
               "previous": ["Cray EX, AMD EPYC 7763, AMD Instinct MI250X, Slingshot-11",
                            "ThinkSystem, Xeon Platinum 8358, NVIDIA A100, Infiniband HDR",
                            "Cray EX, AMD EPYC 7A53, AMD Instinct MI250X, Slingshot-11",
                            "PowerEdge, Xeon Gold 6248, NVIDIA H100 PCIe, Infiniband HDR"]}
    page = lambda ed: "\n".join(f"{r + 1} {s}" for r, s in enumerate(systems[ed])) + "\nList of systems. " * 8
    records = lambda ed, ranks: [{"id": str(r), "title": systems[ed][r - 1]} for r in ranks]
    manifest, ws = _records_project(
        tmp_path, {"role": "adoption", "quota": 1}, {"type": "records", "ranked": True, "unit": "systems",
                                                     "label": "Top list"},
        {ed: (page(ed), records(ed, [1, 2, 4])) for ed in ("current", "previous")}, {"current": 4, "previous": 4})
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "a ranked list needs ids 1 to 4, each once; the file has 3 records" in r["problems"][0]
    doc = json.loads((ws / "items" / "src-key.json").read_text())
    for ed in ("current", "previous"):
        doc["editions"][ed]["items"] = records(ed, [1, 2, 3, 4])
    write(ws / "items" / "src-key.json", doc)
    assert run("trends", "items-check", "--manifest", manifest)["ok"]
    assert run("trends", "classify-prep", "--manifest", manifest)["sources"] == {}   # records are not classified
    terms = run("trends", "terms", "--manifest", manifest, "--source", "src-key")
    assert terms["items"] == {"current": 4, "previous": 4}
    assert "slingshot 11" in {t["term"] for t in json.loads((ws / "terms_src-key.json").read_text())["terms"]}
    write(ws / "topics.json", {"topics": [
        {"id": "nvidia-hopper", "name": "NVIDIA Hopper", "kind": "platform", "aliases": ["H100", "H200"],
         "foundation": None, "vendor": "NVIDIA", "qualified": "NVIDIA Hopper"},
        {"id": "amd-instinct", "name": "AMD Instinct", "kind": "platform", "aliases": ["AMD Instinct"],
         "foundation": None, "vendor": "AMD", "qualified": "AMD Instinct"}]})
    r = run("trends", "topics-check", "--manifest", manifest)
    assert r["ok"] and r["unmatched_records"] == {"src-key": 1}   # GH200 is no alias yet
    assert "src-key: 1 of 4, e.g. Eviden BullSequana, Grace 72C, NVIDIA GH200" in (ws / "topics.md").read_text()
    assert run("trends", "attention", "--manifest", manifest)["ok"]
    att = json.loads((ws / "attention.json").read_text())["topics"]
    hopper = att["nvidia-hopper"]["adoption"]["src-key"]
    assert hopper["current"] == 2 and hopper["previous"] == 1 and hopper["delta_pp"] == 25.0
    assert hopper["direction"] == "flat"   # 2 of 4 against 1 of 4: the interval still includes no change
    assert adoption_cell(hopper, short=False) == "Top list 50.0% of systems (+25.0 pp, flat)"
    assert att["amd-instinct"]["adoption"]["src-key"]["percent_previous"] == 50.0
    assert "50.0% (+25.0 pp) →" in (ws / "attention.md").read_text()


def test_forum_records_counted_by_date(tmp_path):
    """A forum's records count in the window their date falls in, whichever edition's pages list them."""
    from sglib.attention import COUNTERS
    from sglib.trends import _manifest
    posts = [("p1", "2025-10-02", "Slurm accounting with MariaDB"), ("p2", "2025-10-20", "Slurm on Kubernetes nodes"),
             ("p3", "2026-03-01", "MPI over Slingshot fabric"), ("p4", "2024-09-30", "Old Slurm question here")]
    page = "October 2025 archive. " + " ".join(t for _, _, t in posts) + " Archive page of the list." * 8
    rec = lambda ps: [{"id": i, "title": t, "date": d} for i, d, t in ps]
    manifest, ws = _records_project(
        tmp_path, {"role": "forum", "quota": 1}, {"type": "records"},
        {"current": (page, rec(posts[1:3])), "previous": (page, rec([posts[0], posts[1], posts[3]]))},
        {"current": 2, "previous": 3})
    r = run("trends", "items-check", "--manifest", manifest)
    assert r["ok"]
    summary = json.loads((ws / "items_summary.json").read_text())["sources"][0]
    assert summary["previous_outside_window"] == 2   # p2 belongs to the current window, p4 to neither
    topics = [{"id": "slurm", "name": "Slurm", "qualified": "Slurm Workload Manager", "aliases": ["Slurm"],
               "kind": "tool"}]
    cfg = _manifest(manifest)
    n, k = COUNTERS["records"](cfg, "src-key", {"type": "records"}, topics)
    assert n == {"current": 2, "previous": 1} and k["slurm"] == {"current": 1, "previous": 1}
    n, k = COUNTERS["records"](cfg, "src-key", {"type": "records", "match": "qualified"}, topics)
    assert k["slurm"] == {"current": 0, "previous": 0}
    doc = json.loads((ws / "items" / "src-key.json").read_text())
    doc["editions"]["current"]["items"][0]["date"] = None
    write(ws / "items" / "src-key.json", doc)
    r = run("trends", "items-check", "--manifest", manifest)
    assert not r["ok"] and "1 records without a YYYY-MM-DD date" in r["problems"][0]


def test_top500_classification():
    """Parts are classified by what they name; accelerators by model, processors and interconnects by family."""
    from sglib.top500 import classify
    c = classify("HPE Cray EX255a, AMD 4th Gen EPYC 24C 1.8GHz, AMD Instinct MI300A, Slingshot-11, TOSS")
    assert c["processor"] == {"AMD EPYC"} and c["accelerator"] == {"AMD Instinct MI300A"}
    assert c["interconnect"] == {"Slingshot"} and not c["unknown"]
    c = classify("Peano B200, Xeon 6710E 64C 2.4GHz/Xeon 6960P 72C 2.7GHz, "
                 "NVIDIA H200 SXM5 141 GB/NVIDIA B200 SXM 180 GB, Infiniband NDR400, Ubuntu 24.04.4")
    assert c["processor"] == {"Intel Xeon"} and c["accelerator"] == {"NVIDIA H200", "NVIDIA B200"}
    c = classify("SGI ICE X, Xeon E5-2699v3/E5-2697 v3, Infiniband FDR, NVIDIA Tesla K40, Intel Xeon Phi 7120P")
    assert c["accelerator"] == {"NVIDIA K40", "Intel Xeon Phi"} and c["interconnect"] == {"InfiniBand"}
    c = classify("PowerEdge R740, Xeon 8358/6148/6248, NVIDIA Tesla A100 80G/40G, InfiniBand HDR100")
    assert c["processor"] == {"Intel Xeon"} and c["accelerator"] == {"NVIDIA A100"}
    c = classify("Supermicro AS-4124GQ-TNMI, AMD EPYC 7713 64C 3.7GHz, AMD Instinct MI250X, Ethernet, 4x 200Gb/s, "
                 "Rocky Linux 8.9")
    assert c["interconnect"] == {"Ethernet"} and not c["unknown"]
    c = classify("InfiniBand XDR (800 Gb/s, 4X) box, NVIDIA Grace 72C 3.1GHz, NVIDIA GB200 Superchip, "
                 "InfiniBand XDR (800 Gb/s, 4X), Rocky Linux 9.8")
    assert c["processor"] == {"NVIDIA Grace"} and c["accelerator"] == {"NVIDIA GB200"}
    c = classify("Sunway MPP, Sunway SW26010 260C 1.45GHz, Sunway")   # interconnect taken from its position
    assert c["processor"] == {"Sunway"} and c["interconnect"] == {"Sunway network"}
    c = classify("LingKun, LX2 304C 1.55GHz, LingQi, Kylin OS")
    assert c["processor"] == {"LX2"} and c["interconnect"] == {"LingQi"} and len(c["unmapped"]) == 2


def _list_page(systems: list[tuple[int, str]]) -> str:
    rows = "".join(f'<tr>\n<td>{rank}</td>\n<td>\n<a href="/system/{1000 + rank}">\n<b>S{rank}</b> - {desc},\n'
                   f'</a> Vendor<br/></td><td>1</td></tr>' for rank, desc in systems)
    return f'<table class="table">{rows}</table>'


def test_top500_collect_and_recount(tmp_path):
    """The collector counts systems per answer in the stored list pages; survey-check recounts them."""
    root = tmp_path / "t"
    gpu, cpu = "Cray EX, AMD EPYC 9654 96C 2.4GHz, NVIDIA H100 SXM5 80GB, Slingshot-11", \
        "ThinkSystem, Xeon Platinum 8480+ 56C 2GHz, Infiniband NDR"
    pages = {"c1": [(1, gpu), (2, cpu)], "c2": [(3, gpu), (4, gpu)],
             "p1": [(1, cpu), (2, cpu)], "p2": [(3, gpu), (4, "Cray EX, AMD EPYC 7763 64C 2.45GHz, "
                                                          "NVIDIA B200 SXM 180GB, Slingshot-11")]}
    for pid, systems in pages.items():
        write(root / "sources" / "raw" / f"{pid}.html", _list_page(systems))
    verified = {"collector": {"type": "top500_list"},
                "current": {"fetched": "c1", "period": "2026-06", "more_pages": [{"fetched": "c2"}]},
                "previous": {"fetched": "p1", "period": "2025-06", "more_pages": [{"fetched": "p2"}]}}
    write(root / "trends" / "sources_panel.json", {"sources": [{"key": "top500", "family": "adoption",
                                                                "verified": verified, "selected": True}]})
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "f", "scope": "s", "windows": {"current": ["2025-10-09", "2026-10-09"],
                                                "previous": ["2024-10-09", "2025-10-08"]},
        "routes": {"lists": "x"}, "families": {"talks": {"role": "items", "quota": 1}}, "anchors": [{"name": "x"}],
        "collectors": {"top500": {"type": "top500_list", "systems_per_page": 2}}}))
    r = run("trends", "collect", "--manifest", manifest, "--source", "top500")
    assert r["ok"] and r["collected"]["current"]["systems"] == 4
    table = json.loads((root / "trends" / "queries" / "top500.json").read_text())
    cur = {x["name"]: x for x in table["editions"]["current"]["rows"]}
    prev = {x["name"]: x for x in table["editions"]["previous"]["rows"]}
    assert cur["NVIDIA H100"] == {"name": "NVIDIA H100", "percent": 75.0, "count": 3}
    assert cur["Systems with accelerators"]["count"] == 3 and cur["Intel Xeon"]["count"] == 1
    assert prev["NVIDIA B200"]["count"] == 1 and cur["NVIDIA B200"]["count"] == 0   # a list counts every system
    assert run("trends", "survey-check", "--manifest", manifest, "--source", "top500")["ok"]
    cur["NVIDIA H100"]["count"] = 2
    table["editions"]["current"]["rows"] = list(cur.values())
    write(root / "trends" / "queries" / "top500.json", table)
    r = run("trends", "survey-check", "--manifest", manifest, "--source", "top500")
    assert not r["ok"] and "1 answers differ from a recount" in r["problems"][0]
    write(root / "sources" / "raw" / "c2.html", _list_page([(3, gpu)]))
    r = run("trends", "collect", "--manifest", manifest, "--source", "top500")
    r = run("trends", "survey-check", "--manifest", manifest, "--source", "top500")
    assert not r["ok"] and any("pages without 2 systems" in p for p in r["problems"])
