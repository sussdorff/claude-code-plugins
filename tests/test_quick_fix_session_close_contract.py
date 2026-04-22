"""Regression tests for CCP-793 quick-fix -> session-close handoff."""

from pathlib import Path


QUICK_FIX_MD = Path("beads-workflow/agents/quick-fix.md")


def section(content: str, start_marker: str, end_marker: str) -> str:
    start = content.find(start_marker)
    end = content.find(end_marker, start)
    return content[start:end] if start != -1 and end != -1 else ""


def test_phase0_captures_runtime_branch_context():
    content = QUICK_FIX_MD.read_text()
    assert "CURRENT_BRANCH=$(git branch --show-current)" in content
    assert 'WORKTREE_MODE="worktree"' in content
    assert 'WORKTREE_MODE="main-or-standalone"' in content


def test_runtime_context_explicitly_supports_main_mode():
    content = QUICK_FIX_MD.read_text()
    runtime_section = section(content, "## Runtime Context", "## Portless Namespace")
    assert "spawned inline as an `Agent(...)` subagent" in runtime_section
    assert "Never assume `worktree-bead-{BEAD_ID}` exists." in runtime_section


def test_phase5_requires_bare_agent_invocation_retry():
    content = QUICK_FIX_MD.read_text()
    phase5 = section(content, "### Phase 5: Auto-Trigger Session-Close", "### Why Agent() and not cmux send")
    assert "must contain the `Agent(...)` tool call" in phase5
    assert "and NO prose before or after it" in phase5
    assert 'If the runtime responds with **"Your tool call was malformed and could not be parsed"**' in phase5
    assert "Your **next response must be ONLY** the retried `Agent(subagent_type=\"core:session-close\", ...)`" in phase5


def test_phase5_forbids_parent_side_session_close_emulation():
    content = QUICK_FIX_MD.read_text()
    phase5 = section(content, "### Phase 5: Auto-Trigger Session-Close", "### Why Agent() and not cmux send")
    assert "git/tag/`bd close`/learnings work yourself" in phase5
    assert "Do NOT reinterpret this handoff as `--debrief-only` or `--ship-only` from the parent." in phase5
    assert "- Current branch: {CURRENT_BRANCH}" in phase5
    assert "- Worktree mode: {WORKTREE_MODE}" in phase5
    assert "Feature branch: worktree-bead-{BEAD_ID}" not in phase5
