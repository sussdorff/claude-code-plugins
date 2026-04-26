#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "pytest>=8.0",
# ]
# ///
"""
Tests for core/skills/daily-brief/scripts/config.py

Covers:
- load_config(): bootstrap on missing file, idempotent reload, envelope contract
- resolve_project(): all projects, single project by name, not-found error
- brief_path(): correct path construction
- brief_exists(): file presence check
- briefs_dir(): directory path construction
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Path setup — make config.py importable without uv shebang stripping
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).parent.parent / "core" / "skills" / "daily-brief" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import config as cfg  # noqa: E402  (after sys.path manipulation)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    """Return a path for a non-existent config file inside tmp_path."""
    return tmp_path / ".claude" / "daily-brief.yml"


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    """Write a minimal valid config file and return its path."""
    config_path = tmp_path / ".claude" / "daily-brief.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "projects": [
            {
                "name": "test-project",
                "path": str(tmp_path / "test-project"),
                "slug": "test-project",
                "beads": True,
                "docs_dir": "docs",
            }
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
# Envelope contract helpers
# ---------------------------------------------------------------------------

REQUIRED_ENVELOPE_KEYS = {"status", "summary", "data", "errors", "next_steps", "open_items", "meta"}
REQUIRED_META_KEYS = {"contract_version", "producer", "generated_at", "schema"}


def assert_valid_envelope(result: dict) -> None:
    """Assert that result conforms to execution-result.schema.json structure."""
    assert REQUIRED_ENVELOPE_KEYS == set(result.keys()), (
        f"Envelope missing keys: {REQUIRED_ENVELOPE_KEYS - set(result.keys())}"
    )
    assert result["status"] in ("ok", "warning", "error"), f"Invalid status: {result['status']}"
    assert isinstance(result["summary"], str) and result["summary"]
    assert isinstance(result["data"], dict)
    assert isinstance(result["errors"], list)
    assert isinstance(result["next_steps"], list)
    assert isinstance(result["open_items"], list)
    meta = result["meta"]
    for k in REQUIRED_META_KEYS:
        assert k in meta, f"meta missing key: {k}"


# ---------------------------------------------------------------------------
# load_config() tests
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_bootstrap_creates_file_when_missing(self, tmp_config: Path) -> None:
        """load_config() creates the config file with default content when it doesn't exist."""
        assert not tmp_config.exists()
        result = cfg.load_config(tmp_config)
        assert tmp_config.exists()
        assert result["data"]["bootstrapped"] is True

    def test_bootstrap_idempotent(self, tmp_config: Path) -> None:
        """Calling load_config() twice does not change the file on second call."""
        cfg.load_config(tmp_config)
        mtime1 = tmp_config.stat().st_mtime

        result2 = cfg.load_config(tmp_config)
        mtime2 = tmp_config.stat().st_mtime

        assert mtime1 == mtime2, "Config file should not be rewritten on second load"
        assert result2["data"]["bootstrapped"] is False

    def test_bootstrapped_has_four_default_projects(self, tmp_config: Path) -> None:
        """Default bootstrap produces config with exactly four projects."""
        result = cfg.load_config(tmp_config)
        assert result["data"]["project_count"] == 4

    def test_bootstrapped_project_names(self, tmp_config: Path) -> None:
        """Default bootstrap contains the four canonical project names."""
        cfg.load_config(tmp_config)
        with tmp_config.open() as fh:
            raw = yaml.safe_load(fh)
        names = {p["name"] for p in raw["projects"]}
        assert names == {"claude-code-plugins", "mira", "polaris", "open-brain"}

    def test_bootstrapped_defaults_section(self, tmp_config: Path) -> None:
        """Bootstrap includes defaults section with all required keys."""
        cfg.load_config(tmp_config)
        with tmp_config.open() as fh:
            raw = yaml.safe_load(fh)
        defaults = raw.get("defaults", {})
        for key in ("since", "format", "detailed", "language", "timezone"):
            assert key in defaults, f"defaults missing key: {key}"

    def test_returns_valid_envelope(self, tmp_config: Path) -> None:
        """load_config() returns a valid execution-result envelope."""
        result = cfg.load_config(tmp_config)
        assert_valid_envelope(result)
        assert result["status"] == "ok"

    def test_loads_existing_config(self, minimal_config: Path) -> None:
        """load_config() loads an existing file without bootstrapping."""
        result = cfg.load_config(minimal_config)
        assert result["data"]["bootstrapped"] is False
        assert result["data"]["project_count"] == 1

    def test_config_path_in_data(self, tmp_config: Path) -> None:
        """data.config_path matches the resolved path."""
        result = cfg.load_config(tmp_config)
        assert result["data"]["config_path"] == str(tmp_config)


