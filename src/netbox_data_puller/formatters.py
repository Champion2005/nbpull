"""🎨 Rich table formatters for NetBox IPAM resources."""

import json
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _display_or_dash(obj: Any) -> str:
    """Extract display name from a nested ref, or return '—'."""
    if obj is None:
        return "—"
    if hasattr(obj, "display"):
        return str(obj.display)
    return str(obj)


def _tags_str(tags: list[Any]) -> str:
    """Format tags as a comma-separated string."""
    return ", ".join(t.display for t in tags) if tags else "—"


def _styled_status(obj: Any) -> Text:
    """Return a Rich Text object with colour-coded status."""
    if obj is None:
        return Text("—", style="dim")
    label = str(obj.display) if hasattr(obj, "display") else str(obj)
    value = obj.value if hasattr(obj, "value") else ""
    style_map = {
        "active": "bold green",
        "reserved": "bold yellow",
        "deprecated": "bold red",
        "container": "bold blue",
        "dhcp": "bold magenta",
        "slaac": "bold magenta",
    }
    return Text(label, style=style_map.get(value, ""))


# ------------------------------------------------------------------
# JSON output
# ------------------------------------------------------------------


def print_json(records: list[Any]) -> None:
    """Print records as formatted JSON to stdout."""
    data = [
        r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in records
    ]
    console.print_json(json.dumps(data, indent=2, default=str))


# ------------------------------------------------------------------
# Prefixes
# ------------------------------------------------------------------


def print_prefixes(records: list[Any]) -> None:
    """Render prefixes as a Rich table."""
    table = Table(
        title="📡 IPAM Prefixes",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Prefix", style="bold green")
    table.add_column("Status")
    table.add_column("VRF")
    table.add_column("Tenant")
    table.add_column("Site")
    table.add_column("VLAN")
    table.add_column("Role")
    table.add_column("Pool", justify="center")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.prefix,
            _styled_status(r.status),
            _display_or_dash(r.vrf),
            _display_or_dash(r.tenant),
            _display_or_dash(r.resolved_site),
            _display_or_dash(r.vlan),
            _display_or_dash(r.role),
            "✅" if r.is_pool else "—",
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} prefixes[/dim]\n")


