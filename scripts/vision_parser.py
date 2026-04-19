#!/usr/bin/env python3
"""
vision-parser: Parse project-level vision.md into structured data.

Parses vision.md files conformant to the v1 template produced by /vision-author.
Consumed by /vision-review (CCP-a67), /vision-author --refresh (CCP-hf1),
architecture-scout (CCP-2hd), and review-agent (CCP-wxv).

Template v1 format:
  YAML frontmatter: template_version: 1
  Seven locked H2 sections in order:
    1. Vision Statement
    2. Target Group
    3. Core Need (JTBD)          (also: Core Need)
    4. Positioning
    5. Value Principles           (contains principles + 4-col boundary table)
    6. Business Goal
    7. NOT in Vision              (also: Not in Vision)

Principles in "Value Principles":
  Format: ``- **P1**: text`` or ``* **P1**: text``
  IDs are AUTHORED in the markdown, not position-assigned.
  Parser reads the prefix; ordering is slug-stable.

Boundary table in "Value Principles":
  4-column markdown table: rule_id | rule | scope | source-section
  Every rule_id MUST match a known principle ID (VisionParseError otherwise).

Public API:
    parse_vision(path: Path) -> Vision
        Parse a vision.md file; return a Vision dataclass on success.
        Raises VisionParseError with line:col on any malformed input.

    VisionParseError
        Exception raised for parse failures.
        Attributes:
          .line (int): 1-based line number of the error
          .col  (int): 1-based column (1 for section-level errors,
                       exact column for inline errors)
        str(err) includes "line N:C" at the end.

    Vision dataclass fields:
        vision_statement  (str)  — content of ## Vision Statement section
        target_group      (str)  — content of ## Target Group section
        core_need         (str)  — content of ## Core Need (JTBD) section
        positioning       (str)  — content of ## Positioning section
        business_goal     (str)  — content of ## Business Goal section
        not_in_vision     (str)  — content of ## NOT in Vision section
        principles        (list[Principle]) — authored principles from Value Principles
        boundary_table    (list[BoundaryRule]) — parsed boundary rules
        template_version  (int)  — from frontmatter (must be 1)
        raw_text          (str)  — full original file content

    Principle dataclass fields:
        id             (str)  — authored ID, e.g. "P1"
        text           (str)  — principle text
        source_section (str)  — always "Value Principles"

    BoundaryRule dataclass fields:
        rule_id        (str)  — must match a Principle.id
        rule           (str)  — rule description
        scope          (str)  — scope of the rule
        source_section (str)  — source-section column from table

Exception contract:
    All parse failures raise VisionParseError with an actionable message
    including the offending line number. Example messages:
      "Missing required section '## Business Goal' (line 45:1)"
      "Boundary table has 3 columns, expected 4 (line 28:1)"
      "Boundary rule_id 'P99' has no matching principle (line 29:1)"
      "Missing frontmatter 'template_version' (line 1:1)"
      "Unsupported template_version: 2 (expected 1) (line 1:1)"
      "Section '## Value Principles' found after '## Business Goal' (line 33:1)"

Usage (as script):
    python3 scripts/vision_parser.py docs/vision.md
    # Prints JSON summary to stdout; exits 0 on success, 1 on parse error.

Usage (as module):
    from scripts.vision_parser import parse_vision, VisionParseError
    vision = parse_vision(Path("docs/vision.md"))
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex constants (pre-compiled)
# ---------------------------------------------------------------------------

# Matches H2 headers: ## Section Name
H2_RE = re.compile(r"^##\s+(.+)$")

# Matches authored principle lines: - **P1**: text  OR  * **P1**: text
PRINCIPLE_RE = re.compile(r"^\s*[-*]\s+\*\*([Pp]\d+)\*\*[:\s]+(.*)")

# Matches boundary table separator rows (e.g. |---|---|---|---|)
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[-| :]+\|\s*$")

# Matches any table row (contains at least one |)
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")

# Seven locked H2 sections in order (canonical lowercase keys)
# Aliases map to the canonical field name
SECTION_ALIASES: dict[str, str] = {
    "vision statement": "vision_statement",
    "target group": "target_group",
    "core need": "core_need",
    "core need (jtbd)": "core_need",
    "positioning": "positioning",
    "value principles": "value_principles",
    "business goal": "business_goal",
    "not in vision": "not_in_vision",
    "not in vision": "not_in_vision",
}

# Ordered list of required canonical section keys
REQUIRED_SECTIONS_ORDER: list[str] = [
    "vision_statement",
    "target_group",
    "core_need",
    "positioning",
    "value_principles",
    "business_goal",
    "not_in_vision",
]

# Human-readable display names for error messages
SECTION_DISPLAY: dict[str, str] = {
    "vision_statement": "## Vision Statement",
    "target_group": "## Target Group",
    "core_need": "## Core Need (JTBD)",
    "positioning": "## Positioning",
    "value_principles": "## Value Principles",
    "business_goal": "## Business Goal",
    "not_in_vision": "## NOT in Vision",
}


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------

class VisionParseError(Exception):
    """Raised when vision.md does not conform to the v1 template.

    Attributes:
        line (int): 1-based line number of the error.
        col  (int): 1-based column (1 for most errors).
    """

    def __init__(self, message: str, line: int, col: int = 1) -> None:
        self.line = line
        self.col = col
        super().__init__(f"{message} (line {line}:{col})")


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Principle:
    """An authored value principle extracted from the Value Principles section.

    Attributes:
        id:             Authored ID string, e.g. "P1".
        text:           The principle text (stripped).
        source_section: Always "Value Principles".
    """

    id: str
    text: str
    source_section: str = "Value Principles"


@dataclass
class BoundaryRule:
    """A row from the 4-column boundary table in Value Principles.

    Attributes:
        rule_id:        Must match a Principle.id.
        rule:           Rule description.
        scope:          Scope of the rule.
        source_section: Source-section column value from the table.
    """

    rule_id: str
    rule: str
    scope: str
    source_section: str


@dataclass
class Vision:
    """Parsed representation of a v1 vision.md file.

    Attributes:
        vision_statement: Content of ## Vision Statement.
        target_group:     Content of ## Target Group.
        core_need:        Content of ## Core Need (JTBD).
        positioning:      Content of ## Positioning.
        business_goal:    Content of ## Business Goal.
        not_in_vision:    Content of ## NOT in Vision.
        principles:       Ordered list of Principle objects from Value Principles.
        boundary_table:   List of BoundaryRule objects from the 4-col table.
        template_version: Integer from frontmatter (must be 1).
        raw_text:         Full original file content.
    """

    vision_statement: str = ""
    target_group: str = ""
    core_need: str = ""
    positioning: str = ""
    business_goal: str = ""
    not_in_vision: str = ""
    principles: list[Principle] = field(default_factory=list)
    boundary_table: list[BoundaryRule] = field(default_factory=list)
    template_version: int = 0
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> tuple[dict[str, str], int]:
    """Parse YAML-like frontmatter between --- delimiters.

    Returns a tuple of (fields_dict, end_line_number).
    end_line_number is 1-based index of the line AFTER the closing ---.
    If no frontmatter, returns ({}, 1).
    """
    if not content.startswith("---"):
        return {}, 1

    # Find the closing ---
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return {}, 1

    front_block = content[3:end_idx].strip()
    result: dict[str, str] = {}
    for line in front_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()

    # Count lines up to and including closing ---
    end_line = content[: end_idx + 4].count("\n") + 1
    return result, end_line


def _parse_table_row(line: str) -> list[str] | None:
    """Parse a markdown table row into a list of cell strings.

    Returns None if the line is not a table row.
    Strips leading/trailing whitespace from each cell.
    """
    m = TABLE_ROW_RE.match(line)
    if not m:
        return None
    cells = [c.strip() for c in m.group(1).split("|")]
    return cells


def _parse_value_principles(
    section_lines: list[tuple[int, str]],
) -> tuple[list[Principle], list[BoundaryRule]]:
    """Parse principles and boundary table from the Value Principles section.

    Args:
        section_lines: List of (lineno, line_text) pairs for the section content.

    Returns:
        (principles, boundary_rules)

    Raises:
        VisionParseError: On malformed principles or boundary table.
    """
    principles: list[Principle] = []
    boundary_rules: list[BoundaryRule] = []

    # Two passes: collect principles first, then boundary table
    # State machine for table detection
    in_table = False
    table_header_parsed = False
    table_start_line = 0

    for lineno, line in section_lines:
        # Try to match principle
        pm = PRINCIPLE_RE.match(line)
        if pm and not in_table:
            pid = pm.group(1).upper()  # normalize to uppercase
            text = pm.group(2).strip()
            principles.append(Principle(id=pid, text=text))
            continue

        # Detect table rows
        if TABLE_ROW_RE.match(line):
            if not in_table:
                in_table = True
                table_start_line = lineno
                table_header_parsed = False
                # Parse header row
                cells = _parse_table_row(line)
                if cells is None or len(cells) != 4:
                    raise VisionParseError(
                        f"Boundary table has {len(cells) if cells else 0} columns, expected 4",
                        lineno,
                    )
                # Header must have 4 columns (we validated above)
                table_header_parsed = True
                continue
            else:
                # Check if it's a separator row
                if TABLE_SEPARATOR_RE.match(line):
                    continue

                # It's a data row
                cells = _parse_table_row(line)
                if cells is None or len(cells) != 4:
                    raise VisionParseError(
                        f"Boundary table has {len(cells) if cells else 0} columns, expected 4",
                        lineno,
                    )
                rule_id, rule, scope, source_section = (c.strip() for c in cells)
                boundary_rules.append(
                    BoundaryRule(
                        rule_id=rule_id,
                        rule=rule,
                        scope=scope,
                        source_section=source_section,
                    )
                )
        else:
            in_table = False

    # Validate: boundary rule_ids must reference known principles
    principle_ids = {p.id for p in principles}
    for br in boundary_rules:
        br_id = br.rule_id.upper()
        if br_id not in principle_ids:
            # Find the line number for this rule
            # Search for the rule_id in section_lines
            rule_lineno = 0
            for lineno, line in section_lines:
                if br.rule_id in line and TABLE_ROW_RE.match(line):
                    rule_lineno = lineno
                    break
            raise VisionParseError(
                f"Boundary rule_id '{br.rule_id}' has no matching principle",
                rule_lineno or table_start_line,
            )

    return principles, boundary_rules


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_vision(path: Path) -> Vision:
    """Parse a v1 vision.md file into a Vision dataclass.

    Args:
        path: Path to the vision.md file.

    Returns:
        A fully populated Vision dataclass.

    Raises:
        VisionParseError: On any malformed input, with a message including
                          line:col of the offending location.
        FileNotFoundError: If path does not exist.
    """
    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()

    # --- Frontmatter ---
    frontmatter, fm_end_line = _parse_frontmatter(raw_text)

    if "template_version" not in frontmatter:
        raise VisionParseError("Missing frontmatter 'template_version'", 1)

    try:
        template_version = int(frontmatter["template_version"])
    except ValueError:
        raise VisionParseError(
            f"Invalid frontmatter 'template_version': '{frontmatter['template_version']}'", 1
        )

    if template_version != 1:
        raise VisionParseError(
            f"Unsupported template_version: {template_version} (expected 1)", 1
        )

    # --- Section parsing ---
    # Walk through lines tracking H2 sections
    # Each section maps to a canonical field name
    # We collect (lineno, line) pairs per section

    section_content: dict[str, list[tuple[int, str]]] = {k: [] for k in REQUIRED_SECTIONS_ORDER}
    section_order: list[str] = []  # order in which sections appear

    current_section: str | None = None
    current_section_lineno: int = 0

    for i, line in enumerate(lines, start=1):
        h2m = H2_RE.match(line)
        if h2m:
            header_text = h2m.group(1).strip()
            canonical = SECTION_ALIASES.get(header_text.lower())
            if canonical:
                # Validate ordering: must appear in REQUIRED_SECTIONS_ORDER order
                if section_order:
                    last_canonical = section_order[-1]
                    last_idx = REQUIRED_SECTIONS_ORDER.index(last_canonical)
                    this_idx = REQUIRED_SECTIONS_ORDER.index(canonical)
                    if this_idx <= last_idx:
                        raise VisionParseError(
                            f"Section '{SECTION_DISPLAY[canonical]}' found after "
                            f"'{SECTION_DISPLAY[last_canonical]}'",
                            i,
                        )
                section_order.append(canonical)
                current_section = canonical
                current_section_lineno = i
            else:
                # Unknown H2 — ignore it (don't reset current_section)
                # Actually stop collecting for the current section
                current_section = None
        elif current_section is not None:
            section_content[current_section].append((i, line))

    # Validate all required sections are present
    for canonical in REQUIRED_SECTIONS_ORDER:
        if canonical not in section_order:
            # Report at end of file or last known position
            raise VisionParseError(
                f"Missing required section '{SECTION_DISPLAY[canonical]}'",
                len(lines),
            )

    # --- Build Vision ---
    vision = Vision(template_version=template_version, raw_text=raw_text)

    # Simple text sections: join lines, strip
    def _section_text(canonical: str) -> str:
        return "\n".join(line for _, line in section_content[canonical]).strip()

    vision.vision_statement = _section_text("vision_statement")
    vision.target_group = _section_text("target_group")
    vision.core_need = _section_text("core_need")
    vision.positioning = _section_text("positioning")
    vision.business_goal = _section_text("business_goal")
    vision.not_in_vision = _section_text("not_in_vision")

    # Value Principles: principles + boundary table
    principles, boundary_rules = _parse_value_principles(section_content["value_principles"])
    vision.principles = principles
    vision.boundary_table = boundary_rules

    return vision


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _vision_to_json(vision: Vision) -> dict:
    """Convert a Vision to a JSON-serialisable dict for CLI output."""
    return {
        "template_version": vision.template_version,
        "vision_statement": vision.vision_statement,
        "target_group": vision.target_group,
        "core_need": vision.core_need,
        "positioning": vision.positioning,
        "business_goal": vision.business_goal,
        "not_in_vision": vision.not_in_vision,
        "principles": [
            {"id": p.id, "text": p.text, "source_section": p.source_section}
            for p in vision.principles
        ],
        "boundary_table": [
            {
                "rule_id": br.rule_id,
                "rule": br.rule,
                "scope": br.scope,
                "source_section": br.source_section,
            }
            for br in vision.boundary_table
        ],
    }


def main(argv: list[str]) -> int:
    """CLI: python3 scripts/vision_parser.py <vision.md> [...]

    Prints a JSON summary for each file to stdout.
    Exits 0 on success, 1 on parse error, 2 on usage error.
    """
    if not argv:
        print("Usage: vision_parser.py <vision.md> [<vision.md> ...]", file=sys.stderr)
        return 2

    exit_code = 0
    for arg in argv:
        path = Path(arg)
        if not path.exists():
            print(f"vision-parser: file not found: {arg}", file=sys.stderr)
            exit_code = 1
            continue
        try:
            vision = parse_vision(path)
            print(json.dumps(_vision_to_json(vision), indent=2))
        except VisionParseError as exc:
            print(f"vision-parser: {exc}", file=sys.stderr)
            exit_code = 1
        except Exception as exc:
            print(f"vision-parser: unexpected error reading {arg}: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
