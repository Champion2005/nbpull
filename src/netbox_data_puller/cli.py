"""🖥️ CLI commands for querying NetBox IPAM data.

All commands are READ-ONLY — no data is ever written to NetBox.
"""

import asyncio
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
        lines.append("# status = \"active\"")
        lines.append("# vrf = \"Production\"")
        lines.append("# tenant = \"Ops\"")
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
    """🛠️  Interactive setup wizard for configuring nbpull.

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
                "\n[dim]Check your URL and token, then run "
                "'nbpull setup' again.[/dim]",
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
            "[bold green]✅ Pass[/bold green]"
            if ok
            else "[bold red]❌ Fail[/bold red]"
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
            "[dim]Enter prefixes one per line (CIDR notation, "
            "e.g. 10.0.0.0/8).\n"
            "Press Enter on an empty line when done.[/dim]",
        )
        console.print()

        prefix_list: list[str] = []
        cidr_re = re.compile(
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$",
        )
        while True:
            value = Prompt.ask(
                f"[cyan]Prefix {len(prefix_list) + 1}[/cyan]",
                console=console,
                default="",
            )
            value = value.strip()
            if not value:
                break
            if not cidr_re.match(value):
                console.print(
                    f"[yellow]⚠️  '{value}' doesn't look like a valid "
                    "CIDR — added anyway.[/yellow]",
                )
            prefix_list.append(value)

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
