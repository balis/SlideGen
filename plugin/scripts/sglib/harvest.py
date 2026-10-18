"""Field trends, stage 1: every item of every panel edition, classified as in scope or not, and candidate topics.

A forum or adoption source whose collector type is `records` is harvested here too: its records (posts of an
archive, systems of a ranked list, rows of a result list) come from its stored pages through a parser, as items
do, and stage 2 counts the records that name each topic. Records are not classified.

Layout, relative to the directory of the trends manifest:
  trends/parsers/<source>.py               the harvester's parser, kept so that the harvest can be run again
  trends/items/<source>.json               harvester output: every item (or record) of both editions
  trends/items_summary.md                  sg trends items-check
  trends/classify/<source>/batch_NN.json   blinded batches (sg trends classify-prep); map.json links them back
  trends/classify/<source>/batch_NN.labels.json, check.labels.json   classifier output
  trends/classified/<source>.json          in-scope and sponsored items per edition (sg trends classify-join)
  trends/terms.json|.md                    candidate terms (sg trends terms); terms_<source>.json|.md for one
                                           records source (sg trends terms --source)
  trends/topics.json                       topic-curator output; trends/matches.json (sg trends topics-check)
"""
from __future__ import annotations

import hashlib
import html
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

from .sources import _normalize
from .trends import _entries, _manifest, _texts, collector_of, page_origin
from .util import SgError, load_json, today, write_json

MIN_FOUND = 0.95          # share of item titles that must be found in the stored pages
COUNT_RANGE = (0.8, 1.25)  # harvested / verified item count, unless the edition explains the difference
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}")
UNMATCHED_EXAMPLES = 8    # records no topic names, shown by topics-check
MIN_TITLE = 8             # shorter titles cannot be checked against the page
COMPARABLE_TEXT = 0.8     # abstracts count only if this share of items in both editions has one
BATCH = 300
CHECK_SAMPLE = 40         # items per edition labelled again by a second classifier
MIN_KAPPA = 0.6
MIN_AGREEMENT = 0.85


def clean(text: str | None) -> str:
    """Text for matching: entities and percent-encoding decoded, hyphens, underscores, slashes and plus signs read
    as spaces, whitespace collapsed."""
    if not text:
        return ""
    text = unquote(html.unescape(text))
    return re.sub(r"\s+", " ", re.sub(r"[-_/+]", " ", text)).strip()


def _panel(cfg: dict) -> dict:
    """Panel sources that are selected or pending, by key."""
    path = cfg["_ws"] / "sources_panel.json"
    rows = load_json(path)["sources"]
    return {r["key"]: r for r in rows if r.get("selected") or r.get("pending")}


def families_with(cfg: dict, *roles: str) -> list[str]:
    """Families whose role is one of `roles` (items, forum, adoption), in manifest order."""
    return [f for f, v in cfg["families"].items() if v["role"] in roles]


def _item_sources(cfg: dict) -> dict:
    return {k: r for k, r in _panel(cfg).items() if r["family"] in families_with(cfg, "items")}


def records_sources(cfg: dict) -> dict:
    """Forum and adoption sources of the panel measured on records that a parser extracted from their stored
    pages (collector type `records`)."""
    return {k: r for k, r in _panel(cfg).items() if r["family"] not in families_with(cfg, "items")
            and (collector_of(cfg, r, k) or {}).get("type") == "records"}


def in_window(cfg: dict, row: dict, items: list[dict], edition: str) -> list[dict]:
    """The records of an edition that stage 2 counts. A forum's records count in the window their date falls in,
    so an archive page that spans a window boundary can be listed in both editions; a list's records all count."""
    if cfg["families"][row["family"]]["role"] != "forum":
        return items
    lo, hi = cfg["windows"][edition]
    return [i for i in items if lo <= (i.get("date") or "")[:10] <= hi]


def record_texts(cfg: dict, key: str) -> dict:
    """{edition: [text]} of the records stage 2 counts for a records source: the title, with the description when
    both editions have one."""
    row = _panel(cfg)[key]
    path = cfg["_ws"] / "items" / f"{key}.json"
    if not path.exists():
        raise SgError(f"trends/items/{key}.json is missing; harvest {key} in stage 1")
    doc = load_json(path, "trend_items")
    with_text = _comparable(cfg["_ws"]).get(key, False)
    return {ed: [clean(i["title"] + (" " + i["text"] if with_text and i.get("text") else ""))
                 for i in in_window(cfg, row, doc["editions"][ed]["items"], ed)] for ed in ("current", "previous")}


