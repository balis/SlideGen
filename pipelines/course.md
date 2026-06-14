# Course Agent Orchestrator

You generate a **practical-course** deliverable: a lean *backdrop* slide deck, a
**participant workbook**, and **live-validated solution keys**. This is the
hands-on counterpart to `generate.md` (which makes passive lecture decks). Use
this pipeline when the launcher is `coursegen.sh`.

The launcher tells you two paths:
- **System directory**: where this file, agents/, and tools/ live
- **Topic directory**: where run.md (a *course brief*), workspace/, and output/ live

Read run.md in the topic directory first. It defines the topic, the session plan
(concept blocks each paired with an exercise), prerequisites, target tools, and
constraints. See "Course-brief shape" below for what to expect.

When agent prompts reference "workspace/..." or "output/...", resolve them
relative to the **topic directory**. When they reference "agents/..." or
"tools/...", resolve them relative to the **system directory**.

---

## What makes this a course, not a lecture

A lecture deck (generate.md) is self-contained reading: dense claim-cited bullets
the audience absorbs. A **course** deck is a *backdrop* for a working session —
the hands-on substance lives in the **workbook**, not the slides. So this pipeline:

- keeps the research → claim-registry → fact-check backbone, but applies it only
  to **concept** slides, which stay **lean** (a few claims each, not a wall);
