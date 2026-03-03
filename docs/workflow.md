# nbpull Workflow Reference

This document describes the AI-assisted development workflow for **nbpull**. All workflow components live in `.github/` and are automatically active when working in this repository with a compatible Copilot agent.

---

## Overview

The workflow follows a **START → PLAN → BUILD → END** cycle, supported by specialized subagents, reusable skills, and lifecycle hooks.

```
User request
     │
     ▼
  START prompt      ← context gathering, PRD/ADR discovery
     │
     ▼
  PLAN prompt       ← proposal + phased implementation plan
     │
     ▼
  BUILD prompt      ← phase-by-phase execution with review gates
     │
     ▼
  END prompt        ← safety check, session log, open items
```

---

## Prompts

Prompts are invoked by the user (`/START`, `/PLAN`, etc.). Each one orchestrates subagents to complete a distinct workflow stage.

| Prompt | When to use |
|--------|-------------|
| `START` | Begin a new feature — ingests context, discovers PRDs/ADRs, scaffolds `plans/<feature>-context.md` |
| `PLAN` | Turn context into a phased plan — produces `plans/<feature>-proposal.md` then `plans/<feature>-plan.md` |
| `BUILD` | Execute an approved plan phase by phase — writes code, reviews, commits each phase |
| `END` | Session wrap-up — checks git state, open items, docs currency; writes session log |
| `git-COMMIT` | Stage and commit — groups large changesets into atomic logical commits |
| `git-PUSH` | Push branch — checks divergence, sets upstream, reports PR status |
| `git-PR` | Open a PR — writes description, handles large branch splits |
| `git-ISSUE` | Create or triage GitHub issues |
| `new-command` | Scaffold a new read-only CLI command (model → formatter → CLI → tests → docs) |
| `release` | Cut a release — bumps version, promotes changelog, tags, pushes |
| `update-changelog` | Add entries to `CHANGELOG.md` under `[Unreleased]` |
| `workflow-CUSTOMIZE` | Modify the workflow itself — guided interactive setup |

---

## Subagents

Subagents are **agent-initiated only** — they are never invoked directly by the user. The main agent orchestrates them via `START`, `PLAN`, and `BUILD` prompts.

| Agent | Role | Tools |
|-------|------|-------|
| `reader` | 🔍 Read-only codebase explorer — parallel file/pattern discovery | read, search |
| `writer` | ✏️ File writer — creates and edits source, tests, docs | read, edit, search |
| `fetcher` | 🌐 Web explorer — finds docs, libraries, examples online | web, search |
| `github` | 🐙 Git/GitHub ops — commits, branches, PRs, issues | execute, github/* |

**Key rules for subagents:**
- Never address the user directly — return results to the calling prompt
- Read file paths directly from disk; never have contents pasted into the prompt
- Operate on the current branch only; do not push, merge, or alter git history

---

## Skills

Skills are lazy-loaded capability modules invoked on demand.

| Skill | When to use |
|-------|-------------|
| `skill-finder` | Find available skills — use when unsure what capabilities exist |
| `skill-creator` | Build a new custom skill or improve an existing one |
| `adr-prd-review` | Create or review ADRs and PRDs using repo templates |
| `doc-coauthoring` | Structured 3-stage workflow for writing docs and specs |
| `github` | Detailed git/GitHub procedures used by the `github` subagent |

---

## Lifecycle Hooks

Hooks fire automatically on agent lifecycle events. They are configured in `.github/hooks/*.json`.

| Hook | When | What it does |
|------|------|--------------|
| `SessionStart` | Session begins | Injects git state, Python venv status, GitHub CLI auth status |
| `Stop` | Session ends | Logs branch name and dirty file count |
| `PreCompact` | Before context compaction | Logs git state; helps agent re-orient after compaction |
| `PreToolUse` | Before every tool call | Blocks destructive commands (rm -rf /, force push to main, DROP TABLE); warns on GitHub CLI auth |
| `PostToolUse` (logging) | After every tool call | Writes full audit line to `tool-audit.log` |
| `PostToolUse` (lint) | After file create/edit | Runs ruff (Python) or shellcheck (shell) and injects results as context |
| `SubagentStart` | Subagent spawned | Logs spawn; injects enforcement context (branch, constraints) |
| `SubagentStop` | Subagent completes | Logs completion |

### Log Files

| File | Contents |
|------|----------|
| `.github/hooks/session.log` | Session start/stop and PreCompact events |
| `.github/hooks/tool-audit.log` | Every tool call: `[TIMESTAMP] TOOL | in=[...] | out=[...] | session=ID` |
| `.github/hooks/subagent.log` | Subagent start/stop: `[TIMESTAMP] SubagentStart/Stop | agent_type='X' | session=ID agent_id=Y` |

> **Note:** Hook scripts in `.github/hooks/scripts/` handle all lifecycle events. Log line format: IDs (session, agent) are always at the **end** of each line.

---

## Plan Artifacts

Plan artifacts live in `plans/` and are created by the START/PLAN workflow.

| Artifact | Created by | Purpose |
|----------|-----------|---------|
| `<feature>-context.md` | `START` | Raw context from user + discovery findings |
| `<feature>-proposal.md` | `PLAN` | High-level approach, PRD traceability, ADR decisions |
| `<feature>-plan.md` | `PLAN` | Phased implementation plan with acceptance criteria |
| `ADR-NNN-<slug>.md` | `PLAN` / `BUILD` | Architectural decision records |
| `session-log.md` | `END` | Running log of sessions and their outcomes |

Templates for all artifacts live in `.github/templates/`.

---

## GitHub Actions (CI/CD)

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `ci.yml` | Push / PR to `main` | Lint (ruff), typecheck (mypy), test (pytest unit) |
| `publish.yml` | GitHub Release published | Build sdist+wheel, publish to PyPI via trusted publishers |

---

## Adding a New CLI Command

Use the `new-command` prompt or follow this checklist manually:

1. Create `src/netbox_data_puller/models/<resource>.py` — Pydantic model
2. Export from `models/__init__.py`
3. Add formatter in `formatters.py`
4. Add Typer command in `cli.py` (fetch → validate → render)
5. Add unit tests in `tests/test_cli.py`
6. Update `docs/commands.md` with options table
7. Update commands table in `README.md`
8. Add entry in `CHANGELOG.md` under `[Unreleased]`
9. Run `make all` to verify everything passes

---

## Development Cycle

```bash
# Daily start
git checkout -b feat/<feature>
source .venv/bin/activate

# Edit code, then verify
make all           # format → lint → typecheck → test

# Commit and push
git add <files>
git commit -m "feat(<scope>): <description>"
git push --set-upstream origin feat/<feature>

# Open PR
gh pr create --fill

# Release
make release VERSION=x.y.z
```
