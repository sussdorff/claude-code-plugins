#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "mcp>=1.11",
# ]
# ///
"""
orchestrate-brief.py — Daily-brief CLI orchestration.

Thin orchestration layer that ties config + query + render into a usable
/daily-brief skill entry point.

Flow:
  1. Parse CLI args (project, date/since/range, --detailed, --all-active)
  2. Load config, resolve project(s)
  3. If --all-active: discover unconfigured active projects and merge
  4. For each (project, date): check brief_exists → if missing, run render-brief.py
  5. Persist each new brief to open-brain via MCP save_memory (idempotent)
  6. Emit aggregated markdown to stdout (with warning block if unconfigured found)

Usage:
    # All projects, yesterday (default)
    python3 scripts/orchestrate-brief.py

    # Single project
    python3 scripts/orchestrate-brief.py claude-code-plugins

    # Last N days
    python3 scripts/orchestrate-brief.py --since=3d

    # Specific date
    python3 scripts/orchestrate-brief.py --date=2026-04-23

    # Date range (inclusive)
    python3 scripts/orchestrate-brief.py --range=2026-04-20..2026-04-22

    # Detailed mode (~300 words/project instead of ~150)
    python3 scripts/orchestrate-brief.py --detailed

    # Discover and include all active projects (even unconfigured)
    python3 scripts/orchestrate-brief.py --all-active

    # With explicit config path (for testing)
    python3 scripts/orchestrate-brief.py --config ~/.claude/daily-brief.yml
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup: make config.py importable when invoked from scripts/
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_CONFIG_SCRIPTS = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_CONFIG_SCRIPTS))

import config as _cfg  # noqa: E402  (after sys.path manipulation)

# Import discover-projects via importlib (hyphen in filename)
import importlib.util as _importlib_util

try:
    _DISCOVER_SPEC = _importlib_util.spec_from_file_location(
        "discover_projects", Path(__file__).parent / "discover-projects.py"
    )
    _discover_mod = _importlib_util.module_from_spec(_DISCOVER_SPEC)  # type: ignore[arg-type]
    _DISCOVER_SPEC.loader.exec_module(_discover_mod)  # type: ignore[union-attr]
    discover_active_projects = _discover_mod.discover_active_projects
except Exception as _discover_import_err:  # noqa: BLE001
    # Discovery is an optional feature; if the module fails to load, provide a
    # stub that returns an error envelope so --all-active degrades gracefully.
    def discover_active_projects(**kwargs):  # type: ignore[misc]
        return {
            "status": "error",
            "summary": f"discover-projects.py failed to load: {_discover_import_err}",
            "data": {"unconfigured": [], "unconfigured_configs": [], "all_projects": []},
            "errors": [{"code": "import-error", "message": str(_discover_import_err)}],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1", "producer": "orchestrate-brief.py"},
        }

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PRODUCER = "scripts/orchestrate-brief.py"
_TZ = datetime.timezone.utc


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def parse_since(since_str: str) -> list[str]:
    """Parse a --since=Nd string into a list of ISO date strings.

    Args:
        since_str: String like "3d", "7d", "1d".

    Returns:
        List of ISO date strings from N days ago to yesterday (inclusive).
        Ordered oldest-first.

    Raises:
        ValueError: If format is invalid.
    """
    if since_str == "yesterday":
        since_str = "1d"

    if not since_str.endswith("d") or not since_str[:-1].isdigit():
        raise ValueError(
            f"Invalid --since format '{since_str}'. Expected Nd (e.g. 3d) or 'yesterday'."
        )

    n = int(since_str[:-1])
    today = datetime.date.today()
    return [
        (today - datetime.timedelta(days=i)).isoformat()
        for i in range(n, 0, -1)
    ]


def parse_range_str(range_str: str) -> list[str]:
    """Parse a --range=START..END string into a list of ISO date strings.

    Args:
        range_str: String like "2026-04-20..2026-04-22".

    Returns:
        List of ISO date strings from START to END (inclusive).

    Raises:
        ValueError: If format is invalid.
    """
    if ".." not in range_str:
        raise ValueError(
            f"Invalid --range format '{range_str}'. Expected YYYY-MM-DD..YYYY-MM-DD."
        )
    parts = range_str.split("..", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid --range format '{range_str}'. Expected YYYY-MM-DD..YYYY-MM-DD."
        )
    start_str, end_str = parts
    start = datetime.date.fromisoformat(start_str)
    end = datetime.date.fromisoformat(end_str)
    dates: list[str] = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += datetime.timedelta(days=1)
    return dates


def dates_for_args(
    *,
    date: str | None,
    since: str | None,
    range_str: str | None,
) -> list[str]:
    """Resolve the list of dates to process from CLI args.

    Priority: date > range_str > since > default (yesterday).

    Args:
        date: Explicit date string (YYYY-MM-DD) or None.
        since: Since string (Nd) or None.
        range_str: Range string (START..END) or None.

    Returns:
        List of ISO date strings to process (oldest-first).
    """
    if date is not None:
        return [date]
    if range_str is not None:
        return parse_range_str(range_str)
    if since is not None:
        return parse_since(since)
    # Default: yesterday
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    return [yesterday]


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the orchestrate-brief command.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace.
    """
    p = argparse.ArgumentParser(
        description="Generate and manage daily project briefs.",
        prog="daily-brief",
    )
    p.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project name from daily-brief.yml. Omit to process all configured projects.",
    )
    mode_group = p.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Generate brief for a specific date.",
    )
    mode_group.add_argument(
        "--since",
        metavar="Nd",
        help="Generate briefs for last N days (e.g. --since=3d).",
    )
    mode_group.add_argument(
        "--range",
        metavar="START..END",
        help="Generate briefs for date range (e.g. --range=2026-04-20..2026-04-22).",
    )
    p.add_argument(
        "--detailed",
        action="store_true",
        help="Detailed mode: raise word cap from ~150 to ~300 words/project.",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml).",
    )
    p.add_argument(
        "--all-active",
        action="store_true",
        dest="all_active",
        help=(
            "Discover and include all active projects (from ~/.claude/projects/ and ~/code/), "
            "even if not in daily-brief.yml. Emits a warning block for unconfigured projects."
        ),
    )
    p.add_argument(
        "--persist-disk",
        action="store_true",
        dest="persist_disk",
        default=False,
        help=(
            "Also write briefs to disk (<project>/.claude/daily-briefs/YYYY-MM-DD.md). "
            "Default: open-brain only. Use this flag for local backups."
        ),
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Open-brain persistence
# ---------------------------------------------------------------------------


def make_session_ref(project: str, date: str) -> str:
    """Build the idempotent session_ref for open-brain storage.

    Includes the project slug in the key to prevent collisions across projects
    when searching open-brain by session_ref.

    Args:
        project: Project name (slug).
        date: ISO date string.

    Returns:
        session_ref string like 'daily-brief-claude-code-plugins-2026-04-23'.
    """
    return f"daily-brief-{project}-{date}"


def _resolve_ob_credentials() -> tuple[str | None, str]:
    """Resolve open-brain token and URL from the environment / token file / config.json.

    Resolution order for the token:
      1. OB_TOKEN env var
      2. ~/.open-brain/token (plaintext file)
      3. ~/.open-brain/config.json — reads "api_key" field

    Resolution order for the endpoint URL:
      1. OB_URL env var
      2. ~/.open-brain/config.json — reads "server_url" + appends "/mcp"
      3. Hardcoded default: "https://open-brain.sussdorff.org/mcp"

    Returns:
        (token, ob_url) — token is None when no credentials are available.
    """
    import json

    ob_home = Path.home() / ".open-brain"
    token_env = os.environ.get("OB_TOKEN")
    token_file = ob_home / "token"
    config_file = ob_home / "config.json"

    # Read config.json once unconditionally — used for both token and URL fallbacks
    cfg: dict = {}
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text())
        except OSError:
            pass
        except json.JSONDecodeError as exc:
            print(
                f"warning: ~/.open-brain/config.json is malformed: {exc}",
                file=sys.stderr,
            )

    # Resolve token: env var > token file > config.json api_key
    token: str | None = token_env
    if not token and token_file.exists():
        token = token_file.read_text().strip() or None
    if not token:
        token = cfg.get("api_key") or None

    # Resolve URL: env var > config.json server_url > hardcoded default
    if os.environ.get("OB_URL"):
        ob_url = os.environ["OB_URL"]
    elif cfg.get("server_url"):
        ob_url = cfg["server_url"].rstrip("/") + "/mcp"
    else:
        ob_url = "https://open-brain.sussdorff.org/mcp"

    return token, ob_url


