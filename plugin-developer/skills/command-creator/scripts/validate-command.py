#!/usr/bin/env python3
"""
Validate Claude Code slash command structure and content.

Usage:
    python3 validate-command.py <command-file>

Examples:
    python3 validate-command.py .claude/commands/review-pr.md
    python3 validate-command.py ~/.claude/commands/test-all.md
"""

import argparse
import re
import sys
from pathlib import Path


class CommandValidator:
    """Validator for Claude Code slash command files."""

    VALID_MODELS = {
        "claude-3-5-haiku-20241022",
        "claude-3-7-sonnet-20250219",
        "claude-opus-4-20250514"
    }

    COMMON_TOOLS = {
        "Read", "Write", "Edit", "Bash", "Grep", "Glob",
        "WebFetch", "WebSearch", "Task", "Skill", "TodoWrite",
        "AskUserQuestion", "NotebookEdit"
    }

    def __init__(self, command_file: Path):
        """Initialize validator with command file path."""
        self.command_file = command_file
        self.errors = []
        self.warnings = []
        self.content = ""
        self.frontmatter = {}
        self.body = ""

    def validate(self) -> bool:
        """
        Run all validations.

        Returns:
            True if valid, False if errors found
        """
        # Check file exists
        if not self.command_file.exists():
            self.errors.append(f"Command file not found: {self.command_file}")
            return False

        # Read file
        try:
            self.content = self.command_file.read_text()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        # Run validations
        self._validate_frontmatter()
        self._validate_description()
        self._validate_allowed_tools()
        self._validate_model()
        self._validate_body()
        self._check_todos()

        return len(self.errors) == 0

    def _validate_frontmatter(self):
        """Validate YAML frontmatter exists and is properly formatted."""
        if not self.content.startswith("---\n"):
            self.errors.append("File must start with '---' (YAML frontmatter)")
            return

        # Find end of frontmatter
        end_match = re.search(r"\n---\n", self.content[4:])
        if not end_match:
            self.errors.append("Frontmatter not properly closed with '---'")
            return

        # Extract frontmatter and body
        frontmatter_end = end_match.end() + 4
        frontmatter_text = self.content[4:frontmatter_end-4]
        self.body = self.content[frontmatter_end:].strip()

        # Parse frontmatter (simple key: value parsing)
        for line in frontmatter_text.strip().split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, value = line.split(":", 1)
                self.frontmatter[key.strip()] = value.strip()

    def _validate_description(self):
        """Validate description field."""
        if "description" not in self.frontmatter:
            self.errors.append("Missing required field: description")
            return

        desc = self.frontmatter["description"]

        # Check not empty
        if not desc or "TODO" in desc:
            self.errors.append("Description is empty or contains TODO")
            return

        # Check length
        if len(desc) < 10:
            self.warnings.append("Description is very short. Be more descriptive.")

        if len(desc) > 200:
            self.warnings.append("Description is very long. Keep it concise (1-2 sentences).")

    def _validate_allowed_tools(self):
        """Validate allowed-tools field if present."""
        if "allowed-tools" not in self.frontmatter:
            self.warnings.append(
                "No allowed-tools specified. Command will have access to ALL tools. "
                "Consider restricting for security."
            )
            return

        tools_str = self.frontmatter["allowed-tools"]
        if not tools_str:
            self.warnings.append("allowed-tools field is empty")
            return

        # Parse tools
        tools = [t.strip() for t in tools_str.split(",")]

        # Check for common tool names
        for tool in tools:
            # Skip Bash patterns
            if tool.startswith("Bash("):
                continue

            if tool not in self.COMMON_TOOLS:
                self.warnings.append(f"Unusual tool '{tool}'. Verify this is correct")

    def _validate_model(self):
        """Validate model field if present."""
        if "model" not in self.frontmatter:
            return  # Optional field

        model = self.frontmatter["model"]

        if model not in self.VALID_MODELS:
            self.errors.append(
                f"Invalid or outdated model '{model}'. "
                f"Valid options: {', '.join(sorted(self.VALID_MODELS))}"
            )

    def _validate_body(self):
        """Validate command body content."""
        if not self.body:
            self.errors.append("Command body is empty. Add instructions for Claude.")
            return

        # Check for numbered lists
        has_numbered = bool(re.search(r"^\d+\.", self.body, re.MULTILINE))
        if not has_numbered:
            self.warnings.append(
                "No numbered steps found. Use numbered lists for clarity."
            )

    def _check_todos(self):
        """Check for TODO markers."""
        if "TODO" in self.content:
            todo_count = self.content.count("TODO")
            self.warnings.append(
                f"Found {todo_count} TODO marker(s). Complete these before deploying."
            )

    def print_report(self):
        """Print validation report."""
        print(f"\n{'='*60}")
        print(f"Command Validation Report: {self.command_file.name}")
        print(f"{'='*60}\n")

        if not self.errors and not self.warnings:
            print("✅ Command is valid! No errors or warnings.\n")
            return

        if self.errors:
            print(f"❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print(f"⚠️  Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        if self.errors:
            print("❌ Validation failed. Fix errors before deploying.\n")
        else:
            print("✅ No errors, but consider addressing warnings.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Claude Code slash command structure and content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .claude/commands/review-pr.md
  %(prog)s ~/.claude/commands/test-all.md

Validation Checks:
  - YAML frontmatter structure
  - Required fields (description)
  - Tool specifications
  - Model ID validity
  - Content structure
  - TODO markers
        """
    )

    parser.add_argument(
        "command_file",
        type=Path,
        help="Path to command markdown file"
    )

    args = parser.parse_args()

    # Validate
    validator = CommandValidator(args.command_file)
    is_valid = validator.validate()
    validator.print_report()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
