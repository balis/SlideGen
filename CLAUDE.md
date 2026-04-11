# SlideGen Orchestrator

This project has two pipelines. The launcher script tells you which one to run.

## Path resolution

- **System directory**: where this file, agents/, pipelines/, and tools/ live
- **Topic directory**: where the input files, workspace/, and output/ live

When agent prompts reference "workspace/..." or "output/...", resolve them
relative to the **topic directory**. When they reference "agents/...", "pipelines/...",
or "tools/...", resolve them relative to the **system directory**.

## How to execute

You are the orchestrator. For each step in the pipeline:
- Read the agent .md file for its instructions, inputs, and output format
- Either do the work yourself OR launch a sub-agent with the Agent tool
- Use sub-agents when work can be parallelized

## Pipelines

### Generate (`pipelines/generate.md`)

Creates new lecture slides from a topic description (run.md).
Invoked by `slidegen.sh`.

**Input:** topic directory with run.md
**Output:** output/slides.md + output/provenance.json

### Review (`pipelines/review.md`)

Fact-checks an existing slide deck and produces revision recommendations.
Invoked by `slidereview.sh`.

**Input:** a deck file (md, pdf, or pptx)
**Output:** output/recommendations.md

## Which pipeline to run

The launcher script's prompt tells you. Read the specified pipeline .md file
and follow its steps.
