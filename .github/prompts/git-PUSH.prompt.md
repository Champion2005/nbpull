---
description: "Push the current branch to origin. Handles upstream setup, pre-push checks, and conflict detection."
argument-hint: "Optional: target remote or branch override"
tools: [agent]
model: Claude Sonnet 4.6 (copilot)
---

# 📤 PUSH

Spawn **`github` subagent** to:

1. Run `git status` and `git log origin/<branch>..HEAD --oneline` to confirm what will be pushed
2. Check if the upstream is set — if not, set it: `git push --set-upstream origin <branch>`
3. Check for diverged history (local and remote have diverged) — if so, surface the conflict and stop; do not force-push
4. Push: `git push`
5. Report result:
   - URL of the branch on GitHub
   - Number of commits pushed
   - Whether a PR already exists for this branch (`gh pr view` — if none, offer to run the PR prompt)

**Gate before pushing if:**
- The branch is `main` or a protected branch — ask the user to confirm
- There are uncommitted changes — warn that they won't be included

Never force-push. Surface the reason and ask the user to decide.
