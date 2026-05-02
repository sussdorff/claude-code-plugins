from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PREPARE_SCRIPT = (
    REPO_ROOT / "core" / "agents" / "session-close-handlers" / "phase-b-prepare.sh"
)


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


def _write_script(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _setup_repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    repo = tmp_path / "repo"

    _run(["git", "init", "--bare", str(remote)])
    _run(["git", "init", "-b", "main", str(repo)])
    _run(["git", "-C", str(repo), "config", "user.name", "Test User"])
    _run(["git", "-C", str(repo), "config", "user.email", "test@example.com"])

    (repo / "README.md").write_text("hello\n")
    _run(["git", "-C", str(repo), "add", "README.md"])
    _run(["git", "-C", str(repo), "commit", "-m", "initial commit"])
    _run(["git", "-C", str(repo), "remote", "add", "origin", str(remote)])
    _run(["git", "-C", str(repo), "push", "-u", "origin", "main"])

    return repo


def _setup_handlers(tmp_path: Path) -> Path:
    handlers_dir = tmp_path / "handlers"
    handlers_dir.mkdir()
    prepare_script = handlers_dir / "phase-b-prepare.sh"
    shutil.copy2(SOURCE_PREPARE_SCRIPT, prepare_script)
    prepare_script.chmod(prepare_script.stat().st_mode | stat.S_IXUSR)

    _write_script(
        handlers_dir / "merge-from-main.sh",
        """#!/usr/bin/env bash
set -euo pipefail
echo "MERGE_FROM_MAIN_STATUS=success"
""",
    )
    _write_script(
        handlers_dir / "session-close-lock.sh",
        """#!/usr/bin/env bash
set -euo pipefail
exit 0
""",
    )
    _write_script(
        handlers_dir / "docs-check.sh",
        """#!/usr/bin/env bash
set -euo pipefail
exit 0
""",
    )

    return prepare_script


def _run_prepare(prepare_script: Path, repo: Path) -> dict:
    result = subprocess.run(
        ["bash", str(prepare_script), "--skip-audit", "--skip-simplify"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _execution_result(status: str, summary: str, errors: list[dict] | None = None) -> str:
    return json.dumps(
        {
            "status": status,
            "summary": summary,
            "data": {},
            "errors": errors or [],
            "next_steps": [],
            "open_items": [],
            "meta": {"contract_version": "1.0", "producer": "test-hook"},
        }
    )


def test_phase_b_prepare_skips_missing_local_verify_hook(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    prepare_script = _setup_handlers(tmp_path)

    payload = _run_prepare(prepare_script, repo)

    assert payload["local_verify"]["status"] == "skipped"
    assert payload["local_verify"]["summary"] == "no scripts/session-close-verify.sh hook"


def test_phase_b_prepare_runs_structured_local_verify_hook(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    prepare_script = _setup_handlers(tmp_path)
    hook_result = _execution_result("ok", "local gates passed")
    _write_script(
        repo / "scripts" / "session-close-verify.sh",
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "running local gate"
printf 'generated\\n' > generated-by-hook.txt
printf '%s\\n' '{hook_result}'
""",
    )

    payload = _run_prepare(prepare_script, repo)

    assert payload["local_verify"]["status"] == "ok"
    assert payload["local_verify"]["summary"] == "local gates passed"
    assert payload["local_verify"]["errors"] == []
    assert "generated-by-hook.txt" in payload["git_state"]["untracked"]


def test_phase_b_prepare_reports_structured_local_verify_error(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    prepare_script = _setup_handlers(tmp_path)
    hook_result = _execution_result(
        "error",
        "local gates failed",
        [{"code": "unit_failed", "message": "unit tests failed"}],
    )
    _write_script(
        repo / "scripts" / "session-close-verify.sh",
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' '{hook_result}'
""",
    )

    payload = _run_prepare(prepare_script, repo)

    assert payload["local_verify"]["status"] == "error"
    assert payload["local_verify"]["summary"] == "local gates failed"
    assert payload["local_verify"]["errors"] == ["unit tests failed"]


def test_phase_b_prepare_treats_legacy_nonzero_hook_as_error(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    prepare_script = _setup_handlers(tmp_path)
    _write_script(
        repo / "scripts" / "session-close-verify.sh",
        """#!/usr/bin/env bash
set -euo pipefail
echo "legacy failure"
exit 7
""",
    )

    payload = _run_prepare(prepare_script, repo)

    assert payload["local_verify"]["status"] == "error"
    assert payload["local_verify"]["summary"] == (
        "local verification hook failed without structured JSON"
    )
    assert payload["local_verify"]["exit_code"] == 7
    assert payload["local_verify"]["errors"] == [
        "scripts/session-close-verify.sh exited 7"
    ]
