# Review: SlideGen as a Claude Code plugin

**Reviewed document:** [slidegen-plugin.md](slidegen-plugin.md) (proposal dated 2026-10-08)
**Review date:** 2026-10-08

The proposal was revised on the same day to address these findings. Section
numbers in this review refer to the version that was reviewed.

## Method

Two reviewers worked independently. Neither saw the discussion that produced the
proposal. Both had read-only access to the repository, the 14 deck workspaces, and
the Claude Code documentation.

- **Evidence check.** Re-measured every factual claim the proposal makes about the
  current system and the platform.
- **Design critique.** Judged the design against its goals: reusable skills for
  creating, reviewing, and modernizing decks, and the immediate need to refresh last
  year's decks.

The findings that change the design most were then verified again directly. The
**Verified** column marks those. Other items are as reported by a reviewer, with
the evidence they cited.

## 1. Verdict

The proposal's diagnosis of the current system holds in substance. Several of its
statements are wrong, though, and four of the errors change the design:

- The "no fact without a source" guarantee does not hold today.
- Subagents can nest.
- File dates cannot define the window for the new-developments search.
- The proposed quote check would compare model-written text with model-written text.

The modernize design also has gaps that would make its first real run unreliable.

Recommended path:

1. Revise the proposal.
2. Build the course-level modernize report first, with sources fetched by a
   script and every count computed by a script.
3. Run it on one course before porting `deck-create` or packaging the plugin.

## 2. Corrections to the proposal

