"""🧪 Tests for Rich table and JSON formatters."""

from netbox_data_puller.formatters import (
    _display_or_dash,
    _prefix_len,
    _styled_status,
    _tags_str,
    print_batch_summary,
    print_ip_addresses,
    print_json,
    print_prefixes,
    print_prefixes_status,
    print_vlans,
    print_vrfs,
)
from netbox_data_puller.models.common import ChoiceRef, NestedRef
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF

# ------------------------------------------------------------------
# Helper function tests
# ------------------------------------------------------------------


class TestDisplayOrDash:
    def test_none_returns_dash(self) -> None:
        assert _display_or_dash(None) == "—"

    def test_nested_ref_returns_display(self) -> None:
        ref = NestedRef(id=1, display="Production")
        assert _display_or_dash(ref) == "Production"

    def test_plain_string_returns_str(self) -> None:
        assert _display_or_dash("hello") == "hello"


class TestTagsStr:
    def test_empty_tags(self) -> None:
        assert _tags_str([]) == "—"

    def test_single_tag(self) -> None:
        tags = [NestedRef(id=1, display="critical")]
        assert _tags_str(tags) == "critical"

    def test_multiple_tags(self) -> None:
        tags = [
            NestedRef(id=1, display="critical"),
            NestedRef(id=2, display="prod"),
        ]
        assert _tags_str(tags) == "critical, prod"


class TestStyledStatus:
    def test_none_returns_dash(self) -> None:
        text = _styled_status(None)
        assert text.plain == "—"

    def test_active_status(self) -> None:
        status = ChoiceRef(value="active", label="Active")
        text = _styled_status(status)
        assert text.plain == "Active"
        assert "green" in str(text.style)

    def test_reserved_status(self) -> None:
        status = ChoiceRef(value="reserved", label="Reserved")
        text = _styled_status(status)
        assert text.plain == "Reserved"
        assert "yellow" in str(text.style)

    def test_deprecated_status(self) -> None:
        status = ChoiceRef(value="deprecated", label="Deprecated")
        text = _styled_status(status)
        assert text.plain == "Deprecated"
        assert "red" in str(text.style)

    def test_unknown_status_no_style(self) -> None:
        status = ChoiceRef(value="custom", label="Custom")
        text = _styled_status(status)
        assert text.plain == "Custom"


class TestPrefixLen:
    def test_valid_cidr(self) -> None:
        assert _prefix_len("10.0.0.0/8") == 8
        assert _prefix_len("192.168.0.0/24") == 24

    def test_no_slash(self) -> None:
        assert _prefix_len("10.0.0.0") == 0

    def test_invalid_mask(self) -> None:
        assert _prefix_len("10.0.0.0/abc") == 0


# ------------------------------------------------------------------
# Render-to-console tests (no crash, no exceptions)
# ------------------------------------------------------------------

_SAMPLE_PREFIX = Prefix.model_validate(
    {
        "id": 1,
        "display": "10.0.0.0/8",
        "prefix": "10.0.0.0/8",
        "status": {"value": "active", "label": "Active"},
        "vrf": None,
        "tenant": None,
        "site": None,
        "vlan": None,
        "role": None,
        "is_pool": False,
        "mark_utilized": False,
        "description": "RFC1918",
        "tags": [],
    }
)

_SAMPLE_IP = IPAddress.model_validate(
    {
        "id": 10,
        "display": "10.0.0.1/32",
        "address": "10.0.0.1/32",
        "status": {"value": "active", "label": "Active"},
        "dns_name": "server01.example.com",
    }
)

_SAMPLE_VLAN = VLAN.model_validate(
    {
        "id": 1,
        "display": "VLAN 100",
        "vid": 100,
        "name": "Management",
        "status": {"value": "active", "label": "Active"},
    }
)

_SAMPLE_VRF = VRF.model_validate(
    {
        "id": 5,
        "display": "Production",
        "name": "Production",
        "rd": "65000:100",
        "enforce_unique": True,
    }
)


class TestPrintPrefixes:
    def test_renders_without_error(self) -> None:
        print_prefixes([_SAMPLE_PREFIX])

    def test_renders_empty_list(self) -> None:
        print_prefixes([])


class TestPrintPrefixesStatus:
    def test_renders_without_error(self) -> None:
        print_prefixes_status([_SAMPLE_PREFIX])

    def test_renders_empty_list(self) -> None:
        print_prefixes_status([])


class TestPrintIPAddresses:
    def test_renders_without_error(self) -> None:
        print_ip_addresses([_SAMPLE_IP])

    def test_renders_empty_list(self) -> None:
        print_ip_addresses([])


class TestPrintVLANs:
    def test_renders_without_error(self) -> None:
        print_vlans([_SAMPLE_VLAN])

    def test_renders_empty_list(self) -> None:
        print_vlans([])


class TestPrintVRFs:
    def test_renders_without_error(self) -> None:
        print_vrfs([_SAMPLE_VRF])

    def test_renders_empty_list(self) -> None:
        print_vrfs([])


class TestPrintJson:
    def test_renders_without_error(self) -> None:
        print_json([_SAMPLE_PREFIX])

    def test_renders_empty_list(self) -> None:
        print_json([])


class TestPrintBatchSummary:
    def test_with_results(self) -> None:
        results = [("10.0.0.0/8", [_SAMPLE_PREFIX])]
        print_batch_summary(results, [])

    def test_with_not_found(self) -> None:
        print_batch_summary([], ["99.99.99.0/24"])

    def test_approximate_match(self) -> None:
        """When no exact match, shows closest parent."""
        parent = Prefix.model_validate(
            {
                "id": 2,
                "display": "10.0.0.0/8",
                "prefix": "10.0.0.0/8",
                "status": {"value": "container", "label": "Container"},
            }
        )
        results = [("10.32.16.0/20", [parent])]
        print_batch_summary(results, [])
