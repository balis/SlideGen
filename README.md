# SlideGen

AI-powered slide generator and reviewer with source verification. Generates
passive **lecture** decks, hands-on **practical-course** material (deck + workbook +
validated solutions), and fact-check **reviews** of existing decks.

## Three pipelines

### Generate — create new slides from a topic description

```bash
mkdir -p decks/my-topic/{workspace/sources,output}
# Write decks/my-topic/run.md (see format below)
./slidegen.sh decks/my-topic
```

**Pipeline:** Research → Outline → Write → Execute Code → Fact-Check → Finalize (steps 3-5 loop up to 3 iterations)

**Output:** `output/slides.md` (Marp markdown) + `output/provenance.json` (claim-to-source traceability)

### Course — create hands-on practical-course material

For a working session (slides + live exercises), not a passive lecture. The deck
is a lean backdrop; the hands-on depth lives in a participant workbook, and every
exercise's sample solution is validated by running it against a real model.

```bash
mkdir -p decks/my-course/{workspace/sources,output}
# Write decks/my-course/run.md as a course brief (see format below)
./coursegen.sh decks/my-course
```

**Pipeline:** Research → Course Outline → Design Exercises → Write deck + workbook → Verify (fact-check claims **and** live-validate exercises) → Finalize (loops up to 3 iterations)

**Output:** `output/slides.md` (lean backdrop deck with exercise-launch slides) + `output/workbook.md` (participant workbook) + `output/solutions.md` (live-validated, date-stamped solution keys) + `output/provenance.json` (claims **and** exercise-validation log)

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

## run.md format (for course)

A *course brief* is a lecture request plus a **session plan**: concept blocks each
paired with an exercise, plus the tools learners use.

```markdown
# Course Brief

**Topic:** ...
**Audience:** non-IT professionals (no coding assumed)
**Prerequisites:** ...
**Duration:** 60 minutes (hands-on)
**Target tools:** a general consumer chat LLM

**Session plan** (concept block → paired exercise):
1. <concept block>  — Exercise: <one-line scenario> · input: <data learner uses> · 10 min · keeps: <what they produce>
2. ...

**Source recency policy:** <carried over from the lecture brief, governs concept facts>
```

## Project structure

```
agents/
  research.md           # Finds and verifies sources for claims (shared)
  outline.md            # Structures lecture slides from claim registry (generate)
  writer.md             # Produces lecture Marp slides with claim tags (generate)
  fact_checker.md       # Adversarial review of claims against sources (shared)
  code_executor.md      # Runs code blocks marked EXEC_TEST (shared)
  claim_extractor.md    # Extracts claims from existing decks (review)
  review_writer.md      # Produces revision recommendations (review)
  course_outline.md     # Lean concept slides + exercise launch slides (course)
  course_writer.md      # Produces backdrop slides + launch slides (course)
  exercise_designer.md  # Designs each hands-on exercise spec (course)
  exercise_validator.md # Runs each exercise against a real model (course)
  workbook_writer.md    # Renders participant workbook + solution keys (course)
pipelines/
  generate.md           # Generate (lecture) pipeline steps
  course.md             # Course (hands-on) pipeline steps
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
