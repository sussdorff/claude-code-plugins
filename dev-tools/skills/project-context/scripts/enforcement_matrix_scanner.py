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

def _strip_quotes(value: str) -> str:
    """Strip matching pairs of single or double quotes from a scalar value."""
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value


def _strip_inline_comment(value: str) -> str:
    """Strip inline YAML comment (# ...) from a scalar value outside of quotes."""
    # Only strip if not a quoted string
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value
    # Remove trailing # comment
    idx = value.find(" #")
    if idx != -1:
        value = value[:idx]
    return value.strip()


def _parse_inline_list(value: str) -> list:
    """Parse inline YAML list syntax [a, b, c] or ["a", "b"] into a list of strings."""
    inner = value[1:-1]  # Strip [ and ]
    items = [_strip_quotes(_strip_inline_comment(item.strip())) for item in inner.split(",")]
    return [item for item in items if item]


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
            m = re.match(r"^\s*-\s+(.*)", line)
            raw_item = m.group(1).strip() if m else line.strip()
            item = _strip_quotes(_strip_inline_comment(raw_item))
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
                # Strip inline comment first, then detect list vs scalar
                value = _strip_inline_comment(value)
                if value.startswith("[") and value.endswith("]"):
                    result[current_key] = _parse_inline_list(value)
                else:
                    value = _strip_quotes(value)
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
        contract = fm.get("contract", "")
        if not isinstance(contract, str):
            print(f"Warning: 'contract' field in {md_file} is not a string, skipping.", file=sys.stderr)
            continue
        contract = contract.strip()
        applies_to = fm.get("applies_to", [])
        if isinstance(applies_to, str):
            applies_to = [applies_to]
        status_raw = fm.get("status", "proposed")
        if not isinstance(status_raw, str):
            status_raw = "proposed"
        status = status_raw.strip().lower()
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
# Excluded path component names for filesystem scans
# ---------------------------------------------------------------------------

_EXCLUDED_DIRS = {"node_modules", "dist", "build", ".git", "__pycache__"}


def _is_excluded(path: Path) -> bool:
    """Return True if any component of the path is in the exclusion list."""
    return any(part in _EXCLUDED_DIRS for part in path.parts)


# ---------------------------------------------------------------------------
# Trinity column scanners (per package)
# ---------------------------------------------------------------------------

def _has_helper(pkg_dir: Path, search_terms: list[str]) -> bool:
    """Check if src/ contains a file/dir whose name token-matches any search term."""
    src_dir = pkg_dir / "src"
    if not src_dir.exists():
        return False
    for item in src_dir.rglob("*"):
        if _is_excluded(item):
            continue
        name = item.name.lower()
        # Split filename name on non-alphanumeric chars to get tokens
        tokens = set(re.split(r"[^a-z0-9]+", name))
        for term in search_terms:
            if term in tokens:
                return True
    return False


def _is_gen_script_name(stem: str) -> bool:
    """
    Return True if the script stem contains 'gen' as a whole token.
    e.g. 'gen-schema' -> True, 'generate-types' -> False (unless token is 'gen')
    """
    tokens = set(re.split(r"[^a-z0-9]+", stem.lower()))
    return "gen" in tokens


def _is_gen_package_script_key(key: str) -> bool:
    """
    Return True if the package.json script key is a gen-related key.
    Matches: codegen, generate, gen-, gen: prefixes, or the key itself equals 'gen'.
    """
    key_lower = key.lower()
    if key_lower in ("codegen", "generate", "gen"):
        return True
    if key_lower.startswith("codegen:") or key_lower.startswith("codegen-"):
        return True
    if key_lower.startswith("generate:") or key_lower.startswith("generate-"):
        return True
    if key_lower.startswith("gen:") or key_lower.startswith("gen-"):
        return True
    return False


def _is_gen_script_value(value: str) -> bool:
    """Return True if the script value contains 'gen' as a full word."""
    return bool(re.search(r"\bgen\b", value.lower()))


def _stem_tokens(stem: str) -> set:
    """Split a filename stem on non-alphanumeric chars and return lowercase token set."""
    return set(re.split(r"[^a-z0-9]+", stem.lower()))


def _terms_match_tokens(tokens: set, search_terms: list[str]) -> bool:
    """Return True if any search term intersects with the token set."""
    return bool(tokens & set(search_terms))


def _has_proactive(pkg_dir: Path, search_terms: list[str], repo_root: "Path | None" = None) -> bool:
    """
    Check if package has proactive (codegen) enforcers relevant to the given search_terms:
    - scripts/*gen*.{ts,js,py} in the package directory whose stem tokens intersect search_terms
    - package.json scripts matching codegen/generate/gen-/gen: patterns (filtered by search_terms)
    - repo-root scripts/ directory for gen scripts (filtered by search_terms)
    """
    # Check package scripts/ subdirectory for gen* files whose stem intersects search_terms
    scripts_dir = pkg_dir / "scripts"
    if scripts_dir.exists():
        for item in scripts_dir.iterdir():
            if item.is_file() and _is_gen_script_name(item.stem):
                if _terms_match_tokens(_stem_tokens(item.stem), search_terms):
                    return True

    # Check repo-root scripts/ directory if provided
    if repo_root is not None:
        root_scripts_dir = repo_root / "scripts"
        if root_scripts_dir.exists():
            for item in root_scripts_dir.iterdir():
                if item.is_file() and _is_gen_script_name(item.stem):
                    if _terms_match_tokens(_stem_tokens(item.stem), search_terms):
                        return True

    # Check package.json scripts
    pkg_json = pkg_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            scripts = data.get("scripts", {})
            for key, value in scripts.items():
                key_lower = key.lower()
                if key_lower.startswith("schema:"):
                    # suffix after "schema:" — check if suffix tokens or "schema" itself matches
                    suffix = key_lower[len("schema:"):]
                    suffix_tokens = set(re.split(r"[^a-z0-9]+", suffix)) | {"schema"}
                    if _terms_match_tokens(suffix_tokens, search_terms):
                        return True
                elif _is_gen_package_script_key(key):
                    # Check if key suffix tokens intersect search_terms OR script value contains term
                    # Extract suffix after prefix (gen:, gen-, codegen:, etc.)
                    for prefix in ("codegen:", "codegen-", "generate:", "generate-", "gen:", "gen-"):
                        if key_lower.startswith(prefix):
                            suffix = key_lower[len(prefix):]
                            suffix_tokens = set(re.split(r"[^a-z0-9]+", suffix))
                            if _terms_match_tokens(suffix_tokens, search_terms):
                                return True
                            break
                    else:
                        # bare "codegen", "generate", "gen" — check script value
                        val_lower = str(value).lower()
                        if any(re.search(r"\b" + re.escape(term) + r"\b", val_lower) for term in search_terms):
                            return True
                elif _is_gen_script_value(str(value)):
                    # Script value contains "gen" — check if any search term in value
                    val_lower = str(value).lower()
                    if any(re.search(r"\b" + re.escape(term) + r"\b", val_lower) for term in search_terms):
                        return True
        except json.JSONDecodeError:
            pass

    return False


