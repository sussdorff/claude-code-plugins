#!/usr/bin/env python3
"""
Unit tests for the enforcement_matrix_scanner.py script.
Uses a mira-adapters-snapshot fixture to validate scanner output.
"""
import sys
import json
import subprocess
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
TESTS_DIR = SKILL_ROOT / "tests"
FIXTURE_DIR = TESTS_DIR / "fixtures" / "mira-adapters-snapshot"
SCANNER = SCRIPTS_DIR / "enforcement_matrix_scanner.py"


def run_scanner(args=None, fixture=None):
    """Run the scanner on the fixture directory, return (stdout, returncode)."""
    target = fixture or FIXTURE_DIR
    cmd = [sys.executable, str(SCANNER), str(target)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.returncode


def test_scanner_script_exists():
    assert SCANNER.exists(), f"Scanner script not found at {SCANNER}"


def test_scanner_produces_section_header():
    stdout, rc = run_scanner()
    assert rc == 0, f"Scanner exited with code {rc}"
    assert "## Enforcement Matrix" in stdout, "Output must contain '## Enforcement Matrix'"


def test_scanner_produces_contracts_as_rows():
    stdout, _ = run_scanner()
    assert "Error Envelope" in stdout, "Output must contain 'Error Envelope' contract row"
    assert "ID Taxonomy" in stdout, "Output must contain 'ID Taxonomy' contract row"
    assert "Schema Codegen" in stdout, "Output must contain 'Schema Codegen' contract row"


def test_scanner_produces_packages_as_columns():
    stdout, _ = run_scanner()
    assert "adapter-common" in stdout, "Output must contain 'adapter-common' package column"
    assert "pvs-x-isynet" in stdout, "Output must contain 'pvs-x-isynet' package column"


def test_scanner_gap_signal():
    stdout, _ = run_scanner()
    assert "Enforcement gaps:" in stdout, (
        "Output must contain 'Enforcement gaps: N' machine-readable signal line"
    )


def test_scanner_empty_matrix_when_no_adrs():
    """Scanner on a directory without docs/adr/ should produce the empty-matrix message."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        stdout, rc = run_scanner(fixture=Path(tmp))
    assert rc == 0, f"Scanner should exit 0 on empty repo, got {rc}"
    assert "No contracts declared yet" in stdout, (
        "Empty repo should output 'No contracts declared yet'"
    )
    assert "Enforcement gaps:" not in stdout, (
        "Empty matrix must NOT contain gap signal"
    )


def test_scanner_json_flag():
    """--json flag should output valid JSON with required keys."""
    stdout, rc = run_scanner(args=["--json"])
    assert rc == 0, f"Scanner --json exited with code {rc}"
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        assert False, f"--json output is not valid JSON: {e}\nOutput was:\n{stdout}"
    assert "contracts" in data, "JSON must contain 'contracts' key"
    assert "packages" in data, "JSON must contain 'packages' key"
    assert "matrix" in data, "JSON must contain 'matrix' key"
    assert "gaps" in data, "JSON must contain 'gaps' key"
    assert "gap_count" in data, "JSON must contain 'gap_count' key"
    assert "contract_count" in data, "JSON must contain 'contract_count' key"


def test_scanner_json_contains_correct_contracts():
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    contracts = data["contracts"]
    assert "Error Envelope" in contracts
    assert "ID Taxonomy" in contracts
    assert "Schema Codegen" in contracts
    assert len(contracts) == 3, f"Expected 3 contracts, got {len(contracts)}: {contracts}"


def test_scanner_json_contains_correct_packages():
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    packages = data["packages"]
    assert "adapter-common" in packages
    assert "adapter-cli" in packages
    assert "pvs-charly" in packages
    assert "pvs-x-isynet" in packages
    assert "pvs-xdt" in packages
    assert len(packages) == 5, f"Expected 5 packages, got {len(packages)}: {packages}"


def test_scanner_id_taxonomy_adapter_common_cell():
    """adapter-common should have full coverage for ID Taxonomy (ADR accepted, helper present)."""
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    cell = data["matrix"]["ID Taxonomy"]["adapter-common"]
    assert cell["adr"] == "✅", f"Expected ✅ for ADR, got {cell['adr']}"
    assert cell["helper"] == "✅", f"Expected ✅ for helper (id-taxonomy.ts), got {cell['helper']}"
    assert cell["reactive"] == "✅", f"Expected ✅ for reactive (check:ids script), got {cell['reactive']}"


def test_scanner_error_envelope_adapter_common_adr_proposed():
    """Error Envelope ADR is proposed — adapter-common should show ⚠️ for ADR."""
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    cell = data["matrix"]["Error Envelope"]["adapter-common"]
    assert cell["adr"] == "⚠️", f"Expected ⚠️ for proposed ADR, got {cell['adr']}"


def test_scanner_na_for_packages_not_in_applies_to():
    """adapter-cli is not in any applies_to list — all cells for it should be n/a."""
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    for contract in data["contracts"]:
        cell = data["matrix"][contract]["adapter-cli"]
        for col in ["adr", "helper", "proactive", "reactive"]:
            assert cell[col] == "n/a", (
                f"adapter-cli/{contract}/{col} should be n/a, got {cell[col]}"
            )


def test_scanner_pvs_x_isynet_id_taxonomy_full_coverage():
    """pvs-x-isynet has id-taxonomy helper, gen-schema.ts, eslint+schema:check — should be all ✅."""
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    cell = data["matrix"]["ID Taxonomy"]["pvs-x-isynet"]
    assert cell["adr"] == "✅"
    assert cell["helper"] == "✅"
    assert cell["proactive"] == "✅"
    assert cell["reactive"] == "✅"


def test_scanner_gap_count():
    """Gap count must be 5 (5 (contract, package) pairs with any ❌)."""
    stdout, _ = run_scanner(args=["--json"])
    data = json.loads(stdout)
    assert data["gap_count"] == 5, f"Expected gap_count=5, got {data['gap_count']}"


def test_scanner_golden_output():
    """Scanner output must match the expected-enforcement-matrix.md golden file."""
    golden_path = FIXTURE_DIR / "expected-enforcement-matrix.md"
    assert golden_path.exists(), f"Golden file not found at {golden_path}"
    expected = golden_path.read_text().strip()
    stdout, _ = run_scanner()
    actual = stdout.strip()
    assert actual == expected, (
        f"Scanner output does not match golden file.\n"
        f"--- Expected ---\n{expected}\n"
        f"--- Actual ---\n{actual}"
    )


def test_output_template_has_enforcement_matrix_section():
    """output-template.md must reference the Enforcement Matrix section."""
    template_path = SKILL_ROOT / "references" / "output-template.md"
    content = template_path.read_text()
    assert "Enforcement Matrix" in content, (
        "output-template.md must include Enforcement Matrix section"
    )


def test_skill_md_has_enforcement_matrix_phase():
    """SKILL.md workflow must include enforcement matrix phase."""
    skill_path = SKILL_ROOT / "SKILL.md"
    content = skill_path.read_text()
    assert "Enforcement Matrix" in content, (
        "SKILL.md must document the Enforcement Matrix phase"
    )
    assert "enforcement_matrix_scanner" in content, (
        "SKILL.md must reference enforcement_matrix_scanner.py"
    )


if __name__ == "__main__":
    import traceback

    tests = [
        test_scanner_script_exists,
        test_scanner_produces_section_header,
        test_scanner_produces_contracts_as_rows,
        test_scanner_produces_packages_as_columns,
        test_scanner_gap_signal,
        test_scanner_empty_matrix_when_no_adrs,
        test_scanner_json_flag,
        test_scanner_json_contains_correct_contracts,
        test_scanner_json_contains_correct_packages,
        test_scanner_id_taxonomy_adapter_common_cell,
        test_scanner_error_envelope_adapter_common_adr_proposed,
        test_scanner_na_for_packages_not_in_applies_to,
        test_scanner_pvs_x_isynet_id_taxonomy_full_coverage,
        test_scanner_gap_count,
        test_scanner_golden_output,
        test_output_template_has_enforcement_matrix_section,
        test_skill_md_has_enforcement_matrix_phase,
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
