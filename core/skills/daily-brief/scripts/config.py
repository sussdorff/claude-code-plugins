#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
config.py — daily-brief config loader and per-project path helpers.

Loads ~/.claude/daily-brief.yml, bootstrapping it with default project list if
missing. Provides path helpers for per-project brief storage layout.

Storage layout: <project>/.claude/daily-briefs/YYYY-MM-DD.md

Multi-field functions emit core/contracts/execution-result.schema.json envelopes.
Single atomic values (Path, bool) are returned bare.

Usage (CLI — for testing / shell integration):
    python3 config.py load
    python3 config.py resolve [<name>]
    python3 config.py brief-path <name> <YYYY-MM-DD>
    python3 config.py brief-exists <name> <YYYY-MM-DD>
    python3 config.py briefs-dir <name>
"""

from __future__ import annotations

import datetime
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_PATH = Path.home() / ".claude" / "daily-brief.yml"
_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_PRODUCER = "core/skills/daily-brief/scripts/config.py"
_CONTRACT_VERSION = "1"

_DEFAULT_CONFIG: dict[str, Any] = {
    "projects": [
        {
            "name": "claude-code-plugins",
            "path": "/Users/malte/code/claude-code-plugins",
            "slug": "claude-code-plugins",
            "beads": True,
            "docs_dir": "docs",
        },
        {
            "name": "mira",
            "path": "/Users/malte/code/mira",
            "slug": "mira",
            "beads": True,
            "docs_dir": "docs",
        },
        {
            "name": "polaris",
            "path": "/Users/malte/code/polaris",
            "slug": "polaris",
            "beads": False,
            "docs_dir": "docs",
        },
        {
            "name": "open-brain",
            "path": "/Users/malte/code/open-brain",
            "slug": "open-brain",
            "beads": True,
            "docs_dir": "docs",
        },
    ],
    "defaults": {
        "since": "yesterday",
        "format": "markdown",
        "detailed": False,
        "language": "de",
        "timezone": "Europe/Berlin",
    },
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ProjectConfig:
    """A single project entry from daily-brief.yml."""

    name: str
    path: Path
    slug: str
    beads: bool = True
    docs_dir: str = "docs"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ProjectConfig":
        return cls(
            name=d["name"],
            path=Path(d["path"]),
            slug=d.get("slug", d["name"]),
            beads=bool(d.get("beads", True)),
            docs_dir=d.get("docs_dir", "docs"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "slug": self.slug,
            "beads": self.beads,
            "docs_dir": self.docs_dir,
        }


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------


def _envelope(
    status: str,
    summary: str,
    data: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    next_steps: list[dict[str, Any]] | None = None,
    open_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "data": data,
        "errors": errors or [],
        "next_steps": next_steps or [],
        "open_items": open_items or [],
        "meta": {
            "contract_version": _CONTRACT_VERSION,
            "producer": _PRODUCER,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "schema": _SCHEMA_PATH,
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load ~/.claude/daily-brief.yml, creating it with defaults if missing.

    Returns:
        Execution-result envelope. data.config holds the loaded configuration dict.
        data.bootstrapped is True if the file was created by this call.
    """
    bootstrapped = False

    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w") as fh:
            yaml.dump(_DEFAULT_CONFIG, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)
        bootstrapped = True

    with config_path.open() as fh:
        raw = yaml.safe_load(fh) or {}

    # Normalise: ensure projects list and defaults exist
    raw.setdefault("projects", [])
    raw.setdefault("defaults", {})

    summary = (
        f"Config bootstrapped at {config_path}" if bootstrapped
        else f"Config loaded from {config_path} ({len(raw['projects'])} projects)"
    )

    return _envelope(
        status="ok",
        summary=summary,
        data={
            "config": raw,
            "config_path": str(config_path),
            "bootstrapped": bootstrapped,
            "project_count": len(raw["projects"]),
        },
    )