_ESLINT_CONFIG_NAMES = {
    "eslint.config.js",
    "eslint.config.cjs",
    "eslint.config.mjs",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".eslintrc.yaml",
    ".eslintrc.cjs",
    ".eslintrc",
}


def _eslint_content_matches(path: Path, search_terms: list[str]) -> bool:
    """Return True if any search term appears as a whole word-token in the eslint config content."""
    try:
        content = path.read_text(errors="replace")
        for term in search_terms:
            if re.search(r"\b" + re.escape(term) + r"\b", content, re.IGNORECASE):
                return True
    except OSError:
        pass
    return False


def _suffix_tokens_match(suffix: str, search_terms: list[str]) -> bool:
    """
    Return True if any search term matches a token in the suffix using prefix matching.
    e.g. "ids" with term "id" → matches because "ids".startswith("id")
    """
    tokens = re.split(r"[^a-z0-9]+", suffix.lower())
    tokens = [t for t in tokens if t]
    for tok in tokens:
        for term in search_terms:
            if tok.startswith(term) or term.startswith(tok):
                return True
    return False


def _has_reactive(pkg_dir: Path, search_terms: list[str], repo_root: "Path | None" = None) -> bool:
    """
    Check if package has reactive (lint/check) enforcers relevant to the given search_terms:
    - eslint config files: read content and check for search_terms as whole word-tokens
    - package.json check:* scripts: suffix tokens must intersect search_terms
    - package.json schema:* scripts: "schema" in search_terms
    """
    # Check for eslint config in package directory — content-aware
    for eslint_name in _ESLINT_CONFIG_NAMES:
        eslint_path = pkg_dir / eslint_name
        if eslint_path.exists():
            if _eslint_content_matches(eslint_path, search_terms):
                return True

    # Check for eslint config at repo root — content-aware
    if repo_root is not None:
        for eslint_name in _ESLINT_CONFIG_NAMES:
            eslint_path = repo_root / eslint_name
            if eslint_path.exists():
                if _eslint_content_matches(eslint_path, search_terms):
                    return True

    # Check package.json scripts
    pkg_json = pkg_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            scripts = data.get("scripts", {})
            for key in scripts:
                key_lower = key.lower()
                if key_lower.startswith("check:"):
                    suffix = key_lower[len("check:"):]
                    if _suffix_tokens_match(suffix, search_terms):
                        return True
                elif key_lower.startswith("schema:"):
                    # schema:check etc — match if "schema" is a search term
                    if "schema" in search_terms:
                        return True
        except json.JSONDecodeError:
            pass

    return False


# ---------------------------------------------------------------------------
# Matrix builder
# ---------------------------------------------------------------------------

def build_matrix(
    adrs: list[dict],
    packages: list[str],
    repo_root: Path,
    packages_base: "Path | None" = None,
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

            if packages_base is not None:
                pkg_dir = packages_base / pkg
            else:
                pkg_dir = repo_root / "packages" / pkg
                if not pkg_dir.exists():
                    pkg_dir = repo_root  # single-package / root-only fallback

            helper_sym = "✅" if _has_helper(pkg_dir, search_terms) else "❌"
            proactive_sym = "✅" if _has_proactive(pkg_dir, search_terms, repo_root) else "❌"
            reactive_sym = "✅" if _has_reactive(pkg_dir, search_terms, repo_root) else "❌"

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

_COL_LABELS = {"adr": "ADR", "helper": "Helper", "proactive": "Proactive", "reactive": "Reactive"}


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
            for col, label in _COL_LABELS.items():
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
        "contracts_with_gaps": contracts_with_gaps,
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
            print(json.dumps({"contracts": [], "packages": packages, "matrix": {}, "gaps": [], "gap_count": 0, "contracts_with_gaps": 0}, indent=2))
        else:
            print(render_empty())
        return

    contracts = sorted(adr["contract"] for adr in adrs)
    packages_dir = repo_root / "packages"
    packages_base = packages_dir if packages_dir.exists() else None
    if not packages:
        # Use repo root as single pseudo-package
        packages = [repo_root.name]

    matrix = build_matrix(adrs, packages, repo_root, packages_base=packages_base)
    gaps = compute_gaps(matrix, contracts, packages)

    if args.json:
        output = build_json_output(contracts, packages, matrix, gaps)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(contracts, packages, matrix, gaps))


if __name__ == "__main__":
    main()
