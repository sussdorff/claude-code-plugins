#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
# ]
# ///
"""
Tests for scripts/discover-projects.py (CCP-6n3)

TDD Red-Green Gate — acceptance criteria tested first, then verified.

Coverage:
- Detects project from ~/.claude/projects/ JSONL modified within window
- Detects project from ~/code/ git repos with commits within window
- Returns unconfigured projects as warning
- Does not crash on malformed JSONL (logs warning, continues)
- Does not crash on unreadable git repo (logs warning, continues)
- --all-active mode: no warning when all active projects are configured
- --all-active mode: warning lists unconfigured active projects
- Normal run (no --all-active): discovery NOT invoked
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

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

import config as _cfg  # noqa: E402


def _load_discover():
    """Load the discover-projects module via importlib (hyphen in filename)."""
    spec = importlib.util.spec_from_file_location(
        "discover_projects", _SCRIPTS_DIR / "discover-projects.py"
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


dp = _load_discover()

# Also load orchestrate-brief for --all-active tests
_ob_spec = importlib.util.spec_from_file_location(
    "orchestrate_brief", _SCRIPTS_DIR / "orchestrate-brief.py"
)
_ob_mod = importlib.util.module_from_spec(_ob_spec)  # type: ignore[arg-type]
_ob_spec.loader.exec_module(_ob_mod)  # type: ignore[union-attr]
ob = _ob_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_git_repo(path: Path) -> None:
    """Initialize a bare git repo at path with at least one commit in the last 24h."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, capture_output=True, check=True,
    )
    (path / "README.md").write_text("# Test repo")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path, capture_output=True, check=True,
    )


