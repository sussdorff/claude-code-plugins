#!/usr/bin/env python3
"""Deep analysis of LinkedIn connections network.

Provides company distribution, role/title clustering, and connection
timeline analysis from a Connections.csv GDPR export file.

Usage:
    uv run python connections_analysis.py /path/to/Connections.csv [--top N] [--output json|markdown]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file with encoding fallback: utf-8-sig -> utf-8 -> latin-1.

    Handles LinkedIn GDPR exports that have preamble lines (Notes, disclaimers)
    before the actual CSV header by scanning for the header row.
    """
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as f:
                lines = f.readlines()
            # Find the actual header line (contains "First Name" for Connections.csv)
            header_idx = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and "," in stripped and not stripped.startswith(("Notes", '"When', '"')):
                    header_idx = i
                    break
            csv_text = "".join(lines[header_idx:])
            import io
            return list(csv.DictReader(io.StringIO(csv_text)))
        except (UnicodeDecodeError, UnicodeError):
            continue
    return []


def parse_date(text: str) -> datetime | None:
    """Try multiple date formats, return datetime or None."""
    if not text or not text.strip():
        return None
    text = text.strip()
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


# --- Role clustering ---

ROLE_CLUSTERS: dict[str, list[str]] = {
    "C-Suite": ["ceo", "cto", "cfo", "coo", "cio", "cmo", "chief"],
    "VP / Director": ["vp", "vice president", "director", "head of"],
    "Engineering": ["engineer", "developer", "programmer", "software", "sre", "devops", "backend", "frontend", "fullstack", "full-stack", "full stack"],
    "Data / ML": ["data", "machine learning", "ml ", "ai ", "analytics", "scientist"],
    "Product": ["product manager", "product owner", "product lead"],
    "Design": ["designer", "ux", "ui ", "design lead"],
    "Management": ["manager", "lead", "team lead", "principal"],
    "Sales / BD": ["sales", "account executive", "business development", "bd "],
    "Marketing": ["marketing", "growth", "content", "brand"],
    "HR / People": ["recruiter", "recruiting", "talent", "people", "human resources", "hr "],
    "Consulting": ["consultant", "advisor", "consulting"],
    "Founder": ["founder", "co-founder", "cofounder", "entrepreneur"],
    "Student / Intern": ["student", "intern", "trainee", "apprentice"],
}


def classify_role(title: str) -> str:
    """Classify a job title into a role cluster."""
    if not title:
        return "Other"
    lower = title.lower()
    for cluster_name, keywords in ROLE_CLUSTERS.items():
        for keyword in keywords:
            if keyword in lower:
                return cluster_name
    return "Other"


# --- Data models ---

@dataclass
class CompanyStats:
    name: str
    count: int
    titles: list[str] = field(default_factory=list)


@dataclass
class TimelineBucket:
    period: str
    count: int


@dataclass
class ConnectionsReport:
    total_connections: int = 0
    date_range: tuple[str, str] | None = None
    company_distribution: list[CompanyStats] = field(default_factory=list)
    role_distribution: dict[str, int] = field(default_factory=dict)
    timeline_monthly: list[TimelineBucket] = field(default_factory=list)
    timeline_yearly: list[TimelineBucket] = field(default_factory=list)
    connections_without_company: int = 0
    connections_without_date: int = 0