def _save_to_open_brain(
    *,
    title: str,
    text: str,
    ob_type: str,
    project: str,
    session_ref: str,
    metadata: dict[str, Any],
) -> None:
    """Save a daily brief to open-brain via the official mcp SDK.

    Uses the save_memory MCP tool with idempotent session_ref. The mcp SDK
    handles session lifecycle (initialize handshake, session-id management,
    SSE parsing) transparently via the Streamable HTTP transport.

    open-brain is the system-of-record for daily briefs (v1.5). Failure to
    write is a hard error — raises RuntimeError if no credentials, re-raises
    any connection/tool error so callers can surface it.

    Args:
        title: Brief title (e.g. "claude-code-plugins — 2026-04-23").
        text: Full brief markdown text.
        ob_type: Memory type (always "daily_brief").
        project: Project slug.
        session_ref: Idempotent key ("daily-brief-{project}-YYYY-MM-DD").
        metadata: Additional metadata dict (do_not_compact and schema_version
            are injected automatically).

    Raises:
        RuntimeError: When no credentials are configured.
        Exception: Re-raised from _async_save_memory on connection/tool error.
    """
    token, ob_url = _resolve_ob_credentials()

    if not token:
        raise RuntimeError(
            "open-brain: no credentials configured — cannot persist brief. "
            "Set OB_TOKEN env var or create ~/.open-brain/token."
        )

    # Inject required v1.5 metadata fields
    effective_metadata = {
        **metadata,
        "do_not_compact": True,
        "schema_version": "1.5",
        "version": "v1.5",
    }

    asyncio.run(
        _async_save_memory(
            ob_url=ob_url,
            token=token,
            title=title,
            text=text,
            ob_type=ob_type,
            project=project,
            session_ref=session_ref,
            metadata=effective_metadata,
        )
    )


