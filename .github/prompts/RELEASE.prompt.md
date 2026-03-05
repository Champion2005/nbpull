---
description: "Cut a release — semver bump, changelog promotion, make all, commit, tag, and push."
argument-hint: "Semver version string (e.g. 1.2.3)"
tools: [execute, agent]
model: Claude Sonnet 4.6 (copilot)
---

# 🚀 RELEASE — Cut a Release

You are running the **release** workflow. Automates: version bump → changelog promotion → quality gate → commit → tag → push.

> **Irreversible after push.** Gate with the user before running `git push`.

---

## Step 1 — Pre-flight Check

Spawn **`reader` subagent** in parallel with **`github` subagent** to check:

- **Reader:** Current version in `pyproject.toml` and `src/netbox_data_puller/__init__.py` — do they match? What is the current `[Unreleased]` section in `CHANGELOG.md`?
- **GitHub:** `git status` (must be clean), `git log origin/main..HEAD --oneline` (must be pushed or on main)

If either check fails, report and stop. Do not proceed with a dirty tree or mismatched versions.

---

## Step 2 — Gate

Present the release summary:

```
## Release Plan: v<VERSION>

**Current version:** x.y.z
**New version:** <VERSION>
**Branch:** <branch> (<N> ahead of origin)

**Changelog entries to promote:**
<paste [Unreleased] content>

---
Proceed with release?
```

**Wait for explicit approval before touching any files.**

---

## Step 3 — Bump & Promote

Spawn **`writer` subagent** to:
1. Update `__version__` in `src/netbox_data_puller/__init__.py` to `<VERSION>`
2. Update `version` in `pyproject.toml` to `<VERSION>`
3. In `CHANGELOG.md`:
   - Rename `## [Unreleased]` → `## [<VERSION>] — <today's date>`
   - Add a new empty `## [Unreleased]` section above it
   - Update comparison links at the bottom:
     - `[Unreleased]` compares `v<VERSION>...HEAD`
     - `[<VERSION>]` compares `vPREVIOUS...v<VERSION>`

---

## Step 4 — Quality Gate

Spawn **`github` subagent** to run:

```bash
make all
```

If any step fails (format / lint / typecheck / test), report the failure and stop. Fix before proceeding.

---

## Step 5 — Commit, Tag, Push, and Publish

Spawn **`github` subagent** to:

```bash
git add src/netbox_data_puller/__init__.py pyproject.toml CHANGELOG.md
git commit -m "chore: release v<VERSION>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git tag v<VERSION>
git push && git push --tags
gh release create v<VERSION> --title "v<VERSION>" --notes "<release notes>"
```

---

## Step 6 — Report

```
## ✅ Released v<VERSION>

**Commit:** <sha>
**Tag:** v<VERSION>
**Pushed:** ✅

CI will run on push. PyPI publish triggers automatically when a GitHub
Release is created from tag v<VERSION>.

---
Next: create a GitHub Release at https://github.com/<owner>/nbpull/releases/new
```

