import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureCsrf, fixtureGeneration, fixtureProofId, otherGeneration, otherProofId, sessionAcknowledgement, stepUpAcknowledgement } from '@/test/auth-fixture';
import type { StepUpApproval } from './step-up-contract';

const fetchMock = vi.fn<typeof fetch>();
const stored = new Map<string, string>();
const credentials = { email: 'synthetic@example.test', password: 'fixture-only-password' };
let api: typeof import('./client-api');

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

async function seed(generation = fixtureGeneration) {
  fetchMock.mockResolvedValueOnce(Response.json(sessionAcknowledgement(generation)));
  expect(await api.loginSession(credentials, () => true)).toBe(true);
  fetchMock.mockClear();
}

beforeEach(async () => {
  vi.resetModules();
  stored.clear();
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => stored.set(key, value),
    removeItem: (key: string) => stored.delete(key),
  });
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  api = await import('./client-api');
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('explicit browser session selection and ownership', () => {
  it('adopts only the current login ACK; an older delayed login cannot overwrite newer G', async () => {
    const first = deferred<Response>();
    const second = deferred<Response>();
    fetchMock.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const oldLogin = api.loginSession(credentials, () => true);
    const newLogin = api.loginSession(credentials, () => true);
    second.resolve(Response.json(sessionAcknowledgement(otherGeneration)));
    expect(await newLogin).toBe(true);
    first.resolve(Response.json(sessionAcknowledgement(fixtureGeneration)));
    expect(await oldLogin).toBe(false);
    expect(api.captureAdminSession().generation).toBe(otherGeneration);
    expect([...stored]).toEqual([['kira-admin-session-generation', otherGeneration]]);
    expect(JSON.stringify([...stored])).not.toContain(fixtureCsrf);
    expect(JSON.stringify([...stored])).not.toContain(credentials.password);
  });

  it('does not adopt a successful login after its owning screen/action is retired', async () => {
    const response = deferred<Response>();
    fetchMock.mockReturnValueOnce(response.promise);
    let current = true;
    const login = api.loginSession(credentials, () => current);
    current = false;
    response.resolve(Response.json(sessionAcknowledgement()));
    expect(await login).toBe(false);
    expect(stored.size).toBe(0);
    expect(() => api.captureAdminSession()).toThrow('Sign in again');
  });

  it('captures logout headers and retires client ownership synchronously; delayed completion cannot erase a later login', async () => {
    await seed();
    const oldSession = api.captureAdminSession();
    const reply = deferred<Response>();
    fetchMock.mockReturnValueOnce(reply.promise);
    const logout = api.logoutSession();
    expect(oldSession.isCurrent()).toBe(false);
    expect(() => api.captureAdminSession()).toThrow('Sign in again');
    expect(stored.size).toBe(0);
    expect(Object.fromEntries(new Headers(fetchMock.mock.calls[0][1]?.headers))).toEqual({
      'x-kira-session-generation': fixtureGeneration, 'x-kira-csrf': fixtureCsrf,
    });
    await seed(otherGeneration);
    reply.resolve(Response.json({ ok: true }));
    await logout;
    expect(api.captureAdminSession().generation).toBe(otherGeneration);
    expect(stored.get('kira-admin-session-generation')).toBe(otherGeneration);
  });

  it.each([200, 401, 403])('does not let an old session check (%i) replace or clear a newer G/CSRF', async (status) => {
    await seed();
    const reply = deferred<Response>();
    fetchMock.mockReturnValueOnce(reply.promise);
    const check = api.sessionFetch();
    await seed(otherGeneration);
    reply.resolve(Response.json({ id: 'admin', email: credentials.email, role: 'ADMIN', createdAt: '2026-09-20T00:00:00Z', ...sessionAcknowledgement() }, { status }));
    expect(await check).toBeUndefined();
    expect(api.captureAdminSession().generation).toBe(otherGeneration);
    expect(api.captureAdminSession().csrfToken).toBe(fixtureCsrf);
  });

  it('requires an explicit per-tab selector and never discovers a session by cookie scanning', async () => {
    expect(await api.sessionFetch()).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
    // A reload reads only the opaque selector, then confirms it with the selected signed cookie.
    vi.resetModules();
    stored.set('kira-admin-session-generation', otherGeneration);
    api = await import('./client-api');
    fetchMock.mockResolvedValueOnce(Response.json({ detail: 'Missing selected cookie.' }, { status: 401 }));
    expect(await api.sessionFetch()).toBeNull();
    expect(Object.fromEntries(new Headers(fetchMock.mock.calls[0][1]?.headers))).toEqual({ 'x-kira-session-generation': otherGeneration });
    expect(stored.size).toBe(0);
  });

  it('rehydrates CSRF only after a matching bounded selected-session response, storing G alone', async () => {
    stored.set('kira-admin-session-generation', fixtureGeneration);
    const session = { id: 'synthetic-admin', email: credentials.email, role: 'ADMIN', createdAt: '2026-09-20T00:00:00Z', ...sessionAcknowledgement() };
    fetchMock.mockResolvedValueOnce(Response.json(session));
    expect(await api.sessionFetch()).toEqual(session);
    expect(api.captureAdminSession().csrfToken).toBe(fixtureCsrf);
    expect(api.captureAdminSession().generation).toBe(fixtureGeneration);
    expect([...stored]).toEqual([['kira-admin-session-generation', fixtureGeneration]]);
    fetchMock.mockResolvedValueOnce(Response.json({ detail: 'Synthetic outage.' }, { status: 503 }));
    await expect(api.sessionFetch()).rejects.toThrow('could not be checked');
    expect(api.captureAdminSession().generation).toBe(fixtureGeneration);
  });

  it('keeps signed-session CSRF in memory and includes explicit G on media and upload requests', async () => {
    await seed();
    expect(api.adminMediaUrl('synthetic-id')).toBe(`/api/media/synthetic-id?sessionGeneration=${fixtureGeneration}`);
    class FakeUpload {
      static last: FakeUpload;
      headers = new Map<string, string>();
      listeners = new Map<string, () => void>();
      upload = { addEventListener: vi.fn() };
      timeout = 0;
      status = 200;
      responseText = '{"id":"uploaded"}';
      constructor() { FakeUpload.last = this; }
      open = vi.fn();
      setRequestHeader(name: string, value: string) { this.headers.set(name, value); }
      addEventListener(name: string, callback: () => void) { this.listeners.set(name, callback); }
      send() { this.listeners.get('load')?.(); }
    }
    vi.stubGlobal('XMLHttpRequest', FakeUpload);
    expect(await api.apiUpload('/api/tutorial-media-upload', new FormData(), vi.fn())).toEqual({ id: 'uploaded' });
    expect(FakeUpload.last.headers.get('X-Kira-Session-Generation')).toBe(fixtureGeneration);
    expect(FakeUpload.last.headers.get('X-Kira-CSRF')).toBe(fixtureCsrf);
    expect(FakeUpload.last.timeout).toBe(70_000);
    expect([...stored.values()]).toEqual([fixtureGeneration]);
  });

  it('fails closed on malformed or over-bound login acknowledgements without storing any authority', async () => {
    for (const fields of [{ generation: 'not-a-generation' }, { csrfToken: 'not-a-token' }, { csrfToken: fixtureCsrf + '\n' },
      { expiresAt: '2000-01-01T00:00:00Z' }, { expiresAt: '2099-01-01T00:00:00Z\n' }, { token: 'must-not-be-exposed' }]) {
      fetchMock.mockResolvedValueOnce(Response.json({ ...sessionAcknowledgement(), ...fields }));
      await expect(api.loginSession(credentials, () => true)).rejects.toThrow('could not be confirmed');
      expect(stored.size).toBe(0);
    }
    const cancel = vi.fn();
    fetchMock.mockResolvedValueOnce(new Response(new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array(4097)); }, cancel })));
    await expect(api.loginSession(credentials, () => true)).rejects.toThrow('could not be confirmed');
    expect(cancel).toHaveBeenCalledOnce();
    expect(stored.size).toBe(0);
  });
});