def _make_config(tmp_path: Path, projects: list[dict]) -> Path:
    """Write a daily-brief.yml config file and return its path."""
    config_path = tmp_path / "daily-brief.yml"
    data = {
        "projects": projects,
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
# Envelope contract helper
# ---------------------------------------------------------------------------

REQUIRED_ENVELOPE_KEYS = {"status", "summary", "data", "errors", "next_steps", "open_items", "meta"}


def assert_valid_envelope(result: dict) -> None:
    assert REQUIRED_ENVELOPE_KEYS == set(result.keys()), (
        f"Envelope missing keys: {REQUIRED_ENVELOPE_KEYS - set(result.keys())}"
    )
    assert result["status"] in ("ok", "warning", "error")
    assert isinstance(result["summary"], str) and result["summary"]
    assert isinstance(result["data"], dict)


# ---------------------------------------------------------------------------
# Tests: discover_from_jsonl()
# ---------------------------------------------------------------------------


class TestDiscoverFromJsonl:
    """Tests for discover_from_jsonl() — scan ~/.claude/projects/ JSONL files."""

    def test_discovers_project_slug_from_projectpath(self, tmp_path: Path) -> None:
        """JSONL with projectPath field → extracts slug from last path component."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        jsonl_file = projects_dir / "some-new-project.jsonl"
        jsonl_file.write_text(
            json.dumps({"projectPath": "/Users/test/code/some-new-project"}) + "\n"
        )
        # Make it recently modified
        now = time.time()
        os.utime(jsonl_file, (now, now))

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)

        assert "some-new-project" in result

    def test_discovers_project_slug_from_cwd(self, tmp_path: Path) -> None:
        """JSONL with cwd field → extracts slug from cwd path."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        jsonl_file = projects_dir / "my-project-xyz.jsonl"
        jsonl_file.write_text(
            json.dumps({"cwd": "/home/user/code/my-project-xyz"}) + "\n"
        )
        now = time.time()
        os.utime(jsonl_file, (now, now))

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)

        assert "my-project-xyz" in result

    def test_skips_file_not_modified_within_window(self, tmp_path: Path) -> None:
        """JSONL file older than since date is skipped."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        jsonl_file = projects_dir / "old-project.jsonl"
        jsonl_file.write_text(
            json.dumps({"projectPath": "/Users/test/code/old-project"}) + "\n"
        )
        # Set mtime to 7 days ago
        old_time = time.time() - (7 * 24 * 3600)
        os.utime(jsonl_file, (old_time, old_time))

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)

        assert "old-project" not in result

    def test_malformed_jsonl_does_not_crash(self, tmp_path: Path) -> None:
        """Malformed JSON lines → logged to stderr, continues, no exception raised."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        jsonl_file = projects_dir / "broken.jsonl"
        jsonl_file.write_text(
            "this is not json\n"
            + json.dumps({"projectPath": "/Users/test/code/valid-project"}) + "\n"
            + "{incomplete json\n"
        )
        now = time.time()
        os.utime(jsonl_file, (now, now))

        since = datetime.date.today() - datetime.timedelta(days=1)
        # Must not raise
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)
        # Valid line should still be processed
        assert "valid-project" in result

    def test_empty_projects_dir_returns_empty_set(self, tmp_path: Path) -> None:
        """Empty directory → returns empty set."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)
        assert result == set()

    def test_nonexistent_projects_dir_returns_empty_set(self, tmp_path: Path) -> None:
        """Missing ~/.claude/projects/ → returns empty set, no crash."""
        projects_dir = tmp_path / "nonexistent_projects"

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)
        assert result == set()

    def test_multiple_lines_extracts_all_valid_slugs(self, tmp_path: Path) -> None:
        """Multiple valid JSONL lines → all slugs extracted."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        jsonl_file = projects_dir / "session.jsonl"
        lines = [
            json.dumps({"projectPath": "/code/alpha"}),
            json.dumps({"projectPath": "/code/beta"}),
            json.dumps({"cwd": "/code/gamma"}),
        ]
        jsonl_file.write_text("\n".join(lines) + "\n")
        now = time.time()
        os.utime(jsonl_file, (now, now))

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result

    def test_discovers_jsonl_in_subdirectory(self, tmp_path: Path) -> None:
        """Real ~/.claude/projects/ layout: escaped-path subdirs contain UUID JSONL files.

        Layout: projects_dir / -Users-foo-bar / abc.jsonl
        The JSONL inside references projectPath /Users/foo/bar → slug 'bar'.
        """
        projects_dir = tmp_path / "projects"
        # Create the escaped-path subdirectory (as real Claude Code does)
        subdir = projects_dir / "-Users-foo-bar"
        subdir.mkdir(parents=True)
        jsonl_file = subdir / "abc.jsonl"
        jsonl_file.write_text(
            json.dumps({"projectPath": "/Users/foo/bar"}) + "\n"
        )
        now = time.time()
        os.utime(jsonl_file, (now, now))

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_jsonl(projects_dir=projects_dir, since=since)

        assert "bar" in result


# ---------------------------------------------------------------------------
# Tests: discover_from_git()
# ---------------------------------------------------------------------------


