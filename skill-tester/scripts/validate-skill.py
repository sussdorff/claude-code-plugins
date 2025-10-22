#!/usr/bin/env python3
"""
Validate a skill without packaging it.
Wrapper around the skill-creator validation logic.
"""

import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: validate-skill.py <skill-name>")
        print("\nExample: validate-skill.py jira-context-fetcher")
        sys.exit(1)

    skill_name = sys.argv[1]
    project_root = Path(__file__).parent.parent.parent
    skill_path = project_root / skill_name

    if not skill_path.exists():
        print(f"❌ Error: Skill directory not found: {skill_path}")
        print("\nAvailable skills:")
        for item in sorted(project_root.iterdir()):
            if item.is_dir() and not item.name.startswith('.') and '-' in item.name:
                print(f"  - {item.name}")
        sys.exit(1)

    # Use the quick_validate.py script from skill-creator
    validator_script = Path.home() / ".claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/scripts/quick_validate.py"

    if not validator_script.exists():
        print(f"❌ Error: Validator script not found: {validator_script}")
        print("Make sure the skill-creator skill is installed.")
        sys.exit(1)

    print(f"🔍 Validating skill: {skill_name}")
    print(f"   Path: {skill_path}")
    print()

    # Run validation
    result = subprocess.run(
        [sys.executable, str(validator_script), str(skill_path)],
        capture_output=False
    )

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
