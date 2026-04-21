#!/usr/bin/env python3
"""
Grab character-windows of context around regex matches in a large text file.

This is the right tool for searching minified JavaScript bundles (Webpack /
esbuild output), where everything is on one giant line and line-based grep
loses all context.

Usage:
    python search.py <file> <pattern> [context_chars] [max_hits]

Defaults:
    context_chars = 300
    max_hits      = 10

The pattern is a standard Python regex. Matches are printed with a small
header showing the offset, followed by the surrounding text.
"""

import re
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    path = sys.argv[1]
    pattern = sys.argv[2]
    context = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    max_hits = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            s = f.read()
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}", file=sys.stderr)
        return 1

    try:
        rx = re.compile(pattern)
    except re.error as e:
        print(f"ERROR: bad regex: {e}", file=sys.stderr)
        return 1

    hits = 0
    for m in rx.finditer(s):
        start = max(0, m.start() - context)
        end = min(len(s), m.end() + context)
        print(f"--- match at offset {m.start()} ---")
        print(s[start:end])
        hits += 1
        if hits >= max_hits:
            break

    print(f"\nTotal hits shown: {hits}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
