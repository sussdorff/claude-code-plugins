#!/usr/bin/env python3
"""Write docs/adr/0000-vision-initial.md using vision_renderer.

Usage: python3 write-genesis-adr.py [project-name]
If project-name is omitted, uses the git repo directory name.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

repo_root = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip())
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

project_name = sys.argv[1] if len(sys.argv) > 1 else repo_root.name

try:
    from scripts.vision_renderer import render_genesis_adr
    adr_dir = repo_root / "docs/adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    adr_path = adr_dir / "0000-vision-initial.md"
    adr_path.write_text(render_genesis_adr(project_name, str(date.today())), encoding="utf-8")
    print(f"{adr_path} created (genesis ADR)")
except ImportError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(2)
