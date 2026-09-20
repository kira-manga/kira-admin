import { describe, expect, it } from 'vitest';

import { ComplaintReadWireError, decodeComplaintAdminDetail } from './complaint-read-wire';

// Synthetic fields from backend79859f2a ComplaintAdminReadResponses/HttpTest, not
// production captures or an authenticated reader. Version is emitted as a raw token.
type Fields = Record<string, string | null>;
const id = '12345678-1234-4234-8234-123456789abc';
const otherId = '87654321-1234-4234-8234-123456789abc';
const noticeId = '12345678-1234-3234-8234-123456789abc';
const ownerId = 'a9439d39-0ef2-4d30-8eb6-324486a9d36e';
const version = '9007199254740993';
const now = '2026-09-20T01:02:03.123456Z';
const tag = (value = version, target = id) => `"complaint-${target}-v${value}"`;
const bytes = (value: string) => new TextEncoder().encode(value);

function content(overrides: Fields = {}): Fields {
  return {
    id, kind: 'REPORT', status: 'OPEN', createdAt: now, updatedAt: now, version,
    ownership: 'INSTALLATION', ownerReference: ownerId, type: 'TECHNICAL', subject: 'Synthetic subject',
    body: 'Synthetic body', actionTag: tag(), appVersion: null, platform: 'ANDROID', osVersion: '',
    manufacturer: '', deviceModel: '', closureReason: null, replyToId: null,
    closedAt: null, closureProvenance: null, closureActorId: null, ...overrides,
  };
}

function notice(overrides: Fields = {}): Fields {
  return {
    id: noticeId, kind: 'NOTICE', status: 'PINNED', createdAt: now, updatedAt: now,
    version: '1', ownership: 'SYSTEM', ownerReference: null, noticeKey: 'admin.read.notice', ...overrides,
  };
}

function raw(fields = content()): string {
  return `{${Object.entries(fields).map(([name, value]) => `${JSON.stringify(name)}:${name === 'version' ? value : JSON.stringify(value)}`).join(',')}}`;
}

function response(fields = content()) {
  return { status: 200, contentType: 'application/json;charset=UTF-8', contract: '1', etag: fields.actionTag ?? null, body: bytes(raw(fields)) };
}

function rejects(action: () => unknown) {
  try {
    action();
  } catch (error) {
    expect(error).toBeInstanceOf(ComplaintReadWireError);
    expect(error).toMatchObject({ reason: 'INVALID_RESPONSE' });
    expect(String(error)).toBe('ComplaintReadWireError: Complaint read: INVALID_RESPONSE.');
    expect(error).not.toHaveProperty('cause');
    return;
  }
  throw new Error('Expected detail refusal.');
}