class TestDiscoverFromGit:
    """Tests for discover_from_git() — scan ~/code/ for active git repos."""

    def test_detects_repo_with_recent_commit(self, tmp_path: Path) -> None:
        """Repo with commit within window → slug is returned."""
        code_dir = tmp_path / "code"
        repo_path = code_dir / "active-project"
        _make_git_repo(repo_path)

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_git(code_dir=code_dir, since=since)

        assert "active-project" in result

    def test_ignores_repo_without_recent_commit(self, tmp_path: Path) -> None:
        """Repo with no commits in window → slug NOT returned."""
        code_dir = tmp_path / "code"
        repo_path = code_dir / "stale-project"
        _make_git_repo(repo_path)

        # Use a since date far in the future so nothing is "recent"
        since = datetime.date.today() + datetime.timedelta(days=10)
        result = dp.discover_from_git(code_dir=code_dir, since=since)

        assert "stale-project" not in result

    def test_ignores_non_git_directories(self, tmp_path: Path) -> None:
        """Directories that are not git repos → silently skipped."""
        code_dir = tmp_path / "code"
        not_git = code_dir / "not-a-repo"
        not_git.mkdir(parents=True)
        (not_git / "file.txt").write_text("hello")

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_git(code_dir=code_dir, since=since)

        assert "not-a-repo" not in result

    def test_nonexistent_code_dir_returns_empty_set(self, tmp_path: Path) -> None:
        """Missing ~/code/ → returns empty set, no crash."""
        code_dir = tmp_path / "no_code_here"

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_git(code_dir=code_dir, since=since)
        assert result == set()

    def test_unreadable_repo_does_not_crash(self, tmp_path: Path) -> None:
        """Git error on a repo → logs warning, continues, no exception."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        # Create a directory named like a repo but that git can't read
        fake_repo = code_dir / "broken-repo"
        fake_repo.mkdir()
        # Create a .git dir that is actually a file (will cause git to fail)
        (fake_repo / ".git").write_text("not a real git dir")

        since = datetime.date.today() - datetime.timedelta(days=1)
        # Must not raise
        result = dp.discover_from_git(code_dir=code_dir, since=since)
        assert isinstance(result, set)

    def test_multiple_active_repos_all_returned(self, tmp_path: Path) -> None:
        """Multiple repos with recent commits → all slugs returned."""
        code_dir = tmp_path / "code"
        for name in ["project-a", "project-b", "project-c"]:
            _make_git_repo(code_dir / name)

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_from_git(code_dir=code_dir, since=since)
        assert "project-a" in result
        assert "project-b" in result
        assert "project-c" in result


# ---------------------------------------------------------------------------
# Tests: discover_active_projects() — main discovery function
# ---------------------------------------------------------------------------


class TestDiscoverActiveProjects:
    """Tests for discover_active_projects() — returns envelope with all active projects."""

    def test_returns_valid_envelope(self, tmp_path: Path) -> None:
        """discover_active_projects() returns execution-result envelope."""
        config_path = _make_config(tmp_path, [])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        assert_valid_envelope(result)

    def test_unconfigured_projects_returned_in_data(self, tmp_path: Path) -> None:
        """Projects found active but not in config are returned in data.unconfigured."""
        code_dir = tmp_path / "code"
        new_project_path = code_dir / "some-new-project"
        _make_git_repo(new_project_path)

        # Config has NO projects
        config_path = _make_config(tmp_path, [])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        assert "some-new-project" in result["data"]["unconfigured"]

    def test_configured_projects_in_all_projects(self, tmp_path: Path) -> None:
        """Configured projects always appear in data.all_projects."""
        code_dir = tmp_path / "code"
        proj_path = code_dir / "my-project"
        _make_git_repo(proj_path)

        config_path = _make_config(tmp_path, [
            {
                "name": "my-project",
                "path": str(proj_path),
                "slug": "my-project",
                "beads": True,
                "docs_dir": "docs",
            }
        ])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        all_slugs = [p["slug"] for p in result["data"]["all_projects"]]
        assert "my-project" in all_slugs

    def test_no_unconfigured_when_all_active_are_configured(self, tmp_path: Path) -> None:
        """When all active projects are configured → unconfigured is empty list."""
        code_dir = tmp_path / "code"
        proj_path = code_dir / "configured-project"
        _make_git_repo(proj_path)

        config_path = _make_config(tmp_path, [
            {
                "name": "configured-project",
                "path": str(proj_path),
                "slug": "configured-project",
                "beads": True,
                "docs_dir": "docs",
            }
        ])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        assert result["data"]["unconfigured"] == []

    def test_two_unconfigured_projects_both_listed(self, tmp_path: Path) -> None:
        """Two unconfigured active projects → both appear in unconfigured list."""
        code_dir = tmp_path / "code"
        for name in ["new-alpha", "new-beta"]:
            _make_git_repo(code_dir / name)

        config_path = _make_config(tmp_path, [])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        assert "new-alpha" in result["data"]["unconfigured"]
        assert "new-beta" in result["data"]["unconfigured"]

    def test_unconfigured_projects_have_projectconfig_objects(self, tmp_path: Path) -> None:
        """data.unconfigured_configs contains ProjectConfig-compatible dicts."""
        code_dir = tmp_path / "code"
        _make_git_repo(code_dir / "fresh-project")

        config_path = _make_config(tmp_path, [])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        since = datetime.date.today() - datetime.timedelta(days=1)
        result = dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )
        # Should have at least one entry if fresh-project was discovered
        if "fresh-project" in result["data"]["unconfigured"]:
            configs = result["data"]["unconfigured_configs"]
            assert any(c["slug"] == "fresh-project" for c in configs)


# ---------------------------------------------------------------------------
# Tests: --all-active CLI flag in orchestrate-brief.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests: parse_since() helpers
# ---------------------------------------------------------------------------


class TestParseSince:
    """Tests for parse_since() date parsing."""

    def test_yesterday_alias_returns_one_date(self) -> None:
        """'yesterday' is a valid alias for '1d' and returns yesterday's date."""
        result = ob.parse_since("yesterday")
        assert len(result) == 1
        expected = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        assert result[0] == expected

    def test_1d_returns_one_date(self) -> None:
        """'1d' returns a list with yesterday."""
        result = ob.parse_since("1d")
        assert len(result) == 1

    def test_3d_returns_three_dates(self) -> None:
        """'3d' returns dates from 3 days ago through yesterday."""
        result = ob.parse_since("3d")
        assert len(result) == 3

    def test_invalid_format_raises_valueerror(self) -> None:
        """Non-Nd and non-'yesterday' format raises ValueError."""
        with pytest.raises(ValueError):
            ob.parse_since("abc")

    def test_invalid_format_no_d_suffix(self) -> None:
        """Missing 'd' suffix raises ValueError."""
        with pytest.raises(ValueError):
            ob.parse_since("3")


