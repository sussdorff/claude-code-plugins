# Vision — mira-adapters Architecture

This document describes the high-level architecture and enforced layer boundaries
for the mira-adapters project.

## Overview

mira-adapters is a set of healthcare data integration adapters that bridge various
PVS (Practice Management Software) systems with a common platform layer.

## Layer Boundaries

The architecture enforces strict unidirectional dependencies between layers.

| rule | scope | source-section |
|------|-------|----------------|
| platform-no-application-import | layer:platform must not depend on layer:application | Layer Definitions |
| application-no-infra-import | layer:application must not depend on layer:infrastructure directly | Layer Definitions |

## Layer Definitions

### Layer: platform

The `platform` layer provides shared utilities, types, and cross-cutting concerns
used by all adapters. It must NOT depend on any specific adapter implementation.

**Packages in this layer:**
- `adapter-common` — shared types, helpers, and utilities

**Forbidden imports:**
- Must not import from `pvs-charly`, `pvs-x-isynet`, `pvs-xdt`, or `adapter-cli`

### Layer: application

The `application` layer contains adapter-specific business logic. Each adapter
implements a specific PVS integration.

**Packages in this layer:**
- `pvs-charly` — Charly PVS adapter
- `pvs-x-isynet` — iSYNET PVS adapter
- `pvs-xdt` — XDT file format adapter

**Allowed imports:**
- May import from `adapter-common` (platform layer)
- Must NOT import from other application-layer adapters directly

### Layer: infrastructure

**Packages in this layer:**
- `adapter-cli` — CLI tooling for running adapters

## Trinity Coverage for Boundary Enforcement

| Contract | ADR | Helper | Proactive | Reactive | Status |
|----------|-----|--------|-----------|----------|--------|
| Layer boundaries | vision.md (this file) | ❌ | ❌ | ❌ | pre-trinity |

> Note: vision.md serves as the ADR for layer boundaries. The Reactive Enforcer
> (ESLint import rules) is tracked as technical debt.
