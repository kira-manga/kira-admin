import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { GET } from './route';

vi.mock('../../../../lib/server-config', () => ({ backendUrl: 'http://backend.internal:8080' }));

const requestUrl = 'https://admin.example/api/catalog/manifest';
const maximumBodyBytes = 1_048_576;
const fetchMock = vi.fn<typeof fetch>();
const fixture = new TextEncoder().encode('{\n  "catalogRevision": 7, "sources": [{"api": "漫画"}]\n}\n');
const publicHeaders = {
  'Content-Type': 'application/json; charset=UTF-8',
  ETag: '"manifest-checksum"',
  'X-Config-Revision': '7',
  'X-Config-Checksum': 'manifest-checksum',
  'X-Config-Signature-Format': 'kira-source-catalog-manifest-v1',
  'X-Config-Signature-Algorithm': 'Ed25519',
  'X-Config-Signing-Key-Id': 'test-key',
  'X-Config-Signature': 'test-signature',
  'X-Config-Previous-Revision': '6',
  'X-Config-Previous-Checksum': 'previous-checksum',
  'X-Config-Created-At': '2026-09-09T00:00:00Z',
};

function openBody(chunks: Uint8Array[] = [], cancel = vi.fn()) {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk);
    },
    cancel,
  });
  return { body, cancel };
}

