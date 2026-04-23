#!/usr/bin/env python3
"""LinkedIn GDPR Export Analyzer - Main entry point.

Discovers and analyzes all CSV files in a LinkedIn GDPR data export,
producing JSON reports and markdown summaries.

Usage:
    uv run python gdpr_analyzer.py /path/to/export [--output json|markdown|both] [--output-dir /path/]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file with encoding fallback: utf-8-sig -> utf-8 -> latin-1."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except (UnicodeDecodeError, UnicodeError):
            continue
    return []


def parse_date(text: str, formats: list[str] | None = None) -> datetime | None:
    """Try multiple date formats, return datetime or None."""
    if not text or not text.strip():
        return None
    text = text.strip()
    if formats is None:
        formats = [
            "%d %b %Y",      # 15 Jan 2023
            "%Y-%m-%d",      # 2023-01-15
            "%m/%d/%Y",      # 01/15/2023
            "%m/%d/%y",      # 01/15/23
            "%d/%m/%Y",      # 15/01/2023
            "%b %d, %Y",     # Jan 15, 2023
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def date_range(dates: list[datetime]) -> tuple[str, str] | None:
    """Return (earliest, latest) as ISO date strings, or None if empty."""
    if not dates:
        return None
    earliest = min(dates)
    latest = max(dates)
    return earliest.strftime("%Y-%m-%d"), latest.strftime("%Y-%m-%d")


# --- Data models ---

@dataclass
class ConnectionsSummary:
    total: int = 0
    date_range: tuple[str, str] | None = None
    top_companies: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class MessagesSummary:
    total_messages: int = 0
    conversation_count: int = 0
    date_range: tuple[str, str] | None = None


@dataclass
class PositionsSummary:
    total: int = 0
    positions: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ProfileSummary:
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class SkillsSummary:
    total: int = 0
    skills: list[str] = field(default_factory=list)


@dataclass
class EndorsementsSummary:
    total: int = 0
    top_skills: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class SharesSummary:
    total: int = 0
    date_range: tuple[str, str] | None = None


@dataclass
class ReactionsSummary:
    total: int = 0
    type_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class InvitationsSummary:
    total: int = 0
    sent: int = 0
    received: int = 0


@dataclass
class ExportReport:
    export_path: str = ""
    files_found: list[str] = field(default_factory=list)
    files_missing: list[str] = field(default_factory=list)
    connections: ConnectionsSummary | None = None
    messages: MessagesSummary | None = None
    positions: PositionsSummary | None = None
    profile: ProfileSummary | None = None
    skills: SkillsSummary | None = None
    endorsements: EndorsementsSummary | None = None
    shares: SharesSummary | None = None
    reactions: ReactionsSummary | None = None
    invitations: InvitationsSummary | None = None


# --- Analyzers ---

KNOWN_FILES = [
    "Connections.csv",
    "Messages.csv",
    "Positions.csv",
    "Profile.csv",
    "Skills.csv",
    "Endorsement Received Info.csv",
    "Shares.csv",
    "Reactions.csv",
    "Invitations.csv",
]


def analyze_connections(rows: list[dict[str, str]]) -> ConnectionsSummary:
    companies: Counter[str] = Counter()
    dates: list[datetime] = []
    for row in rows:
        company = row.get("Company", "").strip()
        if company:
            companies[company] += 1
        dt = parse_date(row.get("Connected On", ""))
        if dt:
            dates.append(dt)
    return ConnectionsSummary(
        total=len(rows),
        date_range=date_range(dates),
        top_companies=companies.most_common(10),
    )


def analyze_messages(rows: list[dict[str, str]]) -> MessagesSummary:
    conversations: set[str] = set()
    dates: list[datetime] = []
    for row in rows:
        conv_id = row.get("CONVERSATION ID", row.get("Conversation ID", "")).strip()
        if conv_id:
            conversations.add(conv_id)
        date_str = row.get("DATE", row.get("Date", ""))
        dt = parse_date(date_str)
        if dt:
            dates.append(dt)
    return MessagesSummary(
        total_messages=len(rows),
        conversation_count=len(conversations),
        date_range=date_range(dates),
    )


def analyze_positions(rows: list[dict[str, str]]) -> PositionsSummary:
    positions = []
    for row in rows:
        positions.append({
            "company": row.get("Company Name", row.get("Company", "")).strip(),
            "title": row.get("Title", "").strip(),
            "started": row.get("Started On", "").strip(),
            "ended": row.get("Finished On", row.get("Ended On", "")).strip() or "Present",
        })
    return PositionsSummary(total=len(positions), positions=positions)


def analyze_profile(rows: list[dict[str, str]]) -> ProfileSummary:
    fields: dict[str, str] = {}
    for row in rows:
        for key, value in row.items():
            if value and value.strip():
                fields[key] = value.strip()
    return ProfileSummary(fields=fields)


def analyze_skills(rows: list[dict[str, str]]) -> SkillsSummary:
    skills = [row.get("Name", row.get("Skill", "")).strip() for row in rows if row]
    skills = [s for s in skills if s]
    return SkillsSummary(total=len(skills), skills=skills)


def analyze_endorsements(rows: list[dict[str, str]]) -> EndorsementsSummary:
    skill_counts: Counter[str] = Counter()
    for row in rows:
        skill = row.get("Skill Name", row.get("Skill", "")).strip()
        if skill:
            skill_counts[skill] += 1
    return EndorsementsSummary(
        total=len(rows),
        top_skills=skill_counts.most_common(10),
    )


def analyze_shares(rows: list[dict[str, str]]) -> SharesSummary:
    dates: list[datetime] = []
    for row in rows:
        date_str = row.get("Date", row.get("SharedDate", ""))
        dt = parse_date(date_str)
        if dt:
            dates.append(dt)
    return SharesSummary(total=len(rows), date_range=date_range(dates))


def analyze_reactions(rows: list[dict[str, str]]) -> ReactionsSummary:
    types: Counter[str] = Counter()
    for row in rows:
        rtype = row.get("Type", row.get("Reaction Type", "")).strip()
        if rtype:
            types[rtype] += 1
    return ReactionsSummary(total=len(rows), type_distribution=dict(types))


def analyze_invitations(rows: list[dict[str, str]]) -> InvitationsSummary:
    sent = 0
    received = 0
    for row in rows:
        direction = row.get("Direction", row.get("direction", "")).strip().upper()
        if direction == "OUTGOING" or direction == "SENT":
            sent += 1
        elif direction == "INCOMING" or direction == "RECEIVED":
            received += 1
    return InvitationsSummary(total=len(rows), sent=sent, received=received)


ANALYZERS: dict[str, tuple[str, type]] = {
    "Connections.csv": ("connections", ConnectionsSummary),
    "Messages.csv": ("messages", MessagesSummary),
    "Positions.csv": ("positions", PositionsSummary),
    "Profile.csv": ("profile", ProfileSummary),
    "Skills.csv": ("skills", SkillsSummary),
    "Endorsement Received Info.csv": ("endorsements", EndorsementsSummary),
    "Shares.csv": ("shares", SharesSummary),
    "Reactions.csv": ("reactions", ReactionsSummary),
    "Invitations.csv": ("invitations", InvitationsSummary),
}

ANALYZE_FUNCS = {
    "Connections.csv": analyze_connections,
    "Messages.csv": analyze_messages,
    "Positions.csv": analyze_positions,
    "Profile.csv": analyze_profile,
    "Skills.csv": analyze_skills,
    "Endorsement Received Info.csv": analyze_endorsements,
    "Shares.csv": analyze_shares,
    "Reactions.csv": analyze_reactions,
    "Invitations.csv": analyze_invitations,
}


def discover_csvs(export_dir: Path) -> dict[str, Path]:
    """Find all CSV files in the export directory (case-insensitive match)."""
    found: dict[str, Path] = {}
    if not export_dir.is_dir():
        return found
    known_lower = {name.lower(): name for name in KNOWN_FILES}
    for csv_file in export_dir.glob("*.csv"):
        lower_name = csv_file.name.lower()
        if lower_name in known_lower:
            found[known_lower[lower_name]] = csv_file
        else:
            found[csv_file.name] = csv_file
    return found


def analyze_export(export_dir: Path) -> ExportReport:
    """Run full analysis on a LinkedIn GDPR export directory."""
    report = ExportReport(export_path=str(export_dir))
    csvs = discover_csvs(export_dir)

    report.files_found = sorted(csvs.keys())
    report.files_missing = sorted(set(KNOWN_FILES) - set(csvs.keys()))

    for filename, filepath in csvs.items():
        if filename not in ANALYZE_FUNCS:
            continue
        rows = read_csv(filepath)
        if not rows:
            continue
        attr_name = ANALYZERS[filename][0]
        result = ANALYZE_FUNCS[filename](rows)
        setattr(report, attr_name, result)

    return report


# --- Output formatters ---

def report_to_dict(report: ExportReport) -> dict:
    """Convert report to a JSON-serializable dict."""
    d = asdict(report)
    # Remove None values for cleaner output
    return {k: v for k, v in d.items() if v is not None}


def report_to_markdown(report: ExportReport) -> str:
    """Generate a markdown summary of the report."""
    lines: list[str] = []
    lines.append("# LinkedIn GDPR Export Analysis")
    lines.append("")
    lines.append(f"**Export path:** `{report.export_path}`")
    lines.append(f"**Files found:** {len(report.files_found)}")
    if report.files_missing:
        lines.append(f"**Files missing:** {', '.join(report.files_missing)}")
    lines.append("")

    if report.connections:
        c = report.connections
        lines.append("## Connections")
        lines.append(f"- **Total:** {c.total}")
        if c.date_range:
            lines.append(f"- **Date range:** {c.date_range[0]} to {c.date_range[1]}")
        if c.top_companies:
            lines.append("- **Top companies:**")
            for company, count in c.top_companies:
                lines.append(f"  - {company}: {count}")
        lines.append("")

    if report.messages:
        m = report.messages
        lines.append("## Messages")
        lines.append(f"- **Total messages:** {m.total_messages}")
        lines.append(f"- **Conversations:** {m.conversation_count}")
        if m.date_range:
            lines.append(f"- **Date range:** {m.date_range[0]} to {m.date_range[1]}")
        lines.append("")

    if report.positions:
        p = report.positions
        lines.append("## Career History")
        lines.append(f"- **Total positions:** {p.total}")
        for pos in p.positions:
            period = f"{pos['started']} - {pos['ended']}"
            lines.append(f"  - **{pos['title']}** at {pos['company']} ({period})")
        lines.append("")

    if report.profile:
        lines.append("## Profile")
        for key, value in report.profile.fields.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    if report.skills:
        s = report.skills
        lines.append("## Skills")
        lines.append(f"- **Total:** {s.total}")
        if s.skills:
            lines.append(f"- {', '.join(s.skills)}")
        lines.append("")

    if report.endorsements:
        e = report.endorsements
        lines.append("## Endorsements")
        lines.append(f"- **Total:** {e.total}")
        if e.top_skills:
            lines.append("- **Top endorsed skills:**")
            for skill, count in e.top_skills:
                lines.append(f"  - {skill}: {count}")
        lines.append("")

    if report.shares:
        s = report.shares
        lines.append("## Shares/Posts")
        lines.append(f"- **Total:** {s.total}")
        if s.date_range:
            lines.append(f"- **Date range:** {s.date_range[0]} to {s.date_range[1]}")
        lines.append("")

    if report.reactions:
        r = report.reactions
        lines.append("## Reactions")
        lines.append(f"- **Total:** {r.total}")
        if r.type_distribution:
            for rtype, count in r.type_distribution.items():
                lines.append(f"  - {rtype}: {count}")
        lines.append("")

    if report.invitations:
        i = report.invitations
        lines.append("## Invitations")
        lines.append(f"- **Total:** {i.total}")
        lines.append(f"- **Sent:** {i.sent}")
        lines.append(f"- **Received:** {i.received}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a LinkedIn GDPR data export."
    )
    parser.add_argument(
        "export_dir",
        type=Path,
        help="Path to the LinkedIn GDPR export directory",
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output files (default: export directory)",
    )
    args = parser.parse_args()

    export_dir = args.export_dir.resolve()
    if not export_dir.is_dir():
        print(f"Error: {export_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    output_dir = (args.output_dir or export_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report = analyze_export(export_dir)

    if args.output in ("json", "both"):
        json_path = output_dir / "linkedin_analysis.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report_to_dict(report), f, indent=2, ensure_ascii=False)
        print(f"JSON report written to {json_path}")

    if args.output in ("markdown", "both"):
        md_path = output_dir / "linkedin_analysis.md"
        md_path.write_text(report_to_markdown(report), encoding="utf-8")
        print(f"Markdown report written to {md_path}")

    # Also print markdown to stdout for quick viewing
    print()
    print(report_to_markdown(report))


if __name__ == "__main__":
    main()
