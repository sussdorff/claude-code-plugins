#!/usr/bin/env python3
"""
Comprehensive plugin structure validation script.

Validates plugin structure against Claude Code plugin specifications:
- Plugin manifest (plugin.json) structure and required fields
- Directory structure and component organization
- Command files (YAML frontmatter and naming)
- Skill directories and SKILL.md files
- Naming conventions (kebab-case)
- Path specifications

Based on official Claude Code documentation:
https://docs.claude.com/en/docs/claude-code/plugins-reference.md
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ValidationError:
    """Represents a validation error with severity level"""

    def __init__(self, severity: str, component: str, message: str):
        self.severity = severity  # 'error' or 'warning'
        self.component = component
        self.message = message

    def __str__(self):
        emoji = "❌" if self.severity == "error" else "⚠️"
        return f"{emoji} [{self.component}] {self.message}"


class PluginValidator:
    """Validates Claude Code plugin structure"""

    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, component: str, message: str):
        """Add an error to the validation results"""
        self.errors.append(ValidationError("error", component, message))

    def add_warning(self, component: str, message: str):
        """Add a warning to the validation results"""
        self.warnings.append(ValidationError("warning", component, message))

    def validate(self) -> bool:
        """Run all validations. Returns True if no errors found."""
        print(f"🔍 Validating plugin: {self.plugin_path.name}\n")

        # Core structure validation
        self.validate_plugin_structure()
        manifest_data = self.validate_manifest()

        # Component validations (only if manifest is valid)
        if manifest_data:
            self.validate_directory_structure()
            self.validate_commands()
            self.validate_skills()
            self.validate_naming_conventions(manifest_data)

        # Report results
        return self.report_results()

    def validate_plugin_structure(self):
        """Validate basic plugin directory structure"""
        if not self.plugin_path.exists():
            self.add_error("Structure", f"Plugin directory not found: {self.plugin_path}")
            return

        if not self.plugin_path.is_dir():
            self.add_error("Structure", f"Plugin path is not a directory: {self.plugin_path}")
            return

        # Check for .claude-plugin directory
        claude_plugin_dir = self.plugin_path / ".claude-plugin"
        if not claude_plugin_dir.exists():
            self.add_error("Structure", "Missing .claude-plugin directory")
            return

        if not claude_plugin_dir.is_dir():
            self.add_error("Structure", ".claude-plugin must be a directory")

    def validate_manifest(self) -> dict:
        """Validate plugin.json manifest file"""
        manifest_path = self.plugin_path / ".claude-plugin" / "plugin.json"

        if not manifest_path.exists():
            self.add_error("Manifest", "Missing plugin.json in .claude-plugin directory")
            return None

        # Parse JSON
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.add_error("Manifest", f"Invalid JSON in plugin.json: {e}")
            return None
        except Exception as e:
            self.add_error("Manifest", f"Failed to read plugin.json: {e}")
            return None

        # Validate required fields
        if "name" not in data:
            self.add_error("Manifest", "Missing required field 'name' in plugin.json")
        else:
            name = data["name"]
            # Validate kebab-case naming
            if not re.match(r'^[a-z0-9-]+$', name):
                self.add_error("Manifest", f"Plugin name '{name}' must be kebab-case (lowercase letters, digits, hyphens only)")
            if name.startswith('-') or name.endswith('-'):
                self.add_error("Manifest", f"Plugin name '{name}' cannot start or end with hyphen")
            if '--' in name:
                self.add_error("Manifest", f"Plugin name '{name}' cannot contain consecutive hyphens")
            if ' ' in name:
                self.add_error("Manifest", f"Plugin name '{name}' cannot contain spaces")

        # Validate optional but recommended fields
        if "description" not in data:
            self.add_warning("Manifest", "Missing recommended field 'description'")

        if "version" not in data:
            self.add_warning("Manifest", "Missing recommended field 'version'")
        else:
            # Basic semantic versioning check
            version = data["version"]
            if not re.match(r'^\d+\.\d+\.\d+', version):
                self.add_warning("Manifest", f"Version '{version}' does not follow semantic versioning (e.g., 1.0.0)")

        # Validate custom paths if specified
        if "commands" in data:
            self.validate_custom_paths(data["commands"], "commands")
        if "agents" in data:
            self.validate_custom_paths(data["agents"], "agents")
        if "hooks" in data:
            if isinstance(data["hooks"], str):
                self.validate_custom_paths(data["hooks"], "hooks")

        return data

    def validate_custom_paths(self, paths, component: str):
        """Validate custom path specifications"""
        if isinstance(paths, str):
            paths = [paths]

        for path in paths if isinstance(paths, list) else [paths]:
            if not path.startswith('./'):
                self.add_error("Manifest", f"Custom path '{path}' for {component} must be relative and start with './'")

    def validate_directory_structure(self):
        """Validate that component directories are at plugin root, not inside .claude-plugin"""
        claude_plugin_dir = self.plugin_path / ".claude-plugin"

        # Check for misplaced directories inside .claude-plugin
        for subdir in ['commands', 'skills', 'agents', 'hooks']:
            misplaced = claude_plugin_dir / subdir
            if misplaced.exists():
                self.add_error("Structure",
                    f"'{subdir}/' directory must be at plugin root, not inside .claude-plugin/")

        # Verify .claude-plugin only contains plugin.json
        for item in claude_plugin_dir.iterdir():
            if item.name != "plugin.json":
                self.add_warning("Structure",
                    f"Unexpected item in .claude-plugin/: {item.name} (should only contain plugin.json)")

    def validate_commands(self):
        """Validate command files"""
        commands_dir = self.plugin_path / "commands"

        if not commands_dir.exists():
            # Commands are optional
            return

        if not commands_dir.is_dir():
            self.add_error("Commands", "commands/ must be a directory")
            return

        # Find all .md files
        command_files = list(commands_dir.rglob("*.md"))

        if not command_files:
            self.add_warning("Commands", "commands/ directory exists but contains no .md files")
            return

        for cmd_file in command_files:
            self.validate_command_file(cmd_file)

    def validate_command_file(self, cmd_file: Path):
        """Validate individual command file"""
        # Check naming convention
        if not re.match(r'^[a-z0-9-]+\.md$', cmd_file.name):
            self.add_warning("Commands",
                f"Command file '{cmd_file.name}' should use kebab-case naming")

        try:
            content = cmd_file.read_text()
        except Exception as e:
            self.add_error("Commands", f"Failed to read {cmd_file.name}: {e}")
            return

        # Check for optional frontmatter
        if content.startswith('---'):
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                self.add_warning("Commands",
                    f"{cmd_file.name}: Invalid frontmatter format")
                return

            frontmatter = match.group(1)

            # Check for description (recommended)
            if 'description:' not in frontmatter:
                self.add_warning("Commands",
                    f"{cmd_file.name}: Missing recommended 'description' in frontmatter")

    def validate_skills(self):
        """Validate skill directories and SKILL.md files"""
        skills_dir = self.plugin_path / "skills"

        if not skills_dir.exists():
            # Skills are optional
            return

        if not skills_dir.is_dir():
            self.add_error("Skills", "skills/ must be a directory")
            return

        # Find all skill directories
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]

        if not skill_dirs:
            self.add_warning("Skills", "skills/ directory exists but contains no skill directories")
            return

        for skill_dir in skill_dirs:
            self.validate_skill_directory(skill_dir)

    def validate_skill_directory(self, skill_dir: Path):
        """Validate individual skill directory"""
        skill_name = skill_dir.name

        # Check naming convention
        if not re.match(r'^[a-z0-9-]+$', skill_name):
            self.add_warning("Skills",
                f"Skill directory '{skill_name}' should use kebab-case naming")

        if skill_name.startswith('-') or skill_name.endswith('-') or '--' in skill_name:
            self.add_error("Skills",
                f"Skill directory '{skill_name}' cannot start/end with hyphen or contain consecutive hyphens")

        # Check for SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            self.add_error("Skills", f"{skill_name}/: Missing required SKILL.md file")
            return

        self.validate_skill_md(skill_md, skill_name)

    def validate_skill_md(self, skill_md: Path, skill_name: str):
        """Validate SKILL.md file"""
        try:
            content = skill_md.read_text()
        except Exception as e:
            self.add_error("Skills", f"{skill_name}/SKILL.md: Failed to read: {e}")
            return

        # Check for YAML frontmatter
        if not content.startswith('---'):
            self.add_error("Skills", f"{skill_name}/SKILL.md: Missing YAML frontmatter")
            return

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            self.add_error("Skills", f"{skill_name}/SKILL.md: Invalid frontmatter format")
            return

        frontmatter = match.group(1)

        # Check required fields
        if 'name:' not in frontmatter:
            self.add_error("Skills", f"{skill_name}/SKILL.md: Missing required 'name' in frontmatter")
        else:
            # Extract and validate name
            name_match = re.search(r'name:\s*(.+)', frontmatter)
            if name_match:
                name = name_match.group(1).strip()
                # Check kebab-case
                if not re.match(r'^[a-z0-9-]+$', name):
                    self.add_error("Skills",
                        f"{skill_name}/SKILL.md: Name '{name}' should be kebab-case")
                if name.startswith('-') or name.endswith('-') or '--' in name:
                    self.add_error("Skills",
                        f"{skill_name}/SKILL.md: Name '{name}' cannot start/end with hyphen or contain consecutive hyphens")

        if 'description:' not in frontmatter:
            self.add_error("Skills",
                f"{skill_name}/SKILL.md: Missing required 'description' in frontmatter")
        else:
            # Extract and validate description
            desc_match = re.search(r'description:\s*(.+)', frontmatter)
            if desc_match:
                description = desc_match.group(1).strip()
                if '<' in description or '>' in description:
                    self.add_error("Skills",
                        f"{skill_name}/SKILL.md: Description cannot contain angle brackets (< or >)")
                if not description:
                    self.add_error("Skills",
                        f"{skill_name}/SKILL.md: Description cannot be empty")

    def validate_naming_conventions(self, manifest_data: dict):
        """Validate overall naming conventions"""
        plugin_name = manifest_data.get("name", "")

        # Check if directory name matches manifest name
        if plugin_name and self.plugin_path.name != plugin_name:
            self.add_warning("Naming",
                f"Plugin directory name '{self.plugin_path.name}' does not match manifest name '{plugin_name}'")

    def report_results(self) -> bool:
        """Print validation results and return success status"""
        print()

        if self.errors:
            print("❌ VALIDATION FAILED\n")
            print(f"Found {len(self.errors)} error(s):\n")
            for error in self.errors:
                print(f"  {error}")
            print()

        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warning(s):\n")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ VALIDATION PASSED\n")
            print("Plugin structure is valid!")
            print()
            return True

        if not self.errors:
            print("✅ VALIDATION PASSED (with warnings)\n")
            print("Plugin structure is valid, but consider addressing warnings.")
            print()
            return True

        return False


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python validate-plugin.py <plugin-directory>")
        print()
        print("Validates a Claude Code plugin structure against official specifications.")
        print()
        print("Example:")
        print("  python validate-plugin.py my-plugin")
        print("  python validate-plugin.py /path/to/plugin")
        sys.exit(1)

    plugin_path = Path(sys.argv[1])
    validator = PluginValidator(plugin_path)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
