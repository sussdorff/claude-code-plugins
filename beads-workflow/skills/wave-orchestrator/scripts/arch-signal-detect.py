#!/usr/bin/env python3
"""
arch-signal-detect.py — Detect architecture review signals for beads.

Usage: arch-signal-detect.py <bead-id1> [bead-id2] ...
Output (stdout): JSON array with signal scores per bead (backward-compat)
Sidecar: /tmp/<bead_id>.arch-signal.json — execution-result.schema.json envelope

Signal scoring:
  STRONG patterns (3 points each): [ARCH], state machine, boundary, protocol, API contract
  MEDIUM patterns (2 points each): [REFACTOR], alternative approaches, migration path
  Dependency count >=2 blocks = +2 pts (MEDIUM)
  Score >= 6 -> REVIEW_YES
  Score 3-5  -> REVIEW_MAYBE
  Score < 3  -> REVIEW_NO

Exit codes: 0 = success, 1 = no bead IDs given
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Signal patterns (same as Bash version)
# ---------------------------------------------------------------------------

STRONG_PATTERNS: list[tuple[str, str]] = [
    (r"\[ARCH\]", "[ARCH]"),
    (r"state.machine", "state machine"),
    (r"boundary|boundaries", "boundary"),
    (r"protocol", "protocol"),
    (r"API.contract", "API contract"),
    (r"layer.separation|layer.trennung", "layer separation"),
]

MEDIUM_PATTERNS: list[tuple[str, str]] = [
    (r"\[REFACTOR\]", "[REFACTOR]"),
    (r"alternative.approach|trade.off", "alternative approach"),
    (r"migration.path|migration.strateg", "migration path"),
]

# Verdicts
REVIEW_YES = "REVIEW_YES"
REVIEW_MAYBE = "REVIEW_MAYBE"
REVIEW_NO = "REVIEW_NO"

# Types that never need arch review
SKIP_TYPES = {"bug", "chore"}


@dataclass
class Signal:
    match: str
    strength: str  # "STRONG" or "MEDIUM"
    points: int


@dataclass
class BeadResult:
    id: str
    title: str = ""
    score: int = 0
    verdict: str = REVIEW_NO
    reason: str = ""
    signals: list[Signal] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id}
        if self.error:
            d["error"] = self.error
            return d
        d["title"] = self.title
        d["score"] = self.score
        d["verdict"] = self.verdict
        if self.reason:
            d["reason"] = self.reason
        d["signals"] = [
            {"match": s.match, "strength": s.strength, "points": s.points}
            for s in self.signals
        ]
        return d


def _re_search(pattern: str, text: str) -> str | None:
    """Case-insensitive search; returns first match or None."""
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(0) if m else None


def analyze_bead(bead_id: str, bd_runner: "CommandRunner") -> BeadResult:
    """Analyze a single bead and return its signal result."""
    result = BeadResult(id=bead_id)

    json_out = bd_runner.run_json(["bd", "show", bead_id, "--json"])
    if json_out is None:
        result.error = "bead not found"
        return result

    # bd show --json returns an array
    if isinstance(json_out, list) and json_out:
        bead_data = json_out[0]
    elif isinstance(json_out, dict):
        bead_data = json_out
    else:
        result.error = "unexpected JSON shape"
        return result

    title = bead_data.get("title") or ""
    description = bead_data.get("description") or ""
    issue_type = bead_data.get("issue_type") or ""
    blocks = bead_data.get("blocks") or []

    result.title = title

    # Skip types that don't need arch review
    if issue_type in SKIP_TYPES:
        result.verdict = REVIEW_NO
        result.reason = f"type={issue_type} (auto-skip)"
        return result

    full_text = f"{title} {description}"
    score = 0
    signals: list[Signal] = []

    # Check strong signals (3 pts each)
    for pattern, label in STRONG_PATTERNS:
        matched = _re_search(pattern, full_text)
        if matched:
            score += 3
            signals.append(Signal(match=matched, strength="STRONG", points=3))

    # Check medium signals (2 pts each)
    for pattern, label in MEDIUM_PATTERNS:
        matched = _re_search(pattern, full_text)
        if matched:
            score += 2
            signals.append(Signal(match=matched, strength="MEDIUM", points=2))

    # Dependency count: blocks >=2 beads → +2 pts (MEDIUM)
    blocks_count = len(blocks) if isinstance(blocks, list) else 0
    if blocks_count >= 2:
        score += 2
        signals.append(
            Signal(
                match=f"blocks {blocks_count} beads",
                strength="MEDIUM",
                points=2,
            )
        )

    # Determine verdict
    if score >= 6:
        verdict = REVIEW_YES
    elif score >= 3:
        verdict = REVIEW_MAYBE
    else:
        verdict = REVIEW_NO

    result.score = score
    result.verdict = verdict
    result.signals = signals
    return result


class CommandRunner:
    """Dependency-injectable subprocess runner for bd calls."""

    def run_json(self, cmd: list[str]) -> Any:
        """Run a command and return parsed JSON, or None on failure."""
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                return None
            return json.loads(proc.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            return None


def build_envelope(
    signals: list[dict[str, Any]],
    *,
    status: str = "ok",
    errors: list[dict] | None = None,
) -> dict[str, Any]:
    """Build an execution-result.schema.json envelope wrapping the signal array."""
    yes_count = sum(1 for s in signals if s.get("verdict") == REVIEW_YES)
    no_count = sum(1 for s in signals if s.get("verdict") == REVIEW_NO)
    maybe_count = sum(1 for s in signals if s.get("verdict") == REVIEW_MAYBE)
    error_count = sum(1 for s in signals if "error" in s)
    total = len(signals)

    summary_parts = [f"Analyzed {total} bead(s):"]
    if yes_count:
        summary_parts.append(f"{yes_count} REVIEW_YES")
    if maybe_count:
        summary_parts.append(f"{maybe_count} REVIEW_MAYBE")
    if no_count:
        summary_parts.append(f"{no_count} REVIEW_NO")
    if error_count:
        summary_parts.append(f"{error_count} error(s)")

    return {
        "status": status,
        "summary": " ".join(summary_parts),
        "data": {"signals": signals},
        "errors": errors or [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1.0",
            "producer": "arch-signal-detect.py",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema": "core/contracts/execution-result.schema.json",
        },
    }


def write_sidecar(bead_id: str, envelope: dict[str, Any]) -> None:
    """Write envelope as sidecar JSON file to /tmp."""
    try:
        sidecar_path = Path(f"/tmp/{bead_id}.arch-signal.json")
        sidecar_path.write_text(json.dumps(envelope, indent=2))
    except OSError:
        pass  # sidecar write failure is non-fatal


def main(runner: CommandRunner | None = None) -> int:
    if runner is None:
        runner = CommandRunner()

    bead_ids = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not bead_ids:
        print('{"error": "No bead IDs provided"}', file=sys.stderr)
        return 1

    results: list[BeadResult] = []
    for bead_id in bead_ids:
        results.append(analyze_bead(bead_id, runner))

    signal_dicts = [r.to_dict() for r in results]

    # Primary stdout: raw JSON array (backward-compat with Bash version)
    print(json.dumps(signal_dicts, indent=2))

    # Determine overall envelope status
    has_errors = any("error" in d for d in signal_dicts)
    envelope_status = "warning" if has_errors else "ok"
    envelope = build_envelope(signal_dicts, status=envelope_status)

    # Write per-bead sidecars (one per bead_id analyzed)
    for bead_id in bead_ids:
        write_sidecar(bead_id, envelope)

    return 0


if __name__ == "__main__":
    sys.exit(main())