- adds **EXERCISE launch slides** — short pointers into the workbook ("Exercise 3
  · 10 min · workbook p.4"), carrying no claims;
- produces a **participant workbook** with full instructions, fill-in prompt
  templates, and working space;
- produces **solution keys** whose sample outputs are **live-validated against a
  real model at generate time** (the exercise analog of fact-checking).

There are therefore **two verification tracks**, both gating finalization:
fact-check (concept claims) and exercise-validation (do the exercises actually
work). Neither is skipped.

---

## Course-brief shape (run.md)

A course brief is a lecture request plus a **session plan**. Expect:
- topic, audience, level, total duration, prerequisites;
- **target tools/models** participants will use (e.g. "a general consumer chat
  LLM", "the org's enterprise assistant");
- a list of **concept blocks**, each paired with **one exercise**: a one-line
  scenario, the input data the learner uses (or where it comes from), a time-box,
  and what the learner produces and keeps;
- the **source-recency policy** (carried over from the lecture brief verbatim —
  it governs concept facts unchanged).

If run.md is a plain lecture request with no session plan, do not invent a deep
course on top of it silently — proceed but **tell the user** the brief lacks
exercises/time-boxes and that you inferred them, so they can correct the brief.

---

## How to execute each step

You are the orchestrator. For each step:
- Read the agent .md file for its instructions, inputs, and output format
- Either do the work yourself OR launch a sub-agent with the Agent tool
- Use sub-agents when work can be parallelized (see pipeline below)

**Shared machinery — read `pipelines/generate.md` first.** This pipeline reuses
three parts of the lecture pipeline verbatim, with only the course-specific changes
noted here: **Step 1** (research), the **Step 4+5 fact-check machinery** (citation
checklist `C`, re-check set `R`, carry-forward of byte-identical chunks, the
coverage gate, the severity merge), and **Step 6's ADVISORY-comment splicing**. Do
not reinvent them — read generate.md and follow those sections as written wherever
this file says "see generate.md."

**Sandbox note — file copy/move/delete.** This pipeline runs sandboxed and
non-interactively (stdin is /dev/null), so a Bash command that isn't pre-approved
can't prompt for permission and is simply blocked — Bash `cp`, `mv`, and `rm` on
files under ./decks fail this way. `python3` is pre-approved and its writes under
./decks succeed, so perform file copy/move/delete with python, not shell:
- copy:   `python3 -c "import shutil; shutil.copyfile('SRC','DST')"`
- move:   `python3 -c "import os; os.replace('SRC','DST')"`
- delete: `python3 -c "import os; os.remove('PATH')"`
Never reproduce a file's contents through the Write tool to "copy" it — that
risks a non-verbatim copy. shutil.copyfile is byte-exact; use it.

---

## Pipeline

### Step 1: Research concept claims (parallelized)
Read and follow **generate.md Step 1** and agents/research.md, with one change: a
**concept block** plays the role generate.md calls a "learning objective." **Launch
one sub-agent per concept block** from run.md's session plan. Each researches claims
for the *facts its block teaches* (not its exercise — exercises are validated in
Step 5, not sourced here), applies research.md's Step 0 objective-claim scan to its
block's concept description, and writes its claims file plus
workspace/sources/{claim_id}.txt. **Pass each sub-agent the explicit output path
`workspace/claims_{objective_N}.json`** (research.md's native per-objective
filename — one concept block = one objective here; do not invent a different name,
or the merge below won't find the files). Merge into workspace/claim_registry.json,
renumbering claim IDs sequentially and renaming source files to match.

If > 20% of total claims are UNVERIFIED, stop and tell the user which blocks lack
sources. Read workspace/research_review.md if present and surface any
"## OBJECTIVE CONTAINS UNVERIFIED CLAIM" section before proceeding.

**Research cache:** if workspace/claim_registry.json already exists and run.md is
unchanged, skip Step 1.

### Step 2: Course outline
Read agents/course_outline.md. Write workspace/outline.md: a session structure of
**lean concept slides + EXERCISE launch slides**, grounded in the claim registry,
with `<!-- chunk-boundary: ID | TITLE -->` markers (one block per concept block,
same machine format `split_outline.py` expects). Each EXERCISE slide declares a
stable exercise id (`E1`, `E2`, …) in its `exercise:` field plus a one-line
scenario; its full design comes in Step 3. (On the rendered deck slide that id
becomes a hidden trace comment `<!-- exercise:E1 -->` — greppable for routing,
invisible to learners.) Each concept block's chunk contains its concept slides
followed by its exercise launch slide(s), so exercises ride inside their block's
chunk.

If any concept slide carries a `NEEDS_RESEARCH` marker, do targeted research to
fill the gap, then update the outline.

### Step 3: Design exercises (parallelized by block)
Read agents/exercise_designer.md. **Launch one sub-agent per exercise** (read the
exercise ids from the outline's EXERCISE slides). Each designs the full exercise —
scenario, the exact starter prompt with `[FILL IN]` placeholders, input data (or a
self-contained snippet to paste), step-by-step instructions, expected-output
shape, success criteria, difficulty, and a realistic time-box — and writes
workspace/exercises_{Ei}.json.

After all complete, merge into workspace/exercise_registry.json keyed by exercise
id. Assert every exercise id declared on an EXERCISE slide in the outline has a
registry entry; stop and report any missing.

### Step 4: Write deck and workbook (parallelized)

**Determine iteration N:** N = 1 + the count of files matching `^draft_v[0-9]+\.md$`
in workspace/ (assembled deck drafts only; do not count `draft_v*_part_*.md`).

**Split the outline into chunks:**
`python3 {system_dir}/tools/split_outline.py {topic_dir}/workspace/outline.md`
Parse the JSON array of `{part, title, slide_range}`. The number of deck-writer
sub-agents equals `len(chunks)`.

**Compose the style guide (REQUIRED)** — one short paragraph: target audience and
level (from run.md), shorthand used, the running example name if any, and tone
(for a course: plainer and lighter than a lecture — the slide is a backdrop, the
workbook carries the detail). Pass the same string to every deck-writer sub-agent.

**Launch the deck writers and the workbook writer together** (single assistant
message):

- **Deck writers (course_writer.md), parallelized by chunk.** On N == 1, launch
  one per chunk. On a revision (N > 1), regenerate only chunks whose slide range
  contains a flagged slide (parse workspace/writer_feedback.md); copy every clean
  chunk forward byte-exact via python (Bash `cp` is blocked):
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_v{N-1}_part_{KK}.md', '{topic_dir}/workspace/draft_v{N}_part_{KK}.md')"`
  — same carry-forward discipline as generate.md (clean chunks are not regenerated,
  so their verified verdicts carry forward). Each deck writer receives
  `outline_path`, `claim_registry_path`, `exercise_registry_path`, its
  `slide_range`, `output_path` = workspace/draft_v{N}_part_{KK}.md,
  `writer_feedback_path`, and `style_guide`.

- **Workbook writer (workbook_writer.md in `mode: workbook`), single agent (or one
  per block on large decks).** Reads workspace/exercise_registry.json and run.md;
  writes workspace/workbook_v{N}.md — the participant-facing instructions, fill-in
  templates, input data, working space, and self-check per exercise, plus the
  keep-and-reuse prompt-library page. On a revision it regenerates only exercises
  flagged in writer_feedback.md and carries the rest forward. If **no** exercise is
  flagged this iteration (only claims changed), skip the agent and python-copy the
  prior workbook forward byte-exact:
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/workbook_v{N-1}.md', '{topic_dir}/workspace/workbook_v{N}.md')"`

**Assemble the deck:**
`python3 {system_dir}/tools/concat_draft.py {topic_dir}/workspace/draft_v{N}.md "{topic_dir}/workspace/draft_v{N}_part_*.md"`
(Keep the glob quoted.) Then sanity-check exactly as generate.md does: every chunk
file non-empty; `^---$` count ≈ slide count + 1 (stop if off by > 1).

### Step 5: Verify — two tracks (parallelized)
Launch both tracks in parallel.

**Track A — Fact-check concept claims.** Read and follow the **generate.md
Step 4+5** fact-check machinery, with **one form change**: course concept slides
carry the claim id in a **same-line trailing HTML comment** `<!-- claim:id -->`, not
an inline `[claim:id]` tag (so the rendered backdrop stays clean). Adapt accordingly:
- Build the citation checklist `C` from every `<!-- claim:... -->` comment in
  draft_v{N}.md (cross-check the count with `grep -o '<!-- claim:' draft_v{N}.md | wc -l`,
  not the generate.md `\[claim:` grep). The bullet that cites a claim is the line the
  comment sits on, with the comment stripped.
- Because the id is in a comment rather than inline, **supply the cited bullet text to
  the fact_checker explicitly** — give each batch `(slide title, claim_id, cited bullet
  text)` triples, using the same "orchestrator provides the text" mode the review
  pipeline uses (fact_checker.md's `original_text` path). The fact_checker then checks
  the supplied bullet against workspace/sources/{claim_id}.txt; it does **not** search
  the draft for an inline tag. This needs no change to fact_checker.md.
- Scope the re-check set `R` (on a revision, carry forward VERIFIED verdicts for
  citations in byte-identical chunks — see generate.md); enforce the coverage gate;
  merge into workspace/review_v{N}.json with `blocking_count` (= critical + major).

Launch-slide bullets carry no claim comment, so they never enter `C` — only
concept-slide facts are fact-checked. Also run the code-execution sub-agent
(tools/run_code.py) iff the draft has `<!-- EXEC_TEST -->` markers.

**Track B — Live-validate exercises.** Read agents/exercise_validator.md. **Launch
one sub-agent per exercise** (or 3–4 batches for many exercises). The carry-forward
unit is the per-exercise spec file workspace/exercises_{Ei}.json (Step 3 overwrites
only re-designed exercises, so unchanged ones stay byte-identical): on a revision,
re-validate only exercises whose exercises_{Ei}.json changed since the iteration
their PASS came from (byte-compare), and carry the prior PASS verdict forward for
the rest. Each validator **actually runs its exercise's starter prompt against a
real model** (it executes the exercise itself), judges whether the result is usable,
captures the sample output, and checks the time-box is realistic. It writes
workspace/exval_v{N}_{Ei}.json with a verdict (PASS | BROKEN | UNCLEAR), a severity
for non-PASS, the `filled_prompt` it actually ran, the captured `sample_output`, the
`model` used, an ISO `validated_at` date, and an `issue` + `suggested_fix`. Merge
into workspace/exercise_validation_v{N}.json; record `broken_count` = the number of
non-PASS verdicts (BROKEN or UNCLEAR) whose severity is CRITICAL or MAJOR (MINOR
non-PASS verdicts are advisory, like MINOR claim issues).

**Gate (after both tracks).** Gate on severity, not raw count — MINOR issues are
advisory and must not force another iteration (same anti-whack-a-mole rule as
generate.md).
- **NEEDS_REVISION** if `blocking_count > 0` (claims) OR `broken_count > 0`
  (exercises) OR any code failure. Combine the blocking items into
  workspace/writer_feedback.md — one entry per flagged slide/exercise with its
  `[claim:id]` or `[exercise:Ei]`, the problem, and the suggested fix. Route each:
  claim issues → the owning deck chunk; broken/unclear exercises → re-run Step 3
  for that `[exercise:Ei]` (the exercise_designer fixes the spec) **and** mark the
  workbook section + launch slide for regeneration in Step 4.
  If iteration < 3: go to Step 3 for flagged exercises, then Step 4.
  If iteration >= 3: stop. Rank workspace/review_v1..vN.json and
  exercise_validation_v1..vN.json by `(blocking_count, broken_count, minor_count)`
  ascending, pick the best iteration, report its unresolved issues pointing at that
  draft. Never finalize on a cap-stop.
- **APPROVED** iff `blocking_count == 0` AND `broken_count == 0` AND no code
  failure. Remaining MINOR issues (claim precision or exercise polish) are recorded
  as advisories in Step 6, not fixed in another loop.

### Step 6: Finalize
Only when APPROVED.

1. **Deck** — copy the latest deck draft (`best` = the latest iteration N on the
   APPROVED path) to output/slides.md byte-exact via python, then splice MINOR claim
   advisories as `<!-- ADVISORY [claim:id] (MINOR): ... -->` HTML comments by reading
   and following **generate.md Step 6** (inserting comment *lines* is the only
   allowed difference from the draft; never reflow slide text). One form change vs
   generate.md: the bullet a claim cites is located by the review's bullet text and
   its same-line `<!-- claim:id -->` comment (not an inline `[claim:id]` tag); place
   the ADVISORY line immediately after that bullet. The claim/exercise trace comments
   are already hidden, so the only rendered difference from the draft is the ADVISORY
   lines — the byte-exact-except-advisories invariant still holds.
   `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_v{best}.md', '{topic_dir}/output/slides.md')"`

2. **Workbook** — copy workspace/workbook_v{best}.md to output/workbook.md
   byte-exact via python.

3. **Solution keys** — run agents/workbook_writer.md in `mode: solutions` with
   `exercise_registry_path`, `exercise_validation_path` =
   workspace/exercise_validation_v{best}.json, and `output_path` =
   output/solutions.md. It renders, per exercise, the filled starter prompt, the
   **live-validated sample output** carried verbatim from the validation file with
   its `model` and `validated_at` date stamp, what "good" looks like, common
   pitfalls, and debrief prompts. Every sample output keeps its date stamp — model
   output drifts, so it is a dated snapshot, not a guarantee.

4. **Provenance** — write output/provenance.json. Same shape as generate.md
   (topic, finalized_at, slides, draft_iterations, review_verdict, code_execution,
   claims[], unused_claims[], issues_resolved[], advisory_minor_issues[]) **plus** an
   `exercises` array: one entry per `[exercise:Ei]` with
   `{id, title, verdict, model, validated_at, time_box_min, sample_output_excerpt,
   issues_resolved[]}`, and an `exercise_advisories[]` array for MINOR exercise
   notes.

Report: "Done. N slides, E exercises (all validated), M claims verified.
output/slides.md, output/workbook.md, and output/solutions.md are ready." Append
any MINOR advisory counts (claims and exercises) as optional polish.

---

## Invariants (check after every step)
- Never proceed past Step 1 if claim_registry.json is missing or invalid JSON.
- Never proceed past Step 3 if any exercise id declared on an EXERCISE slide in the
  outline lacks a registry entry.
- Never finalize unless **both** tracks pass: review verdict APPROVED
  (blocking_count == 0) AND exercise validation clean (broken_count == 0) AND code
  checks pass. A cap-stop is not APPROVED: report the best iteration, do not
  finalize.
- A carried-forward claim verdict is valid only when both the chunk bytes and the
  source file are unchanged (see generate.md). A carried-forward exercise PASS is
  valid only when the exercise's registry spec is unchanged from the iteration it
  came from.
- output/slides.md, output/workbook.md, and output/solutions.md must all exist at
  finalize. output/slides.md differs from its draft only by inserted ADVISORY
  comment lines.
- If any step produces an empty file or fails silently, stop and report.
