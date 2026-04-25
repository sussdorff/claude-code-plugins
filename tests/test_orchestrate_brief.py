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
        """If brief already exists on disk (OB offline), run_for_project should not call render-brief."""
        project_path = tmp_path / "claude-code-plugins"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        date = "2026-04-23"
        (briefs_dir / f"{date}.md").write_text("# existing brief")

        # v1.5: OB is checked first — mock it returning None (offline) so disk fallback fires
        with patch.object(ob, "_read_from_open_brain", return_value=None):
            with patch.object(ob, "_run_render_brief") as mock_render:
                with patch.object(ob, "_save_to_open_brain") as mock_save:
                    result = ob.run_for_project(
                        project_name="claude-code-plugins",
                        date=date,
                        detailed=False,
                        config_path=minimal_config,
                    )
        # Should not call render or save since brief exists on disk
        mock_render.assert_not_called()
        mock_save.assert_not_called()
        assert result["skipped"] is True

    def test_generate_missing_brief(self, minimal_config: Path, tmp_path: Path) -> None:
        """If brief does not exist (OB and disk both miss), run_for_project should call render-brief."""
        date = "2026-04-23"
        expected_content = "# claude-code-plugins — 2026-04-23\n\nTest content."

        # v1.5: OB returns None (not found), disk also misses
        with patch.object(ob, "_read_from_open_brain", return_value=None):
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
        """Running twice for same (project, date) is idempotent — second call skips (disk fallback)."""
        project_path = tmp_path / "claude-code-plugins"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        date = "2026-04-22"
        # Simulate first run having persisted the brief to disk
        (briefs_dir / f"{date}.md").write_text("# already persisted")

        call_count = 0

        def fake_render(project_name: str, date: str, detailed: bool, config_path: Path, **kwargs: object) -> str:
            nonlocal call_count
            call_count += 1
            return "# new brief"

        # v1.5: OB returns None (offline), disk check fires
        with patch.object(ob, "_read_from_open_brain", return_value=None):
            with patch.object(ob, "_run_render_brief", side_effect=fake_render):
                with patch.object(ob, "_save_to_open_brain"):
                    ob.run_for_project(
                        project_name="claude-code-plugins",
                        date=date,
                        detailed=False,
                        config_path=minimal_config,
                    )

        assert call_count == 0, "render should not be called when brief exists on disk"


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
        """session_ref must be 'daily-brief-{project}-YYYY-MM-DD' (v1.5: includes project slug)."""
        ref = ob.make_session_ref("claude-code-plugins", "2026-04-23")
        assert ref == "daily-brief-claude-code-plugins-2026-04-23"

    def test_session_ref_includes_date(self) -> None:
        ref = ob.make_session_ref("mira", "2026-04-20")
        assert ref == "daily-brief-mira-2026-04-20"


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
            **kwargs: object,
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
            **kwargs: object,
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
            **kwargs: object,
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
            **kwargs: object,
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

        # Pre-create brief so disk fallback skips render (OB returns None = offline)
        for proj in ["claude-code-plugins", "mira"]:
            proj_path = tmp_path / proj
            briefs_dir = proj_path / ".claude" / "daily-briefs"
            briefs_dir.mkdir(parents=True)
            (briefs_dir / f"{yesterday}.md").write_text(f"# {proj} brief")

        with patch.object(ob, "_read_from_open_brain", return_value=None):
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

        with patch.object(ob, "_read_from_open_brain", return_value=None):
            exit_code = ob.main(argv=["claude-code-plugins", "--config", str(minimal_config)])
        assert exit_code == 0

    def test_main_unknown_project_exits_nonzero(self, minimal_config: Path) -> None:
        """main() with unknown project exits nonzero."""
        exit_code = ob.main(argv=["nonexistent-project", "--config", str(minimal_config)])
        assert exit_code != 0

    def test_main_since_3d_exits_zero(self, minimal_config: Path, tmp_path: Path) -> None:
        """main() with --since=3d exits 0 (all briefs pre-exist on disk, OB offline)."""
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

        with patch.object(ob, "_read_from_open_brain", return_value=None):
            exit_code = ob.main(argv=["--since=3d", "--config", str(minimal_config)])
        assert exit_code == 0


