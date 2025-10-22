---
name: reference-file-compactor
description: Compact reference files using validation-driven workflow with workspace isolation. Auto-detects single file or mass compaction mode. Uses concrete baseline generation and quality validation to ensure 100% value retention.
---

# Reference File Compactor

Validation-driven compaction workflow that removes redundant content while preserving all unique technical value through isolated workspace processing and quality validation.

## Overview

Skills often have reference files (`references/*.md`) containing redundant basic content. This skill compacts reference files by:

1. **Generating concrete baseline**: What ANY developer could write from a summary
2. **Comparing actual vs baseline**: Identify unique value vs generic content
3. **Validating quality**: Independent agent confirms value preservation
4. **Auto-applying changes**: Only after validation passes

**Key innovation**: Fresh context subagents generate baseline and validate results, ensuring unbiased quality assessment.

## Input Modes

This skill supports two modes with automatic detection:

### Single File Mode

Compact one reference file.

**Input**: `path/to/skill/references/filename.md`

**Detection**: Path ends with `.md` AND file exists

**Example**:
```
/compact-reference bash-best-practices/references/01-bash-vs-zsh.md
```

### Mass Compaction Mode

Compact all reference files in a skill.

**Input**: `path/to/skill-directory`

**Detection**: Directory contains `references/` subdirectory

**Example**:
```
/compact-reference bash-best-practices
```

**Behavior**:
- Discovers all `*.md` files in `references/` (top-level only)
- Processes each file through single-file workflow
- Reports aggregate metrics

## Compaction Workflow

**CRITICAL**: This workflow uses workspace isolation and validation to ensure quality.

### Prerequisites

- Reference file exists
- Parent skill has SKILL.md
- (No summaries.md required - generated fresh each time)

### Step 1: Workspace Setup

Create isolated workspace to avoid context pollution.

**Action**: Call setup script

```bash
WORKSPACE=$(bash reference-file-compactor/scripts/setup-workspace.sh "$REFERENCE_FILE" "$SKILL_DIR")
```

**Result**: Workspace created at `/tmp/compaction-<skill>-<timestamp>/`

**Structure**:
```
/tmp/compaction-<skillname>-<timestamp>/
├── original/              # Read-only copies
│   ├── reference.md
│   └── SKILL.md
├── artifacts/             # Generated during workflow
│   ├── summary.md         # What the reference contains
│   └── baseline.md        # What COULD be written from summary
├── compacted/             # Proposed changes
│   ├── reference-COMPACTED.md
│   └── SKILL-updated.md
├── validation/            # Quality evaluation
│   └── report.md          # ACCEPT/REJECT verdict
└── metadata/              # Paths for finalization
    ├── reference_path
    └── skill_dir
```

### Step 2: Generate Summary

**Agent**: Main agent (has context of the workflow)

**Action**: Read the reference file and generate a structured summary.

**Output**: `${WORKSPACE}/artifacts/summary.md`

**Structure**:
```markdown
## <basename>.md

**When to read**: [Specific scenario or question that leads user to this reference]

**What to expect**:
- [Major topic 1]: [Specific sub-topics, counts if applicable]
- [Major topic 2]: [Pattern libraries, examples, configurations]
- [Major topic 3]: [Pitfalls, anti-patterns, edge cases]

**Summary for SKILL.md**: "[One sentence capturing unique value - patterns, counts, categories]"
```

**Guidelines**:
- "When to read" = scenario-based triggers (not generic descriptions)
- "What to expect" = inventory of unique value (pattern counts, ❌/✅ comparisons, checklists)
- "Summary for SKILL.md" = what SURVIVES compaction (Tier 1/2), NOT basic concepts (Tier 3)

**Examples**:

Good summary for SKILL.md:
```
"Array slicing, associative arrays (Bash 4+), 6 patterns, 5 pitfalls"
```

Bad summary (too generic):
```
"Everything about arrays in Bash"
```

### Step 3: Launch Subagent A - Generate Baseline

**Purpose**: Create concrete baseline representing Tier 3 (removable) content

