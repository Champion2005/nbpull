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

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
CWD=$(echo "$INPUT" | jq -r '.cwd')

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
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:"Catastrophically destructive command blocked by safety policy. Confirm you intend this before proceeding."}}'
  exit 0
fi

# git push --force / -f
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(-f\b|--force)'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:"Force push rewrites shared history and can cause data loss for other contributors. Confirm you intend this."}}'
  exit 0
fi

# direct push to main/master
if echo "$COMMAND" | grep -qE 'git\s+push\s+(\S+\s+)?(main|master)\b'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:"Direct push to main/master detected. Use a feature branch and PR. Confirm only if this is intentional."}}'
  exit 0
fi

# ── Contextual warnings (non-blocking) ────────────────────────────────────────
WARNINGS=()

# GitHub auth
if echo "$COMMAND" | grep -qE '\bgh\b'; then
  if command -v gh >/dev/null 2>&1; then
    if ! gh auth status >/dev/null 2>&1; then
      WARNINGS+=("⚠️  GitHub CLI is not authenticated. Run 'gh auth login' or this command will fail.")
    fi
  fi
fi

# Python venv
if echo "$COMMAND" | grep -qE '\b(python|python3|pip|pip3|pytest|uv)\b'; then
  if [ -d "${CWD}/.venv" ] || [ -d "${CWD}/venv" ]; then
    if [ -z "${VIRTUAL_ENV:-}" ]; then
      WARNINGS+=("⚠️  Python venv exists but is NOT active. This command will use system Python. Activate first: source .venv/bin/activate")
    fi
  fi
fi

if [ ${#WARNINGS[@]} -gt 0 ]; then
  CONTEXT=$(printf '%s\n' "${WARNINGS[@]}")
  jq -n --arg ctx "$CONTEXT" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"allow",additionalContext:$ctx}}'
  exit 0
fi

echo '{"continue": true}'