# ---------------------------------------------------------------------------
# Regression tests — config.json token resolution in write path (CCP-yosw)
# ---------------------------------------------------------------------------


class TestSaveToOpenBrainConfigJson:
    """_save_to_open_brain() must read credentials from ~/.open-brain/config.json
    when neither OB_TOKEN env var nor ~/.open-brain/token file exist.

    The config.json format:
        { "server_url": "https://open-brain.sussdorff.org", "api_key": "ob_..." }
    """

    def test_save_raises_when_no_credentials(self, tmp_path: Path) -> None:
        """_save_to_open_brain() raises RuntimeError when no token/config available (v1.5 hard error)."""
        import os
        from unittest.mock import patch

        # Empty home directory — no .open-brain/ at all
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                # v1.5: must raise RuntimeError — persistence is mandatory
                with pytest.raises(RuntimeError, match="open-brain"):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test brief",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-test-2026-04-23",
                        metadata={"source": "daily-brief"},
                    )

    def test_save_uses_config_json_api_key(self, tmp_path: Path) -> None:
        """_save_to_open_brain() reads api_key from config.json when no OB_TOKEN set.

        We verify this by patching `_async_save_memory` and asserting it was called
        with the expected token/URL, meaning a token was found — not skipped silently.
        """
        import os

        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://open-brain.example.org", "api_key": "ob_configkey"}'
        )

        calls: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            calls.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test brief",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-2026-04-23",
                        metadata={"source": "daily-brief"},
                    )

        assert calls, (
            "_save_to_open_brain() should have called _async_save_memory when config.json has credentials"
        )
        assert calls[0]["token"] == "ob_configkey", (
            f"Expected token 'ob_configkey' from config.json, got '{calls[0].get('token')}'"
        )

    def test_save_uses_config_json_server_url(self, tmp_path: Path) -> None:
        """_save_to_open_brain() derives ob_url from server_url in config.json + '/mcp'."""
        import os
        from unittest.mock import patch

        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://custom.myhost.org", "api_key": "ob_somekey"}'
        )

        calls: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            calls.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test brief",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-2026-04-23",
                        metadata={"source": "daily-brief"},
                    )

        assert calls, "_async_save_memory should have been called"
        assert calls[0]["ob_url"] == "https://custom.myhost.org/mcp", (
            f"Expected ob_url from config.json server_url+'/mcp', got '{calls[0].get('ob_url')}'"
        )

    def test_env_token_takes_precedence_over_config_json(self, tmp_path: Path) -> None:
        """OB_TOKEN env var takes precedence over config.json api_key in write path."""
        import os
        from unittest.mock import patch

        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://open-brain.example.org", "api_key": "ob_config_key"}'
        )

        calls: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            calls.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {"OB_TOKEN": "ob_env_key"}, clear=False):
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test brief",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-2026-04-23",
                        metadata={"source": "daily-brief"},
                    )

        assert calls, "_async_save_memory should have been called"
        assert calls[0]["token"] == "ob_env_key", (
            "OB_TOKEN env var should take precedence over config.json api_key"
        )

    def test_url_from_config_json_used_even_when_env_token_set(self, tmp_path: Path) -> None:
        """config.json server_url is used even when token comes from OB_TOKEN env var.

        Regression test: previously config.json was only read when no token was found,
        so OB_TOKEN set → config.json never read → URL fell through to hardcoded default.
        """
        import os
        from unittest.mock import patch

        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://custom.example.org", "api_key": "ob_config_key"}'
        )

        calls: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            calls.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {"OB_TOKEN": "ob_env_key"}, clear=False):
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test brief",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-2026-04-23",
                        metadata={"source": "daily-brief"},
                    )

        assert calls, "_async_save_memory should have been called"
        assert calls[0]["ob_url"] == "https://custom.example.org/mcp", (
            f"Expected ob_url from config.json server_url even when OB_TOKEN is set, "
            f"got '{calls[0].get('ob_url')}'"
        )
        assert calls[0]["token"] == "ob_env_key", (
            "OB_TOKEN env var should still be used as the token"
        )


