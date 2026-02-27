# Test Instructions

Apply to: `tests/**/*.py`

## Rules

- Each test file mirrors a source module: `test_client.py` tests
  `client.py`, `test_models.py` tests `models/`, etc.
- **Unit tests** must never touch the network — use
  [respx](https://github.com/lundberg/respx) to mock httpx responses
- **Integration tests** must be marked with `@pytest.mark.integration`
  and live in `test_integration.py`
- Use `pytest.fixture` for shared setup (client instances, mock
  responses, etc.)
- Async test functions use `async def test_...` — pytest-asyncio
  handles the event loop (`asyncio_mode = "auto"`)
- Assert specific values, not just truthiness
- Test edge cases: empty responses, pagination boundaries, missing
  optional fields
- Verify the **read-only invariant** — ensure `NetBoxClient` has no
  write methods (POST/PUT/PATCH/DELETE)
- Use descriptive test names: `test_prefixes_filters_by_status`,
  `test_pagination_stops_at_limit`

## Mock Pattern

```python
import respx
from httpx import Response

@respx.mock
async def test_example(client: NetBoxClient) -> None:
    respx.get("https://netbox.example.com/api/ipam/prefixes/").mock(
        return_value=Response(200, json={"count": 0, "next": None, "results": []})
    )
    results = await client.get("ipam/prefixes/")
    assert results == []
```

## Do NOT

- Use `unittest.TestCase` — use plain pytest functions
- Use `print()` for debugging — use `pytest.fail()` or assertions
- Skip tests without documenting why (`@pytest.mark.skip(reason="...")`)
