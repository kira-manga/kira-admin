import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { AdminSessionCookie } from '@/lib/server-session';
import { sessionGenerationHeader } from '@/lib/session-contract';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';

// Real signed-cookie/session and GET cache boundary; only upstream fetch is replaced.
let session: AdminSessionCookie;

const mediaId = 'b6d2ae21-1fab-4db6-9abf-7fb9a5e50cf1';
const sessionToken = 'fixture-only-media-session-jwt';
const mediaBytes = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 255]);
const etag = '"fixture-media-checksum"';
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'false');
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  session = createSessionFixture(sessionToken);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  fetchMock.mockReset();
  vi.resetModules();
});

describe('real media GET cache-policy passthrough', () => {
  it('supports an image GET with only a non-secret explicit query selector plus its signed cookie', async () => {
    const headers = signedRequestHeaders(session);
    headers.delete(sessionGenerationHeader);
    fetchMock.mockResolvedValue(new Response(mediaBytes, { headers: { 'Content-Type': 'image/png', 'Cache-Control': 'private, no-store' } }));
    const { GET } = await import('./route');
    const response = await GET(new Request(`https://admin.example.test/api/media/${mediaId}?sessionGeneration=${session.generation}`, { headers }), { params: Promise.resolve({ id: mediaId }) });
    expect(response.status).toBe(200);
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('Authorization')).toBe(`Bearer ${sessionToken}`);
    expect(response.headers.get('Cache-Control')).toBe('private, no-store');
  });

  it.each(['missing selector', 'missing signed cookie', 'duplicate query', 'mismatched header'])('refuses %s rather than falling back to another media session', async (failure) => {
    const headers = signedRequestHeaders(session);
    headers.delete(sessionGenerationHeader);
    let query = `?sessionGeneration=${session.generation}`;
    if (failure === 'missing selector') query = '';
    if (failure === 'missing signed cookie') headers.delete('cookie');
    if (failure === 'duplicate query') query += `&sessionGeneration=${session.generation}`;
    if (failure === 'mismatched header') headers.set(sessionGenerationHeader, '12345678-1234-4234-8234-123456789abc');
    const { GET } = await import('./route');
    const response = await GET(new Request(`https://admin.example.test/api/media/${mediaId}${query}`, { headers }), { params: Promise.resolve({ id: mediaId }) });
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(fetchMock).not.toHaveBeenCalled();
  });

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
    const response = await GET(new Request('https://admin.example.test/api/media/' + mediaId + '?sessionGeneration=' + session.generation, {
      headers: signedRequestHeaders(session, [], { Authorization: 'Bearer caller-must-not-be-forwarded' }),
    }), { params: Promise.resolve({ id: mediaId }) });

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith('http://backend:8080/api/v1/tutorial-media/' + mediaId, {
      headers: { Authorization: 'Bearer ' + sessionToken },
      cache: 'no-store', redirect: 'manual',
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
