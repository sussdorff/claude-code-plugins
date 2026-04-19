#!/usr/bin/env python3
"""
Unit tests for adr-hoist-check.py.
Uses the adr-gap-mira fixture to validate hoist detection and pre-trinity reporting.
"""
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
PLUGIN_ROOT = SKILL_ROOT.parent.parent
FIXTURE_DIR = SKILL_ROOT / "tests" / "fixtures" / "adr-gap-mira"
CHECKER = PLUGIN_ROOT / "scripts" / "adr-hoist-check.py"


def run_checker(args=None, fixture=None):
    """Run adr-hoist-check.py on a fixture directory, return (stdout, stderr, returncode)."""
    target = fixture or FIXTURE_DIR
    cmd = ["uv", "run", str(CHECKER), str(target)] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# 1. Script exists
# ---------------------------------------------------------------------------

def test_script_exists():
    assert CHECKER.exists(), f"Script not found at {CHECKER}"


# ---------------------------------------------------------------------------
# 2. Condition true: report HOIST DUE + bead title
# ---------------------------------------------------------------------------

def test_condition_true_no_bead_reports_hoist_due():
    """Run on fixture (2 packages implement id-taxonomy, no --create-beads).
    stdout must contain 'HOIST DUE' and the trigger bead title."""
    stdout, stderr, rc = run_checker()
    assert rc == 0, f"Expected exit 0, got {rc}\nstderr: {stderr}"
    assert "HOIST DUE" in stdout, f"Expected 'HOIST DUE' in output:\n{stdout}"
    assert "[HOIST] makeIdHelper to adapter-common" in stdout, (
        f"Expected bead title in output:\n{stdout}"
    )


# ---------------------------------------------------------------------------
# 3. Evidence listed
# ---------------------------------------------------------------------------

def test_condition_true_reports_evidence():
    """pvs-charly should appear in the output as evidence of the second implementor."""
    stdout, stderr, rc = run_checker()
    assert "pvs-charly" in stdout, (
        f"Expected 'pvs-charly' in output as evidence:\n{stdout}"
    )


# ---------------------------------------------------------------------------
# 4. Pre-trinity packages listed
# ---------------------------------------------------------------------------

def test_pre_trinity_packages_listed():
    """adapter-common has no contracts.yml linking it to any ADR's applies_to/target.
    It should appear in the pre-trinity packages section."""
    stdout, stderr, rc = run_checker()
    assert "adapter-common" in stdout, (
        f"Expected 'adapter-common' in pre-trinity section:\n{stdout}"
    )


# ---------------------------------------------------------------------------
# 5. ADR without hoist_when is skipped silently
# ---------------------------------------------------------------------------

def test_no_hoist_when_block_skipped():
    """An ADR with no hoist_when block should be skipped without error."""
    tmp = tempfile.mkdtemp()
    try:
        root = Path(tmp)
        (root / "docs" / "adr").mkdir(parents=True)
        (root / "docs" / "adr" / "ADR-002-no-hoist.md").write_text(
            "---\nstatus: accepted\ncontract: other-contract\napplies_to: [some-package]\n---\n\n# ADR-002\n"
        )
        (root / "packages" / "some-package").mkdir(parents=True)
        stdout, stderr, rc = run_checker(fixture=root)
        assert rc == 0, f"Expected exit 0, got {rc}\nstderr: {stderr}"
        assert "error" not in stderr.lower(), (
            f"Expected no errors for ADR without hoist_when:\n{stderr}"
        )
    finally:
        shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# 6. Malformed frontmatter reports error
# ---------------------------------------------------------------------------

def test_malformed_frontmatter_reports_error():
    """An ADR with malformed YAML frontmatter should print an error with the file path."""
    tmp = tempfile.mkdtemp()
    try:
        root = Path(tmp)
        (root / "docs" / "adr").mkdir(parents=True)
        bad_adr = root / "docs" / "adr" / "ADR-BAD.md"
        bad_adr.write_text(
            "---\nstatus: [unclosed bracket\nhoist_when:\n  condition: x\n---\n"
        )
        stdout, stderr, rc = run_checker(fixture=root)
        combined = stdout + stderr
        assert "ADR-BAD.md" in combined, (
            f"Expected file path in error output:\n{combined}"
        )
    finally:
        shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# 7. Unknown condition prints warning