async def _async_save_memory(
    *,
    ob_url: str,
    token: str,
    title: str,
    text: str,
    ob_type: str,
    project: str,
    session_ref: str,
    metadata: dict[str, Any],
) -> None:
    """Drive the MCP save_memory tool call asynchronously via the official mcp SDK.

    Uses mcp.client.streamable_http.streamablehttp_client which handles the
    MCP Streamable-HTTP session lifecycle:
    - initialize handshake and session-id negotiation
    - SSE response parsing
    - capability negotiation

    The open-brain server authenticates via x-api-key header. Authorization: Bearer
    is rejected because api_key values are opaque strings, not JWTs.
    """
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client  # headers= API

    # x-api-key is the correct authentication header for open-brain.
    # SDK passes these headers in the Streamable HTTP transport.
    headers = {"x-api-key": token}

    async with streamablehttp_client(ob_url, headers=headers) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            # Call save_memory tool (idempotent via session_ref + dedup_mode=merge)
            result = await session.call_tool(
                "save_memory",
                {
                    "title": title,
                    "text": text,
                    "type": ob_type,
                    "project": project,
                    "session_ref": session_ref,
                    "metadata": metadata,
                    "dedup_mode": "merge",
                },
            )
            # SDK tool-level errors: isError=True means the tool reported failure.
            # Raise so the caller (_save_to_open_brain) can log a warning.
            if result.isError:
                error_text = " ".join(
                    block.text
                    for block in result.content
                    if hasattr(block, "type") and block.type == "text"
                )
                raise RuntimeError(
                    f"MCP save_memory tool returned error: {error_text or 'unknown error'}"
                )