describe('captured immutable proof selectors, not a mutable latest-proof pointer', () => {
  it('does not continue an old verification after logout/re-login to another generation', async () => {
    await seed();
    const { verifyProtectedAction } = await import('./step-up');
    const reply = deferred<Response>();
    fetchMock.mockReturnValueOnce(reply.promise);
    const onApproved = vi.fn(async () => {});
    const clearPassword = vi.fn();
    const work = verifyProtectedAction({ password: 'fixture', isCurrent: () => true, clearPassword, onApproved });
    fetchMock.mockResolvedValueOnce(Response.json({ ok: true }));
    await api.logoutSession();
    await seed(otherGeneration);
    reply.resolve(Response.json(stepUpAcknowledgement()));
    await work;
    expect(onApproved).not.toHaveBeenCalled();
    expect(clearPassword).not.toHaveBeenCalled();
    expect(api.captureAdminSession().generation).toBe(otherGeneration);
  });

  it('hands each concurrent approval its own immutable P, even when the newer issuance resolves first', async () => {
    await seed();
    const { verifyProtectedAction } = await import('./step-up');
    const first = deferred<Response>();
    const second = deferred<Response>();
    fetchMock.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const forwarded: StepUpApproval[] = [];
    const onApproved = async (approval: StepUpApproval) => {
      expect(Object.isFrozen(approval)).toBe(true);
      const headers = new Headers(api.sourceApprovalInit(approval, { headers: { 'If-Match': '"saved"' } }).headers);
      expect(headers.get('X-Kira-Step-Up-Proof-Id')).toBe(approval.proofId);
      expect(headers.get('X-Kira-Session-Generation')).toBe(approval.generation);
      expect(headers.get('If-Match')).toBe('"saved"');
      forwarded.push(approval);
    };
    const action = { password: 'fixture', isCurrent: () => true, clearPassword: vi.fn(), onApproved };
    const oldWork = verifyProtectedAction(action);
    const newWork = verifyProtectedAction(action);
    second.resolve(Response.json(stepUpAcknowledgement('source-admin-mutation', otherProofId)));
    await newWork;
    first.resolve(Response.json(stepUpAcknowledgement('source-admin-mutation', fixtureProofId)));
    await oldWork;
    expect(forwarded.map((approval) => approval.proofId)).toEqual([otherProofId, fixtureProofId]);
    expect([...stored.values()]).toEqual([fixtureGeneration]);
  });

  it('refuses a captured old-G action instead of replacing its explicit selector with current G', async () => {
    await seed();
    const oldApproval = stepUpAcknowledgement();
    const oldInit = api.sourceApprovalInit(oldApproval, { method: 'POST' });
    await seed(otherGeneration);
    expect(() => api.sourceApprovalInit(oldApproval)).toThrow('Verify your password');
    await expect(api.apiFetch('sources/Azora/editor-draft/publish', oldInit)).rejects.toThrow('previous admin session');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
