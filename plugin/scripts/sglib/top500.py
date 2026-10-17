"""Shares of TOP500 systems by processor, accelerator and interconnect, counted in the stored list pages.

A TOP500 list page shows 100 systems. Each row describes its system in one comma-separated text: system name and
model, then processor, accelerator, interconnect and operating system, where the accelerator and the operating
system are often missing and the order is not always kept. Each part is classified by what it names, not by its
position; only the parts before the first processor are taken as the model.

Answers are named at the level that topics compare:
- accelerators by model, without memory size, form factor or board prefix ("NVIDIA H100 SXM5 80 GB" and
  "NVIDIA HGX H100" are both "NVIDIA H100"), so that a topic can group models into a family through its
  `survey_names`;
- processors and interconnects by product family ("Intel Xeon", "InfiniBand"), because their raw strings differ
  by SKU, clock and speed grade, which no topic compares.
A part that no rule names keeps its own text (without core count and clock) and is listed as unmapped.
"""
from __future__ import annotations

import html
import re
from collections import Counter

CORES = re.compile(r"\b\d+C\b|\d\s*GHz", re.I)
ACCELERATOR = re.compile(
    r"\b(nvidia|tesla)\b.*\b([abhlvk]\d{2,3}[a-z]?|g[bh]\d00|gp100|gv100|p-?100|rtx|quadro)\b|"
    r"\b(nvidia|tesla)\s+(k\d+|[abhv]\d00)|instinct|gpu max|data center gpu|xeon phi \d{4}p?\s*$|xeon phi \d{4}p?,|"
    r"matrix-\d+|deep computing processor|pezy|mn-core|\bDCU\b|\bgpu\b", re.I)
INTERCONNECT = re.compile(
    r"infiniband|\bIB\b|ethernet|\bGbE\b|\bRoCE\b|slingshot|omni-?path|\bCN5000\b|tofu|aries|gemini|\bBXI\b|"
    r"TH Express|torus|hypercube|NetXtreme|ConnectX|Mellanox|\b[EHNFX]DR\d*\b|Spectrum|NVLink|\bBroadcom\b|"
    r"interconnect|network", re.I)
PROCESSOR = re.compile(r"xeon|epyc|opteron|\bAMD Rome\b|a64fx|grace|power\d|\bpower\b|sparc|sunway|sw26010|"
                       r"hygon|kunpeng|thunderx|ampere altra|phytium|vector engine", re.I)
OPERATING_SYSTEM = re.compile(r"linux|\bOS\b|\bRHEL\b|red ?hat|ubuntu|centos|rocky|suse|\bSLES|\bTOSS\b|windows|"
                              r"debian|alma|\bCLE\b|kylin|unix|operating system|\bVEOS\b|ParaStation", re.I)

# Product families of processors and interconnects; the first matching rule names the part.
PROCESSOR_FAMILIES = [
    ("AMD Instinct MI300A", r"MI300A"), ("NEC Vector Engine", r"vector engine"),
    ("Intel Xeon Phi", r"xeon phi"), ("Intel Xeon", r"xeon|\bE5-\d{4}"), ("AMD EPYC", r"epyc|\bAMD Rome\b"),
    ("AMD Opteron", r"opteron"), ("NVIDIA Grace", r"grace|GH Superchip"), ("Fujitsu A64FX", r"a64fx"),
    ("IBM POWER", r"power\d|\bpower\b"), ("Sunway", r"sunway|sw26010"), ("Hygon", r"hygon"),
    ("Huawei Kunpeng", r"kunpeng"), ("Marvell ThunderX", r"thunderx"), ("Ampere Altra", r"ampere altra"),
    ("Phytium", r"phytium"), ("SPARC", r"sparc")]
INTERCONNECT_FAMILIES = [
    ("NVLink", r"nvlink"), ("InfiniBand", r"infiniband|\bIB\b|ConnectX|Mellanox|\b[EHNFX]DR\d*\b"),
    ("Slingshot", r"slingshot"), ("Omni-Path", r"omni-?path|\bCN5000\b"),
    ("Ethernet", r"ethernet|\bGbE\b|\bRoCE\b|NetXtreme|Spectrum|^Broadcom$"),
    ("Tofu", r"tofu"), ("Aries", r"aries"), ("Gemini", r"gemini"), ("BXI", r"\bBXI\b"),
    ("TH Express", r"TH Express"), ("Sunway network", r"sunway")]


def _rules(rules):
    return [(name, re.compile(p, re.I)) for name, p in rules]


PROCESSOR_RULES, INTERCONNECT_RULES = _rules(PROCESSOR_FAMILIES), _rules(INTERCONNECT_FAMILIES)


def _parts(desc: str) -> list[str]:
    """Comma-separated parts, keeping commas inside parentheses ("InfiniBand XDR (800 Gb/s, 4X)")."""
    parts, depth, cur = [], 0, ""
    for ch in desc:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in parts + [cur] if p.strip()]


def _kind(part: str) -> str:
    if CORES.search(part):
        return "processor"
    if ACCELERATOR.search(part):
        return "accelerator"
    if INTERCONNECT.search(part):
        return "interconnect"
    if PROCESSOR.search(part):
        return "processor"
    if OPERATING_SYSTEM.search(part):
        return "os"
    return "unknown"


NVIDIA_MODEL = re.compile(r"\b(GB\d00|GH\d00|[ABHLV]\d00S?|[KP]-?\d+X?|GP100|GV100)M?\b", re.I)