async def _async_search_memory(
    *,
    ob_url: str,
    token: str,
    project: str,
    date: str,
) -> str | None:
    """Search open-brain for an existing daily brief via the MCP search tool.

    Uses session_ref as the search key for exact match. Returns the brief text
    if found, or None if not present or if OB is unreachable.

    Args:
        ob_url: Open-brain MCP endpoint URL.
        token: Open-brain API token.
        project: Project slug.
        date: ISO date string.

    Returns:
        Brief text string if found, None otherwise.
    """
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    session_ref = make_session_ref(project, date)
    headers = {"x-api-key": token}

    async with streamablehttp_client(ob_url, headers=headers) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "search",
                {
                    "query": session_ref,
                    "type": "daily_brief",
                    "project": project,
                    "limit": 1,
                },
            )
            if result.isError:
                return None
            # Parse content: look for the brief text in the result
            for block in result.content:
                if hasattr(block, "type") and block.type == "text" and block.text:
                    # The search tool returns JSON with observations
                    try:
                        parsed = json.loads(block.text)
                        observations = parsed.get("observations") or parsed.get("results") or []
                        for obs in observations:
                            obs_ref = obs.get("session_ref") or obs.get("sessionRef", "")
                            if obs_ref == session_ref:
                                return obs.get("text") or obs.get("content")
                    except (json.JSONDecodeError, AttributeError):
                        pass
            return None


def _read_from_open_brain(project: str, date: str) -> str | None:
    """Read an existing daily brief from open-brain.

    Attempts to find the brief by session_ref in open-brain. Returns the text
    if found, or None if not found or if OB is unreachable (so callers can
    fall back to disk).

    Args:
        project: Project slug.
        date: ISO date string.

    Returns:
        Brief text if found in open-brain, None otherwise.
    """
    token, ob_url = _resolve_ob_credentials()
    if not token:
        return None

    try:
        return asyncio.run(
            _async_search_memory(
                ob_url=ob_url,
                token=token,
                project=project,
                date=date,
            )
        )
    except Exception:  # noqa: BLE001
        # OB is unreachable or search failed — fall back to disk
        return None


# ---------------------------------------------------------------------------
# Render dispatch
# ---------------------------------------------------------------------------


def _run_render_brief(
    project_name: str,
    date: str,
    detailed: bool,
    config_path: Path,
    persist_disk: bool = False,
) -> str:
    """Invoke render-brief.py as a subprocess for a single (project, date).

    By default (persist_disk=False), passes --no-persist to render-brief.py so
    that disk writes are suppressed. open-brain is the system-of-record (v1.5).
    When persist_disk=True, omits --no-persist so render-brief.py writes to disk.

    Args:
        project_name: Project name from config.
        date: ISO date string.
        detailed: Whether to use higher word cap.
        config_path: Path to daily-brief.yml.
        persist_disk: When True, allow render-brief.py to write brief to disk.
            Default False: disk write is suppressed (OB-only mode).

    Returns:
        Rendered markdown string (empty string on failure).
    """
    render_script = Path(__file__).parent / "render-brief.py"
    cmd = [
        sys.executable, str(render_script),
        "--project", project_name,
        "--date", date,
        "--config", str(config_path),
    ]
    if detailed:
        cmd.append("--detailed")
    if not persist_disk:
        cmd.append("--no-persist")

    proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if proc.returncode != 0:
        return ""
    return proc.stdout


# ---------------------------------------------------------------------------
# Per-project, per-date execution
# ---------------------------------------------------------------------------


