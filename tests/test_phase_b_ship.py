from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHIP_SCRIPT = REPO_ROOT / "core" / "agents" / "session-close-handlers" / "phase-b-ship.sh"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)


def _write_script(path: Path, body: str) -> None:
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


def _setup_handlers(tmp_path: Path) -> tuple[Path, Path]:
    handlers_dir = tmp_path / "handlers"
    handlers_dir.mkdir()
    ship_script = handlers_dir / "phase-b-ship.sh"
    shutil.copy2(SOURCE_SHIP_SCRIPT, ship_script)
    ship_script.chmod(ship_script.stat().st_mode | stat.S_IXUSR)

    call_log = tmp_path / "helper-calls.log"
    helper_template = """#!/usr/bin/env bash
set -euo pipefail
printf '%s:%s\n' "$(basename "$0")" "$*" >> "$CALL_LOG"

case "$(basename "$0")" in
  merge-from-main.sh)
    echo "MERGE_FROM_MAIN_STATUS=success"
    ;;
  merge-feature.sh)
    echo "MERGE_FEATURE_STATUS=success"
    ;;
  version.sh)
    echo "TAG_PENDING="
    echo "TAG_MESSAGE="
    ;;
  pipeline-watch.sh)
    echo "PIPELINE_STATUS=success"
    echo "PIPELINE_RUN_URL="
    ;;
  sync-plugin-cache.sh)
    echo "skipping no plugin"
    ;;
esac
"""

    for helper_name in (
        "merge-from-main.sh",
        "merge-feature.sh",
        "version.sh",
        "pipeline-watch.sh",
        "sync-plugin-cache.sh",
    ):
        _write_script(handlers_dir / helper_name, helper_template)

    return ship_script, call_log


def test_regression_phase_b_ship_does_not_forward_dry_run_by_default(tmp_path: Path) -> None:
    """Guard CCP-33b: DRY_RUN=false must not expand to a helper --dry-run flag."""
    repo = _setup_repo(tmp_path)
    ship_script, call_log = _setup_handlers(tmp_path)

    env = os.environ.copy()
    env["CALL_LOG"] = str(call_log)

    result = subprocess.run(
        ["bash", str(ship_script)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["second_merge"]["status"] == "ok"
    assert payload["version"]["status"] == "ok"
    assert payload["push"]["status"] == "ok"
    assert payload["pipeline"]["status"] == "success"

    calls = call_log.read_text().splitlines()
    relevant_calls = [
        call for call in calls
        if call.startswith(("merge-from-main.sh:", "version.sh:", "pipeline-watch.sh:"))
    ]
    assert relevant_calls, "expected helper scripts to be invoked"
    assert all("--dry-run" not in call for call in relevant_calls), relevant_calls
