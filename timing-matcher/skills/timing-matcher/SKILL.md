---
name: timing-matcher
description: Process large Timing app JSON exports to match unassigned activities to projects using pattern recognition, git commit correlation, and intelligent aggregation. Use when processing Timing exports, matching time entries to projects/tickets, or analyzing activity patterns to generate time entry proposals for bulk creation.
---

# Timing Matcher

## Overview

Process large Timing app JSON exports (tens of thousands of entries) and intelligently match them to projects using ticket patterns, git commit correlation, and learned activity patterns. Generate reviewable time entry proposals for bulk creation via the Timing MCP server.

This skill handles:
- Incremental processing of large JSON files (too big for LLM context)
- Pattern extraction from existing matched entries (training data)
- Git commit correlation for developer workflows
- Intelligent aggregation of activities into coherent time entries
- Confidence scoring and duplicate detection

## When to Use

Use this skill when:
- Processing Timing app exports with unassigned activities
- User asks to "match my time entries to projects"
- Analyzing activity patterns from training data
- Generating time entry proposals from raw activity data
- User mentions processing "apps with matches" or "unzugewiesen" (unassigned) JSON files

## Workflow

### Step 1: Understand the Input Data

Ask the user to identify their data sources:

1. **Unassigned activities export** - The main data to process
   - Typical location: `~/Downloads/unzugewiesen.json` or `~/Downloads/unzugewiesen-full.json`
   - Contains: `activityTitle`, `application`, `duration`, `startDate`, `endDate`
   - Volume: Typically 800+ entries/day

2. **Matched activities (training data)** - Examples of correct matches
   - Typical location: `~/Downloads/apps with matches.json`
   - Contains: `activityTitle`, `activityType`, `day`, `duration`, `project`
   - Purpose: Learn patterns for automatic matching

3. **Git repositories** (optional but recommended)
   - Typical location: `~/code/solutio/charly-server` or similar
   - Purpose: Correlate activities with commit history for better matching

### Step 2: Initialize or Load Configuration

Check if a configuration file exists:
- If `matcher-config.json` exists, load it
- If not, offer to generate one from training data or use the template

To generate configuration from training data:
1. Read `scripts/matcher.py --generate-config` section
2. Parse the matched activities JSON
3. Extract patterns:
   - Ticket prefixes (e.g., `CH2-`, `FALL-`, `CHAR-`)
   - Activity patterns (e.g., "Daily Fuchs", "Container.*Update")
   - Applications to ignore (e.g., "Systemeinstellungen", "Bluetooth")
4. Prompt user for Timing project IDs for each detected pattern
5. Write configuration to `matcher-config.json`

Configuration structure is documented in `references/config-schema.md`.

### Step 3: Process Unassigned Entries

Run the matcher in dry-run mode (default):

```bash
python scripts/matcher.py \
  --input ~/Downloads/unzugewiesen-full.json \
  --config matcher-config.json \
  --output matches.json
```

The processing flow:

1. **Chunk the data** (`scripts/chunker.py`)
   - Use `jq` to split large JSON into weekly/daily chunks
   - Process one chunk at a time to avoid memory issues
   - Example: Filter by date range for incremental processing

2. **Match patterns** (`scripts/matcher.py`)
   - Extract ticket numbers using regex from config
   - Match activity patterns from config
   - Score confidence (high: 0.85+, medium: 0.6-0.85, low: 0.3-0.6)
   - Ignore patterns from config

3. **Correlate git commits** (`scripts/git_analyzer.py`)
   - Build commit index from git log
   - Find commits within ±15 min of activities
   - Prefer commits with matching ticket numbers
   - Add commit SHAs to time entry notes

4. **Aggregate activities** (`scripts/aggregator.py`)
   - Group consecutive activities by:
     - Same ticket number
     - Same application (if no ticket)
     - Within same hour
   - Handle gaps:
     - < 5 min: merge into single entry
     - 5-15 min: separate if different context
     - > 15 min: always separate
   - Enforce minimum duration (30s)

