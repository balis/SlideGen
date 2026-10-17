---
name: field-trends
description: Describe the topics of a field as they stand today - growing attention, technical maturity, production use, and reported benefits and limits - from a measurement panel of independent sources compared over the current and previous 12 months (conferences, research venues, forums, surveys, job postings, downloads, newsletters) and a discovery collection (engineering blogs, proposals, specifications, release notes, targeted surveys, radars). Works for any field; drafts the field's manifest from a course brief. Writes a profile per topic. Use before planning or modernizing a course, or when asked what is new or trending in a field.
argument-hint: <trends.yaml, or a folder and a course brief for a new field>
allowed-tools: Read, Write, Bash(python3 *), WebSearch, WebFetch
---

# field-trends

Answers: which topics of this field gain attention now, how mature are they,
where do they run in production, and what do practitioners report about them?
The answer is only as good as its sources, so the first stages define the field
and select its sources with explicit, checkable rules, and the author approves
both before anything is measured.

Two collections:

- the **measurement panel**: sources with a comparable edition in each of two
  consecutive 12-month windows, in families of evidence, each with a role:
  `items` (conference programmes, papers, curated posts and links), `forum`
  (public discussion collected per window), `adoption` (surveys, job ads,
  downloads, reported source by source);
- the **discovery collection**: sources that find and explain topics without
  year-over-year comparison (engineering blogs, project proposals and releases,
  specifications, platform release notes, targeted surveys, radars).

## Setup

- `SG` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sg.py`. On `"ok": false`, read the
  output, fix the cause (usually by sending the problem back to the agent that
  wrote the file), and run the command again. Never edit files that sg writes.
- `T` = the field's manifest (`trends.yaml`); `ROOT` = its directory. Work files
  go to `ROOT/trends/`, downloads to `ROOT/sources/`. Every sg command checks `T`
  against its schema first.
- Agents: start each as the plugin agent `slidegen:<name>`, or as a
  general-purpose subagent with the body of
  `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md` and the model named in its frontmatter.
  Pass absolute paths, the expanded `SG` command, today's date, the parts of `T`
  the agent needs (quoted, not summarized), and a scratch folder of the agent's
  own (`<scratchpad>/<agent>-<batch>/`): parallel agents that share file names
  overwrite each other's work.
- Skip any step whose output already exists and is valid. Once the author has
  approved the collections, later runs reuse them.

## Running it well

- **Models.** Scouts, verifiers, harvesters, discovery scouts, evidence
  researchers, the trend mapper: the mid-size model. Item classifiers: start
  them without a model so they run on the model their agent file names, and run
  the second classifier for the check samples on the mid-size model. Field
  scoper, topic curator, reviewers: the largest model.
- **Batches.** Verifiers about 8 sources each; harvesters one per family;
  classifiers three to six batches of 300 items each; evidence researchers six
  topics each, about seven cited items per topic. Keep a family's sources in one
  batch.
- **Downloads.** Collectors run for minutes to an hour; start them in the
  background, and run them again if they stop: they resume. If the Bash tool
  has an `allowed_domains` parameter, list the collector's API hosts in it.
- **Gap rounds.** Each check that finds a gap (short family, uncovered anchor,
  missing source named by a reviewer, broken file) goes back to the agent that
  can close it, once, with the gap named. A second failure goes to the author.
- **Cost.** A full run for one field takes about 8 million tokens, most of them
  on the small and mid-size models, and several hours.

## Scope (a new field)

1. One **field-scoper** drafts `T` from the course brief, using an approved
   manifest of another field as the template, until
   `SG trends manifest-check --manifest T` passes.
2. Show the author the draft and its `# QUESTION:` points. Stop until the author
   approves the scope; a wrong scope biases every later result.

## Stage 0: the two collections

1. **Nominate.** Start one **source-scout** per route in `T` in parallel, each
   writing `ROOT/trends/sources/candidates_<route>.json`.
