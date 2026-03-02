# 🔍 nbpull

[![CI](https://github.com/Champion2005/nbpull/actions/workflows/ci.yml/badge.svg)](https://github.com/Champion2005/nbpull/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Typed](https://img.shields.io/badge/typing-strict-brightgreen.svg)](https://mypy-lang.org/)

**Read-only CLI tool to pull IPAM data from
[NetBox](https://netbox.dev).**

> **🔒 Safety guarantee:** nbpull **only reads** data from NetBox. No
> POST / PUT / PATCH / DELETE requests are ever made. The HTTP client is
> hardcoded to GET-only — this invariant is enforced by code structure
> and verified by tests.

---

## ✨ Features

- 📡 **Prefixes** — list and filter IPAM prefixes
- 🖥️ **IP Addresses** — query IP address allocations
- 🏷️ **VLANs** — browse VLAN assignments
- 🔀 **VRFs** — inspect VRF instances
- 📊 **Aggregates** — list top-level IP space by RIR
- 🏢 **Sites** — browse DCIM sites
- 🖧 **Devices** — query DCIM devices
- 🏛️ **Tenants** — list tenancy tenants
- 🌐 **RFC 1918** — inventory Global VRF RFC 1918 prefixes with mapping status
- 📦 **Batch queries** — check many prefixes at once from a TOML file
- 🎨 Rich table output (default) or JSON saved to a file (`--format json`)
- 🔎 Filter by status, VRF, tenant, site, tag, or free-text search
- ⚡ Async HTTP with automatic pagination
- 🔒 Strict typing (mypy strict mode + Pydantic v2)

## 📦 Installation

### With [uv](https://docs.astral.sh/uv/) (recommended)

```bash
uv tool install nbpull
```

### With [pipx](https://pipx.pypa.io/)

```bash
pipx install nbpull
```

### With pip

```bash
pip install nbpull
```

### From source

```bash
git clone https://github.com/Champion2005/nbpull.git
cd nbpull
make install   # uses uv sync
```

## 🚀 Quick Start

```bash
# 1. Run the interactive setup wizard
nbpull setup

# Or configure manually:
export NETBOX_URL=https://netbox.example.com
export NETBOX_TOKEN=your_read_only_token
# Or: cp .env.example .env && edit .env

# 2. Pull data
nbpull prefixes
nbpull prefixes --status active --vrf Production
nbpull ip-addresses --prefix 10.0.0.0/24
nbpull vlans --site DC1
nbpull vrfs --tenant Ops
nbpull aggregates --rir ARIN
nbpull sites --status active
nbpull devices --role "Core Router"
nbpull tenants
nbpull rfc1918
nbpull batch-prefixes --file my_prefixes.toml --status-only
```

## 📋 Commands

| Command | Description |
|---|---|
| `nbpull setup` | Interactive setup wizard |
| `nbpull prefixes` | List IPAM prefixes |
| `nbpull ip-addresses` | List IP addresses |
| `nbpull vlans` | List VLANs |
| `nbpull vrfs` | List VRFs |
| `nbpull aggregates` | List IPAM aggregates (top-level space by RIR) |
| `nbpull sites` | List DCIM sites |
| `nbpull devices` | List DCIM devices |
| `nbpull tenants` | List tenancy tenants |
| `nbpull rfc1918` | Inventory Global VRF RFC 1918 prefixes with mapping status |
| `nbpull batch-prefixes` | Query multiple prefixes from a TOML file |

### Common Flags

| Flag | Description |
|---|---|
| `--status` | Filter by status (active, reserved, deprecated, container) |
| `--vrf` | Filter by VRF name |
| `--tenant` | Filter by tenant name |
| `--site` | Filter by site name |
| `--tag` | Filter by tag slug |
| `--search` / `-s` | Free-text search |
| `--limit` / `-l` | Max results (default: 50) |
| `--format` / `-f` | Output format: `table` (default) or `json` (writes to file) |
| `--output` / `-o` | JSON output file path (prompts with default if omitted) |
| `--verbose` / `-v` | Enable debug logging |

See the full [command reference](docs/commands.md) for all options.

## ⚙️ Configuration

Set these in `.env` or as environment variables:

| Variable | Required | Default | Description |
|---|---|---|---|
| `NETBOX_URL` | ✅ | — | NetBox instance URL |
| `NETBOX_TOKEN` | ✅ | — | API token (read-only recommended) |
| `NETBOX_PAGE_SIZE` | ❌ | `100` | Results per API page |
| `NETBOX_TIMEOUT` | ❌ | `30` | Request timeout (seconds) |
| `NETBOX_VERIFY_SSL` | ❌ | `true` | Verify SSL certificates |

See [docs/configuration.md](docs/configuration.md) for details on
token setup and SSL options.

## 📦 Batch Queries

Create a TOML file to query multiple prefixes in one run:

```toml
prefixes = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]

[filters]
# status = "active"
# vrf = "Production"
```

```bash
nbpull batch-prefixes --file prefixes.toml --status-only
```

## 📐 Architecture

```
src/netbox_data_puller/
├── cli.py          # Typer commands + filtering + JSON file output
├── client.py       # Async GET-only NetBox API client
├── config.py       # Pydantic Settings (.env)
├── formatters.py   # Rich table renderers
└── models/         # Pydantic models per resource
    ├── __init__.py
    ├── common.py   # Shared field types / base classes
    ├── aggregate.py
    ├── device.py
    ├── ip_address.py
    ├── prefix.py
    ├── site.py
    ├── tenant.py
    ├── vlan.py
    └── vrf.py
```

See [docs/architecture.md](docs/architecture.md) for a full breakdown.

## 🛠️ Development

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

### Setup

```bash
git clone https://github.com/Champion2005/nbpull.git
cd nbpull
make install    # Install dependencies
```

### Commands

```bash
make all        # format → lint → typecheck → test
make test       # unit tests (no network)
make lint       # ruff linter
make format     # auto-format with ruff
make typecheck  # mypy strict mode
make test-integration  # hits real NetBox API
```

### Running Tests

Unit tests use mocked HTTP responses and require no network access:

```bash
make test
```

Integration tests require `NETBOX_URL` and `NETBOX_TOKEN`:

```bash
make test-integration
```

## 🤝 Contributing

Contributions are welcome! Please read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes.

## 📄 License

This project is licensed under the
**GNU General Public License v3.0** — see the [LICENSE](LICENSE) file
for details.

## 🙏 Acknowledgements

- [NetBox](https://netbox.dev) — the leading open-source IPAM/DCIM
  platform
- [Typer](https://typer.tiangolo.com/) — CLI framework
- [Rich](https://rich.readthedocs.io/) — beautiful terminal formatting
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [Pydantic](https://docs.pydantic.dev/) — data validation
