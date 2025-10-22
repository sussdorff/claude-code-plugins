# Validation Criteria for Subagent B

## Purpose

Guide Subagent B in evaluating compaction quality holistically. This document provides a comprehensive framework for determining whether to ACCEPT or REJECT a compaction.

## Evaluation Framework

### 1. Discovery Flow Validation

**Question**: Would a user successfully use SKILL.md → reference flow?

**Check**:
- Quick Decision Tree entry describes a clear, specific scenario
- Scenario matches "When to read" from summary
- User can easily decide if they need this reference
- Reference delivers on the promise made in Quick Decision Tree

**Example PASS**:
```
Quick Decision Tree: "Array indexing issues? → 04-arrays.md - Slicing, associative arrays (Bash 4+), 6 patterns, 5 pitfalls"

Compacted file contains:
- Array slicing section with complete examples ✓
- Associative arrays section with Bash 4+ note ✓
- 6 complete patterns with code ✓
- 5 detailed pitfalls with explanations ✓
```

**Example FAIL**:
```
Quick Decision Tree: "Array indexing issues? → 04-arrays.md - 6 patterns"

Compacted file contains:
- Pattern 1: Array from file lines (header only, no code) ❌
- Pattern 2: Splitting strings (header only, no code) ❌
- ...

Problem: Promises "6 patterns" but delivers only headers without actual pattern code
```

### 2. Promises Alignment

**Question**: Does compacted file match Quick Decision Tree claims exactly?

**Check counts**:
- "6 patterns" → Exactly 6 complete patterns present with full code?
- "4 pitfalls" → Exactly 4 detailed pitfalls present with explanations?
- "3 variations" → Exactly 3 variations documented with examples?

**Check content types**:
- "Edge cases" → Specific edge cases with examples (not just generic mentions)?
- "❌/✅ comparisons" → Actual side-by-side code comparisons?
- "Production examples" → Complete, working, real-world examples?
- "Configuration templates" → Full, copy-paste ready configs?

**Red flags** (immediate REJECT):
- Counts don't match (says "6 patterns" but has 4)
- Promised content missing (says "edge cases" but has none)
- Only placeholders/headers without details
- Generic descriptions instead of specific content

**Example PASS**:
```
Quick Decision Tree: "Need strict error handling? → 02-strict-mode.md - set -euo pipefail deep dive, 4 edge cases, exit trap patterns"

Compacted file has:
- set -euo pipefail section with detailed explanation ✓
- 4 specific edge cases with code examples ✓
- Exit trap patterns section with multiple examples ✓
```

**Example FAIL**:
```
Quick Decision Tree: "ShellCheck warnings? → 09-shellcheck-integration.md - 12 most common fixes with before/after"

Compacted file has:
- 8 fixes (not 12) ❌
- Some fixes missing "before" code ❌
- Generic descriptions instead of actual code ❌
```

### 3. Value Preservation

**Question**: Is all Tier 1/2 content intact and complete?

**Tier 1 checks** (Must be 100% complete):
- Pattern libraries: All patterns with full, working code
- Checklists: All items present with descriptions
- Production scripts: Complete scripts that actually run
- Real-world examples: Full context + complete code
- Configuration templates: Full, copy-paste ready configs

**Tier 2 checks** (Must be detailed and specific):
- Exact syntax: Beyond basic examples, including flags and options
- Edge cases: Specific scenarios with explanations of why they matter
- ❌/✅ comparisons: Both wrong and right approaches with actual code
- Configuration examples: Complete working configs with comments
- Detailed pitfalls: Not just "watch out for X" but how/why/solution

**How to verify**:
1. Compare compacted file side-by-side with original
2. For each Tier 1/2 item in original:
   - Is it present in compacted? (Not just mentioned, but fully present)
   - Is it complete? (Not truncated or summarized)
   - Is the code intact? (Not replaced with "..." or comments)
3. Check pattern counts match
4. Verify all ❌/✅ comparisons have both sides

**Example correct preservation**:
```
Original:
Pattern 3: Remove duplicates while preserving order
```bash
# Using associative array (Bash 4+)
declare -A seen
result=()
for item in "${arr[@]}"; do
    if [[ ! ${seen[$item]} ]]; then
        seen[$item]=1
        result+=("$item")
    fi
done
```

Compacted:
[Same exact code block] ✓
```

**Example incorrect (REJECT)**:
```
Original:
Pattern 3: Remove duplicates while preserving order
[Full code block as above]

Compacted:
Pattern 3: Remove duplicates while preserving order
Use associative array to track seen items. ❌

Problem: Replaced complete pattern code (Tier 1) with generic description (Tier 3)
```

### 4. Tier Classification Accuracy

**Question**: Was baseline comparison done correctly?

#### Check Tier 3 removal (should be removed)

**What should be removed**:
- Generic explanations matching baseline
- Basic examples identical to what's in baseline
- Conceptual overviews without specifics
- Redundant introductions
- Summary sections that duplicate the summary file

