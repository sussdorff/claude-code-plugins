# Refactoring Patterns

Common skill improvement patterns with before/after examples. Reference during Refactor mode.

## 1. Vague Description to Specific Triggers

**Before:**
```
description: Helps with code tasks and development workflows.
```

**After:**
```
description: >
  Analyze Python code for performance bottlenecks and memory leaks.
  Use when profiling code, investigating slow functions, or optimizing
  hot paths. Triggers on "profile", "slow code", "memory leak", "optimize performance".
  Do NOT use for general code review (use code-reviewer instead).
```

**Why:** Auto-delegation matches on keywords. Vague descriptions cause missed triggers or false positives.

## 2. Monolithic SKILL.md to Progressive Disclosure

**Before:** 800-line SKILL.md containing everything -- checklists, examples, reference tables, scripts inline.

**After:**
```
skill-name/
  SKILL.md              (200 lines - routing, overview, key workflow)
  references/
    detailed-guide.md   (examples, edge cases)
    checklist.md        (scoring criteria)
  scripts/
    automate.sh         (repetitive tasks)
```

**Why:** Claude loads SKILL.md on every invocation. Keep it lean so context window stays focused. References load on demand.

## 3. Passive Voice to Imperative Style

**Before:**
```
The user should be asked about their preferences before the configuration
is updated. It is recommended that validation should be performed.
```

**After:**
```
Ask about preferences before updating configuration. Validate all inputs.
```

**Why:** Imperative is shorter, clearer, and matches how instructions are naturally processed. Saves tokens.

## 4. Rigid Procedures to Decision Heuristics

**Before:**
```
Step 1: Check if file exists
Step 2: Read the file
Step 3: Parse the YAML
Step 4: Validate each field
Step 5: Report errors
Step 6: ...
```

**After:**
```
Validation rules:
- Required fields: name, description (fail fast if missing)
- name: kebab-case, 2-50 chars
- description: 150-300 chars, contains trigger phrases
- If field invalid -> report with expected format
```

**Why:** Decision heuristics handle edge cases better than rigid step lists. Claude can reason about rules; it merely follows steps.

## 5. Missing Forbidden Lists

**Before:** Skill describes what to do but not what to avoid.

**After:** Add explicit "Do NOT" section:
```
## Do NOT
- Generate mock data without user approval
- Modify files outside the target directory
- Skip validation even for "simple" cases
- Assume defaults when config is ambiguous -- ask
```

**Why:** Forbidden lists prevent common convergence traps where Claude optimizes for speed over correctness.

## 6. Context Overload to Hierarchical Loading

**Before:** All context loaded unconditionally:
```
Read config.yaml
Read schema.json
Read examples/basic.yaml
Read examples/advanced.yaml
Read migration-guide.md
```

**After:**
```
## Required Context (always load)
- config.yaml
- schema.json

## Optional Context (load when needed)
- examples/ -- load when user asks for examples
- migration-guide.md -- load only for migration tasks
```

**Why:** Unnecessary context wastes tokens and can confuse focus. Load what you need, reference what you might need.
