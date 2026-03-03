"""🖥️ CLI commands for querying NetBox IPAM data.

All commands are READ-ONLY — no data is ever written to NetBox.
"""

import asyncio
import csv
import datetime
import io
import json
import logging
import re
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from netbox_data_puller.client import NetBoxClient
from netbox_data_puller.config import NetBoxSettings
from netbox_data_puller.formatters import (
    print_aggregates,
    print_batch_summary,
    print_devices,
    print_ip_addresses,
    print_prefixes,
    print_prefixes_status,
    print_rfc1918_inventory,
    print_sites,
    print_tenants,
    print_vlans,
    print_vrfs,
)
from netbox_data_puller.models.aggregate import Aggregate
from netbox_data_puller.models.device import Device
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
from netbox_data_puller.models.site import Site
from netbox_data_puller.models.tenant import Tenant
from netbox_data_puller.models.vlan import VLAN
from netbox_data_puller.models.vrf import VRF

logger = logging.getLogger(__name__)
console = Console(stderr=True)

app = typer.Typer(
    name="nbpull",
    help="🔍 Read-only CLI to pull IPAM data from NetBox.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ------------------------------------------------------------------
# Shared types
# ------------------------------------------------------------------


class OutputFormat(StrEnum):
    """Output format selector."""

    table = "table"
    json = "json"
    csv = "csv"


# Common option type aliases
FormatOpt = Annotated[
    OutputFormat,
    typer.Option("--format", "-f", help="Output format."),
]
StatusOpt = Annotated[
    str | None,
    typer.Option(help="Filter by status (e.g. active, reserved)."),
]
VRFOpt = Annotated[
    str | None,
    typer.Option("--vrf", help="Filter by VRF name."),
]
TenantOpt = Annotated[
    str | None,
    typer.Option("--tenant", help="Filter by tenant name."),
]
SiteOpt = Annotated[
    str | None,
    typer.Option("--site", help="Filter by site name."),
]
TagOpt = Annotated[
    str | None,
    typer.Option("--tag", help="Filter by tag slug."),
]
SearchOpt = Annotated[
    str | None,
    typer.Option("--search", "-s", help="Free-text search."),
]
LimitOpt = Annotated[
    int,
    typer.Option("--limit", "-l", help="Maximum results to return."),
]
VerboseOpt = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable debug logging."),
]
StatusOnlyOpt = Annotated[
    bool,
    typer.Option(
        "--status-only",
        help="Show only prefix and status columns.",
    ),
]
RoleOpt = Annotated[
    str | None,
    typer.Option("--role", help="Filter by role name."),
]
RegionOpt = Annotated[
    str | None,
    typer.Option("--region", help="Filter by region name."),
]
MappingStatusOpt = Annotated[
    str | None,
    typer.Option(
        "--mapping-status",
        help="Filter by mapping status (mapped/unmapped/ambiguous).",
    ),
]
OutputOpt = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        help=(
            "Write JSON/CSV output to this file. "
            "If omitted, you will be prompted for a filename."
        ),
    ),
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_params(**kwargs: Any) -> dict[str, Any]:
    """Build API query params, dropping None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


def _save_json(records: list[Any], output: Path | None, command_name: str) -> None:
    """Serialise records to JSON and write to a file.

    If *output* is ``None``, the user is prompted for a filename with a
    sensible default (``<command>_YYYY-MM-DD.json``).  The written path
    is echoed to stderr on success.
    """
    if output is None:
        today = datetime.date.today().isoformat()
        default_name = f"{command_name}_{today}.json"
        raw = Prompt.ask(
            "[cyan]Output file[/cyan]",
            console=console,
            default=default_name,
        )
        output = Path(raw.strip())

    data = [
        r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in records
    ]
    output.write_text(json.dumps(data, indent=2, default=str))
    console.print(
        f"[bold green]✅ {len(records)} record(s) saved to "
        f"[cyan]{output}[/cyan][/bold green]"
    )


def _flatten_record(record: Any) -> dict[str, Any]:
    """Flatten a Pydantic model to a dict suitable for CSV output.

    Nested objects (NestedRef, ChoiceRef) are reduced to their display
    string so every CSV cell is a plain scalar.
    """
    raw = record.model_dump(mode="json") if hasattr(record, "model_dump") else record
    flat: dict[str, Any] = {}
    for key, val in raw.items():
        if isinstance(val, dict):
            # NestedRef / ChoiceRef — use display or label or value
            flat[key] = (
                val.get("display")
                or val.get("label")
                or val.get("value")
                or val.get("name")
                or ""
            )
        elif isinstance(val, list):
            flat[key] = ", ".join(
                (
                    item.get("display") or item.get("name") or str(item)
                    if isinstance(item, dict)
                    else str(item)
                )
                for item in val
            )
        else:
            flat[key] = val if val is not None else ""
    return flat


def _save_csv(
    rows: list[dict[str, Any]],
    output: Path | None,
    command_name: str,
) -> None:
    """Serialise *rows* (list of flat dicts) to CSV and write to a file.

    If *output* is ``None``, the user is prompted for a filename with a
    sensible default (``<command>_YYYY-MM-DD.csv``).
    """
    if output is None:
        today = datetime.date.today().isoformat()
        default_name = f"{command_name}_{today}.csv"
        raw = Prompt.ask(
            "[cyan]Output file[/cyan]",
            console=console,
            default=default_name,
        )
        output = Path(raw.strip())

    if not rows:
        output.write_text("")
        console.print(
            f"[bold yellow]⚠️  0 records — empty file written to "
            f"[cyan]{output}[/cyan][/bold yellow]"
        )
        return

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    output.write_text(buf.getvalue())
    console.print(
        f"[bold green]✅ {len(rows)} record(s) saved to "
        f"[cyan]{output}[/cyan][/bold green]"
    )


def _get_settings() -> NetBoxSettings:
    """Load settings, with a friendly error on misconfiguration."""
    try:
        return NetBoxSettings()
    except Exception as exc:
        console.print(
            f"[bold red]❌ Configuration error:[/bold red] {exc}\n\n"
            "Make sure NETBOX_URL and NETBOX_TOKEN are set in your "
            ".env file or environment variables.\n"
            "See .env.example for reference.",
        )
        raise typer.Exit(code=2) from exc


def _configure_logging(verbose: bool) -> None:
    """Set up logging level based on verbosity flag."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


