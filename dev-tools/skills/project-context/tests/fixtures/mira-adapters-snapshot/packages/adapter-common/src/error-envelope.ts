/**
 * Error Envelope — pre-trinity stub.
 *
 * ADR-0003 (docs/adr/0003-error-envelope.md) is proposed but not yet accepted.
 * This file exists as a placeholder — no Helper, Proactive, or Reactive enforcer
 * has been implemented yet. Used by architecture-scout as a test fixture for
 * detecting a "pre-trinity" contract.
 *
 * TODO: Once ADR-0003 is accepted, replace this stub with the full implementation
 * and add:
 *   - createErrorEnvelope() helper
 *   - no-inline-error-shape ESLint rule (Reactive Enforcer)
 */

export interface ErrorEnvelope {
  error: string;
  code: number;
  details?: unknown;
}

// Inline usage — not yet using a shared helper (pre-trinity pattern):
// { error: "Not found", code: 404 }
// { error: "Timeout", code: 408 }
// These inline shapes appear in multiple files — see architecture-scout heuristic: inline-error-shape
