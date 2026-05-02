import importlib.util
import os
import stat
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_EXEC = REPO_ROOT / "beads-workflow" / "scripts" / "codex-exec.py"


def _make_model_not_supported_codex(bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    mock = bin_dir / "codex"
    mock.write_text(
        """#!/usr/bin/env bash
printf 'Error: model_not_supported HTTP 400: o4-mini is not configured\\n' >&2
sleep 60
"""
    )
    mock.chmod(mock.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _load_codex_exec():
    spec = importlib.util.spec_from_file_location("codex_exec", CODEX_EXEC)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_fast_fail_detector_matches_http_400_and_model_not_supported() -> None:
    codex_exec = _load_codex_exec()

    assert codex_exec._codex_fast_fail_reason("Error: HTTP 400") is not None
    assert codex_exec._codex_fast_fail_reason("model_not_supported") is not None


def test_codex_exec_fast_fails_on_http_400_model_not_supported(tmp_path: Path) -> None:
    """A model-unsupported 400 on stderr must not wait for CODEX_EXEC_TIMEOUT."""
    mock_dir = _make_model_not_supported_codex(tmp_path / "mock_bin")
    env = os.environ.copy()
    env["PATH"] = f"{mock_dir}:{env.get('PATH', '')}"
    env["CODEX_EXEC_TIMEOUT"] = "30"
    env.pop("RUN_ID", None)

    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(CODEX_EXEC), "review prompt"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    elapsed = time.monotonic() - start

    assert result.returncode != 0
    assert result.returncode != 124
    assert elapsed < 5, f"fast-fail took {elapsed:.1f}s"
    assert "model_not_supported" in result.stderr
    assert "non-retryable Codex error" in result.stderr
