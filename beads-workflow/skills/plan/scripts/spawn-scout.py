#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0"
# ]
# ///
"""
Spawn the architecture-scout agent for a given bead.

This script is a reference template showing the input contract for the scout.
In practice the /plan skill constructs this dict inline and passes it to Agent().

Usage (as a template — not meant to be run directly):
    python3 spawn-scout.py <bead_id> <bead_description> [touched_path ...]
"""
import json
import os
import sys

import yaml


def _read_scout_mode() -> str:
    """Read architecture-scout.mode from .claude/project-config.yml, default 'advisor'."""
    config_path = ".claude/project-config.yml"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        return config.get("architecture-scout", {}).get("mode", "advisor")
    return "advisor"


def build_scout_input(bead_id: str, bead_description: str, touched_paths: list) -> dict:
    return {
        "bead_id": bead_id,
        "bead_description": bead_description,
        "touched_paths": touched_paths,
        "mode": _read_scout_mode(),
        "conformance_skip": os.environ.get("CONFORMANCE_SKIP") == "1",
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: spawn-scout.py <bead_id> <bead_description> [touched_path ...]", file=sys.stderr)
        sys.exit(1)

    bead_id = sys.argv[1]
    bead_description = sys.argv[2]
    touched_paths = sys.argv[3:]

    scout_input = build_scout_input(bead_id, bead_description, touched_paths)
    print(json.dumps(scout_input, indent=2))
