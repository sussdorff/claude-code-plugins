#!/usr/bin/env python3
"""
enforcement_matrix_scanner.py — Scan a repo for Architecture Trinity coverage.

Usage:
    python3 enforcement_matrix_scanner.py <repo_root> [--json]

Scans:
  - docs/adr/**/*.md      for contract declarations (YAML frontmatter)
  - packages/*/src/**     for Helper artifacts
  - packages/*/scripts/*  for Enforcer-Proactive (codegen) artifacts
  - packages/*/eslint.*   for Enforcer-Reactive (lint) artifacts
  - packages/*/package.json scripts for check:* / schema:* patterns

Outputs a Markdown section (## Enforcement Matrix) to stdout.
With --json: outputs intermediate JSON for testing/debugging.
"""
import sys
import json
import re
import argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# ADR parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter between --- fences. Returns dict or {}."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fm_lines = lines[1:end]
    result = {}
    current_key = None
    current_list = None
    for line in fm_lines:
        # List item
        if line.startswith("  - ") or line.startswith("- "):
            item = line.strip().lstrip("- ").strip()
            if current_list is not None:
                current_list.append(item)
            continue
        # Key: value
        m = re.match(r"^(\w[\w\-]*)\s*:\s*(.*)", line)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if value == "":
                # List follows
                current_list = []
                result[current_key] = current_list
            else:
                current_list = None
                result[current_key] = value
    return result


def scan_adrs(repo_root: Path) -> list[dict]:
    """Return list of contract dicts: {contract, applies_to, status}."""
    adr_dir = repo_root / "docs" / "adr"
    if not adr_dir.exists():
        return []
    contracts = []
    for md_file in sorted(adr_dir.rglob("*.md")):
        text = md_file.read_text(errors="replace")
        fm = parse_frontmatter(text)
        if "contract" not in fm:
            continue
        contract = fm.get("contract", "").strip()
        applies_to = fm.get("applies_to", [])
        if isinstance(applies_to, str):
            applies_to = [applies_to]
        status = fm.get("status", "proposed").strip().lower()
        contracts.append({
            "contract": contract,
            "applies_to": [p.strip() for p in applies_to],
            "status": status,
        })
    return contracts


# ---------------------------------------------------------------------------
# Package discovery
# ---------------------------------------------------------------------------

