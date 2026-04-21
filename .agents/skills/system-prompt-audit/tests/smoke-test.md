# Smoke Test: system-prompt-audit

## Purpose

Defines expected behavior for manual verification of the skill.
Run through each scenario and check the output matches expectations.

## Scenario A: Up to Date (baseline == latest)

**Setup**: Baseline file version matches the API latest version.

**Trigger**: "run system prompt audit" or "/system-prompt-audit"

**Expected output** (contains all sections):
```
## System Prompt Audit — v2.1.92 → v2.1.92
Run: <timestamp>

### Version Status
- Baseline: v2.1.92 (captured: <date>)
- Latest: v2.1.92
- Status: UP TO DATE

### Changes Since Baseline
No changes — baseline is current.

### Custom Prompt Review
| File | Status | Notes |
|------|--------|-------|
| golden.md | ✅ Compatible | ... |
| agents/_core.md | ✅ Compatible | ... |
| ... (all files discovered from registry.yml) | ... | ... |

### Recommendations
(none or minor notes)

### Next Steps
Baseline is current. No update needed.
```

**Invariants**:
- Version Status section always present
- Custom Prompt Review table always present (even when up-to-date)
- No prompt download prompt to user when status is current

---

## Scenario B: New Version Available (baseline < latest)

**Setup**: API returns a version newer than the baseline file.

**Expected output**:
```
## System Prompt Audit — v2.1.92 → v2.1.93
Run: <timestamp>

### Version Status
- Baseline: v2.1.92
- Latest: v2.1.93
- Status: UPDATE AVAILABLE

### Changes Since Baseline
#### Behavioral Changes (🔴 High Impact)
- [Doing tasks]: "..." → "..."
  Impact: affects how Claude handles tool execution

#### Structural Changes (🟡 Low Impact)
- Added tool definition for X

### Custom Prompt Review
| File | Status | Notes |
|------|--------|-------|
| golden.md | ⚠️ Review needed | Overrides X which changed |
| agents/session-close.md | ✅ Compatible | No overlap with changes |

### Recommendations
1. Adopt: [specific behavior from Anthropic]
2. Remove: [deprecated instruction in golden.md]
3. Adapt: [update agents/session-close.md for Y]

### Next Steps
Run: `bd update baseline` to update baseline to v2.1.93
(or: "update the baseline" to confirm)
```

**Invariants**:
- Diff section always present when versions differ
- Behavioral changes marked separately from structural
- Skill ASKS before updating baseline (never auto-updates)
- After user confirms, baseline file is replaced with new content
  and renamed to `anthropic-v{latest}.md`

---

## Scenario C: API Unreachable

**Expected**: `fetch-latest.sh` exits with code 1 and prints an error to stderr. The skill outputs an error message and aborts — no diff, no custom prompt review.

---

## Behavioral vs Structural Classification Rules

| Behavioral (🔴) | Structural (🟡) |
|-----------------|-----------------|
| Changes in "# Doing tasks" | New tool definitions |
| Changes in "# Executing actions with care" | Formatting adjustments |
| Security policy changes | Version header updates |
| Tool usage constraints | Added examples or clarifications |
| Response style directives | Whitespace/ordering changes |
