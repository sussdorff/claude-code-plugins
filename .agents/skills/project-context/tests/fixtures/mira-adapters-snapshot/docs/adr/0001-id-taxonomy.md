---
contract: ID Taxonomy
applies_to:
  - adapter-common
  - pvs-x-isynet
  - pvs-charly
status: accepted
---
# ADR 0001: ID Taxonomy

All entity IDs must use typed helpers, not raw strings.

## Context

Raw string IDs cause type confusion and make it easy to accidentally pass the wrong ID type.

## Decision

All packages that deal with entity IDs must use the `makeIdHelper` function to create typed ID accessors.

## Consequences

- Type safety at compile time
- No accidental mixing of ID types
- Requires helper in every applicable package
