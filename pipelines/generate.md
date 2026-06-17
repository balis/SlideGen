# Slide Agent Orchestrator

You generate verified lecture slides. The launcher script tells you two paths:
- **System directory**: where this file, agents/, and tools/ live
- **Topic directory**: where run.md, workspace/, and output/ live

Read run.md in the topic directory first. It defines the topic, objectives, and constraints.

When the agent prompts reference files like "workspace/..." or "output/...", resolve them
relative to the **topic directory**. When they reference "agents/..." or "tools/...",
resolve them relative to the **system directory**.

---

## How to execute each step

You are the orchestrator. For each step:
- Read the agent .md file for its instructions, inputs, and output format
- Either do the work yourself OR launch a sub-agent with the Agent tool
- Use sub-agents when work can be parallelized (see pipeline below)

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

### Step 1: Research (parallelized)
Read agents/research.md for instructions and run.md for the topic.
**Launch one sub-agent per learning objective** from run.md using the Agent tool.
Each sub-agent researches claims for its objective and writes:
- Its portion of claims to workspace/claims_{objective_N}.json
- Source files to workspace/sources/{claim_id}.txt

After all sub-agents complete, merge their outputs into workspace/claim_registry.json.
**During the merge, renumber claim IDs sequentially across all objectives** (e.g.,
objective 1 gets 001-008, objective 2 gets 009-015, etc.). For each renumbered claim,
rename the corresponding source file in workspace/sources/ to match the new ID.
Delete or rename any stale source files so that every entry in claim_registry.json
has a source file at workspace/sources/{claim_id}.txt with an exactly matching name.

If > 20% of total claims are UNVERIFIED, stop and tell the user which objectives lack sources.
Also read workspace/research_review.md if it exists (the research agents write it): if it
contains an "## OBJECTIVE CONTAINS UNVERIFIED CLAIM" section, stop and surface those
objective-level assertions to the user before proceeding.

### Step 2: Outline
Read agents/outline.md for instructions.
Write workspace/outline.md grounded in the claim registry.
If any slides contain NEEDS_RESEARCH markers, do targeted research to fill gaps,
then update the outline.

### Step 3: Write (parallelized by section)
Read agents/writer.md for instructions.

**Determine iteration N:** N = 1 + the count of files matching the regex
`^draft_v[0-9]+\.md$` in workspace/ (i.e. only assembled drafts; do **not**
count `draft_v*_part_*.md` chunk files, which are intermediate artifacts).

**Split the outline into chunks:**
Run: `python3 {system_dir}/tools/split_outline.py {topic_dir}/workspace/outline.md`
This emits a JSON array of chunks, each with `{part, title, slide_range}`.
Parse it. The number of writer sub-agents you launch below equals
`len(chunks)`.

**Compose the style guide (REQUIRED) before launching any sub-agent.**
Write one short paragraph (~3-5 sentences) covering:
- target audience and level (from run.md)
- abbreviations or shorthand used in this deck
- the running example name, if any
- tone (e.g., "graduate-level, technical, neutral; sparing use of 'we'")
Pass the *same* string to every chunk sub-agent. **Do not skip this step**
— writer.md rule 10 requires it, and without it chunks drift in voice
across section boundaries.

**On the first iteration (N == 1), launch one writer sub-agent per chunk,
in parallel** — all Agent tool calls in a single assistant message.

**On a revision (N > 1), apply only the changes feedback calls for — never
regenerate a chunk wholesale just because it contains one flagged bullet.**
Regenerating a chunk is not idempotent: the model rewrites already-verified
bullets in the *unflagged* slides that share the chunk and can introduce fresh
misrepresentations into text that was correct. The routing below confines each
change to the bullet that needs it.

workspace/writer_feedback.md (built in Step 4+5) tags every blocking item as
**SURGICAL** or **REWRITE**, and for surgical items carries the exact **OLD** line
and exact **NEW** line. Parse it, map each flagged slide to its chunk via the
`slide_range`s from split_outline.py, and classify each chunk. Then, in a single
assistant message, handle every chunk:

- **Clean chunk (no feedback in its slide range):** do **not** regenerate it. Copy
  the previous iteration's chunk file forward unchanged, byte-exact via python (Bash
  `cp` is blocked — see the Sandbox note):
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_v{N-1}_part_{KK}.md', '{topic_dir}/workspace/draft_v{N}_part_{KK}.md')"`

