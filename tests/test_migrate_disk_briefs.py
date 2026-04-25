#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
# ]
# ///
"""
Tests for scripts/migrate-disk-briefs-to-open-brain.py

Coverage:
- Dry-run: reports briefs found without writing
- Apply: writes briefs to open-brain
- Idempotency: already-in-OB briefs are not duplicated
- Error handling: failed writes reported in result envelope
- Empty project: no crash on empty briefs dir
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

_CONFIG_DIR = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_CONFIG_DIR))

# Load migrate-disk-briefs-to-open-brain.py via importlib (hyphen in filename)
_spec = importlib.util.spec_from_file_location(
    "migrate_disk_briefs",
    _SCRIPTS_DIR / "migrate-disk-briefs-to-open-brain.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
mig = _mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    """Write a minimal valid config file and return its path."""
    config_path = tmp_path / "daily-brief.yml"

    project_path_ccp = tmp_path / "claude-code-plugins"
    project_path_mira = tmp_path / "mira"

    data = {
        "projects": [
            {
                "name": "claude-code-plugins",
                "path": str(project_path_ccp),
                "slug": "claude-code-plugins",
                "beads": True,
                "docs_dir": "docs",
            },
            {
                "name": "mira",
                "path": str(project_path_mira),
                "slug": "mira",
                "beads": True,
                "docs_dir": "docs",
            },
        ],
        "defaults": {
            "since": "yesterday",
            "format": "markdown",
            "detailed": False,
            "language": "de",
            "timezone": "Europe/Berlin",
        },
    }
    with config_path.open("w") as fh:
        yaml.dump(data, fh)
    return config_path


@pytest.fixture()
def config_with_briefs(tmp_path: Path) -> tuple[Path, Path]:
    """Config + pre-created disk briefs for claude-code-plugins.

    Returns:
        (config_path, project_path)
    """
    config_path = tmp_path / "daily-brief.yml"
    project_path = tmp_path / "claude-code-plugins"
    briefs_dir = project_path / ".claude" / "daily-briefs"
    briefs_dir.mkdir(parents=True)

    # Create two brief files
    (briefs_dir / "2026-04-23.md").write_text("# CCP — 2026-04-23\n\nContent A.")
    (briefs_dir / "2026-04-24.md").write_text("# CCP — 2026-04-24\n\nContent B.")

    data = {
        "projects": [
            {
                "name": "claude-code-plugins",
                "path": str(project_path),
                "slug": "claude-code-plugins",
                "beads": True,
                "docs_dir": "docs",
            },
        ],
        "defaults": {"since": "yesterday", "format": "markdown"},
    }
    with config_path.open("w") as fh:
        yaml.dump(data, fh)
    return config_path, project_path


# ---------------------------------------------------------------------------
# Unit: dry-run (default mode)
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_reports_briefs_without_writing(
        self, config_with_briefs: tuple[Path, Path]
    ) -> None:
        """Dry-run reports what would be migrated but calls _save_to_open_brain 0 times."""
        config_path, _ = config_with_briefs

        with patch.object(mig._ob_mod, "_save_to_open_brain") as mock_save:
            result_code = mig.main(argv=["--config", str(config_path)])

        mock_save.assert_not_called()
        assert result_code == 0

    def test_dry_run_stdout_is_valid_json(
        self,
        config_with_briefs: tuple[Path, Path],
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Dry-run emits valid execution-result JSON to stdout."""
        config_path, _ = config_with_briefs

        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(config_path)])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["data"]["dry_run"] is True
        assert data["data"]["total"] == 2

    def test_dry_run_lists_would_migrate(
        self,
        config_with_briefs: tuple[Path, Path],
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Dry-run lists all briefs that would be migrated."""
        config_path, _ = config_with_briefs

        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(config_path)])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        would_migrate = data["data"].get("would_migrate", [])
        dates = [item["date"] for item in would_migrate]
        assert "2026-04-23" in dates
        assert "2026-04-24" in dates

    def test_dry_run_empty_dir_reports_zero(
        self, minimal_config: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Dry-run on a project with no brief files reports total=0."""
        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(minimal_config)])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["data"]["total"] == 0


# ---------------------------------------------------------------------------
# Unit: apply mode
# ---------------------------------------------------------------------------


