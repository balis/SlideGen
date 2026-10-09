"""Field trends, stage 3: a profile per shortlisted topic - attention, technical maturity, production use, and
reported benefits and limitations.

  sg trends shortlist        trends/shortlist.json: topics to profile, in batches for evidence-researchers
  sg trends evidence-check   checks trends/evidence/<batch>.json (quotes, sources, references)
  sg trends profiles         trends/profiles.md|.json
"""
from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urlparse

from .attention import adoption_cell
from .harvest import clean, compile_topics, topic_matches
from .trends import _manifest, _quote_ok, _texts
from .util import SgError, load_json, today, write_json

BATCH = 6
TOP_BY_SHARE = 20
MIN_QUOTE = 20


def shortlist(args) -> dict:
    """Topics a course must decide on: all with a change in attention, every anchor's topic, and the topics with
    the largest share of current items."""
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    att = load_json(ws / "attention.json")["topics"]
    topics = load_json(ws / "topics.json", "trend_topics")["topics"]
    compiled = compile_topics(topics)
    picked = {}
    for tid, r in att.items():
        if r["verdict"] in ("growing", "rising in one family", "mixed", "falling in one family", "declining"):
            picked[tid] = f"attention: {r['verdict']}"
    for a in cfg.get("anchors", []):
        for name in [a["name"]] + a.get("aliases", []):
            for tid in topic_matches(compiled, clean(name)):
                picked.setdefault(tid, "anchor")
    share = lambda r: sum(e["share_current"] or 0 for e in r["families"].values())
    for tid, r in sorted(att.items(), key=lambda x: -share(x[1]))[:TOP_BY_SHARE]:
        picked.setdefault(tid, "large share of current items")
    ids = sorted(picked, key=lambda t: (att[t]["verdict"] != "growing", -share(att[t])))
    batches = [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]
    write_json(ws / "shortlist.json", {"generated_by": "sg trends shortlist", "reasons": picked,
                                       "batches": {f"e{n + 1:02d}": b for n, b in enumerate(batches)}})
    return {"ok": True, "topics": len(ids), "batches": len(batches), "out": str(ws / "shortlist.json")}


def evidence_check(args) -> dict:
    cfg = _manifest(args.manifest)
    ws, texts = cfg["_ws"], _texts(cfg["_store"])
    short = load_json(ws / "shortlist.json")
    wanted = {t for b in short["batches"].values() for t in b}
    batch_of = {t: b for b, ts in short["batches"].items() for t in ts}
    discovery = {d["key"]: d for d in load_json(ws / "discovery_collection.json")["sources"]}
    seen, problems = set(), []
    for path in sorted((ws / "evidence").glob("*.json")):
        try:
            doc = load_json(path, "trend_evidence")
        except SgError as e:   # one broken file must not hide the problems of the others
            problems.append(str(e))
            continue
        for t in doc["topics"]:
            if t["topic"] not in wanted:
                problems.append(f"{path.name}: {t['topic']} is not on the shortlist")
            elif batch_of[t["topic"]] != path.stem:
                problems.append(f"{path.name}: {t['topic']} belongs to batch {batch_of[t['topic']]}")
            if t["topic"] in seen:
                problems.append(f"{path.name}: {t['topic']} appears in more than one evidence file")
            seen.add(t["topic"])
            ids = [e["id"] for e in t["evidence"]]
            if len(ids) != len(set(ids)):
                problems.append(f"{t['topic']}: duplicate evidence ids")
            for e in t["evidence"]:
                if e["source"] and e["source"] not in discovery:
                    problems.append(f"{t['topic']} {e['id']}: source {e['source']} is not in the discovery collection")
                elif e["source"] and not _same_site(e["url"], discovery[e["source"]]):
                    problems.append(f"{t['topic']} {e['id']}: {e['url']} is not a page of {e['source']}; "
                                    "name the right source or set it to null")
                if not _quote_ok(texts, e["fetched"], e["quote"]):
                    problems.append(f"{t['topic']} {e['id']}: quote not found in its downloaded page")
            for note in ("status_note", "production_note", "limitations_note"):
                for ref in [w.strip("[](),.;:") for w in t[note].split()]:
                    if ref.startswith("e") and ref[1:].isdigit() and ref not in ids:
                        problems.append(f"{t['topic']}: {note} cites {ref}, which is not in its evidence")
    missing = sorted(wanted - seen)
    return {"ok": not problems and not missing, "topics": len(seen), "missing": missing, "problems": problems[:30]}