- **Surgical-only chunk (every feedback item in its range is SURGICAL):** do **not**
  launch a writer. Copy the prior chunk file forward byte-exact (command above), then
  *you* (the orchestrator) apply each surgical edit to the copied file: Read it, then
  for each item use the Edit tool to replace its exact **OLD** line with its exact
  **NEW** line. The OLD line must match exactly one line in the file; if it does not
  match uniquely, the feedback's OLD text is stale — stop and report rather than
  guessing. Record the (slide, claim_id) of every bullet you edit — that list is the
  chunk's only contribution to the re-check set `R` (Step 4+5). Every other bullet in
  the chunk stays byte-identical to the prior draft and carries its prior verdict
  forward. A literal line replacement touches only the flagged bullet, so verified
  neighbors cannot regress.

- **Chunk with any REWRITE item:** launch a writer sub-agent for that chunk. A REWRITE
  item needs judgment a literal replacement cannot express — restructuring a slide,
  splitting or merging bullets, removing or retagging a citation to a different
  claim/source, or content the fix only describes. Pass the writer `prior_chunk_path`
  (the prior chunk file) and require it to carry every non-flagged slide and bullet
  forward byte-identical, changing only the flagged bullets (writer.md rules 8 and 12).
  Fold any SURGICAL items in the same chunk into that writer's feedback so it applies
  them too — do **not** also run an orchestrator Edit pass on writer-rewritten text
  (the OLD lines would no longer match). Every (slide, claim_id) in a writer-touched
  chunk goes into `R`.

  **Enforce rule 12 when the writer returns (mechanical, not trust-based).** writer.md
  rule 12 tells the writer to change only the flagged bullets and carry every other line
  forward byte-identical, but that is a soft instruction the model can violate — in a
  real run a writer rewrote an *unflagged*, previously-VERIFIED bullet and regressed it.
  So verify: diff the returned `draft_v{N}_part_{KK}.md` against `prior_chunk_path` line
  by line (e.g.
  `python3 -c "import difflib,sys; a=open(sys.argv[1]).read().splitlines(); b=open(sys.argv[2]).read().splitlines(); print('\n'.join(difflib.unified_diff(a,b,lineterm='')))" PRIOR NEW`).
  **Every** differing line must belong to a slide+bullet named in this chunk's feedback.
  If an **unflagged** line changed, the writer overstepped: revert those specific lines
  to their `prior_chunk_path` bytes (re-Edit them back to the prior text), or re-dispatch
  the writer telling it explicitly to leave those bullets identical. Only flagged-bullet
  lines may differ from the prior chunk — this makes rule 12 an invariant, so a REWRITE
  for one slide cannot silently regress a verified neighbor. (After any revert, the
  reverted bullets are byte-identical to the prior draft and qualify for carry-forward;
  only the genuinely-changed flagged bullets remain in `R`.)

Each writer sub-agent receives:
- `outline_path`: workspace/outline.md
- `claim_registry_path`: workspace/claim_registry.json
- `slide_range`: the chunk's `[start, end]`
- `output_path`: workspace/draft_v{N}_part_{KK}.md (KK = zero-padded 2-digit
  part index, e.g. `part_00`, `part_01`, ..., `part_09`, `part_10`)
- `writer_feedback_path`: workspace/writer_feedback.md (pass this path
  whether or not the file exists; the writer checks for existence and
  addresses only the items in its slide range)
- `prior_chunk_path`: workspace/draft_v{N-1}_part_{KK}.md (revisions only —
  the previous version of *this* chunk; the writer starts from it and changes
  only the flagged bullets, carrying every other line forward byte-identical
  per writer.md rule 12)
- `style_guide`: the paragraph composed above

Each sub-agent writes its assigned slide range to its `output_path` (raw
slide content, no Marp frontmatter, no leading/trailing `---`).

**After all chunk sub-agents complete, concatenate:**
Run: `python3 {system_dir}/tools/concat_draft.py {topic_dir}/workspace/draft_v{N}.md "{topic_dir}/workspace/draft_v{N}_part_*.md"`
(Keep the glob quoted; the Python tool expands it internally.)

This produces the assembled `draft_v{N}.md` with the Marp frontmatter at
the top and `---` separators between chunks.

