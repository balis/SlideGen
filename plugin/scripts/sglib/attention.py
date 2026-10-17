"""Field trends, stage 2: how attention to each topic changed between the two windows, per family.

Families with role `items` are measured on the classified items of stage 1. Families with role `forum` or
`adoption` are measured on data that a collector downloads once per window from a public API; each such source names
its collector (type and parameters) in the manifest's `collectors` or in its verification record:
  sg trends collect --source <key>    raw data under trends/queries/raw/<key>/ (resumable)
  sg trends attention                 trends/attention.json|.md

Within an item or forum family, each source gives a log ratio of a topic's share between the windows with its
variance; sources are combined with a DerSimonian-Laird random-effects model. Adoption sources are reported one by
one, because surveys, job postings and downloads measure different things.
"""
from __future__ import annotations

import email.header
import email.utils
import gzip
import html
import json
import mailbox
import math
import re
import statistics
import tempfile
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from .harvest import _selected_items, clean, compile_topics, families_with, topic_matches
from .sources import _normalize
from .trends import _entries, _manifest, _texts, page_origin
from .util import SgError, load_json, today, write_json

Z = 1.96
UA = {"User-Agent": "slidegen-field-trends/1.0 (research; contact via repository)"}
KIND = {"hn_stories": "posts", "reddit": "posts", "discourse": "topics", "mailman3": "threads",
        "stackexchange_tags": "questions", "hn_hiring": "job_postings", "itjobswatch": "job_ads", "pypi": "downloads",
        "stackoverflow_survey": "survey", "survey_table": "survey", "top500_list": "survey"}
SHARE_TABLES = ("survey_table", "top500_list")   # adoption read from a table in queries/<key>.json


def _ts(day: str, end: bool = False) -> int:
    d = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return int(d.timestamp()) + (86399 if end else 0)


def _get(url: str, params: dict | None = None, pause: float = 1.0, tries: int = 8) -> dict:
    """GET JSON with polite pacing and exponential backoff on rate limits and timeouts."""
    wait = pause
    for _ in range(tries):
        time.sleep(pause)
        try:
            r = requests.get(url, params=params, headers=UA, timeout=90)
            if r.status_code == 200:
                data = r.json()
                if not (isinstance(data, dict) and data.get("error")):
                    return data
        except (requests.RequestException, ValueError):
            pass
        wait *= 2
        time.sleep(wait)
    raise SgError(f"giving up on {url} {params}")


def collector_of(cfg: dict, row: dict | None, key: str) -> dict | None:
    """The collector of a source: the manifest's entry, else the one named in its verification record."""
    return (cfg.get("collectors") or {}).get(key) or ((row or {}).get("verified") or {}).get("collector")


# ---------------------------------------------------------------- collectors (raw data, once per window)


def _windows(cfg: dict) -> dict:
    return {"current": cfg["windows"]["current"], "previous": cfg["windows"]["previous"]}


def _hn_day(day: str, min_points: int) -> list[str]:
    """Titles of the stories with at least `min_points` posted on one day (split when a slice exceeds 1000 hits)."""
    titles, slices = [], [(0, 86400)]
    while slices:
        lo, hi = slices.pop()
        s = _ts(day) + lo
        data = _get("https://hn.algolia.com/api/v1/search", {
            "tags": "story", "hitsPerPage": 1000, "attributesToRetrieve": "title",
            "numericFilters": f"created_at_i>={s},created_at_i<{s + hi - lo},points>={min_points}"}, pause=0.1)
        if data["nbHits"] > 1000:
            mid = (lo + hi) // 2
            slices += [(lo, mid), (mid, hi)]
        else:
            titles += [h.get("title") or "" for h in data["hits"]]
    return titles


