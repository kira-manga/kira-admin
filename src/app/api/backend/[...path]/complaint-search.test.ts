import { Buffer } from 'node:buffer';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { issueAdminProof, type AdminProofCookie, type AdminSessionCookie } from '@/lib/server-session';
import { sessionGenerationHeader } from '@/lib/session-contract';
import { complaintScope } from '@/test/complaint-mutation-fixture';
import { searchContent, searchCursor, searchPage, searchResponse } from '@/test/complaint-search-fixture';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';

const fetchMock = vi.fn<typeof fetch>();
const bytes = (value: string) => new TextEncoder().encode(value);
const defaultBody = `{"dataScopeId":"${complaintScope}"}`;
let session: AdminSessionCookie;
let proofs: AdminProofCookie[];
let outputs: Response[];
let requests: AbortController[];

async function invoke(options: { body?: BodyInit; headers?: HeadersInit; remove?: string[]; query?: string; pathname?: string; path?: string[]; signal?: AbortSignal } = {}) {
  const headers = signedRequestHeaders(session, proofs, { 'X-Kira-Complaint-Contract': '1', Authorization: 'Bearer caller-override', 'X-Kira-Admin-Step-Up': 'caller-proof-override' });
  for (const [name, value] of new Headers(options.headers)) headers.set(name, value);
  options.remove?.forEach((name) => headers.delete(name));
  const controller = new AbortController(); requests.push(controller);
  const request = new Request(`https://admin.example.test${options.pathname ?? '/api/backend/complaints/search'}${options.query ?? ''}`, {
    method: 'POST', headers, body: options.body ?? defaultBody, duplex: 'half',
    signal: options.signal ? AbortSignal.any([controller.signal, options.signal]) : controller.signal,
  } as RequestInit);
  const { POST } = await import('./route');
  const response = await POST(request, { params: Promise.resolve({ path: options.path ?? ['complaints', 'search'] }) });
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

describe('actual bounded complaint POST search connection', () => {
  it('uses only the fixed producer and signed session, preserving body/Long bytes without forwarding proof or private response metadata', async () => {
    const raw = searchPage([searchContent()], searchCursor);
    fetchMock.mockResolvedValue(searchResponse(raw, 200, { 'Set-Cookie': 'private=never', Authorization: 'private',
      'X-Kira-Admin-Step-Up': 'private', 'X-Kira-Admin-Step-Up-Consumed': 'true', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': complaintScope,
      'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"', Location: 'https://private.example', 'Content-Length': String(bytes(raw).length) }));
    const body = ` {"text":"  raw\\r\\nquery  ","dataScopeId":"${complaintScope}","cursor":"${searchCursor}"} `;
    const response = await invoke({ body });
    expect(response.status).toBe(200);
    expect(await response.text()).toBe(raw);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://backend:8080/api/v1/admin/complaints/search');
    expect(new TextDecoder().decode(init?.body as Uint8Array)).toBe(body);
    expect(init).toMatchObject({ method: 'POST', redirect: 'manual', cache: 'no-store', signal: expect.any(AbortSignal) });
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({ authorization: `Bearer ${session.token}`, 'content-type': 'application/json',
      accept: 'application/json, application/problem+json', 'accept-encoding': 'identity', 'x-kira-complaint-contract': '1' });
    expect(Object.fromEntries(response.headers)).toEqual({ 'content-type': 'application/json;charset=UTF-8', 'x-kira-complaint-contract': '1',
      'cache-control': 'no-store, no-transform', 'x-content-type-options': 'nosniff' });
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects path/query aliases, origin/session/CSRF, contradictory framing and mutation headers before upstream work', async () => {
    const cases: Array<[Parameters<typeof invoke>[0], number]> = [
      [{ pathname: '/api/backend/complaints/se%61rch' }, 404], [{ path: ['complaints', 'stats'] }, 404], [{ path: ['complaints', 'batch'] }, 404],
      [{ query: '?' }, 400], [{ query: '?text=private' }, 400], [{ query: `?dataScopeId=${complaintScope}` }, 400],
      [{ headers: { Origin: 'https://outside.example' } }, 403], [{ remove: ['X-Kira-CSRF'] }, 403], [{ remove: [sessionGenerationHeader] }, 401],
      [{ headers: { 'Content-Type': 'application/json, application/json' } }, 415], [{ headers: { 'Content-Encoding': 'gzip' } }, 415],
      [{ headers: { 'Content-Length': '1', 'Transfer-Encoding': 'chunked' } }, 400], [{ headers: { 'Content-Length': '1' } }, 400],
      [{ headers: { 'Content-Length': '1, 1' } }, 400], [{ headers: { 'X-Kira-Complaint-Contract': '1, 1' } }, 400],
      [{ headers: { 'If-Match': 'not-a-search-header' } }, 400], [{ headers: { 'X-Kira-Idempotency-Key': complaintScope } }, 400],
      [{ headers: new Headers(Array.from({ length: 129 }, (_, index) => [`X-Test-${index}`, 'bounded'] as [string, string])) }, 431],
    ];
    for (const [options, status] of cases) expect((await invoke(options)).status).toBe(status);
    const local = await invoke({ remove: [sessionGenerationHeader] });
    expect(local.headers.get('WWW-Authenticate')).toBe('KiraSession realm="kira-admin-bff"');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('accepts exact32KiB input and2MiB output, preserving every byte rather than an equality sample', async () => {
    const raw = searchPage();
    const expected = bytes(raw + ' '.repeat(2_097_152 - bytes(raw).length));
    fetchMock.mockResolvedValue(searchResponse(expected));
    const response = await invoke({ body: defaultBody + ' '.repeat(32_768 - defaultBody.length) });
    expect(response.status).toBe(200);
    const actual = Buffer.from(await response.arrayBuffer());
    expect(actual.byteLength).toBe(2_097_152);
    expect(actual.equals(expected)).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('withholds a late inbound extra byte and rejects duplicate/unknown search fields before fetch', async () => {
    for (const length of [undefined, '1']) {
      const cancel = vi.fn();
      const input = new ReadableStream({ start(output) { output.enqueue(bytes(defaultBody + ' '.repeat(32_768 - defaultBody.length))); output.enqueue(bytes(' ')); }, cancel });
      expect((await invoke({ body: input, ...(length ? { headers: { 'Content-Length': length } } : {}) })).status).toBe(413);
      expect(cancel).toHaveBeenCalledOnce();
    }
    for (const body of [`{"dataScopeId":"${complaintScope}","text":"a","te\\u0078t":"b"}`, `{"dataScopeId":"${complaintScope}","actor":"caller"}`]) {
      expect((await invoke({ body })).status).toBe(400);
    }
    expect(fetchMock).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('withholds oversized/false-length/encoded/redirected/malformed search replies and cancels open overflow', async () => {
    for (const mode of ['overflow', 'false-length', 'encoded', 'redirect', 'wrong-contract', 'page-etag', 'invalid-page']) {
      const cancel = vi.fn();
      let upstream = searchResponse();
      if (mode === 'overflow') upstream = searchResponse(new ReadableStream({ start(output) { output.enqueue(new Uint8Array(2_097_152)); output.enqueue(bytes(' ')); }, cancel }));
      if (mode === 'false-length') upstream.headers.set('Content-Length', '1');
      if (mode === 'encoded') upstream.headers.set('Content-Encoding', 'gzip');
      if (mode === 'redirect') upstream = searchResponse(null, 302, { Location: 'https://private.example' });
      if (mode === 'wrong-contract') upstream.headers.set('X-Kira-Complaint-Contract', '1, 1');
      if (mode === 'page-etag') upstream.headers.set('ETag', 'not-a-detail');
      if (mode === 'invalid-page') upstream = searchResponse('{"items":[{"private":"unvalidated prefix"}]}');
      fetchMock.mockResolvedValueOnce(upstream);
      const result = await invoke();
      expect(result.status, mode).toBe(502);
      expect(await result.text()).not.toMatch(/unvalidated prefix|private\.example|"items"/);
      expect(result.headers.getSetCookie()).toHaveLength(0);
      if (mode === 'overflow') expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('strips every upstream401 challenge and private error body without changing either scoped proof or G', async () => {
    for (const challenge of [null, 'Bearer realm="kira-complaints"', 'KiraSession realm="kira-admin-bff"']) {
      const cancel = vi.fn();
      const upstream = searchResponse(new ReadableStream({ start(output) { output.enqueue(bytes('private read failure')); }, cancel }), 401,
        { 'Set-Cookie': 'retire-something=never', ...(challenge ? { 'WWW-Authenticate': challenge } : {}) });
      fetchMock.mockResolvedValueOnce(upstream);
      const response = await invoke();
      expect(response.status).toBe(401);
      expect(response.headers.get('www-authenticate')).toBeNull();
      expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(await response.text()).not.toContain('private read failure');
      expect(cancel).toHaveBeenCalledOnce();
      expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).get('Authorization')).toBe(`Bearer ${session.token}`);
    }
    expect(proofs.map((proof) => proof.scope)).toEqual(['source-admin-mutation', 'complaint-moderation-mutation']);
  });

  it('admits exactly eight pending upstream exchanges and returns the ninth503 before fetching', async () => {
    const ready = deferred<void>();
    const release: Array<(response: Response) => void> = [];
    fetchMock.mockImplementation((_, init) => new Promise<Response>((resolve, reject) => {
      release.push(resolve);
      init?.signal?.addEventListener('abort', () => reject(new Error('private abort')), { once: true });
      if (release.length === 8) ready.resolve();
    }));
    const pending = Array.from({ length: 8 }, () => invoke());
    await ready.promise;
    expect((await invoke()).status).toBe(503);
    expect(fetchMock).toHaveBeenCalledTimes(8);
    release.forEach((resolve) => resolve(searchResponse()));
    const accepted = await Promise.all(pending);
    for (const response of accepted) { expect(response.status).toBe(200); await response.body!.cancel(); }
    expect(vi.getTimerCount()).toBe(0);
    fetchMock.mockResolvedValue(searchResponse());
    expect((await invoke()).status).toBe(200);
  });

  it('holds all eight returned response leases through a paused downstream reader until EOF or cancellation', async () => {
    const raw = searchPage() + ' '.repeat(40_000);
    fetchMock.mockImplementation(async () => searchResponse(raw));
    const accepted = await Promise.all(Array.from({ length: 8 }, () => invoke()));
    expect(accepted.every((response) => response.status === 200)).toBe(true);
    expect((await invoke()).status).toBe(503);
    const reader = accepted[0].body!.getReader();
    expect((await reader.read()).value?.byteLength).toBe(16_384);
    expect((await invoke()).status).toBe(503); // Not released just by constructing200 or delivering one chunk.
    expect(fetchMock).toHaveBeenCalledTimes(8);
    await reader.cancel(); reader.releaseLock();
    const replacement = await invoke();
    expect(replacement.status).toBe(200);
    expect(await replacement.text()).toBe(raw); // EOF returns the replacement's lease too.
    const next = await invoke(); expect(next.status).toBe(200); await next.body!.cancel();
    for (const response of accepted.slice(1)) await response.body!.cancel();
    expect(vi.getTimerCount()).toBe(0);
  });

  it.each(['request', 'upstream', 'delivery'] as const)('cleans up %s ownership on both caller abort and the absolute exchange deadline', async (phase) => {
    for (const cause of ['caller', 'deadline']) {
      fetchMock.mockReset();
      const caller = new AbortController(), started = deferred<void>();
      const cancel = vi.fn();
      const stream = new ReadableStream({ start(output) { output.enqueue(bytes('{')); }, pull() { started.resolve(); return new Promise<void>(() => {}); }, cancel });
      if (phase === 'upstream') fetchMock.mockResolvedValue(searchResponse(stream));
      else fetchMock.mockResolvedValue(searchResponse());
      const pending = invoke({ signal: caller.signal, ...(phase === 'request' ? { body: stream } : {}) });
      const delivered = phase === 'delivery' ? await pending : null;
      if (!delivered) await started.promise;
      if (delivered) expect(delivered.status).toBe(200); // Leave it unread; draining would release the lease.
      if (cause === 'caller') caller.abort('private caller reason');
      else await vi.advanceTimersByTimeAsync(65_000);
      if (delivered) expect(await delivered.text().then(() => 'unexpected success', () => 'interrupted')).toBe('interrupted');
      else {
        const response = await pending;
        expect(response.status).toBe(cause === 'deadline' ? 504 : 502);
        expect(await response.text()).not.toContain('private');
        expect(cancel).toHaveBeenCalledOnce();
      }
      expect(vi.getTimerCount()).toBe(0);
      fetchMock.mockResolvedValue(searchResponse());
      const after = await invoke(); expect(after.status).toBe(200); await after.body!.cancel();
    }
  });
});