**Sanity-check the assembled draft:**
- Every chunk file must be non-empty. If any `draft_v{N}_part_{KK}.md` is
  missing or zero-byte, stop and report which part failed.
- Count `^---$` lines in the assembled `draft_v{N}.md`. With `S` total
  slides, expect `S + 1` separators: 2 from the frontmatter (open + close)
  plus `S - 1` between-slide separators (the join points concat inserted
  between chunks plus the slide separators inside chunks).
- If counts are off by more than 1 from the outline's slide count, stop
  and report — do not pass a malformed draft to Step 4+5.

### Step 4+5: Verify (parallelized)
**Launch two sub-agents in parallel:**

**Sub-agent A: Execute Code**
- Skip if the draft contains no `<!-- EXEC_TEST -->` markers.
- Run: python3 {system_dir}/tools/run_code.py {topic_dir}/workspace/draft_vN.md {topic_dir}/workspace/code_results_vN.json
- Write results to workspace/code_results_vN.json.

**Sub-agents B1..B4: Fact-Check (parallelized by batch)**
- Read agents/fact_checker.md for instructions.
- **Build the citation checklist first.** Scan draft_vN.md for every
  `[claim:id]` occurrence and record one `(slide title, claim_id)` pair per
  occurrence. This list is the authoritative set of citations that MUST be
  checked; note its length `C` (a claim cited on three slides counts three
  times). `grep -o '\[claim:' draft_vN.md | wc -l` gives C as a cross-check.
- **Scope the re-check set `R` (incremental verification).** On the first
  iteration (N == 1) every citation is re-checked: `R` = the full checklist `C`.
  On a revision (N > 1), do **not** re-fact-check a citation whose text did not
  change and already passed — re-checking byte-identical text against frozen
  sources cannot reveal a new truth, it only resamples the fact-checker's
  non-determinism and can flip a previously-VERIFIED claim to MISREPRESENTED,
  which wastes budget and blocks convergence. Partition `C`:
  - **Carry-forward set (skip re-check).** A citation skips re-check and keeps a prior
    VERIFIED verdict if it qualifies under **either** rule:
    - **Unchanged-and-passed:** it was VERIFIED in workspace/review_v{N-1}.json **and**
      its own bullet text is unchanged this iteration — i.e. **either (a)** it lives in
      a clean chunk carried forward byte-identical (`draft_v{N}_part_{KK}.md` is
      byte-identical to `draft_v{N-1}_part_{KK}.md`; confirm with a byte compare, e.g.
      `python3 -c "import sys;sys.exit(open(a,'rb').read()!=open(b,'rb').read())"`),
      **or (b)** it lives in a **surgically-edited** chunk (Step 3) and is **not** one
      of the (slide, claim_id) bullets you edited there (you applied those edits line
      by line, so you know exactly which lines changed; cross-check that the differing
      lines equal the lines you edited).
    - **(c) Verdict hysteresis (carry-best on identical bytes):** even if the citation
      was MISREPRESENTED or UNVERIFIED in review_v{N-1}.json, if its **current exact
      bullet text** is byte-identical to the `bullet` of a VERIFIED entry in **any**
      prior review (review_v1 .. review_v{N-1}), carry that VERIFIED verdict forward and
      exclude it from `R`. Sources are frozen after Step 1, so text that earned VERIFIED
      on those exact bytes once is correct on them always; a later MISREPRESENTED on the
      *same bytes* is fact-checker non-determinism, not a new truth. Without this, a
      noise-flagged claim re-enters `R` every round and can escalate
      (VERIFIED→MINOR→MAJOR) until it spuriously blocks finalization at the iteration
      cap — an observed real-run failure. Hysteresis is deliberately asymmetric:
      identical bytes keep their **best** historical verdict, never their worst, and a
      citation leaves this protection the moment its **text changes**.
    Carry the qualifying citation's prior VERIFIED verdict forward verbatim (severity
    null).
  - **Re-check set `R`:** everything else — every citation in a writer-regenerated
    chunk, every bullet you surgically edited this iteration, every citation that was
    MISREPRESENTED or UNVERIFIED in review_v{N-1}.json **and is not rescued by
    hysteresis rule (c)**, and any citation new to this draft. These are the only pairs
    batched out below.
