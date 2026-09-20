import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { issueAdminProof, type AdminProofCookie, type AdminSessionCookie } from '@/lib/server-session';
import { sessionGenerationHeader, stepUpProofIdHeader } from '@/lib/session-contract';
import { appliedResponse, complaintId, complaintScope, grantA, grantB, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';

const origin = 'https://admin.example.test';
const consumedId = 'X-Kira-Admin-Step-Up-Consumed-Grant-Id';
const fetchMock = vi.fn<typeof fetch>();
let session: AdminSessionCookie;
let proofA: AdminProofCookie;
let proofB: AdminProofCookie;

function proof(grant: string, owner = session) {
  const token = grant === grantB ? 'B'.repeat(42) + 'A' : 'A'.repeat(43);
  return issueAdminProof(owner, token, 'complaint-moderation-mutation', new Date(Date.now() + 300_000).toISOString(), grant);
}

async function invoke(options: { operation?: 'content' | 'status' | 'closure'; body?: BodyInit; proofs?: AdminProofCookie[];
  headers?: HeadersInit; remove?: string[]; path?: string; query?: string; signal?: AbortSignal } = {}) {
  const operation = options.operation ?? 'status';
  const description = mutationRequest(operation);
  const headers = signedRequestHeaders(session, options.proofs ?? [proofB, proofA], { ...description.headers,
    Authorization: 'Bearer browser-override', 'X-Kira-Admin-Step-Up': 'browser-proof-override',
  });
  for (const [name, value] of new Headers(options.headers)) headers.set(name, value);
  options.remove?.forEach((name) => headers.delete(name));
  const { PATCH } = await import('./route');
  const path = ['complaints', complaintId, operation];
  const request = new Request(`${origin}${options.path ?? '/api/backend/' + path.join('/')}${options.query ?? `?dataScopeId=${complaintScope}`}`, {
    method: 'PATCH', headers, body: options.body ?? description.body, signal: options.signal, duplex: 'half',
  } as RequestInit);
  return PATCH(request, { params: Promise.resolve({ path }) });
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_ORIGIN', origin);
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  session = createSessionFixture();
  proofA = proof(grantA);
  proofB = proof(grantB);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('actual bounded ordinary complaint PATCH connection', () => {
  it.each([
    ['status', '{"status":"RESOLVED"}'], ['closure', '{"reason":"  original\\r\\nreason  "}'],
    ['content', '{"type":"CUSTOM","subject":"Original","body":"raw 😀"}'], ['content', '{"body":"notice reply"}'],
  ] as const)('forwards only the captured request/session and selected complaint proof for %s', async (operation, body) => {
    fetchMock.mockResolvedValue(appliedResponse(mutationRequest(operation, body), { [consumedId]: grantB,
      'Set-Cookie': 'upstream-secret=never', Authorization: 'never', Location: 'https://outside.example.test/secret',
    }));
    const response = await invoke({ operation, body });
    expect(response.status).toBe(200);
    expect(await response.text()).toBe(`{"id":"${complaintId}","version":9007199254740993}`);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/${complaintId}/${operation}?dataScopeId=${complaintScope}`);
    expect(init).toMatchObject({ method: 'PATCH', body, redirect: 'manual', cache: 'no-store', signal: expect.any(AbortSignal) });
    const headers = new Headers(init?.headers);
    expect(headers.get('authorization')).toBe(`Bearer ${session.token}`);
    expect(headers.get('X-Kira-Admin-Step-Up')).toBe(proofB.token);
    expect(headers.get('accept-encoding')).toBe('identity');
    for (const name of ['Cookie', sessionGenerationHeader, stepUpProofIdHeader, consumedId]) expect(headers.has(name)).toBe(false);
    expect(response.headers.getSetCookie()).toHaveLength(1);
    expect(response.headers.getSetCookie()[0]).toContain(`${proofB.name}=; Path=/api;`);
    for (const name of ['authorization', 'location', consumedId, 'X-Kira-Admin-Step-Up-Grant-Id']) expect(response.headers.has(name)).toBe(false);
    expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
  });

  it('replay A with selected fresh B retires A only; proofless replay can retire captured A too', async () => {
    for (const remove of [[], [stepUpProofIdHeader]]) {
      fetchMock.mockResolvedValueOnce(appliedResponse(undefined, { [consumedId]: grantA }));
      const response = await invoke({ remove });
      expect(response.status).toBe(200);
      expect(response.headers.getSetCookie()).toHaveLength(1);
      expect(response.headers.get('set-cookie')).toContain(proofA.name);
      expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
      expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).get('X-Kira-Admin-Step-Up')).toBe(remove.length ? null : proofB.token);
    }
  });

  it('does not infer a current proof from NULL, unknown, ambiguous or cross-session association', async () => {
    const other = createSessionFixture(session.token);
    const otherProof = proof(grantA, other);
    const duplicate = proof(grantA);
    for (const [proofs, association] of [[[proofB, proofA], null], [[proofB], grantA], [[proofB, otherProof], grantA], [[proofA, duplicate], grantA]] as const) {
      fetchMock.mockResolvedValueOnce(appliedResponse(undefined, association ? { [consumedId]: association } : {}));
      const response = await invoke({ proofs: [...proofs] });
      expect(response.status).toBe(200);
      expect(response.headers.getSetCookie()).toHaveLength(0);
    }
    const withoutMarker = appliedResponse();
    withoutMarker.headers.delete('X-Kira-Admin-Step-Up-Consumed');
    fetchMock.mockResolvedValueOnce(withoutMarker);
    const confirmed = await invoke();
    expect(confirmed.status).toBe(200); // A valid ACK and proof retirement are separate facts.
    expect(confirmed.headers.getSetCookie()).toHaveLength(0);
  });

  it('has no fresh-proof replay gate and never forwards a missing, expired, wrong-scope or forged proof', async () => {
    const source = issueAdminProof(session, 'A'.repeat(43), 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    const forged = { ...proofA, value: proofA.value.slice(0, -1) + (proofA.value.endsWith('A') ? 'E' : 'A') };
    for (const proofs of [[], [source], [forged]]) {
      fetchMock.mockResolvedValueOnce(appliedResponse());
      expect((await invoke({ proofs })).status).toBe(200);
      expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).has('X-Kira-Admin-Step-Up')).toBe(false);
    }
    vi.useFakeTimers();
    vi.setSystemTime(Date.now() + 301_000);
    fetchMock.mockResolvedValueOnce(problemResponse('ADMIN_STEP_UP_REQUIRED', 401));
    const expired = await invoke();
    expect(expired.status).toBe(401);
    expect(expired.headers.get('www-authenticate')).toBe('Bearer realm="kira-complaints"');
    expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).has('X-Kira-Admin-Step-Up')).toBe(false);
    expect(expired.headers.getSetCookie()).toHaveLength(0);
  });

  it.each(['', grantA.toUpperCase(), `${grantA}, ${grantA}`, 'not-a-uuid'])('rejects unusable consumed identity %j without retirement', async (id) => {
    fetchMock.mockResolvedValue(appliedResponse(undefined, { [consumedId]: id }));
    const response = await invoke();
    expect(response.status).toBe(502);
    expect(response.headers.getSetCookie()).toHaveLength(0);
  });

  it('keeps proof retirement separate from a complete bounded post-receipt503 and a rejected412', async () => {
    for (const [code, status] of [['SERVICE_UNAVAILABLE', 503], ['PRECONDITION_FAILED', 412]] as const) {
      fetchMock.mockResolvedValueOnce(problemResponse(code, status, { [consumedId]: grantA, 'X-Kira-Admin-Step-Up-Consumed': 'true' }));
      const response = await invoke();
      expect(response.status).toBe(status);
      expect(response.headers.get('set-cookie')).toContain(proofA.name);
      expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
      expect(await response.text()).toContain(code);
    }
  });

  it('checks exact route/scope, origin, session/CSRF and canonical private headers before upstream work', async () => {
    const cases: Array<[Parameters<typeof invoke>[0], number]> = [
      [{ path: `/api/backend/complaints/%31${complaintId.slice(1)}/status` }, 404], [{ query: `?dataScopeId=${complaintScope}&extra=1` }, 400],
      [{ headers: { Origin: 'https://outside.example.test' } }, 403], [{ remove: ['X-Kira-CSRF'] }, 403], [{ remove: [sessionGenerationHeader] }, 401],
      [{ headers: { 'X-Kira-Idempotency-Key': `${grantA}, ${grantB}` } }, 400], [{ headers: { [stepUpProofIdHeader]: `${proofA.proofId}, ${proofB.proofId}` } }, 400],
      [{ headers: { 'If-Match': 'W/"bad"' } }, 412], [{ remove: ['If-Match'] }, 428], [{ headers: { 'X-Kira-Complaint-Contract': '1, 1' } }, 400],
      [{ headers: { 'Content-Encoding': 'gzip' } }, 415], [{ headers: { 'Content-Type': 'application/json, application/json' } }, 415],
      [{ headers: { 'Content-Length': '1', 'Transfer-Encoding': 'chunked' } }, 400], [{ headers: { 'Content-Length': '1' } }, 400],
      [{ headers: new Headers(Array.from({ length: 129 }, (_, index) => [`X-Fixture-${index}`, 'bounded'] as [string, string])) }, 431],
      [{ headers: { Cookie: `${session.name}=${session.value}; ${proofA.name}=${proofA.value}; ${proofA.name}=${proofA.value}` } }, 400],
    ];
    for (const [options, expected] of cases) expect((await invoke(options)).status).toBe(expected);
    const missing = await invoke({ remove: [sessionGenerationHeader] });
    expect(missing.headers.get('www-authenticate')).toBe('KiraSession realm="kira-admin-bff"');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('collects all inbound bytes before fetch; exact ceiling works and a late extra byte cannot mutate', async () => {
    const original = mutationRequest().body;
    const exact = original + ' '.repeat(16_384 - original.length);
    fetchMock.mockResolvedValueOnce(appliedResponse());
    expect((await invoke({ body: exact })).status).toBe(200);
    fetchMock.mockClear();
    const cancel = vi.fn();
    const stream = new ReadableStream({ start(controller) {
      controller.enqueue(new TextEncoder().encode(exact));
      controller.enqueue(new Uint8Array([32]));
    }, cancel });
    expect((await invoke({ body: stream })).status).toBe(413);
    expect(cancel).toHaveBeenCalled();
    for (const body of ['{"status":"OPEN","status":"RESOLVED"}', '{"status":"OPEN","statu\\u0073":"RESOLVED"}',
      '{"status":["OPEN"]}', '{"status":"OPEN","actor":"caller"}', '{"status":"OPEN",}', '{"status":"CLOSED"}']) {
      expect((await invoke({ body })).status).toBe(400);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('withholds malformed/encoded/oversized/partial/redirected replies and never retires from their headers', async () => {
    for (const mode of ['oversize', 'partial', 'redirect', 'encoded', 'wrong-etag', 'duplicate-marker', 'wrong-body']) {
      let response = appliedResponse(undefined, { [consumedId]: grantA });
      if (mode === 'oversize') response = new Response(' '.repeat(32_769), { headers: response.headers });
      if (mode === 'partial') response = new Response(new ReadableStream({ start(controller) { controller.enqueue(new TextEncoder().encode('{')); controller.error(new Error('private transport text')); } }), { headers: response.headers });
      if (mode === 'redirect') response = new Response(null, { status: 302, headers: response.headers });
      if (mode === 'encoded') response.headers.set('Content-Encoding', 'gzip');
      if (mode === 'wrong-etag') response.headers.set('ETag', 'wrong');
      if (mode === 'duplicate-marker') response.headers.set('X-Kira-Admin-Step-Up-Consumed', 'true, true');
      if (mode === 'wrong-body') response = new Response('{"token":"private"}', { headers: response.headers });
      fetchMock.mockResolvedValueOnce(response);
      const result = await invoke();
      expect(result.status).toBe(502);
      expect(result.headers.getSetCookie()).toHaveLength(0);
      expect(await result.text()).not.toMatch(/private|9007199254740993/);
    }
  });

  it('retains proofs on finite stalled-body deadline and on transport failure without retries', async () => {
    vi.useFakeTimers();
    const cancel = vi.fn();
    let started!: () => void;
    const reading = new Promise<void>((resolve) => { started = resolve; });
    fetchMock.mockResolvedValue(new Response(new ReadableStream({
      start(controller) { controller.enqueue(new TextEncoder().encode('{')); },
      pull() { started(); return new Promise<void>(() => {}); }, cancel,
    }), {
      headers: appliedResponse(undefined, { [consumedId]: grantA }).headers,
    }));
    const pending = invoke();
    await reading;
    await vi.advanceTimersByTimeAsync(65_001);
    const response = await pending;
    expect(response.status).toBe(504);
    expect(response.headers.getSetCookie()).toHaveLength(0);
    expect(cancel).toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
    fetchMock.mockRejectedValueOnce(new TypeError('private URL/token'));
    const failure = await invoke();
    expect(failure.status).toBe(502);
    expect(failure.headers.getSetCookie()).toHaveLength(0);
  });

  it('bounds stalled inbound acquisition before dispatch and cancels an upstream body when the caller leaves', async () => {
    vi.useFakeTimers();
    const inboundCancel = vi.fn();
    let inboundStarted!: () => void;
    const inboundReading = new Promise<void>((resolve) => { inboundStarted = resolve; });
    const body = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode('{')); },
      pull() { inboundStarted(); return new Promise<void>(() => {}); }, cancel: inboundCancel,
    });
    const collecting = invoke({ body });
    await inboundReading;
    await vi.advanceTimersByTimeAsync(65_000);
    expect((await collecting).status).toBe(504);
    expect(inboundCancel).toHaveBeenCalledOnce();
    expect(fetchMock).not.toHaveBeenCalled();

    const caller = new AbortController();
    const outboundCancel = vi.fn();
    let outboundStarted!: () => void;
    const outboundReading = new Promise<void>((resolve) => { outboundStarted = resolve; });
    fetchMock.mockResolvedValueOnce(new Response(new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode('{')); },
      pull() { outboundStarted(); return new Promise<void>(() => {}); }, cancel: outboundCancel,
    }), { headers: appliedResponse(undefined, { [consumedId]: grantA }).headers }));
    const dispatched = invoke({ signal: caller.signal });
    await outboundReading;
    caller.abort('private caller reason');
    const result = await dispatched;
    expect(result.status).toBe(502);
    expect(result.headers.getSetCookie()).toHaveLength(0);
    expect(outboundCancel).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
