#!/usr/bin/env python3
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


def build_scout_input(bead_id: str, bead_description: str, touched_paths: list) -> dict:
    return {
        "bead_id": bead_id,
        "bead_description": bead_description,
        "touched_paths": touched_paths,
        "mode": os.environ.get("ARCHITECTURE_SCOUT_MODE", "advisor"),
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
