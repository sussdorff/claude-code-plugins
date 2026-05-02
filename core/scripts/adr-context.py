#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""
adr-context.py — Discover, inject, and verify ADR constraints for a bead.

Three subcommands:
  discover  — find ADRs in scope based on changed paths and bead description
  inject    — format relevant ADRs as a markdown block for implementer prompts
  verify    — re-discover ADRs from a diff range and check for violations

Output: execution-result envelope (core/contracts/execution-result.schema.json)

Usage:
  uv run core/scripts/adr-context.py discover --bead=<id> [--changed-paths=p1,p2] --output=json
  uv run core/scripts/adr-context.py inject --bead=<id> --output=markdown
  uv run core/scripts/adr-context.py verify --bead=<id> --diff=<git-range> --output=json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PRODUCER = "adr-context.py"
_CONTRACT_VERSION = "1"
_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_MAX_ADR_BLOCK_CHARS = 2048


# ---------------------------------------------------------------------------
# Execution-result envelope
# ---------------------------------------------------------------------------


def _envelope(
    status: str,
    summary: str,
    data: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    next_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Wrap a result payload in the canonical execution-result envelope."""
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
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "schema": _SCHEMA_PATH,
        },
    }


# ---------------------------------------------------------------------------
# ADR frontmatter parsing
# ---------------------------------------------------------------------------


def parse_adr_frontmatter(adr_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from an ADR markdown file.

    Returns a dict with keys: id, status, date, applies_to, prohibits,
    decision_summary, path — or None if no frontmatter is found.
    """
    text = adr_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    # Extract the YAML block between the first --- delimiters
    end = text.find("---", 3)
    if end == -1:
        return None
    yaml_block = text[3:end].strip()
    try:
        meta: dict[str, Any] = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        return None
    if "id" not in meta:
        return None
    meta["path"] = str(adr_path)
    meta.setdefault("applies_to", [])
    meta.setdefault("prohibits", [])
    meta.setdefault("decision_summary", "")
    return meta


def _load_adrs(adr_dir: Path) -> list[dict[str, Any]]:
    """Walk adr_dir and return all successfully parsed ADR frontmatter dicts."""
    adrs: list[dict[str, Any]] = []
    for md_file in sorted(adr_dir.glob("*.md")):
        parsed = parse_adr_frontmatter(md_file)
        if parsed is not None:
            adrs.append(parsed)
    return adrs


# ---------------------------------------------------------------------------
# Path glob matching
# ---------------------------------------------------------------------------


def _matches_glob(path: str, pattern: str) -> bool:
    """Return True if path matches the given glob pattern.

    Uses PurePosixPath.match which is path-segment-aware (treats '/' as a
    boundary, unlike fnmatch.fnmatch). Supports '**' glob patterns natively
    in Python 3.12+ (which we target).
    """
    return PurePosixPath(path).match(pattern)


def _path_matches_adr(changed_paths: list[str], applies_to: list[str]) -> bool:
    """Return True if any changed path matches any applies_to glob."""
    for path in changed_paths:
        for pattern in applies_to:
            if _matches_glob(path, pattern):
                return True
    return False


# ---------------------------------------------------------------------------
# Bead description fetching
# ---------------------------------------------------------------------------


def _fetch_bead_description(bead_id: str) -> str | None:
    """Fetch bead description text via `bd show <id>`.

    Returns the output string, or None on any failure.
    """
    try:
        result = subprocess.run(
            ["bd", "show", bead_id],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# Core logic: discover
# ---------------------------------------------------------------------------


def discover_adrs(
    *,
    adr_dir: Path,
    changed_paths: list[str],
    bead_description_override: str | None,
    bead_id: str | None = None,
    _adrs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Discover ADRs in scope for a bead.

    Args:
        adr_dir: Directory containing ADR markdown files.
        changed_paths: List of file paths that changed (from git diff or CLI).
        bead_description_override: Pre-fetched bead description (for testing).
            If None and bead_id is given, attempts to call `bd show <bead_id>`.
        bead_id: Bead identifier used to fetch description when override is None.
        _adrs: Optional pre-loaded ADR list (avoids re-reading disk when the
            caller has already called _load_adrs). Internal use only.

    Returns:
        List of ADR dicts with keys: id, path, decision_summary, match_reason.
    """
    adrs = _adrs if _adrs is not None else _load_adrs(adr_dir)

    # Determine bead description text for text-based matching
    if bead_description_override is not None:
        bead_text: str | None = bead_description_override
    elif bead_id is not None:
        bead_text = _fetch_bead_description(bead_id)
    else:
        bead_text = None

    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []

    for adr in adrs:
        adr_id: str = adr["id"]
        match_reason: str | None = None

        # Path-based matching
        if changed_paths and _path_matches_adr(changed_paths, adr["applies_to"]):
            match_reason = "path"

        # Text-based matching (bead description references the ADR id)
        if bead_text and re.search(rf"\b{re.escape(adr_id)}\b", bead_text, re.IGNORECASE):
            if match_reason is None:
                match_reason = "text"
            else:
                match_reason = "path+text"

        if match_reason is not None and adr_id not in seen_ids:
            seen_ids.add(adr_id)
            results.append(
                {
                    "id": adr_id,
                    "path": adr["path"],
                    "decision_summary": adr["decision_summary"],
                    "match_reason": match_reason,
                }
            )

    return results


def discover_adrs_envelope(
    *,
    adr_dir: Path,
    changed_paths: list[str],
    bead_description_override: str | None,
    bead_id: str | None = None,
) -> dict[str, Any]:
    """Run discover and return execution-result envelope."""
    adrs_in_scope = discover_adrs(
        adr_dir=adr_dir,
        changed_paths=changed_paths,
        bead_description_override=bead_description_override,
        bead_id=bead_id,
    )
    count = len(adrs_in_scope)
    return _envelope(
        status="ok",
        summary=f"Discovered {count} ADR(s) in scope.",
        data={"adrs_in_scope": adrs_in_scope},
    )


# ---------------------------------------------------------------------------
# Core logic: inject
# ---------------------------------------------------------------------------


def _format_adr_block(adr_meta: dict[str, Any], adr_id: str) -> str:
    """Format a single ADR as a markdown section, truncated to _MAX_ADR_BLOCK_CHARS."""
    prohibitions = "\n".join(f"- {p}" for p in adr_meta.get("prohibits", []))
    block = (
        f"### {adr_id} — {adr_meta['decision_summary']}\n"
        f"Prohibits:\n{prohibitions}\n"
        f"Read: {adr_meta['path']}\n"
    )
    if len(block) > _MAX_ADR_BLOCK_CHARS:
        block = block[: _MAX_ADR_BLOCK_CHARS - 3] + "..."
    return block


def inject_adrs_envelope(
    *,
    adr_dir: Path,
    changed_paths: list[str],
    bead_description_override: str | None,
    bead_id: str | None = None,
) -> dict[str, Any]:
    """Discover ADRs and format them as an injected markdown block.

    Returns execution-result envelope with data.markdown.
    """
    # Load ADR metadata once — reused for both discovery and formatting.
    all_adrs_list = _load_adrs(adr_dir)
    all_adrs = {a["id"]: a for a in all_adrs_list}

    adrs_in_scope = discover_adrs(
        adr_dir=adr_dir,
        changed_paths=changed_paths,
        bead_description_override=bead_description_override,
        bead_id=bead_id,
        _adrs=all_adrs_list,
    )

    if not adrs_in_scope:
        markdown = "No ADRs in scope for this bead."
        summary = "No ADRs in scope."
    else:
        # Use already-loaded full metadata for each ADR to format prohibitions
        sections: list[str] = ["## ADR Constraints (mandatory)\n"]
        for entry in adrs_in_scope:
            adr_id = entry["id"]
            meta = all_adrs.get(adr_id, {"decision_summary": entry["decision_summary"], "prohibits": [], "path": entry["path"]})
            sections.append(_format_adr_block(meta, adr_id))
        markdown = "\n".join(sections)
        summary = f"Injected {len(adrs_in_scope)} ADR constraint(s)."

    return _envelope(
        status="ok",
        summary=summary,
        data={"markdown": markdown},
    )


# ---------------------------------------------------------------------------
# Core logic: verify
# ---------------------------------------------------------------------------


def verify_adrs_envelope(
    *,
    adr_dir: Path,
    changed_paths: list[str],
    diff_text: str,
    bead_description_override: str | None,
    bead_id: str | None = None,
) -> dict[str, Any]:
    """Re-discover ADRs from diff and check prohibitions against diff_text.

    Does NOT accept caller-provided adrs_in_scope — always re-discovers.

    Returns execution-result envelope with:
        data.verdict: "VERIFIED" or "DISPUTED"
        data.discovered_adrs: list of {id, path, decision_summary}
        data.violations: list of {adr, rule, evidence, fixability}
    """
    # Load once — reused for both discovery and violation checking.
    all_adrs_list = _load_adrs(adr_dir)
    all_adrs = {a["id"]: a for a in all_adrs_list}

    # Always re-discover from changed_paths (ignores caller-supplied provenance)
    adrs_in_scope = discover_adrs(
        adr_dir=adr_dir,
        changed_paths=changed_paths,
        bead_description_override=bead_description_override,
        bead_id=bead_id,
        _adrs=all_adrs_list,
    )

    discovered_adrs: list[dict[str, Any]] = [
        {"id": a["id"], "path": a["path"], "decision_summary": a["decision_summary"]}
        for a in adrs_in_scope
    ]

    violations: list[dict[str, Any]] = []
    diff_lower = diff_text.lower()

    for entry in adrs_in_scope:
        adr_id = entry["id"]
        meta = all_adrs.get(adr_id, {})
        prohibits: list[str] = meta.get("prohibits", [])
        for rule in prohibits:
            # NOTE: violation detection uses prohibition prose as a heuristic.
            # Only catches violations where the diff contains the exact prohibition
            # text (e.g. as a comment). For structural violation detection, extend
            # ADR frontmatter with a `pattern:` field and check that instead.
            key = rule[:60].lower()
            if key and key in diff_lower:
                violations.append(
                    {
                        "adr": adr_id,
                        "rule": rule,
                        "evidence": f"Prohibited pattern found in diff: {rule[:80]}",
                        "fixability": "human",
                    }
                )

    verdict = "DISPUTED" if violations else "VERIFIED"
    status = "warning" if violations else "ok"
    summary = (
        f"Verification {verdict}: {len(violations)} violation(s) found across "
        f"{len(discovered_adrs)} discovered ADR(s)."
    )

    return _envelope(
        status=status,
        summary=summary,
        data={
            "verdict": verdict,
            "discovered_adrs": discovered_adrs,
            "violations": violations,
        },
    )


# ---------------------------------------------------------------------------
# Git helpers for CLI mode
# ---------------------------------------------------------------------------


def _git_changed_paths(diff_range: str | None = None) -> list[str]:
    """Return list of changed file paths from git diff.

    If diff_range is None, uses 'main...HEAD'.
    """
    range_arg = diff_range or "main...HEAD"
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", range_arg],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return [p for p in result.stdout.splitlines() if p.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return []


def _git_diff_text(diff_range: str) -> str:
    """Return full git diff text for the given range."""
    try:
        result = subprocess.run(
            ["git", "diff", diff_range],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return ""


def _find_adr_dir() -> Path | None:
    """Locate docs/adr/ relative to cwd or repo root."""
    candidates = [
        Path("docs/adr"),
        Path(".") / "docs" / "adr",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="ADR context helper for bead orchestration")
    sub = parser.add_subparsers(dest="command", required=True)

    # discover
    p_discover = sub.add_parser("discover", help="Discover ADRs in scope")
    p_discover.add_argument("--bead", default=None, help="Bead ID for text-matching")
    p_discover.add_argument("--changed-paths", default=None, help="Comma-separated list of changed paths")
    p_discover.add_argument("--output", default="json", choices=["json", "paths"])
    p_discover.add_argument("--adr-dir", default=None, help="Path to ADR directory (default: docs/adr/)")

    # inject
    p_inject = sub.add_parser("inject", help="Inject ADR constraints as markdown")
    p_inject.add_argument("--bead", default=None, help="Bead ID")
    p_inject.add_argument("--changed-paths", default=None, help="Comma-separated list of changed paths")
    p_inject.add_argument("--output", default="markdown", choices=["markdown", "json"])
    p_inject.add_argument("--adr-dir", default=None, help="Path to ADR directory")

    # verify
    p_verify = sub.add_parser("verify", help="Verify ADR compliance against a diff")
    p_verify.add_argument("--bead", default=None, help="Bead ID")
    p_verify.add_argument("--diff", default="main...HEAD", help="Git diff range")
    p_verify.add_argument("--output", default="json", choices=["json"])
    p_verify.add_argument("--adr-dir", default=None, help="Path to ADR directory")

    args = parser.parse_args()

    # Resolve ADR directory
    if hasattr(args, "adr_dir") and args.adr_dir:
        adr_dir = Path(args.adr_dir)
    else:
        adr_dir = _find_adr_dir()

    if adr_dir is None or not adr_dir.is_dir():
        result = _envelope(
            status="error",
            summary="ADR directory not found. Expected docs/adr/.",
            data={"adrs_in_scope": []},
            errors=[{"code": "ADR_DIR_NOT_FOUND", "message": "docs/adr/ not found"}],
        )
        print(json.dumps(result, indent=2))
        return

    # Resolve changed paths from CLI or git
    changed_paths: list[str] = []
    if hasattr(args, "changed_paths") and args.changed_paths:
        changed_paths = [p.strip() for p in args.changed_paths.split(",") if p.strip()]
    elif args.command in ("discover", "inject"):
        changed_paths = _git_changed_paths()

    bead_id: str | None = getattr(args, "bead", None)

    if args.command == "discover":
        result = discover_adrs_envelope(
            adr_dir=adr_dir,
            changed_paths=changed_paths,
            bead_description_override=None,
            bead_id=bead_id,
        )
        if args.output == "paths":
            # One ADR file path per line — no JSON wrapper, for shell variable capture.
            for entry in result["data"]["adrs_in_scope"]:
                print(entry["path"])
        else:
            print(json.dumps(result, indent=2))

    elif args.command == "inject":
        result = inject_adrs_envelope(
            adr_dir=adr_dir,
            changed_paths=changed_paths,
            bead_description_override=None,
            bead_id=bead_id,
        )
        if args.output == "markdown":
            print(result["data"]["markdown"])
        else:
            print(json.dumps(result, indent=2))

    elif args.command == "verify":
        diff_range: str = args.diff
        changed_paths = _git_changed_paths(diff_range)
        diff_text = _git_diff_text(diff_range)
        result = verify_adrs_envelope(
            adr_dir=adr_dir,
            changed_paths=changed_paths,
            diff_text=diff_text,
            bead_description_override=None,
            bead_id=bead_id,
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
