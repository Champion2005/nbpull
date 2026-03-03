#!/usr/bin/env bash
# PostToolUse hook — language-aware linting after file create/edit.
# Only fires for editFiles and createFile tool calls.
# Injects lint results as additionalContext — never blocks the agent.
#
# Supported linters (used only if installed):
#   Python   → ruff (preferred), flake8 (fallback)
#   Terraform → terraform fmt --check, tflint
#   JS/TS    → eslint
#   Shell    → shellcheck
#   JSON     → python3 json.tool (built-in)
#
# Input: JSON with tool_name, tool_input, timestamp, sessionId, cwd

set -uo pipefail

_ERR_LOG="${TMPDIR:-/tmp}/copilot-post-tool-lint-errors.log"
handle_error() {
  local code=$1 line=$2
  printf '[%s] ERROR | hook=post-tool-lint.sh | exit=%d | line=%d\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$code" "$line" \
    >> "$_ERR_LOG" 2>/dev/null || true
  echo '{"continue": true}'
  exit 0
}
trap 'handle_error $? $LINENO' ERR

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Only act on file write operations
if [ "$TOOL_NAME" != "editFiles" ] && [ "$TOOL_NAME" != "createFile" ]; then
  echo '{"continue": true}'
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.cwd')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')

SESSION_LOG="${CWD}/.github/hooks/logs/session.log"
mkdir -p "$(dirname "$SESSION_LOG")"
_ERR_LOG="$SESSION_LOG"  # redirect errors to real log

# Collect affected file paths — handles both editFiles (array) and createFile (single path)
FILES=$(echo "$INPUT" | jq -r '
  if .tool_input.files then .tool_input.files[]
  elif .tool_input.path then .tool_input.path
  else empty
  end' 2>/dev/null || echo "")

if [ -z "$FILES" ]; then
  echo '{"continue": true}'
  exit 0
fi

RESULTS=()

while IFS= read -r FILE; do
  [ -z "$FILE" ] && continue
  FULL_PATH="${CWD}/${FILE}"
  [ -f "$FULL_PATH" ] || continue
  EXT="${FILE##*.}"

  case "$EXT" in

    py)
      if command -v ruff >/dev/null 2>&1; then
        OUT=$(ruff check "$FULL_PATH" 2>&1 | head -20 || true)
        [ -n "$OUT" ] && RESULTS+=("ruff • ${FILE}:\n${OUT}")
      elif command -v flake8 >/dev/null 2>&1; then
        OUT=$(flake8 "$FULL_PATH" 2>&1 | head -20 || true)
        [ -n "$OUT" ] && RESULTS+=("flake8 • ${FILE}:\n${OUT}")
      fi
      ;;

    tf|tfvars)
      if command -v terraform >/dev/null 2>&1; then
        if ! terraform fmt -check "$FULL_PATH" >/dev/null 2>&1; then
          RESULTS+=("terraform fmt • ${FILE}: not properly formatted — run 'terraform fmt'")
        fi
      fi
      if command -v tflint >/dev/null 2>&1; then
        DIR=$(dirname "$FULL_PATH")
        OUT=$(tflint --chdir="$DIR" 2>&1 | head -20 || true)
        [ -n "$OUT" ] && RESULTS+=("tflint • ${FILE}:\n${OUT}")
      fi
      ;;

    ts|tsx|js|jsx)
      if command -v eslint >/dev/null 2>&1; then
        OUT=$(eslint "$FULL_PATH" 2>&1 | head -20 || true)
        [ -n "$OUT" ] && RESULTS+=("eslint • ${FILE}:\n${OUT}")
      fi
      ;;

    sh|bash)
      if command -v shellcheck >/dev/null 2>&1; then
        OUT=$(shellcheck "$FULL_PATH" 2>&1 | head -20 || true)
        [ -n "$OUT" ] && RESULTS+=("shellcheck • ${FILE}:\n${OUT}")
      fi
      ;;

    json)
      if command -v python3 >/dev/null 2>&1; then
        if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$FULL_PATH" 2>/dev/null; then
          ERR=$(python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$FULL_PATH" 2>&1 || true)
          RESULTS+=("json • ${FILE}: invalid JSON — ${ERR}")
        fi
      fi
      ;;

  esac
done <<< "$FILES"

if [ ${#RESULTS[@]} -gt 0 ]; then
  CONTEXT=$(printf '%b\n\n' "${RESULTS[@]}")
  # Log lint findings to session log for observability
  printf '[%s] LintWarning | session=%s | findings=%d | files=%s\n' \
    "$TIMESTAMP" "$SESSION_ID" "${#RESULTS[@]}" \
    "$(echo "$FILES" | tr '\n' ',' | head -c 200)" >> "$SESSION_LOG" 2>/dev/null || true
  jq -n --arg ctx "Lint results after edit:\n\n${CONTEXT}" \
    '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$ctx}}'
  exit 0
fi

echo '{"continue": true}'
