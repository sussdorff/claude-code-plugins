#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "python-dateutil>=2.8.2"
# ]
# ///
"""
Git Commit Analyzer for timing-matcher

Parses git logs and correlates commits with time tracking activities.
"""

import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from dateutil import parser as date_parser


@dataclass
class Commit:
    """Represents a git commit."""
    sha: str
    timestamp: datetime
    message: str
    author: str
    tickets: Set[str]


class GitAnalyzer:
    """Analyzes git repositories and correlates commits with activities."""

    def __init__(self, repo_path: Path, ticket_prefixes: List[str]):
        """
        Initialize git analyzer.

        Args:
            repo_path: Path to git repository
            ticket_prefixes: List of ticket prefixes to extract (e.g., ["CH2-", "FALL-"])
        """
        self.repo_path = Path(repo_path).expanduser()
        self.ticket_prefixes = ticket_prefixes
        self.commits: List[Commit] = []
        self.commits_by_date: Dict[str, List[Commit]] = defaultdict(list)
        self.commits_by_ticket: Dict[str, List[Commit]] = defaultdict(list)

    def load_commits(self, start_date: str, end_date: str) -> None:
        """
        Load commits from repository for date range.

        Args:
            start_date: ISO date string (e.g., "2025-08-01")
            end_date: ISO date string (e.g., "2025-10-31")
        """
        if not self.repo_path.exists():
            print(f"Warning: Git repo not found: {self.repo_path}", file=sys.stderr)
            return

        try:
            # Run git log
            result = subprocess.run(
                [
                    "git", "log",
                    f"--since={start_date}",
                    f"--until={end_date}",
                    "--format=%H|%ai|%s|%an",
                    "--all"
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse commits
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 3)
                if len(parts) != 4:
                    continue

                sha, timestamp_str, message, author = parts
                timestamp = date_parser.parse(timestamp_str)

                # Extract tickets from commit message
                tickets = self._extract_tickets(message)

                commit = Commit(
                    sha=sha[:8],  # Short SHA
                    timestamp=timestamp,
                    message=message,
                    author=author,
                    tickets=tickets
                )

                self.commits.append(commit)

                # Index by date
                date_key = timestamp.date().isoformat()
                self.commits_by_date[date_key].append(commit)

                # Index by ticket
                for ticket in tickets:
                    self.commits_by_ticket[ticket].append(commit)

            print(f"Loaded {len(self.commits)} commits from {self.repo_path.name}",
                  file=sys.stderr)

        except subprocess.CalledProcessError as e:
            print(f"Error running git log: {e.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Error loading commits: {e}", file=sys.stderr)

    def _extract_tickets(self, text: str) -> Set[str]:
        """
        Extract ticket numbers from text.

        Args:
            text: Text to search

        Returns:
            Set of ticket numbers (e.g., {"CH2-13130", "FALL-1510"})
        """
        tickets = set()
        for prefix in self.ticket_prefixes:
            # Create pattern like (CH2-\d+)
            pattern = f"({re.escape(prefix)}\\d+)"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            tickets.update(m.group(1).upper() for m in matches)
        return tickets

    def find_commits_for_activity(
        self,
        activity_start: datetime,
        activity_end: datetime,
        ticket: Optional[str] = None,
        time_window_minutes: int = 15
    ) -> List[Commit]:
        """
        Find commits that correlate with an activity.

        Args:
            activity_start: Activity start time
            activity_end: Activity end time
            ticket: Optional ticket number to prefer
            time_window_minutes: Time window (±minutes) for matching

        Returns:
            List of matching commits, sorted by relevance
        """
        # Expand search window
        search_start = activity_start - timedelta(minutes=time_window_minutes)
        search_end = activity_end + timedelta(minutes=time_window_minutes)

        # If ticket specified, prioritize commits with that ticket
        if ticket and ticket in self.commits_by_ticket:
            ticket_commits = [
                c for c in self.commits_by_ticket[ticket]
                if search_start <= c.timestamp <= search_end
            ]
            if ticket_commits:
                return ticket_commits

        # Otherwise find commits by time range
        matching_commits = []
        date_key = activity_start.date().isoformat()

        # Check commits on the activity date
        for commit in self.commits_by_date.get(date_key, []):
            if search_start <= commit.timestamp <= search_end:
                matching_commits.append(commit)

        # Also check previous/next day if activity spans midnight
        if activity_start.date() != activity_end.date():
            next_date = activity_end.date().isoformat()
            for commit in self.commits_by_date.get(next_date, []):
                if search_start <= commit.timestamp <= search_end:
                    matching_commits.append(commit)

        return sorted(matching_commits, key=lambda c: c.timestamp)

    def format_commit_notes(self, commits: List[Commit]) -> str:
        """
        Format commits as notes string for time entry.

        Args:
            commits: List of commits

        Returns:
            Formatted string like "Commits: abc123, def456"
        """
        if not commits:
            return ""

        commit_refs = ", ".join(c.sha for c in commits)
        return f"Commits: {commit_refs}"

    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about loaded commits.

        Returns:
            Dictionary of statistics
        """
        return {
            "total_commits": len(self.commits),
            "date_range": (
                min(c.timestamp for c in self.commits).date().isoformat()
                if self.commits else None,
                max(c.timestamp for c in self.commits).date().isoformat()
                if self.commits else None
            ),
            "tickets_found": len(self.commits_by_ticket),
            "authors": len(set(c.author for c in self.commits))
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Analyze git commits")
    parser.add_argument("repo_path", type=Path, help="Path to git repository")
    parser.add_argument("--start-date", required=True, help="Start date (ISO format)")
    parser.add_argument("--end-date", required=True, help="End date (ISO format)")
    parser.add_argument("--ticket-prefixes", nargs="+", default=["CH2-", "FALL-"],
                        help="Ticket prefixes to extract")
    parser.add_argument("--stats-only", action="store_true",
                        help="Only show statistics")

    args = parser.parse_args()

    analyzer = GitAnalyzer(args.repo_path, args.ticket_prefixes)
    analyzer.load_commits(args.start_date, args.end_date)

    stats = analyzer.get_stats()
    print(json.dumps(stats, indent=2))

    if not args.stats_only and analyzer.commits:
        print("\nCommits by ticket:", file=sys.stderr)
        for ticket, commits in sorted(analyzer.commits_by_ticket.items()):
            print(f"  {ticket}: {len(commits)} commits", file=sys.stderr)
