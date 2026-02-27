# Copilot Instructions — nbpull

## Project Overview

**nbpull** is a read-only CLI tool that queries NetBox IPAM data via
its REST API. Package name on PyPI is `nbpull`; the Python module is
`netbox_data_puller`.

## Critical Safety Invariant

**This tool is read-only.** The `NetBoxClient` in `client.py` only
exposes HTTP `GET` methods. Never add `POST`, `PUT`, `PATCH`, or
`DELETE` capabilities — not in the client, CLI, or anywhere else. This
invariant is enforced by code structure and verified by tests.

## Tech Stack

| Layer | Technology |
|---|---|
| CLI framework | [Typer](https://typer.tiangolo.com/) |
| HTTP client | [httpx](https://www.python-httpx.org/) (async) |
| Data models | [Pydantic v2](https://docs.pydantic.dev/) |
| Configuration | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Output | [Rich](https://rich.readthedocs.io/) tables / JSON |
| Linter / Formatter | [Ruff](https://docs.astral.sh/ruff/) |
| Type checker | [mypy](https://mypy-lang.org/) (strict mode) |
| Tests | [pytest](https://docs.pytest.org/) + [respx](https://github.com/lundberg/respx) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## Module Layout

```
src/netbox_data_puller/
├── __init__.py      # Package version (__version__)
├── cli.py           # Typer commands, flag definitions, orchestration
├── client.py        # Async GET-only NetBox API client
├── config.py        # Pydantic Settings (.env / env vars)
├── formatters.py    # Rich table + JSON renderers
└── models/          # Pydantic v2 models per resource type
    ├── prefix.py
    ├── ip_address.py
    ├── vlan.py
    └── vrf.py
```

## Coding Conventions

- **Python 3.13+** — use modern syntax (type unions with `|`, etc.)
- **Strict typing** — all code must pass `mypy --strict`
- **Ruff** — line length 88, rule sets: E, F, I, N, W, UP, B, SIM, RUF
- **f-strings** exclusively for interpolation — no `%` or `.format()`
- **`logging`** stdlib for diagnostics — never use `print()`
- **Async** all HTTP I/O — `async def` + `await`
- **Pydantic v2 models** — `extra="allow"` to tolerate new API fields
- **Conventional Commits** — `feat:`, `fix:`, `docs:`, `test:`,
  `chore:`, `refactor:`, `ci:`

## Versioning & Release

- Version is stored in two places: `pyproject.toml` (project.version)
  and `src/netbox_data_puller/__init__.py` (__version__). Both must
  match.
- Follows [Semantic Versioning](https://semver.org/) and
  [Keep a Changelog](https://keepachangelog.com/).
- Release flow: `make release VERSION=x.y.z`
- See `docs/releasing.md` for the full checklist.

## Testing

- **Unit tests** (`make test`) — mock HTTP with respx, no network
- **Integration tests** (`make test-integration`) — real NetBox API,
  requires `NETBOX_URL` + `NETBOX_TOKEN`
- Test files live in `tests/` and mirror the module they test
  (e.g. `test_client.py` → `client.py`)
- Use `pytest.mark.integration` for live-API tests

## Build & Run Commands

```bash
make install          # uv sync --all-groups
make all              # format → lint → typecheck → test
make test             # unit tests only
make lint             # ruff check
make format           # ruff format + fix
make typecheck        # mypy strict
make test-integration # requires live NetBox
make release VERSION=x.y.z  # bump, changelog, tag, push
```
