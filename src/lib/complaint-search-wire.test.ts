import { describe, expect, it } from 'vitest';

import { complaintId, complaintScope } from '@/test/complaint-mutation-fixture';
import { searchContent, searchCursor, searchNotice, searchNoticeId, searchPage, searchVersion } from '@/test/complaint-search-fixture';
import { ComplaintReadWireError, decodeComplaintAdminPage } from './complaint-read-wire';
import { ComplaintSearchWireError, isComplaintSearchCursor, parseComplaintAdminSearchBody, prepareComplaintAdminSearch } from './complaint-search-wire';

const bytes = (value: string) => new TextEncoder().encode(value);
const parse = (value: string) => parseComplaintAdminSearchBody(bytes(value));
function page(raw = searchPage(), limit = 50) {
  return decodeComplaintAdminPage(limit, { status: 200, contentType: 'application/json;charset=UTF-8', contract: '1', etag: null, body: bytes(raw) });
}

describe('closed backend-bound complaint search request', () => {
  it('matches the existing defaults and all closed fields without supplying authority', () => {
    const defaults = prepareComplaintAdminSearch({ dataScopeId: complaintScope });
    expect(defaults).toEqual({ dataScopeId: complaintScope, text: '', status: null, type: null, ownership: null,
      updatedFrom: null, updatedBefore: null, sort: 'UPDATED_DESC', limit: 50, cursor: null });
    expect(parse(`{"dataScopeId":"${complaintScope}"}`)).toEqual(defaults);
    const selected = prepareComplaintAdminSearch({ dataScopeId: complaintScope, text: ' \u2007query\r\ntext\u00a0 ', status: 'OPEN', type: 'CUSTOM',
      ownership: 'INSTALLATION', updatedFrom: '0001-01-01T00:00:00.1Z', updatedBefore: '9999-12-31T23:59:59.999999Z', limit: 1, cursor: searchCursor });
    expect(parse(JSON.stringify(selected))).toEqual(selected);
    expect(selected.text).toBe('query\ntext');
    expect(Object.isFrozen(selected)).toBe(true);
    expect(selected).not.toHaveProperty('authenticated');
  });

  it('reuses Kotlin-compatible normalization, including empty text and validation before trim', () => {
    expect(prepareComplaintAdminSearch({ dataScopeId: complaintScope, text: ' \t\n\u3000' }).text).toBe('');
    expect(prepareComplaintAdminSearch({ dataScopeId: complaintScope, text: '\uFEFF' }).text).toBe('\uFEFF');
    expect(prepareComplaintAdminSearch({ dataScopeId: complaintScope, text: '😀'.repeat(100) }).text).toHaveLength(200);
    for (const text of ['😀'.repeat(101), 'x'.repeat(101), '\u0000 query', 'query\u007f', '\u0085', 'query\r', '\ud800', '\udc00']) {
      expect(() => prepareComplaintAdminSearch({ dataScopeId: complaintScope, text })).toThrow(ComplaintSearchWireError);
    }
  });

  it('rejects ambiguous/nonclosed JSON and noncanonical small integer tokens at the streamed request boundary', () => {
    const original = `{"dataScopeId":"${complaintScope}"}`;
    for (const raw of [original + 'null', '\uFEFF' + original, original.slice(0, -1) + ',}',
      original.slice(0, -1) + ',"dataScopeId":"' + complaintScope + '"}',
      original.slice(0, -1) + ',"dataScope\\u0049d":"' + complaintScope + '"}',
      original.slice(0, -1) + ',"actor":"caller"}', original.replace(`"${complaintScope}"`, 'null'),
      original.slice(0, -1) + ',"text":null}', original.slice(0, -1) + ',"text":{"nested":"secret"}}',
      original.slice(0, -1) + ',"status":["OPEN"]}', original.slice(0, -1) + ',"text":"\\ud800"}',
      ...['"1"', '0', '01', '51', '-1', '1.0', '1e1', 'true', 'null'].map((value) => original.slice(0, -1) + `,"limit":${value}}`)]) {
      expect(() => parse(raw), raw).toThrow(ComplaintSearchWireError);
    }
    expect(parse(original + ' '.repeat(32_768 - original.length)).limit).toBe(50);
    expect(() => parse(original + ' '.repeat(32_769 - original.length))).toThrow(ComplaintSearchWireError);
    expect(() => parseComplaintAdminSearchBody(new Uint8Array([0xff]))).toThrow(ComplaintSearchWireError);
  });

  it('refuses unsupported scope/enums/sort and invalid UTC calendar/range values', () => {
    for (const fields of [{ dataScopeId: 'ABCDEFAB-1111-4111-8111-111111111111' }, { dataScopeId: searchNoticeId }, { dataScopeId: '00000000-0000-0000-0000-000000000000' },
      { status: 'UNKNOWN' }, { ownership: 'LEGACY_UNCLAIMED' }, { type: 'FUTURE' }, { sort: 'CREATED_ASC' },
      ...['0000-01-01T00:00:00Z', '2025-02-29T00:00:00Z', '2026-04-31T00:00:00Z', '2026-09-20T24:00:00Z',
        '2026-09-20T00:00:60Z', '2026-09-20T00:00:00.1234567Z', '2026-09-20T00:00:00+00:00'].map((updatedFrom) => ({ updatedFrom })),
      { updatedFrom: '2026-09-20T01:02:03.1Z', updatedBefore: '2026-09-20T01:02:03.100000Z' }]) {
      expect(() => parse(JSON.stringify({ dataScopeId: complaintScope, ...fields }))).toThrow(ComplaintSearchWireError);
    }
    expect(parse(JSON.stringify({ dataScopeId: complaintScope, updatedFrom: '2024-02-29T01:02:03.000001Z', updatedBefore: '2024-02-29T01:02:03.000002Z' })).updatedBefore).toContain('000002');
  });

  it('checks only bounded canonical cursor syntax, never inventing verification of its MAC/binding', () => {
    expect(isComplaintSearchCursor(searchCursor)).toBe(true);
    expect(isComplaintSearchCursor(`v1.${'A'.repeat(683)}.${'A'.repeat(43)}`)).toBe(true); //512-byte payload.
    for (const cursor of ['', searchCursor + '\n', `v1.AB.${'A'.repeat(43)}`, `v1.AA.${'B'.repeat(43)}`,
      `v1.A.${'A'.repeat(43)}`, `v1.${'A'.repeat(684)}.${'A'.repeat(43)}`, searchCursor + '=', 'v2.' + searchCursor.slice(3), 'x'.repeat(2049)]) {
      expect(isComplaintSearchCursor(cursor)).toBe(false);
      expect(() => prepareComplaintAdminSearch({ dataScopeId: complaintScope, cursor })).toThrow(ComplaintSearchWireError);
    }
  });
});

