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

**Launch one writer sub-agent per chunk, in parallel** (all Agent tool
calls in a single assistant message). Each sub-agent receives:
- `outline_path`: workspace/outline.md
- `claim_registry_path`: workspace/claim_registry.json
- `slide_range`: the chunk's `[start, end]`
- `output_path`: workspace/draft_v{N}_part_{KK}.md (KK = zero-padded 2-digit
  part index, e.g. `part_00`, `part_01`, ..., `part_09`, `part_10`)
- `writer_feedback_path`: workspace/writer_feedback.md (pass this path
  whether or not the file exists; the writer checks for existence)
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

**Sub-agents B1..B4: Fact-Check (parallelized by section)**
- Read agents/fact_checker.md for instructions.
- Split the draft's claim-bearing slides into 3-4 roughly equal batches.
- Launch one sub-agent per batch. Each checks its slides' [claim:id] references
  against the corresponding workspace/sources/{claim_id}.txt files.
- Each sub-agent writes workspace/review_vN_batch_{K}.json with its verdicts.
- After all complete, merge into workspace/review_vN.json.
  The merged file must include the **full claim_verdicts entries** for all
  MISREPRESENTED and UNVERIFIED claims from every batch — with their bullet text,
  source excerpt, issue description, and suggested fix. VERIFIED claims can be
  represented as a count only. Do not summarize or omit detail for flagged claims
  during the merge. Verdict is APPROVED only if every batch verdict is VERIFIED.

**After both complete**, merge feedback:
- If code failures exist OR review verdict is NEEDS_REVISION:
  Combine issues into workspace/writer_feedback.md.
  If iteration < 3: go to Step 3.
  If iteration >= 3: stop and report unresolved issues to the user.

### Step 6: Finalize
If review verdict is APPROVED and code results all PASS (or were skipped):
  Copy latest draft_vN.md to output/slides.md.
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
- **Incremental re-check**: On revision loops (Step 3 → 4+5), only re-check claims and
  code blocks that changed between draft_v(N-1) and draft_vN. Unchanged claims keep their
  previous verdict.
- **Skip code execution**: If no `<!-- EXEC_TEST -->` markers exist in the draft,
  sub-agent A returns immediately with {blocks_found: 0, passed: 0, failed: 0}.

---

## Invariants (check after every step)

- Never proceed past Step 1 if claim_registry.json is missing or invalid JSON.
- Never proceed past Step 4+5 if review verdict is not APPROVED.
- Never overwrite output/slides.md unless all checks pass.
- If any step produces an empty file or fails silently, stop and report.
