// @vitest-environment jsdom

import { act, StrictMode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { captureAdminSession } from '@/lib/client-api';
import { fixtureGeneration, fixtureProofId, otherGeneration, otherProofId, seedClientSession, sessionAcknowledgement, stepUpAcknowledgement } from '@/test/auth-fixture';
import { appliedResponse, complaintId, complaintScope, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { AdminApp } from './admin-app';

// Only unrelated view effects are suppressed. Shell, login, detail decoder, both existing editors,
// password dialog, authenticatedFetch and mutation transport are real. This is not browser automation.
vi.mock('./overview-view', () => ({ OverviewView: () => null }));
vi.mock('./sources-view', () => ({ SourcesView: () => null }));

const fetchMock = vi.fn<typeof fetch>();
let container: HTMLDivElement;
let root: Root;
let generation: string;
let proofId: string;
let version: string;
let detailBody: string;
let notice: boolean;
let detailReply: () => Response | Promise<Response>;
let mutationReply: (init: RequestInit) => Response | Promise<Response>;

function detailResponse() {
  const actionTag = `"complaint-${complaintId}-v${version}"`;
  const common = { id: complaintId, version, createdAt: '2026-09-20T01:02:03Z', updatedAt: '2026-09-20T01:02:03Z' };
  const item = notice ? { ...common, kind: 'NOTICE', status: 'PINNED', ownership: 'SYSTEM', ownerReference: null, noticeKey: 'privacy.notice' }
    : { ...common, kind: 'REPORT', status: 'OPEN', ownership: 'INSTALLATION', ownerReference: complaintScope,
      type: 'TECHNICAL', subject: 'Synthetic original subject', body: detailBody, actionTag,
      appVersion: null, platform: 'ANDROID', osVersion: '16', manufacturer: 'Fixture', deviceModel: 'Fixture',
      closureReason: null, replyToId: null, closedAt: null, closureProvenance: null, closureActorId: null };
  const raw = JSON.stringify(item).replace(`"version":"${version}"`, `"version":${version}`);
  return new Response(raw, { headers: { 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', ...(notice ? {} : { ETag: actionTag }) } });
}

function acknowledgement(init: RequestInit) {
  const tag = new Headers(init.headers).get('If-Match')!;
  const baseVersion = /-v([0-9]+)"$/.exec(tag)![1];
  return appliedResponse({ ...mutationRequest(), baseVersion });
}

function detailReadFailure(challenge: string | null) {
  return Response.json({ detail: 'private upstream read failure' }, {
    status: 401, headers: challenge === null ? {} : { 'WWW-Authenticate': challenge },
  });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
const patches = () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'PATCH');
const verifications = () => fetchMock.mock.calls.filter(([path]) => path === '/api/auth/step-up');
const detailReads = () => fetchMock.mock.calls.filter(([path, init]) => init?.method === 'GET' && String(path).startsWith('/api/backend/complaints/'));
const logouts = () => fetchMock.mock.calls.filter(([path]) => path === '/api/auth/logout');
function form(label: string) { return container.querySelector<HTMLFormElement>(`[aria-label="${label}"] form`)!; }
function submit(element: HTMLFormElement) { element.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); }
async function enter(selector: string, value: string) {
  const input = container.querySelector<HTMLInputElement | HTMLTextAreaElement>(selector)!;
  const prototype = input.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(prototype, 'value')!.set!;
  await act(async () => { setter.call(input, value); input.dispatchEvent(new Event('input', { bubbles: true })); });
}
async function choose(name: string, value: string) {
  const input = container.querySelector<HTMLSelectElement>(`select[name="${name}"]`)!;
  await act(async () => { input.value = value; input.dispatchEvent(new Event('change', { bubbles: true })); });
}
async function click(text: string) {
  const button = [...container.querySelectorAll('button')].find((value) => value.textContent === text);
  expect(button, text).toBeDefined();
  await act(async () => { button!.click(); });
}
async function navigate(label: string) {
  const button = [...container.querySelectorAll<HTMLButtonElement>('nav button')].find((value) => value.querySelector('strong')?.textContent === label)!;
  await act(async () => { button.click(); });
}
async function loadDetail() {
  await act(async () => { root.render(<StrictMode><AdminApp /></StrictMode>); });
  await navigate('Complaints');
  await enter('input[name="dataScopeId"]', complaintScope);
  await enter('input[name="complaintId"]', complaintId);
  await click('Load detail');
}
async function prepareStatus() {
  await choose('status', 'RESOLVED');
  await act(async () => { submit(form('Complaint moderation editor')); });
}
async function approve() {
  await enter('[role="dialog"] input[type="password"]', 'fixture-only-password');
  await act(async () => { submit(form('Confirm protected action')); });
}

beforeEach(async () => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
  sessionStorage.clear(); localStorage.clear();
  await seedClientSession();
  generation = fixtureGeneration; proofId = fixtureProofId; version = '9007199254740992';
  detailBody = 'Synthetic original body'; notice = false;
  detailReply = detailResponse;
  mutationReply = acknowledgement;
  fetchMock.mockReset();
  fetchMock.mockImplementation(async (path, init) => {
    if (path === '/api/auth/session') return Response.json({ id: complaintId, email: 'synthetic@example.test', role: 'ADMIN', createdAt: '2026-09-20T01:02:03Z', ...sessionAcknowledgement(generation) });
    if (path === '/api/auth/login') return Response.json(sessionAcknowledgement(generation));
    if (path === '/api/auth/logout') return new Response(null, { status: 204 });
    if (path === '/api/auth/step-up') return Response.json(stepUpAcknowledgement('complaint-moderation-mutation', proofId, generation));
    if (init?.method === 'PATCH') return mutationReply(init);
    if (init?.method === 'GET' && String(path).startsWith('/api/backend/complaints/')) return detailReply();
    throw new Error('Unexpected fixture request.');
  });
  vi.stubGlobal('fetch', fetchMock);
  container = document.createElement('div'); document.body.append(container); root = createRoot(container);
});
afterEach(async () => {
  await act(async () => { root.unmount(); });
  container.remove();
  vi.clearAllTimers(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals();
});

describe('bounded mounted Admin ordinary moderation connection', () => {
  it('hands off only one same-turn intent from the real editors and sends it only after scoped password approval', async () => {
    await loadDetail();
    expect(patches()).toHaveLength(0);
    expect(container.querySelector('[aria-label="Complaint content editor"]')).not.toBeNull();
    await choose('status', 'RESOLVED');
    await act(async () => {
      submit(form('Complaint moderation editor'));
      submit(form('Complaint content editor'));
      submit(form('Complaint moderation editor'));
    });
    expect(container.querySelectorAll('[role="dialog"]')).toHaveLength(1);
    expect(patches()).toHaveLength(0);
    expect(container.querySelector('fieldset')!.disabled).toBe(true);
    await approve();
    expect(patches()).toHaveLength(1);
    expect(verifications()).toHaveLength(1);
    expect(JSON.parse(verifications()[0][1]!.body as string)).toEqual({ password: 'fixture-only-password', scope: 'complaint-moderation-mutation' });
    const [path, init] = patches()[0];
    expect(path).toBe(`/api/backend/complaints/${complaintId}/status?dataScopeId=${complaintScope}`);
    expect(init?.body).toBe('{"status":"RESOLVED"}');
    expect(new Headers(init?.headers).get('If-Match')).toBe(`"complaint-${complaintId}-v9007199254740992"`);
    expect(new Headers(init?.headers).get('X-Kira-Step-Up-Proof-Id')).toBe(fixtureProofId);
    expect(container.textContent).toContain('Applied response verified.');
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(container.textContent).not.toContain('fixture-only-password');
    expect(container.textContent).not.toContain('Nothing was sent or saved');
  });

  it('keeps the exact original through timeout, explicit proofless replay and backend-requested reapproval', async () => {
    const reading = deferred<void>();
    const cancel = vi.fn();
    mutationReply = (init) => new Response(new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new TextEncoder().encode('{')); },
      pull() { reading.resolve(); return new Promise<void>(() => {}); }, cancel,
    }), { headers: acknowledgement(init).headers });
    await loadDetail(); await prepareStatus(); await approve(); await reading.promise;
    await act(async () => { await vi.advanceTimersByTimeAsync(70_000); });
    expect(cancel).toHaveBeenCalledOnce();
    expect(container.textContent).toContain('Outcome unknown or unavailable.');
    expect(patches()).toHaveLength(1);
    mutationReply = () => problemResponse('ADMIN_STEP_UP_REQUIRED', 401);
    await click('Retry original operation without new proof');
    expect(patches()).toHaveLength(2);
    expect(verifications()).toHaveLength(1);
    expect(new Headers(patches()[1][1]?.headers).has('X-Kira-Step-Up-Proof-Id')).toBe(false);
    expect(container.textContent).toContain('The backend requires complaint password approval.');
    proofId = otherProofId; mutationReply = acknowledgement;
    await click('Approve original operation'); await approve();
    expect(verifications()).toHaveLength(2);
    expect(patches()).toHaveLength(3);
    for (const [path, init] of patches()) {
      expect(path).toBe(patches()[0][0]);
      expect(init?.body).toBe(patches()[0][1]?.body);
      for (const name of ['If-Match', 'X-Kira-Idempotency-Key', 'X-Kira-Session-Generation']) {
        expect(new Headers(init?.headers).get(name)).toBe(new Headers(patches()[0][1]?.headers).get(name));
      }
    }
    expect(new Headers(patches()[2][1]?.headers).get('X-Kira-Step-Up-Proof-Id')).toBe(otherProofId);
    expect(container.textContent).toContain('Applied response verified.');
  });

  it('retains a 412 draft through explicit reload; only reviewed new intent discards it and supplies a new key/tag', async () => {
    mutationReply = () => problemResponse('PRECONDITION_FAILED', 412, { 'X-Kira-Admin-Step-Up-Consumed': 'true' });
    await loadDetail();
    await enter('textarea[name="body"]', '  synthetic operator draft  ');
    await act(async () => { submit(form('Complaint content editor')); });
    await approve();
    expect(container.textContent).toContain('Terminal rejection verified.');
    const first = patches()[0][1]!;
    expect(container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')!.value).toBe('  synthetic operator draft  ');
    version = '9007199254740994'; detailBody = 'Synthetic reviewed current body';
    await click('Reload target to review');
    expect(container.querySelector('article')?.textContent).toContain(detailBody);
    expect(container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')!.value).toBe('  synthetic operator draft  ');
    expect(patches()).toHaveLength(1);
    await click('Start new intent from reviewed detail (discard prior draft)');
    expect(container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')!.value).toBe(detailBody);
    mutationReply = acknowledgement;
    await enter('textarea[name="body"]', 'Synthetic new intent body');
    await act(async () => { submit(form('Complaint content editor')); });
    await approve();
    const second = patches()[1][1]!;
    expect(new Headers(second.headers).get('If-Match')).toBe(`"complaint-${complaintId}-v${version}"`);
    expect(new Headers(second.headers).get('X-Kira-Idempotency-Key')).not.toBe(new Headers(first.headers).get('X-Kira-Idempotency-Key'));
    expect(JSON.parse(second.body as string).body).toBe('Synthetic new intent body');
  });

  it('retains unknown above view navigation, warns before tab loss and refuses the unmounted attempt\'s late success', async () => {
    const reply = deferred<Response>();
    mutationReply = () => reply.promise;
    await loadDetail(); await prepareStatus(); await approve();
    const first = patches()[0][1]!;
    const before = new Event('beforeunload', { cancelable: true }); window.dispatchEvent(before);
    expect(before.defaultPrevented).toBe(true);
    await navigate('Sources');
    expect(first.signal?.aborted).toBe(true);
    await navigate('Complaints');
    expect(container.textContent).toContain('Outcome unknown or unavailable.');
    expect(container.querySelector('article')).toBeNull();
    await act(async () => { reply.resolve(acknowledgement(first)); });
    expect(container.textContent).not.toContain('Applied response verified.');
    mutationReply = acknowledgement;
    await click('Retry original operation without new proof');
    expect(patches()[1][1]?.body).toBe(first.body);
    expect(new Headers(patches()[1][1]?.headers).get('X-Kira-Idempotency-Key')).toBe(new Headers(first.headers).get('X-Kira-Idempotency-Key'));
    expect(container.textContent).toContain('Applied response verified.');
    const after = new Event('beforeunload', { cancelable: true }); window.dispatchEvent(after);
    expect(after.defaultPrevented).toBe(false);
  });

  it('warns on logout, then keeps old-G work non-sendable and its prose hidden under a later login', async () => {
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const reply = deferred<Response>(); mutationReply = () => reply.promise;
    await loadDetail();
    await enter('textarea[name="body"]', 'Synthetic retained private prose');
    await act(async () => { submit(form('Complaint content editor')); });
    await approve();
    const first = patches()[0][1]!;
    await act(async () => { container.querySelector<HTMLButtonElement>('button[title="Sign out"]')!.click(); });
    expect(confirm).toHaveBeenCalledOnce();
    expect(container.querySelector('nav')).not.toBeNull();
    confirm.mockReturnValue(true);
    await act(async () => { container.querySelector<HTMLButtonElement>('button[title="Sign out"]')!.click(); });
    expect(container.querySelector('nav')).toBeNull();
    expect(container.textContent).not.toContain('Synthetic retained private prose');
    generation = otherGeneration;
    await enter('input[type="email"]', 'synthetic@example.test');
    await enter('input[type="password"]', 'fixture-only-password');
    await act(async () => { submit(container.querySelector('form')!); });
    expect(container.textContent).toContain('previous session is retained and non-sendable');
    expect(container.querySelector('textarea')).toBeNull();
    expect(container.textContent).not.toContain('Synthetic retained private prose');
    expect(container.textContent).not.toContain('Synthetic original subject');
    await act(async () => { reply.resolve(acknowledgement(first)); });
    expect(container.textContent).not.toContain('Applied response verified.');
    expect(container.textContent).not.toContain('Retry original operation');
    expect(patches()).toHaveLength(1);
    expect(localStorage.length).toBe(0);
    expect(storage).toHaveBeenCalledWith('kira-admin-session-generation', otherGeneration);
    for (const [key, value] of storage.mock.calls) {
      expect(key).toBe('kira-admin-session-generation');
      expect([fixtureGeneration, otherGeneration]).toContain(value);
    }
    expect(sessionStorage.length).toBe(1);
  });

  it('does not log out for a backend Bearer denial, but does for the bounded local KiraSession expiry', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    mutationReply = () => problemResponse('UNAUTHORIZED', 401);
    await loadDetail(); await prepareStatus(); await approve();
    expect(container.textContent).toContain('This is not a local session-expiry response');
    expect(container.querySelector('nav')).not.toBeNull();
    mutationReply = () => Response.json({ detail: 'Not signed in.' }, { status: 401, headers: { 'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"' } });
    await click('Retry original operation without new proof');
    expect(container.querySelector('nav')).toBeNull();
    expect(container.querySelector('input[type="email"]')).not.toBeNull();
    expect(confirm).not.toHaveBeenCalled();
    expect(verifications()).toHaveLength(1);
  });

  it.each([null, 'Bearer realm="kira-complaints"'])('keeps valid G on an initial detail401 with challenge %s and permits an explicit same-G continuation', async (challenge) => {
    const session = captureAdminSession();
    detailReply = () => detailReadFailure(challenge);
    await loadDetail();
    expect(container.querySelector('nav')).not.toBeNull();
    expect(container.querySelector('input[type="email"], article, [role="dialog"]')).toBeNull();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('does not confirm local session expiry');
    expect(container.textContent).not.toContain('private upstream read failure');
    expect(session.isCurrent()).toBe(true);
    expect(captureAdminSession().generation).toBe(fixtureGeneration);
    expect(sessionStorage.getItem('kira-admin-session-generation')).toBe(fixtureGeneration);
    expect(logouts()).toHaveLength(0);
    expect(detailReads()).toHaveLength(1);
    expect(patches()).toHaveLength(0);
    expect(verifications()).toHaveLength(0);
    detailReply = detailResponse;
    await click('Load detail');
    expect(detailReads()).toHaveLength(2);
    expect(container.querySelector('article')).not.toBeNull();
    expect(container.querySelector('[role="alert"]')).toBeNull();
    await prepareStatus(); await approve();
    expect(patches()).toHaveLength(1);
    expect(new Headers(patches()[0][1]?.headers).get('X-Kira-Session-Generation')).toBe(fixtureGeneration);
    expect(new Headers(patches()[0][1]?.headers).get('X-Kira-Step-Up-Proof-Id')).toBe(fixtureProofId);
    expect(container.textContent).toContain('Applied response verified.');
    expect(container.textContent).not.toContain('previous session');
    expect(logouts()).toHaveLength(0);
  });

  it.each([null, 'Bearer realm="kira-complaints"'])('retains G, the terminal rejection and raw draft across a post-rejection reload401 with challenge %s', async (challenge) => {
    mutationReply = () => problemResponse('PRECONDITION_FAILED', 412, { 'X-Kira-Admin-Step-Up-Consumed': 'true' });
    await loadDetail();
    await enter('textarea[name="body"]', '  synthetic retained read-denial draft  ');
    await act(async () => { submit(form('Complaint content editor')); });
    await approve();
    const session = captureAdminSession();
    const originalBody = container.querySelector('[aria-label="Retained complaint operation"] pre')!.textContent;
    detailReply = () => detailReadFailure(challenge);
    await click('Reload target to review');
    expect(container.querySelector('nav')).not.toBeNull();
    expect(container.querySelector('input[type="email"], [role="dialog"]')).toBeNull();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('does not confirm local session expiry');
    expect(container.textContent).not.toContain('private upstream read failure');
    expect(container.textContent).toContain('Terminal rejection verified.');
    expect(container.textContent).not.toContain('previous session');
    expect(container.textContent).not.toContain('Start new intent from reviewed detail');
    expect(container.querySelector('[aria-label="Retained complaint operation"] pre')!.textContent).toBe(originalBody);
    expect(container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')!.value).toBe('  synthetic retained read-denial draft  ');
    expect(container.querySelector('fieldset')!.disabled).toBe(true);
    expect(session.isCurrent()).toBe(true);
    expect(captureAdminSession().generation).toBe(fixtureGeneration);
    expect(sessionStorage.getItem('kira-admin-session-generation')).toBe(fixtureGeneration);
    expect(logouts()).toHaveLength(0);
    expect(detailReads()).toHaveLength(2);
    expect(new Headers(detailReads()[1][1]?.headers).get('X-Kira-Session-Generation')).toBe(fixtureGeneration);
    expect(patches()).toHaveLength(1);
    expect(verifications()).toHaveLength(1);
    detailReply = detailResponse; version = '9007199254740994'; detailBody = 'Synthetic reviewed after denied read';
    await click('Reload target to review');
    expect(container.querySelector('article')?.textContent).toContain(detailBody);
    expect(container.textContent).toContain('Start new intent from reviewed detail');
    expect(container.querySelector('[aria-label="Retained complaint operation"] pre')!.textContent).toBe(originalBody);
    expect(container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')!.value).toBe('  synthetic retained read-denial draft  ');
    expect(patches()).toHaveLength(1);
    expect(logouts()).toHaveLength(0);
  });

  it.each(['initial lookup', 'post-rejection reload'])('returns to login only for the exact local KiraSession detail401 during %s', async (phase) => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const reload = phase === 'post-rejection reload';
    if (reload) {
      mutationReply = () => problemResponse('PRECONDITION_FAILED', 412, { 'X-Kira-Admin-Step-Up-Consumed': 'true' });
      await loadDetail(); await prepareStatus(); await approve();
    }
    detailReply = () => detailReadFailure('KiraSession realm="kira-admin-bff"');
    if (reload) await click('Reload target to review');
    else await loadDetail();
    expect(container.querySelector('nav, article, textarea, [role="dialog"]')).toBeNull();
    expect(container.querySelector('input[type="email"]')).not.toBeNull();
    expect(container.textContent).not.toContain('private upstream read failure');
    expect(container.textContent).not.toContain('Synthetic original body');
    expect(logouts()).toHaveLength(1);
    expect(new Headers(logouts()[0][1]?.headers).get('X-Kira-Session-Generation')).toBe(fixtureGeneration);
    expect(sessionStorage.getItem('kira-admin-session-generation')).toBeNull();
    expect(() => captureAdminSession()).toThrow();
    expect(confirm).not.toHaveBeenCalled();
    expect(patches()).toHaveLength(reload ? 1 : 0);
    expect(verifications()).toHaveLength(reload ? 1 : 0);
  });

  it('keeps a decoded NOTICE read-only even when the actual Admin moderation controls are supplied', async () => {
    notice = true;
    await loadDetail();
    expect(container.querySelector('article')?.textContent).toContain('privacy.notice');
    expect(container.querySelector('fieldset, [role="dialog"]')).toBeNull();
    expect(container.querySelector('[aria-label="Complaint content editor"]')).toBeNull();
    expect(container.querySelector('[aria-label="Complaint moderation editor"]')).toBeNull();
    expect(patches()).toHaveLength(0);
  });

  it('returns to login on local expiry during complaint password verification without dispatching the prepared mutation', async () => {
    await loadDetail(); await prepareStatus();
    fetchMock.mockResolvedValueOnce(Response.json({ detail: 'Not signed in.' }, { status: 401, headers: { 'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"' } }));
    await approve();
    expect(container.querySelector('nav, [role="dialog"]')).toBeNull();
    expect(container.querySelector('input[type="email"]')).not.toBeNull();
    expect(patches()).toHaveLength(0);
    expect(container.textContent).not.toContain('Synthetic original body');
  });
});
