import { prepareComplaintAppVersion, type ComplaintContentType } from './complaint-content-editor';
import { ComplaintReadWireError, readComplaintJsonString, readComplaintLongToken } from './complaint-read-wire';
import { complaintSearchStatuses, complaintSearchTypes, type ComplaintSearchStatus } from './complaint-search-wire';
import { isSessionSelector } from './session-contract';

export const complaintStatsTypes: readonly (ComplaintContentType | null)[] = Object.freeze([...complaintSearchTypes, null]);
export const complaintStatsOwnerships = ['INSTALLATION', 'SYSTEM'] as const;
type VersionBucket = Readonly<{ appVersion: string | null; count: string }>;

/** Exact decimal strings are display/comparison data, not numeric estimates or ADMIN/TEST authority. */
export type ParsedComplaintAdminStats = Readonly<{
  dataScopeId: string;
  total: string;
  byStatus: readonly Readonly<{ status: ComplaintSearchStatus; count: string }>[];
  byType: readonly Readonly<{ type: ComplaintContentType | null; count: string }>[];
  byOwnership: readonly Readonly<{ ownership: typeof complaintStatsOwnerships[number]; count: string }>[];
  appVersions: Readonly<{ buckets: readonly VersionBucket[]; otherCount: string }>;
}>;

