import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.resetModules();
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => { vi.unstubAllGlobals(); });

describe('apiFetchWithMeta additive history metadata', () => {
  it('keeps the raw array and ETag while returning a decimal-string cursor without Long precision loss', async () => {
    const { apiFetchWithMeta } = await import('./client-api');
    const data = [{ revisionNumber: 14 }];
    const cursor = '9007199254740993';
    fetchMock.mockResolvedValue(Response.json(data, { headers: { ETag: '"history"', 'X-Kira-History-Next-Before': cursor } }));
    expect(await apiFetchWithMeta<typeof data>(`documents?size=20&beforeRevision=${cursor}`)).toEqual({
      data, etag: '"history"', historyNextBefore: cursor,
    });
    expect(fetchMock.mock.calls[0][0]).toBe(`/api/backend/documents?size=20&beforeRevision=${cursor}`);
    expect(fetchMock.mock.calls[0][1]?.cache).toBe('no-store');
  });

  it('omits missing metadata and keeps existing typed data/etag request mocks assignable', async () => {
    const { apiFetchWithMeta } = await import('./client-api');
    const data = { id: 'fixture' };
    fetchMock.mockResolvedValue(Response.json(data));
    expect(await apiFetchWithMeta<typeof data>('sources')).toEqual({ data, etag: null });
    // DraftRequest/ChangesetRequest use this same generic function type.
    const existingRequest: typeof apiFetchWithMeta<typeof data> = async () => ({ data, etag: '"draft-4"' });
    expect(await existingRequest('sources/fixture/editor-draft')).toEqual({ data, etag: '"draft-4"' });
  });

  it('preserves 204 data and ETag without trying to parse an absent body', async () => {
    const { apiFetchWithMeta } = await import('./client-api');
    fetchMock.mockResolvedValue(new Response(null, { status: 204, headers: { ETag: '"draft-5"' } }));
    expect(await apiFetchWithMeta<void>('sources/fixture/editor-draft', { method: 'DELETE' })).toEqual({
      data: undefined, etag: '"draft-5"',
    });
  });

  it('leaves apiFetch callers data-only even when history metadata exists', async () => {
    const { apiFetch } = await import('./client-api');
    fetchMock.mockResolvedValue(Response.json([{ revisionNumber: 20 }], { headers: { 'X-Kira-History-Next-Before': '20' } }));
    expect(await apiFetch('sources/fixture/revisions?size=20')).toEqual([{ revisionNumber: 20 }]);
  });

  it('preserves session CSRF, JSON content type, If-Match and caller abort signal on mutations', async () => {
    const { apiFetchWithMeta, sessionFetch } = await import('./client-api');
    fetchMock.mockResolvedValueOnce(Response.json({ csrfToken: 'fixture-only-csrf' }));
    await sessionFetch();
    fetchMock.mockResolvedValueOnce(Response.json({ id: 'draft' }, { headers: { ETag: '"draft-5"' } }));
    const controller = new AbortController();
    const body = JSON.stringify({ content: '{"api":"Azora"}' });
    await apiFetchWithMeta('/sources/Azora/editor-draft', {
      method: 'PUT', body, headers: { 'If-Match': '"draft-4"' }, signal: controller.signal,
    });
    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe('/api/backend/sources/Azora/editor-draft');
    expect(init).toMatchObject({ method: 'PUT', body, cache: 'no-store', signal: controller.signal });
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({
      'content-type': 'application/json', 'if-match': '"draft-4"', 'x-kira-csrf': 'fixture-only-csrf',
    });
  });

  it.each([
    { status: 409, body: JSON.stringify({ detail: 'Draft version conflict.', title: 'Ignored title' }), message: 'Draft version conflict.' },
    { status: 400, body: JSON.stringify({ fieldErrors: [{ message: 'Invalid revision.' }] }), message: 'Invalid revision.' },
    { status: 502, body: 'not JSON', message: 'Request failed (502)' },
  ])('preserves ApiError status/message at $status instead of returning metadata', async ({ status, body, message }) => {
    const { apiFetchWithMeta, ApiError } = await import('./client-api');
    fetchMock.mockResolvedValue(new Response(body, { status, headers: { 'X-Kira-History-Next-Before': '14' } }));
    const request = apiFetchWithMeta('sources/fixture/revisions?size=20');
    await expect(request).rejects.toBeInstanceOf(ApiError);
    await expect(request).rejects.toMatchObject({ status, message });
  });
});
