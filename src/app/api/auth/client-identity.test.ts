import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Only the Next request-cookie boundary and upstream transport are mocked. The handlers,
// config, identity parsing, Origin/CSRF checks and NextResponse cookie serialization are real.
const cookieBoundary = vi.hoisted(() => {
  const values = new Map<string, string>();
  const get = vi.fn((name: string) => {
    const value = values.get(name);
    return value === undefined ? undefined : { name, value };
  });
  return { values, get, cookies: vi.fn(async () => ({ get })) };
});

vi.mock('next/headers', () => ({ cookies: cookieBoundary.cookies }));

type AuthRoute = 'login' | 'step-up';
const authRoutes: AuthRoute[] = ['login', 'step-up'];
const adminOrigin = 'https://admin.example.test';
const sessionToken = 'fixture-only-session-jwt';
const csrfToken = 'fixture-only-csrf-token';
const proofToken = 'fixture-only-step-up-proof';
const requestBodies = {
  login: JSON.stringify({ email: 'admin@example.test', password: 'fixture-only-password' }),
  'step-up': JSON.stringify({ password: 'fixture-only-password' }),
};
const backendPaths = { login: '/api/v1/auth/login', 'step-up': '/api/v1/admin/step-up' };
const fetchMock = vi.fn<typeof fetch>();
const spoofedHeaders = {
  'X-Forwarded-For': '203.0.113.200, 198.51.100.200',
  Forwarded: 'for=203.0.113.201;by=attacker',
  Authorization: 'Bearer attacker-selected-token',
  'X-Kira-Admin-Step-Up': 'attacker-selected-proof',
  'X-Arbitrary': 'must-not-reach-backend',
  'X-Forwarded-Host': 'attacker.example.test',
  'X-Forwarded-Proto': 'http',
  Host: 'attacker.example.test',
  Accept: 'text/html',
  'Content-Type': 'text/plain',
};

function validHeaders(extra: HeadersInit = {}) {
  const headers = new Headers({
    Origin: adminOrigin,
    'Sec-Fetch-Site': 'same-origin',
    'Content-Type': 'application/json',
    'X-Kira-Csrf': csrfToken,
    'X-Real-IP': '192.0.2.1',
    Cookie: [...cookieBoundary.values].map(([name, value]) => `${name}=${value}`).join('; '),
  });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return headers;
}

function authRequest(route: AuthRoute, headers = validHeaders()) {
  return new Request(`${adminOrigin}/api/auth/${route}`, {
    method: 'POST', headers, body: requestBodies[route],
  });
}

async function loadHandler(route: AuthRoute) {
  return route === 'login' ? (await import('./login/route')).POST : (await import('./step-up/route')).POST;
}

function mockSuccess(route: AuthRoute) {
  fetchMock.mockImplementation(async () => Response.json(route === 'login' ? {
    accessToken: sessionToken, expiresInSeconds: 600, role: 'ADMIN',
  } : {
    token: proofToken, expiresAt: new Date(Date.now() + 300_000).toISOString(), scope: 'SOURCE_CONFIG_WRITE',
  }));
}

function expectUpstream(route: AuthRoute, identity: string | null, index = 0, backend = 'http://backend:8080') {
  const [url, options] = fetchMock.mock.calls[index];
  expect(url).toBe(backend + backendPaths[route]);
  expect(options).toEqual({
    method: 'POST',
    headers: expect.any(Object),
    body: requestBodies[route],
    cache: 'no-store',
    ...(route === 'step-up' ? { signal: expect.any(AbortSignal) } : {}),
  });
  expect(Object.fromEntries(new Headers(options?.headers))).toEqual({
    accept: route === 'login' ? 'application/json' : 'application/json, application/problem+json',
    'content-type': 'application/json',
    ...(route === 'step-up' ? { authorization: `Bearer ${sessionToken}` } : {}),
    ...(identity ? { 'x-forwarded-for': identity } : {}),
  });
}

