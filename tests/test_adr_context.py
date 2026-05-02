"""
Tests for CCP-2n67: adr-context.py discover/inject/verify modes.

Verifies:
1. discover correctly filters ADRs based on applies_to globs and changed paths
2. inject produces a markdown block ≤ 2KB per ADR (Decision + Prohibitions + path)
3. verify re-discovers from diff and ignores caller-supplied provenance
4. All modes emit execution-result envelope where applicable
5. parse_adr_frontmatter correctly parses required fields
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the script module directly (PEP 723 scripts are importable if we
# add the directory to sys.path and strip the shebang/PEP-723 metadata)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "core" / "scripts" / "adr-context.py"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "adr_context"


def _load_adr_context():
    """Load adr-context.py as a module, stripping PEP-723 header lines.

    pyyaml must be installed in the test environment (e.g. via `uv run pytest`
    which resolves the PEP-723 dependencies, or by listing pyyaml as a dev
    dependency). If pyyaml is missing this will raise ImportError with a clear
    message — do not probe hardcoded site-packages paths.
    """
    import yaml as _yaml_mod  # noqa: PLC0415

    source = SCRIPT_PATH.read_text()
    # Strip shebang + PEP-723 inline script metadata block so Python can parse it
    lines = source.splitlines()
    filtered: list[str] = []
    in_meta = False
    for line in lines:
        if line.startswith("#!"):
            filtered.append("")
            continue
        if line.strip() == "# /// script":
            in_meta = True
            filtered.append("")
            continue
        if in_meta:
            filtered.append("")
            if line.strip() == "# ///":
                in_meta = False
            continue
        filtered.append(line)
    cleaned = "\n".join(filtered)
    # Build a minimal module namespace with yaml pre-injected
    module_ns: dict = {"__name__": "adr_context", "__file__": str(SCRIPT_PATH), "yaml": _yaml_mod}
    exec(compile(cleaned, str(SCRIPT_PATH), "exec"), module_ns)  # noqa: S102
    # Wrap dict as a simple namespace object so attribute access works
    import types  # noqa: PLC0415
    module = types.SimpleNamespace(**module_ns)
    return module


@pytest.fixture(scope="module")
def adr_mod():
    return _load_adr_context()


@pytest.fixture()
def tmp_adr_dir(tmp_path: Path) -> Path:
    """Copy fixture ADRs into a temporary directory."""
    import shutil
    dest = tmp_path / "adr"
    dest.mkdir()
    for f in FIXTURES_DIR.glob("*.md"):
        shutil.copy(f, dest / f.name)
    return dest


# ---------------------------------------------------------------------------
# TestParseFrontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_parses_required_fields(self, adr_mod, tmp_adr_dir: Path):
        adr_file = tmp_adr_dir / "adr_alpha.md"
        result = adr_mod.parse_adr_frontmatter(adr_file)
        assert result["id"] == "ADR-alpha"
        assert result["decision_summary"] == (
            "All subprocess invocations must go through CommandRunner to enable testing and auditing."
        )
        assert "scripts/*.py" in result["applies_to"]
        assert "core/**/*.py" in result["applies_to"]
        assert any("CommandRunner" in p for p in result["prohibits"])
        assert result["path"] == str(adr_file)

    def test_returns_none_for_no_frontmatter(self, adr_mod, tmp_path: Path):
        f = tmp_path / "no_frontmatter.md"
        f.write_text("# Plain markdown\nNo YAML here.\n")
        result = adr_mod.parse_adr_frontmatter(f)
        assert result is None


# ---------------------------------------------------------------------------
# TestDiscoverAdrs
# ---------------------------------------------------------------------------


class TestDiscoverAdrs:
    def test_returns_matching_adr_by_glob(self, adr_mod, tmp_adr_dir: Path):
        """Changed path scripts/foo.py matches only ADR-alpha (scripts/*.py)."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        ids = [r["id"] for r in results]
        assert "ADR-alpha" in ids
        assert "ADR-beta" not in ids
        assert "ADR-gamma" not in ids

    def test_no_match_returns_empty(self, adr_mod, tmp_adr_dir: Path):
        """Changed path that matches no ADR applies_to glob returns empty list."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["unrelated/file.ts"],
            bead_description_override=None,
        )
        assert results == []

    def test_text_match_from_bead_description(self, adr_mod, tmp_adr_dir: Path):
        """Bead description containing 'ADR-alpha' includes that ADR even without path match."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["unrelated/file.ts"],
            bead_description_override="This bead relates to ADR-alpha compliance.",
        )
        ids = [r["id"] for r in results]
        assert "ADR-alpha" in ids
        assert "ADR-beta" not in ids

    def test_deduplicates_path_and_text_match(self, adr_mod, tmp_adr_dir: Path):
        """ADR matched by both path and text appears only once."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override="References ADR-alpha again.",
        )
        ids = [r["id"] for r in results]
        assert ids.count("ADR-alpha") == 1

    def test_match_reason_path(self, adr_mod, tmp_adr_dir: Path):
        """Path-matched ADR has match_reason containing 'path'."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        assert any("path" in r["match_reason"] for r in results)

    def test_match_reason_text(self, adr_mod, tmp_adr_dir: Path):
        """Text-matched ADR has match_reason containing 'text'."""
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=[],
            bead_description_override="ADR-beta is important",
        )
        beta = next((r for r in results if r["id"] == "ADR-beta"), None)
        assert beta is not None
        assert "text" in beta["match_reason"]

    def test_glob_matches_direct_children_for_double_star(self, adr_mod, tmp_adr_dir: Path):
        """Regression: ADR-alpha applies_to=['core/**/*.py'] must match core/foo.py.

        Previously _matches_glob delegated to PurePosixPath.match, which in
        Python 3.12 only matches `**` against exactly one segment — so direct
        children like `core/foo.py` and deeply nested children like
        `core/a/b/foo.py` were both skipped, missing real ADR violations.
        """
        # Direct child (zero `**` segments)
        results = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["core/foo.py"],
            bead_description_override=None,
        )
        ids = [r["id"] for r in results]
        assert "ADR-alpha" in ids, (
            "ADR-alpha (applies_to: core/**/*.py) must match direct child core/foo.py"
        )
        # Multi-segment child (2+ `**` segments)
        results_deep = adr_mod.discover_adrs(
            adr_dir=tmp_adr_dir,
            changed_paths=["core/a/b/foo.py"],
            bead_description_override=None,
        )
        ids_deep = [r["id"] for r in results_deep]
        assert "ADR-alpha" in ids_deep, (
            "ADR-alpha (applies_to: core/**/*.py) must match deeply nested core/a/b/foo.py"
        )

    def test_loads_adrs_recursively(self, adr_mod, tmp_path: Path):
        """Regression: _load_adrs must walk subdirectories (rglob, not glob)."""
        nested = tmp_path / "adr" / "subdir"
        nested.mkdir(parents=True)
        # Copy fixture into a nested directory
        import shutil
        shutil.copy(FIXTURES_DIR / "adr_alpha.md", nested / "adr_alpha.md")
        results = adr_mod.discover_adrs(
            adr_dir=tmp_path / "adr",
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        ids = [r["id"] for r in results]
        assert "ADR-alpha" in ids, "ADR in subdirectory must be discovered (recursive load)"

    def test_envelope_structure(self, adr_mod, tmp_adr_dir: Path):
        """discover_adrs_envelope emits valid execution-result envelope."""
        envelope = adr_mod.discover_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        assert envelope["status"] in ("ok", "warning", "error")
        assert "summary" in envelope
        assert "data" in envelope
        assert "adrs_in_scope" in envelope["data"]
        assert "errors" in envelope
        assert "next_steps" in envelope
        assert "open_items" in envelope
        assert "meta" in envelope
        assert envelope["meta"]["producer"] == "adr-context.py"


# ---------------------------------------------------------------------------
# TestInjectAdrs
# ---------------------------------------------------------------------------


class TestInjectAdrs:
    def test_produces_markdown_block(self, adr_mod, tmp_adr_dir: Path):
        envelope = adr_mod.inject_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        md = envelope["data"]["markdown"]
        assert "## ADR Constraints" in md
        assert "ADR-alpha" in md

    def test_each_adr_under_2kb(self, adr_mod, tmp_adr_dir: Path):
        """Each individual ADR block in the injected markdown must be ≤ 2048 chars."""
        envelope = adr_mod.inject_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py", "docs/something.md"],
            bead_description_override=None,
        )
        md: str = envelope["data"]["markdown"]
        # Split on ADR headings and check each section
        import re
        sections = re.split(r"(?=### ADR-)", md)
        for section in sections:
            if section.startswith("### ADR-"):
                assert len(section) <= 2048, f"ADR block too long ({len(section)} chars)"

    def test_empty_when_no_match(self, adr_mod, tmp_adr_dir: Path):
        """No ADRs in scope → message saying no ADRs."""
        envelope = adr_mod.inject_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["unrelated/file.ts"],
            bead_description_override=None,
        )
        md: str = envelope["data"]["markdown"]
        assert "No ADRs in scope" in md

    def test_includes_prohibitions(self, adr_mod, tmp_adr_dir: Path):
        envelope = adr_mod.inject_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        md: str = envelope["data"]["markdown"]
        assert "CommandRunner" in md

    def test_envelope_ok_status(self, adr_mod, tmp_adr_dir: Path):
        envelope = adr_mod.inject_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            bead_description_override=None,
        )
        assert envelope["status"] == "ok"


# ---------------------------------------------------------------------------
# TestVerifyAdrs
# ---------------------------------------------------------------------------


class TestVerifyAdrs:
    def test_verified_when_no_violations(self, adr_mod, tmp_adr_dir: Path):
        """Diff that doesn't contain prohibited patterns → VERIFIED."""
        diff_text = "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n@@ -1 +1 @@\n+x = 1\n"
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        assert envelope["data"]["verdict"] == "VERIFIED"
        assert envelope["data"]["violations"] == []

    def test_disputed_when_violation_found(self, adr_mod, tmp_adr_dir: Path):
        """Diff containing prohibited text → DISPUTED with violation entry."""
        diff_text = (
            "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n"
            "@@ -1 +1 @@\n"
            "+import subprocess\n"
            "+subprocess.run(['ls'])  # No direct subprocess calls without CommandRunner\n"
        )
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        assert envelope["data"]["verdict"] == "DISPUTED"
        assert len(envelope["data"]["violations"]) >= 1
        violation = envelope["data"]["violations"][0]
        assert violation["adr"] == "ADR-alpha"
        assert violation["fixability"] == "human"

    def test_rediscovers_from_diff_ignoring_caller_scope(self, adr_mod, tmp_adr_dir: Path):
        """Caller passes empty adrs_in_scope but diff touches scripts/foo.py → ADR-alpha discovered."""
        diff_text = "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n@@ -1 +1 @@\n+x = 1\n"
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],  # from diff, not from caller-provided scope
            diff_text=diff_text,
            bead_description_override=None,
        )
        discovered_ids = [a["id"] for a in envelope["data"]["discovered_adrs"]]
        assert "ADR-alpha" in discovered_ids

    def test_disputed_for_fresh_adr_discovered_from_diff(self, adr_mod, tmp_adr_dir: Path):
        """A newly relevant ADR must still dispute the diff even if caller provenance was empty."""
        fresh_adr = tmp_adr_dir / "adr_fresh.md"
        fresh_adr.write_text(
            """---
id: ADR-fresh
status: accepted
date: 2026-05-02
contract: subprocess-policy
applies_to:
  - scripts/*.py
prohibits:
  - Do not add direct subprocess.run without CommandRunner
decision_summary: "Subprocess calls must route through CommandRunner."
---

# ADR-fresh
""",
            encoding="utf-8",
        )
        diff_text = (
            "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n"
            "@@ -1 +1 @@\n"
            "+subprocess.run(['ls'])  # Do not add direct subprocess.run without CommandRunner\n"
        )
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        assert envelope["data"]["verdict"] == "DISPUTED"
        violation = next(v for v in envelope["data"]["violations"] if v["adr"] == "ADR-fresh")
        assert violation["fixability"] == "human"

    def test_discovered_adrs_structure(self, adr_mod, tmp_adr_dir: Path):
        """Each discovered_adrs entry has id, path, decision_summary."""
        diff_text = "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n@@ -1 +1 @@\n+x = 1\n"
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        for entry in envelope["data"]["discovered_adrs"]:
            assert "id" in entry
            assert "path" in entry
            assert "decision_summary" in entry

    def test_envelope_status_ok_for_verified(self, adr_mod, tmp_adr_dir: Path):
        diff_text = "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n@@ -1 +1 @@\n+x = 1\n"
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        assert envelope["status"] == "ok"

    def test_envelope_status_warning_for_disputed(self, adr_mod, tmp_adr_dir: Path):
        diff_text = (
            "--- a/scripts/foo.py\n+++ b/scripts/foo.py\n"
            "@@ -1 +1 @@\n"
            "+subprocess.run(['ls'])  # No direct subprocess calls without CommandRunner\n"
        )
        envelope = adr_mod.verify_adrs_envelope(
            adr_dir=tmp_adr_dir,
            changed_paths=["scripts/foo.py"],
            diff_text=diff_text,
            bead_description_override=None,
        )
        assert envelope["status"] == "warning"
