# Client Instructions

Apply to: `src/netbox_data_puller/client.py`

## Critical Invariant

**This file must remain read-only.** Only HTTP `GET` methods are
permitted. Never add `POST`, `PUT`, `PATCH`, or `DELETE` methods.
This is the core safety guarantee of nbpull.

## Rules

- `NetBoxClient` is an async context manager (`async with`)
- Uses [httpx.AsyncClient](https://www.python-httpx.org/) internally
- Exposes only `get()` and `get_single()` public methods
- `get()` handles automatic pagination (follows `next` links)
- Pagination must respect the caller's `max_results` limit
- All parameters are passed as typed values — never string-interpolated
- Base URL and auth token come from `config.py` (`NetBoxSettings`)
- Timeout and SSL settings are configurable via settings
- Raise clear exceptions on HTTP errors (4xx, 5xx)
- Log request details at DEBUG level using `logging`

## Pagination Pattern

```python
async def get(self, endpoint: str, params: dict | None = None,
              max_results: int | None = None) -> list[dict]:
    results: list[dict] = []
    page_size = (
        min(self._page_size, max_results)
        if max_results is not None
        else self._page_size
    )
    query = {**(params or {}), "limit": page_size, "offset": 0}

    while True:
        response = await self._client.get(endpoint, params=query)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results", []))
        if max_results and len(results) >= max_results:
            return results[:max_results]
        if data.get("next") is None:
            break
        query["offset"] = query["offset"] + page_size
    return results
```

## Do NOT

- Add any HTTP method besides GET
- Store credentials in the client object beyond what's needed for auth
  headers
- Catch and silence HTTP errors — let them propagate to the CLI layer
