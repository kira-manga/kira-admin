import { describe, expect, it, vi } from 'vitest';

import {
  ComplaintContentError,
  createComplaintContentDraft,
  prepareComplaintContentEdit,
  type ComplaintContentDraft,
  type ComplaintContentField,
  type ComplaintContentReason,
  type ComplaintContentSnapshot,
  type ComplaintContentType,
} from './complaint-content-editor';

// Synthetic local inputs, not a wire fixture: resource IDs are not restricted to v4,
// and the original action tag must survive without narrowing its long version.
const id = '12345678-1234-5234-8234-123456789abc';
const actionTag = '"complaint-12345678-1234-5234-8234-123456789abc-v9223372036854775807"';
const idempotencyKey = 'd9439d39-0ef2-4d30-8eb6-324486a9d36e';

function ordinarySnapshot(kind: 'REPORT' | 'REPLY' = 'REPORT', type: ComplaintContentType = 'TECHNICAL') {
  return { variant: 'ordinary' as const, kind, id, actionTag, content: { type, subject: 'Loaded subject', body: 'Loaded body' } };
}

function noticeReplySnapshot() {
  return { variant: 'notice-reply' as const, kind: 'REPLY' as const, id, actionTag, content: { body: 'Loaded body' } };
}

function ordinaryDraft(snapshot = ordinarySnapshot()) {
  const draft = createComplaintContentDraft(snapshot);
  if (draft?.variant !== 'ordinary') throw new Error('Expected an ordinary draft.');
  return draft;
}

function noticeReplyDraft(snapshot = noticeReplySnapshot()) {
  const draft = createComplaintContentDraft(snapshot);
  if (draft?.variant !== 'notice-reply') throw new Error('Expected a notice-reply draft.');
  return draft;
}

function captureText(name: 'subject' | 'body' | 'noticeBody', text: string): string {
  if (name === 'noticeBody') {
    const draft = noticeReplyDraft();
    draft.content.body = text;
    return prepareComplaintContentEdit(draft, idempotencyKey).content.body;
  }
  const draft = ordinaryDraft();
  draft.content[name] = text;
  const captured = prepareComplaintContentEdit(draft, idempotencyKey);
  if (captured.variant !== 'ordinary') throw new Error('Expected an ordinary capture.');
  return captured.content[name];
}

const textFields = [
  { name: 'subject', field: 'SUBJECT', maximum: 200, maximumBytes: 800 },
  { name: 'body', field: 'BODY', maximum: 1_000, maximumBytes: 4_000 },
  { name: 'noticeBody', field: 'BODY', maximum: 1_000, maximumBytes: 4_000 },
] as const;

function expectContentError(action: () => unknown, field: ComplaintContentField, reason: ComplaintContentReason): void {
  try {
    action();
  } catch (error) {
    expect(error).toBeInstanceOf(ComplaintContentError);
    expect(error).toMatchObject({ field, reason });
    expect(String(error)).toBe(`ComplaintContentError: Complaint content ${field}: ${reason}.`);
    expect(error).not.toHaveProperty('cause');
    return;
  }
  throw new Error('Expected a complaint content error.');
}

