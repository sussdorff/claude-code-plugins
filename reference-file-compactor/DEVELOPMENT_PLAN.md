# Reference File Compactor - Validation-Based Workflow

## Development Plan

**Branch**: `feat/reference-compactor-validation-workflow`
**Status**: Planning
**Goal**: Implement validation-driven compaction workflow with workspace isolation, quality assurance, and mass processing

---

## Architecture Overview

### Key Design Decisions

1. **No summaries.md**: Use ephemeral `/tmp/<basename>-summary.md` to avoid context pollution
2. **Unified command**: Single `/compact-reference` command auto-detects file vs directory
3. **Workspace isolation**: All work in `/tmp/compaction-<skill>-<timestamp>/`, atomic apply
4. **Validation-driven**: Subagent B validates quality before auto-applying changes
5. **Hybrid approach**: Task tool for AI analysis, bash scripts for file operations
6. **Self-correcting**: Retry loop with specific validator feedback (max 2 attempts)

### Workflow Architecture

```
/compact-reference <file-or-skill-directory>
  ↓
[Auto-detect: .md file OR skill directory]
  ↓
Setup workspace (/tmp/compaction-*)
  ↓
Main Agent: Read reference → Generate summary → Save to artifacts/
  ↓
Subagent A (fresh context): Read summary → Generate baseline → Return
  ↓
Main Agent: Compare reference vs baseline → Compact
  ↓
Main Agent: Update SKILL.md Quick Decision Tree
  ↓
Subagent B (fresh context): Validate quality (4 files) → ACCEPT/REJECT
  ↓
Decision:
├─ ACCEPT → finalize-compaction.sh --apply → Report success
├─ REJECT (attempt < 2) → Retry with specific guidance
└─ REJECT (attempt >= 2) → finalize-compaction.sh (cleanup only) → Report optimal
```

### Workspace Structure

```
/tmp/compaction-<skillname>-<timestamp>/
├── original/              # Read-only copies of source files
│   ├── reference.md
│   └── SKILL.md
├── artifacts/             # Generated during workflow
│   ├── summary.md         # What the reference contains
│   └── baseline.md        # What COULD be written from summary
├── compacted/             # Proposed changes
│   ├── reference-COMPACTED.md
│   └── SKILL-updated.md
└── validation/            # Subagent B evaluation
    └── report.md          # ACCEPT/REJECT + reasoning
```

---

## Implementation Phases

### Phase 1: Create Workspace Management Scripts

#### 1.1 Create `scripts/setup-workspace.sh`

**Purpose**: Create isolated workspace, copy source files

**Interface**:
```bash
scripts/setup-workspace.sh <reference-file-path> <skill-directory>
# Output: /tmp/compaction-<skillname>-<timestamp>
```

**Logic**:
```bash
#!/usr/bin/env bash
set -euo pipefail

REFERENCE_FILE="$1"
SKILL_DIR="$2"
SKILL_NAME="$(basename "$SKILL_DIR")"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
WORKSPACE="/tmp/compaction-${SKILL_NAME}-${TIMESTAMP}"

# Create structure
mkdir -p "$WORKSPACE"/{original,artifacts,compacted,validation}

# Copy source files (read-only reference)
cp "$REFERENCE_FILE" "$WORKSPACE/original/reference.md"
cp "${SKILL_DIR}/SKILL.md" "$WORKSPACE/original/SKILL.md"

# Output workspace path
echo "$WORKSPACE"
```

**Validation**:
- Reference file exists
- SKILL.md exists in skill directory
- Workspace created successfully

#### 1.2 Create `scripts/finalize-compaction.sh`

**Purpose**: Apply changes (optional) + cleanup workspace (always)

**Interface**:
```bash
scripts/finalize-compaction.sh --workspace=<path> [--apply]
```

