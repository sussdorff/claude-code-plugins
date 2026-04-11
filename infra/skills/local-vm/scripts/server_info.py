#!/usr/bin/env python3
"""
Server-Info: SSH Config Parser for Server Discovery.

Reads server metadata from SSH config comments (# @key: value)
and provides CLI and programmatic access to server information.

Usage:
    python server_info.py list [--type TYPE] [--metadata-only] [-v]
    python server_info.py show <server-name> [-v]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class ServerInfo:
    """Information about an SSH server from config metadata."""

    name: str
    type: str | None = None
    platform: str | None = None
    vm_host: str | None = None
    host_machine: str | None = None
    parallels_vm: str | None = None
    hostname: str | None = None
    user: str | None = None


@dataclass
class _ServerCache:
    """Internal cache for server information."""

    servers: dict[str, ServerInfo] = field(default_factory=dict)
    timestamp: float = 0.0
    ttl: float = 300.0  # 5 minutes

    def is_valid(self) -> bool:
        """Check if the cache is still valid."""
        return time.time() - self.timestamp < self.ttl

    def clear(self) -> None:
        """Clear the cache."""
        self.servers.clear()
        self.timestamp = 0.0


# Global cache
_cache = _ServerCache()


def _get_ssh_config_paths() -> list[Path]:
    """Return all SSH config file paths."""
    ssh_dir = Path.home() / ".ssh"
    paths: list[Path] = []

    # Main config
    main_config = ssh_dir / "config"
    if main_config.exists():
        paths.append(main_config)

    # config.d directory
    config_d = ssh_dir / "config.d"
    if config_d.is_dir():
        for config_file in sorted(config_d.iterdir()):
            if config_file.is_file() and not config_file.name.startswith("."):
                paths.append(config_file)

    return paths


def _parse_ssh_config_file(path: Path) -> Iterator[ServerInfo]:
    """Parse a single SSH config file."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    # Metadata pattern: # @key: value
    metadata_pattern = re.compile(r"^#\s*@([\w-]+):\s*(.+)$")

    # Host pattern: Host hostname (without wildcards)
    host_pattern = re.compile(r"^Host\s+([^\s*?]+)$", re.IGNORECASE)

    # SSH option patterns
    hostname_pattern = re.compile(r"^\s*HostName\s+(.+)$", re.IGNORECASE)
    user_pattern = re.compile(r"^\s*User\s+(.+)$", re.IGNORECASE)

    current_metadata: dict[str, str] = {}
    current_host: str | None = None
    current_hostname: str | None = None
    current_user: str | None = None

    def _emit_server() -> ServerInfo | None:
        """Create ServerInfo from current data."""
        if current_host is None:
            return None

        return ServerInfo(
            name=current_host,
            type=current_metadata.get("server-type"),
            platform=current_metadata.get("platform"),
            vm_host=current_metadata.get("vm-host"),
            host_machine=current_metadata.get("host-machine"),
            parallels_vm=current_metadata.get("parallels-vm"),
            hostname=current_hostname,
            user=current_user,
        )

    # Metadata is collected BEFORE the Host block
    # and belongs to the next Host entry
    pending_metadata: dict[str, str] = {}

    for line in content.splitlines():
        line = line.rstrip()

        # Skip empty lines but keep metadata
        if not line:
            continue

        # Collect metadata (before Host block)
        meta_match = metadata_pattern.match(line)
        if meta_match:
            key = meta_match.group(1).lower()
            value = meta_match.group(2).strip()
            # If we have a current host and a metadata comment appears,
            # a new block is starting - emit and reset
            if current_host is not None:
                server = _emit_server()
                if server is not None:
                    yield server
                current_host = None
                current_hostname = None
                current_user = None
                current_metadata.clear()
            pending_metadata[key] = value
            continue

        # Regular comment (without @) - treat like empty line for metadata
        if line.startswith("#"):
            continue

        # Host line
        host_match = host_pattern.match(line)
        if host_match:
            # Emit previous host if present
            if current_host is not None:
                server = _emit_server()
                if server is not None:
                    yield server
                current_metadata.clear()

            # Start new host with collected metadata
            current_host = host_match.group(1)
            current_hostname = None
            current_user = None
            current_metadata = pending_metadata.copy()
            pending_metadata.clear()
            continue

        # HostName option
        hostname_match = hostname_pattern.match(line)
        if hostname_match and current_host is not None:
            current_hostname = hostname_match.group(1).strip()
            continue

        # User option
        user_match = user_pattern.match(line)
        if user_match and current_host is not None:
            current_user = user_match.group(1).strip()
            continue

    # Emit last host
    if current_host is not None:
        server = _emit_server()
        if server is not None:
            yield server


