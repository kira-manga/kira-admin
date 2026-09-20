import { prepareComplaintBatchStatusRequest, type ComplaintBatchStatusRequest } from '../lib/complaint-batch-status-wire';
import type { ComplaintModerationTarget } from '../lib/complaint-moderation-wire';
import { complaintId, complaintKey, complaintScope } from './complaint-mutation-fixture';

export const batchSecondId = '44444444-4444-4444-8444-444444444444';
export function batchTarget(id = complaintId, version = '9007199254740992'): ComplaintModerationTarget {
  return { id, kind: 'REPORT', ownership: 'INSTALLATION', actionTag: `"complaint-${id}-v${version}"` };
}
export function batchRequest() {
  return prepareComplaintBatchStatusRequest([batchTarget(batchSecondId, '9223372036854775806'), batchTarget()], 'RESOLVED', complaintScope, complaintKey);
}
/** Synthetic exact backend encoding; numeric Long digits never pass through a JavaScript Number. */
export function batchAck(request: ComplaintBatchStatusRequest = batchRequest()) {
  return `{"items":[${request.targets.map((target) => `{"id":"${target.id}","version":${BigInt(target.baseVersion) + BigInt(1)}}`).join(',')}]}`;
}
export function batchResponse(request: ComplaintBatchStatusRequest = batchRequest(), extra: HeadersInit = {}) {
  const headers = new Headers({ 'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Admin-Step-Up-Consumed': 'true' });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return new Response(batchAck(request), { headers });
}
