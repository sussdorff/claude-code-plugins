# Reference File Compactor

Validation-driven skill compaction workflow with workspace isolation and quality assurance.

## Overview

A Claude Code skill that compacts reference documentation by removing redundant content while preserving 100% of unique technical value. Uses fresh-context subagents for baseline generation and validation to ensure quality.

**Key innovation**: Concrete baseline generation + independent validation prevents both over-compaction (losing value) and under-compaction (keeping bloat).

## Purpose

Skills accumulate reference files (`references/*.md`) that often contain:
- Generic explanations derivable from summaries
- Basic examples anyone could write
- Redundant introductions
- Content that could be inferred from context

This skill removes Tier 3 content (generic/derivable) while preserving Tier 1/2 content (unique value).

## Features

### Workspace Isolation
- All work in `/tmp/compaction-*/` - no context pollution
- Atomic apply (all-or-nothing)
- Always cleaned up, even on failure
- No `summaries.md` required (generated fresh)

### Validation-Driven
- **Subagent A**: Generates baseline (what ANY dev could write from summary)
- **Main agent**: Compacts by comparing actual vs baseline
- **Subagent B**: Validates quality with fresh, unbiased context
- **Self-correcting**: Up to 2 retry attempts with specific guidance

### Auto-Detection
- Single file: `/compact-reference path/to/file.md`
- Mass compaction: `/compact-reference path/to/skill/`
- Automatic mode detection based on input

### Quality Assurance
- Discovery flow validation (Quick Decision Tree → reference works?)
- Promises alignment (counts and content match?)
- Value preservation (all Tier 1/2 intact?)
- Tier classification accuracy (baseline comparison correct?)
- Format quality (opening line, cross-references)

## Workflow

```
Single File Compaction:
┌────────────────────────────────────────────────────────────┐
│ /compact-reference path/to/reference.md                   │
└────────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  1. Setup Workspace      │
         │  /tmp/compaction-*       │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  2. Generate Summary     │
         │  (Main Agent)            │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  3. Generate Baseline    │
         │  (Subagent A - fresh)    │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  4. Compare & Compact    │
         │  (Main Agent)            │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  5. Update SKILL.md      │
         │  (Main Agent)            │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  6. Validate Quality     │
         │  (Subagent B - fresh)    │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  7. Decision Logic       │
         │  ACCEPT → Apply          │
         │  REJECT → Retry/Report   │
         └──────────────────────────┘

Mass Compaction:
┌────────────────────────────────────────────────────────────┐
│ /compact-reference bash-best-practices/                   │
└────────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Discover all .md files  │
         │  in references/          │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  For each file:          │
         │  └→ Single file workflow │
         │     (Steps 1-7 above)    │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Aggregate Report        │
         │  - Total files           │
         │  - Compacted count       │
         │  - Rejected count        │
         │  - Total reduction %     │
         └──────────────────────────┘
```

## Usage

### Install

This is a Claude Code plugin. Install it using:

```bash
/plugin install reference-file-compactor@<marketplace-name>
```

Or for local development/testing, add this plugin to a local marketplace and install from there.

### Single File Compaction

```bash
/compact-reference bash-best-practices/references/01-bash-vs-zsh.md
```

**Output**:
```
✓ Compaction accepted and applied

**File**: 01-bash-vs-zsh.md
**Metrics**:
- Original: 584 lines
- Compacted: 375 lines
- Reduction: 209 lines (35.8%)
- Verdict: ACCEPT (first attempt)

**Changes applied**:
- bash-best-practices/references/01-bash-vs-zsh.md (updated)
- bash-best-practices/SKILL.md (Quick Decision Tree updated)
```

### Mass Compaction

```bash
/compact-reference bash-best-practices
```

