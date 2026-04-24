#!/usr/bin/env python3
"""
capability-extractor.py — Daily-brief capability signal parser.

Parses closed bead titles/descriptions for capability signals and session
summaries for What's New blocks. Emits short present-tense capability sentences
grounded in source data.

Input: execution-result envelope from query-sources.py (via --stdin or re-run)
Output: execution-result envelope with data.capabilities[] list

Usage:
    # Pipe from query-sources.py
    python3 scripts/query-sources.py --project claude-code-plugins --date 2026-04-23 | \
        python3 scripts/capability-extractor.py --stdin

    # Run standalone (calls query-sources internally)
    python3 scripts/capability-extractor.py --project claude-code-plugins --date 2026-04-23

    # Run standalone with config override
    python3 scripts/capability-extractor.py --project mira --date 2026-04-23 \
        --config ~/.claude/daily-brief.yml
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
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

_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_PRODUCER = "scripts/capability-extractor.py"
_CONTRACT_VERSION = "1"

# Capability signal keywords in bead titles/descriptions
_CAPABILITY_KEYWORDS = frozenset([
    "now", "new gate", "now verified", "now possible", "unblocks", "[feat]", "[qg]",
])

# Session summary "What's New" line prefixes
_WHATS_NEW_PREFIXES = ("New:", "Fixed:", "Internal:")


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------


def _envelope(
    status: str,
    summary: str,
    data: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    next_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a conforming execution-result envelope."""
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    return {
        "status": status,
        "summary": summary,
        "data": data,
        "errors": errors or [],
        "next_steps": next_steps or [],
        "open_items": [],
        "meta": {
            "contract_version": _CONTRACT_VERSION,
            "producer": _PRODUCER,
            "generated_at": now,
            "schema": _SCHEMA_PATH,
        },
    }


# ---------------------------------------------------------------------------
# Capability signal detection
# ---------------------------------------------------------------------------


def _has_capability_signal(text: str) -> bool:
    """Return True if text contains any capability signal keyword (case-insensitive)."""
    lower = text.lower()
    return any(kw in lower for kw in _CAPABILITY_KEYWORDS)


def _bead_type_label(bead: dict[str, Any]) -> str:
    """Return a short type label for a bead: [FEAT], [task], [bug], etc."""
    issue_type = bead.get("issue_type") or bead.get("type") or ""
    if issue_type.lower() == "feature":
        return "[FEAT]"
    if issue_type.lower() == "bug":
        return "[bug]"
    return f"[{issue_type}]" if issue_type else "[task]"


def _extract_from_bead(bead: dict[str, Any]) -> str | None:
    """Extract a capability sentence from a closed bead if it has a signal.

    Returns a present-tense capability sentence, or None if no signal found.
    Both feature AND task beads qualify.
    """
    bead_id = bead.get("id", "")
    title = bead.get("title", "")
    description = bead.get("description", "") or ""

    # Check title and description for capability signals
    if not (_has_capability_signal(title) or _has_capability_signal(description)):
        return None

    type_label = _bead_type_label(bead)

    # Build capability sentence from bead title
    # Strip common prefixes like [FEAT], [REFACTOR] from title for cleaner output
    clean_title = re.sub(r"^\[(?:FEAT|BUG|REFACTOR|CHORE|TASK)\]\s*", "", title, flags=re.IGNORECASE).strip()

    # Check commits linked to this bead for additional context
    commits = bead.get("commits", [])
    commit_hint = ""
    if commits:
        commit_hint = f" ({len(commits)} commit{'s' if len(commits) > 1 else ''})"

    return f"{bead_id} {type_label} geschlossen: {clean_title}{commit_hint}"


def _extract_from_session(session: dict[str, Any]) -> list[str]:
    """Extract capability sentences from session summary What's New blocks.

    Parses lines starting with New:, Fixed:, Internal: from session text.
    Returns list of present-tense capability sentences.
    """
    capabilities: list[str] = []

    text = session.get("text", "") or ""
    title = session.get("title", "") or ""
    session_ref = session.get("session_ref", "") or ""

    # Look for What's New section or direct New:/Fixed:/Internal: lines
    in_whats_new = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.search(r"what.s new|was ist neu|neue.*features?", stripped, re.IGNORECASE):
            in_whats_new = True
            continue
        if stripped.startswith("##") and in_whats_new:
            # New section starts — exit What's New context
            in_whats_new = False
        for prefix in _WHATS_NEW_PREFIXES:
            if stripped.startswith(prefix):
                content = stripped[len(prefix):].strip()
                if content:
                    category = prefix.rstrip(":")
                    ref = session_ref or title or "session"
                    capabilities.append(f"{category} [{ref}]: {content}")
                break

    return capabilities


