---
name: deck-modernize
description: Find what is outdated or wrong in existing lecture decks (PPTX, PDF, or Marp) and what the field now covers that they miss, then write a change plan, a report, a checklist, and an annotated copy per deck, plus a course summary. Use for refreshing last year's lectures.
argument-hint: <course.yaml> [--phase report]
allowed-tools: Read, Write, Bash(python3 *), WebSearch, WebFetch
---

# deck-modernize

Answers, for each deck in a course manifest: what has changed since this deck
was written, and what should change on it? This file describes the report
phase. It ends with a report and a checklist for the author; nothing in the
deck is changed.

## Setup

- `SG` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sg.py`. Every sg command prints
  one line of JSON. On `"ok": false`, read `error`, fix the cause (usually by
  re-running the agent it names), and run the command again. Never edit files
  that sg writes (`slides.json`, `claims.json`, `quotes.json`,
  `claim_check.json`, `findings.json`, reports).
- `M` = the manifest given as the argument. `ROOT` = its directory. Deck `<id>`
  works in `ROOT/<id>/workspace/` and writes to `ROOT/<id>/output/`; course
  files go to `ROOT/course/`; downloaded sources go to `ROOT/sources/`.
- `RUBRIC` = `${CLAUDE_PLUGIN_ROOT}/references/severity.md`.
- Agents: start each as the plugin agent `slidegen:<name>`. If plugin agents are
  not available, start a general-purpose subagent whose instructions are the
  body of `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md`, and give it the model named
  in that file's frontmatter. Pass every input the agent file lists, with
  absolute paths, and the expanded `SG` command.
- Run independent agents in parallel, at most 10 at a time. Pass today's date
  explicitly.
- Skip any step whose output already exists and is valid; this makes the run
  resumable.

## Phase A: per deck (run the decks in parallel)

1. `SG ingest <deck path> --out ROOT/<id>/workspace` (add `--pdf` when the
   manifest names a PDF export). Excluded slides are hidden slides (unless the
   manifest says `hidden_slides: include`) and `out_of_scope` ranges.
2. In parallel:
   - **topic-mapper** with `skip` = the excluded slides.
   - **claim-extractor**, one per range of about 25 slides, with parts `a`,
     `b`, `c`, ... and the same `skip`.
3. `SG claims merge ROOT/<id>/workspace --manifest M`, then
   `SG claims select ROOT/<id>/workspace --batch-size 10`. Assumed values of
   worked examples are listed but not checked; arithmetic goes to batches
   `c01`, ... with `research: false`.
4. **researcher**, one per batch with `research: true` in
   `research/batches.json`, with `store` = `ROOT/sources`, `content_date` = the
   deck's `last_revised`, the deck's `target_versions`, and `scratch` = a folder
   of its own (for example `$TMPDIR/research-<batch>`).
5. `SG quotes ROOT/<id>/workspace --store ROOT/sources`.
6. **fact-checker**, one per group of up to three batches (each batch gets its
   own `checks/<batch>.json`), with `RUBRIC`, `content_date`, and
   `target_versions`. Arithmetic batches need no research and can go to a
   fact-checker at once.
7. `SG claims summary ROOT/<id>/workspace`. If it lists `needs_second_check`,
   then for each such claim:
   - run two **researcher** agents with `blind: true`, batch ids `x<NN>a` and
     `x<NN>b`, and output files `research/second_<NN>a.json` and
     `research/second_<NN>b.json`;
   - run `SG quotes` again;
   - run two **fact-checker** agents with `second_check: true` on the two new
     batches, writing `checks/second_<NN>a.json` and `checks/second_<NN>b.json`;
   - run `SG claims summary` again until it passes.

## Phase B: per course (after every deck finished phase A)

8. Read every deck's `topic_map.json` and write `ROOT/course/clusters.json`.
   Group sections from different decks that share a subject into one cluster,
   so that each subject is surveyed once. Every section belongs to exactly one
   cluster. Aim for clusters a single researcher can survey (one to four
   sections). Check with `SG findings clusters --manifest M`.
9. **developments-researcher**, one per cluster. Give it the out-of-scope topics
   from the manifest and the titles of the other clusters.
10. **findings-reviewer**, one per cluster.
11. `SG findings merge --manifest M`.

## Phase C: per deck (run the decks in parallel)

12. **change-planner** for each deck. It iterates until
    `SG plan validate --manifest M --deck <id>` passes.
13. `SG plan report --manifest M --deck <id>`; for PPTX decks also
    `SG pptx annotate --manifest M --deck <id>`.
14. `SG plan course-summary --manifest M`.

## Finish

Tell the author, per deck, the rating and the paths of
`output/modernization_report.md`, `output/checklist.md`, and
`output/annotated.pptx`, and the path of `course/course_summary.md`. Quote only
numbers that sg printed. Say that the next step is to tick items in each
checklist and run the apply phase.
