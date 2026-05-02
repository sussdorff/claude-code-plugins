---
id: ADR-alpha
status: accepted
date: 2026-05-01
contract: command-runner-contract
applies_to:
  - scripts/*.py
  - core/**/*.py
prohibits:
  - "No direct subprocess calls without CommandRunner"
decision_summary: "All subprocess invocations must go through CommandRunner to enable testing and auditing."
---
# ADR-alpha: Use CommandRunner for All Subprocess Calls

## Decision

All subprocess invocations must use CommandRunner.
