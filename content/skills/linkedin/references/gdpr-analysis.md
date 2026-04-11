# LinkedIn GDPR Data Export Analysis

Detailed reference for analyzing LinkedIn GDPR data exports.

## How to Request Your Data

1. Go to LinkedIn Settings > Data Privacy > Get a copy of your data
2. Select the data categories you want (or "All")
3. LinkedIn prepares the export (can take up to 24 hours)
4. Download the ZIP file when ready

**Direct URL:** `https://www.linkedin.com/mypreferences/d/download-my-data`

## What's Included

The export contains CSV files with your LinkedIn data:

| File | Contents |
|------|----------|
| `Connections.csv` | All connections with name, company, position, connected date, email |
| `Messages.csv` | Full message history with timestamps and conversation IDs |
| `Invitations.csv` | Sent and received invitation history |
| `Endorsement_Received_Info.csv` | Skill endorsements from connections |
| `Positions.csv` | Your work experience entries |
| `Education.csv` | Your education entries |
| `Skills.csv` | Your listed skills |
| `Profile.csv` | Your profile information |
| `Registration.csv` | Account registration details |
| `Company_Follows.csv` | Companies you follow |
| `Reactions.csv` | Your likes and reactions |
| `Comments.csv` | Your comments on posts |
| `Shares.csv` | Your shared posts |

## Analysis Tools

Python analysis tools are available in the `gdpr/` subdirectory:

```bash
# Full analysis of a GDPR export
uv run python gdpr/gdpr_analyzer.py /path/to/linkedin-export/

# Analyze connections specifically
uv run python gdpr/gdpr_analyzer.py /path/to/export/ --section connections

# Export analysis results to JSON
uv run python gdpr/gdpr_analyzer.py /path/to/export/ --format json --output analysis.json
```

The analyzer provides:
- **Connection analytics:** Growth over time, company distribution, role/industry clusters
- **Message analytics:** Most active conversations, response patterns, messaging timeline
- **Network insights:** Connection degree distribution, mutual connection patterns
- **Activity timeline:** Engagement trends (reactions, comments, shares over time)

## GDPR Export Gotchas

### Export is asynchronous

The GDPR data export is **not** an instant download. The workflow is:
1. Request export at `linkedin.com/mypreferences/d/download-my-data`
2. LinkedIn prepares the archive (minutes to hours)
3. Email notification when ready with download link
4. Download the ZIP, extract, then run analysis tools

### Two-part delivery

LinkedIn splits the archive into two parts. Part 1 ("Fast") arrives quickly but contains reduced data (e.g. Connections without company/position/date). Part 2 arrives within 24 hours with the full dataset. Both must be combined for complete analysis.
WHY: Starting analysis on Part 1 alone produces incomplete results and misleading statistics.

### Data storage paths

- GDPR exports: `~/code/second-brain/data/linkedin/exports/`
- Analysis results: `~/code/second-brain/data/linkedin/analysis/`

### Downloading archives with playwright-cli

**Known limitation:** playwright-cli has no dedicated `download` command, and headless click discards downloads. Use `--headed` mode for GDPR archive downloads.
WHY: Headless Chromium discards downloads triggered by click events.

```bash
# Correct: use headed mode so the browser saves the file to disk
playwright-cli -s=linkedin open --headed --profile=~/.local/share/playwright-cli/profiles/linkedin "https://www.linkedin.com/mypreferences/d/download-my-data"
sleep 3
playwright-cli -s=linkedin click e15  # e15 = "Download archive" button ref
# File downloads to the browser's default download directory

# Wrong: headless click triggers download but file never reaches disk
playwright-cli -s=linkedin click e15  # file lost in headless mode
```

**Rate limiting:** The download API (`settingsApiArchivedMemberDataDownload`) rate-limits aggressively. Do not retry via curl/fetch after a failed attempt -- wait and retry with headed mode.
