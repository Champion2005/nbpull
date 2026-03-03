---
description: "Stage and commit changes. Automatically groups large changesets into atomic commits by logical area."
argument-hint: "Commit message or topic — leave blank to auto-detect from changed files"
tools: [execute, agent]
model: Claude Sonnet 4.6 (copilot)
---

# 📝 COMMIT

Spawn **`github` subagent** to check current state:
- `git status` — what's changed
- `git diff --stat` — file-level summary

## If changes are small / clearly one topic

Commit everything as a single atomic commit. Follow the commit workflow in `.github/skills/github/SKILL.md` — conventional message, selective staging, co-author trailer.

## If changes span multiple topics

**Do not commit everything together.** Group files by logical area and propose a split:

```
Proposed commit plan:

1. feat(auth): add JWT token validation   ← src/auth/*, tests/auth/*
2. fix(api): correct error response shape ← src/api/handlers.ts
3. docs: update README with auth section  ← README.md
```

**Gate:** *"Does this split look right? Any grouping to change?"*

After approval, execute commits in order — one subagent call per commit to keep staging precise.

## Rules

- Never `git add .` blindly — stage only files belonging to that commit
- If a file touches multiple concerns, note it and ask the user which commit it belongs to
- Always verify with `git log --oneline -5` after the last commit