def _collect_hn_stories(cfg: dict, out, params: dict) -> dict:
    """All Hacker News stories above a score threshold, day by day, four requests at a time."""
    from concurrent.futures import ThreadPoolExecutor
    min_points = params.get("min_points", 5)
    counts = {}
    for edition, (start, end) in _windows(cfg).items():
        path = out / f"{edition}.jsonl"
        done = set()
        if path.exists():
            done = {json.loads(line)["day"] for line in path.open(encoding="utf-8")}
        first, last = date.fromisoformat(start).toordinal(), date.fromisoformat(end).toordinal()
        days = [date.fromordinal(d).isoformat() for d in range(first, last + 1)]
        todo = [d for d in days if d not in done]
        with path.open("a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=4) as pool:
            for day, titles in zip(todo, pool.map(lambda d: _hn_day(d, min_points), todo)):
                f.write(json.dumps({"day": day, "titles": titles}, ensure_ascii=False) + "\n")
                f.flush()
        counts[edition] = sum(len(json.loads(line)["titles"]) for line in path.open(encoding="utf-8"))
    return counts


def _collect_reddit(cfg: dict, out, params: dict) -> dict:
    """All post titles of one subreddit (Arctic Shift), week by week: long ranges time out on the server."""
    if not params.get("subreddit"):
        raise SgError("a reddit collector needs `subreddit`")
    counts = {}
    for edition, (start, end) in _windows(cfg).items():
        path, weeks_file = out / f"{edition}.jsonl", out / f"{edition}.weeks"
        seen = {json.loads(line)["id"] for line in path.open(encoding="utf-8")} if path.exists() else set()
        done = set(weeks_file.read_text().split()) if weeks_file.exists() else set()
        first, last = date.fromisoformat(start).toordinal(), date.fromisoformat(end).toordinal() + 1
        with path.open("a", encoding="utf-8") as f:
            for lo in range(first, last, 7):
                week = date.fromordinal(lo).isoformat()
                if week in done:
                    continue
                cursor = date.fromordinal(min(lo + 7, last)).isoformat()
                while True:
                    data = _get("https://arctic-shift.photon-reddit.com/api/posts/search", {
                        "subreddit": params["subreddit"], "after": week, "before": cursor, "limit": 100,
                        "sort": "desc", "fields": "id,created_utc,title"}, pause=0.7)["data"]
                    for p in data:
                        if p["id"] not in seen:
                            seen.add(p["id"])
                            f.write(json.dumps(p, ensure_ascii=False) + "\n")
                    if len(data) < 100:
                        break
                    cursor = min(p["created_utc"] for p in data)
                f.flush()
                with weeks_file.open("a") as w:
                    w.write(week + "\n")
        counts[edition] = len(seen)
    return counts


def _collect_discourse(cfg: dict, out, params: dict) -> dict:
    """Titles of the topics created in each window on one Discourse forum. The latest-topics list is ordered by last
    activity, so a topic created inside the windows appears before the first unpinned topic whose last activity
    predates them."""
    base = (params.get("url") or "").rstrip("/")
    if not base:
        raise SgError("a discourse collector needs `url`, the forum's base URL")
    windows = _windows(cfg)
    if all((out / f"{ed}.jsonl").exists() for ed in windows):
        return {ed: sum(1 for _ in (out / f"{ed}.jsonl").open(encoding="utf-8")) for ed in windows}
    first = min(start for start, _ in windows.values())
    topics, page = {}, 0
    while True:
        listing = _get(f"{base}/latest.json", {"no_definitions": "true", "page": page}, pause=1.0)["topic_list"]
        for t in listing["topics"]:
            topics[t["id"]] = t
        recent = [t for t in listing["topics"] if not t.get("pinned") and t["bumped_at"][:10] >= first]
        if not recent or not listing.get("more_topics_url"):
            break
        page += 1
    counts = {}
    for ed, (start, end) in windows.items():
        rows = sorted((t for t in topics.values() if start <= t["created_at"][:10] <= end),
                      key=lambda t: t["created_at"])
        with (out / f"{ed}.jsonl").open("w", encoding="utf-8") as f:
            for t in rows:
                f.write(json.dumps({"id": t["id"], "created_at": t["created_at"], "title": t["title"]},
                                   ensure_ascii=False) + "\n")
        counts[ed] = len(rows)
    return counts


def _mail_subject(message) -> str:
    """A message's subject, decoded and unfolded, without the list's bracketed tag."""
    subject = str(email.header.make_header(email.header.decode_header(message["Subject"] or "")))
    return re.sub(r"^\s*\[[^\]]*\]\s*", "", re.sub(r"\s+", " ", subject)).strip()


def _collect_mailman3(cfg: dict, out, params: dict) -> dict:
    """The thread-starting messages of one Mailman 3 list in each window, from HyperKitty's mbox export. A message
    starts a thread when it answers no other message; replies repeat the subject, so they are not counted."""
    archive = (params.get("archive") or "").rstrip("/")
    if not re.search(r"/list/[^/@]+@[^/]+$", archive):
        raise SgError("a mailman3 collector needs `archive`, the HyperKitty list URL ending in /list/<name>@<host>")
    name = archive.rsplit("/", 1)[1].split("@")[0]
    counts = {}
    for ed, (start, end) in _windows(cfg).items():
        path = out / f"{ed}.jsonl"
        if not path.exists():
            # the export's end date is exclusive
            after = date.fromordinal(date.fromisoformat(end).toordinal() + 1).isoformat()
            try:
                r = requests.get(f"{archive}/export/{name}.mbox.gz", params={"start": start, "end": after},
                                 headers=UA, timeout=300)
            except requests.RequestException as e:
                raise SgError(f"mbox export of {name} failed ({type(e).__name__}); run the collector again") from e
            if r.status_code != 200:
                raise SgError(f"mbox export of {name} answered {r.status_code}; run the collector again")
            with tempfile.TemporaryDirectory() as tmp:
                box_path = Path(tmp) / "list.mbox"
                box_path.write_bytes(gzip.decompress(r.content))
                rows = []
                for m in mailbox.mbox(str(box_path)):
                    sent = email.utils.parsedate_to_datetime(m["Date"]) if m["Date"] else None
                    day = sent.astimezone(timezone.utc).date().isoformat() if sent and sent.tzinfo else None
                    subject = _mail_subject(m)
                    if m["In-Reply-To"] or m["References"] or re.match(r"(re|aw|sv)\s*:", subject, re.I):
                        continue
                    if day and start <= day <= end:
                        rows.append({"id": (m["Message-ID"] or "").strip(), "date": day, "title": subject})
            with path.open("w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        counts[ed] = sum(1 for _ in path.open(encoding="utf-8"))
    return counts


def _collect_hiring(cfg: dict, out, params: dict) -> dict:
    """Top-level postings of every 'Ask HN: Who is hiring?' thread posted inside each window."""
    threads = _get("https://hn.algolia.com/api/v1/search_by_date", {
        "tags": "story,author_whoishiring", "query": "hiring", "hitsPerPage": 60})["hits"]
    threads = [t for t in threads if t["title"].lower().startswith("ask hn: who is hiring")]
    counts = {}
    for edition, (start, end) in _windows(cfg).items():
        path = out / f"{edition}.jsonl"
        if not path.exists():
            with path.open("w", encoding="utf-8") as f:
                for t in threads:
                    if _ts(start) <= t["created_at_i"] <= _ts(end, True):
                        item = _get(f"https://hn.algolia.com/api/v1/items/{t['objectID']}", pause=0.5)
                        for c in item.get("children", []):
                            if c.get("text"):
                                f.write(json.dumps({"thread": t["objectID"], "id": c["id"], "text": c["text"]},
                                                   ensure_ascii=False) + "\n")
        counts[edition] = sum(1 for _ in path.open(encoding="utf-8"))
    return counts


def _collect_se_tags(cfg: dict, out, params: dict) -> dict:
    """Questions per tag and window on one Stack Exchange site."""
    tags, site = params.get("tags") or [], params.get("site", "stackoverflow")
    if not tags:
        raise SgError("a stackexchange_tags collector needs `tags`")
    path = out / "tags.json"
    data = load_json(path) if path.exists() else {}
    for edition, (start, end) in _windows(cfg).items():
        for tag in tags:
            if tag in data.get(edition, {}):
                continue
            r = _get("https://api.stackexchange.com/2.3/questions", {
                "tagged": tag, "site": site, "fromdate": _ts(start), "todate": _ts(end, True),
                "pagesize": 1, "filter": "!nNPvSNVZJS"}, pause=0.5)
            data.setdefault(edition, {})[tag] = r["total"]
            write_json(path, data)
    return {ed: sum(v.values()) for ed, v in data.items()}


def _collect_pypi(cfg: dict, out, params: dict) -> dict:
    """Monthly downloads of a fixed package set (ClickPy, ClickHouse's public PyPI dataset)."""
    packages = params.get("packages") or []
    if not packages:
        raise SgError("a pypi collector needs `packages`")
    quoted = ",".join("'" + p.replace("'", "") + "'" for p in packages)
    start, end = cfg["windows"]["previous"][0], cfg["windows"]["current"][1]
    sql = (f"SELECT project, toStartOfMonth(date) AS month, sum(count) AS downloads FROM pypi.pypi_downloads_per_day "
           f"WHERE project IN ({quoted}) AND date >= '{start}' AND date <= '{end}' "
           f"GROUP BY project, month ORDER BY project, month FORMAT JSON")
    data = _get("https://sql-clickhouse.clickhouse.com/", {"user": "demo", "query": sql}, pause=0.5)
    write_json(out / "monthly.json", data["data"])
    return {"rows": len(data["data"])}


def _parse_itjw(page: str) -> dict | None:
    """Permanent UK job ads citing a skill, and their share of all ads: last 6 months and the same period a year
    earlier."""
    flat = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " | ", page)))
    jobs = re.search(r"Permanent jobs citing [^|]+\|[ |]*([\d,]+)[ |]+([\d,]+)", flat)
    share = re.search(r"As % of all permanent jobs in the UK[ |]+([\d.]+)%[ |]+([\d.]+)%", flat)
    period = re.search(r"6 months to[ |]+([^|]+?)[ |]+Same period", flat)
    if not (jobs and share):
        return None
    k1, k0 = (int(x.replace(",", "")) for x in jobs.groups())
    p1, p0 = (float(x) / 100 for x in share.groups())
    return {"current": k1, "previous": k0, "share_current": p1, "share_previous": p0,
            "period": period.group(1).strip() if period else None}


