#!/usr/bin/env python3
"""
Invoke the business:council subagent for a contested vision principle.
Called once per contested principle (confirmed = N) during vision review.

Usage (called by the skill, not directly by end users):
    principle_id, principle_text, and evidence are passed as arguments.
"""

import sys

def invoke_council(principle_id: str, principle_text: str, evidence: str) -> None:
    """Invoke council subagent for a contested principle."""
    Agent(subagent_type="business:council", prompt=f"""
Architecture vision review — contested principle:

**{principle_id}**: {principle_text}

User evidence: {evidence}

Assess whether this principle should be revised, removed, or kept as-is.
Focus on architectural coherence, not stylistic preference.
""")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: council_review.py <principle_id> <principle_text> <evidence>", file=sys.stderr)
        sys.exit(1)
    invoke_council(sys.argv[1], sys.argv[2], sys.argv[3])
