import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureCsrf, fixtureGeneration, seedClientSession } from '@/test/auth-fixture';
import { complaintScope } from '@/test/complaint-mutation-fixture';
import { statsDocument, statsFixture, statsResponse, statsTotal } from '@/test/complaint-stats-fixture';
import { captureAdminSession } from './client-api';
import { fetchComplaintAdminStats } from './complaint-read-client';

const fetchMock = vi.fn<typeof fetch>();
const bytes = (value: string) => new TextEncoder().encode(value);
const load = (signal = new AbortController().signal) => fetchComplaintAdminStats({ dataScopeId: complaintScope, signal });

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  vi.stubGlobal('fetch', fetchMock);
  await seedClientSession(); fetchMock.mockReset();
});
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('fixed same-origin scope statistics client', () => {
  it('sends only the scoped GET with selected G and contract1, preserving Long counts without browser proof or JSON number decoding', async () => {
    const response = statsResponse();
    const json = vi.spyOn(response, 'json'), buffer = vi.spyOn(response, 'arrayBuffer');
    fetchMock.mockResolvedValue(response);
    expect((await load()).total).toBe(statsTotal);
    expect(json).not.toHaveBeenCalled(); expect(buffer).not.toHaveBeenCalled();
    const [path, init] = fetchMock.mock.calls[0];
    expect(path).toBe(`/api/backend/complaints/stats?dataScopeId=${complaintScope}`);
    expect(init).toMatchObject({ method: 'GET', credentials: 'same-origin', redirect: 'error', cache: 'no-store' });
    expect(init?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({ accept: 'application/json, application/problem+json',
      'x-kira-complaint-contract': '1', 'x-kira-csrf': fixtureCsrf, 'x-kira-session-generation': fixtureGeneration });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects invalid scope or scope echo and distinguishes local expiry from backend denial without consuming error bytes or session ownership', async () => {
    for (const dataScopeId of ['', '00000000-0000-0000-0000-000000000000', `${complaintScope}&limit=50`, 'ABCDEFAB-1234-4234-8234-123456789ABC']) {
      await expect(fetchComplaintAdminStats({ dataScopeId, signal: new AbortController().signal })).rejects.toMatchObject({ reason: 'INVALID_RESPONSE' });
    }
    expect(fetchMock).not.toHaveBeenCalled();
    const foreign = statsFixture(); foreign.dataScopeId = '33333333-3333-4333-8333-333333333333';
    fetchMock.mockResolvedValueOnce(statsResponse(statsDocument(foreign)));
    await expect(load()).rejects.toMatchObject({ reason: 'INVALID_RESPONSE' });
    const captured = captureAdminSession();
    for (const [status, challenge, reason] of [[401, null, 'UNAUTHORIZED'], [401, 'Bearer realm="kira-complaints"', 'UNAUTHORIZED'],
      [401, 'KiraSession realm="kira-admin-bff"', 'SESSION_EXPIRED'], [403, null, 'FORBIDDEN'], [404, null, 'UNAVAILABLE'],
      [429, null, 'UNAVAILABLE'], [503, null, 'UNAVAILABLE'], [400, null, 'INVALID_RESPONSE']] as const) {
      const cancel = vi.fn();
      const response = statsResponse(new ReadableStream({ start(output) { output.enqueue(bytes('private failure, never a zero total')); }, cancel }), status,
        challenge ? { 'WWW-Authenticate': challenge } : {});
      const read = vi.spyOn(response.body!, 'getReader');
      fetchMock.mockResolvedValueOnce(response);
      await expect(load()).rejects.toMatchObject({ reason });
      expect(read).not.toHaveBeenCalled(); expect(cancel).toHaveBeenCalledOnce();
      expect(captured.isCurrent()).toBe(true); // Only the current mounted ticket handles local expiry.
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('accepts the actual2MiB limit and cancels a late extra byte without accepting partial statistics', async () => {
    const raw = statsDocument(), maximum = bytes(raw + ' '.repeat(2_097_152 - bytes(raw).byteLength));
    fetchMock.mockResolvedValueOnce(statsResponse(maximum));
    expect((await load()).total).toBe(statsTotal);
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(statsResponse(new ReadableStream({ start(output) { output.enqueue(maximum); output.enqueue(bytes(' ')); }, cancel }), 200, { 'Content-Length': '1' }));
    await expect(load()).rejects.toMatchObject({ reason: 'INVALID_RESPONSE' });
    expect(cancel).toHaveBeenCalledOnce(); expect(vi.getTimerCount()).toBe(0);
  });

  it('keeps the existing full-body deadline and caller cancellation with sanitized failure and released reader', async () => {
    for (const cause of ['caller', 'deadline']) {
      const caller = new AbortController(), cancel = vi.fn();
      let start!: () => void;
      const started = new Promise<void>((resolve) => { start = resolve; });
      fetchMock.mockResolvedValueOnce(statsResponse(new ReadableStream({ start(output) { output.enqueue(bytes('{')); },
        pull() { start(); return new Promise<void>(() => {}); }, cancel })));
      const pending = load(caller.signal).then(() => new Error('Unexpected success'), (error: unknown) => error);
      await started;
      if (cause === 'caller') caller.abort('private caller reason');
      else await vi.advanceTimersByTimeAsync(70_000);
      const error = await pending;
      expect(error).toMatchObject(cause === 'caller' ? { name: 'AbortError' } : { reason: 'NETWORK' });
      expect(String(error)).not.toContain('private'); expect(cancel).toHaveBeenCalledOnce(); expect(vi.getTimerCount()).toBe(0);
    }
  });
});
