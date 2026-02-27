# Add a New CLI Command

Scaffold a new read-only CLI command for a NetBox resource.

## Steps

1. **Create the Pydantic model** in `src/netbox_data_puller/models/`
   - Inherit from `BaseModel` with `extra="allow"`
   - Use `NestedRef` and `ChoiceRef` for related/enum fields
   - Export from `models/__init__.py`

2. **Add a formatter** in `src/netbox_data_puller/formatters.py`
   - Rich table function: `format_<resource>_table()`
   - JSON output: `model_dump()` serialization

3. **Add the Typer command** in `src/netbox_data_puller/cli.py`
   - Reuse standard filter options (status, tenant, tag, search,
     limit, format, verbose)
   - Follow the fetch → validate → render pipeline
   - Use `asyncio.run()` for the async client call

4. **Write tests** in `tests/test_cli.py`
   - Mock HTTP with respx
   - Test filters, empty responses, pagination edge cases

5. **Update docs**
   - Add to `docs/commands.md` with options table
   - Add to the commands table in `README.md`
   - Add entry under `[Unreleased]` in `CHANGELOG.md`

6. **Verify** — run `make all` to confirm everything passes
