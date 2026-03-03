---
applyTo: "src/netbox_data_puller/cli.py, src/netbox_data_puller/formatters.py"
---

# CLI Instructions

Apply to: `src/netbox_data_puller/cli.py`

## Rules

- All commands are defined using [Typer](https://typer.tiangolo.com/)
- Each command follows the pattern: parse flags → build params →
  fetch → format → output
- Use `typer.Option()` with descriptive `help=` text for every flag
- Common filters (status, vrf, tenant, site, tag, search, limit,
  format, verbose) should be consistent across commands
- Use `asyncio.run()` to bridge sync Typer commands with async client
  calls
- Progress indicators use Rich spinners on **stderr** (never stdout)
- Never use `print()` — use `rich.console.Console()` for output and
  `logging` for diagnostics
- The `--format json` flag writes JSON to a file instead of stdout; if
  `--output`/`-o` is not provided the CLI prompts for a filename with a
  default of `<command>_YYYY-MM-DD.json`. Use `_save_json()` in `cli.py`
  for all JSON file output — do not call `print_json()` from commands
- The `--format csv` flag writes a flat CSV file; nested objects (NestedRef,
  ChoiceRef) are reduced to their display string via `_flatten_record()`.
  Use `_save_csv([_flatten_record(r) for r in records], output, "name")`.
  Default filename is `<command>_YYYY-MM-DD.csv`
- Exit codes: 0 = success, 1 = error, 2 = config/auth failure
- Keep the CLI thin — business logic belongs in `client.py` and
  `formatters.py`

## Adding a New Command

1. Add the Typer command function in `cli.py`
2. Reuse existing filter options (copy from `prefixes` command), including
   `output: OutputOpt = None` for JSON/CSV file output
3. Handle all three format branches: `json` → `_save_json()`, `csv` →
   `_save_csv([_flatten_record(r) for r in records], ...)`, else → formatter
3. Add a formatter function in `formatters.py`
4. Add a Pydantic model in `models/` if it's a new resource type
5. Export the new model from `models/__init__.py`
6. Update `docs/commands.md` with the new command reference
7. Update `CHANGELOG.md` under `[Unreleased]`
8. Add unit tests in `tests/test_cli.py`, `tests/test_models.py`, `tests/test_formatters.py`
9. Update the `setup` completion panel in `cli.py` to list the new command

## Do NOT

- Add any write operations (POST/PUT/PATCH/DELETE)
- Import or use `click` directly — use Typer's abstractions
- Put formatting logic inside CLI functions
