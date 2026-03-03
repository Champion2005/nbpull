# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.3.0] — 2026-03-03

### Added

- 🌐 **NetBox v4.4+ compatibility** — `Prefix` model now supports the
  generic `scope` relation (`scope_type`, `scope_id`, `scope`) introduced
  in NetBox v4.2. A `resolved_site` property transparently handles both
  v4.2+ `scope` and legacy `site` fields. All CLI commands, formatters,
  and tests updated.
- 📋 **Expanded `location-report` CSV columns** — output now includes both
  PRD columns (`ip_range`, `building`, `province_state`, `city`) for
  CMDB/SMO consumption and general columns (`prefix`, `site`, `region`,
  `facility`, `tenant`, `description`, `status`) for broad utility.
- 📊 CSV output format (`--format csv`) on all data commands — writes a
  flat CSV file; nested NetBox objects (site, tenant, role, etc.) are
  reduced to their display string. Default output file is
  `<command>_YYYY-MM-DD.csv` when `--output` is not provided.
- 🖧 `--exclude-role`/`-R` filter on `rfc1918` and `location-report` —
  exclude prefixes whose role matches the given name (case-insensitive),
  e.g. `--exclude-role kubernetes` to drop stub/infrastructure networks
  that are out of scope per the PRD.
- 🗂️ Role and Description columns added to `rfc1918` table output.
- 🔍 `--status` filter on `rfc1918` — filter audit to a specific prefix
  status (e.g. `--status active` to exclude deprecated/decommissioned
  prefixes per PRD out-of-scope).
- 📊 Coverage percentage displayed in `rfc1918` table footer — shows
  `X.X% coverage` with a green/red indicator against the 90% PRD target
  (SC-1: "100% mapped, or 90%+ with remaining delegated to NetOps").
- 📋 `location-report` command (Phase 2 scaffold) — extracts all
  **mapped** RFC 1918 Global VRF prefixes (site-assigned only) and writes
  a flat CSV with columns `prefix, site, region, facility, tenant,
  description` for ServiceNow CMDB discovery scanning. Default format is
  `csv`; supports `--format json`, `--output`/`-o`, and
  `--exclude-role`/`-R`. Region and facility are **enriched** from full
  Site objects (batch-fetched via `dcim/sites/`), not just the NestedRef
  on each prefix.

## [0.2.1] — 2026-03-02

### Added

- 📄 `--output`/`-o` flag on all data commands (`prefixes`,
  `ip-addresses`, `vlans`, `vrfs`, `aggregates`, `sites`, `devices`,
  `tenants`, `rfc1918`, `batch-prefixes`) — when `--format json` is
  used, output is written to a file instead of the terminal. If
  `--output` is not provided, the CLI prompts for a filename with a
  sensible default (`<command>_YYYY-MM-DD.json`).
- 🗂️ `setup` batch prefix entry now supports three input modes:
  **1** — paste a comma-separated list inline;
  **2** — load from an existing file containing comma-separated CIDRs;
  **3** — enter prefixes one per line interactively (original behaviour).

## [0.2.0] — 2026-03-02

### Added

- 📊 `aggregates` command — list IPAM aggregates (top-level IP space by
  RIR) with `--rir`, `--tenant`, `--tag`, `--search`, `--limit`, and
  `--format` filters
- 🏢 `sites` command — list DCIM sites with `--status`, `--tenant`,
  `--region`, `--tag`, `--search`, `--limit`, and `--format` filters
- 🖧 `devices` command — list DCIM devices with `--status`, `--site`,
  `--tenant`, `--role`, `--tag`, `--search`, `--limit`, and `--format`
  filters; table shows ID, Name, Status, Site, Role, Device Type,
  Tenant, Tags; full detail available via `--format json`
- 🏛️ `tenants` command — list Tenancy tenants with `--group`, `--tag`,
  `--search`, `--limit`, and `--format` filters
- 📦 Pydantic models: `Aggregate` (`models/aggregate.py`),
  `Site` (`models/site.py`), `Device` (`models/device.py`),
  `Tenant` (`models/tenant.py`)
