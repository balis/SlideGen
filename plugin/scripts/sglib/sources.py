"""Download sources and check that quoted text occurs in them.

`fetch` stores each source once in a source store (shared by the decks of a
course): the original bytes, the extracted text, and metadata in index.json.
`quotes` matches every quote in a workspace's research files against the
stored text and writes quotes.json, the only view of sources the fact-checker
gets.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .util import SgError, load_json, write_json

USER_AGENT = "Mozilla/5.0 (compatible; slidegen-source-fetch/1.0)"
MAX_BYTES = 40 * 1024 * 1024
TIMEOUT = 30
NOT_FETCHABLE_STATUS = {401, 402, 403, 407, 429, 451}
WINDOW_CHARS = 700          # text shown to the fact-checker on each side of a quote
MIN_MATCH_CHARS = 25        # a quote shorter than this proves nothing
PUBLISHED_META = ["article:published_time", "citation_publication_date", "citation_date",
                  "dc.date", "dcterms.issued", "date", "pubdate", "og:published_time"]


# ---------------------------------------------------------------- text extraction

def _html_text(raw: bytes) -> tuple[str, str | None, str | None]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else None
    published = None
    for name in PUBLISHED_META:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            published = tag["content"].strip()
            break
    if published is None:
        time_tag = soup.find("time", attrs={"datetime": True})
        published = time_tag["datetime"] if time_tag else None
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "svg", "form"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text, title, published


def _pdf_text(raw: bytes) -> tuple[str, str | None, str | None]:
    import fitz
    with fitz.open(stream=raw, filetype="pdf") as doc:
        text = "\n".join(page.get_text() for page in doc)
        meta = doc.metadata or {}
    published = meta.get("creationDate") or None
    if published and published.startswith("D:") and len(published) >= 10:
        published = f"{published[2:6]}-{published[6:8]}-{published[8:10]}"
    return text, meta.get("title") or None, published


def _extract(raw: bytes, content_type: str, name: str) -> tuple[str, str | None, str | None, str]:
    ctype = (content_type or "").lower()
    head = raw.lstrip()[:15].lower()
    if "pdf" in ctype or raw[:5] == b"%PDF-":
        return (*_pdf_text(raw), "pdf")
    if "html" in ctype or "xhtml" in ctype:
        return (*_html_text(raw), "html")
    if "json" in ctype or name.lower().endswith(".json"):   # API responses: decoded, one field per line
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            raise SgError(f"invalid JSON from {name}: {e}") from e
        return json.dumps(data, indent=1, ensure_ascii=False), None, None, "json"
    if ctype.startswith("text/") or "xml" in ctype or name.lower().endswith((".txt", ".md", ".rst", ".xml")):
        return raw.decode("utf-8", errors="replace"), None, None, "text"
    if head.startswith((b"<!doctype html", b"<html")):  # no usable content type: sniff
        return (*_html_text(raw), "html")
    raise SgError(f"unsupported content type '{content_type}' for {name}")


# ---------------------------------------------------------------- fetch

def _store_paths(store: Path, content_id: str, kind: str) -> tuple[Path, Path]:
    ext = {"pdf": ".pdf", "html": ".html", "text": ".txt", "json": ".json"}[kind]
    return store / "raw" / f"{content_id}{ext}", store / "text" / f"{content_id}.txt"


def _record(store: Path, entry: dict) -> None:
    """Add an entry to index.json under a lock: researchers fetch in parallel."""
    import fcntl
    store.mkdir(parents=True, exist_ok=True)
    with open(store / ".index.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        index_file = store / "index.json"
        index = load_json(index_file) if index_file.exists() else {"sources": {}}
        previous = index["sources"].get(entry["url"])
        if not (previous and previous.get("status") == "fetched" and entry["status"] != "fetched"):
            if previous and previous.get("status") == "fetched" and previous["fetched"] != entry.get("fetched"):
                # the page changed between two downloads: keep the earlier content, which may already be cited
                earlier = previous.get("earlier", []) + [{k: previous[k] for k in ("fetched", "text_file", "retrieved")
                                                          if k in previous}]
                entry = {**entry, "earlier": earlier}
            index["sources"][entry["url"]] = entry  # never replace a good fetch with a failure
        write_json(index_file, index)


def entries_by_id(index: dict) -> dict:
    """Every downloaded content id (including earlier downloads of the same URL) -> its index entry."""
    out = {}
    for e in index.values():
        if e.get("status") != "fetched":
            continue
        out[e["fetched"]] = e
        for x in e.get("earlier", []):
            out[x["fetched"]] = {**e, **x}
    return out


def _cached(store: Path, url: str) -> dict | None:
    index_file = store / "index.json"
    if not index_file.exists():
        return None
    entry = load_json(index_file)["sources"].get(url)
    return entry if entry and entry.get("status") == "fetched" else None


LIST_PAUSE = 0.5            # seconds between downloads of a URL list


def fetch_list(args) -> dict:
    """Download every URL of a list file (one per line; blank lines and # comments skipped), each stored as its
    own page: paged feeds, archive months and API pages, kept as the server sent them."""
    import time
    from argparse import Namespace
    path = Path(args.list)
    if not path.exists():
        raise SgError(f"file not found: {path}")
    urls = [u.strip() for u in path.read_text(encoding="utf-8").splitlines() if u.strip() and not u.startswith("#")]
    if not urls:
        raise SgError(f"{path} lists no URLs")
    pages = []
    for url in urls:
        try:
            r = fetch(Namespace(url=url, file=None, list=None, store=args.store, force=args.force))
        except SgError as e:
            r = {"ok": False, "url": url, "reason": str(e)}
        pages.append({"url": url, "fetched": r.get("fetched") if r["ok"] else None,
                      **({} if r["ok"] else {"reason": r.get("reason")})})
        if not r.get("cached"):
            time.sleep(LIST_PAUSE)
    failed = [p for p in pages if not p["fetched"]]
    return {"ok": not failed, "fetched": len(pages) - len(failed), "failed": len(failed), "pages": pages}


def fetch(args) -> dict:
    if getattr(args, "list", None):
        return fetch_list(args)
    store = Path(args.store).resolve()
    key = f"file:{Path(args.file).name}" if args.file else args.url
    cached = _cached(store, key)
    if cached and not args.force:
        return {"ok": True, "cached": True, **cached}
    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.file:
        path = Path(args.file).resolve()
        if not path.exists():
            raise SgError(f"file not found: {path}")
        raw, url, final_url, ctype, last_modified = path.read_bytes(), f"file:{path.name}", None, "", None
    else:
        import requests
        url = args.url
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT},
                                stream=True, allow_redirects=True)
        except requests.RequestException as e:
            entry = {"url": url, "status": "not_fetchable", "reason": f"request failed: {e.__class__.__name__}",
                     "retrieved": retrieved}
            _record(store, entry)
            return {"ok": False, **entry, "hint": "record this source with \"fetched\": null"}
        if resp.status_code in NOT_FETCHABLE_STATUS or resp.status_code >= 400:
            entry = {"url": url, "status": "not_fetchable", "reason": f"HTTP {resp.status_code}",
                     "retrieved": retrieved}
            _record(store, entry)
            return {"ok": False, **entry, "hint": "record this source with \"fetched\": null"}
        raw = resp.raw.read(MAX_BYTES + 1, decode_content=True)
        if len(raw) > MAX_BYTES:
            raise SgError(f"{url}: larger than {MAX_BYTES // (1024 * 1024)} MB")
        final_url, ctype = resp.url, resp.headers.get("content-type", "")
        last_modified = resp.headers.get("last-modified")

    text, title, published_hint, kind = _extract(raw, ctype, url)
    if len(text.strip()) < 200:
        entry = {"url": url, "status": "not_fetchable", "retrieved": retrieved,
                 "reason": "almost no text extracted (login wall, bot check, or script-only page)"}
        _record(store, entry)
        return {"ok": False, **entry, "hint": "record this source with \"fetched\": null"}

    content_id = hashlib.sha256(raw).hexdigest()[:16]
    raw_path, text_path = _store_paths(store, content_id, kind)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.parent.mkdir(parents=True, exist_ok=True)
    if args.file:
        shutil.copyfile(Path(args.file), raw_path)
    else:
        raw_path.write_bytes(raw)
    text_path.write_text(text, encoding="utf-8")
    entry = {"url": url, "status": "fetched", "fetched": content_id, "final_url": final_url,
             "kind": kind, "title": title, "published_hint": published_hint,
             "last_modified": last_modified, "retrieved": retrieved, "chars": len(text),
             "text_file": str(text_path.relative_to(store))}
    _record(store, entry)
    return {"ok": True, **entry}


# ---------------------------------------------------------------- quote matching

_CHAR_MAP = {"‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
             "“": '"', "”": '"', "„": '"', "″": '"', "`": "'",
             "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
             "―": "-", "−": "-", "­": "", "™": "", "®": "", "©": ""}
_ELLIPSIS = re.compile(r"\s*(?:\.\.\.|…|\[\s*\.\.\.\s*\]|\[…\])\s*")
_CLOSE = set(".,;:!?)]}")
_OPEN = set("([{")


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalize text for matching and keep, for each output char, its source index."""
    out: list[str] = []
    index: list[int] = []
    prev_space = True
    line_start = True
    for i, ch in enumerate(text):
        # comment leaders of source files (" * text", "// text", "# text") are not part of a quote
        if line_start and (ch in "*#" or (ch == "/" and text[i + 1:i + 2] in ("/", "*"))
                           or (ch == "/" and i > 0 and text[i - 1] in "/*")):
            ch = " "
        elif ch == "\n":
            line_start = True
        elif not ch.isspace():
            line_start = False
        ch = _CHAR_MAP.get(ch, ch)
        for c in unicodedata.normalize("NFKC", ch).casefold():
            if c.isspace():
                if prev_space:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = False
            out.append(c)
            index.append(i)
    # HTML-to-text extraction puts spaces around inline links ("dataset . CDC", "( ETL )"); quotes copied
    # from the rendered page do not have them, so spaces before closing and after opening punctuation go
    keep = [not (c == " " and ((k + 1 < len(out) and out[k + 1] in _CLOSE) or (k > 0 and out[k - 1] in _OPEN)))
            for k, c in enumerate(out)]
    return "".join(c for c, ok in zip(out, keep) if ok), [i for i, ok in zip(index, keep) if ok]


def _normalize(text: str) -> str:
    return _normalize_with_map(text)[0].strip()


def match_quote(quote: str, text: str, min_chars: int = MIN_MATCH_CHARS) -> tuple[bool, int, int]:
    """Return (matched, start, end) in the original text; parts split at ellipses match in order."""
    norm_text, index = _normalize_with_map(text)
    parts = [_normalize(p).strip(" \"'.,;:") for p in _ELLIPSIS.split(quote)]
    parts = [p for p in parts if p]
    if sum(len(p) for p in parts) < min_chars:
        return False, -1, -1
    pos, first = 0, None
    for part in parts:
        found = norm_text.find(part, pos)
        if found < 0:
            return False, -1, -1
        first = found if first is None else first
        pos = found + len(part)
    return True, index[first], index[pos - 1] + 1


def quotes(args) -> dict:
    workspace = Path(args.workspace).resolve()
    store = Path(args.store).resolve()
    index = load_json(store / "index.json")["sources"] if (store / "index.json").exists() else {}
    by_id = entries_by_id(index)
    results, counts = [], {"matched": 0, "not_found": 0, "too_short": 0, "not_machine_checked": 0}
    files = sorted(p for p in (workspace / "research").glob("*.json") if p.name != "batches.json")
    if not files:
        raise SgError(f"no research files in {workspace / 'research'}")
    known = ({c["id"] for c in load_json(workspace / "claims.json")["claims"]}
             if (workspace / "claims.json").exists() else None)
    members = ({b["batch"]: {c["claim_id"] for c in b["claims"]}
                for b in load_json(workspace / "research" / "batches.json")["batches"]}
               if (workspace / "research" / "batches.json").exists() else {})
    wrong_ids = []
    for path in files:
        doc = load_json(path, "research")
        for claim in doc["claims"]:
            # a mistyped id (a-61 for a-061) would silently detach the evidence from its claim
            allowed = members.get(doc["batch"], known)
            if allowed is not None and claim["claim_id"] not in allowed:
                wrong_ids.append(f"{path.name}: {claim['claim_id']}")
            for i, src in enumerate(claim["sources"]):
                entry = {"batch": doc["batch"], "claim_id": claim["claim_id"], "source": i,
                         "url": src["url"], "title": src.get("title"),
                         "role": src.get("role"), "published": src.get("published")}
                if src["fetched"] is None:
                    entry["status"] = "not_machine_checked"
                elif src["fetched"] not in by_id:
                    raise SgError(f"{path.name}: {claim['claim_id']} source {i} cites fetched id "
                                  f"'{src['fetched']}', which is not in {store / 'index.json'}; "
                                  f"run `sg fetch` for {src['url']}")
                else:
                    text = (store / by_id[src["fetched"]]["text_file"]).read_text(encoding="utf-8")
                    ok, start, end = match_quote(src["quote"], text)
                    short = len(_normalize(_ELLIPSIS.sub(" ", src["quote"]))) < MIN_MATCH_CHARS
                    entry["status"] = "matched" if ok else ("too_short" if short else "not_found")
                    if ok:
                        entry["window"] = text[max(0, start - WINDOW_CHARS):end + WINDOW_CHARS]
                        entry["quote"] = text[start:end]
                    else:
                        entry["quote_claimed"] = src["quote"]
                counts[entry["status"]] += 1
                results.append(entry)
    if wrong_ids:
        raise SgError("research files name claims that are not in their batch (or not in claims.json); "
                      "fix the ids or re-run the researcher: " + "; ".join(wrong_ids[:12]))
    write_json(workspace / "quotes.json", {"generated_by": "sg quotes", "results": results})
    # One small file per batch: each fact-checker reads only the evidence for its own batch.
    by_batch: dict[str, list] = {}
    for r in results:
        by_batch.setdefault(r["batch"], []).append(r)
    for batch, rows in by_batch.items():
        write_json(workspace / "quotes" / f"{batch}.json", {"generated_by": "sg quotes", "batch": batch,
                                                           "results": rows})
    not_found = [f"{r['claim_id']}#{r['source']}" for r in results if r["status"] == "not_found"]
    return {"ok": True, "out": str(workspace / "quotes.json"), **counts, "not_found": not_found}
