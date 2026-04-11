#!/usr/bin/env python3
"""
SessionStart hook: rules.d loader

Loads active behavioral rules from ~/.claude/rules.d/*.txt and injects them
into the conversation as a system reminder. Files not ending in .txt are
skipped (the .disabled suffix convention is one way to disable a rule).

Fires once at session start — rules changes require a session restart.

Exit codes: always 0 (info only, never blocks session start).

Input: SessionStart JSON event on stdin (drained, not parsed).
Output: stdout → injected as system reminder into the conversation.
Stderr: per-file read errors logged; exit always 0.
"""

import glob
import os
import sys


def main() -> None:
    # Read and discard stdin (SessionStart event) — not needed for logic
    try:
        sys.stdin.read()
    except OSError:
        pass

    # Locate rules.d directory
    rules_dir = os.path.expanduser("~/.claude/rules.d")

    # Glob for active rule files (sorted alphabetically for ordering)
    pattern = os.path.join(rules_dir, "*.txt")
    rule_files = sorted(glob.glob(pattern))

    if not rule_files:
        sys.exit(0)

    # Read all rule files
    rules: list[str] = []
    for path in rule_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                rules.append(content)
        except OSError as e:
            # Log to stderr but don't block — fail-open
            print(f"rules-loader: could not read {path}: {e}", file=sys.stderr)

    if not rules:
        sys.exit(0)

    # Output rules as system reminder to stdout
    sections = "\n\n---\n\n".join(rules)
    print(f"## Active Rules (rules.d)\n\n{sections}")

    sys.exit(0)


if __name__ == "__main__":
    main()