2. **Merge.** Run `SG trends sources-merge --manifest T`. Read
   `trends/source_candidates.md`; if two keys name the same source (the output
   lists possible duplicates), add them to `same_source` in `T` and merge again.
   If a family has fewer than twice its quota of candidates, send every scout
   back once with the short families and their counts named (scouts keep their
   route), then merge again.
3. **Verify.** Split the candidates marked `verify` in
   `trends/source_candidates.json` into batches and start one
   **source-verifier** per batch in parallel, each writing
   `ROOT/trends/sources/verified_<batch>.json`. A later batch (v2 after v1, v10
   after v9) replaces an earlier record of the same source. Verifiers record a
   `collector` for every forum and adoption source.
4. **Select.** Run `SG trends sources-check --manifest T`. It selects the panel
   by the rules stated in its output (`trends/sources_panel.md`). Sources whose
   in-scope range straddles a family's minimum are pending: stage 1 classifies
   their items and the exact counts decide. Every selected source run by a vendor
   or dedicated to one technology needs an `own_topics` entry in `T`, and every
   selected forum or adoption source a collector.
5. **Discovery collection.** Start **discovery-scouts** in parallel, one per
   group of kinds (for example blogs; proposals and specifications; release
   notes, surveys and radars), with the targets from `discovery` in `T`, each
   writing `ROOT/trends/discovery/<group>.json`. Run
   `SG trends discovery-check --manifest T`; send short kinds back once.
6. **Review.** One **sources-reviewer** writes `trends/sources_review.json`
   about both collections; run `SG trends sources-check --manifest T` again so
   the panel shows its notes. Fill the gaps once: families below quota, anchors
   not covered, missing sources named in `high` or `medium` issues.
7. **Approve.** Show the author `trends/sources_panel.md` and
   `trends/discovery_collection.md`. Stop until the author approves. The author
   changes the panel through `exclude` (key: reason) and `include` (keys) in `T`;
   run `SG trends sources-check --manifest T` after each change.

## Stage 1: items, classification, topics

1. **Harvest.** Start **item-harvester** agents in parallel, one per item
   family, each writing `ROOT/trends/items/<source>.json` with a parser script,
   until `SG trends items-check --manifest T` passes.
2. **Classify.** Run `SG trends classify-prep --manifest T` (blinded, shuffled
   batches; no edition shown). Start **item-classifier** agents for the batches
   and the second classifier for the `check.json` samples. Run
   `SG trends classify-join --manifest T`; a source whose agreement is too low
   goes back to a classifier on the mid-size model.
3. **Settle the panel.** Run `SG trends sources-check --manifest T`: classified
   counts replace the estimates, so pending sources are decided.
4. **Topics.** Run `SG trends terms --manifest T`, then one **topic-curator**
   writes `trends/topics.json` until `SG trends topics-check --manifest T`
   passes (it also matches topics to items).

## Stage 2: attention

1. Run `SG trends collect --manifest T --source <key>` for every forum and
   adoption source in the panel (job-board collectors need `topics.json`).
2. For every `survey_table` source, one **survey-extractor** writes
   `trends/queries/<key>.json` until
   `SG trends survey-check --manifest T --source <key>` passes.
3. Run `SG trends attention --manifest T`; it writes `trends/attention.md`.

## Stage 3: profiles

1. Run `SG trends shortlist --manifest T`.
2. Start one **evidence-researcher** per batch in `trends/shortlist.json`, each
   writing `ROOT/trends/evidence/<batch>.json`, until
   `SG trends evidence-check --manifest T` passes.
3. Run `SG trends profiles --manifest T`; it writes `trends/profiles.md`.

Show the author `trends/profiles.md` and `trends/attention.md`. A course plan
uses them through the `trends` key of its plan.yaml (/slidegen:course-plan).

## Finish

Quote only numbers that sg printed. Say which families are below quota, which
sources are pending, which anchors are not covered, which discovery kinds are
below target, and which reviewer issues are still open.
