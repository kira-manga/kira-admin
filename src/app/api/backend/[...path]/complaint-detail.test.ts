import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { issueAdminProof, type AdminSessionCookie, type AdminProofCookie } from '@/lib/server-session';
import { sessionGenerationHeader } from '@/lib/session-contract';
import { createSessionFixture, fixtureSigningSecret } from '@/test/server-session-fixture';

// Real policy, signed cookies and proxy; only the upstream transport is replaced.
const cookieBoundary = { values: new Map<string, string>() };
let session: AdminSessionCookie;
let proof: AdminProofCookie;

const origin = 'https://admin.example.test';
const id = '12345678-1234-4234-8234-123456789abc';
const scope = '87654321-1234-4234-8234-123456789abc';
const tag = `"complaint-${id}-v9007199254740993"`;
const raw = `{"id":"${id}","kind":"REPORT","status":"OPEN","createdAt":"2026-09-20T00:00:00Z","updatedAt":"2026-09-20T00:00:00Z","version":9007199254740993,"ownership":"INSTALLATION","ownerReference":"${scope}","type":"TECHNICAL","subject":"Synthetic","body":"Raw 😀","actionTag":${JSON.stringify(tag)},"appVersion":null,"platform":"ANDROID","osVersion":"","manufacturer":"","deviceModel":"","closureReason":null,"replyToId":null,"closedAt":null,"closureProvenance":null,"closureActorId":null}`;
const bytes = (value: string) => new TextEncoder().encode(value);
const fetchMock = vi.fn<typeof fetch>();

function upstream(body: BodyInit | null = raw, status = 200) {
  return new Response(body, { status, headers: {
    'Content-Type': 'application/json;charset=UTF-8', ETag: tag, 'X-Kira-Complaint-Contract': '1',
    'Cache-Control': 'public, max-age=3600', 'Set-Cookie': 'private-cookie=fixture',
    Authorization: 'private-upstream-token', 'X-Kira-Admin-Step-Up': 'private-upstream-proof',
    'X-Kira-Admin-Step-Up-Consumed': 'true', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': scope, 'X-Arbitrary': 'private-metadata', Location: 'https://outside.example.test',
  } });
}

