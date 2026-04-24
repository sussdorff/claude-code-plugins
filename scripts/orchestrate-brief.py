#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "httpx>=0.27",
# ]
# ///
"""
orchestrate-brief.py — Daily-brief CLI orchestration.

Thin orchestration layer that ties config + query + render into a usable
/daily-brief skill entry point.

Flow:
  1. Parse CLI args (project, date/since/range, --detailed)
  2. Load config, resolve project(s)
  3. For each (project, date): check brief_exists → if missing, run render-brief.py
  4. Persist each new brief to open-brain via MCP save_memory (idempotent)
  5. Emit aggregated markdown to stdout

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
    if not since_str.endswith("d") or not since_str[:-1].isdigit():
        raise ValueError(f"Invalid --since format '{since_str}'. Expected Nd (e.g. 3d).")

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
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Open-brain persistence
# ---------------------------------------------------------------------------


def make_session_ref(project: str, date: str) -> str:
    """Build the idempotent session_ref for open-brain storage.

    Args:
        project: Project name (slug).
        date: ISO date string.

    Returns:
        session_ref string like 'daily-brief-2026-04-23'.
    """
    return f"daily-brief-{date}"


def _save_to_open_brain(
    *,
    title: str,
    text: str,
    ob_type: str,
    project: str,
    session_ref: str,
    metadata: dict[str, Any],
) -> None:
    """Save a daily brief to open-brain via MCP JSON-RPC.

    Uses the save_memory MCP tool with idempotent session_ref. If
    open-brain is unavailable (no token / connection error), silently
    skips — persistence failure must never block the brief output.

    Args:
        title: Brief title (e.g. "claude-code-plugins — 2026-04-23").
        text: Full brief markdown text.
        ob_type: Memory type (always "daily_brief").
        project: Project slug.
        session_ref: Idempotent key ("daily-brief-YYYY-MM-DD").
        metadata: Additional metadata dict.
    """
    ob_url = os.environ.get("OB_URL", "https://open-brain.sussdorff.org/mcp/mcp")
    token_env = os.environ.get("OB_TOKEN")
    token_file = Path.home() / ".open-brain" / "token"

    token: str | None = token_env
    if not token and token_file.exists():
        token = token_file.read_text().strip()

    if not token:
        # No credentials — skip silently
        return

    try:
        import httpx

        asyncio.run(
            _async_save_memory(
                ob_url=ob_url,
                token=token,
                title=title,
                text=text,
                ob_type=ob_type,
                project=project,
                session_ref=session_ref,
                metadata=metadata,
            )
        )
    except Exception:  # noqa: BLE001
        # Non-blocking: persistence failure must not abort brief output
        pass


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
    """Drive the MCP JSON-RPC save_memory call asynchronously."""
    import httpx

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # MCP JSON-RPC initialize
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "orchestrate-brief", "version": "1"},
            },
        }
        await client.post(ob_url, json=init_payload, headers=headers)

        # Call save_memory tool (idempotent via session_ref + dedup_mode=merge)
        call_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "save_memory",
                "arguments": {
                    "title": title,
                    "text": text,
                    "type": ob_type,
                    "project": project,
                    "session_ref": session_ref,
                    "metadata": metadata,
                    "dedup_mode": "merge",
                },
            },
        }
        await client.post(ob_url, json=call_payload, headers=headers)


# ---------------------------------------------------------------------------
# Render dispatch
# ---------------------------------------------------------------------------


def _run_render_brief(
    project_name: str,
    date: str,
    detailed: bool,
    config_path: Path,
) -> str:
    """Invoke render-brief.py as a subprocess for a single (project, date).

    Args:
        project_name: Project name from config.
        date: ISO date string.
        detailed: Whether to use higher word cap.
        config_path: Path to daily-brief.yml.

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
) -> dict[str, Any]:
    """Run the backfill + persist logic for one (project, date) pair.

    Checks if a brief already exists on disk. If it does, returns
    immediately (no-op). Otherwise, calls render-brief.py and persists
    the result to disk (via render-brief.py's own --persist default) and
    to open-brain.

    Args:
        project_name: Project name from daily-brief.yml.
        date: ISO date string.
        detailed: Whether to use detailed mode.
        config_path: Path to daily-brief.yml.

    Returns:
        Dict with keys: skipped (bool), content (str or None).
    """
    # Resolve the project to get its path for brief_exists check
    resolve_result = _cfg.resolve_project(project_name, config_path)
    if resolve_result["status"] != "ok" or not resolve_result["data"]["projects"]:
        return {"skipped": False, "content": None, "error": "project-not-found"}

    project = _cfg.ProjectConfig.from_dict(resolve_result["data"]["projects"][0])

    # Backfill check: skip if brief already exists on disk
    if _cfg.brief_exists(project, date):
        return {"skipped": True, "content": None}

    # Generate brief via render-brief.py subprocess
    content = _run_render_brief(project_name, date, detailed, config_path)

    if content:
        # Persist to open-brain (non-blocking — failure does not abort)
        slug = project.slug
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
) -> list[dict[str, Any]]:
    """Orchestrate brief generation across projects and dates.

    For each (project, date) pair: run_for_project. Results are returned
    as a list for caller to aggregate into output.

    Args:
        project: Project name to target, or None for all configured projects.
        dates: Ordered list of ISO date strings to process.
        detailed: Whether to use detailed mode.
        config_path: Path to daily-brief.yml.

    Returns:
        List of result dicts per (project, date) pair.
    """
    # Resolve project list
    resolve_result = _cfg.resolve_project(project, config_path)
    if resolve_result["status"] != "ok":
        return [{"error": resolve_result.get("summary", "config-error")}]

    projects = [
        _cfg.ProjectConfig.from_dict(p)
        for p in resolve_result["data"]["projects"]
    ]

    results: list[dict[str, Any]] = []
    for proj in projects:
        for date in dates:
            result = run_for_project(
                project_name=proj.name,
                date=date,
                detailed=detailed,
                config_path=config_path,
            )
            result["project"] = proj.name
            result["date"] = date
            results.append(result)

    return results


# ---------------------------------------------------------------------------
# Output aggregation
# ---------------------------------------------------------------------------


def _aggregate_output(results: list[dict[str, Any]], dates: list[str]) -> str:
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
        return "No new briefs generated. All requested briefs already exist on disk.\n"
    return "\n".join(lines)


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
        results = _orchestrate_range(
            project=args.project,
            dates=dates,
            detailed=args.detailed,
            config_path=config_path,
        )
    else:
        # Single date or default
        results = orchestrate(
            project=args.project,
            dates=dates,
            detailed=args.detailed,
            config_path=config_path,
        )

    # Emit aggregated output
    output = _aggregate_output(results, dates)
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