def run_for_project(
    project_name: str,
    date: str,
    detailed: bool,
    config_path: Path,
    project_config: "_cfg.ProjectConfig | None" = None,
    persist_disk: bool = False,
) -> dict[str, Any]:
    """Run the backfill + persist logic for one (project, date) pair.

    Read path (v1.5 SoR): checks open-brain first. If the brief is found in OB,
    returns immediately (skipped=True, content=ob_content). Falls back to disk
    check when OB returns None (offline/unavailable). If neither OB nor disk has
    the brief, calls render-brief.py and persists to OB (hard error on failure).

    Args:
        project_name: Project name from daily-brief.yml.
        date: ISO date string.
        detailed: Whether to use detailed mode.
        config_path: Path to daily-brief.yml.
        project_config: Optional pre-resolved ProjectConfig (for discovered projects
            not in config). When provided, config lookup is skipped.
        persist_disk: When True, also write brief to disk via render-brief.py.
            Default False: OB-only mode.

    Returns:
        Dict with keys: skipped (bool), content (str or None).

    Raises:
        RuntimeError: When OB write fails (no credentials or connection error).
    """
    # Resolve the project to get its path for brief_exists check
    is_discovered = project_config is not None
    if project_config is not None:
        project = project_config
    else:
        resolve_result = _cfg.resolve_project(project_name, config_path)
        if resolve_result["status"] != "ok" or not resolve_result["data"]["projects"]:
            return {"skipped": False, "content": None, "error": "project-not-found"}
        project = _cfg.ProjectConfig.from_dict(resolve_result["data"]["projects"][0])

    slug = project.slug

    # v1.5 SoR: check open-brain first
    ob_content = _read_from_open_brain(slug, date)
    if ob_content is not None:
        return {"skipped": True, "content": ob_content}

    # Fallback: disk check (for offline / OB-unavailable scenarios)
    if _cfg.brief_exists(project, date):
        return {"skipped": True, "content": None}

    # Discovered (unconfigured) projects: render a stub section instead of
    # delegating to render-brief.py (which would fail — project not in config).
    if is_discovered:
        content = (
            f"## {project_name} (discovered, not configured)\n\n"
            f"> ⚠️ This project was found via git activity but is not in daily-brief.yml.\n"
            f"> No brief content is available. To include full briefs, add this project to your config.\n"
        )
        return {"skipped": False, "content": content}

    # Generate brief via render-brief.py subprocess
    content = _run_render_brief(project_name, date, detailed, config_path, persist_disk=persist_disk)

    if content:
        # Persist to open-brain — hard error on failure (v1.5)
        session_ref = make_session_ref(slug, date)
        _save_to_open_brain(
            title=f"{project_name} — {date}",
            text=content,
            ob_type="daily_brief",
            project=slug,
            session_ref=session_ref,
            metadata={"source": "daily-brief"},
        )

    return {"skipped": False, "content": content}


# ---------------------------------------------------------------------------
# Orchestration: multi-project + multi-date
# ---------------------------------------------------------------------------


