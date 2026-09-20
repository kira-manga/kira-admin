import { ApiError, authenticatedFetch, captureAdminSession } from './client-api';
import { complaintBatchStatusDestination, decodeComplaintBatchStatusOutcome, isCompleteComplaintBatchStatusResult, type ComplaintBatchStatusOutcome, type ComplaintBatchStatusRequest } from './complaint-batch-status-wire';
import { complaintMutationDestination, complaintReceiptHeader, decodeComplaintMutationOutcome, type ComplaintMutationOutcome, type ComplaintMutationRequest } from './complaint-mutation-wire';
import { sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';
import { isStepUpApproval, type StepUpApproval } from './step-up-contract';

/** Memory-only, owned above navigation. It is not a durable journal or authority to cross sessions. */
export type ComplaintOperationRequest = ComplaintMutationRequest | ComplaintBatchStatusRequest;
export type ComplaintOperationOutcome = ComplaintMutationOutcome | ComplaintBatchStatusOutcome;
export type ComplaintOperation = Readonly<{
  generation: string;
  request: ComplaintOperationRequest;
  phase: 'prepared' | 'sending' | 'settled';
  outcome?: ComplaintOperationOutcome;
}>;

/** Navigation/clear controls never treat a partial batch result as a terminal operation. */
export function isTerminalComplaintOperation(operation: ComplaintOperation | null | undefined): boolean {
  if (operation?.phase !== 'settled' || !operation.outcome) return false;
  if (operation.outcome.kind === 'rejected') return true;
  if (operation.request.method === 'POST') return operation.outcome.kind === 'batch-applied'
    && isCompleteComplaintBatchStatusResult(operation.request, operation.outcome.items);
  if (operation.request.method === 'DELETE') return operation.outcome.kind === 'deleted' && operation.outcome.id === operation.request.targetId;
  return operation.outcome.kind === 'applied' && operation.outcome.id === operation.request.targetId;
}

/** Exactly one explicit attempt. No retry, key/ETag repair, JSON-number conversion or credential storage. */
export async function sendComplaintMutation(operation: ComplaintOperation, signal: AbortSignal, approval?: StepUpApproval): Promise<ComplaintOperationOutcome> {
  let session;
  try { session = captureAdminSession(); } catch (error) { return { kind: error instanceof ApiError && error.status === 401 ? 'session-expired' : 'unknown' }; }
  if (operation.generation !== session.generation) return { kind: 'stale-session' };
  const lostSession = (): ComplaintMutationOutcome => {
    try { captureAdminSession(); return { kind: 'stale-session' }; }
    catch { return { kind: 'session-expired' }; }
  };
  const controller = new AbortController();
  const abort = () => controller.abort();
  const deadline = performance.now() + 70_000;
  const active = () => {
    if (performance.now() >= deadline) abort();
    controller.signal.throwIfAborted();
  };
  const timer = setTimeout(abort, 70_000);
  signal.addEventListener('abort', abort, { once: true });
  let response: Response | undefined;
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  const cancel = () => { void reader?.cancel().catch(() => {}); };
  controller.signal.addEventListener('abort', cancel, { once: true });
  try {
    if (signal.aborted) abort();
    active();
    const url = operation.request.method === 'POST' ? complaintBatchStatusDestination(operation.request) : complaintMutationDestination(operation.request);
    const headers = new Headers(operation.request.headers);
    headers.set(sessionGenerationHeader, operation.generation);
    if (approval) {
      // Only a real backend challenge permits the UI's same-descriptor reapproval action.
      if (!isStepUpApproval(approval, 'complaint-moderation-mutation') || approval.generation !== operation.generation) return { kind: 'unknown' };
      headers.set(stepUpProofIdHeader, approval.proofId);
    }
    response = await authenticatedFetch(url, { method: operation.request.method, headers, body: operation.request.method === 'DELETE' ? undefined : operation.request.body,
      credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal: controller.signal,
    });
    if (!session.isCurrent()) return lostSession();
    active();
    if (response.redirected || response.headers.has('X-Kira-Admin-Step-Up-Grant-Id') || response.headers.has('X-Kira-Admin-Step-Up-Consumed-Grant-Id')) return { kind: 'unknown' };
    const encoding = response.headers.get('content-encoding');
    const length = response.headers.get('content-length');
    const transfer = response.headers.get('transfer-encoding');
    if (encoding !== null && encoding.toLowerCase() !== 'identity'
      || length !== null && (!/^[0-9]{1,20}$/.test(length) || Number(length) > 32_768)
      || transfer !== null && (response.status === 204 || transfer.toLowerCase() !== 'chunked' || length !== null)) return { kind: 'unknown' };
    const emptyDeletion = operation.request.method === 'DELETE' && response.status === 204;
    reader = response.body?.getReader();
    if (!reader && !emptyDeletion) return { kind: 'unknown' };
    const bytes = new Uint8Array(emptyDeletion ? 0 : 32_768);
    let size = 0;
    while (reader) {
      active();
      const next = await reader.read();
      active();
      if (next.done) break;
      if (next.value.byteLength > bytes.length - size) return { kind: 'unknown' };
      bytes.set(next.value, size);
      size += next.value.byteLength;
    }
    if (!session.isCurrent()) return lostSession();
    if (length !== null && Number(length) !== size) return { kind: 'unknown' };
    if (response.status === 401 && response.headers.get('www-authenticate') === 'KiraSession realm="kira-admin-bff"') return { kind: 'session-expired' };
    const metadata = {
      status: response.status, contentType: response.headers.get('content-type'), contract: response.headers.get('X-Kira-Complaint-Contract'),
      etag: response.headers.get('etag'), consumed: response.headers.get(complaintReceiptHeader), challenge: response.headers.get('www-authenticate'),
      retryAfter: response.headers.get('retry-after'), location: response.headers.get('location'), body: bytes.subarray(0, size),
    };
    return operation.request.method === 'POST' ? decodeComplaintBatchStatusOutcome(operation.request, metadata) : decodeComplaintMutationOutcome(operation.request, metadata);
  } catch { return session.isCurrent() ? { kind: 'unknown' } : lostSession(); }
  finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
    controller.signal.removeEventListener('abort', cancel);
    cancel();
    reader?.releaseLock();
    controller.abort();
    if (response && !response.bodyUsed) void response.body?.cancel().catch(() => {});
  }
}
