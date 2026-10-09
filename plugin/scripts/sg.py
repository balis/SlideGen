#!/usr/bin/env python3
"""sg: the deterministic steps of the SlideGen skills.

Every command prints a one-line JSON summary and exits non-zero when its
result is not usable; the "error" field says what to fix or re-run.

Deck commands work on a workspace directory (WS). Course commands take the
course manifest (course.yaml); deck workspaces then live in
<manifest dir>/<deck id>/workspace/ and course files in <manifest dir>/course/.

  sg.py ingest DECK --out WS [--pdf EXPORT] [--force]
  sg.py fetch (URL | --file PATH) --store DIR [--force]
  sg.py quotes WS --store DIR
  sg.py claims merge WS [--manifest M]
  sg.py claims select WS [--batch-size N]
  sg.py claims summary WS
  sg.py findings clusters --manifest M
  sg.py findings merge --manifest M [--allow-unreviewed]
  sg.py plan validate --manifest M --deck ID
  sg.py plan report --manifest M --deck ID
  sg.py plan course-summary --manifest M
  sg.py pptx annotate --manifest M --deck ID [--approved CHECKLIST]
  sg.py course refs|taxonomy|gaps|trends|validate|report --plan PLAN.yaml
  sg.py lecture outline-check --plan PLAN.yaml --lecture N [--outline FILE] [--spec DECK.json]
  sg.py trends sources-merge|sources-check --manifest TRENDS.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sglib import (attention, claims, course, findings, harvest, ingest, lecture, plan, pptx_build,  # noqa: E402
                   pptx_out, profiles, sources, trends)
from sglib.util import SgError  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sg", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="read a deck into WS/slides.json")
    p.add_argument("deck", help="PPTX, PDF, or Marp Markdown file")
    p.add_argument("--out", required=True, help="workspace directory")
    p.add_argument("--pdf", help="PDF export of a PPTX deck, used to render image-heavy slides")
    p.add_argument("--force", action="store_true", help="re-read even if slides.json is current")
    p.set_defaults(func=ingest.run)

    p = sub.add_parser("fetch", help="download a source into the source store")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("url", nargs="?")
    src.add_argument("--file", help="a local file supplied by the author")
    p.add_argument("--store", required=True, help="source store directory")
    p.add_argument("--force", action="store_true", help="download again even if already stored")
    p.set_defaults(func=sources.fetch)

    p = sub.add_parser("quotes", help="match every quote in WS/research against fetched text")
    p.add_argument("workspace")
    p.add_argument("--store", required=True)
    p.set_defaults(func=sources.quotes)

    group = sub.add_parser("claims", help="claim bookkeeping").add_subparsers(dest="action", required=True)
    p = group.add_parser("merge", help="claims/extract_*.json -> claims.json")
    p.add_argument("workspace")
    p.add_argument("--manifest", help="course.yaml, for hidden and out-of-scope slides")
    p.set_defaults(func=claims.merge)
    p = group.add_parser("select", help="claims.json -> research/batches.json")
    p.add_argument("workspace")
    p.add_argument("--batch-size", type=int, default=6)
    p.set_defaults(func=claims.select)
    p = group.add_parser("summary", help="checks/*.json -> claim_check.json")
    p.add_argument("workspace")
    p.set_defaults(func=claims.summary)

    group = sub.add_parser("findings", help="course developments").add_subparsers(dest="action", required=True)
    p = group.add_parser("clusters", help="check that clusters cover every section once")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=findings.clusters)
    p = group.add_parser("merge", help="merge cluster findings and reviews, compute priorities")
    p.add_argument("--manifest", required=True)
    p.add_argument("--allow-unreviewed", action="store_true")
    p.set_defaults(func=findings.merge)

    group = sub.add_parser("plan", help="change plans").add_subparsers(dest="action", required=True)
    for name, func in (("validate", plan.validate), ("report", plan.report)):
        p = group.add_parser(name)
        p.add_argument("--manifest", required=True)
        p.add_argument("--deck", required=True)
        p.set_defaults(func=func)
    p = group.add_parser("course-summary")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=plan.course_summary)

    group = sub.add_parser("course", help="course planning").add_subparsers(dest="action", required=True)
    for name, func, text in (
            ("refs", course.refs, "check reference curricula: quotes, recency, quotas, vendor share"),
            ("taxonomy", course.taxonomy, "check the taxonomy and compute topic coverage"),
            ("gaps", course.gaps, "compare the current curriculum with the references"),
            ("trends", course.trends, "join the field's trend topics to the course topics"),
            ("validate", course.validate, "check the proposed lecture plan"),
            ("report", course.report, "render the proposal and the decisions checklist")):
        p = group.add_parser(name, help=text)
        p.add_argument("--plan", required=True, help="plan.yaml of the course")
        p.set_defaults(func=func)

    group = sub.add_parser("lecture", help="lecture building").add_subparsers(dest="action", required=True)
    p = group.add_parser("outline-check", help="check a lecture outline against the course plan")
    p.add_argument("--plan", required=True, help="plan.yaml of the course")
    p.add_argument("--lecture", required=True, type=int, help="lecture number")
    p.add_argument("--outline", help="outline file (default: lectures/L<NN>/outline.json next to plan.yaml)")
    p.add_argument("--spec", help="deck specification to compare with the outline (deck.json)")
    p.set_defaults(func=lecture.outline_check)

    group = sub.add_parser("trends", help="field trends").add_subparsers(dest="action", required=True)
    for name, func, text in (
            ("manifest-check", trends.manifest_check, "check a drafted trends manifest"),
            ("sources-merge", trends.sources_merge, "merge source nominations from all discovery routes"),
            ("sources-check", trends.sources_check, "apply eligibility rules and select the source panel"),
            ("discovery-check", trends.discovery_check, "check the discovery collection"),
            ("items-check", harvest.items_check, "check harvested items against stored pages and verified counts"),
            ("classify-prep", harvest.classify_prep, "write blinded batches of items for classification"),
            ("classify-join", harvest.classify_join, "join relevance labels and check classifier agreement"),
            ("terms", harvest.terms, "frequent words and phrases in measured items"),
            ("topics-check", harvest.topics_check, "check the topic list and match topics to measured items")):
        p = group.add_parser(name, help=text)
        p.add_argument("--manifest", required=True, help="trends.yaml of the field")
        if name == "terms":
            p.add_argument("--limit", type=int, default=1500, help="number of terms to list")
        p.set_defaults(func=func)
    p = group.add_parser("collect", help="download raw data of a forum or adoption source for both windows")
    p.add_argument("--manifest", required=True, help="trends.yaml of the field")
    p.add_argument("--source", required=True, help="panel source key")
    p.set_defaults(func=attention.collect)
    p = group.add_parser("survey-check", help="check an extracted survey table against the stored pages")
    p.add_argument("--manifest", required=True, help="trends.yaml of the field")
    p.add_argument("--source", required=True, help="panel source key")
    p.set_defaults(func=attention.survey_check)
    p = group.add_parser("attention", help="change in attention per topic and family")
    p.add_argument("--manifest", required=True, help="trends.yaml of the field")
    p.set_defaults(func=attention.attention)
    for name, func, text in (("shortlist", profiles.shortlist, "topics to profile, in batches"),
                             ("evidence-check", profiles.evidence_check, "check evidence files"),
                             ("profiles", profiles.profiles, "write the topic profiles")):
        p = group.add_parser(name, help=text)
        p.add_argument("--manifest", required=True, help="trends.yaml of the field")
        p.set_defaults(func=func)

    group = sub.add_parser("pptx", help="PowerPoint output").add_subparsers(dest="action", required=True)
    p = group.add_parser("annotate", help="copy the deck with plan items in speaker notes")
    p.add_argument("--manifest", required=True)
    p.add_argument("--deck", required=True)
    p.add_argument("--approved", help="checklist.md; only ticked items are written")
    p.set_defaults(func=pptx_out.annotate)
    p = group.add_parser("build", help="build a deck from a specification on a base deck's master")
    p.add_argument("--spec", required=True, help="deck specification (schema deck_spec)")
    p.set_defaults(func=pptx_build.build)
    p = group.add_parser("render", help="render a deck to PNG per slide with LibreOffice")
    p.add_argument("--pptx", required=True)
    p.add_argument("--out", required=True, help="folder for the PDF and the PNG files")
    p.add_argument("--dpi", type=int, default=80)
    p.set_defaults(func=pptx_build.render)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        summary = args.func(args)
    except SgError as e:
        summary = {"ok": False, "error": str(e)}
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
