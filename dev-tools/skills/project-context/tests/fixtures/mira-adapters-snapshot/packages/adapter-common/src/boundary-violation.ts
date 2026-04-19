/**
 * BOUNDARY VIOLATION — Test Fixture File
 *
 * This file intentionally imports from pvs-charly (layer:application),
 * which violates the vision.md boundary rule:
 *   "layer:platform must not depend on layer:application"
 *
 * adapter-common is layer:platform — it must NOT import from pvs-charly.
 *
 * This file exists as a TEST FIXTURE for architecture-scout to detect
 * vision boundary violations (Step 5 of the agent's workflow).
 *
 * Expected scout output:
 *   severity: BLOCKING
 *   rule: vision-boundary:platform-no-application-import
 *   source: packages/adapter-common/src/boundary-violation.ts:3
 */

// This import violates the platform-no-application-import boundary rule:
import { processDeltaEvent } from '../../pvs-charly/src/sync';

export function adapterCommonWrapper(event: unknown): void {
  // Calling into application layer from platform layer — forbidden
  processDeltaEvent(event as Parameters<typeof processDeltaEvent>[0]);
}