class TestApplyMode:
    def test_apply_calls_save_for_each_brief(
        self, config_with_briefs: tuple[Path, Path]
    ) -> None:
        """--apply calls _save_to_open_brain once per brief."""
        config_path, _ = config_with_briefs
        save_calls: list[dict] = []

        def fake_save(**kwargs: object) -> None:
            save_calls.append(dict(kwargs))

        with patch.object(mig._ob_mod, "_save_to_open_brain", side_effect=fake_save):
            result_code = mig.main(argv=["--config", str(config_path), "--apply"])

        assert result_code == 0
        assert len(save_calls) == 2

    def test_apply_stdout_reports_migrated(
        self,
        config_with_briefs: tuple[Path, Path],
        capsys: pytest.CaptureFixture,
    ) -> None:
        """--apply emits JSON with migrated list."""
        config_path, _ = config_with_briefs

        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(config_path), "--apply"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["data"]["dry_run"] is False
        assert len(data["data"]["migrated"]) == 2
        assert len(data["data"]["failed"]) == 0

    def test_apply_session_ref_includes_project_and_date(
        self, config_with_briefs: tuple[Path, Path]
    ) -> None:
        """Each OB write uses session_ref=daily-brief-{slug}-{date}."""
        config_path, _ = config_with_briefs
        captured_refs: list[str] = []

        def fake_save(**kwargs: object) -> None:
            captured_refs.append(kwargs.get("session_ref", ""))  # type: ignore[arg-type]

        with patch.object(mig._ob_mod, "_save_to_open_brain", side_effect=fake_save):
            mig.main(argv=["--config", str(config_path), "--apply"])

        assert any("claude-code-plugins" in ref for ref in captured_refs), (
            f"session_ref must include project slug; got: {captured_refs}"
        )
        assert any("2026-04-23" in ref for ref in captured_refs)
        assert any("2026-04-24" in ref for ref in captured_refs)

    def test_apply_failed_write_reported_in_result(
        self,
        config_with_briefs: tuple[Path, Path],
        capsys: pytest.CaptureFixture,
    ) -> None:
        """When _save_to_open_brain raises, the failure is reported in the result (not crash)."""
        config_path, _ = config_with_briefs
        call_count = [0]

        def fake_save(**kwargs: object) -> None:
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("OB unreachable")

        with patch.object(mig._ob_mod, "_save_to_open_brain", side_effect=fake_save):
            result_code = mig.main(argv=["--config", str(config_path), "--apply"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        # One migrated, one failed
        assert data["data"]["failed"], "Failed writes must be in result envelope"
        assert len(data["data"]["failed"]) == 1
        assert data["status"] in ("warning", "error")

    def test_apply_skips_non_date_filenames(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Non-date filenames like README.md are skipped during discovery."""
        config_path = tmp_path / "daily-brief.yml"
        project_path = tmp_path / "proj"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        (briefs_dir / "2026-04-25.md").write_text("# Valid brief")
        (briefs_dir / "README.md").write_text("# Not a brief")
        (briefs_dir / "notes.txt").write_text("some notes")

        data = {
            "projects": [
                {
                    "name": "proj",
                    "path": str(project_path),
                    "slug": "proj",
                    "beads": False,
                    "docs_dir": "docs",
                }
            ],
            "defaults": {"since": "yesterday", "format": "markdown"},
        }
        with config_path.open("w") as fh:
            yaml.dump(data, fh)

        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(config_path)])

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        # Only 1 valid brief found (2026-04-25.md)
        assert result["data"]["total"] == 1


# ---------------------------------------------------------------------------
# Unit: project filter
# ---------------------------------------------------------------------------


class TestProjectFilter:
    def test_project_filter_limits_to_single_project(
        self,
        minimal_config: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """--project filters discovery to the specified project only."""
        # Create briefs for both projects
        for proj in ["claude-code-plugins", "mira"]:
            briefs_dir = tmp_path / proj / ".claude" / "daily-briefs"
            briefs_dir.mkdir(parents=True)
            (briefs_dir / "2026-04-25.md").write_text(f"# {proj} brief")

        with patch.object(mig._ob_mod, "_save_to_open_brain"):
            mig.main(argv=["--config", str(minimal_config), "--project", "mira"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        # Only mira's brief found
        assert data["data"]["total"] == 1
        if "would_migrate" in data["data"]:
            for item in data["data"]["would_migrate"]:
                assert item["project"] == "mira"
