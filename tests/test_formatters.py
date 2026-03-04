"""🧪 Tests for Rich table and JSON formatters."""

import io
import unittest.mock

from rich.console import Console

from netbox_data_puller.formatters import (
    _display_or_dash,
    _mapping_status,
    _prefix_len,
    _rfc1918_block,
    _styled_status,
    _tags_str,
    print_aggregates,
    print_batch_summary,
    print_devices,
    print_ip_addresses,
    print_json,
    print_prefixes,
    print_prefixes_status,
    print_rfc1918_inventory,
    print_sites,
    print_tenants,
    print_vlans,
    print_vrfs,
)
from netbox_data_puller.models.aggregate import Aggregate
from netbox_data_puller.models.common import ChoiceRef, NestedRef
from netbox_data_puller.models.device import Device
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.site import Site
from netbox_data_puller.models.tenant import Tenant
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


_SAMPLE_AGGREGATE = Aggregate.model_validate(
    {
        "id": 1,
        "display": "10.0.0.0/8",
        "prefix": "10.0.0.0/8",
        "rir": {"id": 1, "display": "RFC 1918"},
        "date_added": "2024-01-01",
        "description": "Private",
    }
)

_SAMPLE_SITE = Site.model_validate(
    {
        "id": 1,
        "display": "DC1",
        "name": "DC1",
        "slug": "dc1",
        "status": {"value": "active", "label": "Active"},
        "region": {"id": 1, "display": "US East"},
        "facility": "NY5",
    }
)

_SAMPLE_DEVICE = Device.model_validate(
    {
        "id": 1,
        "display": "router01",
        "name": "router01",
        "device_type": {"id": 1, "display": "Cisco ASR-9001"},
        "role": {"id": 1, "display": "Core Router"},
        "site": {"id": 1, "display": "DC1"},
        "status": {"value": "active", "label": "Active"},
        "primary_ip": {"id": 5, "display": "10.0.0.1/32"},
    }
)

_SAMPLE_TENANT = Tenant.model_validate(
    {
        "id": 1,
        "display": "Ops",
        "name": "Ops",
        "slug": "ops",
        "group": {"id": 1, "display": "Internal"},
    }
)


class TestPrintAggregates:
    def test_renders_without_error(self) -> None:
        print_aggregates([_SAMPLE_AGGREGATE])

    def test_renders_empty_list(self) -> None:
        print_aggregates([])

    def test_renders_minimal_aggregate(self) -> None:
        a = Aggregate.model_validate(
            {"id": 99, "display": "192.168.0.0/16", "prefix": "192.168.0.0/16"}
        )
        print_aggregates([a])


class TestPrintSites:
    def test_renders_without_error(self) -> None:
        print_sites([_SAMPLE_SITE])

    def test_renders_empty_list(self) -> None:
        print_sites([])

    def test_renders_minimal_site(self) -> None:
        s = Site.model_validate(
            {"id": 1, "display": "DC1", "name": "DC1", "slug": "dc1"}
        )
        print_sites([s])


class TestPrintDevices:
    def test_renders_without_error(self) -> None:
        print_devices([_SAMPLE_DEVICE])

    def test_renders_empty_list(self) -> None:
        print_devices([])

    def test_renders_unnamed_device(self) -> None:
        """Devices without a name (name=None) should render '—'."""
        d = Device.model_validate({"id": 5, "display": "[unnamed]"})
        print_devices([d])


class TestPrintTenants:
    def test_renders_without_error(self) -> None:
        print_tenants([_SAMPLE_TENANT])

    def test_renders_empty_list(self) -> None:
        print_tenants([])

    def test_renders_minimal_tenant(self) -> None:
        t = Tenant.model_validate(
            {"id": 1, "display": "Ops", "name": "Ops", "slug": "ops"}
        )
        print_tenants([t])


# ------------------------------------------------------------------
# RFC 1918 Inventory
# ------------------------------------------------------------------

_SAMPLE_RFC1918_MAPPED = Prefix.model_validate(
    {
        "id": 10,
        "display": "10.0.0.0/24",
        "prefix": "10.0.0.0/24",
        "status": {"value": "active", "label": "Active"},
        "site": None,
        "scope_type": "dcim.site",
        "scope_id": 1,
        "scope": {"id": 1, "display": "NYC"},
        "tenant": {"id": 1, "display": "Ops"},
    }
)
_SAMPLE_RFC1918_UNMAPPED = Prefix.model_validate(
    {
        "id": 11,
        "display": "192.168.0.0/24",
        "prefix": "192.168.0.0/24",
        "status": {"value": "reserved", "label": "Reserved"},
        "site": None,
        "scope_type": None,
        "scope_id": None,
        "scope": None,
        "tenant": None,
    }
)
_SAMPLE_RFC1918_AMBIGUOUS = Prefix.model_validate(
    {
        "id": 12,
        "display": "172.16.0.0/24",
        "prefix": "172.16.0.0/24",
        "status": {"value": "active", "label": "Active"},
        "site": None,
        "scope_type": "dcim.site",
        "scope_id": 2,
        "scope": {"id": 2, "display": "LAX"},
        "tenant": None,
    }
)


