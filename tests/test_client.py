"""🔒 Tests for the read-only NetBox API client.

Verifies:
- Only GET requests are ever made
- Pagination is followed correctly
- Results are aggregated across pages
"""

import httpx
import pytest
import respx

from netbox_data_puller.client import NetBoxClient
from netbox_data_puller.config import NetBoxSettings


def _make_settings() -> NetBoxSettings:
    """Create test settings pointing to a mock URL."""
    return NetBoxSettings.model_validate(
        {
            "url": "https://netbox.example.com",
            "token": "test-token-read-only",
            "page_size": 2,
            "timeout": 5,
            "verify_ssl": False,
        }
    )


@pytest.fixture
def settings() -> NetBoxSettings:
    return _make_settings()


# ------------------------------------------------------------------
# Read-only enforcement
# ------------------------------------------------------------------


class TestReadOnlyEnforcement:
    """Verify the client has NO write methods."""

    def test_no_post_method(self, settings: NetBoxSettings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "post")
        assert not hasattr(client, "create")

    def test_no_put_method(self, settings: NetBoxSettings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "put")
        assert not hasattr(client, "update")

    def test_no_patch_method(self, settings: NetBoxSettings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "patch")

    def test_no_delete_method(self, settings: NetBoxSettings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "delete")
        assert not hasattr(client, "destroy")


# ------------------------------------------------------------------
# Single page fetch
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_single_page(settings: NetBoxSettings) -> None:
    """Single-page response returns all results."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 1,
                "next": None,
                "previous": None,
                "results": [{"id": 1, "prefix": "10.0.0.0/8", "display": "10.0.0.0/8"}],
            },
        )
    )

    async with NetBoxClient(settings) as client:
        results = await client.get("ipam/prefixes/")

    assert len(results) == 1
    assert results[0]["prefix"] == "10.0.0.0/8"


# ------------------------------------------------------------------
# Paginated fetch
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_paginated(settings: NetBoxSettings) -> None:
    """Multi-page responses are aggregated into a single list."""
    # Page 1
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
        params__contains={"offset": "0"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 3,
                "next": "https://netbox.example.com/api/ipam/prefixes/?limit=2&offset=2",
                "previous": None,
                "results": [
                    {"id": 1, "prefix": "10.0.0.0/8", "display": "10.0.0.0/8"},
                    {"id": 2, "prefix": "172.16.0.0/12", "display": "172.16.0.0/12"},
                ],
            },
        )
    )
    # Page 2
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
        params__contains={"offset": "2"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 3,
                "next": None,
                "previous": "https://netbox.example.com/api/ipam/prefixes/?limit=2&offset=0",
                "results": [
                    {
                        "id": 3,
                        "prefix": "192.168.0.0/16",
                        "display": "192.168.0.0/16",
                    },
                ],
            },
        )
    )

    async with NetBoxClient(settings) as client:
        results = await client.get("ipam/prefixes/")

    assert len(results) == 3
    prefixes = [r["prefix"] for r in results]
    assert "10.0.0.0/8" in prefixes
    assert "172.16.0.0/12" in prefixes
    assert "192.168.0.0/16" in prefixes


# ------------------------------------------------------------------
# Auth header
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_auth_header_sent(settings: NetBoxSettings) -> None:
    """Authorization header is sent with the configured token."""
    route = respx.get(
        "https://netbox.example.com/api/ipam/vrfs/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"count": 0, "next": None, "previous": None, "results": []},
        )
    )

    async with NetBoxClient(settings) as client:
        await client.get("ipam/vrfs/")

    assert route.called
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Token test-token-read-only"


# ------------------------------------------------------------------
# HTTP method verification
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_only_get_method_used(settings: NetBoxSettings) -> None:
    """Confirm only GET requests are made."""
    route = respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"count": 0, "next": None, "previous": None, "results": []},
        )
    )

    async with NetBoxClient(settings) as client:
        await client.get("ipam/prefixes/")

    assert route.calls[0].request.method == "GET"


# ------------------------------------------------------------------
# Filters passed as query params
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_filters_passed_as_params(settings: NetBoxSettings) -> None:
    """Filter params are forwarded to the API."""
    route = respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"count": 0, "next": None, "previous": None, "results": []},
        )
    )

    async with NetBoxClient(settings) as client:
        await client.get(
            "ipam/prefixes/",
            params={"status": "active", "vrf": "Production"},
        )

    request = route.calls[0].request
    assert "status=active" in str(request.url)
    assert "vrf=Production" in str(request.url)


# ------------------------------------------------------------------
# max_results limiting
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_pagination_stops_at_limit(settings: NetBoxSettings) -> None:
    """max_results truncates results even when more pages exist."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 5,
                "next": "https://netbox.example.com/api/ipam/prefixes/?limit=2&offset=2",
                "previous": None,
                "results": [
                    {"id": 1, "prefix": "10.0.0.0/8", "display": "10.0.0.0/8"},
                    {"id": 2, "prefix": "172.16.0.0/12", "display": "172.16.0.0/12"},
                    {"id": 3, "prefix": "192.168.0.0/16", "display": "192.168.0.0/16"},
                ],
            },
        )
    )

    async with NetBoxClient(settings) as client:
        results = await client.get("ipam/prefixes/", max_results=2)

    assert len(results) == 2


