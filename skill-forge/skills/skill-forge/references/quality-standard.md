# Skill Quality Standard

## Trigger Context

Apply when creating, reviewing, or improving Claude Code skills (SKILL.md files).

## Frontmatter

```yaml
---
name: kebab-case-name          # e.g., code-reviewer, not CodeReviewer
description: >-
  [Primary function]. Use when [specific triggers].
  [What it does]. [Target audience].
# 150-300 chars, action-oriented, specific trigger phrases
---
```

**Rules:**
- Name after the job, not the team ("code-reviewer" not "dev-team-helper")
- Description first sentence = primary function as verb phrase
- Include 2-3 concrete trigger phrases users would actually say
- First paragraph after frontmatter is critical for router matching

**Anti-pattern:** `"A helpful skill for various development tasks"` -- too vague, no triggers.

## SKILL.md Structure

Follow this section order strictly:

```
1. Title (# Name)
2. Overview (1-2 sentences: what + why)
3. When to Use / Triggers
4. Main Content (procedures, rules, templates)
5. Resources / References (links to references/)
6. Limitations / Out of Scope
```

**Token budget:** SKILL.md under 500 lines (~2000 tokens for core instructions).
Move detailed reference material to `references/`, scripts to `scripts/`.

## Writing Style

- **Imperative form:** "Analyze the codebase" not "You should analyze the codebase"
- **Name patterns, not instances:** "Check for missing error handling" not "Check if fetchUser() has a try-catch"
- **Specificity over abstraction:** "Run tests with `uv run pytest -x`" not "Execute the test suite"
- **WHY statements:** Add rationale to non-obvious rules -- eliminates 80% of wrong answers

```markdown
# GOOD
Separate investigation from execution.
WHY: Premature action on incomplete analysis causes cascading errors.

# BAD
First look at things, then do things.
```

## Progressive Disclosure

```
SKILL.md          -- Essential instructions only (what the agent MUST know)
references/       -- Deep context loaded on demand (patterns, examples, specs)
scripts/          -- Executable tools the skill can invoke
examples/         -- Sample inputs/outputs for calibration
```

**Decision heuristic:**
- Agent needs it every invocation -> SKILL.md
- Agent needs it for specific sub-tasks -> references/
- Agent executes it -> scripts/

## Prompt Engineering

### Six-Layer Specification Stack

Layer each skill instruction through:

| Layer | Purpose | Example |
|-------|---------|---------|
| FORMAT | Output structure | "Return as YAML with fields: severity, file, suggestion" |
| TONE | Communication style | "Direct, no hedging, cite line numbers" |
| CONSTRAINTS | Hard boundaries | "Never modify files outside src/" |
| SUCCESS LOOKS LIKE | Expected outcome | "A passing CI pipeline with no new warnings" |
| EDGE CASES | Boundary behavior | "If no tests exist, create the test file first" |
| REFERENCE EXAMPLE | Calibration anchor | "See references/example-review.md for tone" |

### Goldilocks Zone (~500 tokens for instructions)

- Too few tokens: agent guesses, inconsistent results
- Too many tokens: agent ignores, attention diluted
- Sweet spot: ~500 tokens of core instructions + references on demand

### Categorical Examples

Provide 3-4 examples per category, not exhaustive lists:

```markdown
# GOOD -- patterns
Severity levels:
- CRITICAL: security vulnerabilities, data loss, crashes
- WARNING: performance issues, deprecated APIs, missing validation
- INFO: style inconsistencies, naming conventions

# BAD -- exhaustive lists
- SQL injection is CRITICAL
- XSS is CRITICAL
- CSRF is CRITICAL
- (50 more items...)
```

## XML Boundaries

Use XML tags to create explicit context boundaries:

```markdown
<investigation>
Read all modified files. Map dependencies. Identify risk areas.
</investigation>

<execution>
Apply fixes. Run tests. Report results.
</execution>
```

WHY: Prevents context bleed between phases -- investigation findings stay separate from execution actions.

## Quality Checklist

Pass/fail -- all must pass:

- [ ] Description contains concrete trigger phrases users would say
- [ ] SKILL.md under 500 lines
- [ ] Imperative voice throughout (no "you should", "we can")
- [ ] Each rule has a WHY or the reason is self-evident
- [ ] No duplicate skills with overlapping triggers in the system
- [ ] Progressive disclosure: SKILL.md has only essentials
- [ ] At least one REFERENCE EXAMPLE or expected output format
- [ ] Forbidden list: explicitly states what the skill must NOT do

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Kitchen sink SKILL.md | >500 lines, agent ignores half | Move details to references/ |
| Vague triggers | "help with code" matches everything | Use specific phrases: "review this PR" |
| Tutorial style | "First, you might want to..." | Imperative: "Read the diff. Identify..." |
| No forbidden list | Agent invents scope | Add "Out of Scope" section |
| Similar overlapping skills | Router picks wrong one | Merge or differentiate triggers |
| Version-coupled content | "As of v2.3..." becomes stale | State behavior, not versions |
| Instance-level rules | "Check fetchUser()" | "Check async functions for error handling" |
| Missing WHY | Agent follows letter, breaks spirit | Add rationale to non-obvious rules |
| Rigid rules only | Edge cases break everything | Add decision heuristics for gray areas |
| No calibration example | Output format varies wildly | Add reference example output |
