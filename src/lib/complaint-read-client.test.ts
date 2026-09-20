import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { sessionFetch } from './client-api';
import { ComplaintReadClientError, fetchComplaintAdminDetail, type ComplaintAdminDetailRequest, type ComplaintReadClientReason } from './complaint-read-client';

const id = '12345678-1234-4234-8234-123456789abc';
const scope = '87654321-1234-4234-8234-123456789abc';
const version = '9007199254740993';
const tag = `"complaint-${id}-v${version}"`;
const raw = `{"id":"${id}","kind":"REPORT","status":"OPEN","createdAt":"2026-09-20T00:00:00Z","updatedAt":"2026-09-20T00:00:00Z","version":${version},"ownership":"INSTALLATION","ownerReference":"${scope}","type":"TECHNICAL","subject":"Synthetic","body":"Raw 😀","actionTag":${JSON.stringify(tag)},"appVersion":null,"platform":"ANDROID","osVersion":"","manufacturer":"","deviceModel":"","closureReason":null,"replyToId":null,"closedAt":null,"closureProvenance":null,"closureActorId":null}`;
const bytes = (value: string) => new TextEncoder().encode(value);
const fetchMock = vi.fn<typeof fetch>();

function request(overrides: Partial<ComplaintAdminDetailRequest> = {}): ComplaintAdminDetailRequest {
  return { id, dataScopeId: scope, signal: new AbortController().signal, ...overrides };
}

function response(body: BodyInit | null = raw, status = 200) {
  return new Response(body, { status, headers: { 'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1', ETag: tag } });
}

async function refusal(reason: ComplaintReadClientReason, pending: Promise<unknown>) {
  const error: unknown = await pending.then(() => 'Unexpected success', (caught: unknown) => caught);
  expect(error).toBeInstanceOf(ComplaintReadClientError);
  expect(error).toMatchObject({ reason, message: new ComplaintReadClientError(reason).message });
  expect(error).not.toHaveProperty('cause');
}

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockResolvedValueOnce(Response.json({ csrfToken: 'fixture-only-csrf' }));
  await sessionFetch();
  fetchMock.mockReset();
});

afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('same-origin complaint detail client', () => {
  it('uses the existing session/CSRF fetch and decodes bounded raw bytes without JSON-number conversion', async () => {
    const input = bytes(raw);
    const upstream = response(new ReadableStream({ start(controller) {
      controller.enqueue(input.slice(0, 331));
      controller.enqueue(input.slice(331));
      controller.close();
    } }));
    const json = vi.spyOn(upstream, 'json');
    const arrayBuffer = vi.spyOn(upstream, 'arrayBuffer');
    fetchMock.mockResolvedValue(upstream);
    const caller = new AbortController();
    const loaded = await fetchComplaintAdminDetail(request({ signal: caller.signal }));
    expect(loaded.item.version).toBe(version);
    expect(loaded.contentSnapshot.id).toBe(id);
    expect(loaded.moderationTarget?.actionTag).toBe(tag);
    expect(Object.isFrozen(loaded)).toBe(true);
    expect(json).not.toHaveBeenCalled();
    expect(arrayBuffer).not.toHaveBeenCalled();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`/api/backend/complaints/${id}?dataScopeId=${scope}`);
    expect(init).toMatchObject({ method: 'GET', credentials: 'same-origin', redirect: 'error', cache: 'no-store', signal: expect.any(AbortSignal) });
    expect(init?.body).toBeUndefined();
    expect(Object.fromEntries(new Headers(init?.headers))).toEqual({
      accept: 'application/json, application/problem+json', 'x-kira-complaint-contract': '1', 'x-kira-csrf': 'fixture-only-csrf',
    });
    caller.abort();
    expect(init?.signal?.aborted).toBe(false); // The completed read removed its caller listener.
    expect(vi.getTimerCount()).toBe(0);
  });

  it('maps unavailable/session/forbidden/gateway statuses statically and never reads private problem bodies', async () => {
    const cases: Array<[number, ComplaintReadClientReason]> = [
      [404, 'UNAVAILABLE'], [503, 'UNAVAILABLE'], [401, 'SESSION_EXPIRED'], [403, 'FORBIDDEN'],
      [502, 'NETWORK'], [204, 'INVALID_RESPONSE'], [302, 'INVALID_RESPONSE'],
    ];
    for (const [status, reason] of cases) {
      const cancel = vi.fn();
      const upstream = response(status === 204 ? null : new ReadableStream({ start(controller) { controller.enqueue(bytes('private problem')); }, cancel }), status);
      const json = vi.spyOn(upstream, 'json');
      fetchMock.mockResolvedValueOnce(upstream);
      await refusal(reason, fetchComplaintAdminDetail(request()));
      expect(json).not.toHaveBeenCalled();
      if (status !== 204) expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('refuses bad local scope/ID before fetch and delegates success integrity to the existing decoder', async () => {
    for (const input of [request({ id: id.toUpperCase() }), request({ dataScopeId: '00000000-0000-0000-0000-000000000000' }), request({ dataScopeId: `${scope}&extra=1` })]) {
      await refusal('INVALID_RESPONSE', fetchComplaintAdminDetail(input));
    }
    expect(fetchMock).not.toHaveBeenCalled();
    const wrongTag = response(); wrongTag.headers.set('ETag', `"complaint-${id}-v9007199254740992"`);
    const missingContract = response(); missingContract.headers.delete('X-Kira-Complaint-Contract');
    for (const input of [wrongTag, missingContract, response(raw.slice(0, -1))]) {
      fetchMock.mockResolvedValueOnce(input);
      await refusal('INVALID_RESPONSE', fetchComplaintAdminDetail(request()));
    }
  });

  it('accepts the exact body ceiling but cancels overflow instead of buffering an arbitrary response', async () => {
    fetchMock.mockResolvedValueOnce(response(bytes(raw + ' '.repeat(32_768 - bytes(raw).length))));
    expect((await fetchComplaintAdminDetail(request())).item.version).toBe(version);
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(response(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(32_769)); }, cancel })));
    await refusal('INVALID_RESPONSE', fetchComplaintAdminDetail(request()));
    expect(cancel).toHaveBeenCalledOnce();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('keeps caller cancellation recognizable and enforces a finite deadline even on a stalled response body', async () => {
    const already = new AbortController();
    already.abort('private cancellation reason');
    await expect(fetchComplaintAdminDetail(request({ signal: already.signal }))).rejects.toMatchObject({ name: 'AbortError', message: 'Complaint detail request cancelled.' });
    expect(fetchMock).not.toHaveBeenCalled();
    for (const source of ['caller', 'deadline']) {
      const caller = new AbortController();
      let started = () => {};
      const reading = new Promise<void>((resolve) => { started = resolve; });
      const cancel = vi.fn();
      fetchMock.mockResolvedValueOnce(response(new ReadableStream({
        start(controller) { controller.enqueue(bytes('{')); },
        pull() { started(); return new Promise<void>(() => {}); }, cancel,
      })));
      const pending = fetchComplaintAdminDetail(request({ signal: caller.signal }));
      const error = pending.catch((caught: unknown) => caught);
      await reading;
      if (source === 'caller') caller.abort('private cancellation reason');
      else await vi.advanceTimersByTimeAsync(70_000);
      const caught = await error;
      if (source === 'caller') expect(caught).toMatchObject({ name: 'AbortError', message: 'Complaint detail request cancelled.' });
      else expect(caught).toMatchObject({ reason: 'NETWORK', message: new ComplaintReadClientError('NETWORK').message });
      expect(caller.signal.aborted).toBe(source === 'caller');
      expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
  });

  it('turns fetch and midstream failures into a static NETWORK error without retrying', async () => {
    fetchMock.mockRejectedValueOnce(new Error('private network failure'));
    await refusal('NETWORK', fetchComplaintAdminDetail(request()));
    const failed = new ReadableStream<Uint8Array>({ start(controller) { controller.error(new Error('private stream failure')); } });
    fetchMock.mockResolvedValueOnce(response(failed));
    await refusal('NETWORK', fetchComplaintAdminDetail(request()));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(vi.getTimerCount()).toBe(0);
  });
});
