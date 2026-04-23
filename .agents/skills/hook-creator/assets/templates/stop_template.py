#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

"""
Stop Hook Template

Purpose: Validate completion criteria before allowing Claude to stop.
Use cases: Ensure tests pass, validate deliverables, enforce quality gates.

This hook receives JSON on stdin with:
{
  "session_id": "...",
  "transcript_path": "..."
}

Exit codes:
  0 - Allow stopping (stdout shown in transcript mode)
  2 - Block stopping, force Claude to continue (stderr shown to Claude)
  Other - Error (shown to user, does not block)
"""

import json
import sys
import os
import subprocess

def run_tests():
    """
    Run the project test suite.

    Returns:
        (success, output) tuple
    """
    # Detect test command based on project type
    test_commands = [
        ["npm", "test"],
        ["pytest"],
        ["go", "test", "./..."],
        ["cargo", "test"],
    ]

    for cmd in test_commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Command exists, return result
            return result.returncode == 0, result.stdout, result.stderr
        except FileNotFoundError:
            # Command not found, try next
            continue
        except subprocess.TimeoutExpired:
            return False, "", "Tests timed out after 60 seconds"
        except Exception as e:
            return False, "", str(e)

    # No test command found
    return True, "No test command found, skipping validation", ""

def run_build():
    """
    Run the project build.

    Returns:
        (success, output) tuple
    """
    # Detect build command based on project type
    build_commands = [
        ["npm", "run", "build"],
        ["yarn", "build"],
        ["make"],
        ["cargo", "build"],
        ["go", "build"],
    ]

    for cmd in build_commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            # Command exists, return result
            return result.returncode == 0, result.stdout, result.stderr
        except FileNotFoundError:
            # Command not found, try next
            continue
        except subprocess.TimeoutExpired:
            return False, "", "Build timed out after 120 seconds"
        except Exception as e:
            return False, "", str(e)

    # No build command found
    return True, "No build command found, skipping validation", ""

def check_todos():
    """
    Check if there are unresolved TODOs in recently modified files.

    Returns:
        (success, message) tuple
    """
    try:
        # Get modified files from git
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return True, "Cannot check TODOs (not a git repo)"

        modified_files = result.stdout.strip().split("\n")

        # Search for TODO comments in modified files
        todos_found = []
        for filepath in modified_files:
            if not os.path.exists(filepath):
                continue

            try:
                with open(filepath, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        if "TODO" in line or "FIXME" in line:
                            todos_found.append(f"{filepath}:{line_num}: {line.strip()}")
            except:
                continue

        if todos_found:
            message = "Found unresolved TODOs in modified files:\n" + "\n".join(todos_found[:10])
            if len(todos_found) > 10:
                message += f"\n... and {len(todos_found) - 10} more"
            return False, message

        return True, "No unresolved TODOs found"

    except Exception as e:
        return True, f"Cannot check TODOs: {e}"

def validate_completion():
    """
    Main validation logic for completion criteria.

    Returns:
        (can_complete, message) tuple
    """
    validations = []

    # Run tests
    test_success, test_stdout, test_stderr = run_tests()
    if not test_success:
        msg = "Tests are failing. Please fix the failing tests before completing."
        if test_stderr:
            msg += f"\n\nError output:\n{test_stderr[:500]}"
        return False, msg

    validations.append("✓ Tests passed")

    # Check build (optional - comment out if not needed)
    # build_success, build_stdout, build_stderr = run_build()
    # if not build_success:
    #     msg = "Build is failing. Please fix build errors before completing."
    #     if build_stderr:
    #         msg += f"\n\nError output:\n{build_stderr[:500]}"
    #     return False, msg
    # validations.append("✓ Build succeeded")

    # Check TODOs (optional - comment out if not needed)
    # todo_success, todo_msg = check_todos()
    # if not todo_success:
    #     return False, todo_msg
    # validations.append("✓ No unresolved TODOs")

    # All validations passed
    summary = "\n".join(validations)
    return True, f"Completion criteria met:\n{summary}"

def main():
    try:
        # Read JSON input from stdin (may not be used in simple cases)
        try:
            input_data = json.loads(sys.stdin.read())
        except:
            input_data = {}

        # Validate completion criteria
        can_complete, message = validate_completion()

        if not can_complete:
            # Block completion
            print(message, file=sys.stderr)
            sys.exit(2)

        # Allow completion
        if message:
            print(message)
        sys.exit(0)

    except Exception as e:
        # On error, allow completion but log the error
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(0)

def test_hook():
    """
    Test this hook with sample validations.
    Run with: uv run stop_template.py --test
    """
    print("Testing Stop hook...\n")

    # Test test runner detection
    print("Testing test command detection:")
    test_success, test_stdout, test_stderr = run_tests()
    if test_success:
        print(f"  ✓ Tests: {test_stdout[:100]}")
    else:
        print(f"  ✗ Tests failed: {test_stderr[:100]}")
    print()

    # Test build detection (optional)
    print("Testing build command detection:")
    build_success, build_stdout, build_stderr = run_build()
    if build_success:
        print(f"  ✓ Build: {build_stdout[:100]}")
    else:
        print(f"  ⚠ Build: {build_stderr[:100]}")
    print()

    # Test TODO checking
    print("Testing TODO detection:")
    todo_success, todo_msg = check_todos()
    if todo_success:
        print(f"  ✓ {todo_msg}")
    else:
        print(f"  ⚠ {todo_msg}")
    print()

    # Test overall validation
    print("Testing completion validation:")
    can_complete, message = validate_completion()
    if can_complete:
        print(f"  ✓ Can complete: {message}")
    else:
        print(f"  ✗ Cannot complete: {message}")
    print()

    print("Test run complete.")
    print("\nNote: Customize validate_completion() to enable/disable specific checks.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = test_hook()
        sys.exit(0 if success else 1)
    else:
        main()
