# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Champion2005/nbpull/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/Champion2005/nbpull/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Champion2005/nbpull/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Champion2005/nbpull/releases/tag/v0.1.0
