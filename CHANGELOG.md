# 📝 Changelog

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Champion2005/nbpull/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Champion2005/nbpull/releases/tag/v0.1.0
