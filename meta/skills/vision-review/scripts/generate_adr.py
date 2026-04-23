#!/usr/bin/env python3
"""
Generate a draft ADR for a contested vision principle.
Wraps scripts/vision_review.py::generate_draft_adr.

Usage:
    python3 scripts/generate_adr.py <vision_review_module_path>
    (Called programmatically by the vision-review skill workflow.)
"""

import sys
from pathlib import Path


def run(principle, evidence, council_finding, run_date, adr_dir=Path("docs/adr/drafts/")):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.vision_review import generate_draft_adr

    adr_path = generate_draft_adr(
        principle=principle,
        evidence=evidence,
        council_finding=council_finding,  # None if council skipped
        run_date=run_date,
        adr_dir=adr_dir,
    )
    return adr_path


if __name__ == "__main__":
    print("generate_adr.py: call run() programmatically from the skill workflow.")
    sys.exit(0)
