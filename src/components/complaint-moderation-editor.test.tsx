// @vitest-environment jsdom

import { act, StrictMode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { prepareComplaintModerationRequest, type ComplaintModerationTarget } from '@/lib/complaint-moderation-wire';
import type { ComplaintMutationRequest } from '@/lib/complaint-mutation-wire';
import { ComplaintModerationEditor } from './complaint-moderation-editor';

// Existing React/jsdom component-test pattern, real preparation helper, synthetic
// local inputs only. This is not browser/device automation or authenticated intake.
const id = '12345678-1234-5234-8234-123456789abc';
const actionTag = `"complaint-${id}-v9007199254740993"`;
const dataScopeId = 'aa437ccf-1ee1-4a01-9adf-9c9a771897d0';
const nextScope = 'bb437ccf-1ee1-4a01-9adf-9c9a771897d0';
const idempotencyKey = 'd9439d39-0ef2-4d30-8eb6-324486a9d36e';
const nextKey = '64c5c620-01cb-445f-9cb9-b0fa0aa79d7d';

function target(kind: 'REPORT' | 'REPLY' = 'REPORT'): ComplaintModerationTarget {
  return { id, actionTag, kind, ownership: 'INSTALLATION' };
}

let container: HTMLDivElement;
let root: Root | null;
const externalEffect = vi.fn(() => { throw new Error('Unexpected external effect.'); });

function select(name: 'operation' | 'status'): HTMLSelectElement {
  const element = container.querySelector<HTMLSelectElement>(`select[name="${name}"]`);
  if (!element) throw new Error(`Missing ${name} editor.`);
  return element;
}

function reasonInput(): HTMLTextAreaElement {
  const element = container.querySelector<HTMLTextAreaElement>('textarea[name="reason"]');
  if (!element) throw new Error('Missing closure reason editor.');
  return element;
}

function form(): HTMLFormElement {
  const element = container.querySelector('form');
  if (!element) throw new Error('Missing moderation form.');
  return element;
}

function prepareButton(): HTMLButtonElement {
  const element = container.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (!element) throw new Error('Missing prepare action.');
  return element;
}

function preparedBody(): HTMLPreElement {
  const element = container.querySelector<HTMLPreElement>('pre[aria-label="Last prepared body inspection"]');
  if (!element) throw new Error('Missing prepared body inspection.');
  return element;
}

async function renderEditor(loaded: ComplaintModerationTarget, onPrepared: (request: ComplaintMutationRequest) => void, key = idempotencyKey, scope = dataScopeId) {
  const mounted = root;
  if (!mounted) throw new Error('Missing fixture root.');
  await act(async () => {
    mounted.render(<StrictMode><ComplaintModerationEditor target={loaded} dataScopeId={scope} idempotencyKey={key} onPrepared={onPrepared} /></StrictMode>);
  });
}

async function choose(name: 'operation' | 'status', value: string) {
  const element = select(name);
  await act(async () => {
    element.value = value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
  });
}

async function enterReason(value: string) {
  const element = reasonInput();
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
  if (!setter) throw new Error('Missing native textarea setter.');
  await act(async () => {
    setter.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
  });
}

async function prepare() {
  await act(async () => { prepareButton().click(); });
}

async function submitDirectly() {
  const event = new Event('submit', { bubbles: true, cancelable: true });
  await act(async () => { form().dispatchEvent(event); });
  expect(event.defaultPrevented).toBe(true);
}

async function unmount() {
  const mounted = root;
  root = null;
  if (mounted) await act(async () => { mounted.unmount(); });
}

beforeEach(() => {
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
  externalEffect.mockClear();
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  vi.stubGlobal('fetch', externalEffect);
  const storage = { getItem: externalEffect, setItem: externalEffect, removeItem: externalEffect, clear: externalEffect };
  vi.stubGlobal('localStorage', storage);
  vi.stubGlobal('sessionStorage', storage);
  vi.stubGlobal('crypto', { randomUUID: externalEffect, getRandomValues: externalEffect });
});

afterEach(async () => {
  try {
    await unmount();
    expect(externalEffect).not.toHaveBeenCalled();
  } finally {
    container.remove();
    vi.unstubAllGlobals();
  }
});

describe('unmounted-by-product complaint moderation editor', () => {
  it('hands off the supplied status intent synchronously only after explicit selection and submission', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), onPrepared);
    expect(Array.from(select('operation').options).map((option) => option.value)).toEqual(['status', 'closure']);
    expect(select('status').value).toBe('');
    expect(container.querySelector('textarea')).toBeNull();
    expect(onPrepared).not.toHaveBeenCalled();
    await prepare();
    expect(onPrepared).not.toHaveBeenCalled();
    expect(select('status').getAttribute('aria-invalid')).toBe('true');
    expect(container.querySelector('[role="alert"]')?.textContent).toBe('Choose a status target before preparing.');
    await choose('status', 'PLANNED');
    expect(onPrepared).not.toHaveBeenCalled();
    expect(container.querySelector('[role="alert"]')).toBeNull();
    await act(async () => {
      prepareButton().click();
      expect(onPrepared).toHaveBeenCalledTimes(1);
    });
    const captured = onPrepared.mock.calls[0][0];
    // Existing wire tests own DTO fields/vocabulary. This checks the component's binding.
    expect(captured).toEqual(prepareComplaintModerationRequest(target(), { operation: 'status', status: 'PLANNED' }, dataScopeId, idempotencyKey));
    expect(Object.isFrozen(captured)).toBe(true);
    expect(Object.isFrozen(captured.headers)).toBe(true);
    expect(container.querySelector('.notice-success')).toBeNull();
    expect(container.querySelector('[role="status"]')?.textContent).toContain('Preparation itself sends nothing; the parent workflow reports any submission separately.');
  });

  it('keeps raw closure editing and the detached original body, with safe directional/markup inspection only', async () => {
    const loaded = target('REPLY');
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(loaded, onPrepared);
    await choose('operation', 'closure');
    expect(container.querySelector('[name="status"]')).toBeNull();
    expect(reasonInput().getAttribute('maxlength')).toBeNull();
    const raw = ' \u2007Reason 😀\n<img src="fixture"> literal \\u202E; actual \u202E\u00a0 ';
    const expected = prepareComplaintModerationRequest(loaded, { operation: 'closure', reason: raw }, dataScopeId, idempotencyKey);
    await enterReason(raw);
    await prepare();
    const captured = onPrepared.mock.calls[0][0];
    expect(captured).toEqual(expected);
    expect(reasonInput().value).toBe(raw);
    expect(reasonInput().dir).toBe('auto');
    expect(reasonInput().style.unicodeBidi).toBe('isolate');
    expect(container.querySelector('.notice-warning')?.textContent).toContain('Directional marks are present.');
    const inspection = preparedBody().textContent;
    expect(inspection).not.toContain('\u202E');
    expect(inspection).toContain('literal \\\\u202E; actual \\u202E');
    expect(preparedBody().dir).toBe('ltr');
    expect(preparedBody().style.unicodeBidi).toBe('isolate');
    expect(container.querySelector('img, script, a, iframe')).toBeNull();
    const visible = container.querySelector<HTMLPreElement>('[aria-label="Closure reason visible inspection"]')!;
    expect(visible.textContent).toContain('[U+202E]');
    expect(visible.textContent).not.toContain('\u202E');
    expect(visible.style.overflowWrap).toBe('anywhere');
    reasonInput().setSelectionRange(0, raw.length);
    const setData = vi.fn();
    const copy = new Event('copy', { bubbles: true, cancelable: true });
    Object.defineProperty(copy, 'clipboardData', { value: { setData } });
    reasonInput().dispatchEvent(copy);
    expect(copy.defaultPrevented).toBe(true);
    expect(setData).toHaveBeenCalledWith('text/plain', raw.replace('\u202E', '[U+202E]'));
    expect(reasonInput().value).toBe(raw);
    await enterReason('Later draft');
    Object.assign(loaded, { actionTag: `"complaint-${id}-v2"` });
    expect(captured).toEqual(expected);
    expect(preparedBody().textContent).toBe(inspection);
    expect(onPrepared).toHaveBeenCalledTimes(1);
  });

  it('keeps the visible draft and unconsumed key available after a preparation refusal', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), onPrepared);
    await choose('operation', 'closure');
    const raw = ' \u2007\t ';
    await enterReason(raw);
    await prepare();
    expect(onPrepared).not.toHaveBeenCalled();
    expect(reasonInput().value).toBe(raw);
    expect(prepareButton().disabled).toBe(false);
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    expect(container.querySelector('[role="status"]')).toBeNull();
    await enterReason('Corrected reason');
    expect(container.querySelector('[role="alert"]')).toBeNull();
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0].headers['X-Kira-Idempotency-Key']).toBe(idempotencyKey);
    expect(prepareButton().disabled).toBe(true);
  });

  it('exposes no controls or callbacks for read-only and unsupported local targets', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    for (const loaded of [
      { ...target(), kind: 'NOTICE' },
      { ...target(), ownership: 'SYSTEM' },
      { ...target(), kind: 'LEGACY' },
      { ...target(), ownership: 'UNSUPPORTED' },
    ]) {
      await renderEditor(loaded as ComplaintModerationTarget, onPrepared);
      expect(container.querySelector('form, button, textarea, select, input')).toBeNull();
      expect(container.textContent).toContain('No moderation description can be prepared.');
    }
    expect(onPrepared).not.toHaveBeenCalled();
  });

  it('fences operation changes and old keys while preserving editing across invalid and unused key rotation', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), onPrepared);
    await choose('status', 'IN_PROGRESS');
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    await choose('operation', 'closure');
    const raw = ' \nKeep editing 😀 \t ';
    await enterReason(raw);
    expect(reasonInput().disabled).toBe(false);
    await submitDirectly();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(preparedBody().textContent).toBe(onPrepared.mock.calls[0][0].body);
    expect(container.textContent).toContain('another key is not a retry');
    await renderEditor(target(), onPrepared, nextKey.toUpperCase());
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(reasonInput().value).toBe(raw);
    expect(container.querySelector('[role="alert"]')).not.toBeNull();
    await renderEditor(target(), onPrepared, nextKey);
    expect(select('operation').value).toBe('closure');
    expect(reasonInput().value).toBe(raw);
    expect(prepareButton().disabled).toBe(false);
    expect(container.querySelector('[role="alert"]')).toBeNull();
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(2);
    expect(onPrepared.mock.calls[1][0].headers['X-Kira-Idempotency-Key']).toBe(nextKey);
    expect(onPrepared.mock.calls[1][0]).toEqual(prepareComplaintModerationRequest(target(), { operation: 'closure', reason: raw }, dataScopeId, nextKey));
    await renderEditor(target(), onPrepared, idempotencyKey);
    expect(reasonInput().value).toBe(raw);
    expect(prepareButton().disabled).toBe(true);
    await submitDirectly();
    expect(onPrepared).toHaveBeenCalledTimes(2);
    await choose('operation', 'status');
    expect(select('status').value).toBe('IN_PROGRESS');
    await submitDirectly();
    expect(onPrepared).toHaveBeenCalledTimes(2);
  });

  it('keeps the original key consumed when the synchronous callback reenters and throws', async () => {
    const failure = new Error('Synthetic local handoff failure.');
    const reported: unknown[] = [];
    const onError = (event: ErrorEvent) => {
      if (event.error === failure) {
        reported.push(event.error);
        event.preventDefault();
      }
    };
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>().mockImplementationOnce(() => {
      form().dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      throw failure;
    });
    window.addEventListener('error', onError);
    try {
      await renderEditor(target(), onPrepared);
      await choose('status', 'OPEN');
      await prepare();
      expect(onPrepared).toHaveBeenCalledTimes(1);
      expect(prepareButton().disabled).toBe(true);
      await choose('operation', 'closure');
      await enterReason('Edited after local handoff failure');
      await submitDirectly();
      const replacement = { ...target(), actionTag: `"complaint-${id}-v2"` };
      await renderEditor(replacement, onPrepared, idempotencyKey, nextScope);
      await choose('status', 'RESOLVED');
      await submitDirectly();
      expect(onPrepared).toHaveBeenCalledTimes(1);
      expect(onPrepared.mock.calls[0][0].headers['If-Match']).toBe(actionTag);
      expect(onPrepared.mock.calls[0][0].dataScopeId).toBe(dataScopeId);
      expect(reported).toEqual([failure]);
    } finally {
      window.removeEventListener('error', onError);
    }
  });

  it('retires drafts/captures on target, tag, scope and read-only replacements without releasing keys on return', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), onPrepared);
    await choose('operation', 'closure');
    await enterReason('Original A');
    await prepare();
    const replacements: { loaded: ComplaintModerationTarget; scope: string }[] = [
      { loaded: { ...target(), id: '87654321-1234-5234-8234-123456789abc', actionTag: '"complaint-87654321-1234-5234-8234-123456789abc-v1"' }, scope: dataScopeId },
      { loaded: { ...target(), actionTag: `"complaint-${id}-v2"` }, scope: dataScopeId },
      { loaded: target(), scope: nextScope },
      { loaded: { ...target(), kind: 'NOTICE' }, scope: dataScopeId },
      { loaded: { ...target(), ownership: 'SYSTEM' }, scope: dataScopeId },
    ];
    for (const { loaded, scope } of replacements) {
      await enterReason('Unprepared A');
      const oldForm = form();
      await renderEditor(loaded, onPrepared, idempotencyKey, scope);
      expect(oldForm.isConnected).toBe(false);
      expect(container.querySelector('[aria-label="Last prepared moderation"]')).toBeNull();
      if (loaded.kind === 'NOTICE' || loaded.ownership === 'SYSTEM') {
        expect(container.querySelector('form')).toBeNull();
      } else {
        expect(select('operation').value).toBe('status');
        expect(select('status').value).toBe('');
        await choose('operation', 'closure');
        expect(reasonInput().value).toBe('');
        expect(prepareButton().disabled).toBe(true);
        await enterReason('Valid but must not hand off');
        await submitDirectly();
      }
      await act(async () => { oldForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
      await renderEditor(target(), onPrepared);
      await choose('operation', 'closure');
      expect(reasonInput().value).toBe('');
      expect(prepareButton().disabled).toBe(true);
      await enterReason('Valid but still consumed');
      await submitDirectly();
    }
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0]).toEqual(prepareComplaintModerationRequest(target(), { operation: 'closure', reason: 'Original A' }, dataScopeId, idempotencyKey));
  });

  it('preserves equivalent-prop editing, uses the current callback and copies the original local target before handoff', async () => {
    const first = vi.fn<(request: ComplaintMutationRequest) => void>();
    const current = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), first);
    await choose('operation', 'closure');
    await enterReason(' Keep original binding ');
    const replacement = target();
    await renderEditor(replacement, current);
    expect(reasonInput().value).toBe(' Keep original binding ');
    // Mutation without a parent render must not retarget the existing draft/capture.
    Object.assign(replacement, { actionTag: `"complaint-${id}-v2"` });
    await prepare();
    expect(first).not.toHaveBeenCalled();
    expect(current).toHaveBeenCalledTimes(1);
    expect(current.mock.calls[0][0]).toEqual(prepareComplaintModerationRequest(target(), { operation: 'closure', reason: ' Keep original binding ' }, dataScopeId, idempotencyKey));
  });

  it('never hands off on mount, edits or unmount, including a detached unprepared submission', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>();
    await renderEditor(target(), onPrepared);
    await choose('status', 'NOT_PLANNED');
    const oldForm = form();
    await unmount();
    await act(async () => { oldForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
    expect(container.childElementCount).toBe(0);
    expect(onPrepared).not.toHaveBeenCalled();
  });

  it('allows the synchronous local callback to remove the editor without later handoffs', async () => {
    const onPrepared = vi.fn<(request: ComplaintMutationRequest) => void>(() => { root?.render(null); });
    await renderEditor(target(), onPrepared);
    await choose('status', 'NOT_PLANNED');
    await prepare();
    expect(container.childElementCount).toBe(0);
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0]).toEqual(prepareComplaintModerationRequest(target(), { operation: 'status', status: 'NOT_PLANNED' }, dataScopeId, idempotencyKey));
  });
});
