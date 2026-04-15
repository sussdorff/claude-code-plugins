#!/usr/bin/env python3
"""
Structural tests for the /project-context skill.
Validates SKILL.md structure and output template completeness.
"""
import sys
from pathlib import Path

# Required sections in SKILL.md
REQUIRED_SKILL_SECTIONS = [
    "# /project-context",
    "## When to Use",
    "## Arguments",
    "## Workflow",
    "Tech-Stack",
    "Module Map",
    "Patterns",
    "Invarianten",
]

# Required sections in the output template
REQUIRED_TEMPLATE_SECTIONS = [
    "## Tech Stack",
    "## Architecture Principles",
    "## Module Map",
    "## Established Patterns",
    "## Critical Invariants",
]

def test_skill_md_exists():
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

def test_skill_md_has_required_sections():
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    for section in REQUIRED_SKILL_SECTIONS:
        assert section in content, f"Missing required section in SKILL.md: {section}"

def test_skill_md_has_frontmatter():
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
    assert "name: project-context" in content, "frontmatter must have name: project-context"
    assert "description:" in content, "frontmatter must have description"

def test_output_template_exists():
    template_path = Path(__file__).parent.parent / "references" / "output-template.md"
    assert template_path.exists(), f"output-template.md not found at {template_path}"

def test_output_template_has_required_sections():
    template_path = Path(__file__).parent.parent / "references" / "output-template.md"
    content = template_path.read_text()
    for section in REQUIRED_TEMPLATE_SECTIONS:
        assert section in content, f"Missing required section in output-template.md: {section}"

def test_skill_handles_overwrite_scenario():
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "exist" in content.lower() and ("overwrite" in content.lower() or "--force" in content.lower()),         "SKILL.md must describe overwrite handling"

def test_skill_has_argument_hint():
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    content = skill_path.read_text()
    assert "argument-hint" in content, "frontmatter must have argument-hint"

if __name__ == "__main__":
    import traceback
    tests = [
        test_skill_md_exists,
        test_skill_md_has_required_sections,
        test_skill_md_has_frontmatter,
        test_output_template_exists,
        test_output_template_has_required_sections,
        test_skill_handles_overwrite_scenario,
        test_skill_has_argument_hint,
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
