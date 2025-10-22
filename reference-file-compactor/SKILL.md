---
name: reference-file-compactor
description: This skill should be used to compact individual reference files within a skill by removing content redundant with summaries while preserving 100% of unique value. Designed to be called by an orchestrator for each reference file. Processes one file at a time with fresh context.
---

# Reference File Compactor

Compact individual skill reference files by removing redundancy with summaries while preserving all unique technical value.

## Overview

Skills often have reference files (`references/*.md`) that contain redundant basic content that could be generated from SKILL.md summaries alone. This skill compacts a single reference file by:

1. Using the summary as a baseline
2. Identifying removable content (Tier 3)
3. Preserving unique value (Tier 1/2)
4. Reducing file size 5-50% while keeping 100% value

**Designed for orchestration**: Process one file at a time. An orchestrator should call this skill for each reference file in sequence.

## When to Use

Use this skill when:
- A skill has `references/` directory with documentation files
- A `summaries.md` file exists describing each reference
- Need to reduce context usage while preserving value
- Preparing skill for distribution

**Input requirements**:
- Path to a single reference file to compact
- Path to `summaries.md` containing description of that file
- Both files must exist

## Compaction Workflow

**CRITICAL: Follow steps IN ORDER to avoid context contamination.**

### Step 1: Read ONLY the Summary (DO NOT Read Actual File Yet)

**Purpose**: Generate a clean baseline without being influenced by the actual file content.

```bash
# Read the summaries file
Read: <skill-path>/summaries.md
```

**Extract for the target file**:
- When to read this reference
- What to expect in the reference
- Summary for SKILL.md

**Mental baseline**: Based ONLY on the summary, mentally note what content you could generate yourself. This becomes the "removable content" baseline.

### Step 2: Read the Actual Reference File

```bash
# Now read the actual file
Read: <skill-path>/references/<filename>.md
```

Count total lines for metrics reporting.

### Step 3: Read Compaction Rules

```bash
# Read the tier classification system
Read: reference-file-compactor/references/compaction-rules.md
```

This provides:
- Tier 1/2/3 definitions
- Decision framework
- Common removal patterns
- Special cases (checklists, configs, patterns)
- Output format requirements

### Step 4: Compare Actual vs Baseline

For each section in the actual file, categorize:

**❌ REMOVE (Tier 3)**: Content you COULD generate from summary alone
- Generic explanations of concepts mentioned in summary
- Basic examples showing concepts in summary
- Redundant introductions
- Summary sections duplicating the summary

**✅ KEEP (Tier 1/2)**: Content you COULD NOT generate from summary
- Exact syntax and command examples
- Specific edge cases and exceptions
- Complete pattern libraries
- ❌/✅ code comparisons
- Detailed pitfalls with solutions
- Configuration files and templates
- Real-world production examples
- Anti-patterns with code

**Document your thinking**: For transparency, document why each major section is removed or kept.

### Step 5: Create Compacted Version

**File location**: Write to same directory with `-COMPACTED` suffix
```
<skill-path>/references/<filename>-COMPACTED.md
```

**Opening line** (required format):
```markdown
# [Topic Name]

*See SKILL.md for [basic concepts from summary]. This reference covers [unique value from summary].*
```

**Content**: Include ONLY Tier 1/2 content

**No closing summary**: Remove any summary sections at the end

### Step 6: Report Results

Provide metrics:

```markdown
## Compaction Results

**File**: <filename>.md

**Metrics**:
- Original lines: XXX
- Compacted lines: XXX
- Reduction: XXX lines (XX.X%)
- Value retained: 100%

**Removed (Tier 3)**:
- [Category 1]: [brief description] ([line count] lines)
- [Category 2]: [brief description] ([line count] lines)
- ...

**Kept (Tier 1/2)**:
- [Category 1]: [what was preserved and why]
- [Category 2]: [what was preserved and why]
- ...

**Key Achievement**: [One sentence explaining what makes the compacted version valuable]
```

## Special File Types

### Checklists (e.g., code-review-checklist.md)

**Expect**: <10% reduction
- The checklist items ARE the value
- Only remove generic intros and redundant summaries
- Keep 95%+ of content

### Pattern Libraries (e.g., common-patterns.md)

**Expect**: ~5% reduction
- Pattern code is the value
- Only remove redundant overviews
- Keep nearly everything

### Configuration Files (e.g., ci-cd-integration.md)

**Expect**: ~5% reduction
- Configurations are unique
- Only remove generic explanations
- Keep working configs

### Technical Concept Files (e.g., strict-mode.md, arrays.md)

**Expect**: 20-50% reduction
- Remove basic explanations
- Remove simple examples
- Keep edge cases, pitfalls, advanced patterns

## Quality Validation

Before completing, verify:

- [ ] Opening line uses correct format
- [ ] All Tier 1/2 content present
- [ ] No Tier 3 content remains
- [ ] All ❌/✅ comparisons intact
- [ ] All code examples complete
- [ ] All configs/templates intact
- [ ] All real-world examples present
- [ ] No broken cross-references

## Common Pitfalls to Avoid

1. **Reading file before summary** → Context contamination
   - You already know what's in the file
   - Can't generate clean baseline
   - **Solution**: Always read summary first

2. **Removing Tier 2 content** → Value loss
   - Removing exact syntax because concept is in summary
   - **Solution**: If summary says "covers X", keep the exact code for X

3. **Keeping Tier 3 content** → Bloat remains
   - Keeping basic explanations because "they're helpful"
   - **Solution**: If you could write it from summary, remove it

4. **Inconsistent opening line** → Poor cross-referencing
   - Not following the required format
   - **Solution**: Use the exact template

## Expected Outcomes

**Per file**:
- 5-50% size reduction (depends on file type)
- 100% value retention
- Clear cross-reference to SKILL.md
- Faster jump to unique value

**Across skill**:
- 15-20% overall reduction in reference content
- Improved signal-to-noise ratio
- Better user experience
- Maintained quality

## Resources

### references/compaction-rules.md

Comprehensive tier classification system and decision framework:

- **Tier 3 (Remove)**: Content generatable from summary
- **Tier 2 (Keep)**: Detailed technical content
- **Tier 1 (Keep)**: Unique value patterns

Includes:
- Decision framework with questions
- Common removal patterns
- Special case handling
- Output format requirements
- Validation checklist

**Read this file** in Step 3 of the workflow to understand what to keep vs remove.
