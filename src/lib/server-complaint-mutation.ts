import { NextResponse } from 'next/server';

import { isComplaintBatchPath, isComplaintDetailPath, isComplaintDetailQuery, isComplaintMutationPath } from './admin-route-policy';
import { captureComplaintBatchStatusRequest, ComplaintBatchStatusBodyError, decodeComplaintBatchStatusOutcome } from './complaint-batch-status-wire';
import { complaintReceiptHeader, decodeComplaintMutationOutcome, prepareComplaintMutationRequest, validateComplaintMutationBody, type ComplaintMutationOperation } from './complaint-mutation-wire';
import { backendUrl } from './server-config';
import { requireCsrf, requireSameOrigin } from './server-security';
import { capturedComplaintProofs, readAdminSession, readOptionalComplaintProof, retireConsumedComplaintProof, sessionFailure } from './server-session';
import { isSessionSelector } from './session-contract';

const consumedGrantHeader = 'X-Kira-Admin-Step-Up-Consumed-Grant-Id';
const contractHeader = 'X-Kira-Complaint-Contract';
const jsonMedia = /^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i;

function failure(status: number) {
  return NextResponse.json({ detail: 'Complaint request could not be confirmed. Keep the original operation.' }, {
    status, headers: { 'Content-Type': 'application/problem+json', 'Cache-Control': 'no-store, no-transform', 'X-Content-Type-Options': 'nosniff' },
  });
}