def _itjw_page(skill: str, cache) -> str:
    """The skill's IT Jobs Watch page, cached in `cache`; empty when the board has no page for the skill. A failed
    request is not cached, so running the collector again retries it."""
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    time.sleep(2.0)
    url = f"https://www.itjobswatch.co.uk/jobs/uk/{requests.utils.quote(skill.lower())}.do"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (research)"}, timeout=60)
    except requests.RequestException as e:
        raise SgError(f"IT Jobs Watch request for {skill!r} failed ({type(e).__name__}); "
                      f"run the collector again to resume") from e
    if r.status_code in (404, 410):
        text = ""
    elif r.status_code == 200:
        text = r.text
    else:
        raise SgError(f"IT Jobs Watch answered {r.status_code} for {skill!r}; run the collector again to resume")
    cache.write_text(text, encoding="utf-8")
    return text


def _collect_itjw(cfg: dict, out, params: dict, key: str = "it-jobs-watch") -> dict:
    """IT Jobs Watch page of every skill named by a topic; per-topic results go to queries/<key>.json."""
    topics = load_json(cfg["_ws"] / "topics.json", "trend_topics")["topics"]
    result, missing = {}, []
    for t in topics:
        if not t.get("job_skills"):
            continue
        names, seen = [], set()   # the curator's skill names first, then the topic's own names
        for n in t["job_skills"] + [t["name"], t["qualified"]] + t["aliases"][:4]:
            if n.lower() not in seen:
                seen.add(n.lower())
                names.append(n)
        for skill in names:
            cache = out / (re.sub(r"[^a-z0-9]+", "-", skill.lower()) + ".html")
            parsed = _parse_itjw(_itjw_page(skill, cache))
            if parsed is None:
                continue
            n1, n0 = parsed["current"] / parsed["share_current"], parsed["previous"] / parsed["share_previous"]
            y, v = log_ratio(parsed["current"], round(n1), parsed["previous"], round(n0))
            result[t["id"]] = {**parsed, "skill": skill, "_y": y, "_v": v}
            break   # the first name that has a page represents the topic
        else:
            missing.append(t["id"])
    # The board's total of ads changes between periods, which moves every share alike; compare each skill with
    # the median change of all skills measured here, as for downloads.
    baseline = statistics.median(r["_y"] for r in result.values()) if result else 0.0
    for r in result.values():
        y, v = r.pop("_y") - baseline, r.pop("_v")
        r["relative_change"] = round(math.exp(y), 2)
        r["direction"] = direction({"log_ratio": y, "low": y - Z * math.sqrt(v), "high": y + Z * math.sqrt(v)})
    write_json(cfg["_ws"] / "queries" / f"{key}.json", {"generated_by": "sg trends collect",
                                                         "median_change_of_all_skills": round(math.exp(baseline), 2),
                                                         "topics": result, "topics_without_page": missing})
    return {"topics": len(result), "topics_without_page": missing}