**Output**:
```
Found 20 reference files to compact
========================================

[1/20] Processing: 01-bash-vs-zsh.md
  → Setup workspace: /tmp/compaction-bash-best-practices-20250122-143022
  → Summary → Baseline → Compact → Validate
  → ACCEPT (first attempt): 584 → 375 lines (-35.8%)
  ✓ Applied

[2/20] Processing: 02-strict-mode.md
  → Setup workspace: /tmp/compaction-bash-best-practices-20250122-143145
  → Summary → Baseline → Compact → Validate
  → REJECT (first attempt): Over-compaction detected
  → Retry with guidance
  → ACCEPT (second attempt): 472 → 279 lines (-40.9%)
  ✓ Applied

[3/20] Processing: 03-variable-scoping.md
  → ACCEPT: 389 → 267 lines (-31.4%)
  ✓ Applied

...

[18/20] Processing: 18-ci-cd-integration.md
  → REJECT (after 2 attempts): Reference is optimally structured
  → No changes applied

[19/20] Processing: 19-pre-commit-hooks.md
  → ACCEPT: 445 → 312 lines (-29.9%)
  ✓ Applied

[20/20] Processing: 20-function-discovery-extract-json.md
  → ACCEPT: 123 → 98 lines (-20.3%)
  ✓ Applied

========================================
Mass Compaction Summary
========================================
Total files: 20
Successfully compacted: 18
Rejected (optimal): 2
Total reduction: 1,234 lines (32.1%)
Average per file: -28.4%

Files requiring retry: 4
Files optimal on first try: 14
```

## Tier System

### Tier 3 - REMOVE (Generic/Derivable)
- Generic explanations derivable from summary
- Basic examples anyone could create
- Conceptual overviews without specifics
- Redundant introductions

**Example**:
```
Summary: "Arrays store multiple values"
Content: "Arrays in Bash allow you to store multiple values in a single variable..."
Action: REMOVE (derivable from summary)
```

### Tier 2 - KEEP (Detailed Technical)
- Exact syntax with flags and options
- Specific edge cases with explanations
- ❌/✅ code comparisons
- Detailed configuration examples
- Pitfalls with solutions

**Example**:
```
Content: "Edge case: Empty arrays arr=() are safe with ${arr[@]} but not ${arr[*]} in unquoted contexts..."
Action: KEEP (specific edge case beyond summary)
```

### Tier 1 - KEEP (Unique Value Patterns)
- Complete pattern libraries with code
- Full checklists
- Production-ready scripts
- Real-world examples
- Configuration templates

**Example**:
```
Content: "Pattern 3: Remove duplicates [full working code block]"
Action: KEEP (complete pattern is unique value)
```

## Expected Results

### Per File Type

| File Type | Expected Reduction | What's Kept | Example |
|-----------|-------------------|-------------|---------|
| **Technical concepts** | 20-50% | Edge cases, pitfalls, advanced patterns | strict-mode.md, arrays.md |
| **Checklists** | <10% | All checklist items (items ARE the value) | code-review-checklist.md |
| **Pattern libraries** | ~5% | All pattern code (patterns ARE the value) | common-patterns.md |
| **Configuration files** | ~5% or REJECT | All configs (configs ARE the value) | ci-cd-integration.md |

### Across Skill

- **Overall reduction**: 15-35% of reference content
- **Value retention**: 100% (validated)
- **Signal-to-noise**: Significantly improved
- **User experience**: Faster jump to unique value

## Validation Workflow

### Why Validation?

Without validation, compaction can:
- **Over-compact**: Remove Tier 2 content (lose value)
- **Under-compact**: Keep Tier 3 content (bloat remains)
- **Misalign promises**: Quick Decision Tree doesn't match content

### How Validation Works

