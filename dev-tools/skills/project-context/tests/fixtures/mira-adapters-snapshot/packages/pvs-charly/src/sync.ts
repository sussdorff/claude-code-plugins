/**
 * PVS-Charly Sync Module
 *
 * Processes delta events from the PVS Charly adapter. This file contains
 * inline `event.kind === 'literal'` checks — an implicit contract pattern
 * flagged by architecture-scout heuristic `repeated-event-kind`.
 *
 * See: docs/adr/ — no ADR currently covers delta event kind semantics.
 * Suggested: ADR-0004 delta-event-kind + makeDeltaKindHelper
 */

interface DeltaEvent {
  kind: string;
  payload: unknown;
  timestamp: number;
}

export function processDeltaEvent(event: DeltaEvent): void {
  // Implicit contract: repeated event.kind string checks — no shared enum or ADR
  if (event.kind === 'created') {
    handleCreated(event.payload);
  } else if (event.kind === 'updated') {
    handleUpdated(event.payload);
  } else if (event.kind === 'deleted') {
    handleDeleted(event.payload);
  } else {
    console.warn(`Unknown event kind: ${event.kind}`);
  }
}

export function reconcileEvents(events: DeltaEvent[]): DeltaEvent[] {
  // Another occurrence of repeated-event-kind pattern (line 28)
  return events.filter((e) => e.kind === 'created' || e.kind === 'updated');
}

function handleCreated(payload: unknown): void {
  // Inline error shape (pre-trinity, no shared helper yet)
  if (!payload) {
    throw { error: 'Missing payload for created event', code: 400 };
  }
  console.log('created', payload);
}

function handleUpdated(payload: unknown): void {
  console.log('updated', payload);
}

function handleDeleted(payload: unknown): void {
  console.log('deleted', payload);
}
