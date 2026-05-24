#!/usr/bin/env bash
set -euo pipefail

# Ensure we use fnm's Node (not system v12)
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env 2>/dev/null)" || true

# Usage: ./slidereview.sh <deck-file> [output-folder]
#
# Supported formats: .md, .pdf, .pptx
# If no output folder is given, creates one next to the input file.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DECK_FILE="${1:?Usage: $0 <deck-file> [output-folder]}"
DECK_FILE="$(cd "$(dirname "$DECK_FILE")" && pwd)/$(basename "$DECK_FILE")"

if [[ ! -f "$DECK_FILE" ]]; then
  echo "Error: $DECK_FILE not found."
  exit 1
fi

# Determine output directory
DECK_NAME="$(basename "$DECK_FILE" | sed 's/\.[^.]*$//')"
TOPIC_DIR="${2:-$(dirname "$DECK_FILE")/review-${DECK_NAME}}"
TOPIC_DIR="$(mkdir -p "$TOPIC_DIR" && cd "$TOPIC_DIR" && pwd)"

# Ensure workspace dirs exist
mkdir -p "$TOPIC_DIR/workspace/sources" "$TOPIC_DIR/output"

# Build the prompt
PROMPT="$(cat <<EOF
You are running the slide-review pipeline.

**System directory:** $SCRIPT_DIR
  - CLAUDE.md (orchestrator instructions) is here
  - agents/ (agent prompts) are here
  - pipelines/ (pipeline definitions) are here
  - tools/ (utilities) are here

**Topic directory:** $TOPIC_DIR
  - workspace/ (all intermediate artifacts go here)
  - output/ (recommendations go here)

**Deck to review:** $DECK_FILE

CLAUDE.md (the orchestrator) is already in your context.
**Pipeline:** Read $SCRIPT_DIR/pipelines/review.md and follow it.
All workspace paths resolve to $TOPIC_DIR/workspace/.
All output paths resolve to $TOPIC_DIR/output/.

Start the review now.
EOF
)"

echo "=== SlideReview ==="
echo "System: $SCRIPT_DIR"
echo "Deck:   $DECK_FILE"
echo "Output: $TOPIC_DIR"
echo "==================="

cd "$SCRIPT_DIR"

# Hard wall-clock limit so a dead TCP socket (e.g. laptop sleep) eventually
# surfaces as an exit code instead of hanging in epoll_wait forever.
# Override with: SLIDEREVIEW_TIMEOUT=7200 ./slidereview.sh ...
: "${SLIDEREVIEW_TIMEOUT:=10800}"

# stdin from /dev/null so claude never tries to read the controlling terminal
# (a background process group reading the TTY gets SIGTTIN and stops).
# Note: no --max-thinking-tokens override here — the review pipeline is entirely
# fact-checking (adversarial reasoning), which benefits from extended thinking.
timeout "$SLIDEREVIEW_TIMEOUT" claude -p "$PROMPT" \
  --max-turns 50 \
  --verbose \
  --output-format stream-json \
  </dev/null \
  | tee "$TOPIC_DIR/workspace/stream.jsonl" \
  | jq -r --unbuffered 'select(.type == "assistant") | .message.content[] | select(.type == "text") | .text'
