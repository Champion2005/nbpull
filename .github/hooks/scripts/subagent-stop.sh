#!/usr/bin/env bash
# SubagentStop hook — fires when a subagent completes.
# Logs completion and guards against runaway subagent loops.
#
# Input (stdin): JSON with fields: timestamp, cwd, sessionId, hookEventName,
#                                  agent_id, agent_type, stop_hook_active
# Output (stdout): JSON — optionally blocks the subagent from stopping (use sparingly)

set -euo pipefail

INPUT=$(cat)

TIMESTAMP=$(echo "$INPUT"       | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT"      | jq -r '.sessionId')
AGENT_ID=$(echo "$INPUT"        | jq -r '.agent_id')
AGENT_TYPE=$(echo "$INPUT"      | jq -r '.agent_type')
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')
CWD=$(echo "$INPUT"             | jq -r '.cwd')

LOG_FILE="${CWD}/.github/hooks/subagent.log"

# Append completion entry to session log
echo "[${TIMESTAMP}] SubagentStop  | agent_type='${AGENT_TYPE}' | session=${SESSION_ID} agent_id=${AGENT_ID}" >> "$LOG_FILE"

# Guard: if this hook is already running as part of a stop-hook cycle, do not block again.
# This prevents the subagent from running indefinitely.
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  echo '{"continue": true}'
  exit 0
fi

# Allow the subagent to stop normally.
# Extend this script to validate results or trigger follow-up actions before completion.
echo '{"continue": true}'
