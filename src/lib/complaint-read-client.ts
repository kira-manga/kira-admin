import { isComplaintDetailPath, isComplaintDetailQuery } from './admin-route-policy';
import { authenticatedFetch } from './client-api';
import { ComplaintReadWireError, decodeComplaintAdminDetail, type ParsedComplaintAdminDetail } from './complaint-read-wire';

export type ComplaintAdminDetailRequest = Readonly<{ id: string; dataScopeId: string; signal: AbortSignal }>;
export type ComplaintReadClientReason = 'UNAVAILABLE' | 'SESSION_EXPIRED' | 'UNAUTHORIZED' | 'FORBIDDEN' | 'INVALID_RESPONSE' | 'NETWORK';

const messages: Record<ComplaintReadClientReason, string> = {
  UNAVAILABLE: 'Complaint detail is unavailable or not found.',
  SESSION_EXPIRED: 'Your admin session has expired.',
  UNAUTHORIZED: 'Complaint detail was not authorized.',
  FORBIDDEN: 'Administrator access is required.',
  INVALID_RESPONSE: 'Complaint detail could not be validated.',
  NETWORK: 'Complaint detail could not be reached.',
};

export class ComplaintReadClientError extends Error {
  constructor(readonly reason: ComplaintReadClientReason) {
    super(messages[reason]);
    this.name = 'ComplaintReadClientError';
  }
}

/** One same-origin, session-backed read. Neither an entered scope nor parsed data proves activation. */
export async function fetchComplaintAdminDetail({ id, dataScopeId, signal }: ComplaintAdminDetailRequest): Promise<ParsedComplaintAdminDetail> {
  if (signal.aborted) throw cancelled();
  const query = `?dataScopeId=${dataScopeId}`;
  if (!isComplaintDetailPath(['complaints', id]) || !isComplaintDetailQuery(query)) throw new ComplaintReadClientError('INVALID_RESPONSE');
  const deadline = new AbortController();
  const abort = () => deadline.abort();
  signal.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(abort, 70_000);
  let response: Response | undefined;
  try {
    response = await authenticatedFetch(`/api/backend/complaints/${id}${query}`, {
      method: 'GET', credentials: 'same-origin', redirect: 'error', signal: deadline.signal,
      headers: { Accept: 'application/json, application/problem+json', 'X-Kira-Complaint-Contract': '1' },
    });
    if (deadline.signal.aborted) throw new ComplaintReadClientError('NETWORK');
    if (response.redirected) throw new ComplaintReadClientError('INVALID_RESPONSE');
    if (response.status === 401) {
      // The GET BFF strips upstream challenges; only its exact local boundary declares expiry.
      const localExpiry = response.headers.get('www-authenticate') === 'KiraSession realm="kira-admin-bff"';
      throw new ComplaintReadClientError(localExpiry ? 'SESSION_EXPIRED' : 'UNAUTHORIZED');
    }
    if (response.status === 403) throw new ComplaintReadClientError('FORBIDDEN');
    if (response.status === 502 || response.status === 504) throw new ComplaintReadClientError('NETWORK');
    if (response.status === 404 || response.status === 429 || response.status >= 500) throw new ComplaintReadClientError('UNAVAILABLE');
    if (response.status !== 200) throw new ComplaintReadClientError('INVALID_RESPONSE');
    const body = await readDetailBytes(response, deadline.signal);
    if (deadline.signal.aborted) throw new ComplaintReadClientError('NETWORK');
    return decodeComplaintAdminDetail(id, {
      status: response.status, contentType: response.headers.get('content-type'),
      contract: response.headers.get('X-Kira-Complaint-Contract'), etag: response.headers.get('etag'), body,
    });
  } catch (error) {
    if (signal.aborted) throw cancelled();
    if (deadline.signal.aborted) throw new ComplaintReadClientError('NETWORK');
    if (error instanceof ComplaintReadClientError) throw error;
    if (error instanceof ComplaintReadWireError) throw new ComplaintReadClientError('INVALID_RESPONSE');
    // No response body, arbitrary exception message, identifier or nested cause crosses this boundary.
    throw new ComplaintReadClientError('NETWORK');
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
    void response?.body?.cancel().catch(() => {});
  }
}

async function readDetailBytes(response: Response, signal: AbortSignal): Promise<Uint8Array> {
  const reader = response.body?.getReader();
  if (!reader) throw new ComplaintReadClientError('INVALID_RESPONSE');
  const cancel = () => { void reader.cancel().catch(() => {}); };
  signal.addEventListener('abort', cancel, { once: true });
  try {
    const body = new Uint8Array(32_768);
    let length = 0;
    while (true) {
      if (signal.aborted) throw new ComplaintReadClientError('NETWORK');
      const next = await reader.read();
      if (signal.aborted) throw new ComplaintReadClientError('NETWORK');
      if (next.done) break;
      if (next.value.byteLength > body.length - length) throw new ComplaintReadClientError('INVALID_RESPONSE');
      body.set(next.value, length);
      length += next.value.byteLength;
    }
    return body.slice(0, length);
  } catch (error) {
    cancel();
    throw error;
  } finally {
    signal.removeEventListener('abort', cancel);
    reader.releaseLock();
  }
}

function cancelled(): DOMException {
  return new DOMException('Complaint detail request cancelled.', 'AbortError');
}
