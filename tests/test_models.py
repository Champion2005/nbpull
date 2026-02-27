"""🧪 Tests for Pydantic models — validation with real-ish NetBox payloads."""

from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF


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
