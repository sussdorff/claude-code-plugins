#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "mcp>=1.11",
# ]
# ///
"""
migrate-disk-briefs-to-open-brain.py — Import disk briefs into open-brain.

Reads all existing per-project daily-brief markdown files from disk and
posts them to open-brain idempotently (session_ref-based dedup). Default
mode is --dry-run (reports what would be migrated). Use --apply to perform
actual writes.

Part of the daily-brief v1.5 migration: open-brain becomes the SoR.

Disk paths searched (per project):
  - New path (CCP-gtue+): ~/.claude/projects/<slug>/daily-briefs/
  - Legacy path (pre-CCP-gtue): <project.path>/.claude/daily-briefs/
Briefs found in the new path take precedence; duplicates by date are skipped.

Usage:
    # Preview what would be migrated
    python3 scripts/migrate-disk-briefs-to-open-brain.py

    # Run the migration
    python3 scripts/migrate-disk-briefs-to-open-brain.py --apply

    # Specific config
    python3 scripts/migrate-disk-briefs-to-open-brain.py --config ~/.claude/daily-brief.yml --apply

Output:
    Execution-result envelope (JSON) per core/contracts/execution-result.schema.json
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup: make orchestrate-brief helpers importable
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_CONFIG_SCRIPTS = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"

sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_CONFIG_SCRIPTS))

import importlib.util as _importlib_util

# Load orchestrate-brief.py for shared helpers
_ob_spec = _importlib_util.spec_from_file_location(
    "orchestrate_brief", _SCRIPTS_DIR / "orchestrate-brief.py"
)
_ob_mod = _importlib_util.module_from_spec(_ob_spec)  # type: ignore[arg-type]
_ob_spec.loader.exec_module(_ob_mod)  # type: ignore[union-attr]

import config as _cfg  # noqa: E402

_PRODUCER = "scripts/migrate-disk-briefs-to-open-brain.py"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI args for the migration script.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace.
    """
    p = argparse.ArgumentParser(
        description="Migrate disk daily-briefs into open-brain.",
        prog="migrate-disk-briefs",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml).",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Perform actual writes to open-brain. Default: dry-run only.",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Migrate only this project. Omit to migrate all configured projects.",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _discover_disk_briefs(
    config_path: Path,
    project_filter: str | None,
) -> list[dict[str, Any]]:
    """Find all disk brief files across configured projects.

    Args:
        config_path: Path to daily-brief.yml.
        project_filter: Optional project name to restrict discovery.

    Returns:
        List of dicts with keys: project_name, slug, date, path, text.
    """
    resolve_result = _cfg.resolve_project(project_filter, config_path)
    if resolve_result["status"] != "ok":
        return []

    briefs: list[dict[str, Any]] = []
    for p_dict in resolve_result["data"]["projects"]:
        project = _cfg.ProjectConfig.from_dict(p_dict)
        # Check new path (primary) first, then legacy path (backward compat)
        new_path = _cfg.briefs_dir(project)
        legacy_path = _cfg.legacy_briefs_dir(project)

        seen_dates: set[str] = set()
        for search_dir in [new_path, legacy_path]:
            if not search_dir.exists():
                continue
            for brief_file in sorted(search_dir.glob("*.md")):
                # Extract date from filename (YYYY-MM-DD.md)
                stem = brief_file.stem
                if len(stem) != 10 or stem.count("-") != 2:
                    continue  # Skip non-date filenames
                try:
                    year, month, day = stem.split("-")
                    if not (year.isdigit() and month.isdigit() and day.isdigit()):
                        continue
                except ValueError:
                    continue

                if stem in seen_dates:
                    continue  # Prefer new path (checked first)
                seen_dates.add(stem)

                try:
                    text = brief_file.read_text()
                except OSError:
                    continue

                briefs.append(
                    {
                        "project_name": project.name,
                        "slug": project.slug,
                        "date": stem,
                        "path": str(brief_file),
                        "text": text,
                    }
                )

    return briefs