/** One closed scope-wide snapshot. Counts never enter JSON.parse/Number; no generic recursive JSON AST. */
export function decodeComplaintAdminStats(
  expectedScope: string,
  response: { status: number; contentType: string | null; contract: string | null; etag: string | null; body: Uint8Array },
): ParsedComplaintAdminStats {
  try {
    if (!isSessionSelector(expectedScope) || response.status !== 200 || response.contract !== '1' || response.etag !== null
      || response.body.byteLength < 1 || response.body.byteLength > 2_097_152
      || !response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType)
      || !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) return invalid();
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body);
    let offset = 0;
    const space = () => { while (offset < raw.length && /[ \t\r\n]/.test(raw[offset])) offset++; };
    const string = () => {
      //64 scalars can require128 escaped UTF-16 units:768 ASCII bytes plus quotes.
      const token = readComplaintJsonString(raw, offset, 770);
      offset = token.end;
      return token.value;
    };
    const nullableString = () => {
      if (raw.startsWith('null', offset)) { offset += 4; return null; }
      return string();
    };
    const count = (allowZero = true) => {
      const token = readComplaintLongToken(raw, offset, allowZero);
      offset = token.end;
      return token.value;
    };
    const object = (fields: readonly string[], field: (name: string) => void) => {
      if (raw[offset++] !== '{') return invalid();
      const seen = new Set<string>();
      space();
      while (raw[offset] !== '}') {
        const name = string();
        if (!fields.includes(name) || seen.has(name)) return invalid();
        seen.add(name); space();
        if (raw[offset++] !== ':') return invalid();
        space(); field(name); space();
        if (raw[offset] !== ',') break;
        offset++; space();
        if (raw[offset] === '}') return invalid();
      }
      if (raw[offset++] !== '}' || seen.size !== fields.length) return invalid();
    };
    const array = <T,>(maximum: number, item: (index: number) => T): T[] => {
      if (raw[offset++] !== '[') return invalid();
      const values: T[] = [];
      space();
      while (raw[offset] !== ']') {
        if (values.length >= maximum) return invalid();
        values.push(item(values.length)); space();
        if (raw[offset] !== ',') break;
        offset++; space();
        if (raw[offset] === ']') return invalid();
      }
      if (raw[offset++] !== ']') return invalid();
      return values;
    };
    const finiteCounts = (key: string, values: readonly (string | null)[]): readonly string[] => {
      const result = array(values.length, (index) => {
        const bucket: { label?: string | null; value?: string } = {};
        object([key, 'count'], (name) => { if (name === key) bucket.label = nullableString(); else bucket.value = count(); });
        const { label, value } = bucket;
        if (label !== values[index] || value === undefined) return invalid();
        return value;
      });
      if (result.length !== values.length) return invalid();
      return result;
    };
    const parsed: { dataScopeId?: string; total?: string; statuses?: readonly string[]; types?: readonly string[];
      ownerships?: readonly string[]; buckets?: VersionBucket[]; otherCount?: string } = {};
    space();
    object(['dataScopeId', 'total', 'byStatus', 'byType', 'byOwnership', 'appVersions'], (name) => {
      switch (name) {
        case 'dataScopeId': parsed.dataScopeId = string(); break;
        case 'total': parsed.total = count(); break;
        case 'byStatus': parsed.statuses = finiteCounts('status', complaintSearchStatuses); break;
        case 'byType': parsed.types = finiteCounts('type', complaintStatsTypes); break;
        case 'byOwnership': parsed.ownerships = finiteCounts('ownership', complaintStatsOwnerships); break;
        case 'appVersions': object(['buckets', 'otherCount'], (member) => {
          if (member === 'otherCount') { parsed.otherCount = count(); return; }
          parsed.buckets = array(50, () => {
            const bucket: { appVersion?: string | null; value?: string } = {};
            object(['appVersion', 'count'], (key) => { if (key === 'appVersion') bucket.appVersion = nullableString(); else bucket.value = count(false); });
            const { appVersion, value } = bucket;
            if (appVersion === undefined || value === undefined || appVersion !== null && prepareComplaintAppVersion(appVersion) !== appVersion) return invalid();
            return Object.freeze({ appVersion, count: value }); // Never normalize, trim, rename or merge an observed key.
          });
        }); break;
      }
    });
    space();
    const { dataScopeId, total, statuses, types, ownerships, buckets, otherCount } = parsed;
    if (offset !== raw.length || dataScopeId !== expectedScope || total === undefined || !statuses || !types || !ownerships
      || !buckets || otherCount === undefined) return invalid();
    const sum = (values: readonly string[]) => values.reduce((result, value) => result + BigInt(value), BigInt(0));
    const expected = BigInt(total);
    if (sum(statuses) !== expected || sum(types) !== expected || sum(ownerships) !== expected || types[6] !== ownerships[1]
      || sum(buckets.map((bucket) => bucket.count)) + BigInt(otherCount) !== expected
      || buckets.length < 50 && otherCount !== '0') return invalid();
    const seenVersions = new Set<string | null>();
    for (let index = 0; index < buckets.length; index++) {
      const current = buckets[index];
      if (seenVersions.has(current.appVersion)) return invalid();
      seenVersions.add(current.appVersion);
      if (index > 0) {
        const previous = buckets[index - 1];
        if (BigInt(previous.count) < BigInt(current.count)
          || previous.count === current.count && compareVersionKeys(previous.appVersion, current.appVersion) >= 0) return invalid();
      }
    }
    return Object.freeze({ dataScopeId, total,
      byStatus: Object.freeze(complaintSearchStatuses.map((status, index) => Object.freeze({ status, count: statuses[index] }))),
      byType: Object.freeze(complaintStatsTypes.map((type, index) => Object.freeze({ type, count: types[index] }))),
      byOwnership: Object.freeze(complaintStatsOwnerships.map((ownership, index) => Object.freeze({ ownership, count: ownerships[index] }))),
      appVersions: Object.freeze({ buckets: Object.freeze(buckets), otherCount }),
    });
  } catch { return invalid(); }
}

/** PostgreSQL COLLATE "C" on well-formed UTF-8, not localeCompare or UTF-16 code-unit order. */
function compareVersionKeys(left: string | null, right: string | null): number {
  if (left === null) return right === null ? 0 : -1;
  if (right === null) return 1;
  const encoder = new TextEncoder(), a = encoder.encode(left), b = encoder.encode(right);
  for (let index = 0; index < Math.min(a.length, b.length); index++) if (a[index] !== b[index]) return a[index] - b[index];
  return a.length - b.length;
}

function invalid(): never { throw new ComplaintReadWireError(); }
