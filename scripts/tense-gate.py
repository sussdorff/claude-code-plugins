#!/usr/bin/env python3
"""
tense-gate: Lint prescriptive-present documents for future-tense markers.

Scans vision.md and any file with YAML frontmatter `document_type: prescriptive-present`
for future-tense language that violates the "present-tense truth" contract.

Exits 0 if clean, 1 if violations found.

Allowlist: a comment `<!-- tense-gate-ignore: <reason> -->` on the line IMMEDIATELY
BEFORE a violating line causes that line to be skipped.

Usage:
    python3 scripts/tense-gate.py docs/vision.md
    python3 scripts/tense-gate.py docs/vision.md docs/strategy.md
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Marker definitions
# Each entry: (pattern, tag, explanation)
# ---------------------------------------------------------------------------
MARKERS = [
    # Future-tense verb constructions
    (r"\bwill\s+\w+", "will", "Future-tense marker in prescriptive document."),
    (r"\bshould\s+\w+", "should", "Future-tense / deferral marker in prescriptive document."),

    # Planning language
    (r"\bplan(?:ning)?\s+to\b", "plan to", "Planning language not allowed in prescriptive document."),
    (r"\bgoing\s+to\b", "going to", "Planning language not allowed in prescriptive document."),

    # Temporal deferral
    (r"\bby\s+Q[1-4]\b", "by Qn", "Roadmap quarter reference not allowed in prescriptive document."),
    (
        r"\bby\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
        "by <month>",
        "Roadmap month reference not allowed in prescriptive document.",
    ),
    (r"\bby\s+(?:20\d{2})\b", "by <year>", "Roadmap year reference not allowed in prescriptive document."),
    (r"\beventually\b", "eventually", "Deferral language not allowed in prescriptive document."),
    (r"\blater\b", "later", "Deferral language not allowed in prescriptive document."),
    (r"\bin\s+the\s+future\b", "in the future", "Deferral language not allowed in prescriptive document."),

    # Stub / placeholder markers
    (r"\bTBD\b", "TBD", "Placeholder marker not allowed in prescriptive document."),
    (r"\bSTUB\b", "STUB", "Placeholder marker not allowed in prescriptive document."),
    (r"\bTODO\b", "TODO", "TODO marker not allowed in prescriptive document."),

    # Explicit deferral phrases
    (r"\bto\s+be\s+locked\s+by\b", "to be locked by", "Deferral phrase not allowed in prescriptive document."),
    (r"\bto\s+be\s+decided\b", "to be decided", "Deferral phrase not allowed in prescriptive document."),
    (r"\bto\s+be\s+determined\b", "to be determined", "Deferral phrase not allowed in prescriptive document."),
]

# Pre-compile all patterns (case-insensitive)
COMPILED = [(re.compile(pattern, re.IGNORECASE), tag, explanation) for pattern, tag, explanation in MARKERS]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PRESCRIPTIVE_TYPE_RE = re.compile(r"document_type:\s*[\"']?prescriptive-present[\"']?")
IGNORE_COMMENT_RE = re.compile(r"<!--\s*tense-gate-ignore\s*:", re.IGNORECASE)

VISION_MD_NAMES = {"vision.md"}


def is_prescriptive(path: Path, content: str) -> bool:
    """Return True if the file should be linted."""
    if path.name in VISION_MD_NAMES:
        return True
    # Check YAML frontmatter
    m = FRONTMATTER_RE.match(content)
    if m and PRESCRIPTIVE_TYPE_RE.search(m.group(1)):
        return True
    return False


def lint_file(path: Path) -> list[tuple[int, str, str, str]]:
    """
    Lint a single file. Returns a list of (lineno, tag, explanation, matched_line).
    """
    content = path.read_text(encoding="utf-8")
    if not is_prescriptive(path, content):
        return []

    lines = content.splitlines()
    violations = []
    in_code_fence = False

    for i, line in enumerate(lines, start=1):
        # Toggle code fence tracking (``` or ~~~)
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        prev_line = lines[i - 2] if i >= 2 else ""
        if IGNORE_COMMENT_RE.search(prev_line):
            continue  # allowlisted

        for pattern, tag, explanation in COMPILED:
            if pattern.search(line):
                violations.append((i, tag, explanation, line.strip()))
                break  # Only report the first matching marker per line

    return violations


def format_violation(rel_path: str, lineno: int, tag: str, explanation: str, line: str) -> str:
    suggest = (
        f"  Suggest: rewrite as principle (present-tense) OR move to bead/roadmap"
    )
    return (
        f"{rel_path}:{lineno}:1: [{tag}] {explanation}\n"
        f"  Found: '{line}'\n"
        f"{suggest}"
    )


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: tense-gate.py <file> [<file> ...]", file=sys.stderr)
        return 2

    total_violations = 0

    for arg in argv:
        path = Path(arg)
        if not path.exists():
            print(f"tense-gate: file not found: {arg}", file=sys.stderr)
            total_violations += 1
            continue

        try:
            violations = lint_file(path)
        except Exception as exc:
            print(f"tense-gate: error reading {arg}: {exc}", file=sys.stderr)
            total_violations += 1
            continue

        rel_path = arg  # Use the path as supplied
        for lineno, tag, explanation, line in violations:
            print(format_violation(rel_path, lineno, tag, explanation, line))
            total_violations += 1

    return 1 if total_violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
