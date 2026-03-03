#!/usr/bin/env bash
# PreToolUse hook — safety, auth, and environment validation before tool execution.
# Fires before every tool call. Exits immediately for non-terminal tools.
# Tailored for netbox_data_puller: Python + GitHub only (no Terraform, no Azure).
#
# Checks:
#   - Dangerous command patterns: deny or require confirmation
#   - GitHub CLI auth: warn if gh command and not logged in
#   - Python venv: warn if python/pip command and venv not active
#
# Input: JSON with tool_name, tool_input, timestamp, sessionId, cwd

set -uo pipefail

# Pre-parse fallback log; overwritten with real path once CWD is known.
_ERR_LOG="${TMPDIR:-/tmp}/copilot-pre-tool-safety-errors.log"
SESSION_ID="unknown"

handle_error() {
  local code=$1 line=$2
  printf '[%s] ERROR | hook=pre-tool-safety.sh | exit=%d | line=%d | session=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$code" "$line" "$SESSION_ID" \
    >> "$_ERR_LOG" 2>/dev/null || true
  echo '{"continue": true}'
  exit 0
}
trap 'handle_error $? $LINENO' ERR

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
CWD=$(echo "$INPUT" | jq -r '.cwd')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')

SECURITY_LOG="${CWD}/.github/hooks/logs/security.log"
mkdir -p "$(dirname "$SECURITY_LOG")" 2>/dev/null || true
_ERR_LOG="$SECURITY_LOG"  # redirect errors to real log

# ── Log helpers ───────────────────────────────────────────────────────────────
log_block() {
  local rule=$1 cmd=$2 reason=$3
  local cmd_safe
  cmd_safe=$(printf '%s' "$cmd" | tr -d "\"'" | head -c 300)
  printf '[%s] BLOCKED | session=%s | rule=%s | cmd=%s | reason=%s\n' \
    "$TIMESTAMP" "$SESSION_ID" "$rule" "$cmd_safe" "$reason" >> "$SECURITY_LOG" 2>/dev/null || true
}

log_warn() {
  local rule=$1 cmd=$2 warning=$3
  local cmd_safe
  cmd_safe=$(printf '%s' "$cmd" | tr -d "\"'" | head -c 300)
  printf '[%s] WARNED  | session=%s | rule=%s | cmd=%s | warning=%s\n' \
    "$TIMESTAMP" "$SESSION_ID" "$rule" "$cmd_safe" "$warning" >> "$SECURITY_LOG" 2>/dev/null || true
}

# ── Only act on terminal/execute tool calls ───────────────────────────────────
if [ "$TOOL_NAME" != "runTerminalCommand" ] && [ "$TOOL_NAME" != "execute" ]; then
  echo '{"continue": true}'
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.cmd // empty' 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  echo '{"continue": true}'
  exit 0
fi


# ── Require confirmation ───────────────────────────────────────────────────────
# Catastrophically destructive commands: rm -rf /, DROP TABLE, DELETE FROM without WHERE
if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+/[^/]|DROP\s+TABLE|DELETE\s+FROM\s+\S+\s*;\s*$'; then
  REASON="Catastrophically destructive command blocked by safety policy. Confirm you intend this before proceeding."
  log_block "catastrophic-destroy" "$COMMAND" "$REASON"
  jq -n --arg r "$REASON" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'
  exit 0
fi

# git push --force / -f
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(-f\b|--force)'; then
  REASON="Force push rewrites shared history and can cause data loss for other contributors. Confirm you intend this."
  log_block "force-push" "$COMMAND" "$REASON"
  jq -n --arg r "$REASON" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'
  exit 0
fi

# direct push to main/master
if echo "$COMMAND" | grep -qE 'git\s+push\s+(\S+\s+)?(main|master)\b'; then
  REASON="Direct push to main/master detected. Use a feature branch and PR. Confirm only if this is intentional."
  log_block "push-to-main" "$COMMAND" "$REASON"
  jq -n --arg r "$REASON" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'
  exit 0
fi

# ── Contextual warnings (non-blocking) ────────────────────────────────────────
WARNINGS=()

# GitHub auth
if echo "$COMMAND" | grep -qE '\bgh\b'; then
  if command -v gh >/dev/null 2>&1; then
    if ! gh auth status >/dev/null 2>&1; then
      MSG="GitHub CLI is not authenticated. Run 'gh auth login' or this command will fail."
      log_warn "gh-auth" "$COMMAND" "$MSG"
      WARNINGS+=("⚠️  ${MSG}")
    fi
  fi
fi

# Python venv
if echo "$COMMAND" | grep -qE '\b(python|python3|pip|pip3|pytest|uv)\b'; then
  if [ -d "${CWD}/.venv" ] || [ -d "${CWD}/venv" ]; then
    if [ -z "${VIRTUAL_ENV:-}" ]; then
      MSG="Python venv exists but is NOT active. This command will use system Python. Activate first: source .venv/bin/activate"
      log_warn "venv-inactive" "$COMMAND" "$MSG"
      WARNINGS+=("⚠️  ${MSG}")
    fi
  fi
fi

if [ ${#WARNINGS[@]} -gt 0 ]; then
  CONTEXT=$(printf '%s\n' "${WARNINGS[@]}")
  jq -n --arg ctx "$CONTEXT" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"allow",additionalContext:$ctx}}'
  exit 0
fi

echo '{"continue": true}'
