#!/usr/bin/env python3
"""
vision-conformance: Check if a vision.md file conforms to the v1 template.

Used by the /vision-author skill --refresh mode to verify a file can be
loaded as defaults before re-running the 7-question dialogue.

Conformance criteria (v1):
    1. File exists and is readable
    2. YAML frontmatter present with template_version: 1
    3. All 7 required H2 sections present (in any order)
    4. Value Principles section contains a parseable 4-column boundary table
    5. All boundary rule_ids reference known principle IDs

Public API:
    ConformanceResult  — dataclass with conformance status and diagnostics
    check_conformance  — checks a vision.md Path -> ConformanceResult
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class ConformanceResult:
    """Result of a vision.md v1 conformance check.

    Attributes:
        is_conformant:    True if the file passes all conformance checks.
        missing_sections: List of section display names that are absent.
        has_boundary_table: True if Value Principles contains a 4-col table.
        errors:           List of human-readable error messages.
    """

    is_conformant: bool
    missing_sections: list[str] = field(default_factory=list)
    has_boundary_table: bool = True
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Required sections (display names for error messages)
# ---------------------------------------------------------------------------

_REQUIRED_SECTION_DISPLAY: list[str] = [
    "## Vision Statement",
    "## Target Group",
    "## Core Need (JTBD)",
    "## Positioning",
    "## Value Principles",
    "## Business Goal",
    "## NOT in Vision",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_conformance(path: Path) -> ConformanceResult:
    """Check if a vision.md file conforms to the v1 template.

    Runs a two-stage check:
      Stage 1 — Structural: verify all 7 H2 headers are present
      Stage 2 — Semantic: attempt parse_vision() to catch boundary table issues

    Args:
        path: Path to the vision.md file to check.

    Returns:
        ConformanceResult with detailed diagnostics. Never raises — all errors
        are captured in the result's errors field.
    """
    # Guard: file must exist
    if not path.exists():
        return ConformanceResult(
            is_conformant=False,
            errors=[f"File not found: {path}"],
            has_boundary_table=False,
        )

    # Stage 1: read and check structural requirements
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ConformanceResult(
            is_conformant=False,
            errors=[f"Cannot read file: {exc}"],
            has_boundary_table=False,
        )

    missing_sections: list[str] = []
    errors: list[str] = []
    has_boundary_table = True

    # Check required H2 headers
    # Use canonical alias matching (same as vision_parser)
    lines = content.splitlines()
    found_headers: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            header_text = stripped[3:].strip().lower()
            found_headers.add(header_text)

    # Check each required section
    section_aliases: dict[str, str] = {
        "## Vision Statement": "vision statement",
        "## Target Group": "target group",
        "## Core Need (JTBD)": "core need (jtbd)",
        "## Positioning": "positioning",
        "## Value Principles": "value principles",
        "## Business Goal": "business goal",
        "## NOT in Vision": "not in vision",
    }
    # Expanded aliases (accept "core need" without JTBD, "not in vision" case variants)
    section_alias_alternatives: dict[str, list[str]] = {
        "## Core Need (JTBD)": ["core need (jtbd)", "core need"],
        "## NOT in Vision": ["not in vision"],
    }

    for display_name in _REQUIRED_SECTION_DISPLAY:
        canonical = section_aliases[display_name].lower()
        alternatives = section_alias_alternatives.get(display_name, [canonical])
        found = any(alt in found_headers for alt in alternatives)
        if not found:
            missing_sections.append(display_name)

    # Stage 2: attempt full parse to catch boundary table issues
    # Only if structural check passes
    parse_error: str | None = None
    if not missing_sections:
        try:
            from scripts.vision_parser import parse_vision, VisionParseError
            parse_vision(path)
        except Exception as exc:
            # Any parse error (including boundary table issues) is a conformance failure
            error_msg = str(exc)
            parse_error = error_msg
            # Detect boundary table specifically
            if "boundary table" in error_msg.lower() or "table" in error_msg.lower():
                has_boundary_table = False
            errors.append(f"Parse error: {error_msg}")
    else:
        # If sections are missing, we can't reliably parse — mark boundary table unknown
        # but check heuristically whether the table line pattern is present
        has_boundary_table = any(
            "rule_id" in line and "scope" in line and "source-section" in line
            for line in lines
        )

    is_conformant = (
        len(missing_sections) == 0
        and len(errors) == 0
    )

    return ConformanceResult(
        is_conformant=is_conformant,
        missing_sections=missing_sections,
        has_boundary_table=has_boundary_table,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    """CLI: python3 scripts/vision_conformance.py <vision.md>

    Prints conformance summary. Exits 0 if conformant, 1 if not.
    """
    if not argv:
        print("Usage: vision_conformance.py <vision.md>", file=sys.stderr)
        return 2

    path = Path(argv[0])
    result = check_conformance(path)

    if result.is_conformant:
        print(f"CONFORMANT: {path}")
        return 0
    else:
        print(f"NOT CONFORMANT: {path}", file=sys.stderr)
        if result.missing_sections:
            print(f"  Missing sections: {', '.join(result.missing_sections)}", file=sys.stderr)
        if not result.has_boundary_table:
            print("  Missing or malformed 4-column boundary table", file=sys.stderr)
        for err in result.errors:
            print(f"  Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
