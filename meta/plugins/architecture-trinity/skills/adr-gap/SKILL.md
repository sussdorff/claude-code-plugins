---
name: adr-gap
description: >-
  Audit a repo for ADR hoist debt and pre-trinity packages. Triggers on: adr gap, hoist debt,
  adr audit, pre-trinity packages, architecture drift.
argument-hint: "[repo_root] [--create-beads] [--ci] [--allow-unknown]"
tags: architecture, adr, audit
---

# /adr-gap

Audit a repository for ADR hoist debt and pre-trinity packages.

**Hoist debt** occurs when an Architecture Decision Record's `hoist_when` condition becomes true —
meaning it's time to move a helper or pattern from a specific package into a shared location.

**Pre-trinity packages** are packages not yet covered by any ADR (not in any `applies_to` or
`hoist_when.target` list). These represent architecture drift — packages that predate the
Architecture Trinity decision framework.

## When to Use

- After adding a new package to a monorepo — check for newly triggered hoist conditions
- In CI, with `--ci` flag, to block on unresolved hoist debt
- Periodically to audit architecture coverage and find pre-trinity packages
- Before a refactoring session to understand what needs hoisting

## How It Works

The skill runs `adr-hoist-check.py` against a repository root:

1. Walks `docs/adr/*.md` and parses YAML frontmatter
2. For each ADR with a `hoist_when` block, evaluates the specified condition
3. If the condition is met, reports "HOIST DUE" with the trigger bead title and evidence
4. Optionally creates a bead for each due hoist (with `--create-beads`)
5. Reports all packages not covered by any ADR as "pre-trinity"

## Usage

```bash
# Basic audit (report only, no side effects)
uv run scripts/adr-hoist-check.py <repo_root>

# Create beads for all due hoists
uv run scripts/adr-hoist-check.py <repo_root> --create-beads

# CI mode: exit non-zero if any hoists are due
uv run scripts/adr-hoist-check.py <repo_root> --ci

# CI mode, allow unknown condition strings without failing
uv run scripts/adr-hoist-check.py <repo_root> --ci --allow-unknown
```

## Flags

| Flag | Effect |
|------|--------|
| (none) | Report only — list hoist debt and pre-trinity packages, exit 0 |
| `--create-beads` | Create a bead (via `bd create`) for each due hoist (if no open bead exists) |
| `--ci` | Exit non-zero if hoists are due, conditions are unknown, or frontmatter is malformed |
| `--allow-unknown` | With `--ci`: do not exit non-zero for unknown condition strings |

## ADR Frontmatter

ADRs use YAML frontmatter to declare hoist conditions. See `references/adr-frontmatter.md`
for the full specification.

Minimal example triggering a hoist check:

```yaml
---
status: accepted
contract: id-taxonomy
applies_to: [pvs-x-isynet]
hoist_when:
  condition: second_package_implements_contract
  contract: id-taxonomy
  target: adapter-common
  trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'
---
```

## Supported Conditions

| Condition | Description |
|-----------|-------------|
| `second_package_implements_contract` | True when any package beyond `applies_to` has declared this contract in its `contracts.yml` |
| `allowlist_entry_exists_for` | Reserved for future use |

## Contract Detection

Packages declare their contracts via a `contracts.yml` marker file:

```
packages/
  pvs-x-isynet/
    contracts.yml        # contains: [id-taxonomy, error-envelope]
  pvs-charly/
    contracts.yml        # contains: [id-taxonomy]
  adapter-common/
    (no contracts.yml)   # pre-trinity: no declared contracts
```

## Output Format

```
ADR Hoist Debt:
  HOIST DUE: ADR-001-id-taxonomy.md
    Condition: second_package_implements_contract
    Bead: [HOIST] makeIdHelper to adapter-common
    Evidence: pvs-charly

Pre-trinity packages:
  adapter-common
```

## Integration

- Pairs with `enforcement_matrix_scanner.py` from `/project-context` skill
- Uses `bd create` and `bd list` for bead integration (requires `bd` CLI)
- References: `references/adr-frontmatter.md` for frontmatter schema
