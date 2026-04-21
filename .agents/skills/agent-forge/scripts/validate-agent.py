#!/usr/bin/env python3
"""
Validate Claude Code agent structure and content.

Usage:
    python3 validate-agent.py <agent-path>

Claude Code only supports single-file .md agents with YAML frontmatter.
Split format (directory with agent.yml + prompt.md) is also accepted for
validation but is not supported by Claude Code itself.

Examples:
    python3 validate-agent.py .claude/agents/my-agent.md
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
        "WebFetch", "WebSearch", "Agent", "Skill",
        "AskUserQuestion", "NotebookEdit"
    }
    QUALITY_GATE_SECTIONS = [
        (r"##\s+Pre-flight(\s+Checklist)?", "Pre-flight Checklist"),
        (r"##\s+Responsibility", "Responsibility"),
        (r"##\s+[Vv][Ee][Rr][Ii][Ff][Yy]", "VERIFY"),
        (r"##\s+[Ll][Ee][Aa][Rr][Nn]", "LEARN"),
    ]

    def __init__(self, agent_path: Path, strict: bool = False):
        """Initialize validator with agent path (file or directory)."""
        self.agent_path = agent_path
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.frontmatter = {}
        self.body = ""
        self.is_split = False
        self.display_name = ""

    def validate(self) -> bool:
        """
        Run all validations.

        Returns:
            True if valid, False if errors found
        """
        # Determine format and load content
        if not self._load_agent():
            return False

        # Run validations
        self._validate_name()
        self._validate_description()
        self._validate_tools()
        self._validate_model()
        self._validate_color()
        self._validate_body()
        self._check_token_count()
        self._check_todos()

        return len(self.errors) == 0

    def _load_agent(self) -> bool:
        """Detect format and load agent content. Returns False on fatal errors."""
        path = self.agent_path

        # Case 1: Directory -> split format
        if path.is_dir():
            return self._load_split(path)

        # Case 2: agent.yml file -> split format (look for sibling prompt.md)
        if path.name == "agent.yml" and path.is_file():
            return self._load_split(path.parent)

        # Case 3: .md file -> single file (legacy)
        if path.suffix == ".md" and path.is_file():
            return self._load_single(path)

        # Case 4: Path doesn't exist
        if not path.exists():
            self.errors.append(f"Path not found: {path}")
            return False

        self.errors.append(f"Unrecognized input: {path}. Provide a directory, agent.yml, or .md file")
        return False

    def _load_split(self, agent_dir: Path) -> bool:
        """Load split format (agent.yml + prompt.md)."""
        self.is_split = True
        self.display_name = agent_dir.name

        yml_file = agent_dir / "agent.yml"
        prompt_file = agent_dir / "prompt.md"

        if not yml_file.exists():
            self.errors.append(f"Missing agent.yml in {agent_dir}")
            return False

        if not prompt_file.exists():
            self.errors.append(f"Missing prompt.md in {agent_dir}")
            return False

        # Parse agent.yml (simple key: value, no yaml library)
        try:
            yml_text = yml_file.read_text()
        except Exception as e:
            self.errors.append(f"Failed to read {yml_file}: {e}")
            return False

        for line in yml_text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                val = value.strip()
                # Strip surrounding quotes if present
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                self.frontmatter[key.strip()] = val

        # Read prompt.md as body
        try:
            self.body = prompt_file.read_text().strip()
        except Exception as e:
            self.errors.append(f"Failed to read {prompt_file}: {e}")
            return False

        return True

    def _load_single(self, agent_file: Path) -> bool:
        """Load single-file format (.md with frontmatter)."""
        self.is_split = False
        self.display_name = agent_file.name

        try:
            content = agent_file.read_text()
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False

        # Validate frontmatter
        if not content.startswith("---\n"):
            self.errors.append("File must start with '---' (YAML frontmatter)")
            return False

        end_match = re.search(r"\n---\n", content[4:])
        if not end_match:
            self.errors.append("Frontmatter not properly closed with '---'")
            return False

        frontmatter_end = end_match.end() + 4
        frontmatter_text = content[4:frontmatter_end-4]
        self.body = content[frontmatter_end:].strip()

        # Parse frontmatter (simple key: value parsing)
        for line in frontmatter_text.strip().split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, value = line.split(":", 1)
                self.frontmatter[key.strip()] = value.strip()

        return True

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
            self.warnings.append("No model specified. Will default to 'inherit' (caller's model). Set explicitly to avoid surprises")
            return

        model = self.frontmatter["model"]

        if model not in self.VALID_MODELS:
            self.errors.append(
                f"Invalid model '{model}'. "
                f"Valid options: {', '.join(sorted(self.VALID_MODELS))}"
            )

        # Best practices suggestions
        if model == "haiku":
            self.warnings.append(
                "Using Haiku model. Confirm the task is truly routine/deterministic. "
                "Start with opus and downgrade only after verifying quality"
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

        # Quality Gate sections (mandatory)
        for pattern, section_name in self.QUALITY_GATE_SECTIONS:
            if not re.search(pattern, self.body):
                msg = (
                    f"Missing '## {section_name}' quality gate section. "
                    "See agent-quality-gates standard"
                )
                if self.strict:
                    self.errors.append(msg)
                else:
                    self.warnings.append(msg)

    def _check_token_count(self):
        """Estimate token count and warn if excessive."""
        # Rough estimate: 1 token ~ 4 characters
        estimated_tokens = len(self.body) // 4

        if estimated_tokens > 10000:
            self.errors.append(
                f"System prompt is very large (~{estimated_tokens} tokens). "
                "This will create bottlenecks. Move content to references/ or split into multiple agents"
            )
        elif estimated_tokens > 3000:
            self.warnings.append(
                f"System prompt is large (~{estimated_tokens} tokens). "
                "Consider keeping under 3k tokens for better performance. "
                "Move detailed docs to references/"
            )

    def _check_todos(self):
        """Check for TODO markers."""
        if "TODO" in self.body:
            todo_count = self.body.count("TODO")
            self.warnings.append(
                f"Found {todo_count} TODO marker(s). Complete these before deploying agent"
            )

        # Also check description for TODOs
        desc = self.frontmatter.get("description", "")
        if "TODO" in desc:
            self.warnings.append("Description contains TODO marker. Complete before deploying")

    def print_report(self):
        """Print validation report."""
        fmt = "split" if self.is_split else "single-file"
        print(f"\n{'='*60}")
        print(f"Agent Validation Report: {self.display_name} ({fmt})")
        print(f"{'='*60}\n")

        if not self.errors and not self.warnings:
            print("Agent is valid! No errors or warnings.\n")
            return

        if self.errors:
            print(f"Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print(f"Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        if self.errors:
            print("Validation failed. Fix errors before deploying.\n")
        else:
            print("No errors, but consider addressing warnings for best practices.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Claude Code agent structure and content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split format (preferred)
  %(prog)s .claude/agents/code-reviewer/
  %(prog)s .claude/agents/code-reviewer/agent.yml

  # Single file (legacy)
  %(prog)s .claude/agents/code-reviewer.md
  %(prog)s my-agent.md

Validation Checks:
  - Metadata structure (agent.yml or frontmatter)
  - Required fields (name, description)
  - Name format (kebab-case)
  - Description quality (trigger keywords)
  - Tool permissions
  - Model selection
  - Color validity
  - System prompt structure
  - Quality gate sections (Pre-flight, Responsibility, VERIFY, LEARN)
  - Token count estimates
  - TODO markers

Quality Gates:
  By default, missing quality gate sections produce warnings.
  Use --strict to treat them as errors.
        """
    )

    parser.add_argument(
        "agent_path",
        type=Path,
        help="Path to agent directory, agent.yml, or .md file"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing quality gate sections as errors instead of warnings"
    )

    args = parser.parse_args()

    # Validate
    validator = AgentValidator(args.agent_path, strict=args.strict)
    is_valid = validator.validate()
    validator.print_report()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