function responseCookie(response: Response, name: string) {
  const cookie = response.headers.getSetCookie().find((value) => value.startsWith(`${name}=`));
  if (!cookie) throw new Error(`Expected the ${name} response cookie.`);
  return cookie;
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('NODE_ENV', 'production');
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'true');
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_ORIGIN', adminOrigin);
  cookieBoundary.values.clear();
  cookieBoundary.values.set('kira_admin_session', sessionToken);
  cookieBoundary.values.set('kira_admin_csrf', csrfToken);
  cookieBoundary.get.mockClear();
  cookieBoundary.cookies.mockClear();
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe.each(authRoutes)('real %s authentication handler', (route) => {
  it.each([
    { family: 'IPv4', clients: [
      ['192.0.2.1', '192.0.2.1'],
      ['198.51.100.2', '198.51.100.2'],
    ] },
    { family: 'IPv6', clients: [
      ['2001:0DB8:0:0:0001::0001', '2001:db8:0:0:1:0:0:1'],
      ['2001:db8::2', '2001:db8:0:0:0:0:0:2'],
    ] },
  ])('keeps two $family clients distinct using only fresh canonical XFF', async ({ clients }) => {
    const post = await loadHandler(route);
    mockSuccess(route);

    for (const [index, [input, expected]] of clients.entries()) {
      const response = await post(authRequest(route, validHeaders({ ...spoofedHeaders, 'X-Real-IP': input })));
      expect(response.status).toBe(200);
      expectUpstream(route, expected, index);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const identities = fetchMock.mock.calls.map(([, options]) => new Headers(options?.headers).get('x-forwarded-for'));
    expect(new Set(identities).size).toBe(2);
  });

  it.each([
    ['::ffff:192.0.2.1', '192.0.2.1'],
    ['::FFFF:c000:0201', '192.0.2.1'],
    ['::192.0.2.1', '0:0:0:0:0:0:c000:201'],
    ['::ffff:0:192.0.2.1', '0:0:0:0:ffff:0:c000:201'],
  ])('applies the shared mapped/compatible IPv6 contract to %s', async (input, expected) => {
    const post = await loadHandler(route);
    mockSuccess(route);
    const response = await post(authRequest(route, validHeaders({ ...spoofedHeaders, 'X-Real-IP': input })));

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, expected);
  });

  it('does not let changes to caller XFF or Forwarded choose a different identity', async () => {
    const post = await loadHandler(route);
    mockSuccess(route);
    for (const [index, spoof] of ['203.0.113.1', '203.0.113.2'].entries()) {
      const response = await post(authRequest(route, validHeaders({
        ...spoofedHeaders, 'X-Forwarded-For': spoof, Forwarded: `for=${spoof}`,
      })));
      expect(response.status).toBe(200);
      expectUpstream(route, '192.0.2.1', index);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it.each([undefined, 'false'])('is header-blind in production with trust %s and a configurable backend', async (setting) => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', setting);
    vi.stubEnv('KIRA_BACKEND_URL', 'https://direct-api.example.test/custom/');
    const post = await loadHandler(route);
    mockSuccess(route);
    const response = await post(authRequest(route, validHeaders(spoofedHeaders)));

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, null, 0, 'https://direct-api.example.test/custom');
  });

  it.each([
    ['', 'empty'],
    ['192.0.2.1, 198.51.100.1', 'list'],
    ['192.0.02.1', 'leading-zero IPv4'],
    ['2001:::1', 'malformed IPv6'],
    ['fe80::1%eth0', 'zone'],
    ['[2001:db8::1]', 'brackets'],
    ['[2001:db8::1]:443', 'IPv6 endpoint'],
    ['192.0.2.1:443', 'IPv4 endpoint'],
    ['attacker.example.test', 'hostname'],
    ['192.0.2.1 198.51.100.1', 'embedded whitespace'],
    ['é::1', 'non-ASCII'],
    ['1'.repeat(46), 'oversized'],
  ])('falls back to the unforwarded BFF peer for %s (%s)', async (input) => {
    const post = await loadHandler(route);
    mockSuccess(route);
    const response = await post(authRequest(route, validHeaders({ ...spoofedHeaders, 'X-Real-IP': input })));

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, null);
  });

  it('rejects duplicate X-Real-IP fields even if they repeat the same numeric identity', async () => {
    const post = await loadHandler(route);
    mockSuccess(route);
    const headers = validHeaders(spoofedHeaders);
    headers.append('X-Real-IP', '192.0.2.1');
    expect(headers.get('x-real-ip')).toBe('192.0.2.1, 192.0.2.1');
    const response = await post(authRequest(route, headers));

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, null);
  });

  it('leaves missing metadata in a degraded shared-peer bucket, not distinct-client isolation', async () => {
    const post = await loadHandler(route);
    mockSuccess(route);
    for (const [index, spoof] of ['203.0.113.1', '203.0.113.2'].entries()) {
      const headers = validHeaders({ ...spoofedHeaders, 'X-Forwarded-For': spoof, Forwarded: `for=${spoof}` });
      headers.delete('x-real-ip');
      const response = await post(authRequest(route, headers));
      expect(response.status).toBe(200);
      expectUpstream(route, null, index);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect([...new Headers(fetchMock.mock.calls[0][1]?.headers)]).toEqual([
      ...new Headers(fetchMock.mock.calls[1][1]?.headers),
    ]);
  });

  it.each(['missing', 'wrong', 'cross-site'])('retains real %s Origin refusal before fetch or cookie access', async (failure) => {
    const post = await loadHandler(route);
    const headers = validHeaders(spoofedHeaders);
    if (failure === 'missing') headers.delete('origin');
    if (failure === 'wrong') headers.set('origin', 'https://attacker.example.test');
    if (failure === 'cross-site') headers.set('sec-fetch-site', 'cross-site');
    const response = await post(authRequest(route, headers));

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ detail: 'Cross-site request rejected.' });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(cookieBoundary.cookies).not.toHaveBeenCalled();
    expect(cookieBoundary.get).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it('preserves an upstream refusal without issuing cookies or forwarding upstream private headers', async () => {
    const post = await loadHandler(route);
    fetchMock.mockResolvedValue(Response.json({ detail: 'Fixture authentication refused.' }, {
      status: 429,
      headers: { 'Content-Type': 'application/problem+json', 'Set-Cookie': 'upstream=private', 'X-Private': 'private' },
    }));
    const response = await post(authRequest(route, validHeaders(spoofedHeaders)));

    expect(response.status).toBe(429);
    expect(await response.json()).toEqual({ detail: 'Fixture authentication refused.' });
    expect(response.headers.get('content-type')).toBe('application/problem+json');
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(response.headers.get('x-private')).toBeNull();
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, '192.0.2.1');
  });
});