function expectLocalHeaders(response: Response) {
  expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
  expect(response.headers.get('x-content-type-options')).toBe('nosniff');
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('fixed public live catalog route', () => {
  it('uses the real v2 mapping with no credentials and preserves bytes and only public headers', async () => {
    const upstream = new Response(fixture, {
      headers: {
        ...publicHeaders,
        'Cache-Control': 'public, max-age=300',
        'Content-Length': '1',
        'Content-Encoding': 'gzip',
        'Set-Cookie': 'private=secret',
        Location: 'http://backend.internal:8080/private',
        'X-Config-Unrecognized': 'private',
        'X-Private': 'secret',
        'X-Content-Type-Options': 'wrong',
      },
    });
    fetchMock.mockResolvedValue(upstream);
    const response = await GET(new Request(requestUrl + '?url=https://attacker.example&path=/api/v1/admin/sources', {
      headers: {
        Authorization: 'Bearer secret',
        Cookie: 'kira_admin_session=secret',
        'X-Kira-Admin-Step-Up': 'secret',
        'X-Kira-Csrf': 'secret',
        Host: 'attacker.example',
        'X-Arbitrary': 'secret',
        Accept: 'text/html',
        'Cache-Control': 'only-if-cached',
        'If-None-Match': '"previous"',
      },
    }));

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://backend.internal:8080/api/v2/source-config/manifest');
    expect(options).toMatchObject({ method: 'GET', credentials: 'omit', cache: 'no-store', redirect: 'error' });
    expect([...new Headers(options?.headers)]).toEqual([
      ['accept', 'application/json'],
      ['cache-control', 'no-cache'],
      ['if-none-match', '"previous"'],
    ]);
    expect(response.status).toBe(200);
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(fixture);
    for (const [name, value] of Object.entries(publicHeaders)) expect(response.headers.get(name)).toBe(value);
    for (const name of ['set-cookie', 'location', 'content-length', 'content-encoding', 'x-config-unrecognized', 'x-private']) {
      expect(response.headers.get(name)).toBeNull();
    }
    expectLocalHeaders(response);
    expect(upstream.body?.locked).toBe(false);
  });

  it('accepts a bodiless 304 without Content-Type and retains its integrity metadata', async () => {
    const headers = new Headers(publicHeaders);
    headers.delete('content-type');
    fetchMock.mockResolvedValue(new Response(null, { status: 304, headers }));
    const response = await GET(new Request(requestUrl));
    expect(response.status).toBe(304);
    expect(response.body).toBeNull();
    expect(response.headers.get('content-type')).toBeNull();
    expect(response.headers.get('etag')).toBe(publicHeaders.ETag);
    expect(response.headers.get('x-config-signature')).toBe(publicHeaders['X-Config-Signature']);
    expectLocalHeaders(response);
  });

  it('accepts exactly 1 MiB of decoded bytes regardless of a falsely small encoded length', async () => {
    const bytes = new Uint8Array(maximumBodyBytes).fill(32);
    bytes.set(new TextEncoder().encode('{}'));
    fetchMock.mockResolvedValue(new Response(bytes, {
      headers: { 'Content-Type': 'application/json', 'Content-Length': '1', 'Content-Encoding': 'gzip' },
    }));
    const response = await GET(new Request(requestUrl));
    expect(response.status).toBe(200);
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(bytes);
    expect(response.headers.get('content-length')).toBeNull();
    expect(response.headers.get('content-encoding')).toBeNull();
  });

  it.each([undefined, '1'])('cancels a streamed 1 MiB+1 response with Content-Length %s before returning any signed bytes', async (length) => {
    const { body, cancel } = openBody([new Uint8Array(maximumBodyBytes - 1), new Uint8Array(2)]);
    const headers = new Headers(publicHeaders);
    if (length !== undefined) headers.set('Content-Length', length);
    fetchMock.mockResolvedValue(new Response(body, { headers }));
    const response = await GET(new Request(requestUrl));

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'The live catalog could not be loaded.' });
    expect(response.headers.get('etag')).toBeNull();
    expect(response.headers.get('x-config-signature')).toBeNull();
    expect(cancel).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][1]?.signal?.aborted).toBe(true);
    expect(body.locked).toBe(false);
    expectLocalHeaders(response);
  });

  it.each([
    [302, 'application/json', 502],
    [200, 'text/html', 502],
    [206, 'application/json', 502],
    [202, 'application/json', 502],
    [404, 'application/problem+json', 404],
    [503, 'application/problem+json', 502],
  ])('sanitizes upstream %s/%s and cancels without reading the error body', async (status, type, expected) => {
    const { body, cancel } = openBody([new TextEncoder().encode('http://backend.internal:8080 private secret')]);
    const getReader = vi.spyOn(body, 'getReader');
    fetchMock.mockResolvedValue(new Response(body, {
      status: Number(status),
      headers: { ...publicHeaders, 'Content-Type': String(type), Location: 'http://backend.internal:8080/private' },
    }));
    const response = await GET(new Request(requestUrl));

    expect(response.status).toBe(expected);
    expect(await response.json()).toEqual({
      detail: expected === 404 ? 'The live catalog is not available.' : 'The live catalog could not be loaded.',
    });
    expect(getReader).not.toHaveBeenCalled();
    expect(cancel).toHaveBeenCalledOnce();
    for (const name of ['etag', 'x-config-signature', 'location']) expect(response.headers.get(name)).toBeNull();
    expectLocalHeaders(response);
  });

  it('keeps cleanup rejection from replacing a sanitized error', async () => {
    const cancel = vi.fn(() => Promise.reject(new Error('http://backend.internal:8080 private cleanup')));
    const { body } = openBody([], cancel);
    fetchMock.mockResolvedValue(new Response(body, { status: 503 }));
    const response = await GET(new Request(requestUrl));
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'The live catalog could not be loaded.' });
    expect(cancel).toHaveBeenCalledOnce();
  });

  it('sanitizes a transport failure without exposing the configured origin', async () => {
    fetchMock.mockRejectedValue(new Error('http://backend.internal:8080 secret'));
    const response = await GET(new Request(requestUrl));
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'The live catalog could not be loaded.' });
    expectLocalHeaders(response);
  });

  it('treats a non-deadline body AbortError as 502 and releases the reader', async () => {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.error(new DOMException('private upstream failure', 'AbortError'));
      },
    });
    fetchMock.mockResolvedValue(new Response(body, { headers: publicHeaders }));
    const response = await GET(new Request(requestUrl));
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'The live catalog could not be loaded.' });
    expect(body.locked).toBe(false);
  });

  it('enforces the deadline after headers and cancels a stalled partially read body', async () => {
    vi.useFakeTimers();
    const { body, cancel } = openBody([fixture.subarray(0, 8)]);
    fetchMock.mockResolvedValue(new Response(body, { headers: publicHeaders }));
    const pending = GET(new Request(requestUrl));
    await vi.advanceTimersByTimeAsync(0);
    expect(body.locked).toBe(true);
    await vi.advanceTimersByTimeAsync(10_000);
    const response = await pending;

    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ detail: 'The live catalog request timed out.' });
    expect(response.headers.get('etag')).toBeNull();
    expect(cancel).toHaveBeenCalledOnce();
    expect(body.locked).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
    expectLocalHeaders(response);
  });

  it('cancels body work on caller abort without reporting a backend timeout', async () => {
    vi.useFakeTimers();
    const caller = new AbortController();
    const { body, cancel } = openBody([fixture.subarray(0, 8)]);
    fetchMock.mockResolvedValue(new Response(body, { headers: publicHeaders }));
    const pending = GET(new Request(requestUrl, { signal: caller.signal }));
    await vi.advanceTimersByTimeAsync(0);
    expect(body.locked).toBe(true);
    caller.abort(new DOMException('caller left', 'AbortError'));
    const response = await pending;

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'The live catalog could not be loaded.' });
    expect(cancel).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][1]?.signal?.reason).toBe(caller.signal.reason);
    expect(body.locked).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('does not fetch when the caller is already cancelled', async () => {
    const caller = new AbortController();
    caller.abort();
    const response = await GET(new Request(requestUrl, { signal: caller.signal }));
    expect(response.status).toBe(502);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
