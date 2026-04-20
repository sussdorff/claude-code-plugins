/**
 * PVS-Charly Reconciliation Module
 *
 * Cross-adapter reconciliation logic. Contains additional `event.kind === 'literal'`
 * checks — a third occurrence in pvs-charly of the implicit `repeated-event-kind`
 * contract pattern flagged by architecture-scout.
 *
 * See: docs/adr/ — no ADR currently covers delta event kind semantics.
 * Suggested: ADR-0004 delta-event-kind + makeDeltaKindHelper
 */

interface DeltaEvent {
  kind: string;
  sourceAdapter: string;
  payload: unknown;
  timestamp: number;
}

export function reconcileWithRemote(localEvents: DeltaEvent[], remoteEvents: DeltaEvent[]): DeltaEvent[] {
  // Implicit contract: event.kind checks without shared enum (line 28)
  const conflictKinds = ['updated', 'deleted'];
  const conflicts = localEvents.filter(
    (local) =>
      conflictKinds.includes(local.kind) &&
      remoteEvents.some((remote) => remote.kind === local.kind && remote.timestamp > local.timestamp)
  );
  return conflicts;
}

export function applyReconciled(event: DeltaEvent): void {
  // Repeated event.kind === literal pattern — same implicit contract as sync.ts
  if (event.kind === 'created') {
    insertReconciled(event.payload);
  } else if (event.kind === 'updated') {
    updateReconciled(event.payload);
  } else if (event.kind === 'deleted') {
    deleteReconciled(event.payload);
  }
}

function insertReconciled(payload: unknown): void {
  console.log('reconcile insert', payload);
}

function updateReconciled(payload: unknown): void {
  console.log('reconcile update', payload);
}

function deleteReconciled(payload: unknown): void {
  console.log('reconcile delete', payload);
}
