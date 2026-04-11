# Review Pipeline

You are running the slide-review pipeline. Your job is to fact-check an existing
slide deck and produce revision recommendations.

---

## Step 1: Ingest

Determine the input format and extract text:

- **Markdown (.md):** Read directly using the Read tool.
- **PDF (.pdf):** Read using the Read tool (it handles PDFs natively).
- **PowerPoint (.pptx):** Install python-pptx if needed (`pip install python-pptx`),
  then write a short inline script to extract text. Or ask the user to export to PDF.

Save the readable text as workspace/deck_text.md for reference.

## Step 2: Extract Claims

Read agents/claim_extractor.md for instructions.
Run the claim extractor on the deck text.
Wait for workspace/extracted_claims.json.

Invariant: if no claims are extracted, stop and tell the user.

## Step 3: Research Sources (parallelized)

Read agents/research.md for instructions, but with a key difference:
instead of researching claims for objectives, research sources for the
**existing claims** in workspace/extracted_claims.json.

**Launch sub-agents in parallel** — split the extracted claims into batches
of 5-8 claims each. Each sub-agent:
- Takes a batch of claims from extracted_claims.json
- Searches for authoritative sources that support or contradict each claim
- Writes workspace/sources/{claim_id}.txt for each claim where a source is found
- Writes workspace/claims_batch_{K}.json with updated source fields

After all complete, merge into workspace/claim_registry.json.
Claims without sources get confidence: "UNVERIFIED".

## Step 4: Fact-Check (parallelized)

Read agents/fact_checker.md for instructions.
Split claims into batches and launch parallel fact-check sub-agents,
same as the generate pipeline.

Each sub-agent compares the slide text (from `original_text` in extracted_claims.json)
against the source excerpt (from workspace/sources/{claim_id}.txt).

Merge batch results into workspace/review_v1.json.
The merged file must include full detail for all MISREPRESENTED and UNVERIFIED claims.

## Step 5: Write Recommendations

Read agents/review_writer.md for instructions.
Write output/recommendations.md.

Report to user: "Review complete. N claims extracted, X verified, Y issues found.
See output/recommendations.md."

---

## Invariants

- Never proceed past Step 2 if extracted_claims.json is missing or empty.
- Never proceed past Step 3 if claim_registry.json is missing or invalid JSON.
- If any step produces an empty file or fails silently, stop and report.
