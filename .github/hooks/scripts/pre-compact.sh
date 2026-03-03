#!/usr/bin/env bash
# PreCompact hook — fires before conversation context is compacted.
# Logs compaction with current git state so sessions can be reconstructed.
# Also injects a context reminder so the agent recovers faster post-compaction.
#
# Input: JSON with trigger, timestamp, sessionId, cwd

set -uo pipefail

_ERR_LOG="${TMPDIR:-/tmp}/copilot-pre-compact-errors.log"
handle_error() {
  local code=$1 line=$2
  printf '[%s] ERROR | hook=pre-compact.sh | exit=%d | line=%d\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$code" "$line" \
    >> "$_ERR_LOG" 2>/dev/null || true
  echo '{"continue": true}'
  exit 0
}
trap 'handle_error $? $LINENO' ERR

INPUT=$(cat)
TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
CWD=$(echo "$INPUT" | jq -r '.cwd')
TRIGGER=$(echo "$INPUT" | jq -r '.trigger')

LOG_FILE="${CWD}/.github/hooks/logs/session.log"
mkdir -p "$(dirname "$LOG_FILE")"
_ERR_LOG="$LOG_FILE"  # redirect errors to real log
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
DIRTY=$(git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
LAST_COMMIT=$(git -C "$CWD" log --oneline -1 2>/dev/null | tr -d "\"'" || echo "none")

echo "[${TIMESTAMP}] PreCompact | session=${SESSION_ID} | trigger=${TRIGGER} branch=${BRANCH} dirty=${DIRTY} last_commit='${LAST_COMMIT}'" >> "$LOG_FILE"

# Inject recovery context so the agent re-orients quickly after compaction
jq -n \
  --arg branch "$BRANCH" \
  --arg dirty "$DIRTY" \
  --arg commit "$LAST_COMMIT" \
  '{
    hookSpecificOutput: {
      hookEventName: "PreCompact"
    }
  }'
