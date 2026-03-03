---
description: "Generate a proposal and phased implementation plan from a curated context artifact."
argument-hint: "Path to the context artifact (plans/<feature>-context.md) or feature name"
tools: [agent, memory, todo, vscode/askQuestions]
model: Claude Opus 4.6 (copilot)
---

# 📐 PLAN — Proposal & Implementation Plan

You are running the **PLAN** workflow. You operate in two modes:

- **Propose** — high-level approach the user approves before you detail it
- **Task** — granular phased plan the BUILD prompt executes

Run Propose first, gate on user approval, then run Task.

> **PRDs and ADRs are the source of truth.** Every proposal and plan must trace back to a PRD. Every significant architectural decision must be captured in an ADR. Never propose an approach or create a plan phase without first checking what the PRD requires.

---

## Mode 1 — Propose

**Input:** `plans/<feature>-context.md`
**Output:** `plans/<feature>-proposal.md`

### Step 1 — Load PRD & ADRs

Spawn **`reader` subagent** instances in parallel to:
- Find and read the PRD for this feature — search `plans/` for `*-PRD.md` matching the feature. If no PRD exists, **stop and ask the user** whether to create one now (using the `adr-prd-review` skill) or confirm that none is needed.
- Find all relevant ADRs in `plans/ADR-*.md` — read any that touch the feature's domain (infrastructure, security, data, APIs)
- Do any additional codebase research needed — one subagent per independent question

All decisions in the proposal must be consistent with existing ADRs. If any proposed decision contradicts an existing ADR, surface the conflict explicitly before proceeding.

### Step 2 — Draft Proposal

Produce `plans/<feature>-proposal.md` using `.github/templates/proposal-template.md`. The proposal must:
- Derive the approach directly from the PRD's goals and functional requirements (reference FR-NNN IDs)
- Note which ADRs constrain or inform each key decision
- Flag any decisions that are **not yet covered by an ADR** — these need an ADR before planning begins

Delegate writing to **`writer` subagent** with the output path and structured findings.

### Step 3 — ADR Gate

Before gating with the user, for each key decision flagged as ADR-needed:
- Spawn **`writer` subagent** to draft a new ADR using `.github/templates/ADR-template.md`
- Save to `plans/ADR-NNN-<slug>.md` with the next available number

Then present to the user:
- Summary of the approach
- PRD requirements being addressed
- ADRs referenced + any new ADRs drafted
- Open questions requiring user input

**Gate:** *"Does this approach align with your requirements? Any decisions to revisit before I detail the plan?"*

Do not proceed until user approves.

---

## Mode 2 — Task

**Input:** `plans/<feature>-proposal.md` + the PRD + all relevant ADRs
**Output:** `plans/<feature>-plan.md`

### Step 1 — Map Requirements to Phases

Spawn **MULTIPLE `reader` subagent** instances in parallel to:
- Read the approved proposal
- Read the PRD — extract every functional requirement (FR-NNN) and non-functional requirement (NFR-NNN) that must be satisfied
- Map relevant files and existing code — one subagent per area

Every PRD requirement must be traceable to at least one plan phase. If a requirement is not covered, surface it before writing the plan.

### Step 2 — Write Plan

Break the proposal into a phase-by-phase plan. Each phase must include:

```markdown
## Phase N — <name>
**Goal:** <what done looks like>
**PRD Requirements:** FR-1, NFR-2  ← trace to PRD IDs
**ADR Constraints:** ADR-001, ADR-003  ← list applicable ADRs
**Files:**
- `path/to/file` — <what changes>
**Tests:**
- <test case to write or update>
**Acceptance criteria:**
- [ ] <verifiable criterion matching PRD requirement>
```

Each phase must be self-contained, ordered by dependency, and have every acceptance criterion traceable to a PRD requirement or ADR constraint.

Delegate writing to **`writer` subagent** with the output path and phase breakdown.

**Gate:** *"Does this plan cover all the requirements? Any phases to split, merge, or reorder before we build?"*

Do not proceed to BUILD until user approves.