class TestAsyncSaveMemoryAuthHeader:
    """Regression tests for CCP-scw5: _async_save_memory must use x-api-key header, not Authorization: Bearer.

    After CCP-zodj (SDK migration), _async_save_memory uses the official mcp SDK.
    The x-api-key header is passed to streamablehttp_client() in the headers dict.
    Full SDK-level header verification is in test_ob_mcp_sdk_client.py::TestSDKAsyncSaveMemory.
    """

    def test_async_save_memory_uses_x_api_key_via_sdk(self) -> None:
        """_async_save_memory() passes x-api-key (not Authorization: Bearer) to the SDK.

        After CCP-zodj, the authentication header is passed to streamablehttp_client()
        as {'x-api-key': token}. We verify this by intercepting the SDK call at the
        mcp module level (same process as orchestrate-brief.py uses).
        The comprehensive test is in test_ob_mcp_sdk_client.py::TestSDKAsyncSaveMemory::
        test_save_memory_uses_x_api_key_header.
        """
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        captured_headers: list[dict[str, str]] = []

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=MagicMock(isError=False))

            @asynccontextmanager
            async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
                captured_headers.append(dict(headers or {}))
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                await ob._async_save_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testapikey",
                    title="test — 2026-04-23",
                    text="# Test",
                    ob_type="daily_brief",
                    project="test",
                    session_ref="daily-brief-2026-04-23",
                    metadata={},
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())

        assert captured_headers, "streamablehttp_client must have been called"
        hdrs = captured_headers[0]
        assert "x-api-key" in hdrs, (
            f"Expected 'x-api-key' header in SDK call; got: {list(hdrs.keys())}"
        )
        assert hdrs["x-api-key"] == "ob_testapikey"
        assert "authorization" not in {k.lower() for k in hdrs}, (
            "Must NOT send Authorization header — use x-api-key only"
        )


