import { Buffer } from 'node:buffer';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { issueAdminProof, type AdminProofCookie, type AdminSessionCookie } from '@/lib/server-session';
import { sessionGenerationHeader } from '@/lib/session-contract';
import { complaintId, complaintScope } from '@/test/complaint-mutation-fixture';
import { searchContent, searchPage, searchResponse, searchVersion } from '@/test/complaint-search-fixture';
import { statsDocument, statsFixture, statsResponse } from '@/test/complaint-stats-fixture';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';

// Real route, parser, signed selected session and the one shared response owner; only fetch is replaced.
type ReadKind = 'search' | 'stats' | 'detail';
const mixedReads: ReadKind[] = ['stats', 'search', 'detail', 'stats', 'search', 'detail', 'stats', 'search'];
const fetchMock = vi.fn<typeof fetch>();
const bytes = (value: string) => new TextEncoder().encode(value);
let session: AdminSessionCookie;
let proofs: AdminProofCookie[];
let outputs: Response[];
let requests: AbortController[];

function readResponse(kind: ReadKind, padding = 0) {
  const suffix = ' '.repeat(padding);
  if (kind === 'stats') return statsResponse(statsDocument() + suffix);
  if (kind === 'search') return searchResponse(searchPage() + suffix);
  return searchResponse(searchContent() + suffix, 200, { ETag: `"complaint-${complaintId}-v${searchVersion}"` });
}

async function invoke(kind: ReadKind = 'stats', options: {
  headers?: HeadersInit; remove?: string[]; query?: string; pathname?: string; path?: string[];
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'; signal?: AbortSignal; syntheticGetBody?: ReadableStream<Uint8Array>;
} = {}) {
  const path = options.path ?? ['complaints', kind === 'detail' ? complaintId : kind];
  const method = options.method ?? (kind === 'search' ? 'POST' : 'GET');
  const headers = signedRequestHeaders(session, proofs, { 'X-Kira-Complaint-Contract': '1',
    Authorization: 'Bearer caller-override', 'X-Kira-Admin-Step-Up': 'caller-proof-override' });
  for (const [name, value] of new Headers(options.headers)) headers.set(name, value);
  options.remove?.forEach((name) => headers.delete(name));
  const controller = new AbortController(); requests.push(controller);
  const request = new Request(`https://admin.example.test${options.pathname ?? `/api/backend/${path.join('/')}`}${options.query ?? (kind === 'search' ? '' : `?dataScopeId=${complaintScope}`)}`, {
    method, headers, signal: options.signal ? AbortSignal.any([controller.signal, options.signal]) : controller.signal,
    ...(method === 'POST' ? { body: `{"dataScopeId":"${complaintScope}"}` } : {}),
  });
  // Native Request refuses GET bodies; exercise the server's defensive guard for a non-native adapter.
  if (options.syntheticGetBody) Object.defineProperty(request, 'body', { value: options.syntheticGetBody });
  const handlers = await import('./route');
  const response = await handlers[method](request, { params: Promise.resolve({ path }) });
  outputs.push(response);
  return response;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  vi.resetModules();
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_ORIGIN', 'https://admin.example.test');
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  session = createSessionFixture();
  proofs = ['source-admin-mutation', 'complaint-moderation-mutation'].map((scope) => issueAdminProof(session, 'A'.repeat(43), scope as AdminProofCookie['scope'], new Date(Date.now() + 300_000).toISOString(), null));
  outputs = []; requests = []; fetchMock.mockReset(); vi.stubGlobal('fetch', fetchMock);
});
afterEach(async () => {
  requests.forEach((request) => request.abort());
  for (const response of outputs) await response.body?.cancel().catch(() => {});
  vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs();
});

