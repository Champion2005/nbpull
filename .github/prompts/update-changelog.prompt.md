---
description: "Add entries to CHANGELOG.md under [Unreleased] following Keep a Changelog format."
argument-hint: "Change description, or leave blank to auto-detect from recent git diff"
tools: [execute, agent]
model: Claude Sonnet 4.6 (copilot)
---

# 📝 UPDATE-CHANGELOG — Add Changelog Entries

You are running the **update-changelog** workflow. Add one or more entries to `CHANGELOG.md` under `[Unreleased]`.

---

## Step 1 — Discover Changes

If the user provided a description, use it directly. Otherwise, spawn **`github` subagent** to run:

```bash
git diff main..HEAD --stat
git log main..HEAD --oneline
```

Return the file-level diff summary and commit list. Use this to infer what categories and entries to add.

---

## Step 2 — Draft Entries

Draft changelog entries following this format:

```markdown
## [Unreleased]

### Added
- 📡 `<command>` — <what it does> (#<issue> if applicable)

### Changed
- <description of changed behaviour>

### Fixed
- 🐛 <bug description>

### Removed
- <removed feature>

### CI
- 📦 <CI/CD change>

### Docs
- 📝 <documentation change>
```

**Rules:**
- Only include sections that have entries — omit empty sections
- Use past tense: "Added X", "Fixed Y" — not "Add X", "Fix Y"
- Start each entry with an emoji matching the category:
  - Added commands: 📡 | UI/output: 🎨 | performance: ⚡ | data: 📊
  - Fixed: 🐛 | CI: 📦 | Docs: 📝
- Keep entries concise but descriptive — one line per entry
- Reference issue/PR numbers when applicable: `(#42)`

Present the draft to the user:

```
## Proposed Changelog Entries

<draft entries>

---
Add these entries?
```

**Gate:** Wait for approval before writing.

---

## Step 3 — Write

Spawn **`writer` subagent** to insert the approved entries under `## [Unreleased]` in `CHANGELOG.md`. If `[Unreleased]` does not exist, create it at the top (above the most recent version section).

---

## Step 4 — Confirm

Spawn **`reader` subagent** to read the updated `[Unreleased]` section and confirm the entries were inserted correctly.

Report:

```
## ✅ Changelog Updated

### Added under [Unreleased]
<entries>

CHANGELOG.md — ✅
```