def resolve_project(
    name_or_none: str | None = None,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    """Resolve one or all projects from config.

    Args:
        name_or_none: Project name to look up. None returns all projects.
        config_path: Path to config file (injectable for tests).

    Returns:
        Execution-result envelope. data.projects holds list[dict] of matching projects.
    """
    result = load_config(config_path)
    if result["status"] != "ok":
        return result

    raw_projects: list[dict[str, Any]] = result["data"]["config"].get("projects", [])
    projects = [ProjectConfig.from_dict(p) for p in raw_projects]

    if name_or_none is None:
        matched = projects
        summary = f"Resolved all {len(matched)} projects"
    else:
        matched = [p for p in projects if p.name == name_or_none]
        if not matched:
            return _envelope(
                status="error",
                summary=f"Project '{name_or_none}' not found in config",
                data={"projects": [], "query": name_or_none},
                errors=[
                    {
                        "code": "project-not-found",
                        "message": f"No project named '{name_or_none}' in {config_path}",
                        "retryable": False,
                        "suggested_fix": f"Add the project to {config_path} or check spelling.",
                        "continue_with": "Use resolve_project(None) to list all available projects.",
                    }
                ],
            )
        summary = f"Resolved project '{name_or_none}'"

    return _envelope(
        status="ok",
        summary=summary,
        data={
            "projects": [p.to_dict() for p in matched],
            "query": name_or_none,
            "count": len(matched),
        },
    )


def briefs_dir(project: ProjectConfig) -> Path:
    """Return the daily-briefs directory for a project.

    Args:
        project: Resolved ProjectConfig instance.

    Returns:
        Path to <project.path>/.claude/daily-briefs/ (not guaranteed to exist).
    """
    return project.path / ".claude" / "daily-briefs"


def brief_path(project: ProjectConfig, date: datetime.date | str) -> Path:
    """Return the path for a single brief file.

    Args:
        project: Resolved ProjectConfig instance.
        date: Date as datetime.date or ISO string YYYY-MM-DD.

    Returns:
        Path to <project>/.claude/daily-briefs/YYYY-MM-DD.md
    """
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date)
    return briefs_dir(project) / f"{date.isoformat()}.md"


def brief_exists(project: ProjectConfig, date: datetime.date | str) -> bool:
    """Check whether a brief file exists on disk.

    Args:
        project: Resolved ProjectConfig instance.
        date: Date as datetime.date or ISO string YYYY-MM-DD.

    Returns:
        True if the brief file exists, False otherwise.
    """
    return brief_path(project, date).is_file()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _cli_load(args: list[str]) -> int:
    result = load_config()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


def _cli_resolve(args: list[str]) -> int:
    name = args[0] if args else None
    result = resolve_project(name)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ok" else 1


def _cli_brief_path(args: list[str]) -> int:
    if len(args) < 2:
        print("Usage: brief-path <project-name> <YYYY-MM-DD>", file=sys.stderr)
        return 2
    result = resolve_project(args[0])
    if result["status"] != "ok" or not result["data"]["projects"]:
        print(json.dumps(result, indent=2))
        return 1
    p = ProjectConfig.from_dict(result["data"]["projects"][0])
    print(brief_path(p, args[1]))
    return 0


def _cli_brief_exists(args: list[str]) -> int:
    if len(args) < 2:
        print("Usage: brief-exists <project-name> <YYYY-MM-DD>", file=sys.stderr)
        return 2
    result = resolve_project(args[0])
    if result["status"] != "ok" or not result["data"]["projects"]:
        print(json.dumps(result, indent=2))
        return 1
    p = ProjectConfig.from_dict(result["data"]["projects"][0])
    print(str(brief_exists(p, args[1])).lower())
    return 0


def _cli_briefs_dir(args: list[str]) -> int:
    if not args:
        print("Usage: briefs-dir <project-name>", file=sys.stderr)
        return 2
    result = resolve_project(args[0])
    if result["status"] != "ok" or not result["data"]["projects"]:
        print(json.dumps(result, indent=2))
        return 1
    p = ProjectConfig.from_dict(result["data"]["projects"][0])
    print(briefs_dir(p))
    return 0


_COMMANDS = {
    "load": _cli_load,
    "resolve": _cli_resolve,
    "brief-path": _cli_brief_path,
    "brief-exists": _cli_brief_exists,
    "briefs-dir": _cli_briefs_dir,
}


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] not in _COMMANDS:
        cmds = " | ".join(_COMMANDS)
        print(f"Usage: config.py <{cmds}> [args...]", file=sys.stderr)
        return 2
    return _COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main())