**Why fresh context?**: Subagent hasn't seen the actual file, so generates what ANY developer could write knowing ONLY the summary. This becomes the "removable content" baseline.

**Subagent type**: `general-purpose` (fresh context)

**Prompt for Subagent A**:

```
You are given a summary of a reference file at: ${WORKSPACE}/artifacts/summary.md

Generate a baseline reference document that represents what ANY competent developer could write knowing ONLY this summary.

Output to: ${WORKSPACE}/artifacts/baseline.md

Guidelines:

**INCLUDE** (generic content anyone could write):
- Section headers for topics mentioned in summary
- Generic explanations (e.g., "Arrays store multiple values")
- Basic examples anyone could create (e.g., `arr=("a" "b" "c")`)
- Placeholder text for patterns (e.g., "There are 6 common patterns" without actual patterns)
- Conceptual overviews without specific details

**DO NOT INCLUDE** (unique value):
- Specific edge cases or pitfalls
- Complete pattern code with explanations
- ❌/✅ comparisons
- Detailed configuration examples
- Production-ready scripts
- Exact command syntax beyond basics

This baseline represents Tier 3 content that will be removed from the actual reference file.

Keep it minimal and generic - think "what would a junior developer write as placeholder structure?"
```

**Result**: Baseline document saved to `${WORKSPACE}/artifacts/baseline.md`

### Step 4: Compare and Compact

**Agent**: Main agent (already has reference in context from Step 2)

**Action**:

1. Read the baseline document
2. Compare actual reference vs baseline side-by-side
3. For each section:
   - Content similar to baseline → Tier 3 (REMOVE)
   - Content NOT in baseline or exceeds baseline → Tier 1/2 (KEEP)
4. Read `reference-file-compactor/references/compaction-rules.md` for detailed Tier classification
5. Generate compacted file

**Classification examples**:

```markdown
Baseline: "Arrays store multiple values. Basic syntax: arr=(a b c)"
Original: "Arrays store multiple values. Basic syntax: arr=(a b c). Edge case: arr=() creates empty array, ${arr[@]} safely handles this..."
Compacted: "Edge case: arr=() creates empty array, ${arr[@]} safely handles this..." ✓
```

```markdown
Baseline: "There are 6 common patterns"
Original: "Pattern 1: Array from file lines\nmapfile -t lines < file.txt\n..."
Compacted: Keep ALL 6 complete patterns with code ✓
```

**Output**: `${WORKSPACE}/compacted/reference-COMPACTED.md`

**Format requirements**:
```markdown
# [Topic Name]

*See SKILL.md for [basic concepts from baseline]. This reference covers [unique value from summary].*

[Only Tier 1/2 content follows]
```

### Step 5: Update SKILL.md

**Agent**: Main agent

**Action**: Generate updated SKILL.md with Quick Decision Tree entry

1. Read original SKILL.md from workspace
2. Locate Quick Decision Tree section (or create if missing)
3. Find or create entry for this reference file
4. Use "Summary for SKILL.md" line from summary (Step 2)
5. Format: `- **[scenario]** → [filename.md] - [unique value one-liner]`

**Example entries**:
```markdown
## Quick Decision Tree

- **Array indexing issues?** → 04-arrays.md - Slicing, associative arrays (Bash 4+), 6 patterns, 5 pitfalls
- **Need strict error handling?** → 02-strict-mode.md - set -euo pipefail deep dive, 4 edge cases, exit trap patterns
- **ShellCheck warnings?** → 09-shellcheck-integration.md - 12 most common fixes with before/after
```

**Output**: `${WORKSPACE}/compacted/SKILL-updated.md`

### Step 6: Launch Subagent B - Validate Quality

**Purpose**: Holistic evaluation of compaction quality with fresh, unbiased perspective

**Why fresh context?**: Subagent hasn't seen the compaction process, so provides objective assessment of the final result.

**Subagent type**: `general-purpose` (fresh context)

**Prompt for Subagent B**:

