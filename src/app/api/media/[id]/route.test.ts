import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Keep the GET handler and server config real; mock only request cookies and upstream fetch.
const cookieBoundary = vi.hoisted(() => {
  const get = vi.fn<(name: string) => { name: string; value: string } | undefined>();
  return { get, cookies: vi.fn(async () => ({ get })) };
});

vi.mock('next/headers', () => ({ cookies: cookieBoundary.cookies }));

const mediaId = 'b6d2ae21-1fab-4db6-9abf-7fb9a5e50cf1';
const sessionToken = 'fixture-only-media-session-jwt';
const mediaBytes = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 255]);
const etag = '"fixture-media-checksum"';
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'false');
  cookieBoundary.get.mockReset();
  cookieBoundary.get.mockImplementation((name) => (
    name === 'kira_admin_session' ? { name, value: sessionToken } : undefined
  ));
  cookieBoundary.cookies.mockClear();
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  cookieBoundary.get.mockReset();
  cookieBoundary.cookies.mockClear();
  fetchMock.mockReset();
  vi.resetModules();
});

describe('real media GET cache-policy passthrough', () => {
  it.each([
    { label: 'unpublished ADMIN media', policy: 'private, no-store' },
    { label: 'published media', policy: 'public, max-age=31536000, immutable' },
  ])('preserves $label policy and bytes without exposing the cookie token', async ({ policy }) => {
    // Mocked 200 passthrough only: this BFF does not forward If-None-Match.
    fetchMock.mockResolvedValue(new Response(mediaBytes, {
      status: 200,
      headers: {
        'Content-Type': 'image/png',
        'Content-Length': mediaBytes.byteLength.toString(),
        ETag: etag,
        'Cache-Control': policy,
        'Set-Cookie': 'upstream=' + sessionToken,
        'X-Upstream-Token': sessionToken,
      },
    }));
    const { GET } = await import('./route');
    const response = await GET(new Request('https://admin.example.test/api/media/' + mediaId, {
      headers: { Authorization: 'Bearer caller-must-not-be-forwarded' },
    }), { params: Promise.resolve({ id: mediaId }) });

    expect(cookieBoundary.cookies).toHaveBeenCalledOnce();
    expect(cookieBoundary.get.mock.calls).toEqual([['kira_admin_session']]);
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith('http://backend:8080/api/v1/tutorial-media/' + mediaId, {
      headers: { Authorization: 'Bearer ' + sessionToken },
      cache: 'no-store',
    });
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe(policy);
    expect(response.headers.get('etag')).toBe(etag);
    expect(response.headers.get('content-type')).toBe('image/png');
    expect(response.headers.get('content-length')).toBe(mediaBytes.byteLength.toString());
    expect([...response.headers.keys()].sort()).toEqual(['cache-control', 'content-length', 'content-type', 'etag']);
    for (const value of response.headers.values()) expect(value).not.toContain(sessionToken);
    const body = new Uint8Array(await response.arrayBuffer());
    expect(body).toEqual(mediaBytes);
    expect(new TextDecoder().decode(body)).not.toContain(sessionToken);
  });
});