describe('local complaint content preparation', () => {
  it('captures REPORT and ordinary REPLY with exactly type, subject and body', () => {
    const types = ['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM'] as const;
    for (const kind of ['REPORT', 'REPLY'] as const) {
      for (const type of types) {
        const loaded = ordinarySnapshot(kind, type);
        const draft = ordinaryDraft(loaded);
        expect(draft.content).toEqual(loaded.content);
        Object.assign(draft.content, { type, subject: ' Edited subject ', body: ' Edited body ', metadata: 'not captured' });
        const captured = prepareComplaintContentEdit(draft, idempotencyKey);
        expect(captured).toEqual({
          operation: 'content', variant: 'ordinary', base: loaded, idempotencyKey,
          content: { type, subject: 'Edited subject', body: 'Edited body' },
        });
        expect(Object.keys(captured.content).sort()).toEqual(['body', 'subject', 'type']);
        expect(draft.content.subject).toBe(' Edited subject ');
        expect(draft.content.body).toBe(' Edited body ');
      }
    }
  });

  it('captures notice-thread REPLY as body only and excludes unrelated local metadata', () => {
    const loaded = Object.assign(noticeReplySnapshot(), { metadata: 'not part of the local base' });
    Object.assign(loaded.content, { type: 'CUSTOM', subject: 'not editable' });
    const draft = noticeReplyDraft(loaded);
    expect(draft.content).toEqual({ body: 'Loaded body' });
    expect(draft.base).toEqual(noticeReplySnapshot());
    Object.assign(draft.content, { body: ' Edited reply ', type: 'FEATURES', subject: 'never captured' });
    const captured = prepareComplaintContentEdit(draft, idempotencyKey);
    expect(captured).toEqual({
      operation: 'content', variant: 'notice-reply', base: noticeReplySnapshot(), idempotencyKey,
      content: { body: 'Edited reply' },
    });
    expect(Object.keys(captured.content)).toEqual(['body']);
    expect(Object.keys(captured.base.content)).toEqual(['body']);
    expect(draft.content.body).toBe(' Edited reply ');
  });

  it('keeps NOTICE and unsupported snapshots non-actionable and rejects variant or type mismatches', () => {
    const readOnly: ComplaintContentSnapshot[] = [
      { variant: 'notice', kind: 'NOTICE', id },
      { variant: 'unsupported', id },
    ];
    for (const snapshot of readOnly) {
      const draft = createComplaintContentDraft(snapshot);
      expect(draft).toBeNull();
      expectContentError(() => prepareComplaintContentEdit(draft, idempotencyKey), 'TARGET', 'READ_ONLY');
    }

    const wrongKind = { ...ordinarySnapshot(), kind: 'NOTICE' } as unknown as ComplaintContentSnapshot;
    expectContentError(() => createComplaintContentDraft(wrongKind), 'TARGET', 'VARIANT_MISMATCH');
    const unsupportedType = { ...ordinarySnapshot(), content: { type: 'FUTURE', subject: 'subject', body: 'body' } } as unknown as ComplaintContentSnapshot;
    expectContentError(() => createComplaintContentDraft(unsupportedType), 'TYPE', 'UNSUPPORTED_TYPE');

    const ordinary = ordinaryDraft();
    const notice = noticeReplyDraft();
    const mismatches = [
      { ...ordinary, base: notice.base },
      { ...notice, base: ordinary.base },
    ] as unknown as ComplaintContentDraft[];
    for (const draft of mismatches) {
      expectContentError(() => prepareComplaintContentEdit(draft, idempotencyKey), 'TARGET', 'VARIANT_MISMATCH');
    }
    ordinary.content.type = 'FUTURE' as ComplaintContentType;
    expectContentError(() => prepareComplaintContentEdit(ordinary, idempotencyKey), 'TYPE', 'UNSUPPORTED_TYPE');
    expect(ordinary.content.type).toBe('FUTURE');
    expect(ordinary.base.content.type).toBe('TECHNICAL');
  });

  it('requires a supplied canonical version-4 key without generating or normalizing it', () => {
    const draft = ordinaryDraft();
    for (const variant of ['8', '9', 'a', 'b']) {
      const key = `d9439d39-0ef2-4d30-${variant}eb6-324486a9d36e`;
      expect(prepareComplaintContentEdit(draft, key).idempotencyKey).toBe(key);
    }
    for (const key of ['', idempotencyKey.toUpperCase(), ` ${idempotencyKey}`, `${idempotencyKey}\n`, `{${idempotencyKey}}`, idempotencyKey.replaceAll('-', ''), `${idempotencyKey},${idempotencyKey}`]) {
      expectContentError(() => prepareComplaintContentEdit(draft, key), 'IDEMPOTENCY_KEY', 'NON_CANONICAL_UUID');
    }
    for (const key of ['d9439d39-0ef2-1d30-8eb6-324486a9d36e', 'd9439d39-0ef2-4d30-7eb6-324486a9d36e', 'd9439d39-0ef2-4d30-ceb6-324486a9d36e', '00000000-0000-0000-0000-000000000000']) {
      expectContentError(() => prepareComplaintContentEdit(draft, key), 'IDEMPOTENCY_KEY', 'UUID_NOT_V4');
    }
  });

  it('matches CRLF and Kotlin outer whitespace without changing internal Unicode', () => {
    const outer = '\t\n \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000';
    const raw = `${outer}العربية\r\n😀\t e\u0301  é\u00a0\u2028\u2029\u2067text\u2069${outer}`;
    const expected = 'العربية\n😀\t e\u0301  é\u00a0\u2028\u2029\u2067text\u2069';
    for (const { name } of textFields) {
      expect(captureText(name, raw)).toBe(expected);
      for (const preserved of ['\ufeff', '\u200b', '\u180e']) {
        expect(captureText(name, preserved)).toBe(preserved);
        expect(captureText(name, ` ${preserved} text ${preserved} `)).toBe(`${preserved} text ${preserved}`);
      }
      expect(captureText(name, ' \r\nfirst\r\nsecond\r\n ')).toBe('first\nsecond');
    }
  });

  it('rejects controls and malformed UTF-16 before trimming or encoding without leaking prose', () => {
    const prose = 'synthetic-private-prose';
    const controls = [...Array.from({ length: 32 }, (_, index) => index), ...Array.from({ length: 33 }, (_, index) => index + 127)]
      .filter((unit) => unit !== 9 && unit !== 10);
    const malformed = ['\ud800', '\udc00', 'body\ud800', '\udc00body', 'a\ud800b', '\ud800\ud800', '\udc00\ud800', '\ud83d\ude00\udc00'];
    for (const { name, field } of textFields) {
      for (const unit of controls) {
        const control = String.fromCharCode(unit);
        for (const text of [`${control}${prose}`, `${prose}${control}${prose}`, `${prose}${control}`]) {
          expectContentError(() => captureText(name, text), field, 'FORBIDDEN_CONTROL');
        }
      }
      for (const text of malformed) {
        expectContentError(() => captureText(name, ` ${text}${prose} `), field, 'MALFORMED_UNICODE');
      }
      expectContentError(() => captureText(name, prose.repeat(100)), field, 'TOO_LONG');
    }
    const draft = ordinaryDraft();
    draft.content.body = `\u000b${prose}`;
    expectContentError(() => prepareComplaintContentEdit(draft, idempotencyKey), 'BODY', 'FORBIDDEN_CONTROL');
    expect(draft.content.body).toBe(`\u000b${prose}`);
    expect(draft.base.content.body).toBe('Loaded body');
  });

  it('enforces nonempty text and exact code-point and UTF-8 ceilings for both content variants', () => {
    const widths = [{ text: 'a', bytes: 1 }, { text: 'é', bytes: 2 }, { text: '€', bytes: 3 }, { text: '😀', bytes: 4 }];
    for (const { name, field, maximum, maximumBytes } of textFields) {
      for (const { text, bytes } of widths) {
        const atLimit = text.repeat(maximum);
        expect([...atLimit]).toHaveLength(maximum);
        expect(new TextEncoder().encode(atLimit)).toHaveLength(maximum * bytes);
        expect(captureText(name, ` \t${atLimit}\r\n `)).toBe(atLimit);
        expectContentError(() => captureText(name, atLimit + text), field, 'TOO_LONG');
      }
      const astralLimit = '😀'.repeat(maximum);
      expect(new TextEncoder().encode(astralLimit)).toHaveLength(maximumBytes);
      expect(new TextEncoder().encode(astralLimit + 'a')).toHaveLength(maximumBytes + 1);
      expectContentError(() => captureText(name, astralLimit + 'a'), field, 'TOO_LONG');
      const combiningLimit = 'e\u0301'.repeat(maximum / 2);
      expect(captureText(name, combiningLimit)).toBe(combiningLimit);
      expectContentError(() => captureText(name, combiningLimit + '\u0301'), field, 'TOO_LONG');
      expect(captureText(name, ' x ')).toBe('x');
      for (const blank of ['', ' \t\r\n\u00a0\u2007\u202f ']) {
        expectContentError(() => captureText(name, blank), field, 'REQUIRED');
      }
    }
  });

  it('owns a detached immutable base and capture while visible drafts remain editable', () => {
    for (const loaded of [ordinarySnapshot(), noticeReplySnapshot()]) {
      const originalBase = { ...loaded, content: { ...loaded.content } };
      const draft = createComplaintContentDraft(loaded);
      if (!draft) throw new Error('Expected an editable draft.');
      expect(Object.isFrozen(loaded)).toBe(false);
      expect(Object.isFrozen(loaded.content)).toBe(false);
      expect(Object.isFrozen(draft)).toBe(true);
      expect(Object.isFrozen(draft.base)).toBe(true);
      expect(Object.isFrozen(draft.base.content)).toBe(true);
      expect(Object.isFrozen(draft.content)).toBe(false);
      expect(draft.base).not.toBe(loaded);
      expect(draft.base.content).not.toBe(loaded.content);
      expect(draft.content).not.toBe(loaded.content);
      expect(draft.content).not.toBe(draft.base.content);

      loaded.id = 'changed-source-id';
      loaded.actionTag = 'changed-source-tag';
      loaded.content.body = 'Changed source body';
      if (loaded.variant === 'ordinary') {
        loaded.content.subject = 'Changed source subject';
        loaded.content.type = 'CUSTOM';
      }
      expect(draft.base).toEqual(originalBase);
      expect(draft.content).toEqual(originalBase.content);
      draft.content.body = ' Visible\r\nbody ';
      if (draft.variant === 'ordinary') {
        draft.content.subject = ' Visible subject ';
        draft.content.type = 'FEATURES';
      }
      const keyHolder = { value: idempotencyKey };
      const captured = prepareComplaintContentEdit(draft, keyHolder.value);
      const expectedContent = draft.variant === 'ordinary'
        ? { type: 'FEATURES', subject: 'Visible subject', body: 'Visible\nbody' }
        : { body: 'Visible\nbody' };
      expect(captured).toEqual({ operation: 'content', variant: draft.variant, base: originalBase, idempotencyKey, content: expectedContent });
      expect(draft.content.body).toBe(' Visible\r\nbody ');
      expect(captured.base).not.toBe(draft.base);
      expect(captured.base.content).not.toBe(draft.base.content);
      expect(captured.content).not.toBe(draft.content);
      expect(captured.content).not.toBe(captured.base.content);
      for (const record of [captured, captured.base, captured.base.content, captured.content]) {
        expect(Object.isFrozen(record)).toBe(true);
      }
      expect(Reflect.set(captured, 'idempotencyKey', 'replacement-key')).toBe(false);
      expect(Reflect.set(captured.base, 'actionTag', 'replacement-tag')).toBe(false);
      expect(Reflect.set(captured.base.content, 'body', 'replacement-base')).toBe(false);
      expect(Reflect.set(captured.content, 'body', 'replacement-body')).toBe(false);

      keyHolder.value = 'changed-caller-key';
      draft.content.body = 'Later visible body';
      if (draft.variant === 'ordinary') {
        draft.content.type = 'CUSTOM';
        draft.content.subject = 'Later visible subject';
      }
      expect(captured).toEqual({ operation: 'content', variant: draft.variant, base: originalBase, idempotencyKey, content: expectedContent });
      expect(captured.base.id).toBe(id);
      expect(captured.base.actionTag).toBe(actionTag);
      expect(draft.base).toEqual(originalBase);
      expect(draft.content.body).toBe('Later visible body');
    }
  });

  it('prepares locally without network, browser storage or key-generation calls', () => {
    const externalEffect = vi.fn(() => { throw new Error('Unexpected external effect.'); });
    const storage = { getItem: externalEffect, setItem: externalEffect, removeItem: externalEffect, clear: externalEffect };
    vi.stubGlobal('fetch', externalEffect);
    vi.stubGlobal('localStorage', storage);
    vi.stubGlobal('sessionStorage', storage);
    vi.stubGlobal('crypto', { randomUUID: externalEffect, getRandomValues: externalEffect });
    try {
      const draft = ordinaryDraft();
      expect(prepareComplaintContentEdit(draft, idempotencyKey).idempotencyKey).toBe(idempotencyKey);
      expect(prepareComplaintContentEdit(noticeReplyDraft(), idempotencyKey).content).toEqual({ body: 'Loaded body' });
      expect(createComplaintContentDraft({ variant: 'notice', kind: 'NOTICE', id })).toBeNull();
      draft.content.body = '\u0000';
      expectContentError(() => prepareComplaintContentEdit(draft, idempotencyKey), 'BODY', 'FORBIDDEN_CONTROL');
      expect(externalEffect).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
