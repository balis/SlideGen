# SlideGen

AI-powered lecture slide generator and reviewer with source verification.

## Two pipelines

### Generate — create new slides from a topic description

```bash
mkdir -p decks/my-topic/{workspace/sources,output}
# Write decks/my-topic/run.md (see format below)
./slidegen.sh decks/my-topic
```

**Pipeline:** Research → Outline → Write → Execute Code → Fact-Check → Finalize (steps 3-5 loop up to 3 iterations)

**Output:** `output/slides.md` (Marp markdown) + `output/provenance.json` (claim-to-source traceability)

### Review — fact-check an existing deck

```bash
./slidereview.sh path/to/deck.md
./slidereview.sh path/to/deck.pdf
./slidereview.sh path/to/deck.pptx
```

**Pipeline:** Ingest → Extract Claims → Research Sources → Fact-Check → Write Recommendations

**Output:** `output/recommendations.md` (revision recommendations grouped by severity)

## run.md format (for generate)

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

## Project structure

```
agents/
  research.md           # Finds and verifies sources for claims
  outline.md            # Structures slides from claim registry
  writer.md             # Produces Marp slides with claim tags
  fact_checker.md       # Adversarial review against sources
  code_executor.md      # Runs code blocks marked EXEC_TEST
  claim_extractor.md    # Extracts claims from existing decks (review)
  review_writer.md      # Produces revision recommendations (review)
pipelines/
  generate.md           # Generate pipeline steps
  review.md             # Review pipeline steps
tools/
  run_code.py           # Code execution harness
```

## Example deck

See `decks/spark-structured-streaming/` for a complete generated example including run.md, workspace artifacts, and final output.

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- Python 3
- `jq` (for streaming progress output)
- `python-pptx` (only for reviewing .pptx files: `pip install python-pptx`)
- Java 21+ (only for code execution of Java slides)