describe('actual bounded scope statistics BFF and shared read custody', () => {
  it('uses only the fixed scoped GET and signed G, preserving raw Long bytes without requesting approval or forwarding private metadata', async () => {
    const raw = statsDocument();
    fetchMock.mockResolvedValue(statsResponse(raw, 200, { 'Set-Cookie': 'private=never', Authorization: 'private',
      'X-Kira-Admin-Step-Up': 'private', 'X-Kira-Admin-Step-Up-Consumed': 'true', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': complaintScope,
      'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"', Location: 'https://private.example', 'Content-Length': String(bytes(raw).length) }));
    const before = [session.value, ...proofs.map((proof) => proof.value)];
    const response = await invoke('stats', { remove: ['Origin', 'Sec-Fetch-Site', 'X-Kira-CSRF', 'Content-Type'] });
    expect(response.status).toBe(200);
    expect(await response.text()).toBe(raw);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/stats?dataScopeId=${complaintScope}`);
    expect(init).toMatchObject({ method: 'GET', cache: 'no-store', redirect: 'manual', signal: expect.any(AbortSignal) });
    expect(init?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({ authorization: `Bearer ${session.token}`,
      accept: 'application/json, application/problem+json', 'accept-encoding': 'identity', 'x-kira-complaint-contract': '1' });
    expect(Object.fromEntries(response.headers)).toEqual({ 'content-type': 'application/json;charset=UTF-8', 'x-kira-complaint-contract': '1',
      'cache-control': 'no-store, no-transform', 'x-content-type-options': 'nosniff' });
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect([session.value, ...proofs.map((proof) => proof.value)]).toEqual(before);
    expect(fetchMock).toHaveBeenCalledOnce(); expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects aliases, non-TEST or extra queries, missing G, contract/body/framing and mutation headers before any upstream work', async () => {
    const cases: Array<[Parameters<typeof invoke>[1], number]> = [
      [{ pathname: '/api/backend/complaints/st%61ts' }, 404], [{ path: ['complaints', 'Stats'] }, 404],
      [{ path: ['complaints', 'stats', 'detail'] }, 404], [{ method: 'POST' }, 404], [{ method: 'PATCH' }, 404], [{ method: 'DELETE' }, 404],
      [{ query: '' }, 400], [{ query: '?' }, 400], [{ query: '?dataScopeId=00000000-0000-0000-0000-000000000000' }, 400],
      [{ query: '?dataScopeId=ABCDEFAB-1234-4234-8234-123456789ABC' }, 400],
      [{ query: `?dataScopeId=%32${complaintScope.slice(1)}` }, 400], [{ query: `?dataScopeId=${complaintScope}&dataScopeId=${complaintScope}` }, 400],
      ...['text=private', 'status=OPEN', 'cursor=private', 'limit=50', 'sort=UPDATED_DESC'].map((extra) => [{ query: `?dataScopeId=${complaintScope}&${extra}` }, 400] as [Parameters<typeof invoke>[1], number]),
      [{ remove: [sessionGenerationHeader] }, 401], [{ remove: ['Cookie'] }, 401],
      [{ remove: ['X-Kira-Complaint-Contract'] }, 400], [{ headers: { 'X-Kira-Complaint-Contract': '1, 1' } }, 400],
      [{ headers: { 'If-Match': 'not-stats' } }, 400], [{ headers: { 'If-None-Match': '*' } }, 400],
      [{ headers: { 'X-Kira-Idempotency-Key': complaintScope } }, 400], [{ headers: { 'Content-Length': '1' } }, 400],
      [{ headers: { 'Content-Length': '0, 0' } }, 400], [{ headers: { 'Transfer-Encoding': 'chunked' } }, 400],
      [{ headers: { 'Content-Encoding': 'gzip' } }, 415],
      [{ headers: new Headers(Array.from({ length: 129 }, (_, index) => [`X-Test-${index}`, 'bounded'] as [string, string])) }, 431],
    ];
    for (const [options, status] of cases) expect((await invoke('stats', options)).status).toBe(status);
    const cancel = vi.fn();
    expect((await invoke('stats', { syntheticGetBody: new ReadableStream({ cancel }) })).status).toBe(400);
    expect(cancel).toHaveBeenCalledOnce();
    const local = await invoke('stats', { remove: [sessionGenerationHeader] });
    expect(local.headers.get('WWW-Authenticate')).toBe('KiraSession realm="kira-admin-bff"');
    expect(fetchMock).not.toHaveBeenCalled(); expect(vi.getTimerCount()).toBe(0);
  });

  it('accepts the actual2MiB stats ceiling with complete byte equality, not the smaller detail ceiling or an equality sample', async () => {
    const raw = statsDocument(), expected = bytes(raw + ' '.repeat(2_097_152 - bytes(raw).length));
    fetchMock.mockResolvedValue(statsResponse(expected, 200, { 'Content-Length': String(expected.length) }));
    const response = await invoke();
    expect(response.status).toBe(200);
    const actual = Buffer.from(await response.arrayBuffer());
    expect(actual.byteLength).toBe(2_097_152); expect(actual.equals(expected)).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('withholds oversized, contradictory, redirected and invalid entire responses without exposing a partial200', async () => {
    const raw = statsDocument();
    const foreign = statsFixture(); foreign.dataScopeId = '33333333-3333-4333-8333-333333333333';
    for (const mode of ['overflow', 'false-length', 'encoded', 'transfer-length', 'redirect', 'followed-redirect', 'contract', 'etag', 'media', 'shape', 'scope', 'utf8']) {
      const cancel = vi.fn();
      let upstream = statsResponse(raw);
      if (mode === 'overflow') upstream = statsResponse(new ReadableStream({ start(output) {
        output.enqueue(bytes(raw + ' '.repeat(2_097_152 - bytes(raw).length))); output.enqueue(bytes(' '));
      }, cancel }));
      if (mode === 'false-length') upstream.headers.set('Content-Length', '1');
      if (mode === 'encoded') upstream = statsResponse(new ReadableStream({ start(output) { output.enqueue(bytes('private compressed body')); }, cancel }), 200, { 'Content-Encoding': 'gzip' });
      if (mode === 'transfer-length') { upstream.headers.set('Transfer-Encoding', 'chunked'); upstream.headers.set('Content-Length', String(bytes(raw).length)); }
      if (mode === 'redirect') upstream = statsResponse(null, 302, { Location: 'https://private.example' });
      if (mode === 'followed-redirect') Object.defineProperty(upstream, 'redirected', { value: true });
      if (mode === 'contract') upstream.headers.set('X-Kira-Complaint-Contract', '1, 1');
      if (mode === 'etag') upstream.headers.set('ETag', 'not-a-detail');
      if (mode === 'media') upstream.headers.set('Content-Type', 'text/html');
      if (mode === 'shape') upstream = statsResponse(raw.slice(0, -1) + ',"actionTag":"private unvalidated field"}');
      if (mode === 'scope') upstream = statsResponse(statsDocument(foreign));
      if (mode === 'utf8') upstream = statsResponse(new Uint8Array([0xc0, 0xaf]));
      fetchMock.mockResolvedValueOnce(upstream);
      const response = await invoke();
      expect(response.status, mode).toBe(502);
      expect(await response.text()).not.toMatch(/private|"total"|"byStatus"|"actionTag"/);
      expect(response.headers.getSetCookie()).toHaveLength(0);
      if (mode === 'overflow' || mode === 'encoded') expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('strips forged local401 challenges and private errors without retiring either scoped P or G, and bounds retry metadata', async () => {
    for (const challenge of [null, 'Bearer realm="kira-complaints"', 'KiraSession realm="kira-admin-bff"']) {
      const cancel = vi.fn();
      fetchMock.mockResolvedValueOnce(statsResponse(new ReadableStream({ start(output) { output.enqueue(bytes('private stats failure')); }, cancel }), 401,
        { 'Set-Cookie': 'retire-something=never', 'X-Kira-Admin-Step-Up-Consumed': 'true', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': complaintScope,
          ...(challenge ? { 'WWW-Authenticate': challenge } : {}) }));
      const response = await invoke();
      expect(response.status).toBe(401);
      expect(response.headers.get('WWW-Authenticate')).toBeNull(); expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(response.headers.has('X-Kira-Admin-Step-Up-Consumed-Grant-Id')).toBe(false);
      expect(await response.text()).not.toContain('private'); expect(cancel).toHaveBeenCalledOnce();
    }
    for (const retry of ['1', '999999', '0', '01', '1000000', '1, 2', 'Fri, 20 Sep 2026 00:00:00 GMT']) {
      for (const status of [429, 503]) {
        fetchMock.mockResolvedValueOnce(statsResponse('private capacity detail', status, { 'Retry-After': retry }));
        const response = await invoke();
        expect(response.status).toBe(status);
        expect(response.headers.get('Retry-After')).toBe(['1', '999999'].includes(retry) ? retry : null);
        expect(await response.text()).not.toContain('private');
      }
    }
    expect(proofs.map((proof) => proof.scope)).toEqual(['source-admin-mutation', 'complaint-moderation-mutation']);
    for (const [, init] of fetchMock.mock.calls) expect(new Headers(init?.headers).get('Authorization')).toBe(`Bearer ${session.token}`);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('admits only eight mixed pending search, stats and detail exchanges, rejecting any ninth read before fetch', async () => {
    const ready = deferred<void>();
    const releases: Array<{ kind: ReadKind; resolve: (response: Response) => void }> = [];
    fetchMock.mockImplementation((url, init) => new Promise<Response>((resolve, reject) => {
      const kind = String(url).includes('/search') ? 'search' : String(url).includes('/stats') ? 'stats' : 'detail';
      releases.push({ kind, resolve });
      init?.signal?.addEventListener('abort', () => reject(new Error('private abort')), { once: true });
      if (releases.length === 8) ready.resolve();
    }));
    const pending = mixedReads.map((kind) => invoke(kind));
    await ready.promise;
    for (const kind of ['stats', 'search', 'detail'] as const) expect((await invoke(kind)).status).toBe(503);
    expect(fetchMock).toHaveBeenCalledTimes(8);
    releases.forEach(({ kind, resolve }) => resolve(readResponse(kind)));
    for (const response of await Promise.all(pending)) { expect(response.status).toBe(200); await response.body!.cancel(); }
    expect(vi.getTimerCount()).toBe(0);
    fetchMock.mockResolvedValue(statsResponse());
    const replacement = await invoke(); expect(replacement.status).toBe(200); await replacement.body!.cancel();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('holds mixed returned leases through paused detached chunks, releasing only on downstream EOF or cancellation', async () => {
    fetchMock.mockImplementation(async (url) => readResponse(String(url).includes('/search') ? 'search' : String(url).includes('/stats') ? 'stats' : 'detail', 24_000));
    const accepted = await Promise.all(mixedReads.map((kind) => invoke(kind)));
    expect(accepted.every((response) => response.status === 200)).toBe(true);
    expect((await invoke()).status).toBe(503);
    const reader = accepted[0].body!.getReader();
    const chunk = (await reader.read()).value!;
    expect(chunk.byteLength).toBe(16_384); expect(chunk.buffer.byteLength).toBe(16_384);
    for (const kind of ['stats', 'search', 'detail'] as const) expect((await invoke(kind)).status).toBe(503);
    expect(fetchMock).toHaveBeenCalledTimes(8);
    await reader.cancel(); reader.releaseLock();
    expect(new TextDecoder().decode(chunk)).toBe((statsDocument() + ' '.repeat(24_000)).slice(0, 16_384)); // Returned chunk is not zeroed with the original buffer.
    const replacement = await invoke('detail'); expect(replacement.status).toBe(200);
    expect(await replacement.text()).toBe(searchContent() + ' '.repeat(24_000)); // EOF frees this slot.
    const next = await invoke('search'); expect(next.status).toBe(200); await next.body!.cancel();
    for (const response of accepted.slice(1)) await response.body!.cancel();
    expect(vi.getTimerCount()).toBe(0);
  });

  it.each(['upstream', 'delivery'] as const)('releases stats %s ownership on caller abort and the absolute65s deadline without leaking capacity', async (phase) => {
    for (const cause of ['caller', 'deadline']) {
      const caller = new AbortController(), started = deferred<void>(), cancel = vi.fn();
      fetchMock.mockResolvedValue(phase === 'upstream' ? statsResponse(new ReadableStream({
        start(output) { output.enqueue(bytes('{')); }, pull() { started.resolve(); return new Promise<void>(() => {}); }, cancel,
      })) : statsResponse());
      const pending = invoke('stats', { signal: caller.signal });
      const delivered = phase === 'delivery' ? await pending : null;
      if (!delivered) await started.promise;
      if (delivered) expect(delivered.status).toBe(200); // Paused delivery must still own its slot.
      if (cause === 'caller') caller.abort('private caller reason');
      else await vi.advanceTimersByTimeAsync(65_000);
      if (delivered) expect(await delivered.text().then(() => 'unexpected success', () => 'interrupted')).toBe('interrupted');
      else {
        const response = await pending;
        expect(response.status).toBe(cause === 'deadline' ? 504 : 502);
        expect(await response.text()).not.toContain('private'); expect(cancel).toHaveBeenCalledOnce();
      }
      expect(vi.getTimerCount()).toBe(0);
      fetchMock.mockResolvedValue(statsResponse());
      const replacement = await invoke(); expect(replacement.status).toBe(200); await replacement.body!.cancel();
      expect(vi.getTimerCount()).toBe(0);
    }
  });
});
