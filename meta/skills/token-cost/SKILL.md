---
name: token-cost
model: sonnet
description: >-
  Measure static context token overhead for agent sessions. Use when auditing
  context window usage, checking skill/agent/conventions token costs, or generating
  a ranked report of heaviest context contributors.
requires_standards: [english-only]
---

# Token Cost Measurement

Scan the config filesystem and produce a ranked report of static context overhead per category: skills, agents, conventions file chain, and MCP server configs.

## When to Use

- "How much context do my skills use?"
- "Token audit" / "measure context overhead" / "context budget report"
- "Which skill is heaviest?" / "rank context contributors"
- "What percentage of my context window is already used at session start?"

## Workflow

### 1. Run the Measurement Script

Run the `measure-context.sh` script from this skill's `scripts/` directory.
See your harness adapter for the exact invocation path and default scan directories.

Default scans include: the skills directory, agents directory, the project conventions file chain, and MCP/settings configs. See harness adapter for exact paths.

**Flags:**
- `--skills-dir DIR` — override skills path
- `--agents-dir DIR` — override agents path
- `--claude-md FILE` — comma-separated list of CLAUDE.md files to scan
- `--mcp-config FILE` — override MCP config path
- `--category skills|agents|claude-md|mcp|all` — scan only one category
- `--format table|json` — output format (default: table)
- `--window N` — context window size in tokens (default: 200000)
- `--save` — save open-brain observation with audit summary

### 2. Interpret Output

The script produces three sections:

**Summary** — total static token overhead and % of 200k context window used.

**By Category** — breakdown across skills, agents, CLAUDE.md chain, MCP configs.

**Ranked Contributors** — individual files sorted heaviest-first, with budget status for skills.

**Budget Warnings** — skills that exceed their tier budget (light < 1k, medium total < 5k, heavy total < 8k).

### 3. Save Trending Observation (optional)

Run with `--save` to append a `### SAVE_OBSERVATION` block to the output.

When that block appears, save the observation to persistent memory if supported:
- `type`: `observation`
- `title`: from the `title:` line (e.g. `Token Cost Audit 2026-04-05`)
- `text`: full text block (totals + top contributors + warnings)

If cross-session memory is unavailable, skip this step — the delta tracking feature will be absent.

See your harness adapter for the exact memory-save mechanism.

WHY: Persistent observations enable delta tracking — you can detect slow token creep as skills accumulate reference files across sessions.

## Token Estimation Method

`wc -w FILE | awk '{print int($1 * 1.33)}'` — word count times 1.33 approximates Claude/GPT token count for English prose. Code-heavy files may have higher ratios; treat as an estimate.

## Limitations

- **MCP instruction text**: MCP servers provide instructions at runtime — static config files only reveal server names and transport. The script counts server metadata (~20 tokens/server) as a placeholder. Actual MCP overhead is unmeasurable without runtime inspection.
- **Dynamic context**: system prompts injected by hooks or tool calls are not included.
- **Symlinked skills**: resolved via `pwd -P` to avoid double-counting.

## Output Example

```
## Context Token Audit — 2026-04-05

### Summary
Total context components: ~42,000 tokens
Context window: 200,000 tokens (21.00% used by static context)

### By Category
| Category        | Tokens | % of Context |
|-----------------|--------|--------------|
| Skills          | 35000  | 17.50%       |
| Agents          |  4000  |  2.00%       |
| CLAUDE.md chain |  2500  |  1.25%       |
| MCP configs     |   500  |  0.25%       |
| **TOTAL**       | 42000  | 21.00%       |
```

## Resources

- `scripts/measure-context.sh` — measurement engine
- Token budget tiers standard — tier budget definitions (see harness adapter for path)
- `skill-auditor` skill — fleet quality audit (complementary tool)

## Out of Scope

- Modifying or improving skills (use `skill-auditor` + `skill-creator`)
- Runtime token measurement (requires API instrumentation)
- Measuring project-specific context beyond CLAUDE.md
