# ADR Frontmatter Specification

Architecture Decision Records in this project use YAML frontmatter (between `---` fences) to
declare contracts, coverage scope, and optional hoist-trigger conditions.

## Full Schema

```yaml
---
# Required fields
status: accepted           # accepted | proposed | deprecated | superseded

# Contract declaration (optional but recommended)
contract: id-taxonomy      # machine-readable contract name (kebab-case)
applies_to:                # packages this ADR applies to
  - pvs-x-isynet           # one package name per line (or inline list)

# Trinity artifact references (optional)
helper: makeIdHelper       # helper function/module that implements this contract
enforcer_proactive: id-codegen   # codegen tool (Enforcer-Proactive)
enforcer_reactive: no-raw-id     # lint rule (Enforcer-Reactive)

# Hoist trigger (optional) — evaluated by adr-hoist-check.py
hoist_when:
  condition: second_package_implements_contract  # evaluator ID (see below)
  contract: id-taxonomy                          # which contract to check
  target: adapter-common                         # where to hoist the helper to
  trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'  # bead title to create
---
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | ADR lifecycle state: `accepted`, `proposed`, `deprecated`, or `superseded` |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `contract` | string | Machine-readable contract name (kebab-case). Used by enforcement_matrix_scanner. |
| `applies_to` | list\|string | Package(s) this decision applies to. Inline or block list format accepted. |
| `helper` | string | Name of the Helper artifact implementing this contract. |
| `enforcer_proactive` | string | Name of the Enforcer-Proactive (codegen) artifact. |
| `enforcer_reactive` | string | Name of the Enforcer-Reactive (lint rule) artifact. |
| `hoist_when` | object | Hoist trigger block — see below. |

## `hoist_when` Block

The `hoist_when` block declares a condition that, when true, signals that a helper or pattern
is ready to be hoisted from a specific package into a shared location.

```yaml
hoist_when:
  condition: <evaluator-id>       # required: which evaluator to use
  contract: <contract-name>       # required for most evaluators
  target: <package-name>          # target package to hoist into
  trigger_bead_title: '<title>'   # bead title to create (must be unique enough to find)
```

### Supported Conditions

#### `second_package_implements_contract`

**True when**: Any package beyond those listed in `applies_to` has declared the same contract
in its `contracts.yml` file.

**Rationale**: If a second team independently implements the same contract, the helper should
be extracted to a shared package rather than duplicated.

**Example**:
```yaml
hoist_when:
  condition: second_package_implements_contract
  contract: id-taxonomy
  target: adapter-common
  trigger_bead_title: '[HOIST] makeIdHelper to adapter-common'
```

This fires when any package (not in `applies_to`) has `id-taxonomy` in its `contracts.yml`.

#### `allowlist_entry_exists_for` (reserved)

Reserved for future use. Will fire when a named allowlist file contains an entry for a
specific identifier — e.g., when a team has been granted an exception that should trigger
a migration bead.

### Trigger Bead Title Convention

Use the format `[HOIST] <artifact> to <target>` for trigger bead titles. This prefix allows
`adr-hoist-check.py` to efficiently query open beads via `bd list --title-contains=[HOIST]`.

## Contract Declaration in Packages

Packages declare which contracts they implement via a `contracts.yml` file at the package root:

```
packages/
  pvs-x-isynet/
    contracts.yml    # declares: [id-taxonomy, error-envelope]
  pvs-charly/
    contracts.yml    # declares: [id-taxonomy]
  adapter-common/
    (no contracts.yml — pre-trinity package, not yet covered by any ADR)
```

**`contracts.yml` format** (YAML list):
```yaml
- id-taxonomy
- error-envelope
```

## Pre-Trinity Packages

A package is "pre-trinity" if it does not appear in any ADR's `applies_to` list or
`hoist_when.target` field. These packages predate the Architecture Trinity framework and
have no declared contracts. The `/adr-gap` skill reports them separately.

## Examples

### Minimal ADR (no hoist trigger)

```yaml
---
status: accepted
contract: error-envelope
applies_to:
  - adapter-common
  - pvs-x-isynet
helper: createErrorEnvelope
---
```

### ADR with hoist trigger

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

### Proposed ADR (not yet accepted)

```yaml
---
status: proposed
contract: schema-codegen
applies_to:
  - adapter-common
enforcer_proactive: gen-schema
---
```

## Tool Integration

| Tool | Uses | Fields consumed |
|------|------|-----------------|
| `adr-hoist-check.py` | Hoist detection | `hoist_when`, `applies_to` |
| `enforcement_matrix_scanner.py` | Coverage matrix | `contract`, `applies_to`, `status`, `helper`, `enforcer_proactive`, `enforcer_reactive` |
| `/adr-gap` skill | Both of the above | All fields |
