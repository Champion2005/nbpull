---
description: "Create a pull request. Handles standard PRs and splits large branches into multiple focused PRs."
argument-hint: "PR title or topic — leave blank to derive from branch and commits"
tools: [agent, vscode/askQuestions]
model: Claude Sonnet 4.6 (copilot)
---

# 🔀 PR

Spawn **`github` subagent** to assess the branch:
- `git log main..HEAD --oneline` — list commits on this branch
- `git diff main --stat` — files changed vs base
- `gh pr list --head <branch>` — check if a PR already exists

## If a PR already exists

Report its URL, status, and CI checks. Offer to update the description or add reviewers.

## If the branch is focused (≤ 10 files or single topic)

Draft and create a standard PR using the format in `.github/skills/github/SKILL.md`:
- **What** — what changed
- **Why** — reason/ticket
- **How to test** — steps

**Gate:** *"Does this PR description look right before I open it?"*

## If the branch is large (> 10 files or multiple unrelated topics)

**Propose a PR split plan** before creating anything:

1. Analyze commits and changed files — group by logical area
2. Propose stacked branches and PRs:

```
Proposed PR split:

Branch: feat/auth-core  ← commits A, B, C  → PR: "feat(auth): JWT validation"
Branch: feat/auth-ui    ← commits D, E     → PR: "feat(auth): login form"
Branch: fix/api-errors  ← commit F         → PR: "fix(api): error response shape"

Each PR targets main (or the previous branch if stacked).
```

**Gate:** *"Does this split look right? Any groups to merge or reorder?"*

After approval, spawn **`github` subagent** to:
1. Create each branch from the appropriate commits (`git cherry-pick` or `git checkout -b` from commit range)
2. Push each branch
3. Open each PR in order (stacked PRs link to their base)

## Rules

- Never open a PR directly to `main` from a large mixed branch without the user's explicit approval of the split plan
- Always check CI status after opening: `gh pr checks <number>`