def _top500_pages(cfg: dict, params: dict, row: dict | None) -> dict:
    """{edition: [fetched id]} of the stored list pages: the collector's `pages`, else the verification record's
    page and its more_pages."""
    if params.get("pages"):
        return {ed: list(params["pages"][ed]) for ed in ("current", "previous")}
    v = (row or {}).get("verified") or {}
    if not all(v.get(ed, {}).get("fetched") for ed in ("current", "previous")):
        raise SgError("a top500_list collector needs `pages` ({current: [ids], previous: [ids]}) or a verification "
                      "record with the fetched list pages")
    return {ed: [v[ed]["fetched"]] + [p["fetched"] for p in v[ed].get("more_pages", [])]
            for ed in ("current", "previous")}


def _top500_count(cfg: dict, pages: dict) -> dict:
    from .top500 import count
    raw = cfg["_store"] / "raw"
    missing = [i for ids in pages.values() for i in ids if not (raw / f"{i}.html").exists()]
    if missing:
        raise SgError(f"list pages not in the store: {missing}")
    return {ed: count([(raw / f"{i}.html").read_text(encoding="utf-8") for i in ids]) for ed, ids in pages.items()}


def _top500_table(key: str, pages: dict, counts: dict, row: dict | None) -> dict:
    """The counts as a survey table. A list counts every system, so an answer seen in one edition only has 0
    systems in the other, and that 0 is written."""
    from .top500 import ANY_ACCELERATOR
    names = sorted(set(counts["current"]["counts"]) | set(counts["previous"]["counts"]),
                   key=lambda n: (-counts["current"]["counts"].get(n, 0), n))
    v = (row or {}).get("verified") or {}
    editions = {}
    for ed, c in counts.items():
        k = c["counts"]
        editions[ed] = {"fetched": pages[ed], **({"period": v[ed]["period"]} if v.get(ed, {}).get("period") else {}),
                        "systems": c["systems"], "unmapped": c["unmapped"],
                        "rows": [{"name": n, "percent": round(100 * k.get(n, 0) / c["systems"], 1),
                                  "count": k.get(n, 0)} for n in names]}
    return {"source": key, "question": "Which processor, accelerator and interconnect does each listed system use?",
            "population": f"the systems of the list; '{ANY_ACCELERATOR}' counts systems with any accelerator; a "
                          "system with two models or families counts once for each",
            "editions": editions}


def _collect_top500(cfg: dict, out, params: dict, key: str, row: dict | None) -> dict:
    """Systems per processor family, accelerator model and interconnect family in each edition's stored list
    pages; the table goes to queries/<key>.json and `sg trends survey-check` recounts it."""
    pages = _top500_pages(cfg, params, row)
    counts = _top500_count(cfg, pages)
    if any(c["systems"] == 0 for c in counts.values()):
        raise SgError("no systems found in the stored list pages; are they TOP500 list pages?")
    write_json(cfg["_ws"] / "queries" / f"{key}.json", _top500_table(key, pages, counts, row))
    return {ed: {"systems": c["systems"], "answers": len(c["counts"]), "unmapped": c["unmapped"]}
            for ed, c in counts.items()}


def _collect_nothing(cfg: dict, out, params: dict) -> dict:
    return {"note": "this source is read from stored pages or an extracted table; nothing to download"}


COLLECTORS = {"hn_stories": _collect_hn_stories, "reddit": _collect_reddit, "discourse": _collect_discourse,
              "mailman3": _collect_mailman3, "hn_hiring": _collect_hiring,
              "stackexchange_tags": _collect_se_tags, "pypi": _collect_pypi, "itjobswatch": _collect_itjw,
              "top500_list": _collect_top500,
              "stackoverflow_survey": _collect_nothing, "survey_table": _collect_nothing}


def collect(args) -> dict:
    """Download the raw data of one forum or adoption source for both windows (resumable)."""
    cfg = _manifest(args.manifest)
    rows = {r["key"]: r for r in load_json(cfg["_ws"] / "sources_panel.json")["sources"]}
    col = collector_of(cfg, rows.get(args.source), args.source)
    if not col:
        raise SgError(f"{args.source} names no collector (manifest `collectors` or its verification record)")
    out = cfg["_ws"] / "queries" / "raw" / args.source
    out.mkdir(parents=True, exist_ok=True)
    fn = COLLECTORS[col["type"]]
    extra = {"key": args.source} if col["type"] == "itjobswatch" else \
        {"key": args.source, "row": rows.get(args.source)} if col["type"] == "top500_list" else {}
    return {"ok": True, "source": args.source, "type": col["type"], "collected": fn(cfg, out, col, **extra)}


# ---------------------------------------------------------------- statistics


def log_ratio(k1: int, n1: int, k0: int, n0: int) -> tuple[float, float]:
    """Log ratio of shares k1/n1 to k0/n0 and its variance, with 0.5 added to every count."""
    y = math.log((k1 + 0.5) / (n1 + 0.5)) - math.log((k0 + 0.5) / (n0 + 0.5))
    v = 1 / (k1 + 0.5) - 1 / (n1 + 0.5) + 1 / (k0 + 0.5) - 1 / (n0 + 0.5)
    return y, v


def random_effects(ys: list[float], vs: list[float]) -> dict:
    """DerSimonian-Laird random-effects estimate with a 95% interval."""
    w = [1 / v for v in vs]
    fixed = sum(wi * yi for wi, yi in zip(w, ys)) / sum(w)
    q = sum(wi * (yi - fixed) ** 2 for wi, yi in zip(w, ys))
    c = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (q - (len(ys) - 1)) / c) if len(ys) > 1 and c > 0 else 0.0
    ws = [1 / (v + tau2) for v in vs]
    est = sum(wi * yi for wi, yi in zip(ws, ys)) / sum(ws)
    se = math.sqrt(1 / sum(ws))
    return {"log_ratio": est, "low": est - Z * se, "high": est + Z * se, "tau2": tau2, "sources": len(ys)}


