#!/usr/bin/env python3
"""
wave-completion.py — Quick check if a wave is fully complete.

Usage: wave-completion.py <wave-config.json>

Checks both bead database status (bd show) and surface state.
Returns JSON with completion status and any stragglers.

Exit codes:
  0 — all beads done
  1 — wave not yet complete
  2 — error
"""

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from wave_helpers import (
    _DEAD_SURFACE_RE,
    _bd_status,
    _elapsed_minutes,
    _read_surface,
    _surface_is_idle,
)


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------

STALL_THRESHOLD_MIN = 15
ACTIVE_WINDOW_MIN = 5


def _check_recent_activity(bead_id: str, metrics_db: Path, active_window_min: int) -> bool:
    """Return True if there has been recent agent activity for this bead."""
    try:
        threshold_secs = active_window_min * 60
        with sqlite3.connect(str(metrics_db)) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM agent_calls WHERE bead_id=? "
                "AND (strftime('%s','now') - strftime('%s', recorded_at)) < ?",
                (bead_id, threshold_secs),
            ).fetchone()
        return bool(row and row[0] > 0)
    except Exception:
        return False


def _check_recent_tool_use(surface: str) -> bool:
    """Fallback: check scrollback for recent tool-use markers."""
    screen = _read_surface(surface, lines=100, scrollback=True)
    if _DEAD_SURFACE_RE.search(screen):
        return False
    last_30 = "\n".join(screen.splitlines()[-30:])
    return bool(
        re.search(r"\bBash\b|\bRead\b|\bWrite\b|\bEdit\b|\bGrep\b|\bGlob\b|\bAgent\b|ToolUse|tool_use", last_30)
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_wave_completion(config: dict, runner=None) -> tuple[dict, int]:
    """Check completion status for all beads in a wave config.

    Args:
        config: Parsed wave config dict (beads, wave_id, dispatch_time, ...).
        runner: Optional callable with the same signature as subprocess.run.
                Defaults to subprocess.run. Inject a mock for testing.

    Returns:
        (output_dict, exit_code) where exit_code is 0 (complete) or 1 (not complete).
    """
    if runner is None:
        runner = subprocess.run

    beads = config.get("beads", [])
    wave_id = config.get("wave_id", "unknown")
    dispatch_time = config.get("dispatch_time", "")
    elapsed_min = _elapsed_minutes(dispatch_time) if dispatch_time else 0

    all_closed = True
    all_idle = True
    stragglers: list[dict] = []
    stalls: list[dict] = []

    metrics_db = Path.home() / ".claude" / "metrics.db"

    for bead in beads:
        bead_id = bead.get("id", "")
        surface = bead.get("surface", "")

        # Check bd status
        bd_st = _bd_status(bead_id, runner=runner)

        # Check surface state
        last_lines = _read_surface(surface, lines=5, runner=runner)
        surface_idle = False

        if _DEAD_SURFACE_RE.search(last_lines):
            surface_idle = True
        elif _surface_is_idle(last_lines):
            surface_idle = True

        if bd_st != "closed":
            all_closed = False
            stragglers.append({
                "id": bead_id,
                "bd_status": bd_st,
                "surface_idle": surface_idle,
            })

        if not surface_idle:
            all_idle = False

        # Stall detection
        if surface_idle and bd_st == "in_progress" and elapsed_min >= STALL_THRESHOLD_MIN:
            is_active = False

            if metrics_db.exists():
                is_active = _check_recent_activity(bead_id, metrics_db, ACTIVE_WINDOW_MIN)

            if not is_active:
                is_active = _check_recent_tool_use(surface)

            if not is_active:
                stall_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print(
                    f"STALL: {bead_id} surface idle but bd status != closed "
                    f"(elapsed: {elapsed_min}min)",
                    file=sys.stderr,
                )

                # Write diagnostic note (idempotency via temp file marker)
                stall_marker = Path(f"/tmp/wave-stall-{wave_id}-{bead_id}")
                if not stall_marker.exists():
                    stall_marker.touch()
                    try:
                        runner(
                            [
                                "bd",
                                "update",
                                bead_id,
                                f"--append-notes=STALL-DETECTED: wave-orchestrator observed surface idle "
                                f"+ bd in_progress at {stall_ts}. Manual investigation required.",
                            ],
                            capture_output=True,
                            timeout=15,
                        )
                    except Exception as exc:
                        print(f"WARNING: bd update failed for {bead_id}: {exc}", file=sys.stderr)

                stalls.append({"id": bead_id, "detected_at": stall_ts, "elapsed_minutes": elapsed_min})

    # Check follow-up beads
    follow_ups: list[dict] = []
    for bead in beads:
        surface = bead.get("surface", "")
        screen = _read_surface(surface, lines=30, scrollback=True, runner=runner)
        if _DEAD_SURFACE_RE.search(screen):
            continue
        new_beads = re.findall(r"Created issue: ([a-zA-Z0-9_-]+)", screen)
        for new_id in new_beads:
            fu_st = _bd_status(new_id, runner=runner)
            if fu_st != "closed":
                all_closed = False
                follow_ups.append({"id": new_id, "status": fu_st})

    complete = all_closed and all_idle

    # Metrics sanity check
    bead_count = len(beads)
    bead_runs_count = 0
    metrics_sanity = "skipped"

    if metrics_db.exists() and wave_id != "unknown":
        if re.match(r"^[A-Za-z0-9_-]+$", wave_id):
            try:
                with sqlite3.connect(str(metrics_db)) as conn:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM bead_runs WHERE wave_id = ?", (wave_id,)
                    ).fetchone()
                bead_runs_count = row[0] if row else 0
                if bead_runs_count == bead_count:
                    metrics_sanity = "ok"
                else:
                    metrics_sanity = (
                        f"mismatch: expected {bead_count} bead_runs rows, got {bead_runs_count}"
                    )
                    print(
                        f"WARN: metrics sanity mismatch for wave {wave_id}: "
                        f"expected {bead_count} rows, got {bead_runs_count}",
                        file=sys.stderr,
                    )
            except Exception as e:
                metrics_sanity = f"error: {e}"
        else:
            metrics_sanity = "skipped: invalid wave_id"

    output = {
        "complete": complete,
        "all_beads_closed": all_closed,
        "all_surfaces_idle": all_idle,
        "stragglers": stragglers,
        "unclosed_follow_ups": follow_ups,
        "stalls": stalls,
        "metrics_sanity": metrics_sanity,
        "bead_runs_count": bead_runs_count,
    }
    return output, 0 if complete else 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: wave-completion.py <wave-config.json>", file=sys.stderr)
        return 2

    config_path = Path(sys.argv[1])
    if not config_path.is_file():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 2

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in config: {e}", file=sys.stderr)
        return 2

    output, exit_code = check_wave_completion(config)
    print(json.dumps(output, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
