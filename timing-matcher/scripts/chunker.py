#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "python-dateutil>=2.8.2"
# ]
# ///
"""
JSON Chunker for large Timing exports

Splits large JSON files into manageable chunks using jq subprocess.
Never loads the full file into memory.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, List, Dict, Any

from dateutil import parser as date_parser


def chunk_by_date_range(
    json_file: Path,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Extract activities within a specific date range using jq.

    Args:
        json_file: Path to JSON file
        start_date: ISO date string (e.g., "2025-08-01")
        end_date: ISO date string (e.g., "2025-08-08")

    Returns:
        List of activity dictionaries
    """
    jq_filter = (
        f'[.[] | select(.startDate >= "{start_date}" and .startDate < "{end_date}")]'
    )

    try:
        result = subprocess.run(
            ["jq", jq_filter, str(json_file)],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running jq: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing jq output: {e}", file=sys.stderr)
        return []


def chunk_by_week(
    json_file: Path,
    start_date: str,
    end_date: str
) -> Iterator[tuple[str, str, List[Dict[str, Any]]]]:
    """
    Yield weekly chunks of activities.

    Args:
        json_file: Path to JSON file
        start_date: ISO date string for range start
        end_date: ISO date string for range end

    Yields:
        Tuples of (week_start, week_end, activities)
    """
    current = date_parser.parse(start_date).date()
    end = date_parser.parse(end_date).date()

    while current < end:
        week_end = min(current + timedelta(days=7), end)

        activities = chunk_by_date_range(
            json_file,
            current.isoformat(),
            week_end.isoformat()
        )

        if activities:
            yield (current.isoformat(), week_end.isoformat(), activities)

        current = week_end


def chunk_by_day(
    json_file: Path,
    start_date: str,
    end_date: str
) -> Iterator[tuple[str, List[Dict[str, Any]]]]:
    """
    Yield daily chunks of activities.

    Args:
        json_file: Path to JSON file
        start_date: ISO date string for range start
        end_date: ISO date string for range end

    Yields:
        Tuples of (date, activities)
    """
    current = date_parser.parse(start_date).date()
    end = date_parser.parse(end_date).date()

    while current < end:
        day_end = current + timedelta(days=1)

        activities = chunk_by_date_range(
            json_file,
            current.isoformat(),
            day_end.isoformat()
        )

        if activities:
            yield (current.isoformat(), activities)

        current = day_end


def get_date_range(json_file: Path) -> tuple[str, str]:
    """
    Extract the min and max dates from the JSON file using jq.

    Args:
        json_file: Path to JSON file

    Returns:
        Tuple of (min_date, max_date) as ISO strings
    """
    jq_filter = '[.[] | .startDate] | sort | [first, last]'

    try:
        result = subprocess.run(
            ["jq", "-r", jq_filter, str(json_file)],
            capture_output=True,
            text=True,
            check=True
        )
        dates = json.loads(result.stdout)
        return dates[0][:10], dates[1][:10]  # Extract date part only
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError) as e:
        print(f"Error getting date range: {e}", file=sys.stderr)
        return "", ""


def count_entries(json_file: Path) -> int:
    """
    Count total entries in JSON file using jq.

    Args:
        json_file: Path to JSON file

    Returns:
        Number of entries
    """
    try:
        result = subprocess.run(
            ["jq", "length", str(json_file)],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error counting entries: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chunk large JSON files by date range")
    parser.add_argument("json_file", type=Path, help="Path to JSON file")
    parser.add_argument("--start-date", help="Start date (ISO format, e.g., 2025-08-01)")
    parser.add_argument("--end-date", help="End date (ISO format)")
    parser.add_argument("--mode", choices=["week", "day"], default="week",
                        help="Chunking mode (default: week)")
    parser.add_argument("--stats-only", action="store_true",
                        help="Only show statistics, don't process chunks")

    args = parser.parse_args()

    if not args.json_file.exists():
        print(f"Error: File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # Get date range if not specified
    if not args.start_date or not args.end_date:
        print("Determining date range from file...", file=sys.stderr)
        start, end = get_date_range(args.json_file)
        args.start_date = args.start_date or start
        args.end_date = args.end_date or end

    # Show statistics
    total = count_entries(args.json_file)
    print(f"Total entries: {total}", file=sys.stderr)
    print(f"Date range: {args.start_date} to {args.end_date}", file=sys.stderr)

    if args.stats_only:
        sys.exit(0)

    # Process chunks
    if args.mode == "week":
        for week_start, week_end, activities in chunk_by_week(
            args.json_file, args.start_date, args.end_date
        ):
            print(f"\nWeek {week_start} to {week_end}: {len(activities)} entries",
                  file=sys.stderr)
            print(json.dumps(activities, indent=2))
    else:
        for day, activities in chunk_by_day(
            args.json_file, args.start_date, args.end_date
        ):
            print(f"\nDay {day}: {len(activities)} entries", file=sys.stderr)
            print(json.dumps(activities, indent=2))
