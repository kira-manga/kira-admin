import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureCsrf, fixtureGeneration, seedClientSession } from '@/test/auth-fixture';
import { complaintScope } from '@/test/complaint-mutation-fixture';
import { searchCursor, searchPage, searchResponse, searchVersion } from '@/test/complaint-search-fixture';
import { captureAdminSession } from './client-api';
import { fetchComplaintAdminSearch } from './complaint-read-client';

const fetchMock = vi.fn<typeof fetch>();
const bytes = (value: string) => new TextEncoder().encode(value);
const search = (signal = new AbortController().signal) => fetchComplaintAdminSearch({ dataScopeId: complaintScope }, signal);

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  vi.stubGlobal('fetch', fetchMock);
  await seedClientSession(); fetchMock.mockReset();
});
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('fixed same-origin complaint search client', () => {
  it('keeps filters/cursors in the POST body and uses selected G/CSRF without credentials, source approval or numeric loss', async () => {
    const response = searchResponse();
    const json = vi.spyOn(response, 'json'), buffer = vi.spyOn(response, 'arrayBuffer');
    fetchMock.mockResolvedValue(response);
    const loaded = await fetchComplaintAdminSearch({ dataScopeId: complaintScope, text: ' private\r\nquery ', cursor: searchCursor, limit: 25 }, new AbortController().signal);
    expect(loaded.items[0].version).toBe(searchVersion);
    expect(json).not.toHaveBeenCalled(); expect(buffer).not.toHaveBeenCalled();
    const [path, init] = fetchMock.mock.calls[0];
    expect(path).toBe('/api/backend/complaints/search');
    expect(init).toMatchObject({ method: 'POST', credentials: 'same-origin', redirect: 'error', cache: 'no-store' });
    expect(JSON.parse(init!.body as string)).toEqual({ dataScopeId: complaintScope, text: 'private\nquery', status: null, type: null, ownership: null,
      updatedFrom: null, updatedBefore: null, sort: 'UPDATED_DESC', limit: 25, cursor: searchCursor });
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({ accept: 'application/json, application/problem+json', 'content-type': 'application/json',
      'x-kira-complaint-contract': '1', 'x-kira-csrf': fixtureCsrf, 'x-kira-session-generation': fixtureGeneration });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('refuses local bad selections before fetch and never treats error/denial bodies as page data', async () => {
    await expect(fetchComplaintAdminSearch({ dataScopeId: complaintScope, limit: 51 }, new AbortController().signal)).rejects.toMatchObject({ reason: 'INVALID_RESPONSE' });
    expect(fetchMock).not.toHaveBeenCalled();
    const captured = captureAdminSession();
    for (const [status, challenge, reason] of [[401, null, 'UNAUTHORIZED'], [401, 'Bearer realm="kira-complaints"', 'UNAUTHORIZED'],
      [401, 'KiraSession realm="kira-admin-bff"', 'SESSION_EXPIRED'], [403, null, 'FORBIDDEN'], [400, null, 'INVALID_RESPONSE'], [503, null, 'UNAVAILABLE']] as const) {
      const cancel = vi.fn();
      const response = searchResponse(new ReadableStream({ start(output) { output.enqueue(bytes('private problem, not an empty page')); }, cancel }), status,
        challenge ? { 'WWW-Authenticate': challenge } : {});
      const read = vi.spyOn(response.body!, 'getReader');
      fetchMock.mockResolvedValueOnce(response);
      await expect(search()).rejects.toMatchObject({ reason });
      expect(read).not.toHaveBeenCalled(); expect(cancel).toHaveBeenCalledOnce();
      expect(captured.isCurrent()).toBe(true); // Only the currently mounted owner may handle local expiry.
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('accepts exact2MiB but cancels a streamed one-byte-over body despite a falsely small encoded length', async () => {
    const raw = searchPage();
    const maximum = bytes(raw + ' '.repeat(2_097_152 - bytes(raw).length));
    fetchMock.mockResolvedValueOnce(searchResponse(maximum));
    expect((await search()).items[0].version).toBe(searchVersion);
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(searchResponse(new ReadableStream({ start(output) {
      output.enqueue(maximum); output.enqueue(bytes(' '));
    }, cancel }), 200, { 'Content-Length': '1' }));
    await expect(search()).rejects.toMatchObject({ reason: 'INVALID_RESPONSE' });
    expect(cancel).toHaveBeenCalledOnce();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('owns the full fetch/body deadline and caller cancellation without leaking response text', async () => {
    for (const cause of ['caller', 'deadline']) {
      const caller = new AbortController(), cancel = vi.fn();
      let started!: () => void;
      const reading = new Promise<void>((resolve) => { started = resolve; });
      fetchMock.mockResolvedValueOnce(searchResponse(new ReadableStream({
        start(output) { output.enqueue(bytes('{')); }, pull() { started(); return new Promise<void>(() => {}); }, cancel,
      })));
      const result = search(caller.signal).then(() => new Error('Unexpected success'), (error: unknown) => error);
      await reading;
      if (cause === 'caller') caller.abort('private caller reason');
      else await vi.advanceTimersByTimeAsync(70_000);
      expect(await result).toMatchObject(cause === 'caller' ? { name: 'AbortError' } : { reason: 'NETWORK' });
      expect(String(await result)).not.toContain('private');
      expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
  });
});
