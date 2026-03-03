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

LOG_FILE="${CWD}/.github/hooks/session.log"
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
DIRTY=$(git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

echo "[${TIMESTAMP}] Stop | branch=${BRANCH} dirty=${DIRTY} | session=${SESSION_ID}" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

echo '{"continue": true}'
