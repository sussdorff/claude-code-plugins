# Prompt Techniques

Condensed reference of techniques applicable to skill writing. Use when suggesting improvements.

## 1. Goldilocks Principle

Optimal prompt length: ~500 tokens for the core instruction. Seven principles:

| Principle | Description |
|-----------|------------|
| Name Patterns | Use specific names that signal intent (e.g., "code-reviewer" not "helper") |
| Categorical Examples | 3-5 examples spanning the category, not exhaustive lists |
| Decision Heuristics | Rules and formulas over step-by-step procedures |
| Calibrate Through Contrast | Show what IS and IS NOT (positive + negative examples) |
| Action Directives | Direct commands: "Score each dimension", "Output as table" |
| Forbidden Lists | Explicit "Do NOT" items to prevent convergence traps |
| Second-Order Warning | "Do not sacrifice X for Y" to prevent over-optimization |

## 2. Six-Layer Specification

Structure skill instructions across six layers:

1. **FORMAT**: How output should look (table, checklist, prose)
2. **TONE**: Voice and style (imperative, technical, concise)
3. **CONSTRAINTS**: Boundaries and limits (token budget, scope)
4. **SUCCESS LOOKS LIKE**: Concrete success criteria
5. **EDGE CASES**: What to do in ambiguous situations
6. **REFERENCE EXAMPLE**: One complete input/output example

Not every skill needs all six layers. Apply where ambiguity exists.

## 3. WHY Statements

Adding "why" narrows solution space by ~80%.

**Without WHY:**
```
Format output as JSON.
```

**With WHY:**
```
Format output as JSON -- downstream scripts parse it with jq for CI integration.
```

The model now knows to prioritize machine-readability over human aesthetics.

## 4. Hierarchical Context

Split context into loading tiers:

- **REQUIRED**: Always loaded, essential for any invocation
- **OPTIONAL**: Loaded on demand based on user intent or mode

Apply to both skill structure (SKILL.md vs references/) and within-skill sections.

## 5. Reverse Prompting

For complex refactoring suggestions: ask the model to write the optimal prompt for a task first, then execute it. Useful when rewriting skill descriptions or restructuring content.

Pattern:
```
1. "What would the ideal SKILL.md look like for a skill that does X?"
2. Review the generated structure
3. Apply to actual rewrite
```

## Applying Techniques to Skill Review

When reviewing or refactoring skills, check:
- Does the description follow Goldilocks naming? (Principle 1)
- Are instructions using decision heuristics over rigid steps? (Principle 3)
- Is there a forbidden list? (Principle 6)
- Are WHY statements present for non-obvious rules?
- Is context hierarchically organized?
