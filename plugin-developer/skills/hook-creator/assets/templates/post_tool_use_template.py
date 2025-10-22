#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

"""
PostToolUse Hook Template

Purpose: Process results after tool execution completes.
Use cases: Auto-formatting, linting, logging, triggering follow-up actions.

This hook receives JSON on stdin with:
{
  "session_id": "...",
  "transcript_path": "...",
  "tool_name": "ToolName",
  "tool_input": { ... tool-specific parameters ... },
  "tool_output": { ... tool execution results ... }
}

Exit codes:
  0 - Success (stdout shown in transcript mode)
  Non-zero - Error (shown to user, does not block)

Note: PostToolUse hooks cannot block operations (already completed).
"""

import json
import sys
import os
import subprocess

def format_file(file_path):
    """
    Auto-format a file based on its extension.

    Args:
        file_path: Path to file to format

    Returns:
        (success, message) tuple
    """
    if not file_path or not os.path.exists(file_path):
        return False, "File not found"

    ext = os.path.splitext(file_path)[1]

    formatters = {
        ".js": ["npx", "prettier", "--write", file_path],
        ".jsx": ["npx", "prettier", "--write", file_path],
        ".ts": ["npx", "prettier", "--write", file_path],
        ".tsx": ["npx", "prettier", "--write", file_path],
        ".py": ["black", file_path],
        ".go": ["gofmt", "-w", file_path],
    }

    if ext not in formatters:
        return True, f"No formatter configured for {ext}"

    try:
        result = subprocess.run(
            formatters[ext],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, f"Formatted: {file_path}"
        else:
            return False, f"Format error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Formatter timed out"
    except FileNotFoundError:
        return False, f"Formatter not found for {ext}"
    except Exception as e:
        return False, f"Format error: {e}"

def lint_file(file_path):
    """
    Lint a file and provide feedback.

    Args:
        file_path: Path to file to lint

    Returns:
        (success, message) tuple
    """
    if not file_path or not os.path.exists(file_path):
        return False, "File not found"

    ext = os.path.splitext(file_path)[1]

    linters = {
        ".js": ["npx", "eslint", file_path],
        ".jsx": ["npx", "eslint", file_path],
        ".ts": ["npx", "eslint", file_path],
        ".tsx": ["npx", "eslint", file_path],
        ".py": ["pylint", file_path],
    }

    if ext not in linters:
        return True, f"No linter configured for {ext}"

    try:
        result = subprocess.run(
            linters[ext],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Note: Linters often return non-zero for warnings
        if result.stdout:
            return True, result.stdout
        return True, f"Linting passed for {file_path}"
    except subprocess.TimeoutExpired:
        return False, "Linter timed out"
    except FileNotFoundError:
        return False, f"Linter not found for {ext}"
    except Exception as e:
        return False, f"Lint error: {e}"

def process_tool_output(tool_name, tool_input, tool_output):
    """
    Main logic for processing tool output.

    Args:
        tool_name: Name of the tool that was used
        tool_input: Dictionary of tool parameters
        tool_output: Dictionary of tool results

    Returns:
        (success, message) tuple
    """
    # Process Edit and Write tools
    if tool_name in ["Edit", "Write"]:
        file_path = tool_input.get("file_path", "")

        # Auto-format the file
        success, msg = format_file(file_path)
        if not success:
            return False, msg

        # Optionally lint the file
        # success, msg = lint_file(file_path)
        # return success, msg

        return True, f"Processed: {file_path}"

    # Other tools - no processing needed
    return True, None

def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_output = input_data.get("tool_output", {})

        # Create logs directory if needed
        log_dir = ".claude/hooks/logs"
        os.makedirs(log_dir, exist_ok=True)

        # Log tool usage (optional)
        log_file = os.path.join(log_dir, "post_tool_use.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "tool_name": tool_name,
                "tool_input": tool_input
            }) + "\n")

        # Process the tool output
        success, message = process_tool_output(tool_name, tool_input, tool_output)

        if message:
            print(message)

        sys.exit(0 if success else 1)

    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)

def test_hook():
    """
    Test this hook with sample inputs.
    Run with: uv run post_tool_use_template.py --test
    """
    import tempfile

    test_cases = [
        {
            "name": "Format Python file",
            "input": {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/tmp/test.py"},
                "tool_output": {}
            },
            "description": "Should attempt to format Python file with black"
        },
        {
            "name": "Format JavaScript file",
            "input": {
                "tool_name": "Write",
                "tool_input": {"file_path": "/tmp/test.js"},
                "tool_output": {}
            },
            "description": "Should attempt to format JS file with prettier"
        },
        {
            "name": "Non-code file",
            "input": {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/tmp/test.txt"},
                "tool_output": {}
            },
            "description": "Should skip formatting for non-code files"
        },
    ]

    print("Running hook tests...\n")
    print("Note: These tests may fail if formatters (black, prettier) are not installed.")
    print("Tests will show expected behavior even if formatters are missing.\n")

    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"  {test['description']}")

        tool_name = test["input"]["tool_name"]
        tool_input = test["input"]["tool_input"]
        tool_output = test["input"]["tool_output"]

        # Create a temporary file for testing
        file_path = tool_input["file_path"]
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Create test file with sample content
            with open(file_path, "w") as f:
                if file_path.endswith(".py"):
                    f.write("def hello():\n    print('hello')\n")
                elif file_path.endswith(".js"):
                    f.write("function hello() { console.log('hello'); }\n")
                else:
                    f.write("Hello world\n")

            # Run the formatter
            success, message = process_tool_output(tool_name, tool_input, tool_output)

            if success:
                print(f"  ✓ Result: {message}")
            else:
                print(f"  ⚠ Result: {message}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
        finally:
            # Clean up test file
            if os.path.exists(file_path):
                os.remove(file_path)

        print()

    print("Test run complete.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_hook()
        sys.exit(0 if success else 1)
    else:
        main()
