#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

"""
SessionStart Hook Template

Purpose: Initialize session context and load environment information.
Use cases: Load git status, set up workspace, load project context.

This hook receives JSON on stdin with:
{
  "session_id": "...",
  "transcript_path": "..."
}

Special: Has access to CLAUDE_ENV_FILE for persisting environment variables.

Exit codes:
  0 - Success (stdout shown to Claude as context)
  Non-zero - Error (shown to user, does not block session)
"""

import json
import sys
import os
import subprocess

def run_command(cmd, timeout=5):
    """
    Run a shell command and return output.

    Args:
        cmd: Command to run (list or string)
        timeout: Timeout in seconds

    Returns:
        (success, stdout, stderr) tuple
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def get_git_info():
    """
    Gather git repository information.

    Returns:
        Dictionary with git info
    """
    info = {}

    # Current branch
    success, stdout, _ = run_command(["git", "branch", "--show-current"])
    if success and stdout:
        info["branch"] = stdout

    # Git status
    success, stdout, _ = run_command(["git", "status", "--short"])
    if success and stdout:
        info["status"] = stdout

    # Recent commits
    success, stdout, _ = run_command(["git", "log", "--oneline", "-5"])
    if success and stdout:
        info["commits"] = stdout

    # Uncommitted changes count
    success, stdout, _ = run_command(["git", "diff", "--shortstat"])
    if success and stdout:
        info["diff_stat"] = stdout

    return info

def get_project_info():
    """
    Gather project-specific information.

    Returns:
        Dictionary with project info
    """
    info = {}

    # Check for package.json (Node.js project)
    if os.path.exists("package.json"):
        info["type"] = "Node.js"
        with open("package.json") as f:
            data = json.load(f)
            info["name"] = data.get("name", "Unknown")
            info["version"] = data.get("version", "Unknown")

    # Check for pyproject.toml (Python project)
    elif os.path.exists("pyproject.toml"):
        info["type"] = "Python"

    # Check for Cargo.toml (Rust project)
    elif os.path.exists("Cargo.toml"):
        info["type"] = "Rust"

    # Check for go.mod (Go project)
    elif os.path.exists("go.mod"):
        info["type"] = "Go"

    return info

def load_context_files():
    """
    Load important context files for the project.

    Returns:
        List of important file paths or contents
    """
    context = []

    # Common important files
    important_files = [
        "README.md",
        "CONTRIBUTING.md",
        ".claude/CLAUDE.md",
        "TODO.md",
    ]

    for filepath in important_files:
        if os.path.exists(filepath):
            context.append(f"Found: {filepath}")

    return context

def format_context_message(git_info, project_info, context_files):
    """
    Format context information into a message for Claude.

    Args:
        git_info: Dictionary of git information
        project_info: Dictionary of project information
        context_files: List of context file information

    Returns:
        Formatted message string
    """
    lines = []

    # Project info
    if project_info:
        lines.append("=== Project Information ===")
        if "name" in project_info:
            lines.append(f"Name: {project_info['name']}")
        if "type" in project_info:
            lines.append(f"Type: {project_info['type']}")
        if "version" in project_info:
            lines.append(f"Version: {project_info['version']}")
        lines.append("")

    # Git info
    if git_info:
        lines.append("=== Git Status ===")
        if "branch" in git_info:
            lines.append(f"Branch: {git_info['branch']}")
        if "status" in git_info and git_info["status"]:
            lines.append(f"\nModified files:\n{git_info['status']}")
        if "diff_stat" in git_info:
            lines.append(f"\nChanges: {git_info['diff_stat']}")
        if "commits" in git_info:
            lines.append(f"\nRecent commits:\n{git_info['commits']}")
        lines.append("")

    # Context files
    if context_files:
        lines.append("=== Available Context ===")
        for ctx in context_files:
            lines.append(ctx)
        lines.append("")

    return "\n".join(lines)

def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        session_id = input_data.get("session_id", "")

        # Gather context information
        git_info = get_git_info()
        project_info = get_project_info()
        context_files = load_context_files()

        # Format and output context
        context_message = format_context_message(git_info, project_info, context_files)

        if context_message:
            print(context_message)

        # Optionally persist environment variables via CLAUDE_ENV_FILE
        env_file = os.environ.get("CLAUDE_ENV_FILE")
        if env_file:
            with open(env_file, "a") as f:
                f.write(f"SESSION_ID={session_id}\n")
                if "branch" in git_info:
                    f.write(f"GIT_BRANCH={git_info['branch']}\n")

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)

def test_hook():
    """
    Test this hook with sample inputs.
    Run with: uv run session_start_template.py --test
    """
    print("Testing SessionStart hook...\n")

    # Test git info gathering
    print("Testing git info gathering:")
    git_info = get_git_info()
    if git_info:
        for key, value in git_info.items():
            preview = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✓ {key}: {preview}")
    else:
        print("  ⚠ No git repository found (this is okay for non-git projects)")
    print()

    # Test project info gathering
    print("Testing project info gathering:")
    project_info = get_project_info()
    if project_info:
        for key, value in project_info.items():
            print(f"  ✓ {key}: {value}")
    else:
        print("  ⚠ No recognized project files found")
    print()

    # Test context files discovery
    print("Testing context files discovery:")
    context_files = load_context_files()
    if context_files:
        for ctx in context_files:
            print(f"  ✓ {ctx}")
    else:
        print("  ⚠ No context files found")
    print()

    # Test formatted output
    print("Testing formatted context message:")
    print("-" * 60)
    context_message = format_context_message(git_info, project_info, context_files)
    if context_message:
        print(context_message)
    else:
        print("  ⚠ No context generated")
    print("-" * 60)
    print()

    print("Test run complete.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_hook()
        sys.exit(0 if success else 1)
    else:
        main()