**Example correct removal**:
```
Baseline: "Arrays in Bash store multiple values. Basic syntax: arr=(a b c). Access with ${arr[0]}."

Original: "Arrays in Bash store multiple values. Basic syntax: arr=(a b c). Access with ${arr[0]}. Edge case: Empty arrays arr=() are safe with ${arr[@]} but not ${arr[*]} in unquoted contexts..."

Compacted: "Edge case: Empty arrays arr=() are safe with ${arr[@]} but not ${arr[*]} in unquoted contexts..." ✓

Reasoning: Removed content matching baseline exactly (Tier 3), kept edge case not in baseline (Tier 2)
```

#### Check Tier 2 preservation (must be kept)

**What must be preserved**:
- Exact syntax beyond what's in baseline
- Specific edge cases not in baseline
- Complete patterns (baseline has placeholders only)
- ❌/✅ comparisons (not in baseline)
- Detailed configurations (baseline has generic mentions)

**Example incorrect classification (REJECT)**:
```
Baseline: "There are 6 common array patterns for file handling, string processing, and data manipulation."

Original:
Pattern 1: Array from file lines
```bash
mapfile -t lines < file.txt
# Preserves empty lines, handles large files efficiently
```

Compacted:
Pattern 1: Array from file lines ❌ (removed the actual code)

Problem: Baseline mentions patterns exist, but actual pattern code is Tier 1 (unique value).
Compaction incorrectly treated pattern code as Tier 3.
```

#### Baseline comparison test

For any removed content, ask:
1. Is this exact content in the baseline? → OK to remove (Tier 3)
2. Is this content beyond the baseline? → MUST keep (Tier 1/2)

### 5. Format Quality

#### Check opening line format

**Required format**:
```markdown
# [Topic Name]

*See SKILL.md for [basic concepts]. This reference covers [unique value].*
```

**Validation**:
- Format exactly matches template?
- [basic concepts] = things that WERE in baseline (removed content)?
- [unique value] = things that were NOT in baseline (kept content)?
- Cross-reference makes sense?

**Example PASS**:
```
# Bash Arrays

*See SKILL.md for array basics and syntax. This reference covers slicing, associative arrays (Bash 4+), 6 patterns, and 5 pitfalls.*

✓ Format correct
✓ "array basics and syntax" were in baseline (removed)
✓ "slicing, associative arrays, 6 patterns, 5 pitfalls" are NOT in baseline (kept)
```

**Example FAIL**:
```
# Bash Arrays

*This reference covers arrays in Bash.*

❌ Wrong format (doesn't reference SKILL.md)
❌ Doesn't distinguish basic vs unique content
```

#### Check for broken links

- Internal cross-references still valid?
- References to other files still work?
- No references to removed sections?
- Section anchors still exist?

## Decision Framework

### ACCEPT if

**All 5 criteria pass**:
- ✅ Discovery flow works (user can find and use content)
- ✅ Promises align (counts and content match Quick Decision Tree)
- ✅ Value preserved (all Tier 1/2 content intact and complete)
- ✅ Tier classification accurate (baseline comparison correct)
- ✅ Format quality good (opening line correct, no broken links)

**AND**:
- ✅ Compaction improved signal-to-noise ratio
- ✅ User experience is better (faster jump to value)
- ✅ No value was lost

### REJECT if