async def _fetch(
    endpoint: str,
    params: dict[str, Any],
    *,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """Execute a read-only fetch against NetBox."""
    settings = _get_settings()
    async with NetBoxClient(settings) as client:
        return await client.get(endpoint, params, max_results=max_results)


def _fetch_with_spinner(
    endpoint: str,
    params: dict[str, Any],
    label: str = "Querying NetBox",
    *,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch with a live spinner shown on stderr."""
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(label, total=None)
        return asyncio.run(_fetch(endpoint, params, max_results=max_results))


# ------------------------------------------------------------------
# Setup command
# ------------------------------------------------------------------

_ENV_PATH = Path(".env")
_BATCH_PATH = Path("batch_prefixes.toml")


def _mask_token(token: str) -> str:
    """Mask an API token, showing only the last 4 characters."""
    if len(token) <= 4:
        return "****"
    return "*" * (len(token) - 4) + token[-4:]


def _parse_existing_env(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and blanks."""
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


def _write_env_file(
    path: Path,
    url: str,
    token: str,
) -> None:
    """Write a .env file with the given NetBox settings."""
    content = (
        "# 🔍 NetBox connection settings\n"
        "# Generated by: nbpull setup\n"
        "#\n"
        "# These values are READ from NetBox — no data is ever written.\n"
        "\n"
        f"NETBOX_URL={url}\n"
        f"NETBOX_TOKEN={token}\n"
        "\n"
        "# Optional: Results per API page (default: 100)\n"
        "# NETBOX_PAGE_SIZE=100\n"
        "\n"
        "# Optional: Request timeout in seconds (default: 30)\n"
        "# NETBOX_TIMEOUT=30\n"
        "\n"
        "# Optional: Verify SSL certificates (default: true)\n"
        "# NETBOX_VERIFY_SSL=true\n"
    )
    path.write_text(content)


def _write_batch_toml(
    path: Path,
    prefixes: list[str],
    filters: dict[str, str],
) -> None:
    """Write a batch_prefixes.toml file."""
    lines = ["prefixes = ["]
    for p in prefixes:
        lines.append(f'    "{p}",')
    lines.append("]")
    lines.append("")
    lines.append("[filters]")
    if filters:
        for key, val in filters.items():
            lines.append(f'{key} = "{val}"')
    else:
        lines.append('# status = "active"')
        lines.append('# vrf = "Production"')
        lines.append('# tenant = "Ops"')
    lines.append("")
    path.write_text("\n".join(lines))


async def _run_probe(url: str, token: str) -> list[tuple[str, bool, str]]:
    """Run connection probes against a NetBox instance."""
    settings = NetBoxSettings(url=url, token=token)
    async with NetBoxClient(settings) as client:
        return await client.probe()


@app.command()
def setup(
    verbose: VerboseOpt = False,
) -> None:
    """🛠️ Interactive setup wizard for configuring nbpull.

    Walks you through:
    1. Creating a .env file with your NetBox URL and API token
    2. Testing the connection against the NetBox API
    3. Optionally creating a batch_prefixes.toml file
    """
    _configure_logging(verbose)

    console.print()
    console.print(
        Panel(
            "[bold]Welcome to nbpull setup![/bold]\n\n"
            "This wizard will configure your NetBox connection\n"
            "and verify everything works.\n\n"
            "[dim]🔒 nbpull is read-only — no data will be "
            "written to NetBox.[/dim]",
            title="🛠️  nbpull setup",
            border_style="cyan",
            expand=False,
        ),
    )
    console.print()

    # ----------------------------------------------------------
    # Step 1: Check for existing .env
    # ----------------------------------------------------------
    existing_url = ""
    existing_token = ""

    if _ENV_PATH.exists():
        existing = _parse_existing_env(_ENV_PATH)
        existing_url = existing.get("NETBOX_URL", "")
        existing_token = existing.get("NETBOX_TOKEN", "")

        console.print("[yellow]⚠️  An existing .env file was found.[/yellow]")
        info_lines = []
        if existing_url:
            info_lines.append(f"  [bold]URL:[/bold]   {existing_url}")
        if existing_token:
            info_lines.append(
                f"  [bold]Token:[/bold] {_mask_token(existing_token)}",
            )
        if info_lines:
            console.print("\n".join(info_lines))
        console.print()

        if not Confirm.ask(
            "[bold]Overwrite existing .env?[/bold]",
            console=console,
            default=False,
        ):
            console.print("[dim]Keeping existing .env.[/dim]")
            console.print()
            # Still offer connection test + batch setup with existing config
            url = existing_url
            token = existing_token
        else:
            url = ""
            token = ""
    else:
        url = ""
        token = ""

    # ----------------------------------------------------------
    # Step 2: Collect URL + Token
    # ----------------------------------------------------------
    if not url:
        console.print(
            Panel(
                "[bold]Step 1:[/bold] NetBox Connection",
                border_style="blue",
                expand=False,
            ),
        )
        console.print()

        url = Prompt.ask(
            "[bold cyan]NetBox URL[/bold cyan]",
            console=console,
            default=existing_url if existing_url else "",
        )
        # Normalise: strip trailing slashes, ensure scheme
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

    if not token:
        token = Prompt.ask(
            "[bold cyan]API Token[/bold cyan]",
            console=console,
        )
        token = token.strip()

    if not url or not token:
        console.print("[bold red]❌ URL and Token are required.[/bold red]")
        raise typer.Exit(code=2)

    # Write the .env file
    _write_env_file(_ENV_PATH, url, token)
    console.print()
    console.print(f"[bold green]✅ .env written to[/bold green] {_ENV_PATH.resolve()}")
    console.print(
        "[dim]Tip: You can also set NETBOX_PAGE_SIZE, NETBOX_TIMEOUT, "
        "and NETBOX_VERIFY_SSL as environment variables.[/dim]",
    )
    console.print()

    # ----------------------------------------------------------
    # Step 3: Connection test
    # ----------------------------------------------------------
    console.print(
        Panel(
            "[bold]Step 2:[/bold] Connection Test",
            border_style="blue",
            expand=False,
        ),
    )
    console.print()

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Probing NetBox API", total=None)
        try:
            probe_results = asyncio.run(_run_probe(url, token))
        except Exception as exc:
            console.print(
                f"[bold red]❌ Connection failed:[/bold red] {exc}",
            )
            console.print(
                "\n[dim]Check your URL and token, then run 'nbpull setup' again.[/dim]",
            )
            raise typer.Exit(code=2) from exc

    # Display probe results table
    probe_table = Table(
        title="Connection Probe Results",
        show_header=True,
        header_style="bold",
        expand=False,
    )
    probe_table.add_column("Endpoint", style="cyan")
    probe_table.add_column("Status")
    probe_table.add_column("Detail", style="dim")

    all_ok = True
    for endpoint, ok, detail in probe_results:
        status_text = (
            "[bold green]✅ Pass[/bold green]" if ok else "[bold red]❌ Fail[/bold red]"
        )
        if not ok:
            all_ok = False
        probe_table.add_row(endpoint, status_text, detail)

    console.print(probe_table)
    console.print()

    if all_ok:
        console.print("[bold green]✅ All endpoints reachable![/bold green]")
    else:
        console.print(
            "[bold yellow]⚠️  Some endpoints failed. "
            "Check your token permissions.[/bold yellow]",
        )
    console.print()

    # ----------------------------------------------------------
    # Step 4: Batch prefixes TOML
    # ----------------------------------------------------------
    console.print(
        Panel(
            "[bold]Step 3:[/bold] Batch Prefixes File",
            border_style="blue",
            expand=False,
        ),
    )
    console.print()

    if _BATCH_PATH.exists():
        console.print(
            f"[dim]{_BATCH_PATH} already exists — skipping.[/dim]",
        )
    elif Confirm.ask(
        "[bold]Create a batch_prefixes.toml file?[/bold]",
        console=console,
        default=True,
    ):
        console.print()
        console.print(
            "[dim]How would you like to enter your prefixes?[/dim]\n"
            "  [cyan]1[/cyan] — Type or paste a comma-separated list\n"
            "  [cyan]2[/cyan] — Load from an existing file (comma-separated CIDRs)\n"
            "  [cyan]3[/cyan] — Enter one per line interactively",
        )
        console.print()
        input_mode = Prompt.ask(
            "[cyan]Choice[/cyan]",
            console=console,
            choices=["1", "2", "3"],
            default="1",
        )

        cidr_re = re.compile(
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$",
        )

        def _validate_and_warn(prefixes: list[str]) -> list[str]:
            """Warn on non-CIDR entries but keep them."""
            result: list[str] = []
            for p in prefixes:
                p = p.strip()
                if not p:
                    continue
                if not cidr_re.match(p):
                    console.print(
                        f"[yellow]⚠️  '{p}' doesn't look like a valid "
                        "CIDR — added anyway.[/yellow]",
                    )
                result.append(p)
            return result

        prefix_list: list[str] = []

        if input_mode == "1":
            # Comma-separated inline input
            console.print(
                "[dim]Enter prefixes separated by commas "
                "(e.g. 10.0.0.0/8, 172.16.0.0/12).[/dim]",
            )
            console.print()
            raw_input = Prompt.ask(
                "[cyan]Prefixes[/cyan]",
                console=console,
            )
            prefix_list = _validate_and_warn(raw_input.split(","))

        elif input_mode == "2":
            # Load from file
            console.print(
                "[dim]Enter the path to a text file containing "
                "comma-separated CIDRs.[/dim]",
            )
            console.print()
            file_path_str = Prompt.ask(
                "[cyan]File path[/cyan]",
                console=console,
            )
            file_path = Path(file_path_str.strip())
            if not file_path.exists():
                console.print(
                    f"[bold red]❌ File not found:[/bold red] {file_path}",
                )
            else:
                file_contents = file_path.read_text()
                # Support comma-separated on one or multiple lines
                raw_prefixes = [
                    p for line in file_contents.splitlines() for p in line.split(",")
                ]
                prefix_list = _validate_and_warn(raw_prefixes)
                console.print(
                    f"[dim]Loaded {len(prefix_list)} prefix(es) from "
                    f"[cyan]{file_path}[/cyan].[/dim]",
                )

        else:
            # One per line (original behaviour)
            console.print(
                "[dim]Enter prefixes one per line (CIDR notation, "
                "e.g. 10.0.0.0/8).\n"
                "Press Enter on an empty line when done.[/dim]",
            )
            console.print()
            while True:
                value = Prompt.ask(
                    f"[cyan]Prefix {len(prefix_list) + 1}[/cyan]",
                    console=console,
                    default="",
                )
                value = value.strip()
                if not value:
                    break
                prefix_list.extend(_validate_and_warn([value]))

        if not prefix_list:
            console.print("[dim]No prefixes entered — skipping.[/dim]")
        else:
            # Ask about global filters
            batch_filters: dict[str, str] = {}
            console.print()
            if Confirm.ask(
                "[bold]Add global filters?[/bold] (status, vrf, tenant)",
                console=console,
                default=False,
            ):
                status_filter = Prompt.ask(
                    "[cyan]Status filter[/cyan] "
                    "[dim](active/reserved/deprecated/container, "
                    "blank to skip)[/dim]",
                    console=console,
                    default="",
                )
                if status_filter.strip():
                    batch_filters["status"] = status_filter.strip()

                vrf_filter = Prompt.ask(
                    "[cyan]VRF filter[/cyan] [dim](blank to skip)[/dim]",
                    console=console,
                    default="",
                )
                if vrf_filter.strip():
                    batch_filters["vrf"] = vrf_filter.strip()

                tenant_filter = Prompt.ask(
                    "[cyan]Tenant filter[/cyan] [dim](blank to skip)[/dim]",
                    console=console,
                    default="",
                )
                if tenant_filter.strip():
                    batch_filters["tenant"] = tenant_filter.strip()

            _write_batch_toml(_BATCH_PATH, prefix_list, batch_filters)
            console.print()
            console.print(
                f"[bold green]✅ {_BATCH_PATH} created with "
                f"{len(prefix_list)} prefix(es).[/bold green]",
            )
    else:
        console.print("[dim]Skipping batch file creation.[/dim]")

    # ----------------------------------------------------------
    # Done!
    # ----------------------------------------------------------
    console.print()
    console.print(
        Panel(
            "[bold green]Setup complete![/bold green]\n\n"
            "Try these commands:\n"
            "  [cyan]nbpull prefixes[/cyan]           — list prefixes\n"
            "  [cyan]nbpull ip-addresses[/cyan]       — list IPs\n"
            "  [cyan]nbpull vlans[/cyan]              — list VLANs\n"
            "  [cyan]nbpull vrfs[/cyan]               — list VRFs\n"
            "  [cyan]nbpull aggregates[/cyan]         — list IP aggregates\n"
            "  [cyan]nbpull sites[/cyan]              — list DCIM sites\n"
            "  [cyan]nbpull devices[/cyan]            — list DCIM devices\n"
            "  [cyan]nbpull tenants[/cyan]            — list tenants\n"
            "  [cyan]nbpull rfc1918[/cyan]            — RFC 1918 inventory\n"
            "  [cyan]nbpull batch-prefixes[/cyan]     — batch query",
            title="🎉 Done",
            border_style="green",
            expand=False,
        ),
    )


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------


@app.command()
def prefixes(
    status: StatusOpt = None,
    vrf: VRFOpt = None,
    tenant: TenantOpt = None,
    site: SiteOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    status_only: StatusOnlyOpt = False,
    verbose: VerboseOpt = False,
) -> None:
    """📡 List IPAM prefixes from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        status=status,
        vrf=vrf,
        tenant=tenant,
        site=site,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "ipam/prefixes/",
        params,
        "Fetching prefixes",
        max_results=limit,
    )
    records = [Prefix.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "prefixes")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "prefixes")
    elif status_only:
        print_prefixes_status(records)
    else:
        print_prefixes(records)


@app.command(name="ip-addresses")
def ip_addresses(
    status: StatusOpt = None,
    vrf: VRFOpt = None,
    tenant: TenantOpt = None,
    site: SiteOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    prefix: Annotated[
        str | None,
        typer.Option(
            "--prefix",
            help="Filter by parent prefix (e.g. 10.0.0.0/24).",
        ),
    ] = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🖥️ List IPAM IP addresses from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        status=status,
        vrf=vrf,
        tenant=tenant,
        site=site,
        tag=tag,
        q=search,
        parent=prefix,
    )
    raw = _fetch_with_spinner(
        "ipam/ip-addresses/",
        params,
        "Fetching IP addresses",
        max_results=limit,
    )
    records = [IPAddress.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "ip-addresses")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "ip-addresses")
    else:
        print_ip_addresses(records)


@app.command()
def vlans(
    status: StatusOpt = None,
    tenant: TenantOpt = None,
    site: SiteOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🏷️ List IPAM VLANs from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        status=status,
        tenant=tenant,
        site=site,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "ipam/vlans/",
        params,
        "Fetching VLANs",
        max_results=limit,
    )
    records = [VLAN.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "vlans")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "vlans")
    else:
        print_vlans(records)


@app.command()
def vrfs(
    tenant: TenantOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🔀 List IPAM VRFs from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        tenant=tenant,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "ipam/vrfs/",
        params,
        "Fetching VRFs",
        max_results=limit,
    )
    records = [VRF.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "vrfs")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "vrfs")
    else:
        print_vrfs(records)


@app.command()
def aggregates(
    rir: Annotated[
        str | None,
        typer.Option("--rir", help="Filter by RIR name (e.g. ARIN, RIPE, RFC1918)."),
    ] = None,
    tenant: TenantOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """📊 List IPAM aggregates (top-level IP space) from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        rir=rir,
        tenant=tenant,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "ipam/aggregates/",
        params,
        "Fetching aggregates",
        max_results=limit,
    )
    records = [Aggregate.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "aggregates")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "aggregates")
    else:
        print_aggregates(records)


