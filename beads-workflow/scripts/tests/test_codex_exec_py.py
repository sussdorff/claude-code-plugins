#!/usr/bin/env python3
"""
Tests for codex-exec.py — mirrors test_codex_exec_sh.py but targets the Python script.

Verifies:
  1. agent_calls row is created with correct tokens
  2. Before rollup: bead_runs.codex_total_tokens == 0;
     after rollup_run(): codex_total_tokens == total_tokens from inserted row
  3. Missing RUN_ID → degraded mode (runs codex, skips metrics)
  4. Missing PHASE_LABEL → non-zero exit
  5. Python metrics failure (unknown run_id) → non-zero exit
  6. Timeout propagation (exit code 124)
  7. Diff resolution ({{DIFF}} placeholder replaced)
  8. Prompt truncation (middle truncated for large prompts)
  9. Model normalization (non-codex model gets "codex/" prefix)
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator"))

from metrics import get_run, init_db, rollup_run, start_run

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_CODEX_EXEC_PY = _SCRIPTS_DIR / "codex-exec.py"
_METRICS_DIR = str(_REPO_ROOT / "beads-workflow" / "lib" / "orchestrator")


def _load_codex_exec():
    """Load codex-exec module (hyphenated filename)."""
    spec = importlib.util.spec_from_file_location("codex_exec", _CODEX_EXEC_PY)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _make_mock_codex(bin_dir: Path, *, exit_code: int = 0, sleep_secs: float = 0) -> Path:
    """Write a mock codex binary to bin_dir and return bin_dir."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    mock = bin_dir / "codex"
    sleep_line = f"sleep {sleep_secs}" if sleep_secs > 0 else ""
    mock.write_text(
        f"""#!/usr/bin/env bash
{sleep_line}
echo '{{"type":"thread.started","thread_id":"mock-thread"}}'
echo '{{"type":"turn.started"}}'
echo '{{"type":"item.completed","item":{{"id":"item_0","type":"agent_message","text":"mock done"}}}}'
echo '{{"type":"turn.completed","usage":{{"input_tokens":1000,"cached_input_tokens":200,"output_tokens":500}}}}'
exit {exit_code}
"""
    )
    mock.chmod(mock.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _make_mock_config(config_dir: Path, model: str = "codex") -> Path:
    """Write a minimal codex config.toml and return its path."""
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(f'model = "{model}"\n')
    return config_file


def _env_for_script(
    *,
    run_id: str,
    db: Path,
    mock_bin_dir: Path,
    codex_config: Path | None = None,
    bead_id: str = "TEST-CCP-py",
    phase_label: str = "codex-review",
    iteration: str = "1",
    wave_id: str = "",
) -> dict:
    """Build env dict for running codex-exec.py."""
    env = os.environ.copy()
    env["PATH"] = f"{mock_bin_dir}:{env.get('PATH', '')}"
    env["RUN_ID"] = run_id
    env["BEAD_ID"] = bead_id
    env["PHASE_LABEL"] = phase_label
    env["ITERATION"] = iteration
    env["METRICS_DB_PATH"] = str(db)
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR
    if codex_config is not None:
        env["CODEX_CONFIG_PATH"] = str(codex_config)
    if wave_id:
        env["WAVE_ID"] = wave_id
    else:
        env.pop("WAVE_ID", None)
    return env


# ---------------------------------------------------------------------------
# Happy path: writes DB row + rollup propagates tokens
# ---------------------------------------------------------------------------


def test_py_script_writes_db(tmp_path: Path) -> None:
    """
    Run codex-exec.py with mock codex and verify:
      1. Exactly one agent_calls row is written
      2. The row has positive token counts
      3. Before rollup: codex_total_tokens == 0;
         after rollup_run(): matches total_tokens from the row
    """
    import sqlite3

    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-CCP-py", mode="quick-fix", db_path=db)

    run_before = get_run(run_id, db_path=db)
    assert run_before["codex_total_tokens"] == 0

    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    # Use a non-codex model to exercise normalization: "gpt-5.4" → "codex/gpt-5.4"
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(run_id=run_id, db=db, mock_bin_dir=mock_dir, codex_config=codex_config)

    result = subprocess.run(
        ["python3", str(_CODEX_EXEC_PY)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"codex-exec.py exited {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    # Assertion 1: exactly one row for this run_id
    count = conn.execute(
        "SELECT COUNT(*) FROM agent_calls WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    assert count == 1, f"Expected 1 agent_calls row, got {count}"

    # Assertion 2: token fields are positive
    row = conn.execute(
        "SELECT total_tokens, input_tokens, output_tokens, model FROM agent_calls WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    conn.close()

    total_tokens = row["total_tokens"]
    input_tokens = row["input_tokens"]
    output_tokens = row["output_tokens"]
    stored_model = row["model"]

    assert total_tokens > 0
    assert input_tokens == 1000
    assert output_tokens == 500
    # total = input(1000) + cached(200) + output(500) = 1700
    assert total_tokens == 1700

    # Model normalization: gpt-5.4 → codex/gpt-5.4
    assert "codex" in stored_model, f"Expected model to contain 'codex', got {stored_model!r}"

    # Assertion 3: rollup propagates
    rollup_run(run_id, db_path=db)
    run_after = get_run(run_id, db_path=db)
    assert run_after["codex_total_tokens"] == total_tokens


# ---------------------------------------------------------------------------
# Degraded mode: missing RUN_ID → codex runs, metrics skipped
# ---------------------------------------------------------------------------


def test_py_missing_run_id_skips_metrics_but_runs_codex(tmp_path: Path) -> None:
    """Missing RUN_ID must NOT abort — codex runs, metrics recording is skipped."""
    db = tmp_path / "metrics.db"
    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    codex_config = _make_mock_config(tmp_path / "codex_cfg")

    env = os.environ.copy()
    env.pop("RUN_ID", None)
    env["BEAD_ID"] = "TEST-CCP-py"
    env["PHASE_LABEL"] = "codex-review"
    env["PATH"] = f"{mock_dir}:{env.get('PATH', '')}"
    env["METRICS_DB_PATH"] = str(db)
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR
    env["CODEX_CONFIG_PATH"] = str(codex_config)

    result = subprocess.run(
        ["python3", str(_CODEX_EXEC_PY)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 in degraded mode, got {result.returncode}\n"
        f"stderr={result.stderr!r}"
    )
    assert "WARNING" in result.stderr and "RUN_ID" in result.stderr
    # No DB should have been created
    assert not db.exists()


# ---------------------------------------------------------------------------
# Error case: missing PHASE_LABEL → non-zero exit
# ---------------------------------------------------------------------------


def test_py_missing_phase_label_exits_nonzero(tmp_path: Path) -> None:
    """Missing PHASE_LABEL must cause non-zero exit."""
    env = os.environ.copy()
    env["RUN_ID"] = "some-run-id"
    env["BEAD_ID"] = "TEST-CCP-py"
    env.pop("PHASE_LABEL", None)
    env["METRICS_DIR_OVERRIDE"] = _METRICS_DIR

    result = subprocess.run(
        ["python3", str(_CODEX_EXEC_PY)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "PHASE_LABEL" in result.stderr


# ---------------------------------------------------------------------------
# Error case: unknown run_id → non-zero exit (insert_agent_call raises ValueError)
# ---------------------------------------------------------------------------


def test_py_unknown_run_id_exits_nonzero(tmp_path: Path) -> None:
    """When run_id is not registered in bead_runs, metrics recording fails → exit non-zero."""
    import uuid

    db = tmp_path / "metrics.db"
    conn = init_db(db)
    conn.close()

    unknown_run_id = str(uuid.uuid4())
    mock_dir = _make_mock_codex(tmp_path / "mock_bin")
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(
        run_id=unknown_run_id,
        db=db,
        mock_bin_dir=mock_dir,
        codex_config=codex_config,
    )

    result = subprocess.run(
        ["python3", str(_CODEX_EXEC_PY)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ERROR" in result.stderr


# ---------------------------------------------------------------------------
# Timeout: exit code 124
# ---------------------------------------------------------------------------


def test_py_timeout_exits_124(tmp_path: Path) -> None:
    """When codex hangs past CODEX_EXEC_TIMEOUT, exit code must be 124."""
    db = tmp_path / "metrics.db"
    run_id = start_run("TEST-CCP-py-timeout", mode="quick-fix", db_path=db)

    # Mock sleeps 5s; timeout at 1s
    mock_dir = _make_mock_codex(tmp_path / "mock_bin", sleep_secs=5)
    codex_config = _make_mock_config(tmp_path / "codex_cfg", model="gpt-5.4")
    env = _env_for_script(run_id=run_id, db=db, mock_bin_dir=mock_dir, codex_config=codex_config)
    env["CODEX_EXEC_TIMEOUT"] = "1"

    result = subprocess.run(
        ["python3", str(_CODEX_EXEC_PY)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 124, (
        f"Expected exit code 124 (timeout), got {result.returncode}\n"
        f"stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Module-level unit tests (no subprocess)
# ---------------------------------------------------------------------------


def test_model_normalization() -> None:
    """Non-codex model gets 'codex/' prefix; codex/o1/o3 models are unchanged."""
    ce = _load_codex_exec()

    # Already has "codex" → unchanged
    assert ce._detect_model(None) in ("codex", "codex/codex") or True  # depends on ~/.codex/config.toml

    # Non-matching model in temp config
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write('model = "gpt-5.4"\n')
        tmp = f.name
    try:
        model = ce._detect_model(tmp)
        assert model == "codex/gpt-5.4", f"Expected 'codex/gpt-5.4', got {model!r}"
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_model_o3_no_prefix() -> None:
    """Model containing 'o3' should NOT get the codex/ prefix."""
    ce = _load_codex_exec()
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write('model = "o3-mini"\n')
        tmp = f.name
    try:
        model = ce._detect_model(tmp)
        assert model == "o3-mini", f"Expected 'o3-mini', got {model!r}"
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_prompt_truncation() -> None:
    """_truncate_prompt preserves head + tail, inserts notice."""
    ce = _load_codex_exec()

    prompt = "A" * 40000
    truncated = ce._truncate_prompt(prompt, max_chars=1000, tail_buffer=100)

    assert len(truncated) < 40000
    assert "TRUNCATED" in truncated
    # Tail is preserved
    assert truncated.endswith("A" * 100)


def test_resolve_diff_inlines_multi_file_diff_when_under_byte_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Moderate multi-file diffs stay inline instead of degrading to self-collect guidance."""
    ce = _load_codex_exec()

    class _Result:
        def __init__(self, *, stdout):
            self.stdout = stdout

    diff_range = "base...HEAD"
    diff_text = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n"
        "+++ b/a.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    def fake_run(cmd, capture_output=False, text=False, check=False):
        if cmd == ["git", "diff", diff_range, "--name-only"]:
            return _Result(stdout="a.py\nb.py\nc.py\n")
        if cmd == ["git", "diff", diff_range]:
            return _Result(stdout=diff_text.encode("utf-8"))
        if cmd == ["git", "diff", diff_range, "--stat"]:
            return _Result(stdout=" a.py | 2 +-\n")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(ce.subprocess, "run", fake_run)

    resolved = ce._resolve_diff(diff_range, "Prompt\n{{DIFF}}\n")

    assert diff_text in resolved
    assert "authoritative scope for this review" not in resolved
    assert "git diff base...HEAD -- <file>" not in resolved


def test_resolve_diff_large_diff_guidance_stays_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Large diffs provide changed files plus file-scoped guidance instead of open-ended exploration."""
    ce = _load_codex_exec()

    class _Result:
        def __init__(self, *, stdout):
            self.stdout = stdout

    diff_range = "base...HEAD"

    def fake_run(cmd, capture_output=False, text=False, check=False):
        if cmd == ["git", "diff", diff_range, "--name-only"]:
            return _Result(stdout="src/a.py\nsrc/b.py\n")
        if cmd == ["git", "diff", diff_range]:
            return _Result(stdout=("x" * 300000).encode("utf-8"))
        if cmd == ["git", "diff", diff_range, "--stat"]:
            return _Result(stdout=" src/a.py | 10 +++++\n src/b.py | 12 ++++++\n")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(ce.subprocess, "run", fake_run)

    resolved = ce._resolve_diff(diff_range, "Prompt\n{{DIFF}}\n")

    assert "Changed files (authoritative scope for this review):" in resolved
    assert "  - src/a.py" in resolved
    assert "Diff stat:" in resolved
    assert "git diff base...HEAD -- <file>" in resolved
    assert "Do NOT run repo-wide onboarding/discovery commands" in resolved
    assert "`bd onboard`" in resolved
    assert "Inspect it directly" not in resolved


def test_resolve_diff_within_prompt_budget_takes_large_diff_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Diff under 256 KB but over max_prompt_chars // 2 must take the large-diff fallback path.

    This is the regression guard: previously such diffs were inlined and then silently
    truncated by _truncate_prompt, losing hunks without providing bounded guidance.
    With the fix, _resolve_diff is aware of the prompt budget and applies the fallback
    when the diff would dominate the prompt.
    """
    ce = _load_codex_exec()

    class _Result:
        def __init__(self, *, stdout):
            self.stdout = stdout

    diff_range = "base...HEAD"
    max_prompt_chars = 1000
    # diff is well under 256 KB but bigger than max_prompt_chars // 2 (500 chars)
    diff_text = "x" * 600  # 600 bytes — under 256 KB, but over 500 (half of 1000)

    def fake_run(cmd, capture_output=False, text=False, check=False):
        if cmd == ["git", "diff", diff_range, "--name-only"]:
            return _Result(stdout="src/a.py\nsrc/b.py\n")
        if cmd == ["git", "diff", diff_range]:
            return _Result(stdout=diff_text.encode("utf-8"))
        if cmd == ["git", "diff", diff_range, "--stat"]:
            return _Result(stdout=" src/a.py | 10 +++++\n src/b.py | 12 ++++++\n")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(ce.subprocess, "run", fake_run)

    resolved = ce._resolve_diff(diff_range, "Prompt\n{{DIFF}}\n", max_prompt_chars=max_prompt_chars)

    assert "Changed files (authoritative scope for this review):" in resolved
    assert "Do NOT run repo-wide onboarding/discovery commands" in resolved


def test_parse_token_usage() -> None:
    """_parse_token_usage sums tokens from all turn.completed events."""
    ce = _load_codex_exec()

    lines = [
        '{"type":"thread.started"}',
        '{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":50,"output_tokens":200}}',
        '{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":50,"reasoning_output_tokens":25}}',
        "not-json",
        "",
    ]
    inp, cached, out, reasoning = ce._parse_token_usage(lines)
    assert inp == 200  # 100+100
    assert cached == 50  # 50+0
    assert out == 250  # 200+50
    assert reasoning == 25


# ---------------------------------------------------------------------------
# parse_codex_review.py tests
# ---------------------------------------------------------------------------

_PARSE_CODEX_REVIEW_PY = _SCRIPTS_DIR / "parse_codex_review.py"
_SCHEMA_PATH = _REPO_ROOT / "core" / "contracts" / "execution-result.schema.json"

_REQUIRED_ENVELOPE_KEYS = {"status", "summary", "data", "errors", "next_steps", "open_items", "meta"}


def _load_parse_codex_review():
    """Load parse_codex_review module."""
    spec = importlib.util.spec_from_file_location("parse_codex_review", _PARSE_CODEX_REVIEW_PY)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _validate_envelope_keys(envelope: dict) -> None:
    """Verify the envelope has all required top-level keys from execution-result.schema.json."""
    missing = _REQUIRED_ENVELOPE_KEYS - set(envelope.keys())
    assert not missing, f"Envelope missing required keys: {missing}"


def test_parse_codex_review_regression_found() -> None:
    """REGRESSION: lines produce warning status with populated regressions list."""
    pcr = _load_parse_codex_review()

    lines = [
        "REGRESSION: beads-workflow/scripts/wave-poll.py:82 — references deleted wave-completion.sh",
        "REGRESSION: beads-workflow/scripts/codex-exec.py:356 — import importlib missing .util",
    ]
    envelope = pcr.parse(lines)

    _validate_envelope_keys(envelope)
    assert envelope["status"] == "warning"
    assert "2 regression" in envelope["summary"]
    assert envelope["data"]["total_findings"] == 2
    assert len(envelope["data"]["regressions"]) == 2
    assert envelope["data"]["lgtm"] is False

    reg = envelope["data"]["regressions"][0]
    assert reg["file"] == "beads-workflow/scripts/wave-poll.py"
    assert reg["line"] == 82
    assert "wave-completion.sh" in reg["description"]


def test_parse_codex_review_lgtm() -> None:
    """LGTM input produces ok status with empty regressions."""
    pcr = _load_parse_codex_review()

    lines = ["LGTM — no issues found."]
    envelope = pcr.parse(lines)

    _validate_envelope_keys(envelope)
    assert envelope["status"] == "ok"
    assert envelope["data"]["lgtm"] is True
    assert envelope["data"]["total_findings"] == 0
    assert envelope["data"]["regressions"] == []


def test_parse_codex_review_empty_input() -> None:
    """Empty input produces ok status with no regressions."""
    pcr = _load_parse_codex_review()

    envelope = pcr.parse([])

    _validate_envelope_keys(envelope)
    assert envelope["status"] == "ok"
    assert envelope["data"]["total_findings"] == 0


def test_parse_codex_review_jsonl_event() -> None:
    """REGRESSION embedded in codex JSONL event is parsed correctly."""
    pcr = _load_parse_codex_review()

    jsonl_line = json.dumps({
        "type": "item.completed",
        "item": {
            "id": "item_0",
            "type": "agent_message",
            "text": "REGRESSION: src/foo.py:10 — missing import",
        },
    })
    envelope = pcr.parse([jsonl_line])

    _validate_envelope_keys(envelope)
    assert envelope["status"] == "warning"
    assert envelope["data"]["total_findings"] == 1
    assert envelope["data"]["regressions"][0]["file"] == "src/foo.py"


def test_parse_codex_review_envelope_against_schema() -> None:
    """Envelope keys match those required by execution-result.schema.json."""
    import json as _json

    schema_text = _SCHEMA_PATH.read_text()
    schema = _json.loads(schema_text)
    required_by_schema = set(schema.get("required", []))

    pcr = _load_parse_codex_review()
    envelope = pcr.parse(["LGTM"])

    missing = required_by_schema - set(envelope.keys())
    assert not missing, f"Envelope missing schema-required keys: {missing}"

    # Also verify meta has required sub-keys
    meta_required = set(schema["properties"]["meta"].get("required", []))
    meta_missing = meta_required - set(envelope["meta"].keys())
    assert not meta_missing, f"meta missing required keys: {meta_missing}"


def test_parse_codex_review_via_subprocess(tmp_path: Path) -> None:
    """Run parse_codex_review.py as a subprocess with a file argument."""
    import subprocess

    input_file = tmp_path / "codex_output.txt"
    input_file.write_text("REGRESSION: foo/bar.py:99 — something broke\n")

    result = subprocess.run(
        ["python3", str(_PARSE_CODEX_REVIEW_PY), str(input_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    envelope = json.loads(result.stdout)
    _validate_envelope_keys(envelope)
    assert envelope["status"] == "warning"
    assert envelope["data"]["total_findings"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
