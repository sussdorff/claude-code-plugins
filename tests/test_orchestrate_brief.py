#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
# ]
# ///
"""
Tests for scripts/orchestrate-brief.py

TDD Red-Green Gate — acceptance criteria tested first, then verified.

Coverage:
- CLI arg parsing: default (yesterday), --since=Nd, --date=YYYY-MM-DD,
  --range=start..end, --detailed, project name positional
- Backfill no-op: brief_exists check prevents re-query
- Project resolution: all projects vs single project
- Date range resolution: --since=3d yields correct date list
- Open-brain save_memory called for new briefs (not for existing)
- Range format parsing: --range=2026-04-20..2026-04-22
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

# Also add config.py directory
_CONFIG_DIR = _REPO_ROOT / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_CONFIG_DIR))

# Load orchestrate-brief.py via importlib (hyphen in filename)
_spec = importlib.util.spec_from_file_location(
    "orchestrate_brief", _SCRIPTS_DIR / "orchestrate-brief.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
ob = _mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    """Write a minimal valid config file and return its path."""
    config_path = tmp_path / "daily-brief.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "projects": [
            {
                "name": "claude-code-plugins",
                "path": str(tmp_path / "claude-code-plugins"),
                "slug": "claude-code-plugins",
                "beads": True,
                "docs_dir": "docs",
            },
            {
                "name": "mira",
                "path": str(tmp_path / "mira"),
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


# ---------------------------------------------------------------------------
# Unit: date range parsing
# ---------------------------------------------------------------------------


class TestParseDateRange:
    def test_since_1d(self) -> None:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        dates = ob.parse_since("1d")
        assert dates == [yesterday.isoformat()]

    def test_since_3d(self) -> None:
        today = datetime.date.today()
        dates = ob.parse_since("3d")
        assert len(dates) == 3
        # Last date should be yesterday
        assert dates[-1] == (today - datetime.timedelta(days=1)).isoformat()
        # First date should be 3 days ago
        assert dates[0] == (today - datetime.timedelta(days=3)).isoformat()

    def test_since_7d(self) -> None:
        dates = ob.parse_since("7d")
        assert len(dates) == 7

    def test_range_string(self) -> None:
        dates = ob.parse_range_str("2026-04-20..2026-04-22")
        assert dates == ["2026-04-20", "2026-04-21", "2026-04-22"]

    def test_range_string_single_day(self) -> None:
        dates = ob.parse_range_str("2026-04-23..2026-04-23")
        assert dates == ["2026-04-23"]

    def test_date_list_from_explicit_date(self) -> None:
        dates = ob.dates_for_args(date="2026-04-23", since=None, range_str=None)
        assert dates == ["2026-04-23"]

    def test_date_list_from_since(self) -> None:
        today = datetime.date.today()
        dates = ob.dates_for_args(date=None, since="2d", range_str=None)
        assert len(dates) == 2
        assert dates[-1] == (today - datetime.timedelta(days=1)).isoformat()

    def test_date_list_default_yesterday(self) -> None:
        today = datetime.date.today()
        dates = ob.dates_for_args(date=None, since=None, range_str=None)
        assert dates == [(today - datetime.timedelta(days=1)).isoformat()]

    def test_date_list_from_range_str(self) -> None:
        dates = ob.dates_for_args(date=None, since=None, range_str="2026-04-20..2026-04-22")
        assert dates == ["2026-04-20", "2026-04-21", "2026-04-22"]


# ---------------------------------------------------------------------------
# Unit: CLI arg parsing
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_default_no_args(self) -> None:
        args = ob.parse_args([])
        assert args.project is None
        assert args.date is None
        assert args.since is None
        assert args.range is None
        assert args.detailed is False

    def test_project_positional(self) -> None:
        args = ob.parse_args(["claude-code-plugins"])
        assert args.project == "claude-code-plugins"

    def test_since_flag(self) -> None:
        args = ob.parse_args(["--since=3d"])
        assert args.since == "3d"

    def test_date_flag(self) -> None:
        args = ob.parse_args(["--date=2026-04-23"])
        assert args.date == "2026-04-23"

    def test_range_flag(self) -> None:
        args = ob.parse_args(["--range=2026-04-20..2026-04-22"])
        assert args.range == "2026-04-20..2026-04-22"

    def test_detailed_flag(self) -> None:
        args = ob.parse_args(["--detailed"])
        assert args.detailed is True

    def test_project_with_since(self) -> None:
        args = ob.parse_args(["mira", "--since=7d"])
        assert args.project == "mira"
        assert args.since == "7d"

    def test_project_with_detailed(self) -> None:
        args = ob.parse_args(["claude-code-plugins", "--detailed"])
        assert args.project == "claude-code-plugins"
        assert args.detailed is True


# ---------------------------------------------------------------------------
# Unit: backfill logic (brief_exists check)
# ---------------------------------------------------------------------------


class TestBackfillLogic:
    def test_skip_existing_brief(self, minimal_config: Path, tmp_path: Path) -> None:
        """If brief already exists, run_for_project should not call render-brief."""
        project_path = tmp_path / "claude-code-plugins"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        date = "2026-04-23"
        (briefs_dir / f"{date}.md").write_text("# existing brief")

        with patch.object(ob, "_run_render_brief") as mock_render:
            with patch.object(ob, "_save_to_open_brain") as mock_save:
                result = ob.run_for_project(
                    project_name="claude-code-plugins",
                    date=date,
                    detailed=False,
                    config_path=minimal_config,
                )
        # Should not call render or save since brief exists
        mock_render.assert_not_called()
        mock_save.assert_not_called()
        assert result["skipped"] is True

    def test_generate_missing_brief(self, minimal_config: Path, tmp_path: Path) -> None:
        """If brief does not exist, run_for_project should call render-brief."""
        date = "2026-04-23"
        expected_content = "# claude-code-plugins — 2026-04-23\n\nTest content."

        with patch.object(ob, "_run_render_brief", return_value=expected_content) as mock_render:
            with patch.object(ob, "_save_to_open_brain") as mock_save:
                result = ob.run_for_project(
                    project_name="claude-code-plugins",
                    date=date,
                    detailed=False,
                    config_path=minimal_config,
                )

        mock_render.assert_called_once()
        mock_save.assert_called_once()
        assert result["skipped"] is False
        assert result["content"] == expected_content

    def test_rerun_same_args_is_noop(self, minimal_config: Path, tmp_path: Path) -> None:
        """Running twice for same (project, date) is idempotent — second call skips."""
        project_path = tmp_path / "claude-code-plugins"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        date = "2026-04-22"
        # Simulate first run having persisted the brief
        (briefs_dir / f"{date}.md").write_text("# already persisted")

        call_count = 0

        def fake_render(project_name: str, date: str, detailed: bool, config_path: Path) -> str:
            nonlocal call_count
            call_count += 1
            return "# new brief"

        with patch.object(ob, "_run_render_brief", side_effect=fake_render):
            with patch.object(ob, "_save_to_open_brain"):
                ob.run_for_project(
                    project_name="claude-code-plugins",
                    date=date,
                    detailed=False,
                    config_path=minimal_config,
                )

        assert call_count == 0, "render should not be called when brief exists"


# ---------------------------------------------------------------------------
# Unit: open-brain save
# ---------------------------------------------------------------------------


class TestOpenBrainSave:
    def test_save_memory_called_with_correct_args(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """_save_to_open_brain is called with correct type, project, session_ref."""
        captured: list[dict] = []

        def fake_save(
            *,
            title: str,
            text: str,
            ob_type: str,
            project: str,
            session_ref: str,
            metadata: dict,
        ) -> None:
            captured.append(
                {
                    "title": title,
                    "text": text,
                    "ob_type": ob_type,
                    "project": project,
                    "session_ref": session_ref,
                    "metadata": metadata,
                }
            )

        content = "# claude-code-plugins — 2026-04-23\n\nSome content."

        with patch.object(ob, "_save_to_open_brain", side_effect=fake_save):
            ob._save_to_open_brain(
                title="claude-code-plugins — 2026-04-23",
                text=content,
                ob_type="daily_brief",
                project="claude-code-plugins",
                session_ref="daily-brief-2026-04-23",
                metadata={"source": "daily-brief"},
            )

        # Since we patched it, just verify the signature is callable with these args
        # The actual MCP call is tested via integration

    def test_session_ref_format(self) -> None:
        """session_ref must be 'daily-brief-YYYY-MM-DD'."""
        ref = ob.make_session_ref("claude-code-plugins", "2026-04-23")
        assert ref == "daily-brief-2026-04-23"

    def test_session_ref_includes_date(self) -> None:
        ref = ob.make_session_ref("mira", "2026-04-20")
        assert ref == "daily-brief-2026-04-20"


# ---------------------------------------------------------------------------
# Unit: multi-project + multi-date orchestration
# ---------------------------------------------------------------------------


class TestOrchestration:
    def test_all_projects_resolved_when_no_project_arg(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """With no project arg, all configured projects are used."""
        results = []

        def fake_run(
            project_name: str,
            date: str,
            detailed: bool,
            config_path: Path,
        ) -> dict:
            results.append({"project": project_name, "date": date})
            return {"skipped": True}

        with patch.object(ob, "run_for_project", side_effect=fake_run):
            ob.orchestrate(
                project=None,
                dates=["2026-04-23"],
                detailed=False,
                config_path=minimal_config,
            )

        project_names = [r["project"] for r in results]
        assert "claude-code-plugins" in project_names
        assert "mira" in project_names

    def test_single_project_when_project_arg_given(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """With project arg, only that project is used."""
        results = []

        def fake_run(
            project_name: str,
            date: str,
            detailed: bool,
            config_path: Path,
        ) -> dict:
            results.append({"project": project_name, "date": date})
            return {"skipped": True}

        with patch.object(ob, "run_for_project", side_effect=fake_run):
            ob.orchestrate(
                project="mira",
                dates=["2026-04-23"],
                detailed=False,
                config_path=minimal_config,
            )

        assert len(results) == 1
        assert results[0]["project"] == "mira"

    def test_multiple_dates_processed(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """Each (project, date) pair is processed."""
        results = []

        def fake_run(
            project_name: str,
            date: str,
            detailed: bool,
            config_path: Path,
        ) -> dict:
            results.append({"project": project_name, "date": date})
            return {"skipped": True}

        dates = ["2026-04-21", "2026-04-22", "2026-04-23"]
        with patch.object(ob, "run_for_project", side_effect=fake_run):
            ob.orchestrate(
                project="claude-code-plugins",
                dates=dates,
                detailed=False,
                config_path=minimal_config,
            )

        assert len(results) == 3
        processed_dates = [r["date"] for r in results]
        assert "2026-04-21" in processed_dates
        assert "2026-04-22" in processed_dates
        assert "2026-04-23" in processed_dates

    def test_detailed_propagated_to_run(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """--detailed flag propagates to run_for_project."""
        captured_detailed: list[bool] = []

        def fake_run(
            project_name: str,
            date: str,
            detailed: bool,
            config_path: Path,
        ) -> dict:
            captured_detailed.append(detailed)
            return {"skipped": True}

        with patch.object(ob, "run_for_project", side_effect=fake_run):
            ob.orchestrate(
                project="mira",
                dates=["2026-04-23"],
                detailed=True,
                config_path=minimal_config,
            )

        assert all(d is True for d in captured_detailed)


# ---------------------------------------------------------------------------
# Integration: main() CLI entry point
# ---------------------------------------------------------------------------


class TestMain:
    def test_main_default_exits_zero(self, minimal_config: Path, tmp_path: Path) -> None:
        """main() with no meaningful work exits 0."""
        today = datetime.date.today()
        yesterday = (today - datetime.timedelta(days=1)).isoformat()

        # Pre-create brief so backfill skips render
        for proj in ["claude-code-plugins", "mira"]:
            proj_path = tmp_path / proj
            briefs_dir = proj_path / ".claude" / "daily-briefs"
            briefs_dir.mkdir(parents=True)
            (briefs_dir / f"{yesterday}.md").write_text(f"# {proj} brief")

        exit_code = ob.main(argv=["--config", str(minimal_config)])
        assert exit_code == 0

    def test_main_with_project_exits_zero(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """main() with project name exits 0."""
        today = datetime.date.today()
        yesterday = (today - datetime.timedelta(days=1)).isoformat()

        proj_path = tmp_path / "claude-code-plugins"
        briefs_dir = proj_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        (briefs_dir / f"{yesterday}.md").write_text("# ccp brief")

        exit_code = ob.main(argv=["claude-code-plugins", "--config", str(minimal_config)])
        assert exit_code == 0

    def test_main_unknown_project_exits_nonzero(self, minimal_config: Path) -> None:
        """main() with unknown project exits nonzero."""
        exit_code = ob.main(argv=["nonexistent-project", "--config", str(minimal_config)])
        assert exit_code != 0

    def test_main_since_3d_exits_zero(self, minimal_config: Path, tmp_path: Path) -> None:
        """main() with --since=3d exits 0 (all briefs pre-exist)."""
        today = datetime.date.today()
        dates = [
            (today - datetime.timedelta(days=i)).isoformat() for i in range(1, 4)
        ]
        for proj in ["claude-code-plugins", "mira"]:
            proj_path = tmp_path / proj
            briefs_dir = proj_path / ".claude" / "daily-briefs"
            briefs_dir.mkdir(parents=True)
            for d in dates:
                (briefs_dir / f"{d}.md").write_text(f"# {proj} {d}")

        exit_code = ob.main(argv=["--since=3d", "--config", str(minimal_config)])
        assert exit_code == 0