5. **Generate output** - Creates `matches.json` with:
   - Metadata (statistics, confidence distribution)
   - Project mappings summary
   - Proposed time entries with confidence scores
   - Unmatched activity summary

### Step 4: Review Results

Present the summary statistics to the user:

```
Processing Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Statistics:
  Total entries: 72,000
  Date range: 2025-08-01 to 2025-10-31

Matching Results:
  ✓ High confidence: 30,000 entries (41.7%)
  ≈ Medium confidence: 12,000 entries (16.7%)
  ? Low confidence: 3,000 entries (4.2%)
  ✗ Unmatched: 27,000 entries (37.5%)

Proposed Time Entries: 3,200
  Entwicklung charly-server: 150 entries (120.5h)
  Fallklärung: 80 entries (65.2h)
  ...
```

Ask the user if they want to:
1. Review specific matches (filter by project/confidence)
2. Adjust configuration and reprocess
3. Proceed to execution

### Step 5: Execute (Optional)

Only after user approval, run the executor:

```bash
python scripts/matcher.py --execute matches.json
```

The executor will:
1. Check for duplicate time entries via Timing MCP
2. Respect Timing API rate limits (500 requests/hour)
3. Create time entries via Timing MCP server tools
4. Report progress and any failures
5. Log errors to `matcher-errors.log`

## Configuration

The skill uses a JSON configuration file (`matcher-config.json`) that defines:

- **Project mappings**: Ticket prefixes → Timing projects
- **Activity patterns**: Regex patterns → Timing projects
- **Ignore patterns**: Activities to skip
- **Matching thresholds**: Confidence scores, gap handling, duration limits
- **Git repositories**: Paths and ticket prefixes to scan

See `references/config-schema.md` for full documentation.

Template configuration available in `assets/matcher-config-template.json`.

## Advanced Features

### Confidence Filtering

Filter proposed entries by confidence level:

```bash
# Only review high-confidence matches
jq '.proposedEntries[] | select(.confidence == "high")' matches.json

# Review uncertain matches requiring manual decision
jq '.proposedEntries[] | select(.confidence == "low")' matches.json
```

### Incremental Processing

Process date ranges incrementally:

```bash
# Process August only
python scripts/matcher.py \
  --input ~/Downloads/unzugewiesen-full.json \
  --start-date 2025-08-01 \
  --end-date 2025-08-31 \
  --output matches-august.json
```

### Pattern Discovery

Analyze unmatched activities to discover new patterns:

```bash
# Show most common unmatched patterns
jq '.unmatchedSummary | sort_by(.count) | reverse | .[:10]' matches.json
```

## Resources

### scripts/

- `chunker.py` - Split large JSON files using jq subprocess
- `matcher.py` - Main orchestrator with pattern matching and execution
- `git_analyzer.py` - Parse git logs and correlate commits
- `aggregator.py` - Group activities into time entries

All scripts use PEP 723 inline dependencies with `uv` for self-contained execution.

### references/

- `config-schema.md` - Complete matcher-config.json documentation
- `pattern-examples.md` - Common patterns extracted from training data

### assets/

- `matcher-config-template.json` - Template configuration file for customization

## Error Handling

The skill handles common issues gracefully:

- **Large files**: Automatically chunks data, never loads full file into memory
- **Missing git repos**: Continues without commit correlation
- **Parsing errors**: Logs errors, continues with remaining chunks
- **Rate limits**: Automatic retry with exponential backoff
- **Duplicate detection**: Queries existing entries before creation

All errors logged to `matcher-errors.log` for troubleshooting.

## Performance

Expected performance:
- Process 72k entries in < 5 minutes
- Achieve >80% match rate (high + medium confidence)
- Parallel processing where possible (jq chunks)
- Git log cached per run

## Dependencies

Required tools (specify in script shebangs):
- Python 3.10+
- `jq` CLI tool (for JSON processing)
- Git CLI (for commit correlation)
- Timing MCP server (for execution mode)

Python libraries (PEP 723 inline dependencies):
- `pydantic` - Data validation
- `python-dateutil` - Date parsing
- `rich` - Pretty console output
