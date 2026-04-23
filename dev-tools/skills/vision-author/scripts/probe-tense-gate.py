#!/usr/bin/env python3
"""Probe for tense-gate.py in the current git repo.
Exit 0 if found, exit 2 if not found."""
import subprocess
import sys
from pathlib import Path

try:
    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip())
except subprocess.CalledProcessError:
    print("ERROR: not in a git repository", file=sys.stderr)
    sys.exit(2)

tense_gate = repo_root / "scripts" / "tense-gate.py"
if not tense_gate.exists():
    print(f"ERROR: tense-gate not found at {tense_gate}")
    print("Install via: /tense-gate (CCP-2q2)")
    sys.exit(2)

print(f"FOUND: {tense_gate}")
