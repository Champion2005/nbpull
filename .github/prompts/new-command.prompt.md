---
description: "Scaffold a new read-only CLI command — model, formatter, Typer command, tests, and docs."
argument-hint: "NetBox resource name and API endpoint (e.g. 'circuits /api/dcim/circuits/')"
tools: [execute, agent]
model: Claude Sonnet 4.6 (copilot)
---

# 🧩 NEW-COMMAND — Scaffold a CLI Command

You are running the **new-command** workflow. Your job is to add a complete, tested, documented read-only command for a new NetBox resource. Every step is delegated; you orchestrate only.

---

## Step 1 — Discover Patterns (Parallel)

Spawn **MULTIPLE `reader` subagent** instances in parallel:
- Read an existing similar command end-to-end: `cli.py` (find a comparable command), `formatters.py` (matching formatter), `models/<similar>.py` (matching model)
- Check `models/__init__.py` for the current export list
- Check `docs/commands.md` for the existing table format and options layout
- Confirm the target API endpoint exists in NetBox — look for a matching model file or check `client.py` patterns

Identify:
- Which model fields the NetBox API returns for this resource
- Which filter flags make sense (status, tenant, tag, site, search, limit, format, verbose)
- What the formatter table columns should be

---

## Step 2 — Gate

Present a brief spec to the user:

```
## New Command Spec: nbpull <name>

**API endpoint:** /api/<endpoint>/
**Model fields:** <list key fields>
**Filter flags:** <list flags to add>
**Table columns:** <list columns>

Ready to scaffold?
```

Wait for approval before writing any files.

---

## Step 3 — Write (Sequential)

Spawn **`writer` subagent** with:
- The approved spec
- File paths to create/edit: `models/<resource>.py`, `models/__init__.py`, `formatters.py`, `cli.py`
- Instruction: follow the patterns from the similar command discovered in Step 1 exactly — same flag set, same fetch→validate→render pipeline, same three output branches (table / json / csv)

After writer completes, spawn a second **`writer` subagent** to write:
- Tests in `tests/test_cli.py` — at minimum: table output, json output, csv output, one filter, empty response
- Docs: add row to commands table in `docs/commands.md` and `README.md`, add entry to `CHANGELOG.md` under `[Unreleased]`

---

## Step 4 — Verify

Spawn **`reader` subagent** to review the new command against the spec:
- Does the model have `extra="allow"` and use `NestedRef`/`ChoiceRef`?
- Does the CLI command support all three output formats?
- Are the filter flags consistent with existing commands?
- Are tests present for table, json, csv, empty response?
- Are docs updated?

If issues found, spawn **`writer` subagent** with specific feedback. Max 2 rework cycles.

---

## Step 5 — Run & Report

```bash
make all
```

Report:

```
## ✅ New Command: nbpull <name>

### Files Created / Updated
- `models/<resource>.py` — new model
- `formatters.py` — new formatter function
- `cli.py` — new command added
- `tests/test_cli.py` — N tests added
- `docs/commands.md` — documented
- `README.md` — commands table updated
- `CHANGELOG.md` — entry added

### make all
✅ format / lint / typecheck / test — all passed (N tests)

---
Ready to commit — run `/git-COMMIT` when ready.
```

