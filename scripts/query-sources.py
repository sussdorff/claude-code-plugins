#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "httpx>=0.27",
# ]
# ///
"""
query-sources.py — Daily-brief data aggregator.

Collects data from three sources for a given project + date window:
  1. open-brain (MCP JSON-RPC via httpx)
  2. beads (bd CLI)
  3. git log

Emits a single JSON object conforming to core/contracts/execution-result.schema.json.
Exit 0 always — branching is via JSON status field.

Usage:
    python3 scripts/query-sources.py --project claude-code-plugins --date 2026-04-23
    python3 scripts/query-sources.py --project mira --date 2026-04-23 \\
        --config ~/.claude/daily-brief.yml

NOTE: query_sources() is a sync-only entrypoint. It uses asyncio.run() internally
to drive async open-brain calls. It CANNOT be called from within an already-running
async event loop — doing so raises RuntimeError("This event loop is already running").
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Path setup: make config.py importable when invoked from scripts/
# We use sys.path.insert here because config.py is a sibling module that
# may be imported in environments where uv creates separate venvs per script.
# Using importlib.util would break cross-venv imports (config.py imports yaml).
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_CONFIG_SCRIPTS = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_CONFIG_SCRIPTS))

import config as _cfg  # noqa: E402  (after sys.path manipulation)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_PRODUCER = "scripts/query-sources.py"
_CONTRACT_VERSION = "1"
_BEAD_ID_RE = re.compile(r"\b(CCP-[A-Za-z0-9]+)\b")
_REVERT_RE = re.compile(r'^Revert[\s"]')
_FOLLOWUP_PREFIXES = ("Decide:", "Need input:", "Follow-up:")
_TZ_BERLIN = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------------------------
# CommandRunner DI
# ---------------------------------------------------------------------------


class CommandRunner:
    """Protocol for subprocess execution (injectable for testing)."""

    def run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise NotImplementedError


class RealCommandRunner(CommandRunner):
    """Production implementation — calls subprocess.run()."""

    def run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        defaults: dict[str, Any] = {
            "capture_output": True,
            "text": True,
        }
        defaults.update(kwargs)
        return subprocess.run(cmd, **defaults)  # noqa: S603


class MockCommandRunner(CommandRunner):
    """Test double — matches command by prefix and returns canned stdout."""

    def __init__(
        self,
        responses: dict[str, str],
        *,
        git_fail: bool = False,
        bd_fail: bool = False,
    ) -> None:
        self._responses = responses
        self._git_fail = git_fail
        self._bd_fail = bd_fail

    def run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        # Strip the "--db <path>" pair from bd invocations before matching so
        # tests can be written in terms of the logical command ("bd list ...")
        # without caring which database it was scoped to. Production code
        # always passes the flag; the test double ignores it.
        match_cmd = cmd
        if cmd and cmd[0] == "bd" and len(cmd) >= 3 and cmd[1] == "--db":
            match_cmd = [cmd[0]] + cmd[3:]

        cmd_str = " ".join(match_cmd)

        # Check for failure modes first
        if self._git_fail and cmd and cmd[0] == "git":
            return subprocess.CompletedProcess(
                args=cmd, returncode=128, stdout="", stderr="fatal: not a git repository"
            )
        if self._bd_fail and cmd and cmd[0] == "bd":
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr="bd: command failed"
            )

        # Match by longest matching prefix
        best_key = None
        best_len = -1
        for key in self._responses:
            if cmd_str.startswith(key) and len(key) > best_len:
                best_key = key
                best_len = len(key)

        if best_key is not None:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout=self._responses[best_key], stderr=""
            )

        # Fall through: return empty success
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")


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


def _warning_entry(source: str, reason: str, project: str, date: str) -> dict[str, Any]:
    return {"source": source, "reason": reason, "project": project, "date": date}


def _empty_data_fields(project: str, date: str) -> dict[str, Any]:
    """Return a dict with all required data fields set to their empty defaults.

    Use this in both error paths and the CLI invalid-date path to prevent drift
    when new fields are added.
    """
    return {
        "project": project,
        "date": date,
        "sessions": [],
        "closed_beads": [],
        "open_beads": [],
        "ready_beads": [],
        "blocked_beads": [],
        "commits": [],
        "learnings": [],
        "decisions": [],
        "decision_requests": [],
        "followups": [],
        "rework_signals": [],
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# Date window helpers
# ---------------------------------------------------------------------------


def _date_window(date_str: str) -> tuple[datetime.datetime, datetime.datetime]:
    """Return (start, end) as timezone-aware datetimes (Europe/Berlin midnight-to-midnight)."""
    d = datetime.date.fromisoformat(date_str)
    start = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_TZ_BERLIN)
    end = start + datetime.timedelta(days=1)
    return start, end


# ---------------------------------------------------------------------------
# Git data collection
# ---------------------------------------------------------------------------


def _collect_git(
    project: str,
    date: str,
    repo_path: Path,
    runner: CommandRunner,
    warnings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect git commits in the date window.

    Returns:
        (all_commits, rework_signals) where all_commits is every commit
        parsed and rework_signals are revert commits.
        Callers must merge bead-linked commits separately.
    """
    start, end = _date_window(date)
    since = start.isoformat()
    until = end.isoformat()

    git_fmt = "%H|%s|%an|%ad"
    cmd = [
        "git", "-C", str(repo_path),
        "log",
        f"--since={since}",
        f"--until={until}",
        f"--pretty=format:{git_fmt}",
        "--date=iso",
    ]
    result = runner.run(cmd)

    if result.returncode != 0:
        warnings.append(_warning_entry(
            source="git",
            reason=f"git log failed (rc={result.returncode}): {result.stderr.strip() or 'unknown error'}",
            project=project,
            date=date,
        ))
        return [], []

    commits: list[dict[str, Any]] = []
    rework_signals: list[dict[str, Any]] = []

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        sha, subject, author, authored_at = parts
        commit = {
            "sha": sha,
            "subject": subject,
            "author": author,
            "authored_at": authored_at,
        }
        if _REVERT_RE.match(subject):
            rework_signals.append({
                "type": "revert_commit",
                "sha": sha,
                "subject": subject,
                "author": author,
                "authored_at": authored_at,
            })
        else:
            commits.append(commit)

    return commits, rework_signals


