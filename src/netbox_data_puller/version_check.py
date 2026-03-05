"""Version checking utilities for nbpull CLI."""

from __future__ import annotations

import datetime
import json
import logging
import os
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import typer
from packaging.version import parse as parse_version

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)

_PACKAGE_NAME = "nbpull"
_PYPI_URL = f"https://pypi.org/pypi/{_PACKAGE_NAME}/json"
_CHECK_INTERVAL = datetime.timedelta(days=7)
_HTTP_TIMEOUT = 3.0


def get_installed_version() -> str:
    """Return the installed version of nbpull."""
    try:
        return pkg_version(_PACKAGE_NAME)
    except Exception:
        from netbox_data_puller import __version__

        return __version__


def _get_cache_path() -> Path:
    """Return the path to the update check cache file."""
    return Path(typer.get_app_dir(_PACKAGE_NAME)) / "update_check.json"


def _read_cache() -> dict[str, str] | None:
    """Read the cached update check data, or None if missing/corrupt."""
    try:
        cache_path = _get_cache_path()
        if cache_path.exists():
            data: dict[str, str] = json.loads(cache_path.read_text())
            return data
    except Exception:
        pass
    return None


def _write_cache(latest_version: str) -> None:
    """Write the latest version and timestamp to the cache file."""
    try:
        cache_path = _get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now(datetime.UTC)
        cache_path.write_text(
            json.dumps(
                {
                    "last_check": now.isoformat(),
                    "latest_version": latest_version,
                }
            )
        )
    except Exception:
        pass


def _fetch_latest_version() -> str | None:
    """Fetch the latest version string from PyPI. Returns None on any error.

    Intentionally synchronous: this function is called from an atexit handler
    registered by the CLI, where an active asyncio event loop may no longer be
    running, making async I/O non-viable.
    """
    try:
        resp = httpx.get(_PYPI_URL, timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()
        data: dict[str, object] = resp.json()
        info = data.get("info")
        if isinstance(info, dict):
            version = info.get("version")
            if isinstance(version, str):
                return version
    except Exception:
        pass
    return None


def check_for_update() -> str | None:
    """Check if a newer version of nbpull is available on PyPI.

    Returns the latest version string if newer than installed, else None.
    Uses a local cache with a 7-day TTL. Silently returns None on any error.
    """
    try:
        now = datetime.datetime.now(datetime.UTC)
        cached = _read_cache()
        latest: str | None = None

        if cached:
            last_check_str = cached.get("last_check")
            if last_check_str:
                last_check = datetime.datetime.fromisoformat(last_check_str)
                if (now - last_check) < _CHECK_INTERVAL:
                    latest = cached.get("latest_version")

        if latest is None:
            latest = _fetch_latest_version()
            if latest:
                _write_cache(latest)

        if latest is None:
            return None

        current = get_installed_version()
        if parse_version(latest) > parse_version(current):
            return latest
    except Exception:
        pass
    return None


def maybe_warn_upgrade(console: Console) -> None:
    """Print a warning to stderr if a newer version is available.

    Respects the NBPULL_NO_UPDATE_CHECK environment variable.
    Silently does nothing on any error.
    """
    try:
        opt_out = os.environ.get("NBPULL_NO_UPDATE_CHECK", "").lower()
        if opt_out in ("1", "true", "yes"):
            return

        latest = check_for_update()
        if latest:
            current = get_installed_version()
            console.print(
                f"[yellow]⚠ nbpull {latest} is available "
                f"(you have {current}). "
                f"Upgrade: pip install --upgrade nbpull[/yellow]"
            )
    except Exception:
        pass