@app.command()
def sites(
    status: StatusOpt = None,
    tenant: TenantOpt = None,
    region: RegionOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🏢 List DCIM sites from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        status=status,
        tenant=tenant,
        region=region,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "dcim/sites/",
        params,
        "Fetching sites",
        max_results=limit,
    )
    records = [Site.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "sites")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "sites")
    else:
        print_sites(records)


@app.command()
def devices(
    status: StatusOpt = None,
    site: SiteOpt = None,
    tenant: TenantOpt = None,
    role: RoleOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🖧  List DCIM devices from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        status=status,
        site=site,
        tenant=tenant,
        role=role,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "dcim/devices/",
        params,
        "Fetching devices",
        max_results=limit,
    )
    records = [Device.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "devices")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "devices")
    else:
        print_devices(records)


@app.command()
def tenants(
    group: Annotated[
        str | None,
        typer.Option("--group", help="Filter by tenant group name."),
    ] = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🏛️ List tenancy tenants from NetBox."""
    _configure_logging(verbose)
    params = _build_params(
        group=group,
        tag=tag,
        q=search,
    )
    raw = _fetch_with_spinner(
        "tenancy/tenants/",
        params,
        "Fetching tenants",
        max_results=limit,
    )
    records = [Tenant.model_validate(r) for r in raw]

    if fmt == OutputFormat.json:
        _save_json(records, output, "tenants")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "tenants")
    else:
        print_tenants(records)


# ------------------------------------------------------------------
# RFC 1918 Inventory
# ------------------------------------------------------------------

_RFC1918_BLOCKS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]


async def _fetch_rfc1918_blocks(
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch Global VRF prefixes within RFC 1918 space.

    Issues three requests — one per canonical RFC 1918 supernet — using
    ``within_include`` to capture all sub-prefixes.  Results are filtered
    to the **Global VRF** (``vrf == null``) in Python, because NetBox does
    not support a ``vrf_id=null`` query parameter across all versions.
    Deduplicates by prefix ID.
    """
    settings = _get_settings()
    seen: set[int] = set()
    results: list[dict[str, Any]] = []
    async with NetBoxClient(settings) as client:
        for block in _RFC1918_BLOCKS:
            raw = await client.get(
                "ipam/prefixes/",
                {"within_include": block},
                max_results=max_results,
            )
            for r in raw:
                # Keep only Global VRF (no VRF assignment)
                if r.get("vrf") is not None:
                    continue
                if r["id"] not in seen:
                    seen.add(r["id"])
                    results.append(r)
    return results


async def _fetch_sites_by_ids(site_ids: list[int]) -> dict[int, Site]:
    """Batch-fetch full Site objects for a list of IDs.

    Returns a mapping of site_id → Site.  Used to enrich location-report
    rows with region and facility data that is not available on the prefix
    NestedRef alone.
    """
    if not site_ids:
        return {}
    settings = _get_settings()
    async with NetBoxClient(settings) as client:
        raw = await client.get(
            "dcim/sites/",
            {"id": site_ids},
            max_results=len(site_ids) + 10,
        )
    return {r["id"]: Site.model_validate(r) for r in raw}


def _rfc1918_mapping_status(prefix: Prefix) -> str:
    """Derive mapping status from site/tenant assignments.

    - ``mapped``    — has **both** site and tenant
    - ``unmapped``  — has **neither** site nor tenant
    - ``ambiguous`` — has one but not the other
    """
    has_site = prefix.resolved_site is not None
    has_tenant = prefix.tenant is not None
    if has_site and has_tenant:
        return "mapped"
    if not has_site and not has_tenant:
        return "unmapped"
    return "ambiguous"


@app.command()
def rfc1918(
    mapping_status: MappingStatusOpt = None,
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            help=(
                "Filter by prefix status "
                "(active, reserved, deprecated, container). "
                "Use 'active' to exclude decommissioned prefixes."
            ),
        ),
    ] = None,
    exclude_role: Annotated[
        str | None,
        typer.Option(
            "--exclude-role",
            "-R",
            help=(
                "Exclude prefixes whose role matches this name "
                "(e.g. 'kubernetes', 'docker'). Case-insensitive."
            ),
        ),
    ] = None,
    limit: LimitOpt = 500,
    fmt: FormatOpt = OutputFormat.table,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """🏠 RFC 1918 Global VRF prefix inventory with mapping status.

    Queries all three RFC 1918 blocks (10/8, 172.16/12, 192.168/16)
    from the Global VRF (no VRF) and labels each prefix:

    \b
      mapped    — has both site and tenant
      unmapped  — has neither site nor tenant
      ambiguous — has one but not the other

    Use --mapping-status to filter by a specific label.
    Use --status active to exclude decommissioned/deprecated prefixes.
    Use --exclude-role to drop stub/infrastructure networks (e.g. kubernetes).
    """
    _configure_logging(verbose)

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Fetching RFC 1918 prefixes…", total=None)
        raw = asyncio.run(_fetch_rfc1918_blocks(max_results=limit))

    records = [Prefix.model_validate(r) for r in raw]

    if status:
        records = [r for r in records if r.status and r.status.value == status]

    if mapping_status:
        records = [r for r in records if _rfc1918_mapping_status(r) == mapping_status]

    if exclude_role:
        exclude_lower = exclude_role.lower()
        records = [
            r
            for r in records
            if not (r.role and r.role.display.lower() == exclude_lower)
        ]

    if fmt == OutputFormat.json:
        _save_json(records, output, "rfc1918")
    elif fmt == OutputFormat.csv:
        _save_csv([_flatten_record(r) for r in records], output, "rfc1918")
    else:
        print_rfc1918_inventory(records)


