#!/usr/bin/env python3
"""
render-brief.py — Daily-brief markdown renderer (v1.0).

Renders a Chief-of-Staff report in Voice B (journalistic narrator, past tense,
third-person observational, German) from query-sources.py data envelopes.

Sections rendered (v1.0):
  1. Executive Summary (synthesized prose, German, ~150 words)
  2. Was sich verändert hat (What Changed) — deterministic from closed_beads + commits
  3. Warum es zählt (Why It Matters) — synthesized prose, only from cited facts
  4. Offene Fäden (Open Loops) — deterministic from open_beads + blocked_beads
  5. Nächste sinnvolle Schritte (Next Best Moves) — max 3 items, sourced
  6. Belege (Evidence) — bullet list of beads/commits/sessions/decisions/warnings

Usage:
    # Single day
    python3 scripts/render-brief.py --project claude-code-plugins --date 2026-04-23

    # Range (compressed rollup by default)
    python3 scripts/render-brief.py --project claude-code-plugins --since 2026-04-20
    python3 scripts/render-brief.py --project claude-code-plugins \
        --range 2026-04-20 2026-04-22

    # Detailed mode (full per-day sections)
    python3 scripts/render-brief.py --project claude-code-plugins \
        --since 2026-04-20 --detailed
"""

from __future__ import annotations

import argparse
import datetime
import json
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

_EMPTY_DAY_MSG = "Ruhiger Tag — keine Aktivität verzeichnet."
_WORD_SOFT_CAP = 150
_WORD_SOFT_CAP_DETAILED = 300


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------