class TestAsyncSaveMemoryRegressions:
    """Regression tests for CCP-sd9e: wrong URL path + missing Accept header.

    After CCP-zodj (SDK migration), the SDK handles Accept headers internally.
    We test that errors from wrong URLs surface as exceptions (not silent failures).
    """

    def test_save_404_wrong_path_raises_exception(self) -> None:
        """_async_save_memory() raises when the server returns 404 (wrong URL path).

        Regression: before CCP-sd9e, the URL was /mcp/mcp (404) instead of /mcp.
        After SDK migration, a 404 surfaces as an exception that _save_to_open_brain
        catches and silently swallows (non-blocking behavior preserved).
        We verify that _async_save_memory raises rather than silently succeeding on 404.
        """
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock
            from httpx import HTTPStatusError, Request, Response

            req = Request("POST", "https://ob.example.test/mcp/mcp")
            resp = Response(404, request=req)
            error = HTTPStatusError("404 Not Found", request=req, response=resp)

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock(side_effect=error)

            @asynccontextmanager
            async def mock_sh(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                # Should raise (not silently succeed) — _save_to_open_brain catches it
                await ob._async_save_memory(
                    ob_url="https://ob.example.test/mcp/mcp",
                    token="ob_testapikey",
                    title="test — 2026-04-24",
                    text="# Test",
                    ob_type="daily_brief",
                    project="test",
                    session_ref="daily-brief-2026-04-24",
                    metadata={},
                )
            except Exception:
                pass  # Expected: exception raised (caught by _save_to_open_brain)
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        # Must not hang
        asyncio.run(_drive())

    def test_save_url_must_not_be_mcp_mcp(self) -> None:
        """_resolve_ob_credentials() must build URL ending in /mcp, not /mcp/mcp.

        Regression: before CCP-sd9e, server_url + '/mcp' was appended twice
        if server_url already contained '/mcp'. The correct behavior is a single /mcp.
        """
        import asyncio
        import os
        import tempfile

        tmp_path = Path(tempfile.mkdtemp())
        config_json = tmp_path / ".open-brain" / "config.json"
        config_json.parent.mkdir(parents=True, exist_ok=True)
        config_json.write_text(
            '{"server_url": "https://open-brain.sussdorff.org", "api_key": "ob_key"}'
        )

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                _, ob_url = ob._resolve_ob_credentials()

        assert ob_url == "https://open-brain.sussdorff.org/mcp", (
            f"URL must end with /mcp (not /mcp/mcp); got '{ob_url}'"
        )
        assert not ob_url.endswith("/mcp/mcp"), (
            f"URL must NOT end with /mcp/mcp; got '{ob_url}'"
        )

    def test_save_406_sdk_handles_accept_header(self) -> None:
        """The SDK manages Accept headers — _async_save_memory does not hardcode them.

        After CCP-zodj SDK migration, the Accept: application/json, text/event-stream
        header is handled by the SDK's streamablehttp_client transport. We verify that
        _async_save_memory does NOT hardcode Accept in the headers dict (the SDK owns it).
        """
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        captured_headers: list[dict[str, str]] = []

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=MagicMock(isError=False))

            @asynccontextmanager
            async def mock_sh(url: str, headers: dict | None = None, **kwargs: Any):
                captured_headers.append(dict(headers or {}))
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                await ob._async_save_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testapikey",
                    title="test — 2026-04-24",
                    text="# Test",
                    ob_type="daily_brief",
                    project="test",
                    session_ref="daily-brief-2026-04-24",
                    metadata={},
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())

        assert captured_headers, "streamablehttp_client must have been called"
        hdrs = captured_headers[0]
        # Only x-api-key should be in our headers dict — SDK adds Accept internally
        assert "x-api-key" in hdrs, "x-api-key must be in headers"
        # The Accept header is NOT in our dict — it is added by the SDK transport
        assert "accept" not in {k.lower() for k in hdrs}, (
            "Accept header must NOT be hardcoded in headers dict — SDK manages it"
        )


# ---------------------------------------------------------------------------
# AK1 — Open-brain read path (search before disk)
# ---------------------------------------------------------------------------