**Subagent B** (fresh context, hasn't seen compaction process) evaluates:

1. **Discovery flow**: Quick Decision Tree → reference navigation works?
2. **Promises alignment**: Counts and content match Quick Decision Tree?
3. **Value preservation**: All Tier 1/2 content intact and complete?
4. **Tier classification**: Baseline comparison done correctly?
5. **Format quality**: Opening line format, cross-references valid?

**Verdict**:
- **ACCEPT**: Apply changes atomically
- **REJECT (attempt < 2)**: Retry with specific guidance
- **REJECT (attempt >= 2)**: Report as optimal, no changes

## Common Scenarios

### Scenario 1: Over-Compaction (Validator Catches)

```
Compaction removes pattern code (Tier 1)
Validator: REJECT - "Pattern 5 and 6 code blocks missing, these are Tier 1"
Retry: Restore patterns 5 and 6
Validator: ACCEPT
Result: Applied with all value preserved
```

### Scenario 2: Already Optimal (Validator Confirms)

```
File: ci-cd-integration.md (configuration file)
Compaction: Removes 5% generic intros
Validator: REJECT - "Minimal improvement, configs already optimal"
Result: No changes applied (file already good)
```

### Scenario 3: Clean Accept

```
File: strict-mode.md (technical concept)
Compaction: Removes 35% basic explanations, keeps edge cases
Validator: ACCEPT - "All edge cases preserved, Tier 3 correctly removed"
Result: Applied immediately
```

## Project Structure

```
reference-file-compactor/              # Plugin package
├── .claude-plugin/
│   └── plugin.json                    # Plugin metadata
├── commands/
│   └── compact-reference.md           # Slash command (/compact-reference)
├── skills/
│   └── reference-file-compactor/      # Skill directory
│       ├── SKILL.md                   # Skill workflow documentation
│       ├── references/
│       │   ├── compaction-rules.md    # Tier classification system
│       │   └── validation-criteria.md # Validation framework
│       └── scripts/
│           ├── setup-workspace.sh     # Create isolated workspace
│           └── finalize-compaction.sh # Apply changes + cleanup
└── README.md                          # This file
```

## Technical Details

### Workspace Structure

```
/tmp/compaction-<skillname>-<timestamp>/
├── original/                # Read-only source files
│   ├── reference.md
│   └── SKILL.md
├── artifacts/               # Generated during workflow
│   ├── summary.md          # What the reference contains
│   └── baseline.md         # What COULD be written from summary
├── compacted/              # Proposed changes
│   ├── reference-COMPACTED.md
│   └── SKILL-updated.md
├── validation/             # Quality evaluation
│   └── report.md          # ACCEPT/REJECT verdict
└── metadata/               # Paths for finalization
    ├── reference_path
    └── skill_dir
```

### Scripts (Bash)

All scripts use Bash with proper error handling:
- `set -euo pipefail` (strict mode)
- Clear error messages
- Atomic operations with rollback
- Guaranteed cleanup
- ShellCheck validated

### Subagent Design

**Fresh context is critical**:
- **Subagent A**: Hasn't seen actual file, generates unbiased baseline
- **Subagent B**: Hasn't seen compaction process, provides objective validation
- **Main agent**: Has full context, performs compaction with baseline comparison

## Known Limitations

### Current Scope

- Processes `.md` files only
- Requires parent skill to have SKILL.md
- Quick Decision Tree section expected in SKILL.md (created if missing)

### Not Suitable For

- Files that are entirely unique value (configs, checklists) → Will REJECT as optimal
- Files without generic content to remove → Minimal reduction expected
- Non-markdown reference files

### Future Enhancements

- Support for other file formats (JSON, YAML, etc.)
- Configurable validation strictness
- Batch processing with parallelization
- Metrics dashboard for historical tracking

## Contributing

To enhance this skill:

1. **Test with your skills**: Run on your reference files
2. **Report edge cases**: Files that don't compact well
3. **Improve validation**: Additional criteria for Subagent B
4. **Script improvements**: Better error handling, performance

## License

See repository LICENSE file.

## Credits

Part of the Claude Code Plugins marketplace.

**Approach**: Validation-driven compaction with workspace isolation and fresh-context quality assurance.
