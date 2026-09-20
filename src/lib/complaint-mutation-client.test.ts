import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureCsrf, fixtureGeneration, fixtureProofId, otherGeneration, seedClientSession, stepUpAcknowledgement } from '@/test/auth-fixture';
import { appliedResponse, complaintId, complaintScope, deletedResponse, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { batchRequest, batchResponse, deleteBatchRequest, deleteBatchResponse } from '@/test/complaint-batch-status-fixture';
import { isTerminalComplaintOperation, sendComplaintMutation, type ComplaintOperation } from './complaint-mutation-client';
import { sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';

const fetchMock = vi.fn<typeof fetch>();
const operation = () => Object.freeze({ generation: fixtureGeneration, request: mutationRequest(), phase: 'prepared' as const, outcome: undefined }) satisfies ComplaintOperation;
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

describe('one-attempt atomic STATUS batch client', () => {
  it('keeps a partial ACK unknown and explicitly retries one identical captured POST with G/CSRF and no repaired key or tags', async () => {
    const original = Object.freeze({ generation: fixtureGeneration, request: batchRequest(), phase: 'prepared' as const });
    const before = JSON.stringify(original);
    const partial = new Response(`{"items":[{"id":"${complaintId}","version":9007199254740993}]}`, { headers: batchResponse().headers });
    fetchMock.mockResolvedValueOnce(partial).mockResolvedValueOnce(batchResponse());
    expect(await sendComplaintMutation(original, signal(), stepUpAcknowledgement('complaint-moderation-mutation'))).toEqual({ kind: 'unknown' });
    expect(fetchMock).toHaveBeenCalledOnce();
    const outcome = await sendComplaintMutation(original, signal());
    expect(outcome.kind).toBe('batch-applied');
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome })).toBe(true);
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome: { kind: 'batch-applied', items: [] } })).toBe(false);
    for (const [index, [url, init]] of fetchMock.mock.calls.entries()) {
      expect(url).toBe(`/api/backend/complaints/batch?dataScopeId=${complaintScope}`);
      expect(init).toMatchObject({ method: 'POST', body: original.request.body, credentials: 'same-origin', redirect: 'error', cache: 'no-store' });
      const headers = new Headers(init?.headers);
      expect(headers.get(sessionGenerationHeader)).toBe(fixtureGeneration); expect(headers.get('X-Kira-CSRF')).toBe(fixtureCsrf);
      expect(headers.get(stepUpProofIdHeader)).toBe(index === 0 ? fixtureProofId : null);
      expect(headers.get('X-Kira-Idempotency-Key')).toBe(original.request.headers['X-Kira-Idempotency-Key']);
      for (const name of ['If-Match', 'Authorization', 'Cookie', 'X-Kira-Admin-Step-Up']) expect(headers.has(name)).toBe(false);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2); expect(JSON.stringify(original)).toBe(before); expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects a forged batch destination or stale G and cannot adopt a complete late ACK after equal-G lifetime replacement', async () => {
    const original: ComplaintOperation = Object.freeze({ generation: fixtureGeneration, request: batchRequest(), phase: 'prepared' });
    expect(await sendComplaintMutation({ ...original, request: { ...batchRequest(), path: 'https://outside.example.test/' } }, signal())).toEqual({ kind: 'unknown' });
    expect(fetchMock).not.toHaveBeenCalled();
    const entered = deferred<void>(), reply = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return reply.promise; });
    const pending = sendComplaintMutation(original, signal()); await entered.promise;
    await seedClientSession(); reply.resolve(batchResponse());
    expect(await pending).toEqual({ kind: 'stale-session' });
    await seedClientSession(otherGeneration);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'stale-session' });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});

