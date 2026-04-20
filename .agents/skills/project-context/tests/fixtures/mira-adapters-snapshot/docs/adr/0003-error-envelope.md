---
contract: Error Envelope
applies_to:
  - adapter-common
status: proposed
---
# ADR 0003: Error Envelope

All errors must be wrapped in a standard envelope.

## Context

Inconsistent error shapes make client-side handling brittle.

## Decision (proposed)

All errors returned from adapter functions should be wrapped in a standard `ErrorEnvelope` type.

## Status

This ADR is still in proposal stage — not yet accepted or implemented.