# ---------------------------------------------------------------------------
# Beads data collection
# ---------------------------------------------------------------------------


def _run_bd(
    runner: CommandRunner,
    args: list[str],
    project: str,
    date: str,
    warnings: list[dict[str, Any]],
    warn_source: str = "beads",
    warn_reason_prefix: str = "",
    db_flag: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Run a bd command and return parsed JSON list.

    On non-zero exit or unparseable output, appends a warning and returns [].
    Never swallows errors silently (AK #5).

    Args:
        db_flag: Optional ``["--db", "<path>"]`` prefix to scope bd at a specific
            database. When omitted, bd runs against whatever DB it resolves from
            the caller's cwd — which is NOT the intended project for cross-project
            daily briefs. Callers should pass a db_flag derived from the resolved
            project path.
    """
    cmd = ["bd"] + (db_flag or []) + args
    result = runner.run(cmd)
    if result.returncode != 0:
        reason = warn_reason_prefix or f"bd {' '.join(args)} failed"
        warnings.append(_warning_entry(
            source=warn_source,
            reason=f"{reason} (rc={result.returncode}): {result.stderr.strip() or 'unknown error'}",
            project=project,
            date=date,
        ))
        return []
    try:
        data = json.loads(result.stdout.strip() or "[]")
        if isinstance(data, list):
            return data
        warnings.append(_warning_entry(
            source=warn_source,
            reason=f"bd {' '.join(args)} returned non-list JSON: {type(data).__name__}",
            project=project,
            date=date,
        ))
        return []
    except json.JSONDecodeError as exc:
        warnings.append(_warning_entry(
            source=warn_source,
            reason=f"bd {' '.join(args)} returned non-JSON output: {exc}",
            project=project,
            date=date,
        ))
        return []


def _detect_reopens(
    open_beads: list[dict[str, Any]],
    in_progress_beads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect reopened beads.

    A reopen event is a bead that is currently open or in_progress AND
    has a non-None closed_at field (meaning it was previously closed).

    Args:
        open_beads: Beads with status=open from bd CLI.
        in_progress_beads: Beads with status=in_progress from bd CLI.

    Returns:
        List of rework_signal dicts with type="reopen_event".
    """
    reopen_signals: list[dict[str, Any]] = []
    for bead in open_beads + in_progress_beads:
        if bead.get("closed_at") is not None:
            reopen_signals.append({
                "type": "reopen_event",
                "bead_id": bead.get("id"),
                "title": bead.get("title"),
                "status": bead.get("status"),
                "date": bead.get("closed_at"),
            })
    return reopen_signals


def _resolve_bd_db_flag(project_path: Path) -> list[str] | None:
    """Return ``["--db", "<db_path>"]`` if a beads DB exists for the project.

    Looks in ``<project_path>/.beads/*.db`` and picks the first match. Returns
    ``None`` when no DB is present — callers should then treat beads as
    unavailable (no error, just empty results).
    """
    beads_dir = project_path / ".beads"
    if not beads_dir.is_dir():
        return None
    db_files = sorted(beads_dir.glob("*.db"))
    if not db_files:
        return None
    return ["--db", str(db_files[0])]


def _collect_beads(
    project: str,
    date: str,
    runner: CommandRunner,
    warnings: list[dict[str, Any]],
    db_flag: list[str] | None = None,
) -> dict[str, Any]:
    """Collect all bead data.

    Args:
        db_flag: Optional ``["--db", "<path>"]`` prefix scoping bd at a specific
            database. Without it, bd resolves the DB from cwd, which leaks beads
            from whatever repo invoked the script. See ``_resolve_bd_db_flag``.

    Returns dict with keys:
        closed_beads, open_beads, ready_beads, blocked_beads,
        decision_requests, rework_signals (supersede + reopen events)
    """
    start, _end = _date_window(date)
    date_str = start.date().isoformat()
    next_date_str = (start.date() + datetime.timedelta(days=1)).isoformat()

    def _bd(args: list[str]) -> list[dict[str, Any]]:
        return _run_bd(runner, args, project, date, warnings, db_flag=db_flag)

    # Query closed beads with date filter.
    # On failure we DO NOT fall back to an unfiltered ``bd list --status=closed``
    # — that would silently pollute a single-day brief with historical closed
    # work. Instead we emit a warning and return an empty list so the caller
    # can flag the missing data.
    filtered_args = [
        "list",
        "--status=closed",
        f"--closed-after={date_str}",
        f"--closed-before={next_date_str}",
        "--json",
    ]
    filtered_cmd = ["bd"] + (db_flag or []) + filtered_args
    filtered_result = runner.run(filtered_cmd)
    closed_beads: list[dict[str, Any]] = []
    if filtered_result.returncode != 0:
        warnings.append(_warning_entry(
            source="beads",
            reason=(
                f"bd list --status=closed (date-filtered) failed "
                f"(rc={filtered_result.returncode}): "
                f"{filtered_result.stderr.strip() or 'unknown error'}"
            ),
            project=project,
            date=date,
        ))
    else:
        try:
            raw = json.loads(filtered_result.stdout.strip() or "[]")
            if isinstance(raw, list):
                closed_beads = raw
            else:
                warnings.append(_warning_entry(
                    source="beads",
                    reason=f"bd list --status=closed returned non-list JSON: {type(raw).__name__}",
                    project=project,
                    date=date,
                ))
        except json.JSONDecodeError as exc:
            warnings.append(_warning_entry(
                source="beads",
                reason=f"bd list --status=closed returned non-JSON output: {exc}",
                project=project,
                date=date,
            ))

    open_beads = _bd(["list", "--status=open", "--json"])
    in_progress_beads = _bd(["list", "--status=in_progress", "--json"])
    ready_beads = _bd(["ready", "--json"])
    blocked_beads = _bd(["blocked", "--json"])
    decision_requests = _bd(["human", "list", "--json"])

    # Detect supersede events in closed beads
    rework_signals: list[dict[str, Any]] = []
    for bead in closed_beads:
        close_reason = str(bead.get("close_reason", "")).lower()
        if "superseded" in close_reason:
            rework_signals.append({
                "type": "supersede_event",
                "bead_id": bead.get("id"),
                "title": bead.get("title"),
                "close_reason": bead.get("close_reason"),
                "closed_at": bead.get("closed_at"),
            })

    # Detect reopen events: beads currently open or in_progress that were previously closed.
    rework_signals.extend(_detect_reopens(open_beads, in_progress_beads))

    return {
        "closed_beads": closed_beads,
        "open_beads": open_beads,
        "ready_beads": ready_beads,
        "blocked_beads": blocked_beads,
        "decision_requests": decision_requests,
        "rework_signals": rework_signals,
    }


# ---------------------------------------------------------------------------
# Open-brain data collection
# ---------------------------------------------------------------------------


def _extract_followups(content: str) -> list[dict[str, Any]]:
    """Extract follow-up items from debrief content."""
    followups = []
    for line in content.splitlines():
        line = line.strip()
        for prefix in _FOLLOWUP_PREFIXES:
            if line.startswith(prefix):
                followups.append({
                    "type": prefix.rstrip(":"),
                    "text": line[len(prefix):].strip(),
                    "raw_line": line,
                })
                break
    return followups


async def _collect_open_brain(
    project: str,
    date: str,
    ob_client: Any,
    slug: str,
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Query open-brain for session, learning, and decision entries.

    Returns dict with keys: sessions, learnings, decisions, followups.
    Only decisions with metadata.status == "pending" are included in decisions[].
    Malformed individual entries are skipped with a warning (AK #5).
    """
    start, end = _date_window(date)

    try:
        entries = await ob_client.search(
            type_filter=["session_summary", "debrief", "learning", "decision"],
            project=slug,
            date_start=start.isoformat(),
            date_end=end.isoformat(),
        )
    except Exception as exc:
        warnings.append(_warning_entry(
            source="open-brain",
            reason=f"search failed: {exc}",
            project=project,
            date=date,
        ))
        return {"sessions": [], "learnings": [], "decisions": [], "followups": []}

    sessions: list[dict[str, Any]] = []
    learnings: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    followups: list[dict[str, Any]] = []

    seen_session_summary_refs: set[str] = set()
    seen_debrief_refs: set[str] = set()

    for entry in entries:
        try:
            if not isinstance(entry, dict):
                warnings.append(_warning_entry(
                    source="open-brain",
                    reason=f"malformed entry skipped (not a dict): {type(entry).__name__}",
                    project=project,
                    date=date,
                ))
                continue
            session_ref = entry.get("session_ref")
            entry_type = entry.get("type", "")

            # Dedup by session_ref per type — session_summary and debrief use
            # separate sets so a debrief is never skipped because a session_summary
            # with the same session_ref was already processed.
            if session_ref and entry_type == "session_summary":
                if session_ref in seen_session_summary_refs:
                    continue
                seen_session_summary_refs.add(session_ref)
            elif session_ref and entry_type == "debrief":
                if session_ref in seen_debrief_refs:
                    continue
                seen_debrief_refs.add(session_ref)

            if entry_type == "session_summary":
                sessions.append(entry)
            elif entry_type == "learning":
                learnings.append(entry)
            elif entry_type == "decision":
                # Include ALL decision entries; callers can filter by metadata.status
                decisions.append(entry)
            elif entry_type == "debrief":
                # Debrief entries belong in sessions[] per the skill contract
                # ("sessions contains session_summary + debrief entries"). The
                # follow-up extraction still happens below so Decide:/Need
                # input:/Follow-up: lines are also surfaced in followups[].
                sessions.append(entry)
                content = entry.get("content", "")
                extracted = _extract_followups(content)
                for fu in extracted:
                    fu["entry_id"] = entry.get("id")
                    fu["session_ref"] = session_ref
                followups.extend(extracted)
        except Exception as exc:
            entry_id = entry.get("id", "unknown") if isinstance(entry, dict) else "unknown"
            warnings.append(_warning_entry(
                source="open-brain",
                reason=f"malformed entry skipped (id={entry_id}): {exc}",
                project=project,
                date=date,
            ))

    return {
        "sessions": sessions,
        "learnings": learnings,
        "decisions": decisions,
        "followups": followups,
    }


# ---------------------------------------------------------------------------
# Bead-commit linking
# ---------------------------------------------------------------------------


def _link_commits_to_beads(
    commits: list[dict[str, Any]],
    closed_beads: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Match commits by bead ID (CCP-xxx) in subject to closed beads.

    Returns:
        (standalone_commits, enriched_closed_beads) where bead-linked commits
        are removed from standalone and merged into the matching bead record.
    """
    # Build bead index
    bead_index: dict[str, dict[str, Any]] = {}
    for bead in closed_beads:
        bead_id = bead.get("id", "")
        if bead_id:
            bead_index[bead_id] = dict(bead)
            bead_index[bead_id].setdefault("commits", [])

    standalone: list[dict[str, Any]] = []
    for commit in commits:
        subject = commit.get("subject", "")
        matches = _BEAD_ID_RE.findall(subject)
        linked = False
        for bead_id in matches:
            if bead_id in bead_index:
                bead_index[bead_id]["commits"].append(commit)
                linked = True
        if not linked:
            standalone.append(commit)

    return standalone, list(bead_index.values())


# ---------------------------------------------------------------------------
# Main aggregator
# ---------------------------------------------------------------------------


def query_sources(
    project: str,
    date: str,
    config_path: Path,
    runner: CommandRunner,
    ob_client: Any | None,
) -> dict[str, Any]:
    """Aggregate data from all sources for the given project and date.

    Args:
        project: Project name (must exist in config).
        date: ISO date string (YYYY-MM-DD) in Europe/Berlin timezone.
        config_path: Path to daily-brief.yml config.
        runner: CommandRunner for subprocess calls (injectable).
        ob_client: Optional open-brain async client (None = skip gracefully).

    Returns:
        Execution-result envelope conforming to execution-result.schema.json.
    """
    warnings: list[dict[str, Any]] = []

    # Resolve project config
    resolve_result = _cfg.resolve_project(project, config_path=config_path)
    if resolve_result["status"] != "ok" or not resolve_result["data"]["projects"]:
        data = _empty_data_fields(project, date)
        data["warnings"] = warnings
        return _envelope(
            status="error",
            summary=f"Project '{project}' not found in config at {config_path}",
            data=data,
            errors=resolve_result.get("errors", []),
        )

    proj_dict = resolve_result["data"]["projects"][0]
    proj = _cfg.ProjectConfig.from_dict(proj_dict)

    # Collect from git
    all_commits, git_rework = _collect_git(
        project=project,
        date=date,
        repo_path=proj.path,
        runner=runner,
        warnings=warnings,
    )

    # Collect from beads
    # Resolve the project-specific beads DB so `bd` never runs against the
    # caller's cwd (which would return beads from an unrelated repo).
    # If the project has `beads: false` or no `.beads/*.db` file, skip the
    # bd queries entirely and return empty lists — not an error; not every
    # project uses beads.
    if not proj.beads:
        beads_data = {
            "closed_beads": [],
            "open_beads": [],
            "ready_beads": [],
            "blocked_beads": [],
            "decision_requests": [],
            "rework_signals": [],
        }
    else:
        db_flag = _resolve_bd_db_flag(proj.path)
        if db_flag is None:
            warnings.append(_warning_entry(
                source="beads",
                reason=(
                    f"no beads database found under {proj.path}/.beads/*.db — "
                    "beads data skipped for this project"
                ),
                project=project,
                date=date,
            ))
            beads_data = {
                "closed_beads": [],
                "open_beads": [],
                "ready_beads": [],
                "blocked_beads": [],
                "decision_requests": [],
                "rework_signals": [],
            }
        else:
            beads_data = _collect_beads(
                project=project,
                date=date,
                runner=runner,
                warnings=warnings,
                db_flag=db_flag,
            )

    # Link commits to closed beads
    standalone_commits, enriched_beads = _link_commits_to_beads(
        commits=all_commits,
        closed_beads=beads_data["closed_beads"],
    )

    # Combine rework signals
    rework_signals = git_rework + beads_data["rework_signals"]

    # Collect from open-brain
    if ob_client is None:
        warnings.append(_warning_entry(
            source="open-brain",
            reason="ob_client not provided — open-brain data unavailable",
            project=project,
            date=date,
        ))
        ob_data: dict[str, Any] = {"sessions": [], "learnings": [], "decisions": [], "followups": []}
    else:
        try:
            ob_data = asyncio.run(_collect_open_brain(
                project=project,
                date=date,
                ob_client=ob_client,
                slug=proj.slug,
                warnings=warnings,
            ))
        except RuntimeError as exc:
            warnings.append(_warning_entry(
                source="open-brain",
                reason=(
                    f"asyncio.run() failed — query_sources() cannot be called from within "
                    f"an async event loop: {exc}"
                ),
                project=project,
                date=date,
            ))
            ob_data = {"sessions": [], "learnings": [], "decisions": [], "followups": []}

    # Determine overall status
    status = "warning" if warnings else "ok"
    summary = (
        f"Collected data for {project} on {date}: "
        f"{len(ob_data['sessions'])} sessions, "
        f"{len(enriched_beads)} closed beads, "
        f"{len(standalone_commits)} commits"
    )
    if warnings:
        summary += f" ({len(warnings)} warning(s))"

    return _envelope(
        status=status,
        summary=summary,
        data={
            "project": project,
            "date": date,
            "sessions": ob_data["sessions"],
            "closed_beads": enriched_beads,
            "open_beads": beads_data["open_beads"],
            "ready_beads": beads_data["ready_beads"],
            "blocked_beads": beads_data["blocked_beads"],
            "commits": standalone_commits,
            "learnings": ob_data["learnings"],
            "decisions": ob_data["decisions"],
            "decision_requests": beads_data["decision_requests"],
            "followups": ob_data["followups"],
            "rework_signals": rework_signals,
            "warnings": warnings,
        },
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Aggregate daily-brief data from open-brain, beads, and git."
    )
    p.add_argument("--project", required=True, help="Project name from daily-brief.yml")
    p.add_argument("--date", required=True, help="Date in YYYY-MM-DD format (Europe/Berlin)")
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml)",
    )
    return p


def _build_ob_client() -> Any | None:
    """Build an open-brain client from environment / token file / config.json.

    Resolution order for the token:
      1. OB_TOKEN env var
      2. ~/.open-brain/token (plaintext file)
      3. ~/.open-brain/config.json — reads "api_key" field

    Resolution order for the endpoint URL:
      1. OB_URL env var
      2. ~/.open-brain/config.json — reads "server_url" + appends "/mcp/mcp"
      3. Hardcoded default: "https://open-brain.sussdorff.org/mcp/mcp"

    Returns None when no token can be resolved.
    """
    import json as _json
    import os

    import httpx

    ob_home = Path.home() / ".open-brain"
    token_env = os.environ.get("OB_TOKEN")
    token_file = ob_home / "token"
    config_file = ob_home / "config.json"

    token: str | None = token_env
    config_server_url: str | None = None

    if not token and token_file.exists():
        token = token_file.read_text().strip() or None

    if not token and config_file.exists():
        try:
            cfg = _json.loads(config_file.read_text())
            token = cfg.get("api_key") or None
            config_server_url = cfg.get("server_url") or None
        except Exception:  # noqa: BLE001 — malformed config is non-fatal
            pass

    if not token:
        return None

    # Resolve URL: env var wins, then config.json server_url + path, then default
    if os.environ.get("OB_URL"):
        ob_url = os.environ["OB_URL"]
    elif config_server_url:
        ob_url = config_server_url.rstrip("/") + "/mcp/mcp"
    else:
        ob_url = "https://open-brain.sussdorff.org/mcp/mcp"

    class _OBClient:
        def __init__(self, url: str, token: str) -> None:
            self._url = url
            self._token = token

        async def search(
            self,
            type_filter: list[str],
            project: str,
            date_start: str,
            date_end: str,
        ) -> list[dict[str, Any]]:
            headers = {
                "Authorization": f"Bearer {self._token}",
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
                        "clientInfo": {"name": "query-sources", "version": "1"},
                    },
                }
                await client.post(self._url, json=init_payload, headers=headers)

                # Call search tool
                call_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "search",
                        "arguments": {
                            "type": type_filter,
                            "project": project,
                            "date_start": date_start,
                            "date_end": date_end,
                        },
                    },
                }
                resp = await client.post(self._url, json=call_payload, headers=headers)
                resp.raise_for_status()
                body = resp.json()
                # MCP / JSON-RPC error envelopes arrive with HTTP 200. Detect
                # the ``error`` field and raise so ``_collect_open_brain`` can
                # turn it into a warning instead of silently returning an
                # empty success.
                if isinstance(body, dict) and body.get("error") is not None:
                    raise RuntimeError(f"MCP error: {body['error']}")
                result = body.get("result", {}) if isinstance(body, dict) else {}
                content = result.get("content", []) if isinstance(result, dict) else []
                entries = []
                for item in content:
                    if item.get("type") == "text":
                        # Let parse errors propagate — _collect_open_brain wraps in warning
                        entries.extend(json.loads(item["text"]))
                return entries

    return _OBClient(ob_url, token)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Validate date
    try:
        datetime.date.fromisoformat(args.date)
    except ValueError:
        print(
            json.dumps(
                _envelope(
                    status="error",
                    summary=f"Invalid date format: '{args.date}'. Expected YYYY-MM-DD.",
                    data=_empty_data_fields(args.project, args.date),
                    errors=[{
                        "code": "invalid-date",
                        "message": f"Date '{args.date}' is not a valid ISO date",
                        "retryable": False,
                        "suggested_fix": "Use YYYY-MM-DD format, e.g. 2026-04-23",
                    }],
                ),
                indent=2,
            )
        )
        return 0  # Exit 0 — valid envelope was emitted

    runner = RealCommandRunner()
    ob_client = _build_ob_client()

    result = query_sources(
        project=args.project,
        date=args.date,
        config_path=args.config,
        runner=runner,
        ob_client=ob_client,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
