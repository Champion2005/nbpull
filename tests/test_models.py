"""🧪 Tests for Pydantic models — validation with real-ish NetBox payloads."""

from netbox_data_puller.models import (
    VLAN,
    VRF,
    ChoiceRef,
    IPAddress,
    NestedRef,
    Prefix,
)
from netbox_data_puller.models.common import ChoiceRef as CommonChoiceRef
from netbox_data_puller.models.common import NestedRef as CommonNestedRef


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