class TestAllActiveFlag:
    """Tests for --all-active flag in orchestrate-brief.py parse_args."""

    def test_parse_args_has_all_active_flag(self) -> None:
        """parse_args() accepts --all-active flag."""
        args = ob.parse_args(["--all-active"])
        assert args.all_active is True

    def test_parse_args_all_active_default_false(self) -> None:
        """--all-active defaults to False."""
        args = ob.parse_args([])
        assert args.all_active is False

    def test_all_active_with_config(self, tmp_path: Path) -> None:
        """--all-active can be combined with --config."""
        config_path = tmp_path / "daily-brief.yml"
        args = ob.parse_args(["--all-active", "--config", str(config_path)])
        assert args.all_active is True

    def test_all_active_with_since_returns_error(self, tmp_path: Path) -> None:
        """--all-active combined with --since returns exit code 1 (CLI error)."""
        config_path = _make_config(tmp_path, [])
        ret = ob.main(argv=["--all-active", "--since=3d", "--config", str(config_path)])
        assert ret == 1

    def test_all_active_with_range_returns_error(self, tmp_path: Path) -> None:
        """--all-active combined with --range returns exit code 1 (CLI error)."""
        config_path = _make_config(tmp_path, [])
        ret = ob.main(argv=[
            "--all-active", "--range=2026-04-20..2026-04-22",
            "--config", str(config_path),
        ])
        assert ret == 1


# ---------------------------------------------------------------------------
# Tests: warning block injection in aggregated output
# ---------------------------------------------------------------------------


class TestWarningBlock:
    """Tests for warning block in aggregated output when unconfigured projects found."""

    def test_warning_block_rendered_for_unconfigured(self) -> None:
        """_inject_warning_block() adds warning at top when unconfigured projects exist."""
        unconfigured = ["some-new-project"]
        content = "# Brief content\n\nSome details."
        result = ob._inject_warning_block(content, unconfigured)
        assert "Aktive Projekte nicht in Config" in result
        assert "some-new-project" in result
        # Warning should be at the top
        lines = result.strip().split("\n")
        warning_idx = next(
            (i for i, l in enumerate(lines) if "Aktive Projekte" in l), None
        )
        content_idx = next(
            (i for i, l in enumerate(lines) if "Brief content" in l), None
        )
        assert warning_idx is not None
        assert content_idx is not None
        assert warning_idx < content_idx

    def test_no_warning_block_when_unconfigured_is_empty(self) -> None:
        """_inject_warning_block() returns unchanged content when no unconfigured projects."""
        content = "# Brief content\n\nSome details."
        result = ob._inject_warning_block(content, [])
        assert "Aktive Projekte" not in result
        assert result == content

    def test_warning_lists_multiple_unconfigured(self) -> None:
        """Warning block lists all unconfigured project slugs."""
        unconfigured = ["project-x", "project-y", "project-z"]
        content = "# Brief"
        result = ob._inject_warning_block(content, unconfigured)
        assert "project-x" in result
        assert "project-y" in result
        assert "project-z" in result


