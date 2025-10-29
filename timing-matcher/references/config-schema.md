# Matcher Configuration Schema

This document describes the structure of `matcher-config.json`, which controls how the timing-matcher skill processes and matches activities.

## Complete Schema

```json
{
  "projectMappings": {
    "ticketPrefixes": {
      "CH2-": {
        "projectName": "Entwicklung charly-server",
        "projectId": "timing-project-id-here",
        "description": "Charly server development tickets"
      },
      "FALL-": {
        "projectName": "Fallklärung",
        "projectId": "timing-project-id-here",
        "description": "Case clarification tasks"
      }
    },
    "activityPatterns": [
      {
        "pattern": "Daily Fuchs",
        "regex": false,
        "projectName": "Füchse Allgemein",
        "projectId": "timing-project-id-here",
        "description": "Daily team standup"
      },
      {
        "pattern": "Container.*Update",
        "regex": true,
        "projectName": "Container Support",
        "projectId": "timing-project-id-here",
        "description": "Container infrastructure updates"
      },
      {
        "pattern": "elysium",
        "regex": false,
        "projectName": "Spaß Haben",
        "projectId": "timing-project-id-here",
        "description": "Gaming and fun activities"
      }
    ],
    "ignorePatterns": [
      "Systemeinstellungen",
      "Bluetooth",
      "Finder",
      "^\\d+$"
    ]
  },
  "matching": {
    "minDurationSeconds": 30,
    "maxGapMinutes": 15,
    "commitTimeWindowMinutes": 15,
    "confidenceThresholds": {
      "high": 0.85,
      "medium": 0.6,
      "low": 0.3
    }
  },
  "gitRepos": [
    {
      "path": "~/code/solutio/charly-server",
      "ticketPrefixes": ["CH2-", "CHAR-"],
      "description": "Main charly server repository"
    }
  ],
  "output": {
    "includeSourceActivities": true,
    "includeCommitShas": true,
    "groupByProject": true
  }
}
```

## Section Details

### projectMappings

Defines how activities are matched to Timing projects.

#### ticketPrefixes

Maps ticket number prefixes to projects.

**Fields:**
- `key` (string): The ticket prefix (e.g., "CH2-", "FALL-")
- `projectName` (string): Human-readable project name
- `projectId` (string): Timing project UUID (get from Timing MCP)
- `description` (string, optional): Notes about this mapping

**Matching logic:**
- Extracts ticket numbers from `activityTitle` using regex: `(PREFIX-\\d+)`
- High confidence match (0.9+)
- Takes precedence over activity patterns

**Example:**
```json
"CH2-": {
  "projectName": "Entwicklung charly-server",
  "projectId": "abc-123-def-456",
  "description": "Charly server development"
}
```

This matches activities like:
- "CH2-13130"
- "CH2-12889 bug fix"
- "Working on CH2-13157 feature"

#### activityPatterns

Maps activity title/application patterns to projects when no ticket is found.

**Fields:**
- `pattern` (string): Text or regex pattern to match
- `regex` (boolean): Whether pattern is regex (default: false)
- `projectName` (string): Human-readable project name
- `projectId` (string): Timing project UUID
- `description` (string, optional): Notes about this pattern

**Matching logic:**
- Searches in `activityTitle` and `application` fields
- Case-insensitive matching
- Medium confidence match (0.6-0.8) unless very specific
- Processes in order (first match wins)

**Example - Literal matching:**
```json
{
  "pattern": "Daily Fuchs",
  "regex": false,
  "projectName": "Füchse Allgemein",
  "projectId": "xyz-789"
}
```

Matches:
- "Daily Fuchs"
- "Meeting: Daily Fuchs standup"
- "daily fuchs" (case-insensitive)

**Example - Regex matching:**
```json
{
  "pattern": "Chat \\| Fuchsbau.*Teams",
  "regex": true,
  "projectName": "Füchse Allgemein",
  "projectId": "xyz-789"
}
```

Matches:
- "Chat | Fuchsbau (Belebtes Büro) | solutio GmbH & Co. KG | malte.sussdorff@solutio.de | Microsoft Teams"

#### ignorePatterns

List of patterns to exclude from processing.

**Fields:**
- Array of strings (literal or regex patterns)
- Checked against both `activityTitle` and `application`
- Case-insensitive matching
- Activities matching these patterns are logged to `unmatchedSummary` but not proposed

**Common patterns:**
```json
"ignorePatterns": [
  "Systemeinstellungen",     // System preferences
  "Bluetooth",                // Bluetooth pairing
  "Finder",                   // Finder window
  "^\\d+$",                   // Pure numbers (often Teams meeting IDs)
  "^[a-f0-9]{8,}$"           // Long hex strings
]
```

### matching

Controls the aggregation and confidence scoring behavior.

#### minDurationSeconds

Minimum activity duration to consider (in seconds).

**Default:** 30

Activities shorter than this are ignored as noise (e.g., brief window switches).

#### maxGapMinutes

Maximum time gap between activities for merging (in minutes).

**Default:** 15

