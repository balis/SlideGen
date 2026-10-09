---
name: course-plan
description: Build a reference state-of-the-art curriculum for a course's subject from independent sources (university syllabi, textbooks, survey papers, professional programmes), compare the current curriculum with it, and propose the best-fit plan for the course's lectures, with a short list of decisions for the author. Use before modernizing or creating the lectures of a course.
argument-hint: <plan.yaml>
allowed-tools: Read, Write, Bash(python3 *), WebSearch, WebFetch
---

# course-plan

Answers: what does the field teach today about this course's subject, what does
the current curriculum miss or over-weight, and how should the available
lectures be filled? The output is a proposal and a decisions checklist; nothing
else changes.

## Setup

- `SG` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sg.py`. On `"ok": false`, read
  `error`, fix the cause (usually by sending the problem back to the agent that
  wrote the file), and run the command again. Never edit files that sg writes.
- `P` = the plan manifest given as the argument (`plan.yaml`): course name,
  level, audience, lecture count and hours, the current lectures, existing decks,
  the lecture language (slides and titles) and the curriculum language (the
  official curriculum document), and reference quotas. `ROOT` = its directory; work
  files go to `ROOT/plan/`, downloads to `ROOT/sources/`.
- `lectures.slides` in `P` is the author's expected slide count per lecture, as
  `[min, max]`. If it is missing, ask the author. `SG course validate`
  suggests a range from the median size of the decks listed in `P`, so offer
  that as the default. Every lecture's reused slides plus new material must
  fill this range.
- Agents: start each as the plugin agent `slidegen:<name>`, or as a
  general-purpose subagent with the body of
  `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md` and the model named in its frontmatter.
  Pass absolute paths, the expanded `SG` command, and today's date.
- Skip any step whose output already exists and is valid.

## Steps

1. **References.** Start four **reference-scout** agents in parallel, one per
   kind (`syllabus`, `textbook`, `paper`, `professional`), each with its quota
   from `P` and `course` = the course name in both languages, its level and
   audience, and the current lecture titles, writing
   `ROOT/plan/references/<kind>.json`. Then run
   `SG course refs --plan P`. If quotas are not met, send the scouts of the short
   kinds back for more references (once), then continue with what is accepted.
2. **Taxonomy.** One **taxonomist** writes `plan/taxonomy.json` until
   `SG course taxonomy --plan P` passes. That command also writes
   `plan/reference_curriculum.md`.
3. **Current curriculum.** One **curriculum-mapper** writes `plan/mapping.json`
   until `SG course gaps --plan P` passes, which writes `plan/gap_analysis.md`.
4. **Trends** (when `P` names a `trends` folder from /slidegen:field-trends). One
   **trend-mapper** writes `plan/trend_map.json` until
   `SG course trends --plan P` passes, which writes `plan/trends.json` and
   `plan/trend_gaps.md`: attention, maturity and use per course topic, and new
   course topics for current trends the reference curriculum lacks.
5. **Proposal.** One **course-architect** writes `plan/proposal.json` until
   `SG course validate --plan P` passes.
6. **Review.** One **course-reviewer** writes `plan/review.json`. If it lists
   `high` issues about the proposal, send them to the course-architect once for
   a revision, and validate again.
7. **Report.** `SG course report --plan P` writes `plan/curriculum_proposal.md`
   and `plan/decisions.md`.

## Finish

Tell the author where `reference_curriculum.md`, `gap_analysis.md`,
`curriculum_proposal.md`, and `decisions.md` are. Quote only numbers sg printed.
`decisions.md` has at most 12 decisions, all accepted by default: the author
unticks the ones they reject.
