# Spec Template

Use this structure for generated spec documents. Each section includes guidance on what to include and target length. Total output: 550-800 lines.

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

**Brownfield note**: When this spec modifies existing code, include a subsection "Preserved Behavior" that lists the requirements that already work and must continue to work after the change. Format: `FR-P-[NNN]: [Behavior that must be preserved]`. Missing preserved behavior = silent regressions in the spec.

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

## Section 11: Behavioral Contract (20-40 lines)

Declarative statements mapping triggers to system responses. Each statement must be verifiable in isolation. No implementation details — only observable inputs and outputs.

Format each statement as one of:

- `When [trigger/condition], the system [action/response].`
- `When [condition], the system MUST NOT [action].`

Guidance:
- One trigger maps to exactly one system response per statement.
- Cover the happy path, primary error conditions, and boundary inputs.
- MUST NOT statements belong here when they describe observable behavior; move them to Section 12 when they are design constraints rather than response rules.
- Example of Section 11 (observable behavior): `When payment fails, the system MUST NOT silently succeed — the caller observes the error response`
- Example of Section 12 (internal design constraint): `The system MUST NOT reformat user-supplied text even if it appears inconsistent — this constrains internal processing`
- Example: "When a user submits a form with a missing required field, the system returns a validation error listing all missing fields without submitting the form."
- Example: "When the external payment service is unreachable, the system MUST NOT silently succeed — it must return a retryable error to the caller."

Target 8-15 contract statements.

## Section 12: Explicit Non-Behaviors (15-25 lines)

Constraints that an implementing agent might violate while trying to be "helpful." Each non-behavior states what the system must not do and why the constraint exists.

Format each as:

- `The system MUST NOT [action]. Reason: [why this constraint exists].`

Guidance:
- Focus on plausible-but-wrong behaviors: auto-formatting, auto-sorting, auto-normalizing, silent type coercion, adding unrequested features.
- Cover non-behaviors at API boundaries (what the system must not return or accept), state transitions (what the system must not do mid-operation), and side effects (what the system must not trigger implicitly).
- Example: "The system MUST NOT reformat user-supplied text. Reason: downstream consumers depend on the original whitespace and encoding."
- Example: "The system MUST NOT auto-retry a failed external call without the caller's knowledge. Reason: retry storms during outages."

Target 4-8 MUST NOT statements.

## Section 13: Integration Boundaries (20-35 lines)

One subsection per external system or service this feature integrates with. Document both what flows in/out and what happens when the integration fails.

Format each as:

```markdown
### [External System Name]
- **Data Flow In**: [what this feature sends to the system]
- **Data Flow Out**: [what this feature receives from the system]
- **Failure Mode**: [behavior when the system is unavailable or returns an error]
- **Timeout Strategy**: [how long to wait; what happens on timeout]
```

Guidance:
- If a system has no outbound flow (write-only), document that explicitly: "Data Flow Out: none."
- Failure Mode must be concrete: "returns cached value", "returns 503 to caller", "enqueues for retry", not "handles gracefully."
- If there are no external integrations, write: "This feature has no external integration boundaries. Internal couplings are documented in Section 10."

## Section 14: Ambiguity Warnings (10-20 lines)

Items that are NOT yet Open Questions (they may not require user decisions) but where an implementing agent would likely make a silent assumption that could be wrong. These are spec gaps that could produce plausible-but-incorrect implementations.

Format each as:

- `**AW-[N]**: [What is ambiguous] — [Likely agent assumption if unresolved] — [Question to resolve it]`

Guidance:
- Distinguish from Open Questions (OQ): OQs are known unknowns the user must decide. AW items are gaps where an agent would fill in a default that might be wrong.
- Every unresolved AW item increases implementation risk. Aim to resolve AW items before handoff.
- Example: "**AW-1**: The spec says 'notify the user' but does not specify channel — Likely agent assumption: send an in-app notification — Question: Should this be in-app, email, or both?"
- Example: "**AW-2**: Pagination strategy is unspecified for the list endpoint — Likely agent assumption: offset-based pagination — Question: Is cursor-based pagination required for consistency with other endpoints?"

Target 3-6 ambiguity warnings.

## Section 15: Open Questions / Risks (10-25 lines)

Items that surfaced during Q&A but remain unresolved:

```markdown
- **OQ-[N]**: [Question] — [Context / why it matters] — **Owner**: [who decides]
```

Include risk level (High / Medium / Low) and suggested resolution timeline.

## Section 16: Glossary (5-15 lines)

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
| Behavioral Contract | 20-40 |
| Explicit Non-Behaviors | 15-25 |
| Integration Boundaries | 20-35 |
| Ambiguity Warnings | 10-20 |
| Open Questions | 10-25 |
| Glossary | 5-15 |
| **Total** | **360-670 + header/spacing = 550-800** |
