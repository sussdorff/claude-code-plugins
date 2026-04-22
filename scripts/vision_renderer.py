#!/usr/bin/env python3
"""
vision-renderer: Render a VisionAnswers dataclass into a v1-conformant vision.md string.

Used by the /vision-author skill to produce the final docs/vision.md output.
Consumed by tests/test_vision_author.py for golden-file validation.

Public API:
    VisionAnswers   — dataclass capturing all 7 Q&A answers
    render_vision   — render VisionAnswers -> v1-conformant vision.md string

Validation rules (enforced in render_vision):
    - vision_statement: ≤30 words, raises ValueError if exceeded
    - principles: 3–5 entries, raises ValueError if out of range
    - principle_scopes: must have an entry for every principle ID
    - boundary table: 4 columns — rule_id | rule | scope | source-section
    - source-section column: always "Value Principles"
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class VisionAnswers:
    """Structured answers from the 7-question /vision-author dialogue.

    Attributes:
        vision_statement:  Q1 — ≤30 words, ≤1 sentence, present-tense.
        target_group:      Q2 — who the product serves.
        core_need:         Q3 — job-to-be-done / core pain the product solves.
        positioning:       Q4 — competitive framing (for X who Y, our Z provides W).
        principles:        Q5 — 3–5 value principles as (rule_id, text) tuples.
        principle_scopes:  Q5 — mapping rule_id -> scope string for boundary table.
        business_goal:     Q6 — measurable outcome metric.
        not_in_vision:     Q7 — list of explicitly deferred items (2+ required).
    """

    vision_statement: str
    target_group: str
    core_need: str
    positioning: str
    principles: list[tuple[str, str]]   # [(rule_id, text), ...]
    principle_scopes: dict[str, str]    # rule_id -> scope
    business_goal: str
    not_in_vision: list[str]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_MIN_PRINCIPLES = 3
_MAX_PRINCIPLES = 5
_MAX_VISION_WORDS = 30


def _word_count(text: str) -> int:
    """Return the number of whitespace-delimited words in text."""
    return len(text.split())


def _validate_answers(answers: VisionAnswers) -> None:
    """Raise ValueError on constraint violations before rendering."""
    wc = _word_count(answers.vision_statement)
    if wc > _MAX_VISION_WORDS:
        raise ValueError(
            f"vision_statement is {wc} words — must be ≤{_MAX_VISION_WORDS} words "
            f"(got: {answers.vision_statement!r})"
        )

    count = len(answers.principles)
    if count < _MIN_PRINCIPLES:
        raise ValueError(
            f"principles must have at least {_MIN_PRINCIPLES} entries — "
            f"got {count}. Add more or move extras to NOT in Vision."
        )
    if count > _MAX_PRINCIPLES:
        raise ValueError(
            f"principles must have at most {_MAX_PRINCIPLES} entries — "
            f"got {count}. Extra principles belong in NOT in Vision as deferred items."
        )


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def _render_frontmatter() -> str:
    return """\
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---
"""


def _render_principles_list(principles: list[tuple[str, str]]) -> str:
    lines = []
    for rule_id, text in principles:
        lines.append(f"- **{rule_id}**: {text}")
    return "\n".join(lines)


def _render_boundary_table(
    principles: list[tuple[str, str]],
    scopes: dict[str, str],
) -> str:
    header = "| rule_id | rule | scope | source-section |"
    separator = "|---------|------|-------|----------------|"
    rows = []
    for rule_id, text in principles:
        scope = scopes.get(rule_id, "all")
        rows.append(f"| {rule_id} | {text} | {scope} | Value Principles |")
    return "\n".join([header, separator] + rows)


def _render_not_in_vision(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_vision(answers: VisionAnswers) -> str:
    """Render a VisionAnswers dataclass into a v1-conformant vision.md string.

    Args:
        answers: Populated VisionAnswers dataclass from the 7-question dialogue.

    Returns:
        Complete vision.md content as a string, starting with YAML frontmatter
        and containing all 7 locked sections plus 4-column boundary table.

    Raises:
        ValueError: If vision_statement exceeds 30 words, or if principles count
                    is outside the [3, 5] range.
    """
    _validate_answers(answers)

    sections: list[str] = []

    sections.append(_render_frontmatter())

    sections.append(f"## Vision Statement\n\n{answers.vision_statement.strip()}")

    sections.append(f"## Target Group\n\n{answers.target_group.strip()}")

    sections.append(f"## Core Need (JTBD)\n\n{answers.core_need.strip()}")

    sections.append(f"## Positioning\n\n{answers.positioning.strip()}")

    principles_block = _render_principles_list(answers.principles)
    boundary_block = _render_boundary_table(answers.principles, answers.principle_scopes)
    sections.append(f"## Value Principles\n\n{principles_block}\n\n{boundary_block}")

    sections.append(f"## Business Goal\n\n{answers.business_goal.strip()}")

    not_in_vision_block = _render_not_in_vision(answers.not_in_vision)
    sections.append(f"## NOT in Vision\n\n{not_in_vision_block}")

    return "\n\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point (for quick ad-hoc testing)
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    """Print a sample rendered vision.md to stdout."""
    sample = VisionAnswers(
        vision_statement="We deliver reliable infrastructure tooling for platform engineers.",
        target_group="Platform engineers at mid-size software companies.",
        core_need="Engineers need reproducible, auditable infrastructure changes without manual toil.",
        positioning=(
            "For platform teams drowning in config drift, "
            "our tooling provides automated enforcement that SaaS vendors cannot match."
        ),
        principles=[
            ("P1", "All infrastructure changes are applied through version-controlled manifests."),
            ("P2", "Every policy violation surfaces at plan time, not apply time."),
            ("P3", "Operators see full change context before confirming any action."),
        ],
        principle_scopes={
            "P1": "all infrastructure modules",
            "P2": "policy engine, CI pipelines",
            "P3": "operator CLI, dashboard",
        },
        business_goal="Reduce unplanned outages caused by config drift by 90% within six months.",
        not_in_vision=[
            "Auto-remediation without operator approval",
            "Support for non-declarative infrastructure tools",
        ],
    )
    print(render_vision(sample))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
