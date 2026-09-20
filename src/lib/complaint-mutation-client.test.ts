import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureCsrf, fixtureGeneration, fixtureProofId, otherGeneration, seedClientSession, stepUpAcknowledgement } from '@/test/auth-fixture';
import { appliedResponse, complaintId, complaintScope, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { sendComplaintMutation, type ComplaintOperation } from './complaint-mutation-client';
import { sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';

const fetchMock = vi.fn<typeof fetch>();
const operation = (): ComplaintOperation => Object.freeze({ generation: fixtureGeneration, request: mutationRequest(), phase: 'prepared' });
const signal = () => new AbortController().signal;
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  await seedClientSession();
});
afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('one-attempt complaint client transport with real session ownership', () => {
  it('sends the fixed BFF path with G/CSRF/optional P, and retries only explicitly with identical original bytes', async () => {
    const original = operation();
    const approval = stepUpAcknowledgement('complaint-moderation-mutation');
    fetchMock.mockRejectedValueOnce(new Error('private URL/token')).mockResolvedValueOnce(appliedResponse());
    expect(await sendComplaintMutation(original, signal(), approval)).toEqual({ kind: 'unknown' });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(await sendComplaintMutation(original, signal())).toMatchObject({ kind: 'applied', version: '9007199254740993' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const [index, [url, init]] of fetchMock.mock.calls.entries()) {
      expect(url).toBe(`/api/backend/complaints/${complaintId}/status?dataScopeId=${complaintScope}`);
      expect(init).toMatchObject({ method: 'PATCH', body: original.request.body, credentials: 'same-origin', redirect: 'error', cache: 'no-store' });
      const headers = new Headers(init?.headers);
      expect(headers.get(sessionGenerationHeader)).toBe(fixtureGeneration);
      expect(headers.get('X-Kira-CSRF')).toBe(fixtureCsrf);
      expect(headers.get(stepUpProofIdHeader)).toBe(index === 0 ? fixtureProofId : null);
      expect(headers.get('If-Match')).toBe(original.request.headers['If-Match']);
      expect(headers.get('X-Kira-Idempotency-Key')).toBe(original.request.headers['X-Kira-Idempotency-Key']);
      for (const name of ['Authorization', 'Cookie', 'X-Kira-Admin-Step-Up', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id']) expect(headers.has(name)).toBe(false);
    }
    expect(original.phase).toBe('prepared');
    expect(original.outcome).toBeUndefined();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('refuses stale G, malformed destinations and mismatched/expired approvals without fetching or selecting another proof', async () => {
    const original = operation();
    for (const approval of [stepUpAcknowledgement(), stepUpAcknowledgement('complaint-moderation-mutation', fixtureProofId, otherGeneration),
      { ...stepUpAcknowledgement('complaint-moderation-mutation'), expiresAt: new Date(Date.now() - 1).toISOString() }]) {
      expect(await sendComplaintMutation(original, signal(), approval)).toEqual({ kind: 'unknown' });
    }
    expect(await sendComplaintMutation({ ...original, request: { ...original.request, path: 'https://outside.example.test' } }, signal())).toEqual({ kind: 'unknown' });
    await seedClientSession(otherGeneration);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'stale-session' });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('distinguishes local expiry, backend Bearer unauthorized, and explicit step-up-required', async () => {
    fetchMock.mockResolvedValueOnce(Response.json({ detail: 'Not signed in.' }, { status: 401, headers: { 'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"' } }))
      .mockResolvedValueOnce(problemResponse('UNAUTHORIZED', 401)).mockResolvedValueOnce(problemResponse('ADMIN_STEP_UP_REQUIRED', 401));
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'session-expired' });
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'unauthorized' });
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'step-up-required' });
    expect(fetchMock).toHaveBeenCalledTimes(3); // No implicit verification or retry.
  });

  it('reads complete bounded bytes rather than response.json(), rejecting framing/leaks/partial data', async () => {
    const valid = appliedResponse();
    const json = vi.spyOn(valid, 'json');
    const arrayBuffer = vi.spyOn(valid, 'arrayBuffer');
    fetchMock.mockResolvedValueOnce(valid);
    expect((await sendComplaintMutation(operation(), signal())).kind).toBe('applied');
    expect(json).not.toHaveBeenCalled();
    expect(arrayBuffer).not.toHaveBeenCalled();
    for (const name of ['Content-Encoding', 'Content-Length', 'X-Kira-Admin-Step-Up-Grant-Id', 'X-Kira-Admin-Step-Up-Consumed-Grant-Id']) {
      const invalid = appliedResponse();
      invalid.headers.set(name, name === 'Content-Encoding' ? 'gzip' : '1');
      fetchMock.mockResolvedValueOnce(invalid);
      expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'unknown' });
    }
    const cancel = vi.fn();
    const overflow = new Response(new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new Uint8Array(32_769)); }, cancel }), { headers: appliedResponse().headers });
    fetchMock.mockResolvedValueOnce(overflow);
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'unknown' });
    expect(cancel).toHaveBeenCalledOnce();
    fetchMock.mockResolvedValueOnce(new Response(new ReadableStream<Uint8Array>({ start(controller) { controller.error(new Error('private truncated body')); } }), { headers: appliedResponse().headers }));
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'unknown' });
  });

  it('cancels stalled response acquisition on caller abort or the finite deadline without retrying', async () => {
    const already = new AbortController(); already.abort();
    expect(await sendComplaintMutation(operation(), already.signal)).toEqual({ kind: 'unknown' });
    expect(fetchMock).not.toHaveBeenCalled();
    for (const source of ['caller', 'deadline']) {
      const caller = new AbortController();
      const reading = deferred<void>();
      const cancel = vi.fn();
      fetchMock.mockResolvedValueOnce(new Response(new ReadableStream<Uint8Array>({
        start(controller) { controller.enqueue(new TextEncoder().encode('{')); },
        pull() { reading.resolve(); return new Promise<void>(() => {}); }, cancel,
      }), { headers: appliedResponse().headers }));
      const pending = sendComplaintMutation(operation(), caller.signal);
      await reading.promise;
      if (source === 'caller') caller.abort('private reason');
      else await vi.advanceTimersByTimeAsync(70_000);
      expect(await pending).toEqual({ kind: 'unknown' });
      expect(cancel).toHaveBeenCalledOnce();
      expect(vi.getTimerCount()).toBe(0);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('cannot adopt a late result after session change, including an equal-G login lifetime replacement', async () => {
    for (const replacement of [otherGeneration, fixtureGeneration]) {
      await seedClientSession();
      const entered = deferred<void>();
      const reply = deferred<Response>();
      fetchMock.mockImplementationOnce(() => { entered.resolve(); return reply.promise; });
      const pending = sendComplaintMutation(operation(), signal());
      await entered.promise;
      await seedClientSession(replacement);
      reply.resolve(appliedResponse());
      expect(await pending).toEqual({ kind: 'stale-session' });
    }
  });

  it('reports session expiry when the same G expires during an attempt, not a silently retryable stale action', async () => {
    vi.useFakeTimers();
    await seedClientSession();
    const entered = deferred<void>();
    const reply = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return reply.promise; });
    const pending = sendComplaintMutation(operation(), signal());
    await entered.promise;
    vi.setSystemTime(Date.now() + 3_600_001);
    reply.resolve(appliedResponse());
    expect(await pending).toEqual({ kind: 'session-expired' });
    expect(await sendComplaintMutation(operation(), signal())).toEqual({ kind: 'session-expired' });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
