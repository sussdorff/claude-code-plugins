#!/usr/bin/env python3
"""
Initialize a new Claude Code slash command with proper template.

Usage:
    python3 init-command.py <command-name> [--path <output-directory>]

Examples:
    python3 init-command.py review-pr
    python3 init-command.py test-all --path .claude/commands/
"""

import argparse
import sys
from pathlib import Path


def validate_command_name(name: str) -> tuple[bool, str]:
    """
    Validate command name follows conventions.

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Command name cannot be empty"

    if "_" in name:
        return False, f"Command name '{name}' contains underscores. Use hyphens (kebab-case)"

    if name != name.lower():
        return False, f"Command name '{name}' contains uppercase. Use lowercase only"

    if " " in name:
        return False, f"Command name '{name}' contains spaces. Use hyphens"

    if not name.replace("-", "").isalnum():
        return False, f"Command name '{name}' contains invalid characters"

    if name.startswith("-") or name.endswith("-"):
        return False, f"Command name '{name}' cannot start/end with hyphen"

    if "--" in name:
        return False, f"Command name '{name}' contains consecutive hyphens"

    return True, ""


def get_command_template(name: str) -> str:
    """Generate command template content."""
    return f"""---
description: TODO: Brief, clear explanation of what this command does (1-2 sentences)
argument-hint: [TODO: expected arguments, e.g., issue-number, file-path]
allowed-tools: Read, Edit, Bash(git:*)
model: claude-3-7-sonnet-20250219
---

TODO: Replace with command instructions

Execute the following steps:

1. [TODO: First step - be specific]
2. [TODO: Second step]
3. [TODO: Third step]
4. [TODO: Final step]

Success criteria:
- [TODO: How to know this succeeded]
- [TODO: What should be true when done]

# Notes for customization:
# - Remove TODO markers
# - Update description (shows in /help)
# - Set argument-hint for auto-completion
# - Configure allowed-tools (or remove for all tools)
# - Choose model: haiku (fast), sonnet (balanced), opus (complex)
# - Remove this notes section before deploying
"""


def create_command(name: str, output_path: str) -> bool:
    """
    Create new command file with template.

    Args:
        name: Command name (kebab-case)
        output_path: Directory where command file should be created

    Returns:
        True if successful, False otherwise
    """
    # Validate name
    is_valid, error = validate_command_name(name)
    if not is_valid:
        print(f"❌ Invalid command name: {error}", file=sys.stderr)
        return False

    # Resolve output path
    if output_path:
        output_dir = Path(output_path).resolve()
    else:
        output_dir = Path.cwd() / ".claude" / "commands"

    # Create directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create command file
    command_file = output_dir / f"{name}.md"

    if command_file.exists():
        print(f"❌ Command file already exists: {command_file}", file=sys.stderr)
        print(f"   To recreate, first remove the existing file", file=sys.stderr)
        return False

    # Write template
    try:
        command_file.write_text(get_command_template(name))
        print(f"✅ Created command: {command_file}")
        print()
        print("Next steps:")
        print(f"1. Edit {command_file}")
        print("2. Replace all TODO items with actual content")
        print("3. Update frontmatter fields:")
        print("   - description: Clear explanation (shows in /help)")
        print("   - argument-hint: Expected arguments for auto-completion")
        print("   - allowed-tools: Only necessary tools (or remove for all)")
        print("   - model: haiku (fast) | sonnet (balanced) | opus (complex)")
        print("4. Write specific, numbered steps")
        print("5. Define success criteria")
        print(f"6. Test: /{name} [arguments]")
        print()
        print("💡 Tip: Commands are available immediately after saving")
        return True

    except Exception as e:
        print(f"❌ Failed to create command file: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize a new Claude Code slash command with proper template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s review-pr
  %(prog)s test-all --path .claude/commands/
  %(prog)s fix-issue --path /path/to/commands/

Command Naming Rules:
  - Use kebab-case (lowercase with hyphens)
  - Examples: review-pr, test-all, fix-issue, analyze-logs
  - Avoid: ReviewPR (PascalCase), test_all (snake_case), rp (too short)
        """
    )

    parser.add_argument(
        "name",
        help="Command name in kebab-case (e.g., review-pr, test-all)"
    )

    parser.add_argument(
        "--path",
        help="Output directory for command file (default: .claude/commands/)"
    )

    args = parser.parse_args()

    # Create command
    print(f"🚀 Initializing command: {args.name}")
    if args.path:
        print(f"   Location: {args.path}")
    else:
        print(f"   Location: .claude/commands/ (default)")
    print()

    success = create_command(args.name, args.path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