- 🎨 Rich table formatters: `print_aggregates`, `print_sites`,
  `print_devices`, `print_tenants` in `formatters.py`
- 🧪 Tests for all 4 new models, formatters, and CLI commands
- 🏠 `rfc1918` command — inventory all RFC 1918 prefixes from the Global
  VRF with computed mapping status (`mapped` / `unmapped` / `ambiguous`)
  based on site+tenant assignments; supports `--mapping-status` filter
  and `--format json`; queries all three RFC 1918 supernets
  (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) using
  `vrf_id=0&within_include=<block>` per block
- 🎨 `print_rfc1918_inventory` formatter and `_mapping_status` /
  `_rfc1918_block` helpers in `formatters.py`
- 🧪 Tests for `rfc1918` command, formatter, and helpers
- 🛠️ `setup` completion panel now lists all 9 commands

### Changed

- 📦 `models/__init__.py` now exports `Aggregate`, `Site`, `Device`,
  `Tenant` alongside existing types
- 🖧 `print_devices` table renders 8 columns (omits Platform and
  Primary IP to fit an 80-char terminal; use `--format json` for all
  fields)

## [0.1.3] — 2026-02-27

### Added

- 🛠️ `setup` command — interactive wizard that creates `.env`, tests
  the NetBox connection (probes `status/` + all 4 IPAM endpoints),
  and optionally creates `batch_prefixes.toml` with user-provided
  prefixes and global filters
- 🔍 `NetBoxClient.probe()` — read-only endpoint probe method for
  verifying connectivity and auth against multiple API paths

## [0.1.2] — 2026-02-27

### Added

- 📡 `--site` filter for `ip-addresses` command, matching all other commands
- 🧪 `test_formatters.py` — unit tests for all Rich table and JSON formatters
- 🧪 CLI tests for `ip-addresses`, `vlans`, `vrfs` commands
- 🧪 Client tests for `max_results` limiting, `get_single()`, HTTP error propagation, empty responses
- 🧪 Model tests for `extra="allow"` preservation, `models/__init__` re-exports, missing optional fields

### Changed

- 🎨 Renamed `Settings` to `NetBoxSettings` in `config.py` to match documented convention
- 🎨 Moved `NestedRef` and `ChoiceRef` from `prefix.py` into new `models/common.py`
- 🎨 Models now use `model_config = ConfigDict(extra="allow")` instead of class keyword arg
- 🎨 `NestedRef` and `ChoiceRef` now set `extra="allow"` to preserve unknown API fields
- 🎨 `models/__init__.py` re-exports all public types (`Prefix`, `IPAddress`, `VLAN`, `VRF`, `NestedRef`, `ChoiceRef`)

### Fixed

- 🐛 Config/auth errors now exit with code 2 (was 1), matching CLI instruction spec

### Docs

- 📝 Updated `client.instructions.md` pagination pattern to match actual offset-based implementation

## [0.1.1] — 2026-02-27

### Fixed

- 🐛 Respect `--limit` flag — stop pagination after `max_results`
  reached instead of fetching all pages

### CI

- 📦 Add PyPI publish workflow via trusted publishers

## [0.1.0] — 2026-02-27

### Added

- 📡 `prefixes` command — list and filter IPAM prefixes
- 🖥️ `ip-addresses` command — query IP address allocations
- 🏷️ `vlans` command — browse VLAN assignments
- 🔀 `vrfs` command — inspect VRF instances
- 📦 `batch-prefixes` command — query multiple prefixes from a
  TOML file
- 🎨 Rich table output with colour-coded status
- 📄 JSON output via `--format json`
- 🔎 Filters: `--status`, `--vrf`, `--tenant`, `--site`, `--tag`,
  `--search`
- ⚡ Async HTTP client with automatic pagination
- 🔒 Read-only safety guarantee — only GET requests, ever
- ⚙️ Configuration via `.env` / environment variables (pydantic-settings)

[Unreleased]: https://github.com/Champion2005/nbpull/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Champion2005/nbpull/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/Champion2005/nbpull/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Champion2005/nbpull/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/Champion2005/nbpull/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Champion2005/nbpull/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Champion2005/nbpull/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Champion2005/nbpull/releases/tag/v0.1.0
