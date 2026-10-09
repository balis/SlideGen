"""Change plans: validation, time budget, rating, and the rendered report and checklist.

The report and checklist are rendered from data files only (slides.json,
claim_check.json, course/findings.json, plan.json), so every count and verdict
they state comes from sg, not from a model.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .util import SgError, excluded_slides, load_json, load_manifest, manifest_deck, today, write_json

BLOCKING = {"CRITICAL", "MAJOR"}
CHANGING_TYPES = {"EDIT", "REPLACE", "REMOVE", "MERGE", "COMPRESS", "REBUILD"}
STRUCTURAL_TYPES = {"REPLACE", "REMOVE", "MERGE", "COMPRESS"}
REBUILD_SHARE = 0.40        # share of slides restructured above which a rebuild is recommended
SIGNIFICANT_SHARE = 0.15    # share of slides changed above which the update is significant
SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, None: 3}


class _Deck:
    """Everything known about one deck of a manifest."""

    def __init__(self, manifest_path: str, deck_id: str):
        self.manifest = load_manifest(manifest_path)
        self.cfg = manifest_deck(self.manifest, deck_id)
        self.root = Path(manifest_path).resolve().parent
        self.ws = self.root / deck_id / "workspace"
        self.out = self.root / deck_id / "output"
        self.slides_doc = load_json(self.ws / "slides.json")
        self.slides = {s["index"]: s for s in self.slides_doc["slides"]}
        self.excluded = excluded_slides(self.slides_doc, self.cfg)
        self.in_scope = [i for i in self.slides if i not in self.excluded]
        self.claims = load_json(self.ws / "claim_check.json")
        self.claim_rows = {r["claim_id"]: r for r in self.claims["claims"]}
        findings_file = self.root / "course" / "findings.json"
        self.findings_doc = load_json(findings_file) if findings_file.exists() else {"findings": []}
        self.findings = [f for f in self.findings_doc["findings"] if deck_id in f["decks"]]
        self.finding_keys = {f["key"] for f in self.findings_doc["findings"]}
        self.plan = load_json(self.ws / "plan.json", "plan") if (self.ws / "plan.json").exists() else None
        quotes_file = self.ws / "quotes.json"
        self.quotes = {(q["batch"], q["claim_id"], q["source"]): q
                       for q in (load_json(quotes_file)["results"] if quotes_file.exists() else [])}

    def title(self, index: int) -> str:
        s = self.slides.get(index)
        return (s and s["title"]) or "(image slide)"


def _protected_slides(deck: _Deck) -> set[int]:
    from .util import parse_range
    out: set[int] = set()
    for entry in deck.cfg.get("_protected", []):
        if any(ch.isdigit() for ch in str(entry)) and all(ch in "0123456789-, " for ch in str(entry)):
            out |= set(parse_range(entry))
    return out


def _check(deck: _Deck) -> list[str]:
    if deck.plan is None:
        raise SgError(f"missing {deck.ws / 'plan.json'}; run the change-planner")
    problems = []
    items = deck.plan["items"]
    ids = Counter(i["id"] for i in items)
    problems += [f"duplicate item id {k}" for k, n in ids.items() if n > 1]
    protected = _protected_slides(deck)
    recreate = {tuple(r["_slides"]): r for r in deck.cfg.get("_recreate", [])}
    rebuilt = set()
    for it in items:
        for s in it["slides"]:
            if s not in deck.slides:
                problems.append(f"{it['id']}: slide {s} does not exist")
            elif s in deck.excluded and it["type"] != "INSERT":
                problems.append(f"{it['id']}: slide {s} is excluded ({deck.excluded[s]})")
            if s in protected and it["type"] in {"REMOVE", "COMPRESS"}:
                problems.append(f"{it['id']}: slide {s} is protected")
        problems += [f"{it['id']}: unknown claim {c}" for c in it["claims"] if c not in deck.claim_rows]
        problems += [f"{it['id']}: unknown finding {k}" for k in it["findings"] if k not in deck.finding_keys]
        if it["type"] == "REBUILD":
            span = tuple(it["slides"])
            match = next((r for r in recreate if set(span) == set(r)), None)
            if match is None:
                problems.append(f"{it['id']}: REBUILD slides {span[0]}-{span[-1]} match no 'recreate' range")
            else:
                rebuilt.add(match)
    problems += [f"recreate range {r[0]}-{r[-1]} has no REBUILD item" for r in recreate if r not in rebuilt]

    rebuild_slides = {s for it in items if it["type"] == "REBUILD" for s in it["slides"]}
    addressed_claims = {c for it in items for c in it["claims"]}
    for cid, row in deck.claim_rows.items():
        if row["severity"] in BLOCKING and cid not in addressed_claims and row["slide"] not in rebuild_slides:
            problems.append(f"{row['verdict']}/{row['severity']} claim {cid} (slide {row['slide']}) "
                            f"is addressed by no item")
    addressed_findings = {k for it in items for k in it["findings"]}
    for f in deck.findings:
        if f["priority"] == "MUST" and f["key"] not in addressed_findings:
            problems.append(f"MUST finding {f['key']} is addressed by no item")
    return problems


def _budget(deck: _Deck) -> dict:
    visible = [i for i in deck.in_scope]
    minutes = deck.cfg.get("minutes") or 90
    per_slide = minutes / max(len(visible), 1)
    delta = sum(it["slides_delta"] for it in deck.plan["items"])
    return {"slides_in_scope": len(visible), "minutes": minutes,
            "minutes_per_slide": round(per_slide, 2), "net_slides_delta": delta,
            "projected_minutes": round((len(visible) + delta) * per_slide),
            "over_budget_minutes": max(0, round(delta * per_slide))}


def _rating(deck: _Deck) -> dict:
    """Rebuild is recommended when the plan restructures much of the deck; line edits and
    author-requested REBUILD ranges make an update significant but do not call for a rebuild."""
    items = deck.plan["items"]
    in_scope = set(deck.in_scope)
    changed = {s for it in items if it["type"] in CHANGING_TYPES for s in it["slides"]} & in_scope
    structural = {s for it in items if it["type"] in STRUCTURAL_TYPES for s in it["slides"]} & in_scope
    share = len(changed) / max(len(in_scope), 1)
    structural_share = len(structural) / max(len(in_scope), 1)
    blocking = [r for r in deck.claim_rows.values()
                if r["verdict"] in {"OUTDATED", "MISREPRESENTED"} and r["severity"] in BLOCKING]
    must = [f for f in deck.findings if f["priority"] == "MUST"]
    reasons = [f"{len(changed)} of {len(in_scope)} slides in scope change ({share:.0%}); "
               f"{len(structural)} are restructured ({structural_share:.0%})"]
    if structural_share > REBUILD_SHARE:
        rating = "rebuild recommended"
    elif blocking or must or share > SIGNIFICANT_SHARE:
        rating = "significant update"
        if blocking:
            reasons.append(f"{len(blocking)} claims outdated or misrepresented at CRITICAL/MAJOR")
        if must:
            reasons.append(f"{len(must)} MUST findings")
    else:
        rating = "light refresh"
    return {"rating": rating, "changed_share": round(share, 3),
            "structural_share": round(structural_share, 3), "reasons": reasons}


def validate(args) -> dict:
    deck = _Deck(args.manifest, args.deck)
    problems = _check(deck)
    if problems:
        raise SgError(f"plan.json for {args.deck}: " + "; ".join(problems[:12]))
    return {"ok": True, "items": len(deck.plan["items"]),
            "by_type": dict(Counter(i["type"] for i in deck.plan["items"])),
            "budget": _budget(deck), **_rating(deck)}


# ---------------------------------------------------------------- rendering

def _source_line(deck: _Deck, batch: str, claim_id: str, index: int | None) -> str:
    if index is None:
        return "none"
    q = deck.quotes.get((batch, claim_id, index))
    if q is None:
        return f"source {index} (not in quotes.json)"
    status = {"matched": "quote matched", "not_found": "QUOTE NOT FOUND", "too_short": "quote too short to check",
              "not_machine_checked": "not machine-checked"}[q["status"]]
    published = f", {q['published']}" if q.get("published") else ""
    return f"[{q.get('title') or q['url']}]({q['url']}){published} ({status})"


def _claim_block(deck: _Deck, r: dict) -> list[str]:
    lines = [f"### Slide {r['slide']}: {deck.title(r['slide'])}", "",
             f"- **On the slide:** {r['text']}",
             f"- **Verdict:** {r['verdict']} ({r['severity']})"
             + (" after a second check, votes " + ", ".join(r["votes"]) if r.get("second_checked") else "")]
    if r.get("outdated"):
        o = r["outdated"]
        label = {"changed-since": "changed since the deck was written",
                 "stale-when-written": "already out of date when written"}[o["label"]]
        lines.append(f"- **Status:** {label}" + (f", change dated {o['change_date']}" if o["change_date"] else "")
                     + ("; concerns versions newer than the labs use" if o["beyond_target_versions"] else ""))
        lines.append(f"- **Supporting source:** {_source_line(deck, r['batch'], r['claim_id'], o['supporting_source'])}")
        lines.append(f"- **Source showing the change:** {_source_line(deck, r['batch'], r['claim_id'], o['changing_source'])}")
    else:
        for i in r["sources_used"]:
            lines.append(f"- **Source:** {_source_line(deck, r['batch'], r['claim_id'], i)}")
    if r["issue"]:
        lines.append(f"- **Issue:** {r['issue']}")
    if r["suggested_fix"]:
        lines.append(f"- **Suggested fix:** {r['suggested_fix']}")
    return lines + [""]


def _finding_block(deck: _Deck, f: dict) -> list[str]:
    d = f["decks"][deck.cfg["id"]]
    src = f["primary_source"]
    age = {"new": "new since the last revision", "missing": "older than the last revision, but missing",
           "undated": "undated"}[d["age"]]
    lines = [f"### {f['key']} ({f['priority']})", "", f"{f['statement']}", "",
             f"- **Date:** {f['date'] or 'unknown'} ({age}); **maturity:** {f['maturity']}",
             f"- **Relates to slides:** {d['slides'][0]}-{d['slides'][-1]}",
             f"- **Primary source:** [{src['title'] or src['url']}]({src['url']})",
             f"- **Why it matters:** {f['relevance']}",
             f"- **Priority basis:** {f['priority_reason']}"]
    if f["teaching_signals"]:
        lines.append("- **Teaching signals:** " + "; ".join(
            f"[{s['title']}]({s['url']}) ({s['kind']}{', vendor' if s['vendor'] else ''})"
            for s in f["teaching_signals"]))
    return lines + [""]


def report(args) -> dict:
    deck = _Deck(args.manifest, args.deck)
    problems = _check(deck)
    if problems:
        raise SgError(f"plan.json for {args.deck} is not valid; run `sg plan validate` first: {problems[0]}")
    budget, rating = _budget(deck), _rating(deck)
    rows = sorted(deck.claim_rows.values(), key=lambda r: (SEVERITY_ORDER[r["severity"]], r["slide"]))
    counts = deck.claims["counts"]
    by_v = counts["by_verdict"]
    q = counts.get("quotes", {})
    prio = Counter(f["priority"] for f in deck.findings)
    deck_name = Path(deck.cfg["_path"]).name

    md = [f"# Modernization report: {deck_name}", "",
          f"Generated {today()} by `sg plan report` from claim_check.json, findings.json and plan.json.", "",
          f"**Rating: {rating['rating']}.** " + "; ".join(rating["reasons"]) + ".", "",
          "## Summary", "",
          "| | |", "|---|---|",
          f"| Claims checked | {counts['claims']} |",
          f"| Verified | {by_v.get('VERIFIED', 0)} |",
          f"| Outdated | {by_v.get('OUTDATED', 0)} |",
          f"| Misrepresented | {by_v.get('MISREPRESENTED', 0)} |",
          f"| Unverified | {by_v.get('UNVERIFIED', 0)} |",
          f"| Quotes matched / not found / too short / not machine-checked | {q.get('matched', 0)} / {q.get('not_found', 0)} / {q.get('too_short', 0)} / {q.get('not_machine_checked', 0)} |",
          f"| New developments (MUST / SHOULD / OPTIONAL) | {prio.get('MUST', 0)} / {prio.get('SHOULD', 0)} / {prio.get('OPTIONAL', 0)} |",
          f"| Plan items | {len(deck.plan['items'])} |",
          f"| Net slide change | {budget['net_slides_delta']:+d} (about {budget['projected_minutes']} of {budget['minutes']} minutes) |",
          ""]
    outdated = [r for r in rows if r["verdict"] == "OUTDATED"]
    wrong = [r for r in rows if r["verdict"] in {"MISREPRESENTED", "UNVERIFIED"}]
    md += ["## Outdated claims", ""] + (sum((_claim_block(deck, r) for r in outdated), []) or ["None.", ""])
    md += ["## Misrepresented and unverified claims", ""] + (sum((_claim_block(deck, r) for r in wrong), []) or ["None.", ""])
    md += ["## New developments", ""] + (sum((_finding_block(deck, f) for f in deck.findings), []) or ["None.", ""])
    md += ["## Change plan", "", "Each item is also in checklist.md.", ""]
    for it in sorted(deck.plan["items"], key=lambda i: (i["slides"][0], i["id"])):
        span = f"{it['slides'][0]}-{it['slides'][-1]}" if len(it["slides"]) > 1 else str(it["slides"][0])
        where = f"after slide {span}" if it["type"] == "INSERT" else f"slide{'s' if len(it['slides']) > 1 else ''} {span}"
        md += [f"### {it['id']} · {it['type']} · {where}: {deck.title(it['slides'][0])}", "",
               f"**Why:** {it['reason']}", ""]
        if it["current_text"]:
            md += [f"**Now:** {it['current_text']}", ""]
        md += [f"**Proposed:** {it['proposed']}", "",
               f"Slides {it['slides_delta']:+d}." + (f" Claims: {', '.join(it['claims'])}." if it["claims"] else "")
               + (f" Findings: {', '.join(it['findings'])}." if it["findings"] else ""), ""]
    skipped = sorted(deck.excluded.items())
    if skipped:
        md += ["## Not checked", "",
               ", ".join(f"{i} ({why})" for i, why in skipped) + ".", ""]
    if deck.plan.get("notes"):
        md += ["## Planner notes", "", deck.plan["notes"], ""]

    checklist = [f"# Checklist: {deck_name}", "",
                 "Tick the items to apply (`- [x]`), then run deck-modernize with `--phase apply`.", ""]
    for it in sorted(deck.plan["items"], key=lambda i: (i["slides"][0], i["id"])):
        span = f"{it['slides'][0]}-{it['slides'][-1]}" if len(it["slides"]) > 1 else str(it["slides"][0])
        checklist.append(f"- [ ] {it['id']} · {it['type']} · slide {span} ({deck.title(it['slides'][0])}): "
                         f"{it['reason']}")
    deck.out.mkdir(parents=True, exist_ok=True)
    (deck.out / "modernization_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (deck.out / "checklist.md").write_text("\n".join(checklist) + "\n", encoding="utf-8")
    write_json(deck.ws / "plan_status.json", {"budget": budget, **rating})
    return {"ok": True, "report": str(deck.out / "modernization_report.md"),
            "checklist": str(deck.out / "checklist.md"), **rating, "budget": budget}


def course_summary(args) -> dict:
    manifest = load_manifest(args.manifest)
    root = Path(args.manifest).resolve().parent
    findings_doc = load_json(root / "course" / "findings.json")
    lines = [f"# Course summary: {manifest.get('name', root.name)}", "",
             f"Generated {today()} by `sg plan course-summary`.", "",
             "| Deck | Rating | Claims | Outdated (C/M/m) | Misrepresented | MUST | SHOULD | Net slides |",
             "|---|---|---|---|---|---|---|---|"]
    for cfg in manifest["decks"]:
        deck = _Deck(args.manifest, cfg["id"])
        rating = _rating(deck)
        sev = Counter(r["severity"] for r in deck.claim_rows.values() if r["verdict"] == "OUTDATED")
        mis = sum(r["verdict"] == "MISREPRESENTED" for r in deck.claim_rows.values())
        prio = Counter(f["priority"] for f in deck.findings)
        lines.append(f"| {Path(cfg['_path']).name} | {rating['rating']} | {len(deck.claim_rows)} | "
                     f"{sev.get('CRITICAL', 0)}/{sev.get('MAJOR', 0)}/{sev.get('MINOR', 0)} | {mis} | "
                     f"{prio.get('MUST', 0)} | {prio.get('SHOULD', 0)} | {_budget(deck)['net_slides_delta']:+d} |")
    lines += ["", "## Developments that fit no lecture in this set", ""]
    lines += [f"- **{f['key']}** ({f['maturity']}, {f['date'] or 'undated'}): {f['statement']} "
              f"[source]({f['primary_source']['url']})" for f in findings_doc["no_lecture"]] or ["None."]
    lines += ["", "## Developments already covered", ""]
    lines += [f"- **{f['key']}**: {f['review']['already_covered']['note']}"
              for f in findings_doc["already_covered"]] or ["None."]
    out = root / "course" / "course_summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "out": str(out)}
