# Release nbpull

Automates: version bump → changelog update → commit → tag → push.

## Usage

Run `make release VERSION=x.y.z` from the repo root.

## Steps

1. Verify the version follows semver (MAJOR.MINOR.PATCH)
2. Update `__version__` in `src/netbox_data_puller/__init__.py`
3. Update `version` in `pyproject.toml`
4. Move items from `[Unreleased]` to a new `[x.y.z]` section in
   `CHANGELOG.md` with today's date
5. Update the comparison links at the bottom of `CHANGELOG.md`:
   - `[Unreleased]` should compare `vx.y.z...HEAD`
   - `[x.y.z]` should compare `vPREVIOUS...vx.y.z`
6. Run `make all` to ensure format / lint / typecheck / test all pass
7. Commit with message: `chore: release vx.y.z`
8. Create git tag: `git tag vx.y.z`
9. Push commit and tag: `git push && git push --tags`
10. CI publishes to PyPI automatically via trusted publishers
