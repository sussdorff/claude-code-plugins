"""
Bead Claim Gate
===============

Provides two public functions:
  - check_claim_status(bead_id, command_runner) -> dict
      Read-only probe. Returns execution-result envelope with current status.
  - claim_bead(bead_id, session_id, wave_id, run_id, command_runner) -> dict
      Attempts to claim an open bead by setting status=in_progress and writing
      metadata.claim. Returns execution-result envelope.

Both functions use the CommandRunner dependency-injection pattern so that
tests can mock bd calls without invoking the real binary.

Output conforms to core/contracts/execution-result.schema.json.
"""

from __future__ import annotations

import json
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# CommandRunner protocol + implementations
# ---------------------------------------------------------------------------


class CommandRunner(Protocol):
    """Injectable dependency for running subprocess commands."""

    def run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Run cmd and return the CompletedProcess result."""
        ...


@dataclass
class DefaultCommandRunner:
    """Production runner — invokes real subprocesses."""

    def run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True)


@dataclass
class MockCommandRunner:
    """
    Test runner — returns preset responses keyed on a prefix of the command.

    responses: mapping of "bd <subcommand> <first-arg>" → CompletedProcess.
    Tracks all calls in self.calls for assertion.
    """

    responses: dict[str, subprocess.CompletedProcess]
    calls: list[list[str]] = field(default_factory=list)

    def run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        self.calls.append(cmd)
        # Try progressively shorter prefixes to find a match
        for length in range(len(cmd), 0, -1):
            key = " ".join(cmd[:length])
            if key in self.responses:
                return self.responses[key]
        # Default: return empty success
        result = subprocess.CompletedProcess(args=cmd, returncode=0)
        result.stdout = ""
        result.stderr = ""
        return result


# ---------------------------------------------------------------------------
# Execution-result envelope helper
# ---------------------------------------------------------------------------

_SCHEMA_PATH = "core/contracts/execution-result.schema.json"
_PRODUCER = "claim.py"
_CONTRACT_VERSION = "1"


def _envelope(
    status: str,
    summary: str,
    data: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    next_steps: list[dict[str, Any]] | None = None,
    open_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a canonical execution-result envelope."""
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
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema": _SCHEMA_PATH,
        },
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _probe_bead(bead_id: str, runner: CommandRunner) -> tuple[str, dict]:
    """
    Query bead status via bd show --json.

    Returns (status, raw_bead_dict).
    status is "not_found" if bead doesn't exist, "bd_error" if bd failed.

    Real bd behavior:
    - Exit code 1 + JSON dict {"error": "..."} when bead not found
    - Exit code 0 + JSON list with bead record when found
    - Exit code 127 when bd binary is missing
    """
    result = runner.run(["bd", "show", bead_id, "--json"])

    if result.returncode not in (0, 1):
        # returncode 127 = command not found; other unexpected non-zero = bd error
        return "bd_error", {}

    # Exit code 1 or empty stdout → not found
    if result.returncode == 1 or not (result.stdout or "").strip():
        return "not_found", {}

    try:
        records = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return "bd_error", {}

    # bd returns {"error": "..."} dict when bead not found
    if isinstance(records, dict) and "error" in records:
        return "not_found", {}

    # Empty list → not found
    if isinstance(records, list) and len(records) == 0:
        return "not_found", {}

    if not isinstance(records, list):
        return "bd_error", {}

    bead = records[0]
    return bead.get("status", ""), bead


