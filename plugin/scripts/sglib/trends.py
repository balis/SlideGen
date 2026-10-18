"""Field trends, stage 0: choosing the panel of sources that later stages measure.

Layout, relative to the directory of the trends manifest (trends.yaml):
  trends/sources/candidates_<route>.json  source-scout output, one file per discovery route
  trends/source_candidates.json|.md       merged nominations (sg trends sources-merge)
  trends/sources/verified_<batch>.json    source-verifier output
  trends/sources_panel.json|.md           the selected panel (sg trends sources-check)
  trends/sources_review.json              sources-reviewer output (optional)
  sources/                                downloaded pages
"""
from __future__ import annotations

import calendar
import html
import math
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml

from .shares import page_rows, paired
from .sources import _normalize, entries_by_id, match_quote
from .util import SgError, check_schema, load_json, today, write_json

MIN_EVIDENCE_QUOTE = 10
MIN_SCOPE_FIT = 0.1   # default floor: excludes sources that are barely about the field
SCOPE_SAMPLE = 20     # items sampled for a scope estimate, unless the record says otherwise
Z = 1.96              # 95% interval for scope estimates
PAGE_COLLECTORS = {"survey_table", "records", "stackoverflow_survey", "top500_list"}   # measured on the stored pages


def _manifest(path: str) -> dict:
    p = Path(path).resolve()
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    check_schema(cfg, "trend_manifest", p)
    cfg["_root"], cfg["_ws"], cfg["_store"] = p.parent, p.parent / "trends", p.parent / "sources"
    return cfg


def collector_of(cfg: dict, row: dict | None, key: str) -> dict | None:
    """The collector of a source: the manifest's entry, else the one named in its verification record."""
    return (cfg.get("collectors") or {}).get(key) or ((row or {}).get("verified") or {}).get("collector")


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _texts(store: Path) -> dict[str, str]:
    """Content id -> path of the extracted text, for every downloaded page."""
    index_file = store / "index.json"
    if not index_file.exists():
        return {}
    return {cid: store / e["text_file"] for cid, e in entries_by_id(load_json(index_file)["sources"]).items()}


def _entries(store: Path) -> dict:
    """Content id -> index entry, for every downloaded page."""
    index_file = store / "index.json"
    return entries_by_id(load_json(index_file)["sources"]) if index_file.exists() else {}


def _plain_url(url: str) -> str:
    p = urlparse(url)
    host = p.netloc.lower().removeprefix("www.")
    return host + p.path.rstrip("/") + (f"?{p.query}" if p.query else "")


def page_origin(entries: dict, content_id: str | None, url: str | None = None) -> str | None:
    """Why a stored page is not sg's download of the page a record names, or None. Items and shares are checked
    against stored pages, so a file an agent wrote checks the agent's work against itself."""
    e = entries.get(content_id) if content_id else None
    if e is None:
        return None   # a page missing from the store is reported by each check
    if e["url"].startswith("file:"):
        return f"page {content_id} was stored from a local file ({e['url'][5:]}), not downloaded"
    if url and _plain_url(url) not in {_plain_url(e["url"]), _plain_url(e.get("final_url") or e["url"])}:
        return f"page {content_id} was downloaded from {e['url']}, not from {url}"
    return None


def _plain(text: str) -> str:
    """Text for finding a title: entities and percent-encoding decoded, hyphens and slashes read as spaces."""
    return re.sub(r"\s+", " ", _normalize(re.sub(r"[-_/+]", " ", unquote(html.unescape(text)))))


def _sample_unseen(store: Path, entries: dict, edition: dict) -> list[str]:
    """Sample rows of a verified edition that its stored pages do not print: an answer with its percentage on one
    row (sglib.shares), or a title in the text. A source whose sample fails cannot be measured from these pages."""
    sample = edition.get("sample") or []
    pages = [entries[f] for f in _edition_pages(edition) if f in entries]
    if not sample or not pages:
        return []
    rows = [r for p in pages for r in page_rows(store, p)]
    text = " ".join(_plain((store / p["text_file"]).read_text(encoding="utf-8")) for p in pages)
    names = [s["name"] for s in sample]
    return [s["name"] + (f" {s['percent']}%" if "percent" in s else "") for s in sample
            if not (paired(rows, s["name"], s["percent"], names) if "percent" in s else _plain(s["name"]) in text)]


