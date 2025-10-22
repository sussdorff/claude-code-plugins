#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

"""
Hook Manager - Install, remove, and manage Claude Code hooks

This script helps manage hooks in Claude Code settings.json files.
It can install new hooks, remove existing ones, and list configured hooks.
"""

import json
import sys
import os
import argparse
from pathlib import Path

def find_settings_file(scope="project"):
    """Find the appropriate settings.json file based on scope"""
    if scope == "user":
        return Path.home() / ".claude" / "settings.json"
    elif scope == "project":
        # Look for .claude/settings.json in current directory or parents
        current = Path.cwd()
        while current != current.parent:
            settings = current / ".claude" / "settings.json"
            if settings.exists():
                return settings
            current = current.parent
        # If not found, create in current directory
        return Path.cwd() / ".claude" / "settings.json"
    else:
        return Path(scope)

def load_settings(settings_path):
    """Load settings.json or create empty structure"""
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            return json.load(f)
    return {"hooks": {}}

def save_settings(settings_path, settings):
    """Save settings.json with proper formatting"""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')

def install_hook(settings_path, hook_type, matcher, command):
    """Install a new hook"""
    settings = load_settings(settings_path)

    # Ensure hooks structure exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    # Ensure hook type exists
    if hook_type not in settings["hooks"]:
        settings["hooks"][hook_type] = []

    # Find or create matcher entry
    matcher_entry = None
    for entry in settings["hooks"][hook_type]:
        if entry.get("matcher") == matcher:
            matcher_entry = entry
            break

    if matcher_entry is None:
        matcher_entry = {"matcher": matcher, "hooks": []}
        settings["hooks"][hook_type].append(matcher_entry)

    # Add the hook
    hook_config = {"type": "command", "command": command}

    # Check if hook already exists
    if hook_config not in matcher_entry["hooks"]:
        matcher_entry["hooks"].append(hook_config)
        save_settings(settings_path, settings)
        print(f"✓ Installed {hook_type} hook: {command}")
        return True
    else:
        print(f"Hook already exists: {command}")
        return False

def remove_hook(settings_path, hook_type, command):
    """Remove a hook by command"""
    settings = load_settings(settings_path)

    if "hooks" not in settings or hook_type not in settings["hooks"]:
        print(f"No hooks found for type: {hook_type}")
        return False

    removed = False
    for matcher_entry in settings["hooks"][hook_type]:
        original_count = len(matcher_entry["hooks"])
        matcher_entry["hooks"] = [
            h for h in matcher_entry["hooks"]
            if h.get("command") != command
        ]
        if len(matcher_entry["hooks"]) < original_count:
            removed = True

    # Clean up empty matcher entries
    settings["hooks"][hook_type] = [
        entry for entry in settings["hooks"][hook_type]
        if entry["hooks"]
    ]

    # Clean up empty hook types
    if not settings["hooks"][hook_type]:
        del settings["hooks"][hook_type]

    if removed:
        save_settings(settings_path, settings)
        print(f"✓ Removed {hook_type} hook: {command}")
        return True
    else:
        print(f"Hook not found: {command}")
        return False

def list_hooks(settings_path):
    """List all configured hooks"""
    settings = load_settings(settings_path)

    if "hooks" not in settings or not settings["hooks"]:
        print("No hooks configured")
        return

    print(f"\nHooks configured in: {settings_path}\n")

    for hook_type, matcher_entries in settings["hooks"].items():
        print(f"═══ {hook_type} ═══")
        for entry in matcher_entries:
            matcher = entry.get("matcher", "")
            print(f"  Matcher: {matcher if matcher else '(all)'}")
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                print(f"    → {command}")
        print()

def validate_hook_type(hook_type):
    """Validate that hook_type is one of the 8 valid types"""
    valid_types = [
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "Notification",
        "Stop",
        "SubagentStop",
        "PreCompact"
    ]

    if hook_type not in valid_types:
        print(f"Error: Invalid hook type '{hook_type}'")
        print(f"Valid types: {', '.join(valid_types)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Manage Claude Code hooks",
        epilog="""
Examples:
  # List all hooks
  %(prog)s list

  # Install a PreToolUse hook (project scope)
  %(prog)s install PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"

  # Install a PostToolUse hook with matcher (user scope)
  %(prog)s install PostToolUse --matcher "Edit|Write" --command "npx prettier --write \\"$file_path\\"" --scope user

  # Remove a hook
  %(prog)s remove PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "action",
        choices=["install", "remove", "list"],
        help="Action to perform"
    )

    parser.add_argument(
        "hook_type",
        nargs="?",
        help="Hook type (SessionStart, PreToolUse, PostToolUse, etc.)"
    )

    parser.add_argument(
        "--command",
        help="Hook command to execute"
    )

    parser.add_argument(
        "--matcher",
        default="",
        help="Matcher pattern (default: empty for all)"
    )

    parser.add_argument(
        "--scope",
        choices=["user", "project"],
        default="project",
        help="Settings scope (default: project)"
    )

    parser.add_argument(
        "--settings-path",
        help="Custom path to settings.json file"
    )

    args = parser.parse_args()

    # Determine settings path
    if args.settings_path:
        settings_path = Path(args.settings_path)
    else:
        settings_path = find_settings_file(args.scope)

    # Handle list action
    if args.action == "list":
        list_hooks(settings_path)
        return

    # Validate hook type for install/remove
    if not args.hook_type:
        parser.error(f"{args.action} action requires hook_type")

    if not validate_hook_type(args.hook_type):
        sys.exit(1)

    # Handle install action
    if args.action == "install":
        if not args.command:
            parser.error("install action requires --command")
        install_hook(settings_path, args.hook_type, args.matcher, args.command)

    # Handle remove action
    elif args.action == "remove":
        if not args.command:
            parser.error("remove action requires --command")
        remove_hook(settings_path, args.hook_type, args.command)

if __name__ == "__main__":
    main()
