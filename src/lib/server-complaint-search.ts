import { isComplaintSearchPath } from './admin-route-policy';
import { decodeComplaintAdminPage } from './complaint-read-wire';
import { parseComplaintAdminSearchBody } from './complaint-search-wire';
import { backendUrl } from './server-config';
import { requireCsrf, requireSameOrigin } from './server-security';
import { readAdminSession, sessionFailure } from './server-session';

const contractHeader = 'X-Kira-Complaint-Contract';
const jsonMedia = /^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i;
// Resource admission only, never a session/authorization registry. One owner for this large route.
let activeResponses = 0;

function failure(status: number, retry: string | null = null) {
  return Response.json({ detail: 'Complaint search could not be loaded. Restart the search if its cursor is no longer valid.' }, {
    status, headers: { 'Content-Type': 'application/problem+json', 'Cache-Control': 'no-store, no-transform',
      'X-Content-Type-Options': 'nosniff',
      ...([429, 503].includes(status) && retry !== null && /^[1-9][0-9]{0,5}$/.test(retry) ? { 'Retry-After': retry } : {}),
    },
  });
}

function cancelUnused(message: Request | Response | undefined) {
  if (message && !message.bodyUsed) void message.body?.cancel().catch(() => {});
}

function reject(request: Request, status: number) { cancelUnused(request); return failure(status); }