def _quote_ok(texts: dict, content_id: str | None, quote: str) -> bool:
    if not content_id or content_id not in texts:
        return False
    return match_quote(quote, texts[content_id].read_text(encoding="utf-8"), min_chars=MIN_EVIDENCE_QUOTE)[0]


def sources_merge(args) -> dict:
    """Merge the scouts' nominations; count the independent routes that nominated each source."""
    cfg = _manifest(args.manifest)
    ws, texts = cfg["_ws"], _texts(cfg["_store"])
    families = set(cfg["families"])
    files = sorted((ws / "sources").glob("candidates_*.json"))
    if not files:
        raise SgError(f"no candidate files in {ws / 'sources'}")
    same = {alias: key for key, aliases in (cfg.get("same_source") or {}).items() for alias in aliases}
    merged: dict[str, dict] = {}
    rejected, problems = [], []
    for path in files:
        doc = load_json(path, "trend_candidates")
        for c in doc["candidates"]:
            if c["family"] not in families:
                problems.append(f"{path.name}: {c['name']} has unknown family {c['family']}")
                continue
            ev = c["evidence"]
            if not _quote_ok(texts, ev["fetched"], ev["quote"]):
                rejected.append({"name": c["name"], "route": doc["route"],
                                 "reason": "evidence quote not found in a downloaded page"})
                continue
            key = c.get("key") or _key(c["name"])
            key = same.get(key, key)
            m = merged.setdefault(key, {"key": key, "name": c["name"], "family": c["family"],
                                        "homepage": c["homepage"], "organiser": c["organiser"],
                                        "vendor": c["vendor"], "single_technology": c["single_technology"],
                                        "routes": [], "evidence": []})
            if doc["route"] not in m["routes"]:
                m["routes"].append(doc["route"])
            m["evidence"].append({"route": doc["route"], "url": ev["url"], "quote": ev["quote"]})
            m["vendor"] = m["vendor"] or c["vendor"]
            m["single_technology"] = m["single_technology"] or c["single_technology"]
    if problems:
        raise SgError("; ".join(problems[:10]))
    rows = sorted(merged.values(), key=lambda m: (m["family"], -len(m["routes"]), m["key"]))
    for m in rows:
        m["nominations"] = len(m["routes"])
    excluded = cfg.get("exclude") or {}
    for m in rows:
        m["verify"] = _family_reason(cfg["families"][m["family"]], m) is None and m["key"] not in excluded
    write_json(ws / "source_candidates.json", {"generated_by": "sg trends sources-merge",
                                               "candidates": rows, "rejected": rejected})
    hosts = defaultdict(list)   # same family and home page host: probably one source under two names
    for m in rows:
        hosts[(m["family"], urlparse(m["homepage"]).netloc.lower().removeprefix("www."))].append(m["key"])
    duplicates = [keys for keys in hosts.values() if len(keys) > 1]
    by_family = defaultdict(lambda: {"total": 0, "two_or_more_routes": 0})
    for m in rows:
        by_family[m["family"]]["total"] += 1
        by_family[m["family"]]["two_or_more_routes"] += m["nominations"] >= 2
    lines = [f"# Source candidates: {cfg['field']}", "", f"Generated {today()} by `sg trends sources-merge`.", "",
             "| Family | Source | Routes | Vendor | Verify |", "|---|---|---|---|---|"]
    lines += [f"| {m['family']} | [{m['name']}]({m['homepage']}) | {m['nominations']} ({', '.join(m['routes'])}) | "
              f"{'yes' if m['vendor'] else 'no'} | "
              f"{'yes' if m.get('verify') else _family_reason(cfg['families'][m['family']], m) or 'no'} |" for m in rows]
    if duplicates:
        lines += ["", "Possible duplicates (same home page host): " + "; ".join(", ".join(k) for k in duplicates)]
    (ws / "source_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "candidates": len(rows), "to_verify": sum(bool(m.get("verify")) for m in rows),
            "rejected": len(rejected), "possible_duplicates": duplicates, "by_family": dict(by_family),
            "out": str(ws / "source_candidates.md")}


