---
name: github
description: "Git and GitHub operations — commits, branches, PRs, issues, releases, code review, and repo health checks. Use this skill for any git or GitHub operation: checking status, staging files, writing commit messages, creating PRs, reviewing PRs, listing/creating issues, managing releases, or reporting session-end health. Triggers on any git/GitHub task — even if the user just says 'commit this', 'push it', 'make a PR', 'what's the status', or mentions git/GitHub in passing."
---

# 🐙 GitHub Operations

## Commit Workflow

Always follow this sequence — never skip steps:

1. **Check state first**
   ```bash
   git status
   git diff --stat
   ```
2. **Stage only task-relevant files** — never `git add .` blindly
3. **Write a conventional commit message**
   ```
   type(scope): subject

   Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
   ```
   Types: `feat` · `fix` · `docs` · `chore` · `refactor` · `test`
4. **Verify after commit**
   ```bash
   git log --oneline -3
   ```

## Branch Operations

```bash
git checkout -b <type>/<slug>   # create
git branch -a                   # list
git checkout <name>             # switch
```

Branch naming: `feat/<slug>` · `fix/<slug>` · `chore/<slug>`

## Pull Requests (`gh` CLI or MCP)

```bash
gh pr create --title "type(scope): subject" --body "$(cat <<'EOF'
## What
<what changed>

## Why
<reason>

## How to test
<steps>
EOF
)" --base main
```

Always include What / Why / How to test in the PR body.

## Issues (`gh` CLI or MCP)

```bash
gh issue list --state open
gh issue view <number>
gh issue create --title "<title>" --body "<description>"
```

## Session Health Check

When asked for a session-end health check, return exactly this structure:

```
## Git Status
- Branch: <name> [<N> commits ahead of origin | up to date]
- Uncommitted changes: <none | list of files>
- Unpushed commits: <none | N commits>

## Open PRs (this branch)
- <none | #N: title [state]>

## Recent Commits
- <sha7> <message>
- <sha7> <message>
```

## 🔍 Pull Request Reviews

When reviewing a PR:
```bash
gh pr view <number>
gh pr diff <number>
gh pr checks <number>
```

Review checklist:
- Does the PR description explain What / Why / How to test?
- Are commits atomic and well-messaged?
- Are there any files that shouldn't be included (debug logs, `.env`, etc.)?
- Do the CI checks pass?

```bash
# Approve
gh pr review <number> --approve --body "LGTM"

# Request changes
gh pr review <number> --request-changes --body "<feedback>"
```

## 🏷️ Releases

```bash
# Create a release from the latest tag
gh release create v<version> --title "v<version>" --generate-notes

# List recent releases
gh release list --limit 5
```

Follow semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR** — breaking changes
- **MINOR** — new features (backward compatible)
- **PATCH** — bug fixes

## 📦 Stash Operations

```bash
git stash                      # Stash uncommitted changes
git stash list                 # List stashes
git stash pop                  # Apply and remove latest stash
git stash apply stash@{N}     # Apply without removing
```

Stashing is useful when you need to switch branches but have uncommitted work — it avoids messy partial commits.

## 🛡️ Safety Rules

These exist to protect shared history and prevent accidental data loss:

- **Never force-push or amend pushed commits** — rewriting shared history causes merge conflicts for everyone else on the team
- **Never push directly to `main` or protected branches** — always use feature branches and PRs. This ensures code review happens before changes land
- **Never delete a branch without explicit instruction** — branches may contain work-in-progress that hasn't been merged
- **Stage files selectively** — confirm the scope matches the task. Accidentally committing `.env`, `node_modules`, or debug files creates security and noise issues
- **Always include `Co-authored-by` trailer** — proper attribution for AI-assisted commits
