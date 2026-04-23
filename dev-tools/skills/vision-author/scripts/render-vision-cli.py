#!/usr/bin/env python3
"""Render vision.md content from answers JSON file.

Usage: python3 render-vision-cli.py <answers.json>

answers.json must have keys: vision_statement, target_group, core_need,
positioning, principles (list of [rule_id, text]), principle_scopes (dict),
business_goal, not_in_vision (list).

Prints rendered content to stdout.
"""
import subprocess
import sys
import json
from pathlib import Path

repo_root = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip())
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

if len(sys.argv) < 2:
    print("Usage: render-vision-cli.py <answers.json>", file=sys.stderr)
    sys.exit(1)

answers_path = Path(sys.argv[1])
data = json.loads(answers_path.read_text())

try:
    from scripts.vision_renderer import render_vision, VisionAnswers
    answers = VisionAnswers(
        vision_statement=data["vision_statement"],
        target_group=data["target_group"],
        core_need=data["core_need"],
        positioning=data["positioning"],
        principles=[tuple(p) for p in data["principles"]],
        principle_scopes=data["principle_scopes"],
        business_goal=data["business_goal"],
        not_in_vision=data["not_in_vision"],
    )
    print(render_vision(answers))
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(2)
