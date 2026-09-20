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
const proofToken = 'A'.repeat(43); // Synthetic canonical encoding of exactly 32 bytes, not a real grant.
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
  'Content-Type': 'application/json',
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

function authRequest(route: AuthRoute, headers = validHeaders(), body: BodyInit = requestBodies[route], signal?: AbortSignal) {
  const init: RequestInit & { duplex?: 'half' } = { method: 'POST', headers, body, signal };
  if (body instanceof ReadableStream) init.duplex = 'half';
  return new Request(`${adminOrigin}/api/auth/${route}`, init);
}

function stepUpProof(scope = 'source-admin-mutation') {
  return { token: proofToken, expiresAt: new Date(Date.now() + 300_000).toISOString(), scope };
}

async function loadHandler(route: AuthRoute) {
  return route === 'login' ? (await import('./login/route')).POST : (await import('./step-up/route')).POST;
}

function mockSuccess(route: AuthRoute) {
  fetchMock.mockImplementation(async () => Response.json(route === 'login' ? {
    accessToken: sessionToken, expiresInSeconds: 600, role: 'ADMIN',
  } : stepUpProof()));
}

function expectUpstream(route: AuthRoute, identity: string | null, index = 0, backend = 'http://backend:8080') {
  const [url, options] = fetchMock.mock.calls[index];
  expect(url).toBe(backend + backendPaths[route]);
  expect(options).toEqual({
    method: 'POST',
    headers: expect.any(Object),
    body: requestBodies[route],
    cache: 'no-store',
    ...(route === 'step-up' ? { signal: expect.any(AbortSignal), redirect: 'manual' } : {}),
  });
  expect(Object.fromEntries(new Headers(options?.headers))).toEqual({
    accept: route === 'login' ? 'application/json' : 'application/json, application/problem+json',
    'content-type': 'application/json',
    ...(route === 'step-up' ? { authorization: `Bearer ${sessionToken}`, 'accept-encoding': 'identity' } : {}),
    ...(identity ? { 'x-forwarded-for': identity } : {}),
  });
}

function responseCookie(response: Response, name: string) {
  const cookie = response.headers.getSetCookie().find((value) => value.startsWith(`${name}=`));
  if (!cookie) throw new Error(`Expected the ${name} response cookie.`);
  return cookie;
}

function expectExpiredProofCookies(response: Response) {
  for (const name of ['kira_admin_step_up', 'kira_admin_complaint_step_up']) {
    const cookie = responseCookie(response, name);
    for (const attribute of [`${name}=;`, 'Path=/api/backend;', 'Expires=Thu, 01 Jan 1970 00:00:00 GMT', 'Max-Age=0', 'HttpOnly', 'SameSite=strict', 'Secure']) {
      expect(cookie).toContain(attribute);
    }
    expect(cookie).not.toContain('Domain=');
  }
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
  cookieBoundary.values.set('kira_admin_step_up', 'old-source-proof');
  cookieBoundary.values.set('kira_admin_complaint_step_up', 'old-complaint-proof');
  cookieBoundary.get.mockClear();
  cookieBoundary.cookies.mockClear();
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.useRealTimers();
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

  it('preserves an upstream refusal without setting/clearing cookies or forwarding upstream private headers', async () => {
    const post = await loadHandler(route);
    fetchMock.mockResolvedValue(Response.json({ detail: 'Fixture authentication refused.' }, {
      status: 429,
      headers: { 'Content-Type': 'application/problem+json', 'Set-Cookie': 'upstream=private', 'X-Private': 'private' },
    }));
    const response = await post(authRequest(route, validHeaders(spoofedHeaders)));

    expect(response.status).toBe(429);
    expect(await response.json()).toEqual({ detail: route === 'step-up' ? 'Too many attempts. Try again later.' : 'Fixture authentication refused.' });
    expect(response.headers.get('content-type')).toBe('application/problem+json');
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(response.headers.get('x-private')).toBeNull();
    expect(fetchMock).toHaveBeenCalledOnce();
    expectUpstream(route, '192.0.2.1');
  });
});

