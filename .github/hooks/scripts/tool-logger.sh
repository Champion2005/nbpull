#!/usr/bin/env bash
# PostToolUse hook — full audit log of every tool invocation.
# Logs tool name, session, input summary, and response summary.
# Fires after every tool call. Always exits 0 (non-blocking).
#
# Input: JSON with tool_name, tool_input, tool_response, timestamp, sessionId, cwd

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
LOG_FILE="${CWD}/.github/hooks/logs/tool-audit.log"
mkdir -p "$(dirname "$LOG_FILE")"

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Sanitize: collapse to single line, strip both " and ' to prevent log line breakage, truncate
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' | tr -d '\n' | tr -d "\"'" | head -c 200)
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // ""' | tr -d '\n' | tr -d "\"'" | head -c 150)

echo "[${TIMESTAMP}] ${TOOL_NAME} | in='${TOOL_INPUT}' | out='${TOOL_RESPONSE}' | session=${SESSION_ID}" >> "$LOG_FILE"

echo '{"continue": true}'
