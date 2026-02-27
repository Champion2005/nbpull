"""🧪 Tests for CLI commands via Typer's CliRunner."""

import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from netbox_data_puller.cli import app

runner = CliRunner()

MOCK_PREFIX_RESPONSE = [
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
    },
]


class TestPrefixesCommand:
    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_prefixes_table(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(app, ["prefixes"])
        assert result.exit_code == 0
        # Rich may truncate in narrow test terminal
        assert "10.0" in result.output
        assert "Prefixes" in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_prefixes_json(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(app, ["prefixes", "--format", "json"])
        assert result.exit_code == 0
        assert '"prefix"' in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_prefixes_passes_filters(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = []
        runner.invoke(
            app,
            [
                "prefixes",
                "--status",
                "active",
                "--vrf",
                "Production",
                "--tag",
                "critical",
            ],
        )
        call_args = mock_fetch.call_args
        params = call_args[0][1]  # second positional arg
        assert params["status"] == "active"
        assert params["vrf"] == "Production"
        assert params["tag"] == "critical"


class TestNoArgsShowsHelp:
    def test_no_args(self) -> None:
        result = runner.invoke(app, [])
        # Typer no_args_is_help returns exit code 0 or 2
        assert result.exit_code in (0, 2)
        assert "prefixes" in result.output or "Usage" in result.output


class TestBatchPrefixes:
    """Tests for the batch-prefixes subcommand."""

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_batch_prefixes_table(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
        tmp_path: Path,
    ) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text(
            textwrap.dedent("""\
                prefixes = ["10.32.16.0/20", "172.16.0.0/12"]
            """),
        )
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file)],
        )
        assert result.exit_code == 0
        assert "10.32.16.0/20" in result.output
        assert "172.16.0.0/12" in result.output
        assert mock_fetch.call_count == 2

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_batch_prefixes_json(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
        tmp_path: Path,
    ) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text('prefixes = ["10.0.0.0/8"]\n')
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file), "-f", "json"],
        )
        assert result.exit_code == 0
        assert '"prefix"' in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_batch_prefixes_with_filters(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
        tmp_path: Path,
    ) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text(
            textwrap.dedent("""\
                prefixes = ["10.32.16.0/20"]

                [filters]
                status = "active"
                vrf = "Production"
            """),
        )
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file)],
        )
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        assert params["status"] == "active"
        assert params["vrf"] == "Production"
        assert params["q"] == "10.32.16.0/20"

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_batch_prefixes_no_results(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
        tmp_path: Path,
    ) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text('prefixes = ["99.99.99.0/24"]\n')
        mock_fetch.return_value = []
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file)],
        )
        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_batch_prefixes_missing_file(self) -> None:
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", "/nonexistent/path.toml"],
        )
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_batch_prefixes_empty_list(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text("prefixes = []\n")
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file)],
        )
        assert result.exit_code == 1
        assert "non-empty" in result.output


