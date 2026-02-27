"""🔒 Read-only async HTTP client for the NetBox REST API.

SAFETY: This client ONLY performs GET requests. No data is ever
written, modified, or deleted in NetBox. The HTTP method is
hardcoded — there are no POST/PUT/PATCH/DELETE methods.
"""

import logging
from typing import Any

import httpx

from netbox_data_puller.config import NetBoxSettings

logger = logging.getLogger(__name__)


class NetBoxClient:
    """Async, read-only NetBox API client.

    All requests use HTTP GET. No write operations are exposed
    or possible through this client.
    """

    def __init__(self, settings: NetBoxSettings) -> None:
        base_url = str(settings.url).rstrip("/")
        self._base_url = f"{base_url}/api"
        self._page_size = settings.page_size
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Token {settings.token}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(settings.timeout),
            verify=settings.verify_ssl,
        )

    # ------------------------------------------------------------------
    # Public interface — READ ONLY
    # ------------------------------------------------------------------

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch results from a NetBox API endpoint.

        Uses HTTP GET exclusively. Automatically follows pagination
        until *max_results* records have been collected or all pages
        are exhausted.

        Args:
            endpoint: API path relative to /api/ (e.g. "ipam/prefixes/").
            params: Optional query parameters for filtering.
            max_results: Stop after collecting this many records.
                When ``None`` (default), fetch **all** pages.

        Returns:
            Flat list of result dicts across fetched pages.
        """
        results: list[dict[str, Any]] = []
        page_size = (
            min(self._page_size, max_results)
            if max_results is not None
            else self._page_size
        )
        query = {**(params or {}), "limit": page_size, "offset": 0}

        while True:
            logger.debug("GET %s params=%s", endpoint, query)
            response = await self._client.get(endpoint, params=query)
            response.raise_for_status()
            data = response.json()

            results.extend(data.get("results", []))

            # Stop if we've reached the requested cap
            if max_results is not None and len(results) >= max_results:
                results = results[:max_results]
                break

            if data.get("next") is None:
                break

            query["offset"] = query["offset"] + page_size

        logger.info(
            "Fetched %d records from %s",
            len(results),
            endpoint,
        )
        return results

    async def get_single(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch a single object from a NetBox API endpoint.

        Uses HTTP GET exclusively.

        Args:
            endpoint: API path (e.g. "ipam/prefixes/42/").
            params: Optional query parameters.

        Returns:
            Single result dict.
        """
        logger.debug("GET %s params=%s", endpoint, params)
        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    # ------------------------------------------------------------------
    # Connection probing (read-only)
    # ------------------------------------------------------------------

    async def probe(
        self,
        endpoints: list[str] | None = None,
    ) -> list[tuple[str, bool, str]]:
        """Probe NetBox API endpoints to verify connectivity and auth.

        Uses HTTP GET exclusively. Returns a list of
        ``(endpoint, success, detail)`` tuples.

        Args:
            endpoints: API paths to probe.  Defaults to
                ``["status/", "ipam/prefixes/", "ipam/ip-addresses/",
                "ipam/vlans/", "ipam/vrfs/"]``.

        Returns:
            List of ``(endpoint, ok, detail)`` for each probed path.
        """
        if endpoints is None:
            endpoints = [
                "status/",
                "ipam/prefixes/",
                "ipam/ip-addresses/",
                "ipam/vlans/",
                "ipam/vrfs/",
            ]

        results: list[tuple[str, bool, str]] = []
        for ep in endpoints:
            try:
                logger.debug("PROBE GET %s", ep)
                params: dict[str, int] = {}
                if ep != "status/":
                    params["limit"] = 1
                response = await self._client.get(ep, params=params)
                response.raise_for_status()
                results.append((ep, True, f"{response.status_code} OK"))
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                reason = exc.response.reason_phrase
                results.append((ep, False, f"{code} {reason}"))
            except httpx.ConnectError:
                results.append((ep, False, "Connection refused"))
            except httpx.TimeoutException:
                results.append((ep, False, "Timeout"))
            except Exception as exc:
                results.append((ep, False, str(exc)))
        return results

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "NetBoxClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
