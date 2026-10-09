"""Claim bookkeeping: merge extraction parts, carry earlier verdicts, select research batches, summarize."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .util import SgError, excluded_slides, load_json, load_manifest, manifest_deck, write_json

SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, None: 3}
NOT_CHECKED = ("assumption", "framing")   # kinds listed for the author, never researched
MIN_CARRY_CHARS = 25                       # shorter texts (table cells, labels) match by accident


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


def carry(args) -> dict:
    """Mark claims whose slide text equals a VERIFIED claim in another deck's check (claims_carried.json).

    Used when a lecture reuses slides of a deck checked in the same revision cycle: the earlier verdict
    stands and the claim is not researched again.
    """
    from .sources import _normalize
    ws = Path(args.workspace).resolve()
    claims = load_json(ws / "claims.json")["claims"]
    verified: dict[str, str] = {}
    for other in args.sources:
        doc = load_json(Path(other).resolve() / "claim_check.json")
        for r in doc["claims"]:
            text = _normalize(r["text"])
            if r["verdict"] == "VERIFIED" and len(text) >= MIN_CARRY_CHARS:
                verified.setdefault(text, r.get("carried_from") or f"{doc['deck']}:{r['claim_id']}")
    carried = {c["id"]: verified[_normalize(c["text"])] for c in claims
               if not {*NOT_CHECKED, "arithmetic"} & set(c["kind"]) and _normalize(c["text"]) in verified}
    write_json(ws / "claims_carried.json", {"generated_by": "sg claims carry",
                                            "from": [str(Path(o).resolve()) for o in args.sources],
                                            "claims": carried})
    return {"ok": True, "out": str(ws / "claims_carried.json"), "claims": len(claims), "carried": len(carried)}


def select(args) -> dict:
    """Write research/batches.json: claims grouped by slide order into batches.

    Assumptions and framing are listed but not checked; claims carried from another deck's check keep
    that verdict. Arithmetic on slide values goes to separate batches (research false) that the
    fact-checker recomputes without sources.
    """
    ws = Path(args.workspace).resolve()
    doc = load_json(ws / "claims.json")
    size = args.batch_size
    claims = doc["claims"]
    carried_file = ws / "claims_carried.json"
    carried = load_json(carried_file)["claims"] if carried_file.exists() else {}
    not_checked = [(c, next(k for k in NOT_CHECKED if k in c["kind"])) for c in claims
                   if set(NOT_CHECKED) & set(c["kind"]) and "arithmetic" not in c["kind"]]
    skipped = {c["id"] for c, _ in not_checked}
    carried = {cid: src for cid, src in carried.items() if cid not in skipped}
    arithmetic = [c for c in claims if "arithmetic" in c["kind"]]
    research = [c for c in claims if c["id"] not in skipped and c["id"] not in carried
                and "arithmetic" not in c["kind"]]
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
    slide_of = {c["id"]: c["slide"] for c in claims}
    write_json(ws / "research" / "batches.json",
               {"deck": doc["deck"], "batches": batches,
                "not_checked": [{"claim_id": c["id"], "slide": c["slide"], "reason": why} for c, why in not_checked],
                "carried": [{"claim_id": cid, "slide": slide_of[cid], "from": src}
                            for cid, src in carried.items() if cid in slide_of]})
    return {"ok": True, "out": str(ws / "research" / "batches.json"),
            "batches": sum(b["research"] for b in batches),
            "arithmetic_batches": sum(not b["research"] for b in batches),
            "claims": len(claims), "researched": len(research), "arithmetic": len(arithmetic),
            "not_checked": dict(Counter(why for _, why in not_checked)), "carried": len(carried),
            "search_for_change": sum(c["search_for_change"] for b in batches for c in b["claims"])}


def _majority(verdicts: list[dict]) -> dict:
    """Majority of (verdict, severity); ties go to the lower severity."""
    counts = Counter((v["verdict"], v.get("severity")) for v in verdicts)
    best = max(counts.items(), key=lambda kv: (kv[1], SEVERITY_ORDER[kv[0][1]]))[0]
    chosen = next(v for v in verdicts if (v["verdict"], v.get("severity")) == best)
    return {**chosen, "second_checked": True,
            "votes": [f"{v['verdict']}/{v.get('severity')}" for v in verdicts]}


def summary(args) -> dict:
    """Merge checks/*.json into claim_check.json and compute every count a report states."""
    ws = Path(args.workspace).resolve()
    claims = {c["id"]: c for c in load_json(ws / "claims.json")["claims"]}
    batch_doc = load_json(ws / "research" / "batches.json")
    batches = batch_doc["batches"]
    assigned = {c["claim_id"]: b["batch"] for b in batches for c in b["claims"]}
    not_checked = {a["claim_id"]: a["reason"] for a in batch_doc.get("not_checked", [])}
    not_checked.update({a["claim_id"]: "assumption" for a in batch_doc.get("assumptions", [])})  # older files
    carried = {a["claim_id"]: a["from"] for a in batch_doc.get("carried", [])}
    unplaced = sorted(set(claims) - set(assigned) - set(not_checked) - set(carried))
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
        if v.get("severity") == "CRITICAL" and len(second.get(cid, [])) < 2:
            needs_second.append(cid)
        final[cid] = _majority([v] + second[cid][:2]) if len(second.get(cid, [])) >= 2 else v

    quote_status = Counter()
    for q in quotes:
        quote_status[q["status"]] += 1
    unmatched_claims = sorted({q["claim_id"] for q in quotes if q["status"] == "not_found"})

    rows = []
    for cid, c in claims.items():
        if cid in not_checked:
            continue
        v = final.get(cid) or {"verdict": "VERIFIED", "sources_used": [], "batch": None,
                               "carried_from": carried[cid]}   # verified in another deck's check
        rows.append({"claim_id": cid, "slide": c["slide"], "slide_title": c.get("slide_title"),
                     "text": c["text"], "statement": c["statement"], "kind": c["kind"],
                     "verdict": v["verdict"], "severity": v.get("severity"), "fix_kind": v.get("fix_kind"),
                     "outdated": v.get("outdated"), "issue": v.get("issue"),
                     "suggested_fix": v.get("suggested_fix"), "sources_used": v["sources_used"],
                     "batch": v["batch"], "carried_from": v.get("carried_from"),
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
                         "carried": sum(1 for r in rows if r["carried_from"]),
                         "not_checked": dict(Counter(not_checked.values()))},
              "needs_second_check": needs_second, "claims": rows,
              "not_checked": [{"claim_id": cid, "slide": claims[cid]["slide"], "reason": why,
                               "text": claims[cid]["text"]}
                              for cid, why in sorted(not_checked.items(), key=lambda x: (claims[x[0]]["slide"], x[0]))]}
    write_json(ws / "claim_check.json", result)
    return {"ok": not needs_second, "out": str(ws / "claim_check.json"), **result["counts"],
            "needs_second_check": needs_second}
