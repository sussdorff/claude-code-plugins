#!/usr/bin/env python3
"""Extract user's own LinkedIn content for pipeline integration.

Parses Shares.csv, Reactions.csv, and Comments.csv from a LinkedIn GDPR export
and outputs structured content suitable for other tools.

Usage:
    uv run python content_extractor.py /path/to/export [--format json|markdown]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
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


def parse_date(text: str) -> datetime | None:
    """Try multiple date formats, return datetime or None."""
    if not text or not text.strip():
        return None
    text = text.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


@dataclass
class Post:
    date: str
    text: str
    url: str = ""
    media_url: str = ""
    shared_url: str = ""


@dataclass
class Reaction:
    date: str
    reaction_type: str
    target_url: str = ""


@dataclass
class Comment:
    date: str
    text: str
    target_url: str = ""


@dataclass
class ContentReport:
    posts: list[Post] = field(default_factory=list)
    reactions: list[Reaction] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    post_count: int = 0
    reaction_count: int = 0
    comment_count: int = 0


def extract_posts(rows: list[dict[str, str]]) -> list[Post]:
    """Extract posts from Shares.csv rows."""
    posts: list[Post] = []
    for row in rows:
        date_str = row.get("Date", row.get("SharedDate", ""))
        dt = parse_date(date_str)
        date_out = dt.strftime("%Y-%m-%d") if dt else date_str.strip()

        text = row.get("ShareCommentary", row.get("Commentary", row.get("Text", ""))).strip()
        url = row.get("ShareLink", row.get("PostLink", row.get("Url", ""))).strip()
        media_url = row.get("MediaUrl", row.get("Media Url", "")).strip()
        shared_url = row.get("SharedUrl", row.get("Shared Url", "")).strip()

        posts.append(Post(
            date=date_out,
            text=text,
            url=url,
            media_url=media_url,
            shared_url=shared_url,
        ))

    # Sort by date descending
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def extract_reactions(rows: list[dict[str, str]]) -> list[Reaction]:
    """Extract reactions from Reactions.csv rows."""
    reactions: list[Reaction] = []
    for row in rows:
        date_str = row.get("Date", "")
        dt = parse_date(date_str)
        date_out = dt.strftime("%Y-%m-%d") if dt else date_str.strip()

        reaction_type = row.get("Type", row.get("Reaction Type", "")).strip()
        target_url = row.get("Link", row.get("Url", row.get("Target Url", ""))).strip()

        reactions.append(Reaction(
            date=date_out,
            reaction_type=reaction_type,
            target_url=target_url,
        ))

    reactions.sort(key=lambda r: r.date, reverse=True)
    return reactions


def extract_comments(rows: list[dict[str, str]]) -> list[Comment]:
    """Extract comments from Comments.csv rows."""
    comments: list[Comment] = []
    for row in rows:
        date_str = row.get("Date", "")
        dt = parse_date(date_str)
        date_out = dt.strftime("%Y-%m-%d") if dt else date_str.strip()

        text = row.get("Message", row.get("Comment", row.get("Text", ""))).strip()
        target_url = row.get("Link", row.get("Url", "")).strip()

        comments.append(Comment(
            date=date_out,
            text=text,
            target_url=target_url,
        ))

    comments.sort(key=lambda c: c.date, reverse=True)
    return comments


def extract_content(export_dir: Path) -> ContentReport:
    """Extract all user content from a GDPR export directory."""
    report = ContentReport()

    shares_path = export_dir / "Shares.csv"
    if shares_path.exists():
        rows = read_csv(shares_path)
        report.posts = extract_posts(rows)
        report.post_count = len(report.posts)

    reactions_path = export_dir / "Reactions.csv"
    if reactions_path.exists():
        rows = read_csv(reactions_path)
        report.reactions = extract_reactions(rows)
        report.reaction_count = len(report.reactions)

    comments_path = export_dir / "Comments.csv"
    if comments_path.exists():
        rows = read_csv(comments_path)
        report.comments = extract_comments(rows)
        report.comment_count = len(report.comments)

    return report


def report_to_dict(report: ContentReport) -> dict:
    """Convert to JSON-serializable dict."""
    return asdict(report)


def report_to_markdown(report: ContentReport) -> str:
    """Generate markdown summary."""
    lines: list[str] = []
    lines.append("# LinkedIn Content Extract")
    lines.append("")
    lines.append(f"- **Posts:** {report.post_count}")
    lines.append(f"- **Reactions:** {report.reaction_count}")
    lines.append(f"- **Comments:** {report.comment_count}")
    lines.append("")

    if report.posts:
        lines.append("## Posts")
        lines.append("")
        for post in report.posts:
            lines.append(f"### {post.date}")
            if post.text:
                lines.append("")
                lines.append(post.text)
            if post.url:
                lines.append(f"\n[Post link]({post.url})")
            if post.shared_url:
                lines.append(f"[Shared link]({post.shared_url})")
            if post.media_url:
                lines.append(f"[Media]({post.media_url})")
            lines.append("")
            lines.append("---")
            lines.append("")

    if report.comments:
        lines.append("## Comments")
        lines.append("")
        for comment in report.comments:
            lines.append(f"**{comment.date}**: {comment.text}")
            if comment.target_url:
                lines.append(f"  [Link]({comment.target_url})")
            lines.append("")

    if report.reactions:
        lines.append("## Reactions")
        lines.append("")
        lines.append("| Date | Type | Target |")
        lines.append("|------|------|--------|")
        for reaction in report.reactions[:50]:  # Limit table size
            target = f"[link]({reaction.target_url})" if reaction.target_url else "-"
            lines.append(f"| {reaction.date} | {reaction.reaction_type} | {target} |")
        if len(report.reactions) > 50:
            lines.append(f"\n*... and {len(report.reactions) - 50} more reactions*")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract LinkedIn content from GDPR export."
    )
    parser.add_argument(
        "export_dir",
        type=Path,
        help="Path to the LinkedIn GDPR export directory",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Write output to file instead of stdout",
    )
    args = parser.parse_args()

    export_dir = args.export_dir.resolve()
    if not export_dir.is_dir():
        print(f"Error: {export_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    report = extract_content(export_dir)

    if args.format == "json":
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
