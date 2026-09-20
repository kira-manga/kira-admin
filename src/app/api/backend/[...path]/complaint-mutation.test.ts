import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { issueAdminProof, type AdminProofCookie, type AdminSessionCookie } from '@/lib/server-session';
import type { ComplaintMutationOperation } from '@/lib/complaint-mutation-wire';
import { prepareComplaintBatchStatusRequest } from '@/lib/complaint-batch-status-wire';
import { sessionGenerationHeader, stepUpProofIdHeader } from '@/lib/session-contract';
import { appliedResponse, complaintId, complaintScope, deletedResponse, grantA, grantB, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';
import { batchAck, batchRequest, batchResponse, batchTarget, deleteBatchAck, deleteBatchRequest, deleteBatchResponse } from '@/test/complaint-batch-status-fixture';

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

async function invoke(options: { operation?: ComplaintMutationOperation; body?: BodyInit; proofs?: AdminProofCookie[];
  headers?: HeadersInit; remove?: string[]; path?: string; query?: string; signal?: AbortSignal } = {}) {
  const operation = options.operation ?? 'status';
  const description = mutationRequest(operation);
  const headers = signedRequestHeaders(session, options.proofs ?? [proofB, proofA], { ...description.headers,
    Authorization: 'Bearer browser-override', 'X-Kira-Admin-Step-Up': 'browser-proof-override',
  });
  for (const [name, value] of new Headers(options.headers)) headers.set(name, value);
  options.remove?.forEach((name) => headers.delete(name));
  const handlers = await import('./route');
  const path = operation === 'delete' ? ['complaints', complaintId] : ['complaints', complaintId, operation];
  const request = new Request(`${origin}${options.path ?? '/api/backend/' + path.join('/')}${options.query ?? `?dataScopeId=${complaintScope}`}`, {
    method: description.method, headers, body: options.body ?? (operation === 'delete' ? undefined : description.body), signal: options.signal, duplex: 'half',
  } as RequestInit);
  return handlers[description.method](request, { params: Promise.resolve({ path }) });
}

async function invokeBatch(options: { body?: BodyInit; headers?: HeadersInit; remove?: string[]; query?: string;
  method?: 'POST' | 'DELETE'; path?: string[]; pathname?: string } = {}) {
  const description = batchRequest();
  const headers = signedRequestHeaders(session, [proofB, proofA], { ...description.headers,
    Authorization: 'Bearer browser-override', 'X-Kira-Admin-Step-Up': 'browser-proof-override' });
  for (const [name, value] of new Headers(options.headers)) headers.set(name, value);
  options.remove?.forEach((name) => headers.delete(name));
  const path = options.path ?? ['complaints', 'batch'], method = options.method ?? 'POST';
  const request = new Request(`${origin}${options.pathname ?? '/api/backend/' + path.join('/')}${options.query ?? `?dataScopeId=${complaintScope}`}`, {
    method, headers, body: options.body ?? description.body, duplex: 'half',
  } as RequestInit);
  const handlers = await import('./route');
  return handlers[method](request, { params: Promise.resolve({ path }) });
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

describe('actual atomic STATUS batch BFF connection', () => {
  it('forwards one captured batch without aggregate If-Match and retires only its historical captured proof association', async () => {
    const raw = ` \n${batchRequest().body}\t`;
    for (const remove of [[], [stepUpProofIdHeader]]) {
      fetchMock.mockResolvedValueOnce(batchResponse(undefined, { [consumedId]: grantA, 'Set-Cookie': 'private=never', Authorization: 'never' }));
      const response = await invokeBatch({ body: raw, remove });
      expect(response.status).toBe(200); expect(await response.text()).toBe(batchAck());
      const [url, init] = fetchMock.mock.calls.at(-1)!;
      expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/batch?dataScopeId=${complaintScope}`);
      expect(init).toMatchObject({ method: 'POST', body: raw, redirect: 'manual', cache: 'no-store', signal: expect.any(AbortSignal) });
      const headers = new Headers(init?.headers);
      expect(headers.get('Authorization')).toBe(`Bearer ${session.token}`);
      expect(headers.get('X-Kira-Admin-Step-Up')).toBe(remove.length ? null : proofB.token);
      expect(headers.get('X-Kira-Idempotency-Key')).toBe(batchRequest().headers['X-Kira-Idempotency-Key']);
      expect(headers.get('accept-encoding')).toBe('identity');
      for (const name of ['If-Match', 'Cookie', sessionGenerationHeader, stepUpProofIdHeader]) expect(headers.has(name)).toBe(false);
      expect(response.headers.getSetCookie()).toHaveLength(1);
      expect(response.headers.get('set-cookie')).toContain(`${proofA.name}=; Path=/api;`);
      expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
      for (const name of ['etag', 'location', consumedId, 'X-Kira-Admin-Step-Up-Grant-Id', 'authorization']) expect(response.headers.has(name)).toBe(false);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2); // Two explicit requests, never N per-target writes.
  });

  it('requires existing origin, G and CSRF plus exact batch route/query/body semantics before any dispatch', async () => {
    const body = (targets: unknown) => JSON.stringify({ action: 'STATUS', status: 'RESOLVED', targets });
    const pair = { id: complaintId, actionTag: batchTarget().actionTag };
    const cases: [Parameters<typeof invokeBatch>[0], number][] = [
      [{ headers: { Origin: 'https://other.example.test' } }, 403], [{ remove: ['X-Kira-CSRF'] }, 403],
      [{ remove: [sessionGenerationHeader] }, 401], [{ query: '' }, 400], [{ query: `?dataScopeId=${complaintScope}&dataScopeId=${complaintScope}` }, 400],
      [{ method: 'DELETE' }, 404], [{ path: ['complaints', 'batch', 'delete'] }, 404], [{ pathname: '/api/backend/complaints/b%61tch' }, 404],
      [{ headers: { 'If-Match': pair.actionTag } }, 400], [{ body: body([{ id: complaintId }]) }, 428],
      [{ body: body([{ ...pair, actionTag: `W/${pair.actionTag}` }]) }, 412], [{ body: body([{ ...pair, actionTag: null }]) }, 400],
      [{ body: body([pair, pair]) }, 400], [{ body: body([pair]).replace('"STATUS"', '"DELETE"') }, 400],
      [{ body: body([{ id: complaintId }]).replace('"status":', '"status":"OPEN","statu\\u0073":') }, 400],
    ];
    for (const [options, status] of cases) {
      const response = await invokeBatch(options);
      expect(response.status).toBe(status);
      expect(response.headers.getSetCookie()).toHaveLength(0);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('accepts50 exact members within32KiB but refuses51 or oversized bodies before forwarding any prefix', async () => {
    const targets = Array.from({ length: 50 }, (_, index) => batchTarget(`${index.toString(16).padStart(8, '0')}-1111-4111-8111-111111111111`, '1'));
    const description = prepareComplaintBatchStatusRequest(targets, 'PLANNED', complaintScope, batchRequest().headers['X-Kira-Idempotency-Key']);
    const raw = description.body.padEnd(32_768, ' ');
    fetchMock.mockResolvedValueOnce(batchResponse(description));
    const complete = await invokeBatch({ body: raw });
    expect(complete.status).toBe(200); expect(await complete.text()).toBe(batchAck(description));
    expect(fetchMock.mock.calls[0][1]?.body).toBe(raw);
    expect((await invokeBatch({ body: raw + ' ' })).status).toBe(413);
    expect((await invokeBatch({ body: JSON.stringify({ action: 'STATUS', status: 'PLANNED', targets: [...targets, batchTarget()].map(({ id, actionTag }) => ({ id, actionTag })) }) })).status).toBe(400);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('withholds malformed or partial ACKs and aggregate response tags without retiring any captured proof', async () => {
    const raw = batchAck();
    for (const response of [
      new Response(`{"items":[{"id":"${complaintId}","version":9007199254740993}]}`, { headers: batchResponse(undefined, { [consumedId]: grantA }).headers }),
      new Response(raw.replace('9007199254740993', '9007199254740992'), { headers: batchResponse(undefined, { [consumedId]: grantA }).headers }),
      batchResponse(undefined, { [consumedId]: grantA, ETag: '"aggregate"' }),
      batchResponse(undefined, { [consumedId]: grantA, Location: '/partial' }),
      new Response(raw, { status: 207, headers: batchResponse(undefined, { [consumedId]: grantA }).headers }),
    ]) {
      fetchMock.mockResolvedValueOnce(response);
      const refused = await invokeBatch();
      expect(refused.status).toBe(502); expect(refused.headers.getSetCookie()).toHaveLength(0);
      expect(await refused.text()).not.toContain(complaintId);
      expect(refused.headers.has('X-Kira-Admin-Step-Up-Consumed')).toBe(false);
    }
  });

  it('preserves post-receipt503 uncertainty while retiring only the matching captured original proof', async () => {
    fetchMock.mockResolvedValueOnce(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true', [consumedId]: grantA }));
    const response = await invokeBatch();
    expect(response.status).toBe(503); expect(response.headers.getSetCookie()).toHaveLength(1);
    expect(response.headers.get('set-cookie')).toContain(proofA.name); expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
    expect(await response.text()).toContain('SERVICE_UNAVAILABLE');
    expect(response.headers.has(consumedId)).toBe(false);
  });
});

describe('actual atomic DELETE batch BFF connection', () => {
  it('preserves one original DELETE body across consumed503 and proofless replay, retiring only its matching captured proof', async () => {
    const description = deleteBatchRequest();
    const raw = ` \n${JSON.stringify({ targets: [...description.targets].reverse().map(({ id, actionTag }) => ({ actionTag, id })), action: 'DELETE' })}\t`;
    fetchMock.mockResolvedValueOnce(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true', [consumedId]: grantA }))
      .mockResolvedValueOnce(deleteBatchResponse(description, { [consumedId]: grantA, 'Set-Cookie': 'private=never' }));
    const unknown = await invokeBatch({ body: raw });
    expect(unknown.status).toBe(503); expect(await unknown.text()).toContain('SERVICE_UNAVAILABLE');
    const completed = await invokeBatch({ body: raw, remove: [stepUpProofIdHeader] });
    expect(completed.status).toBe(200); expect(await completed.text()).toBe(deleteBatchAck(description));
    for (const response of [unknown, completed]) {
      expect(response.headers.getSetCookie()).toHaveLength(1);
      expect(response.headers.get('set-cookie')).toContain(`${proofA.name}=; Path=/api;`);
      expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
      for (const name of ['etag', 'location', consumedId, 'X-Kira-Admin-Step-Up-Grant-Id', 'authorization']) expect(response.headers.has(name)).toBe(false);
      expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
    }
    for (const [index, [url, init]] of fetchMock.mock.calls.entries()) {
      expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/batch?dataScopeId=${complaintScope}`);
      expect(init).toMatchObject({ method: 'POST', body: raw, redirect: 'manual', cache: 'no-store' });
      const headers = new Headers(init?.headers);
      expect(headers.get('Authorization')).toBe(`Bearer ${session.token}`);
      expect(headers.get('X-Kira-Admin-Step-Up')).toBe(index === 0 ? proofB.token : null);
      expect(headers.get('X-Kira-Idempotency-Key')).toBe(description.headers['X-Kira-Idempotency-Key']);
      for (const name of ['If-Match', 'Cookie', sessionGenerationHeader, stepUpProofIdHeader]) expect(headers.has(name)).toBe(false);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('rejects DELETE root widening and structural errors before tag errors without bypassing G, CSRF or the fixed POST route', async () => {
    const description = deleteBatchRequest(), pair = { id: complaintId, actionTag: batchTarget().actionTag };
    const body = (targets: unknown, extra: Record<string, unknown> = {}) => JSON.stringify({ action: 'DELETE', targets, ...extra });
    const cases: [Parameters<typeof invokeBatch>[0], number][] = [
      [{ body: description.body, headers: { Origin: 'https://other.example.test' } }, 403],
      [{ body: description.body, remove: ['X-Kira-CSRF'] }, 403], [{ body: description.body, remove: [sessionGenerationHeader] }, 401],
      [{ body: description.body, method: 'DELETE' }, 404], [{ body: description.body, headers: { 'If-Match': pair.actionTag } }, 400],
      [{ body: body([{ id: complaintId }], { status: 'OPEN' }) }, 400], [{ body: body([{ id: complaintId }], { cascade: true }) }, 400],
      [{ body: body([{ ...pair, actionTag: 'bad' }, { id: deleteBatchRequest().targets[1].id }]) }, 428],
      [{ body: body([{ ...pair, actionTag: `W/${pair.actionTag}` }]) }, 412], [{ body: body([{ ...pair, actionTag: 7 }]) }, 400],
      [{ body: body([pair, pair]) }, 400], [{ body: body([pair]) + '{}' }, 400],
      [{ body: description.body.padEnd(32_769, ' ') }, 413],
    ];
    for (const [options, status] of cases) {
      const response = await invokeBatch(options);
      expect(response.status).toBe(status); expect(response.headers.getSetCookie()).toHaveLength(0);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('never forwards a partial, extra, duplicate, reordered, STATUS-shaped, tagged or alternate-success ACK or retires proof for it', async () => {
    const description = deleteBatchRequest(), raw = deleteBatchAck(description);
    const first = `{"id":"${description.targets[0].id}"}`, second = `{"id":"${description.targets[1].id}"}`;
    const headers = deleteBatchResponse(description, { [consumedId]: grantA }).headers;
    const malformed = [`{"items":[${first}]}`, `{"items":[${first},${first}]}`, `{"items":[${second},${first}]}`,
      `{"items":[${first},${second},${second}]}`, batchAck(), raw.slice(0, -1) + ',"partial":true}'];
    for (const upstream of [
      ...malformed.map((body) => new Response(body, { headers })),
      deleteBatchResponse(description, { [consumedId]: grantA, ETag: '"aggregate"' }),
      deleteBatchResponse(description, { [consumedId]: grantA, Location: '/partial' }),
      new Response(raw, { status: 207, headers }), deletedResponse({ [consumedId]: grantA }),
    ]) {
      fetchMock.mockResolvedValueOnce(upstream);
      const response = await invokeBatch({ body: description.body });
      expect(response.status).toBe(502); expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(response.headers.has('X-Kira-Admin-Step-Up-Consumed')).toBe(false);
      expect(await response.text()).not.toContain(complaintId);
    }
    fetchMock.mockResolvedValueOnce(deleteBatchResponse());
    const statusRequest = await invokeBatch();
    expect(statusRequest.status).toBe(502); expect(statusRequest.headers.getSetCookie()).toHaveLength(0);
  });
});

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

describe('actual bounded single complaint DELETE connection', () => {
  it('forwards the exact captured method/path/key/tag with no body and emits a genuinely bodyless204', async () => {
    for (const headers of [{}, { 'Content-Length': '0' }, { 'Transfer-Encoding': 'chunked' }] as HeadersInit[]) {
      fetchMock.mockResolvedValueOnce(deletedResponse({ [consumedId]: grantA, 'Set-Cookie': 'upstream-secret=never', Authorization: 'never' }));
      const response = await invoke({ operation: 'delete', remove: ['Content-Type'], headers });
      expect(response.status).toBe(204);
      expect(response.body).toBeNull();
      expect(await response.text()).toBe('');
      expect(response.headers.get('X-Kira-Complaint-Contract')).toBe('1');
      expect(response.headers.get('cache-control')).toBe('no-store, no-transform');
      expect(response.headers.getSetCookie()).toHaveLength(1);
      expect(response.headers.get('set-cookie')).toContain(`${proofA.name}=; Path=/api;`);
      expect(response.headers.get('set-cookie')).not.toContain(proofB.name);
      for (const name of ['Content-Type', 'ETag', 'Location', consumedId, 'X-Kira-Admin-Step-Up-Grant-Id', 'Authorization']) expect(response.headers.has(name)).toBe(false);
      const [url, init] = fetchMock.mock.calls.at(-1)!;
      expect(url).toBe(`http://backend:8080/api/v1/admin/complaints/${complaintId}?dataScopeId=${complaintScope}`);
      expect(init?.method).toBe('DELETE');
      expect(init?.body).toBeUndefined();
      const forwarded = new Headers(init?.headers);
      expect(forwarded.get('Authorization')).toBe(`Bearer ${session.token}`);
      expect(forwarded.get('X-Kira-Admin-Step-Up')).toBe(proofB.token);
      expect(forwarded.get('If-Match')).toBe(mutationRequest('delete').headers['If-Match']);
      expect(forwarded.get('X-Kira-Idempotency-Key')).toBe(mutationRequest('delete').headers['X-Kira-Idempotency-Key']);
      for (const name of ['Cookie', sessionGenerationHeader, stepUpProofIdHeader, consumedId, 'Content-Length', 'Transfer-Encoding']) expect(forwarded.has(name)).toBe(false);
    }
  });

  it('retires only original captured A on authorized503 and never treats selected fresh B or an uncaptured A as its replacement', async () => {
    fetchMock.mockResolvedValueOnce(problemResponse('SERVICE_UNAVAILABLE', 503, { [consumedId]: grantA, 'X-Kira-Admin-Step-Up-Consumed': 'true' }))
      .mockResolvedValueOnce(deletedResponse({ [consumedId]: grantA }));
    const authorized = await invoke({ operation: 'delete' });
    expect(authorized.status).toBe(503);
    expect(await authorized.text()).toContain('SERVICE_UNAVAILABLE');
    expect(authorized.headers.getSetCookie()).toHaveLength(1);
    expect(authorized.headers.get('set-cookie')).toContain(proofA.name);
    expect(authorized.headers.get('set-cookie')).not.toContain(proofB.name);
    const replay = await invoke({ operation: 'delete', proofs: [proofB], remove: [stepUpProofIdHeader] });
    expect(replay.status).toBe(204);
    expect(replay.headers.getSetCookie()).toHaveLength(0);
    expect(new Headers(fetchMock.mock.calls[1][1]?.headers).has('X-Kira-Admin-Step-Up')).toBe(false);
    for (const [url, init] of fetchMock.mock.calls) {
      expect(url).toBe(fetchMock.mock.calls[0][0]);
      expect(init?.method).toBe('DELETE');
      expect(init?.body).toBeUndefined();
      for (const name of ['If-Match', 'X-Kira-Idempotency-Key']) expect(new Headers(init?.headers).get(name)).toBe(new Headers(fetchMock.mock.calls[0][1]?.headers).get(name));
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('supports proofless exact replay but never guesses retirement from missing, stale, foreign-scope/session or duplicate grant matches', async () => {
    const other = createSessionFixture(session.token);
    const otherProof = proof(grantA, other);
    const duplicate = proof(grantA);
    const source = issueAdminProof(session, 'A'.repeat(43), 'source-admin-mutation', new Date(Date.now() + 300_000).toISOString(), null);
    for (const [proofs, association] of [
      [[proofB, proofA], null], [[proofB], grantA], [[proofB, otherProof], grantA], [[proofB, source], grantA], [[proofA, duplicate], grantA],
    ] as const) {
      fetchMock.mockResolvedValueOnce(deletedResponse(association ? { [consumedId]: association } : {}));
      const response = await invoke({ operation: 'delete', proofs: [...proofs], remove: [stepUpProofIdHeader] });
      expect(response.status).toBe(204);
      expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).has('X-Kira-Admin-Step-Up')).toBe(false);
    }
    fetchMock.mockResolvedValueOnce(deletedResponse({ [consumedId]: grantA }));
    const matching = await invoke({ operation: 'delete', remove: [stepUpProofIdHeader] });
    expect(matching.headers.getSetCookie()).toHaveLength(1);
    expect(matching.headers.get('set-cookie')).toContain(proofA.name);
    vi.useFakeTimers(); vi.setSystemTime(Date.now() + 301_000);
    fetchMock.mockResolvedValueOnce(deletedResponse({ [consumedId]: grantA }));
    const expired = await invoke({ operation: 'delete' });
    expect(expired.status).toBe(204);
    expect(expired.headers.getSetCookie()).toHaveLength(0);
    expect(new Headers(fetchMock.mock.calls.at(-1)?.[1]?.headers).has('X-Kira-Admin-Step-Up')).toBe(false);
  });

  it('cannot retire a same-token replacement session or fresh proof issued after the original request capture', async () => {
    let entered!: () => void;
    let finish!: (response: Response) => void;
    const dispatched = new Promise<void>((resolve) => { entered = resolve; });
    fetchMock.mockImplementationOnce(() => { entered(); return new Promise<Response>((resolve) => { finish = resolve; }); });
    const originalName = proofA.name;
    const pending = invoke({ operation: 'delete', proofs: [proofA] });
    await dispatched;
    const freshProof = proof(grantB);
    const replacement = createSessionFixture(session.token);
    const replacementProof = proof(grantA, replacement);
    finish(deletedResponse({ [consumedId]: grantA }));
    const result = await pending;
    expect(result.status).toBe(204);
    expect(result.headers.getSetCookie()).toHaveLength(1);
    expect(result.headers.get('set-cookie')).toContain(`${originalName}=; Path=/api;`);
    for (const name of [freshProof.name, replacement.name, replacementProof.name]) expect(result.headers.get('set-cookie')).not.toContain(name);
  });

  it('refuses nonempty bodies and exact-route/query/precondition/session/framing violations before dispatch', async () => {
    const tag = mutationRequest('delete').headers['If-Match'];
    const cases: Array<[Parameters<typeof invoke>[0], number]> = [
      [{ body: ' ' }, 400], [{ body: '{}' }, 400], [{ body: '\r\n' }, 400], [{ body: new Uint8Array([0]) }, 400],
      [{ path: `/api/backend/complaints/${complaintId}/delete` }, 404], [{ path: `/api/backend/complaints/%31${complaintId.slice(1)}` }, 404],
      [{ query: `?dataScopeId=${complaintScope}&cascade=true` }, 400], [{ query: `?dataScopeId=${complaintScope}&dataScopeId=${complaintScope}` }, 400],
      [{ query: '?dataScopeId=00000000-0000-0000-0000-000000000000' }, 400], [{ headers: { Origin: 'https://outside.example.test' } }, 403],
      [{ remove: ['X-Kira-CSRF'] }, 403], [{ remove: [sessionGenerationHeader] }, 401],
      [{ headers: { [sessionGenerationHeader]: createSessionFixture(session.token).generation } }, 401],
      [{ remove: ['If-Match'] }, 428], [{ headers: { 'If-Match': `W/${tag}` } }, 412], [{ headers: { 'If-Match': '*' } }, 412],
      [{ headers: { 'If-Match': `${tag}, ${tag}` } }, 412], [{ headers: { 'If-Match': `"complaint-${complaintId}-v9223372036854775808"` } }, 412],
      [{ headers: { 'If-None-Match': '*' } }, 400], [{ headers: { 'X-Kira-Idempotency-Key': `${grantA}, ${grantB}` } }, 400],
      [{ headers: { 'X-Kira-Complaint-Contract': '1, 1' } }, 400], [{ headers: { 'Content-Type': 'text/plain' } }, 415],
      [{ headers: { 'Content-Encoding': 'gzip' } }, 415], [{ headers: { 'Content-Length': '1' } }, 400],
      [{ headers: { 'Content-Length': '0', 'Transfer-Encoding': 'chunked' } }, 400], [{ headers: { 'Transfer-Encoding': 'gzip' } }, 400],
    ];
    for (const [options, status] of cases) expect((await invoke({ ...options, operation: 'delete' })).status).toBe(status);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('keeps receipted NOTICE/absent, stale-version and pending rejections as problems, not empty204', async () => {
    for (const [code, status] of [['COMPLAINT_NOT_FOUND', 404], ['PRECONDITION_FAILED', 412], ['COMPLAINT_DELETION_PENDING', 409]] as const) {
      fetchMock.mockResolvedValueOnce(problemResponse(code, status, { [consumedId]: grantA, 'X-Kira-Admin-Step-Up-Consumed': 'true' }));
      const response = await invoke({ operation: 'delete' });
      expect(response.status).toBe(status);
      expect(await response.text()).toContain(code);
      expect(response.headers.get('set-cookie')).toContain(proofA.name);
      expect(response.headers.has(consumedId)).toBe(false);
    }
  });

  it('withholds malformed204, ACK/202, illegal body bytes and malformed association without proof retirement', async () => {
    for (const extra of [
      { 'Content-Type': 'application/json' }, { ETag: mutationRequest('delete').headers['If-Match'] }, { Location: '/elsewhere' },
      { 'Content-Length': '1' }, { 'Transfer-Encoding': 'chunked' }, { 'Content-Encoding': 'gzip' },
      { 'X-Kira-Complaint-Contract': '1, 1' }, { 'X-Kira-Admin-Step-Up-Consumed': 'true, true' },
      { [consumedId]: '' }, { [consumedId]: `${grantA}, ${grantA}` }, { [consumedId]: grantA.toUpperCase() },
    ] as HeadersInit[]) {
      const headers = new Headers({ [consumedId]: grantA });
      for (const [name, value] of new Headers(extra)) headers.set(name, value);
      fetchMock.mockResolvedValueOnce(deletedResponse(headers));
      const response = await invoke({ operation: 'delete' });
      expect(response.status).toBe(502);
      expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(response.headers.has('X-Kira-Admin-Step-Up-Consumed')).toBe(false);
    }
    const illegalBody = new Response(new Uint8Array([32]), { headers: deletedResponse({ [consumedId]: grantA }).headers });
    Object.defineProperty(illegalBody, 'status', { value: 204 }); // Synthetic acquisition seam; real Fetch normally suppresses it.
    for (const upstream of [illegalBody, appliedResponse(undefined, { [consumedId]: grantA }), new Response(null, { status: 202, headers: deletedResponse({ [consumedId]: grantA }).headers })]) {
      fetchMock.mockResolvedValueOnce(upstream);
      const response = await invoke({ operation: 'delete' });
      expect(response.status).toBe(502);
      expect(response.headers.getSetCookie()).toHaveLength(0);
    }
  });

  it('requires complete inbound EOF before dispatch and retains proofs on an apparent204 timeout or caller cancellation', async () => {
    vi.useFakeTimers();
    for (const stage of ['inbound', 'upstream', 'caller'] as const) {
      let entered!: () => void;
      const reading = new Promise<void>((resolve) => { entered = resolve; });
      const cancel = vi.fn();
      const stream = new ReadableStream<Uint8Array>({ pull() { entered(); return new Promise<void>(() => {}); }, cancel }, { highWaterMark: 0 });
      if (stage !== 'inbound') {
        const upstream = new Response(stream, { headers: deletedResponse({ [consumedId]: grantA }).headers });
        Object.defineProperty(upstream, 'status', { value: 204 });
        fetchMock.mockResolvedValueOnce(upstream);
      }
      const caller = new AbortController();
      const pending = invoke({ operation: 'delete', ...(stage === 'inbound' ? { body: stream } : {}), signal: caller.signal });
      await reading;
      if (stage === 'caller') caller.abort();
      else await vi.advanceTimersByTimeAsync(65_000);
      const response = await pending;
      expect(response.status).toBe(stage === 'caller' ? 502 : 504);
      expect(response.headers.getSetCookie()).toHaveLength(0);
      expect(cancel).toHaveBeenCalledOnce();
      if (stage === 'inbound') expect(fetchMock).not.toHaveBeenCalled();
      expect(vi.getTimerCount()).toBe(0);
    }
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
