#!/usr/bin/env python3
"""Validate answer text against tense gate rules.
Reads answer text from stdin. Prints violations if any.

Usage: python3 validate-tense.py < answer.txt
"""
import os
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path

repo_root = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True
).strip())
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

answer_text = sys.stdin.read()

tg_path = repo_root / "scripts" / "tense-gate.py"
spec = importlib.util.spec_from_file_location("tense_gate", tg_path)
tg = importlib.util.module_from_spec(spec)
sys.modules["tense_gate"] = tg
spec.loader.exec_module(tg)

with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
    f.write("---\ndocument_type: prescriptive-present\ntemplate_version: 1\ngenerator: vision-author\n---\n\n")
    f.write(answer_text)
    tmp_path = f.name

try:
    violations = tg.lint_file(Path(tmp_path))
    if violations:
        for lineno, tag, explanation, matched in violations:
            print(f"  line {lineno}: [{tag}] {explanation}")
            print(f"    Found: '{matched}'")
        sys.exit(1)
    else:
        print("OK: no tense violations")
finally:
    os.unlink(tmp_path)
