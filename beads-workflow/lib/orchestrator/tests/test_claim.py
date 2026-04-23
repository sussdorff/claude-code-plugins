#!/usr/bin/env python3
"""
Test suite for claim.py — bead claim gate module.

Tests:
  1. Successful claim — returns ok envelope with metadata.claim fields
  2. Already-in-progress refusal — returns error envelope
  3. Closed-bead refusal — returns error envelope
  4. Not-found handling — returns error envelope
  5. Concurrent claim race — two processes claim same bead, only one wins

Run with:
    python3 -m pytest beads-workflow/lib/orchestrator/tests/test_claim.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# Allow importing the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))

import claim as claim_module
from claim import (
    ClaimResult,
    CommandRunner,
    MockCommandRunner,
    check_claim_status,
    claim_bead,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed_process(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    """Build a minimal CompletedProcess for use in mock responses."""
    result = subprocess.CompletedProcess(args=[], returncode=returncode)
    result.stdout = stdout
    result.stderr = ""
    return result


def _bd_show_json(status: str, bead_id: str = "test-1") -> str:
    """Return a minimal bd show --json response."""
    return json.dumps([{
        "id": bead_id,
        "status": status,
        "assignee": "",
        "metadata": {}
    }])


def _bd_show_not_found() -> str:
    """Return an empty bd show --json response (bead not found)."""
    return json.dumps([])


# ---------------------------------------------------------------------------
# AK1 / AK6: Successful claim
# ---------------------------------------------------------------------------

class TestSuccessfulClaim(unittest.TestCase):
    """Successful claim sets metadata.claim and bd assignee."""

    def setUp(self):
        """Set up a mock runner that simulates a successful claim flow."""
        # Responses keyed on the first argument of the command list
        self.runner = MockCommandRunner(responses={
            # check status: bead is open
            "bd show test-1 --json": _make_completed_process(_bd_show_json("open", "test-1")),
            # bd update --assignee --status
            "bd update test-1": _make_completed_process(""),
            # dolt commit
            "bd dolt commit": _make_completed_process(""),
            # dolt pull
            "bd dolt pull": _make_completed_process(""),
            # dolt push
            "bd dolt push": _make_completed_process(""),
        })

    def test_claim_returns_ok_envelope(self):
        """claim_bead() on an open bead returns status=ok."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            wave_id="wave-1",
            run_id="run-xyz",
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "ok")

    def test_claim_envelope_has_required_fields(self):
        """ok envelope has all required execution-result fields."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            command_runner=self.runner,
        )
        for field in ["status", "summary", "data", "errors", "next_steps", "open_items", "meta"]:
            self.assertIn(field, result, f"Missing field: {field}")

    def test_claim_data_contains_claim_metadata(self):
        """data.claim contains all required AK6 fields."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            wave_id="wave-1",
            run_id="run-xyz",
            command_runner=self.runner,
        )
        claim_meta = result["data"].get("claim", {})
        self.assertEqual(claim_meta["claimed_by"], "session-abc")
        self.assertEqual(claim_meta["wave_id"], "wave-1")
        self.assertEqual(claim_meta["run_id"], "run-xyz")
        self.assertIn("claimed_at", claim_meta)
        self.assertIn("claim_host", claim_meta)

    def test_claim_data_bead_id(self):
        """data.bead_id is set correctly."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertEqual(result["data"]["bead_id"], "test-1")

    def test_claim_wave_id_nullable(self):
        """wave_id=None is allowed and stored as null in claim metadata."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            wave_id=None,
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["data"]["claim"]["wave_id"])

    def test_claim_meta_producer(self):
        """meta.producer is set to 'claim.py'."""
        result = claim_bead(
            bead_id="test-1",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertEqual(result["meta"]["producer"], "claim.py")


# ---------------------------------------------------------------------------
# AK7 (test 2): Already-in-progress refusal
# ---------------------------------------------------------------------------

class TestInProgressRefusal(unittest.TestCase):
    """claim_bead() refuses when bead is already in_progress."""

    def setUp(self):
        self.runner = MockCommandRunner(responses={
            "bd show test-2 --json": _make_completed_process(
                _bd_show_json("in_progress", "test-2")
            ),
        })

    def test_refusal_returns_error_status(self):
        """claim_bead on in_progress bead returns status=error."""
        result = claim_bead(
            bead_id="test-2",
            session_id="session-xyz",
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "error")

    def test_refusal_error_code(self):
        """Error code is ALREADY_CLAIMED."""
        result = claim_bead(
            bead_id="test-2",
            session_id="session-xyz",
            command_runner=self.runner,
        )
        self.assertTrue(len(result["errors"]) > 0)
        self.assertEqual(result["errors"][0]["code"], "ALREADY_CLAIMED")

    def test_refusal_suggested_fix(self):
        """Error includes suggested_fix to reset status."""
        result = claim_bead(
            bead_id="test-2",
            session_id="session-xyz",
            command_runner=self.runner,
        )
        fix = result["errors"][0].get("suggested_fix", "")
        self.assertIn("bd update test-2 --status=open", fix)

    def test_refusal_data_contains_current_status(self):
        """data.current_status is 'in_progress'."""
        result = claim_bead(
            bead_id="test-2",
            session_id="session-xyz",
            command_runner=self.runner,
        )
        self.assertEqual(result["data"]["current_status"], "in_progress")


# ---------------------------------------------------------------------------
# AK7 (test 3): Closed-bead refusal
# ---------------------------------------------------------------------------

class TestClosedBeadRefusal(unittest.TestCase):
    """claim_bead() refuses when bead is closed."""

    def setUp(self):
        self.runner = MockCommandRunner(responses={
            "bd show test-3 --json": _make_completed_process(
                _bd_show_json("closed", "test-3")
            ),
        })

    def test_closed_bead_returns_error(self):
        """claim_bead on closed bead returns status=error."""
        result = claim_bead(
            bead_id="test-3",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "error")

    def test_closed_bead_error_code(self):
        """Error code is BEAD_CLOSED."""
        result = claim_bead(
            bead_id="test-3",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertTrue(len(result["errors"]) > 0)
        self.assertEqual(result["errors"][0]["code"], "BEAD_CLOSED")

    def test_closed_bead_data_current_status(self):
        """data.current_status is 'closed'."""
        result = claim_bead(
            bead_id="test-3",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertEqual(result["data"]["current_status"], "closed")


# ---------------------------------------------------------------------------
# AK7 (test 4): Not-found handling
# ---------------------------------------------------------------------------

class TestNotFoundHandling(unittest.TestCase):
    """claim_bead() returns error when bead not found (empty json array)."""

    def setUp(self):
        self.runner = MockCommandRunner(responses={
            "bd show ghost-99 --json": _make_completed_process(_bd_show_not_found()),
        })

    def test_not_found_returns_error(self):
        """claim_bead on nonexistent bead returns status=error."""
        result = claim_bead(
            bead_id="ghost-99",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "error")

    def test_not_found_error_code(self):
        """Error code is BEAD_NOT_FOUND."""
        result = claim_bead(
            bead_id="ghost-99",
            session_id="session-abc",
            command_runner=self.runner,
        )
        self.assertTrue(len(result["errors"]) > 0)
        self.assertEqual(result["errors"][0]["code"], "BEAD_NOT_FOUND")


# ---------------------------------------------------------------------------
# AK7 (test 4 alt): bd binary not found
# ---------------------------------------------------------------------------

class TestBdBinaryNotFound(unittest.TestCase):
    """check_claim_status() returns error when bd binary is not found."""

    def setUp(self):
        self.runner = MockCommandRunner(responses={
            "bd show nobd-1 --json": _make_completed_process("", returncode=127),
        })

    def test_bd_not_found_returns_error(self):
        """check_claim_status when bd exits 127 returns status=error."""
        result = check_claim_status(
            bead_id="nobd-1",
            command_runner=self.runner,
        )
        self.assertEqual(result["status"], "error")


# ---------------------------------------------------------------------------
# AK7 (test 5): Concurrent claim race
# ---------------------------------------------------------------------------

class TestConcurrentClaimRace(unittest.TestCase):
    """Two processes claim same bead; second one is refused."""

    def test_first_claim_wins_second_refused(self):
        """
        Simulate race: process A claims successfully, then process B
        sees in_progress and is refused.
        """
        # Process A: bead is open → claims successfully
        runner_a = MockCommandRunner(responses={
            "bd show race-1 --json": _make_completed_process(_bd_show_json("open", "race-1")),
            "bd update race-1": _make_completed_process(""),
            "bd dolt commit": _make_completed_process(""),
            "bd dolt pull": _make_completed_process(""),
            "bd dolt push": _make_completed_process(""),
        })
        result_a = claim_bead(
            bead_id="race-1",
            session_id="session-A",
            command_runner=runner_a,
        )
        self.assertEqual(result_a["status"], "ok", "First claimant should succeed")

        # Process B: by now bead is in_progress → refused
        runner_b = MockCommandRunner(responses={
            "bd show race-1 --json": _make_completed_process(
                _bd_show_json("in_progress", "race-1")
            ),
        })
        result_b = claim_bead(
            bead_id="race-1",
            session_id="session-B",
            command_runner=runner_b,
        )
        self.assertEqual(result_b["status"], "error", "Second claimant should be refused")
        self.assertEqual(result_b["errors"][0]["code"], "ALREADY_CLAIMED")


# ---------------------------------------------------------------------------
# check_claim_status (read-only probe)
# ---------------------------------------------------------------------------

class TestCheckClaimStatus(unittest.TestCase):
    """check_claim_status() returns envelope with current status, no side effects."""

    def test_open_bead_status(self):
        """check_claim_status on open bead returns ok + status=open."""
        runner = MockCommandRunner(responses={
            "bd show probe-1 --json": _make_completed_process(_bd_show_json("open", "probe-1")),
        })
        result = check_claim_status(bead_id="probe-1", command_runner=runner)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["current_status"], "open")

    def test_in_progress_bead_status(self):
        """check_claim_status on in_progress bead returns warning."""
        runner = MockCommandRunner(responses={
            "bd show probe-2 --json": _make_completed_process(
                _bd_show_json("in_progress", "probe-2")
            ),
        })
        result = check_claim_status(bead_id="probe-2", command_runner=runner)
        self.assertEqual(result["status"], "warning")

    def test_closed_bead_status(self):
        """check_claim_status on closed bead returns warning."""
        runner = MockCommandRunner(responses={
            "bd show probe-3 --json": _make_completed_process(
                _bd_show_json("closed", "probe-3")
            ),
        })
        result = check_claim_status(bead_id="probe-3", command_runner=runner)
        self.assertEqual(result["status"], "warning")

    def test_no_bd_calls_for_update(self):
        """check_claim_status does NOT call bd update (read-only)."""
        runner = MockCommandRunner(responses={
            "bd show probe-4 --json": _make_completed_process(_bd_show_json("open", "probe-4")),
        })
        check_claim_status(bead_id="probe-4", command_runner=runner)
        # Only bd show should have been called — not bd update
        update_calls = [c for c in runner.calls if "bd update" in " ".join(c)]
        self.assertEqual(len(update_calls), 0, "check_claim_status must not call bd update")


if __name__ == "__main__":
    unittest.main()
