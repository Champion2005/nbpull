#!/usr/bin/env bash
# SessionStart hook — fires once when the agent session begins.
# Detects project environment, checks auth status, and injects context.
# Only surfaces what is relevant — skips checks for tools not installed.
#
# Output: additionalContext injected into the agent's conversation window.

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
SESSION_ID=$(echo "$INPUT" | jq -r '.sessionId')
TIMESTAMP=$(echo "$INPUT" | jq -r '.timestamp')

LOG_FILE="${CWD}/.github/hooks/session.log"
echo "[${TIMESTAMP}] SessionStart | session=${SESSION_ID}" >> "$LOG_FILE"

LINES=()

# ── Git state ────────────────────────────────────────────────────────────────
BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "unknown")
DIRTY=$(git -C "$CWD" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
DIRTY_MSG=$( [ "$DIRTY" -gt 0 ] && echo "${DIRTY} uncommitted file(s)" || echo "clean" )
LINES+=("Git: branch=${BRANCH} | ${DIRTY_MSG}")

# ── Python venv ───────────────────────────────────────────────────────────────
if [ -d "${CWD}/.venv" ] || [ -d "${CWD}/venv" ]; then
  if [ -z "${VIRTUAL_ENV:-}" ]; then
    LINES+=("⚠️  Python: venv found but NOT active. Run: source .venv/bin/activate")
  else
    LINES+=("✅ Python: venv active (${VIRTUAL_ENV})")
  fi
fi

# ── Node.js ───────────────────────────────────────────────────────────────────
if [ -f "${CWD}/package.json" ] && command -v node >/dev/null 2>&1; then
  NODE_VER=$(node -v 2>/dev/null || echo "unknown")
  LINES+=("Node: ${NODE_VER}")
fi

# ── Terraform ────────────────────────────────────────────────────────────────
if find "$CWD" -maxdepth 4 -name "*.tf" -print -quit 2>/dev/null | grep -q .; then
  if command -v terraform >/dev/null 2>&1; then
    TF_VER=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || echo "unknown")
    LINES+=("Terraform: v${TF_VER}")
  else
    LINES+=("⚠️  Terraform: .tf files found but terraform CLI not installed")
  fi
fi

# ── GitHub auth ───────────────────────────────────────────────────────────────
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "authenticated")
    LINES+=("✅ GitHub CLI: logged in as ${GH_USER}")
  else
    LINES+=("⚠️  GitHub CLI: NOT authenticated — run 'gh auth login' before git/GitHub operations")
  fi
fi

# ── Azure auth ────────────────────────────────────────────────────────────────
if command -v az >/dev/null 2>&1; then
  AZ_NAME=$(az account show --query "name" -o tsv 2>/dev/null || echo "")
  if [ -n "$AZ_NAME" ]; then
    LINES+=("✅ Azure CLI: active subscription = ${AZ_NAME}")
  else
    LINES+=("⚠️  Azure CLI: NOT authenticated — run 'az login' before Azure operations")
  fi
fi

CONTEXT=$(printf '%s\n' "${LINES[@]}")

jq -n --arg ctx "$CONTEXT" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}'
