import { prepareComplaintClosureReason } from './complaint-content-editor';
import { ComplaintMutationWireError, prepareComplaintMutationRequest, type ComplaintMutationRequest } from './complaint-mutation-wire';

export { decodeComplaintMutationApplied as decodeComplaintModerationApplied } from './complaint-mutation-wire';

export type ComplaintStatusTarget = 'OPEN' | 'IN_PROGRESS' | 'PLANNED' | 'RESOLVED' | 'NOT_PLANNED';

/** Supplied by a verified snapshot reader, never evidence of authorization by itself. */
export type ComplaintModerationTarget = Readonly<{
  id: string;
  actionTag: string;
  kind: 'REPORT' | 'REPLY' | 'NOTICE';
  ownership: 'INSTALLATION' | 'SYSTEM';
}>;

export type ComplaintModerationChange =
  | Readonly<{ operation: 'status'; status: ComplaintStatusTarget }>
  | Readonly<{ operation: 'closure'; reason: string }>;

/**
 * Capture one status/closure intent. Keep the returned description on timeout or conflict:
 * no regenerated key, changed If-Match, or inferred step-up consumption. There is no fetch,
 * BFF registration, storage or credential handling here. Backend authorization stays mandatory.
 */
export function prepareComplaintModerationRequest(
  target: ComplaintModerationTarget,
  change: ComplaintModerationChange,
  dataScopeId: string,
  idempotencyKey: string,
): ComplaintMutationRequest {
  const invalid = (): never => { throw new ComplaintMutationWireError('INVALID_CAPTURE'); };
  if ((target.kind !== 'REPORT' && target.kind !== 'REPLY') || target.ownership !== 'INSTALLATION') invalid();
  let body: string;
  try {
    switch (change.operation) {
      case 'status':
        if (!['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'].includes(change.status)) invalid();
        body = JSON.stringify({ status: change.status });
        break;
      case 'closure':
        body = JSON.stringify({ reason: prepareComplaintClosureReason(change.reason) });
        break;
      default:
        return invalid();
    }
    return prepareComplaintMutationRequest(change.operation, target.id, dataScopeId, idempotencyKey, target.actionTag, body);
  } catch {
    // Never attach caller text, credentials, snapshots or a nested parser exception.
    return invalid();
  }
}
