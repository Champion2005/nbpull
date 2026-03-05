"""Tests for version_check module."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from netbox_data_puller.version_check import (
    check_for_update,
    get_installed_version,
    maybe_warn_upgrade,
)


class TestGetInstalledVersion:
    @patch("netbox_data_puller.version_check.pkg_version")
    def test_returns_metadata_version(self, mock_pkg: MagicMock) -> None:
        mock_pkg.return_value = "1.2.3"
        assert get_installed_version() == "1.2.3"


class TestCheckForUpdate:
    @patch(
        "netbox_data_puller.version_check.get_installed_version",
        return_value="1.0.0",
    )
    @patch("netbox_data_puller.version_check._fetch_latest_version")
    @patch("netbox_data_puller.version_check._read_cache", return_value=None)
    @patch("netbox_data_puller.version_check._write_cache")
    def test_outdated_returns_latest(
        self,
        mock_write: MagicMock,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
        mock_ver: MagicMock,
    ) -> None:
        mock_fetch.return_value = "2.0.0"
        result = check_for_update()
        assert result == "2.0.0"
        mock_write.assert_called_once_with("2.0.0")

    @patch(
        "netbox_data_puller.version_check.get_installed_version",
        return_value="1.0.0",
    )
    @patch("netbox_data_puller.version_check._fetch_latest_version")
    @patch("netbox_data_puller.version_check._read_cache", return_value=None)
    @patch("netbox_data_puller.version_check._write_cache")
    def test_up_to_date_returns_none(
        self,
        mock_write: MagicMock,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
        mock_ver: MagicMock,
    ) -> None:
        mock_fetch.return_value = "1.0.0"
        result = check_for_update()
        assert result is None

    @patch(
        "netbox_data_puller.version_check.get_installed_version",
        return_value="1.0.0",
    )
    @patch("netbox_data_puller.version_check._fetch_latest_version")
    @patch("netbox_data_puller.version_check._read_cache")
    def test_cache_hit_skips_fetch(
        self,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
        mock_ver: MagicMock,
    ) -> None:
        now = datetime.datetime.now(datetime.UTC)
        mock_cache.return_value = {
            "last_check": now.isoformat(),
            "latest_version": "2.0.0",
        }
        result = check_for_update()
        assert result == "2.0.0"
        mock_fetch.assert_not_called()

    @patch(
        "netbox_data_puller.version_check.get_installed_version",
        return_value="1.0.0",
    )
    @patch("netbox_data_puller.version_check._fetch_latest_version")
    @patch("netbox_data_puller.version_check._read_cache")
    @patch("netbox_data_puller.version_check._write_cache")
    def test_cache_expired_fetches(
        self,
        mock_write: MagicMock,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
        mock_ver: MagicMock,
    ) -> None:
        old = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)
        mock_cache.return_value = {
            "last_check": old.isoformat(),
            "latest_version": "1.5.0",
        }
        mock_fetch.return_value = "2.0.0"
        result = check_for_update()
        assert result == "2.0.0"
        mock_fetch.assert_called_once()

    @patch("netbox_data_puller.version_check._fetch_latest_version")
    @patch("netbox_data_puller.version_check._read_cache", return_value=None)
    def test_network_error_returns_none(
        self,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        mock_fetch.return_value = None
        result = check_for_update()
        assert result is None


class TestMaybeWarnUpgrade:
    @patch("netbox_data_puller.version_check.check_for_update", return_value="2.0.0")
    @patch(
        "netbox_data_puller.version_check.get_installed_version",
        return_value="1.0.0",
    )
    def test_shows_warning_when_outdated(
        self, mock_ver: MagicMock, mock_check: MagicMock
    ) -> None:
        console = Console(stderr=True, force_terminal=True, highlight=False)
        with console.capture() as capture:
            maybe_warn_upgrade(console)
        output = capture.get()
        assert "2.0.0" in output
        assert "available" in output

    @patch("netbox_data_puller.version_check.check_for_update", return_value=None)
    def test_no_warning_when_current(self, mock_check: MagicMock) -> None:
        console = Console(stderr=True, force_terminal=True)
        with console.capture() as capture:
            maybe_warn_upgrade(console)
        output = capture.get()
        assert output.strip() == ""

    @patch("netbox_data_puller.version_check.check_for_update", return_value="2.0.0")
    def test_opt_out_disables_check(
        self, mock_check: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NBPULL_NO_UPDATE_CHECK", "1")
        console = Console(stderr=True, force_terminal=True)
        with console.capture() as capture:
            maybe_warn_upgrade(console)
        output = capture.get()
        assert output.strip() == ""
        mock_check.assert_not_called()
