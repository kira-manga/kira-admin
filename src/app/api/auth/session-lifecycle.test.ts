import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { isSessionAcknowledgement, sessionGenerationHeader, stepUpProofIdHeader, type SessionAcknowledgement } from '@/lib/session-contract';
import { issueAdminProof, readAdminProof, readAdminSession, type AdminSessionCookie } from '@/lib/server-session';
import { isStepUpApproval, type StepUpApproval, type StepUpScope } from '@/lib/step-up-contract';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';
import { appliedResponse, complaintId, complaintScope, grantA, grantB, mutationRequest } from '@/test/complaint-mutation-fixture';

const origin = 'https://admin.example.test';
const jwt = 'same-second-fixture-jwt';
const proofToken = 'A'.repeat(43);
const grantId = '12345678-1234-4234-8234-123456789abc';
const fetchMock = vi.fn<typeof fetch>();

// A bounded fixture jar applies only actual NextResponse Set-Cookie fields, including Path.
// This models response ordering; it is not a claim of physical-browser verification.
class CookieJar {
  private values = new Map<string, { name: string; value: string; path: string }>();
  receive(response: Response) {
    for (const raw of response.headers.getSetCookie()) {
      const [pair, ...attributes] = raw.split(';').map((part) => part.trim());
      const separator = pair.indexOf('=');
      const name = pair.slice(0, separator);
      const value = pair.slice(separator + 1);
      const path = attributes.find((part) => part.startsWith('Path='))?.slice(5) ?? '/';
      const key = `${name}:${path}`;
      if (attributes.includes('Max-Age=0')) this.values.delete(key);
      else this.values.set(key, { name, value, path });
    }
  }
  header(path: string) {
    return [...this.values.values()].filter((cookie) => cookie.path === '/' || path === cookie.path || path.startsWith(cookie.path + '/'))
      .map(({ name, value }) => `${name}=${value}`).join('; ');
  }
  names() { return [...this.values.values()].map((cookie) => cookie.name); }
  request(path: string, session: SessionAcknowledgement | null, method = 'POST', extra: HeadersInit = {}, body = '{}') {
    const headers = new Headers({ Origin: origin, 'Sec-Fetch-Site': 'same-origin', 'Content-Type': 'application/json', Cookie: this.header(path) });
    if (session) { headers.set(sessionGenerationHeader, session.generation); headers.set('X-Kira-CSRF', session.csrfToken); }
    for (const [name, value] of new Headers(extra)) headers.set(name, value);
    return new Request(origin + path, { method, headers, ...(method === 'GET' ? {} : { body }) });
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function upstreamLogin() { return Response.json({ accessToken: jwt, expiresInSeconds: 3600, role: 'ADMIN' }); }
function upstreamProof(scope: StepUpScope = 'source-admin-mutation', headers?: HeadersInit) {
  return Response.json({ token: proofToken, expiresAt: new Date(Date.now() + 300_000).toISOString(), scope }, { headers });
}
async function login(jar: CookieJar) {
  fetchMock.mockResolvedValueOnce(upstreamLogin());
  const { POST } = await import('./login/route');
  const response = await POST(jar.request('/api/auth/login', null));
  expect(response.status).toBe(200);
  const session = await response.json();
  expect(isSessionAcknowledgement(session)).toBe(true);
  jar.receive(response);
  return session as SessionAcknowledgement;
}
async function stepUp(jar: CookieJar, session: SessionAcknowledgement, scope: StepUpScope = 'source-admin-mutation', association: string | null = null) {
  fetchMock.mockResolvedValueOnce(upstreamProof(scope, association ? { 'X-Kira-Admin-Step-Up-Grant-Id': association } : {}));
  const { POST } = await import('./step-up/route');
  const response = await POST(jar.request('/api/auth/step-up', session, 'POST', {}, JSON.stringify({ password: 'fixture', ...(scope === 'complaint-moderation-mutation' ? { scope } : {}) })));
  expect(response.status).toBe(200);
  const approval = await response.json();
  expect(isStepUpApproval(approval, scope)).toBe(true);
  jar.receive(response);
  return approval as StepUpApproval;
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('NODE_ENV', 'production');
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_ORIGIN', origin);
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'false');
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('real mounted auth handlers under reordered responses', () => {
  it('returns only the bounded selected session profile/CSRF and no upstream credential fields', async () => {
    const session = createSessionFixture();
    const profile = { id: grantId, email: 'synthetic@example.test', role: 'ADMIN', createdAt: '2026-09-20T00:00:00Z' };
    fetchMock.mockResolvedValueOnce(Response.json({ ...profile, accessToken: session.token, backendUrl: 'http://private-fixture' }));
    const { GET } = await import('./session/route');
    const request = new Request(origin + '/api/auth/session', { headers: signedRequestHeaders(session) });
    const response = await GET(request);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ...profile, generation: session.generation, csrfToken: session.csrfToken, expiresAt: new Date(session.expiresAt).toISOString() });
    expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('Authorization')).toBe(`Bearer ${session.token}`);
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(new Response(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(4097)); }, cancel })));
    const refused = await GET(request);
    expect(refused.status).toBe(503);
    expect(refused.headers.getSetCookie()).toHaveLength(0);
    expect(cancel).toHaveBeenCalledOnce();
  });

  it.each([{ accessToken: 'bad-token\n' }, { accessToken: 'x'.repeat(2049) }, { expiresInSeconds: 0 }, { expiresInSeconds: '3600' }])
  ('refuses invalid bounded login credentials without creating a generation cookie: %j', async (fields) => {
    fetchMock.mockResolvedValueOnce(Response.json({ accessToken: jwt, role: 'ADMIN', expiresInSeconds: 3600, ...fields }));
    const { POST } = await import('./login/route');
    const response = await POST(new CookieJar().request('/api/auth/login', null));
    expect(response.status).toBe(502);
    expect(response.headers.getSetCookie()).toHaveLength(0);
  });

  it('gives identical JWTs distinct authenticated G and never lets an old logout erase newer G/P', async () => {
    const jar = new CookieJar();
    const first = await login(jar);
    const firstProof = await stepUp(jar, first);
    const { POST } = await import('./logout/route');
    const oldLogout = await POST(jar.request('/api/auth/logout', first)); // Hold its delivery.
    const second = await login(jar);
    const secondProof = await stepUp(jar, second);
    expect(second.generation).not.toBe(first.generation);
    expect(secondProof.proofId).not.toBe(firstProof.proofId);
    jar.receive(oldLogout);
    const headers = jar.request('/api/backend/sources/Azora/editor-draft/publish', second, 'POST', { [stepUpProofIdHeader]: secondProof.proofId }).headers;
    const selected = readAdminSession(headers);
    expect(selected.token).toBe(jwt);
    expect(readAdminProof(headers, selected, 'source-admin-mutation').proofId).toBe(secondProof.proofId);
    for (const cookie of oldLogout.headers.getSetCookie()) {
      expect(cookie).not.toContain(second.generation);
      expect(cookie).not.toContain(secondProof.proofId);
    }
  });

  it('does not let an old auth/me rejection delete a later same-JWT session', async () => {
    const jar = new CookieJar();
    const first = await login(jar);
    const entered = deferred<void>();
    const upstream = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return upstream.promise; });
    const { GET } = await import('./session/route');
    const oldCheck = GET(jar.request('/api/auth/session', first, 'GET'));
    await entered.promise;
    const second = await login(jar);
    upstream.resolve(Response.json({ detail: 'Expired synthetic session.' }, { status: 401 }));
    const rejected = await oldCheck;
    expect(rejected.status).toBe(401);
    jar.receive(rejected);
    expect(readAdminSession(jar.request('/api/auth/session', second, 'GET').headers).generation).toBe(second.generation);
    expect(rejected.headers.get('set-cookie')).not.toContain(second.generation);
  });

  it('keeps a delayed old-session issuance unselected and unusable under the new G', async () => {
    const jar = new CookieJar();
    const first = await login(jar);
    const entered = deferred<void>();
    const upstream = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return upstream.promise; });
    const issuer = (await import('./step-up/route')).POST;
    const oldIssue = issuer(jar.request('/api/auth/step-up', first, 'POST', {}, '{"password":"fixture"}'));
    await entered.promise;
    const logout = (await import('./logout/route')).POST;
    jar.receive(await logout(jar.request('/api/auth/logout', first)));
    const second = await login(jar);
    const selectedProof = await stepUp(jar, second);
    upstream.resolve(upstreamProof());
    const late = await oldIssue;
    expect(late.status).toBe(200);
    const oldApproval = await late.json() as StepUpApproval;
    jar.receive(late);
    expect(oldApproval.generation).toBe(first.generation);
    const headers = jar.request('/api/backend/sources/Azora/operational-mode', second, 'PUT', { [stepUpProofIdHeader]: oldApproval.proofId }).headers;
    expect(() => readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation')).toThrow('Verify your password');
    headers.set(stepUpProofIdHeader, selectedProof.proofId);
    expect(readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation').proofId).toBe(selectedProof.proofId);
    expect(jar.names().filter((name) => name.startsWith('kira_admin_session_'))).toHaveLength(1);
  });

  it('never lets an older login response overwrite a newer generation cookie', async () => {
    const jar = new CookieJar();
    const entered = deferred<void>();
    const upstream = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return upstream.promise; });
    const { POST } = await import('./login/route');
    const oldRequest = POST(jar.request('/api/auth/login', null));
    await entered.promise;
    const second = await login(jar);
    const secondProof = await stepUp(jar, second);
    upstream.resolve(upstreamLogin());
    const late = await oldRequest;
    jar.receive(late);
    const oldAcknowledgement = await late.json() as SessionAcknowledgement;
    expect(oldAcknowledgement.generation).not.toBe(second.generation);
    const headers = jar.request('/api/backend/sources/Azora/operational-mode', second, 'PUT', { [stepUpProofIdHeader]: secondProof.proofId }).headers;
    expect(readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation').proofId).toBe(secondProof.proofId);
    // The client separately decides which ACK may be adopted; the server sets no shared current selector.
    expect(late.headers.getSetCookie()).toHaveLength(1);
    expect(late.headers.get('set-cookie')).not.toContain(second.generation);
  });
});

