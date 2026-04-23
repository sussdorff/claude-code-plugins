"""
Tests for the server_info module (standalone version).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# Add scripts directory to path for local imports
_scripts_dir = Path(__file__).parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import server_info
from server_info import ServerInfo, _parse_ssh_config_file, _ServerCache


class TestServerInfo:
    """Tests for the ServerInfo dataclass."""

    def test_basic_creation(self) -> None:
        """Test: ServerInfo can be created with minimal data."""
        info = ServerInfo(name="test-server")
        assert info.name == "test-server"
        assert info.type is None
        assert info.platform is None

    def test_full_creation(self) -> None:
        """Test: ServerInfo with all fields."""
        info = ServerInfo(
            name="charly-dev",
            type="windows",
            platform="windows-11",
            vm_host="charly-dev-vm",
            host_machine=None,
            parallels_vm="Windows 11 (Solutio)",
            hostname="192.168.2.100",
            user="administrator",
        )
        assert info.name == "charly-dev"
        assert info.type == "windows"
        assert info.platform == "windows-11"
        assert info.vm_host == "charly-dev-vm"
        assert info.parallels_vm == "Windows 11 (Solutio)"
        assert info.hostname == "192.168.2.100"
        assert info.user == "administrator"

    def test_frozen_dataclass(self) -> None:
        """Test: ServerInfo is immutable."""
        info = ServerInfo(name="test")
        with pytest.raises(AttributeError):
            info.name = "changed"  # type: ignore[misc]


class TestServerCache:
    """Tests for the internal cache."""

    def test_cache_initially_invalid(self) -> None:
        """Test: New cache is invalid."""
        cache = _ServerCache()
        assert not cache.is_valid()

    def test_cache_valid_after_timestamp(self) -> None:
        """Test: Cache is valid after timestamp update."""
        cache = _ServerCache()
        cache.timestamp = time.time()
        assert cache.is_valid()

    def test_cache_expires(self) -> None:
        """Test: Cache expires after TTL."""
        cache = _ServerCache(ttl=1.0)
        cache.timestamp = time.time() - 2.0  # 2 seconds in the past
        assert not cache.is_valid()

    def test_cache_clear(self) -> None:
        """Test: Cache can be cleared."""
        cache = _ServerCache()
        cache.servers = {"test": ServerInfo(name="test")}
        cache.timestamp = time.time()
        cache.clear()
        assert cache.servers == {}
        assert cache.timestamp == 0.0


class TestParseSSHConfigFile:
    """Tests for parsing SSH config files."""

    def test_parse_simple_host(self, tmp_path: Path) -> None:
        """Test: Simple host without metadata."""
        config = tmp_path / "config"
        config.write_text("""\
