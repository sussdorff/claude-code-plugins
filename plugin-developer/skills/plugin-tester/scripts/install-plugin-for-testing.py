#!/usr/bin/env python3
"""
Install a plugin for local testing by copying to .claude directories.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Install a plugin for local testing"
    )
    parser.add_argument("plugin_name", help="Name of the plugin to install")
    args = parser.parse_args()

    plugin_name = args.plugin_name

    # Detect PROJECT_ROOT based on repository structure
    current_dir = Path.cwd()

    # Case 1: Current directory is the plugin itself (has .claude-plugin/plugin.json)
    if (current_dir / ".claude-plugin" / "plugin.json").exists():
        project_root = current_dir
        plugin_dir = project_root

        # Verify the plugin name matches
        with open(plugin_dir / ".claude-plugin" / "plugin.json") as f:
            plugin_data = json.load(f)
            actual_name = plugin_data.get("name")
            if actual_name != plugin_name:
                print(f"⚠️  Warning: Plugin name '{plugin_name}' doesn't match actual name '{actual_name}' in plugin.json", file=sys.stderr)
                print(f"Using actual name: {actual_name}", file=sys.stderr)
                plugin_name = actual_name

    # Case 2: Marketplace/multi-plugin repository (plugin is a subdirectory)
    else:
        project_root = current_dir
        plugin_dir = project_root / plugin_name

    # Validation
    if not plugin_dir.exists():
        print(f"❌ Error: Plugin directory not found: {plugin_dir}", file=sys.stderr)
        sys.exit(1)

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        print(f"❌ Error: Plugin metadata not found: {plugin_json_path}", file=sys.stderr)
        print("This doesn't appear to be a valid plugin.", file=sys.stderr)
        sys.exit(1)

    # Read plugin metadata
    with open(plugin_json_path) as f:
        plugin_data = json.load(f)
        plugin_version = plugin_data.get("version", "unknown")
        plugin_desc = plugin_data.get("description", "")

    print(f"📦 Installing plugin: {plugin_name} (v{plugin_version})")
    print(f"   {plugin_desc}")
    print()

    # Track what was installed
    installed_commands = False
    installed_skills = False
    commands_count = 0
    skills_count = 0

    # Install commands to .claude/commands/
    commands_src = plugin_dir / "commands"
    if commands_src.exists() and commands_src.is_dir():
        commands_dst = project_root / ".claude" / "commands"
        commands_dst.mkdir(parents=True, exist_ok=True)

        # Copy all command files
        command_files = list(commands_src.glob("*.md"))
        if command_files:
            print("📋 Installing commands...")
            for cmd_file in command_files:
                dst_file = commands_dst / cmd_file.name
                shutil.copy2(cmd_file, dst_file)
                print(f"   ✓ {cmd_file.stem}")
                commands_count += 1
            installed_commands = True
            print()

    # Install skills to .claude/skills/
    skills_src = plugin_dir / "skills"
    if skills_src.exists() and skills_src.is_dir():
        skills_dst = project_root / ".claude" / "skills"
        skills_dst.mkdir(parents=True, exist_ok=True)

        print("🧠 Installing skills...")
        # Copy each skill directory
        skill_dirs = [d for d in skills_src.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            skill_name = skill_dir.name

            # Skip special files like .zip
            if skill_name.startswith('.'):
                continue

            skill_dst = skills_dst / skill_name

            # Check if new or update
            if skill_dst.exists():
                print(f"   🔄 Updating: {skill_name}")
                # Remove existing directory
                shutil.rmtree(skill_dst)
            else:
                print(f"   ✨ New: {skill_name}")

            # Copy skill directory
            shutil.copytree(skill_dir, skill_dst)
            skills_count += 1

        installed_skills = True
        print()

    # Summary
    print("✅ Plugin installed successfully")
    print()
    print("📊 Summary:")
    if installed_commands:
        print(f"   Commands: {commands_count} installed to .claude/commands/")
    if installed_skills:
        print(f"   Skills: {skills_count} installed to .claude/skills/")
    print()

    # Next steps guidance
    if installed_commands or installed_skills:
        print("⚠️  RESTART REQUIRED")
        print("   Commands and skills are loaded at Claude Code startup.")
        print()
        print("   Steps:")
        print("   1. Exit this Claude Code session: exit")
        print("   2. Start a new session: claude")
        if installed_commands:
            print("   3. Test commands: /<command-name>")
        if installed_skills:
            print("   3. Skills will be auto-invoked based on their descriptions")
        print()

    print(f"📍 Plugin source: {plugin_dir}")
    print(f"📍 Commands: {project_root / '.claude' / 'commands'}")
    print(f"📍 Skills: {project_root / '.claude' / 'skills'}")


if __name__ == "__main__":
    main()
