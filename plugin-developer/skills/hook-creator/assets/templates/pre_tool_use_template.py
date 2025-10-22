#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

"""
PreToolUse Hook Template

Purpose: Validate and potentially block tool executions before they run.
Use cases: Security validation, file protection, dangerous command blocking.

This hook receives JSON on stdin with:
{
  "session_id": "...",
  "transcript_path": "...",
  "tool_name": "ToolName",
  "tool_input": { ... tool-specific parameters ... }
}

Exit codes:
  0 - Allow operation (stdout shown in transcript mode)
  2 - Block operation (stderr message shown to Claude)
  Other - Non-blocking error (shown to user)
"""

import json
import sys
import os

def validate_bash_command(command):
    """
    Validate bash commands for security issues.

    Args:
        command: The bash command to validate

    Returns:
        (is_valid, error_message) tuple
    """
    # Example: Block dangerous rm commands
    dangerous_patterns = [
        "rm -rf /",
        "rm -rf ~",
        "chmod 777",
    ]

    for pattern in dangerous_patterns:
        if pattern in command.lower():
            return False, f"Blocked dangerous command: {command}"

    return True, None

def validate_file_operation(file_path):
    """
    Validate file operations for sensitive files.

    Args:
        file_path: Path to file being accessed

    Returns:
        (is_valid, error_message) tuple
    """
    if not file_path:
        return True, None

    filename = os.path.basename(file_path)

    # Example: Protect .env files
    if filename == ".env":
        return False, f"Blocked access to sensitive file: {file_path}"

    # Example: Allow .env.sample
    if filename in [".env.sample", ".env.example"]:
        return True, None

    return True, None

def validate_tool_use(tool_name, tool_input):
    """
    Main validation logic for tool usage.

    Args:
        tool_name: Name of the tool being used
        tool_input: Dictionary of tool parameters

    Returns:
        (is_valid, error_message) tuple
    """
    # Validate Bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        return validate_bash_command(command)

    # Validate file operations
    if tool_name in ["Read", "Edit", "Write"]:
        file_path = tool_input.get("file_path", "")
        return validate_file_operation(file_path)

    # Allow all other operations
    return True, None

def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Create logs directory if needed
        log_dir = ".claude/hooks/logs"
        os.makedirs(log_dir, exist_ok=True)

        # Log all tool usage attempts (optional)
        log_file = os.path.join(log_dir, "pre_tool_use.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(input_data) + "\n")

        # Validate the tool usage
        is_valid, error_msg = validate_tool_use(tool_name, tool_input)

        if not is_valid:
            # Block the operation
            print(error_msg, file=sys.stderr)
            sys.exit(2)

        # Allow the operation
        sys.exit(0)

    except json.JSONDecodeError as e:
        # Invalid JSON - log but don't block
        print(f"Warning: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        # Unexpected error - log but don't block
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)

def test_hook():
    """
    Test this hook with sample inputs.
    Run with: uv run pre_tool_use_template.py --test
    """
    import io

    test_cases = [
        {
            "name": "Dangerous rm command",
            "input": {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"}
            },
            "expected_exit": 2,
            "description": "Should block dangerous rm -rf /"
        },
        {
            "name": "Safe command",
            "input": {
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"}
            },
            "expected_exit": 0,
            "description": "Should allow safe ls command"
        },
        {
            "name": "Sensitive file access",
            "input": {
                "tool_name": "Read",
                "tool_input": {"file_path": "/path/to/.env"}
            },
            "expected_exit": 2,
            "description": "Should block .env file access"
        },
        {
            "name": "Sample file access",
            "input": {
                "tool_name": "Read",
                "tool_input": {"file_path": "/path/to/.env.sample"}
            },
            "expected_exit": 0,
            "description": "Should allow .env.sample access"
        },
    ]

    print("Running hook tests...\n")
    passed = 0
    failed = 0

    for test in test_cases:
        # Redirect stdin
        sys.stdin = io.StringIO(json.dumps(test["input"]))

        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        # Run validation
        try:
            tool_name = test["input"]["tool_name"]
            tool_input = test["input"]["tool_input"]
            is_valid, error_msg = validate_tool_use(tool_name, tool_input)

            if is_valid:
                exit_code = 0
            else:
                exit_code = 2

            # Restore output
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Check result
            if exit_code == test["expected_exit"]:
                print(f"✓ PASS: {test['name']}")
                print(f"  {test['description']}")
                passed += 1
            else:
                print(f"✗ FAIL: {test['name']}")
                print(f"  Expected exit {test['expected_exit']}, got {exit_code}")
                print(f"  {test['description']}")
                failed += 1
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            print(f"✗ ERROR: {test['name']}")
            print(f"  {str(e)}")
            failed += 1

        print()

    # Restore stdin
    sys.stdin = sys.__stdin__

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_hook()
        sys.exit(0 if success else 1)
    else:
        main()
