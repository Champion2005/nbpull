#!/usr/bin/env bash
# PostToolUse hook — full audit log of every tool invocation.
# Logs tool name, session, input summary, and response summary.
# Fires after every tool call. Always exits 0 (non-blocking).
#
# Input: JSON with tool_name, tool_input, tool_response, timestamp, sessionId, cwd

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
LOG_FILE="${CWD}/.github/hooks/tool-audit.log"

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Summarise input — collapse to single line, replace " with ' to avoid log breakage, truncate at 200 chars
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' | tr -d '\n' | tr '"' "'" | head -c 200)

# Summarise response — collapse, replace " with ', truncate at 150 chars
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // ""' | tr -d '\n' | tr '"' "'" | head -c 150)

echo "[${TIMESTAMP}] ${TOOL_NAME} | session=${SESSION_ID} | in='${TOOL_INPUT}' | out='${TOOL_RESPONSE}'" >> "$LOG_FILE"

echo '{"continue": true}'