def direction(est: dict | None) -> str:
    if est is None:
        return "not measured"
    if est["low"] > 0:
        return "up"
    if est["high"] < 0:
        return "down"
    return "flat"


# ---------------------------------------------------------------- visibility


def _names(topic: dict) -> set[str]:
    return {_normalize(clean(x)) for x in [topic["name"], topic["qualified"]] + topic["aliases"]}


def _visible(cfg: dict, source: dict, topic: dict) -> tuple[bool, str | None]:
    """Whether a source can measure a topic: not its own topic, not a competitor's product at a vendor event, and
    inside its declared partial view."""
    key = source["key"]
    own = {_normalize(clean(x)) for x in (cfg.get("own_topics") or {}).get(key, [])}
    organiser = source.get("organiser", "").lower()
    if own & _names(topic) or (topic.get("vendor") and topic["vendor"].lower() in organiser):
        return False, "own topic"
    if (cfg.get("families") or {}).get(source["family"], {}).get("vendor") is True and topic.get("vendor"):
        return False, "competitor's product"
    view = (cfg.get("sees_only") or {}).get(key)
    if isinstance(view, dict) and view.get("foundation"):
        if topic["kind"] not in ("concept", "practice") and topic.get("foundation") != view["foundation"]:
            return False, "outside the source's view"
    return True, None


# ---------------------------------------------------------------- measurement per source


def _item_counts(cfg: dict, topics: list[dict]) -> dict:
    """{source: {"family", "n": {ed: n}, "k": {topic: {ed: k}}, "orgs": {topic: {ed: set}}}} for item sources."""
    ws = cfg["_ws"]
    matches = load_json(ws / "matches.json")["matches"]
    data = _selected_items(cfg)
    out = {}
    for key, src in data.items():
        presenters = {ed: {i["id"]: i.get("presenter") for i, _ in items} for ed, items in src["editions"].items()}
        entry = {"family": src["family"], "n": {ed: len(items) for ed, items in src["editions"].items()},
                 "k": {}, "orgs": {}}
        for t in topics:
            m = matches.get(t["id"], {}).get(key, {"current": [], "previous": []})
            entry["k"][t["id"]] = {ed: len(m.get(ed, [])) for ed in ("current", "previous")}
            entry["orgs"][t["id"]] = {ed: sorted({o.strip() for i in m.get(ed, []) if presenters[ed].get(i)
                                                  for o in presenters[ed][i].split(",") if o.strip()})
                                      for ed in ("current", "previous")}
        out[key] = entry
    return out


def _local_counts(texts: dict, compiled: dict) -> tuple[dict, dict]:
    n = {ed: len(t) for ed, t in texts.items()}
    k = defaultdict(lambda: {"current": 0, "previous": 0})
    for ed, rows in texts.items():
        for text in rows:
            for tid in topic_matches(compiled, text):
                k[tid][ed] += 1
    return n, k


def _raw(cfg, key):
    return cfg["_ws"] / "queries" / "raw" / key


def _count_hn_stories(cfg, key, col, topics):
    texts = {ed: [clean(t) for line in (_raw(cfg, key) / f"{ed}.jsonl").open(encoding="utf-8")
                  for t in json.loads(line)["titles"]] for ed in ("current", "previous")}
    # general forum: match the unambiguous qualified name only
    compiled = compile_topics([{**t, "aliases": [t["qualified"]], "exclude": t.get("exclude", [])} for t in topics])
    return _local_counts(texts, compiled)


def _count_titles(cfg, key, col, topics):
    """Posts, topics or threads by title (reddit, discourse, mailman3), matched on every alias."""
    texts = {ed: [clean(json.loads(line)["title"]) for line in (_raw(cfg, key) / f"{ed}.jsonl").open(encoding="utf-8")]
             for ed in ("current", "previous")}
    return _local_counts(texts, compile_topics(topics))


def _count_hiring(cfg, key, col, topics):
    texts = {ed: [clean(re.sub(r"<[^>]+>", " ", html.unescape(json.loads(line)["text"])))
                  for line in (_raw(cfg, key) / f"{ed}.jsonl").open(encoding="utf-8")] for ed in ("current", "previous")}
    return _local_counts(texts, compile_topics(topics))


def _count_se_tags(cfg, key, col, topics):
    """Questions with the topic's tags, as a share of all questions with the source's tags. Topics without a tag in
    the set are not measured here."""
    data = load_json(_raw(cfg, key) / "tags.json")
    n = {ed: sum(v.values()) for ed, v in data.items()}
    k = {}
    for t in topics:
        tags = [x for x in t.get("tags", []) if x in data["current"]]
        if tags:
            k[t["id"]] = {ed: sum(data[ed][x] for x in tags) for ed in ("current", "previous")}
    return n, k


COUNTERS = {"hn_stories": _count_hn_stories, "reddit": _count_titles, "discourse": _count_titles,
            "mailman3": _count_titles, "hn_hiring": _count_hiring,
            "stackexchange_tags": _count_se_tags}


def _survey_shares(cfg, key, col, row) -> tuple[dict, dict]:
    """Share of respondents (or listed systems) per answer in the current and previous edition."""
    if col["type"] in SHARE_TABLES:   # written by a survey-extractor or the top500_list collector; sg trends survey-check
        table = load_json(cfg["_ws"] / "queries" / f"{key}.json", "trend_survey_table")["editions"]
        return ({r["name"]: r["percent"] for r in table[ed]["rows"]} for ed in ("current", "previous"))
    texts = _texts(cfg["_store"])   # stackoverflow_survey: the survey's 'Full data' page and an extracted chart
    v = row["verified"]
    block = texts[v["current"]["fetched"]].read_text(encoding="utf-8").split("Respondents\nPercent\n", 1)[-1]
    current = {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r"([^\n]+)\n[\d,]+\n([\d.]+)%", block)}
    prev = json.loads(texts[v["previous"]["fetched"]].read_text(encoding="utf-8"))
    previous = {d["name"]: float(d["percent"].rstrip("%")) for d in prev["databases"]}
    return current, previous


