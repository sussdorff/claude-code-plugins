---
contract: Schema Codegen
applies_to:
  - pvs-x-isynet
  - pvs-charly
  - pvs-xdt
status: accepted
---
# ADR 0002: Schema Codegen

Schemas must be generated from a single source of truth.

## Context

Manual schema duplication leads to drift between packages.

## Decision

All applicable packages must have a codegen script that generates types/validators from a schema definition.

## Consequences

- Single source of truth for data shapes
- Requires codegen infrastructure in each applicable package
- Violations caught by schema:check scripts
