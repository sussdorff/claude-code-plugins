#!/usr/bin/env python3
"""bd-lint-contracts — Architecture Contracts section linter for beads.

Validates that beads with the `touches-contract` label contain a properly
structured `## Architecture Contracts Touched` section, and detects
false-negatives (section present but label missing).

Usage:
    python bd_lint_contracts.py                    # all open beads with label
    python bd_lint_contracts.py --all              # all beads incl. closed
    python bd_lint_contracts.py --bead CCP-0hr     # single bead
    python bd_lint_contracts.py --check-false-negatives  # run Y check only

Exit codes:
    0 — no lint errors
    1 — lint errors found
    2 — invocation or bd CLI error
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: str | None = None, timeout: int = 10) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timed out"
    except FileNotFoundError:
        return 1, "", f"{cmd[0]}: not found"
    except Exception as e:  # noqa: BLE001
        return 1, "", str(e)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class LintError:
    """A single lint violation."""
    bead_id: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.bead_id}] rule={self.rule}: {self.message}"


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

# Header pattern: any ## level-2 header
_H2_RE = re.compile(r"^## .+", re.MULTILINE)

# ADR bullet: - ADR-NNN (Name): description
_ADR_BULLET_RE = re.compile(r"^\s*-\s+ADR-\d+\s+\([^)]+\):\s+\S", re.MULTILINE)

# Valid Gap-to-Close bullets:
#   - [ ] None
#   - [ ] [ADR-NEEDED] ...
#   - [ ] [HELPER-NEEDED] ...
#   - [ ] [ENFORCER-PROACTIVE-NEEDED] ...
#   - [ ] [ENFORCER-REACTIVE-NEEDED] ...
_VALID_GAP_RE = re.compile(
    r"^\s*-\s+\[\s*\]\s+"
    r"(None|"
    r"\[ADR-NEEDED\]|"
    r"\[HELPER-NEEDED\]|"
    r"\[ENFORCER-PROACTIVE-NEEDED\]|"
    r"\[ENFORCER-REACTIVE-NEEDED\])",
    re.MULTILINE,
)

# Any bullet (to detect non-empty section)
_BULLET_RE = re.compile(r"^\s*-\s+\S", re.MULTILINE)

CONTRACTS_HEADER = "## Architecture Contracts Touched"
GAPS_HEADER = "## Gaps to Close"


def extract_section(description: str, header: str) -> Optional[str]:
    """Extract the body of a ## section from a markdown description.

    Returns the text between `header` and the next ## header (exclusive),
    or None if the header is not found.
    """
    # Find header position
    idx = description.find(header)
    if idx == -1:
        return None

    # Content starts after the header line
    content_start = idx + len(header)
    rest = description[content_start:]

    # Find next ## header
    m = _H2_RE.search(rest)
    if m:
        return rest[: m.start()]
    return rest


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

def validate_contracts_section(bead_id: str, description: str) -> list[LintError]:
    """Validate the Architecture Contracts section of a bead description.

    Returns a list of LintError objects. Empty list means no errors.

    Rules:
      3a — Section must have at least one bullet point
      3b — Section must contain at least one ADR-NNN (Name): ... bullet
      3c — ## Gaps to Close section must exist and contain valid bullets
    """
    errors: list[LintError] = []

    contracts_body = extract_section(description, CONTRACTS_HEADER)
    if contracts_body is None:
        # No section present — no contract errors (false-negative check is separate)
        return errors

    # --- Rule 3a: section must not be empty ---
    bullets = _BULLET_RE.findall(contracts_body)
    if not bullets:
        errors.append(LintError(
            bead_id=bead_id,
            rule="3a",
            message=(
                f"'## Architecture Contracts Touched' section exists but contains "
                f"no bullet points (empty section is invalid)"
            ),
        ))
        # Cannot meaningfully check 3b if section is empty, but still check 3c
    else:
        # --- Rule 3b: must contain at least one ADR bullet ---
        if not _ADR_BULLET_RE.search(contracts_body):
            errors.append(LintError(
                bead_id=bead_id,
                rule="3b",
                message=(
                    "'## Architecture Contracts Touched' section must contain at least one "
                    "ADR bullet in format: '- ADR-NNN (Name): <description>'"
                ),
            ))

    # --- Rule 3c: ## Gaps to Close must exist and have valid bullets ---
    gaps_body = extract_section(description, GAPS_HEADER)
    if gaps_body is None:
        errors.append(LintError(
            bead_id=bead_id,
            rule="3c",
            message=(
                "'## Architecture Contracts Touched' section is present but "
                "'## Gaps to Close' section is missing"
            ),
        ))
    else:
        # Check for any bullet at all
        any_bullets = _BULLET_RE.findall(gaps_body)
        if not any_bullets:
            errors.append(LintError(
                bead_id=bead_id,
                rule="3c",
                message="'## Gaps to Close' section exists but contains no bullet points",
            ))
        else:
            # Check that all bullets match valid patterns
            # Count valid vs total checkboxes
            valid_gap_bullets = _VALID_GAP_RE.findall(gaps_body)
            # Count total checkbox bullets: - [ ] ...
            all_checkbox_bullets = re.findall(r"^\s*-\s+\[\s*\]", gaps_body, re.MULTILINE)
            # Count non-checkbox bullets (also invalid)
            non_checkbox_bullets = re.findall(r"^\s*-\s+(?!\[\s*\])", gaps_body, re.MULTILINE)

            if non_checkbox_bullets:
                errors.append(LintError(
                    bead_id=bead_id,
                    rule="3c",
                    message=(
                        f"'## Gaps to Close' contains {len(non_checkbox_bullets)} non-checkbox "
                        f"bullet(s). All bullets must use '- [ ] None' or "
                        f"'- [ ] [KEYWORD] ...' pattern"
                    ),
                ))
            elif len(valid_gap_bullets) < len(all_checkbox_bullets):
                # Some checkbox bullets don't match valid keyword patterns
                errors.append(LintError(
                    bead_id=bead_id,
                    rule="3c",
                    message=(
                        f"'## Gaps to Close' has {len(all_checkbox_bullets)} checkbox bullet(s) "
                        f"but only {len(valid_gap_bullets)} match valid patterns. "
                        f"Valid patterns: '- [ ] None', '- [ ] [ADR-NEEDED] ...', "
                        f"'- [ ] [HELPER-NEEDED] ...', '- [ ] [ENFORCER-PROACTIVE-NEEDED] ...', "
                        f"'- [ ] [ENFORCER-REACTIVE-NEEDED] ...'"
                    ),
                ))

    return errors


# ---------------------------------------------------------------------------
# False-negative check (Rule Y)
# ---------------------------------------------------------------------------

def check_false_negatives(beads: list[dict]) -> list[LintError]:
    """Check for beads that have the contracts section but NOT the label.

    Args:
        beads: List of bead dicts with keys: id, description, labels.

    Returns:
        List of LintError for each false-negative found.
    """
    errors: list[LintError] = []
    for bead in beads:
        bead_id = bead.get("id", "?")
        description = bead.get("description", "") or ""
        labels = bead.get("labels", []) or []

        has_section = extract_section(description, CONTRACTS_HEADER) is not None
        has_label = "touches-contract" in labels

        if has_section and not has_label:
            errors.append(LintError(
                bead_id=bead_id,
                rule="Y",
                message=(
                    "Bead description contains '## Architecture Contracts Touched' "
                    "section but does NOT have the 'touches-contract' label. "
                    "Add the label or remove the section."
                ),
            ))

    return errors


# ---------------------------------------------------------------------------
# bd CLI wrappers
# ---------------------------------------------------------------------------

def _fetch_bead(bead_id: str) -> Optional[dict]:
    """Fetch a single bead via `bd show <id> --json`.

    Returns the bead dict or None on error.
    """
    rc, stdout, stderr = _run(["bd", "show", bead_id, "--json"])
    if rc != 0:
        return None
    try:
        data = json.loads(stdout)
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return None


def _fetch_bead_labels(bead_id: str) -> list[str]:
    """Fetch labels for a bead via `bd label list <id>`.

    Returns list of label strings (may be empty).
    """
    rc, stdout, _stderr = _run(["bd", "label", "list", bead_id])
    if rc != 0:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _fetch_labeled_beads(include_closed: bool = False) -> list[dict]:
    """Fetch all beads with the `touches-contract` label.

    Args:
        include_closed: If True, also include closed beads.

    Returns:
        List of bead dicts.
    """
    cmd = ["bd", "list", "--label", "touches-contract", "--json", "--limit", "0"]
    if include_closed:
        cmd.append("--all")
    else:
        cmd += ["--status", "open"]

    rc, stdout, stderr = _run(cmd, timeout=30)
    if rc != 0:
        return []
    try:
        data = json.loads(stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _fetch_all_beads(include_closed: bool = False) -> list[dict]:
    """Fetch all beads (for false-negative check).

    Args:
        include_closed: If True, include closed beads.

    Returns:
        List of bead dicts.
    """
    cmd = ["bd", "list", "--json", "--limit", "0"]
    if include_closed:
        cmd.append("--all")

    rc, stdout, stderr = _run(cmd, timeout=30)
    if rc != 0:
        return []
    try:
        data = json.loads(stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------------------------
# High-level lint functions
# ---------------------------------------------------------------------------

def lint_bead(bead_id: str) -> list[LintError]:
    """Lint a single bead by ID.

    Fetches the bead via bd CLI, checks for false negatives and validates
    the contracts section if the label is present.

    Returns:
        List of LintError objects.
    """
    errors: list[LintError] = []

    bead = _fetch_bead(bead_id)
    if bead is None:
        errors.append(LintError(
            bead_id=bead_id,
            rule="io",
            message=f"Could not fetch bead '{bead_id}' via bd CLI",
        ))
        return errors

    description = bead.get("description", "") or ""
    # Fetch labels from bead data or separately
    raw_labels = bead.get("labels", None)
    if raw_labels is None:
        raw_labels = _fetch_bead_labels(bead_id)

    # Normalize: labels might be list of strings or list of dicts
    labels: list[str] = []
    for item in (raw_labels or []):
        if isinstance(item, str):
            labels.append(item)
        elif isinstance(item, dict):
            labels.append(item.get("name", ""))

    has_label = "touches-contract" in labels
    has_section = extract_section(description, CONTRACTS_HEADER) is not None

    # False-negative check (Rule Y)
    if has_section and not has_label:
        errors.append(LintError(
            bead_id=bead_id,
            rule="Y",
            message=(
                "Bead description contains '## Architecture Contracts Touched' "
                "section but does NOT have the 'touches-contract' label. "
                "Add the label or remove the section."
            ),
        ))

    # Validate contracts section (only relevant if label set OR section present)
    if has_section:
        errors.extend(validate_contracts_section(bead_id, description))

    return errors


def lint_labeled_beads(include_closed: bool = False) -> list[LintError]:
    """Lint all beads with the `touches-contract` label.

    Args:
        include_closed: If True, also include closed beads.

    Returns:
        List of LintError objects across all beads.
    """
    beads = _fetch_labeled_beads(include_closed=include_closed)
    errors: list[LintError] = []
    for bead in beads:
        bead_id = bead.get("id", "?")
        description = bead.get("description", "") or ""
        errors.extend(validate_contracts_section(bead_id, description))
    return errors


def lint_false_negatives(include_closed: bool = False) -> list[LintError]:
    """Check all beads for false negatives (section without label).

    Args:
        include_closed: If True, also include closed beads.

    Returns:
        List of LintError objects for false-negatives.
    """
    all_beads = _fetch_all_beads(include_closed=include_closed)
    labeled = {b.get("id") for b in _fetch_labeled_beads(include_closed=include_closed)}

    beads_with_meta = []
    for bead in all_beads:
        bead_id = bead.get("id", "?")
        beads_with_meta.append({
            "id": bead_id,
            "description": bead.get("description", "") or "",
            "labels": ["touches-contract"] if bead_id in labeled else [],
        })

    return check_false_negatives(beads_with_meta)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Lint architecture contract sections in beads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # lint all open beads with touches-contract label
  %(prog)s --all                    # include closed beads
  %(prog)s --bead CCP-0hr           # lint single bead
  %(prog)s --check-false-negatives  # only check for section-without-label
        """,
    )
    parser.add_argument(
        "--bead",
        metavar="ID",
        help="Check a single bead by ID",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="include_closed",
        help="Include closed beads (default: open only)",
    )
    parser.add_argument(
        "--check-false-negatives",
        action="store_true",
        help="Only run the false-negative check (section without label)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output; use exit code only",
    )
    args = parser.parse_args()

    all_errors: list[LintError] = []

    if args.bead:
        all_errors = lint_bead(args.bead)
    elif args.check_false_negatives:
        all_errors = lint_false_negatives(include_closed=args.include_closed)
    else:
        # Default: lint labeled beads + false-negative check
        all_errors.extend(lint_labeled_beads(include_closed=args.include_closed))
        all_errors.extend(lint_false_negatives(include_closed=args.include_closed))

    if all_errors:
        if not args.quiet:
            print(f"bd lint --check=architecture-contracts: {len(all_errors)} error(s) found\n")
            for err in all_errors:
                print(f"  {err}")
            print()
        return 1

    if not args.quiet:
        scope = f"bead {args.bead}" if args.bead else "all labeled beads"
        print(f"bd lint --check=architecture-contracts: OK ({scope})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
