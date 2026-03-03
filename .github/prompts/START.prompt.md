---
description: "Start a new feature. Ingests context, curates requirements, and scaffolds plan artifacts."
argument-hint: "Feature name and description, or point to existing context files"
tools: [agent, memory, todo, vscode/askQuestions]
model: Claude Opus 4.6 (copilot)
---

# 🚀 START — New Feature Kickoff

You are running the **START** workflow. Your job is to take raw context from the user, validate and structure it, and produce a clean `<feature>-context.md` artifact the PLAN prompt can act on.

---

## Step 1 — Intake

Extract from the user's request:
- **Feature slug** — a short kebab-case identifier (e.g. `user-auth`)
- **Goal** — what "done" looks like in one sentence
- **Existing context** — any linked docs, plan files, or code the user mentioned

If the slug or goal is unclear, ask focused clarifying questions before proceeding.

---

## Step 2 — Discover (Parallel)

Spawn **MULTIPLE `reader` subagent** instances in parallel — one per independent question:
- Are there existing PRDs or ADRs in `plans/` relevant to this feature? (search for `*-PRD.md`, `ADR-*.md`)
- What existing code is relevant to this feature?
- What patterns and conventions must the implementation follow?
- Are there similar features already implemented?
- What tests exist in the relevant area?

Brief each Reader with only its specific question and relevant file paths — not the full feature description.

Spawn **`github` subagent** in parallel to report:
- Current branch
- Any existing open PRs or issues related to this feature, nothing else

Spawn **`fetcher` subagent** in parallel to find any relevant online resources (libraries, docs, examples) based on the feature description.
---

## Step 3 — Structure Context

Write `plans/<feature>-context.md` using the template at `.github/templates/context-template.md`. Delegate to **`writer` subagent** with:
- The output path
- The structured findings from Step 2
- The feature goal

---

## Step 4 — Gate

Present a summary to the user:
- Requirements captured
- Open questions (must be resolved before planning)
- Risks flagged

Ask: *"Does this capture the context correctly? Anything to add or correct before I move to planning?"*

Do not proceed to PLAN until the user confirms.