describe('real authentication security and cookie boundaries', () => {
  it('keeps same-origin login bootstrap CSRF-free and returns JWT only in the HttpOnly session cookie', async () => {
    cookieBoundary.values.clear();
    const post = await loadHandler('login');
    mockSuccess('login');
    const headers = validHeaders(spoofedHeaders);
    headers.delete('x-kira-csrf');
    const response = await post(authRequest('login', headers));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ role: 'ADMIN', expiresInSeconds: 600 });
    expect(cookieBoundary.cookies).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream('login', '192.0.2.1');
    expect(response.headers.getSetCookie()).toHaveLength(2);
    const session = responseCookie(response, 'kira_admin_session');
    expect(session).toContain(`kira_admin_session=${sessionToken};`);
    expect(session).toContain('HttpOnly');
    expect(session).toContain('SameSite=strict');
    expect(session).toContain('Secure');
    expect(session).toContain('Path=/;');
    expect(session).toContain('Max-Age=600');
    const csrf = responseCookie(response, 'kira_admin_csrf');
    expect(csrf).toMatch(/^kira_admin_csrf=[A-Za-z0-9_-]{43};/);
    expect(csrf).not.toContain('HttpOnly');
    expect(csrf).toContain('SameSite=strict');
    expect(csrf).toContain('Secure');
    expect(csrf).toContain('Path=/;');
    expect(csrf).toContain('Max-Age=600');
  });

  it.each(['USER', 'admin', ''])('rejects upstream role %j before setting session or CSRF cookies', async (role) => {
    const post = await loadHandler('login');
    fetchMock.mockResolvedValue(Response.json({ accessToken: sessionToken, expiresInSeconds: 600, role }));
    const response = await post(authRequest('login'));

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ detail: 'This dashboard requires an administrator account.' });
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream('login', '192.0.2.1');
  });

  it.each(['missing cookie', 'missing header', 'wrong same-length token', 'wrong length'])
  ('retains real step-up CSRF refusal for %s before session lookup or fetch', async (failure) => {
    const post = await loadHandler('step-up');
    if (failure === 'missing cookie') cookieBoundary.values.delete('kira_admin_csrf');
    const headers = validHeaders(spoofedHeaders);
    if (failure === 'missing header') headers.delete('x-kira-csrf');
    if (failure === 'wrong same-length token') headers.set('x-kira-csrf', 'x'.repeat(csrfToken.length));
    if (failure === 'wrong length') headers.set('x-kira-csrf', 'wrong');
    const response = await post(authRequest('step-up', headers));

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ detail: 'Invalid request token.' });
    expect(cookieBoundary.get.mock.calls).toEqual([['kira_admin_csrf']]);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it('requires a real step-up session cookie, never the incoming Authorization header', async () => {
    cookieBoundary.values.delete('kira_admin_session');
    const post = await loadHandler('step-up');
    const response = await post(authRequest('step-up', validHeaders(spoofedHeaders)));

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({ detail: 'Not signed in.' });
    expect(cookieBoundary.get.mock.calls).toEqual([['kira_admin_csrf'], ['kira_admin_session']]);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it.each([
    { label: 'already expired', offsetMs: -60_000, ttl: 1 },
    { label: 'overlong', offsetMs: 3_600_000, ttl: 900 },
  ])('keeps $label proof HttpOnly, path-scoped, no-store and TTL-bounded', async ({ offsetMs, ttl }) => {
    const post = await loadHandler('step-up');
    const expiresAt = new Date(Date.now() + offsetMs).toISOString();
    fetchMock.mockResolvedValue(Response.json({ token: proofToken, expiresAt, scope: 'SOURCE_CONFIG_WRITE' }));
    const response = await post(authRequest('step-up', validHeaders(spoofedHeaders)));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ expiresAt, scope: 'SOURCE_CONFIG_WRITE' });
    expect(response.headers.get('cache-control')).toBe('no-store');
    expect(response.headers.getSetCookie()).toHaveLength(1);
    const proof = responseCookie(response, 'kira_admin_step_up');
    expect(proof).toContain(`kira_admin_step_up=${proofToken};`);
    expect(proof).toContain('HttpOnly');
    expect(proof).toContain('SameSite=strict');
    expect(proof).toContain('Secure');
    expect(proof).toContain('Path=/api/backend;');
    expect(proof).toContain(`Max-Age=${ttl};`);
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream('step-up', '192.0.2.1');
  });
});