def print_prefixes_status(records: list[Any]) -> None:
    """Render a compact prefix + status table."""
    table = Table(
        title="📡 Prefix Status",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("Prefix", style="bold green")
    table.add_column("Status")

    for r in records:
        table.add_row(r.prefix, _styled_status(r.status))

    console.print(table)
    console.print(f"[dim]  {len(records)} prefixes[/dim]\n")


def print_batch_summary(
    results: list[tuple[str, list[Any]]],
    not_found: list[str],
) -> None:
    """Render a single consolidated table for batch --status-only.

    Groups results by queried CIDR and shows the direct match status
    prominently, with parent containers shown underneath in dim text.
    """
    table = Table(
        title="📦 Batch Prefix Status",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
        padding=(0, 1),
    )
    table.add_column("Queried Prefix", style="bold white")
    table.add_column("Matched Prefix", style="green")
    table.add_column("Status")
    table.add_column("Site")
    table.add_column("Tenant")
    table.add_column("Description", max_width=32)

    for cidr, records in results:
        # Separate direct match from parent containers
        direct = [r for r in records if r.prefix == cidr]
        parents = [r for r in records if r.prefix != cidr]

        if direct:
            for r in direct:
                table.add_row(
                    cidr,
                    r.prefix,
                    _styled_status(r.status),
                    _display_or_dash(r.resolved_site),
                    _display_or_dash(r.tenant),
                    r.description or "—",
                )
        elif parents:
            # No exact match — show closest parent
            closest = max(parents, key=lambda p: _prefix_len(p.prefix))
            table.add_row(
                cidr,
                Text(f"≈ {closest.prefix}", style="yellow"),
                _styled_status(closest.status),
                _display_or_dash(closest.resolved_site),
                _display_or_dash(closest.tenant),
                closest.description or "—",
            )

    for cidr in not_found:
        table.add_row(
            cidr,
            Text("—", style="dim"),
            Text("Not Found", style="bold red"),
            "—",
            "—",
            "—",
        )

    console.print()
    console.print(table)

    # Compact legend
    legend = (
        "[dim]Status: "
        "[bold green]● Active[/bold green]  "
        "[bold blue]● Container[/bold blue]  "
        "[bold yellow]● Reserved[/bold yellow]  "
        "[bold red]● Deprecated[/bold red]"
        "[/dim]"
    )
    console.print(legend)


def _prefix_len(prefix: str) -> int:
    """Extract the CIDR mask length for sorting."""
    try:
        return int(prefix.split("/")[1])
    except (IndexError, ValueError):
        return 0


# ------------------------------------------------------------------
# IP Addresses
# ------------------------------------------------------------------


def print_ip_addresses(records: list[Any]) -> None:
    """Render IP addresses as a Rich table."""
    table = Table(
        title="🖥️  IPAM IP Addresses",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Address", style="bold green")
    table.add_column("Status")
    table.add_column("VRF")
    table.add_column("Tenant")
    table.add_column("DNS Name")
    table.add_column("Role")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.address,
            _styled_status(r.status),
            _display_or_dash(r.vrf),
            _display_or_dash(r.tenant),
            r.dns_name or "—",
            _display_or_dash(r.role),
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} IP addresses[/dim]\n")


# ------------------------------------------------------------------
# VLANs
# ------------------------------------------------------------------


def print_vlans(records: list[Any]) -> None:
    """Render VLANs as a Rich table."""
    table = Table(
        title="🏷️  IPAM VLANs",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("VID", justify="right", style="bold")
    table.add_column("Name", style="bold green")
    table.add_column("Status")
    table.add_column("Tenant")
    table.add_column("Site")
    table.add_column("Group")
    table.add_column("Role")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            str(r.vid),
            r.name,
            _styled_status(r.status),
            _display_or_dash(r.tenant),
            _display_or_dash(r.site),
            _display_or_dash(r.group),
            _display_or_dash(r.role),
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} VLANs[/dim]\n")


# ------------------------------------------------------------------
# VRFs
# ------------------------------------------------------------------


def print_vrfs(records: list[Any]) -> None:
    """Render VRFs as a Rich table."""
    table = Table(
        title="🔀 IPAM VRFs",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Name", style="bold green")
    table.add_column("RD")
    table.add_column("Tenant")
    table.add_column("Enforce Unique", justify="center")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.name,
            r.rd or "—",
            _display_or_dash(r.tenant),
            "✅" if r.enforce_unique else "❌",
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} VRFs[/dim]\n")


# ------------------------------------------------------------------
# Aggregates
# ------------------------------------------------------------------


def print_aggregates(records: list[Any]) -> None:
    """Render IP aggregates as a Rich table."""
    table = Table(
        title="📊 IPAM Aggregates",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Prefix", style="bold green")
    table.add_column("RIR")
    table.add_column("Tenant")
    table.add_column("Date Added")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.prefix,
            _display_or_dash(r.rir),
            _display_or_dash(r.tenant),
            r.date_added or "—",
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} aggregates[/dim]\n")


# ------------------------------------------------------------------
# Sites
# ------------------------------------------------------------------


def print_sites(records: list[Any]) -> None:
    """Render DCIM sites as a Rich table."""
    table = Table(
        title="🏢 DCIM Sites",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Name", style="bold green")
    table.add_column("Slug", style="dim")
    table.add_column("Status")
    table.add_column("Region")
    table.add_column("Tenant")
    table.add_column("Facility")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.name,
            r.slug,
            _styled_status(r.status),
            _display_or_dash(r.region),
            _display_or_dash(r.tenant),
            r.facility or "—",
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} sites[/dim]\n")


# ------------------------------------------------------------------
# Devices
# ------------------------------------------------------------------


def print_devices(records: list[Any]) -> None:
    """Render DCIM devices as a Rich table."""
    table = Table(
        title="🖧 DCIM Devices",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Name", style="bold green")
    table.add_column("Status")
    table.add_column("Site")
    table.add_column("Role")
    table.add_column("Device Type", max_width=20)
    table.add_column("Tenant")
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.name or "—",
            _styled_status(r.status),
            _display_or_dash(r.site),
            _display_or_dash(r.role),
            _display_or_dash(r.device_type),
            _display_or_dash(r.tenant),
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} devices[/dim]\n")


# ------------------------------------------------------------------
# Tenants
# ------------------------------------------------------------------


def print_tenants(records: list[Any]) -> None:
    """Render tenancy tenants as a Rich table."""
    table = Table(
        title="🏛️ Tenancy Tenants",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Name", style="bold green")
    table.add_column("Slug", style="dim")
    table.add_column("Group")
    table.add_column("Description", max_width=30)
    table.add_column("Tags")

    for r in records:
        table.add_row(
            str(r.id),
            r.name,
            r.slug,
            _display_or_dash(r.group),
            r.description or "—",
            _tags_str(r.tags),
        )

    console.print(table)
    console.print(f"[dim]  {len(records)} tenants[/dim]\n")


# ------------------------------------------------------------------
# RFC 1918 Inventory
# ------------------------------------------------------------------

_RFC1918_CIDR_MAP = {
    "10": "10.0.0.0/8",
    "172": "172.16.0.0/12",
    "192": "192.168.0.0/16",
}


def _rfc1918_block(prefix_str: str) -> str:
    """Return the RFC 1918 supernet block for a given prefix string."""
    first_octet = prefix_str.split(".")[0]
    return _RFC1918_CIDR_MAP.get(first_octet, "—")


def _mapping_status(r: Any) -> str:
    """Derive mapping status from site/tenant assignments.

    - ``mapped``    — has **both** site and tenant
    - ``unmapped``  — has **neither** site nor tenant
    - ``ambiguous`` — has one but not the other (partial documentation)
    """
    has_site = r.resolved_site is not None
    has_tenant = r.tenant is not None
    if has_site and has_tenant:
        return "mapped"
    if not has_site and not has_tenant:
        return "unmapped"
    return "ambiguous"


def _styled_mapping(status: str) -> Text:
    """Return a colour-coded Rich Text for mapping status."""
    styles = {
        "mapped": "bold green",
        "unmapped": "bold red",
        "ambiguous": "bold yellow",
    }
    return Text(status, style=styles.get(status, ""))


def print_rfc1918_inventory(records: list[Any]) -> None:
    """Render RFC 1918 Global VRF prefix inventory as a Rich table."""
    table = Table(
        title="🏠 RFC 1918 Global VRF Prefix Inventory",
        show_lines=True,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("Prefix", style="bold green")
    table.add_column("Block")
    table.add_column("Mapping")
    table.add_column("Status")
    table.add_column("Site")
    table.add_column("Tenant")
    table.add_column("Role")
    table.add_column("Description", max_width=40)

    for r in records:
        table.add_row(
            r.prefix,
            _rfc1918_block(r.prefix),
            _styled_mapping(_mapping_status(r)),
            _styled_status(r.status),
            _display_or_dash(r.resolved_site),
            _display_or_dash(r.tenant),
            _display_or_dash(r.role),
            r.description or "—",
        )

    mapped = sum(1 for r in records if _mapping_status(r) == "mapped")
    unmapped = sum(1 for r in records if _mapping_status(r) == "unmapped")
    ambiguous = len(records) - mapped - unmapped
    total = len(records)
    coverage_pct = (mapped / total * 100) if total > 0 else 0.0
    target_met = coverage_pct >= 90.0
    coverage_style = "green" if target_met else "red"
    target_label = "✅ target met" if target_met else "❌ below 90% target"

    console.print(table)
    console.print(
        f"[dim]  {total} prefixes — "
        f"[green]{mapped} mapped[/green], "
        f"[red]{unmapped} unmapped[/red], "
        f"[yellow]{ambiguous} ambiguous[/yellow]  ·  "
        f"[{coverage_style}]{coverage_pct:.1f}% coverage[/{coverage_style}] "
        f"[dim]({target_label})[/dim][/dim]\n"
    )
