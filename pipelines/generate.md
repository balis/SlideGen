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

**On a revision (N > 1), regenerate only the chunks that have feedback.**
Parse workspace/writer_feedback.md for the slide numbers it flags, and map each
flagged slide to its chunk via the chunk `slide_range`s from split_outline.py.
Then, in a single assistant message:
- For every chunk whose slide range contains at least one flagged slide:
  launch a writer sub-agent (inputs below). Each writer reads writer_feedback.md
  and addresses only the items in its own slide range (writer.md rule 8).
- For every chunk with **no** flagged slide: do **not** regenerate it. Copy the
  previous iteration's chunk file forward unchanged, byte-exact via python (Bash
  `cp` is blocked — see the Sandbox note):
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_v{N-1}_part_{KK}.md', '{topic_dir}/workspace/draft_v{N}_part_{KK}.md')"`
  Regenerating a clean chunk is not idempotent — the model rewrites already-
  verified bullets and can introduce new misrepresentations into slides that
  were correct — so clean chunks are carried forward verbatim and only
  re-verified in Step 4+5.

Each writer sub-agent receives:
- `outline_path`: workspace/outline.md
- `claim_registry_path`: workspace/claim_registry.json
- `slide_range`: the chunk's `[start, end]`
- `output_path`: workspace/draft_v{N}_part_{KK}.md (KK = zero-padded 2-digit
  part index, e.g. `part_00`, `part_01`, ..., `part_09`, `part_10`)
- `writer_feedback_path`: workspace/writer_feedback.md (pass this path
  whether or not the file exists; the writer checks for existence and
  addresses only the items in its slide range)
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
- Split the checklist into 3-4 roughly equal batches. Pass each sub-agent its
  **explicit list of (slide, claim_id) pairs** — not just a slide range. A bare
  slide range lets a batch silently sample a subset; an explicit list is a
  closed checklist the batch must return in full.
- Launch one sub-agent per batch. Each checks every assigned citation against
  the corresponding workspace/sources/{claim_id}.txt file and writes
  workspace/review_vN_batch_{K}.json with one claim_verdicts entry per
  assigned citation.
- **Coverage gate (before merging).** Sum the claim_verdicts entries across all
  batch files. If the total is less than `C`, or any batch returned fewer
  entries than it was assigned, the batch under-covered (fact_checker.md rule 7
  violated) — re-dispatch the deficient batch for its missing pairs and wait for
  it. Do **not** compute a verdict from an incomplete scan: partial coverage
  silently understates the misrepresentation count and corrupts the
  iteration-over-iteration comparison.
- After coverage passes, merge into workspace/review_vN.json.
  The merged file must include the **full claim_verdicts entries** for all
  MISREPRESENTED and UNVERIFIED claims from every batch — with their bullet text,
  source excerpt, issue description, and suggested fix. VERIFIED claims can be
  represented as a count only. Record `total_checked` (must equal `C`) and
  `misrepresented_count`. Do not summarize or omit detail for flagged claims
  during the merge. Verdict is APPROVED only if every batch verdict is VERIFIED.

**After both complete**, merge feedback:
- If code failures exist OR review verdict is NEEDS_REVISION:
  Combine the issues into workspace/writer_feedback.md — one entry per
  flagged slide with its [claim:id], the problem, and the suggested fix.
  Include code-execution failures the same way.
  If iteration < 3: go to Step 3.
  If iteration >= 3: stop. Do **not** assume the latest draft is the best —
  regeneration can leave an iteration worse than its predecessor. Compare
  `misrepresented_count` across all of workspace/review_v1.json ..
  review_vN.json, pick the lowest-scoring (best) iteration, and report the
  unresolved issues to the user pointing them at that draft
  (workspace/draft_v{best}.md), stating its score versus the latest. Never
  finalize on a cap-stop — no draft is APPROVED.

### Step 6: Finalize
If review verdict is APPROVED and code results all PASS (or were skipped):
  Copy latest draft_vN.md to output/slides.md, byte-exact via python (Bash `cp`
  is blocked — see the Sandbox note):
  `python3 -c "import shutil; shutil.copyfile('{topic_dir}/workspace/draft_vN.md', '{topic_dir}/output/slides.md')"`
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
      "issue": "Brief description of what was wrong",
      "resolution": "Brief description of how it was fixed"
    }
  ]
}
```

  Report: "Done. N slides, M claims verified. output/slides.md is ready."

---

## Performance notes

- **Research cache**: If workspace/claim_registry.json already exists and run.md has not
  changed, skip Step 1 entirely.
- **Carry clean chunks forward**: On a revision (N > 1), only chunks with feedback
  in their slide range are regenerated; chunks with no feedback are copied forward
  from the previous iteration unchanged (see Step 3). This avoids re-introducing
  errors into verified slides and cuts writer cost to the flagged fraction.
  Verification (Step 4+5) still re-checks the whole draft every iteration — carried-
  forward text is cheap to re-verify, and the full scan still catches anything an
  earlier pass missed.
- **Skip code execution**: If no `<!-- EXEC_TEST -->` markers exist in the draft,
  sub-agent A returns immediately with {blocks_found: 0, passed: 0, failed: 0}.

---

## Invariants (check after every step)

- Never proceed past Step 1 if claim_registry.json is missing or invalid JSON.
- Never proceed past Step 4+5 if review verdict is not APPROVED.
- Never overwrite output/slides.md unless all checks pass.
- If any step produces an empty file or fails silently, stop and report.
