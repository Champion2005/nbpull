"""🔒 Read-only async HTTP client for the NetBox REST API.

SAFETY: This client ONLY performs GET requests. No data is ever
written, modified, or deleted in NetBox. The HTTP method is
hardcoded — there are no POST/PUT/PATCH/DELETE methods.
"""

import logging
from typing import Any

import httpx

from netbox_data_puller.config import Settings

logger = logging.getLogger(__name__)


class NetBoxClient:
    """Async, read-only NetBox API client.

    All requests use HTTP GET. No write operations are exposed
    or possible through this client.
    """

    def __init__(self, settings: Settings) -> None:
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
    ) -> list[dict[str, Any]]:
        """Fetch all pages of results from a NetBox API endpoint.

        Uses HTTP GET exclusively. Automatically follows pagination.

        Args:
            endpoint: API path relative to /api/ (e.g. "ipam/prefixes/").
            params: Optional query parameters for filtering.

        Returns:
            Flat list of result dicts across all pages.
        """
        results: list[dict[str, Any]] = []
        query = {**(params or {}), "limit": self._page_size, "offset": 0}

        while True:
            logger.debug("GET %s params=%s", endpoint, query)
            response = await self._client.get(endpoint, params=query)
            response.raise_for_status()
            data = response.json()

            results.extend(data.get("results", []))

            if data.get("next") is None:
                break

            query["offset"] = query["offset"] + self._page_size

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
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "NetBoxClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
