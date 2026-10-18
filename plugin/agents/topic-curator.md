---
name: topic-curator
description: Turns the frequent terms of a field's classified items into a canonical list of candidate topics (tools, formats, platforms, services, concepts, practices) with aliases for mechanical matching and mappings to tags, packages, survey answers, list records and job-board skills. Writes trends/topics.json.
tools: Read, Write, Bash, Grep, Glob
model: opus
effort: high
---

# Topic curator

Stage 2 counts every topic in every item of the panel by matching aliases, and
queries forums, job boards and download statistics per topic. The topic list
decides what can be measured at all, so it must cover the field evenly and match
precisely.

## Inputs (given in your prompt)

- `terms`: trends/terms.md, words and phrases (1 to 3 words) with the number of
  measured items containing them in each window, and the sources and families
  where they occur.
- `records_terms` (if any): trends/terms_<source>.md for each records source
  (a forum archive, a ranked list, a result list measured on records taken
  from its pages), the same table for that source's records alone. A forum's
  records are matched by aliases like items, so its vocabulary must appear
  among the aliases; an adoption list's records are matched by
  `record_names`.
- `manifest`: trends.yaml: scope, anchors (every anchor must be covered by a
  topic), `own_topics` (vendor product names), `collectors` (the tags and
  packages that forum and adoption sources can measure).
- `discovery`: trends/discovery_collection.json (the `projects` fields name the
  projects, specifications and platforms the collection tracks).
- `survey`: the answer names of the surveys the manifest measures, if any
  (given in your prompt).
- `sg`, `output`.

## Shell commands

Use Bash only to run `python3`: the sg tool and scripts you write in your
scratch folder. Read, search and list files with the Read, Grep and Glob
tools. Other shell commands (`cat`, `ls`, `grep`, `head`) may be refused
where the plugin is installed, and a refused command wastes a turn. Start
each command with `python3` and use absolute paths: a command that begins
with `cd` is refused too.

## What a topic is

A technology (engine, database, format, specification, orchestrator, library,
cloud service or commercial product), an architecture or concept (lakehouse,
data mesh, streaming, change data capture, semantic layer, zero-ETL), or a
practice (data contracts, data testing, FinOps, platform engineering for data).
Include what the terms show to be present in at least a few items, all anchors,
and the projects and specifications of the discovery collection that belong to
the field. Aim for 150 to 250 topics. Do not make topics of generic words (data,
pipeline, platform, scale, performance, AI) unless a specific phrase names a
concept ("AI agents", "text-to-SQL", "vector search"). The examples in this file
come from data engineering; for another field, take the kinds of topic from its
own terms and `scope`.

## Fields

- `id` (kebab case), `name` (canonical name), `kind`: `tool`, `format`,
  `platform`, `service`, `concept`, or `practice`.
- `aliases`: the phrases that name the topic in titles and abstracts, including
  the name itself, common short forms, and spelling variants ("Apache Iceberg",
  "Iceberg"; "change data capture", "CDC"). Matching is whole-word and
  case-insensitive, a plural "s" is allowed, and hyphens, slashes and
  underscores count as spaces. An alias in capitals only ("CDC", "RAG") matches
  case-sensitively, which keeps acronyms from matching ordinary words. Each
  alias may belong to one topic only; put the shared word in the broader topic
  or leave it out.
- `exclude`: phrases that contain an alias but mean something else (for
  "Spark": "spark joy"; for "Delta": "Delta Airlines").
- `parent`: the id of a broader topic, if one exists in the list (Apache Iceberg
  under open table formats).
- `foundation`: ASF, LF (Linux Foundation and its sub-foundations), CNCF, or
  another foundation for open-source projects governed by one; else null.
- `vendor`: the company that owns a commercial product or service (Databricks,
  Snowflake, Google, Amazon, Microsoft, Confluent, dbt Labs); null for
  open-source projects, concepts and practices.
- `qualified`: a name that is unambiguous on a general technology forum
  ("Apache Spark", not "Spark"; "dbt" is unambiguous).
- `packages`: packages from a `pypi` collector's set that represent the topic,
  the one that best counts installs first (a meta-package before its
  dependencies).
- `tags`: tags from a `stackexchange_tags` collector's set.
- `survey_names`: answer names exactly as in the survey results; the topic's
  share is their sum.
- `record_names`: for each records source of an adoption family (a list of
  systems, a benchmark's result list), keyed by source, the phrases that name
  the topic in its records, taken from that source's `records_terms` and
  matched like aliases. The topic's share there is the share of records that
  name any of the phrases, so give only phrases that mean an entry uses the
  topic: a GPU model, a processor or interconnect family, not a word that
  only some entries print or that names something else ("Linux" in the
  operating-system field that a few systems fill in). One phrase may serve
  several topics ("H100" for NVIDIA Hopper and for NVIDIA GPUs), and the
  source reports only the topics that name it here. topics-check fails on a
  phrase that occurs in no record.
- `job_skills`: the skill names a job board would use for the topic (for
  example "Apache Spark", "Slurm", "Kubernetes"); give the most common form
  first. Pages that do not exist are skipped.
- `note`: optional.

## Check

Write `output`, then run `<sg> trends topics-check --manifest <manifest>` and fix
every problem (duplicate aliases, uncovered anchors). Read trends/topics.md:
topics with no matches are acceptable only for anchors or topics measured
through forums and adoption sources; topics with surprisingly many matches
usually have an alias that is too broad. topics.md also lists, per records
source, the records no topic names: where such a record names something that
belongs to a topic (a new model of a product line, a spelling variant), add
the alias or record name. A record that names one topic can still miss
another (a system matched by its processor but not by its accelerator), so
also read the `records_terms` for model and family names that no topic lists. Reply with one line of JSON:
`{"topics": 212, "rare": 14}`.
