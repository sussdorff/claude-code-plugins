# Architecture Trinity Plugin

The Architecture Trinity is a classification model for architectural tooling that distinguishes three orthogonal roles: decision records, proactive enforcers, and reactive enforcers. This shared vocabulary prevents ambiguity when designing, reviewing, or discussing enforcement strategies across plugins and skills.

> **Note**: This is a stub. Full content, skill definitions, and harness integration will be added in CCP-6up.

## Vocabulary Table

| Term | Category | Enforces? | When? | Example (mira-adapters) |
|------|----------|-----------|-------|------------------------|
| **ADR** | Architecture Decision Record | No — governs humans and tooling | N/A — documents the law | ADR-001: typed IDs required |
| **Helper** | Utility / Module | No — passive | N/A — used on demand | — |
| **Enforcer-Proactive** | Codegen / Builder | Yes | At creation time | `makeIdHelper` — typed ID builder |
| **Enforcer-Reactive** | Lint / Test | Yes | At review / CI time | `no-raw-id-concat` — ESLint rule |

## Definitions

**ADR (Architecture Decision Record)**: A documented architectural decision with context, decision, and consequences. Establishes "what is the law" for a given concern. Other tooling implements or enforces that law but does not replace the ADR.

**Helper**: A utility function or module that encapsulates a common operation. Passive — it helps when used, but carries no enforcement mechanism and does not prevent misuse.

**Enforcer-Proactive (Codegen / Builder)**: Tooling that generates code or scaffolding such that the wrong pattern is structurally impossible. The generated API only accepts valid inputs — misuse is a compile-time or type error, not a runtime or lint finding.

**Enforcer-Reactive (Lint / Test)**: Tooling that checks existing code for violations after the fact. Catches forbidden patterns during code review or CI. Complements proactive enforcers by covering hand-written code paths that codegen cannot reach.
