"""🧪 Tests for Pydantic models — validation with real-ish NetBox payloads."""

from netbox_data_puller.models import (
    VLAN,
    VRF,
    Aggregate,
    ChoiceRef,
    Device,
    IPAddress,
    NestedRef,
    Prefix,
    Site,
    Tenant,
)
from netbox_data_puller.models.aggregate import Aggregate as DirectAggregate
from netbox_data_puller.models.common import ChoiceRef as CommonChoiceRef
from netbox_data_puller.models.common import NestedRef as CommonNestedRef
from netbox_data_puller.models.device import Device as DirectDevice
from netbox_data_puller.models.site import Site as DirectSite
from netbox_data_puller.models.tenant import Tenant as DirectTenant


class TestPrefixModel:
    def test_minimal_prefix(self) -> None:
        p = Prefix.model_validate(
            {"id": 1, "display": "10.0.0.0/8", "prefix": "10.0.0.0/8"}
        )
        assert p.prefix == "10.0.0.0/8"
        assert p.vrf is None
        assert p.tags == []

    def test_full_prefix_v4_format(self) -> None:
        """NetBox v4 returns status as {value, label}."""
        p = Prefix.model_validate(
            {
                "id": 42,
                "display": "10.10.0.0/16",
                "prefix": "10.10.0.0/16",
                "status": {"value": "active", "label": "Active"},
                "vrf": {"id": 5, "display": "Production"},
                "tenant": {"id": 3, "display": "Ops"},
                "site": {"id": 7, "display": "DC1"},
                "vlan": {"id": 100, "display": "VLAN 100"},
                "role": {"id": 2, "display": "Production"},
                "is_pool": True,
                "mark_utilized": False,
                "description": "Core network",
                "tags": [{"id": 1, "display": "critical"}],
            }
        )
        assert p.status is not None
        assert p.status.display == "Active"
        assert p.status.value == "active"
        assert p.vrf is not None
        assert p.vrf.display == "Production"
        assert p.is_pool is True
        assert len(p.tags) == 1

    def test_container_status(self) -> None:
        """Real-world case that triggered the original bug."""
        p = Prefix.model_validate(
            {
                "id": 99,
                "display": "10.32.16.0/20",
                "prefix": "10.32.16.0/20",
                "status": {"value": "container", "label": "Container"},
            }
        )
        assert p.status is not None
        assert p.status.value == "container"
        assert p.status.display == "Container"


class TestIPAddressModel:
    def test_minimal_ip(self) -> None:
        ip = IPAddress.model_validate(
            {"id": 1, "display": "10.0.0.1/32", "address": "10.0.0.1/32"}
        )
        assert ip.address == "10.0.0.1/32"

    def test_ip_with_dns(self) -> None:
        ip = IPAddress.model_validate(
            {
                "id": 10,
                "display": "10.0.0.1/32",
                "address": "10.0.0.1/32",
                "dns_name": "server01.example.com",
                "status": {"value": "active", "label": "Active"},
            }
        )
        assert ip.dns_name == "server01.example.com"
        assert ip.status is not None
        assert ip.status.display == "Active"


class TestVLANModel:
    def test_minimal_vlan(self) -> None:
        v = VLAN.model_validate(
            {"id": 1, "display": "VLAN 100", "vid": 100, "name": "Management"}
        )
        assert v.vid == 100
        assert v.name == "Management"


class TestVRFModel:
    def test_minimal_vrf(self) -> None:
        vrf = VRF.model_validate({"id": 1, "display": "Global", "name": "Global"})
        assert vrf.name == "Global"
        assert vrf.enforce_unique is True

    def test_vrf_with_rd(self) -> None:
        vrf = VRF.model_validate(
            {
                "id": 5,
                "display": "Production",
                "name": "Production",
                "rd": "65000:100",
                "tenant": {"id": 3, "display": "Ops"},
            }
        )
        assert vrf.rd == "65000:100"
        assert vrf.tenant is not None


# ------------------------------------------------------------------
# extra="allow" tests — unknown fields must survive
# ------------------------------------------------------------------


