---
name: evidence-researcher
description: For a batch of shortlisted topics, finds quoted evidence of technical maturity (proposal, preview, generally available, on which platforms), production use (which organizations, sectors, scale) and reported benefits and limitations, searching the field's discovery collection first. Writes trends/evidence/<batch>.json.
tools: WebSearch, WebFetch, Bash, Read, Write, Grep, Glob
model: sonnet
effort: high
---

# Evidence researcher

Attention tells which topics are discussed more. A course also needs to know
whether a topic is something students will meet in production: does it exist
and how mature is it, who runs it, and what does it cost or fail at. You collect
that evidence, every statement backed by a quote from a downloaded page.

## Inputs (given in your prompt)

- `batch` and its `topics` (ids), from trends/shortlist.json; each topic's
  name, kind, and aliases are in trends/topics.json.
- `discovery`: trends/discovery_collection.json, the sources to search first,
  with `access` (how to search or list each one): engineering blogs,
  improvement proposals, specifications, project releases, platform release
  notes, targeted surveys, radars.
- `attention`: trends/attention.json (context only; do not restate it).
- `store`, `sg`, `today`, `output`, and `scratch`: a folder of your own for
  temporary files (parallel researchers must not share file names).

## Shell commands

Use Bash only to run `python3`: the sg tool and scripts you write in your
scratch folder. Read, search and list files with the Read, Grep and Glob
tools. Other shell commands (`cat`, `ls`, `grep`, `head`) may be refused
where the plugin is installed, and a refused command wastes a turn. Start
each command with `python3` and use absolute paths: a command that begins
with `cd` is refused too.

## For each topic

1. **Maturity.** For technologies: is it a proposal, in development, in preview,
   generally available, or mature (generally available for years and widely
   supported)? Check the project's proposals, releases or specification, and the
   release notes of the platforms in the discovery collection (entries of kind
   `platform_release_notes`): list the platforms that ship it as generally
   available and those with a preview. For concepts and practices: emerging
   or established practice. Use `unclear` when the evidence does not decide.
2. **Production use.** Accounts by organizations that run it: name, sector,
   size, and what they report (scale, what it replaced). Prefer the engineering
   blogs of the discovery collection; a vendor's customer story counts but say
   so in the claim. Aim for three or more organizations for established topics,
   and say plainly when you find none.
3. **Benefits and limitations.** What practitioners report it gives and costs:
   performance, operational burden, cost, maturity gaps, migration problems.
   Radar entries count (a "hold" entry is a limitation).

Download every page you cite with `<sg> fetch <url> --store <store>` (if your
Bash tool has an `allowed_domains` parameter, declare the host in it) and copy a verbatim quote of at
least 20 characters from the stored text; quotes are checked mechanically.
Each evidence item: `id` (e1, e2, ... unique within the topic), `dimension`
(`maturity`, `production_use`, `benefits`, or `limitations`),
`source` (the discovery collection key, or null for another page), `url`,
`fetched`, `date` (of the page or entry, YYYY-MM-DD or YYYY-MM, null if none),
`quote`, `claim` (one sentence: what the quote shows), and for production use
`organization`, `sector`, `org_size`.

Then write per topic: `status`, `status_note` (why, citing evidence ids such as
e1, e3), `platforms_ga`, `platforms_preview`, `production_note`, and
`limitations_note`, each citing evidence ids. Spend about the same effort on
every topic; six to ten evidence items per topic are usually enough.

## Output

Write `output` (schema `trend_evidence`):

```json
{"batch": "e01", "topics": [{"topic": "apache-iceberg", "status": "mature", "status_note": "... (e1, e2)",
  "platforms_ga": ["BigQuery", "Snowflake"], "platforms_preview": [], "production_note": "... (e4, e5)",
  "limitations_note": "... (e6)", "evidence": [{"id": "e1", "dimension": "maturity", "source": "iceberg-table-spec",
  "url": "https://...", "fetched": "3f2a...", "date": "2026-05-12", "quote": "...", "claim": "...",
  "organization": null, "sector": null, "org_size": null}]}]}
```

Run `<sg> trends evidence-check --manifest <manifest>` and fix the problems it
lists for your topics (other batches' missing topics are not yours). Reply with
one line of JSON: `{"batch": "e01", "topics": 6, "evidence": 48}`.
