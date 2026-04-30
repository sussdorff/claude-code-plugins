---
name: system-prompt-audit
model: sonnet
description: >-
  Audit Anthropic system prompt changes against the local baseline and review
  custom prompts for compatibility. Use when checking for new Claude versions,
  "run system prompt audit", "audit system prompts", or "check for prompt updates".
requires_standards: [english-only]
---

# System Prompt Audit

Fetch the latest Anthropic system prompt from cchistory.mariozechner.at, diff it against the stored baseline, classify behavioral vs structural changes, and review all custom prompts for compatibility. Ask the user before updating the baseline.

## When to Use

- "run system prompt audit" / "audit system prompts"
- "check for prompt updates" / "did Anthropic change the system prompt?"
- "review golden.md against new Claude version"

## Workflow

### 1. Fetch and Compare Versions

Run the `fetch-latest.sh` script from this skill's `scripts/` directory.
See your harness adapter for the exact invocation path.

Parse output:
- `BASELINE_VERSION` — version currently in the baseline directory
- `LATEST_VERSION` — latest version from cchistory API
- `STATUS` — `current` or `outdated`
- `NEW_PROMPT_FILE` — path to downloaded prompt (only when `STATUS=outdated`)

Baseline file path: `{baseline-dir}/anthropic-v{BASELINE_VERSION}.md` (see harness adapter for baseline directory location).

### 2. Generate Diff (when outdated)

When `STATUS=outdated`:
1. Load the baseline file at the path output by the script
2. Load the new prompt at `$NEW_PROMPT_FILE`
3. Generate a unified diff (conceptual — summarize changes, do NOT run `diff` command and dump raw output)
4. Classify each changed section:

**Behavioral (🔴 High Impact)** — changes that alter how Claude acts:
- Sections: "# Doing tasks", "# Executing actions with care", "# Being a good person"
- Security policies, tool-use constraints, response style directives
- Any instruction that would change Claude's decisions or outputs

**Structural (🟡 Low Impact)** — changes that don't alter behavior:
- Tool definitions added/removed, formatting, examples, whitespace, ordering

When `STATUS=current`: skip diff, note "No changes — baseline is current."

### 3. Review Custom Prompts

Load the system prompts registry file to discover all custom prompt files. See your harness adapter for the registry path.

1. Extract all `entries[].file` values and the `default.file` value (if present)
2. Deduplicate the list
3. For each discovered file path, load that file and evaluate it against the diff (or against full baseline when current)

For each file classify:
- **✅ Compatible** — no conflict with changed sections; no action needed
- **⚠️ Review needed** — overlaps with a changed section; evaluate whether update is beneficial
- **❌ Conflicts** — directly overrides a behavioral change in a way that may cause problems

WHY: `golden.md` uses `mode: replace`, so it fully replaces Anthropic's prompt. Changes to Anthropic's defaults don't automatically apply — they must be deliberately adopted.

### 4. Output Report

```markdown
## System Prompt Audit — v{BASELINE_VERSION} → v{LATEST_VERSION}
Run: {timestamp}

### Version Status
- Baseline: v{BASELINE_VERSION}
- Latest: v{LATEST_VERSION}
- Status: UPDATE AVAILABLE | UP TO DATE

### Changes Since Baseline
#### Behavioral Changes (🔴 High Impact)
- [section name]: "old text" → "new text"
  Impact: affects how Claude handles [category]

#### Structural Changes (🟡 Low Impact)
- [description of structural change]

(or: "No changes — baseline is current.")

### Custom Prompt Review
| File | Status | Notes |
|------|--------|-------|
| golden.md | ✅/⚠️/❌ | ... |
| agents/_core.md | ✅/⚠️/❌ | ... |

### Recommendations
1. Adopt: [specific additions from Anthropic that enhance behavior]
2. Remove: [deprecated patterns now handled natively]
3. Adapt: [changes that require custom prompt updates]

### Next Steps
Run: `bd update baseline` to update baseline to v{LATEST_VERSION}
(or: confirm "update the baseline" to proceed)
```

If status is current: omit Recommendations; write "Baseline is current. No update needed."

### 5. Update Baseline (on user confirmation)

When the user confirms they want to update:
1. Copy `$NEW_PROMPT_FILE` to `{baseline-dir}/anthropic-v{LATEST_VERSION}.md`
2. Delete the old baseline file `{baseline-dir}/anthropic-v{BASELINE_VERSION}.md`
3. Remove the temp file: `rm -f "$NEW_PROMPT_FILE"`
4. Confirm: "Baseline updated to v{LATEST_VERSION}."

See your harness adapter for the exact baseline directory path.

NEVER auto-update without explicit user confirmation.
WHY: The baseline is the reference point for future diffs — an accidental update loses the diff history.

## Out of Scope

- Do not modify `golden.md` or agent prompts automatically — flag for human review only
- Do not run raw `diff` output — summarize and classify instead
- Do not fetch from DoltHub or any source other than `cchistory.mariozechner.at`
- Do not commit changes — user is responsible for committing baseline updates

## Resources

- `scripts/fetch-latest.sh` — version check and prompt download
- `tests/smoke-test.md` — expected behavior reference for manual verification
