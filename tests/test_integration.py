"""🌐 Integration tests — real API calls against NetBox.

These tests hit the live NetBox instance using credentials from .env.
They are **read-only** and safe to run at any time.

Skipped automatically when NETBOX_URL / NETBOX_TOKEN are not set.

Run explicitly:
    pytest -m integration -v
    make test-integration

NOTE: The NetBoxClient always paginates through ALL matching results,
so every test uses tight filters to keep response sizes small and
runtimes fast.
"""

import os

import pytest

from netbox_data_puller.client import NetBoxClient
from netbox_data_puller.config import NetBoxSettings
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF

# ------------------------------------------------------------------
# Skip when credentials are missing
# ------------------------------------------------------------------

_has_creds = bool(os.getenv("NETBOX_URL") and os.getenv("NETBOX_TOKEN"))

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _has_creds,
        reason="NETBOX_URL and NETBOX_TOKEN not set — skipping integration tests",
    ),
]


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture(scope="module")
def settings() -> NetBoxSettings:
    """Load real settings from .env / environment."""
    return NetBoxSettings()  # type: ignore[call-arg]


@pytest.fixture(scope="module")
def small_page_settings(settings: NetBoxSettings) -> NetBoxSettings:
    """Settings with a tiny page_size to test pagination."""
    return NetBoxSettings.model_validate(
        {
            "url": str(settings.url),
            "token": settings.token,
            "page_size": 2,
            "timeout": settings.timeout,
            "verify_ssl": settings.verify_ssl,
        }
    )


@pytest.fixture
async def client(settings: NetBoxSettings) -> NetBoxClient:  # type: ignore[misc]
    """Provide a real NetBoxClient that cleans up after itself."""
    c = NetBoxClient(settings)
    yield c  # type: ignore[misc]
    await c.close()


# ------------------------------------------------------------------
# Prefix tests
# ------------------------------------------------------------------


