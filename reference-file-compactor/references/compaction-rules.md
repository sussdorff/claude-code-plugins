# Reference File Compaction Rules

## Tier Classification System

### Tier 3: REMOVE (Redundant with Summary)

Content that can be generated from the summary alone. Remove this to reduce noise.

**Characteristics:**
- Generic explanations of concepts mentioned in summary
- Basic introductions explaining "what is X"
- Simple examples demonstrating concepts listed in summary
- Redundant summary sections duplicating the summary
- Conceptual overviews without specific syntax

**Examples:**
```markdown
❌ REMOVE:
## What is Strict Mode?
Strict mode makes Bash fail fast and loud when errors occur...

## Creating Arrays
arr=("first" "second" "third")
echo "${arr[0]}"  # first
```

**Reasoning**: If the summary says "covers strict mode and arrays," I can generate these basic explanations myself.

---

### Tier 2: KEEP (Detailed Technical Content)

Specific technical content that cannot be generated from summary alone.

**Characteristics:**
- Exact command syntax with options/flags
- Specific code patterns with precise syntax
- Edge cases and exceptions not mentioned in summary
- Multiple solution approaches (❌/✅ comparisons)
- Detailed configuration examples
- Nuanced explanations of behavior

**Examples:**
```markdown
✅ KEEP:
# Safe patterns with set -u
if [[ -n "${var:-}" ]]; then  # Note the :- syntax
    echo "var is set to: $var"
fi

# Array slicing (note space before -)
echo "${arr[@]: -2}"  # Last 2 elements
```

**Reasoning**: Summary may say "covers safe patterns" but doesn't show the exact `${var:-}` syntax or the space-before-minus detail.

---

### Tier 1: KEEP (Unique Value)

Content that is impossible to generate without reading the actual file.

**Characteristics:**
- Complete pattern libraries (collections of reusable code)
- Comprehensive checklists (100+ specific items)
- Production-ready scripts/configurations
- Step-by-step workflows with specific commands
- Anti-pattern examples with full code
- Real-world examples with context

**Examples:**
```markdown
✅ KEEP:
## 6 Array Pattern Library

### Pattern 1: Array from File Lines
mapfile -t lines < file.txt

### Pattern 2: Array from Command Output
mapfile -t files < <(find . -name "*.txt")

### Pattern 3: Check if Array Contains Value
found=false
for item in "${array[@]}"; do
    if [[ "$item" == "$search" ]]; then
        found=true
        break
    fi
done
```

**Reasoning**: Summary says "6 patterns" but doesn't show the working code. This is irreplaceable.

---

## Decision Framework

Ask these questions for each section:

1. **Can I write this from the summary alone?**
   - Yes → Tier 3 (remove)
   - No → Continue to Q2

2. **Does this show exact syntax or specific details?**
   - Yes → Tier 2 (keep)
   - No → Continue to Q3

3. **Is this a complete pattern/checklist/workflow?**
   - Yes → Tier 1 (keep)
   - No → Review again, likely Tier 3

---

## Common Removal Patterns

### Pattern 1: Redundant Introductions

**Summary says**: "Understanding `set -euo pipefail` and variations"

**Remove**:
```markdown
# Bash Strict Mode

Understanding `set -euo pipefail` and error-resistant scripting.

## What is Strict Mode?

Strict mode makes Bash fail fast and loud when errors occur...
```

**Replace with**:
```markdown
# Bash Strict Mode

*See SKILL.md for basic pattern and purpose. This reference covers edge cases, pitfalls, and variations.*
```

---

### Pattern 2: Basic Examples in Summary

**Summary says**: "Array operations, iteration, pitfalls"

**Remove**:
```markdown
## Creating Arrays
arr=()
arr=("first" "second" "third")

## Accessing Elements
echo "${arr[0]}"  # First element
echo "${arr[@]}"  # All elements
```

**Keep**:
```markdown
## Array Slicing
echo "${arr[@]:1:3}"  # From index 1, take 3 elements
echo "${arr[@]: -2}"  # Last 2 elements (note the space before -)
```

---

### Pattern 3: Summary Sections

**Remove all**: Final summary sections that duplicate the summary or SKILL.md

```markdown
❌ REMOVE:
## Summary

**Key patterns**:
- Create: arr=("one" "two")
- Access: "${arr[@]}"
- Iterate: for item in "${arr[@]}"
```

**Reasoning**: This is already in SKILL.md and the file summary.

---

## Special Cases

### Checklists (like code-review-checklist.md)

**Keep**: Nearly 100% of content
- The checklist IS the value
- Only remove generic intro sentences and redundant summaries
- Expect <10% reduction

### Pattern Libraries (like common-patterns.md)

**Keep**: 95%+ of content
- Pattern code is the value
- Only remove overview/intro if redundant
- Expect ~5% reduction

### Configuration Files (like ci-cd-integration.md)

**Keep**: 95%+ of content
- Configurations are unique
- Only remove generic explanations
- Expect ~5% reduction

### Technical Concept Files (like strict-mode.md, arrays.md)

**Remove**: Basic explanations, simple examples
**Keep**: Edge cases, pitfalls, advanced patterns
- Expect 20-50% reduction

---

## Output Format

Compacted files must start with:

```markdown
# [Topic Name]

*See SKILL.md for [basic concepts from summary]. This reference covers [unique value from summary].*
```

Examples:

```markdown
# Bash Strict Mode

*See SKILL.md for basic pattern (`set -euo pipefail`) and purpose. This reference covers edge cases, pitfalls, and variations.*
```

```markdown
# Arrays in Bash

*See SKILL.md for basic operations (0-based indexing, `"${arr[@]}"`, iteration). This reference covers slicing, associative arrays, patterns, and pitfalls.*
```

```markdown
# Bash Code Review Checklist

*See SKILL.md for overview of critical/important/style categories. This is the complete production checklist.*
```

---

## Validation Checklist

Before marking compaction complete, verify:

- [ ] Opening line follows format and cross-references SKILL.md
- [ ] All Tier 1/2 content preserved (patterns, pitfalls, examples, configs)
- [ ] All Tier 3 content removed (generic explanations, basic examples, summaries)
- [ ] All ❌/✅ comparisons intact
- [ ] All code examples complete and copy-paste ready
- [ ] All configuration files/templates intact
- [ ] All real-world examples present
- [ ] All anti-patterns documented
- [ ] No broken cross-references to removed sections
