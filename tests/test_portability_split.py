"""
Test: CCP-tkd — Portability split for pilot skills.
Test: CCP-50y — Portability split for 10 candidate skills.
Verifies that SKILL.md files contain no Claude-specific references,
and that adapter files exist.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOTS = [
    Path("dev-tools/skills/bug-triage"),
    Path("dev-tools/skills/spec-developer"),
    Path("dev-tools/skills/project-context"),
    # CCP-50y: 10 new candidate skills
    Path("dev-tools/skills/project-health"),
    Path("dev-tools/skills/binary-explorer"),
    Path("meta/skills/entropy-scan"),
    Path("meta/skills/nbj-audit"),
    Path("meta/skills/system-prompt-audit"),
    Path("core/skills/vision"),
    Path("infra/skills/infra-principles"),
    Path("meta/skills/skill-auditor"),
    Path("meta/skills/token-cost"),
    Path("meta/skills/agent-forge"),
]

# Patterns that MUST NOT appear in portable SKILL.md
FORBIDDEN_IN_PORTABLE = [
    # Named MCP tool invocations
    r"mcp__open-brain",
    # Harness-specific file paths
    r"~/.claude/events\.db",
    r"~/.claude/CLAUDE\.md",
    r"malte/hooks/buglog",
    # Slash-command invocations
    r"/event-log",
    r"/epic-init\b",
    r"^/[a-z][a-z0-9-]+(?:\s|$)",  # generic slash-command at start of line
    # Harness-specific agent names
    r"bead-orchestrator",
    r"session-close",
    # Non-runtime Claude frontmatter keys
    # NOTE: runtime-consumed keys (model, disable-model-invocation) are EXEMPT —
    # they must stay in SKILL.md because the harness loader only reads SKILL.md frontmatter.
    # See docs/codex-skills-portability-rules.md Rule 5.
    r"\$ARGUMENTS",
    # Imperative references to CLAUDE.md as a direct read target
    r"(?:^|\s)Read\s+`?\.?/?CLAUDE\.md",
    # Named Claude tool identifiers in imperative instructions
    r"\bUse\s+(?:the\s+)?(?:Read|Glob|Grep|Bash|Edit|Write|NotebookEdit|WebFetch|WebSearch|Task|TodoWrite)(?:\s+tools?|\s+tool)?\b",
    r"\bCall\s+(?:the\s+)?(?:Read|Glob|Grep|Bash|Edit|Write|NotebookEdit|WebFetch|WebSearch|Task|TodoWrite)\b",
]

def test_portable_skill_has_no_harness_specific_content():
    for skill_dir in SKILL_ROOTS:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"{skill_file} does not exist"
        content = skill_file.read_text()
        for pattern in FORBIDDEN_IN_PORTABLE:
            matches = re.findall(pattern, content, re.MULTILINE)
            assert not matches, (
                f"Forbidden pattern '{pattern}' found in {skill_file}: {matches}"
            )

def test_claude_adapter_exists_for_each_skill():
    for skill_dir in SKILL_ROOTS:
        adapter_file = skill_dir / "SKILL.claude-adapter.md"
        assert adapter_file.exists(), f"Missing adapter: {adapter_file}"
        content = adapter_file.read_text()
        assert "harness: claude" in content, f"Adapter {adapter_file} missing 'harness: claude' frontmatter"


def test_codex_inventory_discovers_unique_skill_names():
    inventory_script = Path("scripts/codex_skills.py")
    result = subprocess.run(
        [sys.executable, str(inventory_script), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    inventory = json.loads(result.stdout)
    names = [item["name"] for item in inventory]
    assert len(names) == len(set(names)), "codex skill discovery must produce unique names"
    assert "my-skill" not in names, "test fixtures must not leak into the export inventory"

def test_codex_skills_candidates_doc_exists():
    """CCP-50y AC1/AC2: docs/codex-skills-candidates.md must exist and contain required sections."""
    doc = Path("docs/codex-skills-candidates.md")
    assert doc.exists(), "docs/codex-skills-candidates.md does not exist"
    content = doc.read_text()
    # AC2: Selection criteria must be documented
    assert "## Selection Criteria" in content, "Missing '## Selection Criteria' section"
    # AC1: Candidate list with 10 items
    assert "## Candidate List" in content, "Missing '## Candidate List' section"
    # AC4: Deferrals must be documented
    assert "## Deferrals" in content, "Missing '## Deferrals' section"
    # Must have at least 10 candidate rows (each row starts with '|' and has a skill name)
    candidate_rows = [
        line for line in content.splitlines()
        if line.strip().startswith('|')
        and any(token in line for token in ('converted', 'deferred', '✅', '⏭'))
    ]
    assert len(candidate_rows) >= 10, (
        f"Expected at least 10 skill rows in candidate list, found {len(candidate_rows)}"
    )


def test_sync_script_uses_dynamic_discovery_not_default_allowlist():
    """CCP-wyi: sync-codex-skills must use dynamic discovery instead of a hardcoded pilot set."""
    sync_script = Path("scripts/sync-codex-skills")
    assert sync_script.exists(), "scripts/sync-codex-skills does not exist"
    content = sync_script.read_text()
    assert "DEFAULT_SKILLS" not in content
    assert "skills-registry.json" not in content


def test_portability_rules_doc_exists():
    rules_doc = Path("docs/codex-skills-portability-rules.md")
    assert rules_doc.exists(), "docs/codex-skills-portability-rules.md does not exist"
    content = rules_doc.read_text()
    assert "portable core" in content.lower() or "portable" in content.lower()
    assert "adapter" in content.lower()
    assert "naming convention" in content.lower() or "naming" in content.lower()


def test_project_context_phase1a_mentions_both_conventions_files():
    """
    Regression test for CCP-5d0: Phase 1 §1a must load both CLAUDE.md and AGENTS.md
    when both exist, not just one of them.
    """
    skill_file = Path("dev-tools/skills/project-context/SKILL.md")
    assert skill_file.exists(), f"{skill_file} does not exist"
    content = skill_file.read_text()

    # Find the §1a block — it starts at "**1a." and ends before "**1b."
    phase1a_match = re.search(
        r"\*\*1a\.(.*?)(?=\*\*1b\.)", content, re.DOTALL
    )
    assert phase1a_match, "Could not find §1a block in SKILL.md"
    section_1a = phase1a_match.group(0)

    # Both file names must be mentioned in §1a
    assert "CLAUDE.md" in section_1a, "§1a does not mention CLAUDE.md"
    assert "AGENTS.md" in section_1a, "§1a does not mention AGENTS.md"

    # The source-header pattern must be present so agents know how to label each file
    assert "# From CLAUDE.md" in section_1a, (
        "§1a missing source header pattern '# From CLAUDE.md'"
    )
    assert "# From AGENTS.md" in section_1a, (
        "§1a missing source header pattern '# From AGENTS.md'"
    )
