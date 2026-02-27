# 🚀 Releasing

Step-by-step guide for publishing a new version of nbpull.

## Prerequisites

- You are on the `main` branch with a clean working tree
- All CI checks pass (`make all`)
- `CHANGELOG.md` has entries under `[Unreleased]`

## Quick Release (Automated)

```bash
make release VERSION=x.y.z
```

This single command:

1. Bumps `__version__` in `src/netbox_data_puller/__init__.py`
2. Bumps `version` in `pyproject.toml`
3. Runs `make all` (format → lint → typecheck → test)
4. Commits with `chore: release vx.y.z`
5. Creates git tag `vx.y.z`
6. Pushes commit and tag

CI then publishes to PyPI automatically via trusted publishers.

## Manual Release (Step by Step)

If you prefer manual control:

### 1. Decide the Version

Follow [Semantic Versioning](https://semver.org/):

| Change | Bump |
|---|---|
| Breaking API/CLI change | MAJOR |
| New command or feature | MINOR |
| Bug fix, docs, refactor | PATCH |

### 2. Update Version in Two Places

```bash
# src/netbox_data_puller/__init__.py
__version__ = "x.y.z"

# pyproject.toml
version = "x.y.z"
```

Both **must match exactly**.

### 3. Update CHANGELOG.md

Move `[Unreleased]` entries into a new version section:

```markdown
## [x.y.z] — YYYY-MM-DD

### Added
- ...

### Fixed
- ...
```

Update the comparison links at the bottom:

```markdown
[Unreleased]: https://github.com/Champion2005/nbpull/compare/vx.y.z...HEAD
[x.y.z]: https://github.com/Champion2005/nbpull/compare/vPREVIOUS...vx.y.z
```

### 4. Run All Checks

```bash
make all
```

All must pass: format, lint, typecheck, and unit tests.

### 5. Commit, Tag, and Push

```bash
git add -A
git commit -m "chore: release vx.y.z"
git tag vx.y.z
git push && git push --tags
```

### 6. Verify PyPI Release

The `publish.yml` workflow triggers on tag push and publishes to PyPI
via trusted publishers. Check:

- [GitHub Actions](https://github.com/Champion2005/nbpull/actions)
- [PyPI — nbpull](https://pypi.org/project/nbpull/)

### 7. Create GitHub Release (Optional)

Go to [Releases](https://github.com/Champion2005/nbpull/releases/new)
and create a release from the tag, copying the changelog section.

## Post-Release Checklist

- [ ] PyPI shows the new version
- [ ] `uv tool install nbpull` installs the latest
- [ ] GitHub Actions workflow completed successfully
- [ ] GitHub Release created (optional but recommended)

## Troubleshooting

### Version mismatch

If `__init__.py` and `pyproject.toml` have different versions, the
build will produce a package with the `pyproject.toml` version. Always
keep them in sync.

### Tag already exists

```bash
git tag -d vx.y.z          # delete local tag
git push --delete origin vx.y.z  # delete remote tag
```

Then re-tag and push.
