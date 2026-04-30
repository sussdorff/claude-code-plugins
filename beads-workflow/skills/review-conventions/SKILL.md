---
name: review-conventions
description: Review Conventions
requires_standards: [english-only]
---
# Review Conventions

Scan this project for undocumented coding conventions and propose new standards.

## Instructions

Use the `convention-reviewer` agent from `agents/agentos-lite/` to:

1. **Analyze** the current project codebase
2. **Compare** against existing standards in:
   - `<global-standards-dir>/index.yml`
   - `<project-standards-dir>/index.yml` (project, if it exists)
3. **Discover** recurring patterns that are not documented
4. **Propose** new standards for human review

## Scope

Optional input arguments describing the scan scope.

If no scope specified, analyze the entire project.
Examples:
- `review-conventions` - Full project scan
- `review-conventions src/` - Only src directory
- `review-conventions --recent` - Only files changed in last 20 commits

## Output

For each proposed convention, provide:
- Pattern description with evidence
- Draft standard in markdown
- Suggested triggers for index.yml
- Recommendation: Global vs Project-specific

## Human Decision Required

This command does NOT create standards automatically. After review:
1. Approve/modify the proposed standard text
2. Decide placement (global or project)
3. Ask me to create the files

## Example

```
review-conventions src/adapters/
```

Would analyze adapter classes and propose standards for common patterns found.