# ------------------------------------------------------------------
# get_single() tests
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_single_returns_dict(settings: NetBoxSettings) -> None:
    """get_single returns a single object dict."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/42/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"id": 42, "prefix": "10.0.0.0/8", "display": "10.0.0.0/8"},
        )
    )

    async with NetBoxClient(settings) as client:
        result = await client.get_single("ipam/prefixes/42/")

    assert result["id"] == 42
    assert result["prefix"] == "10.0.0.0/8"


# ------------------------------------------------------------------
# HTTP error handling
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_raises_on_404(settings: NetBoxSettings) -> None:
    """4xx errors propagate as httpx.HTTPStatusError."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(return_value=httpx.Response(404))

    async with NetBoxClient(settings) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("ipam/prefixes/")


@respx.mock
@pytest.mark.asyncio
async def test_get_raises_on_500(settings: NetBoxSettings) -> None:
    """5xx errors propagate as httpx.HTTPStatusError."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(return_value=httpx.Response(500))

    async with NetBoxClient(settings) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("ipam/prefixes/")


@respx.mock
@pytest.mark.asyncio
async def test_get_single_raises_on_404(settings: NetBoxSettings) -> None:
    """get_single also propagates HTTP errors."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/999/",
    ).mock(return_value=httpx.Response(404))

    async with NetBoxClient(settings) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_single("ipam/prefixes/999/")


# ------------------------------------------------------------------
# Empty response
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_empty_results(settings: NetBoxSettings) -> None:
    """Empty result set returns an empty list."""
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"count": 0, "next": None, "previous": None, "results": []},
        )
    )

    async with NetBoxClient(settings) as client:
        results = await client.get("ipam/prefixes/")

    assert results == []


# ------------------------------------------------------------------
# Probe tests
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_probe_all_endpoints_ok(settings: NetBoxSettings) -> None:
    """Probe returns success for all default endpoints."""
    respx.get(
        "https://netbox.example.com/api/status/",
    ).mock(
        return_value=httpx.Response(200, json={"netbox-version": "4.0"}),
    )
    for ep in ["ipam/prefixes/", "ipam/ip-addresses/", "ipam/vlans/", "ipam/vrfs/"]:
        respx.get(
            f"https://netbox.example.com/api/{ep}",
        ).mock(
            return_value=httpx.Response(
                200,
                json={"count": 0, "next": None, "results": []},
            ),
        )

    async with NetBoxClient(settings) as client:
        results = await client.probe()

    assert len(results) == 5
    assert all(ok for _, ok, _ in results)


@respx.mock
@pytest.mark.asyncio
async def test_probe_partial_failure(settings: NetBoxSettings) -> None:
    """Probe reports individual failures without aborting."""
    respx.get(
        "https://netbox.example.com/api/status/",
    ).mock(
        return_value=httpx.Response(200, json={"netbox-version": "4.0"}),
    )
    respx.get(
        "https://netbox.example.com/api/ipam/prefixes/",
    ).mock(
        return_value=httpx.Response(403),
    )
    for ep in ["ipam/ip-addresses/", "ipam/vlans/", "ipam/vrfs/"]:
        respx.get(
            f"https://netbox.example.com/api/{ep}",
        ).mock(
            return_value=httpx.Response(
                200,
                json={"count": 0, "next": None, "results": []},
            ),
        )

    async with NetBoxClient(settings) as client:
        results = await client.probe()

    assert len(results) == 5
    status_ok = {ep: ok for ep, ok, _ in results}
    assert status_ok["status/"] is True
    assert status_ok["ipam/prefixes/"] is False
    assert status_ok["ipam/ip-addresses/"] is True


@respx.mock
@pytest.mark.asyncio
async def test_probe_custom_endpoints(settings: NetBoxSettings) -> None:
    """Probe accepts custom endpoint list."""
    respx.get(
        "https://netbox.example.com/api/status/",
    ).mock(
        return_value=httpx.Response(200, json={"netbox-version": "4.0"}),
    )

    async with NetBoxClient(settings) as client:
        results = await client.probe(endpoints=["status/"])

    assert len(results) == 1
    assert results[0][0] == "status/"
    assert results[0][1] is True


@respx.mock
@pytest.mark.asyncio
async def test_probe_uses_only_get(settings: NetBoxSettings) -> None:
    """Probe only uses GET — verifying read-only invariant."""
    route = respx.get(
        "https://netbox.example.com/api/status/",
    ).mock(
        return_value=httpx.Response(200, json={"netbox-version": "4.0"}),
    )

    async with NetBoxClient(settings) as client:
        await client.probe(endpoints=["status/"])

    assert route.calls[0].request.method == "GET"
