#!/usr/bin/env python3
"""
claim-bead.py — CLI wrapper for the claim gate.

Usage:
    python3 claim-bead.py <bead-id> [--check-only] [--json-only]
                          [--session-id ID] [--wave-id ID] [--run-id ID]

Flags:
    --check-only    Read-only status probe (does not claim the bead)
    --json-only     Suppress the human-readable first line, emit only JSON
    --session-id    Session ID to record as claimed_by (default: hostname+pid)
    --wave-id       Wave ID to record in claim metadata (default: None)
    --run-id        Run ID to record in claim metadata (default: None)

Output:
    Line 1 (unless --json-only): Human-readable summary
              "✓ CLAIMED <id> (run_id=..., assignee=..., wave=...)"
           or "✗ ABORT <id>: <reason>. To take over: bd update <id> --status=open"
           or (for check-only): "✓ STATUS <id>: open" / "⚠ STATUS <id>: in_progress"
    Line 2+: JSON execution-result envelope

Exit codes:
    0  Always (unless bd binary crashes or real exception — see below)
    2  Reserved for callers (e.g. cld) to use as a refusal signal
       Claim-bead.py itself always exits 0 unless the tool itself crashes;
       the caller reads the JSON status field.

Stdlib only — no external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path

# Locate claim module: prefer repo-local (worktree), then installed ~/.claude
_REPO_ROOTS = [
    Path(__file__).parent.parent / "lib" / "orchestrator",           # repo-local
    Path.home() / ".claude" / "plugins" / "cache",                   # installed (search)
]

_claim_module_dir: Path | None = None
for _candidate in _REPO_ROOTS:
    if _candidate.is_dir() and (_candidate / "claim.py").exists():
        _claim_module_dir = _candidate
        break

if _claim_module_dir is None:
    # Try searching installed plugins
    _search_root = Path.home() / ".claude" / "plugins"
    if _search_root.is_dir():
        for _p in _search_root.rglob("claim.py"):
            _claim_module_dir = _p.parent
            break

if _claim_module_dir is not None:
    sys.path.insert(0, str(_claim_module_dir))

try:
    from claim import check_claim_status, claim_bead
except ImportError as exc:
    # Emit error envelope and exit
    _err = {
        "status": "error",
        "summary": "claim.py module not found — cannot run claim gate",
        "data": {"bead_id": "unknown"},
        "errors": [{
            "code": "MODULE_NOT_FOUND",
            "message": str(exc),
            "retryable": False,
            "suggested_fix": "Ensure claim.py is in beads-workflow/lib/orchestrator/",
        }],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": "claim-bead.py",
            "schema": "core/contracts/execution-result.schema.json",
        },
    }
    print("✗ ABORT: claim.py module not found", file=sys.stderr)
    print(json.dumps(_err))
    sys.exit(0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_session_id() -> str:
    """Generate a default session ID from hostname + PID."""
    return f"session-{socket.gethostname()}-{os.getpid()}"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Claim a bead or probe its current status.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("bead_id", help="Bead ID to claim or probe")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Read-only probe — do not claim the bead",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Suppress human-readable first line; emit only the JSON envelope",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session ID to record as claimed_by (default: hostname+pid)",
    )
    parser.add_argument(
        "--wave-id",
        default=None,
        help="Wave ID to record in claim metadata",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run ID to record in claim metadata",
    )
    return parser.parse_args(argv)


def _human_line_check(bead_id: str, envelope: dict) -> str:
    """Format first line for --check-only output."""
    status = envelope.get("status", "")
    data = envelope.get("data", {})
    current = data.get("current_status", "unknown")
    if status == "ok":
        return f"✓ STATUS {bead_id}: {current}"
    if status == "warning":
        return f"⚠ STATUS {bead_id}: {current}"
    return f"✗ ERROR {bead_id}: {envelope.get('summary', 'error')}"


def _human_line_claim(bead_id: str, envelope: dict) -> str:
    """Format first line for claim output."""
    status = envelope.get("status", "")
    data = envelope.get("data", {})
    errors = envelope.get("errors", [])

    if status == "ok":
        claim_meta = data.get("claim", {})
        run_id = claim_meta.get("run_id", "")
        assignee = data.get("assignee", "")
        wave_id = claim_meta.get("wave_id", "")
        parts = []
        if run_id:
            parts.append(f"run_id={run_id}")
        if assignee:
            parts.append(f"assignee={assignee}")
        if wave_id:
            parts.append(f"wave={wave_id}")
        detail = f" ({', '.join(parts)})" if parts else ""
        return f"✓ CLAIMED {bead_id}{detail}"

    # error / warning
    summary = envelope.get("summary", "")
    suggested_fix = ""
    if errors:
        suggested_fix = errors[0].get("suggested_fix", "")

    line = f"✗ ABORT {bead_id}: {summary}"
    if suggested_fix:
        line += f". To take over: {suggested_fix}"
    return line


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    session_id = args.session_id or _default_session_id()

    if args.check_only:
        envelope = check_claim_status(bead_id=args.bead_id)
        if not args.json_only:
            print(_human_line_check(args.bead_id, envelope))
    else:
        envelope = claim_bead(
            bead_id=args.bead_id,
            session_id=session_id,
            wave_id=args.wave_id,
            run_id=args.run_id,
        )
        if not args.json_only:
            print(_human_line_claim(args.bead_id, envelope))

    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
