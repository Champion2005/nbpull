# 📋 Command Reference

All commands are **read-only** — nbpull never writes data to NetBox.

## Global Behavior

- Output defaults to **Rich tables** on stdout
- Pass `--format json` for machine-readable JSON output
- Pass `--verbose` / `-v` to enable debug logging (on stderr)
- All commands support filtering via common flags

---

## `nbpull prefixes`

List IPAM prefixes.

```bash
nbpull prefixes
nbpull prefixes --status active --vrf Production
nbpull prefixes --site DC1 --format json
nbpull prefixes --status-only          # compact prefix + status view
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--status` | text | Filter by status (active, reserved, deprecated, container) |
| `--vrf` | text | Filter by VRF name |
| `--tenant` | text | Filter by tenant name |
| `--site` | text | Filter by site name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table` or `json` |
| `--status-only` | flag | Show only prefix and status columns |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull ip-addresses`

List IPAM IP addresses.

```bash
nbpull ip-addresses
nbpull ip-addresses --prefix 10.0.0.0/24
nbpull ip-addresses --status active --vrf Production
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--status` | text | Filter by status |
| `--vrf` | text | Filter by VRF name |
| `--tenant` | text | Filter by tenant name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--prefix` | text | Filter by parent prefix (e.g. 10.0.0.0/24) |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table` or `json` |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull vlans`

List IPAM VLANs.

```bash
nbpull vlans
nbpull vlans --site DC1 --tenant Ops
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--status` | text | Filter by status |
| `--tenant` | text | Filter by tenant name |
| `--site` | text | Filter by site name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table` or `json` |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull vrfs`

List IPAM VRFs.

```bash
nbpull vrfs
nbpull vrfs --tenant Ops --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--tenant` | text | Filter by tenant name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table` or `json` |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull batch-prefixes`

Query multiple prefixes from a TOML file in one run.

```bash
nbpull batch-prefixes                           # uses batch_prefixes.toml
nbpull batch-prefixes --file my_prefixes.toml
nbpull batch-prefixes --status-only             # compact summary table
nbpull batch-prefixes --format json
```

### TOML File Format

```toml
prefixes = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]

[filters]
# status = "active"
# vrf = "Production"
# tenant = "Ops"
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--file` | path | Path to TOML file (default: `batch_prefixes.toml`) |
| `--format` / `-f` | choice | `table` or `json` |
| `--status-only` | flag | Compact prefix + status summary |
| `--verbose` / `-v` | flag | Debug logging |