def _family_reason(fam: dict, c: dict) -> str | None:
    """Why a candidate cannot belong to its family, or None."""
    if "vendor" in fam and c["vendor"] != fam["vendor"]:
        return "run by a vendor; this family takes independent sources" if c["vendor"] else \
            "not run by a vendor; this family takes vendor sources"
    return None


def _bounds(point: str) -> tuple[date, date]:
    """First and last day of '2025-11' or '2025-11-04'."""
    y, m, *d = map(int, point.split("-"))
    return (date(y, m, d[0]), date(y, m, d[0])) if d else (date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1]))


def _window_ok(period: str | None, window: list[str]) -> bool:
    """The midpoint of a period ('2025-11', '2025-11-04', '2025-10..2026-09') lies in the window [start, end]."""
    if not period:
        return False
    parts = period.split("..")
    lo, hi = _bounds(parts[0])[0], _bounds(parts[-1])[1]
    mid = (lo + (hi - lo) / 2).isoformat()
    return window[0] <= mid <= window[1]


def sources_check(args) -> dict:
    """Join verification results with nominations, apply eligibility rules, select the panel."""
    cfg = _manifest(args.manifest)
    ws, texts, entries = cfg["_ws"], _texts(cfg["_store"]), _entries(cfg["_store"])
    cands = {c["key"]: c for c in load_json(ws / "source_candidates.json")["candidates"]}
    verified = {}   # a later batch file (v2 after v1, v10 after v9) replaces an earlier record of the same source
    for path in sorted((ws / "sources").glob("verified_*.json"), key=_natural):
        for v in load_json(path, "trend_verified")["sources"]:
            if v["key"] not in cands:
                raise SgError(f"{path.name}: {v['key']} is not a merged candidate")
            verified[v["key"]] = v
    windows = cfg["windows"]
    rows = []
    for key, c in cands.items():
        v = verified.get(key)
        fam = cfg["families"][c["family"]]
        reasons = [] if _family_reason(fam, c) is None else [_family_reason(fam, c)]
        borderline, exact = [], None
        if v is None:
            reasons.append("not verified")
        elif v.get("not_collectable"):
            reasons.append(f"item lists exist but could not be collected: {v['not_collectable']}")
        elif v["scope_fit"] is None:
            reasons.append("scope fit not estimated")
        else:
            lo_fit, hi_fit = _fit_interval(v)
            exact_path = ws / "classified" / f"{key}.json"   # stage 1 counts every item; they replace the estimate
            exact = load_json(exact_path)["editions"] if exact_path.exists() else None
            for edition, window in (("current", windows["current"]), ("previous", windows["previous"])):
                e = v.get(edition)
                if e is None:
                    if edition == "current" or fam.get("needs_previous", True):
                        reasons.append(f"no {edition} edition found")
                    continue
                if not _window_ok(e["period"], window):
                    reasons.append(f"{edition} edition {e['period']} is outside {window[0]}..{window[1]}")
                if e["fetched"] is not None and not _quote_ok(texts, e["fetched"], e["items_quote"]):
                    reasons.append(f"{edition} edition quote not found in its downloaded page")
                if e["fetched"] is None and not v["api"]:
                    reasons.append(f"{edition} edition could not be downloaded")
                if any(m["fetched"] is not None and m["fetched"] not in texts for m in e.get("more_pages", [])):
                    reasons.append(f"{edition} edition names a further page that is not in the store")
                unseen = _sample_unseen(cfg["_store"], entries, e)
                if unseen:
                    reasons.append(f"{edition} edition is not measurable from its stored pages: sample rows "
                                   f"{unseen} are not printed there")
                need = fam.get("min_items", 0)
                if exact is not None:
                    measured = len(exact[edition]["measured"])
                    if measured < need:
                        reasons.append(f"{edition} edition has {measured} measured items after classification, "
                                       f"below {need}")
                elif e["items"] * hi_fit < need:
                    reasons.append(f"{edition} edition has about {e['items'] * v['scope_fit']:.0f} in-scope items "
                                   f"(at most {e['items'] * hi_fit:.0f}), below {need}")
                elif e["items"] * lo_fit < need:
                    borderline.append(f"{edition} edition has {e['items'] * lo_fit:.0f} to {e['items'] * hi_fit:.0f} "
                                      f"in-scope items, around the minimum of {need}")
            floor = fam.get("min_scope_fit", MIN_SCOPE_FIT)
            if v["scope_fit"] < floor:
                reasons.append(f"scope fit {v['scope_fit']:.0%} is below {floor:.0%}")
        if key in (cfg.get("exclude") or {}):
            reasons.append(f"excluded in the manifest: {cfg['exclude'][key]}")
        rows.append({**c, "verified": v, "eligible": not reasons, "reasons": reasons,
                     "borderline": borderline if not reasons else [], "kind": _kind(cfg, c),
                     "measured": {ed: len(x["measured"]) for ed, x in exact.items()} if exact else None})

    include = set(cfg.get("include") or [])
    unknown = include - {r["key"] for r in rows}
    if unknown:
        raise SgError(f"include names unknown sources: {sorted(unknown)}")
    selected, organisers, pending = [], set(), {}
    for fam_name, fam in cfg["families"].items():
        forced = [r for r in rows if r["family"] == fam_name and r["key"] in include]
        for r in forced:
            r["included_by_author"] = True
            organisers.add((fam_name, r["organiser"].lower()))
        pool = [r for r in rows if r["family"] == fam_name and r["eligible"] and r["key"] not in include]
        chosen = list(forced)
        for r in _round_robin([r for r in pool if not r["borderline"]]):
            org = (fam_name, r["organiser"].lower())
            if org in organisers or len(chosen) >= fam["quota"]:
                continue
            organisers.add(org)
            chosen.append(r)
        for r in chosen:
            r["selected"] = True
        selected += chosen
        # Sources whose in-scope range straddles the minimum wait for stage 1, which classifies every item;
        # the exact counts then decide the remaining places.
        waiting = [r for r in pool if r["borderline"] and (fam_name, r["organiser"].lower()) not in organisers]
        if len(chosen) < fam["quota"] and waiting:
            for r in waiting:
                r["pending"] = True
            pending[fam_name] = {"places": fam["quota"] - len(chosen),
                                 "candidates": [r["key"] for r in sorted(waiting, key=lambda r: -_in_scope(r))]}

    anchors = cfg.get("anchors", [])
    coverage = {}
    for a in anchors:
        pattern = re.compile(r"(?i)\b(" + "|".join(re.escape(x) for x in [a["name"]] + a.get("aliases", [])) + r")s?\b")
        fams = defaultdict(int)
        for r in selected:
            e = (r["verified"] or {}).get("current")
            if e and any(pattern.search(_page_text(texts, f)) for f in _edition_pages(e)):
                fams[r["family"]] += 1
        coverage[a["name"]] = dict(fams)
    blind = [a for a, f in coverage.items() if not f]
    short = {}
    for f, v in cfg["families"].items():
        have = sum(r["family"] == f for r in selected)
        could = have + min(pending.get(f, {}).get("places", 0), len(pending.get(f, {}).get("candidates", [])))
        if could < v["quota"]:
            short[f] = f"{have}/{v['quota']}" + (f" (+{could - have} pending)" if could > have else "")
    missing = [r["key"] for r in rows if r.get("verify") and r["verified"] is None]
    own = cfg.get("own_topics") or {}
    no_own = [r["key"] for r in selected if (r["vendor"] or r["single_technology"]) and not own.get(r["key"])]
    no_collector = [r["key"] for r in selected if cfg["families"][r["family"]]["role"] in ("forum", "adoption")
                    and not collector_of(cfg, r, r["key"])]
    not_downloaded, no_sample = {}, []
    for r in rows:
        if not (r.get("selected") or r.get("pending")):
            continue
        col = collector_of(cfg, r, r["key"]) or {}
        if col.get("type") in PAGE_COLLECTORS and not all(
                (r["verified"].get(ed) or {}).get("sample") for ed in ("current", "previous") if r["verified"].get(ed)):
            no_sample.append(r["key"])
        if cfg["families"][r["family"]]["role"] != "items" and col.get("type") not in PAGE_COLLECTORS:
            continue   # measured on data its collector downloads, not on the stored pages
        notes = [f"{ed}: {note}" for ed in ("current", "previous") if (r["verified"] or {}).get(ed)
                 for page in [r["verified"][ed]] + r["verified"][ed].get("more_pages", [])
                 if (note := page_origin(entries, page.get("fetched"), page.get("url")))]
        if notes:
            not_downloaded[r["key"]] = notes
    result = {"generated_by": "sg trends sources-check", "selected": [r["key"] for r in selected],
              "pending": pending, "short_families": short, "anchor_coverage": coverage,
              "blind_anchors": blind, "not_verified": missing, "missing_own_topics": no_own,
              "missing_collectors": no_collector, "pages_not_downloaded": not_downloaded,
              "missing_samples": no_sample, "sources": rows}
    write_json(ws / "sources_panel.json", result)
    _render_panel(cfg, rows, coverage, short, not_downloaded, no_sample)
    return {"ok": not blind and not short and not missing and not no_own and not no_collector,
            "selected": len(selected), "missing_collectors": no_collector,
            "pending": pending, "short_families": short, "blind_anchors": blind, "not_verified": missing,
            "missing_own_topics": no_own, "pages_not_downloaded": not_downloaded, "missing_samples": no_sample,
            "out": str(ws / "sources_panel.md")}


