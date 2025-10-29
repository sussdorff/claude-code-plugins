#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "python-dateutil>=2.8.2",
#   "pydantic>=2.0.0",
#   "rich>=13.0.0"
# ]
# ///
"""
Timing Activity Matcher

Main orchestrator that processes Timing exports and generates time entry proposals.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from dateutil import parser as date_parser
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

# Import local modules (will be in same directory)
from chunker import chunk_by_week, get_date_range, count_entries
from git_analyzer import GitAnalyzer, Commit
from aggregator import Aggregator, Activity, TimeEntry


# Configuration models
class ProjectMapping(BaseModel):
    """Project mapping configuration."""
    project_name: str
    project_id: str
    description: Optional[str] = None


class ActivityPattern(BaseModel):
    """Activity pattern configuration."""
    pattern: str
    regex: bool = False
    project_name: str
    project_id: str
    description: Optional[str] = None


class MatchingConfig(BaseModel):
    """Matching behavior configuration."""
    min_duration_seconds: int = 30
    max_gap_minutes: int = 15
    commit_time_window_minutes: int = 15
    confidence_thresholds: Dict[str, float] = Field(
        default={"high": 0.85, "medium": 0.6, "low": 0.3}
    )


class GitRepoConfig(BaseModel):
    """Git repository configuration."""
    path: str
    ticket_prefixes: List[str]
    description: Optional[str] = None


class OutputConfig(BaseModel):
    """Output configuration."""
    include_source_activities: bool = True
    include_commit_shas: bool = True
    group_by_project: bool = True


class Config(BaseModel):
    """Complete matcher configuration."""
    project_mappings: Dict[str, any]
    matching: MatchingConfig = Field(default_factory=MatchingConfig)
    git_repos: List[GitRepoConfig] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)


class Matcher:
    """Main matcher orchestrator."""

    def __init__(self, config: Config):
        """
        Initialize matcher.

        Args:
            config: Configuration object
        """
        self.config = config
        self.console = Console(stderr=True)
        self.git_analyzers: List[GitAnalyzer] = []
        self.aggregator = Aggregator(
            min_duration_seconds=config.matching.min_duration_seconds,
            max_gap_minutes=config.matching.max_gap_minutes
        )

        # Compile patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.ticket_patterns = {}
        for prefix, mapping in self.config.project_mappings.get("ticketPrefixes", {}).items():
            pattern = f"({re.escape(prefix)}\\d+)"
            self.ticket_patterns[prefix] = {
                "regex": re.compile(pattern, re.IGNORECASE),
                "mapping": mapping
            }

        self.activity_patterns = []
        for pattern_config in self.config.project_mappings.get("activityPatterns", []):
            if pattern_config.get("regex", False):
                compiled = re.compile(pattern_config["pattern"], re.IGNORECASE)
            else:
                # Convert literal to simple contains check
                compiled = pattern_config["pattern"].lower()

            self.activity_patterns.append({
                "compiled": compiled,
                "regex": pattern_config.get("regex", False),
                "mapping": pattern_config
            })

        self.ignore_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.config.project_mappings.get("ignorePatterns", [])
        ]

    def load_git_repos(self, start_date: str, end_date: str):
        """Load git repositories and their commits."""
        for repo_config in self.config.git_repos:
            analyzer = GitAnalyzer(
                Path(repo_config.path),
                repo_config.ticket_prefixes
            )
            analyzer.load_commits(start_date, end_date)
            self.git_analyzers.append(analyzer)

    def match_activity(self, raw_activity: Dict) -> Optional[Activity]:
        """
        Match a single activity to a project.

        Args:
            raw_activity: Raw activity dictionary from JSON

        Returns:
            Activity object with matching metadata, or None if ignored
        """
        activity_title = raw_activity.get("activityTitle")
        application = raw_activity.get("application", "Unknown")

        # Check ignore patterns
        for ignore_pattern in self.ignore_patterns:
            if activity_title and ignore_pattern.search(activity_title):
                return None
            if ignore_pattern.search(application):
                return None

        # Parse dates
        try:
            start_date = date_parser.parse(raw_activity["startDate"])
            end_date = date_parser.parse(raw_activity["endDate"])
        except (KeyError, ValueError) as e:
            self.console.print(f"[yellow]Warning: Invalid dates in activity: {e}[/yellow]")
            return None

        # Create activity object
        activity = Activity(
            activity_title=activity_title,
            application=application,
            duration_str=raw_activity.get("duration", ""),
            start_date=start_date,
            end_date=end_date,
            path=raw_activity.get("path")
        )

        # Try ticket matching first (highest confidence)
        ticket, mapping = self._match_ticket(activity_title or "")
        if ticket and mapping:
            activity.ticket = ticket
            activity.project_id = mapping["projectId"]
            activity.project_name = mapping["projectName"]
            activity.confidence = 0.95
            activity.match_reason = f"Exact ticket match: {ticket}"
            return activity

        # Try activity pattern matching
        mapping = self._match_pattern(activity_title or "", application)
        if mapping:
            activity.project_id = mapping["projectId"]
            activity.project_name = mapping["projectName"]
            activity.confidence = 0.75
            activity.match_reason = f"Pattern match: {mapping.get('description', 'activity pattern')}"
            return activity

        # No match found
        activity.confidence = 0.2
        activity.match_reason = "No pattern matched"
        return activity

    def _match_ticket(self, text: str) -> tuple[Optional[str], Optional[Dict]]:
        """
        Extract ticket number and find matching project.

        Args:
            text: Text to search

        Returns:
            Tuple of (ticket_number, project_mapping) or (None, None)
        """
        for prefix, pattern_info in self.ticket_patterns.items():
            match = pattern_info["regex"].search(text)
            if match:
                ticket = match.group(1).upper()
                return ticket, pattern_info["mapping"]
        return None, None

    def _match_pattern(self, activity_title: str, application: str) -> Optional[Dict]:
        """
        Match activity against configured patterns.

        Args:
            activity_title: Activity title
            application: Application name

        Returns:
            Project mapping or None
        """
        search_text = f"{activity_title} {application}".lower()

        for pattern_info in self.activity_patterns:
            if pattern_info["regex"]:
                if pattern_info["compiled"].search(search_text):
                    return pattern_info["mapping"]
            else:
                if pattern_info["compiled"] in search_text:
                    return pattern_info["mapping"]

        return None

    def enrich_with_commits(self, entries: List[TimeEntry]):
        """
        Add git commit information to time entries.

        Args:
            entries: List of time entries to enrich
        """
        if not self.git_analyzers or not self.config.output.include_commit_shas:
            return

        window_minutes = self.config.matching.commit_time_window_minutes

        for entry in entries:
            all_commits: List[Commit] = []

            # Search all git repos
            for analyzer in self.git_analyzers:
                # Use first activity's ticket if available
                ticket = None
                for activity in entry.source_activities:
                    if activity.ticket:
                        ticket = activity.ticket
                        break

                commits = analyzer.find_commits_for_activity(
                    entry.start_date,
                    entry.end_date,
                    ticket=ticket,
                    time_window_minutes=window_minutes
                )
                all_commits.extend(commits)

            if all_commits:
                entry.commit_shas = [c.sha for c in all_commits]
                commit_notes = analyzer.format_commit_notes(all_commits)
                if entry.notes:
                    entry.notes = f"{entry.notes}\n{commit_notes}"
                else:
                    entry.notes = commit_notes

    def process(
        self,
        input_file: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Process the input file and generate matches.

        Args:
            input_file: Path to Timing JSON export
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Results dictionary
        """
        self.console.print("[bold blue]Starting Timing Matcher...[/bold blue]")

        # Get date range
        if not start_date or not end_date:
            self.console.print("Determining date range from file...")
            file_start, file_end = get_date_range(input_file)
            start_date = start_date or file_start
            end_date = end_date or file_end

        self.console.print(f"Date range: {start_date} to {end_date}")

        # Load git commits
        self.console.print("Loading git commits...")
        self.load_git_repos(start_date, end_date)

        # Process in chunks
        self.console.print("Processing activities...")
        all_activities: List[Activity] = []
        matched_count = 0
        ignored_count = 0
        total_count = 0

        for week_start, week_end, raw_activities in chunk_by_week(
            input_file, start_date, end_date
        ):
            self.console.print(f"  Week {week_start}: {len(raw_activities)} entries")

            for raw_activity in raw_activities:
                total_count += 1
                activity = self.match_activity(raw_activity)

                if activity is None:
                    ignored_count += 1
                    continue

                if activity.project_id:
                    matched_count += 1

                all_activities.append(activity)

        # Aggregate into time entries
        self.console.print("\nAggregating time entries...")
        matched_activities = [a for a in all_activities if a.project_id]
        entries = self.aggregator.aggregate(matched_activities)

        # Enrich with git commits
        self.console.print("Enriching with git commit data...")
        self.enrich_with_commits(entries)

        # Generate output
        results = self._generate_output(
            entries, all_activities, matched_count, ignored_count, total_count,
            start_date, end_date
        )

        return results

    def _generate_output(
        self,
        entries: List[TimeEntry],
        all_activities: List[Activity],
        matched_count: int,
        ignored_count: int,
        total_count: int,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Generate final output dictionary."""
        # Calculate confidence distribution
        confidence_dist = self.aggregator.get_confidence_distribution(entries)

        # Group by project
        by_project = defaultdict(list)
        for entry in entries:
            by_project[entry.project_name].append(entry)

        project_mappings = []
        for project_name, project_entries in by_project.items():
            total_seconds = sum(e.duration_seconds for e in project_entries)
            hours = total_seconds / 3600

            project_mappings.append({
                "projectName": project_name,
                "projectId": project_entries[0].project_id,
                "entryCount": len(project_entries),
                "totalDuration": f"PT{int(total_seconds//3600)}H{int((total_seconds%3600)//60)}M"
            })

        # Analyze unmatched
        unmatched = [a for a in all_activities if not a.project_id]
        unmatched_summary = self._summarize_unmatched(unmatched)

        return {
            "metadata": {
                "processedDate": datetime.now().isoformat(),
                "totalInputEntries": total_count,
                "matchedEntries": matched_count,
                "unmatchedEntries": len(unmatched),
                "ignoredEntries": ignored_count,
                "proposedTimeEntries": len(entries),
                "confidenceDistribution": confidence_dist
            },
            "projectMappings": project_mappings,
            "proposedEntries": [
                {
                    "startDate": e.start_date.isoformat(),
                    "endDate": e.end_date.isoformat(),
                    "project": e.project_id,
                    "title": e.title,
                    "notes": e.notes,
                    "confidence": e.confidence,
                    "sourceActivities": [
                        {
                            "activityTitle": a.activity_title,
                            "application": a.application,
                            "duration": a.duration_str
                        }
                        for a in e.source_activities
                    ] if self.config.output.include_source_activities else []
                }
                for e in entries
            ],
            "unmatchedSummary": unmatched_summary
        }

    def _summarize_unmatched(self, unmatched: List[Activity]) -> List[Dict]:
        """Summarize unmatched activities for review."""
        # Count by activity title
        patterns = Counter()
        for activity in unmatched:
            key = activity.activity_title or activity.application
            patterns[key] += 1

        return [
            {"pattern": pattern, "count": count, "reason": "No matching pattern"}
            for pattern, count in patterns.most_common(20)
        ]

    def print_summary(self, results: Dict):
        """Print human-readable summary."""
        self.console.print("\n[bold green]Processing Complete![/bold green]")
        self.console.print("━" * 60)

        # Input statistics
        meta = results["metadata"]
        self.console.print("\n[bold]Input Statistics:[/bold]")
        self.console.print(f"  Total entries: {meta['totalInputEntries']:,}")

        # Matching results
        self.console.print("\n[bold]Matching Results:[/bold]")
        matched = meta["matchedEntries"]
        total = meta["totalInputEntries"]
        pct = (matched / total * 100) if total > 0 else 0

        dist = meta["confidenceDistribution"]
        self.console.print(f"  ✓ High confidence: {dist.get('high', 0):,} entries")
        self.console.print(f"  ≈ Medium confidence: {dist.get('medium', 0):,} entries")
        self.console.print(f"  ? Low confidence: {dist.get('low', 0):,} entries")
        self.console.print(f"  ✗ Unmatched: {meta['unmatchedEntries']:,} entries")
        self.console.print(f"\n  Match rate: {pct:.1f}%")

        # Proposed entries
        self.console.print(f"\n[bold]Proposed Time Entries:[/bold] {meta['proposedTimeEntries']}")

        # Project breakdown
        table = Table(title="\nProject Summary")
        table.add_column("Project", style="cyan")
        table.add_column("Entries", justify="right")
        table.add_column("Duration", justify="right")

        for mapping in sorted(results["projectMappings"], key=lambda x: -x["entryCount"]):
            table.add_row(
                mapping["projectName"],
                str(mapping["entryCount"]),
                mapping["totalDuration"]
            )

        self.console.print(table)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Match Timing activities to projects")
    parser.add_argument("--input", type=Path, help="Input JSON file")
    parser.add_argument("--config", type=Path, default="matcher-config.json",
                        help="Configuration file")
    parser.add_argument("--output", type=Path, default="matches.json",
                        help="Output file")
    parser.add_argument("--start-date", help="Start date (ISO format)")
    parser.add_argument("--end-date", help="End date (ISO format)")

    args = parser.parse_args()

    # Load configuration
    if not args.config.exists():
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        print("Hint: Copy assets/matcher-config-template.json to matcher-config.json", file=sys.stderr)
        sys.exit(1)

    with open(args.config) as f:
        config_data = json.load(f)
    config = Config(**config_data)

    # Run matcher
    matcher = Matcher(config)
    results = matcher.process(args.input, args.start_date, args.end_date)

    # Save results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    matcher.print_summary(results)

    print(f"\n✅ Results saved to: {args.output}")


if __name__ == "__main__":
    main()