def orchestrate(
    project: str | None,
    dates: list[str],
    detailed: bool,
    config_path: Path,
    all_active: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Orchestrate brief generation across projects and dates.

    For each (project, date) pair: run_for_project. Results are returned
    as a tuple (results, unconfigured_slugs) to avoid mixing metadata into
    the results list.

    When all_active=True, discover_active_projects() is called to find active
    projects not in config and they are merged into the project list.

    Args:
        project: Project name to target, or None for all configured projects.
        dates: Ordered list of ISO date strings to process.
        detailed: Whether to use detailed mode.
        config_path: Path to daily-brief.yml.
        all_active: If True, discover unconfigured active projects and include them.

    Returns:
        Tuple of (results, unconfigured_slugs) where results is a list of
        run_for_project result dicts and unconfigured_slugs is a sorted list
        of project slugs that were discovered but are not in config.
    """
    # Resolve configured project list
    resolve_result = _cfg.resolve_project(project, config_path)
    if resolve_result["status"] != "ok":
        return [{"error": resolve_result.get("summary", "config-error")}], []

    # List of (ProjectConfig, is_configured) tuples
    configured_projects = [
        _cfg.ProjectConfig.from_dict(p)
        for p in resolve_result["data"]["projects"]
    ]
    project_entries: list[tuple["_cfg.ProjectConfig", bool]] = [
        (proj, True) for proj in configured_projects
    ]

    # Discovery path: find unconfigured active projects
    unconfigured_slugs: list[str] = []
    if all_active and project is None:
        # Use earliest date in range as the since date for discovery
        since_str = min(dates) if dates else (
            datetime.date.today() - datetime.timedelta(days=1)
        ).isoformat()
        try:
            since_date = datetime.date.fromisoformat(since_str)
        except (ValueError, AttributeError):
            since_date = datetime.date.today() - datetime.timedelta(days=1)

        discover_result = discover_active_projects(
            config_path=config_path,
            since=since_date,
        )

        if discover_result.get("status") in ("ok", "warning"):
            unconfigured_slugs = discover_result["data"].get("unconfigured", [])
            unconfigured_configs = discover_result["data"].get("unconfigured_configs", [])
            # Append unconfigured projects to project list (not configured)
            for pc_dict in unconfigured_configs:
                pc = _cfg.ProjectConfig.from_dict(pc_dict)
                project_entries.append((pc, False))

    results: list[dict[str, Any]] = []
    for proj, is_configured in project_entries:
        for date in dates:
            if is_configured:
                result = run_for_project(
                    project_name=proj.name,
                    date=date,
                    detailed=detailed,
                    config_path=config_path,
                )
            else:
                # Discovered projects not in config — pass pre-resolved config
                # to bypass _cfg.resolve_project lookup (which would fail)
                result = run_for_project(
                    project_name=proj.name,
                    date=date,
                    detailed=detailed,
                    config_path=config_path,
                    project_config=proj,
                )
            result["project"] = proj.name
            result["date"] = date
            results.append(result)

    return results, unconfigured_slugs


# ---------------------------------------------------------------------------
# Warning block injection
# ---------------------------------------------------------------------------


def _inject_warning_block(content: str, unconfigured: list[str]) -> str:
    """Prepend a warning block to content when unconfigured active projects exist.

    Args:
        content: Aggregated brief markdown.
        unconfigured: List of slug strings for unconfigured active projects.

    Returns:
        Content with warning block prepended at the top, or unchanged if no unconfigured.
    """
    if not unconfigured:
        return content

    slugs_str = ", ".join(unconfigured)
    warning = f"⚠️ Aktive Projekte nicht in Config: {slugs_str}\n\n"
    return warning + content


# ---------------------------------------------------------------------------
# Output aggregation
# ---------------------------------------------------------------------------


def _aggregate_output(
    results: list[dict[str, Any]],
    dates: list[str],
    unconfigured_projects: list[str] | None = None,
) -> str:
    """Build the final markdown output from orchestration results.

    For single-date runs: concatenate project briefs.
    For multi-date runs: each project's content is already a range rollup
    from render-brief.py. Concatenate projects.

    Args:
        results: List of run_for_project result dicts.
        dates: Dates that were processed.

    Returns:
        Aggregated markdown string.
    """
    lines: list[str] = []
    for r in results:
        if r.get("content"):
            if lines:
                lines.append("\n---\n")
            lines.append(r["content"])
    if not lines:
        base_output = "No new briefs generated. All requested briefs already exist on disk.\n"
    else:
        base_output = "\n".join(lines)

    return _inject_warning_block(base_output, unconfigured_projects or [])


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the daily-brief CLI.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 = success, 1 = error).
    """
    args = parse_args(argv)

    config_path: Path = args.config

    # Validate date args
    if args.date:
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            print(
                f"Error: Invalid date '{args.date}'. Use YYYY-MM-DD format.",
                file=sys.stderr,
            )
            return 1

    if args.range:
        try:
            parse_range_str(args.range)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.since:
        try:
            parse_since(args.since)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    # Validate project if given
    if args.project is not None:
        check = _cfg.resolve_project(args.project, config_path)
        if check["status"] != "ok" or not check["data"]["projects"]:
            print(
                f"Error: Project '{args.project}' not found in {config_path}.",
                file=sys.stderr,
            )
            return 1

    # Validate --all-active compatibility: not supported with multi-date modes
    if getattr(args, "all_active", False) and (args.since or args.range):
        print(
            "Error: --all-active cannot be combined with --since or --range. "
            "Use --all-active with a single --date (or omit for yesterday).",
            file=sys.stderr,
        )
        return 1

    # Resolve dates
    dates = dates_for_args(
        date=args.date,
        since=args.since,
        range_str=args.range,
    )

    # For range/since modes: use render-brief.py range mode for each project
    # For single date: use render-brief.py single-day mode for each project
    if len(dates) > 1:
        # Range mode: delegate to render-brief.py with --since/--range for each project
        clean_results = _orchestrate_range(
            project=args.project,
            dates=dates,
            detailed=args.detailed,
            config_path=config_path,
        )
        unconfigured: list[str] = []
    else:
        # Single date or default
        clean_results, unconfigured = orchestrate(
            project=args.project,
            dates=dates,
            detailed=args.detailed,
            config_path=config_path,
            all_active=getattr(args, "all_active", False),
        )

    # Emit aggregated output
    output = _aggregate_output(clean_results, dates, unconfigured_projects=unconfigured)
    print(output)
    return 0


def _orchestrate_range(
    project: str | None,
    dates: list[str],
    detailed: bool,
    config_path: Path,
) -> list[dict[str, Any]]:
    """Orchestrate range-mode briefs per project.

    For range mode, calls render-brief.py once per project with --since/--range
    (not per-day), which produces a compressed rollup. Per-day backfill is
    still respected — render-brief.py checks brief_exists internally and only
    re-renders days not already on disk.

    Args:
        project: Project name or None for all.
        dates: Ordered list of ISO date strings in the range.
        detailed: Whether to use detailed mode.
        config_path: Path to daily-brief.yml.

    Returns:
        List of result dicts per project.
    """
    resolve_result = _cfg.resolve_project(project, config_path)
    if resolve_result["status"] != "ok":
        return [{"error": resolve_result.get("summary", "config-error")}]

    projects = [
        _cfg.ProjectConfig.from_dict(p)
        for p in resolve_result["data"]["projects"]
    ]

    results: list[dict[str, Any]] = []
    start_date = dates[0]
    end_date = dates[-1]

    render_script = Path(__file__).parent / "render-brief.py"

    for proj in projects:
        # Record which dates are NEW (before render runs and persists them)
        new_dates = [d for d in dates if not _cfg.brief_exists(proj, d)]

        # Call render-brief.py for the full range (handles backfill internally)
        cmd = [
            sys.executable, str(render_script),
            "--project", proj.name,
            "--since", start_date,
            "--until", end_date,
            "--config", str(config_path),
        ]
        if detailed:
            cmd.append("--detailed")

        proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
        content = proc.stdout if proc.returncode == 0 else ""

        if content and new_dates:
            # Save only newly generated days to open-brain.
            # Read each day's brief from disk (not the rollup content) so that
            # per-day open-brain entries contain that day's content, not the range rollup.
            for date in new_dates:
                slug = proj.slug
                session_ref = make_session_ref(slug, date)
                # Read per-day brief from disk (written by render-brief.py)
                try:
                    per_day_brief = _cfg.brief_path(proj, date).read_text()
                except Exception:
                    per_day_brief = content  # Fallback to rollup if disk read fails
                _save_to_open_brain(
                    title=f"{proj.name} — {date}",
                    text=per_day_brief,
                    ob_type="daily_brief",
                    project=slug,
                    session_ref=session_ref,
                    metadata={"source": "daily-brief"},
                )

        results.append(
            {
                "project": proj.name,
                "date": f"{start_date}..{end_date}",
                "skipped": False,
                "content": content,
            }
        )

    return results


if __name__ == "__main__":
    sys.exit(main())
