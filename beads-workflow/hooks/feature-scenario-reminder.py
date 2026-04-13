#!/usr/bin/env python3
"""PostToolUse hook: remind about scenario generation when creating feature beads directly.

Safety net for when users bypass /create and use `bd create --type=feature` directly.
Outputs a reminder to run the scenario generator.

Returns 0 always — never blocks tool execution.
"""

from __future__ import annotations

import json
import re
import sys


# Match: bd create ... --type=feature or --type feature (with or without quotes)
_FEATURE_CREATE = re.compile(
    r"\bbd\s+create\b.*--type[= ]['\"]?feature['\"]?",
    re.IGNORECASE,
)

# Negative match: skip if this was triggered by /create skill (has scenario marker)
_SCENARIO_MARKER = re.compile(r"## Szenario|scenario-generator|bead-scenario")


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError, ValueError, OSError):
        return

    try:
        command = event.get("tool_input", {}).get("command", "")
        if not command:
            return

        # Only trigger on bd create --type=feature
        if not _FEATURE_CREATE.search(command):
            return

        # Skip if the description already contains scenarios (created via /create skill)
        if _SCENARIO_MARKER.search(command):
            return

        # Output reminder
        print(
            "Feature-Bead ohne Szenarien erstellt. "
            "Empfehlung: Scenario-Generator nachtraeglich starten mit:\n"
            '  Agent(subagent_type="dev-tools:scenario-generator", '
            'prompt="Mode: bead-scenario, Bead-ID: <id>")\n'
            "Oder kuenftig `/create` statt direktem `bd create` verwenden."
        )

    except Exception:
        pass


if __name__ == "__main__":
    main()