describe('real authentication security and cookie boundaries', () => {
  it.each([false, true])('keeps ADMIN login CSRF-free, JWT HttpOnly, and resets both proof scopes (prior session: %s)', async (priorSession) => {
    if (!priorSession) cookieBoundary.values.clear();
    else cookieBoundary.values.set('kira_admin_session', 'old-fixture-only-session');
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
    expect(response.headers.getSetCookie()).toHaveLength(4);
    expectExpiredProofCookies(response);
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

  it('expires both proof paths on successful logout while retaining the session/CSRF deletion contract', async () => {
    const { POST } = await import('./logout/route');
    const response = await POST(new Request(`${adminOrigin}/api/auth/logout`, { method: 'POST', headers: validHeaders() }));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ok: true });
    expect(response.headers.getSetCookie()).toHaveLength(4);
    expectExpiredProofCookies(response);
    for (const name of ['kira_admin_session', 'kira_admin_csrf']) {
      const cookie = responseCookie(response, name);
      expect(cookie).toContain(`${name}=;`);
      expect(cookie).toContain('Path=/;');
      expect(cookie).toContain('Expires=Thu, 01 Jan 1970 00:00:00 GMT');
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(['wrong origin', 'missing CSRF cookie', 'missing CSRF header', 'wrong CSRF token'])
  ('never expires either proof on logout refusal: %s', async (failure) => {
    const { POST } = await import('./logout/route');
    if (failure === 'missing CSRF cookie') cookieBoundary.values.delete('kira_admin_csrf');
    const headers = validHeaders();
    if (failure === 'wrong origin') headers.set('origin', 'https://attacker.example.test');
    if (failure === 'missing CSRF header') headers.delete('x-kira-csrf');
    if (failure === 'wrong CSRF token') headers.set('x-kira-csrf', 'x'.repeat(csrfToken.length));
    const response = await POST(new Request(`${adminOrigin}/api/auth/logout`, { method: 'POST', headers }));

    expect(response.status).toBe(403);
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(cookieBoundary.values.get('kira_admin_step_up')).toBe('old-source-proof');
    expect(cookieBoundary.values.get('kira_admin_complaint_step_up')).toBe('old-complaint-proof');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(['USER', 'admin', ''])('rejects upstream role %j without setting or clearing any cookies', async (role) => {
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
    expect(response.headers.get('www-authenticate')).toBe('KiraSession realm="kira-admin-bff"');
    expect(cookieBoundary.get.mock.calls).toEqual([['kira_admin_csrf'], ['kira_admin_session']]);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it.each([
    { label: 'fresh', offsetMs: 300_000, ttl: 300 },
    { label: 'overlong', offsetMs: 3_600_000, ttl: 900 },
  ])('keeps $label proof HttpOnly, path-scoped, no-store and TTL-bounded', async ({ offsetMs, ttl }) => {
    vi.useFakeTimers();
    const post = await loadHandler('step-up');
    const expiresAt = new Date(Date.now() + offsetMs).toISOString();
    fetchMock.mockResolvedValue(Response.json({ token: proofToken, expiresAt, scope: 'source-admin-mutation' }));
    const response = await post(authRequest('step-up', validHeaders(spoofedHeaders)));

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ expiresAt, scope: 'source-admin-mutation' });
    expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
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

describe('bounded scoped step-up issuance only', () => {
  it.each([undefined, 'source-admin-mutation', 'complaint-moderation-mutation'])
  ('selects only the requested cookie for scope %s without changing the password value', async (scope) => {
    const post = await loadHandler('step-up');
    const selected = scope ?? 'source-admin-mutation';
    const proof = stepUpProof(selected);
    cookieBoundary.values.set('kira_admin_step_up', 'old-source-proof');
    cookieBoundary.values.set('kira_admin_complaint_step_up', 'old-complaint-proof');
    fetchMock.mockResolvedValue(Response.json(proof));
    const password = ' \tfixture-only-password\n ';
    const response = await post(authRequest('step-up', validHeaders(spoofedHeaders), JSON.stringify({ password, scope })));

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][0]).toBe('http://backend:8080/api/v1/admin/step-up');
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ password,
      ...(selected === 'complaint-moderation-mutation' ? { scope: selected } : {}),
    }));
    expect(await response.json()).toEqual({ scope: selected, expiresAt: proof.expiresAt });
    const name = selected === 'source-admin-mutation' ? 'kira_admin_step_up' : 'kira_admin_complaint_step_up';
    expect(response.headers.getSetCookie()).toHaveLength(1);
    const cookie = responseCookie(response, name);
    for (const flag of ['HttpOnly', 'SameSite=strict', 'Secure', 'Path=/api/backend;']) expect(cookie).toContain(flag);
    expect(cookieBoundary.values.get('kira_admin_step_up')).toBe('old-source-proof');
    expect(cookieBoundary.values.get('kira_admin_complaint_step_up')).toBe('old-complaint-proof');
    for (const name of ['authorization', 'x-kira-admin-step-up', 'location']) expect(response.headers.get(name)).toBeNull();
  });

  it.each([
    ['syntax', '{'], ['non-object', '[]'], ['missing password', '{}'], ['wrong password type', '{"password":1}'],
    ['unknown scope', '{"password":"fixture","scope":"SOURCE_CONFIG_WRITE"}'],
    ['null scope', '{"password":"fixture","scope":null}'],
    ['duplicate decoded scope', '{"password":"fixture","scope":"source-admin-mutation","sc\\u006fpe":"complaint-moderation-mutation"}'],
    ['duplicate password', '{"password":"first","password":"second"}'],
    ['unknown field', '{"password":"fixture","token":"must-not-forward"}'],
    ['trailing input', '{"password":"fixture"}{}'], ['trailing comma', '{"password":"fixture",}'],
    ['oversize password', JSON.stringify({ password: 'x'.repeat(257) })],
  ])('refuses %s before any upstream request', async (_, raw) => {
    const post = await loadHandler('step-up');
    const response = await post(authRequest('step-up', validHeaders(), raw));
    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(await response.json()).toEqual({ detail: 'Invalid password verification request.' });
  });

  it('allows a fully escaped 256-character password and rejects malformed UTF-8 before fetch', async () => {
    const post = await loadHandler('step-up');
    mockSuccess('step-up');
    const raw = '{"password":"' + '\\u00e9'.repeat(256) + '","scope":"source-admin-mutation"}';
    expect((await post(authRequest('step-up', validHeaders(), raw))).status).toBe(200);
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ password: 'é'.repeat(256) }));
    fetchMock.mockClear();
    const response = await post(authRequest('step-up', validHeaders(), new Uint8Array([0xc3, 0x28])));
    expect(response.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it.each([
    [{ 'Content-Type': 'text/plain' }, 415], [{ 'Content-Encoding': 'gzip' }, 415],
    [{ 'Content-Length': '4097' }, 413], [{ 'Content-Length': '1, 1' }, 400], [{ 'Content-Length': '1' }, 400],
    [{ 'Transfer-Encoding': 'chunked', 'Content-Length': '1' }, 400],
  ] as const)('refuses request metadata %j before forwarding', async (headers, status) => {
    const post = await loadHandler('step-up');
    const response = await post(authRequest('step-up', validHeaders(headers)));
    expect(response.status).toBe(status);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it('collects the complete 4096-byte request and refuses a late excess byte before fetch', async () => {
    const post = await loadHandler('step-up');
    mockSuccess('step-up');
    const raw = requestBodies['step-up'].padEnd(4096, ' ');
    expect((await post(authRequest('step-up', validHeaders({ 'Content-Length': '4096' }), raw))).status).toBe(200);
    expectUpstream('step-up', '192.0.2.1');
    fetchMock.mockClear();
    const cancel = vi.fn();
    const body = new ReadableStream<Uint8Array>({ start(controller) {
      controller.enqueue(new TextEncoder().encode(raw));
      controller.enqueue(new Uint8Array([32]));
    }, cancel });
    const response = await post(authRequest('step-up', validHeaders({ 'Transfer-Encoding': 'chunked' }), body));
    expect(response.status).toBe(413);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(cancel).toHaveBeenCalledOnce();
    expect(body.locked).toBe(false);
    expect(response.headers.get('set-cookie')).toBeNull();
  });

  it.each(['source-admin-mutation', 'complaint-moderation-mutation'])('refuses the other returned scope for %s without fallback or cookie changes', async (scope) => {
    const post = await loadHandler('step-up');
    fetchMock.mockResolvedValue(Response.json(stepUpProof(scope === 'source-admin-mutation' ? 'complaint-moderation-mutation' : 'source-admin-mutation')));
    const response = await post(authRequest('step-up', validHeaders(), JSON.stringify({ password: 'fixture', scope })));
    expect(response.status).toBe(502);
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(await response.json()).toEqual({ detail: 'Password verification is temporarily unavailable.' });
  });

  it.each([
    { token: undefined }, { token: 42 }, { token: 'A'.repeat(42) }, { token: 'A'.repeat(44) },
    { token: 'A'.repeat(42) + 'B' }, { token: proofToken + '\n' }, { token: proofToken + '=' },
    { scope: undefined }, { scope: 'SOURCE_CONFIG_WRITE' }, { extra: 'must-not-forward' },
    { expiresAt: undefined }, { expiresAt: 42 }, { expiresAt: 'not-an-instant' }, { expiresAt: '2099' },
    { expiresAt: '2030-02-30T00:00:00Z' }, { expiresAt: '2030-01-01T00:00:00Z\n' },
    { expiresAt: '2000-01-01T00:00:00Z' },
  ])('refuses invalid upstream proof fields %j without issuing any cookie', async (fields) => {
    const post = await loadHandler('step-up');
    fetchMock.mockResolvedValue(Response.json({ ...stepUpProof(), ...fields }));
    const response = await post(authRequest('step-up'));
    expect(response.status).toBe(502);
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(await response.json()).toEqual({ detail: 'Password verification is temporarily unavailable.' });
  });

  it('rejects duplicate decoded proof fields and invalid UTF-8 without echoing a valid-looking token', async () => {
    const post = await loadHandler('step-up');
    const proof = stepUpProof();
    for (const body of [JSON.stringify(proof).slice(0, -1) + ',"sc\\u006fpe":"source-admin-mutation"}', new Uint8Array([0xc3, 0x28])]) {
      fetchMock.mockResolvedValueOnce(new Response(body, { headers: { 'Content-Type': 'application/json' } }));
      const response = await post(authRequest('step-up'));
      expect(response.status).toBe(502);
      expect(response.headers.get('set-cookie')).toBeNull();
      expect(await response.text()).not.toContain(proofToken);
    }
  });

  it('withholds every success byte/cookie until the bounded 32 KiB response completes', async () => {
    const post = await loadHandler('step-up');
    const raw = JSON.stringify(stepUpProof()).padEnd(32_768, ' ');
    fetchMock.mockResolvedValueOnce(new Response(raw, { headers: { 'Content-Type': 'application/json', 'Content-Length': '32768' } }));
    expect((await post(authRequest('step-up'))).status).toBe(200);
    for (const status of [200, 503]) {
      const cancel = vi.fn();
      const body = new ReadableStream<Uint8Array>({ start(controller) {
        controller.enqueue(new TextEncoder().encode(raw));
        controller.enqueue(new Uint8Array([32]));
      }, cancel });
      fetchMock.mockResolvedValueOnce(new Response(body, { status, headers: { 'Content-Type': 'application/json', 'Content-Length': '1' } }));
      const response = await post(authRequest('step-up'));
      expect(response.status).toBe(502);
      expect(response.headers.get('set-cookie')).toBeNull();
      expect(await response.json()).toEqual({ detail: 'Password verification is temporarily unavailable.' });
      expect(cancel).toHaveBeenCalledOnce();
      expect(body.locked).toBe(false);
    }
  });

  it.each([
    [302, { Location: 'https://other.example.test/private' }],
    [200, { 'Content-Encoding': 'gzip' }], [200, { 'Content-Type': 'text/html' }],
    [200, { 'Content-Length': '32769' }], [200, { 'Content-Length': '1' }], [201, {}],
  ] as const)('refuses upstream status/media/encoding/framing %s %j', async (status, headers) => {
    const post = await loadHandler('step-up');
    fetchMock.mockResolvedValue(Response.json(stepUpProof(), { status, headers }));
    const response = await post(authRequest('step-up'));
    expect(response.status).toBe(502);
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(response.headers.get('location')).toBeNull();
    expect(fetchMock.mock.calls[0][1]?.redirect).toBe('manual');
  });

  it.each([401, 429, 503])('keeps bounded upstream refusal %s without secret prose or cookie replacement', async (status) => {
    const post = await loadHandler('step-up');
    fetchMock.mockResolvedValue(Response.json({ detail: 'private password/proof http://backend:8080', token: proofToken }, {
      status, headers: { 'Set-Cookie': 'upstream=private', 'Retry-After': '1', 'WWW-Authenticate': 'Bearer error="private"' },
    }));
    const response = await post(authRequest('step-up', validHeaders(), JSON.stringify({ password: 'fixture', scope: 'complaint-moderation-mutation' })));
    expect(response.status).toBe(status);
    expect(await response.json()).toEqual({ detail: status === 429 ? 'Too many attempts. Try again later.' : 'Password verification failed.' });
    expect(response.headers.get('www-authenticate')).toBe(status === 401 ? 'Bearer' : null);
    expect(response.headers.get('retry-after')).toBe(status === 401 ? null : '1');
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it.each(['request', 'response'] as const)('ends a stalled %s stream at the original deadline, retaining existing cookies', async (phase) => {
    vi.useFakeTimers();
    const post = await loadHandler('step-up');
    cookieBoundary.values.set('kira_admin_step_up', 'retained-source');
    cookieBoundary.values.set('kira_admin_complaint_step_up', 'retained-complaint');
    const cancel = vi.fn(() => Promise.reject(new Error('private cleanup detail')));
    const body = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new TextEncoder().encode('{')); }, cancel });
    if (phase === 'response') fetchMock.mockResolvedValue(new Response(body, { headers: { 'Content-Type': 'application/json' } }));
    const work = post(authRequest('step-up', validHeaders(), phase === 'request' ? body : requestBodies['step-up']));
    await vi.advanceTimersByTimeAsync(0);
    expect(body.locked).toBe(true);
    await vi.advanceTimersByTimeAsync(15_000);
    const response = await work;
    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ detail: 'Password verification is temporarily unavailable.' });
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(cookieBoundary.values.get('kira_admin_step_up')).toBe('retained-source');
    expect(cookieBoundary.values.get('kira_admin_complaint_step_up')).toBe('retained-complaint');
    expect(fetchMock).toHaveBeenCalledTimes(phase === 'request' ? 0 : 1);
    expect(cancel).toHaveBeenCalledOnce();
    expect(body.locked).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('sanitizes transport failure and caller cancellation without retry or cookie changes', async () => {
    const post = await loadHandler('step-up');
    fetchMock.mockRejectedValue(new Error('private password/proof http://backend:8080'));
    const response = await post(authRequest('step-up'));
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: 'Password verification is temporarily unavailable.' });
    expect(response.headers.get('set-cookie')).toBeNull();
    expect(fetchMock).toHaveBeenCalledOnce();
    fetchMock.mockClear();
    const caller = new AbortController();
    caller.abort();
    expect((await post(authRequest('step-up', validHeaders(), requestBodies['step-up'], caller.signal))).status).toBe(502);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('unchanged real generic BFF boundary', () => {
  it('does not forward client identity outside the two password handlers even when trust is enabled', async () => {
    const { GET } = await import('../backend/[...path]/route');
    fetchMock.mockResolvedValue(Response.json({ entries: [] }));
    const response = await GET(new Request(`${adminOrigin}/api/backend/audit?limit=1`, {
      headers: validHeaders({ ...spoofedHeaders, 'Content-Type': 'text/plain' }),
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
