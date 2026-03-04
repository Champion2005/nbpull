# Copilot Instructions — nbpull

## Critical Safety Invariant

**This tool is read-only.** The `NetBoxClient` in `client.py` only exposes HTTP
`GET` methods. Never add `POST`, `PUT`, `PATCH`, or `DELETE` capabilities —
not in the client, CLI, tests, or anywhere else.

## Project

**nbpull** — read-only CLI for querying NetBox IPAM data via REST API.  
PyPI: `nbpull` | Module: `netbox_data_puller` | Stack: Typer, httpx, Pydantic v2, Rich, uv

## Core Rules

- **No write operations** — enforced everywhere, tested explicitly
- **No `print()`** — use `rich.Console()` for user-facing output, `logging` for diagnostics
- **Strict typing** — all code must pass `mypy --strict`
- **Ruff** — line length 88; rule sets E, F, I, N, W, UP, B, SIM, RUF
- **Conventional Commits** — `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`, `ci:`
- **No secrets in commits** — never commit `.env`, tokens, or credentials
- **No direct pushes to `main`** — use feature branches and PRs
- **Smallest viable change** — no scope creep; do the minimum to satisfy the request

## Workflow Principles

- **Gate before acting** — pause for user approval between stages
- **Explicit over assumed** — ask one focused question when intent is unclear
- **Parallelize when possible** — spawn parallel subagents for independent tasks
- **Delegate via subagents** — main agent orchestrates only; never runs terminal commands directly. Route by task:
  - **`writer`** — create/edit files AND run build, test, install, lint commands (`pytest`, `ruff`, `uv`, etc. NOT GH operations, leave that to the github subagent)
  - **`reader`** — read files, search code, discover patterns (read-only, no commands)
  - **`github`** — all git and `gh` CLI operations
  - **`fetcher`** — external HTTP/URL fetching
- **Minimal subagent briefings** — pass file paths and change descriptions, not file contents
- **No secrets in commits** — never commit `.env`, tokens, or credentials

> **Detailed rules per module:** see `.github/instructions/`  
> **Full workflow reference:** see `docs/workflow.md`

