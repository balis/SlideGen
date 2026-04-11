#!/usr/bin/env bash
set -euo pipefail

# Ensure we use fnm's Node (not system v12)
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env 2>/dev/null)" || true

# Usage: ./slidegen.sh [path/to/topic/folder]
#
# The topic folder must contain a run.md file.
# If no folder is given, uses the current directory.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOPIC_DIR="${1:-.}"
TOPIC_DIR="$(cd "$TOPIC_DIR" && pwd)"

if [[ ! -f "$TOPIC_DIR/run.md" ]]; then
  echo "Error: $TOPIC_DIR/run.md not found."
  echo "Usage: $0 <folder-with-run.md>"
  exit 1
fi

# Ensure workspace dirs exist in the topic folder
mkdir -p "$TOPIC_DIR/workspace/sources" "$TOPIC_DIR/output"

# Build the prompt — tell Claude where things are
PROMPT="$(cat <<EOF
You are running the slide-agent pipeline.

**System directory:** $SCRIPT_DIR
  - CLAUDE.md (orchestrator instructions) is here
  - agents/ (agent prompts) are here
  - tools/ (code execution harness) is here

**Topic directory:** $TOPIC_DIR
  - run.md (lecture request) is here
  - workspace/ (all intermediate artifacts go here)
  - output/ (final slides go here)

CLAUDE.md (the orchestrator) is already in your context.
**Pipeline:** Read $SCRIPT_DIR/pipelines/generate.md and follow it.
Read $TOPIC_DIR/run.md for the topic.
All workspace paths in the agent prompts are relative — resolve them to $TOPIC_DIR/workspace/.
All output paths resolve to $TOPIC_DIR/output/.
The code runner is at $SCRIPT_DIR/tools/run_code.py.

Start the pipeline now. Execute all steps.
EOF
)"

echo "=== SlideGen ==="
echo "System: $SCRIPT_DIR"
echo "Topic:  $TOPIC_DIR"
echo "================"

cd "$SCRIPT_DIR"

claude -p "$PROMPT" \
  --max-turns 50 \
  --verbose \
  --output-format stream-json \
  | tee "$TOPIC_DIR/workspace/stream.jsonl" \
  | jq -r --unbuffered 'select(.type == "assistant") | .message.content[] | select(.type == "text") | .text'
