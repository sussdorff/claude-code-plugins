#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0"
# ]
# ///
"""
adr-hoist-check.py — Detect ADR hoist debt and pre-trinity packages.

Usage:
    uv run adr-hoist-check.py <repo_root> [--create-beads] [--ci] [--allow-unknown]

Walks docs/adr/*.md in repo_root, parses YAML frontmatter, evaluates hoist_when
conditions, and reports which ADRs are due for hoisting plus any pre-trinity packages.

Exit codes:
  0 — success (even if hoists are due, unless --ci)
  1 — failures in --ci mode (unknown conditions, malformed frontmatter, condition true)
"""
import sys
import subprocess
import argparse
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict | None:
    """Parse YAML frontmatter between --- fences. Returns dict or None on failure."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fm_text = "\n".join(lines[1:end])
    return yaml.safe_load(fm_text) or {}


# ---------------------------------------------------------------------------
# Evaluator registry
# ---------------------------------------------------------------------------

def eval_second_package_implements_contract(
    fm: dict, repo_root: Path
) -> tuple[bool, list[str]]:
    """
    True when packages beyond applies_to implement the same contract.
    Returns (condition_met, evidence_list).
    """
    hoist = fm.get("hoist_when", {})
    contract_name = hoist.get("contract", "")
    applies_to = fm.get("applies_to", [])
    if isinstance(applies_to, str):
        applies_to = [applies_to]

    packages_dir = repo_root / "packages"
    if not packages_dir.is_dir():
        return False, []

    implementors = []
    for pkg_dir in sorted(packages_dir.iterdir()):
        if not pkg_dir.is_dir():
            continue
        contracts_file = pkg_dir / "contracts.yml"
        if not contracts_file.exists():
            continue
        try:
            contracts = yaml.safe_load(contracts_file.read_text()) or []
        except yaml.YAMLError:
            continue
        if contract_name in contracts:
            implementors.append(pkg_dir.name)

    # Condition is true when more packages implement it than are in applies_to
    extra = [p for p in implementors if p not in applies_to]
    return bool(extra), extra


EVALUATORS = {
    "second_package_implements_contract": eval_second_package_implements_contract,
    # reserved for future use:
    # "allowlist_entry_exists_for": eval_allowlist_entry_exists_for,
}


# ---------------------------------------------------------------------------
# Bead integration
# ---------------------------------------------------------------------------

def list_open_beads_with_title(title_fragment: str) -> list[str]:
    """Query open beads matching a title fragment via bd list. Returns list of titles."""
    try:
        result = subprocess.run(
            ["bd", "list", f"--title-contains={title_fragment}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []


def create_bead(title: str, note: str = "") -> bool:
    """Create a new bead. Returns True on success."""
    try:
        cmd = ["bd", "create", f"--title={title}", "--type=chore"]
        if note:
            cmd.append(f"--notes={note}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def collect_packages(repo_root: Path) -> list[str]:
    """Return list of package names from packages/ directory."""
    packages_dir = repo_root / "packages"
    if not packages_dir.is_dir():
        return []
    return sorted(
        d.name for d in packages_dir.iterdir() if d.is_dir()
    )


def collect_adr_covered_packages(adrs: list[dict]) -> set[str]:
    """Collect all packages mentioned in applies_to or hoist_when.target across all ADRs."""
    covered = set()
    for adr in adrs:
        fm = adr.get("frontmatter", {})
        applies_to = fm.get("applies_to", [])
        if isinstance(applies_to, str):
            applies_to = [applies_to]
        covered.update(applies_to)
        hoist = fm.get("hoist_when", {})
        if hoist.get("target"):
            covered.add(hoist["target"])
    return covered


def run(repo_root: Path, create_beads: bool, ci_mode: bool, allow_unknown: bool) -> int:
    """Run the hoist check. Returns exit code."""
    adr_dir = repo_root / "docs" / "adr"
    exit_code = 0
    parsed_adrs = []
    hoist_results = []

    # Phase 1: Parse ADRs
    if adr_dir.is_dir():
        for adr_file in sorted(adr_dir.glob("*.md")):
            text = adr_file.read_text()
            try:
                fm = parse_frontmatter(text)
            except yaml.YAMLError as e:
                msg = f"ERROR: malformed frontmatter in {adr_file}: {e}"
                print(msg)
                if ci_mode:
                    exit_code = 1
                continue

            if fm is None:
                msg = f"ERROR: malformed frontmatter in {adr_file}"
                print(msg)
                if ci_mode:
                    exit_code = 1
                continue

            parsed_adrs.append({"path": adr_file, "frontmatter": fm})

    # Phase 2: Evaluate hoist_when conditions
    print("ADR Hoist Debt:")
    any_hoist_due = False

    for adr in parsed_adrs:
        fm = adr["frontmatter"]
        hoist = fm.get("hoist_when")
        if not hoist:
            continue  # silently skip

        condition = hoist.get("condition", "")
        evaluator = EVALUATORS.get(condition)

        if evaluator is None:
            msg = f"WARNING: unknown condition '{condition}' in {adr['path']}"
            print(msg)
            if ci_mode and not allow_unknown:
                exit_code = 1
            continue

        try:
            condition_met, evidence = evaluator(fm, repo_root)
        except Exception as e:
            print(f"ERROR: evaluating condition in {adr['path']}: {e}")
            if ci_mode:
                exit_code = 1
            continue

        trigger_title = hoist.get("trigger_bead_title", "")
        adr_name = adr["path"].name

        if condition_met:
            any_hoist_due = True
            evidence_str = ", ".join(evidence)
            print(f"  HOIST DUE: {adr_name}")
            print(f"    Condition: {condition}")
            print(f"    Bead: {trigger_title}")
            print(f"    Evidence: {evidence_str}")

            hoist_results.append({
                "adr": adr_name,
                "trigger_title": trigger_title,
                "evidence": evidence,
            })

            if ci_mode:
                exit_code = 1

            if create_beads and trigger_title:
                # Check if bead already exists
                existing = list_open_beads_with_title(trigger_title)
                bead_open = any(trigger_title in b for b in existing)
                if not bead_open:
                    note = f"Auto-created by adr-hoist-check. Evidence: {evidence_str}"
                    ok = create_bead(trigger_title, note)
                    if ok:
                        print(f"    Created bead: {trigger_title}")
                    else:
                        print(f"    WARNING: failed to create bead: {trigger_title}")
        else:
            print(f"  OK: {adr_name}")

    if not any_hoist_due and not any(
        adr["frontmatter"].get("hoist_when") for adr in parsed_adrs
    ):
        print("  (no ADRs with hoist_when blocks found)")

    # Phase 3: Pre-trinity packages
    print()
    print("Pre-trinity packages:")
    all_packages = collect_packages(repo_root)
    covered = collect_adr_covered_packages(parsed_adrs)
    pre_trinity = [p for p in all_packages if p not in covered]

    if pre_trinity:
        for pkg in pre_trinity:
            print(f"  {pkg}")
    else:
        print("  (none)")

    return exit_code


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check ADRs for hoist debt and pre-trinity packages."
    )
    parser.add_argument("repo_root", help="Root of the repository to analyze")
    parser.add_argument(
        "--create-beads",
        action="store_true",
        help="Create beads for due hoists (requires bd CLI)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit non-zero if hoists are due or conditions are unknown",
    )
    parser.add_argument(
        "--allow-unknown",
        action="store_true",
        help="In CI mode, do not exit non-zero for unknown conditions",
    )
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        print(f"ERROR: repo_root not a directory: {repo_root}", file=sys.stderr)
        return 1
    return run(repo_root, args.create_beads, args.ci, args.allow_unknown)


if __name__ == "__main__":
    sys.exit(main())