**Merging rules:**
- Gap < 5 min: Always merge if same context
- Gap 5-15 min: Merge if same ticket/app
- Gap > maxGapMinutes: Never merge

**Example:**
```
08:00-08:30  Code (CH2-123)    ─┐
08:30-08:33  Slack              │ 3min gap → merge
08:33-09:00  Code (CH2-123)    ─┘
→ Creates single entry: 08:00-09:00 (CH2-123)

09:00-09:30  Code (CH2-123)    ─┐
09:30-09:50  Lunch break        │ 20min gap → don't merge
09:50-10:30  Code (CH2-123)    ─┘
→ Creates two entries
```

#### commitTimeWindowMinutes

Window for matching activities to git commits (±minutes).

**Default:** 15

**Matching logic:**
- Find commits within ±window of activity timestamp
- Prefer commits with same ticket number
- Add commit SHAs to time entry notes

**Example:**
```
Activity: 08:00-08:30 (CH2-123)
Commits:
  07:58  CH2-123 "Fix bug"     → Matched (within window + same ticket)
  08:15  CH2-123 "Add tests"   → Matched
  08:45  CH2-999 "Other task"  → Not matched (outside window)
```

#### confidenceThresholds

Defines score ranges for confidence levels.

**Defaults:**
```json
{
  "high": 0.85,    // ≥0.85: High confidence
  "medium": 0.6,   // 0.6-0.84: Medium confidence
  "low": 0.3       // 0.3-0.59: Low confidence
}
```

**Scoring factors:**
- **Exact ticket match:** 0.9-1.0
- **Pattern match + reasonable duration:** 0.6-0.85
- **Weak pattern or very short duration:** 0.3-0.6
- **No match:** 0.0-0.3

### gitRepos

List of git repositories to scan for commit correlation.

**Fields:**
- `path` (string): Repository path (supports ~ expansion)
- `ticketPrefixes` (array): Ticket prefixes to extract from commits
- `description` (string, optional): Notes about this repo

**Example:**
```json
{
  "path": "~/code/solutio/charly-server",
  "ticketPrefixes": ["CH2-", "CHAR-"],
  "description": "Main application repository"
}
```

**Processing:**
- Runs `git log --since=START --until=END --format="%H|%ai|%s|%an" --all`
- Extracts ticket numbers from commit messages
- Indexes by date and ticket number
- Correlates with activities based on time and ticket

### output

Controls the format of generated `matches.json`.

**Fields:**
- `includeSourceActivities` (boolean): Include full source activity details in proposals
- `includeCommitShas` (boolean): Add commit SHAs to time entry notes
- `groupByProject` (boolean): Group summary statistics by project

**Default:** All true

## Configuration Generation

### From Training Data

The matcher can automatically generate a configuration from the "apps with matches" training file:

```bash
python scripts/matcher.py --generate-config \
  --training ~/Downloads/"apps with matches.json" \
  --output matcher-config.json
```

**Process:**
1. Analyzes all matched activities
2. Extracts ticket prefixes (patterns like `CH2-\d+`)
3. Identifies common activity title patterns
4. Detects system apps to ignore
5. Prompts for Timing project IDs
6. Writes complete config

### Manual Creation

Copy `assets/matcher-config-template.json` and customize:

1. **Add your projects:**
   - Get project IDs from Timing MCP: `list_projects` tool
   - Map ticket prefixes to projects
   - Add activity patterns you recognize

2. **Configure thresholds:**
   - Adjust confidence thresholds based on your needs
   - Set appropriate gap handling for your workflow
   - Configure git repo paths

3. **Test incrementally:**
   - Start with a small date range
   - Review matches and adjust patterns
   - Iterate until >80% match rate achieved

## Validation

The matcher validates configuration on load:

**Checks:**
- Required fields present
- Project IDs are valid UUIDs (if specified)
- Regex patterns compile successfully
- File paths exist (for git repos)
- Threshold values are in valid ranges (0.0-1.0)

**Error handling:**
- Invalid config: Exits with detailed error message
- Missing optional fields: Uses defaults
- Invalid regex: Skips pattern, logs warning
- Missing git repo: Continues without commit correlation

## Tips

### Iterative Improvement

1. **Start simple:**
   - Begin with only ticket prefixes
   - Run on sample data
   - Review matches

2. **Add patterns gradually:**
   - Analyze unmatched summary
   - Add patterns for common unmatched activities
   - Test each addition

3. **Tune thresholds:**
   - Review low-confidence matches
   - Adjust thresholds if too many false positives/negatives
   - Consider different thresholds for different pattern types

### Common Pitfalls

- **Overlapping patterns:** First match wins, so order matters
- **Too generic patterns:** "meeting" might match everything
- **Missing ticket prefix in git config:** Commits won't correlate
- **Overly strict confidence thresholds:** Many valid matches rejected

### Performance Optimization

- **Regex patterns:** More CPU intensive, use sparingly
- **Ignore patterns:** Reduces processing time significantly
- **Date range limiting:** Process incrementally for large datasets
- **Git repo count:** Each repo adds ~1-2s to processing time