def analyze_connections(rows: list[dict[str, str]], top_n: int = 20) -> ConnectionsReport:
    """Run deep analysis on connections data."""
    report = ConnectionsReport(total_connections=len(rows))

    companies: dict[str, list[str]] = {}
    role_counts: Counter[str] = Counter()
    monthly: Counter[str] = Counter()
    yearly: Counter[str] = Counter()
    dates: list[datetime] = []

    for row in rows:
        company = row.get("Company", "").strip()
        title = row.get("Position", row.get("Title", "")).strip()
        date_str = row.get("Connected On", "").strip()

        # Company analysis
        if company:
            if company not in companies:
                companies[company] = []
            if title:
                companies[company].append(title)
        else:
            report.connections_without_company += 1

        # Role analysis
        role = classify_role(title)
        role_counts[role] += 1

        # Timeline
        dt = parse_date(date_str)
        if dt:
            dates.append(dt)
            monthly[dt.strftime("%Y-%m")] += 1
            yearly[dt.strftime("%Y")] += 1
        else:
            report.connections_without_date += 1

    # Date range
    if dates:
        earliest = min(dates)
        latest = max(dates)
        report.date_range = (earliest.strftime("%Y-%m-%d"), latest.strftime("%Y-%m-%d"))

    # Top companies
    company_counts = sorted(companies.items(), key=lambda x: len(x[1]), reverse=True)
    report.company_distribution = [
        CompanyStats(name=name, count=len(titles), titles=list(set(titles))[:5])
        for name, titles in company_counts[:top_n]
    ]

    # Role distribution
    report.role_distribution = dict(role_counts.most_common())

    # Timeline (sorted chronologically)
    report.timeline_monthly = [
        TimelineBucket(period=k, count=v)
        for k, v in sorted(monthly.items())
    ]
    report.timeline_yearly = [
        TimelineBucket(period=k, count=v)
        for k, v in sorted(yearly.items())
    ]

    return report


def report_to_dict(report: ConnectionsReport) -> dict:
    """Convert to JSON-serializable dict."""
    return asdict(report)


def report_to_markdown(report: ConnectionsReport) -> str:
    """Generate markdown summary."""
    lines: list[str] = []
    lines.append("# LinkedIn Connections Deep Analysis")
    lines.append("")
    lines.append(f"**Total connections:** {report.total_connections}")
    if report.date_range:
        lines.append(f"**Date range:** {report.date_range[0]} to {report.date_range[1]}")
    if report.connections_without_company:
        lines.append(f"**Without company:** {report.connections_without_company}")
    if report.connections_without_date:
        lines.append(f"**Without date:** {report.connections_without_date}")
    lines.append("")

    # Company distribution table
    lines.append("## Top Companies")
    lines.append("")
    lines.append("| # | Company | Connections | Sample Titles |")
    lines.append("|---|---------|-------------|---------------|")
    for i, cs in enumerate(report.company_distribution, 1):
        titles_str = ", ".join(cs.titles[:3]) if cs.titles else "-"
        lines.append(f"| {i} | {cs.name} | {cs.count} | {titles_str} |")
    lines.append("")

    # Role distribution
    lines.append("## Role Distribution")
    lines.append("")
    lines.append("| Role Cluster | Count | % |")
    lines.append("|-------------|-------|---|")
    total = report.total_connections or 1
    for role, count in sorted(report.role_distribution.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        lines.append(f"| {role} | {count} | {pct:.1f}% |")
    lines.append("")

    # Yearly timeline
    lines.append("## Connections by Year")
    lines.append("")
    for bucket in report.timeline_yearly:
        bar = "#" * min(bucket.count, 80)
        lines.append(f"  {bucket.period}: {bar} ({bucket.count})")
    lines.append("")

    # Monthly timeline (last 24 months if available)
    if report.timeline_monthly:
        recent = report.timeline_monthly[-24:]
        lines.append("## Connections by Month (last 24 months)")
        lines.append("")
        for bucket in recent:
            bar = "#" * min(bucket.count, 60)
            lines.append(f"  {bucket.period}: {bar} ({bucket.count})")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deep analysis of LinkedIn connections from GDPR export."
    )
    parser.add_argument(
        "connections_csv",
        type=Path,
        help="Path to Connections.csv",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top companies to show (default: 20)",
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Write output to file instead of stdout",
    )
    args = parser.parse_args()

    csv_path = args.connections_csv.resolve()
    if not csv_path.is_file():
        print(f"Error: {csv_path} is not a file", file=sys.stderr)
        sys.exit(1)

    rows = read_csv(csv_path)
    if not rows:
        print("Error: no data found in CSV", file=sys.stderr)
        sys.exit(1)

    report = analyze_connections(rows, top_n=args.top)

    if args.output == "json":
        content = json.dumps(report_to_dict(report), indent=2, ensure_ascii=False)
    else:
        content = report_to_markdown(report)

    if args.output_file:
        args.output_file.write_text(content, encoding="utf-8")
        print(f"Output written to {args.output_file}")
    else:
        print(content)


if __name__ == "__main__":
    main()
