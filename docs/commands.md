# 📋 Command Reference

All commands are **read-only** — nbpull never writes data to NetBox.

## Global Behavior

- Output defaults to **Rich tables** on stdout
- Pass `--format json` to write output to a JSON file; the CLI prompts for a
  filename with a default of `<command>_YYYY-MM-DD.json`. Use `--output`/`-o`
  to specify the path directly (skips the prompt, useful for scripting)
- Pass `--format csv` to write a flat CSV file (nested objects reduced to
  display strings); default filename `<command>_YYYY-MM-DD.csv`
- Pass `--verbose` / `-v` to enable debug logging (on stderr)
- All commands support filtering via common flags

---

## `nbpull setup`

Interactive setup wizard that configures your NetBox connection.

```bash
nbpull setup
nbpull setup --verbose
```

### What It Does

1. **Creates a `.env` file** — prompts for your NetBox URL and API
   token, writes them to `.env` in the current directory
2. **Tests the connection** — probes `/api/status/` and all four IPAM
   endpoints (`prefixes`, `ip-addresses`, `vlans`, `vrfs`) to verify
   connectivity and permissions
3. **Optionally creates `batch_prefixes.toml`** — walks you through
   entering CIDR prefixes (choose from three input modes: comma-separated
   inline, load from a file, or enter one per line) and optional global
   filters

### Existing Configuration

If a `.env` file already exists, the wizard shows the current URL and
a masked token (last 4 characters visible), then asks whether to
overwrite.

### Options

| Flag | Type | Description |
|---|---|---|
| `--verbose` / `-v` | flag | Debug logging |

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
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
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
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
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
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
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
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
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
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
| `--status-only` | flag | Compact prefix + status summary |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull aggregates`

List IPAM aggregates (top-level IP space allocations from a RIR or organisation).

```bash
nbpull aggregates
nbpull aggregates --rir ARIN
nbpull aggregates --tenant Ops --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--rir` | text | Filter by RIR name (e.g. ARIN, RIPE, RFC1918) |
| `--tenant` | text | Filter by tenant name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull sites`

List DCIM sites (physical or logical locations).

```bash
nbpull sites
nbpull sites --status active --region "US East"
nbpull sites --tenant Ops --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--status` | text | Filter by status (active, planned, retired, etc.) |
| `--tenant` | text | Filter by tenant name |
| `--region` | text | Filter by region name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull devices`

List DCIM devices (physical network hardware).

```bash
nbpull devices
nbpull devices --site DC1 --status active
nbpull devices --role "Core Router" --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--status` | text | Filter by status (active, planned, staged, failed, decommissioning, inventory, offline) |
| `--site` | text | Filter by site name |
| `--tenant` | text | Filter by tenant name |
| `--role` | text | Filter by device role name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
| `--verbose` / `-v` | flag | Debug logging |

> **Note:** The table view shows ID, Name, Status, Site, Role, Device Type, Tenant, and Tags.
> Use `--format json` to access Platform, Primary IP, Serial, and all other fields.

---

## `nbpull tenants`

List tenancy tenants (organisations or customers that own resources).

```bash
nbpull tenants
nbpull tenants --group Internal
nbpull tenants --search ops --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--group` | text | Filter by tenant group name |
| `--tag` | text | Filter by tag slug |
| `--search` / `-s` | text | Free-text search |
| `--limit` / `-l` | int | Max results (default: 50) |
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON output (prompts if omitted with `--format json`) |
| `--verbose` / `-v` | flag | Debug logging |

---

## `nbpull rfc1918`

Inventory all RFC 1918 prefixes in the **Global VRF** (no VRF assignment) and
label each with a **mapping status**:

| Status | Meaning |
|---|---|
| `mapped` | Has **both** a site and a tenant — fully documented |
| `unmapped` | Has **neither** site nor tenant — floating |
| `ambiguous` | Has one but not the other — partially documented |

Queries all three RFC 1918 supernets (`10.0.0.0/8`, `172.16.0.0/12`,
`192.168.0.0/16`) in a single command, deduplicating overlapping results.

```bash
# Full inventory table
nbpull rfc1918

# Show only unmapped prefixes
nbpull rfc1918 --mapping-status unmapped

# Show only ambiguous prefixes as JSON for scripting
nbpull rfc1918 --mapping-status ambiguous --format json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--mapping-status` | text | Filter by `mapped`, `unmapped`, or `ambiguous` |
| `--exclude-role` / `-R` | text | Exclude prefixes whose role matches this name (case-insensitive) |
| `--status` | text | Filter to a specific prefix status (e.g. `active`, `deprecated`); default shows all |
| `--limit` / `-l` | int | Max results per RFC 1918 block (default: 500) |
| `--format` / `-f` | choice | `table`, `json`, or `csv` |
| `--output` / `-o` | path | File to write JSON/CSV output (prompts if omitted) |
| `--verbose` / `-v` | flag | Debug logging |

> **Note:** NetBox does not expose a portable "null VRF" query parameter across
> all versions, so the command fetches all prefixes within each RFC 1918 block
> and filters to the Global VRF (no VRF assignment) in Python.

---

## `nbpull location-report`

Extracts all **mapped** RFC 1918 Global VRF prefixes (those with a site
assignment) and writes a flat CSV suitable for ServiceNow CMDB discovery
scanning or general network documentation. Unmapped prefixes are always excluded.

### CSV Columns

The output includes both **PRD columns** (for CMDB/SMO consumption) and
**general columns** (for broad utility):

| Column | Group | Description |
|--------|-------|-------------|
| `ip_range` | PRD | CIDR notation (same value as `prefix`) |
| `building` | PRD | Site name (same value as `site`) |
| `province_state` | PRD | Region name — depends on NetBox region hierarchy config |
| `city` | PRD | Reserved for future region hierarchy support (currently empty) |
| `prefix` | General | CIDR notation |
| `site` | General | Site name |
| `region` | General | Region name |
| `facility` | General | Facility / address from Site record |
| `tenant` | General | Tenant name |
| `description` | General | Prefix description |
| `status` | General | Prefix status (active, reserved, deprecated, container) |

Default output format is **CSV**.

```bash
# Interactive — prompted for output filename
nbpull location-report

# Write directly to a file
nbpull location-report --output smo_export.csv

# Exclude stub/infrastructure networks
nbpull location-report --exclude-role kubernetes --output smo_export.csv

# JSON format for scripting
nbpull location-report --format json --output smo_export.json
```

### Options

| Flag | Type | Description |
|---|---|---|
| `--exclude-role` / `-R` | text | Exclude prefixes whose role matches this name (case-insensitive) |
| `--limit` / `-l` | int | Max results per RFC 1918 block (default: 1000) |
| `--format` / `-f` | choice | `csv` (default) or `json` |
| `--output` / `-o` | path | Output file path (prompts if omitted) |
| `--verbose` / `-v` | flag | Debug logging |

> **Note:** `region`, `facility`, and their PRD aliases (`province_state`,
> `building`) are populated from the full Site record linked to each prefix.
> If your NetBox Site objects do not have a region or facility set, those
> cells will be empty. `city` is reserved for future support when NetBox
> region hierarchy traversal is implemented. This reflects live NetBox data
> at time of extraction (NFR-1).

> **NetBox v4.2+ compatibility:** Prefixes use the generic `scope` relation
> instead of the legacy `site` field. nbpull transparently handles both via
> the `resolved_site` property on the Prefix model.

