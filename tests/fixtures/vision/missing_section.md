---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---

## Vision Statement

We build tools that make developers faster by removing workflow friction.

## Target Group

Software developers working in mid-size teams on long-lived codebases.

## Core Need (JTBD)

Teams need to maintain architectural quality across many contributors without constant manual review.

## Positioning

For developer teams that struggle with architectural drift, our tool suite provides automated boundary enforcement.

## Value Principles

- **P1**: All architectural boundaries are enforced at commit time, not review time.

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P1 | Boundaries enforced at commit time | git hooks, pre-commit | Value Principles |

## NOT in Vision

- Auto-fixing violations without developer confirmation
