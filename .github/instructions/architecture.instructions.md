---
applyTo: "src/**/*.py, tests/**/*.py, pyproject.toml, Makefile, docs/**"
---

# Architecture Reference — nbpull

## Tech Stack

| Layer | Technology |
|---|---|
| CLI framework | [Typer](https://typer.tiangolo.com/) |
| HTTP client | [httpx](https://www.python-httpx.org/) (async) |
| Data models | [Pydantic v2](https://docs.pydantic.dev/) |
| Configuration | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Output | [Rich](https://rich.readthedocs.io/) tables / JSON / CSV |
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
├── formatters.py    # Rich table renderers
└── models/          # Pydantic v2 models per resource type
    ├── common.py    # Shared: NestedRef ({id,display}), ChoiceRef ({value,label})
    ├── aggregate.py
    ├── prefix.py
    ├── ip_address.py
    ├── vlan.py
    ├── vrf.py
    ├── site.py
    ├── device.py
    └── tenant.py
```

`NestedRef` — related objects (e.g. `tenant`, `vrf`, `site`). `ChoiceRef` — enum fields (e.g. `status`, `role`). Both expose `.display` for consistent rendering.

## Coding Conventions

- **Python 3.13+** — use `|` union syntax, no `Optional`
- **f-strings exclusively** — no `%` or `.format()`
- **`logging`** for diagnostics — never `print()`
- **Async HTTP** — all I/O is `async def` / `await`
- **Pydantic v2** — `extra="allow"` on all models (API adds new fields)

## Available Commands

| Command | API Endpoint | Description |
|---|---|---|
| `prefixes` | `ipam/prefixes/` | IPAM prefixes |
| `ip-addresses` | `ipam/ip-addresses/` | IPAM IP addresses |
| `vlans` | `ipam/vlans/` | IPAM VLANs |
| `vrfs` | `ipam/vrfs/` | IPAM VRFs |
| `aggregates` | `ipam/aggregates/` | IPAM aggregates |
| `sites` | `dcim/sites/` | DCIM sites |
| `devices` | `dcim/devices/` | DCIM devices |
| `tenants` | `tenancy/tenants/` | Tenancy tenants |
| `rfc1918` | `ipam/prefixes/` (×3) | RFC 1918 Global VRF inventory with mapping status |
| `location-report` | `ipam/prefixes/` + `dcim/sites/` | Mapped prefixes export for SMO/CMDB |
| `batch-prefixes` | `ipam/prefixes/` | Batch prefix query from TOML |
| `setup` | — | Interactive setup wizard |

## Build & Run Commands

```bash
make install          # uv sync --all-groups
make all              # format → lint → typecheck → test
make test             # unit tests only
make lint             # ruff check
make format           # ruff format + fix
make typecheck        # mypy strict
make test-integration # requires live NetBox (NETBOX_URL + NETBOX_TOKEN)
make release VERSION=x.y.z  # bump, changelog, tag, push

uv run pytest tests/test_cli.py::TestRfc1918Command -v  # single test class
```

## Versioning

Version lives in two places — both must match:
- `pyproject.toml` → `project.version`
- `src/netbox_data_puller/__init__.py` → `__version__`

Follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

## Branch Naming

| Prefix | Purpose |
|--------|---------|
| `feat/` | New feature |
| `fix/` | Bug fix |
| `docs/` | Documentation only |
| `refactor/` | Code refactoring |
| `test/` | Adding/updating tests |
| `chore/` | Maintenance / tooling |
