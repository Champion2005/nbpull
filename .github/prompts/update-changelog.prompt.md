# Update Changelog

Add entries to `CHANGELOG.md` following Keep a Changelog format.

## Format

```markdown
## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

### CI
- CI/CD pipeline changes

### Docs
- Documentation updates
```

## Rules

- Place new entries under `[Unreleased]`
- Use past tense: "Added", "Fixed", not "Add", "Fix"
- Start each entry with an emoji matching the category:
  - Added: 📡 (commands), 🎨 (UI), ⚡ (performance)
  - Fixed: 🐛
  - CI: 📦
  - Docs: 📝
- Reference issue/PR numbers when applicable: `(#42)`
- Keep entries concise but descriptive
- When releasing, the release process moves `[Unreleased]` items into
  the new version section