**Logic**:
```bash
#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=""
APPLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace=*)
            WORKSPACE="${1#*=}"
            shift
            ;;
        --apply)
            APPLY=true
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$WORKSPACE" ]]; then
    echo "Error: --workspace required" >&2
    exit 1
fi

# Read metadata from workspace
REFERENCE_FILE="$(<"${WORKSPACE}/metadata/reference_path")"
SKILL_DIR="$(<"${WORKSPACE}/metadata/skill_dir")"

# Apply changes if requested
if [[ "$APPLY" == "true" ]]; then
    echo "Applying changes..."

    # Atomic operations with rollback
    BACKUP_DIR="/tmp/compaction-backup-$$"
    mkdir -p "$BACKUP_DIR"

    # Backup originals
    cp "$REFERENCE_FILE" "${BACKUP_DIR}/reference.md.backup"
    cp "${SKILL_DIR}/SKILL.md" "${BACKUP_DIR}/SKILL.md.backup"

    # Apply changes
    if ! cp "${WORKSPACE}/compacted/reference-COMPACTED.md" "$REFERENCE_FILE"; then
        # Rollback on error
        cp "${BACKUP_DIR}/reference.md.backup" "$REFERENCE_FILE"
        echo "Error: Failed to apply reference changes, rolled back" >&2
        rm -rf "$BACKUP_DIR" "$WORKSPACE"
        exit 1
    fi

    if ! cp "${WORKSPACE}/compacted/SKILL-updated.md" "${SKILL_DIR}/SKILL.md"; then
        # Rollback on error
        cp "${BACKUP_DIR}/reference.md.backup" "$REFERENCE_FILE"
        cp "${BACKUP_DIR}/SKILL.md.backup" "${SKILL_DIR}/SKILL.md"
        echo "Error: Failed to apply SKILL.md changes, rolled back" >&2
        rm -rf "$BACKUP_DIR" "$WORKSPACE"
        exit 1
    fi

    # Success - remove backups
    rm -rf "$BACKUP_DIR"
    echo "✓ Changes applied successfully"
fi

# Always cleanup workspace
rm -rf "$WORKSPACE"
echo "✓ Workspace cleaned up"
```

**Features**:
- Atomic apply (all-or-nothing)
- Rollback on error
- Always cleanup (even if apply fails)
- No partial states

#### 1.3 Create `scripts/compact-all.sh`

**Purpose**: Mass compaction orchestrator

**Interface**:
```bash
scripts/compact-all.sh <skill-directory>
```

**Logic**:
```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$1"
REFERENCES_DIR="${SKILL_DIR}/references"

if [[ ! -d "$REFERENCES_DIR" ]]; then
    echo "Error: No references/ directory in $SKILL_DIR" >&2
    exit 1
fi

# Discover all reference files
mapfile -t files < <(find "$REFERENCES_DIR" -name "*.md" -type f | sort)

if [[ ${#files[@]} -eq 0 ]]; then
    echo "No reference files found in $REFERENCES_DIR" >&2
    exit 1
fi

echo "Found ${#files[@]} reference files to compact"
echo "----------------------------------------"

# Track metrics
total_files=0
compacted_files=0
rejected_files=0
total_lines_before=0
total_lines_after=0

# Process each file
for file in "${files[@]}"; do
    ((total_files++))
    echo ""
    echo "[$total_files/${#files[@]}] Processing: $(basename "$file")"

    # Invoke single-file compaction via /compact-reference command
    # (This would actually be invoked by Claude Code, not directly)
    # For now, this script reports the intention
    echo "  → Would invoke: /compact-reference $file"

    # Collect metrics (placeholder - actual implementation would track real metrics)
    # compacted_files++  or  rejected_files++
    # total_lines_before += X
    # total_lines_after += Y
done

echo ""
echo "========================================"
echo "Mass Compaction Summary"
echo "========================================"
echo "Total files: $total_files"
echo "Successfully compacted: $compacted_files"
echo "Rejected (optimal): $rejected_files"
echo "Total reduction: $((total_lines_before - total_lines_after)) lines (XX.X%)"
```

**Enhancement note**: Final implementation should invoke actual compaction workflow and collect real metrics.

---

