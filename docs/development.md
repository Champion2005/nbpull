# 🛠️ Development Guide

Everything you need to set up a local dev environment and contribute
to nbpull.

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| [Python](https://www.python.org/) | 3.13+ | Runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Package management |
| [Git](https://git-scm.com/) | any | Version control |

Optional (but recommended):

| Tool | Purpose |
|---|---|
| [pre-commit](https://pre-commit.com/) | Auto-run linters on commit |
| A NetBox instance + read-only token | Integration tests |

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/Champion2005/nbpull.git
cd nbpull

# 2. Install all dependencies (including dev group)
make install

# 3. (Optional) Install pre-commit hooks
uv run pre-commit install

# 4. Copy the env template
cp .env.example .env
# Edit .env with your NetBox URL and token
```

## Day-to-Day Commands

```bash
make all              # format → lint → typecheck → test (run before every PR)
make test             # unit tests only (no network, fast)
make lint             # ruff linter
make format           # auto-format + auto-fix with ruff
make typecheck        # mypy in strict mode
make test-integration # requires NETBOX_URL + NETBOX_TOKEN
make clean            # remove build artifacts and caches
```

## Project Structure

```
src/netbox_data_puller/
├── __init__.py      # Package version
├── cli.py           # Typer commands (thin orchestration layer)
├── client.py        # Async GET-only HTTP client
├── config.py        # pydantic-settings configuration
├── formatters.py    # Rich table + JSON output renderers
└── models/          # Pydantic v2 models (one per resource)
    ├── __init__.py
    ├── prefix.py
    ├── ip_address.py
    ├── vlan.py
    └── vrf.py

tests/
├── test_cli.py          # CLI command tests
├── test_client.py       # HTTP client tests (mocked)
├── test_models.py       # Model validation tests
└── test_integration.py  # Live API tests (marked integration)
```

## Writing Code

### Style

- **Ruff** handles formatting and linting (line length 88)
- **mypy strict** — all code must be fully typed
- **f-strings** for interpolation — no `%` or `.format()`
- **`logging`** for diagnostics — never `print()`
- **Async** for all HTTP I/O

### Safety Invariant

The `NetBoxClient` in `client.py` only exposes `GET` methods. This is
the core safety promise. **Never add write methods.** Tests verify
this invariant explicitly.

### Adding a New Command

See the [new-command prompt](../.github/prompts/new-command.prompt.md)
for a step-by-step checklist.

## Writing Tests

### Unit Tests

Use [respx](https://github.com/lundberg/respx) to mock httpx:

```python
import respx
from httpx import Response

@respx.mock
async def test_get_prefixes(client):
    respx.get("https://netbox.example.com/api/ipam/prefixes/").mock(
        return_value=Response(200, json={
            "count": 1,
            "next": None,
            "results": [{"id": 1, "prefix": "10.0.0.0/8"}]
        })
    )
    results = await client.get("ipam/prefixes/")
    assert len(results) == 1
```

### Integration Tests

Require `NETBOX_URL` and `NETBOX_TOKEN` environment variables:

```bash
export NETBOX_URL=https://netbox.example.com
export NETBOX_TOKEN=your_token
make test-integration
```

Mark with `@pytest.mark.integration`:

```python
@pytest.mark.integration
async def test_live_prefixes(live_client):
    results = await live_client.get("ipam/prefixes/", max_results=5)
    assert len(results) <= 5
```

## Releasing

See [docs/releasing.md](releasing.md) for the full release process.

Quick version: `make release VERSION=x.y.z`

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add --role filter to prefixes command
fix: handle empty pagination response
docs: expand configuration guide
test: add VRF model edge cases
chore: bump dependencies
ci: add Python 3.14 to test matrix
refactor: extract pagination logic
```

## Troubleshooting

### `uv` not found

Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### mypy errors on Pydantic models

Ensure `plugins = ["pydantic.mypy"]` is in `pyproject.toml` under
`[tool.mypy]`.

### Tests fail with network errors

Unit tests should never hit the network. If they do, a `respx` mock
is missing. Check that `@respx.mock` decorates the test.