def _records_problems(cfg: dict, key: str, row: dict, edition: str, e: dict) -> tuple[list[str], dict]:
    """(problems, stats) of a records source's edition: a ranked list has every rank from 1 to the verified
    count once; a forum's records carry the day they were posted."""
    col, items, problems, stats = collector_of(cfg, row, key) or {}, e["items"], [], {}
    if col.get("ranked"):
        verified = ((row["verified"] or {}).get(edition) or {}).get("items")
        if {i["id"] for i in items} != {str(n) for n in range(1, (verified or 0) + 1)} or len(items) != verified:
            problems.append(f"{key} {edition}: a ranked list needs ids 1 to {verified}, each once; "
                            f"the file has {len(items)} records")
    if cfg["families"][row["family"]]["role"] == "forum":
        undated = [i["id"] for i in items if not DAY.match(i.get("date") or "")]
        if undated:
            problems.append(f"{key} {edition}: {len(undated)} records without a YYYY-MM-DD date, e.g. {undated[:3]}")
        stats["outside_window"] = len(items) - len(in_window(cfg, row, items, edition))
    return problems, stats


# ---------------------------------------------------------------- items


def parser_check(cfg: dict, key: str, doc: dict) -> tuple[list[str], list[str]]:
    """(problems, warnings) about the parser an items file names. The parser must be stored inside the manifest's
    directory and be unchanged since it wrote the file (`parser_sha256`). A file without a hash was written before
    parsers were kept and only gets a warning."""
    if not doc.get("parser_sha256"):
        return [], [f"{key}: the parser is not recorded with its hash, so the harvest cannot be run again; "
                    f"store it as trends/parsers/{key}.py"]
    root = cfg["_root"].resolve()
    path = Path(doc["parser"])
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root):
        return [f"{key}: parser {doc['parser']} is outside the project; store it as trends/parsers/{key}.py"], []
    if not path.exists():
        return [f"{key}: parser {doc['parser']} is missing"], []
    if hashlib.sha256(path.read_bytes()).hexdigest() != doc["parser_sha256"]:
        return [f"{key}: parser {doc['parser']} changed after it wrote the items; run it again"], []
    return [], []