def _build_claim_meta(
    session_id: str,
    wave_id: str | None,
    run_id: str | None,
) -> dict[str, Any]:
    """Build the metadata.claim object (AK6)."""
    return {
        "claimed_by": session_id,
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "claim_host": socket.gethostname(),
        "wave_id": wave_id,
        "run_id": run_id,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_claim_status(
    bead_id: str,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """
    Read-only probe — returns current bead status without side effects.

    Returns:
      status=ok      → bead is open (claimable)
      status=warning → bead is in_progress or closed (not claimable)
      status=error   → bd binary missing, bead not found, or other failure
    """
    runner = command_runner or DefaultCommandRunner()
    current_status, bead = _probe_bead(bead_id, runner)

    if current_status == "bd_error":
        return _envelope(
            status="error",
            summary=f"bd command failed for bead {bead_id}",
            data={"bead_id": bead_id, "current_status": "unknown"},
            errors=[{
                "code": "BD_ERROR",
                "message": f"bd show {bead_id} --json failed (bd not found or returned error)",
                "retryable": False,
            }],
        )

    if current_status == "not_found":
        return _envelope(
            status="error",
            summary=f"Bead {bead_id} not found",
            data={"bead_id": bead_id, "current_status": "not_found"},
            errors=[{
                "code": "BEAD_NOT_FOUND",
                "message": f"No bead with id '{bead_id}' found",
                "retryable": False,
            }],
        )

    if current_status in ("in_progress", "closed"):
        return _envelope(
            status="warning",
            summary=f"Bead {bead_id} is {current_status} — not claimable",
            data={"bead_id": bead_id, "current_status": current_status},
        )

    return _envelope(
        status="ok",
        summary=f"Bead {bead_id} is open — ready to claim",
        data={"bead_id": bead_id, "current_status": current_status},
    )


def claim_bead(
    bead_id: str,
    session_id: str,
    wave_id: str | None = None,
    run_id: str | None = None,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """
    Attempt to claim an open bead.

    Performs:
      1. Probe current status (read-only)
      2. If not open → return error envelope (no side effects)
      3. If open → bd update --status=in_progress --assignee=<session_id> --metadata=<json>
      4. bd dolt commit && bd dolt pull && bd dolt push --force

    Returns execution-result envelope conforming to execution-result.schema.json.
    """
    runner = command_runner or DefaultCommandRunner()

    # Step 1: probe
    current_status, bead = _probe_bead(bead_id, runner)

    if current_status == "bd_error":
        return _envelope(
            status="error",
            summary=f"bd command failed while probing {bead_id}",
            data={"bead_id": bead_id, "current_status": "unknown"},
            errors=[{
                "code": "BD_ERROR",
                "message": f"bd show {bead_id} --json failed (bd not found or returned error)",
                "retryable": False,
            }],
        )

    if current_status == "not_found":
        return _envelope(
            status="error",
            summary=f"Bead {bead_id} not found",
            data={"bead_id": bead_id, "current_status": "not_found"},
            errors=[{
                "code": "BEAD_NOT_FOUND",
                "message": f"No bead with id '{bead_id}' found",
                "retryable": False,
            }],
        )

    # Step 2: guard against already-active states
    if current_status == "in_progress":
        return _envelope(
            status="error",
            summary=f"Bead {bead_id} is already in_progress — refusing claim",
            data={"bead_id": bead_id, "current_status": "in_progress"},
            errors=[{
                "code": "ALREADY_CLAIMED",
                "message": f"Bead {bead_id} is already in_progress.",
                "retryable": False,
                "suggested_fix": f"bd update {bead_id} --status=open",
            }],
        )

    if current_status == "closed":
        return _envelope(
            status="error",
            summary=f"Bead {bead_id} is closed — cannot claim",
            data={"bead_id": bead_id, "current_status": "closed"},
            errors=[{
                "code": "BEAD_CLOSED",
                "message": f"Bead {bead_id} is closed and cannot be claimed.",
                "retryable": False,
                "suggested_fix": f"bd update {bead_id} --status=open  # reopen first",
            }],
        )

    # Step 3: build claim metadata and update bead
    claim_meta = _build_claim_meta(session_id=session_id, wave_id=wave_id, run_id=run_id)
    claim_meta_json = json.dumps({"claim": claim_meta})

    update_result = runner.run([
        "bd", "update", bead_id,
        f"--assignee={session_id}",
        "--status=in_progress",
        f"--metadata={claim_meta_json}",
    ])

    if update_result.returncode != 0:
        return _envelope(
            status="error",
            summary=f"bd update failed for bead {bead_id}",
            data={"bead_id": bead_id, "current_status": current_status},
            errors=[{
                "code": "BD_UPDATE_FAILED",
                "message": f"bd update {bead_id} exited {update_result.returncode}: "
                           f"{update_result.stderr}",
                "retryable": True,
            }],
        )

    # Step 4: dolt sync
    runner.run(["bd", "dolt", "commit", "-m", f"claim: {bead_id} by {session_id}"])
    runner.run(["bd", "dolt", "pull"])
    push_result = runner.run(["bd", "dolt", "push", "--force"])

    result = _envelope(
        status="ok",
        summary=f"Bead {bead_id} claimed by {session_id}",
        data={
            "bead_id": bead_id,
            "current_status": "in_progress",
            "assignee": session_id,
            "claim": claim_meta,
        },
        next_steps=[{
            "id": "proceed",
            "summary": f"Proceed with implementation of {bead_id}",
            "priority": "now",
            "automatable": True,
        }],
    )

    if push_result.returncode != 0:
        # Claim recorded locally but sync failed — add warning so caller can retry push
        result["status"] = "warning"
        result["errors"].append({
            "code": "DOLT_SYNC_FAILED",
            "message": f"Claim recorded locally but dolt push failed: {push_result.stderr}",
            "retryable": True,
            "suggested_fix": "Run: bd dolt pull && bd dolt push --force",
        })

    return result
