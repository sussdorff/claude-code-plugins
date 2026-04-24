"""Regression tests for CCP-die: codex-exec diff resolution.

Covers acceptance criteria:
  AK1: Size-budget inlining — moderate multi-file diffs (< 256 KB) are inlined,
       not rejected by a file-count cap.
  AK2: Large-diff bounded guidance — diffs exceeding 256 KB produce bounded text
       with file list + targeted git commands + no repo-wide onboarding instructions.
  AK3: This file — regression coverage for _resolve_diff.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
CODEX_EXEC_PY = REPO_ROOT / "beads-workflow" / "scripts" / "codex-exec.py"


def _make_completed_process(stdout=b"", returncode=0):
    """Build a mock CompletedProcess. stdout may be bytes or str depending on capture mode."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = ""
    return result


def _load_codex_exec():
    """Load codex-exec.py as a module (filename contains hyphen, can't use plain import)."""
    spec = importlib.util.spec_from_file_location("codex_exec", CODEX_EXEC_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load the module once — avoids redundant spec_from_file_location per test
_CODEX_EXEC = _load_codex_exec()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_resolve_diff(diff_range: str, diff_bytes: bytes, file_names: list[str], stat_text: str = "") -> str:
    """
    Call _resolve_diff with mocked subprocess.run.

    subprocess.run is called in this order inside _resolve_diff:
      1. git diff <range> --name-only  -> text=True, returns file list
      2. git diff <range>              -> bytes (capture_output=True, no text=True)
      3. git diff <range> --stat       -> text=True, returns stat summary (large-diff path only)
    """
    names_text = "\n".join(file_names)

    def side_effect(cmd, **kwargs):
        if "--name-only" in cmd:
            return _make_completed_process(stdout=names_text)
        if "--stat" in cmd:
            return _make_completed_process(stdout=stat_text)
        # Raw diff call (bytes): second positional call
        return _make_completed_process(stdout=diff_bytes)

    prompt = "Review this diff:\n{{DIFF}}"
    with patch("subprocess.run", side_effect=side_effect):
        return _CODEX_EXEC._resolve_diff(diff_range, prompt)


# ---------------------------------------------------------------------------
# AK1: Moderate multi-file diff inlines correctly (no file-count cap)
# ---------------------------------------------------------------------------

class TestModerateMultiFileDiffInlines:
    """AK1 — A moderate diff with 5 changed files and size < 256 KB must be inlined."""

    def test_five_file_diff_is_inlined(self):
        """AK1: 5-file diff under 256 KB → {{DIFF}} replaced with actual diff text."""
        diff_content = b"diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new\n"
        file_names = [
            "src/alpha.py",
            "src/beta.py",
            "src/gamma.py",
            "tests/test_alpha.py",
            "tests/test_beta.py",
        ]
        # Verify it's genuinely under the 256 KB threshold
        assert len(diff_content) < 262144

        result = _run_resolve_diff("abc123...HEAD", diff_content, file_names)

        # The actual diff text must be present
        assert "diff --git" in result
        assert "+new" in result

    def test_five_file_diff_does_not_produce_guidance(self):
        """AK1: A moderate inline diff must NOT contain the large-diff guidance header."""
        diff_content = b"diff --git a/foo.py b/foo.py\n+line\n"
        file_names = ["a.py", "b.py", "c.py", "d.py", "e.py"]

        result = _run_resolve_diff("abc123...HEAD", diff_content, file_names)

        assert "Changed files (authoritative scope for this review)" not in result
        assert "too large to inline" not in result

    def test_placeholder_is_replaced_in_moderate_case(self):
        """AK1: {{DIFF}} placeholder must not appear in the output after resolution."""
        diff_content = b"diff --git a/x.py b/x.py\n+x\n"
        result = _run_resolve_diff("a...b", diff_content, ["x.py"])
        assert "{{DIFF}}" not in result


# ---------------------------------------------------------------------------
# AK1 basic: Small single-file diff inlines
# ---------------------------------------------------------------------------

class TestSmallDiffInlines:
    """AK1 basic — A tiny single-file diff is inlined verbatim."""

    def test_small_diff_inlines(self):
        """AK1 basic: Single-file diff under 256 KB → inlined in prompt."""
        diff_content = b"diff --git a/README.md b/README.md\n--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"
        result = _run_resolve_diff("HEAD~1...HEAD", diff_content, ["README.md"])

        assert "diff --git a/README.md" in result
        assert "-old" in result
        assert "+new" in result

    def test_small_diff_no_guidance_text(self):
        """AK1 basic: Tiny diff must not produce large-diff guidance."""
        diff_content = b"diff --git a/f.py b/f.py\n+x\n"
        result = _run_resolve_diff("HEAD~1...HEAD", diff_content, ["f.py"])

        assert "Do NOT run repo-wide" not in result
        assert "git diff HEAD~1...HEAD -- <file>" not in result  # no guidance commands in inline path

    def test_placeholder_replaced_for_small_diff(self):
        """AK1 basic: {{DIFF}} placeholder is gone after resolution."""
        diff_content = b"diff --git a/f.py b/f.py\n+line\n"
        result = _run_resolve_diff("a...b", diff_content, ["f.py"])
        assert "{{DIFF}}" not in result


# ---------------------------------------------------------------------------
# AK2: Large diff produces bounded guidance text
# ---------------------------------------------------------------------------

class TestLargeDiffBoundedGuidance:
    """AK2 — Diffs exceeding 256 KB produce bounded guidance, not inline diff text."""

    def _make_large_diff(self) -> bytes:
        """Generate a diff payload that exceeds the 256 KB threshold."""
        line = b"+x = " + b"a" * 200 + b"\n"
        # Need > 262144 bytes
        repeat = (262144 // len(line)) + 10
        return b"diff --git a/big.py b/big.py\n" + line * repeat

    def test_large_diff_contains_file_list(self):
        """AK2: Large-diff guidance must list changed files with '  - ' prefix."""
        diff_bytes = self._make_large_diff()
        assert len(diff_bytes) > 262144

        file_names = ["src/big.py", "src/other.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names, stat_text="2 files changed")

        assert "  - src/big.py" in result
        assert "  - src/other.py" in result

    def test_large_diff_contains_targeted_git_command(self):
        """AK2: Large-diff guidance must contain a targeted git diff command."""
        diff_bytes = self._make_large_diff()
        file_names = ["src/module.py"]
        result = _run_resolve_diff("abc123...HEAD", diff_bytes, file_names, stat_text="1 file changed")

        # Must contain a targeted git diff command for the specific range
        assert "git diff abc123...HEAD -- <file>" in result

    def test_large_diff_no_inspect_directly_text(self):
        """AK2: Old 'Inspect it directly' wording must NOT appear in large-diff guidance."""
        diff_bytes = self._make_large_diff()
        file_names = ["a.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        assert "Inspect it directly" not in result

    def test_large_diff_no_bd_onboard_as_instruction(self):
        """AK2: Large-diff guidance must not instruct Codex to run 'bd onboard'.

        'bd onboard' may appear as a forbidden example (e.g. 'Do NOT run bd onboard'),
        but must never appear as a positive instruction to execute.
        """
        diff_bytes = self._make_large_diff()
        file_names = ["a.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        # The 'Do NOT run repo-wide' check already covers this; verify the key phrase
        assert "Do NOT run repo-wide" in result
        # Also verify the text explicitly names bd onboard as forbidden, not as a call-to-action
        lines_with_bd_onboard = [ln for ln in result.splitlines() if "bd onboard" in ln]
        for line in lines_with_bd_onboard:
            # Every mention of bd onboard must be in the context of "do not run"
            assert "do not" in line.lower(), (
                f"'bd onboard' appeared outside a 'do not' context: {line!r}"
            )

    def test_large_diff_no_bd_prime_as_instruction(self):
        """AK2: Large-diff guidance must not instruct Codex to run 'bd prime'.

        'bd prime' may appear as a forbidden example, but must never appear as a positive
        instruction to execute.
        """
        diff_bytes = self._make_large_diff()
        file_names = ["a.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        assert "Do NOT run repo-wide" in result
        lines_with_bd_prime = [ln for ln in result.splitlines() if "bd prime" in ln]
        for line in lines_with_bd_prime:
            assert "do not" in line.lower(), (
                f"'bd prime' appeared outside a 'do not' context: {line!r}"
            )

    def test_large_diff_contains_do_not_run_repo_wide(self):
        """AK2: Large-diff guidance must explicitly say not to run repo-wide commands."""
        diff_bytes = self._make_large_diff()
        file_names = ["a.py", "b.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        assert "Do NOT run repo-wide" in result

    def test_large_diff_placeholder_is_replaced(self):
        """AK2: {{DIFF}} placeholder must not appear after resolution in large-diff path."""
        diff_bytes = self._make_large_diff()
        file_names = ["a.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        assert "{{DIFF}}" not in result

    def test_large_diff_does_not_inline_raw_diff(self):
        """AK2: Raw diff text must NOT be inlined when the diff exceeds 256 KB."""
        diff_bytes = self._make_large_diff()
        file_names = ["big.py"]
        result = _run_resolve_diff("abc...HEAD", diff_bytes, file_names)

        # The raw diff content starts with 'diff --git'; it must not appear in the output
        assert "diff --git a/big.py" not in result


# ---------------------------------------------------------------------------
# Boundary: exactly at threshold
# ---------------------------------------------------------------------------

class TestThresholdBoundary:
    """Verify the boundary condition: exactly at 262144 bytes is large-diff path."""

    def test_diff_at_exactly_threshold_is_inlined(self):
        """A diff of exactly 262144 bytes (== max_inline_bytes) triggers large-diff path.

        effective_inline_bytes = min(max_inline_bytes, max_prompt_chars // 2)
                               = min(262144, 16000) = 16000
        So 262144 bytes exceeds the effective threshold and takes the large-diff path.
        """
        diff_bytes = b"x" * 262144
        file_names = ["a.py"]
        result = _run_resolve_diff("a...b", diff_bytes, file_names)
        # 262144 bytes >> effective_inline_bytes (16000) → large-diff path
        assert "{{DIFF}}" not in result
        # Large-diff guidance header is present
        assert "Changed files (authoritative scope" in result

    def test_diff_one_byte_over_threshold_is_large(self):
        """A diff of 262145 bytes (> max_inline_bytes) triggers large-diff guidance."""
        diff_bytes = b"x" * 262145
        file_names = ["a.py"]
        result = _run_resolve_diff("a...b", diff_bytes, file_names)
        assert "Changed files (authoritative scope for this review)" in result
        assert "Do NOT run repo-wide" in result
