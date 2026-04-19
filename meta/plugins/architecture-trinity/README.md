# Architecture Trinity Plugin

The Architecture Trinity is a classification model for architectural tooling that distinguishes four precise terms: ADR, Helper, Enforcer-Proactive, and Enforcer-Reactive. This shared vocabulary prevents ambiguity when designing, reviewing, or discussing enforcement strategies across plugins and skills.

## Quick Start

This plugin provides tools for declaring and auditing architectural contracts:

- **ADR Frontmatter Spec** (`references/adr-frontmatter.md`) — Declare which contracts your ADRs govern, which packages they apply to, and when helpers should be hoisted to shared locations
- **`/adr-gap` skill** — Audit a repository for hoist debt and pre-trinity packages (packages not yet covered by any ADR)
- **`adr-hoist-check.py`** — Evaluator script that detects when hoist conditions are met and auto-creates beads

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

## ADR Hoist-Trigger Mechanism

ADRs can declare a `hoist_when` condition in their YAML frontmatter. When the condition becomes true, it signals that a Helper or pattern should be hoisted from a specific package into a shared location (typically `adapter-common`).

### How It Works

1. **ADR declares a hoist trigger** — Author adds `hoist_when` block to ADR frontmatter:

   ```yaml
   ---
   status: accepted
   contract: id-taxonomy
   applies_to: [pvs-x-isynet]
   helper: makeIdHelper
   hoist_when:
     condition: second_package_implements_contract
     contract: id-taxonomy
     target: adapter-common
     trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'
   ---
   ```

2. **Evaluator runs periodically (or on-demand)** — `adr-hoist-check.py` walks all ADRs and evaluates their conditions:
   - Checks package contracts via `contracts.yml` marker files
   - Detects when a second team independently implements the same contract
   - If condition is true and no bead exists: creates a hoist bead automatically (if `--create-beads` flag is set)

3. **Developer hoists the Helper** — The created bead tracks the work to move the Helper to the shared location, completing the hoisting workflow

### Supported Conditions

| Condition | Triggers when |
|-----------|---------------|
| `second_package_implements_contract` | Any package beyond `applies_to` declares the same contract in its `contracts.yml` |
| `allowlist_entry_exists_for` | Reserved for future use |

### Using the `/adr-gap` Skill

Audit hoist debt and architecture coverage on demand:

```bash
# Report hoist debt and pre-trinity packages
/adr-gap

# Create beads for all due hoists
/adr-gap --create-beads

# CI mode: fail if any hoists are due
/adr-gap --ci
```

### Pre-Trinity Packages

The `/adr-gap` skill also reports **pre-trinity packages** — packages that don't appear in any ADR's `applies_to` or `hoist_when.target` lists. These packages predate the Architecture Trinity framework and have no declared contracts. Seeing this list helps you plan which packages to bring into the Trinity framework next.

## References

- **`references/adr-frontmatter.md`** — Complete ADR frontmatter specification and contract declaration format
- **`skills/adr-gap/SKILL.md`** — Full documentation for the `/adr-gap` skill