describe('unchanged real generic BFF boundary', () => {
  it('does not forward client identity outside the two password handlers even when trust is enabled', async () => {
    const { GET } = await import('../backend/[...path]/route');
    fetchMock.mockResolvedValue(Response.json({ entries: [] }));
    const response = await GET(new Request(`${adminOrigin}/api/backend/audit?limit=1`, {
      headers: validHeaders(spoofedHeaders),
    }), { params: Promise.resolve({ path: ['audit'] }) });

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://backend:8080/api/v1/admin/audit?limit=1');
    expect(options).toMatchObject({ method: 'GET', cache: 'no-store', signal: expect.any(AbortSignal) });
    expect(options?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(options?.headers))).toEqual({
      accept: 'application/json, application/problem+json',
      authorization: `Bearer ${sessionToken}`,
      'content-type': 'text/plain',
    });
  });

  it('still denies a non-allowlisted mutation before cookies or fetch', async () => {
    const { POST } = await import('../backend/[...path]/route');
    const response = await POST(new Request(`${adminOrigin}/api/backend/documents/republish`, {
      method: 'POST', headers: validHeaders(spoofedHeaders), body: '{}',
    }), { params: Promise.resolve({ path: ['documents', 'republish'] }) });

    expect(response.status).toBe(404);
    expect(await response.json()).toEqual({ detail: 'Admin route is not allowed.' });
    expect(cookieBoundary.cookies).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('still requires real CSRF for an allowed mutation', async () => {
    const { PUT } = await import('../backend/[...path]/route');
    const headers = validHeaders(spoofedHeaders);
    headers.delete('x-kira-csrf');
    const response = await PUT(new Request(`${adminOrigin}/api/backend/sources/Azora/editor-draft`, {
      method: 'PUT', headers, body: '{}',
    }), { params: Promise.resolve({ path: ['sources', 'Azora', 'editor-draft'] }) });

    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ detail: 'Invalid request token.' });
    expect(cookieBoundary.get.mock.calls).toEqual([['kira_admin_csrf']]);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
