#!/usr/bin/env bash
# PostToolUse hook — full audit log of every tool invocation.
# Logs tool name, session, input summary, and response summary.
# Fires after every tool call. Always exits 0 (non-blocking).
#
# Input: JSON with tool_name, tool_input, tool_response, timestamp, sessionId, cwd

set -uo pipefail

_ERR_LOG="${TMPDIR:-/tmp}/copilot-tool-logger-errors.log"
handle_error() {
  local code=$1 line=$2
  printf '[%s] ERROR | hook=tool-logger.sh | exit=%d | line=%d\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$code" "$line" \
    >> "$_ERR_LOG" 2>/dev/null || true
  echo '{"continue": true}'
  exit 0
}
trap 'handle_error $? $LINENO' ERR

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
LOG_FILE="${CWD}/.github/hooks/logs/tool-audit.log"
mkdir -p "$(dirname "$LOG_FILE")"
_ERR_LOG="$LOG_FILE"  # redirect errors to real log

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Sanitize: collapse to single line, strip both " and ' to prevent log line breakage, truncate
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' | tr -d '\n' | tr -d "\"'" | head -c 200)
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // ""' | tr -d '\n' | tr -d "\"'" | head -c 150)

echo "[${TIMESTAMP}] ${TOOL_NAME} | session=${SESSION_ID} | in='${TOOL_INPUT}' | out='${TOOL_RESPONSE}'" >> "$LOG_FILE"

echo '{"continue": true}'