# ---------------------------------------------------------------------------
# resolve_project() tests
# ---------------------------------------------------------------------------


class TestResolveProject:
    def test_none_returns_all_projects(self, minimal_config: Path) -> None:
        """resolve_project(None) returns all projects as a list."""
        result = cfg.resolve_project(None, config_path=minimal_config)
        assert_valid_envelope(result)
        assert result["status"] == "ok"
        assert result["data"]["count"] == 1
        assert result["data"]["query"] is None

    def test_named_project_returned(self, minimal_config: Path) -> None:
        """resolve_project('test-project') returns the matching project."""
        result = cfg.resolve_project("test-project", config_path=minimal_config)
        assert_valid_envelope(result)
        assert result["status"] == "ok"
        assert len(result["data"]["projects"]) == 1
        assert result["data"]["projects"][0]["name"] == "test-project"

    def test_not_found_returns_error(self, minimal_config: Path) -> None:
        """resolve_project() returns error envelope when project is not found."""
        result = cfg.resolve_project("nonexistent", config_path=minimal_config)
        assert_valid_envelope(result)
        assert result["status"] == "error"
        assert len(result["errors"]) >= 1
        assert result["errors"][0]["code"] == "project-not-found"

    def test_project_dict_has_required_fields(self, minimal_config: Path) -> None:
        """Returned project dict contains all required fields."""
        result = cfg.resolve_project("test-project", config_path=minimal_config)
        p = result["data"]["projects"][0]
        for key in ("name", "path", "slug", "beads", "docs_dir"):
            assert key in p, f"project dict missing key: {key}"


# ---------------------------------------------------------------------------
# briefs_dir() tests
# ---------------------------------------------------------------------------


class TestBriefsDir:
    def test_returns_correct_path(self, tmp_path: Path) -> None:
        """briefs_dir() returns ~/.claude/projects/<slug>/daily-briefs/ (user-local, not in project)."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        result = cfg.briefs_dir(p)
        # New path: ~/.claude/projects/foo/daily-briefs
        assert result == Path.home() / ".claude" / "projects" / "foo" / "daily-briefs"
        # Must NOT be inside the project path
        assert str(tmp_path) not in str(result)


# ---------------------------------------------------------------------------
# brief_path() tests
# ---------------------------------------------------------------------------


class TestBriefPath:
    def test_string_date(self, tmp_path: Path) -> None:
        """brief_path() accepts a string date and uses the new user-local path."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        result = cfg.brief_path(p, "2026-04-24")
        assert result == Path.home() / ".claude" / "projects" / "foo" / "daily-briefs" / "2026-04-24.md"

    def test_date_object(self, tmp_path: Path) -> None:
        """brief_path() accepts a datetime.date object and places it under ~/.claude/projects/<slug>/."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        d = datetime.date(2026, 4, 24)
        result = cfg.brief_path(p, d)
        assert result.name == "2026-04-24.md"
        assert result.parent == Path.home() / ".claude" / "projects" / "foo" / "daily-briefs"

    def test_no_year_subfolder(self, tmp_path: Path) -> None:
        """brief_path() uses flat layout — no year subfolder."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        result = cfg.brief_path(p, "2026-04-24")
        # Parent should be daily-briefs/, not daily-briefs/2026/
        assert result.parent.name == "daily-briefs"


# ---------------------------------------------------------------------------
# brief_exists() tests
# ---------------------------------------------------------------------------


class TestBriefExists:
    def test_returns_false_when_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """brief_exists() returns False when brief file does not exist."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        monkeypatch.setattr(cfg, "briefs_dir", lambda proj: tmp_path / "briefs" / proj.slug)
        assert cfg.brief_exists(p, "2026-04-24") is False

    def test_returns_true_when_exists(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """brief_exists() returns True when brief file exists on disk."""
        p = cfg.ProjectConfig(
            name="foo",
            path=tmp_path / "foo",
            slug="foo",
            beads=True,
            docs_dir="docs",
        )
        monkeypatch.setattr(cfg, "briefs_dir", lambda proj: tmp_path / "briefs" / proj.slug)
        controlled_dir = tmp_path / "briefs" / p.slug
        controlled_dir.mkdir(parents=True, exist_ok=True)
        path = controlled_dir / "2026-04-24.md"
        path.write_text("# Brief")
        assert cfg.brief_exists(p, "2026-04-24") is True
