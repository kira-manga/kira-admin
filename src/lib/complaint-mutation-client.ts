import { ApiError, authenticatedFetch, captureAdminSession } from './client-api';
import { complaintMutationDestination, complaintReceiptHeader, decodeComplaintMutationOutcome, type ComplaintMutationOutcome, type ComplaintMutationRequest } from './complaint-mutation-wire';
import { sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';
import { isStepUpApproval, type StepUpApproval } from './step-up-contract';

/** Memory-only, owned above navigation. It is not a durable journal or authority to cross sessions. */
export type ComplaintOperation = Readonly<{
  generation: string;
  request: ComplaintMutationRequest;
  phase: 'prepared' | 'sending' | 'settled';
  outcome?: ComplaintMutationOutcome;
}>;

/** Exactly one explicit attempt. No retry, key/ETag repair, JSON-number conversion or credential storage. */
export async function sendComplaintMutation(operation: ComplaintOperation, signal: AbortSignal, approval?: StepUpApproval): Promise<ComplaintMutationOutcome> {
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
    const url = complaintMutationDestination(operation.request);
    const headers = new Headers(operation.request.headers);
    headers.set(sessionGenerationHeader, operation.generation);
    if (approval) {
      // Only a real backend challenge permits the UI's same-descriptor reapproval action.
      if (!isStepUpApproval(approval, 'complaint-moderation-mutation') || approval.generation !== operation.generation) return { kind: 'unknown' };
      headers.set(stepUpProofIdHeader, approval.proofId);
    }
    response = await authenticatedFetch(url, { method: 'PATCH', headers, body: operation.request.body,
      credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal: controller.signal,
    });
    if (!session.isCurrent()) return lostSession();
    active();
    if (response.redirected || response.headers.has('X-Kira-Admin-Step-Up-Grant-Id') || response.headers.has('X-Kira-Admin-Step-Up-Consumed-Grant-Id')) return { kind: 'unknown' };
    const encoding = response.headers.get('content-encoding');
    const length = response.headers.get('content-length');
    if (encoding !== null && encoding.toLowerCase() !== 'identity'
      || length !== null && (!/^[0-9]{1,20}$/.test(length) || Number(length) > 32_768)) return { kind: 'unknown' };
    reader = response.body?.getReader();
    if (!reader) return { kind: 'unknown' };
    const bytes = new Uint8Array(32_768);
    let size = 0;
    while (true) {
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
    return decodeComplaintMutationOutcome(operation.request, {
      status: response.status, contentType: response.headers.get('content-type'), contract: response.headers.get('X-Kira-Complaint-Contract'),
      etag: response.headers.get('etag'), consumed: response.headers.get(complaintReceiptHeader), challenge: response.headers.get('www-authenticate'),
      retryAfter: response.headers.get('retry-after'), body: bytes.subarray(0, size),
    });
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
