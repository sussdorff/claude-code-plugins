# Activity Pattern Examples

This document contains common patterns extracted from training data (`~/Downloads/apps with matches.json`). Use these patterns as reference when configuring the matcher or understanding matching behavior.

## Project-Specific Patterns

### Entwicklung charly-server

**Ticket patterns:**
- `CH2-\d+` - Charly server tickets (high confidence)
- `CHAR-\d+` - Alternative ticket prefix
- `CH2-12889`, `CH2-12894`, `CH2-13130` - Example ticket numbers

**Activity examples:**
```
- "CH2-13130"
- "CH2-12889"
- "Abstimmung wg. charly testing/vorabversion"
- "Teams-Telefonat: Fuchsbau (Belebtes Büro) | solutio GmbH & Co. KG | malte.sussdorff@solutio.de"
```

**Common applications:**
- VS Code / Cursor (code editors)
- Terminal / iTerm2
- Chrome / Safari (testing)
- GitHub Desktop

### Fallklärung

**Ticket patterns:**
- `FALL-\d+` - Case clarification tickets (high confidence)
- `CH2-\d+` - Some CH2 tickets also map here
- `FALL-1510`, `CH2-13157`, `CH2-13159` - Example tickets

**Activity examples:**
```
- "FALL-1510"
- "CH2-13157"
- "CH2-13159"
- "Chat | https://solutio.atlassian.net/browse/FALL-1510 Datensicherung Px. wurde Informiert | solutio GmbH & Co. KG | malte.sussdorff@solutio.de | Microsoft Teams"
```

**Common applications:**
- Microsoft Teams
- JIRA / Atlassian
- Outlook / Mail

### Füchse Allgemein

**Activity patterns:**
- `Daily Fuchs` - Daily standup meetings (high confidence)
- `Chat \| Fuchsbau` - Team chat activities (medium confidence)
- `Fuchsbau \(Belebtes Büro\)` - Office space chat

**Activity examples:**
```
- "Daily Fuchs"
- "Chat | Fuchsbau (Belebtes Büro) | solutio GmbH & Co. KG | malte.sussdorff@solutio.de | Microsoft Teams"
- "Chat | https://solutio.atlassian.net/browse/FALL-1510 Datensicherung Px. wurde Informiert | solutio GmbH & Co. KG | malte.sussdorff@solutio.de | Microsoft Teams"
```

**Common applications:**
- Microsoft Teams
- Slack
- Zoom

### Container Support

**Activity patterns:**
- `Container.*Update` - Infrastructure updates (medium confidence)
- `Konnektor` - Connector discussions

**Activity examples:**
```
- "Teams und Kanäle | Container Update | solutio GmbH & Co. KG | malte.sussdorff@solutio.de | Microsoft Teams"
- "Diskussion mit Krisztina über Backup möglichkeiten."
- "Konnektor mit Tatjana"
```

**Common applications:**
- Microsoft Teams
- Terminal (for infrastructure work)
- Docker Desktop

### Spaß Haben (Fun / Personal)

**Activity patterns:**
- `elysium` - Gaming activities (high confidence)

**Activity examples:**
```
- "elysium"
```

**Common applications:**
- Steam
- Gaming applications
- YouTube

### cognovis Verwaltung

**Activity patterns:**
- `Aktivitäten` - Administrative activities

**Activity examples:**
```
- "Aktivitäten"
```

**Common applications:**
- Calendar apps
- Email clients
- Administrative tools

## Ignore Patterns

Activities that should NOT be matched (noise/system activities):

### System Applications

```
- "Systemeinstellungen" - System Preferences
- "Bluetooth" - Bluetooth pairing dialogs
- "Finder" - File browser
- "Spotlight" - Search
```

### Numeric IDs

```
- "1 203 096 259" - Pure numbers (Teams meeting IDs)
- "552 678 412"
- "^\\d+$" - Regex: any string of only digits
```

### Short Activities

```
- Duration < 30 seconds - Window switches, brief interactions
- Duration < 2 seconds - System events, accidental focus changes
```

### Generic Terms

```
- "Aktivitäten" (without context)
- Single words that could mean anything
- Empty activityTitle (null)
```

## Multi-Application Patterns

Some activities span multiple applications within a short time. These should be aggregated:

### Development Session

```
08:00-08:15  Code (VS Code) - CH2-13130
08:15-08:20  Terminal - git commands
08:20-08:25  Chrome - Testing feature
08:25-08:30  Code (VS Code) - CH2-13130

→ Aggregate to: 08:00-08:30 "CH2-13130: Feature development"
  Notes: "Applications: VS Code, Terminal, Chrome
          Commits: abc123, def456"
```

### Meeting Pattern

```
10:00-11:00  Teams - "Daily Fuchs"
11:00-11:05  Notes app - Meeting notes
11:05-11:10  JIRA - Update tickets

→ Aggregate to: 10:00-11:10 "Daily Fuchs standup"
  Notes: "Applications: Teams, Notes, JIRA"
```

## Confidence Scoring Examples

### High Confidence (0.85-1.0)

**Exact ticket match:**
```json
{
  "activityTitle": "CH2-13130",
  "application": "Code",
  "duration": "2:15:00",
  "confidence": 0.95,
  "reason": "Exact ticket match with substantial duration"
}
```