# ---------------------------------------------------------------------------

def test_unknown_condition_warning():
    """An ADR with an unknown condition string should produce a warning."""
    tmp = tempfile.mkdtemp()
    try:
        root = Path(tmp)
        (root / "docs" / "adr").mkdir(parents=True)
        (root / "docs" / "adr" / "ADR-UNKNOWN.md").write_text(
            "---\nstatus: accepted\ncontract: some-contract\napplies_to: [pkg-a]\nhoist_when:\n  condition: nonexistent_evaluator\n  contract: some-contract\n  trigger_bead_title: '[HOIST] test'\n---\n"
        )
        (root / "packages" / "pkg-a").mkdir(parents=True)
        stdout, stderr, rc = run_checker(fixture=root)
        combined = stdout + stderr
        assert "unknown" in combined.lower() or "warning" in combined.lower(), (
            f"Expected warning for unknown condition:\n{combined}"
        )
    finally:
        shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# 8. Condition false: no HOIST DUE
# ---------------------------------------------------------------------------

def test_condition_false_no_report():
    """If only one package implements the contract (only pvs-x-isynet, no pvs-charly),
    the condition is false and no 'HOIST DUE' should appear."""
    tmp = tempfile.mkdtemp()
    try:
        root = Path(tmp)
        (root / "docs" / "adr").mkdir(parents=True)
        (root / "docs" / "adr" / "ADR-001-id-taxonomy.md").write_text(
            "---\nstatus: accepted\ncontract: id-taxonomy\napplies_to: [pvs-x-isynet]\nhoist_when:\n  condition: second_package_implements_contract\n  contract: id-taxonomy\n  target: adapter-common\n  trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'\n---\n"
        )
        # Only one package implements the contract (same as applies_to)
        (root / "packages" / "pvs-x-isynet").mkdir(parents=True)
        (root / "packages" / "pvs-x-isynet" / "contracts.yml").write_text("- id-taxonomy\n")
        stdout, stderr, rc = run_checker(fixture=root)
        assert "HOIST DUE" not in stdout, (
            f"Expected no 'HOIST DUE' when condition is false:\n{stdout}"
        )
    finally:
        shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# 9. Idempotent (no side effects without --create-beads)
# ---------------------------------------------------------------------------

def test_idempotent_no_create_beads():
    """Running the checker twice in report mode must produce the same output (no side effects)."""
    stdout1, stderr1, rc1 = run_checker()
    stdout2, stderr2, rc2 = run_checker()
    assert rc1 == rc2, f"Return codes differ: {rc1} vs {rc2}"
    assert stdout1 == stdout2, (
        f"Output differs between runs (not idempotent):\n--- Run 1 ---\n{stdout1}\n--- Run 2 ---\n{stdout2}"
    )


# ---------------------------------------------------------------------------
# 10. adr-gap.sh smoke test — invokes the shell runner directly
# ---------------------------------------------------------------------------

def test_adr_gap_sh_smoke():
    """adr-gap.sh must resolve adr-hoist-check.py correctly, exit 0, and
    report 'HOIST DUE' when run on the adr-gap-mira fixture."""
    shell_script = SKILL_ROOT / "scripts" / "adr-gap.sh"
    assert shell_script.exists(), f"adr-gap.sh not found at {shell_script}"
    result = subprocess.run(
        [str(shell_script), str(FIXTURE_DIR)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"adr-gap.sh exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "HOIST DUE" in result.stdout, (
        f"Expected 'HOIST DUE' in adr-gap.sh output:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        test_script_exists,
        test_condition_true_no_bead_reports_hoist_due,
        test_condition_true_reports_evidence,
        test_pre_trinity_packages_listed,
        test_no_hoist_when_block_skipped,
        test_malformed_frontmatter_reports_error,
        test_unknown_condition_warning,
        test_condition_false_no_report,
        test_idempotent_no_create_beads,
        test_adr_gap_sh_smoke,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} — {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