```
Evaluate the compaction quality holistically by comparing these files:

**Original files**:
- Reference: ${WORKSPACE}/original/reference.md
- SKILL.md: ${WORKSPACE}/original/SKILL.md

**Compacted files**:
- Reference: ${WORKSPACE}/compacted/reference-COMPACTED.md
- SKILL.md: ${WORKSPACE}/compacted/SKILL-updated.md

**Artifacts**:
- Summary: ${WORKSPACE}/artifacts/summary.md
- Baseline: ${WORKSPACE}/artifacts/baseline.md

**Validation guidance**: Read reference-file-compactor/references/validation-criteria.md

**Evaluate**:

1. **Discovery flow**: Does Quick Decision Tree → compacted reference work?
   - User sees Quick Decision Tree entry
   - Decides when to read reference
   - Opens reference, finds promised content

2. **Promises alignment**: Does Quick Decision Tree entry match actual content?
   - If entry says "6 patterns" → compacted file has 6 patterns?
   - If entry says "4 pitfalls" → compacted file has 4 pitfalls?
   - Counts and categories accurate?

3. **Value preservation**: All Tier 1/2 content intact?
   - Pattern libraries complete (not just headers)?
   - ❌/✅ comparisons present?
   - Edge cases and pitfalls detailed?
   - Configuration examples complete?

4. **Tier classification accuracy**:
   - No Tier 3 content kept (generic explanations removed)?
   - No Tier 2 content removed (exact syntax preserved)?
   - Baseline comparison appropriate?

5. **Format quality**:
   - Opening line correct format?
   - Cross-references valid?
   - No broken links?

**Output format**:

VERDICT: [ACCEPT or REJECT]

REASONING:
[Detailed explanation of decision - what works well, what doesn't]

ISSUES (if REJECT):
- Issue 1: [Specific problem with evidence]
- Issue 2: [Specific problem with evidence]

GUIDANCE (if REJECT):
[Specific, actionable instructions for retry - be precise about what to fix and how]
```

**Save output**: `${WORKSPACE}/validation/report.md`

### Step 7: Decision Logic

Parse Subagent B verdict from validation report.

#### If ACCEPT

```bash
bash reference-file-compactor/scripts/finalize-compaction.sh --workspace="$WORKSPACE" --apply
```

**Actions**:
- Atomically copies compacted files to source locations
- Cleans up workspace
- Reports success with metrics

**Report format**:
```markdown
✓ Compaction accepted and applied

**File**: 04-arrays.md
**Metrics**:
- Original: 584 lines
- Compacted: 375 lines
- Reduction: 209 lines (35.8%)
- Verdict: ACCEPT (first attempt)

**Changes applied**:
- reference-file-compactor/references/04-arrays.md (updated)
- reference-file-compactor/SKILL.md (Quick Decision Tree updated)
```

#### If REJECT (attempt < 2)

**Actions**:
1. Read validator's GUIDANCE section
2. Retry compaction (Steps 4-5) with specific corrections
3. Re-validate (Step 6)
4. Loop back to decision logic

**Max attempts**: 2 retries

#### If REJECT (attempt >= 2)

```bash
bash reference-file-compactor/scripts/finalize-compaction.sh --workspace="$WORKSPACE"
```

**Actions**:
- Cleanup only (no apply)
- Report that file is optimally structured

**Report format**:
```markdown
✓ Reference file is optimally structured

**File**: 18-ci-cd-integration.md
**Analysis**: After 2 validation attempts, validator confirms file is already optimal.
This typically occurs with:
- Configuration files (configs ARE the value)
- Checklists (items ARE the value)
- Pattern libraries (code IS the value)

**Recommendation**: No changes needed. File structure is appropriate for content type.
```

## Mass Compaction

When invoked with skill directory instead of single file.

**Input**:
```
/compact-reference bash-best-practices/
```

**Workflow**:

1. **Discovery**: Find all `references/*.md` files (top-level only, excludes subdirectories)
   ```bash
   find "${SKILL_DIR}/references" -maxdepth 1 -name "*.md" -type f | sort
   ```
2. **Process each**: Invoke single-file workflow (Steps 1-7) for every file
3. **Collect metrics**: Track lines before/after, verdicts, attempts
4. **Aggregate report**: Summary of all compactions

