#!/usr/bin/env python3
"""
Generate the vision review report and compute the health score.
Wraps scripts/vision_review.py::compute_health_score and generate_review_report.

Usage:
    python3 scripts/generate_report.py <vision_review_module_path>
    (Called programmatically by the vision-review skill workflow.)
"""

from pathlib import Path
from scripts.vision_review import compute_health_score, generate_review_report


def run(vision_path, results, confirmed_ids, total_count, council_mode, report_dir=Path("docs/")):
    health_score = compute_health_score(confirmed_ids, total_count)
    report_path = generate_review_report(
        vision_path=vision_path,
        results=results,
        health_score=health_score,
        council_mode=council_mode,
        report_dir=report_dir,
    )
    return health_score, report_path