# ------------------------------------------------------------------
# Location report (Phase 2 scaffold — SMO export)
# ------------------------------------------------------------------


def _prefix_to_location_row(prefix: Any, sites: dict[int, Site]) -> dict[str, Any]:
    """Flatten a mapped Prefix to the location-report CSV row shape.

    Includes both **PRD columns** (ip_range, building, province_state, city)
    and **general columns** (prefix, site, region, facility, tenant,
    description, status) so the output serves both the CMDB/SMO use-case
    and general-purpose consumers.

    ``sites`` is a mapping of site_id → Site fetched from dcim/sites/,
    used to populate region and facility which are not available on the
    resolved_site NestedRef returned with each prefix.
    """
    site_ref = prefix.resolved_site
    site_obj = sites.get(site_ref.id) if site_ref else None
    site_name = site_ref.display if site_ref else ""
    region_name = site_obj.region.display if site_obj and site_obj.region else ""
    status_val = prefix.status.value if prefix.status else ""
    return {
        # PRD columns (Province/State, City, Building, IP Range)
        "ip_range": prefix.prefix,
        "building": site_name,
        "province_state": region_name,
        "city": "",
        # General columns
        "prefix": prefix.prefix,
        "site": site_name,
        "region": region_name,
        "facility": site_obj.facility if site_obj else "",
        "tenant": prefix.tenant.display if prefix.tenant else "",
        "description": prefix.description or "",
        "status": status_val,
    }


