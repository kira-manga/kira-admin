// @vitest-environment jsdom

import { act, Profiler, StrictMode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { ComplaintContentSnapshot, PreparedComplaintContentEdit } from '@/lib/complaint-content-editor';
import { ComplaintContentEditor } from './complaint-content-editor';

// Real component, React events and accepted preparation helper. Synthetic local
// snapshots only; jsdom does not establish browser layout or clipboard behavior.
const id = '12345678-1234-5234-8234-123456789abc';
const actionTag = '"complaint-12345678-1234-5234-8234-123456789abc-v9223372036854775807"';
const idempotencyKey = 'd9439d39-0ef2-4d30-8eb6-324486a9d36e';
const nextKey = '64c5c620-01cb-445f-9cb9-b0fa0aa79d7d';

function ordinarySnapshot(kind: 'REPORT' | 'REPLY' = 'REPORT'): Extract<ComplaintContentSnapshot, { variant: 'ordinary' }> {
  return { variant: 'ordinary', kind, id, actionTag, content: { type: 'TECHNICAL', subject: 'Loaded subject', body: 'Loaded body' } };
}

function noticeReplySnapshot(): Extract<ComplaintContentSnapshot, { variant: 'notice-reply' }> {
  return { variant: 'notice-reply', kind: 'REPLY', id, actionTag, content: { body: 'Loaded notice reply' } };
}

let container: HTMLDivElement;
let root: Root | null;
let commits: { body: string | null; prepared: boolean }[];
const externalEffect = vi.fn(() => { throw new Error('Unexpected external effect.'); });

function textarea(name: 'subject' | 'body'): HTMLTextAreaElement {
  const element = container.querySelector<HTMLTextAreaElement>(`textarea[name="${name}"]`);
  if (!element) throw new Error(`Missing ${name} editor.`);
  return element;
}

function typeSelect(): HTMLSelectElement {
  const element = container.querySelector<HTMLSelectElement>('select[name="type"]');
  if (!element) throw new Error('Missing type editor.');
  return element;
}

function prepareButton(): HTMLButtonElement {
  const element = Array.from(container.querySelectorAll<HTMLButtonElement>('button'))
    .find((button) => button.textContent === 'Prepare edit');
  if (!element) throw new Error('Missing prepare action.');
  return element;
}

function form(): HTMLFormElement {
  const element = container.querySelector('form');
  if (!element) throw new Error('Missing editor form.');
  return element;
}

function inspection(label: string): HTMLPreElement {
  const element = container.querySelector<HTMLPreElement>(`pre[aria-label="${label} inspection"]`);
  if (!element) throw new Error(`Missing ${label} inspection.`);
  return element;
}

function fields() {
  return Array.from(container.querySelectorAll('label.field > span')).map((label) => label.textContent);
}

async function renderEditor(snapshot: ComplaintContentSnapshot, onPrepared: (edit: PreparedComplaintContentEdit) => void, key = idempotencyKey) {
  const mounted = root;
  if (!mounted) throw new Error('Missing fixture root.');
  await act(async () => {
    mounted.render(<StrictMode><Profiler id="content-editor" onRender={() => {
      commits.push({
        body: container.querySelector<HTMLTextAreaElement>('textarea[name="body"]')?.value ?? null,
        prepared: container.querySelector('[aria-label="Last prepared content"]') !== null,
      });
    }}><ComplaintContentEditor snapshot={snapshot} idempotencyKey={key} onPrepared={onPrepared} /></Profiler></StrictMode>);
  });
}

async function enter(name: 'subject' | 'body', value: string) {
  const element = textarea(name);
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
  if (!setter) throw new Error('Missing native textarea setter.');
  await act(async () => {
    setter.call(element, value);
    element.dispatchEvent(new Event('input', { bubbles: true }));
  });
}

async function chooseType(value: string) {
  const element = typeSelect();
  await act(async () => {
    element.value = value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
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
  commits = [];
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

describe('unmounted-by-product complaint content editor', () => {
  it.each(['REPORT', 'REPLY'] as const)('offers exactly the ordinary %s fields and supported types', async (kind) => {
    const loaded = ordinarySnapshot(kind);
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(loaded, onPrepared);
    expect(fields()).toEqual(['Type', 'Subject', 'Body']);
    expect(Array.from(typeSelect().options).map((option) => option.value)).toEqual(['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM']);
    expect(textarea('subject').value).toBe(loaded.content.subject);
    expect(textarea('body').value).toBe(loaded.content.body);
    expect(onPrepared).not.toHaveBeenCalled();

    await chooseType('FEATURES');
    await prepare();
    expect(onPrepared).toHaveBeenCalledExactlyOnceWith({
      operation: 'content', variant: 'ordinary', base: loaded, idempotencyKey,
      content: { type: 'FEATURES', subject: 'Loaded subject', body: 'Loaded body' },
    });
    expect(Object.keys(onPrepared.mock.calls[0][0].content).sort()).toEqual(['body', 'subject', 'type']);
    expect(container.querySelector('.notice-success')).toBeNull();
    expect(container.querySelector('[role="status"]')?.textContent).toContain('Preparation itself sends nothing; the parent workflow reports any submission separately.');
  });

  it('offers only body for a notice-thread reply, ignoring unrelated loaded metadata', async () => {
    const loaded = Object.assign(noticeReplySnapshot(), { metadata: 'not editable' });
    Object.assign(loaded.content, { type: 'CUSTOM', subject: 'not editable' });
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(loaded, onPrepared);
    expect(fields()).toEqual(['Body']);
    expect(container.querySelector('select, [name="subject"]')).toBeNull();
    await enter('body', ' \u2007Edited notice reply\nsecond line\u00a0 ');
    await prepare();
    expect(onPrepared).toHaveBeenCalledExactlyOnceWith({
      operation: 'content', variant: 'notice-reply', base: noticeReplySnapshot(), idempotencyKey,
      content: { body: 'Edited notice reply\nsecond line' },
    });
    expect(Object.keys(onPrepared.mock.calls[0][0].content)).toEqual(['body']);
    expect(textarea('body').value).toBe(' \u2007Edited notice reply\nsecond line\u00a0 ');
    expect(container.querySelector('pre[aria-label="Prepared subject inspection"]')).toBeNull();
  });

  it('hands off synchronously, preserves raw visible edits, and detaches the last capture from later edits', async () => {
    const loaded = ordinarySnapshot();
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(loaded, onPrepared);
    const subject = ' \u2007\ufeffEdited subject\n第二 line\u00a0 ';
    const body = '\n \u00a0Draft 😀\nsecond line \t ';
    await chooseType('FEATURES');
    await enter('subject', subject);
    await enter('body', body);
    await act(async () => {
      prepareButton().click();
      expect(onPrepared).toHaveBeenCalledTimes(1);
    });
    const captured = onPrepared.mock.calls[0][0];
    const expectedContent = { type: 'FEATURES', subject: '\ufeffEdited subject\n第二 line', body: 'Draft 😀\nsecond line' };
    expect(captured).toEqual({ operation: 'content', variant: 'ordinary', base: ordinarySnapshot(), idempotencyKey, content: expectedContent });
    expect(textarea('subject').value).toBe(subject);
    expect(textarea('body').value).toBe(body);
    expect(captured.base).not.toBe(loaded);
    expect(captured.base.content).not.toBe(loaded.content);
    for (const record of [captured, captured.base, captured.base.content, captured.content]) expect(Object.isFrozen(record)).toBe(true);

    await chooseType('CUSTOM');
    await enter('subject', 'Later subject');
    await enter('body', 'Later body');
    Object.assign(loaded.content, { body: 'Changed external snapshot' });
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(captured.content).toEqual(expectedContent);
    expect(captured.base).toEqual(ordinarySnapshot());
    expect(inspection('Prepared body').textContent).toBe(JSON.stringify(expectedContent.body));
    expect(inspection('Draft body').textContent).toBe(JSON.stringify('Later body'));
    expect(textarea('body').value).toBe('Later body');
  });

  it('leaves a loaded CRLF draft alone while only the detached capture receives normalization', async () => {
    const loaded = { ...ordinarySnapshot(), content: { type: 'TECHNICAL' as const, subject: ' Subject\r\nsecond ', body: ' Body\r\nsecond ' } };
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(loaded, onPrepared);
    // Native textareas expose LF through value even when React's stored draft
    // contains CRLF. Compare before/after and inspect the unmodified draft too.
    const before = { subject: textarea('subject').value, body: textarea('body').value };
    expect(inspection('Draft body').textContent).toBe(JSON.stringify(loaded.content.body));
    await prepare();
    expect(textarea('subject').value).toBe(before.subject);
    expect(textarea('body').value).toBe(before.body);
    expect(inspection('Draft body').textContent).toBe(JSON.stringify(loaded.content.body));
    expect(onPrepared.mock.calls[0][0].content).toEqual({ type: 'TECHNICAL', subject: 'Subject\nsecond', body: 'Body\nsecond' });
    expect(onPrepared.mock.calls[0][0].base).toEqual(loaded);
  });

  it.each([
    { field: 'subject', value: ' \u2007 ', message: 'Subject is required.' },
    { field: 'body', value: '\t\n ', message: 'Body is required.' },
    { field: 'subject', value: '😀'.repeat(201), message: 'Subject exceeds its code-point or UTF-8 byte limit.' },
    { field: 'body', value: '\u000bsynthetic-prose', message: 'Body contains a forbidden control character.' },
    { field: 'body', value: 'synthetic-prose\ud800', message: 'Body contains malformed Unicode.' },
  ] as const)('preserves the $field draft and rejects preparation: $message', async ({ field, value, message }) => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), onPrepared);
    await enter(field, value);
    await prepare();
    expect(onPrepared).not.toHaveBeenCalled();
    expect(textarea(field).value).toBe(value);
    expect(textarea(field).getAttribute('aria-invalid')).toBe('true');
    expect(container.querySelector('[role="alert"]')?.textContent).toBe(message);
    expect(container.querySelector('[role="status"]')).toBeNull();
    expect(prepareButton().disabled).toBe(false);
    await enter(field, 'Corrected');
    expect(container.querySelector('[role="alert"]')).toBeNull();
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0].idempotencyKey).toBe(idempotencyKey);
    expect(prepareButton().disabled).toBe(true);
  });

  it('accepts the astral code-point/UTF-8 ceilings without a UTF-16 maxLength and rejects excess without truncation', async () => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), onPrepared);
    expect(textarea('subject').getAttribute('maxlength')).toBeNull();
    expect(textarea('body').getAttribute('maxlength')).toBeNull();
    const subject = '😀'.repeat(200);
    const body = '😀'.repeat(1_000);
    await enter('subject', subject);
    await enter('body', body);
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    const captured = onPrepared.mock.calls[0][0];
    expect(captured.content).toEqual({ type: 'TECHNICAL', subject, body });
    await enter('body', `${body}😀`);
    await renderEditor(ordinarySnapshot(), onPrepared, nextKey);
    expect(textarea('body').value).toBe(`${body}😀`);
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(textarea('body').value).toBe(`${body}😀`);
    expect(container.querySelector('[role="alert"]')?.textContent).toBe('Body exceeds its code-point or UTF-8 byte limit.');
    expect(captured.content.body).toBe(body);
    expect(inspection('Prepared body').textContent).toBe(JSON.stringify(body));
    expect(prepareButton().disabled).toBe(false);
  });

  it.each(['', idempotencyKey.toUpperCase(), id])('does not invent or repair the supplied invalid key %j', async (key) => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), onPrepared, key);
    await enter('body', ' Keep this draft ');
    await prepare();
    expect(onPrepared).not.toHaveBeenCalled();
    expect(textarea('body').value).toBe(' Keep this draft ');
    expect(container.querySelector('[role="alert"]')?.textContent).toBe('Idempotency key must be a canonical lowercase UUIDv4.');
    await renderEditor(ordinarySnapshot(), onPrepared, idempotencyKey);
    expect(textarea('body').value).toBe(' Keep this draft ');
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(prepareButton().disabled).toBe(false);
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0].idempotencyKey).toBe(idempotencyKey);
    expect(onPrepared.mock.calls[0][0].content.body).toBe('Keep this draft');
  });

  it('fences reentrant and direct submission before render, and refuses a changed draft with the same consumed key', async () => {
    let reentered = false;
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>(() => {
      if (!reentered) {
        reentered = true;
        form().dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      }
    });
    await renderEditor(ordinarySnapshot(), onPrepared);
    await enter('body', 'Captured once');
    await prepare();
    expect(reentered).toBe(true);
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(prepareButton().disabled).toBe(true);
    await enter('body', 'Changed after capture');
    expect(textarea('body').disabled).toBe(false);
    await prepare();
    await submitDirectly();
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0].content.body).toBe('Captured once');
    expect(textarea('body').value).toBe('Changed after capture');
    expect(inspection('Prepared body').textContent).toBe(JSON.stringify('Captured once'));
  });

  it('preserves raw editing on unused-key rotation and refuses any previously consumed key, not just the latest one', async () => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), onPrepared);
    await enter('body', 'First capture');
    await prepare();
    const subject = ' \u2007Next subject \t ';
    const body = ' \nNext body 😀 \t ';
    await chooseType('CUSTOM');
    await enter('subject', subject);
    await enter('body', body);
    await renderEditor(ordinarySnapshot(), onPrepared, nextKey);
    expect(typeSelect().value).toBe('CUSTOM');
    expect(textarea('subject').value).toBe(subject);
    expect(textarea('body').value).toBe(body);
    expect(prepareButton().disabled).toBe(false);
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(inspection('Prepared body').textContent).toBe(JSON.stringify('First capture'));
    await prepare();
    expect(onPrepared).toHaveBeenCalledTimes(2);
    expect(onPrepared.mock.calls[1][0]).toEqual({
      operation: 'content', variant: 'ordinary', base: ordinarySnapshot(), idempotencyKey: nextKey,
      content: { type: 'CUSTOM', subject: 'Next subject', body: 'Next body 😀' },
    });
    await renderEditor(ordinarySnapshot(), onPrepared, idempotencyKey);
    expect(textarea('subject').value).toBe(subject);
    expect(textarea('body').value).toBe(body);
    expect(prepareButton().disabled).toBe(true);
    await submitDirectly();
    expect(onPrepared).toHaveBeenCalledTimes(2);
    expect(onPrepared.mock.calls[0][0].content.body).toBe('First capture');
  });

  const replacements: { name: string; snapshot: ComplaintContentSnapshot }[] = [
    { name: 'target ID', snapshot: { ...ordinarySnapshot(), id: '87654321-1234-5234-8234-123456789abc', actionTag: '"complaint-87654321-1234-5234-8234-123456789abc-v1"' } },
    { name: 'action tag', snapshot: { ...ordinarySnapshot(), actionTag: '"complaint-12345678-1234-5234-8234-123456789abc-v9223372036854775806"' } },
    { name: 'ordinary kind', snapshot: ordinarySnapshot('REPLY') },
    { name: 'notice-thread variant', snapshot: noticeReplySnapshot() },
    { name: 'NOTICE denial', snapshot: { variant: 'notice', kind: 'NOTICE', id } },
    { name: 'unsupported denial', snapshot: { variant: 'unsupported', id } },
  ];

  it.each(replacements)('retires editing/capture on $name replacement and A→B→A without releasing consumed keys', async ({ snapshot }) => {
    const firstPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    const nextPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), firstPrepared);
    await enter('body', 'Captured A');
    await prepare();
    await enter('body', 'Unprepared A');
    const oldForm = form();
    const oldButton = prepareButton();
    commits = [];
    await renderEditor(snapshot, nextPrepared);
    const expectedBody = 'content' in snapshot ? snapshot.content.body : null;
    expect(commits.length).toBeGreaterThan(0);
    for (const commit of commits) expect(commit).toEqual({ body: expectedBody, prepared: false });
    expect(oldForm.isConnected).toBe(false);
    expect(oldButton.isConnected).toBe(false);
    await act(async () => { oldForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
    expect(firstPrepared).toHaveBeenCalledTimes(1);
    expect(nextPrepared).not.toHaveBeenCalled();
    if (expectedBody === null) {
      expect(container.querySelector('form, button, input, textarea, select')).toBeNull();
      expect(container.textContent).toContain('read-only');
    } else {
      expect(prepareButton().disabled).toBe(true);
      await submitDirectly();
      expect(nextPrepared).not.toHaveBeenCalled();
      await renderEditor(snapshot, nextPrepared, nextKey);
      expect(textarea('body').value).toBe(expectedBody);
      expect(prepareButton().disabled).toBe(false);
      await prepare();
      expect(nextPrepared).toHaveBeenCalledTimes(1);
      expect(nextPrepared.mock.calls[0][0].base).toEqual(snapshot);
      expect(nextPrepared.mock.calls[0][0].idempotencyKey).toBe(nextKey);
    }
    await renderEditor(ordinarySnapshot(), firstPrepared);
    expect(textarea('body').value).toBe('Loaded body');
    expect(container.querySelector('[aria-label="Last prepared content"]')).toBeNull();
    expect(prepareButton().disabled).toBe(true);
    await submitDirectly();
    expect(firstPrepared).toHaveBeenCalledTimes(1);
    expect(firstPrepared.mock.calls[0][0].content.body).toBe('Captured A');
  });

  it('retains a draft across equivalent parent renders while using only the current callback', async () => {
    const firstPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    const nextPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), firstPrepared);
    await enter('body', ' Still editing ');
    await renderEditor(ordinarySnapshot(), nextPrepared);
    expect(textarea('body').value).toBe(' Still editing ');
    await prepare();
    expect(firstPrepared).not.toHaveBeenCalled();
    expect(nextPrepared).toHaveBeenCalledTimes(1);
    expect(nextPrepared.mock.calls[0][0].content.body).toBe('Still editing');
  });

  it('denies an invalid local snapshot rather than exposing a form', async () => {
    const invalid = { ...ordinarySnapshot(), kind: 'NOTICE' } as unknown as ComplaintContentSnapshot;
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(invalid, onPrepared);
    expect(container.querySelector('form, button, input, textarea, select')).toBeNull();
    expect(container.textContent).toContain('No edit can be prepared.');
    expect(onPrepared).not.toHaveBeenCalled();
  });

  it('never notifies on mount, edits or unmount, including old detached submission', async () => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(ordinarySnapshot(), onPrepared);
    await enter('body', 'Unprepared draft');
    const oldForm = form();
    await unmount();
    await act(async () => { oldForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
    expect(container.childElementCount).toBe(0);
    expect(onPrepared).not.toHaveBeenCalled();
  });

  it('allows the synchronous local handoff to remove the editor without later notifications', async () => {
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>(() => { root?.render(null); });
    await renderEditor(noticeReplySnapshot(), onPrepared);
    await prepare();
    expect(container.childElementCount).toBe(0);
    expect(onPrepared).toHaveBeenCalledTimes(1);
    expect(onPrepared.mock.calls[0][0].content).toEqual({ body: 'Loaded notice reply' });
  });

  it('keeps a key consumed after a throwing callback, including across a target-tag change', async () => {
    const failure = new Error('Synthetic local handoff failure.');
    const reported: unknown[] = [];
    const onError = (event: ErrorEvent) => {
      if (event.error === failure) {
        reported.push(event.error);
        event.preventDefault();
      }
    };
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>()
      .mockImplementationOnce(() => { throw failure; });
    window.addEventListener('error', onError);
    try {
      await renderEditor(ordinarySnapshot(), onPrepared);
      await prepare();
      expect(onPrepared).toHaveBeenCalledTimes(1);
      expect(prepareButton().disabled).toBe(true);
      await enter('body', 'Edited after callback failure');
      await submitDirectly();
      expect(onPrepared).toHaveBeenCalledTimes(1);
      const next = { ...ordinarySnapshot(), actionTag: '"complaint-12345678-1234-5234-8234-123456789abc-v2"' };
      await renderEditor(next, onPrepared);
      expect(prepareButton().disabled).toBe(true);
      await submitDirectly();
      expect(onPrepared).toHaveBeenCalledTimes(1);
      await renderEditor(next, onPrepared, nextKey);
      expect(prepareButton().disabled).toBe(false);
      await prepare();
      expect(onPrepared).toHaveBeenCalledTimes(2);
      expect(onPrepared.mock.calls[1][0].idempotencyKey).toBe(nextKey);
      expect(reported).toEqual([failure]);
    } finally {
      window.removeEventListener('error', onError);
    }
  });

  it('warns and escapes directional controls in isolated inspection/copy while preserving raw drafts and payloads', async () => {
    const controls = ['\u061c', '\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e', '\u2066', '\u2067', '\u2068', '\u2069', '\u206a', '\u206b', '\u206c', '\u206d', '\u206e', '\u206f'];
    const body = `<img src="fixture" onerror="fixture"> العربية literal \\u202E; actual \u202E; ${controls.join('x')} end`;
    const subject = 'مرحبا\u202E<strong id="untrusted">subject</strong>\u202C';
    const loaded = { ...ordinarySnapshot(), content: { type: 'TECHNICAL' as const, subject, body } };
    const onPrepared = vi.fn<(edit: PreparedComplaintContentEdit) => void>();
    await renderEditor(loaded, onPrepared);
    expect(textarea('subject').value).toBe(subject);
    expect(textarea('body').value).toBe(body);
    expect(container.querySelector('.notice-warning')?.textContent).toContain('Directional marks are present.');
    expect(container.querySelector('[aria-label="Draft inspection"]')?.textContent).toContain('These previews are not replacement text or request payloads.');
    const preview = inspection('Draft body');
    for (const mark of controls) {
      const hex = mark.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0');
      expect(preview.textContent).not.toContain(mark);
      expect(preview.textContent).toContain(`\\u${hex}`);
      expect(preview.parentElement?.querySelector('small')?.textContent).toContain(`U+${hex}`);
    }
    expect(preview.textContent).toContain('literal \\\\u202E');
    expect(preview.textContent).toContain('actual \\u202E');
    expect(preview.innerHTML).toContain('&lt;img');
    expect(container.querySelector('img, script, a, iframe, #untrusted')).toBeNull();
    expect(preview.dir).toBe('ltr');
    expect(preview.style.unicodeBidi).toBe('isolate');
    expect(preview.style.overflowWrap).toBe('anywhere');
    expect(textarea('body').dir).toBe('auto');
    expect(textarea('body').style.unicodeBidi).toBe('isolate');
    for (const field of ['subject', 'body'] as const) {
      const input = textarea(field);
      input.setSelectionRange(0, input.value.length);
      const setData = vi.fn();
      const copy = new Event('copy', { bubbles: true, cancelable: true });
      Object.defineProperty(copy, 'clipboardData', { value: { setData } });
      input.dispatchEvent(copy);
      expect(copy.defaultPrevented).toBe(true);
      expect(setData).toHaveBeenCalledWith('text/plain', expect.stringContaining('[U+202E]'));
      expect(setData.mock.calls[0][1]).not.toContain('\u202E');
      expect(input.value).toBe(field === 'subject' ? subject : body);
    }
    expect(Array.from(container.querySelectorAll('button')).map((button) => button.textContent)).toEqual(['Prepare edit']);

    await prepare();
    expect(onPrepared.mock.calls[0][0].content).toEqual({ type: 'TECHNICAL', subject, body });
    expect(textarea('subject').value).toBe(subject);
    expect(textarea('body').value).toBe(body);
    expect(inspection('Prepared body').textContent).toBe(preview.textContent);
    await enter('subject', 'Plain subject');
    await enter('body', 'Plain body');
    textarea('body').setSelectionRange(0, 10);
    const plainCopy = new Event('copy', { bubbles: true, cancelable: true });
    textarea('body').dispatchEvent(plainCopy);
    expect(plainCopy.defaultPrevented).toBe(false);
    expect(container.querySelector('.notice-warning')).toBeNull();
    expect(inspection('Prepared body').textContent).toContain('actual \\u202E');
    expect(onPrepared).toHaveBeenCalledTimes(1);
  });
});