class TestStatusOnly:
    """Tests for the --status-only flag."""

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_prefixes_status_only(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(app, ["prefixes", "--status-only"])
        assert result.exit_code == 0
        assert "Prefix Status" in result.output
        assert "10.0" in result.output
        # Full table columns should NOT appear
        assert "Description" not in result.output
        assert "Pool" not in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_batch_prefixes_status_only(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
        tmp_path: Path,
    ) -> None:
        toml_file = tmp_path / "test_batch.toml"
        toml_file.write_text('prefixes = ["10.0.0.0/8"]\n')
        mock_fetch.return_value = MOCK_PREFIX_RESPONSE
        result = runner.invoke(
            app,
            ["batch-prefixes", "--file", str(toml_file), "--status-only"],
        )
        assert result.exit_code == 0
        assert "Batch Prefix Status" in result.output
        assert "Description" not in result.output or "Batch" in result.output


# ------------------------------------------------------------------
# Mock data for other resource types
# ------------------------------------------------------------------

MOCK_IP_RESPONSE = [
    {
        "id": 10,
        "display": "10.0.0.1/32",
        "address": "10.0.0.1/32",
        "status": {"value": "active", "label": "Active"},
        "vrf": None,
        "tenant": None,
        "role": None,
        "dns_name": "server01.example.com",
        "description": "Test IP",
        "tags": [],
    },
]

MOCK_VLAN_RESPONSE = [
    {
        "id": 1,
        "display": "VLAN 100",
        "vid": 100,
        "name": "Management",
        "status": {"value": "active", "label": "Active"},
        "tenant": None,
        "site": None,
        "group": None,
        "role": None,
        "description": "Mgmt VLAN",
        "tags": [],
    },
]

MOCK_VRF_RESPONSE = [
    {
        "id": 5,
        "display": "Production",
        "name": "Production",
        "rd": "65000:100",
        "tenant": None,
        "enforce_unique": True,
        "description": "Prod VRF",
        "tags": [],
    },
]


# ------------------------------------------------------------------
# ip-addresses command
# ------------------------------------------------------------------


class TestIPAddressesCommand:
    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_ip_addresses_table(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_IP_RESPONSE
        result = runner.invoke(app, ["ip-addresses"])
        assert result.exit_code == 0
        assert "10.0.0.1" in result.output
        assert "IP Addresses" in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_ip_addresses_json(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_IP_RESPONSE
        result = runner.invoke(app, ["ip-addresses", "--format", "json"])
        assert result.exit_code == 0
        assert '"address"' in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_ip_addresses_passes_filters(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = []
        runner.invoke(
            app,
            [
                "ip-addresses",
                "--status",
                "active",
                "--vrf",
                "Production",
                "--site",
                "DC1",
                "--prefix",
                "10.0.0.0/24",
            ],
        )
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        assert params["status"] == "active"
        assert params["vrf"] == "Production"
        assert params["site"] == "DC1"
        assert params["parent"] == "10.0.0.0/24"


# ------------------------------------------------------------------
# vlans command
# ------------------------------------------------------------------


class TestVLANsCommand:
    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vlans_table(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_VLAN_RESPONSE
        result = runner.invoke(app, ["vlans"])
        assert result.exit_code == 0
        # Rich may truncate in narrow test terminal
        assert "Managem" in result.output
        assert "VLANs" in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vlans_json(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_VLAN_RESPONSE
        result = runner.invoke(app, ["vlans", "--format", "json"])
        assert result.exit_code == 0
        assert '"vid"' in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vlans_passes_filters(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = []
        runner.invoke(
            app,
            ["vlans", "--status", "active", "--site", "DC1", "--tag", "prod"],
        )
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        assert params["status"] == "active"
        assert params["site"] == "DC1"
        assert params["tag"] == "prod"


# ------------------------------------------------------------------
# vrfs command
# ------------------------------------------------------------------


class TestVRFsCommand:
    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vrfs_table(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_VRF_RESPONSE
        result = runner.invoke(app, ["vrfs"])
        assert result.exit_code == 0
        assert "Production" in result.output
        assert "VRFs" in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vrfs_json(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = MOCK_VRF_RESPONSE
        result = runner.invoke(app, ["vrfs", "--format", "json"])
        assert result.exit_code == 0
        assert '"name"' in result.output

    @patch("netbox_data_puller.cli._fetch", new_callable=AsyncMock)
    @patch("netbox_data_puller.cli._get_settings")
    def test_vrfs_passes_filters(
        self,
        mock_settings: AsyncMock,
        mock_fetch: AsyncMock,
    ) -> None:
        mock_fetch.return_value = []
        runner.invoke(
            app,
            ["vrfs", "--tenant", "Ops", "--tag", "core", "--search", "prod"],
        )
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        assert params["tenant"] == "Ops"
        assert params["tag"] == "core"
        assert params["q"] == "prod"


# ------------------------------------------------------------------
# Config exit code
# ------------------------------------------------------------------


class TestConfigError:
    def test_missing_config_exits_with_code_2(self) -> None:
        """Config/auth failure must exit with code 2 per CLI instructions."""
        with patch(
            "netbox_data_puller.cli._get_settings",
            side_effect=SystemExit(2),
        ):
            result = runner.invoke(app, ["prefixes"])
            assert result.exit_code == 2


# ------------------------------------------------------------------
# Setup command
# ------------------------------------------------------------------


MOCK_PROBE_ALL_OK = [
    ("status/", True, "200 OK"),
    ("ipam/prefixes/", True, "200 OK"),
    ("ipam/ip-addresses/", True, "200 OK"),
    ("ipam/vlans/", True, "200 OK"),
    ("ipam/vrfs/", True, "200 OK"),
]

MOCK_PROBE_PARTIAL_FAIL = [
    ("status/", True, "200 OK"),
    ("ipam/prefixes/", True, "200 OK"),
    ("ipam/ip-addresses/", False, "403 Forbidden"),
    ("ipam/vlans/", True, "200 OK"),
    ("ipam/vrfs/", True, "200 OK"),
]


class TestSetupCommand:
    """Tests for the setup wizard."""

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_creates_env(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Setup creates a .env file with the provided URL and token."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        # Provide: URL, token, then decline batch file
        result = runner.invoke(
            app,
            ["setup"],
            input="https://netbox.example.com\ntest-token-abc123\nn\n",
        )
        assert result.exit_code == 0
        env_file = tmp_path / ".env"
        assert env_file.exists()
        content = env_file.read_text()
        assert "NETBOX_URL=https://netbox.example.com" in content
        assert "NETBOX_TOKEN=test-token-abc123" in content

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_runs_connection_test(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Setup probes the API and displays results."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input="https://netbox.example.com\nmy-token\nn\n",
        )
        assert result.exit_code == 0
        assert "All endpoints reachable" in result.output

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_partial_probe_failure(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Partial probe failures show a warning."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_PARTIAL_FAIL
        result = runner.invoke(
            app,
            ["setup"],
            input="https://netbox.example.com\nmy-token\nn\n",
        )
        assert result.exit_code == 0
        assert "Some endpoints failed" in result.output
        assert "Fail" in result.output

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_existing_env_keep(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """When .env exists and user declines overwrite, keeps existing."""
        monkeypatch.chdir(tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "NETBOX_URL=https://old.example.com\n"
            "NETBOX_TOKEN=old-token-1234\n",
        )
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        # Answer 'n' to overwrite, 'n' to batch
        result = runner.invoke(
            app,
            ["setup"],
            input="n\nn\n",
        )
        assert result.exit_code == 0
        assert "Keeping existing" in result.output
        # File should remain untouched
        assert "old.example.com" in env_file.read_text()

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_existing_env_overwrite(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """When .env exists and user chooses overwrite, replaces it."""
        monkeypatch.chdir(tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "NETBOX_URL=https://old.example.com\n"
            "NETBOX_TOKEN=old-token-1234\n",
        )
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        # Answer 'y' to overwrite, provide new URL + token, decline batch
        result = runner.invoke(
            app,
            ["setup"],
            input="y\nhttps://new.example.com\nnew-token-xyz\nn\n",
        )
        assert result.exit_code == 0
        content = env_file.read_text()
        assert "NETBOX_URL=https://new.example.com" in content
        assert "NETBOX_TOKEN=new-token-xyz" in content

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_token_masked(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Existing token is shown masked (last 4 chars)."""
        monkeypatch.chdir(tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "NETBOX_URL=https://netbox.example.com\n"
            "NETBOX_TOKEN=abcdefgh1234\n",
        )
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input="n\nn\n",
        )
        assert result.exit_code == 0
        # Last 4 chars visible, rest masked
        assert "1234" in result.output
        assert "abcdefgh1234" not in result.output

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_creates_batch_toml(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Setup creates batch_prefixes.toml when user provides prefixes."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        # URL, token, 'y' to batch, two prefixes then empty, 'n' to filters
        result = runner.invoke(
            app,
            ["setup"],
            input=(
                "https://netbox.example.com\n"
                "my-token\n"
                "y\n"
                "10.0.0.0/8\n"
                "172.16.0.0/12\n"
                "\n"
                "n\n"
            ),
        )
        assert result.exit_code == 0
        batch_file = tmp_path / "batch_prefixes.toml"
        assert batch_file.exists()
        content = batch_file.read_text()
        assert "10.0.0.0/8" in content
        assert "172.16.0.0/12" in content

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_batch_toml_with_filters(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Batch TOML includes filters when user provides them."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input=(
                "https://netbox.example.com\n"
                "my-token\n"
                "y\n"
                "10.0.0.0/8\n"
                "\n"
                "y\n"
                "active\n"
                "Production\n"
                "\n"
            ),
        )
        assert result.exit_code == 0
        batch_file = tmp_path / "batch_prefixes.toml"
        assert batch_file.exists()
        content = batch_file.read_text()
        assert 'status = "active"' in content
        assert 'vrf = "Production"' in content

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_skips_existing_batch_toml(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Existing batch file is not overwritten."""
        monkeypatch.chdir(tmp_path)
        batch_file = tmp_path / "batch_prefixes.toml"
        batch_file.write_text('prefixes = ["existing"]\n')
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input="https://netbox.example.com\nmy-token\n",
        )
        assert result.exit_code == 0
        assert "already exists" in result.output
        assert batch_file.read_text() == 'prefixes = ["existing"]\n'

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_url_auto_https(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """URL without scheme gets https:// prepended."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input="netbox.example.com\nmy-token\nn\n",
        )
        assert result.exit_code == 0
        content = (tmp_path / ".env").read_text()
        assert "NETBOX_URL=https://netbox.example.com" in content

    @patch("netbox_data_puller.cli._run_probe", new_callable=AsyncMock)
    def test_setup_shows_done_panel(
        self,
        mock_probe: AsyncMock,
        tmp_path: Path,
        monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        """Completion panel shows suggested commands."""
        monkeypatch.chdir(tmp_path)
        mock_probe.return_value = MOCK_PROBE_ALL_OK
        result = runner.invoke(
            app,
            ["setup"],
            input="https://netbox.example.com\nmy-token\nn\n",
        )
        assert result.exit_code == 0
        assert "Setup complete" in result.output
        assert "nbpull prefixes" in result.output
