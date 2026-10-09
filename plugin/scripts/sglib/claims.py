"""Claim bookkeeping: merge extraction parts, select research batches, summarize verdicts."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .util import SgError, excluded_slides, load_json, load_manifest, manifest_deck, write_json

SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, None: 3}


def _deck_cfg(args, deck_id: str) -> dict | None:
    return manifest_deck(load_manifest(args.manifest), deck_id) if getattr(args, "manifest", None) else None


def merge(args) -> dict:
    """claims/extract_*.json -> claims.json, with unique ids and valid slide references."""
    ws = Path(args.workspace).resolve()
    slides_doc = load_json(ws / "slides.json")
    by_index = {s["index"]: s for s in slides_doc["slides"]}
    files = sorted((ws / "claims").glob("extract_*.json"))
    if not files:
        raise SgError(f"no extraction files in {ws / 'claims'}")
    claims, seen, deck_ids, problems = [], {}, set(), []
    for path in files:
        doc = load_json(path, "extract")
        deck_ids.add(doc["deck"])
        lo, hi = doc["slides"]
        for c in doc["claims"]:
            prefix = f"claim:{doc['deck']}:{doc['part']}-"
            if not c["id"].startswith(prefix):
                problems.append(f"{path.name}: {c['id']} must start with {prefix}")
            if c["id"] in seen:
                problems.append(f"{path.name}: duplicate id {c['id']} (also in {seen[c['id']]})")
            seen[c["id"]] = path.name
            if c["slide"] not in by_index:
                problems.append(f"{path.name}: {c['id']} cites slide {c['slide']}, which does not exist")
            elif not lo <= c["slide"] <= hi:
                problems.append(f"{path.name}: {c['id']} cites slide {c['slide']} outside the part's range {lo}-{hi}")
            claims.append({**c, "part_file": path.name})
    if len(deck_ids) != 1:
        problems.append(f"extraction files name several decks: {sorted(deck_ids)}")
    if problems:
        raise SgError("; ".join(problems[:10]))
    deck_id = deck_ids.pop()
    excluded = excluded_slides(slides_doc, _deck_cfg(args, deck_id))
    dropped = [c["id"] for c in claims if c["slide"] in excluded]
    claims = [c for c in claims if c["slide"] not in excluded]
    claims.sort(key=lambda c: (c["slide"], c["id"]))
    write_json(ws / "claims.json", {"deck": deck_id, "generated_by": "sg claims merge", "claims": claims})
    kinds = Counter(k for c in claims for k in c["kind"])
    return {"ok": True, "out": str(ws / "claims.json"), "claims": len(claims),
            "dropped_excluded_slides": dropped, "kinds": dict(kinds),
            "from_image": sum(c["from_image"] for c in claims)}


def select(args) -> dict:
    """Write research/batches.json: claims grouped by slide order into batches.

    Assumed values of worked examples are listed but not checked. Arithmetic on slide values goes to
    separate batches (research false) that the fact-checker recomputes without sources.
    """
    ws = Path(args.workspace).resolve()
    doc = load_json(ws / "claims.json")
    size = args.batch_size
    claims = doc["claims"]
    assumptions = [c for c in claims if "assumption" in c["kind"] and "arithmetic" not in c["kind"]]
    arithmetic = [c for c in claims if "arithmetic" in c["kind"]]
    research = [c for c in claims if not {"assumption", "arithmetic"} & set(c["kind"])]
    batches = []
    for start in range(0, len(research), size):
        batches.append({
            "batch": f"b{len(batches) + 1:02d}", "research": True,
            "claims": [{"claim_id": c["id"], "slide": c["slide"],
                        "search_for_change": bool({"named", "numeric"} & set(c["kind"]))}
                       for c in research[start:start + size]]})
    calc_size = 2 * size   # recomputing is quick, so arithmetic batches can be larger
    for k, start in enumerate(range(0, len(arithmetic), calc_size), 1):
        batches.append({"batch": f"c{k:02d}", "research": False,
                        "claims": [{"claim_id": c["id"], "slide": c["slide"], "search_for_change": False}
                                   for c in arithmetic[start:start + calc_size]]})
    write_json(ws / "research" / "batches.json",
               {"deck": doc["deck"], "batches": batches,
                "assumptions": [{"claim_id": c["id"], "slide": c["slide"]} for c in assumptions]})
    return {"ok": True, "out": str(ws / "research" / "batches.json"),
            "batches": sum(b["research"] for b in batches),
            "arithmetic_batches": sum(not b["research"] for b in batches),
            "claims": len(claims), "researched": len(research), "arithmetic": len(arithmetic),
            "assumptions_not_checked": len(assumptions),
            "search_for_change": sum(c["search_for_change"] for b in batches for c in b["claims"])}


def _majority(verdicts: list[dict]) -> dict:
    """Majority of (verdict, severity); ties go to the lower severity."""
    counts = Counter((v["verdict"], v["severity"]) for v in verdicts)
    best = max(counts.items(), key=lambda kv: (kv[1], SEVERITY_ORDER[kv[0][1]]))[0]
    chosen = next(v for v in verdicts if (v["verdict"], v["severity"]) == best)
    return {**chosen, "second_checked": True,
            "votes": [f"{v['verdict']}/{v['severity']}" for v in verdicts]}


def summary(args) -> dict:
    """Merge checks/*.json into claim_check.json and compute every count a report states."""
    ws = Path(args.workspace).resolve()
    claims = {c["id"]: c for c in load_json(ws / "claims.json")["claims"]}
    batch_doc = load_json(ws / "research" / "batches.json")
    batches = batch_doc["batches"]
    assigned = {c["claim_id"]: b["batch"] for b in batches for c in b["claims"]}
    assumed = {a["claim_id"] for a in batch_doc.get("assumptions", [])}
    unplaced = sorted(set(claims) - set(assigned) - assumed)
    if unplaced:
        raise SgError(f"{len(unplaced)} claims are in no batch; re-run `sg claims select`: {unplaced[:8]}")
    quotes = load_json(ws / "quotes.json")["results"] if (ws / "quotes.json").exists() else []

    primary: dict[str, dict] = {}
    second: dict[str, list[dict]] = {}
    for path in sorted((ws / "checks").glob("*.json")):
        doc = load_json(path, "check")
        for v in doc["verdicts"]:
            if v["claim_id"] not in claims:
                raise SgError(f"{path.name}: verdict for unknown claim {v['claim_id']}")
            v = {**v, "batch": doc["batch"]}  # source indices refer to research batch doc["batch"]
            if doc.get("second_check"):
                second.setdefault(v["claim_id"], []).append(v)
            elif v["claim_id"] in primary:
                raise SgError(f"{path.name}: second primary verdict for {v['claim_id']}")
            else:
                primary[v["claim_id"]] = {**v, "check_file": path.name}

    missing = sorted(set(assigned) - set(primary))
    if missing:
        by_batch = Counter(assigned[m] for m in missing)
        raise SgError(f"{len(missing)} claims have no verdict; re-run the fact-checker for batches "
                      f"{dict(by_batch)}: {missing[:8]}")

    final, needs_second = {}, []
    for cid, v in primary.items():
        if v["severity"] == "CRITICAL" and len(second.get(cid, [])) < 2:
            needs_second.append(cid)
        final[cid] = _majority([v] + second[cid][:2]) if len(second.get(cid, [])) >= 2 else v

    quote_status = Counter()
    for q in quotes:
        quote_status[q["status"]] += 1
    unmatched_claims = sorted({q["claim_id"] for q in quotes if q["status"] == "not_found"})

    rows = []
    for cid, c in claims.items():
        if cid in assumed:
            continue
        v = final[cid]
        rows.append({"claim_id": cid, "slide": c["slide"], "slide_title": c.get("slide_title"),
                     "text": c["text"], "statement": c["statement"], "kind": c["kind"],
                     "verdict": v["verdict"], "severity": v["severity"], "fix_kind": v["fix_kind"],
                     "outdated": v.get("outdated"), "issue": v["issue"],
                     "suggested_fix": v["suggested_fix"], "sources_used": v["sources_used"],
                     "batch": v["batch"],
                     "second_checked": v.get("second_checked", False), "votes": v.get("votes"),
                     "quote_not_found": cid in unmatched_claims})
    rows.sort(key=lambda r: (r["slide"], r["claim_id"]))
    by_verdict = Counter(r["verdict"] for r in rows)
    by_severity = Counter(f"{r['verdict']}/{r['severity']}" for r in rows if r["severity"])
    outdated_labels = Counter(r["outdated"]["label"] for r in rows if r["outdated"])
    result = {"deck": load_json(ws / "claims.json")["deck"], "generated_by": "sg claims summary",
              "counts": {"claims": len(rows), "by_verdict": dict(by_verdict),
                         "by_verdict_severity": dict(by_severity),
                         "outdated_labels": dict(outdated_labels),
                         "quotes": dict(quote_status),
                         "claims_with_unmatched_quote": len(unmatched_claims),
                         "assumptions_not_checked": len(assumed)},
              "needs_second_check": needs_second, "claims": rows,
              "assumptions": [{"claim_id": cid, "slide": claims[cid]["slide"], "text": claims[cid]["text"]}
                              for cid in sorted(assumed, key=lambda x: (claims[x]["slide"], x))]}
    write_json(ws / "claim_check.json", result)
    return {"ok": not needs_second, "out": str(ws / "claim_check.json"), **result["counts"],
            "needs_second_check": needs_second}
