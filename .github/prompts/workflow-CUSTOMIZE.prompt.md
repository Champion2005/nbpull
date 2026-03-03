---
description: "Customize the .github workflow — prompts, agents, skills, hooks, and templates. Interactive guided setup."
argument-hint: "What to customize: 'prompts', 'agents', 'skills', 'hooks', 'templates', or leave blank for guided tour"
tools: [execute, agent, memory, vscode/askQuestions]
model: Claude Opus 4.6 (copilot)
---

# ⚙️ CUSTOMIZE — Workflow Configuration

You are helping the user customize their `.github` workflow. Read the current state first, then guide them interactively.

## Step 1 — Audit Current Setup

Spawn **MULTIPLE `reader` subagent** to inventory:
- All files in `.github/prompts/` (what prompts exist)
- All files in `.github/agents/` (what subagents exist, their tools and models)
- All files in `.github/skills/` (what skills are loaded)
- `.github/copilot-instructions.md` (current global rules)
- `.github/hooks/subagents.json` (hook config)

Present the inventory to the user as a structured summary.

## Step 2 — Identify What to Change

Ask one focused question at a time. Common customization areas:

**Prompts** — Add a new prompt? Rename, reorder, or remove an existing one?
**Agents** — Change an agent's model, tools, or description? Add a new specialist agent?
**Skills** — Add a new skill? Update an existing skill's description or procedures?
**Global rules** — Change a principle in `copilot-instructions.md`? Add a constraint?
**Hooks** — Modify what the SubagentStart hook injects? Change logging behaviour?
**Templates** — Update an artifact template (context, proposal, plan, ADR, PRD)?

## Step 3 — Execute Changes

For each change confirmed by the user, spawn **`writer` subagent** with:
- The exact file path to edit
- The specific change to make (do not pass file contents — pass the change description and let writer read the file)

After each change:
- Spawn **`reader` subagent** to verify the edit looks correct
- Confirm with the user before moving to the next change

## Step 4 — Validate

After all changes:
- Spawn **`reader` subagent** to check that all frontmatter is valid (description present, tools are valid tool names, `user-invokable: false` on all agents)
- Flag any broken references (e.g. a prompt referencing a skill that doesn't exist)

**Gate:** *"Here's what changed. Does everything look right?"*

Spawn **`github` subagent** to commit all `.github/` changes as a single `chore(workflow): <description>` commit after user approval.

## Rules

- Never modify `.github/hooks/scripts/*.sh` — those require manual review
- Always read a file before editing it — never rewrite from memory
- Validate frontmatter format: skill `description` must be a single quoted line; agent frontmatter must include `user-invokable: false`
