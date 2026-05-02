from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT = REPO_ROOT / "beads-workflow" / "agents" / "wave-orchestrator.md"


def test_wave_orchestrator_bundled_scripts_exist_under_plugin_root() -> None:
    script_dir = REPO_ROOT / "beads-workflow" / "skills" / "wave-orchestrator" / "scripts"
    script_names = [
        "wave-dispatch.py",
        "wave-status.py",
        "wave-completion.py",
        "wave-lock.py",
        "arch-signal-detect.py",
    ]

    for script_name in script_names:
        assert (script_dir / script_name).is_file(), script_name


def test_wave_orchestrator_prompt_uses_plugin_root_before_find() -> None:
    content = PROMPT.read_text()
    start = content.index('if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then')
    end = content.index("## Arguments", start)
    block = content[start:end]
    env_code = block.split("```", 1)[0]

    assert (
        "${CLAUDE_PLUGIN_ROOT}/beads-workflow/skills/wave-orchestrator/scripts"
        in env_code
    )
    assert "find " not in env_code
    assert "Only if `${CLAUDE_PLUGIN_ROOT}` is unset" in block
    assert "find ~/.claude/skills -path" in block
    assert 'find . -path "*/wave-orchestrator/scripts"' in block
    assert "Do not call `find` when `${CLAUDE_PLUGIN_ROOT}` is set" in block

    for variable in [
        "WAVE_DISPATCH_PY",
        "WAVE_STATUS_PY",
        "WAVE_COMPLETION_PY",
        "WAVE_LOCK_PY",
        "ARCH_SIGNAL_DETECT_PY",
    ]:
        assert variable in block


def test_wave_orchestrator_skips_phase_125_for_small_waves_with_notes() -> None:
    content = PROMPT.read_text()
    phase_start = content.index("## Phase 1.25: Wave Structural Review")
    review_start = content.index("### Spawning the Wave-Reviewer Subagent", phase_start)
    skip_block = content[phase_start:review_start]

    assert "if wave_size < 3: skip" in skip_block
    assert "bd update \"$id\" --append-notes=\"Wave review skipped: wave_size=<N> (<3)" in skip_block
    assert "codex exec" not in skip_block