| # | Section | Proposal says | What is true | Verified |
|---|---|---|---|---|
| 1 | §2, §4.1 | A deck cannot contain a fact without a source. | Writers are told to tag every fact, but only tagged bullets are fact-checked. 607 of 1,541 bullets (39%) in the 13 finalized decks carry no claim tag. Some are not facts (agendas, exercise launch slides), but many are, e.g. "Merkle trees locate divergence with O(log N) comparisons" in `dynamo-modernized`. | yes (count) |
| 2 | §5 row 1, §6.9 | A subagent cannot start further subagents. | Since v2.1.219 a subagent can start subagents up to three layers below the main conversation (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). Only forks cannot. A session runs at most 20 subagents at once (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`). Under `-p`, a subagent does not wait for nested *background* subagents. The logged runs used v2.1.72, before nesting existed. | yes (docs) |
| 3 | §4.2 P4 | The Trino slide "was correct when written". | Trino shipped fault-tolerant execution in 2022, and the reviewed deck is the 2026 version. The slide was already out of date when written. | reported; matches Trino release history |
| 4 | §4.2 P1 | The source-file naming rule has existed since the first commit, yet three decks ended without matching files. | `iceberg-internals` and `query-engines` wrote their registries at 12:14 and 12:58 on 2026-03-20, before the first commit at 23:19 that day. `cost-mpr`'s files match once `_` is read as `:`. No run under the committed rule lost a source link. Stronger evidence for P1 is in the run logs: the orchestrator wrote 28 helper scripts in 8 of 10 logged runs, mostly for re-check sets, review merges, and checklists. | yes (timestamps); 28 scripts reported |
| 5 | §4.2 P2 | Besides those three decks, 260 of 600 files in 7 of 14 decks have a header ID that differs from the filename. | The 260 include `cost-mpr`, one of the three. The 600 include 3 `.gitkeep` files and 183 files whose header names no ID. Corrected: 234 of 510 source files, in 6 of the other 11 decks. | reported |
| 6 | §4.2 P3 | The excerpt differs from the source file's copy in 10–30% of claims per deck, and the differences are small. | 0–42% per deck, 22% overall (normalized 120-character prefix test; stripping punctuation gives 14%). Not all differences are small: in `query-engines2`, 17 of 76 excerpts share less than 70% of their 5-word sequences with the source file, so they are paraphrases. | reported |
| 7 | §4.1 | Carry-forward, best-verdict, and 2-of-3 resampling are current practice. | They arrived in the latest commit (2026-06-17), have run on at most one deck, and `course.md` does not use them. `course.md` also regenerates whole flagged chunks and has no SURGICAL/REWRITE routing. The lecture and course modes therefore differ in procedure, not only in tag style. | yes (course.md) |
| 8 | §3, §4.1 | Exercises are validated against a real model. | In the only course run, the validator agent (`claude-opus-4-6`) ran all six exercises itself instead of on the brief's target tool, and graded its own output. | yes (provenance) |
| 9 | §4.2 P4 | "a critical finding" | That review assigns no severities. Its report template files every MISREPRESENTED verdict under "Critical Issues". | reported |
| 10 | §5, §8 | Plugins cannot ship permissions. | Plugin *settings* cannot carry permission rules. But a skill's `allowed-tools` frontmatter pre-approves tools for the turn that invokes the skill, and a headless `claude -p "/slidegen:…"` run is one turn. Project allow rules are not applied by `claude -p` in a folder that was never trusted. The docs do not say whether a skill's grant reaches its subagents. | reported by both reviewers |
| 11 | §5 | Each workflow run needs explicit opt-in, and workflows cannot do the revision loop's file comparisons. | Under `-p`, a workflow launches according to `Workflow(<name>)` allow rules. Workflow agents can read and write files and run scripts; only the workflow script itself cannot. The real limit is that a workflow takes no user input mid-run. | reported |
| 12 | §8 | A headless run stops at the first call that is not allowed. | The call is denied and the run continues. The current pipeline's copy-with-python workaround depends on this. | reported |
| 13 | §3 | Up to three revision rounds. | At most three drafts and three fact-check rounds, which means at most two revisions. | yes (generate.md) |
| 14 | §6.4 | The 14 workspaces can serve as test fixtures. | Only 2–3 workspaces exercise the current verification steps. Review files come in at least 8 shapes. None has known-correct outputs to test against. | reported |

## 3. New evidence about the current review pipeline

From the `query-engines-rev` run. All three items were verified.

- **Slide numbers are off by one.** The extracted text starts with an invented
  "Slide 1: Title Slide", but page 1 of the PDF is "What Is a Query Engine?". Every
  slide number in that report is one too high.
- **Sources without quotes.** 27 of 43 registry entries have no excerpt.
  `sources/claim_036.txt` contains the researcher's verdict ("PARTIALLY SUPPORTED /
  NEEDS QUALIFICATION") and no quote, and a reported finding rests on it.
- **Counts are written by the model.** The report header says "Unsourced: 0" while
  the registry contains UNVERIFIED claims (reported: 6).

## 4. Design findings

### HIGH

**H1. File dates cannot define the window for the new-developments search (§6.8).**
- **Problem:** Decks carried forward each year get re-saved. Neither the PPTX
  `modified` date nor the newest date in the text reflects the content. The
  reviewed Spark PDF was created on 2026-03-21, but the newest year in its text is
  2014. A search limited to "baseline date to today" would miss developments that
  predate the baseline and that the deck still omits, such as Trino's 2022
  fault-tolerant execution. The common case, a slide that was already stale when
  written, cannot be told apart from "true then, false now".
- **Recommendation:**
  - Run step 3b as a survey of the current state of each section's topic, and
    compare the survey with the topic map.
  - Record each finding's own date. Use the baseline only to label and sort
    findings ("new since the deck" versus "older, and missing").
  - Estimate a content date per section from the slides themselves: the newest
    version, paper, or system they name.
  - Ask the author for the year of the last real revision, per course.

**H2. The quote check would compare model text with model text (§6.5 versus the
researcher's tools in §6.1).**
- **Problem:** WebFetch converts a page to Markdown and returns a small model's
  answer about it, not the page text (verified from the tool description). A
  researcher limited to WebSearch, WebFetch, Read, and Write therefore cannot save
  real page text, and cannot download PDFs for PyMuPDF.
- **Recommendation:**
  - Add `fetch_source.py URL`. It downloads in code, extracts text (HTML to text,
    or PyMuPDF for PDFs), and stores the bytes, the text, a hash, and the HTTP
    `Last-Modified` header.
  - Researchers call it through Bash, pre-approved by the skill's `allowed-tools`.
  - `check_quotes.py` matches only against text that this script fetched.
  - Sources it cannot fetch (paywalled publisher pages, bot-blocked sites) are
    marked "quote not machine-checked" instead of LOW.
  - Accept local PDFs supplied by the author, as `alice-2026` already does.
  - The schema forbids verdicts and opinions in source records.
  - The README must state the network rules. On this machine the sandbox lets
    Bash reach only a short list of domains; trino.io, duckdb.org, and dl.acm.org
    are not on it (reported).

**H3. The course batch cannot run in the stated order, and its platform reasoning
is wrong (§6.9).**
- **Problem:** Step 3b runs once over the combined topic maps, but the topic maps
  come from per-deck step 2. The change plan (step 4) needs 3b's results, yet it
  sits in the same per-deck session. No component is named for mapping findings to
  decks.
- **Recommendation:** Run three phases, each waiting for the previous one:
  - **A, per deck:** ingest, topic map, claim check.
  - **B, per course:** merge the topic maps, run the developments survey, map
    findings to decks, and remove duplicates. Assign an owner agent to this phase.
  - **C, per deck:** change plan; then the course summary.

  Add a course manifest with the decks and their order, the syllabus, the
  last-revision year, the time budget, and the software versions used in labs.

  Because subagents can nest (correction 2), one course session can start one
  subagent per deck. Under `-p` those nested calls must run in the foreground, or
  each deck must run as a separate process. A plugin workflow also fits the batch
  (no mid-run input, phases, schema-validated agent output). A workflow script
  cannot call `Date.now()`, so today's date is passed in through `args`
  (reported).

**H4. The implementation order does not serve the immediate need (§7).**
- **Problem:** The shared developments search and the course summary come last,
  although §8 says a course run needs them to stay affordable. The PPTX output
  waits for `deckstate.py`, which it does not use. Modernize's own bookkeeping
  stays in prose: merging research batches, picking claims for second checks,
  counts, each deck's overall rating, validating `plan.json`, and reading the
  ticked checklist. That repeats problem P1, and §3 shows the result.
- **Recommendation:**
  1. `ingest.py`, `fetch_source.py`, `check_quotes.py`, and script-computed counts
     and verdicts for review and modernize.
  2. The modernize report (including the PPTX output) and the course batch, as a
     project-local skill, run on one course.
  3. Measure cost and precision.
  4. Package as a plugin.
  5. `deckstate.py` for `deck-create`.
  6. Marp apply mode.

### MEDIUM

**M1. MUST/SHOULD/OPTIONAL ratings are hard to defend (§6.8 step 3b).**
- **Problem:** The agent that finds an item also rates it. The second check covers
  date, maturity, and statement, but not priority. "Widely adopted" cannot be
  supported by primary sources, because release notes show that a feature exists,
  not that people use it.
- **Recommendation:** Derive priority from recorded criteria.
  - Maturity sets a ceiling: announced and preview items cannot be MUST.
  - A MUST either makes a claim on the deck wrong, or it affects a learning
    objective and has two independent signs that the field now teaches it: current
    official documentation, a new textbook edition or survey, or other courses'
    syllabi.
  - An independent agent re-rates every MUST.
  - Before showing an item, check it against this deck and its neighbours
    ("already on slide N").

**M2. OUTDATED is under-defined and has two owners (§6.7, §6.8 step 3a).**
- **Problem:** Review gives OUTDATED to the fact-checker, while modernize lists a
  `currency-checker` that the text never uses. No evidence rule exists, so a
  current documentation page that simply does not mention the old behaviour will
  be read as a change. "Current" is not always what students use: a course whose
  labs run Spark 3.5 should not get "outdated against the newest release" as a
  MUST. `--as-of` and "baseline date" name one concept twice.
- **Recommendation:**
  - Define OUTDATED as: a dated source shows that the state changed after a source
    that supported the claim. Record both sources. Mark "stale when written" when
    the change predates the content date.
  - Add `target_versions` to the configuration.
  - Use one claim-check stage and one rubric in `severity.md` for both review and
    modernize.
  - Let the change plan decide the kind of fix: a corrected sentence or new
    content.

**M3. Prioritizing claims by volatility saves nothing on this year's run (§6.6).**
- **Problem:** Last year's PPTX decks have no provenance. Also, "stable = described
  in a paper" would put "Trino keeps intermediate data in memory" in the stable
  class, because a 2019 paper describes it, and skip exactly the motivating case.
- **Recommendation:** Select claims by rule. Check every claim that names a
  product, version, or vendor, or that contains a number. Treat as stable only
  algorithm claims that name no system. Give each research agent a batch of 5–8
  claims.

**M4. Tying every INSERT to a removal is fragile (§6.8 step 4).**
- **Problem:** If the author approves an INSERT but not its paired removal, the
  result is undefined. The planner does not know what is examined, used in labs,
  or covered next week, so REMOVE and MERGE are the riskiest suggestions and come
  with the least information.
- **Recommendation:** Report the net slide change against the budget. List
  compressions as separate items, each with a reason. Let the author mark sections
  as protected. Require course context in batch runs.

**M5. The PPTX output could be far more useful (§6.8 step 6b).**
- **Problem:** Slide numbers shift as soon as the author inserts a slide. Exact old
  text from extraction often will not match PowerPoint's text runs. New slides in
  Markdown cannot be pasted into PowerPoint.
- **Recommendation:**
  - Produce a copy of the PPTX with each slide's change items in its speaker notes,
    using python-pptx. The slides themselves stay untouched.
  - Locate items by slide title plus a short text snippet, not by number.
  - Build the approved new slides as a small PPTX on the deck's own slide master.
  - Accept a PPTX together with its PDF export.

**M6. The 2-of-3 vote in review targets the wrong source of error (§6.7).**
- **Problem:** False CRITICAL findings come mostly from research: wrong sources, or
  opinion files like `claim_036.txt`. Three checks against the same file will
  agree with each other. Dropping a finding that fails the vote also loses
  information.
- **Recommendation:** For each CRITICAL, run a second research pass that does not
  see the first source, then check again. Record the majority verdict and
  severity.

**M7. Risks in moving the bookkeeping into `deckstate.py` (§6.4).**
- **Problem:** When a script fails, a headless orchestrator tends to hand-edit the
  JSON until the check passes. Choosing SURGICAL or REWRITE is a judgment, yet the
  `feedback` subcommand would make it.
- **Recommendation:**
  - Write small synthetic fixtures with expected outputs, and use the old
    workspaces only to test parsing.
  - Publish JSON Schemas, and make validation errors name the batch and entry to
    re-run.
  - Use a plugin PreToolUse hook to block direct edits of files the scripts own and
    of `output/slides.md`.
  - Replace the three carry-forward rules with one verdict cache keyed by
    (claim ID, normalized bullet line, source hash).
  - Have the fact-checker output a `fix_kind` field.

**M8. Cost has no estimate, no cap, and no way to resume (§8).**
- **Problem:** Logged sessions cost $7.20–31.05, with a median of about $12.80. The
  one run of the current `generate.md` is the $31 one. Modernize does at least as
  much web research, so 15 decks plausibly cost $150–450 (reviewer estimate).
- **Recommendation:**
  - Choose a model per role: a cheaper model for extraction and topic maps, the
    strongest model for priority and verdict judgments.
  - Make every step skip itself when its output already exists.
  - Pilot 2 decks with a cost cap and keep the logs.

### LOW

- **L1. Components named in one place and missing in another.**
  - The topic-map agent, the agent that checks findings, and the finding-to-deck
    mapping have no names.
  - The modernize diagram omits the researcher, fact-checker, and writer, which
    steps 3a and 6a use.
  - `currency-checker` is never referenced in the text.
  - No step produces the "estimated effort" in the course summary.
  - No thresholds define light refresh, significant update, and rebuild.
- **L2. Claim IDs.** `claim:{objective_letter}:{nnn}` does not fit review or
  modernize, which have no objectives. Include the deck slug so IDs stay unique
  across a course, and accept the old IDs.
- **L3. Format independence.** §1 promises independence from Marp, but only the
  Marp frontmatter becomes configurable. If last year's decks are Beamer, ingest
  the `.tex` source, which can be patched like Marp. Open question: Marp turns HTML
  comments into presenter notes, so hidden `<!-- claim:id -->` tags may show up in
  speaker notes.
- **L4. Skill arguments.** The signatures omit the baseline, budget, course
  context, and `--apply`. Make the author checkpoint depend on an argument, with
  the checklist file as the only approval path. `--apply` reuses `plan.json` with
  stable item IDs and does not rerun steps 1–4.
- **L5. Launcher safeguards.** Keep the wall-clock timeout, stdin from `/dev/null`,
  the stream log (the only cost evidence), and the turn limit in the batch wrapper.
  Pass `--plugin-dir` explicitly, because `--bare` mode skips installed plugins.
- **L6. Rerunning code blocks.** Code from PPTX and PDF decks has no EXEC_TEST
  markers, PDF text loses indentation, and Spark code needs a session and data.
  Limit modernize to static API and deprecation checks.
- **L7. Practical-course decks.** Modernize ignores `workbook.md` and
  `solutions.md`. Re-validating exercises against current models is the obvious
  refresh step for course decks.
- **L8. Dependencies.** State how PyMuPDF, python-pptx, and an HTML-to-text library
  get installed, for example by a SessionStart hook that installs into
  `${CLAUDE_PLUGIN_DATA}`.
- **L9. Configuration outside the repository.** The current permission and sandbox
  setup lives in `.claude/settings.json`, which `.gitignore` excludes. The
  launchers also depend on `jq` and `timeout`. The plugin's README has to replace
  that knowledge.

## 5. Keep as is

- Research before outline, the claim registry as the only source of facts,
  severity-gated revision, and MINOR issues as inline advisory comments.
- The non-determinism handling (carry-forward, best verdict for identical text,
  resampling), moved into code.
- The split between scripts (one correct answer), subagents (judgment), and
  tool-limited roles, including a fact-checker without web access.
- `ingest.py` producing `slides.json` with speaker notes, tables, code, and a flag
  for image-heavy slides.
- The primary-source rule, the maturity field, and recording what was searched
  when a volatile claim is found unchanged.
- One shared developments search per course, including findings that fit no
  existing lecture.
- Report, then author approval, then apply; no in-place PPTX editing.
- The `published` field. Also add `applies_to_version`.
- Measuring on one course before running all of them.

## 6. Suggested revisions to the proposal

1. Apply the corrections in section 2. In particular, restate the guarantee as
   "only tagged bullets are checked", and add an untagged-fact check to
   `deck-create` and `deck-review`.
2. Rewrite §6.8 and §6.9 around H1, H3, M1, M2, M4, and M5:
   - a current-state survey instead of a date window;
   - three batch phases and a course manifest;
   - criteria-based priorities;
   - one OUTDATED definition;
   - annotated PPTX output.
3. Add `fetch_source.py` to §6.5 and drop LOW-by-default for sources that cannot be
   fetched (H2).
4. Replace §7 with the order in H4.
5. Track M3, M6, M7, M8, and the LOW items as design notes for the stages that
   need them.
