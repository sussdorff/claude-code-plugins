#!/usr/bin/env python3
"""
wave-poll.py — Polling loop helper for the wave-monitor agent.

Extracted from beads-workflow/agents/wave-monitor.md ## Implementation section.
Runs wave-completion.sh in a loop, detects terminal conditions, and prints a
canonical execution-result envelope to stdout before exiting.

Output conforms to core/contracts/execution-result.schema.json:
  status: "ok" (wave complete) | "warning" (needs_intervention) | "error" (hard error)
  data.verdict: the wave-monitor Return Contract payload:
    {"status": "complete", "summary": {...}}
    {"status": "needs_intervention", "reason": "...", "bead_id": "...", "details": "..."}

Usage:
  python3 wave-poll.py --config /path/to/wave-config.json \\
      [--stuck-hours N] [--review-max N] [--poll-interval N]

Environment override (for testing):
  WAVE_COMPLETION_OVERRIDE=/path/to/mock-wave-completion.sh
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Execution-result envelope
# ---------------------------------------------------------------------------

_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_PRODUCER = "wave-poll.py"
_CONTRACT_VERSION = "1"


def _envelope(
    status: str,
    summary: str,
    verdict: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    next_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Wrap a verdict in the canonical execution-result envelope."""
    return {
        "status": status,
        "summary": summary,
        "data": {"verdict": verdict},
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
# Discovery
# ---------------------------------------------------------------------------


def _find_wave_completion() -> Path | None:
    """Locate wave-completion.py — env override first, then ~/.claude, then local."""
    override = os.environ.get("WAVE_COMPLETION_OVERRIDE")
    if override:
        p = Path(override)
        if p.exists():
            return p

    # Search ~/.claude tree first
    completions = list((Path.home() / ".claude").rglob("wave-completion.py"))
    if not completions:
        # Fallback: local directory tree
        completions = list(Path(".").rglob("wave-completion.py"))
    return completions[0] if completions else None


# ---------------------------------------------------------------------------
# Verdict helpers
# ---------------------------------------------------------------------------


def _verdict_complete(polls: int, elapsed_minutes: int) -> dict[str, Any]:
    return {
        "status": "complete",
        "summary": {
            "polls_run": polls,
            "elapsed_minutes": elapsed_minutes,
        },
    }


def _verdict_intervention(reason: str, bead_id: str | None, details: str) -> dict[str, Any]:
    return {
        "status": "needs_intervention",
        "reason": reason,
        "bead_id": bead_id,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------


def poll(
    wave_config: Path,
    stuck_hours: float,
    review_max: int,
    poll_interval: int,
) -> dict[str, Any]:
    """Run the polling loop and return the terminal verdict dict."""

    # Validate config path
    if not wave_config.exists():
        return _verdict_intervention(
            "ambiguous", None, f"wave_config_path not found: {wave_config}"
        )

    # Load config once to get bead list
    try:
        config_data: dict[str, Any] = json.loads(wave_config.read_text())
        beads: list[dict[str, Any]] = config_data.get("beads", [])
    except (json.JSONDecodeError, OSError) as exc:
        return _verdict_intervention(
            "ambiguous", None, f"Failed to parse wave config: {exc}"
        )

    # Discover wave-completion.py
    completion_script = _find_wave_completion()
    if completion_script is None:
        return _verdict_intervention(
            "ambiguous", None, "wave-completion.py not found in ~/.claude or local tree"
        )

    polls = 0
    start = time.monotonic()

    while True:
        polls += 1

        # Run wave-completion.py (invoke via python3; bash for .sh override in tests)
        invoke = "python3" if str(completion_script).endswith(".py") else "bash"
        try:
            result = subprocess.run(
                [invoke, str(completion_script), str(wave_config)],
                capture_output=True,
                text=True,
            )
            exit_code = result.returncode
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
        except OSError as exc:
            return _verdict_intervention(
                "ambiguous", None, f"Failed to run wave-completion.py: {exc}"
            )

        # exit code 2 = error
        if exit_code == 2:
            return _verdict_intervention(
                "ambiguous",
                None,
                f"wave-completion.py exited 2. stderr: {stderr}",
            )

        # Validate JSON
        try:
            completion: dict = json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            return _verdict_intervention(
                "ambiguous",
                None,
                "wave-completion.py output not valid JSON",
            )

        # complete=true
        if completion.get("complete", False):
            return _verdict_complete(polls, int((time.monotonic() - start) / 60))

        # Check stalls array
        stalls: list[dict] = completion.get("stalls", [])
        if stalls:
            stall_id = stalls[0].get("id")
            return _verdict_intervention(
                "stuck",
                stall_id,
                "Stall detected by wave-completion.sh",
            )

        # Check stragglers for stuck-by-hours
        for straggler in completion.get("stragglers", []):
            if straggler.get("bd_status") != "in_progress":
                continue
            bead_id = straggler.get("id", "")
            # Query bd show to find updated_at timestamp
            try:
                bd_result = subprocess.run(
                    ["bd", "show", bead_id],
                    capture_output=True,
                    text=True,
                )
                m = re.search(r"Updated:\s+(\d{4}-\d{2}-\d{2})", bd_result.stdout)
                if m:
                    updated = datetime.datetime.strptime(m.group(1), "%Y-%m-%d").replace(
                        tzinfo=datetime.timezone.utc
                    )
                    elapsed_h = (
                        datetime.datetime.now(datetime.timezone.utc) - updated
                    ).total_seconds() / 3600
                    if elapsed_h >= stuck_hours:
                        return _verdict_intervention(
                            "stuck",
                            bead_id,
                            (
                                f"Bead in_progress for {elapsed_h:.1f}h "
                                f"(threshold: {stuck_hours}h). Surface idle."
                            ),
                        )
            except OSError as exc:
                print(f"warn: bd show failed for {bead_id}: {exc}", file=sys.stderr)
                continue  # bd not available — skip stuck-by-hours check

        # Check pane scrollback for error / review-loop signals
        for bead in beads:
            surface = bead.get("surface", "")
            bead_id = bead.get("id", "")

            # Pane error check (tail-10)
            try:
                tail_result = subprocess.run(
                    ["cmux", "read-screen", "--surface", surface, "--lines", "10"],
                    capture_output=True,
                    text=True,
                )
                tail = tail_result.stdout + tail_result.stderr
            except OSError:
                tail = ""

            if tail:
                error_pattern = re.compile(
                    r"error|panic|fatal|traceback|ECONNREFUSED|ENOENT", re.IGNORECASE
                )
                false_positive_pattern = re.compile(
                    r"invalid_params|not a terminal|Surface.*not found"
                )
                if error_pattern.search(tail) and not false_positive_pattern.search(tail):
                    # Extract first matching line for detail
                    detail_line = ""
                    for line in tail.splitlines():
                        if error_pattern.search(line):
                            detail_line = line[:120]
                            break
                    return _verdict_intervention(
                        "pane-error",
                        bead_id,
                        detail_line or tail[:120],
                    )

            # Review-loop check (scrollback-100)
            try:
                scrollback_result = subprocess.run(
                    [
                        "cmux",
                        "read-screen",
                        "--surface",
                        surface,
                        "--scrollback",
                        "--lines",
                        "100",
                    ],
                    capture_output=True,
                    text=True,
                )
                scrollback = scrollback_result.stdout
            except OSError:
                scrollback = ""

            if scrollback:
                review_pattern = re.compile(
                    r"Review iteration \d+|Codex review iteration \d+", re.IGNORECASE
                )
                review_count = len(review_pattern.findall(scrollback))
                if review_count >= review_max:
                    return _verdict_intervention(
                        "review-loop",
                        bead_id,
                        (
                            f"Detected {review_count} review iterations "
                            f"(threshold: {review_max})"
                        ),
                    )

        # Non-terminal — sleep and poll again
        if poll_interval > 0:
            time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll wave completion and emit a JSON verdict to stdout."
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Absolute path to wave-config.json",
    )
    parser.add_argument(
        "--stuck-hours",
        type=float,
        default=4.0,
        help="Hours before an in_progress bead is considered stuck (default: 4)",
    )
    parser.add_argument(
        "--review-max",
        type=int,
        default=3,
        help="Review iterations before review-loop verdict (default: 3)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=270,
        help="Seconds to sleep between polls (default: 270)",
    )
    return parser.parse_args(argv)


def _verdict_to_envelope(verdict: dict[str, Any]) -> dict[str, Any]:
    """Wrap a raw verdict dict in the canonical execution-result envelope."""
    v_status = verdict.get("status", "")

    if v_status == "complete":
        summary_str = (
            f"Wave complete: {verdict.get('summary', {}).get('bead_count', '?')} beads "
            f"in {verdict.get('summary', {}).get('elapsed_minutes', '?')} minutes."
        )
        return _envelope(
            status="ok",
            summary=summary_str,
            verdict=verdict,
        )

    # needs_intervention
    reason = verdict.get("reason", "unknown")
    bead_id = verdict.get("bead_id")
    details = verdict.get("details", "")

    if reason in ("ambiguous",):
        # Hard error — wave infrastructure problem
        summary_str = f"Wave monitoring error: {details}"
        return _envelope(
            status="error",
            summary=summary_str,
            verdict=verdict,
            errors=[
                {
                    "code": f"wave-poll/{reason}",
                    "message": details,
                    "retryable": False,
                }
            ],
            next_steps=[
                {
                    "id": "investigate",
                    "summary": f"Investigate wave monitoring failure: {details}",
                    "priority": "now",
                    "automatable": False,
                }
            ],
        )

    # warning — intervention needed but wave is still running
    if bead_id:
        summary_str = f"Wave needs intervention: {reason} on bead {bead_id}. {details}"
        ns_summary = f"Investigate bead {bead_id}: {details}"
    else:
        summary_str = f"Wave needs intervention: {reason}. {details}"
        ns_summary = f"Investigate wave issue ({reason}): {details}"

    return _envelope(
        status="warning",
        summary=summary_str,
        verdict=verdict,
        next_steps=[
            {
                "id": f"intervention/{reason}",
                "summary": ns_summary,
                "priority": "now",
                "automatable": False,
            }
        ],
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    verdict = poll(
        wave_config=args.config,
        stuck_hours=args.stuck_hours,
        review_max=args.review_max,
        poll_interval=args.poll_interval,
    )
    envelope = _verdict_to_envelope(verdict)
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