describe('one-attempt atomic DELETE batch client', () => {
  it('keeps partial, STATUS-shaped and consumed503 replies unknown until an explicit identical POST receives the full ID-only ACK', async () => {
    const original = Object.freeze({ generation: fixtureGeneration, request: deleteBatchRequest(), phase: 'prepared' as const });
    const before = JSON.stringify(original);
    fetchMock.mockResolvedValueOnce(new Response(`{"items":[{"id":"${complaintId}"}]}`, { headers: deleteBatchResponse().headers }))
      .mockResolvedValueOnce(batchResponse())
      .mockResolvedValueOnce(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true' }))
      .mockResolvedValueOnce(deleteBatchResponse());
    for (let attempt = 0; attempt < 3; attempt++) {
      expect(await sendComplaintMutation(original, signal(), attempt === 0 ? stepUpAcknowledgement('complaint-moderation-mutation') : undefined)).toEqual({ kind: 'unknown' });
      expect(fetchMock).toHaveBeenCalledTimes(attempt + 1); // Each invocation is explicit; the client never retries or fans out.
    }
    const outcome = await sendComplaintMutation(original, signal());
    expect(outcome.kind).toBe('batch-deleted');
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome })).toBe(true);
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome: { kind: 'batch-deleted', items: [] } })).toBe(false);
    const statusItems = original.request.targets.map(({ id, baseVersion }) => ({ id, version: baseVersion }));
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome: { kind: 'batch-deleted', items: statusItems } })).toBe(false);
    expect(isTerminalComplaintOperation({ ...original, phase: 'settled', outcome: { kind: 'batch-applied', items: statusItems } })).toBe(false);
    expect(isTerminalComplaintOperation({ ...original, request: batchRequest(), phase: 'settled', outcome })).toBe(false);
    for (const [index, [url, init]] of fetchMock.mock.calls.entries()) {
      expect(url).toBe(`/api/backend/complaints/batch?dataScopeId=${complaintScope}`);
      expect(init).toMatchObject({ method: 'POST', body: original.request.body, credentials: 'same-origin', redirect: 'error', cache: 'no-store' });
      const headers = new Headers(init?.headers);
      expect(headers.get('X-Kira-Idempotency-Key')).toBe(original.request.headers['X-Kira-Idempotency-Key']);
      expect(headers.get(sessionGenerationHeader)).toBe(fixtureGeneration); expect(headers.get('X-Kira-CSRF')).toBe(fixtureCsrf);
      expect(headers.get(stepUpProofIdHeader)).toBe(index === 0 ? fixtureProofId : null);
      for (const name of ['If-Match', 'Authorization', 'Cookie', 'X-Kira-Admin-Step-Up']) expect(headers.has(name)).toBe(false);
    }
    expect(fetchMock).toHaveBeenCalledTimes(4); expect(JSON.stringify(original)).toBe(before); expect(vi.getTimerCount()).toBe(0);
  });

  it('refuses body/action substitution before dispatch and cannot adopt a late complete DELETE ACK after lifetime or G replacement', async () => {
    const original: ComplaintOperation = Object.freeze({ generation: fixtureGeneration, request: deleteBatchRequest(), phase: 'prepared' });
    expect(await sendComplaintMutation({ ...original, request: { ...deleteBatchRequest(), body: batchRequest().body } }, signal())).toEqual({ kind: 'unknown' });
    expect(await sendComplaintMutation({ ...original, request: { ...batchRequest(), body: deleteBatchRequest().body } }, signal())).toEqual({ kind: 'unknown' });
    expect(fetchMock).not.toHaveBeenCalled();
    const entered = deferred<void>(), reply = deferred<Response>();
    fetchMock.mockImplementationOnce(() => { entered.resolve(); return reply.promise; });
    const pending = sendComplaintMutation(original, signal()); await entered.promise;
    await seedClientSession(); reply.resolve(deleteBatchResponse());
    expect(await pending).toEqual({ kind: 'stale-session' });
    await seedClientSession(otherGeneration);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'stale-session' });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});