**Any critical issue found**:
- ❌ Discovery flow broken (user can't find what they need)
- ❌ Promises don't match content (counts wrong, content missing)
- ❌ Value lost (Tier 1/2 content removed or incomplete)
- ❌ Over-compaction (removed specific details, kept only generic)
- ❌ Under-compaction (kept obvious Tier 3 content)
- ❌ Format issues (wrong opening line, broken links)

### REJECT with specific GUIDANCE

When rejecting, provide actionable feedback:

**Good feedback** (specific, actionable):
```
VERDICT: REJECT

REASONING:
The compaction removed valuable pattern code while keeping generic explanations.
The Quick Decision Tree promises "6 patterns" but the compacted file has incomplete code.

ISSUES:
- Pattern 5 (Remove duplicates): Code block removed, only header remains
- Pattern 6 (Join array): Code block removed, only header remains
- Quick Decision Tree says "6 patterns" but only 4 have complete code
- Kept generic intro "Arrays are useful data structures" (matches baseline exactly)

GUIDANCE:
1. Restore Pattern 5 and Pattern 6 complete code blocks from original file
2. These are Tier 1 content (complete pattern libraries), not Tier 3
3. Remove the intro paragraph "Arrays are useful data structures..." - it matches baseline exactly
4. Verify all 6 patterns have complete, working code blocks before resubmitting
```

**Bad feedback** (vague, not actionable):
```
VERDICT: REJECT

REASONING:
File doesn't look right. Some content seems missing.

ISSUES:
- Too aggressive
- Not enough detail

GUIDANCE:
Try to keep more content and be more careful.
```

## Special Cases

### Checklists

**Characteristics**:
- Checklist items ARE the unique value
- Very little generic content to remove
- Expect <10% reduction

**Validation focus**:
- All checklist items present? (100% of items)
- Item descriptions intact? (not truncated)
- Only generic intros removed?

**Example PASS**:
```
Original: 50 checklist items + 200-word intro
Compacted: 50 checklist items + 50-word intro
Reduction: ~8%
All items present: ✓
```

**Red flag**: >15% reduction likely means checklist items were removed

### Pattern Libraries

**Characteristics**:
- Pattern code IS the unique value
- Expect ~5% reduction
- Almost everything should be kept

**Validation focus**:
- All patterns present with complete code?
- Pattern counts match promises?
- Only redundant overviews removed?

**Example PASS**:
```
Original: 8 patterns with code + overview section
Compacted: 8 patterns with code (overview removed)
Reduction: ~5%
All patterns complete: ✓
```

**Red flag**: Missing patterns or incomplete code blocks

### Configuration Files

**Characteristics**:
- Configurations ARE the unique value
- Expect ~5% reduction
- Often will be REJECT as already optimal

**Validation focus**:
- All config examples present and complete?
- Config files copy-paste ready?
- Only generic explanations removed?

**Example ACCEPT (minimal changes)**:
```
Original: 5 complete config files + explanations
Compacted: 5 complete config files + minimal explanations
Reduction: ~5%
```

**Example REJECT (already optimal)**:
```
Original: 3 complete config files, no fluff
Compacted: Same 3 files with minor edits
Reduction: ~2%

Verdict: REJECT - file is already optimally structured
```

### Technical Concept Files

**Characteristics**:
- Usually have lots of basic explanation
- Expect 20-50% reduction
- Keep edge cases, pitfalls, advanced patterns

**Validation focus**:
- Edge cases preserved?
- Pitfalls detailed (not just mentioned)?
- Advanced patterns intact?
- Basic explanations removed?

**Example PASS**:
```
Original: 500 lines (200 basics, 300 edge cases/pitfalls)
Compacted: 320 lines (20 basics, 300 edge cases/pitfalls)
Reduction: 36%
All edge cases present: ✓
```

**Red flag**: If reduction >50%, check if edge cases were lost

## Output Format Requirements

Your validation report must follow this structure:

```markdown
VERDICT: [ACCEPT or REJECT]

REASONING:
[2-3 paragraphs explaining your decision]
- What criteria passed/failed
- What the compaction did well
- What issues were found (if any)

ISSUES (if REJECT):
- Issue 1: [Specific problem with file/line reference if possible]
- Issue 2: [Specific problem with evidence]
- Issue 3: [etc.]

GUIDANCE (if REJECT):
[Step-by-step instructions for fixing issues]
1. [Specific action item]
2. [Specific action item]
3. [Verification step]

[If ACCEPT, omit ISSUES and GUIDANCE sections]
```

## Validation Checklist

Use this checklist for every validation:

- [ ] **Discovery flow**: Quick Decision Tree entry is clear and specific
- [ ] **Scenario match**: Entry matches "When to read" from summary
- [ ] **Promise counts**: All counts in entry match compacted content
- [ ] **Promise content**: All promised content types present
- [ ] **Tier 1 complete**: All patterns/checklists/configs 100% complete
- [ ] **Tier 2 detailed**: All edge cases/pitfalls/comparisons detailed
- [ ] **Tier 3 removed**: No generic content matching baseline remains
- [ ] **Tier 2 preserved**: No specific content beyond baseline removed
- [ ] **Opening line**: Format exactly matches template
- [ ] **Cross-reference**: [basic concepts] makes sense
- [ ] **Unique value**: [unique value] accurately describes kept content
- [ ] **No broken links**: All internal references valid
- [ ] **Appropriate reduction**: Matches expected % for file type

## Common Mistakes to Catch

### Over-compaction (most common issue)

**Symptoms**:
- Pattern headers without code
- Pitfall mentions without details
- ❌/✅ comparisons with only one side
- Counts don't match (promised 6, delivered 4)

**Response**: REJECT with specific patterns/pitfalls to restore

### Under-compaction

**Symptoms**:
- Generic explanations matching baseline kept
- Redundant intros still present
- Content you could write from summary alone
- <5% reduction on technical concept file

**Response**: REJECT with specific Tier 3 content to remove

### Promise misalignment

**Symptoms**:
- Quick Decision Tree says "6 patterns" but file has 5
- Entry mentions "edge cases" but none in file
- Entry promises "❌/✅ comparisons" but file has plain examples

**Response**: REJECT with count correction or content addition needed

### Format issues

**Symptoms**:
- Opening line missing or wrong format
- No reference to SKILL.md
- Broken cross-references
- Section links don't work

**Response**: REJECT with specific format correction needed

## Final Note

Your role is quality assurance. Be thorough but fair:

- **ACCEPT** when value is preserved and format is correct
- **REJECT** when issues compromise quality or user experience
- **Provide specific guidance** to enable successful retry

The goal is validated, high-quality compactions that users can trust.