class TestExtraAllow:
    """Verify that extra='allow' is set and unknown fields are preserved."""

    def test_prefix_preserves_extra_fields(self) -> None:
        p = Prefix.model_validate(
            {
                "id": 1,
                "display": "10.0.0.0/8",
                "prefix": "10.0.0.0/8",
                "url": "https://netbox.example.com/api/ipam/prefixes/1/",
                "custom_fields": {"foo": "bar"},
            }
        )
        extras = p.model_extra or {}
        assert "url" in extras
        assert "custom_fields" in extras

    def test_ip_address_preserves_extra_fields(self) -> None:
        ip = IPAddress.model_validate(
            {
                "id": 1,
                "display": "10.0.0.1/32",
                "address": "10.0.0.1/32",
                "created": "2024-01-01",
            }
        )
        assert (ip.model_extra or {}).get("created") == "2024-01-01"

    def test_vlan_preserves_extra_fields(self) -> None:
        v = VLAN.model_validate(
            {
                "id": 1,
                "display": "VLAN 100",
                "vid": 100,
                "name": "Mgmt",
                "created": "2024-01-01",
            }
        )
        assert "created" in (v.model_extra or {})

    def test_vrf_preserves_extra_fields(self) -> None:
        vrf = VRF.model_validate(
            {
                "id": 1,
                "display": "Global",
                "name": "Global",
                "created": "2024-01-01",
            }
        )
        assert "created" in (vrf.model_extra or {})

    def test_nested_ref_preserves_extra_fields(self) -> None:
        ref = NestedRef.model_validate(
            {"id": 1, "display": "Foo", "url": "https://example.com", "name": "Foo"}
        )
        extras = ref.model_extra or {}
        assert "url" in extras
        assert "name" in extras

    def test_choice_ref_preserves_extra_fields(self) -> None:
        ref = ChoiceRef.model_validate(
            {"value": "active", "label": "Active", "extra_key": True}
        )
        assert (ref.model_extra or {}).get("extra_key") is True


# ------------------------------------------------------------------
# models/__init__.py re-export tests
# ------------------------------------------------------------------


class TestModelsInit:
    """Verify all public models are re-exported from models/__init__."""

    def test_re_exports_prefix(self) -> None:
        assert Prefix is not None

    def test_re_exports_ip_address(self) -> None:
        assert IPAddress is not None

    def test_re_exports_vlan(self) -> None:
        assert VLAN is not None

    def test_re_exports_vrf(self) -> None:
        assert VRF is not None

    def test_re_exports_nested_ref(self) -> None:
        assert NestedRef is CommonNestedRef

    def test_re_exports_choice_ref(self) -> None:
        assert ChoiceRef is CommonChoiceRef


# ------------------------------------------------------------------
# Missing optional fields
# ------------------------------------------------------------------


class TestMissingOptionalFields:
    """Edge case: all optional fields absent."""

    def test_prefix_all_optional_absent(self) -> None:
        p = Prefix.model_validate(
            {"id": 1, "display": "10.0.0.0/8", "prefix": "10.0.0.0/8"}
        )
        assert p.status is None
        assert p.vrf is None
        assert p.tenant is None
        assert p.site is None
        assert p.vlan is None
        assert p.role is None
        assert p.is_pool is False
        assert p.description == ""
        assert p.tags == []

    def test_ip_all_optional_absent(self) -> None:
        ip = IPAddress.model_validate(
            {"id": 1, "display": "10.0.0.1/32", "address": "10.0.0.1/32"}
        )
        assert ip.status is None
        assert ip.vrf is None
        assert ip.dns_name == ""
        assert ip.tags == []

    def test_vlan_all_optional_absent(self) -> None:
        v = VLAN.model_validate(
            {"id": 1, "display": "VLAN 1", "vid": 1, "name": "Default"}
        )
        assert v.status is None
        assert v.group is None
        assert v.tags == []

    def test_vrf_all_optional_absent(self) -> None:
        vrf = VRF.model_validate({"id": 1, "display": "Global", "name": "Global"})
        assert vrf.rd is None
        assert vrf.tenant is None
        assert vrf.tags == []


# ------------------------------------------------------------------
# Aggregate model
# ------------------------------------------------------------------


class TestAggregateModel:
    def test_minimal_aggregate(self) -> None:
        a = Aggregate.model_validate(
            {"id": 1, "display": "10.0.0.0/8", "prefix": "10.0.0.0/8"}
        )
        assert a.prefix == "10.0.0.0/8"
        assert a.rir is None
        assert a.tenant is None
        assert a.date_added is None
        assert a.tags == []

    def test_full_aggregate(self) -> None:
        a = Aggregate.model_validate(
            {
                "id": 5,
                "display": "10.0.0.0/8",
                "prefix": "10.0.0.0/8",
                "rir": {"id": 3, "display": "RFC 1918"},
                "tenant": {"id": 1, "display": "Ops"},
                "date_added": "2024-01-15",
                "description": "Private space",
                "tags": [{"id": 1, "display": "internal"}],
            }
        )
        assert a.rir is not None
        assert a.rir.display == "RFC 1918"
        assert a.tenant is not None
        assert a.date_added == "2024-01-15"
        assert a.description == "Private space"
        assert len(a.tags) == 1

    def test_aggregate_preserves_extra_fields(self) -> None:
        a = Aggregate.model_validate(
            {
                "id": 1,
                "display": "10.0.0.0/8",
                "prefix": "10.0.0.0/8",
                "created": "2024-01-01",
            }
        )
        assert "created" in (a.model_extra or {})

    def test_re_exports_aggregate(self) -> None:
        assert Aggregate is DirectAggregate


# ------------------------------------------------------------------
# Site model
# ------------------------------------------------------------------