def _natural(path: Path) -> list:
    """Sort key that orders numbered names by number: verified_v9 before verified_v10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path.name)]


def _fit_interval(v: dict) -> tuple[float, float]:
    """95% Wilson interval of a scope fit estimated from a sample of items."""
    n, p = v.get("scope_sample") or SCOPE_SAMPLE, v["scope_fit"]
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def _kind(cfg: dict, c: dict) -> str:
    """What one item of the source is (talk, link, episode, ...)."""
    return (cfg.get("item_kinds") or {}).get(c["key"]) or cfg["families"][c["family"]].get("item_kind", "item")


def _round_robin(pool: list[dict]) -> list[dict]:
    """Order candidates so that every kind of item is represented before any kind gets a second source.

    Within a kind: sources whose minimum is certain before borderline ones, then more in-scope items, then more
    discovery routes."""
    rank = lambda r: (bool(r["borderline"]), -_in_scope(r), -r["nominations"], r["key"])
    by_kind = defaultdict(list)
    for r in sorted(pool, key=rank):
        by_kind[r["kind"]].append(r)
    queues = sorted(by_kind.values(), key=lambda q: rank(q[0]))
    order = []
    while any(queues):
        for q in queues:
            if q:
                order.append(q.pop(0))
    return order


def _view_text(view) -> str:
    return view["text"] if isinstance(view, dict) else view


def _edition_pages(edition: dict) -> list[str]:
    return [f for f in [edition["fetched"]] + [m["fetched"] for m in edition.get("more_pages", [])] if f]


def _page_text(texts: dict, content_id: str) -> str:
    """Downloaded text with percent-encoding decoded and hyphens and underscores read as spaces, so URL slugs
    match multi-word names."""
    if content_id not in texts:
        return ""
    return re.sub(r"[-_+]", " ", unquote(texts[content_id].read_text(encoding="utf-8")))


def _in_scope(row: dict) -> float:
    """Number of in-scope items in the current edition: counted in stage 1 if available, else estimated."""
    if row.get("measured"):
        return row["measured"]["current"]
    return row["verified"]["current"]["items"] * row["verified"]["scope_fit"]


def _render_panel(cfg: dict, rows: list[dict], coverage: dict, short: dict, not_downloaded: dict,
                  no_sample: list[str]) -> None:
    ws = cfg["_ws"]
    review = load_json(ws / "sources_review.json", "course_review") if (ws / "sources_review.json").exists() else None
    lines = [f"# Source panel: {cfg['field']}", "",
             f"Generated {today()} by `sg trends sources-check`. Current window {cfg['windows']['current'][0]} to "
             f"{cfg['windows']['current'][1]}; previous window {cfg['windows']['previous'][0]} to "
             f"{cfg['windows']['previous'][1]}.", "",
             "A source is eligible if both editions were downloaded and fall in the windows and each edition "
             "can have the family's minimum of in-scope items. Scope fit is estimated from a sample, so in-scope "
             "counts are ranges (95% interval). A source whose range straddles the minimum is not ranked on "
             "its estimate: it waits for stage 1, which classifies every item, and the exact counts decide the "
             "family's remaining places. Within a family, every kind of "
             "item (talk, link, episode, ...) is represented before a kind gets a second source; within a kind, "
             "sources with more in-scope items come first and the number of discovery routes breaks ties. One "
             "source per organiser per family. A source run by a vendor or dedicated to one technology must "
             "declare its own topics, which it cannot vote for.", "",
             "Sources that explain trends but cannot be compared year over year are listed in "
             "`discovery_collection.md`.", ""]
    for fam_name, fam in cfg["families"].items():
        fam_rows = [r for r in rows if r["family"] == fam_name]
        lines += [f"## {fam_name} (quota {fam['quota']})", "", fam.get("description", ""), "",
                  "| | Source | Kind | Routes | Current | Previous | Items | Fit | Vendor |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(fam_rows, key=lambda r: (not r.get("selected"), not r["eligible"], -r["nominations"])):
            v = r["verified"] or {}
            cur, prev = v.get("current") or {}, v.get("previous") or {}
            mark = ("**included in the manifest**" if r.get("included_by_author") else
                    "**selected**" if r.get("selected") else "eligible" if r["eligible"] else "–")
            if r.get("pending"):
                mark = "pending classification"
            fit = "–" if v.get("scope_fit") is None else f"{v['scope_fit']:.0%}"
            lines.append(f"| {mark} | [{r['name']}]({r['homepage']}) | {r['kind']} | {r['nominations']} | "
                         f"{cur.get('period', '–')} | {prev.get('period', '–')} | {cur.get('items', '–')} | {fit} | "
                         f"{'yes' if r['vendor'] else 'no'} |")
        subsets = [r for r in fam_rows if r["eligible"] and (r["verified"] or {}).get("subset_rule")]
        if subsets:
            lines += ["", "Measured on a subset: " + "; ".join(f"{r['name']} ({r['verified']['subset_rule']})"
                                                           for r in subsets)]
        waiting = [r for r in fam_rows if r.get("pending")]
        if waiting:
            places = fam["quota"] - sum(bool(r.get("selected")) for r in fam_rows)
            lines += ["", f"Pending classification for {places} remaining place(s); stage 1 classifies every item "
                      "and the exact in-scope counts decide: " +
                      "; ".join(f"{r['name']} ({', '.join(r['borderline'])})" for r in waiting)]
        limited = [r for r in fam_rows if (r.get("selected") or r.get("pending"))
                   and (cfg.get("sees_only") or {}).get(r["key"])]
        if limited:
            lines += ["", "Sees only part of the field (topics outside it are not measured there, not zero): " +
                      "; ".join(f"{r['name']} ({_view_text(cfg['sees_only'][r['key']])})" for r in limited)]
        own = [r for r in fam_rows if r.get("selected") and (cfg.get("own_topics") or {}).get(r["key"])]
        if own:
            lines += ["", "Own topics, not counted from that source: " +
                      "; ".join(f"{r['name']} ({', '.join(cfg['own_topics'][r['key']])})" for r in own)]
        rejected = [r for r in fam_rows if not r["eligible"] and r["reasons"] != ["not verified"]]
        if rejected:
            lines += ["", "Not eligible: " + "; ".join(f"{r['name']} ({', '.join(r['reasons'])})" for r in rejected)]
        lines.append("")
    lines += ["## Anchor coverage", "", "Anchors test coverage only; they do not affect ranking.", "",
              "| Anchor | Families where the selected sources mention it |", "|---|---|"]
    lines += [f"| {a} | {', '.join(f'{f} ({n})' for f, n in fams.items()) or '**none: blind spot**'} |"
              for a, fams in coverage.items()]
    if short:
        lines += ["", f"Families below quota: {short}"]
    if not_downloaded:
        lines += ["", "## Pages not downloaded by sg", "",
                  "Items and shares of these editions are checked against a file an agent made, or against a page "
                  "other than the one the record names. Store the real pages with `sg fetch` where they exist.", ""]
        lines += [f"- {key}: {'; '.join(notes)}" for key, notes in not_downloaded.items()]
    if no_sample:
        lines += ["", "Measured from stored pages but verified without a sample of rows, so whether the pages print "
                  f"what stage 2 reads is not checked yet: {', '.join(no_sample)}"]
    if review:
        lines += ["", "## Reviewer notes", "", review["summary"], ""]
        lines += [f"- **{i['severity']}:** {i['issue']} *Suggestion:* {i['suggestion']}" for i in review["issues"]]
    (ws / "sources_panel.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def discovery_check(args) -> dict:
    """Check the discovery collection: evidence quotes, recent activity, and the targets per kind of source."""
    cfg = _manifest(args.manifest)
    ws, texts = cfg["_ws"], _texts(cfg["_store"])
    targets = cfg.get("discovery") or {}
    files = sorted((ws / "discovery").glob("*.json"))
    if not files:
        raise SgError(f"no discovery files in {ws / 'discovery'}")
    rows, seen, problems = [], {}, []
    for path in files:
        for d in load_json(path, "trend_discovery")["sources"]:
            if d["key"] in seen:
                problems.append(f"{d['key']} is listed in {seen[d['key']]} and {path.name}")
                continue
            seen[d["key"]] = path.name
            reasons = []
            if not _quote_ok(texts, d["latest"]["fetched"], d["latest"]["quote"]):
                reasons.append("latest item quote not found in its downloaded page")
            if not _window_ok(d["latest"]["date"], cfg["windows"]["current"]):
                reasons.append(f"latest item {d['latest']['date']} is outside the current window")
            if d["kind"] == "engineering_blog" and (d.get("tech_company") is None or not d.get("sector")
                                                    or not d.get("org_size")):
                reasons.append("engineering blog without sector, size, or tech_company")
            rows.append({**d, "file": path.name, "active": not reasons, "reasons": reasons})
    if problems:
        raise SgError("; ".join(problems))
    active = [r for r in rows if r["active"]]
    short = {}
    for kind, t in targets.items():
        got, orgs = [], set()
        for r in active:   # one organization with two blogs counts once
            if r["kind"] == kind and r["organiser"].lower() not in orgs:
                orgs.add(r["organiser"].lower())
                got.append(r)
        if len(got) < t.get("min", 0):
            short[kind] = f"{len(got)}/{t['min']}"
        if kind == "engineering_blog":
            non_tech = sum(r["tech_company"] is False for r in got)
            not_large = sum(r["org_size"] in ("medium", "small") for r in got)
            sectors = {r["sector"].lower() for r in got}
            if non_tech < t.get("min_non_tech", 0):
                short["engineering_blog non-tech organizations"] = f"{non_tech}/{t['min_non_tech']}"
            if not_large < t.get("min_not_large", 0):
                short["engineering_blog medium or small organizations"] = f"{not_large}/{t['min_not_large']}"
            if len(sectors) < t.get("min_sectors", 0):
                short["engineering_blog sectors"] = f"{len(sectors)}/{t['min_sectors']}"
    write_json(ws / "discovery_collection.json", {"generated_by": "sg trends discovery-check", "short": short,
                                                  "sources": rows})
    _render_discovery(cfg, rows, short)
    return {"ok": not short and all(r["active"] for r in rows), "sources": len(rows), "active": len(active),
            "inactive": [r["key"] for r in rows if not r["active"]], "short": short,
            "out": str(ws / "discovery_collection.md")}


DIMENSION_NAMES = {"attention": "attention", "maturity": "technical maturity", "production_use": "production use",
                   "limitations": "benefits and limitations"}


def _render_discovery(cfg: dict, rows: list[dict], short: dict) -> None:
    lines = [f"# Discovery collection: {cfg['field']}", "",
             f"Generated {today()} by `sg trends discovery-check`. These sources find candidate topics and explain "
             "them; they are not compared year over year. A source counts as active if an item dated in the "
             f"current window ({cfg['windows']['current'][0]} to {cfg['windows']['current'][1]}) was downloaded "
             "and quoted.", ""]
    for kind in sorted({r["kind"] for r in rows}):
        group = [r for r in rows if r["kind"] == kind]
        lines += [f"## {kind.replace('_', ' ')} ({sum(r['active'] for r in group)} active)", "",
                  "| | Source | Shows | Organiser | Details | Latest |", "|---|---|---|---|---|---|"]
        for r in sorted(group, key=lambda r: (not r["active"], r["name"].lower())):
            if kind == "engineering_blog":
                details = f"{r['sector']}, {r['org_size']}" + ("" if r.get("tech_company") else ", non-tech")
            else:
                details = ", ".join(r.get("projects") or []) or "–"
            if r["vendor"]:
                details += " (vendor)"
            lines.append(f"| {'active' if r['active'] else '–'} | [{r['name']}]({r['latest']['url']}) | "
                         f"{', '.join(DIMENSION_NAMES[d] for d in r['dimensions'])} | {r['organiser']} | {details} | "
                         f"{r['latest']['date']} |")
        inactive = [r for r in group if not r["active"]]
        if inactive:
            lines += ["", "Not active: " + "; ".join(f"{r['name']} ({', '.join(r['reasons'])})" for r in inactive)]
        lines.append("")
    if short:
        lines += [f"Below target: {short}", ""]
    (cfg["_ws"] / "discovery_collection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


DISCOVERY_KINDS = ("engineering_blog", "project_proposals", "project_releases", "specification",
                   "platform_release_notes", "survey", "radar", "report", "conference_recordings", "other")


def manifest_check(args) -> dict:
    """Check a drafted manifest beyond its schema: windows, roles, anchors, discovery targets."""
    cfg = _manifest(args.manifest)
    problems, warnings = [], []
    (ps, pe), (cs, ce) = cfg["windows"]["previous"], cfg["windows"]["current"]
    span = lambda a, b: (date.fromisoformat(b) - date.fromisoformat(a)).days
    if span(pe, cs) != 1:
        problems.append(f"the previous window must end the day before the current one starts ({pe} / {cs})")
    for name, (a, b) in (("previous", (ps, pe)), ("current", (cs, ce))):
        if not 360 <= span(a, b) <= 367:
            problems.append(f"the {name} window spans {span(a, b) + 1} days, not about a year")
    roles = {v["role"] for v in cfg["families"].values()}
    if "items" not in roles:
        problems.append("no family has role `items`; conference programmes, papers or curated posts are the core "
                        "of the measurement")
    if not any(v.get("vendor") is False for v in cfg["families"].values() if v["role"] == "items"):
        warnings.append("no item family is marked independent of vendors (vendor: false); a topic can then never "
                        "be growing")
    bad = [k for k in (cfg.get("discovery") or {}) if k not in DISCOVERY_KINDS]
    if bad:
        problems.append(f"unknown discovery kinds {bad}; use {list(DISCOVERY_KINDS)}")
    if len(cfg["anchors"]) < 12:
        warnings.append(f"only {len(cfg['anchors'])} anchors; cover tools, concepts and practices (about 20)")
    if len(cfg["routes"]) < 3:
        warnings.append("fewer than three discovery routes; sources found by one route only cannot be cross-checked")
    summary = {"field": cfg["field"], "windows": cfg["windows"],
               "families": {f: f"{v['role']}, quota {v['quota']}" + (", vendor" if v.get("vendor") else "")
                            for f, v in cfg["families"].items()},
               "anchors": len(cfg["anchors"]), "routes": list(cfg["routes"]),
               "discovery": {k: v.get("min") for k, v in (cfg.get("discovery") or {}).items()},
               "collectors": {k: v["type"] for k, v in (cfg.get("collectors") or {}).items()}}
    return {"ok": not problems, "problems": problems, "warnings": warnings, **summary}