def _fetch_envelope(
    project: str,
    date: str,
    config_path: Path,
) -> dict[str, Any]:
    """Fetch the query-sources.py envelope for a project+date."""
    qs_script = Path(__file__).parent / "query-sources.py"
    cmd = [
        sys.executable, str(qs_script),
        "--project", project,
        "--date", date,
        "--config", str(config_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if proc.returncode != 0:
        return {}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}


def _fetch_capabilities(
    envelope: dict[str, Any],
    config_path: Path,
) -> list[str]:
    """Extract capability signals from a data envelope."""
    ce_script = Path(__file__).parent / "capability-extractor.py"
    cmd = [sys.executable, str(ce_script), "--stdin"]
    proc = subprocess.run(
        cmd,
        input=json.dumps(envelope),
        capture_output=True,
        text=True,  # noqa: S603
    )
    if proc.returncode != 0:
        return []
    try:
        result = json.loads(proc.stdout)
        return result.get("data", {}).get("capabilities", [])
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def _render_executive_summary(
    data: dict[str, Any],
    capabilities: list[str],
    project: str,
    date: str,
    *,
    detailed: bool = False,
) -> str:
    """Render Executive Summary section.

    Voice B: German, past tense, third-person observational.
    Synthesized prose but only from cited source facts.
    Empty day: emit honest empty state message.
    """
    closed_beads = data.get("closed_beads", [])
    open_beads = data.get("open_beads", [])
    ready_beads = data.get("ready_beads", [])
    commits = data.get("commits", [])
    sessions = data.get("sessions", [])
    warnings = data.get("warnings", [])

    lines: list[str] = [f"## Executive Summary — {project} ({date})", ""]

    # Check for empty day — include open/ready beads and warnings as management anchors
    # (a day with only open/blocked work or degraded sources is not truly empty)
    has_activity = any([closed_beads, commits, capabilities, sessions, open_beads, ready_beads, warnings])
    if not has_activity:
        lines.append(_EMPTY_DAY_MSG)
        lines.append("")
        return "\n".join(lines)

    # Build prose paragraph from actual facts
    paragraphs: list[str] = []

    # Closed beads summary
    if closed_beads:
        count = len(closed_beads)
        bead_ids = ", ".join(b.get("id", "?") for b in closed_beads[:3])
        if len(closed_beads) > 3:
            bead_ids += f" und {len(closed_beads) - 3} weitere"
        paragraphs.append(
            f"{count} Bead{'s' if count > 1 else ''} wurde{'n' if count > 1 else ''} "
            f"geschlossen: {bead_ids}."
        )

    # Capability signals
    if capabilities:
        cap_count = len(capabilities)
        paragraphs.append(
            f"Dabei {'wurden' if cap_count > 1 else 'wurde'} "
            f"{cap_count} neue Capability-Signal{'e' if cap_count > 1 else ''} erkannt."
        )

    # Standalone commits
    if commits and not closed_beads:
        count = len(commits)
        paragraphs.append(
            f"{count} Commit{'s' if count > 1 else ''} "
            f"{'wurden' if count > 1 else 'wurde'} ohne verknüpften Bead eingecheckt."
        )

    # Sessions
    if sessions:
        count = len(sessions)
        noun = "Session-Einträge" if count > 1 else "Session-Eintrag"
        verb = "sind" if count > 1 else "ist"
        paragraphs.append(f"{count} {noun} {verb} dokumentiert.")

    # Open/ready work
    open_count = len(open_beads)
    ready_count = len(ready_beads)
    if open_count > 0 or ready_count > 0:
        if ready_count > 0:
            paragraphs.append(
                f"{ready_count} Bead{'s' if ready_count > 1 else ''} "
                f"{'sind' if ready_count > 1 else 'ist'} bereit für den nächsten Schritt."
            )
        elif open_count > 0:
            paragraphs.append(
                f"{open_count} Bead{'s' if open_count > 1 else ''} "
                f"{'sind' if open_count > 1 else 'ist'} weiterhin in Bearbeitung."
            )

    # Degraded source warning
    if warnings:
        paragraphs.append(
            f"Hinweis: {len(warnings)} Datenquelle{'n' if len(warnings) > 1 else ''} "
            f"{'waren' if len(warnings) > 1 else 'war'} nicht vollständig verfügbar."
        )

    prose = " ".join(paragraphs)

    # In detailed mode, expand with individual bead titles if available
    if detailed and closed_beads:
        detail_lines: list[str] = []
        for bead in closed_beads:
            bead_id = bead.get("id", "?")
            title = bead.get("title", "")
            issue_type = bead.get("issue_type") or bead.get("type") or "task"
            detail_lines.append(f"- **{bead_id}** [{issue_type}]: {title}")
        if detail_lines:
            prose = prose + "\n\n" + "\n".join(detail_lines)

    lines.append(prose)
    lines.append("")
    return "\n".join(lines)


def _render_what_changed(
    data: dict[str, Any],
    capabilities: list[str],
    project: str,
    date: str,
) -> str:
    """Render Was sich verändert hat (What Changed) section.

    Deterministic from closed_beads and standalone commits.
    """
    closed_beads = data.get("closed_beads", [])
    commits = data.get("commits", [])

    lines: list[str] = [f"## Was sich verändert hat — {project} ({date})", ""]

    if not closed_beads and not commits and not capabilities:
        lines.append(_EMPTY_DAY_MSG)
        lines.append("")
        return "\n".join(lines)

    # Closed beads
    if closed_beads:
        lines.append("**Geschlossene Beads:**")
        lines.append("")
        for bead in closed_beads:
            bead_id = bead.get("id", "?")
            title = bead.get("title", "(kein Titel)")
            issue_type = bead.get("issue_type") or bead.get("type") or "task"
            bead_commits = bead.get("commits", [])
            commit_count = f" [{len(bead_commits)} Commit{'s' if len(bead_commits) > 1 else ''}]" if bead_commits else ""
            lines.append(f"- **{bead_id}** [{issue_type}]: {title}{commit_count}")
        lines.append("")

    # Capability signals
    if capabilities:
        lines.append("**Neue Capabilities:**")
        lines.append("")
        for cap in capabilities:
            lines.append(f"- {cap}")
        lines.append("")

    # Standalone commits (not linked to a bead)
    if commits:
        lines.append("**Standalone-Commits:**")
        lines.append("")
        for commit in commits[:10]:  # cap at 10 to keep brief manageable
            sha = commit.get("sha", "?")[:8]
            subject = commit.get("subject", "(kein Subject)")
            lines.append(f"- `{sha}` {subject}")
        if len(commits) > 10:
            lines.append(f"- *(+{len(commits) - 10} weitere)*")
        lines.append("")

    return "\n".join(lines)


def _render_why_it_matters(
    data: dict[str, Any],
    capabilities: list[str],
    project: str,
    date: str,
) -> str:
    """Render Warum es zählt (Why It Matters) section.

    Synthesized prose but ONLY from cited source facts.
    If no source to cite, omit the section entirely.
    """
    closed_beads = data.get("closed_beads", [])
    sessions = data.get("sessions", [])

    # Collect learnings from sessions
    learnings = data.get("learnings", [])
    decisions = data.get("decisions", [])

    # Only render if we have concrete facts to cite
    if not closed_beads and not capabilities and not learnings and not sessions:
        return ""

    lines: list[str] = [f"## Warum es zählt — {project} ({date})", ""]

    paragraphs: list[str] = []

    # Closed feature beads
    feature_beads = [
        b for b in closed_beads
        if (b.get("issue_type") or b.get("type") or "").lower() == "feature"
    ]
    if feature_beads:
        count = len(feature_beads)
        ids = ", ".join(b.get("id", "?") for b in feature_beads[:2])
        if len(feature_beads) > 2:
            ids += f" u.a."
        paragraphs.append(
            f"{count} Feature-Bead{'s' if count > 1 else ''} "
            f"({'wurden' if count > 1 else 'wurde'} geschlossen: {ids}) "
            f"{'erweitern' if count > 1 else 'erweitert'} den Funktionsumfang direkt."
        )

    # Capabilities hint — use neutral temporal language (not "gestern" for explicit dates)
    if capabilities:
        paragraphs.append(
            "Die erkannten Capability-Signale zeigen, was durch die abgeschlossene Arbeit "
            "jetzt möglich geworden ist."
        )

    # Learnings
    if learnings:
        count = len(learnings)
        noun = "Lern-Einträge" if count > 1 else "Lern-Eintrag"
        verb = "wurden" if count > 1 else "wurde"
        paragraphs.append(f"{count} {noun} {verb} dokumentiert.")

    # Decisions pending
    if decisions:
        count = len(decisions)
        paragraphs.append(
            f"{count} Entscheidung{'en' if count > 1 else ''} "
            f"{'liegen' if count > 1 else 'liegt'} vor."
        )

    if not paragraphs:
        return ""

    lines.append(" ".join(paragraphs))
    lines.append("")
    return "\n".join(lines)


def _render_open_loops(
    data: dict[str, Any],
    project: str,
    date: str,
) -> str:
    """Render Offene Fäden (Open Loops) section.

    Deterministic from open_beads, blocked_beads.
    Neutral tone — these are not failures, just in-flight work.
    """
    open_beads = data.get("open_beads", [])
    blocked_beads = data.get("blocked_beads", [])

    lines: list[str] = [f"## Offene Fäden — {project} ({date})", ""]

    if not open_beads and not blocked_beads:
        lines.append("Keine offenen Fäden erfasst.")
        lines.append("")
        return "\n".join(lines)

    if open_beads:
        lines.append(f"**In Bearbeitung / Bereit ({len(open_beads)}):**")
        lines.append("")
        for bead in open_beads[:10]:
            bead_id = bead.get("id", "?")
            title = bead.get("title", "(kein Titel)")
            status = bead.get("status", "open")
            lines.append(f"- **{bead_id}** [{status}]: {title}")
        if len(open_beads) > 10:
            lines.append(f"- *(+{len(open_beads) - 10} weitere)*")
        lines.append("")

    if blocked_beads:
        lines.append(f"**Blockiert ({len(blocked_beads)}):**")
        lines.append("")
        for bead in blocked_beads[:5]:
            bead_id = bead.get("id", "?")
            title = bead.get("title", "(kein Titel)")
            lines.append(f"- **{bead_id}**: {title}")
        if len(blocked_beads) > 5:
            lines.append(f"- *(+{len(blocked_beads) - 5} weitere)*")
        lines.append("")

    return "\n".join(lines)


def _render_next_best_moves(
    data: dict[str, Any],
    project: str,
    date: str,
) -> str:
    """Render Nächste sinnvolle Schritte (Next Best Moves) section.

    Max 3 items total:
    - Max 2 from ready_beads (bd ready / unblocked priority order)
    - Max 1 from explicit session follow-up (followups[])
    Each item cites its source category.
    """
    ready_beads = data.get("ready_beads", [])
    followups = data.get("followups", [])

    lines: list[str] = [f"## Nächste sinnvolle Schritte — {project} ({date})", ""]

    moves: list[tuple[str, str]] = []  # (source_label, text)

    # Up to 2 from ready_beads
    for bead in ready_beads[:2]:
        bead_id = bead.get("id", "?")
        title = bead.get("title", "(kein Titel)")
        moves.append(("ready-bead", f"**{bead_id}**: {title}"))

    # Up to 1 from followups (explicit session follow-up)
    for fu in followups[:1]:
        fu_type = fu.get("type", "Follow-up")
        fu_text = fu.get("text", "")
        if fu_text:
            moves.append(("session-followup", f"**{fu_type}**: {fu_text}"))

    # Hard cap at 3
    moves = moves[:3]

    if not moves:
        lines.append("Keine unmittelbaren nächsten Schritte identifiziert.")
        lines.append("")
        return "\n".join(lines)

    for source_label, text in moves:
        lines.append(f"- {text} *(Quelle: {source_label})*")
    lines.append("")
    return "\n".join(lines)


def _render_evidence(
    data: dict[str, Any],
    project: str,
    date: str,
) -> str:
    """Render Belege (Evidence) section.

    Bullet list of source beads/commits/sessions/decisions/warnings.
    Deterministic from query-sources.py fields.
    """
    closed_beads = data.get("closed_beads", [])
    commits = data.get("commits", [])
    sessions = data.get("sessions", [])
    decisions = data.get("decisions", [])
    warnings = data.get("warnings", [])
    rework_signals = data.get("rework_signals", [])

    lines: list[str] = [f"## Belege — {project} ({date})", ""]

    if not any([closed_beads, commits, sessions, decisions, warnings, rework_signals]):
        lines.append("*(keine Belege für diesen Tag)*")
        lines.append("")
        return "\n".join(lines)

    # Closed beads
    for bead in closed_beads:
        bead_id = bead.get("id", "?")
        title = bead.get("title", "?")
        bead_commits = bead.get("commits", [])
        sha_list = " ".join(f"`{c.get('sha', '?')[:8]}`" for c in bead_commits[:3])
        sha_hint = f" — Commits: {sha_list}" if sha_list else ""
        lines.append(f"- bead/{bead_id}: {title}{sha_hint}")

    # Standalone commits
    for commit in commits[:5]:
        sha = commit.get("sha", "?")[:8]
        subject = commit.get("subject", "?")
        lines.append(f"- commit/`{sha}`: {subject}")
    if len(commits) > 5:
        lines.append(f"- *(+{len(commits) - 5} weitere Commits)*")

    # Sessions
    for session in sessions[:3]:
        session_ref = session.get("session_ref") or session.get("id", "?")
        title = session.get("title", "session")
        lines.append(f"- session/{session_ref}: {title}")

    # Decisions
    for decision in decisions[:3]:
        decision_id = decision.get("id", "?")
        title = decision.get("title", "?")
        lines.append(f"- decision/{decision_id}: {title}")

    # Rework signals
    for signal in rework_signals[:3]:
        signal_type = signal.get("type", "?")
        bead_id = signal.get("bead_id") or signal.get("sha", "?")[:8]
        lines.append(f"- rework/{signal_type}: {bead_id}")

    # Warnings
    for warning in warnings[:3]:
        source = warning.get("source", "?")
        reason = warning.get("reason", "?")
        lines.append(f"- warning/{source}: {reason}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Single-day brief renderer
# ---------------------------------------------------------------------------


def render_single_day(
    project: str,
    date: str,
    config_path: Path,
    *,
    detailed: bool = False,
    persist: bool = True,
) -> str:
    """Render a brief for a single day.

    Args:
        project: Project name from daily-brief.yml.
        date: ISO date string (YYYY-MM-DD).
        config_path: Path to daily-brief.yml.
        detailed: Use higher word cap for prose sections.
        persist: If True, save brief to <project>/.claude/daily-briefs/YYYY-MM-DD.md.

    Returns:
        Rendered markdown string.
    """
    # Fetch data envelope
    envelope = _fetch_envelope(project, date, config_path)
    data = envelope.get("data", {})
    if not data:
        return f"# {project} — {date}\n\n{_EMPTY_DAY_MSG}\n"

    # Extract capabilities
    capabilities = _fetch_capabilities(envelope, config_path)

    # Build sections
    sections: list[str] = []
    sections.append(f"# {project} — {date}\n")

    exec_summary = _render_executive_summary(data, capabilities, project, date, detailed=detailed)
    what_changed = _render_what_changed(data, capabilities, project, date)
    why_matters = _render_why_it_matters(data, capabilities, project, date)
    open_loops = _render_open_loops(data, project, date)
    next_moves = _render_next_best_moves(data, project, date)
    evidence = _render_evidence(data, project, date)

    sections.append(exec_summary)
    sections.append(what_changed)
    if why_matters:
        sections.append(why_matters)
    sections.append(open_loops)
    sections.append(next_moves)
    sections.append(evidence)

    brief = "\n".join(sections)

    # Persist to disk if requested
    if persist:
        try:
            brief_path = _cfg.brief_path(project, date, config_path=config_path)
            brief_path.parent.mkdir(parents=True, exist_ok=True)
            brief_path.write_text(brief)
        except Exception:
            pass  # Non-blocking: persist failure does not abort render

    return brief


# ---------------------------------------------------------------------------
# Range mode renderers
# ---------------------------------------------------------------------------


def _date_range(start: str, end: str) -> list[str]:
    """Return list of ISO date strings from start to end (inclusive)."""
    start_date = datetime.date.fromisoformat(start)
    end_date = datetime.date.fromisoformat(end)
    dates: list[str] = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += datetime.timedelta(days=1)
    return dates


def render_range(
    project: str,
    start_date: str,
    end_date: str,
    config_path: Path,
    *,
    detailed: bool = False,
    persist: bool = True,
) -> str:
    """Render a compressed rollup brief for a date range.

    Per-day briefs are persisted unchanged on disk (unless persist=False).
    Default output is a compressed rollup (one Executive Summary, What Changed
    grouped by day, Open Loops/Next Best Moves/Evidence aggregated).
    In --detailed mode, full per-day sections are included.

    Args:
        project: Project name from daily-brief.yml.
        start_date: Start of range (YYYY-MM-DD).
        end_date: End of range (YYYY-MM-DD).
        config_path: Path to daily-brief.yml.
        detailed: If True, include full per-day sections.
        persist: If True (default), save per-day briefs to disk.

    Returns:
        Rendered markdown string.
    """
    dates = _date_range(start_date, end_date)

    # Optionally persist single-day briefs and collect envelopes
    all_envelopes: list[tuple[str, dict[str, Any]]] = []
    for date in dates:
        envelope = _fetch_envelope(project, date, config_path)
        if envelope:
            # Persist each day's brief unchanged (respects persist flag)
            render_single_day(project, date, config_path, detailed=detailed, persist=persist)
            all_envelopes.append((date, envelope))

    if not all_envelopes:
        return f"# {project} — {start_date} bis {end_date}\n\n{_EMPTY_DAY_MSG}\n"

    lines: list[str] = [f"# {project} — {start_date} bis {end_date}\n"]

    if detailed:
        # Full per-day sections
        for date, envelope in all_envelopes:
            data = envelope.get("data", {})
            capabilities = _fetch_capabilities(envelope, config_path)
            lines.append(f"---\n")
            lines.append(render_single_day(project, date, config_path, detailed=True, persist=False))
    else:
        # Compressed rollup

        # Aggregate data across all days
        all_closed_beads: list[dict[str, Any]] = []
        all_commits: list[dict[str, Any]] = []
        all_open_beads: list[dict[str, Any]] = []
        all_blocked_beads: list[dict[str, Any]] = []
        all_ready_beads: list[dict[str, Any]] = []
        all_followups: list[dict[str, Any]] = []
        all_sessions: list[dict[str, Any]] = []
        all_decisions: list[dict[str, Any]] = []
        all_warnings: list[dict[str, Any]] = []
        all_rework_signals: list[dict[str, Any]] = []
        all_capabilities: list[str] = []

        for date, envelope in all_envelopes:
            data = envelope.get("data", {})
            all_closed_beads.extend(data.get("closed_beads", []))
            all_commits.extend(data.get("commits", []))
            all_sessions.extend(data.get("sessions", []))
            all_decisions.extend(data.get("decisions", []))
            all_warnings.extend(data.get("warnings", []))
            all_rework_signals.extend(data.get("rework_signals", []))
            all_followups.extend(data.get("followups", []))
            # Use last day's snapshot for open/ready/blocked (point-in-time)
            caps = _fetch_capabilities(envelope, config_path)
            all_capabilities.extend(caps)

        # Use last day's snapshot for open/ready/blocked
        if all_envelopes:
            last_data = all_envelopes[-1][1].get("data", {})
            all_open_beads = last_data.get("open_beads", [])
            all_ready_beads = last_data.get("ready_beads", [])
            all_blocked_beads = last_data.get("blocked_beads", [])

        # Aggregate data dict for section renderers
        agg_data = {
            "closed_beads": all_closed_beads,
            "commits": all_commits,
            "open_beads": all_open_beads,
            "ready_beads": all_ready_beads,
            "blocked_beads": all_blocked_beads,
            "followups": all_followups,
            "sessions": all_sessions,
            "decisions": all_decisions,
            "warnings": all_warnings,
            "rework_signals": all_rework_signals,
            "learnings": [],
        }

        date_label = f"{start_date} bis {end_date}"

        # One Executive Summary for the range
        exec_summary = _render_executive_summary(
            agg_data, all_capabilities, project, date_label
        )
        lines.append(exec_summary)

        # What Changed grouped by day
        lines.append(f"## Was sich verändert hat — {project} ({date_label})\n")
        for date, envelope in all_envelopes:
            data = envelope.get("data", {})
            day_caps = _fetch_capabilities(envelope, config_path)
            day_closed = data.get("closed_beads", [])
            day_commits = data.get("commits", [])
            if day_closed or day_commits or day_caps:
                lines.append(f"### {date}")
                lines.append("")
                if day_closed:
                    for bead in day_closed:
                        bead_id = bead.get("id", "?")
                        title = bead.get("title", "?")
                        lines.append(f"- **{bead_id}**: {title}")
                if day_caps:
                    for cap in day_caps:
                        lines.append(f"- {cap}")
                if day_commits and not day_closed:
                    for commit in day_commits[:5]:
                        sha = commit.get("sha", "?")[:8]
                        subject = commit.get("subject", "?")
                        lines.append(f"- `{sha}` {subject}")
                lines.append("")

        # Aggregated Why It Matters
        why_matters = _render_why_it_matters(
            agg_data, all_capabilities, project, date_label
        )
        if why_matters:
            lines.append(why_matters)

        # Aggregated Open Loops
        lines.append(_render_open_loops(agg_data, project, date_label))

        # Aggregated Next Best Moves
        lines.append(_render_next_best_moves(agg_data, project, date_label))

        # Aggregated Evidence
        lines.append(_render_evidence(agg_data, project, date_label))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Render daily-brief markdown report from query-sources.py data."
    )
    p.add_argument("--project", required=True, help="Project name from daily-brief.yml")
    mode_group = p.add_mutually_exclusive_group()
    mode_group.add_argument("--date", help="Single date (YYYY-MM-DD)")
    mode_group.add_argument("--since", help="Start date for range mode (YYYY-MM-DD)")
    p.add_argument(
        "--until",
        help="End date for range mode (default: today). Use with --since.",
    )
    p.add_argument(
        "--range",
        nargs=2,
        metavar=("START", "END"),
        help="Date range START END (YYYY-MM-DD YYYY-MM-DD)",
    )
    p.add_argument(
        "--detailed",
        action="store_true",
        help="Detailed mode: higher word cap and full per-day sections in range output",
    )
    p.add_argument(
        "--no-persist",
        action="store_true",
        help="Do not persist brief to disk",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=_cfg.CONFIG_PATH,
        help="Path to daily-brief.yml (default: ~/.claude/daily-brief.yml)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config_path = args.config
    detailed = args.detailed
    persist = not args.no_persist

    today = datetime.date.today().isoformat()

    if args.date:
        # Single day mode
        try:
            datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"Error: Invalid date '{args.date}'. Use YYYY-MM-DD.", file=sys.stderr)
            return 1

        brief = render_single_day(
            args.project, args.date, config_path, detailed=detailed, persist=persist
        )
        print(brief)

    elif args.since:
        # Range mode with --since [--until]
        start_date = args.since
        end_date = args.until or today

        try:
            datetime.date.fromisoformat(start_date)
            datetime.date.fromisoformat(end_date)
        except ValueError as exc:
            print(f"Error: Invalid date: {exc}", file=sys.stderr)
            return 1

        brief = render_range(
            args.project, start_date, end_date, config_path, detailed=detailed, persist=persist
        )
        print(brief)

    elif args.range:
        # Range mode with --range START END
        start_date, end_date = args.range
        try:
            datetime.date.fromisoformat(start_date)
            datetime.date.fromisoformat(end_date)
        except ValueError as exc:
            print(f"Error: Invalid date: {exc}", file=sys.stderr)
            return 1

        brief = render_range(
            args.project, start_date, end_date, config_path, detailed=detailed, persist=persist
        )
        print(brief)

    else:
        # Default: yesterday
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        brief = render_single_day(
            args.project, yesterday, config_path, detailed=detailed, persist=persist
        )
        print(brief)

    return 0


if __name__ == "__main__":
    sys.exit(main())