class TestSiteModel:
    def test_minimal_site(self) -> None:
        s = Site.model_validate(
            {"id": 1, "display": "DC1", "name": "DC1", "slug": "dc1"}
        )
        assert s.name == "DC1"
        assert s.slug == "dc1"
        assert s.status is None
        assert s.region is None
        assert s.tenant is None
        assert s.facility == ""
        assert s.tags == []

    def test_full_site(self) -> None:
        s = Site.model_validate(
            {
                "id": 7,
                "display": "New York DC",
                "name": "New York DC",
                "slug": "nyc-dc",
                "status": {"value": "active", "label": "Active"},
                "region": {"id": 2, "display": "US East"},
                "tenant": {"id": 1, "display": "Ops"},
                "facility": "NY5",
                "time_zone": "America/New_York",
                "description": "Primary east coast DC",
                "tags": [{"id": 1, "display": "prod"}],
            }
        )
        assert s.status is not None
        assert s.status.value == "active"
        assert s.region is not None
        assert s.region.display == "US East"
        assert s.facility == "NY5"
        assert s.time_zone == "America/New_York"
        assert len(s.tags) == 1

    def test_site_preserves_extra_fields(self) -> None:
        s = Site.model_validate(
            {
                "id": 1,
                "display": "DC1",
                "name": "DC1",
                "slug": "dc1",
                "physical_address": "123 Main St",
            }
        )
        assert "physical_address" in (s.model_extra or {})

    def test_re_exports_site(self) -> None:
        assert Site is DirectSite


# ------------------------------------------------------------------
# Device model
# ------------------------------------------------------------------


class TestDeviceModel:
    def test_minimal_device(self) -> None:
        d = Device.model_validate({"id": 1, "display": "router01"})
        assert d.display == "router01"
        assert d.name is None
        assert d.site is None
        assert d.status is None
        assert d.primary_ip is None
        assert d.serial == ""
        assert d.tags == []

    def test_full_device(self) -> None:
        d = Device.model_validate(
            {
                "id": 10,
                "display": "core-sw-01",
                "name": "core-sw-01",
                "device_type": {"id": 3, "display": "Cisco Catalyst 9300"},
                "role": {"id": 2, "display": "Core Switch"},
                "site": {"id": 7, "display": "DC1"},
                "rack": {"id": 4, "display": "Rack A1"},
                "status": {"value": "active", "label": "Active"},
                "tenant": {"id": 1, "display": "Ops"},
                "platform": {"id": 1, "display": "IOS XE"},
                "primary_ip": {"id": 99, "display": "10.0.0.1/32"},
                "serial": "FCW2045D0AB",
                "description": "Core distribution switch",
                "tags": [{"id": 1, "display": "critical"}],
            }
        )
        assert d.name == "core-sw-01"
        assert d.device_type is not None
        assert d.device_type.display == "Cisco Catalyst 9300"
        assert d.status is not None
        assert d.status.value == "active"
        assert d.primary_ip is not None
        assert d.primary_ip.display == "10.0.0.1/32"
        assert d.serial == "FCW2045D0AB"
        assert len(d.tags) == 1

    def test_device_name_optional(self) -> None:
        """Unnamed devices (e.g. patch panels) have name=None."""
        d = Device.model_validate({"id": 5, "display": "[unnamed]"})
        assert d.name is None

    def test_device_preserves_extra_fields(self) -> None:
        d = Device.model_validate(
            {"id": 1, "display": "rtr01", "asset_tag": "ASSET-001"}
        )
        assert "asset_tag" in (d.model_extra or {})

    def test_re_exports_device(self) -> None:
        assert Device is DirectDevice


# ------------------------------------------------------------------
# Tenant model
# ------------------------------------------------------------------


class TestTenantModel:
    def test_minimal_tenant(self) -> None:
        t = Tenant.model_validate(
            {"id": 1, "display": "Ops", "name": "Ops", "slug": "ops"}
        )
        assert t.name == "Ops"
        assert t.slug == "ops"
        assert t.group is None
        assert t.description == ""
        assert t.tags == []

    def test_full_tenant(self) -> None:
        t = Tenant.model_validate(
            {
                "id": 3,
                "display": "Network Engineering",
                "name": "Network Engineering",
                "slug": "neteng",
                "group": {"id": 1, "display": "Internal"},
                "description": "Core network team",
                "tags": [{"id": 2, "display": "internal"}],
            }
        )
        assert t.group is not None
        assert t.group.display == "Internal"
        assert t.description == "Core network team"
        assert len(t.tags) == 1

    def test_tenant_preserves_extra_fields(self) -> None:
        t = Tenant.model_validate(
            {
                "id": 1,
                "display": "Ops",
                "name": "Ops",
                "slug": "ops",
                "created": "2024-01-01",
            }
        )
        assert "created" in (t.model_extra or {})

    def test_re_exports_tenant(self) -> None:
        assert Tenant is DirectTenant