describe('exact mounted source-consumption recognition', () => {
  const actions = [
    { method: 'POST' as const, path: ['source-changesets', grantId, 'apply'] },
    { method: 'POST' as const, path: ['sources', 'Azora', 'editor-draft', 'publish'] },
    { method: 'PUT' as const, path: ['sources', 'Azora', 'operational-mode'] },
  ];
  it.each(actions)('retires only captured P on a direct 200 from $method $path, even if a later issuance arrived first', async ({ method, path }) => {
    const jar = new CookieJar();
    const session = await login(jar);
    const first = await stepUp(jar, session);
    const upstream = deferred<Response>();
    const entered = deferred<void>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return upstream.promise; });
    const handlers = await import('../backend/[...path]/route');
    const mutation = handlers[method](jar.request('/api/backend/' + path.join('/'), session, method, {
      [stepUpProofIdHeader]: first.proofId, 'If-Match': '"saved-4"', Authorization: 'Bearer caller-token', 'X-Kira-Admin-Step-Up': 'caller-proof',
    }), { params: Promise.resolve({ path }) });
    await entered.promise;
    const forwarded = fetchMock.mock.calls.at(-1)?.[1];
    expect(forwarded?.redirect).toBe('manual');
    expect(Object.fromEntries(new Headers(forwarded?.headers))).toEqual({
      accept: 'application/json, application/problem+json', authorization: `Bearer ${jwt}`, 'content-type': 'application/json',
      'if-match': '"saved-4"', 'x-kira-admin-step-up': proofToken,
    });
    const second = await stepUp(jar, session);
    upstream.resolve(Response.json({ documentRevision: 9 }));
    const response = await mutation;
    expect(response.status).toBe(200);
    expect(response.headers.getSetCookie()).toHaveLength(1);
    expect(response.headers.getSetCookie()[0]).toContain(first.proofId + '=; Path=/api;');
    expect(response.headers.get('set-cookie')).not.toContain(second.proofId);
    jar.receive(response);
    const headers = jar.request('/api/backend/' + path.join('/'), session, method, { [stepUpProofIdHeader]: second.proofId }).headers;
    expect(readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation').proofId).toBe(second.proofId);
  });

  it.each([201, 204, 302, 400, 401, 403, 409, 422, 429, 500, 503])('retains the captured P for ambiguous/unconfirmed HTTP %i regardless of historical complaint headers', async (status) => {
    const session = createSessionFixture();
    const proof = issueAdminProof(session, proofToken, 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    const headers = signedRequestHeaders(session, [proof]);
    fetchMock.mockResolvedValue(new Response(status === 204 ? null : '{}', { status, headers: {
      'X-Kira-Admin-Step-Up-Consumed': 'true', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': grantId,
      Location: 'https://other.example.test/private',
    } }));
    const { POST } = await import('../backend/[...path]/route');
    const path = ['sources', 'Azora', 'editor-draft', 'publish'];
    const response = await POST(new Request(origin + '/api/backend/' + path.join('/'), { method: 'POST', headers }), { params: Promise.resolve({ path }) });
    expect(response.status).toBe(status);
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(response.headers.get('x-kira-admin-step-up-consumed')).toBeNull();
    expect(response.headers.get('x-kira-admin-step-up-consumed-grant-id')).toBeNull();
    expect(response.headers.get('location')).toBeNull();
    expect(fetchMock.mock.calls[0][1]?.redirect).toBe('manual');
  });

  it.each(['timeout', 'network', 'redirected200'])('does not retire a source proof on %s', async (outcome) => {
    const session = createSessionFixture();
    const proof = issueAdminProof(session, proofToken, 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    vi.spyOn(console, 'error').mockImplementation(() => {});
    if (outcome === 'redirected200') {
      const upstream = Response.json({});
      Object.defineProperty(upstream, 'redirected', { value: true });
      fetchMock.mockResolvedValue(upstream);
    } else fetchMock.mockRejectedValue(outcome === 'timeout' ? new DOMException('Synthetic deadline', 'TimeoutError') : new TypeError('Synthetic transport failure'));
    const { PUT } = await import('../backend/[...path]/route');
    const path = ['sources', 'Azora', 'operational-mode'];
    const response = await PUT(new Request(origin + '/api/backend/' + path.join('/'), { method: 'PUT', headers: signedRequestHeaders(session, [proof]) }), { params: Promise.resolve({ path }) });
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(response.status).toBe(outcome === 'timeout' ? 504 : outcome === 'network' ? 502 : 200);
  });

  it('forwards no proof on source non-action shapes, and keeps unsupported complaint methods closed', async () => {
    const session = createSessionFixture();
    const proof = issueAdminProof(session, proofToken, 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    const handlers = await import('../backend/[...path]/route');
    for (const path of [['source-changesets', 'not-a-canonical-uuid', 'apply'], ['sources', 'Azora', 'editor-draft', 'validate']]) {
      fetchMock.mockResolvedValueOnce(Response.json({}));
      const response = await handlers.POST(new Request(origin + '/api/backend/' + path.join('/'), { method: 'POST', headers: signedRequestHeaders(session, [proof]) }), { params: Promise.resolve({ path }) });
      expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).get('X-Kira-Admin-Step-Up')).toBeNull();
    }
    fetchMock.mockClear();
    for (const method of ['POST', 'PUT', 'DELETE'] as const) {
      const path = ['complaints', grantId, 'status'];
      expect((await handlers[method](new Request(origin + '/api/backend/' + path.join('/'), { method, headers: signedRequestHeaders(session, [proof]) }), { params: Promise.resolve({ path }) })).status).toBe(404);
    }
    expect(handlers).toHaveProperty('PATCH');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('server-owned complaint association and runtime availability', () => {
  it.each(['same-session', 'new-session', 'uncaptured-association'] as const)('never retires a later issuance on a delayed complaint response (%s)', async (ordering) => {
    const jar = new CookieJar();
    const firstSession = await login(jar);
    const first = await stepUp(jar, firstSession, 'complaint-moderation-mutation', grantA);
    const description = mutationRequest();
    const path = ['complaints', complaintId, 'status'];
    const url = '/api/backend/' + path.join('/') + `?dataScopeId=${complaintScope}`;
    const entered = deferred<void>();
    const upstream = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return upstream.promise; });
    const { PATCH } = await import('../backend/[...path]/route');
    const pending = PATCH(jar.request(url, firstSession, 'PATCH', { ...description.headers, [stepUpProofIdHeader]: first.proofId }, description.body), { params: Promise.resolve({ path }) });
    await entered.promise;
    const currentSession = ordering === 'new-session' ? await login(jar) : firstSession;
    const later = await stepUp(jar, currentSession, 'complaint-moderation-mutation', grantB);
    upstream.resolve(appliedResponse(description, { 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': ordering === 'uncaptured-association' ? grantB : grantA }));
    const response = await pending;
    expect(response.status).toBe(200);
    expect(response.headers.getSetCookie()).toHaveLength(ordering === 'uncaptured-association' ? 0 : 1);
    expect(response.headers.get('set-cookie') ?? '').not.toContain(later.proofId);
    jar.receive(response);
    const headers = jar.request(url, currentSession, 'PATCH', { [stepUpProofIdHeader]: later.proofId }).headers;
    expect(readAdminProof(headers, readAdminSession(headers), 'complaint-moderation-mutation')).toMatchObject({ proofId: later.proofId, grantId: grantB });
    expect(response.headers.has('X-Kira-Admin-Step-Up-Consumed-Grant-Id')).toBe(false);
  });

  it.each([null, grantId])('keeps issuance association %s server-side and separate from browser P', async (association) => {
    const session = createSessionFixture();
    const headers = signedRequestHeaders(session);
    fetchMock.mockResolvedValue(upstreamProof('complaint-moderation-mutation', association ? { 'X-Kira-Admin-Step-Up-Grant-Id': association } : {}));
    const { POST } = await import('./step-up/route');
    const response = await POST(new Request(origin + '/api/auth/step-up', { method: 'POST', headers, body: '{"password":"fixture","scope":"complaint-moderation-mutation"}' }));
    expect(response.status).toBe(200);
    const approval = await response.json() as StepUpApproval;
    expect(Object.keys(approval).sort()).toEqual(['expiresAt', 'generation', 'proofId', 'scope']);
    expect(approval.proofId).not.toBe(grantId);
    expect(response.headers.get('X-Kira-Admin-Step-Up-Grant-Id')).toBeNull();
    headers.set('cookie', headers.get('cookie') + '; ' + response.headers.getSetCookie()[0].split(';')[0]);
    headers.set(stepUpProofIdHeader, approval.proofId);
    expect(readAdminProof(headers, readAdminSession(headers), 'complaint-moderation-mutation').grantId).toBe(association);
  });

  it.each(['', grantId.toUpperCase(), `${grantId}, ${grantId}`, 'not-an-id'])('refuses malformed/duplicate issuance association %j without a new cookie', async (association) => {
    const session = createSessionFixture();
    fetchMock.mockResolvedValue(upstreamProof('complaint-moderation-mutation', { 'X-Kira-Admin-Step-Up-Grant-Id': association }));
    const { POST } = await import('./step-up/route');
    const response = await POST(new Request(origin + '/api/auth/step-up', { method: 'POST', headers: signedRequestHeaders(session), body: '{"password":"fixture","scope":"complaint-moderation-mutation"}' }));
    expect(response.status).toBe(502);
    expect(response.headers.getSetCookie()).toHaveLength(0);
  });

  it('makes every mounted credential consumer fail closed without a configured signing secret', async () => {
    const session: AdminSessionCookie = createSessionFixture();
    vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', undefined);
    const headers = signedRequestHeaders(session);
    const loginHandler = (await import('./login/route')).POST;
    const logoutHandler = (await import('./logout/route')).POST;
    const sessionHandler = (await import('./session/route')).GET;
    const stepUpHandler = (await import('./step-up/route')).POST;
    const proxyHandler = (await import('../backend/[...path]/route')).GET;
    const mediaHandler = (await import('../media/[id]/route')).GET;
    const responses = [
      await loginHandler(new Request(origin + '/api/auth/login', { method: 'POST', headers, body: '{}' })),
      await logoutHandler(new Request(origin + '/api/auth/logout', { method: 'POST', headers })),
      await sessionHandler(new Request(origin + '/api/auth/session', { headers })),
      await stepUpHandler(new Request(origin + '/api/auth/step-up', { method: 'POST', headers, body: '{"password":"fixture"}' })),
      await proxyHandler(new Request(origin + '/api/backend/sources', { headers }), { params: Promise.resolve({ path: ['sources'] }) }),
      await mediaHandler(new Request(origin + '/api/media/' + grantId + '?sessionGeneration=' + session.generation, { headers }), { params: Promise.resolve({ id: grantId }) }),
    ];
    for (const response of responses) {
      expect(response.status).toBe(503);
      expect(await response.json()).toEqual({ detail: 'Admin authentication is temporarily unavailable.' });
      expect(response.headers.getSetCookie()).toHaveLength(0);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
