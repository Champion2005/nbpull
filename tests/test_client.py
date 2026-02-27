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
from netbox_data_puller.config import Settings


def _make_settings() -> Settings:
    """Create test settings pointing to a mock URL."""
    return Settings.model_validate(
        {
            "url": "https://netbox.example.com",
            "token": "test-token-read-only",
            "page_size": 2,
            "timeout": 5,
            "verify_ssl": False,
        }
    )


@pytest.fixture
def settings() -> Settings:
    return _make_settings()


# ------------------------------------------------------------------
# Read-only enforcement
# ------------------------------------------------------------------


class TestReadOnlyEnforcement:
    """Verify the client has NO write methods."""

    def test_no_post_method(self, settings: Settings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "post")
        assert not hasattr(client, "create")

    def test_no_put_method(self, settings: Settings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "put")
        assert not hasattr(client, "update")

    def test_no_patch_method(self, settings: Settings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "patch")

    def test_no_delete_method(self, settings: Settings) -> None:
        client = NetBoxClient(settings)
        assert not hasattr(client, "delete")
        assert not hasattr(client, "destroy")


# ------------------------------------------------------------------
# Single page fetch
# ------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_get_single_page(settings: Settings) -> None:
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
async def test_get_paginated(settings: Settings) -> None:
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
async def test_auth_header_sent(settings: Settings) -> None:
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
async def test_only_get_method_used(settings: Settings) -> None:
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
async def test_filters_passed_as_params(settings: Settings) -> None:
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