def _survey(cfg, key, col, row, topics):
    """A topic's share is the sum of its answers' shares. An answer printed in one edition only was added to or
    dropped from the survey, so it is skipped rather than counted as 0% in the other edition."""
    current, previous = _survey_shares(cfg, key, col, row)
    out = {}
    for t in topics:
        names = [x for x in t.get("survey_names", []) if x in current and x in previous]
        skipped = [x for x in t.get("survey_names", []) if (x in current) != (x in previous)]
        if names:
            c, p = round(sum(current[x] for x in names), 1), round(sum(previous[x] for x in names), 1)
            delta = c - p
            out[t["id"]] = {"current": c, "previous": p, "delta_pp": round(delta, 1),
                            "direction": "up" if delta >= 1 else "down" if delta <= -1 else "flat",
                            **({"skipped": skipped} if skipped else {})}
    return out


def _pypi(cfg, key, col, topics):
    """Each topic's representative package: mean log monthly downloads per window against the package set."""
    rows = load_json(_raw(cfg, key) / "monthly.json")
    series = defaultdict(dict)
    for r in rows:
        series[r["project"]][r["month"][:7]] = int(r["downloads"])
    (ps, pe), (cs, ce) = cfg["windows"]["previous"], cfg["windows"]["current"]
    full = lambda s, e, m: s[:7] < m < e[:7]   # whole months inside the window
    change = {}
    for pkg, months in series.items():
        prev = [math.log(v) for m, v in months.items() if full(ps, pe, m) and v > 0]
        cur = [math.log(v) for m, v in months.items() if full(cs, ce, m) and v > 0]
        if len(prev) >= 3 and len(cur) >= 3:
            burst = max(months.values()) / max(1, min(months.values())) > 10
            change[pkg] = {"d": statistics.mean(cur) - statistics.mean(prev),
                           "v": statistics.variance(cur) / len(cur) + statistics.variance(prev) / len(prev),
                           "burst": burst}
    baseline = statistics.median(c["d"] for c in change.values())
    out = {}
    for t in topics:
        pkgs = [p for p in t.get("packages", []) if p in change]
        if pkgs:
            c = change[pkgs[0]]
            rel = c["d"] - baseline
            se = math.sqrt(c["v"])
            est = {"log_ratio": rel, "low": rel - Z * se, "high": rel + Z * se}
            out[t["id"]] = {"package": pkgs[0], "relative_growth": round(math.exp(rel), 2),
                            "direction": "flat (bursty)" if c["burst"] else direction(est), "burst": c["burst"]}
    return out


def _adoption(cfg, key, col, row, topics, counts) -> dict:
    """One adoption source's result per topic."""
    kind = KIND[col["type"]]
    if col["type"] in ("stackoverflow_survey",) + SHARE_TABLES:
        values = _survey(cfg, key, col, row, topics)
    elif col["type"] == "pypi":
        values = _pypi(cfg, key, col, topics)
    elif col["type"] == "itjobswatch":
        path = cfg["_ws"] / "queries" / f"{key}.json"
        if not path.exists():
            raise SgError(f"queries/{key}.json missing; run `sg trends collect --source {key}`")
        values = load_json(path)["topics"]
    else:   # counts of postings or posts: log ratio of shares
        n, k = counts
        values = {}
        for t in topics:
            c = k.get(t["id"], {"current": 0, "previous": 0})
            if c["current"] + c["previous"]:
                y, v = log_ratio(c["current"], n["current"], c["previous"], n["previous"])
                est = {"log_ratio": y, "low": y - Z * math.sqrt(v), "high": y + Z * math.sqrt(v)}
                values[t["id"]] = {**c, "direction": direction(est)}
    return {tid: {**v, "kind": kind} for tid, v in values.items()}


# ---------------------------------------------------------------- report


