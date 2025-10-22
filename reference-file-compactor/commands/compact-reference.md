---
description: Compact reference file(s) using validation-driven workflow (single file or whole skill)
---

# Compact Reference File(s)

Orchestrate reference file compaction with workspace isolation and quality validation.

## Arguments

`$1` - Path to reference file OR skill directory

## Auto-Detection

The skill automatically detects the mode based on the input:

**Single file mode**:
- Input ends with `.md`
- File exists at path
- Processes one reference file through validation workflow

**Mass compaction mode**:
- Input is a directory
- Directory contains `references/` subdirectory
- Processes all `*.md` files in `references/` (top-level only)

## Implementation

Simply invoke the reference-file-compactor skill with the provided argument:

```
Use the reference-file-compactor skill to compact: $1
```

The skill handles the complete workflow:
1. **Workspace setup**: Creates isolated `/tmp/compaction-*` workspace
2. **Summary generation**: Analyzes reference content
3. **Baseline generation**: Subagent A creates "removable content" baseline
4. **Compaction**: Compares actual vs baseline, removes Tier 3 content
5. **SKILL.md update**: Generates Quick Decision Tree entry
6. **Quality validation**: Subagent B evaluates with fresh context
7. **Decision logic**: Auto-apply if ACCEPT, retry if REJECT, report if optimal

## Examples

### Compact single file

```bash
/compact-reference bash-best-practices/references/01-bash-vs-zsh.md
```

**Expected output**:
```
✓ Compaction accepted and applied

**File**: 01-bash-vs-zsh.md
**Metrics**:
- Original: 584 lines
- Compacted: 375 lines
- Reduction: 209 lines (35.8%)
- Verdict: ACCEPT (first attempt)
```

### Compact all references in skill

```bash
/compact-reference bash-best-practices
```

**Expected output**:
```
Found 20 reference files to compact
========================================

[1/20] Processing: 01-bash-vs-zsh.md
  → ACCEPT: 584 → 375 lines (-35.8%)
  ✓ Applied

[2/20] Processing: 02-strict-mode.md
  → REJECT (first attempt): Over-compaction
  → Retry with guidance
  → ACCEPT: 472 → 279 lines (-40.9%)
  ✓ Applied

...

========================================
Mass Compaction Summary
========================================
Total files: 20
Successfully compacted: 18
Rejected (optimal): 2
Total reduction: 1,234 lines (32.1%)
```

## Notes

- **Workspace isolation**: All work happens in `/tmp/`, no context pollution
- **Validation-driven**: Changes only applied after quality validation passes
- **Self-correcting**: Up to 2 retry attempts with specific guidance
- **Atomic changes**: All-or-nothing apply with rollback on error
- **Always cleaned up**: Workspace removed even on failure

## Error Handling

The skill handles common errors gracefully:

- **File not found**: Clear error message with path
- **No references/ directory**: Informs user of requirement for mass mode
- **Validation failure**: Reports after max retries, no changes applied
- **Apply failure**: Rolls back partial changes, reports error

## Related Resources

- **SKILL.md**: Complete workflow documentation
- **references/compaction-rules.md**: Tier classification system
- **references/validation-criteria.md**: Validation framework
- **scripts/**: Workspace management automation