def _scan_docs_for_new_files(
    project_path: Path,
    date: str,
    docs_dirs: list[str] | None = None,
) -> list[str]:
    """For polaris-like projects: scan docs/ and docs/adr/ for files created on target date.

    Returns list of capability sentences for newly created docs.
    """
    capabilities: list[str] = []
    if not docs_dirs:
        docs_dirs = ["docs", "docs/adr"]

    try:
        target_date = datetime.date.fromisoformat(date)
    except ValueError:
        return []

    for docs_subdir in docs_dirs:
        docs_path = project_path / docs_subdir
        if not docs_path.is_dir():
            continue
        for md_file in docs_path.glob("*.md"):
            try:
                stat = md_file.stat()
                file_date = datetime.date.fromtimestamp(stat.st_ctime)
                if file_date == target_date:
                    capabilities.append(
                        f"Neue Dokumentation erstellt: {docs_subdir}/{md_file.name}"
                    )
            except OSError:
                continue

    return capabilities


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def extract_capabilities(
    source_envelope: dict[str, Any],
    project_path: Path | None = None,
    scan_docs: bool = False,
) -> list[str]:
    """Extract capability sentences from a query-sources.py envelope.

    Args:
        source_envelope: The execution-result envelope from query-sources.py.
        project_path: Optional path to project root (used for docs scanning).
        scan_docs: Whether to scan docs/ for new files (for polaris project).

    Returns:
        List of present-tense capability sentences grounded in source data.
    """
    data = source_envelope.get("data", {})
    if not isinstance(data, dict):
        return []

    capabilities: list[str] = []
    date = data.get("date", "")

    # 1. Extract from closed beads (both feature AND task beads)
    for bead in data.get("closed_beads", []):
        sentence = _extract_from_bead(bead)
        if sentence:
            capabilities.append(sentence)

    # 2. Extract from session summaries (What's New blocks)
    for session in data.get("sessions", []):
        session_caps = _extract_from_session(session)
        capabilities.extend(session_caps)

    # 3. For polaris-like projects: scan docs/
    if scan_docs and project_path and date:
        docs_caps = _scan_docs_for_new_files(project_path, date)
        capabilities.extend(docs_caps)

    return capabilities


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract capability signals from daily-brief data envelope."
    )
    source_group = p.add_mutually_exclusive_group()
    source_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read query-sources.py JSON envelope from stdin",
    )
    source_group.add_argument(
        "--project",
        help="Project name from daily-brief.yml (runs query-sources internally)",
    )
    p.add_argument(
        "--date",
        help="Date in YYYY-MM-DD format (required unless --stdin)",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml)",
    )
    p.add_argument(
        "--scan-docs",
        action="store_true",
        help="Scan docs/ and docs/adr/ for files created on target date (polaris)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.stdin:
        # Read envelope from stdin
        try:
            source_envelope = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            result = _envelope(
                status="error",
                summary=f"Failed to parse JSON from stdin: {exc}",
                data={"capabilities": []},
                errors=[{
                    "code": "invalid-json-input",
                    "message": str(exc),
                    "retryable": False,
                    "suggested_fix": "Ensure stdin contains valid JSON from query-sources.py",
                }],
            )
            print(json.dumps(result, indent=2))
            return 0
    elif args.project:
        if not args.date:
            parser.error("--date is required when using --project")

        # Validate date
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            result = _envelope(
                status="error",
                summary=f"Invalid date format: '{args.date}'. Expected YYYY-MM-DD.",
                data={"capabilities": []},
                errors=[{
                    "code": "invalid-date",
                    "message": f"Date '{args.date}' is not a valid ISO date",
                    "retryable": False,
                    "suggested_fix": "Use YYYY-MM-DD format, e.g. 2026-04-23",
                }],
            )
            print(json.dumps(result, indent=2))
            return 0

        # Run query-sources to get the envelope
        import subprocess

        qs_script = Path(__file__).parent / "query-sources.py"
        cmd = [
            sys.executable, str(qs_script),
            "--project", args.project,
            "--date", args.date,
            "--config", str(args.config),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
        if proc.returncode != 0:
            result = _envelope(
                status="error",
                summary=f"query-sources.py failed (rc={proc.returncode})",
                data={"capabilities": []},
                errors=[{
                    "code": "query-sources-failed",
                    "message": proc.stderr.strip() or "unknown error",
                    "retryable": True,
                }],
            )
            print(json.dumps(result, indent=2))
            return 0
        try:
            source_envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            result = _envelope(
                status="error",
                summary=f"Failed to parse query-sources.py output: {exc}",
                data={"capabilities": []},
                errors=[{
                    "code": "invalid-json-from-query-sources",
                    "message": str(exc),
                    "retryable": False,
                }],
            )
            print(json.dumps(result, indent=2))
            return 0
    else:
        parser.error("Either --stdin or --project is required")
        return 1  # unreachable but satisfies type checker

    # Resolve project path for docs scanning
    project_path: Path | None = None
    if args.scan_docs:
        project_name = source_envelope.get("data", {}).get("project", "")
        if project_name:
            resolve_result = _cfg.resolve_project(project_name, config_path=args.config)
            if resolve_result["status"] == "ok" and resolve_result["data"]["projects"]:
                proj_dict = resolve_result["data"]["projects"][0]
                project_path = Path(proj_dict.get("path", ""))

    # Extract capabilities
    capabilities = extract_capabilities(
        source_envelope=source_envelope,
        project_path=project_path,
        scan_docs=args.scan_docs,
    )

    project = source_envelope.get("data", {}).get("project", "unknown")
    date = source_envelope.get("data", {}).get("date", "unknown")

    result = _envelope(
        status="ok",
        summary=f"Extracted {len(capabilities)} capability signal(s) for {project} on {date}",
        data={
            "project": project,
            "date": date,
            "capabilities": capabilities,
        },
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
