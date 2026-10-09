"""Course-level developments: validate survey clusters, merge findings, compute priorities.

Layout under the manifest's directory:
  course/clusters.json             survey clusters (written by the orchestrator)
  course/findings/cluster_C*.json  developments-researcher output, one per cluster
  course/findings/review_C*.json   findings-reviewer output, one per cluster
  course/findings.json             merged result (written here)
  <deck id>/workspace/             per-deck files (topic_map.json, claim_check.json)
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .util import SgError, load_json, load_manifest, write_json

MATURITY_RANK = {"announced": 0, "preview": 1, "ga": 2, "widely_adopted": 3}
BLOCKING = {"CRITICAL", "MAJOR"}


def _paths(manifest_path: str):
    manifest = load_manifest(manifest_path)
    root = Path(manifest_path).resolve().parent
    return manifest, root / "course", {d["id"]: root / d["id"] / "workspace" for d in manifest["decks"]}


def _topic_sections(workspaces: dict[str, Path]) -> dict[tuple[str, str], dict]:
    out = {}
    for deck, ws in workspaces.items():
        for s in load_json(ws / "topic_map.json", "topic_map")["sections"]:
            out[(deck, s["id"])] = s
    return out


def clusters(args) -> dict:
    """Check that clusters.json covers every topic-map section exactly once."""
    _, course, workspaces = _paths(args.manifest)
    doc = load_json(course / "clusters.json", "clusters")
    sections = _topic_sections(workspaces)
    seen: dict[tuple[str, str], str] = {}
    problems = []
    for c in doc["clusters"]:
        for ref in c["sections"]:
            key = (ref["deck"], ref["section"])
            if key not in sections:
                problems.append(f"{c['id']} names unknown section {key[0]}/{key[1]}")
            elif key in seen:
                problems.append(f"section {key[0]}/{key[1]} is in both {seen[key]} and {c['id']}")
            seen[key] = c["id"]
    uncovered = [f"{d}/{s}" for (d, s) in sections if (d, s) not in seen]
    if uncovered:
        problems.append(f"sections in no cluster: {uncovered}")
    if problems:
        raise SgError("; ".join(problems))
    return {"ok": True, "clusters": len(doc["clusters"]), "sections": len(sections)}


def _priority(f: dict, blocking_claims: set[str]) -> tuple[str, str]:
    """Priority from recorded criteria; returns (priority, reason)."""
    rank = MATURITY_RANK[f["maturity"]]
    # Only independent sources show that the field teaches something; vendor pages do not.
    signals = sum(not s.get("vendor", False) for s in f["teaching_signals"])
    invalidates_blocking = sorted(set(f["invalidates"]) & blocking_claims)
    if invalidates_blocking:
        prio, why = "MUST", f"makes claims outdated: {', '.join(invalidates_blocking)}"
    elif f["objectives"] and rank >= MATURITY_RANK["ga"] and signals >= 2:
        prio, why = "MUST", f"affects objectives, {f['maturity']}, {signals} independent teaching signals"
    elif (f["objectives"] and rank >= MATURITY_RANK["preview"]) or signals >= 1:
        prio, why = "SHOULD", (f"affects objectives, {f['maturity']}" if f["objectives"]
                               else f"{signals} independent teaching signal(s)")
    else:
        prio, why = "OPTIONAL", "no objective affected and no independent teaching signal"
    cap = {"announced": "OPTIONAL", "preview": "SHOULD"}.get(f["maturity"])
    order = ["OPTIONAL", "SHOULD", "MUST"]
    if cap and order.index(prio) > order.index(cap):
        prio, why = cap, f"{why}; capped at {cap} because maturity is {f['maturity']}"
    return prio, why


def _year(value) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def merge(args) -> dict:
    manifest, course, workspaces = _paths(args.manifest)
    decks = {d["id"]: d for d in manifest["decks"]}
    sections = _topic_sections(workspaces)
    cluster_files = sorted((course / "findings").glob("cluster_*.json"))
    if not cluster_files:
        raise SgError(f"no cluster findings in {course / 'findings'}")

    # Claims with blocking OUTDATED or MISREPRESENTED verdicts, by id, from every deck.
    claim_rows = {}
    for deck, ws in workspaces.items():
        if (ws / "claim_check.json").exists():
            for row in load_json(ws / "claim_check.json")["claims"]:
                claim_rows[row["claim_id"]] = row
    blocking = {cid for cid, r in claim_rows.items()
                if r["verdict"] == "OUTDATED" and r["severity"] in BLOCKING}

    merged: dict[str, dict] = {}
    dropped, problems = [], []
    for path in cluster_files:
        doc = load_json(path, "findings")
        review_path = course / "findings" / path.name.replace("cluster_", "review_")
        reviews = {}
        if review_path.exists():
            reviews = {r["key"]: r for r in load_json(review_path, "finding_review")["reviews"]}
        elif not args.allow_unreviewed:
            raise SgError(f"{path.name} has no review file {review_path.name}; run the findings-reviewer")
        for f in doc["findings"]:
            review = reviews.get(f["key"])
            if review is None and not args.allow_unreviewed:
                problems.append(f"{review_path.name} has no review for {f['key']}")
                continue
            if review and review["decision"] == "drop":
                dropped.append({"key": f["key"], "cluster": doc["cluster"], "reason": review["reason"]})
                continue
            if review:
                f = {**f, **review["corrections"]}
                f["review"] = {"decision": review["decision"], "reason": review["reason"],
                               "already_covered": review["already_covered"]}
            for ref in f["sections"]:
                if (ref["deck"], ref["section"]) not in sections:
                    problems.append(f"{path.name}: {f['key']} maps to unknown section {ref}")
            for cid in f["invalidates"]:
                if cid not in claim_rows:
                    problems.append(f"{path.name}: {f['key']} invalidates unknown claim {cid}")
            f["clusters"] = [doc["cluster"]]
            if f["key"] in merged:  # the same development found by two clusters
                m = merged[f["key"]]
                m["clusters"] += f["clusters"]
                for field in ("sections", "teaching_signals"):
                    known = {str(x) for x in m[field]}
                    m[field] += [x for x in f[field] if str(x) not in known]
                m["objectives"] = sorted(set(m["objectives"]) | set(f["objectives"]))
                m["invalidates"] = sorted(set(m["invalidates"]) | set(f["invalidates"]))
            else:
                merged[f["key"]] = f
    if problems:
        raise SgError("; ".join(problems[:10]))

    findings, covered, no_lecture = [], [], []
    for f in merged.values():
        notes = []
        non_vendor = sum(not s["vendor"] for s in f["teaching_signals"])
        if f["maturity"] == "widely_adopted" and non_vendor < 2:
            f["maturity"] = "ga"
            notes.append("maturity lowered to ga: 'widely adopted' needs two non-vendor signals")
        f["priority"], f["priority_reason"] = _priority(f, blocking)
        f["notes"] = notes
        f["decks"] = {}
        for ref in f["sections"]:
            deck_cfg, sec = decks[ref["deck"]], sections[(ref["deck"], ref["section"])]
            reference_year = _year(deck_cfg.get("last_revised")) or _year(sec["content_date"])
            year = _year(f["date"])
            age = "undated" if year is None or reference_year is None else (
                "new" if year > reference_year else "missing")
            entry = f["decks"].setdefault(ref["deck"], {"sections": [], "slides": [], "age": age})
            entry["sections"].append(ref["section"])
            entry["slides"] = sorted(set(entry["slides"]) | set(range(sec["slides"][0], sec["slides"][1] + 1)))
        if f.get("review", {}).get("already_covered"):
            covered.append(f)
        elif not f["decks"]:
            no_lecture.append(f)
        else:
            findings.append(f)
    findings.sort(key=lambda f: (["MUST", "SHOULD", "OPTIONAL"].index(f["priority"]), f["key"]))
    counts = {"findings": len(findings), "by_priority": dict(Counter(f["priority"] for f in findings)),
              "already_covered": len(covered), "no_lecture": len(no_lecture), "dropped": len(dropped)}
    write_json(course / "findings.json", {"generated_by": "sg findings merge", "counts": counts,
                                          "findings": findings, "already_covered": covered,
                                          "no_lecture": no_lecture, "dropped": dropped})
    return {"ok": True, "out": str(course / "findings.json"), **counts}