**Known pattern with long duration:**
```json
{
  "activityTitle": "Daily Fuchs",
  "application": "Teams",
  "duration": "0:45:00",
  "confidence": 0.90,
  "reason": "Exact pattern match with expected duration"
}
```

### Medium Confidence (0.6-0.84)

**Partial pattern match:**
```json
{
  "activityTitle": "Chat | Fuchsbau (Belebtes Büro)",
  "application": "Teams",
  "duration": "0:15:00",
  "confidence": 0.75,
  "reason": "Pattern match with reasonable duration"
}
```

**Activity with commit correlation:**
```json
{
  "activityTitle": "charly-server - Code",
  "application": "Code",
  "duration": "1:30:00",
  "confidence": 0.70,
  "reason": "Git commits found within time window",
  "commits": ["abc123"]
}
```

### Low Confidence (0.3-0.59)

**Weak pattern, short duration:**
```json
{
  "activityTitle": "Testing",
  "application": "Chrome",
  "duration": "0:05:00",
  "confidence": 0.45,
  "reason": "Generic activity title, short duration"
}
```

**Application match only:**
```json
{
  "activityTitle": null,
  "application": "Code",
  "path": "/Users/malte/code/solutio/charly-server/README.md",
  "duration": "0:10:00",
  "confidence": 0.50,
  "reason": "Path suggests project but no explicit activity"
}
```

### No Match (0.0-0.29)

**System activity:**
```json
{
  "activityTitle": "Bluetooth",
  "application": "Systemeinstellungen",
  "duration": "0:00:02",
  "confidence": 0.0,
  "reason": "Ignored pattern"
}
```

**Unknown pattern:**
```json
{
  "activityTitle": "552 678 412",
  "application": "Teams",
  "duration": "0:00:15",
  "confidence": 0.15,
  "reason": "No matching pattern, very short"
}
```

## Regex Pattern Library

Common regex patterns for matching:

### Ticket Numbers

```regex
# Jira-style tickets
(CH2-\d+)
(FALL-\d+)
(CHAR-\d+)

# Generic ticket patterns
([A-Z]{2,5}-\d{3,6})

# Extract from URLs
https://[^/]+/browse/([A-Z]+-\d+)
```

### Teams Activities

```regex
# Team chat
Chat \| Fuchsbau.*Teams

# Meetings
Teams-Telefonat:.*\|

# Channels
Teams und Kanäle \| (.*?) \|
```

### Application Paths

```regex
# Repository detection
/code/([^/]+)/

# Project name from path
/code/solutio/([^/]+)

# File type focus
\.(py|js|ts|java|go)$
```

### Duration Patterns

```regex
# Long focus sessions (2+ hours)
duration >= 7200

# Meeting length (30-90 min)
duration >= 1800 && duration <= 5400

# Quick switches (< 1 min)
duration < 60
```

## Pattern Discovery Workflow

When analyzing unmatched activities to create new patterns:

1. **Group by frequency:**
   ```bash
   jq '.unmatchedSummary | sort_by(.count) | reverse | .[:20]' matches.json
   ```

2. **Identify commonalities:**
   - Look for repeated words/phrases
   - Check if activities cluster by application
   - Notice time-of-day patterns

3. **Create pattern:**
   - Start literal, make regex if needed
   - Test on sample data
   - Adjust confidence threshold

4. **Validate:**
   - Reprocess with new pattern
   - Check false positive rate
   - Review proposed entries

## Real-World Pattern Examples

Based on actual training data analysis:

| Pattern | Project | Confidence | Frequency | Notes |
|---------|---------|------------|-----------|-------|
| `CH2-\d+` | Entwicklung charly-server | High | 13 | Primary ticket pattern |
| `FALL-\d+` | Fallklärung | High | 11 | Case management |
| `Daily Fuchs` | Füchse Allgemein | High | 50+ | Daily standup |
| `Chat \| Fuchsbau` | Füchse Allgemein | Medium | 50+ | Team communications |
| `elysium` | Spaß Haben | High | 6 | Gaming/personal |
| `Container.*Update` | Container Support | Medium | 5 | Infrastructure |
| `Aktivitäten` | cognovis Verwaltung | Medium | 14 | Admin tasks |
| `^\d+$` | (ignored) | N/A | 192+ | Meeting IDs |
| `Systemeinstellungen` | (ignored) | N/A | High | System activities |

## Tips for Pattern Creation

1. **Start specific, broaden if needed:**
   - "Daily Fuchs Meeting" → "Daily Fuchs" → "Daily.*Fuchs"

2. **Use word boundaries for short patterns:**
   - `\belysium\b` instead of `elysium` (avoids "elysium-test")

3. **Case-insensitive by default:**
   - Matcher converts to lowercase before comparing

4. **Test patterns in isolation:**
   - Use jq to test regex before adding to config
   - `echo "Daily Fuchs" | grep -iE "daily.*fuchs"`

5. **Consider context:**
   - "Meeting" in Teams → probably work
   - "Meeting" in Safari → might be personal

6. **Monitor false positives:**
   - Review low-confidence matches after each run
   - Adjust or remove patterns that match incorrectly
