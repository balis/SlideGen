"""Tests for stage 0 of field trends: merging nominations and selecting the source panel."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sg import run, write  # noqa: E402

# Data Summit Alpha 2026 also lists a talk by URL slug, which must match the anchor "Apache Flink".
LIST_PAGE = ("Top data conferences: Data Summit Alpha, Beta Data Days, the Gamma Vendor Conference, "
             "Delta Vendor Forum and Iceberg Summit." * 5)
ALPHA_2026 = "Data Summit Alpha 2026 programme. Talks: Apache Iceberg at scale; data contracts in practice." * 5
ALPHA_2026_P2 = ("Data Summit Alpha 2026 industry track: /session/streaming-with-apache-flink-at-acme "
                 "/session/Data%20Quality%20at%20Acme") * 3
ALPHA_2025 = "Data Summit Alpha 2025 programme. Talks: Kafka streams; Spark tuning." * 5
BETA_2026 = "Beta Data Days 2026 agenda. Sessions on DuckDB and dbt." * 5
BETA_2023 = "Beta Data Days 2023 agenda. Sessions on Hadoop." * 5


def test_source_panel(tmp_path):
    root = tmp_path / "trends-de"
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "data engineering", "scope": "s",
        "windows": {"current": ["2025-10-08", "2026-10-08"], "previous": ["2024-10-08", "2025-10-08"]}, "routes": {"lists": "x"},
        "families": {"practitioner_talks": {"role": "items", "quota": 1, "min_items": 2, "vendor": False},
                     "vendor_talks": {"role": "items", "quota": 1, "min_items": 2, "vendor": True}},
        "same_source": {"data-summit-alpha": ["alpha-summit"]},
        "anchors": [{"name": "Apache Iceberg", "aliases": ["iceberg"]}, {"name": "Apache Flink", "aliases": ["flink"]},
                    {"name": "Apache Hudi"}, {"name": "data quality"}]}))
    store = root / "sources"
    ids = {}
    for name, text in (("list.txt", LIST_PAGE), ("a26.txt", ALPHA_2026), ("a26p2.txt", ALPHA_2026_P2), ("a25.txt", ALPHA_2025),
                       ("b26.txt", BETA_2026), ("b23.txt", BETA_2023)):
        ids[name] = run("fetch", "--file", write(tmp_path / name, text), "--store", store)["fetched"]
    ws = root / "trends" / "sources"
    ev = lambda q: {"url": "file:list.txt", "fetched": ids["list.txt"], "quote": q}
    cand = lambda name, fam, org, vendor, quote, single=False: {
        "name": name, "family": fam, "homepage": f"https://{org}.example", "organiser": org, "vendor": vendor,
        "single_technology": single, "evidence": ev(quote)}
    write(ws / "candidates_lists.json", {"route": "curated-lists", "searched": ["x"], "candidates": [
        cand("Data Summit Alpha", "practitioner_talks", "alpha", False, "Data Summit Alpha"),
        cand("Beta Data Days", "practitioner_talks", "beta", False, "Beta Data Days"),
        cand("Gamma Vendor Conference", "vendor_talks", "gamma", True, "the Gamma Vendor Conference"),
        cand("Delta Vendor Forum", "practitioner_talks", "delta", True, "Delta Vendor Forum"),
        cand("Iceberg Summit", "practitioner_talks", "asf", False, "Iceberg Summit", single=True),
        cand("Made Up Con", "practitioner_talks", "madeup", False, "Made Up Con is the best")]})
    write(ws / "candidates_search.json", {"route": "web-search", "searched": ["y"], "candidates": [
        {**cand("Data Summit Alpha", "practitioner_talks", "alpha", False, "Data Summit Alpha"), "key": "alpha-summit"}]})
    r = run("trends", "sources-merge", "--manifest", manifest)
    assert r["ok"] and r["candidates"] == 5 and r["rejected"] == 1, r   # the made-up quote is rejected
    merged = {c["key"]: c for c in json.loads((root / "trends" / "source_candidates.json").read_text())["candidates"]}
    assert merged["data-summit-alpha"]["nominations"] == 2
    assert merged["beta-data-days"]["verify"] and merged["iceberg-summit"]["verify"]
    assert not merged["delta-vendor-forum"]["verify"]      # a vendor event cannot be an independent source

    edition = lambda fid, period, items, quote: {"url": "file:x", "fetched": ids[fid], "period": period,
                                                  "items": items, "items_quote": quote}
    write(ws / "verified_v1.json", {"batch": "v1", "sources": [
        {"key": "data-summit-alpha", "api": False, "scope_fit": 0.9, "scope_note": "all talks", "access_note": "html",
         "current": {**edition("a26.txt", "2026-04", 30, "Data Summit Alpha 2026 programme"),
                     "more_pages": [{"url": "file:a26p2.txt", "fetched": ids["a26p2.txt"]}]},
         "previous": edition("a25.txt", "2025-03", 28, "Data Summit Alpha 2025 programme")},
        {"key": "beta-data-days", "api": False, "scope_fit": 0.8, "scope_note": "sample", "access_note": "html",
         "current": edition("b26.txt", "2026-05", 20, "Beta Data Days 2026 agenda"),
         "previous": edition("b23.txt", "2023-05", 20, "Beta Data Days 2023 agenda")}]})
    r = run("trends", "sources-check", "--manifest", manifest)
    panel = json.loads((root / "trends" / "sources_panel.json").read_text())
    rows = {s["key"]: s for s in panel["sources"]}
    assert panel["selected"] == ["data-summit-alpha"]
    assert any("outside" in x for x in rows["beta-data-days"]["reasons"])        # 2023 is not the previous window
    assert rows["gamma-vendor-conference"]["reasons"] == ["not verified"]
    assert "run by a vendor" in rows["delta-vendor-forum"]["reasons"][0]
    assert rows["iceberg-summit"]["reasons"] == ["not verified"]   # single-technology events may be verified
    assert not r["ok"] and r["short_families"] == {"vendor_talks": "0/1"} and r["blind_anchors"] == ["Apache Hudi"]
    assert sorted(r["not_verified"]) == ["gamma-vendor-conference", "iceberg-summit"]
    md = (root / "trends" / "sources_panel.md").read_text()
    assert "blind spot" in md and "Delta Vendor Forum (run by a vendor" in md


def test_window_midpoint():
    from sglib.trends import _window_ok
    current, previous = ["2025-10-08", "2026-10-08"], ["2024-10-08", "2025-10-08"]
    assert _window_ok("2026-06", current) and not _window_ok("2025-06", current) and _window_ok("2025-06", previous)
    assert _window_ok("2025-10..2026-09", current) and not _window_ok("2024-01..2025-06", current)
    assert not _window_ok("2026-10", current) and _window_ok("2026-10-07", current)   # day precision at the edge
    assert _window_ok("2025-10-06..2025-10-08", previous) and not _window_ok("2025-10-08..2025-10-12", previous)


def test_author_overrides(tmp_path):
    """The author can exclude a selected source and force in an unverified one."""
    test_source_panel(tmp_path)
    root = tmp_path / "trends-de"
    cfg = yaml.safe_load((root / "trends.yaml").read_text())
    cfg.update(exclude={"data-summit-alpha": "too US-centric"}, include=["gamma-vendor-conference"])
    manifest = write(root / "trends.yaml", yaml.safe_dump(cfg))
    run("trends", "sources-check", "--manifest", manifest)
    panel = json.loads((root / "trends" / "sources_panel.json").read_text())
    assert panel["selected"] == ["gamma-vendor-conference"]
    assert "included in the manifest" in (root / "trends" / "sources_panel.md").read_text()


def test_fetch_json(tmp_path):
    """API responses are stored as decoded JSON text, so quotes in them can be matched."""
    hits = [{"title": f"Ask HN: Which data conferences are worth attending in 2026? ({i})"} for i in range(20)]
    r = run("fetch", "--file", write(tmp_path / "hn.json", {"hits": hits}), "--store", tmp_path / "store")
    assert r["kind"] == "json"
    assert "worth attending in 2026" in (tmp_path / "store" / r["text_file"]).read_text()


def test_possible_duplicates(tmp_path):
    """Two keys with the same home page host in one family are reported as possible duplicates."""
    root = tmp_path / "t"
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "data engineering", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                 "previous": ["2024-10-08", "2025-10-08"]}, "routes": {"lists": "x"},
        "families": {"practitioner_talks": {"role": "items", "quota": 1}}, "anchors": [{"name": "x"}]}))
    fid = run("fetch", "--file", write(tmp_path / "l.txt", LIST_PAGE), "--store", root / "sources")["fetched"]
    ev = {"url": "file:l.txt", "fetched": fid, "quote": "Beta Data Days"}
    c = {"family": "practitioner_talks", "organiser": "beta", "vendor": False, "single_technology": False, "evidence": ev}
    write(root / "trends" / "sources" / "candidates_a.json", {"route": "a", "searched": [], "candidates": [
        {**c, "name": "Beta Data Days", "homepage": "https://www.beta.example/2026"},
        {**c, "name": "Beta Days", "homepage": "https://beta.example"}]})
    r = run("trends", "sources-merge", "--manifest", manifest)
    assert r["possible_duplicates"] == [["beta-data-days", "beta-days"]]



def test_fit_interval_and_round_robin():
    from sglib.trends import _fit_interval, _round_robin
    lo, hi = _fit_interval({"scope_fit": 0.4})               # 20 sampled items: wide
    assert 0.2 < lo < 0.25 and 0.6 < hi < 0.65
    lo, hi = _fit_interval({"scope_fit": 0.4, "scope_sample": 200})
    assert 0.33 < lo and hi < 0.47
    row = lambda key, kind, items, routes=1, borderline=(): {
        "key": key, "kind": kind, "nominations": routes, "borderline": list(borderline),
        "verified": {"current": {"items": items}, "scope_fit": 1.0}}
    pool = [row("roundup-a", "link", 700), row("roundup-b", "link", 300, routes=3), row("blog", "post", 60),
            row("podcast", "episode", 24, routes=3), row("big-but-unsure", "post", 90, borderline=["x"])]
    order = [r["key"] for r in _round_robin(pool)]
    # one of each kind first (largest first), certain sources before borderline ones
    assert order == ["roundup-a", "blog", "podcast", "roundup-b", "big-but-unsure"]


def test_borderline_not_collectable_and_own_topics(tmp_path):
    root = tmp_path / "t"
    store = root / "sources"
    page = lambda name, text: run("fetch", "--file", write(tmp_path / name, text * 12), "--store", store)["fetched"]
    lst = page("l.txt", "Conferences: Mixed Data Days, Vendor Summit, Locked Summit. ")
    m26, m25 = page("m26.txt", "Mixed Data Days 2026 talks: Apache Iceberg. "), page("m25.txt", "Mixed Data Days 2025 talks. ")
    v26, v25 = page("v26.txt", "Vendor Summit 2026 sessions: Lakehouse. "), page("v25.txt", "Vendor Summit 2025 sessions. ")
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "data engineering", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                 "previous": ["2024-10-08", "2025-10-07"]}, "routes": {"lists": "x"},
        "families": {"practitioner_talks": {"role": "items", "quota": 1, "min_items": 20, "vendor": False},
                     "vendor_talks": {"role": "items", "quota": 2, "min_items": 20, "vendor": True}},
        "anchors": [{"name": "Apache Iceberg"}]}))
    ev = lambda q: {"url": "file:l.txt", "fetched": lst, "quote": q}
    c = lambda name, fam, vendor: {"name": name, "family": fam, "homepage": f"https://{name[:4].lower()}.example",
                                   "organiser": name, "vendor": vendor, "single_technology": False, "evidence": ev(name)}
    write(root / "trends" / "sources" / "candidates_a.json", {"route": "a", "searched": [], "candidates": [
        c("Mixed Data Days", "practitioner_talks", False), c("Vendor Summit", "vendor_talks", True),
        c("Locked Summit", "vendor_talks", True)]})
    run("trends", "sources-merge", "--manifest", manifest)
    ed = lambda fid, period, items, q: {"url": "file:x", "fetched": fid, "period": period, "items": items, "items_quote": q}
    write(root / "trends" / "sources" / "verified_a.json", {"batch": "a", "sources": [
        {"key": "mixed-data-days", "api": False, "scope_fit": 0.4, "scope_note": "8 of 20", "access_note": "",
         "current": ed(m26, "2026-04-01", 55, "Mixed Data Days 2026"), "previous": ed(m25, "2025-04-01", 60, "Mixed Data Days 2025")},
        {"key": "vendor-summit", "api": False, "scope_fit": 0.9, "scope_note": "", "access_note": "",
         "current": ed(v26, "2026-06-01", 300, "Vendor Summit 2026"), "previous": ed(v25, "2025-06-01", 280, "Vendor Summit 2025")},
        {"key": "locked-summit", "api": False, "scope_fit": None, "scope_note": "", "access_note": "",
         "not_collectable": "catalog is a single-page app", "current": None, "previous": None}]})
    r = run("trends", "sources-check", "--manifest", manifest)
    rows = {x["key"]: x for x in json.loads((root / "trends" / "sources_panel.json").read_text())["sources"]}
    assert r["pending"] == {"practitioner_talks": {"places": 1, "candidates": ["mixed-data-days"]}}  # 55 x [0.22, 0.61]
    assert "practitioner_talks" not in r["short_families"]
    assert rows["locked-summit"]["reasons"] == ["item lists exist but could not be collected: catalog is a single-page app"]
    assert r["missing_own_topics"] == ["vendor-summit"] and not r["ok"]
    cfg = yaml.safe_load(manifest.read_text())
    cfg["own_topics"] = {"vendor-summit": ["VendorDB"]}
    write(manifest, yaml.safe_dump(cfg))
    r = run("trends", "sources-check", "--manifest", manifest)
    assert r["missing_own_topics"] == [] and r["short_families"] == {"vendor_talks": "1/2"}
    md = (root / "trends" / "sources_panel.md").read_text()
    assert "pending classification" in md and "Own topics, not counted from that source: Vendor Summit (VendorDB)" in md


def test_discovery_check(tmp_path):
    root = tmp_path / "t"
    store = root / "sources"
    post = run("fetch", "--file", write(tmp_path / "b.txt", "Engineering blog. 2026-03-02 How we moved our lake to Iceberg. " * 5),
               "--store", store)["fetched"]
    manifest = write(root / "trends.yaml", yaml.safe_dump({
        "field": "data engineering", "scope": "s", "windows": {"current": ["2025-10-08", "2026-10-08"],
                                                 "previous": ["2024-10-08", "2025-10-07"]}, "routes": {"lists": "x"},
        "families": {"practitioner_talks": {"role": "items", "quota": 1}}, "anchors": [{"name": "x"}],
        "discovery": {"engineering_blog": {"min": 2, "min_non_tech": 1}}}))
    blog = lambda key, date, tech, quote: {
        "key": key, "name": key, "kind": "engineering_blog", "dimensions": ["production_use"], "organiser": key,
        "vendor": False, "tech_company": tech, "sector": "retail" if not tech else "internet", "org_size": "large",
        "access": "feed", "latest": {"url": "file:b.txt", "fetched": post, "date": date, "quote": quote}}
    write(root / "trends" / "discovery" / "blogs.json", {"group": "blogs", "searched": [], "sources": [
        blog("shop-tech", "2026-03-02", False, "How we moved our lake to Iceberg"),
        blog("old-blog", "2024-05-01", True, "How we moved our lake to Iceberg"),
        blog("made-up", "2026-03-02", True, "We love Hadoop"),
        {**blog("shop-tech-2", "2026-03-02", False, "How we moved our lake to Iceberg"), "organiser": "Shop-Tech"}]})
    r = run("trends", "discovery-check", "--manifest", manifest)
    assert r["active"] == 2 and set(r["inactive"]) == {"old-blog", "made-up"}   # shop-tech-2: same organization
    assert r["short"] == {"engineering_blog": "1/2"} and not r["ok"]
    assert "outside the current window" in (root / "trends" / "discovery_collection.md").read_text()



def test_batch_order():
    from sglib.trends import _natural
    names = ["verified_v10.json", "verified_v2.json", "verified_v1.json", "verified_r1.json"]
    assert sorted(map(Path, names), key=_natural) == list(map(Path, [
        "verified_r1.json", "verified_v1.json", "verified_v2.json", "verified_v10.json"]))
