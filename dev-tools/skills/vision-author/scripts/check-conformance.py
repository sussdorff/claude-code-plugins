#!/usr/bin/env python3
"""Check vision.md conformance using vision_conformance.py from the project.

Usage: python3 check-conformance.py [vision-md-path]
Default path: docs/vision.md
"""
import subprocess
import sys
from pathlib import Path

repo_root = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip())
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

vision_path = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root / "docs/vision.md"

if not vision_path.exists():
    print(f"NOT_FOUND: {vision_path}")
    sys.exit(1)

try:
    from scripts.vision_conformance import check_conformance
    result = check_conformance(vision_path)
    if result.is_conformant:
        print("CONFORMANT")
    else:
        print("CONFORMANCE FAILURE:")
        for s in getattr(result, 'missing_sections', []):
            print(f"  missing: {s}")
        for e in getattr(result, 'errors', []):
            print(f"  error: {e}")
        sys.exit(1)
except ImportError as e:
    print(f"ERROR: cannot import vision_conformance: {e}", file=sys.stderr)
    sys.exit(2)
