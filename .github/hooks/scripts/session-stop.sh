#!/usr/bin/env bash
# Stop hook — fires when the agent session ends.
# Logs session end with branch state. Never blocks stopping.
#
# Input: JSON with stop_hook_active, timestamp, sessionId, cwd

set -euo pipefail

INPUT=$(cat)
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

# Guard: prevent infinite loop — if already in a stop-hook cycle, exit immediately
if [ "$STOP_ACTIVE" = "true" ]; then
  echo '{"continue": true}'
  exit 0
fi

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
CWD=$(echo "$INPUT" | jq -r '.cwd')

HOOKS_DIR="${CWD}/.github/hooks"
LOG_FILE="${HOOKS_DIR}/logs/session.log"
mkdir -p "$(dirname "$LOG_FILE")"
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
DIRTY=$(git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

echo "[${TIMESTAMP}] Stop | branch=${BRANCH} dirty=${DIRTY} | session=${SESSION_ID}" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

# Archive all log files for this session into logs/archive/<date>_<sessionId>/
ARCHIVE_DATE=$(date -u +"%Y-%m-%d_%H-%M-%S" 2>/dev/null || echo "unknown")
ARCHIVE_DIR="${HOOKS_DIR}/logs/archive/${ARCHIVE_DATE}_${SESSION_ID}"
mkdir -p "$ARCHIVE_DIR"

for log_file in session.log tool-audit.log subagent.log; do
  src="${HOOKS_DIR}/logs/${log_file}"
  if [ -f "$src" ] && [ -s "$src" ]; then
    mv "$src" "${ARCHIVE_DIR}/${log_file}"
  fi
done

echo '{"continue": true}'