/** One bounded mutation exchange; never activates the backend's closed complaint composition. */
export async function proxyComplaintMutation(request: Request, path: string[]) {
  const url = new URL(request.url);
  const deleting = request.method === 'DELETE' && isComplaintDetailPath(path);
  const batching = request.method === 'POST' && isComplaintBatchPath(path);
  if (!(deleting || batching || request.method === 'PATCH' && isComplaintMutationPath(path)) || url.pathname !== `/api/backend/${path.join('/')}`) return failure(404);
  if (!isComplaintDetailQuery(url.search)) return failure(400);
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return originFailure;
  let session, selectedProof, captured;
  try {
    session = readAdminSession(request.headers);
    const csrfFailure = await requireCsrf(request, session);
    if (csrfFailure) return csrfFailure;
    selectedProof = readOptionalComplaintProof(request.headers, session);
    captured = capturedComplaintProofs(session);
  } catch (error) { return sessionFailure(error); }

  const controller = new AbortController();
  const timeout = new DOMException('Complaint exchange deadline exceeded.', 'TimeoutError');
  const deadline = performance.now() + 65_000;
  const onAbort = () => controller.abort();
  const timer = setTimeout(() => controller.abort(timeout), 65_000);
  request.signal.addEventListener('abort', onAbort, { once: true });
  const tooLarge = new Error('Body bound.');
  let upstream: Response | undefined;
  let dispatched = false;
  const active = () => {
    if (performance.now() >= deadline) controller.abort(timeout);
    controller.signal.throwIfAborted();
  };
  const read = async (message: Request | Response, maximum: number, allowAbsent = false) => {
    const length = message.headers.get('content-length');
    if (length !== null && !/^[0-9]{1,20}$/.test(length)) throw new Error('Invalid length.');
    if (length !== null && Number(length) > maximum) throw tooLarge;
    if (!message.body) {
      active();
      if (!allowAbsent || length !== null && Number(length) !== 0) throw new Error('Missing body.');
      return new Uint8Array(0);
    }
    const reader = message.body.getReader();
    const bytes = new Uint8Array(maximum);
    let size = 0;
    let complete = false;
    const cancel = () => { void reader.cancel().catch(() => {}); };
    controller.signal.addEventListener('abort', cancel, { once: true });
    try {
      while (true) {
        active();
        const next = await reader.read();
        active();
        if (next.done) break;
        if (next.value.byteLength > maximum - size) throw tooLarge;
        bytes.set(next.value, size);
        size += next.value.byteLength;
      }
      if (length !== null && Number(length) !== size) throw new Error('Incorrect length.');
      complete = true;
      return bytes.slice(0, size);
    } finally {
      controller.signal.removeEventListener('abort', cancel);
      if (!complete) cancel();
      reader.releaseLock();
    }
  };

  try {
    if (request.signal.aborted) onAbort();
    active();
    let fields = 0, total = 0;
    for (const [name, value] of request.headers) {
      total += name.length + value.length;
      if (++fields > 128 || total > 32_768 || name.length > 128 || value.length > 16_384) return failure(431);
    }
    const media = request.headers.get('content-type');
    const encoding = request.headers.get('content-encoding');
    if (media === null ? !deleting : media.length > 128 || /[\r\n]/.test(media) || !jsonMedia.test(media)) return failure(415);
    if (encoding !== null && encoding.toLowerCase() !== 'identity') return failure(415);
    const transfer = request.headers.get('transfer-encoding');
    if (transfer !== null && (transfer.toLowerCase() !== 'chunked' || request.headers.has('content-length'))
      || request.headers.has('if-none-match') || request.headers.get(contractHeader) !== '1') return failure(400);
    const key = request.headers.get('X-Kira-Idempotency-Key');
    if (!isSessionSelector(key)) return failure(400);
    const tag = request.headers.get('if-match');
    if (batching && tag !== null) return failure(400); // A batch never has an aggregate conditional tag.
    if (!batching && tag === null) return failure(428);
    const operation: ComplaintMutationOperation = deleting ? 'delete' : path[2] as ComplaintMutationOperation;
    const scope = url.search.slice('?dataScopeId='.length);
    if (!batching) {
      try { prepareComplaintMutationRequest(operation, path[1], scope, key, tag!, deleting ? '' : '{}'); } catch { return failure(412); }
    }
    const bytes = await read(request, deleting ? 0 : batching ? 32_768 : 16_384, deleting);
    const body = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
    if (!batching) validateComplaintMutationBody(operation, body);
    const description = batching ? captureComplaintBatchStatusRequest(body, scope, key) : prepareComplaintMutationRequest(operation, path[1], scope, key, tag!, body);
    const headers = new Headers({ ...description.headers,
      Authorization: `Bearer ${session.token}`, Accept: 'application/json, application/problem+json', 'Accept-Encoding': 'identity',
    });
    if (selectedProof) headers.set('X-Kira-Admin-Step-Up', selectedProof.token);
    active();
    dispatched = true;
    upstream = await fetch(`${backendUrl}${description.path}`, {
      method: description.method, headers, body: deleting ? undefined : body, cache: 'no-store', redirect: 'manual', signal: controller.signal,
    });
    active();
    const upstreamEncoding = upstream.headers.get('content-encoding');
    const upstreamTransfer = upstream.headers.get('transfer-encoding');
    if (upstream.redirected || upstream.status >= 300 && upstream.status < 400
      || upstreamEncoding !== null && upstreamEncoding.toLowerCase() !== 'identity'
      || upstreamTransfer !== null && (upstream.status === 204 || upstreamTransfer.toLowerCase() !== 'chunked' || upstream.headers.has('content-length'))) return failure(502);
    const emptyDeletion = deleting && upstream.status === 204;
    const responseBytes = await read(upstream, emptyDeletion ? 0 : 32_768, emptyDeletion);
    const consumed = upstream.headers.get(complaintReceiptHeader);
    const grantId = upstream.headers.get(consumedGrantHeader);
    if (grantId !== null && (!isSessionSelector(grantId) || consumed !== 'true')) return failure(502);
    const metadata = {
      status: upstream.status, contentType: upstream.headers.get('content-type'), contract: upstream.headers.get(contractHeader),
      etag: upstream.headers.get('etag'), consumed, challenge: upstream.headers.get('www-authenticate'),
      retryAfter: upstream.headers.get('retry-after'), location: upstream.headers.get('location'), body: responseBytes,
    };
    // Complete exact single ACK or entire sorted batch ACK before downstream bytes or proof retirement.
    if (description.method === 'POST') decodeComplaintBatchStatusOutcome(description, metadata);
    else decodeComplaintMutationOutcome(description, metadata);
    active();
    const outputHeaders = new Headers({ [contractHeader]: '1',
      'Cache-Control': 'no-store, no-transform', 'X-Content-Type-Options': 'nosniff',
    });
    if (metadata.contentType !== null) outputHeaders.set('Content-Type', metadata.contentType);
    for (const [name, value] of [['ETag', metadata.etag], ['WWW-Authenticate', metadata.challenge],
      ['Retry-After', metadata.retryAfter], [complaintReceiptHeader, consumed]] as const) {
      if (value !== null) outputHeaders.set(name, value);
    }
    const response = new NextResponse(emptyDeletion ? null : responseBytes, { status: upstream.status, headers: outputHeaders });
    // Consumption is independent of HTTP success. A complete post-receipt503 still leaves the operation unknown.
    if (consumed === 'true') retireConsumedComplaintProof(response, captured, grantId);
    return response;
  } catch (error) {
    if (controller.signal.aborted) return failure(controller.signal.reason === timeout ? 504 : 502);
    if (error instanceof DOMException && error.name === 'TimeoutError') return failure(504);
    return failure(dispatched ? 502 : error === tooLarge && !deleting ? 413 : error instanceof ComplaintBatchStatusBodyError ? error.status : 400);
  } finally {
    clearTimeout(timer);
    request.signal.removeEventListener('abort', onAbort);
    controller.abort();
    if (!request.bodyUsed) void request.body?.cancel().catch(() => {});
    if (upstream && !upstream.bodyUsed) void upstream.body?.cancel().catch(() => {});
  }
}