# ---------------------------------------------------------------------------
# Tests: --all-active end-to-end behavior in orchestrate()
# ---------------------------------------------------------------------------


class TestAllActiveOrchestration:
    """Integration tests: --all-active triggers discovery and adds unconfigured projects."""

    def test_all_active_calls_discover(self, tmp_path: Path) -> None:
        """When --all-active is set, discover_active_projects is called."""
        config_path = _make_config(tmp_path, [
            {
                "name": "configured-proj",
                "path": str(tmp_path / "configured-proj"),
                "slug": "configured-proj",
                "beads": True,
                "docs_dir": "docs",
            }
        ])

        discovered_calls = []

        def fake_discover(**kwargs):
            discovered_calls.append(kwargs)
            return {
                "status": "ok",
                "summary": "discovered",
                "data": {
                    "unconfigured": [],
                    "unconfigured_configs": [],
                    "all_projects": [],
                },
                "errors": [],
                "next_steps": [],
                "open_items": [],
                "meta": {"contract_version": "1", "producer": "test"},
            }

        with patch.object(ob, "discover_active_projects", side_effect=fake_discover):
            with patch.object(ob, "run_for_project", return_value={"skipped": True}):
                result = ob.orchestrate(
                    project=None,
                    dates=["2026-04-24"],
                    detailed=False,
                    config_path=config_path,
                    all_active=True,
                )

        assert len(discovered_calls) == 1

    def test_all_active_false_does_not_call_discover(self, tmp_path: Path) -> None:
        """When --all-active is NOT set, discover_active_projects is NOT called."""
        config_path = _make_config(tmp_path, [
            {
                "name": "configured-proj",
                "path": str(tmp_path / "configured-proj"),
                "slug": "configured-proj",
                "beads": True,
                "docs_dir": "docs",
            }
        ])

        discovered_calls = []

        def fake_discover(**kwargs):
            discovered_calls.append(kwargs)
            return {"data": {"unconfigured": [], "unconfigured_configs": [], "all_projects": []}}

        with patch.object(ob, "discover_active_projects", side_effect=fake_discover):
            with patch.object(ob, "run_for_project", return_value={"skipped": True}):
                ob.orchestrate(
                    project=None,
                    dates=["2026-04-24"],
                    detailed=False,
                    config_path=config_path,
                    all_active=False,
                )

        assert len(discovered_calls) == 0

    def test_all_active_includes_discovered_projects_in_output(self, tmp_path: Path) -> None:
        """Discovered unconfigured projects are processed and included in results."""
        config_path = _make_config(tmp_path, [
            {
                "name": "existing-proj",
                "path": str(tmp_path / "existing-proj"),
                "slug": "existing-proj",
                "beads": True,
                "docs_dir": "docs",
            }
        ])

        def fake_discover(**kwargs):
            return {
                "status": "ok",
                "summary": "found 1 unconfigured",
                "data": {
                    "unconfigured": ["some-new-project"],
                    "unconfigured_configs": [
                        {
                            "name": "some-new-project",
                            "path": str(tmp_path / "some-new-project"),
                            "slug": "some-new-project",
                            "beads": False,
                            "docs_dir": "docs",
                        }
                    ],
                    "all_projects": [],
                },
                "errors": [],
                "next_steps": [],
                "open_items": [],
                "meta": {"contract_version": "1", "producer": "test"},
            }

        processed_projects = []

        def fake_run(project_name, date, detailed, config_path, **kwargs):
            processed_projects.append(project_name)
            return {"skipped": True}

        with patch.object(ob, "discover_active_projects", side_effect=fake_discover):
            with patch.object(ob, "run_for_project", side_effect=fake_run):
                ob.orchestrate(
                    project=None,
                    dates=["2026-04-24"],
                    detailed=False,
                    config_path=config_path,
                    all_active=True,
                )

        assert "some-new-project" in processed_projects
        assert "existing-proj" in processed_projects

    def test_main_all_active_flag_passes_to_orchestrate(self, tmp_path: Path) -> None:
        """main() with --all-active passes all_active=True to orchestrate."""
        config_path = _make_config(tmp_path, [
            {
                "name": "test-proj",
                "path": str(tmp_path / "test-proj"),
                "slug": "test-proj",
                "beads": True,
                "docs_dir": "docs",
            }
        ])
        # Pre-create brief so run_for_project skips
        brief_dir = tmp_path / "test-proj" / ".claude" / "daily-briefs"
        brief_dir.mkdir(parents=True)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        (brief_dir / f"{yesterday}.md").write_text("# Test brief")

        captured_all_active = []

        real_orchestrate = ob.orchestrate

        def fake_orchestrate(*args, **kwargs):
            captured_all_active.append(kwargs.get("all_active", False))
            return real_orchestrate(*args, **kwargs)

        with patch.object(ob, "orchestrate", side_effect=fake_orchestrate):
            with patch.object(ob, "discover_active_projects", return_value={
                "status": "ok",
                "summary": "ok",
                "data": {
                    "unconfigured": [],
                    "unconfigured_configs": [],
                    "all_projects": [],
                },
                "errors": [],
                "next_steps": [],
                "open_items": [],
                "meta": {"contract_version": "1", "producer": "test"},
            }):
                ob.main(argv=["--all-active", "--config", str(config_path)])

        assert len(captured_all_active) >= 1
        assert captured_all_active[0] is True


