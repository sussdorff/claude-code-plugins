#!/usr/bin/env python3
"""
Validate Claude Code agent structure and content.

Usage:
    python3 validate-agent.py <agent-file>

Examples:
    python3 validate-agent.py .claude/agents/code-reviewer.md
    python3 validate-agent.py my-agent.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


class AgentValidator:
    """Validator for Claude Code agent files."""

    VALID_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
    VALID_MODELS = {"haiku", "sonnet", "opus", "inherit"}
    COMMON_TOOLS = {
        "Read", "Write", "Edit", "Bash", "Grep", "Glob",
        "WebFetch", "WebSearch", "Task", "Skill", "TodoWrite",
        "AskUserQuestion", "NotebookEdit"
    }

    def __init__(self, agent_file: Path):
        """Initialize validator with agent file path."""
        self.agent_file = agent_file
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
        if not self.agent_file.exists():
            self.errors.append(f"Agent file not found: {self.agent_file}")
            return False

        # Read file
        try:
            self.content = self.agent_file.read_text()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        # Run validations
        self._validate_frontmatter()
        self._validate_name()
        self._validate_description()
        self._validate_tools()
        self._validate_model()
        self._validate_color()
        self._validate_body()
        self._check_token_count()
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

    def _validate_name(self):
        """Validate name field."""
        if "name" not in self.frontmatter:
            self.errors.append("Missing required field: name")
            return

        name = self.frontmatter["name"]

        # Check not empty
        if not name:
            self.errors.append("Name cannot be empty")
            return

        # Check kebab-case
        if "_" in name:
            self.errors.append(f"Name '{name}' uses underscores. Use kebab-case (hyphens)")

        if name != name.lower():
            self.errors.append(f"Name '{name}' contains uppercase. Use lowercase only")

        if " " in name:
            self.errors.append(f"Name '{name}' contains spaces. Use hyphens")

        if not name.replace("-", "").isalnum():
            self.errors.append(f"Name '{name}' contains invalid characters")

        if name.startswith("-") or name.endswith("-"):
            self.errors.append(f"Name '{name}' cannot start/end with hyphen")

        if "--" in name:
            self.errors.append(f"Name '{name}' contains consecutive hyphens")

        # Check length
        if len(name) < 3:
            self.warnings.append(f"Name '{name}' is very short. Consider more descriptive name")

        if len(name) > 50:
            self.warnings.append(f"Name '{name}' is very long. Consider shorter name")

    def _validate_description(self):
        """Validate description field."""
        if "description" not in self.frontmatter:
            self.errors.append("Missing required field: description")
            return

        desc = self.frontmatter["description"]

        # Check not empty
        if not desc or desc == "TODO" in desc:
            self.errors.append("Description is empty or contains TODO")
            return

        # Check length
        if len(desc) < 20:
            self.warnings.append("Description is very short. Be more specific for better auto-delegation")

        if len(desc) > 500:
            self.warnings.append("Description is very long. Consider multi-line YAML or being more concise")

        # Check for trigger keywords (best practices)
        trigger_keywords = ["use", "when", "proactively", "must be used", "delegate"]
        has_trigger = any(keyword in desc.lower() for keyword in trigger_keywords)
        if not has_trigger:
            self.warnings.append(
                "Description lacks trigger keywords (use, when, proactively). "
                "Add these for better auto-delegation"
            )

        # Check for vague language
        vague_words = ["helps", "stuff", "things", "agent"]
        if any(word in desc.lower() for word in vague_words):
            self.warnings.append(
                "Description contains vague words (helps, stuff, things). "
                "Be more specific about agent's purpose"
            )

    def _validate_tools(self):
        """Validate tools field if present."""
        if "tools" not in self.frontmatter:
            self.warnings.append(
                "No tools field specified. Agent will inherit ALL tools (including MCP). "
                "Consider specifying minimal required tools for security"
            )
            return

        tools_str = self.frontmatter["tools"]
        if not tools_str:
            self.warnings.append("Tools field is empty")
            return

        # Parse tools
        tools = [t.strip() for t in tools_str.split(",")]

        # Check for common typos
        for tool in tools:
            if tool not in self.COMMON_TOOLS and not tool.startswith("mcp__"):
                self.warnings.append(f"Unusual tool '{tool}'. Verify this is correct")

        # Check for excessive tools
        if len(tools) > 8:
            self.warnings.append(
                f"Many tools specified ({len(tools)}). "
                "Consider if all are necessary for focused agent design"
            )

        # Check for dangerous combinations
        if "Bash" in tools and "Write" in tools:
            self.warnings.append(
                "Agent has both Bash and Write access. "
                "Ensure agent includes safety checks for destructive operations"
            )

    def _validate_model(self):
        """Validate model field if present."""
        if "model" not in self.frontmatter:
            self.warnings.append("No model specified. Will default to 'sonnet'")
            return

        model = self.frontmatter["model"]

        if model not in self.VALID_MODELS:
            self.errors.append(
                f"Invalid model '{model}'. "
                f"Valid options: {', '.join(sorted(self.VALID_MODELS))}"
            )

        # Best practices suggestions
        if model == "opus":
            self.warnings.append(
                "Using Opus model. Ensure task requires complex reasoning. "
                "Consider Sonnet for most tasks (3x cheaper, 2x faster)"
            )

    def _validate_color(self):
        """Validate color field if present."""
        if "color" not in self.frontmatter:
            return  # Color is optional

        color = self.frontmatter["color"]

        if color not in self.VALID_COLORS:
            self.errors.append(
                f"Invalid color '{color}'. "
                f"Valid options: {', '.join(sorted(self.VALID_COLORS))}"
            )

    def _validate_body(self):
        """Validate agent body content."""
        if not self.body:
            self.errors.append("Agent body is empty. Add system prompt with instructions")
            return

        # Check for common sections
        has_purpose = "# Purpose" in self.body or "## Purpose" in self.body
        has_instructions = "## Instructions" in self.body or "# Instructions" in self.body

        if not has_purpose:
            self.warnings.append("Missing '# Purpose' section. Consider adding to clarify agent role")

        if not has_instructions:
            self.warnings.append("Missing '## Instructions' section. Add numbered steps for clarity")

        # Check for numbered lists (best practice)
        has_numbered_list = bool(re.search(r"^\d+\.", self.body, re.MULTILINE))
        if not has_numbered_list:
            self.warnings.append(
                "No numbered lists found. Use numbered steps in Instructions for clarity"
            )

    def _check_token_count(self):
        """Estimate token count and warn if excessive."""
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = len(self.body) // 4

        if estimated_tokens > 3000:
            self.warnings.append(
                f"System prompt is large (~{estimated_tokens} tokens). "
                "Consider keeping under 3k tokens for better performance. "
                "Move detailed docs to references/"
            )
        elif estimated_tokens > 10000:
            self.errors.append(
                f"System prompt is very large (~{estimated_tokens} tokens). "
                "This will create bottlenecks. Move content to references/ or split into multiple agents"
            )

    def _check_todos(self):
        """Check for TODO markers."""
        if "TODO" in self.body:
            todo_count = self.body.count("TODO")
            self.warnings.append(
                f"Found {todo_count} TODO marker(s). Complete these before deploying agent"
            )

    def print_report(self):
        """Print validation report."""
        print(f"\n{'='*60}")
        print(f"Agent Validation Report: {self.agent_file.name}")
        print(f"{'='*60}\n")

        if not self.errors and not self.warnings:
            print("✅ Agent is valid! No errors or warnings.\n")
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
            print("✅ No errors, but consider addressing warnings for best practices.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Claude Code agent structure and content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .claude/agents/code-reviewer.md
  %(prog)s my-agent.md

Validation Checks:
  - YAML frontmatter structure
  - Required fields (name, description)
  - Name format (kebab-case)
  - Description quality (trigger keywords)
  - Tool permissions
  - Model selection
  - Color validity
  - System prompt structure
  - Token count estimates
  - TODO markers
        """
    )

    parser.add_argument(
        "agent_file",
        type=Path,
        help="Path to agent markdown file"
    )

    args = parser.parse_args()

    # Validate
    validator = AgentValidator(args.agent_file)
    is_valid = validator.validate()
    validator.print_report()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