describe('lossless bounded Admin search page', () => {
  it('reuses detail item rules without manufacturing a page ETag, editor base or NOTICE tag', () => {
    const decoded = page(searchPage([searchNotice(), searchContent({ subject: '<img src=x> العربية\u202e raw', version: searchVersion })], searchCursor));
    expect(decoded.items.map((item) => item.id)).toEqual([searchNoticeId, complaintId]);
    expect(decoded.items[0].version).toBe('9223372036854775807');
    expect(decoded.items[0]).not.toHaveProperty('actionTag');
    expect(decoded.items[1].version).toBe(searchVersion);
    expect(decoded.items[1]).toHaveProperty('subject', '<img src=x> العربية\u202e raw');
    expect(decoded.items[1]).toHaveProperty('actionTag', `"complaint-${complaintId}-v${searchVersion}"`);
    for (const value of [decoded, decoded.items, ...decoded.items]) expect(Object.isFrozen(value)).toBe(true);
    expect(decoded).not.toHaveProperty('contentSnapshot');
    expect(decoded).not.toHaveProperty('dataScopeId');
  });

  it('accepts genuinely empty and at-most50 rows but enforces the captured request limit', () => {
    expect(page(searchPage([]))).toEqual({ items: [], nextCursor: null });
    const rows = Array.from({ length: 50 }, (_, index) => searchContent({ id: `${(50 - index).toString(16).padStart(8, '0')}-1111-4111-8111-111111111111` }));
    expect(page(searchPage(rows)).items).toHaveLength(50);
    expect(() => page(searchPage([...rows, searchContent()]))).toThrow(ComplaintReadWireError);
    expect(() => page(searchPage(rows), 49)).toThrow(ComplaintReadWireError);
    expect(() => page(searchPage([], searchCursor))).toThrow(ComplaintReadWireError);
  });

  it('rejects duplicate/out-of-order items and does not round microsecond order or unsigned UUID order', () => {
    expect(() => page(searchPage([searchContent(), searchContent()]))).toThrow(ComplaintReadWireError);
    expect(() => page(searchPage([searchContent(), searchNotice()]))).toThrow(ComplaintReadWireError);
    const newer = searchContent({ updatedAt: '2026-09-20T01:02:03.000002Z' });
    const older = searchNotice({ updatedAt: '2026-09-20T01:02:03.000001Z' });
    expect(page(searchPage([newer, older])).items).toHaveLength(2);
    expect(() => page(searchPage([older, newer]))).toThrow(ComplaintReadWireError);
    expect(() => page(searchPage([searchContent({ version: '9007199254740992', actionTag: `"complaint-${complaintId}-v9007199254740993"` })]))).toThrow(ComplaintReadWireError);
    for (const version of ['"9007199254740993"', '9e15', '0', '9223372036854775808']) expect(() => page(searchPage([searchContent({ version })]))).toThrow(ComplaintReadWireError);
  });

  it('requires a complete closed envelope and scalar items even for valid-looking prefixes', () => {
    const original = searchPage();
    for (const raw of [original.slice(0, -1), original + 'null', '\uFEFF' + original, '{"items":[]}', '{"nextCursor":null}',
      '{"items":[],"items":[],"nextCursor":null}', '{"items":[],"it\\u0065ms":[],"nextCursor":null}',
      '{"items":[],"nextCursor":null,"other":"private"}', '{"items":[[]],"nextCursor":null}', '{"items":[],"nextCursor":"invalid"}',
      original.replace('"version":9007199254740993', '"version":9007199254740993,"version":9007199254740993'),
      original.replace('"body":"Synthetic search body"', '"body":{"nested":"private"}'), original.replace('"nextCursor":null', '"nextCursor":[]')]) {
      expect(() => page(raw)).toThrow(ComplaintReadWireError);
    }
  });

  it('enforces exact whole-envelope and post-escaping item byte ceilings, including multibyte data', () => {
    const original = searchPage();
    expect(page(original + ' '.repeat(2_097_152 - bytes(original).length)).items[0].version).toBe(searchVersion);
    expect(() => page(original + ' '.repeat(2_097_153 - bytes(original).length))).toThrow(ComplaintReadWireError);
    const scalar = searchContent({ body: '😀' });
    const atLimit = scalar.slice(0, -1) + ' '.repeat(32_768 - bytes(scalar).length) + '}';
    expect(page(searchPage([atLimit])).items[0].id).toBe(complaintId);
    expect(() => page(searchPage([atLimit.slice(0, -1) + ' }']))).toThrow(ComplaintReadWireError);
  });

  it('rejects header/encoding mismatches without exposing raw parse diagnostics', () => {
    const base = { status: 200, contentType: 'application/json', contract: '1', etag: null, body: bytes(searchPage()) };
    for (const response of [{ ...base, status: 204 }, { ...base, contract: '1, 1' }, { ...base, etag: 'invented-page-tag' },
      { ...base, contentType: 'text/html' }, { ...base, body: new Uint8Array([0xff]) }, { ...base, body: new Uint8Array() }]) {
      try { decodeComplaintAdminPage(50, response); throw new Error('Expected rejection.'); }
      catch (error) { expect(error).toBeInstanceOf(ComplaintReadWireError); expect(error).not.toHaveProperty('cause'); expect(String(error)).not.toContain('private'); }
    }
  });
});
