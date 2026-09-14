import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Only Next's request-cookie boundary and the upstream transport are mocked.
// Route policy, CSRF/origin checks, header filtering and NextResponse are real.
const cookieBoundary = vi.hoisted(() => {
  const values = new Map<string, string>();
  const get = vi.fn((name: string) => {
    const value = values.get(name);
    return value === undefined ? undefined : { name, value };
  });
  return { values, get, cookies: vi.fn(async () => ({ get })) };
});

vi.mock('next/headers', () => ({ cookies: cookieBoundary.cookies }));

const adminOrigin = 'https://admin.example.test';
const sessionToken = 'fixture-only-session';
const csrfToken = 'fixture-only-csrf';
const proofToken = 'fixture-only-proof';
const cursorHeader = 'X-Kira-History-Next-Before';
const sourcePath = ['sources', 'Azora', 'revisions'];
const rawHistory = '[{"revisionNumber":14,"status":"draft"},{"revisionNumber":20,"valid":false}]';
const fetchMock = vi.fn<typeof fetch>();

function requestHeaders() {
  return new Headers({
    Origin: adminOrigin,
    'Sec-Fetch-Site': 'same-origin',
    'Content-Type': 'application/json',
    'X-Kira-CSRF': csrfToken,
    Authorization: 'Bearer attacker-selected-token',
    'X-Kira-Admin-Step-Up': 'attacker-selected-proof',
    'X-Arbitrary': 'must-not-reach-backend',
  });
}

async function proxy(path: string[], options: { method?: 'GET' | 'POST' | 'PUT'; query?: string; headers?: Headers; signal?: AbortSignal } = {}) {
  const handlers = await import('./route');
  const method = options.method ?? 'GET';
  return handlers[method](new Request(`${adminOrigin}/api/backend/${path.map(encodeURIComponent).join('/')}${options.query ?? ''}`, {
    method,
    headers: options.headers ?? requestHeaders(),
    ...(method === 'GET' ? {} : { body: '{}' }),
    signal: options.signal,
  }), { params: Promise.resolve({ path }) });
}