def attention(args) -> dict:
    cfg = _manifest(args.manifest)
    ws = cfg["_ws"]
    topics = load_json(ws / "topics.json", "trend_topics")["topics"]
    panel = {r["key"]: r for r in load_json(ws / "sources_panel.json")["sources"] if r.get("selected")}
    per_source = {key: {"family": e["family"], "n": e["n"], "k": e["k"], "orgs": e["orgs"]}
                  for key, e in _item_counts(cfg, topics).items()}
    measured_families = families_with(cfg, "items", "forum")
    adoption_sources = [k for k, r in panel.items() if r["family"] in families_with(cfg, "adoption")]
    missing_raw, adoption, labels = [], {}, {}
    for key, row in panel.items():
        if row["family"] in families_with(cfg, "items"):
            continue
        col = collector_of(cfg, row, key)
        if not col:
            missing_raw.append(f"{key}: no collector")
            continue
        labels[key] = col.get("label") or row["name"]
        try:
            counts = COUNTERS[col["type"]](cfg, key, col, topics) if col["type"] in COUNTERS else None
            if key in adoption_sources:
                adoption[key] = _adoption(cfg, key, col, row, topics, counts)
            elif counts is None:
                raise SgError(f"collector type {col['type']} cannot measure a {row['family']} family")
            else:
                n, k = counts
                # a tag-based source measures only topics with a tag in its set; others are not measured there
                per_source[key] = {"family": row["family"], "n": n, "k": dict(k), "orgs": {},
                                   "partial": col["type"] == "stackexchange_tags"}
        except (SgError, FileNotFoundError, KeyError) as e:
            missing_raw.append(f"{key}: {e}")
    independent = {f for f in measured_families if cfg["families"][f].get("vendor") is not True}
    result = {}
    for t in topics:
        fam_est, detail = {}, {}
        for fam in measured_families:
            ys, vs, rows = [], [], []
            for key, src in per_source.items():
                if src["family"] != fam or key not in panel:
                    continue
                ok, why = _visible(cfg, panel[key], t)
                if src.get("partial") and t["id"] not in src["k"]:
                    ok, why = False, "no tag in the source's tag set"
                k = src["k"].get(t["id"], {"current": 0, "previous": 0})
                if not ok:
                    rows.append({"source": key, "measured": False, "why": why})
                    continue
                y, v = log_ratio(k["current"], src["n"]["current"], k["previous"], src["n"]["previous"])
                ys.append(y)
                vs.append(v)
                rows.append({"source": key, "measured": True, "current": k["current"], "previous": k["previous"],
                             "n_current": src["n"]["current"], "n_previous": src["n"]["previous"],
                             "orgs_current": len(src["orgs"].get(t["id"], {}).get("current", []))})
            mentions = sum(r.get("current", 0) + r.get("previous", 0) for r in rows if r["measured"])
            est = random_effects(ys, vs) if ys and mentions > 0 else None
            share = (sum(r["current"] for r in rows if r["measured"]) /
                     max(1, sum(r["n_current"] for r in rows if r["measured"]))) if ys else None
            fam_est[fam] = {"direction": direction(est) if ys else "not measured", "estimate": est,
                            "share_current": share, "mentions": mentions}
            detail[fam] = rows
        up = [f for f, e in fam_est.items() if e["direction"] == "up"]
        down = [f for f, e in fam_est.items() if e["direction"] == "down"]
        measured = [f for f, e in fam_est.items() if e["direction"] != "not measured" and e["mentions"] > 0]
        independent_up = [f for f in up if f in independent]
        if up and down:
            verdict = "mixed"
        elif len(up) >= 2 and independent_up:
            verdict = "growing"
        elif len(down) >= 2:
            verdict = "declining"
        elif len(independent_up) == 1:
            verdict = "rising in one family"
        elif down:
            verdict = "falling in one family"
        elif len(measured) >= 2:
            verdict = "steady"
        else:
            verdict = "too little evidence"
        result[t["id"]] = {"name": t["name"], "kind": t["kind"], "verdict": verdict, "families": fam_est,
                           "detail": detail,
                           "orgs_current": sorted({o for key, src in per_source.items()
                                                   for o in src["orgs"].get(t["id"], {}).get("current", [])}),
                           "adoption": {key: {**vals[t["id"]], "label": labels[key]}
                                        for key, vals in adoption.items() if t["id"] in vals}}
    write_json(ws / "attention.json", {"generated_by": "sg trends attention", "topics": result,
                                       "sources": {k: {"family": v["family"], "n": v["n"]} for k, v in
                                                   per_source.items()},
                                       "adoption_sources": {k: labels[k] for k in adoption}})
    _render(cfg, result, per_source, measured_families, [k for k in adoption_sources if k in adoption], labels)
    counts = defaultdict(int)
    for r in result.values():
        counts[r["verdict"]] += 1
    return {"ok": not missing_raw, "topics": len(result), "verdicts": dict(counts), "missing": missing_raw,
            "out": str(ws / "attention.md")}


ARROW = {"up": "↑", "down": "↓", "flat": "→", "not measured": "·"}
ORDER = ["growing", "rising in one family", "mixed", "steady", "falling in one family", "declining",
         "too little evidence"]


def adoption_cell(a: dict, short: bool = True) -> str:
    """One adoption value as a short table cell or a sentence fragment."""
    if a["kind"] == "survey":
        return f"{a['current']:.1f}% ({a['delta_pp']:+.1f} pp)" if short else \
            f"{a['label']} {a['current']:.1f}% of respondents ({a['delta_pp']:+.1f} pp)"
    if a["kind"] == "downloads":
        return f"{a['relative_growth']}× {ARROW.get(a['direction'], '~')}" if short else \
            f"{a['label']} {a['relative_growth']}× the package set ({a['direction']})"
    if a["kind"] == "job_ads":
        if short:
            return ARROW.get(a["direction"], "·")
        weak = " (small base)" if min(a["current"], a["previous"]) < 50 else ""
        return (f"{a['label']} {a['previous']} → {a['current']} ({a['share_current']:.2%} of ads), growth "
                f"{a.get('relative_change', '?')}× the median skill's ({a['direction']}){weak}")
    return ARROW.get(a["direction"], "·") if short else f"{a['label']} {a['direction']}"


