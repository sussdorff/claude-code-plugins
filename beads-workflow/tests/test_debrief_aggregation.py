#!/usr/bin/env python3
"""
test_debrief_aggregation — Tests for parse_debrief.py and aggregate_debriefs.py.

Run with:
    python3 beads-workflow/tests/test_debrief_aggregation.py

Exit code 0 on success, 1 on failure.

Tests:
  1. Two mock subagent outputs with valid ### Debrief blocks → parse each → aggregate
     → correct merged result
  2. Subagent output with no ### Debrief heading → parse_debrief exits 1 → graceful handling
  3. Empty aggregate → correct empty JSON output
"""

import json
import subprocess
import sys
from pathlib import Path

# Locate the scripts relative to this test file
_ROOT = Path(__file__).resolve().parent.parent
_PARSE_DEBRIEF = _ROOT / "lib" / "orchestrator" / "parse_debrief.py"
_AGGREGATE_DEBRIEFS = _ROOT / "lib" / "orchestrator" / "aggregate_debriefs.py"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AGENT_OUTPUT_1 = """
Some preamble text from the agent.

### Debrief

#### Key Decisions
- Used Python stdlib only to keep scripts portable
- Chose fixed handoff path over env-var to reduce coupling

#### Challenges Encountered
- Parsing markdown with regex is fragile for nested headings

#### Surprising Findings
- The parse_debrief.py already existed with the right interface

#### Follow-up Items
- Consider adding JSON schema validation to the handoff file
"""

AGENT_OUTPUT_2 = """
Implementation complete.

### Debrief

#### Key Decisions
- Extended Context Threading section rather than adding a new top-level section

#### Challenges Encountered
- Phase 16 required careful placement to not disrupt fallback logic

#### Surprising Findings

#### Follow-up Items
- Verify that session-close consumes the handoff correctly in an end-to-end run
- Check if older worktrees need migration guidance
"""

AGENT_OUTPUT_NO_DEBRIEF = """
This agent output has no debrief section at all.
Just regular content.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_parse_debrief(text: str) -> tuple[int, str, str]:
    """Run parse_debrief.py with text on stdin. Returns (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(_PARSE_DEBRIEF)],
        input=text,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def run_aggregate_debriefs(data: list) -> tuple[int, str, str]:
    """Run aggregate_debriefs.py with a JSON array on stdin."""
    result = subprocess.run(
        [sys.executable, str(_AGGREGATE_DEBRIEFS)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_two_debriefs_parse_and_aggregate():
    """Two valid debrief outputs parse correctly and aggregate into merged result."""
    rc1, out1, err1 = run_parse_debrief(AGENT_OUTPUT_1)
    assert rc1 == 0, f"parse_debrief failed for output 1 (rc={rc1}): {err1}"

    rc2, out2, err2 = run_parse_debrief(AGENT_OUTPUT_2)
    assert rc2 == 0, f"parse_debrief failed for output 2 (rc={rc2}): {err2}"

    debrief1 = json.loads(out1)
    debrief2 = json.loads(out2)

    # Verify individual parse results
    assert "Used Python stdlib only to keep scripts portable" in debrief1["key_decisions"]
    assert "Chose fixed handoff path over env-var to reduce coupling" in debrief1["key_decisions"]
    assert "Parsing markdown with regex is fragile for nested headings" in debrief1["challenges_encountered"]
    assert "Consider adding JSON schema validation to the handoff file" in debrief1["follow_up_items"]

    assert "Extended Context Threading section rather than adding a new top-level section" in debrief2["key_decisions"]
    assert debrief2["surprising_findings"] == []  # empty section

    # Aggregate both
    rc_agg, out_agg, err_agg = run_aggregate_debriefs([debrief1, debrief2])
    assert rc_agg == 0, f"aggregate_debriefs failed (rc={rc_agg}): {err_agg}"

    merged = json.loads(out_agg)

    # All key_decisions from both agents
    assert "Used Python stdlib only to keep scripts portable" in merged["key_decisions"]
    assert "Extended Context Threading section rather than adding a new top-level section" in merged["key_decisions"]
    assert len(merged["key_decisions"]) == 3  # 2 from agent1, 1 from agent2

    # Challenges merged
    assert "Parsing markdown with regex is fragile for nested headings" in merged["challenges_encountered"]
    assert "Phase 16 required careful placement to not disrupt fallback logic" in merged["challenges_encountered"]
    assert len(merged["challenges_encountered"]) == 2

    # Surprising findings: only agent1 had one, agent2 had empty
    assert "The parse_debrief.py already existed with the right interface" in merged["surprising_findings"]
    assert len(merged["surprising_findings"]) == 1

    # Follow-up items merged
    assert "Consider adding JSON schema validation to the handoff file" in merged["follow_up_items"]
    assert "Verify that session-close consumes the handoff correctly in an end-to-end run" in merged["follow_up_items"]
    assert "Check if older worktrees need migration guidance" in merged["follow_up_items"]
    assert len(merged["follow_up_items"]) == 3

    print("PASS: test_two_debriefs_parse_and_aggregate")


def test_no_debrief_heading_exits_1():
    """Agent output without ### Debrief heading causes parse_debrief to exit 1."""
    rc, out, err = run_parse_debrief(AGENT_OUTPUT_NO_DEBRIEF)
    assert rc == 1, f"Expected exit code 1, got {rc}"
    assert out == "", f"Expected empty stdout, got: {out!r}"
    assert len(err) > 0, "Expected error message on stderr"

    # Graceful handling: orchestrator should skip this (rc != 0 → skip)
    # Verify that if we ignore it, the aggregate still works with empty input
    rc_agg, out_agg, err_agg = run_aggregate_debriefs([])
    assert rc_agg == 0, f"aggregate_debriefs failed on empty list: {err_agg}"
    merged = json.loads(out_agg)
    assert merged["key_decisions"] == []

    print("PASS: test_no_debrief_heading_exits_1")


def test_empty_aggregate():
    """Empty input array produces correct empty JSON output."""
    rc, out, err = run_aggregate_debriefs([])
    assert rc == 0, f"aggregate_debriefs failed (rc={rc}): {err}"

    merged = json.loads(out)
    assert merged == {
        "key_decisions": [],
        "challenges_encountered": [],
        "surprising_findings": [],
        "follow_up_items": [],
    }, f"Unexpected output for empty aggregate: {merged}"

    print("PASS: test_empty_aggregate")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    """Run all tests and exit 0 on success, 1 on any failure."""
    tests = [
        test_two_debriefs_parse_and_aggregate,
        test_no_debrief_heading_exits_1,
        test_empty_aggregate,
    ]

    failures = []
    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as exc:
            print(f"FAIL: {test_fn.__name__}: {exc}", file=sys.stderr)
            failures.append(test_fn.__name__)
        except Exception as exc:
            print(f"ERROR: {test_fn.__name__}: {exc}", file=sys.stderr)
            failures.append(test_fn.__name__)

    if failures:
        print(f"\n{len(failures)} test(s) failed: {failures}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed.")


if __name__ == "__main__":
    main()
