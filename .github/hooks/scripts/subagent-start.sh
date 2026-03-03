#!/usr/bin/env bash
# SubagentStart hook — fires when a subagent is spawned.
# Logs the spawn and injects enforcement context into the subagent's conversation.
#
# Input (stdin): JSON with fields: timestamp, cwd, sessionId, hookEventName, agent_id, agent_type
# Output (stdout): JSON — additionalContext injected into the subagent's context window

set -euo pipefail

INPUT=$(cat)

TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
AGENT_ID=$(echo "$INPUT"  | jq -r '.agent_id')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type')
CWD=$(echo "$INPUT" | jq -r '.cwd')

LOG_FILE="${CWD}/.github/hooks/subagent.log"

# Append spawn entry to session log
echo "[${TIMESTAMP}] SubagentStart | agent_type='${AGENT_TYPE}' | session=${SESSION_ID} agent_id=${AGENT_ID}" >> "$LOG_FILE"

# Inject enforcement context into the subagent's conversation window.
# This runs for every spawned subagent, ensuring constraints are enforced even though
# subagents start with a clean context and do not inherit the parent's instructions.
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")

jq -n \
  --arg agent_type "$AGENT_TYPE" \
  --arg branch "$BRANCH" \
  '{
    hookSpecificOutput: {
      hookEventName: "SubagentStart",
      additionalContext: ("You are the \($agent_type) subagent. Enforce the following rules without exception:\n\n- You are agent-initiated only. Do not address the user directly; report results back to the calling prompt agent.\n- Read file paths directly from disk. Never ask for file contents to be pasted into your prompt.\n- Return a concise, structured result — the calling agent synthesizes findings, not you.\n- You are operating on branch: \($branch). Do not push, merge, or alter git history.\n- Follow all conventions in .github/copilot-instructions.md.")
    }
  }'