describe('dormant Admin detail decoding and local projections', () => {
  it('maps only the four fixed content shapes and never fabricates a NOTICE moderation tag', () => {
    const variants = [
      content(),
      content({ kind: 'REPLY', replyToId: otherId, status: 'CLOSED', closureReason: 'Synthetic reason', closedAt: now, closureProvenance: 'ADMIN', closureActorId: noticeId }),
      content({ kind: 'REPLY', replyToId: noticeId, type: 'CUSTOM', subject: null, noticeKey: 'admin.read.notice', status: 'PINNED' }),
      notice(),
    ];
    for (const fields of variants) {
      const expectedId = fields.id as string;
      const decoded = decodeComplaintAdminDetail(expectedId, response(fields));
      expect(decoded.item).toEqual(fields); // Only the numeric wire token becomes a decimal string.
      for (const record of [decoded, decoded.item, decoded.contentSnapshot]) expect(Object.isFrozen(record)).toBe(true);
      if (fields.kind === 'NOTICE') {
        expect(decoded.contentSnapshot).toEqual({ variant: 'notice', kind: 'NOTICE', id: noticeId });
        expect(decoded.moderationTarget).toBeNull();
        expect(decoded.item).not.toHaveProperty('actionTag');
      } else {
        expect(decoded.moderationTarget).toEqual({ id, kind: fields.kind, ownership: 'INSTALLATION', actionTag: tag() });
        expect(Object.isFrozen(decoded.moderationTarget)).toBe(true);
        const expected = fields.noticeKey === undefined
          ? { variant: 'ordinary', kind: fields.kind, id, actionTag: tag(), content: { type: fields.type, subject: fields.subject, body: fields.body } }
          : { variant: 'notice-reply', kind: 'REPLY', id, actionTag: tag(), content: { body: fields.body } };
        expect(decoded.contentSnapshot).toEqual(expected);
        if ('content' in decoded.contentSnapshot) expect(Object.isFrozen(decoded.contentSnapshot.content)).toBe(true);
      }
      expect(decoded).not.toHaveProperty('dataScopeId');
      expect(decoded).not.toHaveProperty('authenticated');
      expect(decoded).not.toHaveProperty('verified');
    }
  });

  it('retains original Long digits and microsecond timestamp strings independently of field order', () => {
    for (const original of [version, '9223372036854775807']) {
      const fields = content({ version: original, actionTag: tag(original), createdAt: '0001-01-01T00:00:00Z', updatedAt: '9999-12-31T23:59:59.999999Z' });
      const input = response(fields);
      input.body = bytes(` \n${raw(Object.fromEntries(Object.entries(fields).reverse()))}\t`);
      const decoded = decodeComplaintAdminDetail(id, input);
      expect(decoded.item.version).toBe(original);
      expect(decoded.item.createdAt).toBe(fields.createdAt);
      expect(decoded.item.updatedAt).toBe(fields.updatedAt);
      expect(decoded.moderationTarget?.actionTag).toBe(tag(original));
      input.body.fill(0);
      expect(decoded.item.version).toBe(original);
      expect(decoded.contentSnapshot.id).toBe(id);
    }
    const closed = content({ status: 'CLOSED', closureReason: 'Reason', closedAt: '2026-09-20T01:02:03.123455Z', closureProvenance: 'ADMIN', closureActorId: ownerId });
    const decoded = decodeComplaintAdminDetail(id, response(closed));
    if (decoded.item.kind === 'NOTICE') throw new Error('Expected content.');
    expect(decoded.item.closedAt).toBe(closed.closedAt);
  });

  it('preserves raw loaded text and escapes without applying mutation normalization or retaining caller bytes', () => {
    const fields = content({
      subject: ' \u2007Loaded\r\nsubject\u00a0 ',
      body: ' \nRaw 😀\tالعربية\u202E literal \\u202E; quote "; slash \\; {} [] \n ',
      appVersion: ' synthetic ', manufacturer: ' Device ',
    });
    const input = response(fields);
    const decoded = decodeComplaintAdminDetail(id, input);
    expect(decoded.item).toEqual(fields);
    if (decoded.contentSnapshot.variant !== 'ordinary') throw new Error('Expected ordinary content.');
    expect(decoded.contentSnapshot.content).toEqual({ type: fields.type, subject: fields.subject, body: fields.body });
    fields.body = 'Later caller value';
    input.body.fill(0);
    expect(decoded.contentSnapshot.content.body).not.toBe(fields.body);
    expect(decoded.contentSnapshot.content.body).toContain('literal \\u202E');
    expect(decoded.contentSnapshot.content.body).toContain('\u202E');
  });

  it('enforces complete detail byte/header/expected-ID bounds and exact content ETag binding', () => {
    const base = response();
    const original = raw();
    const atLimit = bytes(original + ' '.repeat(32_768 - bytes(original).length));
    expect(decodeComplaintAdminDetail(id, { ...base, body: atLimit }).item.id).toBe(id);
    for (const input of [
      { ...base, body: new Uint8Array() },
      { ...base, body: bytes(original + ' '.repeat(32_769 - bytes(original).length)) },
      { ...base, status: 204 },
      { ...base, contract: null },
      { ...base, contract: '1, 1' },
      { ...base, contentType: 'application/problem+json' },
      { ...base, contentType: `application/json${' '.repeat(128)};charset=utf-8` },
      { ...base, contentType: 'application/json\n' },
      { ...base, etag: null },
      { ...base, etag: `W/${tag()}` },
      { ...base, etag: tag('9007199254740992') },
      { ...base, etag: 'x'.repeat(70) },
    ]) rejects(() => decodeComplaintAdminDetail(id, input));
    for (const expectedId of [otherId, id.toUpperCase(), `${id}\n`, `${id}/status`]) {
      rejects(() => decodeComplaintAdminDetail(expectedId, base));
    }
    rejects(() => decodeComplaintAdminDetail(id, response(content({ actionTag: tag('9007199254740992') }))));
    rejects(() => decodeComplaintAdminDetail(noticeId, { ...response(notice()), etag: tag('1', noticeId) }));
  });

  it('rejects ambiguous members, missing fields, nonnumeric Long forms, malformed encoding and non-flat or partial JSON', () => {
    const base = response();
    const original = raw();
    const appended = (field: string) => `${original.slice(0, -1)},${field}}`;
    for (const malformed of [
      appended(`"version":${version}`),
      appended(`"ver\\u0073ion":${version}`),
      appended('"unexpected":"Synthetic private text"'),
      appended('"__proto__":null'),
      `${original}null`, `${original.slice(0, -1)},}`, original.slice(0, -1),
      `[${original}]`, '{"items":[],"nextCursor":null}', '\uFEFF' + original,
      original.replace('"body":"Synthetic body"', '"body":{"nested":"value"}'),
      original.replace('"body":"Synthetic body"', '"body":[]'),
      original.replace('"body":"Synthetic body"', '"body":true'),
      original.replace('"body":"Synthetic body"', '"body":"bad\\x20escape"'),
      original.replace('"body":"Synthetic body"', '"body":"raw\nnewline"'),
      raw(content({ body: '\ud800' })), raw(content({ body: '\udc00' })),
    ]) rejects(() => decodeComplaintAdminDetail(id, { ...base, body: bytes(malformed) }));
    for (const token of [`"${version}"`, `${version}.0`, '9.007199254740993e15', '0', '01', '-1', '9223372036854775808', 'null']) {
      // Matching body/header tags must not mask missing numeric-token/range checks.
      const fields = content({ version: token, actionTag: tag(token.startsWith('"') ? version : token) });
      rejects(() => decodeComplaintAdminDetail(id, response(fields)));
    }
    for (const missing of Object.keys(content())) {
      const fields = content();
      delete fields[missing];
      rejects(() => decodeComplaintAdminDetail(id, { ...base, body: bytes(raw(fields)) }));
    }
    rejects(() => decodeComplaintAdminDetail(id, { ...base, body: new Uint8Array([0xff]) }));
    rejects(() => decodeComplaintAdminDetail(id, { ...base, body: new Uint8Array([0xc3]) }));
  });

  it('rejects inconsistent content, parent, notice and closure shapes instead of creating editable projections', () => {
    for (const fields of [
      content({ kind: 'LEGACY' }), content({ ownership: 'LEGACY_UNCLAIMED' }), content({ status: 'UNKNOWN' }),
      content({ id: noticeId, actionTag: tag(version, noticeId) }), content({ ownerReference: noticeId }),
      content({ type: 'UNSUPPORTED' }), content({ platform: 'DESKTOP' }), content({ body: null }),
      content({ subject: null }), content({ replyToId: otherId }), content({ kind: 'REPLY' }),
      content({ kind: 'REPLY', replyToId: id }), content({ kind: 'REPLY', replyToId: `${otherId}\n` }),
      content({ noticeKey: 'admin.read.notice' }), content({ noticeKey: null }),
      content({ kind: 'REPLY', replyToId: noticeId, type: 'CUSTOM', noticeKey: 'admin.read.notice' }),
      content({ kind: 'REPLY', replyToId: noticeId, subject: null, noticeKey: 'admin.read.notice' }),
      content({ kind: 'REPLY', replyToId: noticeId, type: 'CUSTOM', subject: null, noticeKey: 'admin.read.notice\n' }),
      content({ status: 'CLOSED' }), content({ closureReason: 'Not closed' }),
      content({ status: 'CLOSED', closureReason: 'Reason', closedAt: now, closureProvenance: 'LEGACY', closureActorId: ownerId }),
      notice({ status: 'OPEN' }), notice({ ownership: 'INSTALLATION' }), notice({ ownerReference: ownerId }),
      notice({ body: 'Not a notice field' }), notice({ noticeKey: '' }), notice({ noticeKey: 'a'.repeat(97) }),
    ]) rejects(() => decodeComplaintAdminDetail(fields.id as string, response(fields)));
  });

  it('checks calendar and microsecond order without rounding timestamps or requiring invented closure chronology', () => {
    const fields = content({ createdAt: '2024-02-29T01:02:03.123455Z', updatedAt: '2024-02-29T01:02:03.123456Z' });
    expect(decodeComplaintAdminDetail(id, response(fields)).item.updatedAt).toBe(fields.updatedAt);
    rejects(() => decodeComplaintAdminDetail(id, response({ ...fields, createdAt: fields.updatedAt, updatedAt: fields.createdAt })));
    for (const malformed of ['0000-01-01T00:00:00Z', '2025-02-29T00:00:00Z', '2026-13-01T00:00:00Z', '2026-04-31T00:00:00Z',
      '2026-09-20T24:00:00Z', '2026-09-20T00:00:60Z', '2026-09-20T00:00:00.123456789Z', '2026-09-20T00:00:00+00:00', `${now}\n`]) {
      rejects(() => decodeComplaintAdminDetail(id, response(content({ createdAt: malformed }))));
    }
    // Current backend requires a valid closedAt, not a new relative-time rule.
    const closed = content({ status: 'CLOSED', closureReason: 'Reason', closedAt: '9999-12-31T23:59:59.999999Z', closureProvenance: 'ADMIN', closureActorId: ownerId });
    expect(decodeComplaintAdminDetail(id, response(closed)).item).toHaveProperty('closedAt', closed.closedAt);
    rejects(() => decodeComplaintAdminDetail(id, response({ ...closed, closedAt: '2026-02-30T00:00:00Z' })));
  });
});