class TestRfc1918Block:
    def test_10_block(self) -> None:
        assert _rfc1918_block("10.0.1.0/24") == "10.0.0.0/8"

    def test_172_block(self) -> None:
        assert _rfc1918_block("172.16.5.0/24") == "172.16.0.0/12"

    def test_192_block(self) -> None:
        assert _rfc1918_block("192.168.1.0/24") == "192.168.0.0/16"

    def test_unknown_block(self) -> None:
        assert _rfc1918_block("8.8.8.0/24") == "—"


class TestMappingStatus:
    def test_mapped_both(self) -> None:
        assert _mapping_status(_SAMPLE_RFC1918_MAPPED) == "mapped"

    def test_unmapped_neither(self) -> None:
        assert _mapping_status(_SAMPLE_RFC1918_UNMAPPED) == "unmapped"

    def test_ambiguous_site_only(self) -> None:
        assert _mapping_status(_SAMPLE_RFC1918_AMBIGUOUS) == "ambiguous"

    def test_ambiguous_tenant_only(self) -> None:
        p = Prefix.model_validate(
            {
                "id": 99,
                "display": "10.1.0.0/24",
                "prefix": "10.1.0.0/24",
                "site": None,
                "scope_type": None,
                "scope": None,
                "tenant": {"id": 5, "display": "Corp"},
            }
        )
        assert _mapping_status(p) == "ambiguous"


class TestPrintRfc1918Inventory:
    def test_renders_without_error(self) -> None:
        print_rfc1918_inventory(
            [
                _SAMPLE_RFC1918_MAPPED,
                _SAMPLE_RFC1918_UNMAPPED,
                _SAMPLE_RFC1918_AMBIGUOUS,
            ]
        )

    def test_renders_empty_list(self) -> None:
        print_rfc1918_inventory([])

    def test_renders_single_prefix(self) -> None:
        print_rfc1918_inventory([_SAMPLE_RFC1918_MAPPED])

    def test_renders_with_scope_data(self) -> None:
        """v4.4 scope-based prefixes render correctly in the table."""
        print_rfc1918_inventory([_SAMPLE_RFC1918_MAPPED, _SAMPLE_RFC1918_AMBIGUOUS])

    def test_stats_from_all_records(self) -> None:
        """Stats are derived from all_records, not display records."""
        buf = io.StringIO()
        test_console = Console(file=buf, width=200)
        with unittest.mock.patch(
            "netbox_data_puller.formatters.console", test_console
        ):
            print_rfc1918_inventory(
                [_SAMPLE_RFC1918_MAPPED],
                all_records=[
                    _SAMPLE_RFC1918_MAPPED,
                    _SAMPLE_RFC1918_UNMAPPED,
                    _SAMPLE_RFC1918_AMBIGUOUS,
                ],
            )
        output = buf.getvalue()
        assert "showing 1 of 3 prefixes" in output
        assert "1 mapped" in output
        assert "1 unmapped" in output
        assert "1 ambiguous" in output
        assert "33.3%" in output
        assert "Global Coverage" in output

    def test_stats_without_all_records_fallback(self) -> None:
        """Without all_records, stats come from records (backward compat)."""
        buf = io.StringIO()
        test_console = Console(file=buf, width=200)
        with unittest.mock.patch(
            "netbox_data_puller.formatters.console", test_console
        ):
            print_rfc1918_inventory(
                [
                    _SAMPLE_RFC1918_MAPPED,
                    _SAMPLE_RFC1918_UNMAPPED,
                    _SAMPLE_RFC1918_AMBIGUOUS,
                ]
            )
        output = buf.getvalue()
        assert "3 prefixes" in output
        assert "showing" not in output
        assert "Global Coverage" in output

    def test_stats_empty_all_records(self) -> None:
        """Empty all_records doesn't crash; shows 0.0% coverage."""
        buf = io.StringIO()
        test_console = Console(file=buf, width=200)
        with unittest.mock.patch(
            "netbox_data_puller.formatters.console", test_console
        ):
            print_rfc1918_inventory([], all_records=[])
        output = buf.getvalue()
        assert "0.0%" in output