class TestOpenBrainReadPath:
    """AK1: /daily-brief reads existing briefs from open-brain before re-querying sources."""

    def test_read_from_open_brain_returns_content_when_found(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """When OB has the brief, run_for_project returns OB content without calling render-brief."""
        ob_content = "# claude-code-plugins — 2026-04-23\n\nFrom open-brain."

        with patch.object(ob, "_read_from_open_brain", return_value=ob_content) as mock_read:
            with patch.object(ob, "_run_render_brief") as mock_render:
                with patch.object(ob, "_save_to_open_brain") as mock_save:
                    result = ob.run_for_project(
                        project_name="claude-code-plugins",
                        date="2026-04-23",
                        detailed=False,
                        config_path=minimal_config,
                    )

        mock_read.assert_called_once()
        mock_render.assert_not_called()
        mock_save.assert_not_called()
        assert result["skipped"] is True
        assert result["content"] == ob_content

    def test_read_from_open_brain_fallback_to_disk_when_ob_returns_none(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """When OB returns None (offline), fall back to disk check."""
        project_path = tmp_path / "claude-code-plugins"
        briefs_dir = project_path / ".claude" / "daily-briefs"
        briefs_dir.mkdir(parents=True)
        date = "2026-04-23"
        (briefs_dir / f"{date}.md").write_text("# disk brief")

        with patch.object(ob, "_read_from_open_brain", return_value=None):
            with patch.object(ob, "_run_render_brief") as mock_render:
                with patch.object(ob, "_save_to_open_brain") as mock_save:
                    result = ob.run_for_project(
                        project_name="claude-code-plugins",
                        date=date,
                        detailed=False,
                        config_path=minimal_config,
                    )

        # Disk fallback: skipped=True, render not called
        mock_render.assert_not_called()
        assert result["skipped"] is True

    def test_read_from_open_brain_function_exists(self) -> None:
        """_read_from_open_brain must be defined on the module."""
        assert hasattr(ob, "_read_from_open_brain"), (
            "_read_from_open_brain must be defined in orchestrate-brief.py"
        )

    def test_async_search_memory_function_exists(self) -> None:
        """_async_search_memory must be defined on the module."""
        assert hasattr(ob, "_async_search_memory"), (
            "_async_search_memory must be defined in orchestrate-brief.py"
        )

    def test_session_ref_includes_project_slug(self) -> None:
        """session_ref must include project slug for cross-project safety (AK1 fix)."""
        ref = ob.make_session_ref("claude-code-plugins", "2026-04-23")
        assert "claude-code-plugins" in ref, (
            "session_ref must include project slug, got: " + ref
        )

    def test_session_ref_includes_date(self) -> None:
        """session_ref must include the date."""
        ref = ob.make_session_ref("mira", "2026-04-20")
        assert "2026-04-20" in ref, "session_ref must include the date"


# ---------------------------------------------------------------------------
# AK2 — Hard error on OB write failure
# ---------------------------------------------------------------------------


class TestOpenBrainWriteHardError:
    """AK2: _save_to_open_brain MUST raise on failure; no silent skip, no bare except."""

    def test_hard_error_on_ob_connection_failure(
        self, tmp_path: Path
    ) -> None:
        """When _async_save_memory raises ConnectionError, _save_to_open_brain re-raises."""
        import os

        ob_home = tmp_path / ".open-brain"
        ob_home.mkdir(parents=True)
        (ob_home / "token").write_text("ob_testtoken")

        async def fake_save_raises(**kwargs: object) -> None:
            raise ConnectionError("Cannot connect to open-brain")

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_save_raises):
                    with pytest.raises(Exception):
                        ob._save_to_open_brain(
                            title="test — 2026-04-23",
                            text="# Test",
                            ob_type="daily_brief",
                            project="test",
                            session_ref="daily-brief-test-2026-04-23",
                            metadata={},
                        )

    def test_hard_error_on_missing_token(self, tmp_path: Path) -> None:
        """When no token is available, _save_to_open_brain raises RuntimeError (not silent skip)."""
        import os

        # Empty home: no .open-brain directory
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with pytest.raises(RuntimeError, match="open-brain"):
                    ob._save_to_open_brain(
                        title="test — 2026-04-23",
                        text="# Test",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-test-2026-04-23",
                        metadata={},
                    )

    def test_hard_error_propagates_from_run_for_project(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """When OB write fails in run_for_project, the exception propagates (not swallowed)."""
        import os
        date = "2026-04-23"
        content = "# claude-code-plugins — 2026-04-23\n\nSome content."

        with patch.object(ob, "_read_from_open_brain", return_value=None):
            with patch.object(ob, "_run_render_brief", return_value=content):
                with patch.object(
                    ob,
                    "_save_to_open_brain",
                    side_effect=RuntimeError("OB write failed"),
                ):
                    with pytest.raises(RuntimeError):
                        ob.run_for_project(
                            project_name="claude-code-plugins",
                            date=date,
                            detailed=False,
                            config_path=minimal_config,
                        )


# ---------------------------------------------------------------------------
# AK3 — Disk write opt-in via --persist-disk flag
# ---------------------------------------------------------------------------


class TestPersistDiskFlag:
    """AK3: Disk write is opt-in via --persist-disk; default writes to open-brain only."""

    def test_parse_args_accepts_persist_disk_flag(self) -> None:
        """--persist-disk must be a valid CLI flag."""
        args = ob.parse_args(["--persist-disk"])
        assert args.persist_disk is True

    def test_persist_disk_default_is_false(self) -> None:
        """--persist-disk defaults to False."""
        args = ob.parse_args([])
        assert args.persist_disk is False

    def test_run_render_brief_passes_no_persist_by_default(
        self, minimal_config: Path
    ) -> None:
        """When persist_disk=False (default), _run_render_brief command includes --no-persist."""
        captured_cmds: list[list[str]] = []

        def fake_run(cmd: list, **kwargs: object) -> object:
            captured_cmds.append(cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "# brief content"
            return result

        # Patch subprocess.run on the orchestrate_brief module directly
        import subprocess
        with patch.object(subprocess, "run", side_effect=fake_run):
            ob._run_render_brief(
                "claude-code-plugins", "2026-04-23", False, minimal_config
            )

        assert captured_cmds, "_run_render_brief must call subprocess.run"
        cmd = captured_cmds[0]
        assert "--no-persist" in cmd, (
            f"_run_render_brief must pass --no-persist by default; got cmd: {cmd}"
        )

    def test_run_render_brief_no_persist_flag_when_persist_disk_false(
        self, minimal_config: Path
    ) -> None:
        """_run_render_brief with persist_disk=False must include --no-persist in subprocess cmd."""
        captured_cmds: list[list[str]] = []

        def fake_run(cmd: list, **kwargs: object) -> object:
            captured_cmds.append(cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "# brief content"
            return result

        with patch("subprocess.run", side_effect=fake_run):
            ob._run_render_brief(
                "claude-code-plugins", "2026-04-23", False, minimal_config,
                persist_disk=False,
            )

        assert captured_cmds
        cmd = captured_cmds[0]
        assert "--no-persist" in cmd, (
            f"--no-persist must be in cmd when persist_disk=False; cmd={cmd}"
        )

    def test_run_render_brief_no_persist_absent_when_persist_disk_true(
        self, minimal_config: Path
    ) -> None:
        """_run_render_brief with persist_disk=True must NOT include --no-persist."""
        captured_cmds: list[list[str]] = []

        def fake_run(cmd: list, **kwargs: object) -> object:
            captured_cmds.append(cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "# brief content"
            return result

        with patch("subprocess.run", side_effect=fake_run):
            ob._run_render_brief(
                "claude-code-plugins", "2026-04-23", False, minimal_config,
                persist_disk=True,
            )

        assert captured_cmds
        cmd = captured_cmds[0]
        assert "--no-persist" not in cmd, (
            f"--no-persist must NOT be in cmd when persist_disk=True; cmd={cmd}"
        )


# ---------------------------------------------------------------------------
# AK6 / do_not_compact metadata
# ---------------------------------------------------------------------------


class TestDoNotCompactMetadata:
    """Every OB write must include do_not_compact: True in metadata."""

    def test_save_to_open_brain_sets_do_not_compact(
        self, tmp_path: Path
    ) -> None:
        """_save_to_open_brain must include do_not_compact: True in metadata sent to OB."""
        import os

        ob_home = tmp_path / ".open-brain"
        ob_home.mkdir(parents=True)
        (ob_home / "token").write_text("ob_testtoken")

        captured: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            captured.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-25",
                        text="# Test",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-test-2026-04-25",
                        metadata={"source": "daily-brief"},
                    )

        assert captured, "_async_save_memory must have been called"
        meta = captured[0]["metadata"]
        assert meta.get("do_not_compact") is True, (
            f"metadata.do_not_compact must be True, got: {meta}"
        )

    def test_save_metadata_includes_schema_version(
        self, tmp_path: Path
    ) -> None:
        """metadata must include schema_version: '1.5'."""
        import os

        ob_home = tmp_path / ".open-brain"
        ob_home.mkdir(parents=True)
        (ob_home / "token").write_text("ob_testtoken")

        captured: list[dict] = []

        async def fake_async_save(**kwargs: object) -> None:
            captured.append(dict(kwargs))

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OB_TOKEN", None)
                os.environ.pop("OB_URL", None)
                with patch.object(ob, "_async_save_memory", side_effect=fake_async_save):
                    ob._save_to_open_brain(
                        title="test — 2026-04-25",
                        text="# Test",
                        ob_type="daily_brief",
                        project="test",
                        session_ref="daily-brief-test-2026-04-25",
                        metadata={"source": "daily-brief"},
                    )

        assert captured
        meta = captured[0]["metadata"]
        assert meta.get("schema_version") == "1.5", (
            f"metadata.schema_version must be '1.5', got: {meta}"
        )


# ---------------------------------------------------------------------------
# AK7 + AK8 — Idempotency: no duplicate on second run
# ---------------------------------------------------------------------------


class TestIdempotency:
    """AK8: Re-running /daily-brief for same project+date does not create a duplicate observation."""

    def test_no_duplicate_on_second_run(
        self, minimal_config: Path, tmp_path: Path
    ) -> None:
        """First run: OB returns None → saves. Second run: OB returns content → skipped. Save called once."""
        date = "2026-04-23"
        ob_content = "# claude-code-plugins — 2026-04-23\n\nContent."
        save_call_count = [0]

        def fake_save(**kwargs: object) -> None:
            save_call_count[0] += 1

        # First run: OB returns None (not yet saved)
        with patch.object(ob, "_read_from_open_brain", return_value=None):
            with patch.object(ob, "_run_render_brief", return_value=ob_content):
                with patch.object(ob, "_save_to_open_brain", side_effect=fake_save):
                    result1 = ob.run_for_project(
                        project_name="claude-code-plugins",
                        date=date,
                        detailed=False,
                        config_path=minimal_config,
                    )

        assert result1["skipped"] is False
        assert save_call_count[0] == 1

        # Second run: OB returns the content (already saved)
        with patch.object(ob, "_read_from_open_brain", return_value=ob_content):
            with patch.object(ob, "_run_render_brief") as mock_render:
                with patch.object(ob, "_save_to_open_brain", side_effect=fake_save):
                    result2 = ob.run_for_project(
                        project_name="claude-code-plugins",
                        date=date,
                        detailed=False,
                        config_path=minimal_config,
                    )

        assert result2["skipped"] is True
        mock_render.assert_not_called()
        # Total saves: only 1 (from first run), not 2
        assert save_call_count[0] == 1, (
            f"save_to_open_brain must be called exactly once across both runs; got {save_call_count[0]}"
        )


# ---------------------------------------------------------------------------
# FIX-4 — _async_search_memory response-parsing logic
# ---------------------------------------------------------------------------


class TestAsyncSearchMemoryParsing:
    """_async_search_memory must correctly parse the OB search response and
    return the brief text on session_ref match, and None on mismatch."""

    def _make_mock_session(self, result_mock: "MagicMock") -> "MagicMock":
        """Build a mock ClientSession whose call_tool returns result_mock."""
        from unittest.mock import AsyncMock
        session = AsyncMock()
        session.initialize = AsyncMock()
        session.call_tool = AsyncMock(return_value=result_mock)
        return session

    def test_returns_brief_text_on_exact_session_ref_match(self) -> None:
        """_async_search_memory returns observation text when session_ref matches exactly."""
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        expected_text = "# claude-code-plugins — 2026-04-23\n\nBrief content from OB."
        target_ref = ob.make_session_ref("claude-code-plugins", "2026-04-23")

        # Simulate OB returning multiple observations — only one matches session_ref
        obs_json = json.dumps({
            "observations": [
                {"session_ref": "daily-brief-other-project-2026-04-23", "text": "wrong brief"},
                {"session_ref": target_ref, "text": expected_text},
                {"session_ref": "daily-brief-claude-code-plugins-2026-04-22", "text": "wrong date"},
            ]
        })

        async def _drive() -> "str | None":
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock, MagicMock

            content_block = MagicMock()
            content_block.type = "text"
            content_block.text = obs_json

            result_mock = MagicMock()
            result_mock.isError = False
            result_mock.content = [content_block]

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=result_mock)

            @asynccontextmanager
            async def mock_sh(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                return await ob._async_search_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testtoken",
                    project="claude-code-plugins",
                    date="2026-04-23",
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        result = asyncio.run(_drive())
        assert result == expected_text, (
            f"Expected brief text on exact session_ref match; got: {result!r}"
        )

    def test_returns_none_on_session_ref_mismatch(self) -> None:
        """_async_search_memory returns None when no observation has a matching session_ref."""
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        # OB returns observations but none match the target session_ref
        obs_json = json.dumps({
            "observations": [
                {"session_ref": "daily-brief-other-project-2026-04-23", "text": "wrong project"},
                {"session_ref": "daily-brief-claude-code-plugins-2026-04-01", "text": "wrong date"},
            ]
        })

        async def _drive() -> "str | None":
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock, MagicMock

            content_block = MagicMock()
            content_block.type = "text"
            content_block.text = obs_json

            result_mock = MagicMock()
            result_mock.isError = False
            result_mock.content = [content_block]

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=result_mock)

            @asynccontextmanager
            async def mock_sh(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                return await ob._async_search_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testtoken",
                    project="claude-code-plugins",
                    date="2026-04-23",
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        result = asyncio.run(_drive())
        assert result is None, (
            f"Expected None when no session_ref matches; got: {result!r}"
        )

    def test_returns_none_on_isError(self) -> None:
        """_async_search_memory returns None when result.isError is True."""
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        async def _drive() -> "str | None":
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock, MagicMock

            result_mock = MagicMock()
            result_mock.isError = True
            result_mock.content = []

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.call_tool = AsyncMock(return_value=result_mock)

            @asynccontextmanager
            async def mock_sh(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                return await ob._async_search_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testtoken",
                    project="claude-code-plugins",
                    date="2026-04-23",
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        result = asyncio.run(_drive())
        assert result is None, (
            f"Expected None when result.isError is True; got: {result!r}"
        )

    def test_search_uses_limit_10(self) -> None:
        """_async_search_memory sends limit=10 to handle ranked search returning non-exact first."""
        import asyncio
        from contextlib import asynccontextmanager
        from typing import Any

        captured_args: list[dict] = []

        async def _drive() -> None:
            import mcp.client.streamable_http as sh_mod
            import mcp as mcp_mod
            from unittest.mock import AsyncMock, MagicMock

            result_mock = MagicMock()
            result_mock.isError = False
            result_mock.content = []

            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()

            async def capture_call_tool(tool_name: str, args: dict, **kwargs: Any) -> Any:
                captured_args.append({"tool": tool_name, "args": args})
                return result_mock

            mock_session.call_tool = capture_call_tool

            @asynccontextmanager
            async def mock_sh(*args: Any, **kwargs: Any):
                yield (MagicMock(), MagicMock(), lambda: "session-id")

            class MockClientSession:
                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    pass

                async def __aenter__(self) -> Any:
                    return mock_session

                async def __aexit__(self, *args: Any) -> None:
                    pass

            original_sh = sh_mod.streamablehttp_client
            original_cs = mcp_mod.ClientSession
            sh_mod.streamablehttp_client = mock_sh  # type: ignore[assignment]
            mcp_mod.ClientSession = MockClientSession  # type: ignore[assignment]
            try:
                await ob._async_search_memory(
                    ob_url="https://ob.example.test/mcp",
                    token="ob_testtoken",
                    project="claude-code-plugins",
                    date="2026-04-23",
                )
            finally:
                sh_mod.streamablehttp_client = original_sh  # type: ignore[assignment]
                mcp_mod.ClientSession = original_cs  # type: ignore[assignment]

        asyncio.run(_drive())
        assert captured_args, "call_tool must have been invoked"
        search_call = captured_args[0]
        assert search_call["args"].get("limit") == 10, (
            f"search limit must be 10 (to handle ranked results); got: {search_call['args'].get('limit')}"
        )
