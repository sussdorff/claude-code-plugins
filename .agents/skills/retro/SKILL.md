---
name: retro
model: opus
description: >-
  Run a data-driven bi-weekly retrospective using open-brain timeline, bead metrics, and git history. Detects signals, selects a matching retro method, and guides 4 reflection rounds. Use when running a retro, sprint review, or bi-weekly reflection.
disableModelInvocation: true
---

# Bi-Weekly Retrospective

Data-driven retrospective that collects signals from the last 14 days, selects the best-fit
method from the retro-methods catalog, and runs 4 structured reflection rounds. Produces
max 3 concrete action beads.

## When to Use

- Bi-weekly retrospective or sprint review
- User says "retro", "retrospective", "sprint review", "bi-weekly reflection"
- After completing a significant batch of beads
- Periodically (every ~2 weeks) for continuous improvement

## Usage

```
retro                    # Full retrospective with data collection
retro --method=4Ls       # Force a specific method (skip signal detection)
retro --dry-run          # Print analysis and suggestions without creating beads
```

## Phase 1: Previous Retro Follow-Up

Before collecting new data, check for existing retro actions.

```bash
bd list --label=retro-action
```

For each found action bead, report its status (done/in_progress/open). Ask the user
whether to carry over open actions or close them.

WHY: Retrospectives without follow-up accountability are theater. Checking prior actions
first ensures the loop is closed.

## Phase 2: Data Collection (Researcher Subagent)

Spawn a `researcher` subagent to collect data from three sources in parallel:

1. **open-brain timeline** (last 14 days):
   ```
   the open-brain timeline connector with the appropriate date range
   ```

2. **Bead metrics report**:
   ```bash
   uv run python -c "import os, sys; sys.path.insert(0, os.path.join(os.environ['CLAUDE_PLUGIN_ROOT'], 'lib')); from orchestrator.metrics import query_report; print(query_report())"
   ```

3. **Git log** (last 14 days, all branches):
   ```bash
   git log --oneline --all --since='14 days ago'
   ```

The researcher subagent returns a structured summary with: timeline_entries, metrics_data,
git_commits, and detected_signals.

## Phase 3: Signal Detection

Analyze collected data for these signals:

| Signal | Detection Rule |
|--------|---------------|
| `recurring_problems` | Same issue/frustration appears 3+ times in timeline |
| `low_energy` | Confidence < 0.5 or negative sentiment in >40% of entries |
| `data_heavy` | Bead metrics show outlier costs (>2x median total_tokens) |
| `high_churn` | Branches with 5+ force-pushes or impl:review ratio > 5:1 |

If no signal is detected, use `default` (maps to the 4Ls method).

When `--method` is specified, skip signal detection and use the requested method directly.

## Phase 4: Method Selection

Load `standards/retro-methods.yml`. Match detected signals against each method's
`signal_match` list. Select the first method whose signal_match includes a detected signal.
If multiple signals are detected, prefer methods that match the strongest signal (highest
occurrence count).

If the specified method name is not found in the catalog, list available methods and ask the user to choose.

Present the selected method to the user with its description. Allow override before
proceeding.

## Phase 5: Reflection Rounds

Run 4 sequential reflection rounds using the selected method's `round_prompts` from
the catalog. Each round:

1. Present the round prompt to the user
2. Share relevant data excerpts that inform this round's perspective
3. Discuss with the user — ask clarifying questions
4. Summarize key insights from the round before moving to the next

WHY: Sequential rounds prevent premature convergence. Each round_prompts entry provides
a different lens on the same data, surfacing insights that a single-pass review misses.

## Phase 6: Action Creation

After all 4 reflection rounds, synthesize insights into concrete actions.

**Rules:**
- Maximum 3 actions. Force prioritization — more than 3 dilutes focus.
- Each action must be specific and achievable within 2 weeks.
- Title format: `[RETRO-ACTION] <concrete action>`

```bash
bd create --type=task --priority=2 --labels=retro-action --title="[RETRO-ACTION] <action>"
```

If `--dry-run` is set, print proposed actions without creating beads.

## Output Format

```
## Retrospective Summary

**Method:** <selected method name>
**Signal(s):** <detected signals or "none (default)">
**Period:** <date range>

### Previous Actions Follow-Up
| Action | Status |
|--------|--------|
| ... | done/open/carried over |

### Round Insights
1. <Round 1 name>: <key insight>
2. <Round 2 name>: <key insight>
3. <Round 3 name>: <key insight>
4. <Round 4 name>: <key insight>

### New Actions
1. [RETRO-ACTION] <action> → bead <id>
2. [RETRO-ACTION] <action> → bead <id>
3. [RETRO-ACTION] <action> → bead <id>
```

## Do NOT

- Do NOT skip the previous retro follow-up phase. WHY: Untracked actions erode trust in the retro process.
- Do NOT create more than 3 action beads. WHY: Overcommitting guarantees under-delivery.
- Do NOT fabricate signals — only report what the data shows. WHY: Inflated urgency leads to wrong method selection.
- Do NOT skip reflection rounds or collapse them into one. WHY: Each round surfaces different insights through its unique lens.
- Do NOT proceed without user confirmation of the selected method. WHY: User agency over the process increases engagement and ownership.

## Resources

- `standards/retro-methods.yml` — Method catalog with signal mappings and round prompts
- `compound` — Compound retrospective for individual bead debriefs (different scope)
- `learnings-pipeline` — For materializing retro insights into permanent standards
