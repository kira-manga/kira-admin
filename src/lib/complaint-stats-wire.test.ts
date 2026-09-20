import { describe, expect, it, vi } from 'vitest';

import { complaintScope } from '@/test/complaint-mutation-fixture';
import { statsDocument, statsFixture, statsTotal, type StatsFixture } from '@/test/complaint-stats-fixture';
import { ComplaintReadWireError } from './complaint-read-wire';
import { decodeComplaintAdminStats } from './complaint-stats-wire';

const bytes = (value: string) => new TextEncoder().encode(value);
const metadata = { status: 200, contentType: 'application/json;charset=UTF-8', contract: '1', etag: null };
const decode = (value = statsFixture()) => decodeComplaintAdminStats(complaintScope, { ...metadata, body: bytes(statsDocument(value)) });
function refuses(raw: string) {
  expect(() => decodeComplaintAdminStats(complaintScope, { ...metadata, body: bytes(raw) })).toThrow(ComplaintReadWireError);
}

describe('closed lossless scope-wide complaint statistics wire contract', () => {
  it('retains exact Long digits, every fixed zero category and frozen detached records without parsing counts as numbers', () => {
    for (const total of ['0', '1', statsTotal, '9223372036854775807']) {
      const fixture = statsFixture(total), body = bytes(statsDocument(fixture));
      const parse = vi.spyOn(JSON, 'parse');
      let parsed: ReturnType<typeof decodeComplaintAdminStats>;
      try {
        parsed = decodeComplaintAdminStats(complaintScope, { ...metadata, body });
        for (const [input] of parse.mock.calls) expect(String(input).startsWith('"')).toBe(true);
      } finally { parse.mockRestore(); }
      expect(parsed).toEqual(fixture);
      expect(parsed.total).toBe(total);
      body.fill(0); fixture.byStatus[0].count = '11';
      expect(parsed.byStatus[0].count).toBe(total);
      for (const value of [parsed, parsed.byStatus, ...parsed.byStatus, parsed.byType, ...parsed.byType,
        parsed.byOwnership, ...parsed.byOwnership, parsed.appVersions, parsed.appVersions.buckets, ...parsed.appVersions.buckets]) expect(Object.isFrozen(value)).toBe(true);
      expect(parsed).not.toHaveProperty('authenticated'); expect(parsed).not.toHaveProperty('actionTag'); expect(parsed).not.toHaveProperty('nextCursor');
    }
  });

  it('keeps null, empty and literal version keys distinct and checks equal-count ties using UTF8 rather than UTF16 or locale order', () => {
    const fixture = statsFixture('6');
    const keys = [null, '', 'null', 'unreported', '\uE000', '\u{10000}'];
    fixture.appVersions.buckets = keys.map((appVersion) => ({ appVersion, count: '1' }));
    expect(decode(fixture).appVersions.buckets.map((row) => row.appVersion)).toEqual(keys);
    for (const order of [[...keys.slice(1), null], [null, '', 'null', 'unreported', '\u{10000}', '\uE000']]) {
      fixture.appVersions.buckets = order.map((appVersion) => ({ appVersion, count: '1' }));
      refuses(statsDocument(fixture));
    }
    fixture.appVersions.buckets = [{ appVersion: 'higher', count: '5' }, { appVersion: null, count: '1' }];
    expect(decode(fixture).appVersions.buckets[1].appVersion).toBeNull(); // Null is not always first or forced beyond50.
  });

  it('accepts64 Unicode scalars and valid escaped top50 bodies beyond32KiB without normalizing observed keys', () => {
    const fixture = statsFixture('50');
    fixture.appVersions.buckets = Array.from({ length: 50 }, (_, index) => ({ appVersion: String(index).padStart(2, '0') + '😀'.repeat(62), count: '1' }));
    const escaped = statsDocument(fixture).replace(/[\u0080-\uffff]/g, (unit) => `\\u${unit.charCodeAt(0).toString(16).padStart(4, '0')}`);
    expect(bytes(escaped).byteLength).toBeGreaterThan(32_768);
    expect(decodeComplaintAdminStats(complaintScope, { ...metadata, body: bytes(escaped) })).toEqual(fixture);
    const single = statsFixture('1');
    for (const key of ['😀'.repeat(64), 'العربية\u202Eversion', 'a\tb\nc', '\uFEFFliteral']) {
      single.appVersions.buckets[0].appVersion = key;
      expect(decode(single).appVersions.buckets[0].appVersion).toBe(key);
    }
    for (const key of ['😀'.repeat(65), 'x'.repeat(65), ' outer ', 'a\r\nb', 'x\u0000', '\u007f', '\u0085', '\ud800', '\udc00']) {
      single.appVersions.buckets[0].appVersion = key;
      refuses(statsDocument(single));
    }
  });

  it('refuses quoted, signed, fractional, exponential, noncanonical or out-of-Long-range tokens at every count position', () => {
    const positions: Array<(fixture: StatsFixture, token: string) => void> = [
      (fixture, token) => { fixture.total = token; },
      (fixture, token) => { fixture.byStatus[0].count = token; },
      (fixture, token) => { fixture.byType[0].count = token; },
      (fixture, token) => { fixture.byOwnership[0].count = token; },
      (fixture, token) => { fixture.appVersions.buckets[0].count = token; },
      (fixture, token) => { fixture.appVersions.otherCount = token; },
    ];
    for (const token of ['"1"', '-1', '-0', '+1', '01', '1.0', '1e0', 'null', 'true', '9223372036854775808', '999999999999999999999']) {
      for (const set of positions) { const fixture = statsFixture('1'); set(fixture, token); refuses(statsDocument(fixture)); }
    }
    const zeroBucket = statsFixture('0'); zeroBucket.appVersions.buckets = [{ appVersion: null, count: '0' }];
    refuses(statsDocument(zeroBucket));
  });

  it('uses overflow-safe BigInt sums and enforces the NOTICE null-type to SYSTEM equality', () => {
    const rounded = statsFixture(); rounded.byStatus[0].count = '9007199254740992';
    refuses(statsDocument(rounded)); // Number would round both sides to the same value.
    for (const key of ['byStatus', 'byType', 'byOwnership'] as const) {
      const fixture = statsFixture('9223372036854775807'); fixture[key][1].count = '1';
      refuses(statsDocument(fixture));
    }
    const fixture = statsFixture('4');
    fixture.byOwnership = [{ ownership: 'INSTALLATION', count: '3' }, { ownership: 'SYSTEM', count: '1' }];
    refuses(statsDocument(fixture));
    fixture.byType[0].count = '3'; fixture.byType[6].count = '1';
    expect(decode(fixture).byType[6]).toEqual({ type: null, count: '1' });
    const versionOverflow = statsFixture('9223372036854775807');
    versionOverflow.appVersions.buckets.push({ appVersion: null, count: '1' });
    refuses(statsDocument(versionOverflow));
  });

  it('requires all finite categories exactly once in fixed order and closed duplicate-aware objects at every level', () => {
    const original = statsDocument();
    for (const raw of [
      original.replace('"byStatus":', '"unexpected":'), original.replace('"total":', '"to\\u0074al":0,"total":'),
      original.replace('"OPEN"', '"UNKNOWN"'), original.replace('"INSTALLATION"', '"LEGACY_UNCLAIMED"'),
      original.replace('"type":null', '"type":"null"'), original.replace('"status":"OPEN"', '"status":"OPEN","st\\u0061tus":"OPEN"'),
      original.replace('"otherCount":0', '"otherCount":0,"cursor":null'),
      original.replace('"appVersion":"Synthetic version"', '"appVersion":"Synthetic version","ownerReference":"private"'),
      original.replace('"appVersion":"Synthetic version"', '"appVersion":"Synthetic version","co\\u0075nt":1'),
      original.replace('"byType":[', '"byType":[{"type":"NEW_TYPE","count":0},'),
    ]) refuses(raw);
    for (const key of ['byStatus', 'byType', 'byOwnership'] as const) {
      const missing = statsFixture(); missing[key].pop(); refuses(statsDocument(missing));
      const reversed = statsFixture(); reversed[key].reverse(); refuses(statsDocument(reversed));
    }
    for (const member of ['dataScopeId', 'total', 'byStatus', 'byType', 'byOwnership', 'appVersions']) {
      // A renamed required field cannot silently become a default.
      refuses(original.replace(`"${member}":`, '"missing-field":'));
    }
  });

  it('checks positive distinct top50 counts, order and remainder rows without forcing an extra null group', () => {
    const fixture = statsFixture('101');
    fixture.appVersions.buckets = Array.from({ length: 50 }, (_, index) => ({ appVersion: `version-${String(index).padStart(2, '0')}`, count: '2' }));
    fixture.appVersions.otherCount = '1';
    expect(decode(fixture).appVersions).toEqual(fixture.appVersions); // An omitted unreported key may be part of the remainder.
    fixture.total = fixture.byStatus[0].count = fixture.byType[0].count = fixture.byOwnership[0].count = '100';
    fixture.appVersions.otherCount = '0'; expect(decode(fixture).appVersions.buckets).toHaveLength(50);
    fixture.appVersions.buckets.push({ appVersion: null, count: '1' }); refuses(statsDocument(fixture));
    const short = statsFixture('3'); short.appVersions = { buckets: [{ appVersion: 'v', count: '2' }], otherCount: '1' }; refuses(statsDocument(short));
    const duplicate = statsFixture('3'); duplicate.appVersions.buckets = [{ appVersion: 'v', count: '2' }, { appVersion: 'v', count: '1' }]; refuses(statsDocument(duplicate));
    duplicate.appVersions.buckets = [{ appVersion: 'a', count: '1' }, { appVersion: 'b', count: '2' }]; refuses(statsDocument(duplicate));
    duplicate.appVersions.buckets = [{ appVersion: null, count: '2' }, { appVersion: null, count: '1' }]; refuses(statsDocument(duplicate));
  });

  it('requires exact scope and success metadata, complete UTF8 JSON and the actual2MiB bound with sanitized failure', () => {
    const raw = statsDocument(), body = bytes(raw);
    const maximum = bytes(raw + ' '.repeat(2_097_152 - body.byteLength));
    expect(decodeComplaintAdminStats(complaintScope, { ...metadata, body: maximum }).total).toBe(statsTotal);
    for (const response of [
      { ...metadata, body: new Uint8Array() }, { ...metadata, body: new Uint8Array(2_097_153) },
      { ...metadata, body, status: 204 }, { ...metadata, body, contract: null }, { ...metadata, body, contract: '1, 1' },
      { ...metadata, body, etag: '"not-a-stats-tag"' }, { ...metadata, body, contentType: 'application/problem+json' },
      { ...metadata, body, contentType: 'application/json;charset=UTF-16' }, { ...metadata, body, contentType: 'application/json\n' },
      { ...metadata, body: new Uint8Array([0xff]) }, { ...metadata, body: new Uint8Array([0xc3]) },
    ]) expect(() => decodeComplaintAdminStats(complaintScope, response)).toThrow(ComplaintReadWireError);
    for (const malformed of [raw + 'null', raw.slice(0, -1), raw.slice(0, -1) + ',}', `[${raw}]`, '\uFEFF' + raw,
      raw.replace('"Synthetic version"', '[]'), raw.replace('"Synthetic version"', '"bad\\x20escape"'), raw.replace('"Synthetic version"', '"raw\nnewline"')]) refuses(malformed);
    for (const scope of ['00000000-0000-0000-0000-000000000000', 'ABCDEFAB-1234-4234-8234-123456789ABC', `${complaintScope}&text=private`, '33333333-3333-4333-8333-333333333333']) {
      expect(() => decodeComplaintAdminStats(scope, { ...metadata, body })).toThrow(ComplaintReadWireError);
    }
    try { decodeComplaintAdminStats(complaintScope, { ...metadata, body: bytes('{"private":"never echo"}') }); }
    catch (error) { expect(String(error)).toBe('ComplaintReadWireError: Complaint read: INVALID_RESPONSE.'); expect(error).not.toHaveProperty('cause'); }
  });
});