def items_check(args) -> dict:
    """Check every harvested item and record list against its stored pages and the verified counts."""
    cfg = _manifest(args.manifest)
    ws, texts, entries = cfg["_ws"], _texts(cfg["_store"]), _entries(cfg["_store"])
    records = records_sources(cfg)
    sources = {**_item_sources(cfg), **records}
    summary, problems, warnings, missing = [], [], [], []
    for key, row in sorted(sources.items()):
        path = ws / "items" / f"{key}.json"
        if not path.exists():
            missing.append(key)
            continue
        doc = load_json(path, "trend_items")
        if doc["source"] != key:
            problems.append(f"{path.name}: source is {doc['source']}")
            continue
        bad, warn = parser_check(cfg, key, doc)
        problems += bad
        warnings += warn
        stats = {}
        for edition in ("current", "previous"):
            e = doc["editions"][edition]
            unknown = [p for p in e["pages"] if p not in texts]
            if unknown:
                problems.append(f"{key} {edition}: pages not in the store: {unknown}")
                continue
            warnings += [f"{key} {edition}: {note}" for p in e["pages"] if (note := page_origin(entries, p))]
            page = " ".join(_normalize(clean(texts[p].read_text(encoding="utf-8"))) for p in e["pages"])
            ids = [i["id"] for i in e["items"]]
            if len(ids) != len(set(ids)):
                problems.append(f"{key} {edition}: duplicate item ids")
            titles = Counter(_normalize(clean(i["title"])) for i in e["items"])
            dupes = sum(c - 1 for c in titles.values() if c > 1)
            checkable = [i for i in e["items"] if len(clean(i["title"])) >= MIN_TITLE]
            not_found = [i["title"] for i in checkable if _normalize(clean(i["title"])) not in page]
            found_share = 1 - len(not_found) / len(checkable) if checkable else 0.0
            verified = ((row["verified"] or {}).get(edition) or {}).get("items") or 0
            ratio = len(e["items"]) / verified if verified else None
            if found_share < MIN_FOUND:
                problems.append(f"{key} {edition}: {len(not_found)} of {len(checkable)} titles not in the stored "
                                f"pages, e.g. {not_found[:3]}")
            ranked = key in records and (collector_of(cfg, row, key) or {}).get("ranked")   # counted exactly below
            if ratio is not None and not COUNT_RANGE[0] <= ratio <= COUNT_RANGE[1] and not e.get("note") and not ranked:
                problems.append(f"{key} {edition}: {len(e['items'])} items against {verified} verified; "
                                f"explain the difference in the edition's note or fix the parser")
            with_text = sum(bool(clean(i.get("text"))) for i in e["items"]) / max(1, len(e["items"]))
            stats[edition] = {"items": len(e["items"]), "verified": verified, "found": round(found_share, 3),
                              "duplicate_titles": dupes, "with_text": round(with_text, 2), "note": e.get("note")}
            if key in records:
                bad, extra = _records_problems(cfg, key, row, edition, e)
                problems += bad
                stats[edition].update(extra)
        if len(stats) == 2:
            comparable = all(s["with_text"] >= COMPARABLE_TEXT for s in stats.values())
            summary.append({"source": key, "family": row["family"], "text_comparable": comparable, **{
                f"{ed}_{k}": v for ed, s in stats.items() for k, v in s.items()}})
    write_json(ws / "items_summary.json", {"generated_by": "sg trends items-check", "sources": summary,
                                           "missing": missing, "problems": problems, "warnings": warnings})
    lines = ["# Harvested items", "", f"Generated {today()} by `sg trends items-check`. Titles are checked against "
             "the stored pages; abstracts are used only when both editions have them.", "",
             "| Source | Family | Current | Previous | Found | Abstracts |", "|---|---|---|---|---|---|"]
    for s in summary:
        lines.append(f"| {s['source']} | {s['family']} | {s['current_items']} (verified {s['current_verified']}) | "
                     f"{s['previous_items']} (verified {s['previous_verified']}) | "
                     f"{min(s['current_found'], s['previous_found']):.0%} | "
                     f"{'both editions' if s['text_comparable'] else 'titles only'} |")
    outside = [f"{s['source']} ({s['current_outside_window']} current, {s['previous_outside_window']} previous)"
               for s in summary if s.get("current_outside_window") or s.get("previous_outside_window")]
    if outside:
        lines += ["", "Records dated outside their edition's window, not counted: " + "; ".join(outside)]
    if missing:
        lines += ["", f"Not harvested: {', '.join(missing)}"]
    if problems:
        lines += ["", "Problems:", *[f"- {p}" for p in problems]]
    if warnings:
        lines += ["", "Warnings:", *[f"- {w}" for w in warnings]]
    (ws / "items_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": not problems and not missing, "harvested": len(summary), "missing": missing,
            "problems": problems[:20], "warnings": warnings[:20], "out": str(ws / "items_summary.md")}


def _comparable(ws) -> dict:
    return {s["source"]: s["text_comparable"] for s in load_json(ws / "items_summary.json")["sources"]}


def _blind_id(key: str, edition: str, item_id: str) -> str:
    return hashlib.sha1(f"{key}|{edition}|{item_id}".encode()).hexdigest()[:10]


def _blind_item(item: dict, bid: str, with_text: bool) -> dict:
    text = clean(item.get("text"))[:400] if with_text else None
    return {"id": bid, "title": item["title"], "text": text or None, "presenter": item.get("presenter")}


# ---------------------------------------------------------------- classification