# ---------------------------------------------------------------------------
# Open-brain write (idempotent)
# ---------------------------------------------------------------------------


def _migrate_brief(brief: dict[str, Any]) -> dict[str, Any]:
    """Post a single brief to open-brain idempotently.

    Args:
        brief: Dict with project_name, slug, date, text.

    Returns:
        Dict with status ("migrated" | "failed") and optional error message.
    """
    slug = brief["slug"]
    date = brief["date"]
    project_name = brief["project_name"]
    session_ref = _ob_mod.make_session_ref(slug, date)

    try:
        _ob_mod._save_to_open_brain(
            title=f"{project_name} — {date}",
            text=brief["text"],
            ob_type="daily_brief",
            project=slug,
            session_ref=session_ref,
            metadata={"source": "migrate-disk-briefs", "original_path": brief["path"]},
        )
        return {"status": "migrated", "session_ref": session_ref}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": str(exc), "session_ref": session_ref}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the migration script.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 = success, 1 = error).
    """
    args = parse_args(argv)

    # Discover briefs
    briefs = _discover_disk_briefs(args.config, args.project)

    if not briefs:
        result = {
            "status": "ok",
            "summary": "No disk briefs found to migrate.",
            "data": {
                "migrated": [],
                "failed": [],
                "dry_run": not args.apply,
                "total": 0,
            },
            "errors": [],
            "next_steps": [],
            "open_items": [],
            "meta": {
                "contract_version": "1",
                "producer": _PRODUCER,
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    if not args.apply:
        # Dry-run: classify briefs as "would_migrate" (not in OB) vs "already_in_ob" (found in OB)
        would_migrate: list[dict] = []
        already_in_ob: list[dict] = []
        for b in briefs:
            ob_text = _ob_mod._read_from_open_brain(b["slug"], b["date"])
            entry = {"project": b["project_name"], "date": b["date"], "path": b["path"]}
            if ob_text is not None:
                already_in_ob.append(entry)
            else:
                would_migrate.append(entry)
        result = {
            "status": "ok",
            "summary": (
                f"Dry-run: {len(would_migrate)} brief(s) would be migrated, "
                f"{len(already_in_ob)} already in OB. Use --apply to execute."
            ),
            "data": {
                "migrated": [],
                "failed": [],
                "dry_run": True,
                "total": len(briefs),
                "would_migrate": would_migrate,
                "already_in_ob": already_in_ob,
            },
            "errors": [],
            "next_steps": [
                "Run with --apply to migrate all listed briefs to open-brain."
            ],
            "open_items": [],
            "meta": {
                "contract_version": "1",
                "producer": _PRODUCER,
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    # Apply: migrate all briefs
    migrated: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for brief in briefs:
        outcome = _migrate_brief(brief)
        entry = {
            "project": brief["project_name"],
            "date": brief["date"],
            "session_ref": outcome.get("session_ref", ""),
        }
        if outcome["status"] == "migrated":
            migrated.append(entry)
        else:
            failed.append({**entry, "error": outcome.get("error", "unknown")})

    status = "ok" if not failed else ("warning" if migrated else "error")
    summary = (
        f"Migrated {len(migrated)} brief(s)"
        + (f", {len(failed)} failed" if failed else "")
        + "."
    )

    errors = [
        {"code": "write-failed", "message": f["error"], "context": f"{f['project']} {f['date']}"}
        for f in failed
    ]

    result = {
        "status": status,
        "summary": summary,
        "data": {
            "migrated": migrated,
            "failed": failed,
            "dry_run": False,
            "total": len(briefs),
        },
        "errors": errors,
        "next_steps": (
            ["Retry failed briefs or check open-brain credentials."] if failed else []
        ),
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": _PRODUCER,
        },
    }
    print(json.dumps(result, indent=2))
    return 0 if status in ("ok", "warning") else 1


if __name__ == "__main__":
    sys.exit(main())
