#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "python-dateutil>=2.8.2"
# ]
# ///
"""
Activity Aggregator for timing-matcher

Groups consecutive activities into coherent time entries.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dateutil import parser as date_parser


@dataclass
class Activity:
    """Represents a single activity from Timing export."""
    activity_title: Optional[str]
    application: str
    duration_str: str
    start_date: datetime
    end_date: datetime
    path: Optional[str] = None

    # Matching metadata
    ticket: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    confidence: float = 0.0
    match_reason: str = ""

    @property
    def duration_seconds(self) -> int:
        """Calculate duration in seconds."""
        return int((self.end_date - self.start_date).total_seconds())


@dataclass
class TimeEntry:
    """Represents an aggregated time entry proposal."""
    start_date: datetime
    end_date: datetime
    project_id: str
    project_name: str
    title: str
    notes: str
    confidence: str  # "high", "medium", "low"
    source_activities: List[Activity] = field(default_factory=list)
    commit_shas: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        """Calculate total duration in seconds."""
        return int((self.end_date - self.start_date).total_seconds())

    @property
    def duration_iso(self) -> str:
        """Format duration as ISO 8601 duration (PT2H30M)."""
        seconds = self.duration_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"PT{hours}H{minutes}M"


class Aggregator:
    """Aggregates activities into time entry proposals."""

    def __init__(
        self,
        min_duration_seconds: int = 30,
        max_gap_minutes: int = 15
    ):
        """
        Initialize aggregator.

        Args:
            min_duration_seconds: Minimum activity duration to consider
            max_gap_minutes: Maximum gap between activities for merging
        """
        self.min_duration_seconds = min_duration_seconds
        self.max_gap_minutes = max_gap_minutes

    def aggregate(self, activities: List[Activity]) -> List[TimeEntry]:
        """
        Aggregate activities into time entry proposals.

        Args:
            activities: List of matched activities

        Returns:
            List of time entry proposals
        """
        # Filter by minimum duration
        activities = [
            a for a in activities
            if a.duration_seconds >= self.min_duration_seconds
        ]

        # Sort by start time
        activities.sort(key=lambda a: a.start_date)

        # Group by project and consecutive time
        entries: List[TimeEntry] = []
        current_group: List[Activity] = []

        for activity in activities:
            if not current_group:
                # Start new group
                current_group = [activity]
            else:
                # Check if should merge with current group
                last_activity = current_group[-1]

                if self._should_merge(last_activity, activity):
                    current_group.append(activity)
                else:
                    # Finish current group and start new one
                    if current_group:
                        entry = self._create_entry(current_group)
                        if entry:
                            entries.append(entry)
                    current_group = [activity]

        # Finish last group
        if current_group:
            entry = self._create_entry(current_group)
            if entry:
                entries.append(entry)

        return entries

    def _should_merge(self, last: Activity, current: Activity) -> bool:
        """
        Determine if current activity should merge with last.

        Args:
            last: Last activity in current group
            current: Current activity to consider

        Returns:
            True if should merge
        """
        # Check time gap
        gap_minutes = (current.start_date - last.end_date).total_seconds() / 60

        # Must be same project
        if last.project_id != current.project_id:
            return False

        # Small gap: merge if same project
        if gap_minutes < 5:
            return True

        # Medium gap: merge if same ticket or application
        if gap_minutes < self.max_gap_minutes:
            if last.ticket and current.ticket and last.ticket == current.ticket:
                return True
            if last.application == current.application:
                return True

        # Large gap: don't merge
        return False

    def _create_entry(self, activities: List[Activity]) -> Optional[TimeEntry]:
        """
        Create a time entry from a group of activities.

        Args:
            activities: List of activities in the group

        Returns:
            TimeEntry or None if group is invalid
        """
        if not activities:
            return None

        # Use first activity for project info
        first = activities[0]

        # Determine overall confidence
        avg_confidence = sum(a.confidence for a in activities) / len(activities)
        if avg_confidence >= 0.85:
            confidence_level = "high"
        elif avg_confidence >= 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Create title
        title = self._create_title(activities)

        # Create notes
        notes = self._create_notes(activities)

        return TimeEntry(
            start_date=activities[0].start_date,
            end_date=activities[-1].end_date,
            project_id=first.project_id,
            project_name=first.project_name,
            title=title,
            notes=notes,
            confidence=confidence_level,
            source_activities=activities
        )

    def _create_title(self, activities: List[Activity]) -> str:
        """
        Create a descriptive title for the time entry.

        Args:
            activities: List of activities

        Returns:
            Title string
        """
        # If there's a ticket, use it
        tickets = {a.ticket for a in activities if a.ticket}
        if tickets:
            ticket = sorted(tickets)[0]  # Use first ticket alphabetically

            # Find most descriptive activity title
            titles = [
                a.activity_title for a in activities
                if a.activity_title and a.activity_title != ticket
            ]

            if titles:
                # Use first non-ticket title
                return f"{ticket}: {titles[0]}"
            else:
                return ticket

        # No ticket: use most common activity title
        titles = [a.activity_title for a in activities if a.activity_title]
        if titles:
            # Count occurrences and use most common
            from collections import Counter
            most_common = Counter(titles).most_common(1)[0][0]
            return most_common

        # Fallback: use application name
        apps = {a.application for a in activities}
        return f"Work in {', '.join(sorted(apps))}"

    def _create_notes(self, activities: List[Activity]) -> str:
        """
        Create notes for the time entry.

        Args:
            activities: List of activities

        Returns:
            Notes string
        """
        notes_parts = []

        # List applications used
        apps = sorted({a.application for a in activities})
        if len(apps) > 1:
            notes_parts.append(f"Applications: {', '.join(apps)}")

        # Add match reasons if interesting
        reasons = {a.match_reason for a in activities if a.match_reason}
        if reasons and len(reasons) == 1:
            notes_parts.append(f"Match: {list(reasons)[0]}")

        return "\n".join(notes_parts)

    def get_confidence_distribution(
        self,
        entries: List[TimeEntry]
    ) -> Dict[str, int]:
        """
        Calculate confidence distribution across entries.

        Args:
            entries: List of time entries

        Returns:
            Dictionary with counts for each confidence level
        """
        from collections import Counter
        return dict(Counter(e.confidence for e in entries))


if __name__ == "__main__":
    import json

    # Example usage
    activities = [
        Activity(
            activity_title="CH2-13130",
            application="Code",
            duration_str="2:15:00",
            start_date=datetime(2025, 8, 17, 8, 0),
            end_date=datetime(2025, 8, 17, 10, 15),
            ticket="CH2-13130",
            project_id="proj-123",
            project_name="Entwicklung charly-server",
            confidence=0.95,
            match_reason="Exact ticket match"
        ),
        Activity(
            activity_title="Terminal",
            application="iTerm2",
            duration_str="0:10:00",
            start_date=datetime(2025, 8, 17, 10, 15),
            end_date=datetime(2025, 8, 17, 10, 25),
            ticket="CH2-13130",
            project_id="proj-123",
            project_name="Entwicklung charly-server",
            confidence=0.90,
            match_reason="Same ticket"
        )
    ]

    aggregator = Aggregator()
    entries = aggregator.aggregate(activities)

    print(json.dumps([
        {
            "start": e.start_date.isoformat(),
            "end": e.end_date.isoformat(),
            "project": e.project_name,
            "title": e.title,
            "duration": e.duration_iso,
            "confidence": e.confidence
        }
        for e in entries
    ], indent=2))