Host myserver
    HostName 192.168.1.100
    User admin
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].name == "myserver"
        assert servers[0].hostname == "192.168.1.100"
        assert servers[0].user == "admin"
        assert servers[0].type is None

    def test_parse_host_with_metadata(self, tmp_path: Path) -> None:
        """Test: Host with all metadata."""
        config = tmp_path / "config"
        config.write_text("""\
# @server-type: windows
# @platform: windows-11
# @vm-host: dev-vm
# @parallels-vm: Windows 11 (Dev)
Host dev-server
    HostName 10.0.0.50
    User developer
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        info = servers[0]
        assert info.name == "dev-server"
        assert info.type == "windows"
        assert info.platform == "windows-11"
        assert info.vm_host == "dev-vm"
        assert info.parallels_vm == "Windows 11 (Dev)"
        assert info.hostname == "10.0.0.50"
        assert info.user == "developer"

    def test_parse_multiple_hosts(self, tmp_path: Path) -> None:
        """Test: Multiple hosts in one file."""
        config = tmp_path / "config"
        config.write_text("""\
# @server-type: windows
Host server1
    HostName 192.168.1.1
    User admin1

# @server-type: vm
# @host-machine: server1
Host server2
    HostName 192.168.1.2
    User admin2
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 2

        server1 = next(s for s in servers if s.name == "server1")
        assert server1.type == "windows"
        assert server1.hostname == "192.168.1.1"

        server2 = next(s for s in servers if s.name == "server2")
        assert server2.type == "vm"
        assert server2.host_machine == "server1"

    def test_skip_wildcard_hosts(self, tmp_path: Path) -> None:
        """Test: Hosts with wildcards are skipped."""
        config = tmp_path / "config"
        config.write_text("""\
Host *
    AddKeysToAgent yes

Host *.example.com
    User common

Host real-server
    HostName 192.168.1.1
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].name == "real-server"

    def test_parse_host_without_hostname(self, tmp_path: Path) -> None:
        """Test: Host without HostName line."""
        config = tmp_path / "config"
        config.write_text("""\
# @server-type: local
Host localdev
    User developer
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].name == "localdev"
        assert servers[0].hostname is None

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """Test: Empty file."""
        config = tmp_path / "config"
        config.write_text("")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 0

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test: Nonexistent file."""
        config = tmp_path / "nonexistent"
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 0

    def test_metadata_case_insensitive_key(self, tmp_path: Path) -> None:
        """Test: Metadata keys are case-insensitive."""
        config = tmp_path / "config"
        config.write_text("""\
# @Server-Type: windows
# @PLATFORM: windows-10
Host myserver
    HostName 10.0.0.1
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].type == "windows"
        assert servers[0].platform == "windows-10"

    def test_host_keyword_case_insensitive(self, tmp_path: Path) -> None:
        """Test: Host keyword is case-insensitive."""
        config = tmp_path / "config"
        config.write_text("""\
HOST myserver
    HOSTNAME 10.0.0.1
    USER admin
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].name == "myserver"
        assert servers[0].hostname == "10.0.0.1"

    def test_metadata_with_spaces_in_value(self, tmp_path: Path) -> None:
        """Test: Metadata with spaces in value."""
        config = tmp_path / "config"
        config.write_text("""\
# @parallels-vm: Windows 11 Pro (Development)
Host dev
    HostName localhost
""")
        servers = list(_parse_ssh_config_file(config))
        assert len(servers) == 1
        assert servers[0].parallels_vm == "Windows 11 Pro (Development)"


class TestGetServerInfo:
    """Tests for get_server_info()."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        """Clear the cache before each test."""
        server_info.clear_cache()

    def test_get_existing_server(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Get existing server."""
        # Mock SSH config
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host test-server
    HostName 10.0.0.1
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        info = server_info.get_server_info("test-server")
        assert info is not None
        assert info.name == "test-server"
        assert info.type == "windows"

    def test_get_nonexistent_server(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Get nonexistent server."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("Host other-server\n    HostName 10.0.0.1")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        info = server_info.get_server_info("nonexistent")
        assert info is None

    def test_get_server_from_config_d(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test: Load server from config.d."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config_d = ssh_dir / "config.d"
        config_d.mkdir()

        (config_d / "myserver").write_text("""\
# @server-type: vm
Host myserver
    HostName 192.168.1.50
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        info = server_info.get_server_info("myserver")
        assert info is not None
        assert info.type == "vm"


class TestListServers:
    """Tests for list_servers()."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        """Clear the cache before each test."""
        server_info.clear_cache()

    def test_list_all_servers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: List all servers."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
Host server1
    HostName 10.0.0.1

Host server2
    HostName 10.0.0.2
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        servers = server_info.list_servers()
        assert "server1" in servers
        assert "server2" in servers

    def test_list_filter_by_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Filter by type."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host win-server
    HostName 10.0.0.1

# @server-type: vm
Host vm-server
    HostName 10.0.0.2

Host other-server
    HostName 10.0.0.3
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        windows_servers = server_info.list_servers(type="windows")
        assert windows_servers == ["win-server"]

        vm_servers = server_info.list_servers(type="vm")
        assert vm_servers == ["vm-server"]

    def test_list_with_metadata_only(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Only servers with metadata."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host server-with-meta
    HostName 10.0.0.1

Host server-without-meta
    HostName 10.0.0.2
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        servers = server_info.list_servers(with_metadata_only=True)
        assert servers == ["server-with-meta"]

    def test_list_sorted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Results are sorted."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
Host zeta
    HostName 10.0.0.1

Host alpha
    HostName 10.0.0.2

Host beta
    HostName 10.0.0.3
""")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        servers = server_info.list_servers()
        assert servers == ["alpha", "beta", "zeta"]


class TestCacheIntegration:
    """Integration tests for the cache."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        """Clear the cache before each test."""
        server_info.clear_cache()

    def test_cache_is_used(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: Cache is reused."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("Host server1\n    HostName 10.0.0.1")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # First call fills cache
        info1 = server_info.get_server_info("server1")
        assert info1 is not None

        # Change file
        config.write_text("Host server2\n    HostName 10.0.0.2")

        # Second call should use cached data
        info2 = server_info.get_server_info("server1")
        assert info2 is not None  # Still in cache

        # server2 should not be found (cache still valid)
        info3 = server_info.get_server_info("server2")
        assert info3 is None  # Not in cache

    def test_clear_cache_reloads(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test: After clear_cache data is reloaded."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("Host server1\n    HostName 10.0.0.1")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # First call
        server_info.get_server_info("server1")

        # Change file
        config.write_text("Host server2\n    HostName 10.0.0.2")

        # Clear cache and reload
        server_info.clear_cache()

        # Now new data should be loaded
        info1 = server_info.get_server_info("server1")
        assert info1 is None  # No longer present

        info2 = server_info.get_server_info("server2")
        assert info2 is not None  # Now loaded


class TestCLI:
    """Tests for the CLI entry point."""

    @pytest.fixture(autouse=True)
    def clear_cache(self) -> None:
        """Clear the cache before each test."""
        server_info.clear_cache()

    def test_no_command_returns_1(self) -> None:
        """Test: No command prints help and returns 1."""
        result = server_info.main([])
        assert result == 1

    def test_list_command(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Test: list command outputs server names."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host test-server
    HostName 10.0.0.1
""")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = server_info.main(["list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "test-server" in captured.out

    def test_list_with_type_filter(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Test: list --type filters correctly."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host win-server
    HostName 10.0.0.1

# @server-type: vm
Host vm-server
    HostName 10.0.0.2
""")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = server_info.main(["list", "--type", "windows"])
        assert result == 0
        captured = capsys.readouterr()
        assert "win-server" in captured.out
        assert "vm-server" not in captured.out

    def test_list_verbose(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Test: list -v shows detailed output."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
# @platform: windows-11
Host test-server
    HostName 10.0.0.1
    User admin
""")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = server_info.main(["list", "-v"])
        assert result == 0
        captured = capsys.readouterr()
        assert "test-server" in captured.out
        assert "Type: windows" in captured.out
        assert "Platform: windows-11" in captured.out

    def test_show_command(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Test: show command displays server details."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("""\
# @server-type: windows
Host test-server
    HostName 10.0.0.1
    User admin
""")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = server_info.main(["show", "test-server"])
        assert result == 0
        captured = capsys.readouterr()
        assert "test-server" in captured.out
        assert "Type: windows" in captured.out

    def test_show_nonexistent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Test: show for nonexistent server returns 1."""
        ssh_dir = tmp_path / ".ssh"
        ssh_dir.mkdir()
        config = ssh_dir / "config"
        config.write_text("Host other\n    HostName 10.0.0.1")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = server_info.main(["show", "nonexistent"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err
