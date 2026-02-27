"""🖥️ CLI commands for querying NetBox IPAM data.

All commands are READ-ONLY — no data is ever written to NetBox.
"""

import asyncio
import logging
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
from rich.text import Text

from netbox_data_puller.client import NetBoxClient
from netbox_data_puller.config import NetBoxSettings
from netbox_data_puller.formatters import (
    print_batch_summary,
    print_ip_addresses,
    print_json,
    print_prefixes,
    print_prefixes_status,
    print_vlans,
    print_vrfs,
)
from netbox_data_puller.models.ip_address import IPAddress
from netbox_data_puller.models.prefix import Prefix
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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_params(**kwargs: Any) -> dict[str, Any]:
    """Build API query params, dropping None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


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
        print_json(records)
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
    verbose: VerboseOpt = False,
) -> None:
    """🖥️  List IPAM IP addresses from NetBox."""
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
        print_json(records)
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
    verbose: VerboseOpt = False,
) -> None:
    """🏷️  List IPAM VLANs from NetBox."""
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
        print_json(records)
    else:
        print_vlans(records)


@app.command()
def vrfs(
    tenant: TenantOpt = None,
    tag: TagOpt = None,
    search: SearchOpt = None,
    limit: LimitOpt = 50,
    fmt: FormatOpt = OutputFormat.table,
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
        print_json(records)
    else:
        print_vrfs(records)


# ------------------------------------------------------------------
# Batch commands
# ------------------------------------------------------------------

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
        for cidr, records in batch_results:
            console.print(
                f"\n[bold cyan]── {cidr} ──[/bold cyan]",
                highlight=False,
            )
            print_json(records)
        for cidr in not_found:
            console.print(
                f"\n[bold cyan]── {cidr} ──[/bold cyan]",
                highlight=False,
            )
            console.print("[yellow]  ⚠️  No results found.[/yellow]")
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
