import { backendUrl } from '../../../../lib/server-config';

const manifestPath = '/api/v2/source-config/manifest';
const maximumBodyBytes = 1_048_576;
const timeoutMs = 10_000;
const manifestHeaders = [
  'content-type',
  'etag',
  'x-config-revision',
  'x-config-checksum',
  'x-config-signature-format',
  'x-config-signature-algorithm',
  'x-config-signing-key-id',
  'x-config-signature',
  'x-config-previous-revision',
  'x-config-previous-checksum',
  'x-config-created-at',
];

function responseHeaders(upstream?: Response) {
  const headers = new Headers({
    'Cache-Control': 'no-store, no-transform',
    'X-Content-Type-Options': 'nosniff',
  });
  for (const name of manifestHeaders) {
    const value = upstream?.headers.get(name);
    if (value != null) headers.set(name, value);
  }
  return headers;
}

function unavailable(status: 404 | 502 | 504) {
  const detail = status === 404
    ? 'The live catalog is not available.'
    : status === 504
      ? 'The live catalog request timed out.'
      : 'The live catalog could not be loaded.';
  return Response.json({ detail }, { status, headers: responseHeaders() });
}

export async function GET(request: Request): Promise<Response> {
  const controller = new AbortController();
  const deadlineReason = new DOMException('Live catalog deadline exceeded.', 'TimeoutError');
  const deadline = performance.now() + timeoutMs;
  let upstream: Response | undefined;
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let consumed = false;
  let cancellationRequested = false;

  const cancelBody = () => {
    const body = reader ?? upstream?.body;
    if (!body || consumed || cancellationRequested) return;
    cancellationRequested = true;
    try {
      // Do not wait for an uncooperative cancellation promise or leak its rejection.
      void body.cancel().catch(() => {});
    } catch {
      // Cleanup must not replace a bounded local error response.
    }
  };
  const onCallerAbort = () => controller.abort(request.signal.reason);
  const checkActive = () => {
    // Also check the absolute fence if many ready chunks delay the timer callback.
    if (performance.now() >= deadline) controller.abort(deadlineReason);
    controller.signal.throwIfAborted();
  };
  controller.signal.addEventListener('abort', cancelBody, { once: true });
  request.signal.addEventListener('abort', onCallerAbort, { once: true });
  const timer = setTimeout(() => controller.abort(deadlineReason), timeoutMs);

  try {
    if (request.signal.aborted) onCallerAbort();
    checkActive();
    const headers = new Headers({
      Accept: 'application/json',
      'Cache-Control': 'no-cache',
    });
    const etag = request.headers.get('if-none-match');
    if (etag != null) headers.set('If-None-Match', etag);

    upstream = await fetch(backendUrl + manifestPath, {
      method: 'GET',
      headers,
      credentials: 'omit',
      cache: 'no-store',
      redirect: 'error',
      signal: controller.signal,
    });
    checkActive();
    // The canonical writer intentionally omits Content-Type on a 304.
    if (upstream.status === 304) {
      return new Response(null, { status: 304, headers: responseHeaders(upstream) });
    }
    if (upstream.status === 404) return unavailable(404);
    const mediaType = upstream.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
    if (upstream.status !== 200 || mediaType !== 'application/json' || !upstream.body) {
      return unavailable(502);
    }

    // Proxy-local decoded-byte budget, not a backend publication-size limit.
    // One fixed buffer avoids unbounded chunk-list bookkeeping or retained backing buffers.
    const bytes = new Uint8Array(maximumBodyBytes);
    let size = 0;
    reader = upstream.body.getReader();
    while (true) {
      checkActive();
      const chunk = await reader.read();
      checkActive();
      if (chunk.done) break;
      if (chunk.value.byteLength > maximumBodyBytes - size) return unavailable(502);
      bytes.set(chunk.value, size);
      size += chunk.value.byteLength;
    }
    consumed = true;
    return new Response(bytes.subarray(0, size), { status: 200, headers: responseHeaders(upstream) });
  } catch {
    // Body failures can be AbortError even when the deadline caused the abort.
    return unavailable(controller.signal.reason === deadlineReason ? 504 : 502);
  } finally {
    clearTimeout(timer);
    request.signal.removeEventListener('abort', onCallerAbort);
    controller.signal.removeEventListener('abort', cancelBody);
    if (!consumed) {
      controller.abort();
      cancelBody();
    }
    try {
      reader?.releaseLock();
    } catch {
      // The response remains sanitized even if disposal itself fails.
    }
  }
}
