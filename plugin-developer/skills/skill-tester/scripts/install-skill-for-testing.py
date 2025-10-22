#!/usr/bin/env python3
"""
Install a skill from the development directory to .claude/skills/ for testing.
"""

import argparse
import shutil
import sys
from pathlib import Path


def find_available_skills(project_root: Path) -> list[str]:
    """Find available skill directories in the project root."""
    skills = []
    for item in project_root.iterdir():
        if item.is_dir() and not item.name.startswith('.') and '-' in item.name:
            skills.append(item.name)
    return sorted(skills)


def main():
    parser = argparse.ArgumentParser(
        description="Install a skill from the development directory to .claude/skills/ for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s git-worktree-tools
  %(prog)s my-custom-skill

The script will:
  1. Check if skill exists in project
  2. Check if skill already exists in .claude/skills/
  3. Copy skill files to .claude/skills/
  4. Report whether Claude restart is needed
"""
    )
    parser.add_argument(
        "skill_name",
        help="Name of the skill directory (e.g., git-worktree-tools)"
    )
    args = parser.parse_args()

    skill_name = args.skill_name
    current_dir = Path.cwd()

    # Detect PROJECT_ROOT and source directory based on repository structure
    # Case 1: Current directory is the skill itself (has SKILL.md at root)
    if (current_dir / "SKILL.md").exists():
        project_root = current_dir
        source_dir = project_root
    # Case 2: Marketplace/multi-skill repository (skill is a subdirectory)
    else:
        project_root = current_dir
        source_dir = project_root / skill_name

    target_dir = project_root / ".claude" / "skills" / skill_name

    # Validate source exists
    if not source_dir.exists():
        print(f"❌ Error: Skill directory not found: {source_dir}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Available skills:", file=sys.stderr)
        available = find_available_skills(project_root)
        for skill in available:
            print(f"  - {skill}", file=sys.stderr)
        sys.exit(1)

    # Check if SKILL.md exists
    skill_md = source_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {source_dir}", file=sys.stderr)
        print("This doesn't appear to be a valid skill directory.", file=sys.stderr)
        sys.exit(1)

    # Check if skill is new or updated
    skill_is_new = not target_dir.exists()

    if skill_is_new:
        print(f"📦 Installing new skill: {skill_name}")
    else:
        print(f"🔄 Updating existing skill: {skill_name}")

    # Create target directory parent if needed
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    print("📋 Copying files...")

    if target_dir.exists():
        # Remove existing directory for clean update
        shutil.rmtree(target_dir)

    # Copy skill directory
    shutil.copytree(source_dir, target_dir)

    # Report success
    print("")
    print(f"✅ Skill installed to: {target_dir}")
    print("")

    if skill_is_new:
        print("⚠️  NEW SKILL DETECTED")
        print("   Skills are loaded at Claude Code session start.")
        print("   You must EXIT and RESTART Claude Code for this skill to be available.")
        print("")
        print("   Steps:")
        print("   1. Exit this Claude Code session (Ctrl+D or 'exit')")
        print("   2. Start a new session: claude")
        print(f'   3. Test the skill with: "Test {skill_name}"')
    else:
        print("ℹ️  SKILL UPDATED")
        print("   This skill was already installed. Changes are available.")
        print("   If changes don't appear, restart Claude Code session.")

    print("")
    # Show relative path from home directory if possible
    try:
        relative_path = target_dir.relative_to(Path.home())
        print(f"📍 Skill location: ~/{relative_path}")
    except ValueError:
        print(f"📍 Skill location: {target_dir}")


if __name__ == "__main__":
    main()