/** Closed TEST search exchange. No proof, mutation authority, cache or backend activation. */
export async function proxyComplaintSearch(request: Request, path: string[]) {
  const url = new URL(request.url);
  if (request.method !== 'POST' || !isComplaintSearchPath(path) || url.pathname !== '/api/backend/complaints/search') return reject(request, 404);
  if (url.search || request.url.includes('?')) return reject(request, 400);
  let fields = 0, total = 0;
  for (const [name, value] of request.headers) {
    total += name.length + value.length;
    if (++fields > 128 || total > 32_768 || name.length > 128 || value.length > 16_384) return reject(request, 431);
  }
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return reject(request, originFailure.status);
  let session;
  try {
    session = readAdminSession(request.headers);
    const csrfFailure = await requireCsrf(request, session);
    if (csrfFailure) return reject(request, csrfFailure.status);
  } catch (error) { cancelUnused(request); return sessionFailure(error); }
  const media = request.headers.get('content-type'), encoding = request.headers.get('content-encoding');
  if (!media || media.length > 128 || /[\r\n]/.test(media) || !jsonMedia.test(media)
    || encoding !== null && encoding.toLowerCase() !== 'identity') return reject(request, 415);
  const transfer = request.headers.get('transfer-encoding');
  if (transfer !== null && (transfer.toLowerCase() !== 'chunked' || request.headers.has('content-length'))
    || request.headers.get(contractHeader) !== '1'
    || ['if-match', 'if-none-match', 'x-kira-idempotency-key'].some((name) => request.headers.has(name))) return reject(request, 400);
  if (activeResponses >= 8) return reject(request, 503); // Before inbound allocation or upstream fetch.
  activeResponses++;

  const controller = new AbortController();
  const timeout = new DOMException('Complaint search deadline exceeded.', 'TimeoutError');
  const deadline = performance.now() + 65_000;
  const onAbort = () => controller.abort();
  const timer = setTimeout(() => controller.abort(timeout), 65_000);
  request.signal.addEventListener('abort', onAbort, { once: true });
  let upstream: Response | undefined;
  let dispatched = false, handedOff = false, finished = false;
  let owned: Uint8Array<ArrayBuffer> | undefined;
  let delivery: ReadableStreamDefaultController<Uint8Array> | undefined;
  const tooLarge = new Error('Complaint body bound.');
  const active = () => {
    if (performance.now() >= deadline) controller.abort(timeout);
    controller.signal.throwIfAborted();
  };
  const finish = () => {
    if (finished) return;
    finished = true;
    clearTimeout(timer);
    request.signal.removeEventListener('abort', onAbort);
    controller.signal.removeEventListener('abort', abortDelivery);
    owned?.fill(0); owned = undefined; delivery = undefined;
    controller.abort();
    cancelUnused(request); cancelUnused(upstream);
    activeResponses--;
  };
  const abortDelivery = () => {
    if (!delivery) return; // Acquisition's finally, not an early release, owns its still-live buffer.
    delivery.error(new Error('Complaint search delivery interrupted.'));
    finish();
  };
  const read = async (message: Request | Response, maximum: number) => {
    const length = message.headers.get('content-length');
    if (length !== null && !/^[0-9]{1,20}$/.test(length)) throw new Error('Invalid length.');
    if (length !== null && Number(length) > maximum) throw tooLarge;
    if (!message.body) throw new Error('Missing body.');
    const reader = message.body.getReader();
    const bytes = new Uint8Array(maximum);
    let size = 0, complete = false;
    const cancel = () => { void reader.cancel().catch(() => {}); };
    controller.signal.addEventListener('abort', cancel, { once: true });
    try {
      while (true) {
        active();
        const next = await reader.read();
        active();
        if (next.done) break;
        if (next.value.byteLength > maximum - size) throw tooLarge;
        bytes.set(next.value, size); size += next.value.byteLength;
      }
      if (length !== null && Number(length) !== size) throw new Error('Incorrect length.');
      complete = true;
      return bytes.subarray(0, size);
    } finally {
      controller.signal.removeEventListener('abort', cancel);
      if (!complete) { cancel(); bytes.fill(0); }
      reader.releaseLock();
    }
  };

  try {
    if (request.signal.aborted) onAbort();
    active();
    const input = await read(request, 32_768);
    const query = parseComplaintAdminSearchBody(input);
    const headers = new Headers({ Authorization: `Bearer ${session.token}`, 'Content-Type': 'application/json',
      Accept: 'application/json, application/problem+json', 'Accept-Encoding': 'identity', [contractHeader]: '1',
    });
    active();
    dispatched = true;
    upstream = await fetch(`${backendUrl}/api/v1/admin/complaints/search`, {
      method: 'POST', headers, body: input, cache: 'no-store', redirect: 'manual', signal: controller.signal,
    });
    active();
    const upstreamEncoding = upstream.headers.get('content-encoding'), upstreamTransfer = upstream.headers.get('transfer-encoding');
    if (upstream.redirected || upstream.status >= 300 && upstream.status < 400
      || upstreamEncoding !== null && upstreamEncoding.toLowerCase() !== 'identity'
      || upstreamTransfer !== null && (upstreamTransfer.toLowerCase() !== 'chunked' || upstream.headers.has('content-length'))) return failure(502);
    if (upstream.status !== 200) {
      // No upstream problem bytes or challenge (including a forged local KiraSession) cross this read boundary.
      // Local problems are fixed and far below32KiB; proofs/session cookies are never changed by a search.
      return failure([400, 401, 403, 404, 413, 415, 429, 500, 503].includes(upstream.status) ? upstream.status : 502, upstream.headers.get('retry-after'));
    }
    owned = await read(upstream, 2_097_152);
    decodeComplaintAdminPage(query.limit, { status: upstream.status, contentType: upstream.headers.get('content-type'),
      contract: upstream.headers.get(contractHeader), etag: upstream.headers.get('etag'), body: owned,
    }); // Validate the entire envelope/items before constructing any downstream200 response.
    active();
    let offset = 0;
    const body = new ReadableStream<Uint8Array>({
      start(output) { delivery = output; controller.signal.addEventListener('abort', abortDelivery, { once: true }); },
      pull(output) {
        try {
          active();
          if (!owned || offset === owned.byteLength) { output.close(); finish(); return; }
          const end = Math.min(offset + 16_384, owned.byteLength);
          // A paused downstream reader cannot retain our full2MiB backing allocation through one chunk.
          output.enqueue(owned.slice(offset, end)); offset = end;
        } catch { abortDelivery(); }
      },
      cancel() { finish(); },
    }, { highWaterMark: 0 });
    const response = new Response(body, { status: 200, headers: { 'Content-Type': 'application/json;charset=UTF-8',
      [contractHeader]: '1', 'Cache-Control': 'no-store, no-transform', 'X-Content-Type-Options': 'nosniff',
    } });
    handedOff = true;
    return response;
  } catch (error) {
    if (controller.signal.aborted) return failure(controller.signal.reason === timeout ? 504 : 502);
    return failure(dispatched ? 502 : error === tooLarge ? 413 : 400);
  } finally {
    // A completed200 still owns its slot/buffer until downstream EOF, cancellation or the absolute deadline.
    if (!handedOff) finish();
  }
}