- Split `R` into 3-4 roughly equal batches. Pass each sub-agent its
  **explicit list of (slide, claim_id) pairs** — not just a slide range. A bare
  slide range lets a batch silently sample a subset; an explicit list is a
  closed checklist the batch must return in full.
- Launch one sub-agent per batch. Each checks every assigned citation against
  the corresponding workspace/sources/{claim_id}.txt file and writes
  workspace/review_vN_batch_{K}.json with one claim_verdicts entry per
  assigned citation.
- **Coverage gate (before merging).** Sum the claim_verdicts entries across all
  batch files. If the total is less than `|R|`, or any batch returned fewer
  entries than it was assigned, the batch under-covered (fact_checker.md rule 8
  violated) — re-dispatch the deficient batch for its missing pairs and wait for
  it. Do **not** compute a verdict from an incomplete scan: partial coverage
  silently understates the misrepresentation count and corrupts the
  iteration-over-iteration comparison. (The gate is against `|R|`, the set you
  actually dispatched, not `C` — carried-forward citations are not in any batch.)
- After coverage passes, merge into workspace/review_vN.json.
  The merged set = the carried-forward VERIFIED verdicts + every fresh batch
  verdict. Include the **full claim_verdicts entries** for all MISREPRESENTED and
  UNVERIFIED claims — with their bullet text, source excerpt, `severity`, issue
  description, and suggested fix. For VERIFIED claims (fresh or carried-forward)
  write a **compact per-citation entry** — `{slide, claim_id, verdict:"VERIFIED",
  bullet:"<exact citing line>"}` — **not** a bare count: the next iteration's
  carry-forward **and verdict-hysteresis** lookups need to know exactly which
  (slide, claim_id) pairs passed **and the exact text that passed**, so review_vN.json
  must carry a verdict (with its `bullet` text) for every one of the `C` citations. Record `total_checked` (must equal
  `C` = carried-forward + `|R|`), `rechecked_count` (= `|R|`),
  `misrepresented_count`, and the severity breakdown `critical_count`,
  `major_count`, `minor_count`, plus `blocking_count` (= critical + major). Do not
  summarize or omit detail for flagged claims during the merge. **Verdict is
  APPROVED iff `blocking_count == 0`** (MINOR-only issues still approve — see the
  feedback step); otherwise NEEDS_REVISION.

