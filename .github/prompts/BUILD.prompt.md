---
description: "Execute an approved implementation plan phase by phase with review gates."
argument-hint: "Path to the approved plan (plans/<feature>-plan.md) or feature name"
tools: [agent, memory, todo]
model: Claude Opus 4.6 (copilot)
---

# 🔨 BUILD — Execute Plan

You are running the **BUILD** workflow. You execute an approved `plans/<feature>-plan.md` phase by phase. Each phase gets a write → review → commit cycle. Never start the next phase before the user approves the current one.

> **PRDs and ADRs remain the source of truth during build.** Before starting, load the PRD and all ADRs listed in the plan. If a decision arises during build that is not covered by an existing ADR, draft one before proceeding.

---

## Before Starting

Spawn **`reader` subagent** instances in parallel to:
- Read `plans/<feature>-plan.md` — get all phases, PRD requirement IDs, and ADR references
- Read the PRD (`plans/*-PRD.md`) — load functional and non-functional requirements
- Read all ADRs referenced in the plan (`plans/ADR-*.md`)

Keep these on hand throughout all phases.

---

## Phase Execution Loop

For each phase in `plans/<feature>-plan.md`:

### Step 1 — Write & Verify

Spawn **`writer` subagent** with a minimal briefing:
- Phase number, goal (one sentence), and PRD requirement IDs being satisfied
- File paths to read/edit (from the plan)
- Relevant ADR constraints for this phase
- Reference to the plan: `plans/<feature>-plan.md` — Writer reads phase details directly
- Any build, test, or lint commands to run after writing (e.g. `pytest tests/`, `ruff check src/`, `uv run mypy`)

Writer runs the requested commands after making changes and reports pass/fail. Do not spawn a separate terminal step — writer handles both implementation and verification.

### Step 2 — Review

Spawn **MULTIPLE `reader` subagent** to review changed files against the phase acceptance criteria:
- Does each acceptance criterion pass?
- Do the changes satisfy the PRD requirements listed for this phase (FR-NNN / NFR-NNN)?
- Do the changes comply with all ADR constraints listed for this phase?
- Are tests present and meaningful?
- Any obvious issues (bugs, missing error handling, convention violations)?

If a new architectural decision is discovered during review that is **not covered by any existing ADR**:
- Pause the phase
- Spawn **`writer` subagent** to draft a new ADR using `.github/templates/ADR-template.md`
- Gate with user: *"A new architectural decision was encountered: [description]. I've drafted ADR-NNN. Please review before we continue."*
- Resume only after user approves the ADR

If other issues are found:
- Spawn Writer again with specific feedback (bullet points only)
- Re-review
- Max 2 rework cycles; if still blocked, surface to user

### Step 3 — Report & Gate

Present phase summary to user:

```
## Phase <N> Complete: <name>

### Changes
- <file> — <what changed>

### PRD Requirements Satisfied
- FR-N: <requirement text>

### ADR Compliance
- ADR-NNN: ✅ satisfied / ⚠️ <note if partial>

### Tests
- <test added/updated>

### Review
✅ Approved / ⚠️ Resolved after <N> rework cycles

### Committed
<sha> feat(<feature>): phase N — <phase name>

---
Ready for Phase <N+1> — awaiting your approval.
```

Ask: *"Ready to proceed to Phase <N+1>?"* — wait for approval before continuing.

### Step 4 — Commit

Spawn **`github` subagent** to commit the phase changes:
- Stage only files changed in this phase
- Commit message: `feat(<feature>): phase N — <phase name>`

## Completion

When all phases are done:
1. Verify all PRD functional and non-functional requirements are satisfied across phases — surface any gaps
2. Offer to open a PR via the `github` subagent
3. Remind user to mark the PRD status as complete and review any ADRs drafted during build