class TestPrefixIntegration:
    """Validate prefix responses against real NetBox data."""

    async def test_fetch_known_prefix(
        self,
        client: NetBoxClient,
    ) -> None:
        """The 10.0.0.0/8 supernet should always exist."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.0.0.0/8"},
        )
        assert len(raw) >= 1

    async def test_prefix_model_validates_real_payload(
        self,
        client: NetBoxClient,
    ) -> None:
        """Every field in a real response parses into the Prefix model."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.0.0.0/8"},
        )
        for item in raw:
            prefix = Prefix.model_validate(item)
            assert prefix.id > 0
            assert "/" in prefix.prefix

    async def test_known_container_status(
        self,
        client: NetBoxClient,
    ) -> None:
        """The 10.0.0.0/8 Enbridge supernet is a container."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.0.0.0/8"},
        )
        assert len(raw) >= 1
        supernet = Prefix.model_validate(raw[0])
        assert supernet.prefix == "10.0.0.0/8"
        assert supernet.status is not None
        assert supernet.status.value == "container"

    async def test_prefix_status_field_shape(
        self,
        client: NetBoxClient,
    ) -> None:
        """Status returns the v4 {value, label} structure."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.32.16.0/20"},
        )
        for item in raw:
            prefix = Prefix.model_validate(item)
            if prefix.status is not None:
                assert isinstance(prefix.status.value, str)
                assert isinstance(prefix.status.label, str)
                assert prefix.status.value in {
                    "container",
                    "active",
                    "reserved",
                    "deprecated",
                }

    async def test_prefix_tenant_shape(
        self,
        client: NetBoxClient,
    ) -> None:
        """Tenant returns {id, display} when present."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.0.0.0/8"},
        )
        for item in raw:
            prefix = Prefix.model_validate(item)
            if prefix.tenant is not None:
                assert prefix.tenant.id > 0
                assert len(prefix.tenant.display) > 0

    async def test_prefix_extra_fields_preserved(
        self,
        client: NetBoxClient,
    ) -> None:
        """Model uses extra='allow' — real fields like custom_fields survive."""
        raw = await client.get(
            "ipam/prefixes/",
            {"prefix": "10.0.0.0/8"},
        )
        prefix = Prefix.model_validate(raw[0])
        extras = prefix.model_extra or {}
        assert "url" in extras or "created" in extras


# ------------------------------------------------------------------
# IP Address tests
# ------------------------------------------------------------------


class TestIPAddressIntegration:
    """Validate IP address responses against real NetBox data."""

    async def test_fetch_ip_addresses(
        self,
        client: NetBoxClient,
    ) -> None:
        """Fetch IPs within a known small prefix."""
        raw = await client.get(
            "ipam/ip-addresses/",
            {"parent": "10.32.254.0/28"},
        )
        assert len(raw) >= 1

    async def test_ip_model_validates_real_payload(
        self,
        client: NetBoxClient,
    ) -> None:
        raw = await client.get(
            "ipam/ip-addresses/",
            {"parent": "10.32.254.0/28"},
        )
        for item in raw:
            ip = IPAddress.model_validate(item)
            assert ip.id > 0
            assert "/" in ip.address

    async def test_ip_status_shape(
        self,
        client: NetBoxClient,
    ) -> None:
        raw = await client.get(
            "ipam/ip-addresses/",
            {"parent": "10.32.254.0/28"},
        )
        for item in raw:
            ip = IPAddress.model_validate(item)
            if ip.status is not None:
                assert ip.status.value in {
                    "active",
                    "reserved",
                    "deprecated",
                    "dhcp",
                    "slaac",
                }


# ------------------------------------------------------------------
# VLAN tests
# ------------------------------------------------------------------


class TestVLANIntegration:
    """Validate VLAN responses against real NetBox data."""

    async def test_fetch_vlans_by_search(
        self,
        client: NetBoxClient,
    ) -> None:
        """Fetch VLANs matching a known name fragment."""
        raw = await client.get(
            "ipam/vlans/",
            {"q": "Inside-wireless1"},
        )
        assert len(raw) >= 1

    async def test_vlan_model_validates_real_payload(
        self,
        client: NetBoxClient,
    ) -> None:
        raw = await client.get(
            "ipam/vlans/",
            {"q": "Inside-wireless1"},
        )
        for item in raw:
            vlan = VLAN.model_validate(item)
            assert vlan.id > 0
            assert 1 <= vlan.vid <= 4094
            assert len(vlan.name) > 0


# ------------------------------------------------------------------
# VRF tests
# ------------------------------------------------------------------


class TestVRFIntegration:
    """Validate VRF responses against real NetBox data."""

    async def test_fetch_vrfs(
        self,
        client: NetBoxClient,
    ) -> None:
        raw = await client.get(
            "ipam/vrfs/",
            {},
        )
        assert len(raw) >= 1

    async def test_vrf_model_validates_real_payload(
        self,
        client: NetBoxClient,
    ) -> None:
        raw = await client.get(
            "ipam/vrfs/",
            {},
        )
        for item in raw:
            vrf = VRF.model_validate(item)
            assert vrf.id > 0
            assert len(vrf.name) > 0


# ------------------------------------------------------------------
# Pagination test
# ------------------------------------------------------------------


class TestPaginationIntegration:
    """Verify the client correctly follows pagination in production."""

    async def test_pagination_aggregates_results(
        self,
        small_page_settings: NetBoxSettings,
    ) -> None:
        """Fetch with page_size=2 to force multiple pages on a small result."""
        async with NetBoxClient(small_page_settings) as client:
            results = await client.get(
                "ipam/prefixes/",
                {"q": "10.32.16.0/20"},
            )
        # The q= search returns the target + parent containers (3-4 results),
        # which means at least 2 pages with page_size=2.
        assert len(results) >= 3


# ------------------------------------------------------------------
# Client lifecycle
# ------------------------------------------------------------------


class TestClientLifecycle:
    """Verify async context manager works against live API."""

    async def test_context_manager(self, settings: NetBoxSettings) -> None:
        async with NetBoxClient(settings) as client:
            results = await client.get(
                "ipam/prefixes/",
                {"prefix": "10.0.0.0/8"},
            )
        assert len(results) >= 1
