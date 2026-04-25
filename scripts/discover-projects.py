#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
discover-projects.py — Discover active projects not in daily-brief config.

Scans ~/.claude/projects/ JSONL files and ~/code/ git repos to find
projects with activity within a given time window.

Returns an execution-result envelope (core/contracts/execution-result.schema.json)
with:
  data.unconfigured     — list of slugs active but not in config
  data.unconfigured_configs — list of ProjectConfig dicts for unconfigured projects
  data.all_projects     — merged list of all ProjectConfig dicts (configured + unconfigured)

Handles gracefully:
  - Malformed JSONL lines (logs warning to stderr, continues)
  - Unreadable git repos (logs warning to stderr, continues)
  - Missing directories (returns empty set, no crash)

Usage (CLI):
    python3 scripts/discover-projects.py --config ~/.claude/daily-brief.yml --since=2026-04-24
    python3 scripts/discover-projects.py --since=1d
"""

from __future__ import annotations

import argparse
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

import config as _cfg  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PRODUCER = "scripts/discover-projects.py"
_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_CONTRACT_VERSION = "1"

_DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"
_DEFAULT_CODE_DIR = Path.home() / "code"


# ---------------------------------------------------------------------------
# Envelope helper
# ---------------------------------------------------------------------------


def _envelope(
    status: str,
    summary: str,
    data: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "data": data,
        "errors": errors or [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": _CONTRACT_VERSION,
            "producer": _PRODUCER,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "schema": _SCHEMA_PATH,
        },
    }


# ---------------------------------------------------------------------------
# JSONL discovery
# ---------------------------------------------------------------------------


def discover_from_jsonl(
    *,
    projects_dir: Path = _DEFAULT_PROJECTS_DIR,
    since: datetime.date,
) -> set[str]:
    """Scan ~/.claude/projects/ JSONL files modified within window.

    Extracts project slugs from the last path component of `projectPath`
    or `cwd` fields. Lines that fail json.loads() → log warning to stderr, skip.
    Files older than `since` are skipped.

    Args:
        projects_dir: Path to directory containing JSONL session files.
        since: Only consider files with mtime >= this date.

    Returns:
        Set of project slugs found active within the window.
    """
    slugs: set[str] = set()

    if not projects_dir.exists():
        return slugs

    since_ts = datetime.datetime.combine(since, datetime.time.min).timestamp()

    for jsonl_file in projects_dir.iterdir():
        if not jsonl_file.is_file():
            continue

        # Check file modification time
        try:
            mtime = jsonl_file.stat().st_mtime
        except OSError as exc:
            print(f"warning: cannot stat {jsonl_file}: {exc}", file=sys.stderr)
            continue

        if mtime < since_ts:
            continue

        # Parse the file line by line
        try:
            text = jsonl_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"warning: cannot read {jsonl_file}: {exc}", file=sys.stderr)
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: {jsonl_file}:{line_no}: malformed JSON — {exc}",
                    file=sys.stderr,
                )
                continue

            # Extract slug from projectPath or cwd
            for field in ("projectPath", "cwd"):
                raw_path = obj.get(field)
                if raw_path:
                    slug = Path(raw_path).name
                    if slug:
                        slugs.add(slug)
                    break

    return slugs


# ---------------------------------------------------------------------------
# Git repo discovery
# ---------------------------------------------------------------------------


def discover_from_git(
    *,
    code_dir: Path = _DEFAULT_CODE_DIR,
    since: datetime.date,
) -> set[str]:
    """Scan ~/code/ for git repos with commits within the window.

    For each subdirectory, runs `git log --oneline --since=<date>` and checks
    if any output is produced. Directories that are not git repos or where
    git fails → log warning to stderr, continue (no crash).

    Args:
        code_dir: Directory to scan (typically ~/code/).
        since: Only count repos with commits on or after this date.

    Returns:
        Set of project slugs (directory names) with recent commits.
    """
    slugs: set[str] = set()

    if not code_dir.exists():
        return slugs

    since_str = since.isoformat()

    for entry in code_dir.iterdir():
        if not entry.is_dir():
            continue

        # Quick check: is it a git repo?
        git_dir = entry / ".git"
        if not git_dir.exists():
            continue

        # Run git log to see if there are recent commits
        try:
            proc = subprocess.run(  # noqa: S603
                ["git", "-C", str(entry), "log", "--oneline", f"--since={since_str}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                slugs.add(entry.name)
            elif proc.returncode != 0:
                print(
                    f"warning: git log failed for {entry}: {proc.stderr.strip()!r}",
                    file=sys.stderr,
                )
        except subprocess.TimeoutExpired:
            print(f"warning: git log timed out for {entry}", file=sys.stderr)
        except OSError as exc:
            print(f"warning: cannot run git for {entry}: {exc}", file=sys.stderr)

    return slugs


# ---------------------------------------------------------------------------
# Main discovery function
# ---------------------------------------------------------------------------


def discover_active_projects(
    *,
    config_path: Path = _cfg.CONFIG_PATH,
    projects_dir: Path = _DEFAULT_PROJECTS_DIR,
    code_dir: Path = _DEFAULT_CODE_DIR,
    since: datetime.date,
) -> dict[str, Any]:
    """Discover all active projects, merging config and discovered repos.

    Args:
        config_path: Path to daily-brief.yml config file.
        projects_dir: Path to ~/.claude/projects/ JSONL directory.
        code_dir: Path to ~/code/ directory.
        since: Only consider activity on or after this date.

    Returns:
        Execution-result envelope with:
          data.unconfigured       — slugs of active but unconfigured projects
          data.unconfigured_configs — ProjectConfig dicts for unconfigured projects
          data.all_projects       — all ProjectConfig dicts (configured + unconfigured)
    """
    errors: list[dict[str, Any]] = []

    # Load configured projects
    resolve_result = _cfg.resolve_project(None, config_path)
    if resolve_result["status"] != "ok":
        return _envelope(
            status="error",
            summary="Failed to load config",
            data={
                "unconfigured": [],
                "unconfigured_configs": [],
                "all_projects": [],
            },
            errors=[{"code": "config-load-failed", "message": resolve_result.get("summary", "")}],
        )

    configured_projects = [
        _cfg.ProjectConfig.from_dict(p) for p in resolve_result["data"]["projects"]
    ]
    configured_slugs = {p.slug for p in configured_projects}

    # Discover active slugs from JSONL and git
    jsonl_slugs = discover_from_jsonl(projects_dir=projects_dir, since=since)
    git_slugs = discover_from_git(code_dir=code_dir, since=since)

    all_active_slugs = jsonl_slugs | git_slugs

    # Find unconfigured active slugs
    unconfigured_slugs = sorted(all_active_slugs - configured_slugs)

    # Build ProjectConfig objects for unconfigured projects
    unconfigured_configs: list[_cfg.ProjectConfig] = []
    for slug in unconfigured_slugs:
        # Try to resolve path: check code_dir/slug first
        candidate = code_dir / slug
        if candidate.is_dir():
            resolved_path = candidate
        else:
            # Fallback: use code_dir/slug as path even if it doesn't exist
            resolved_path = code_dir / slug

        unconfigured_configs.append(
            _cfg.ProjectConfig(
                name=slug,
                path=resolved_path,
                slug=slug,
                beads=False,
                docs_dir="docs",
            )
        )

    # Merge all projects: configured first, then unconfigured
    all_projects = [p.to_dict() for p in configured_projects] + [
        p.to_dict() for p in unconfigured_configs
    ]

    total_active = len(configured_slugs & all_active_slugs) + len(unconfigured_slugs)
    summary = (
        f"Discovered {len(unconfigured_slugs)} unconfigured active project(s) "
        f"(total active: {total_active})"
    )

    return _envelope(
        status="warning" if unconfigured_slugs else "ok",
        summary=summary,
        data={
            "unconfigured": unconfigured_slugs,
            "unconfigured_configs": [p.to_dict() for p in unconfigured_configs],
            "all_projects": all_projects,
        },
        errors=errors,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Discover active projects not in daily-brief config.",
        prog="discover-projects",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml).",
    )
    p.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Discovery window start date (ISO format). Default: yesterday.",
    )
    p.add_argument(
        "--projects-dir",
        type=Path,
        default=_DEFAULT_PROJECTS_DIR,
        help="Path to ~/.claude/projects/ (default: ~/.claude/projects/).",
    )
    p.add_argument(
        "--code-dir",
        type=Path,
        default=_DEFAULT_CODE_DIR,
        help="Path to ~/code/ directory (default: ~/code/).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point for discover-projects.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 = success, 1 = error).
    """
    args = _parse_args(argv)

    if args.since:
        try:
            since = datetime.date.fromisoformat(args.since)
        except ValueError:
            print(
                f"Error: Invalid --since date '{args.since}'. Use YYYY-MM-DD format.",
                file=sys.stderr,
            )
            return 1
    else:
        since = datetime.date.today() - datetime.timedelta(days=1)

    result = discover_active_projects(
        config_path=args.config,
        projects_dir=args.projects_dir,
        code_dir=args.code_dir,
        since=since,
    )

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] in ("ok", "warning") else 1


if __name__ == "__main__":
    sys.exit(main())