def _render(cfg, result, per_source, families, adoption_sources, labels):
    ws = cfg["_ws"]
    fam_label = {f: cfg["families"][f].get("label", f) for f in families}
    vendor = [fam_label[f] for f in families if cfg["families"][f].get("vendor") is True]
    lines = [f"# Attention: {cfg['field']}", "",
             f"Generated {today()} by `sg trends attention`. Change in each topic's share of measured items between "
             f"the previous window ({cfg['windows']['previous'][0]} to {cfg['windows']['previous'][1]}) and the "
             f"current window ({cfg['windows']['current'][0]} to {cfg['windows']['current'][1]}), per family: ↑ and "
             "↓ when the 95% interval of the combined change excludes no change, → otherwise, · when no source in "
             "the family can measure the topic. Sources within a family are combined with a random-effects model. "
             "Growing: up in at least two families, at least one of them independent of vendors"
             + (f" (not {', '.join(vendor)})" if vendor else "") + ", and down in none. "
             "Adoption sources are reported one by one.", "",
             "Sources: " + "; ".join(f"{k} ({v['family']}: {v['n']['previous']} → {v['n']['current']})"
                                     for k, v in sorted(per_source.items())), ""]
    for verdict in ORDER:
        group = [(tid, r) for tid, r in result.items() if r["verdict"] == verdict]
        if not group:
            continue
        group.sort(key=lambda x: -sum((e["share_current"] or 0) for e in x[1]["families"].values()))
        lines += [f"## {verdict.capitalize()} ({len(group)})", "",
                  "| Topic | " + " | ".join(fam_label[f] for f in families) +
                  "".join(f" | {labels[k]}" for k in adoption_sources) + " |",
                  "|---|" + "---|" * (len(families) + len(adoption_sources))]
        for tid, r in group:
            cells = []
            for f in families:
                e = r["families"][f]
                if e["direction"] == "not measured":
                    cells.append("·")
                    continue
                ratio = math.exp(e["estimate"]["log_ratio"]) if e["estimate"] else None
                cells.append(f"{ARROW[e['direction']]} {ratio:.1f}×" if ratio else "→ 0")
            cells += [adoption_cell(r["adoption"][k]) if k in r["adoption"] else "·" for k in adoption_sources]
            lines.append(f"| {r['name']} | " + " | ".join(cells) + " |")
        lines.append("")
    (ws / "attention.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _number_forms(x: float) -> set[str]:
    """How a percentage may be printed: 57.9, 57,9, 58 (rounded)."""
    text = f"{x:.2f}".rstrip("0").rstrip(".")
    return {text, text.replace(".", ","), str(round(x))}


def _top500_check(cfg: dict, key: str, col: dict, row: dict | None, table: dict) -> dict:
    """Recount the stored list pages and compare with the table: same pages, every page full, every rank once,
    every system with a processor and an interconnect, and the same count for every answer."""
    problems, stats = [], {}
    pages = _top500_pages(cfg, col, row)
    counts = _top500_count(cfg, pages)
    expected = _top500_table(key, pages, counts, row)
    per_page = col.get("systems_per_page", 100)
    for ed, c in counts.items():
        e = table["editions"][ed]
        if e["fetched"] != pages[ed]:
            problems.append(f"{ed}: the table was counted on pages {e['fetched']}, the source names {pages[ed]}")
        short = [(pid, n) for pid, n in zip(pages[ed], c["per_page"]) if n != per_page]
        if short:
            problems.append(f"{ed}: pages without {per_page} systems: {short}")
        if c["ranks"] != list(range(1, c["systems"] + 1)):
            problems.append(f"{ed}: ranks are not 1 to {c['systems']}, each once")
        for what in ("processor", "interconnect"):
            if c[f"without_{what}"]:
                problems.append(f"{ed}: no {what} recognised for ranks {c[f'without_{what}']}")
        if c["unknown"]:
            problems.append(f"{ed}: parts no rule classifies: {c['unknown']}")
        got = {r["name"]: r.get("count") for r in e["rows"]}
        want = {r["name"]: r["count"] for r in expected["editions"][ed]["rows"]}
        diff = sorted(n for n in set(got) | set(want) if got.get(n) != want.get(n))
        if diff:
            problems.append(f"{ed}: {len(diff)} answers differ from a recount, e.g. "
                            f"{[(n, got.get(n), want.get(n)) for n in diff[:3]]}; run `sg trends collect` again")
        stats[ed] = {"systems": c["systems"], "answers": len(want), "differ": len(diff), "unmapped": c["unmapped"]}
    return {"ok": not problems, "source": key, "editions": stats, "problems": problems}


def survey_check(args) -> dict:
    """Check a survey table: every answer and its percentage appear in the edition's stored pages, or, for a
    top500_list source, a recount of the stored list pages gives the same table."""
    cfg = _manifest(args.manifest)
    path = cfg["_ws"] / "queries" / f"{args.source}.json"
    table = load_json(path, "trend_survey_table")
    panel = cfg["_ws"] / "sources_panel.json"
    row = {r["key"]: r for r in load_json(panel)["sources"]}.get(args.source) if panel.exists() else None
    col = collector_of(cfg, row, args.source) or {}
    if col.get("type") == "top500_list":
        return _top500_check(cfg, args.source, col, row, table)
    texts, entries = _texts(cfg["_store"]), _entries(cfg["_store"])
    problems, warnings, stats = [], [], {}
    for ed, e in table["editions"].items():
        missing = [f for f in e["fetched"] if f not in texts]
        if missing:
            problems.append(f"{ed}: pages not in the store: {missing}")
            continue
        warnings += [f"{ed}: {note}" for f in e["fetched"] if (note := page_origin(entries, f))]
        page = _normalize(" ".join(texts[f].read_text(encoding="utf-8") for f in e["fetched"]))
        bad = [r for r in e["rows"] if _normalize(r["name"]) not in page
               or not any(n in page for n in _number_forms(r["percent"]))]
        stats[ed] = {"rows": len(e["rows"]), "not_found": len(bad)}
        if len(bad) > 0.1 * len(e["rows"]):
            problems.append(f"{ed}: {len(bad)} of {len(e['rows'])} rows not found in the stored pages, e.g. "
                            f"{[(r['name'], r['percent']) for r in bad[:3]]}")
    names = [{r["name"] for r in table["editions"][ed]["rows"]} for ed in ("current", "previous")]
    if len(names[0] & names[1]) < 0.5 * min(len(names[0]), len(names[1])):
        problems.append("the two editions share fewer than half of their answers; is it the same question?")
    return {"ok": not problems, "source": args.source, "editions": stats, "problems": problems,
            "warnings": warnings}
