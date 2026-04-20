# Spec Template

Use this structure for generated spec documents. Each section includes guidance on what to include and target length. Total output: 500-700 lines.

---

## Output File Header

```markdown
# Feature Spec: [Feature Name]

**Status**: Draft | Review | Approved
**Author**: [User] + spec-developer
**Date**: [YYYY-MM-DD]
**Version**: 1.0
```

---

## Section 1: Executive Summary (5-10 lines)

One paragraph summarizing what this feature does, why it matters, and who it's for. A reader should understand the feature at a high level after reading only this section.

Include: core purpose, primary user, key benefit, scope boundary.

## Section 2: Problem Statement & Motivation (15-30 lines)

- What specific problem exists today?
- Who experiences this problem and how often?
- What's the current workaround and its limitations?
- What triggered the need for this feature now?
- What happens if we don't build it?

Reference answers from Goals & Motivation round.

## Section 3: User Stories / Use Cases (30-60 lines)

Format each as:

```markdown
### UC-[N]: [Title]
**Actor**: [Role]
**Precondition**: [State before]
**Trigger**: [What initiates this]
**Main Flow**:
1. [Step]
2. [Step]
3. [Step]
**Postcondition**: [State after]
**Exceptions**: [What can go wrong at each step]
```

Include 3-6 use cases covering: primary happy path, secondary flows, admin/operator flows.

## Section 4: Data Model (40-70 lines)

- Entity list with attributes and types
- Entity relationships (one-to-many, many-to-many)
- State machine diagram (ASCII or Mermaid) for stateful entities
- Data validation rules and constraints
- Storage considerations (persistent vs. ephemeral)

Format entities as:

```markdown
### Entity: [Name]
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| ... | ... | ... | ... |

**States**: [state1] -> [state2] -> [state3]
**Invariants**: [rules that must always hold]
```

## Section 5: Functional Requirements (60-100 lines)

Numbered, testable requirements. Each must be verifiable.

Format:

```markdown
**FR-[NNN]**: [Requirement statement]
- **Priority**: Must / Should / Could
- **Acceptance**: [How to verify this is met]
- **Notes**: [Additional context]
```

Group by feature area. Target 15-30 requirements.

## Section 6: Non-Functional Requirements (20-40 lines)

Cover each applicable category:

- **Performance**: Response times, throughput, resource limits
- **Scalability**: Growth projections, bottleneck points
- **Security**: Authentication, authorization, input validation, data protection
- **Reliability**: Uptime targets, failover, data durability
- **Accessibility**: WCAG level, screen reader support, keyboard navigation
- **Internationalization**: Supported locales, RTL, date/number formats

Format as NFR-[NNN] with measurable targets.

## Section 7: API / Interface Contracts (40-70 lines)

Only include if the feature exposes or consumes APIs. Document:

- Endpoint / command / function signatures
- Request/response schemas (simplified, not full OpenAPI)
- Authentication requirements
- Rate limits and quotas
- Versioning strategy
- Error response format

Format:

```markdown
### [METHOD] /path/to/endpoint
**Auth**: [Required / Public]
**Request**: [Schema summary]
**Response 200**: [Schema summary]
**Response 4xx**: [Error cases]
```

If not applicable, write: "This feature does not expose external APIs. Internal interfaces are covered in Functional Requirements."

## Section 8: Error Handling Strategy (20-40 lines)

- Error classification (user errors vs. system errors vs. external failures)
- Error message guidelines (detail level, tone)
- Recovery paths for each error class
- Logging requirements (what, where, retention)
- Alerting thresholds
- Degraded mode behavior

## Section 9: Edge Cases & Boundary Conditions (30-50 lines)

List each as:

```markdown
### EC-[N]: [Title]
**Scenario**: [Specific condition]
**Expected Behavior**: [What should happen]
**Risk if Unhandled**: [Consequence]
```

Cover: empty inputs, maximum scale, concurrent operations, partial failures, timezone boundaries, Unicode edge cases.

## Section 10: Dependencies & Integration Points (15-30 lines)

- External systems and their SLAs
- Internal services and coupling level
- Data migration requirements
- Backward compatibility constraints
- Feature flags or phased rollout needs

## Section 11: Open Questions / Risks (10-25 lines)

Items that surfaced during Q&A but remain unresolved:

```markdown
- **OQ-[N]**: [Question] — [Context / why it matters] — **Owner**: [who decides]
```

Include risk level (High / Medium / Low) and suggested resolution timeline.

## Section 12: Glossary (5-15 lines)

Domain-specific terms used in this spec:

```markdown
| Term | Definition |
|------|-----------|
| [Term] | [Definition] |
```

---

## Line Budget Guide

| Section | Target Lines |
|---------|-------------|
| Executive Summary | 5-10 |
| Problem Statement | 15-30 |
| User Stories | 30-60 |
| Data Model | 40-70 |
| Functional Requirements | 60-100 |
| Non-Functional Requirements | 20-40 |
| API Contracts | 40-70 |
| Error Handling | 20-40 |
| Edge Cases | 30-50 |
| Dependencies | 15-30 |
| Open Questions | 10-25 |
| Glossary | 5-15 |
| **Total** | **290-540 + header/spacing = 500-700** |
