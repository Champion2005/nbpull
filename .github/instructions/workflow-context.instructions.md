---
applyTo: ".github/prompts/*"
---

# Workflow Context

This is **nbpull** — a read-only CLI tool for querying NetBox IPAM data via the NetBox REST API. It is a Python package (PyPI: `nbpull`, module: `netbox_data_puller`) built with Typer, httpx, Pydantic v2, and Rich.

## Repo Layout

```
.github/
  prompts/      # User-invokable workflow triggers
  agents/       # Subagents (agent-initiated only)
  hooks/        # Lifecycle hook config and scripts
  templates/    # Artifact templates
  instructions/ # Copilot instruction files
  skills/       # Lazy-loaded skill definitions
src/
  netbox_data_puller/   # Main package source
    models/             # Pydantic v2 models per resource type
tests/          # Unit and integration tests
docs/           # Project documentation
plans/          # All generated artifacts (context, proposals, plans)
```

## Available Agents

| Agent | Purpose |
|-------|----------|
| `fetcher` | 🌐 Read-only web explorer for docs and online resources |
| `github` | 🐙 Git/GitHub operations (commits, branches, PRs, issues) |
| `reader` | 🔍 Read-only codebase explorer for parallel file/pattern discovery |
| `writer` | ✏️ File writer and documentation specialist |

## Available Skills

| Skill | Purpose |
|-------|----------|
| `skill-finder` | 🔍 Discover and recommend Agent Skills |
| `skill-creator` | 🛠️ Create and improve skills |
| `doc-coauthoring` | 📝 Structured doc co-authoring workflow |
| `github` | 🐙 Git/GitHub operations procedures |
| `adr-prd-review` | 📋 Create and review ADRs/PRDs |

## Available Prompts

| Prompt | Purpose |
|--------|----------|
| `START` | Feature intake and context gathering |
| `PLAN` | Proposal and task planning |
| `BUILD` | Phase-by-phase implementation |
| `END` | Session safety check and wrap-up |
| `git-COMMIT` | Stage and commit changes |
| `git-ISSUE` | Create/view/triage GitHub issues |
| `git-PR` | Create/update pull requests |
| `git-PUSH` | Push branch to origin |
| `new-command` | Scaffold a new CLI command |
| `release` | Cut a release |
| `update-changelog` | Add changelog entries |
| `workflow-CUSTOMIZE` | Customize the workflow itself |
