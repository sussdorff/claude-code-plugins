#!/usr/bin/env python3
"""
parse_codex_review.py — Parse codex JSONL output and emit an execution-result envelope.

Usage:
  python3 parse_codex_review.py [<file>]
  cat codex_output.jsonl | python3 parse_codex_review.py

Input: JSONL from codex (one JSON object per line), or plain text with REGRESSION:/LGTM markers.
Output: execution-result.schema.json envelope to stdout.

Parses lines looking for:
  REGRESSION: <file>:<line> — <description>
  LGTM

Emits:
  status: "ok"      — no regressions found (LGTM)
  status: "warning" — one or more regressions found
"""

import datetime
import json
import re
import sys
from pathlib import Path

_SCHEMA = "core/contracts/execution-result.schema.json"
_PRODUCER = "parse_codex_review.py"
_CONTRACT_VERSION = "1.0"

# REGRESSION: <file>:<line> — <description>
# The separator can be em-dash (—) or double-dash (--)
_REGRESSION_RE = re.compile(
    r"REGRESSION:\s+(.+?):(\d+)\s+[—\-]{1,2}\s+(.+)"
)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _parse_lines(lines: list[str]) -> tuple[list[dict], bool]:
    """Parse input lines and return (regressions, lgtm_found)."""
    regressions: list[dict] = []
    lgtm_found = False

    for raw_line in lines:
        # Each line may be a JSON object (from codex --json) or plain text
        text = raw_line.strip()
        if not text:
            continue

        # Try to extract text content from a JSONL event
        try:
            event = json.loads(text)
            # Look in common text fields from codex JSON events
            candidate = ""
            if isinstance(event, dict):
                candidate = (
                    event.get("text", "")
                    or event.get("content", "")
                    or event.get("message", "")
                    or ""
                )
                # Also check nested item content
                item = event.get("item", {})
                if isinstance(item, dict):
                    candidate = candidate or item.get("text", "") or ""
            text = candidate if candidate else text
        except (json.JSONDecodeError, ValueError):
            pass  # plain text line — use as-is

        if "LGTM" in text:
            lgtm_found = True

        m = _REGRESSION_RE.search(text)
        if m:
            regressions.append(
                {
                    "file": m.group(1).strip(),
                    "line": int(m.group(2)),
                    "description": m.group(3).strip(),
                }
            )

    return regressions, lgtm_found


def _build_envelope(regressions: list[dict], lgtm_found: bool) -> dict:
    """Build an execution-result.schema.json envelope."""
    n = len(regressions)

    if n == 0:
        status = "ok"
        summary = "LGTM" if lgtm_found else "Codex review: 0 regressions found"
    else:
        status = "warning"
        summary = f"Codex review: {n} regression{'s' if n != 1 else ''} found"

    return {
        "status": status,
        "summary": summary,
        "data": {
            "regressions": regressions,
            "lgtm": lgtm_found,
            "total_findings": n,
        },
        "errors": [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": _CONTRACT_VERSION,
            "producer": _PRODUCER,
            "generated_at": _now_iso(),
            "schema": _SCHEMA,
        },
    }


def parse(lines: list[str]) -> dict:
    """Parse lines and return the execution-result envelope (testable entry point)."""
    regressions, lgtm_found = _parse_lines(lines)
    return _build_envelope(regressions, lgtm_found)


def main() -> int:
    if len(sys.argv) >= 2:
        path = Path(sys.argv[1])
        try:
            lines = path.read_text().splitlines()
        except OSError as exc:
            print(f"Error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
    else:
        lines = sys.stdin.read().splitlines()

    envelope = parse(lines)
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
