// @vitest-environment jsdom

import { act, StrictMode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ComplaintReadClientError, fetchComplaintAdminDetail } from '@/lib/complaint-read-client';
import type { ParsedComplaintAdminDetail } from '@/lib/complaint-read-wire';
import { ComplaintDetailView } from './complaint-detail-view';

vi.mock('@/lib/complaint-read-client', async (original) => ({
  ...await original<typeof import('@/lib/complaint-read-client')>(),
  fetchComplaintAdminDetail: vi.fn(),
}));

const fetchDetail = vi.mocked(fetchComplaintAdminDetail);
const id = '11111111-1111-4111-8111-111111111111';
const scope = '22222222-2222-4222-8222-222222222222';
const nextId = '33333333-3333-4333-8333-333333333333';
const nextScope = '44444444-4444-4444-8444-444444444444';
let container: HTMLDivElement;
let root: Root | null;

function detail(identifier = id): ParsedComplaintAdminDetail {
  const actionTag = `"complaint-${identifier}-v9223372036854775807"`;
  return {
    item: {
      id: identifier, version: '9223372036854775807', kind: 'REPORT', status: 'OPEN', ownership: 'INSTALLATION',
      ownerReference: scope, createdAt: '2026-09-20T01:02:03.123456Z', updatedAt: '2026-09-20T01:02:03.123457Z',
      type: 'TECHNICAL', subject: 'Example subject', body: '<img src=x onerror=alert(1)>\nLiteral body', actionTag,
      appVersion: null, platform: 'ANDROID', osVersion: '16', manufacturer: 'Example', deviceModel: 'Device',
      closureReason: null, replyToId: null, closedAt: null, closureProvenance: null, closureActorId: null,
    },
    contentSnapshot: { variant: 'ordinary', kind: 'REPORT', id: identifier, actionTag, content: { type: 'TECHNICAL', subject: 'Example subject', body: 'Body' } },
    moderationTarget: { id: identifier, kind: 'REPORT', ownership: 'INSTALLATION', actionTag },
  };
}

function deferred() {
  let resolve!: (value: ParsedComplaintAdminDetail) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<ParsedComplaintAdminDetail>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

async function enter(name: 'dataScopeId' | 'complaintId', value: string) {
  const input = container.querySelector<HTMLInputElement>(`input[name="${name}"]`)!;
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => { setter.call(input, value); input.dispatchEvent(new Event('input', { bubbles: true })); });
}

async function submit() {
  await act(async () => { container.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
}

async function mount() {
  await act(async () => { root!.render(<StrictMode><ComplaintDetailView /></StrictMode>); });
  await enter('dataScopeId', scope);
  await enter('complaintId', id);
}

beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  fetchDetail.mockReset();
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
});

afterEach(async () => {
  if (root) await act(async () => { root!.unmount(); });
  container.remove();
  vi.unstubAllGlobals();
});

describe('mounted read-only complaint lookup', () => {
  it('loads only on explicit submission and renders raw text, Long digits and timestamps without moderation', async () => {
    fetchDetail.mockResolvedValue(detail());
    await mount();
    expect(fetchDetail).not.toHaveBeenCalled();
    await submit();
    expect(fetchDetail).toHaveBeenCalledTimes(1);
    expect(fetchDetail).toHaveBeenCalledWith({ id, dataScopeId: scope, signal: expect.any(AbortSignal) });
    expect(container.textContent).toContain('9223372036854775807');
    expect(container.textContent).toContain('2026-09-20T01:02:03.123457Z');
    expect(container.textContent).toContain('<img src=x onerror=alert(1)>');
    expect(container.querySelector('img')).toBeNull();
    expect([...container.querySelectorAll('button')].map((button) => button.textContent)).toEqual(['Load detail']);
    await enter('complaintId', nextId);
    expect(container.querySelector('article')).toBeNull();
    expect(fetchDetail).toHaveBeenCalledTimes(1);
  });

  it.each([
    ['UNAVAILABLE', 'unavailable or not found'],
    ['SESSION_EXPIRED', 'session has expired'],
    ['FORBIDDEN', 'do not have permission'],
    ['INVALID_RESPONSE', 'request or response is invalid'],
    ['NETWORK', 'could not be loaded'],
  ] as const)('shows a safe %s state, clears previous content and never retries automatically', async (reason, message) => {
    fetchDetail.mockResolvedValueOnce(detail()).mockRejectedValueOnce(new ComplaintReadClientError(reason));
    await mount();
    await submit();
    await submit();
    expect(container.querySelector('article')).toBeNull();
    expect(container.querySelector('[role="alert"]')?.textContent).toContain(message);
    expect(fetchDetail).toHaveBeenCalledTimes(2);
  });

  it('aborts an old scope lookup and ignores its late success without overwriting the newer result', async () => {
    const old = deferred();
    fetchDetail.mockReturnValueOnce(old.promise).mockResolvedValueOnce(detail(nextId));
    await mount();
    await submit();
    const oldSignal = fetchDetail.mock.calls[0][0].signal;
    await enter('dataScopeId', nextScope);
    await enter('complaintId', nextId);
    expect(oldSignal.aborted).toBe(true);
    expect(container.querySelector('article')).toBeNull();
    await submit();
    await act(async () => { old.resolve(detail()); });
    expect(container.querySelector('article')?.textContent).toContain(nextId);
    expect(container.querySelector('article')?.textContent).not.toContain(id);
    expect(fetchDetail.mock.calls[1][0].dataScopeId).toBe(nextScope);
  });

  it('fences duplicate submissions synchronously and ignores a late failure after an ID edit', async () => {
    const old = deferred();
    fetchDetail.mockReturnValueOnce(old.promise).mockResolvedValueOnce(detail(nextId));
    await mount();
    await act(async () => {
      for (let index = 0; index < 2; index++) container.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });
    expect(fetchDetail).toHaveBeenCalledTimes(1);
    await enter('complaintId', nextId);
    expect(fetchDetail.mock.calls[0][0].signal.aborted).toBe(true);
    await submit();
    await act(async () => { old.reject(new Error('Do not display upstream diagnostics')); });
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(container.querySelector('article')?.textContent).toContain(nextId);
    expect(container.querySelector('button')?.disabled).toBe(false);
  });

  it('aborts on unmount and never lets the old component fill a remounted view', async () => {
    const old = deferred();
    fetchDetail.mockReturnValueOnce(old.promise);
    await mount();
    await submit();
    await act(async () => { root!.unmount(); });
    root = null;
    expect(fetchDetail.mock.calls[0][0].signal.aborted).toBe(true);
    root = createRoot(container);
    await mount();
    await act(async () => { old.resolve(detail()); });
    expect(container.querySelector('article')).toBeNull();
    expect(fetchDetail).toHaveBeenCalledTimes(1);
  });

  it('renders a NOTICE as read-only without invented content or mutation controls', async () => {
    fetchDetail.mockResolvedValue({
      item: { id, version: '1', kind: 'NOTICE', status: 'PINNED', ownership: 'SYSTEM', ownerReference: null, noticeKey: 'privacy.notice', createdAt: '2026-09-20T01:02:03Z', updatedAt: '2026-09-20T01:02:03Z' },
      contentSnapshot: { variant: 'notice', kind: 'NOTICE', id }, moderationTarget: null,
    });
    await mount();
    await submit();
    expect(container.querySelector('article')?.textContent).toContain('privacy.notice');
    expect(container.querySelector('article pre')).toBeNull();
    expect(container.querySelector('article button')).toBeNull();
  });
});
