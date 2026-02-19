# Skill Creation Guide

Workflow and best practices for building Claude Code skills from scratch.

## Creation Workflow

### 1. Gather Requirements

Ask about:
- **Purpose**: What problem does this solve? What does it replace?
- **Trigger scenarios**: When should Claude activate this? (3-5 specific phrases)
- **Scope**: What should it NOT do? What's the boundary?
- **Output**: What does success look like? (format, examples)
- **Content type**: Reference knowledge or task instructions?

### 2. Scaffold Structure

Run `scripts/init-skill.sh <skill-name>` to create the directory skeleton. This creates SKILL.md with a template, plus empty references/ and scripts/ directories.

### 3. Write Frontmatter

Apply the description format from `references/skill-specification.md`:
- Start with a verb phrase describing the function
- Include 3+ trigger phrases users would actually say
- Add negative triggers ("Do NOT use for...")
- Set invocation control (`disable-model-invocation`, `user-invocable`) based on content type
- Add `context: fork` if the skill runs a standalone task

### 4. Write Body

Structure the body following section order:
1. **Title + one-line overview**
2. **When to Use** (or mode routing table for multi-mode skills)
3. **Core workflow / instructions** (the main content)
4. **Do NOT** (forbidden list)
5. **Resources** (pointers to references/, scripts/)

### 5. Extract to References

Apply the 500-line rule: if SKILL.md exceeds 500 lines, extract detail into references/:
- Checklists and scoring criteria -> `references/checklist.md`
- Detailed examples -> `references/examples.md`
- API docs or schemas -> `references/api-reference.md`
- Patterns and templates -> `references/patterns.md`

Keep SKILL.md as the routing layer: overview, workflow skeleton, pointers.

### 6. Validate

Run skill-forge **Review** mode on the new skill. Target grade B+ or better.

Check:
- Description triggers correctly (ask Claude "what skill would you use for X?")
- Negative triggers work (Claude does NOT activate for excluded scenarios)
- Token budget within limits (total < 10000 tokens)
- Progressive disclosure: SKILL.md lean, detail in references

### 7. Test Invocation

- **Auto-invocation**: Ask Claude something matching the description -- does it activate?
- **Manual invocation**: Run `/skill-name` with arguments -- does it behave correctly?
- **Negative test**: Ask something the skill should NOT match -- does it stay quiet?

## Writing Best Practices

### Be Concise and Imperative

```
# Bad
You should consider reading the configuration file before making any changes
to ensure that you have the correct settings.

# Good
Read configuration before making changes.
```

### Specify Degrees of Freedom

Tell Claude where it has latitude and where it doesn't:
```
## Fixed (do not change)
- Output format: always JSON
- Error handling: fail fast, no retries

## Flexible (use judgment)
- File discovery strategy
- Order of operations within each step
```

### Progressive Disclosure Heuristics

Move content to references/ when it:
- Contains 5+ examples of the same pattern
- Is a lookup table or matrix
- Is only needed for one specific mode
- Exceeds 50 lines of contiguous detail

Keep in SKILL.md when it:
- Is needed on every invocation
- Is the routing/decision logic
- Is under 20 lines

### Forbidden Lists

Every skill should have a "Do NOT" section. Common items:
- "Do NOT modify files without asking" (for review/analysis skills)
- "Do NOT assume X -- ask" (for ambiguous situations)
- "Do NOT skip validation" (for safety-critical workflows)

### WHY Statements

Add rationale to non-obvious rules:
```
# Without WHY
Format output as JSON.

# With WHY
Format output as JSON -- downstream scripts parse it with jq for CI integration.
```

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Description too vague | Add specific trigger phrases and negative triggers |
| Monolithic SKILL.md | Extract detail to references/, keep routing in SKILL.md |
| Missing forbidden list | Add "Do NOT" section with 3-5 common traps |
| No output format | Define templates or examples for expected output |
| Over-engineering | Start with minimum viable skill, iterate |
| Rigid step lists | Use decision heuristics over numbered procedures |
| Context overload | Split into REQUIRED (always load) and OPTIONAL (on demand) |
| No negative testing | Verify skill does NOT trigger for out-of-scope requests |

## Evaluation-Driven Development

Use skill-forge Review mode as a quality gate:

1. Write initial skill
2. Run skill-forge Review -> get grade and issues
3. Fix top 3 issues
4. Re-run Review -> target B+ or better
5. Ship

This feedback loop catches description quality, token budget, and structure issues before the skill enters production.
