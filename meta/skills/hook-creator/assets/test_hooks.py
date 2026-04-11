#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pytest>=8.0"
# ]
# ///
"""
Automated Hook Testing Framework

This script tests Claude Code hooks to ensure they behave correctly.
It validates security patterns, exit codes, and integration with settings.json.

Usage:
    uv run test_hooks.py                    # Run all tests
    uv run test_hooks.py -k pre_tool_use    # Test specific hook type
    uv run test_hooks.py --help             # Show help
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def run_hook(hook_script: Path, test_input: Dict[str, Any]) -> int:
    """
    Run a hook script with test input and return exit code.

    Args:
        hook_script: Path to the hook script
        test_input: Dictionary to pass as JSON input to hook

    Returns:
        Exit code from the hook script
    """
    if not hook_script.exists():
        pytest.fail(f"Hook script not found: {hook_script}")

    input_json = json.dumps(test_input)

    try:
        result = subprocess.run(
            ["uv", "run", str(hook_script)],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        pytest.fail(f"Hook timed out: {hook_script}")
    except FileNotFoundError:
        pytest.fail("uv not found. Please install uv: https://github.com/astral-sh/uv")


@pytest.fixture
def hook_dir() -> Path:
    """Get the .claude/hooks directory."""
    return Path.cwd() / ".claude" / "hooks"


# ============================================================================
# PreToolUse Hook Tests
# ============================================================================

class TestPreToolUseHook:
    """Test PreToolUse hook security validations."""

    @pytest.fixture
    def hook_script(self, hook_dir: Path) -> Path:
        """Path to PreToolUse hook script."""
        return hook_dir / "pre_tool_use.py"

    @pytest.mark.parametrize("command,expected_exit,description", [
        ("rm -rf /", 2, "Should block 'rm -rf /'"),
        ("rm -rf ~", 2, "Should block 'rm -rf ~'"),
        ("rm -rf *", 2, "Should block 'rm -rf *'"),
        ("rm -rf /var", 2, "Should block dangerous rm operations"),
        ("chmod 777 file.sh", 2, "Should block 'chmod 777'"),
    ])
    def test_dangerous_bash_commands(
        self,
        hook_script: Path,
        command: str,
        expected_exit: int,
        description: str
    ):
        """Test that dangerous bash commands are blocked."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "tool_name": "Bash",
            "tool_input": {"command": command}
        }

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == expected_exit, f"{description} (expected {expected_exit}, got {exit_code})"

    @pytest.mark.parametrize("command,expected_exit,description", [
        ("ls -la", 0, "Should allow 'ls -la'"),
        ("mkdir test", 0, "Should allow 'mkdir test'"),
        ("chmod 755 file.sh", 0, "Should allow 'chmod 755'"),
        ("git status", 0, "Should allow git commands"),
        ("python script.py", 0, "Should allow safe commands"),
    ])
    def test_safe_bash_commands(
        self,
        hook_script: Path,
        command: str,
        expected_exit: int,
        description: str
    ):
        """Test that safe bash commands are allowed."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "tool_name": "Bash",
            "tool_input": {"command": command}
        }

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == expected_exit, f"{description} (expected {expected_exit}, got {exit_code})"

    @pytest.mark.parametrize("file_path,expected_exit,description", [
        ("/path/to/.env", 2, "Should block access to .env file"),
        ("/path/to/.env.local", 2, "Should block access to .env.local"),
        ("/path/to/secrets.json", 2, "Should block access to secrets file"),
        ("/path/to/credentials.json", 2, "Should block access to credentials"),
    ])
    def test_sensitive_file_access_blocked(
        self,
        hook_script: Path,
        file_path: str,
        expected_exit: int,
        description: str
    ):
        """Test that access to sensitive files is blocked."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "tool_name": "Read",
            "tool_input": {"file_path": file_path}
        }

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == expected_exit, f"{description} (expected {expected_exit}, got {exit_code})"

    @pytest.mark.parametrize("file_path,expected_exit,description", [
        ("/path/to/.env.sample", 0, "Should allow access to .env.sample"),
        ("/path/to/.env.example", 0, "Should allow access to .env.example"),
        ("/path/to/regular.txt", 0, "Should allow access to regular files"),
        ("/path/to/README.md", 0, "Should allow access to documentation"),
    ])
    def test_safe_file_access_allowed(
        self,
        hook_script: Path,
        file_path: str,
        expected_exit: int,
        description: str
    ):
        """Test that access to safe files is allowed."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "tool_name": "Read",
            "tool_input": {"file_path": file_path}
        }

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == expected_exit, f"{description} (expected {expected_exit}, got {exit_code})"


# ============================================================================
# PostToolUse Hook Tests
# ============================================================================

class TestPostToolUseHook:
    """Test PostToolUse hook behavior."""

    @pytest.fixture
    def hook_script(self, hook_dir: Path) -> Path:
        """Path to PostToolUse hook script."""
        return hook_dir / "post_tool_use.py"

    def test_post_hooks_never_block(self, hook_script: Path):
        """PostToolUse hooks should never block (exit 0 or 1, never 2)."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_cases = [
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/tmp/test.py"},
                "tool_output": {}
            },
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/test.js"},
                "tool_output": {}
            },
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/tmp/test.txt"},
                "tool_output": {}
            },
        ]

        for test_input in test_cases:
            exit_code = run_hook(hook_script, test_input)
            assert exit_code in (0, 1), f"PostToolUse should never block (got exit {exit_code})"

    @pytest.mark.parametrize("file_path,description", [
        ("/tmp/test.py", "Should process Python file edit"),
        ("/tmp/test.js", "Should process JavaScript file write"),
        ("/tmp/test.ts", "Should process TypeScript file"),
        ("/tmp/test.txt", "Should handle non-code files"),
    ])
    def test_file_processing(
        self,
        hook_script: Path,
        file_path: str,
        description: str
    ):
        """Test that PostToolUse processes various file types."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
            "tool_output": {}
        }

        exit_code = run_hook(hook_script, test_input)
        # PostToolUse should be non-blocking
        assert exit_code in (0, 1), description


# ============================================================================
# SessionStart Hook Tests
# ============================================================================

class TestSessionStartHook:
    """Test SessionStart hook initialization."""

    @pytest.fixture
    def hook_script(self, hook_dir: Path) -> Path:
        """Path to SessionStart hook script."""
        return hook_dir / "session_start.py"

    def test_session_initialization(self, hook_script: Path):
        """SessionStart should always succeed (exit 0)."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.jsonl"
        }

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == 0, "SessionStart should always succeed"

    def test_empty_input_handling(self, hook_script: Path):
        """SessionStart should handle empty input gracefully."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {}

        exit_code = run_hook(hook_script, test_input)
        assert exit_code == 0, "SessionStart should handle empty input"


# ============================================================================
# Stop Hook Tests
# ============================================================================

class TestStopHook:
    """Test Stop hook validation."""

    @pytest.fixture
    def hook_script(self, hook_dir: Path) -> Path:
        """Path to Stop hook script."""
        return hook_dir / "stop.py"

    def test_stop_validation(self, hook_script: Path):
        """Test that Stop hook runs validation."""
        if not hook_script.exists():
            pytest.skip(f"Hook not found: {hook_script}")

        test_input = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.jsonl"
        }

        exit_code = run_hook(hook_script, test_input)
        # Stop hook may pass or fail depending on project state
        # Just verify it runs without crashing
        assert exit_code in (0, 1, 2), "Stop hook should exit with valid code"


# ============================================================================
# Settings Validation Tests
# ============================================================================

class TestSettingsValidation:
    """Test settings.json validation."""

    @pytest.mark.parametrize("settings_path", [
        ".claude/settings.json",
        Path.home() / ".claude" / "settings.json",
    ])
    def test_settings_json_valid(self, settings_path: Path):
        """Test that settings.json files are valid JSON."""
        if not isinstance(settings_path, Path):
            settings_path = Path(settings_path)

        if not settings_path.exists():
            pytest.skip(f"Settings file not found: {settings_path}")

        try:
            with open(settings_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {settings_path}: {e}")


# ============================================================================
# Template Tests
# ============================================================================

class TestTemplateScripts:
    """Test hook template scripts."""

    @pytest.fixture
    def templates_dir(self) -> Path:
        """Path to templates directory."""
        # Adjust path based on where test is run from
        templates = Path("assets/templates")
        if not templates.exists():
            templates = Path("plugin-developer/skills/hook-creator/assets/templates")
        return templates

    @pytest.mark.parametrize("template_name", [
        "pre_tool_use_template.py",
        "post_tool_use_template.py",
        "session_start_template.py",
        "stop_template.py",
    ])
    def test_template_has_test_mode(self, templates_dir: Path, template_name: str):
        """Test that templates have --test mode implemented."""
        template_path = templates_dir / template_name

        if not template_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        # Check if template has test_hook function
        with open(template_path) as f:
            content = f.read()
            assert "def test_hook" in content, f"{template_name} missing test_hook function"

    @pytest.mark.parametrize("template_name", [
        "pre_tool_use_template.py",
        "post_tool_use_template.py",
        "session_start_template.py",
        "stop_template.py",
    ])
    def test_template_test_mode_runs(self, templates_dir: Path, template_name: str):
        """Test that template test mode executes successfully."""
        template_path = templates_dir / template_name

        if not template_path.exists():
            pytest.skip(f"Template not found: {template_path}")

        try:
            result = subprocess.run(
                ["uv", "run", str(template_path), "--test"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Test mode should not crash
            assert result.returncode in (0, 1), f"{template_name} test mode failed"
        except subprocess.TimeoutExpired:
            pytest.fail(f"{template_name} test mode timed out")
        except FileNotFoundError:
            pytest.skip("uv not found")


# ============================================================================
# Hook Manager Tests
# ============================================================================

class TestHookManager:
    """Test hook manager script functionality."""

    @pytest.fixture
    def hook_manager(self) -> Path:
        """Path to hook manager script."""
        manager = Path("scripts/hook_manager.py")
        if not manager.exists():
            manager = Path("plugin-developer/skills/hook-creator/scripts/hook_manager.py")
        return manager

    def test_list_command(self, hook_manager: Path):
        """Test that hook manager list command works."""
        if not hook_manager.exists():
            pytest.skip(f"Hook manager not found: {hook_manager}")

        try:
            result = subprocess.run(
                ["uv", "run", str(hook_manager), "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, "Hook manager list command should succeed"
        except subprocess.TimeoutExpired:
            pytest.fail("Hook manager list timed out")
        except FileNotFoundError:
            pytest.skip("uv not found")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for running tests."""
    # Run pytest with nice formatting
    pytest_args = [
        __file__,
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
    ] + sys.argv[1:]  # Pass through any command line args

    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
