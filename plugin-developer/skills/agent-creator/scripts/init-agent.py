#!/usr/bin/env python3
"""
Initialize a new Claude Code agent with proper structure and template.

Usage:
    python3 init-agent.py <agent-name> [--path <output-directory>]

Examples:
    python3 init-agent.py code-reviewer
    python3 init-agent.py test-runner --path .claude/agents/
"""

import argparse
import sys
from pathlib import Path


def validate_agent_name(name: str) -> tuple[bool, str]:
    """
    Validate agent name follows kebab-case convention.

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Agent name cannot be empty"

    if "_" in name:
        return False, f"Agent name '{name}' contains underscores. Use hyphens instead (kebab-case)"

    if name != name.lower():
        return False, f"Agent name '{name}' contains uppercase letters. Use lowercase only (kebab-case)"

    if " " in name:
        return False, f"Agent name '{name}' contains spaces. Use hyphens instead (kebab-case)"

    if not name.replace("-", "").isalnum():
        return False, f"Agent name '{name}' contains invalid characters. Use only lowercase letters, numbers, and hyphens"

    if name.startswith("-") or name.endswith("-"):
        return False, f"Agent name '{name}' cannot start or end with hyphen"

    if "--" in name:
        return False, f"Agent name '{name}' contains consecutive hyphens"

    return True, ""


def get_agent_template(name: str) -> str:
    """Generate agent template content."""
    return f"""---
name: {name}
description: TODO: Describe when and why to use this agent. Be specific with trigger keywords. Example - "Reviews code for security vulnerabilities. Use PROACTIVELY when code changes are made."
tools: Read, Grep, Glob
model: sonnet
color: blue
---

# Purpose

TODO: Define the agent's role and expertise. What is this agent an expert in?

## Instructions

TODO: Add numbered, actionable steps for the agent to follow:

1. [Step 1: What to do first]
2. [Step 2: What to do next]
3. [Step 3: etc.]

## Best Practices

TODO: Add domain-specific best practices:

- [Best practice 1]
- [Best practice 2]
- [Best practice 3]

## Output Format

TODO: Define the expected output structure:

```
### Section 1
[Description of what goes here]

### Section 2
[Description of what goes here]

### Summary
[Description of summary format]
```

## Notes

- Keep system prompt lean (<3k tokens ideal)
- Grant minimal tools necessary
- Use Haiku for routine tasks, Sonnet for specialized, Opus for complex reasoning
- Be specific in description for auto-delegation success
- Test with typical user phrases to validate auto-delegation
"""


def create_agent(name: str, output_path: str) -> bool:
    """
    Create new agent file with template.

    Args:
        name: Agent name (kebab-case)
        output_path: Directory where agent file should be created

    Returns:
        True if successful, False otherwise
    """
    # Validate name
    is_valid, error = validate_agent_name(name)
    if not is_valid:
        print(f"❌ Invalid agent name: {error}", file=sys.stderr)
        return False

    # Resolve output path
    if output_path:
        output_dir = Path(output_path).resolve()
    else:
        output_dir = Path.cwd() / ".claude" / "agents"

    # Create directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create agent file
    agent_file = output_dir / f"{name}.md"

    if agent_file.exists():
        print(f"❌ Agent file already exists: {agent_file}", file=sys.stderr)
        print(f"   To recreate, first remove the existing file", file=sys.stderr)
        return False

    # Write template
    try:
        agent_file.write_text(get_agent_template(name))
        print(f"✅ Created agent: {agent_file}")
        print()
        print("Next steps:")
        print(f"1. Edit {agent_file}")
        print("2. Replace all TODO items with actual content")
        print("3. Update frontmatter fields:")
        print("   - description: Specific, keyword-rich (critical for auto-delegation!)")
        print("   - tools: Only necessary tools")
        print("   - model: haiku (fast) | sonnet (balanced) | opus (complex)")
        print("   - color: Visual identifier (red, blue, green, yellow, purple, orange, pink, cyan)")
        print("4. Write clear, numbered instructions")
        print("5. Define expected output format")
        print("6. Test by invoking: 'Use the {name} agent to...'")
        print()
        print("💡 Tip: Keep system prompt under 3k tokens for best performance")
        return True

    except Exception as e:
        print(f"❌ Failed to create agent file: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize a new Claude Code agent with proper structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s code-reviewer
  %(prog)s test-runner --path .claude/agents/
  %(prog)s security-auditor --path /path/to/agents/

Agent Naming Rules:
  - Use kebab-case (lowercase with hyphens)
  - Examples: code-reviewer, test-runner, api-researcher
  - Avoid: CodeReviewer (PascalCase), code_reviewer (snake_case), CR (too short)
        """
    )

    parser.add_argument(
        "name",
        help="Agent name in kebab-case (e.g., code-reviewer, test-runner)"
    )

    parser.add_argument(
        "--path",
        help="Output directory for agent file (default: .claude/agents/)"
    )

    args = parser.parse_args()

    # Create agent
    print(f"🚀 Initializing agent: {args.name}")
    if args.path:
        print(f"   Location: {args.path}")
    else:
        print(f"   Location: .claude/agents/ (default)")
    print()

    success = create_agent(args.name, args.path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