async function proxy(options: { path?: string[]; query?: string; method?: 'GET' | 'POST' | 'PUT' | 'DELETE'; signal?: AbortSignal } = {}) {
  const handlers = await import('./route');
  const path = options.path ?? ['complaints', id];
  const method = options.method ?? 'GET';
  return handlers[method](new Request(`${origin}/api/backend/${path.join('/')}${options.query ?? `?dataScopeId=${scope}`}`, {
    method, signal: options.signal, headers: {
      Origin: origin, 'Sec-Fetch-Site': 'same-origin', 'X-Kira-CSRF': session.csrfToken,
      [sessionGenerationHeader]: session.generation,
      Cookie: [...cookieBoundary.values].map(([name, value]) => `${name}=${value}`).join('; '),
      Authorization: 'Bearer caller-selected-token', 'X-Kira-Admin-Step-Up': 'caller-selected-proof',
      'X-Kira-Idempotency-Key': scope, 'If-Match': tag, 'Content-Type': 'application/problem+json',
    },
  }), { params: Promise.resolve({ path }) });
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_ORIGIN', origin);
  cookieBoundary.values.clear();
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  session = createSessionFixture('fixture-only-session');
  proof = issueAdminProof(session, 'A'.repeat(43), 'complaint-moderation-mutation', new Date(Date.now() + 300_000).toISOString(), null);
  for (const cookie of [session, proof]) cookieBoundary.values.set(cookie.name, cookie.value);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('read-only complaint detail BFF connection', () => {
  it('uses the configured host/session and preserves raw Long bytes while stripping unrelated headers and proofs', async () => {
    const input = bytes(raw);
    fetchMock.mockResolvedValue(upstream(new ReadableStream({ start(controller) {
      controller.enqueue(input.slice(0, 311));
      controller.enqueue(input.slice(311));
      controller.close();
    } })));
    const response = await proxy();
    expect(response.status).toBe(200);
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(input);
    expect(Object.fromEntries(response.headers)).toEqual({
      'content-type': 'application/json;charset=UTF-8', etag: tag,
      'x-kira-complaint-contract': '1', 'cache-control': 'no-store, no-transform',
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/${id}?dataScopeId=${scope}`);
    expect(init).toMatchObject({ method: 'GET', cache: 'no-store', redirect: 'manual', signal: expect.any(AbortSignal) });
    expect(init?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({
      authorization: 'Bearer fixture-only-session', accept: 'application/json, application/problem+json', 'x-kira-complaint-contract': '1',
    });
    expect(cookieBoundary.values.get(proof.name)).toBe(proof.value);
    expect(response.headers.getSetCookie()).toHaveLength(0);
  });

  it('refuses non-detail routes, mutations, nonliteral/duplicate scopes and missing sessions before upstream work', async () => {
    for (const options of [
      { path: ['complaints', 'search'], method: 'POST' as const },
      { path: ['complaints', id, 'status'] }, { path: ['complaints', id.toUpperCase()] },
      { method: 'DELETE' as const }, { query: '' }, { query: `?dataScopeId=${scope}&dataScopeId=${scope}` },
      { query: '?dataScopeId=00000000-0000-0000-0000-000000000000' }, { query: `?dataScopeId=%38${scope.slice(1)}` },
    ]) expect((await proxy(options)).status).toBeGreaterThanOrEqual(400);
    cookieBoundary.values.delete(session.name);
    const localFailure = await proxy();
    expect(localFailure.status).toBe(401);
    expect(localFailure.headers.get('WWW-Authenticate')).toBe('KiraSession realm="kira-admin-bff"');
    expect(localFailure.headers.getSetCookie()).toHaveLength(0);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(await import('./route')).toHaveProperty('PATCH'); // Only the separately bounded three-action connection.
  });

  it('keeps unavailable/auth statuses but discards private error bodies and redirects without claiming activation', async () => {
    for (const status of [401, 403, 404, 429, 503, 302]) {
      const cancel = vi.fn();
      fetchMock.mockResolvedValueOnce(upstream(new ReadableStream({ start(controller) { controller.enqueue(bytes('private problem')); }, cancel }), status));
      const response = await proxy();
      expect(response.status).toBe(status === 302 ? 502 : status);
      expect(await response.json()).toEqual({ detail: 'Complaint detail could not be loaded.' });
      expect(Object.fromEntries(response.headers)).toEqual({ 'cache-control': 'no-store', 'content-type': 'application/json' });
      expect(cancel).toHaveBeenCalledOnce();
    }
  });

  it.each([null, 'Bearer realm="kira-complaints"', 'KiraSession realm="kira-admin-bff"'])('strips upstream read401 challenge %s without retiring the authenticated G or either scoped P', async (challenge) => {
    const sourceProof = issueAdminProof(session, 'B'.repeat(43), 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    cookieBoundary.values.set(sourceProof.name, sourceProof.value);
    const before = [...cookieBoundary.values];
    const cancel = vi.fn();
    const denied = upstream(new ReadableStream({ start(controller) { controller.enqueue(bytes('private upstream read failure')); }, cancel }), 401);
    if (challenge !== null) denied.headers.set('WWW-Authenticate', challenge);
    fetchMock.mockResolvedValueOnce(denied);
    const response = await proxy();
    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({ detail: 'Complaint detail could not be loaded.' });
    expect(Object.fromEntries(response.headers)).toEqual({ 'cache-control': 'no-store', 'content-type': 'application/json' });
    expect(response.headers.get('WWW-Authenticate')).toBeNull();
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect([...cookieBoundary.values]).toEqual(before);
    expect(cookieBoundary.values.get(session.name)).toBe(session.value);
    expect(cookieBoundary.values.get(proof.name)).toBe(proof.value);
    expect(cookieBoundary.values.get(sourceProof.name)).toBe(sourceProof.value);
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('Authorization')).toBe('Bearer fixture-only-session');
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(cancel).toHaveBeenCalledOnce();
  });

  it('bounds actual streamed bytes including the exact ceiling, and refuses empty or invalid-header successes', async () => {
    const maximum = bytes(raw + ' '.repeat(32_768 - bytes(raw).length));
    fetchMock.mockResolvedValueOnce(upstream(maximum));
    expect(new Uint8Array(await (await proxy()).arrayBuffer())).toEqual(maximum);
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(upstream(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(32_769)); }, cancel })));
    expect((await proxy()).status).toBe(502);
    expect(cancel).toHaveBeenCalledOnce();
    const wrongMedia = upstream(); wrongMedia.headers.set('Content-Type', 'text/html');
    const missingContract = upstream(); missingContract.headers.delete('X-Kira-Complaint-Contract');
    const longTag = upstream(); longTag.headers.set('ETag', 'x'.repeat(70));
    for (const input of [upstream(''), wrongMedia, missingContract, longTag]) {
      fetchMock.mockResolvedValueOnce(input);
      expect((await proxy()).status).toBe(502);
    }
  });

  it('cancels stalled body acquisition for both the original request and the existing finite server deadline', async () => {
    const timeout = vi.spyOn(AbortSignal, 'timeout');
    for (const source of ['caller', 'deadline']) {
      const caller = new AbortController();
      const deadline = new AbortController();
      timeout.mockReturnValue(deadline.signal);
      let started = () => {};
      const reading = new Promise<void>((resolve) => { started = resolve; });
      const cancel = vi.fn();
      fetchMock.mockResolvedValueOnce(upstream(new ReadableStream({
        start(controller) { controller.enqueue(bytes('{')); },
        pull() { started(); return new Promise<void>(() => {}); }, cancel,
      })));
      const pending = proxy({ signal: caller.signal });
      await reading;
      if (source === 'caller') caller.abort('private cancellation reason');
      else deadline.abort(new DOMException('private timeout reason', 'TimeoutError'));
      const response = await pending;
      expect(response.status).toBe(source === 'caller' ? 502 : 504);
      expect(await response.json()).toEqual({ detail: 'Complaint detail could not be loaded.' });
      expect(cancel).toHaveBeenCalledOnce();
      expect(timeout).toHaveBeenLastCalledWith(65_000);
    }
  });

  it('returns only a static gateway failure when fetching fails', async () => {
    fetchMock.mockRejectedValue(new Error('private transport detail'));
    const response = await proxy();
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'Complaint detail could not be loaded.' });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
