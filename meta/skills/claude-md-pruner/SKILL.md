---
name: claude-md-pruner
model: sonnet
description: Review CLAUDE.md files for instructions that newer models handle natively and suggest removals. Use after model updates to prune outdated instructions. Triggers on "prune claude-md", "post-update review", "prune instructions", "model update cleanup".
disableModelInvocation: true
---

# CLAUDE.md Post-Model-Update Pruner

Review CLAUDE.md files after Claude model updates to identify and remove instructions that newer models now handle natively. Complements `claude-md-improver` (which adds/improves) by focusing on what to remove.

## When to Use

- After a new Claude model release (e.g., Opus 4.5 -> 4.6)
- Periodically when CLAUDE.md files feel bloated
- When you notice Claude following instructions it would do anyway without being told

## Workflow

### Phase 1: Gather Current Model Info

Identify the current model version:
```bash
claude --version 2>/dev/null || echo "Version unknown"
```

Ask the user: "What model version did you just update to?" (if not obvious from context).

### Phase 2: Discovery

Find all CLAUDE.md files:
```bash
find . -name "CLAUDE.md" -o -name ".claude.local.md" 2>/dev/null | head -50
```

Also check:
- `~/.claude/CLAUDE.md` (global)
- Project-level CLAUDE.md files

### Phase 3: Pattern Matching

For each CLAUDE.md file, scan for common categories of prunable instructions:

#### Category 1: Default Behaviors Now Built-In
Instructions telling Claude to do things it does by default in newer models:
- "Always read files before editing" (built-in since Sonnet 3.5)
- "Use grep/find to search before asking" (default behavior)
- "Think step by step" (thinking is native)
- "Be concise" / "Keep responses short" (default in CLI mode)
- "Don't apologize" (improved in newer models)
- "Use tools instead of suggesting commands" (default agentic behavior)

#### Category 2: Workarounds for Old Limitations
Instructions that worked around bugs or limitations in older models:
- Explicit JSON formatting instructions (models handle JSON well now)
- "Don't hallucinate file contents" (much improved)
- Explicit tool-use ordering instructions (models sequence well now)
- "Don't use interactive commands" (models avoid these now)

#### Category 3: Redundant with System Prompt
Instructions that duplicate what the Claude Code system prompt already says:
- Permission handling instructions
- Safety/security reminders that are in the system prompt
- Tool usage patterns covered by built-in instructions

#### Category 4: Overly Verbose Instructions
Instructions that could be condensed without losing effectiveness:
- Multi-paragraph explanations where one line suffices
- Examples that are obvious
- Repeated instructions (same thing said multiple ways)

### Phase 4: Pruning Report

Output a structured report:

```markdown
## CLAUDE.md Pruning Report

### Model: [current model version]
### Files Scanned: [count]

### Recommended Removals

#### [filename]

| # | Line(s) | Current Instruction | Category | Reason |
|---|---------|-------------------|----------|--------|
| 1 | 15-16 | "Always read files before editing them" | Built-in | Default behavior since Sonnet 3.5 |
| 2 | 23 | "Think through problems step by step" | Built-in | Native thinking mode |
| 3 | 45-52 | [verbose JSON formatting block] | Verbose | Can be condensed to 1 line |

### Recommended Condensations

| # | Line(s) | Current (X lines) | Suggested (Y lines) | Savings |
|---|---------|-------------------|---------------------|---------|
| 1 | 30-38 | [9-line block] | [3-line version] | 6 lines |

### Summary
- Lines removable: X
- Lines condensable: X -> Y
- Estimated token savings: ~X tokens per session
```

### Phase 5: Apply Changes

After user approval:
1. Remove approved lines using Edit tool
2. Apply approved condensations
3. Verify the file still reads coherently after changes

## Important Notes

- **Never remove project-specific instructions** (build commands, architecture notes, gotchas)
- **Never remove user preferences** (formatting, workflow, tool choices)
- **When in doubt, keep it** — removing a needed instruction is worse than keeping an unnecessary one
- **Check with user** before removing anything that looks like it might encode a preference vs. a workaround
- Focus on the **highest-token-saving removals first** for maximum impact