**Consensus gate on newly-blocking verdicts (apply before reading the merge as final).**
A single fresh fact-check sample can over-score a claim — the same byte-identical bullet
has been observed scoring VERIFIED, then MINOR, then MAJOR across runs. So before a
citation that was **non-blocking in review_v{N-1}** (VERIFIED or MINOR there) is allowed
to count as CRITICAL/MAJOR in review_vN, re-sample it: dispatch **2 additional
independent fact-checker sub-agents** on just that (slide, claim_id) pair (same inputs as
the batch). Take the **majority of the 3** verdicts (the original batch verdict + the 2
resamples): accept the blocking severity only if **≥2 of 3** agree it is CRITICAL/MAJOR.
If the majority is non-blocking, record the majority verdict (VERIFIED, or MINOR with the
majority's issue/fix) in review_vN instead, and do **not** let it block. Then recompute
`blocking_count` and the severity breakdown from the post-consensus verdicts. Scope: gate
only **escalations** — a citation already CRITICAL/MAJOR in review_v{N-1} is genuine
carry-over work and needs no resample; a citation **new** to this draft is genuinely new
content and is checked normally (not gated). This stops single-sample noise from
manufacturing a spurious blocker, especially at the iteration cap where there is no round
left to fix it.

**After both complete**, gate on severity, not raw count. MINOR issues are
advisory — real, but they do not change the takeaway and must **not** force
another full iteration. Re-flagging stable MINOR nitpicks each round (a
previously-VERIFIED claim resurfacing as a different nitpick) is the whack-a-mole
that prevents convergence; the deck is "done" when nothing CRITICAL/MAJOR remains,
not when zero nitpicks remain.

- If code failures exist OR `blocking_count > 0` (verdict NEEDS_REVISION):
  Build workspace/writer_feedback.md from the **blocking** issues (CRITICAL/MAJOR)
  and any code failures — one entry per flagged bullet with its slide title and
  [claim:id]. **Classify and format each item so Step 3 can route it:**
  - Tag each item **SURGICAL** or **REWRITE**:
    - **SURGICAL** — the fix is a single self-contained line replacement: the
      review's `suggested_fix` is a concrete corrected bullet, the claim_id stays the
      same, and nothing structural changes (no splitting/merging bullets, no new
      slide, no hunting for a different source). Most dropped-qualifier and
      wrong-figure fixes are surgical.
    - **REWRITE** — the fix needs judgment: restructuring a slide, splitting or
      merging bullets, removing or retagging a citation to a different claim/source,
      or content the `suggested_fix` only describes rather than states verbatim.
  - For every **SURGICAL** item, record the exact **OLD** line (copy the citing line
    verbatim from draft_v{N}.md — leading `- `, any `**bold**`, and the trailing
    `[claim:id]` included) and the exact **NEW** line, formatted identically, so the
    orchestrator can apply it as a literal Edit with no reformatting. The NEW line is
    the review's `suggested_fix` wrapped to mirror the OLD line's formatting.
  - For every **REWRITE** item, state the problem and the intended fix as prose; the
    chunk's writer applies it.
  Code failures are REWRITE items (the writer must fix the code). You **may** also
  fold in a MINOR issue only when its chunk already has a writer scheduled for a
  REWRITE item (cheap while that chunk is open) — tag it the same way; otherwise
  leave MINORs advisory for Step 6. Never schedule a writer, or a surgical edit, for
  an otherwise-clean chunk on account of a MINOR alone.
  If iteration < 3: go to Step 3.
  If iteration >= 3: stop. Do **not** assume the latest draft is the best —
  regeneration can leave an iteration worse than its predecessor. Rank all of
  workspace/review_v1.json .. review_vN.json by `(blocking_count, minor_count,
  misrepresented_count)` ascending, pick the best iteration, and report its
  unresolved issues to the user pointing them at that draft
  (workspace/draft_v{best}.md), stating its severity breakdown versus the latest.
  Never finalize on a cap-stop — no draft is APPROVED.
- If `blocking_count == 0` and no code failures (verdict APPROVED): proceed to
  Step 6. Any remaining MINOR issues are not fixed in another loop — Step 6 records
  them in provenance and inlines them into output/slides.md as advisory comments.

### Step 6: Finalize
If review verdict is APPROVED and code results all PASS (or were skipped):
  Copy latest draft_vN.md to output/slides.md, byte-exact via python (Bash `cp`
  is blocked — see the Sandbox note):
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_vN.md', '{topic_dir}/output/slides.md')"`

  **Then annotate output/slides.md with the MINOR advisories** (only output/slides.md
  — never the draft part-files, which must stay byte-stable for the next run's
  carry-forward compare). For each MINOR issue, splice an HTML comment into
  output/slides.md so the author sees it in context while editing. Inserting comment
  *lines* is the **only** allowed difference between the draft and output/slides.md:
  never alter, reword, or reflow an existing slide line, so the slide content stays
  verbatim from the verified draft. Place each comment on the line immediately after
  the bullet it refers to — locate the bullet within its `## {slide title}` section
  by its `[claim:id]` tag and the review's bullet text; if it can't be uniquely
  located, put the comment directly under the slide heading. Format:
  `<!-- ADVISORY [claim:id] (MINOR): {issue} Suggested: {suggested_fix} -->`
  Do it in python (read lines, splice, write back — inserting lines preserves every
  original content byte); do **not** hand-retype slide text. These are HTML comments,
  so Marp keeps them out of the rendered slide (they surface as source/presenter
  notes), informing the author without reaching the audience. With no MINOR
  advisories, output/slides.md stays the byte-exact copy.

  Write output/provenance.json with this structure:

```json
{
  "topic": "...",
  "finalized_at": "ISO date",
  "slides": N,
  "draft_iterations": N,
  "review_verdict": "APPROVED",
  "code_execution": "PASS (X/X blocks) | SKIPPED (no EXEC_TEST markers)",
  "claims": [
    {
      "id": "claim:topic:concept:nnn",
      "statement": "The claim text from the registry",
      "source_url": "https://... or DOI",
      "source_title": "Human-readable source name",
      "source_file": "workspace/sources/{claim_id}.txt",
      "verdict": "VERIFIED",
      "slides_used_in": ["Slide Title 1", "Slide Title 2"]
    }
  ],
  "unused_claims": [
    {"id": "claim:topic:concept:nnn", "reason": "Not referenced in any slide"}
  ],
  "issues_resolved": [
    {
      "iteration": 1,
      "claim_id": "...",
      "slide": "...",
      "severity": "CRITICAL | MAJOR | MINOR",
      "issue": "Brief description of what was wrong",
      "resolution": "Brief description of how it was fixed"
    }
  ],
  "advisory_minor_issues": [
    {
      "claim_id": "...",
      "slide": "...",
      "issue": "MINOR precision note that did not block approval",
      "suggested_fix": "The rewrite the fact-checker proposed, for the author to apply at their discretion"
    }
  ]
}
```

  `review_verdict` is APPROVED when no CRITICAL/MAJOR issues remain; any unresolved
  MINOR issues go in `advisory_minor_issues` **and** as `<!-- ADVISORY ... -->`
  comments inline in output/slides.md (they do not block finalization). The two must
  agree — every `advisory_minor_issues` entry has exactly one matching comment.

  Report: "Done. N slides, M claims verified. output/slides.md is ready."
  If `advisory_minor_issues` is non-empty, add: "P minor precision notes recorded in
  provenance.json and inline as <!-- ADVISORY --> comments in slides.md — optional
  polish, not blocking."

---

## Performance notes

- **Research cache**: If workspace/claim_registry.json already exists and run.md has not
  changed, skip Step 1 entirely.
- **Surgical edits over chunk regeneration**: On a revision (N > 1), a known fix
  (a concrete replacement bullet, same claim_id) is applied by the orchestrator as a
  literal line edit to the carried-forward chunk — no writer runs, so the unflagged
  verified bullets sharing that chunk are byte-untouched and cannot regress. A writer
  runs only for a chunk with an open-ended REWRITE item (restructuring, retagging, new
  content), and even then it carries every unflagged bullet forward byte-identical
  (writer.md rule 12). Chunks with no feedback are copied forward unchanged. This is
  the fix for the regression mode where regenerating a chunk to repair one bullet
  rewrote — and broke — previously-verified neighbors in the same chunk.
- **Incremental verification**: Verification (Step 4+5) re-checks only the changed
  or previously-flagged citations on a revision — the re-check set `R`. Citations on
  byte-identical carried-forward chunks that already passed keep their prior VERIFIED
  verdict instead of being re-checked. On a surgically-edited chunk the granularity is
  per-bullet: only the bullets the orchestrator actually changed enter `R`; every
  other bullet keeps its prior verdict even though the file as a whole differs. Sources are frozen after Step 1, so identical
  bullet text against an identical source has a known-correct verdict; re-running the
  fact-checker on it cannot reveal a new truth, it only resamples the checker's
  non-determinism — which wastes the bulk of the fact-check budget (on a late
  revision the changed fraction is often a handful of bullets out of ~100) and can
  flip a stable claim to MISREPRESENTED, stalling convergence. The full checklist `C`
  is still rebuilt every iteration so `total_checked` stays comparable across
  versions; only the re-checked subset `R` shrinks to the changed fraction.
- **Skip code execution**: If no `<!-- EXEC_TEST -->` markers exist in the draft,
  sub-agent A returns immediately with {blocks_found: 0, passed: 0, failed: 0}.

---

## Invariants (check after every step)

- Never proceed past Step 1 if claim_registry.json is missing or invalid JSON.
- Never finalize (overwrite output/slides.md) unless the review verdict is
  APPROVED (blocking_count == 0) and code checks pass. A cap-stop is not APPROVED:
  report the best draft, do not finalize.
- A carried-forward verdict is valid only when the **bullet's own line** and its
  **source file** are unchanged from the iteration it came from — either the whole
  chunk is byte-identical, or the chunk was only surgically edited and this bullet was
  not one of the edited lines. If a source file was touched after Step 1, or the
  bullet's line changed (by a writer or a surgical edit), that citation belongs in `R`
  and must be re-checked — never carry a verdict across changed inputs.
- After the merge, assert `total_checked == C` (carried-forward + `|R|`). If they
  disagree, a citation was dropped or double-counted — stop and report.
- If any step produces an empty file or fails silently, stop and report.