**Example output**:

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

...

[18/20] Processing: 18-ci-cd-integration.md
  → Setup workspace: /tmp/compaction-bash-best-practices-20250122-145832
  → Summary → Baseline → Compact → Validate
  → REJECT (after 2 attempts): Reference is optimally structured
  → No changes applied

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

## Special File Types

### Checklists (e.g., code-review-checklist.md)

**Expect**: <10% reduction
- The checklist items ARE the value
- Only remove generic intros and redundant summaries
- Keep 95%+ of content
- Validator should accept with minimal changes

### Pattern Libraries (e.g., common-patterns.md)

**Expect**: ~5% reduction
- Pattern code is the value
- Only remove redundant overviews
- Keep nearly everything
- Validator should confirm all patterns intact

### Configuration Files (e.g., ci-cd-integration.md)

**Expect**: ~5% reduction (often REJECT as optimal)
- Configurations are unique
- Only remove generic explanations
- Keep working configs
- High likelihood of validation REJECT (already optimal)

### Technical Concept Files (e.g., strict-mode.md, arrays.md)

**Expect**: 20-50% reduction
- Remove basic explanations
- Remove simple examples
- Keep edge cases, pitfalls, advanced patterns
- Validator should confirm specifics preserved

## Quality Assurance

The validation workflow ensures:

1. **Unbiased baseline**: Subagent A generates without seeing actual file
2. **Independent validation**: Subagent B evaluates without seeing process
3. **Self-correcting**: Up to 2 retry attempts with specific guidance
4. **Atomic changes**: All-or-nothing apply with rollback on error
5. **Clean workspace**: Always cleaned up, even on failure

## Common Pitfalls to Avoid

### Over-compaction (Removing Tier 2)

**Problem**: Removing exact syntax because concept is in summary

**Example**:
```
Summary: "6 common patterns"
Compaction: Removes actual pattern code, keeps only headers
```

**Prevention**: Validator will REJECT and specify which patterns to restore

### Under-compaction (Keeping Tier 3)

**Problem**: Keeping basic explanations because "they're helpful"

**Example**:
```
Baseline: "Arrays store multiple values"
Original: "Arrays store multiple values" (identical)
Compaction: Keeps it anyway
```

**Prevention**: Validator will REJECT and identify Tier 3 content to remove

### Promise misalignment

**Problem**: Quick Decision Tree entry doesn't match compacted content

**Example**:
```
Quick Decision Tree: "6 patterns, 5 pitfalls"
Compacted file: Has 6 patterns but only 3 pitfalls
```

**Prevention**: Validator checks counts and categories

## Expected Outcomes

**Per file**:
- 5-50% size reduction (depends on file type)
- 100% value retention (validated)
- Clear cross-reference to SKILL.md
- Faster jump to unique value

**Across skill**:
- 15-35% overall reduction in reference content
- Improved signal-to-noise ratio
- Better user experience (clearer navigation)
- Maintained quality (validated)

## Resources

### references/compaction-rules.md

Comprehensive tier classification system:

- **Tier 3 (Remove)**: Content generatable from summary
- **Tier 2 (Keep)**: Detailed technical content
- **Tier 1 (Keep)**: Unique value patterns

Read in Step 4 to understand classification.

### references/validation-criteria.md

Validation framework for Subagent B:

- Discovery flow validation
- Promises alignment checks
- Value preservation verification
- Tier classification accuracy
- Format quality standards

Read this to understand what validators check.

## Implementation Notes

### Workspace Isolation

All work happens in `/tmp/compaction-*/` to avoid:
- Context pollution (no `summaries.md` in skill directory)
- Partial states (atomic apply)
- Leftover artifacts (always cleaned up)

### Token Efficiency

- Scripts handle deterministic operations (setup, finalize, file discovery)
- Main agent handles creative work (summary, compaction)
- Subagents handle analysis only (baseline, validation)
- Context reused where appropriate (main agent reads reference once)

### Error Handling

- Scripts fail fast with clear error messages
- Rollback on partial apply failures
- Guaranteed workspace cleanup
- Detailed logging for debugging