### Phase 2: Update SKILL.md with New Workflow

#### 2.1 Add Auto-Detection Section

```markdown
## Input Modes

This skill supports two modes:

1. **Single file mode**: Compact one reference file
   ```
   Input: path/to/skill/references/filename.md
   ```

2. **Mass compaction mode**: Compact all reference files in a skill
   ```
   Input: path/to/skill-directory
   Detection: Directory contains references/ subdirectory
   ```

Auto-detection logic:
- If input ends with `.md` AND file exists → Single file mode
- If input is directory with `references/` subdirectory → Mass mode
- Otherwise → Error
```

#### 2.2 Complete 7-Step Workflow

Add detailed workflow section:

```markdown
## Compaction Workflow

**CRITICAL**: This workflow uses workspace isolation and validation to ensure quality.

### Prerequisites
- Reference file exists
- Parent skill has SKILL.md
- (No summaries.md required - generated fresh each time)

### Step 1: Workspace Setup

Call setup script to create isolated workspace:

```bash
WORKSPACE=$(bash scripts/setup-workspace.sh "$REFERENCE_FILE" "$SKILL_DIR")
```

Workspace structure created at `/tmp/compaction-<skill>-<timestamp>/`

### Step 2: Generate Summary

**Main agent**: Read the reference file and generate a structured summary.

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
- "When to read" = scenario-based triggers
- "What to expect" = inventory of unique value (pattern counts, ❌/✅ comparisons, checklists)
- "Summary for SKILL.md" = what SURVIVES compaction (Tier 1/2), NOT basic concepts (Tier 3)

### Step 3: Launch Subagent A - Generate Baseline

**Purpose**: Create concrete baseline representing Tier 3 (removable) content

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

Keep it minimal and generic.
```

**Result**: Baseline document returned, saved to `${WORKSPACE}/artifacts/baseline.md`

### Step 4: Compare and Compact

**Main agent** (already has reference in context):

1. Read the baseline document
2. Compare actual reference vs baseline side-by-side
3. For each section:
   - Content similar to baseline → Tier 3 (REMOVE)
   - Content NOT in baseline or exceeds baseline → Tier 1/2 (KEEP)
4. Read `references/compaction-rules.md` for detailed Tier classification
5. Generate compacted file

**Output**: `${WORKSPACE}/compacted/reference-COMPACTED.md`

**Format requirements**:
```markdown
# [Topic Name]

*See SKILL.md for [basic concepts from baseline]. This reference covers [unique value from summary].*

[Only Tier 1/2 content follows]
```

### Step 5: Update SKILL.md

**Main agent**: Generate updated SKILL.md with Quick Decision Tree entry

1. Read original SKILL.md
2. Locate Quick Decision Tree section
3. Find or create entry for this reference file
4. Use "Summary for SKILL.md" line from summary
5. Format: `- **[scenario]** → [filename.md] - [unique value one-liner]`

**Output**: `${WORKSPACE}/compacted/SKILL-updated.md`

### Step 6: Launch Subagent B - Validate Quality

**Purpose**: Holistic evaluation of compaction quality

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

**Validation guidance**: Read references/validation-criteria.md

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
[Detailed explanation of decision]

ISSUES (if REJECT):
- Issue 1: [Specific problem]
- Issue 2: [Specific problem]

GUIDANCE (if REJECT):
[Specific instructions for retry]
```

**Save output**: `${WORKSPACE}/validation/report.md`

### Step 7: Decision Logic

Parse Subagent B verdict:

**If ACCEPT**:
```bash
bash scripts/finalize-compaction.sh --workspace="$WORKSPACE" --apply
```
- Atomically copies compacted files to source
- Cleans up workspace
- Report success with metrics

**If REJECT (attempt < 2)**:
- Read validator's GUIDANCE
- Retry compaction (Step 4-5) with specific corrections
- Re-validate (Step 6)
- Loop back to decision

**If REJECT (attempt >= 2)**:
```bash
bash scripts/finalize-compaction.sh --workspace="$WORKSPACE"
```
- Cleanup only (no apply)
- Report: "Reference file is optimally structured, no compaction needed"

**Metrics to report**:
- Original lines: XXX
- Compacted lines: XXX
- Reduction: XXX lines (XX.X%)
- Verdict: ACCEPT/REJECT
- Attempts: X
```

