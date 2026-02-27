# 📐 Architecture

## Overview

nbpull is a read-only CLI tool that queries the
[NetBox REST API](https://demo.netbox.dev/static/docs/rest-api/overview/)
and renders IPAM data as Rich tables or JSON.

```
┌─────────────────────────────────────────────────────┐
│                    CLI (Typer)                       │
│  prefixes · ip-addresses · vlans · vrfs · batch     │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
         ┌──────▼──────┐      ┌───────▼───────┐
         │   Client    │      │  Formatters   │
         │  (httpx)    │      │   (Rich)      │
         │  GET-only   │      │  table / json │
         └──────┬──────┘      └───────────────┘
                │
         ┌──────▼──────┐
         │   Config    │
         │ (pydantic-  │
         │  settings)  │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   Models    │
         │ (Pydantic)  │
         │ Prefix, IP, │
         │ VLAN, VRF   │
         └─────────────┘
```

## Module Responsibilities

### `cli.py` — Command Layer

- Defines all Typer commands and options
- Builds API query parameters from CLI flags
- Orchestrates fetch → validate → render pipeline
- Shows progress spinners on stderr

### `client.py` — HTTP Client

- **Read-only by design** — only `get()` and `get_single()` methods
- Async HTTP via [httpx](https://www.python-httpx.org/)
- Automatic pagination (follows `next` links)
- Context manager for connection lifecycle

### `config.py` — Settings

- Loads from `.env` file or environment variables
- Validated with [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- Prefixed with `NETBOX_` (e.g. `NETBOX_URL`)

### `formatters.py` — Output Rendering

- Rich table formatters for each resource type
- JSON output via `model_dump()`
- Colour-coded status indicators
- Batch summary with direct-match vs parent-container grouping

### `models/` — Data Validation

- Pydantic v2 models for each NetBox IPAM resource
- `extra="allow"` tolerates API fields we don't explicitly model
- `NestedRef` — for related objects (`{id, display}`)
- `ChoiceRef` — for enum fields (`{value, label}`)

## Design Principles

1. **Read-only safety** — The client has no write methods. This is
   enforced by code structure and verified by tests.
2. **Async I/O** — All HTTP calls use `async`/`await` for efficient
   pagination.
3. **Strict typing** — mypy strict mode with Pydantic plugin.
4. **Fail-fast config** — Bad settings surface immediately with
   helpful error messages.
5. **Tolerant models** — `extra="allow"` means new NetBox API fields
   won't break existing functionality.
