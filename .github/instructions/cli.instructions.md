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
- The `--format json` flag outputs raw JSON to stdout for piping
- Exit codes: 0 = success, 1 = error, 2 = config/auth failure
- Keep the CLI thin — business logic belongs in `client.py` and
  `formatters.py`

## Adding a New Command

1. Add the Typer command function in `cli.py`
2. Reuse existing filter options (copy from `prefixes` command)
3. Add a formatter function in `formatters.py`
4. Add a Pydantic model in `models/` if it's a new resource type
5. Update `docs/commands.md` with the new command reference
6. Add unit tests in `tests/test_cli.py`

## Do NOT

- Add any write operations (POST/PUT/PATCH/DELETE)
- Import or use `click` directly — use Typer's abstractions
- Put formatting logic inside CLI functions