describe('one-attempt single DELETE client', () => {
  const deletion = () => Object.freeze({ ...operation(), request: mutationRequest('delete') }) satisfies ComplaintOperation;

  it('retains the original on transport/authorized503 ambiguity and sends only an explicit identical bodyless replay', async () => {
    const original = deletion();
    const before = JSON.stringify(original);
    fetchMock.mockRejectedValueOnce(new Error('private transport diagnostic'))
      .mockResolvedValueOnce(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true' }))
      .mockResolvedValueOnce(deletedResponse());
    expect(await sendComplaintMutation(original, signal(), stepUpAcknowledgement('complaint-moderation-mutation'))).toEqual({ kind: 'unknown' });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'unknown' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'deleted', id: complaintId });
    for (const [index, [url, init]] of fetchMock.mock.calls.entries()) {
      expect(url).toBe(`/api/backend/complaints/${complaintId}?dataScopeId=${complaintScope}`);
      expect(init?.method).toBe('DELETE');
      expect(init?.body).toBeUndefined();
      const headers = new Headers(init?.headers);
      expect(headers.get(sessionGenerationHeader)).toBe(fixtureGeneration);
      expect(headers.get('X-Kira-CSRF')).toBe(fixtureCsrf);
      expect(headers.get(stepUpProofIdHeader)).toBe(index === 0 ? fixtureProofId : null);
      for (const name of ['If-Match', 'X-Kira-Idempotency-Key'] as const) expect(headers.get(name)).toBe(original.request.headers[name]);
      for (const name of ['Authorization', 'Cookie', 'X-Kira-Admin-Step-Up']) expect(headers.has(name)).toBe(false);
    }
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(JSON.stringify(original)).toBe(before);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('does not confirm an ACK/202, or a204 with body, framing, metadata or private grant ambiguity', async () => {
    const original = deletion();
    for (const response of [appliedResponse(original.request), new Response(null, { status: 202, headers: deletedResponse().headers })]) {
      fetchMock.mockResolvedValueOnce(response);
      expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'unknown' });
    }
    for (const extra of [
      { 'Content-Type': 'application/json' }, { ETag: original.request.headers['If-Match'] }, { Location: '/not-a-deletion' },
      { 'Content-Length': '1' }, { 'Transfer-Encoding': 'chunked' }, { 'Content-Encoding': 'gzip' },
      { 'X-Kira-Complaint-Contract': '1, 1' }, { 'X-Kira-Admin-Step-Up-Consumed': 'true, true' },
      { 'X-Kira-Admin-Step-Up-Consumed-Grant-Id': fixtureProofId }, { 'X-Kira-Admin-Step-Up-Grant-Id': fixtureProofId },
    ] as HeadersInit[]) {
      fetchMock.mockResolvedValueOnce(deletedResponse(extra));
      expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'unknown' });
    }
    // Fetch normally suppresses a204 body. This synthetic response exercises the acquisition seam.
    const cancel = vi.fn();
    const illegalBody = new Response(new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new Uint8Array([32])); }, cancel }), { headers: deletedResponse().headers });
    Object.defineProperty(illegalBody, 'status', { value: 204 });
    fetchMock.mockResolvedValueOnce(illegalBody);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'unknown' });
    expect(cancel).toHaveBeenCalledOnce();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('requires EOF under the same deadline even for an apparent empty204 and retains the operation on timeout', async () => {
    const reading = deferred<void>();
    const cancel = vi.fn();
    const response = new Response(new ReadableStream<Uint8Array>({
      pull() { reading.resolve(); return new Promise<void>(() => {}); }, cancel,
    }, { highWaterMark: 0 }), { headers: deletedResponse().headers });
    Object.defineProperty(response, 'status', { value: 204 });
    fetchMock.mockResolvedValueOnce(response);
    const original = deletion();
    const pending = sendComplaintMutation(original, signal());
    await reading.promise;
    await vi.advanceTimersByTimeAsync(70_000);
    expect(await pending).toEqual({ kind: 'unknown' });
    expect(original.request.body).toBe('');
    expect(cancel).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('never dispatches with an obsolete G/P and cannot adopt a late204 after even an equal-G lifetime replacement', async () => {
    const original = deletion();
    expect(await sendComplaintMutation(original, signal(), stepUpAcknowledgement('source-admin-mutation'))).toEqual({ kind: 'unknown' });
    expect(await sendComplaintMutation(original, signal(), stepUpAcknowledgement('complaint-moderation-mutation', fixtureProofId, otherGeneration))).toEqual({ kind: 'unknown' });
    await seedClientSession(otherGeneration);
    expect(await sendComplaintMutation(original, signal())).toEqual({ kind: 'stale-session' });
    expect(fetchMock).not.toHaveBeenCalled();
    for (const replacement of [otherGeneration, fixtureGeneration]) {
      await seedClientSession();
      const entered = deferred<void>();
      const reply = deferred<Response>();
      fetchMock.mockImplementationOnce(() => { entered.resolve(); return reply.promise; });
      const pending = sendComplaintMutation(original, signal());
      await entered.promise;
      await seedClientSession(replacement);
      reply.resolve(deletedResponse());
      expect(await pending).toEqual({ kind: 'stale-session' });
    }
  });
});
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