def _site(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return ".".join(host.split(".")[-2:]) if host else ""


def _same_site(url: str, source: dict) -> bool:
    """The page belongs to the discovery source: same registered domain as its latest item or its access note."""
    site = _site(url)
    known = {_site(source["latest"]["url"])} | {_site(u) for u in re.findall(r"https?://\S+", source["access"])}
    return bool(site) and site in known


STATUS_ORDER = ["mature", "generally available", "established practice", "preview", "in development",
                "emerging practice", "proposal", "unclear"]


def _attention_cell(r: dict) -> str:
    arrows = {"up": "↑", "down": "↓", "flat": "→"}
    fams = [f"{arrows[e['direction']]}{f.split('_')[0][:5]}" for f, e in r["families"].items()
            if e["direction"] in arrows]
    return f"{r['verdict']} ({' '.join(fams)})" if fams else r["verdict"]


def _adoption_cell(a: dict) -> str:
    return "; ".join(adoption_cell(v, short=False) for v in a.values()) or "–"


def profiles(args) -> dict:
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    att = load_json(ws / "attention.json")["topics"]
    topics = {t["id"]: t for t in load_json(ws / "topics.json", "trend_topics")["topics"]}
    short = load_json(ws / "shortlist.json")
    evidence = {}
    for path in sorted((ws / "evidence").glob("*.json")):
        for t in load_json(path, "trend_evidence")["topics"]:
            evidence[t["topic"]] = t
    ids = [t for b in short["batches"].values() for t in b]
    missing = [t for t in ids if t not in evidence]
    if missing:
        raise SgError(f"no evidence for {len(missing)} shortlisted topics: {missing[:10]}")
    rows = []
    for tid in ids:
        r, e = att[tid], evidence[tid]
        orgs = {x["organization"]: x for x in e["evidence"] if x["dimension"] == "production_use" and x.get("organization")}
        sectors = Counter((x.get("sector") or "unknown") for x in orgs.values())
        rows.append({"id": tid, "name": topics[tid]["name"], "kind": topics[tid]["kind"], "attention": r["verdict"],
                     "families": {f: v["direction"] for f, v in r["families"].items()},
                     "adoption": r.get("adoption", {}), "status": e["status"], "platforms_ga": e["platforms_ga"],
                     "platforms_preview": e["platforms_preview"], "organizations": sorted(orgs),
                     "sectors": dict(sectors), "reason": short["reasons"][tid]})
    write_json(ws / "profiles.json", {"generated_by": "sg trends profiles", "topics": rows})
    lines = [f"# Topic profiles: {cfg['field']}", "",
             f"Generated {today()} by `sg trends profiles`. Attention compares the previous window "
             f"({cfg['windows']['previous'][0]} to {cfg['windows']['previous'][1]}) with the current one "
             f"({cfg['windows']['current'][0]} to {cfg['windows']['current'][1]}); arrows show families whose change "
             "is outside the 95% interval of no change. Maturity, production use and limitations come from the "
             "discovery collection, every statement backed by a quoted page. Organizations and platforms are those "
             "found within a budget of about seven cited items per topic: a sample that shows the kind of use, not a "
             "count of users, and a lower bound for platforms.", "",
             "| Topic | Attention | Maturity | Platforms GA | Production use | Adoption |", "|---|---|---|---|---|---|"]
    order = {"growing": 0, "rising in one family": 1, "mixed": 2, "steady": 3, "falling in one family": 4,
             "declining": 5, "too little evidence": 6}
    rows.sort(key=lambda x: (order.get(x["attention"], 9), STATUS_ORDER.index(x["status"]), x["name"].lower()))
    for x in rows:
        sectors = ", ".join(sorted(x["sectors"]))
        lines.append(f"| [{x['name']}](#{x['id']}) | {_attention_cell(att[x['id']])} | {x['status']} | "
                     f"{len(x['platforms_ga'])} | {len(x['organizations'])} orgs" +
                     (f" ({sectors})" if sectors else "") + f" | {_adoption_cell(x['adoption'])} |")
    for x in rows:
        e = evidence[x["id"]]
        by_id = {v["id"]: v for v in e["evidence"]}
        lines += ["", f"## {x['name']}", "", f"<a id=\"{x['id']}\"></a>",
                  f"*{x['kind']}; shortlisted for: {x['reason']}*", "",
                  f"**Attention:** {_attention_cell(att[x['id']])}.", "",
                  f"**Adoption:** {_adoption_cell(x['adoption'])}.", "",
                  f"**Maturity: {x['status']}.** {e['status_note']}" +
                  (f" Generally available on: {', '.join(e['platforms_ga'])}." if e["platforms_ga"] else "") +
                  (f" In preview on: {', '.join(e['platforms_preview'])}." if e["platforms_preview"] else ""), "",
                  f"**Production use:** {e['production_note']}", "",
                  f"**Benefits and limitations:** {e['limitations_note']}", "", "Evidence:", ""]
        for v in e["evidence"]:
            who = f" ({v['organization']})" if v.get("organization") else ""
            lines.append(f"- {v['id']} [{v['dimension'].replace('_', ' ')}]{who}: {v['claim']} "
                         f"\"{v['quote']}\" ([source]({v['url']}){', ' + v['date'] if v.get('date') else ''})")
    (ws / "profiles.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "topics": len(rows), "out": str(ws / "profiles.md")}