def classify_prep(args) -> dict:
    """Write blinded, shuffled batches (both editions mixed, no edition shown) and a check sample per source."""
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    summary = load_json(ws / "items_summary.json")
    if summary["problems"] or summary["missing"]:
        raise SgError("run `sg trends items-check` until it passes")
    comparable = _comparable(ws)
    out = {}
    for key in sorted(set(comparable) & set(_item_sources(cfg))):   # records are not classified
        doc = load_json(ws / "items" / f"{key}.json", "trend_items")
        rows, mapping = [], {}
        for edition in ("current", "previous"):
            for item in doc["editions"][edition]["items"]:
                bid = _blind_id(key, edition, item["id"])
                mapping[bid] = [edition, item["id"]]
                rows.append(_blind_item(item, bid, comparable[key]))
        rng = random.Random(key)
        rng.shuffle(rows)
        folder = ws / "classify" / key
        for n in range(0, len(rows), BATCH):
            write_json(folder / f"batch_{n // BATCH + 1:02d}.json",
                       {"batch": f"{key}-{n // BATCH + 1:02d}", "items": rows[n:n + BATCH]})
        sample = []
        for edition in ("current", "previous"):
            pool = [r for r in rows if mapping[r["id"]][0] == edition]
            sample += random.Random(f"{key}-check-{edition}").sample(pool, min(CHECK_SAMPLE, len(pool)))
        random.Random(f"{key}-check").shuffle(sample)
        write_json(folder / "check.json", {"batch": f"{key}-check", "items": sample})
        write_json(folder / "map.json", mapping)
        out[key] = {"items": len(rows), "batches": (len(rows) + BATCH - 1) // BATCH, "check": len(sample)}
    return {"ok": True, "sources": out}


def _kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    if not n:
        return 0.0
    agree = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if chance == 1 else (agree - chance) / (1 - chance)


def classify_join(args) -> dict:
    """Join the labels back to items, check completeness and agreement with the second classifier."""
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    families = {k: r["family"] for k, r in _item_sources(cfg).items()}
    results, problems = [], []
    for folder in sorted(p for p in (ws / "classify").iterdir() if (p / "map.json").exists()):
        key = folder.name
        mapping = load_json(folder / "map.json")
        labels = {}
        for path in sorted(folder.glob("batch_*.labels.json")):
            for lab in load_json(path, "trend_labels")["labels"]:
                if lab["id"] in labels:
                    problems.append(f"{key}: {lab['id']} labelled twice")
                labels[lab["id"]] = lab
        unknown = set(labels) - set(mapping)
        missing = set(mapping) - set(labels)
        if unknown or missing:
            problems.append(f"{key}: {len(missing)} items without a label, {len(unknown)} unknown ids")
            continue
        check_path = folder / "check.labels.json"
        if not check_path.exists():
            problems.append(f"{key}: check.labels.json missing")
            continue
        check = {lab["id"]: lab for lab in load_json(check_path, "trend_labels")["labels"]}
        sample = [lab["id"] for lab in load_json(folder / "check.json")["items"]]
        if set(sample) - set(check):
            problems.append(f"{key}: check sample not fully labelled")
            continue
        first = [labels[i]["in_scope"] for i in sample]
        second = [check[i]["in_scope"] for i in sample]
        agreement = sum(x == y for x, y in zip(first, second)) / len(sample)
        kappa = _kappa(first, second)
        editions = {"current": {"n": 0, "in_scope": [], "sponsored": []},
                    "previous": {"n": 0, "in_scope": [], "sponsored": []}}
        for bid, (edition, item_id) in mapping.items():
            e = editions[edition]
            e["n"] += 1
            if labels[bid]["in_scope"]:
                e["in_scope"].append(item_id)
            if labels[bid]["sponsored"]:
                e["sponsored"].append(item_id)
        drop_sponsored = bool(cfg["families"].get(families.get(key), {}).get("sponsor_filter"))
        for e in editions.values():
            e["measured"] = sorted(set(e["in_scope"]) - (set(e["sponsored"]) if drop_sponsored else set()))
        reliable = agreement >= MIN_AGREEMENT or kappa >= MIN_KAPPA
        write_json(ws / "classified" / f"{key}.json", {"source": key, "editions": editions,
                                                       "agreement": round(agreement, 3), "kappa": round(kappa, 3),
                                                       "reliable": reliable})
        results.append({"source": key, "agreement": agreement, "kappa": kappa, "reliable": reliable,
                        **{f"{ed}_{k}": len(v) if isinstance(v, list) else v
                           for ed, e in editions.items() for k, v in e.items()}})
    lines = ["# Classified items", "", f"Generated {today()} by `sg trends classify-join`. Measured items are in "
             "scope and, in families with a sponsor filter, not presented by a sponsor. Agreement compares the classifier with a second classifier "
             f"on {CHECK_SAMPLE} items per edition.", "",
             "| Source | Current: measured / all | Previous: measured / all | Sponsored (cur/prev) | Agreement | Kappa |",
             "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['source']} | {r['current_measured']} / {r['current_n']} | {r['previous_measured']} / "
                     f"{r['previous_n']} | {r['current_sponsored']} / {r['previous_sponsored']} | "
                     f"{r['agreement']:.0%} | {r['kappa']:.2f}{'' if r['reliable'] else ' (unreliable)'} |")
    if problems:
        lines += ["", "Problems:", *[f"- {p}" for p in problems]]
    (ws / "classified_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    unreliable = [r["source"] for r in results if not r["reliable"]]
    return {"ok": not problems and not unreliable, "sources": len(results), "unreliable": unreliable,
            "problems": problems[:20], "out": str(ws / "classified_summary.md")}


# ---------------------------------------------------------------- candidate terms and topics

STOPWORDS = set("""a an and are as at be by can do does for from has have how i in into is it its of on or our so
than that the their them then there these this to up us vs was we what when where which while who why will with
without you your using use used new via towards toward based part session talk keynote panel intro introduction
not more most all any one two three about across over under between beyond""".split())


def _selected_items(cfg: dict) -> dict:
    """Measured items of the selected item sources: {source: {edition: [(item, text)]}}."""
    ws = cfg["_ws"]
    rows = {r["key"]: r for r in load_json(ws / "sources_panel.json")["sources"] if r.get("selected")}
    comparable = _comparable(ws)
    out = {}
    for key, row in rows.items():
        if row["family"] not in families_with(cfg, "items"):
            continue
        cls = ws / "classified" / f"{key}.json"
        if not cls.exists():
            raise SgError(f"{key} is selected but not classified; run classify-join")
        measured = {ed: set(e["measured"]) for ed, e in load_json(cls)["editions"].items()}
        doc = load_json(ws / "items" / f"{key}.json", "trend_items")
        out[key] = {"family": row["family"], "editions": {}}
        for edition in ("current", "previous"):
            out[key]["editions"][edition] = [
                (i, clean(i["title"] + (" " + i["text"] if comparable.get(key) and i.get("text") else "")))
                for i in doc["editions"][edition]["items"] if i["id"] in measured[edition]]
    return out


def _grams(text: str) -> set[str]:
    """Words and phrases of 1 to 3 words that neither start nor end with a stopword."""
    words = re.findall(r"[a-z0-9][a-z0-9.#]*[a-z0-9#]|[a-z0-9]", text.lower())
    grams = set()
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            g = words[i:i + n]
            if g[0] in STOPWORDS or g[-1] in STOPWORDS or all(w.isdigit() or len(w) == 1 for w in g):
                continue
            grams.add(" ".join(g))
    return grams


def terms(args) -> dict:
    """Frequent words and phrases (1 to 3 words) in measured items, as raw material for the topic list; with
    `--source`, in the records of one records source, whose vocabulary the item sources may not share."""
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    source = getattr(args, "source", None)
    if source:
        if source not in records_sources(cfg):
            raise SgError(f"{source} is not a records source of the panel")
        data = {source: {"family": _panel(cfg)[source]["family"],
                         "editions": {ed: [(None, t) for t in texts] for ed, texts in record_texts(cfg, source).items()}}}
        name, min_sources, what = f"terms_{source}", 1, f"Records of {source}"
    else:
        data, name, min_sources, what = _selected_items(cfg), "terms", 2, "Measured items"
    df = defaultdict(lambda: {"current": 0, "previous": 0, "sources": set(), "families": set()})
    totals = {"current": 0, "previous": 0}
    for key, src in data.items():
        for edition, items in src["editions"].items():
            totals[edition] += len(items)
            for _, text in items:
                for g in _grams(text):
                    d = df[g]
                    d[edition] += 1
                    d["sources"].add(key)
                    d["families"].add(src["family"])
    rows = [{"term": t, "current": d["current"], "previous": d["previous"], "sources": len(d["sources"]),
             "families": sorted(d["families"])}
            for t, d in df.items() if d["current"] + d["previous"] >= 3 and len(d["sources"]) >= min_sources]
    rows.sort(key=lambda r: -(r["current"] + r["previous"]))
    rows = rows[:args.limit]
    write_json(ws / f"{name}.json", {"generated_by": "sg trends terms", "items": totals, "terms": rows})
    lines = [f"# Candidate terms ({len(rows)})", "", f"{what}: current {totals['current']}, previous "
             f"{totals['previous']}. Items containing the term per edition; sources and families where it occurs.",
             "", "term | current | previous | sources | families"]
    lines += [f"{r['term']} | {r['current']} | {r['previous']} | {r['sources']} | {','.join(r['families'])}"
              for r in rows]
    (ws / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "terms": len(rows), "items": totals, "out": str(ws / f"{name}.md")}


def _pattern(alias: str) -> re.Pattern:
    """Whole-word pattern for an alias; ALL-CAPS aliases match case-sensitively; a plural s is allowed."""
    norm = clean(alias)
    body = r"\s+".join(re.escape(w) for w in norm.split())
    flags = 0 if (re.search(r"[A-Za-z]", norm) and norm == norm.upper()) else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?:s|es)?(?![A-Za-z0-9])", flags)


def compile_topics(topics: list[dict]) -> dict:
    return {t["id"]: {"include": [_pattern(a) for a in t["aliases"]],
                      "exclude": [_pattern(x) for x in t.get("exclude", [])],
                      "literals": [clean(a).lower() for a in t["aliases"]]} for t in topics}


def compile_for(topics: list[dict], col: dict | None, default: str = "aliases") -> dict:
    """Patterns for the titles a collector counts: every alias, or only each topic's unambiguous qualified name
    (`match: qualified`), which suits a general forum where short aliases mean other things."""
    if (col or {}).get("match", default) == "qualified":
        topics = [{**t, "aliases": [t["qualified"]]} for t in topics]
    return compile_topics(topics)


def topic_matches(compiled: dict, text: str) -> list[str]:
    """Topics named in a cleaned text. A lowercase substring test, necessary for any alias match, skips the
    regular expressions for texts that cannot match."""
    low = text.lower()
    return [tid for tid, p in compiled.items()
            if any(lit in low for lit in p["literals"]) and any(r.search(text) for r in p["include"])
            and not any(r.search(text) for r in p["exclude"])]


def topics_check(args) -> dict:
    """Check the topic list (unique ids and aliases, every anchor covered) and match topics to measured items."""
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    topics = load_json(ws / "topics.json", "trend_topics")["topics"]
    problems = []
    ids = [t["id"] for t in topics]
    if len(ids) != len(set(ids)):
        problems.append("duplicate topic ids: " + ", ".join(sorted({i for i in ids if ids.count(i) > 1})))
    owner = {}
    for t in topics:
        for a in t["aliases"]:
            k = _normalize(clean(a))
            if k in owner and owner[k] != t["id"]:
                problems.append(f"alias '{a}' is in {owner[k]} and {t['id']}")
            owner[k] = t["id"]
    compiled = compile_topics(topics)
    for a in cfg.get("anchors", []):
        names = [a["name"]] + a.get("aliases", [])
        if not any(topic_matches(compiled, clean(n)) for n in names):
            problems.append(f"anchor '{a['name']}' is not covered by any topic")
    data = _selected_items(cfg)
    matches = defaultdict(lambda: defaultdict(lambda: {"current": [], "previous": []}))
    for key, src in data.items():
        for edition, items in src["editions"].items():
            for item, text in items:
                for tid in topic_matches(compiled, text):
                    matches[tid][key][edition].append(item["id"])
    write_json(ws / "matches.json", {"generated_by": "sg trends topics-check", "matches": matches})
    totals = {t["id"]: {ed: sum(len(m[ed]) for m in matches.get(t["id"], {}).values())
                        for ed in ("current", "previous")} for t in topics}
    rare = [t["id"] for t in topics if sum(totals[t["id"]].values()) < 3]
    unmatched = {}   # a record no topic names is not measured; a new product name shows up here
    for key, row in sorted(records_sources(cfg).items()):
        if not row.get("selected"):
            continue
        patterns = compile_for(topics, collector_of(cfg, row, key))
        texts = record_texts(cfg, key)["current"]
        none = [x for x in texts if not topic_matches(patterns, x)]
        unmatched[key] = {"records": len(texts), "unmatched": len(none),
                          "examples": [x for x, _ in Counter(none).most_common(UNMATCHED_EXAMPLES)]}
    lines = [f"# Topics ({len(topics)})", "", f"Generated {today()} by `sg trends topics-check`. Matches: measured "
             "items of the selected item sources that name the topic.", "",
             "| Topic | Kind | Aliases | Current | Previous |", "|---|---|---|---|---|"]
    for t in sorted(topics, key=lambda t: -sum(totals[t["id"]].values())):
        lines.append(f"| {t['name']} | {t['kind']} | {', '.join(t['aliases'][:6])} | {totals[t['id']]['current']} | "
                     f"{totals[t['id']]['previous']} |")
    if rare:
        lines += ["", f"Rare (fewer than 3 matches; measured mainly through forums and adoption): {', '.join(rare)}"]
    if unmatched:
        lines += ["", "Records of the current edition that no topic names (records sources):"]
        lines += [f"- {key}: {u['unmatched']} of {u['records']}" + (", e.g. " + "; ".join(u["examples"])
                                                                    if u["examples"] else "")
                  for key, u in unmatched.items()]
    if problems:
        lines += ["", "Problems:", *[f"- {p}" for p in problems]]
    (ws / "topics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": not problems, "topics": len(topics), "rare": len(rare), "problems": problems[:20],
            "unmatched_records": {k: u["unmatched"] for k, u in unmatched.items()}, "out": str(ws / "topics.md")}