def _load_all_servers() -> dict[str, ServerInfo]:
    """Load all servers from all SSH config files."""
    servers: dict[str, ServerInfo] = {}

    for config_path in _get_ssh_config_paths():
        for server in _parse_ssh_config_file(config_path):
            # Later entries override earlier ones (like SSH itself)
            servers[server.name] = server

    return servers


def _ensure_cache() -> dict[str, ServerInfo]:
    """Ensure the cache is filled and valid."""
    if not _cache.is_valid():
        _cache.servers = _load_all_servers()
        _cache.timestamp = time.time()
    return _cache.servers


def get_server_info(server_name: str) -> ServerInfo | None:
    """
    Get server information from SSH config.

    Args:
        server_name: Name of the server (Host entry in SSH config)

    Returns:
        ServerInfo or None if not found
    """
    servers = _ensure_cache()
    return servers.get(server_name)


def list_servers(
    *,
    type: str | None = None,
    with_metadata_only: bool = False,
) -> list[str]:
    """
    List all configured servers.

    Args:
        type: Filter by server type (windows, vm, etc.)
        with_metadata_only: Only return servers with metadata

    Returns:
        List of server names
    """
    servers = _ensure_cache()

    result: list[str] = []
    for name, info in servers.items():
        # Filter: type
        if type is not None and info.type != type:
            continue

        # Filter: with_metadata_only
        if with_metadata_only:
            has_metadata = any(
                [
                    info.type,
                    info.platform,
                    info.vm_host,
                    info.host_machine,
                    info.parallels_vm,
                ]
            )
            if not has_metadata:
                continue

        result.append(name)

    return sorted(result)


def clear_cache() -> None:
    """Clear the server cache."""
    _cache.clear()


def _format_server_info(info: ServerInfo, verbose: bool = False) -> str:
    """Format a ServerInfo for display."""
    lines = [info.name]

    if verbose:
        fields = [
            ("Type", info.type),
            ("Platform", info.platform),
            ("HostName", info.hostname),
            ("User", info.user),
            ("VM Host", info.vm_host),
            ("Host Machine", info.host_machine),
            ("Parallels VM", info.parallels_vm),
        ]
        for label, value in fields:
            if value is not None:
                lines.append(f"  {label}: {value}")
    else:
        parts = [info.name]
        if info.type:
            parts.append(f"type={info.type}")
        if info.hostname:
            parts.append(f"host={info.hostname}")
        lines = ["  ".join(parts)]

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SSH Config Server Discovery",
        prog="server_info",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List servers")
    list_parser.add_argument("--type", "-t", help="Filter by server type")
    list_parser.add_argument(
        "--metadata-only", "-m", action="store_true",
        help="Only show servers with metadata",
    )
    list_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed information",
    )

    # show command
    show_parser = subparsers.add_parser("show", help="Show server details")
    show_parser.add_argument("server", help="Server name")
    show_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show all fields",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "list":
        servers = list_servers(
            type=args.type,
            with_metadata_only=args.metadata_only,
        )
        if not servers:
            print("No servers found.")
            return 0

        if args.verbose:
            for name in servers:
                info = get_server_info(name)
                if info is not None:
                    print(_format_server_info(info, verbose=True))
                    print()
        else:
            for name in servers:
                info = get_server_info(name)
                if info is not None:
                    print(_format_server_info(info, verbose=False))
        return 0

    if args.command == "show":
        info = get_server_info(args.server)
        if info is None:
            print(f"Server '{args.server}' not found.", file=sys.stderr)
            return 1
        print(_format_server_info(info, verbose=True))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