#### 2.3 Add Mass Compaction Section

```markdown
## Mass Compaction

When invoked with skill directory instead of file:

```
Input: bash-best-practices/
```

Workflow:
1. Discover all `references/*.md` files
2. For each file:
   - Invoke single-file compaction workflow (Steps 1-7)
   - Collect metrics (lines before/after, verdict)
3. Aggregate results
4. Report summary

**Script**: `scripts/compact-all.sh` handles orchestration

**Example output**:
```
Found 20 reference files to compact
----------------------------------------

[1/20] Processing: 01-bash-vs-zsh.md
  → Setup workspace
  → Summary → Baseline → Compact → Validate
  → ACCEPT: 584 → 375 lines (-35.8%)

[2/20] Processing: 02-strict-mode.md
  → Setup workspace
  → Summary → Baseline → Compact → Validate
  → ACCEPT: 472 → 279 lines (-40.9%)

...

[18/20] Processing: 18-ci-cd-integration.md
  → Setup workspace
  → Summary → Baseline → Compact → Validate
  → REJECT: Reference is optimally structured (config file)

========================================
Mass Compaction Summary
========================================
Total files: 20
Successfully compacted: 18
Rejected (optimal): 2
Total reduction: 1,234 lines (32.1%)
```
```

---

### Phase 3: Create Validation Reference

#### Create `references/validation-criteria.md`

```markdown
# Validation Criteria for Subagent B

## Purpose

Guide Subagent B in evaluating compaction quality holistically.

## Evaluation Framework

### 1. Discovery Flow Validation

**Question**: Would a user successfully use SKILL.md → reference flow?

**Check**:
- Quick Decision Tree entry describes a clear scenario
- Scenario matches "When to read" from summary
- User can decide if they need this reference
- Reference delivers on the promise

**Example PASS**:
```
Quick Decision Tree: "Array indexing issues? → 04-arrays.md - Slicing, associative arrays (Bash 4+), 6 patterns, 5 pitfalls"
Compacted file: Has array slicing section, associative arrays section, 6 complete patterns, 5 detailed pitfalls
```

**Example FAIL**:
```
Quick Decision Tree: "Array indexing issues? → 04-arrays.md - 6 patterns"
Compacted file: Has only pattern headers, no actual code
```

### 2. Promises Alignment

**Question**: Does compacted file match Quick Decision Tree claims?

**Check counts**:
- "6 patterns" → Exactly 6 complete patterns present?
- "4 pitfalls" → Exactly 4 detailed pitfalls present?
- "3 variations" → Exactly 3 variations documented?

**Check content types**:
- "Edge cases" → Specific edge cases (not generic explanations)?
- "❌/✅ comparisons" → Actual code comparisons present?
- "Production examples" → Complete working examples?

**Red flags**:
- Counts don't match
- Promised content missing
- Only placeholders/headers without details

### 3. Value Preservation

**Question**: Is all Tier 1/2 content intact?

**Tier 1 (Must be complete)**:
- Pattern libraries: All patterns with full code
- Checklists: All items present
- Production scripts: Complete and working
- Real-world examples: Full context + code

**Tier 2 (Must be detailed)**:
- Exact syntax: Beyond basic examples
- Edge cases: Specific scenarios with explanations
- ❌/✅ comparisons: Both wrong and right approaches
- Configuration examples: Complete working configs
- Detailed pitfalls: Not just "watch out for X" but how to avoid it

**How to verify**:
- Compare compacted vs original
- Check pattern code is complete (not just headers)
- Verify edge cases have explanations (not just mentions)
- Confirm ❌/✅ have both sides with code

### 4. Tier Classification Accuracy

**Question**: Was baseline comparison done correctly?

**Check Tier 3 removal (should be removed)**:
- Generic explanations matching baseline
- Basic examples in baseline
- Conceptual overviews without specifics
- Redundant introductions

**Check Tier 2 preservation (must be kept)**:
- Exact syntax beyond what's in baseline
- Specific edge cases not in baseline
- Complete patterns (baseline has placeholders)
- ❌/✅ comparisons (not in baseline)

**Example correct classification**:
```
Baseline: "Arrays store multiple values. Basic syntax: arr=(a b c)"
Original: "Arrays store multiple values. Basic syntax: arr=(a b c). Edge case: arr=() creates empty array, ${arr[@]} safely handles this..."
Compacted: "Edge case: arr=() creates empty array, ${arr[@]} safely handles this..." (removed match to baseline, kept edge case)
```

**Example incorrect classification** (REJECT):
```
Baseline: "There are 6 common patterns"
Original: "Pattern 1: Array from file lines\nmapfile -t lines < file.txt\n..."
Compacted: "Pattern 1: Array from file lines" (removed actual pattern code - TOO AGGRESSIVE)
```

### 5. Format Quality

**Check opening line**:
```markdown
# [Topic Name]

*See SKILL.md for [basic concepts]. This reference covers [unique value].*
```

- Format correct?
- Cross-reference makes sense?
- "basic concepts" = things in baseline?
- "unique value" = things NOT in baseline?

**Check for broken links**:
- Internal cross-references still valid?
- References to other files still work?
- No references to removed sections?

## Decision Framework

### ACCEPT if:
- ✅ All 5 criteria pass
- ✅ Compaction improved signal-to-noise
- ✅ User experience better (faster jump to value)
- ✅ No value lost

### REJECT if:
- ❌ Discovery flow broken (user can't find what they need)
- ❌ Promises don't match content (counts wrong, content missing)
- ❌ Value lost (Tier 1/2 content removed)
- ❌ Over-compaction (removed specific details, kept only generic)
- ❌ Under-compaction (kept obvious Tier 3 content)

### REJECT with GUIDANCE

Provide specific, actionable feedback:

**Good feedback**:
```
Issue: Quick Decision Tree says "6 patterns" but compacted file has only 4.
Pattern 5 (Remove duplicates) and Pattern 6 (Join array) were incorrectly removed.
These are complete pattern implementations, not generic explanations.

Guidance: Restore Pattern 5 and Pattern 6 to compacted file.
They are Tier 1 content (complete pattern libraries) not Tier 3.
```

**Bad feedback**:
```
Issue: File doesn't look right.
Guidance: Try again.
```

## Special Cases

### Checklists
- Expect <10% reduction
- Checklist items ARE the value
- Only remove generic intros

### Pattern Libraries
- Expect ~5% reduction
- Pattern code is the value
- Only remove redundant overviews

### Configuration Files
- Expect ~5% reduction
- Configs are unique
- Only remove generic explanations

### Technical Concepts
- Expect 20-50% reduction
- Lots of basic explanation to remove
- Keep edge cases and pitfalls
```

---

### Phase 4: Update /compact-reference Command

#### Simplify `.claude/commands/compact-reference.md`

```markdown
---
description: Compact reference file(s) using validation-driven workflow (single file or whole skill)
---

# Compact Reference File(s)

Orchestrate reference file compaction with workspace isolation and quality validation.

## Arguments

`$1` - Path to reference file OR skill directory

## Auto-Detection

```bash
if [[ "$1" =~ \.md$ ]] && [[ -f "$1" ]]; then
    mode="single-file"
    reference_file="$1"
elif [[ -d "$1/references" ]]; then
    mode="mass-compaction"
    skill_dir="$1"
else
    echo "Error: Argument must be .md file or skill directory with references/" >&2
    exit 1
fi
```

## Invocation

Simply invoke the reference-file-compactor skill with the provided argument:

**Single file mode**:
```
Use the reference-file-compactor skill to compact: ${reference_file}
```

**Mass compaction mode**:
```
Use the reference-file-compactor skill to compact all references in: ${skill_dir}
(Call scripts/compact-all.sh to orchestrate)
```

The skill handles:
- Workspace setup and cleanup
- Summary generation
- Baseline generation (Subagent A)
- Compaction
- SKILL.md update
- Quality validation (Subagent B)
- Auto-apply on ACCEPT or retry on REJECT
- Metrics reporting

## Examples

**Compact single file**:
```bash
/compact-reference bash-best-practices/references/01-bash-vs-zsh.md
```

**Compact all references in skill**:
```bash
/compact-reference bash-best-practices
```
```

---

### Phase 5: Update Documentation

#### Update `README.md`

Update sections:

1. **Overview**: Add "concrete baseline + validation" to key innovation
2. **Purpose**: Update workflow to show 7 steps including validation
3. **Usage**: Show both single file and mass compaction examples
4. **Key Features**: Add section on validation workflow
5. **Known Limitations**: Remove "Requires summaries.md" (now auto-generated)
6. **Integration**: Update to reflect `/compact-reference` auto-detection

#### Add Workflow Diagram

```
Single File Compaction:
┌────────────────────────────────────────────────────────────┐
│ /compact-reference path/to/reference.md                   │
└────────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Setup Workspace         │
         │  /tmp/compaction-*       │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Main Agent:             │
         │  - Read reference        │
         │  - Generate summary      │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Subagent A (fresh):     │
         │  - Read summary          │
         │  - Generate baseline     │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Main Agent:             │
         │  - Compare vs baseline   │
         │  - Compact reference     │
         │  - Update SKILL.md       │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Subagent B (fresh):     │
         │  - Validate quality      │
         │  - Return ACCEPT/REJECT  │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Decision:               │
         │  ACCEPT → Apply + cleanup│
         │  REJECT → Retry or report│
         └──────────────────────────┘

Mass Compaction:
┌────────────────────────────────────────────────────────────┐
│ /compact-reference bash-best-practices/                   │
└────────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  scripts/compact-all.sh  │
         │  - Discover all .md      │
         │  - Loop through files    │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  For each file:          │
         │  └→ Single file workflow │
         │     (workspace → compact │
         │      → validate → apply) │
         └──────────────────────────┘
                        ↓
         ┌──────────────────────────┐
         │  Aggregate Report:       │
         │  - Total files           │
         │  - Compacted count       │
         │  - Rejected count        │
         │  - Total reduction %     │
         └──────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: Scripts
- [ ] Create `scripts/setup-workspace.sh`
  - [ ] Create workspace structure
  - [ ] Copy source files
  - [ ] Save metadata (paths)
  - [ ] Test with single file
- [ ] Create `scripts/finalize-compaction.sh`
  - [ ] Parse --workspace and --apply arguments
  - [ ] Implement atomic apply with rollback
  - [ ] Implement guaranteed cleanup
  - [ ] Test apply success case
  - [ ] Test apply failure with rollback
  - [ ] Test cleanup-only case
- [ ] Create `scripts/compact-all.sh`
  - [ ] Discover .md files in references/
  - [ ] Loop and invoke single-file workflow
  - [ ] Collect metrics
  - [ ] Generate aggregate report
  - [ ] Test with small skill (2-3 files)

### Phase 2: SKILL.md Updates
- [ ] Add auto-detection section
- [ ] Add complete 7-step workflow
  - [ ] Step 1: Workspace setup
  - [ ] Step 2: Generate summary
  - [ ] Step 3: Subagent A (baseline)
  - [ ] Step 4: Compare and compact
  - [ ] Step 5: Update SKILL.md
  - [ ] Step 6: Subagent B (validation)
  - [ ] Step 7: Decision logic
- [ ] Add mass compaction section
- [ ] Add inline Subagent prompts
- [ ] Remove all summaries.md references

### Phase 3: Validation Reference
- [ ] Create `references/validation-criteria.md`
  - [ ] Discovery flow validation
  - [ ] Promises alignment
  - [ ] Value preservation
  - [ ] Tier classification accuracy
  - [ ] Format quality
  - [ ] Decision framework
  - [ ] Special cases (checklists, patterns, configs)

### Phase 4: Command Update
- [ ] Update `.claude/commands/compact-reference.md`
  - [ ] Add auto-detection logic
  - [ ] Simplify to skill invocation
  - [ ] Remove orchestration (now in SKILL.md)
  - [ ] Update examples

### Phase 5: Documentation
- [ ] Update `README.md`
  - [ ] Overview: Add validation
  - [ ] Workflow: Show 7 steps
  - [ ] Usage: Both modes
  - [ ] Key Features: Validation section
  - [ ] Remove "Requires summaries.md"
- [ ] Add workflow diagrams
- [ ] Update test results (after implementation)

### Phase 6: Testing
- [ ] Test single file compaction
  - [ ] Simple reference (high reduction expected)
  - [ ] Complex reference (medium reduction)
  - [ ] Checklist (low reduction expected)
- [ ] Test validation workflow
  - [ ] ACCEPT case (good compaction)
  - [ ] REJECT case (over-compaction)
  - [ ] Retry with guidance
  - [ ] Final REJECT after 2 attempts
- [ ] Test mass compaction
  - [ ] Process 3-5 files
  - [ ] Verify all workspaces cleaned up
  - [ ] Check aggregate report
- [ ] Test error handling
  - [ ] Invalid input
  - [ ] Missing files
  - [ ] Workspace creation failure
  - [ ] Apply failure with rollback

---

## Success Criteria

1. ✅ Single file compaction works end-to-end
2. ✅ Mass compaction processes all files automatically
3. ✅ Validation catches over-compaction (Tier 2 removal)
4. ✅ Validation catches under-compaction (Tier 3 kept)
5. ✅ Retry loop improves results
6. ✅ Workspace always cleaned up (success or failure)
7. ✅ No context pollution (no summaries.md)
8. ✅ Atomic apply (all-or-nothing, rollback on error)
9. ✅ 5-50% reduction with 100% value retention
10. ✅ User sees only validated, high-quality results

---

## Migration from Current Implementation

### What to Keep
- `references/compaction-rules.md` (Tier system)
- Existing test results (validation)
- Core compaction logic principles

### What to Change
- SKILL.md: Add validation workflow
- Remove summaries.md dependency
- Add scripts for workspace management

### What to Add
- `references/validation-criteria.md`
- `scripts/` directory (3 new scripts)
- Subagent B validation step
- Retry logic with feedback
- Mass compaction support

---

## Notes for Coding Agent

### Context Isolation
- Subagent A generates baseline WITHOUT seeing actual file
- Subagent B validates WITHOUT seeing compaction process
- Fresh context is critical for unbiased evaluation

### Error Handling
- Scripts must handle errors gracefully
- Always cleanup workspace (even on error)
- Rollback partial applies
- Report clear error messages

### Token Efficiency
- Use scripts for deterministic operations
- Use subagents only for analysis/generation
- Keep prompts focused and specific

### Quality Focus
- Validation is not optional
- Two retry attempts (then give up)
- Auto-apply only on ACCEPT
- Report detailed metrics

### Debugging
- Workspaces in /tmp for inspection
- Save all artifacts (summary, baseline, validation report)
- Clear logging from scripts
- Meaningful error messages

---

## Timeline Estimate

- Phase 1 (Scripts): 2-3 hours
- Phase 2 (SKILL.md): 2 hours
- Phase 3 (Validation ref): 1 hour
- Phase 4 (Command): 30 minutes
- Phase 5 (Docs): 1 hour
- Phase 6 (Testing): 2-3 hours

**Total**: 8-10 hours

---

## Post-Implementation

After implementation is complete:

1. Test on bash-best-practices (20 files)
2. Collect real metrics
3. Update README.md with results
4. Package skill for distribution
5. Write blog post/documentation
6. Consider: Apply same pattern to other skill optimization tasks
