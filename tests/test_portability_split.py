"""
Test: CCP-tkd — Portability split for pilot skills.
Verifies that SKILL.md files contain no Claude-specific references,
and that adapter files exist.
"""
import re
from pathlib import Path

SKILL_ROOTS = [
    Path("dev-tools/skills/bug-triage"),
    Path("dev-tools/skills/spec-developer"),
    Path("dev-tools/skills/project-context"),
]

# Patterns that MUST NOT appear in portable SKILL.md
FORBIDDEN_IN_PORTABLE = [
    r"mcp__open-brain",
    r"~/.claude/events\.db",
    r"~/.claude/CLAUDE\.md",
    r"malte/hooks/buglog",
    r"/event-log",
    r"/epic-init\b",
    r"bead-orchestrator",
    r"session-close",
]

def test_portable_skill_has_no_harness_specific_content():
    for skill_dir in SKILL_ROOTS:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"{skill_file} does not exist"
        content = skill_file.read_text()
        for pattern in FORBIDDEN_IN_PORTABLE:
            matches = re.findall(pattern, content)
            assert not matches, (
                f"Forbidden pattern '{pattern}' found in {skill_file}: {matches}"
            )

def test_claude_adapter_exists_for_each_skill():
    for skill_dir in SKILL_ROOTS:
        adapter_file = skill_dir / "SKILL.claude-adapter.md"
        assert adapter_file.exists(), f"Missing adapter: {adapter_file}"
        content = adapter_file.read_text()
        assert "harness: claude" in content, f"Adapter {adapter_file} missing 'harness: claude' frontmatter"

def test_portability_rules_doc_exists():
    rules_doc = Path("docs/codex-skills-portability-rules.md")
    assert rules_doc.exists(), "docs/codex-skills-portability-rules.md does not exist"
    content = rules_doc.read_text()
    assert "portable core" in content.lower() or "portable" in content.lower()
    assert "adapter" in content.lower()
    assert "naming convention" in content.lower() or "naming" in content.lower()
