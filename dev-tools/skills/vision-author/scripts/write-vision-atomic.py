#!/usr/bin/env python3
"""Write docs/vision.md atomically from content on stdin.

Usage: cat content.md | python3 write-vision-atomic.py

Pipeline: python3 render-vision-cli.py answers.json > /tmp/vision-content.md && cat /tmp/vision-content.md | python3 write-vision-atomic.py
"""
import os
import sys
from pathlib import Path

content = sys.stdin.read()
draft = Path("docs/vision.md.draft")
final = Path("docs/vision.md")

final.parent.mkdir(parents=True, exist_ok=True)
draft.write_text(content, encoding="utf-8")
try:
    os.rename(draft, final)
except Exception as e:
    draft.unlink(missing_ok=True)
    raise
print("docs/vision.md written (atomic rename from draft)")