@app.command(name="location-report")
def location_report(
    exclude_role: Annotated[
        str | None,
        typer.Option(
            "--exclude-role",
            "-R",
            help=(
                "Exclude prefixes whose role matches this name "
                "(e.g. 'kubernetes'). Case-insensitive."
            ),
        ),
    ] = None,
    limit: LimitOpt = 1000,
    fmt: FormatOpt = OutputFormat.csv,
    output: OutputOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    """📋 Location-to-IP report for CMDB discovery scanning.

    Extracts all **mapped** RFC 1918 Global VRF prefixes (those with a
    site assignment) and outputs them in a flat CSV suitable for
    ServiceNow CMDB discovery or general network documentation.

    \b
    PRD columns (for CMDB/SMO):
      ip_range        — CIDR notation (same as prefix)
      building        — site name (same as site)
      province_state  — region name (best available — depends on NetBox
                        region hierarchy configuration)
      city            — empty (reserved for future region hierarchy support)

    \b
    General columns:
      prefix, site, region, facility, tenant, description, status

    Default output format is CSV (--format csv).  Use --format json for
    machine-readable JSON.  Use --output / -o to specify the output file
    directly (skips the interactive prompt).

    \b
    Example:
      nbpull location-report                        # CSV, prompted filename
      nbpull location-report --output smo.csv       # CSV, direct path
      nbpull location-report --exclude-role kubernetes
    """
    _configure_logging(verbose)

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Fetching RFC 1918 prefixes…", total=None)
        raw = asyncio.run(_fetch_rfc1918_blocks(max_results=limit))

    records = [Prefix.model_validate(r) for r in raw]

    # Only mapped prefixes (resolved_site assigned) — unmapped excluded per PRD
    records = [r for r in records if r.resolved_site is not None]

    if exclude_role:
        exclude_lower = exclude_role.lower()
        records = [
            r
            for r in records
            if not (r.role and r.role.display.lower() == exclude_lower)
        ]

    # Enrich with full site details (region, facility)
    unique_site_ids = list({r.resolved_site.id for r in records if r.resolved_site})
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Enriching {len(unique_site_ids)} site(s)…", total=None)
        sites_by_id = asyncio.run(_fetch_sites_by_ids(unique_site_ids))

    if fmt == OutputFormat.json:
        _save_json(records, output, "location-report")
    else:
        rows = [_prefix_to_location_row(r, sites_by_id) for r in records]
        _save_csv(rows, output, "location-report")

    console.print(f"[dim]  {len(records)} mapped prefix(es) exported.[/dim]")


_DEFAULT_BATCH_FILE = "batch_prefixes.toml"


def _load_batch_toml(path: Path) -> dict[str, Any]:
    """Load and validate a batch-prefixes TOML file."""
    if not path.exists():
        console.print(
            f"[bold red]❌ File not found:[/bold red] {path}\n\n"
            f"Create a [bold]{_DEFAULT_BATCH_FILE}[/bold] or pass "
            "--file /path/to/file.toml",
        )
        raise typer.Exit(code=1)

    import tomllib

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    if "prefixes" not in data or not data["prefixes"]:
        console.print(
            "[bold red]❌ TOML file must contain a non-empty "
            "'prefixes' list.[/bold red]",
        )
        raise typer.Exit(code=1)

    return data


@app.command(name="batch-prefixes")
def batch_prefixes(
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            help=(
                f"Path to TOML file with prefix list (default: {_DEFAULT_BATCH_FILE})."
            ),
        ),
    ] = Path(_DEFAULT_BATCH_FILE),
    fmt: FormatOpt = OutputFormat.table,
    status_only: StatusOnlyOpt = False,
    verbose: VerboseOpt = False,
    output: OutputOpt = None,
) -> None:
    """📦 Query NetBox for multiple prefixes defined in a TOML file.

    Reads a list of CIDR prefixes and optional global filters from
    a TOML file, then queries NetBox for each one.

    Example TOML:

        prefixes = ["10.32.16.0/20", "172.16.0.0/12"]

        [filters]

        status = "active"
    """
    _configure_logging(verbose)
    data = _load_batch_toml(file)

    prefix_list: list[str] = data["prefixes"]
    global_filters: dict[str, Any] = data.get("filters", {})

    # Header panel
    header_lines = [
        f"[bold]Source:[/bold]  [cyan]{file}[/cyan]",
        f"[bold]Prefixes:[/bold] {len(prefix_list)}",
    ]
    if global_filters:
        header_lines.append(
            f"[bold]Filters:[/bold] [dim]{global_filters}[/dim]",
        )
    console.print()
    console.print(
        Panel(
            "\n".join(header_lines),
            title="📦 Batch Prefix Query",
            border_style="cyan",
            expand=False,
        ),
    )
    console.print()

    # Fetch all prefixes with a progress bar
    batch_results: list[tuple[str, list[Prefix]]] = []
    not_found: list[str] = []

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            "Querying NetBox",
            total=len(prefix_list),
        )
        for cidr in prefix_list:
            progress.update(task, description=f"Querying [green]{cidr}[/green]")
            params = _build_params(q=cidr, **global_filters)
            raw = asyncio.run(_fetch("ipam/prefixes/", params))
            records = [Prefix.model_validate(r) for r in raw]
            if records:
                batch_results.append((cidr, records))
            else:
                not_found.append(cidr)
            progress.advance(task)

    # Render results
    if fmt == OutputFormat.json:
        all_records = [r for _, records in batch_results for r in records]
        _save_json(all_records, output, "batch-prefixes")
    elif fmt == OutputFormat.csv:
        all_records = [r for _, records in batch_results for r in records]
        _save_csv([_flatten_record(r) for r in all_records], output, "batch-prefixes")
    elif status_only:
        print_batch_summary(batch_results, not_found)
    else:
        for cidr, records in batch_results:
            console.print(
                f"\n[bold cyan]── {cidr} ──[/bold cyan]",
                highlight=False,
            )
            print_prefixes(records)
        for cidr in not_found:
            console.print(
                f"\n[bold cyan]── {cidr} ──[/bold cyan]",
                highlight=False,
            )
            console.print("[yellow]  ⚠️  No results found.[/yellow]")

    # Final summary line
    done = Text()
    done.append("\n✅ ", style="bold green")
    done.append(f"{len(batch_results)}", style="bold")
    done.append(" found")
    if not_found:
        done.append("  ·  ", style="dim")
        done.append(f"⚠️  {len(not_found)}", style="bold yellow")
        done.append(" not found")
    console.print(done)


if __name__ == "__main__":
    app()