def accelerator_model(part: str) -> str:
    """'NVIDIA H100 SXM5 80 GB' -> 'NVIDIA H100'; 'Quadro GP100' -> 'NVIDIA P100' (same chip); 'AMD Instinct MI250X'
    stays."""
    s = re.sub(r"\s+", " ", part.replace("​", "")).strip()
    if re.search(r"\b(xeon phi)\b", s, re.I):
        return "Intel Xeon Phi"
    if re.search(r"gpu max", s, re.I):
        return "Intel Data Center GPU Max"
    m = NVIDIA_MODEL.search(s)
    if m and not re.search(r"\b(amd|intel)\b", s, re.I):
        model = m.group(1).upper().replace("-", "")
        return "NVIDIA " + {"GV100": "V100", "GP100": "P100"}.get(model, model)
    return re.sub(r"\s*\b\d+\s*GB?\b.*$", "", s, flags=re.I)


def _family(part: str, rules) -> str | None:
    return next((name for name, rx in rules if rx.search(part)), None)


def _bare(part: str) -> str:
    """A part without core count and clock: 'LX2 304C 1.55GHz' -> 'LX2'."""
    return re.sub(r"\s+", " ", re.sub(r"\b\d+C\b|\b[\d.]+\s*GHz\b", " ", part, flags=re.I)).strip()


def classify(desc: str) -> dict:
    """{'processor': set, 'accelerator': set, 'interconnect': set, 'unmapped': [part], 'unknown': [part]} of one
    system description (the text after 'Name - ')."""
    parts = _parts(desc)
    kinds = [_kind(p) for p in parts]
    first = next((i for i, k in enumerate(kinds) if k == "processor"), None)
    out = {"processor": set(), "accelerator": set(), "interconnect": set(), "unmapped": [], "unknown": []}
    if first is None:
        out["unknown"] = parts
        return out
    if "interconnect" not in kinds[first + 1:]:
        # The interconnect is the last field before the operating system; a name no rule knows ('LingQi'), or a
        # bare vendor name that also names the processor ('Sunway'), is taken from that position.
        last = max((i for i in range(first + 1, len(parts)) if kinds[i] != "os"), default=None)
        if last is not None and (kinds[last] == "unknown" or (kinds[last] == "processor"
                                                              and not CORES.search(parts[last]))):
            kinds[last] = "interconnect"
    for i in range(first, len(parts)):
        part, kind = parts[i], kinds[i]
        if kind == "processor":
            whole = _family(part, PROCESSOR_RULES)
            for piece in re.split(r"\s*/\s*", part):
                # 'Xeon 8358/6148': a piece without a family name belongs to the family of the whole part
                name = _family(piece, PROCESSOR_RULES) or whole or _bare(piece)
                if name and not whole and not _family(piece, PROCESSOR_RULES):
                    out["unmapped"].append(part)
                if name:
                    out["processor"].add(name)
        elif kind == "accelerator":
            # 'NVIDIA A100 80G/40G': a piece that names no accelerator belongs to the model of the whole part
            out["accelerator"] |= {accelerator_model(p if ACCELERATOR.search(p) or NVIDIA_MODEL.search(p) else part)
                                   for p in re.split(r"\s*/\s*", part) if p}
        elif kind == "interconnect":
            names = {n for n, rx in INTERCONNECT_RULES if rx.search(part)}
            if not names:
                names = {part}
                out["unmapped"].append(part)
            out["interconnect"] |= names
        elif kind == "unknown" and not (i > first and kinds[i - 1] == "interconnect"):
            # an unknown part right after the interconnect continues it ('Ethernet, 4x 200Gb/s')
            out["unknown"].append(part)
    return out


ROW = re.compile(r"<tr>\s*<td>(\d+)</td>\s*<td>\s*<a href=\"/system/(\d+)\">(.*?)</a>", re.S)


def systems(page_html: str) -> list[dict]:
    """[{'rank', 'system', 'desc'}] of one stored list page."""
    rows = []
    for rank, sid, inner in ROW.findall(page_html):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip().rstrip(",").strip()
        name, _, desc = text.partition(" - ")
        rows.append({"rank": int(rank), "system": sid, "desc": desc if desc else name})
    return rows


ANY_ACCELERATOR = "Systems with accelerators"


def count(pages: list[str]) -> dict:
    """Systems per answer over the pages of one list edition, with the checks a recount needs."""
    rows = [r for page in pages for r in systems(page)]
    counts, unmapped, unknown = Counter(), Counter(), Counter()
    without = {"processor": [], "interconnect": []}
    for r in rows:
        c = classify(r["desc"])
        # one count per system and answer: an MI300A named as processor and as accelerator is one system
        counts.update(c["processor"] | c["accelerator"] | c["interconnect"])
        if c["accelerator"]:
            counts[ANY_ACCELERATOR] += 1
        for dim in without:
            if not c[dim]:
                without[dim].append(r["rank"])
        unmapped.update(c["unmapped"])
        unknown.update(c["unknown"])
    return {"systems": len(rows), "ranks": sorted(r["rank"] for r in rows),
            "per_page": [len(systems(p)) for p in pages], "counts": dict(counts),
            "unmapped": dict(unmapped), "unknown": dict(unknown),
            "without_processor": without["processor"], "without_interconnect": without["interconnect"]}