def discover_packages(repo_root: Path) -> list[str]:
    """Return sorted list of package names from packages/*/."""
    packages_dir = repo_root / "packages"
    if not packages_dir.exists():
        return []
    names = sorted(
        d.name for d in packages_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    return names


# ---------------------------------------------------------------------------
# Helper term extraction from contract name
# ---------------------------------------------------------------------------

# Map contract name keywords to search terms for helper detection
_STOP_WORDS = {"the", "a", "an", "of", "and", "or", "for", "to", "in", "on"}

def contract_to_search_terms(contract_name: str) -> list[str]:
    """
    Extract meaningful search terms from contract name.
    'ID Taxonomy' -> ['id', 'taxonomy']
    'Schema Codegen' -> ['schema', 'codegen']
    'Error Envelope' -> ['error', 'envelope']
    """
    words = re.split(r"[\s\-_]+", contract_name.lower())
    return [w for w in words if w and w not in _STOP_WORDS]


# ---------------------------------------------------------------------------
# Trinity column scanners (per package)
# ---------------------------------------------------------------------------

def _has_helper(pkg_dir: Path, search_terms: list[str]) -> bool:
    """Check if src/ contains a file/dir whose name includes any search term."""
    src_dir = pkg_dir / "src"
    if not src_dir.exists():
        return False
    for item in src_dir.rglob("*"):
        name = item.name.lower()
        # Strip extension for matching
        stem = item.stem.lower() if item.is_file() else name
        for term in search_terms:
            if term in stem or term in name:
                return True
    return False


def _has_proactive(pkg_dir: Path) -> bool:
    """
    Check if package has proactive (codegen) enforcers:
    - scripts/*gen*.{ts,js,py} in the package directory
    - package.json scripts matching schema:* or *gen* patterns
    """
    # Check scripts/ subdirectory for gen* files
    scripts_dir = pkg_dir / "scripts"
    if scripts_dir.exists():
        for item in scripts_dir.iterdir():
            if item.is_file():
                stem = item.stem.lower()
                if "gen" in stem:
                    return True

    # Check package.json scripts
    pkg_json = pkg_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            scripts = data.get("scripts", {})
            for key in scripts:
                key_lower = key.lower()
                if key_lower.startswith("schema:") or "gen" in key_lower:
                    return True
        except (json.JSONDecodeError, KeyError):
            pass

    return False


def _has_reactive(pkg_dir: Path) -> bool:
    """
    Check if package has reactive (lint/check) enforcers:
    - eslint.config.js (or eslint.config.cjs/mjs) exists
    - package.json scripts matching check:* patterns
    """
    # Check for eslint config
    for eslint_name in ["eslint.config.js", "eslint.config.cjs", "eslint.config.mjs", ".eslintrc.js", ".eslintrc.json"]:
        if (pkg_dir / eslint_name).exists():
            return True

    # Check package.json check:* scripts
    pkg_json = pkg_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            scripts = data.get("scripts", {})
            for key in scripts:
                if key.startswith("check:"):
                    return True
        except (json.JSONDecodeError, KeyError):
            pass

    return False


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------

def build_matrix(
    adrs: list[dict],
    packages: list[str],
    repo_root: Path,
) -> dict:
    """
    Build the full matrix dict:
    {
        contract_name: {
            package_name: {
                "adr": "✅"|"⚠️"|"❌"|"n/a",
                "helper": "✅"|"❌"|"n/a",
                "proactive": "✅"|"❌"|"n/a",
                "reactive": "✅"|"❌"|"n/a",
            }
        }
    }
    """
    # Build lookup: which contracts apply to which packages
    contract_map = {adr["contract"]: adr for adr in adrs}

    matrix = {}
    for adr in adrs:
        contract = adr["contract"]
        applies_to = set(adr["applies_to"])
        status = adr["status"]
        search_terms = contract_to_search_terms(contract)

        matrix[contract] = {}
        for pkg in packages:
            if pkg not in applies_to:
                # Not in scope for this contract
                matrix[contract][pkg] = {
                    "adr": "n/a",
                    "helper": "n/a",
                    "proactive": "n/a",
                    "reactive": "n/a",
                }
                continue

            # ADR status
            if status == "accepted":
                adr_sym = "✅"
            elif status == "proposed":
                adr_sym = "⚠️"
            else:
                adr_sym = "❌"

            pkg_dir = repo_root / "packages" / pkg

            helper_sym = "✅" if _has_helper(pkg_dir, search_terms) else "❌"
            proactive_sym = "✅" if _has_proactive(pkg_dir) else "❌"
            reactive_sym = "✅" if _has_reactive(pkg_dir) else "❌"

            matrix[contract][pkg] = {
                "adr": adr_sym,
                "helper": helper_sym,
                "proactive": proactive_sym,
                "reactive": reactive_sym,
            }

    return matrix


# ---------------------------------------------------------------------------
# Gap computation
# ---------------------------------------------------------------------------

def compute_gaps(matrix: dict, contracts: list[str], packages: list[str]) -> list[tuple]:
    """
    Return list of (contract, package, [missing_columns]) for cells with any ❌.
    Sorted by number of missing columns descending, then contract name, then package name.
    """
    gaps = []
    for contract in contracts:
        for pkg in packages:
            cell = matrix.get(contract, {}).get(pkg, {})
            missing = []
            col_labels = {"adr": "ADR", "helper": "Helper", "proactive": "Proactive", "reactive": "Reactive"}
            for col, label in col_labels.items():
                if cell.get(col) == "❌":
                    missing.append(label)
            if missing:
                gaps.append((contract, pkg, missing))

    gaps.sort(key=lambda x: (-len(x[2]), x[0], x[1]))
    return gaps


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(
    contracts: list[str],
    packages: list[str],
    matrix: dict,
    gaps: list[tuple],
) -> str:
    """Render the ## Enforcement Matrix section as Markdown."""
    lines = []
    lines.append("## Enforcement Matrix")
    lines.append("")
    lines.append("> Generated by `/project-context`. Shows Trinity coverage per contract × package.")
    lines.append("> Legend: ✅ present · ⚠️ partial · ❌ missing · n/a not-applicable")
    lines.append("> Sub-columns per cell: ADR | Helper | Proactive | Reactive")
    lines.append("")

    # Table header
    header_cols = ["Contract"] + packages
    header_row = "| " + " | ".join(header_cols) + " |"
    separator = "| " + " | ".join("---" for _ in header_cols) + " |"
    lines.append(header_row)
    lines.append(separator)

    for contract in contracts:
        row_cells = [contract]
        for pkg in packages:
            cell = matrix.get(contract, {}).get(pkg, {})
            adr = cell.get("adr", "n/a")
            helper = cell.get("helper", "n/a")
            proactive = cell.get("proactive", "n/a")
            reactive = cell.get("reactive", "n/a")

            if adr == "n/a" and helper == "n/a" and proactive == "n/a" and reactive == "n/a":
                row_cells.append("n/a")
            else:
                row_cells.append(f"{adr} {helper} {proactive} {reactive}")
        lines.append("| " + " | ".join(row_cells) + " |")

    lines.append("")
    lines.append("### Legend")
    lines.append("")
    lines.append("| Sub-column | Meaning |")
    lines.append("| --- | --- |")
    lines.append("| ADR | Architecture Decision Record declares this contract |")
    lines.append("| Helper | Helper utility implementing the contract exists |")
    lines.append("| Proactive | Codegen/builder enforcer makes violations impossible |")
    lines.append("| Reactive | Lint/test enforcer catches violations after the fact |")
    lines.append("")

    lines.append("### Gaps")
    lines.append("")

    if gaps:
        lines.append("Pairs where any sub-column is ❌ (sorted by gap-count descending):")
        lines.append("")
        lines.append("| Contract | Package | Missing |")
        lines.append("| --- | --- | --- |")
        for contract, pkg, missing in gaps:
            lines.append(f"| {contract} | {pkg} | {', '.join(missing)} |")
        lines.append("")

        gap_count = len(gaps)
        contracts_with_gaps = len(set(g[0] for g in gaps))
        lines.append(f"Enforcement gaps: {gap_count} (across {contracts_with_gaps} contracts)")
    else:
        lines.append("No gaps found — all contracts have full Trinity coverage.")

    return "\n".join(lines)


def render_empty() -> str:
    """Render the empty matrix message when no ADRs found."""
    return (
        "## Enforcement Matrix\n"
        "\n"
        "> No contracts declared yet — add ADRs to populate this matrix."
    )


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def build_json_output(
    contracts: list[str],
    packages: list[str],
    matrix: dict,
    gaps: list[tuple],
) -> dict:
    gaps_list = [[g[0], g[1]] for g in gaps]
    contracts_with_gaps = len(set(g[0] for g in gaps))
    return {
        "contracts": contracts,
        "packages": packages,
        "matrix": matrix,
        "gaps": gaps_list,
        "gap_count": len(gaps),
        "contract_count": contracts_with_gaps,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan repo for Architecture Trinity enforcement matrix."
    )
    parser.add_argument("repo_root", help="Path to the repository root")
    parser.add_argument(
        "--json", action="store_true", help="Output intermediate JSON instead of Markdown"
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"Error: repo_root '{repo_root}' does not exist", file=sys.stderr)
        sys.exit(1)

    adrs = scan_adrs(repo_root)
    packages = discover_packages(repo_root)

    if not adrs:
        if args.json:
            print(json.dumps({"contracts": [], "packages": packages, "matrix": {}, "gaps": [], "gap_count": 0, "contract_count": 0}, indent=2))
        else:
            print(render_empty())
        return

    contracts = sorted(adr["contract"] for adr in adrs)
    if not packages:
        # Use repo root as single pseudo-package
        packages = [repo_root.name]

    matrix = build_matrix(adrs, packages, repo_root)
    gaps = compute_gaps(matrix, contracts, packages)

    if args.json:
        output = build_json_output(contracts, packages, matrix, gaps)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(contracts, packages, matrix, gaps))


if __name__ == "__main__":
    main()