function historyResponse(cursor?: string, status = 200) {
  const headers = new Headers({
    'Content-Type': 'application/json',
    ETag: '"fixture-etag"',
    'Cache-Control': 'no-store',
    'Set-Cookie': 'private-upstream=must-not-forward',
    Authorization: 'private-upstream-token',
    'X-Kira-Admin-Step-Up': 'private-upstream-proof',
    'X-Arbitrary': 'must-not-forward',
    Link: '<https://outside.example.test/history>; rel="next"',
    Location: 'https://outside.example.test/history',
  });
  if (cursor !== undefined) headers.set(cursorHeader, cursor);
  return new Response(status === 304 ? null : rawHistory, { status, headers });
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('NODE_ENV', 'production');
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

describe('real history BFF response boundary', () => {
  it('preserves encoded segments, duplicate-bearing query bytes, raw array streaming and the narrow header allowlist', async () => {
    const path = ['sources', 'Azora /%?', 'revisions'];
    const query = '?size=020&beforeRevision=00014&fixture=a%2fb+z&fixture=second';
    const controller = new AbortController();
    const upstream = historyResponse('14');
    fetchMock.mockResolvedValue(upstream);

    const response = await proxy(path, { query, signal: controller.signal });

    expect(response.status).toBe(200);
    expect(response.body).toBe(upstream.body);
    expect(await response.text()).toBe(rawHistory);
    expect(Object.fromEntries(response.headers)).toEqual({
      'content-type': 'application/json', etag: '"fixture-etag"', 'cache-control': 'no-store',
      'x-kira-history-next-before': '14',
    });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://backend:8080/api/v1/admin/sources/Azora%20%2F%25%3F/revisions${query}`);
    expect(init).toMatchObject({ method: 'GET', cache: 'no-store', signal: expect.any(AbortSignal) });
    expect(init?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({
      accept: 'application/json, application/problem+json', authorization: `Bearer ${sessionToken}`, 'content-type': 'application/json',
    });
    controller.abort();
    expect(init?.signal?.aborted).toBe(true);
  });

  it('passes repeated recognized query values unchanged for the backend to reject', async () => {
    const query = '?size=20&size=2&beforeRevision=14&beforeRevision=9';
    fetchMock.mockResolvedValue(Response.json({ detail: 'Invalid history request.' }, { status: 400 }));
    const response = await proxy(sourcePath, { query });
    expect(fetchMock.mock.calls[0][0]).toBe(`http://backend:8080/api/v1/admin/sources/Azora/revisions${query}`);
    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({ detail: 'Invalid history request.' });
    expect(response.headers.get(cursorHeader)).toBeNull();
  });

  it.each([
    { path: sourcePath, cursor: '1' },
    { path: sourcePath, cursor: '2147483647' },
    { path: ['documents'], cursor: '9007199254740992' },
    { path: ['documents'], cursor: '9007199254740993' },
    { path: ['documents'], cursor: '9223372036854775807' },
  ])('forwards a lossless route-bounded scalar $cursor for $path', async ({ path, cursor }) => {
    fetchMock.mockResolvedValue(historyResponse(cursor));
    const response = await proxy(path);
    expect(response.headers.get(cursorHeader)).toBe(cursor);
    expect(await response.text()).toBe(rawHistory);
  });

  it.each([
    undefined, '', '0', '00', '01', '+1', '-1', '1.0', '1e3', '1 4', '1\t4', '\u00b9',
    '14, 14', 'https://outside.example.test/history', '1'.repeat(20),
  ])('does not create navigation metadata for absent/noncanonical header %j', async (cursor) => {
    fetchMock.mockResolvedValue(historyResponse(cursor));
    const response = await proxy(['documents']);
    expect(response.status).toBe(200);
    expect(response.headers.get(cursorHeader)).toBeNull();
    expect(await response.text()).toBe(rawHistory);
  });

  it.each([
    { path: sourcePath, cursor: '2147483648' },
    { path: sourcePath, cursor: '9007199254740993' },
    { path: ['documents'], cursor: '9223372036854775808' },
  ])('rejects the route-specific overflow $cursor for $path', async ({ path, cursor }) => {
    fetchMock.mockResolvedValue(historyResponse(cursor));
    expect((await proxy(path)).headers.get(cursorHeader)).toBeNull();
  });

  it('rejects repeated header fields even when both values are identical', async () => {
    const upstream = historyResponse('14');
    upstream.headers.append(cursorHeader, '14');
    expect(upstream.headers.get(cursorHeader)).toBe('14, 14');
    fetchMock.mockResolvedValue(upstream);
    expect((await proxy(sourcePath)).headers.get(cursorHeader)).toBeNull();
  });

  it.each([
    { path: ['sources'] }, { path: ['sources', 'Azora'] }, { path: ['sources', 'Azora', 'revisions', '14'] },
    { path: ['sources', 'Azora/revisions'] }, { path: ['documents', '14'] }, { path: ['documents', ''] }, { path: ['audit'] },
  ])('does not forward history metadata on another GET shape $path', async ({ path }) => {
    fetchMock.mockResolvedValue(historyResponse('14'));
    const response = await proxy(path);
    expect(response.status).toBe(200);
    expect(response.headers.get(cursorHeader)).toBeNull();
  });

  it.each([400, 404, 500, 304])('does not forward cursor metadata on an unsuccessful history GET (%i)', async (status) => {
    fetchMock.mockResolvedValue(historyResponse('14', status));
    const response = await proxy(sourcePath);
    expect(response.status).toBe(status);
    expect(response.headers.get(cursorHeader)).toBeNull();
  });

  it('does not forward cursor metadata on the allowed revision POST', async () => {
    fetchMock.mockResolvedValue(historyResponse('14'));
    const response = await proxy(sourcePath, { method: 'POST' });
    expect(response.status).toBe(200);
    expect(response.headers.get(cursorHeader)).toBeNull();
    expect(new TextDecoder().decode(fetchMock.mock.calls[0][1]?.body as ArrayBuffer)).toBe('{}');
  });
});

describe('unchanged real authorization and protected mutation boundaries', () => {
  it('does not use caller Authorization in place of the session cookie', async () => {
    cookieBoundary.values.delete('kira_admin_session');
    const response = await proxy(sourcePath);
    expect(response.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each(['origin', 'csrf'])('rejects a bad %s before a revision mutation reaches upstream', async (failure) => {
    const headers = requestHeaders();
    if (failure === 'origin') headers.set('Origin', 'https://outside.example.test');
    else headers.delete('X-Kira-CSRF');
    const response = await proxy(sourcePath, { method: 'POST', headers });
    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(cookieBoundary.get).not.toHaveBeenCalledWith('kira_admin_session');
  });

  it('still denies a nonallowlisted document mutation before cookies or transport', async () => {
    const response = await proxy(['documents', 'republish'], { method: 'POST' });
    expect(response.status).toBe(404);
    expect(cookieBoundary.cookies).not.toHaveBeenCalled();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([200, 409])('keeps protected proof/ETag forwarding and proof consumption at upstream status %i', async (status) => {
    cookieBoundary.values.set('kira_admin_step_up', proofToken);
    const headers = requestHeaders();
    headers.set('If-Match', '"draft-4"');
    fetchMock.mockResolvedValue(historyResponse('14', status));
    const response = await proxy(['sources', 'Azora', 'editor-draft', 'publish'], { method: 'POST', headers });

    expect(response.status).toBe(status);
    expect(Object.fromEntries(new Headers(fetchMock.mock.calls[0][1]?.headers))).toEqual({
      accept: 'application/json, application/problem+json', authorization: `Bearer ${sessionToken}`,
      'content-type': 'application/json', 'if-match': '"draft-4"', 'x-kira-admin-step-up': proofToken,
    });
    expect(response.headers.get(cursorHeader)).toBeNull();
    expect(response.headers.get('authorization')).toBeNull();
    expect(response.headers.get('x-kira-admin-step-up')).toBeNull();
    expect(response.headers.get('link')).toBeNull();
    expect(response.headers.get('location')).toBeNull();
    expect(response.headers.getSetCookie()).toHaveLength(1);
    expect(response.headers.getSetCookie()[0]).toMatch(/^kira_admin_step_up=;/);
    expect(response.headers.getSetCookie()[0]).toContain('Expires=Thu, 01 Jan 1970');
  });
});
