---
description: "Session-end safety check. Verifies changes are committed, issues are captured, docs are current, and logs the session."
tools: [execute, agent, memory, todo, vscode/askQuestions]
model: Claude Opus 4.6 (copilot)
---

# 🔚 END — Session Safety Check

Run all checks in parallel. Report exactly what's safe, what needs attention, and what blocks a clean exit.

---

## Step 1 — Git & GitHub (parallel)

Spawn **`github` subagent** to report:
- Branch name and ahead/behind origin
- Uncommitted changes (staged and unstaged)
- Unpushed commits
- Open PRs on this branch
- Open GH issues assigned to the user or referencing this branch/feature (`gh issue list --assignee @me --state open`)
- Stale local branches with no remote counterpart (`git branch -vv | grep ': gone]'`)

---

## Step 2 — Plan Artifacts & Todos (parallel with Step 1)

Spawn **MULTIPLE `reader` subagent** in parallel to check:
- `plans/` — in-progress artifacts (`*-plan.md`, `*-proposal.md`, `*-context.md`) with unchecked items (`- [ ]`)
- `TODO`, `FIXME`, `HACK` comments in recently touched files
- Open ADRs in `plans/ADR-*.md` with status `Proposed` (not yet `Approved`)
- PRD requirements not yet marked complete

---

## Step 3 — Docs Currency (parallel with Step 1)

Spawn **MULTIPLE `reader` subagent** in parallel to check:
- `README.md` — does it reflect recent changes?
- Inline `<!-- TODO -->` or `<!-- clarify -->` markers in any doc
- Any `CHANGELOG.md` that needs an entry for work done this session

---

## Step 4 — Compile Report

```
## 🔚 Session End Report

### Git Status
- Branch: <name> (<N> ahead / up to date)
- Uncommitted: <none | files>
- Unpushed: <none | N commits>
- Open PRs: <none | #N title>

### GitHub Issues
- Assigned open issues: <none | list>
- Issues referencing this branch: <none | list>
- Stale local branches: <none | list>

### Plan Artifacts
- In-progress: <none | list>
- Open checklist items: <none | list>
- Proposed ADRs pending approval: <none | list>

### Open Todos / Markers
- <none | file:line list>

### Docs
- README: <up to date | stale — reason>
- Inline markers: <none | list>
- Changelog needed: <yes | no>

---

### 🚦 Verdict

**🟢 Clear to end**
OR
**🟡 Minor items** — safe to end, but consider: <list>
OR
**🔴 Blocking** — do not end without resolving: <list>
```

---

## Step 5 — Session Log

Append an entry to `plans/session-log.md` (create it if it doesn't exist) via **`writer` subagent**:

```markdown
## Session — <date> <time>

**Branch:** <name>
**Summary:** <1–2 sentences: what was accomplished>
**Artifacts created/updated:** <list>
**Open items carried forward:** <list or none>
**Verdict:** 🟢 / 🟡 / 🔴
```

---

## Step 6 — Offer Next Actions

Pick the single most important action and ask once:

- **Blocking:** "Want me to commit the uncommitted changes / create a WIP commit?"
- **Minor:** "Here's what I'd suggest before you go: …"
- **Clear:** "You're good to go. 👋"

