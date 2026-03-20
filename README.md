# SlideGen

AI-powered lecture slide generator with source verification. Produces Marp markdown slides where every factual claim is traced to a cited source.

## Quick start

```bash
# Create a new deck
mkdir -p decks/my-topic/{workspace/sources,output}
# Write decks/my-topic/run.md (see below)

# Generate slides
./slidegen.sh decks/my-topic
```

## run.md format

```markdown
# Lecture Request

**Topic:** ...
**Course:** ...
**Prerequisites:** ...
**Duration:** 90 minutes (~25 slides)
**Learning objectives:**
1. ...
2. ...

**Notes:**
- Running example, diagram requests, key readings, etc.
```

## Pipeline

1. **Research** — Fetches and reads real sources (papers, docs, specs). Produces a claim registry with exact quotes. Verifies claims embedded in learning objectives.
2. **Outline** — Structures slides grounded in the claim registry. Every factual slide references at least one claim.
3. **Write** — Produces Marp markdown with `[claim:id]` tags on every factual bullet. Generates speaker hints and detailed lecturer notes.
4. **Execute Code** — Compiles and runs code blocks marked `<!-- EXEC_TEST -->`.
5. **Fact-Check** — Adversarial review comparing every slide bullet against its source excerpt. Flags omitted qualifiers, overgeneralizations, and misattributions.
6. **Finalize** — Copies approved draft to `output/slides.md` with full `provenance.json`.

Steps 3-5 loop up to 3 iterations until the fact-checker approves.

## Output

```
decks/my-topic/
  output/
    slides.md          # Final Marp slides
    provenance.json    # Claim-to-source traceability
  workspace/
    claim_registry.json
    sources/           # One .txt per claim with source excerpt
    outline.md
    draft_v1.md, draft_v2.md, ...
    review_v1.json, review_v2.json, ...
```

## Example deck

See `decks/spark-structured-streaming/` for a complete example including run.md, workspace artifacts, and final output.

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- Java 21+ (for code execution of Java slides)
- Python 3 (for `tools/run_code.py`)
- `jq` (for streaming progress output)