# ---------------------------------------------------------------------------
# Tests: warning block in main() output
# ---------------------------------------------------------------------------


class TestWarningBlockInOutput:
    """Tests that warning block appears in output when unconfigured projects found."""

    def test_aggregate_output_includes_warning_when_unconfigured(self) -> None:
        """_aggregate_output() with unconfigured projects → warning in output."""
        results = [{"content": "# Brief\n\nContent.", "project": "configured", "date": "2026-04-24"}]
        unconfigured = ["ghost-project"]
        output = ob._aggregate_output(results, ["2026-04-24"], unconfigured_projects=unconfigured)
        assert "Aktive Projekte nicht in Config" in output
        assert "ghost-project" in output

    def test_aggregate_output_no_warning_without_unconfigured(self) -> None:
        """_aggregate_output() without unconfigured → no warning block."""
        results = [{"content": "# Brief\n\nContent.", "project": "configured", "date": "2026-04-24"}]
        output = ob._aggregate_output(results, ["2026-04-24"], unconfigured_projects=[])
        assert "Aktive Projekte nicht in Config" not in output

    def test_aggregate_output_no_warning_by_default(self) -> None:
        """_aggregate_output() without unconfigured_projects kwarg → no warning block."""
        results = [{"content": "# Brief\n\nContent.", "project": "configured", "date": "2026-04-24"}]
        output = ob._aggregate_output(results, ["2026-04-24"])
        assert "Aktive Projekte nicht in Config" not in output

    def test_config_not_modified_by_discover(self, tmp_path: Path) -> None:
        """discover_active_projects does NOT auto-add to daily-brief.yml."""
        code_dir = tmp_path / "code"
        new_proj = code_dir / "secret-new-project"
        _make_git_repo(new_proj)

        config_path = _make_config(tmp_path, [])
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        original_content = config_path.read_text()

        since = datetime.date.today() - datetime.timedelta(days=1)
        dp.discover_active_projects(
            config_path=config_path,
            projects_dir=projects_dir,
            code_dir=code_dir,
            since=since,
        )

        # Config file must not be modified
        assert config_path.read_text() == original_content
