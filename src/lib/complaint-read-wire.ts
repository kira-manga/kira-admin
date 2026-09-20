import type { ComplaintContentSnapshot, ComplaintContentType } from './complaint-content-editor';
import type { ComplaintModerationTarget, ComplaintStatusTarget } from './complaint-moderation-wire';

type ReadStatus = ComplaintStatusTarget | 'CLOSED' | 'PINNED';
type CommonItem = Readonly<{ id: string; version: string; createdAt: string; updatedAt: string }>;

export type ParsedComplaintAdminItem =
  | CommonItem & Readonly<{
    kind: 'NOTICE'; status: 'PINNED'; ownership: 'SYSTEM'; ownerReference: null; noticeKey: string;
  }>
  | CommonItem & Readonly<{
    kind: 'REPORT' | 'REPLY'; status: ReadStatus; ownership: 'INSTALLATION'; ownerReference: string;
    type: ComplaintContentType; subject: string | null; body: string; actionTag: string;
    appVersion: string | null; platform: 'ANDROID' | 'IOS'; osVersion: string; manufacturer: string; deviceModel: string;
    closureReason: string | null; replyToId: string | null; closedAt: string | null;
    closureProvenance: 'ADMIN' | null; closureActorId: string | null; noticeKey?: string;
  }>;

/** Parsed local data only: no ADMIN identity, scope binding, freshness or mutation authority. */
export type ParsedComplaintAdminDetail = Readonly<{
  item: ParsedComplaintAdminItem;
  contentSnapshot: ComplaintContentSnapshot;
  moderationTarget: ComplaintModerationTarget | null;
}>;

export class ComplaintReadWireError extends Error {
  readonly reason = 'INVALID_RESPONSE';
  constructor() {
    super('Complaint read: INVALID_RESPONSE.');
    this.name = 'ComplaintReadWireError';
  }
}

const commonFields = ['id', 'kind', 'status', 'createdAt', 'updatedAt', 'version', 'ownership', 'ownerReference'];
const contentFields = [
  ...commonFields, 'type', 'subject', 'body', 'actionTag', 'appVersion', 'platform', 'osVersion', 'manufacturer',
  'deviceModel', 'closureReason', 'replyToId', 'closedAt', 'closureProvenance', 'closureActorId',
];
const knownFields = new Set([...contentFields, 'noticeKey']);
const types: readonly ComplaintContentType[] = ['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM'];
const statuses: readonly ReadStatus[] = ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'PLANNED', 'PINNED', 'NOT_PLANNED'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const maximumLong = '9223372036854775807';

/**
 * One complete detail only, never a search page. The caller owns bounded body acquisition
 * and original header metadata. ID/tag consistency is not origin authentication: this wire
 * body has no dataScopeId, credential, freshness proof or step-up consumption information.
 * Strings remain verbatim; existing preparation helpers own editing/text normalization.
 */
export function decodeComplaintAdminDetail(
  expectedId: string,
  response: { status: number; contentType: string | null; contract: string | null; etag: string | null; body: Uint8Array },
): ParsedComplaintAdminDetail {
  try {
    if (!isUuid(expectedId) || response.status !== 200 || response.contract !== '1' ||
        response.body.byteLength < 1 || response.body.byteLength > 32_768 ||
        !response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType) ||
        !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType) ||
        response.etag !== null && (response.etag.length > 69 || /[\r\n]/.test(response.etag))) invalid();
    // Preserve a leading BOM so the closed JSON reader rejects it instead of stripping it.
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body);
    const fields = readFlatDetail(raw);
    const id = stringField(fields, 'id');
    if (id !== expectedId) invalid();
    const kind = stringField(fields, 'kind');
    const version = stringField(fields, 'version'); // Original numeric token, never Number/JSON.parse.
    const createdAt = stringField(fields, 'createdAt');
    const updatedAt = stringField(fields, 'updatedAt');
    if (timeKey(createdAt) > timeKey(updatedAt)) invalid();
    const common = { id, version, createdAt, updatedAt };

    if (kind === 'NOTICE') {
      requireFields(fields, [...commonFields, 'noticeKey']);
      if (stringField(fields, 'ownership') !== 'SYSTEM' || stringField(fields, 'status') !== 'PINNED' ||
          nullableField(fields, 'ownerReference') !== null || response.etag !== null) invalid();
      const noticeKey = stringField(fields, 'noticeKey');
      requireNoticeKey(noticeKey);
      return Object.freeze({
        item: Object.freeze({ ...common, kind: 'NOTICE' as const, status: 'PINNED' as const, ownership: 'SYSTEM' as const, ownerReference: null, noticeKey }),
        contentSnapshot: Object.freeze({ variant: 'notice' as const, kind: 'NOTICE' as const, id }),
        moderationTarget: null, // NOTICE has no actionTag: never manufacture one from its version.
      });
    }

    if (kind !== 'REPORT' && kind !== 'REPLY') return invalid();
    requireFields(fields, fields.has('noticeKey') ? [...contentFields, 'noticeKey'] : contentFields);
    if (!isV4(id) || stringField(fields, 'ownership') !== 'INSTALLATION') invalid();
    const ownerReference = stringField(fields, 'ownerReference');
    if (!isV4(ownerReference)) invalid();
    const type = stringField(fields, 'type') as ComplaintContentType;
    const status = stringField(fields, 'status') as ReadStatus;
    if (!types.includes(type) || !statuses.includes(status)) invalid();
    const actionTag = stringField(fields, 'actionTag');
    if (actionTag !== `"complaint-${id}-v${version}"` || response.etag !== actionTag) invalid();
    const subject = nullableField(fields, 'subject');
    const body = stringField(fields, 'body');
    const replyToId = nullableField(fields, 'replyToId');
    if ((kind === 'REPLY') !== (replyToId !== null) || replyToId === id || replyToId !== null && !isUuid(replyToId)) invalid();
    const noticeKey = fields.has('noticeKey') ? stringField(fields, 'noticeKey') : undefined;
    if (noticeKey !== undefined) {
      requireNoticeKey(noticeKey);
      if (kind !== 'REPLY' || type !== 'CUSTOM' || subject !== null) invalid();
    } else if (subject === null) invalid();

    const closureReason = nullableField(fields, 'closureReason');
    const closedAt = nullableField(fields, 'closedAt');
    const closureProvenance = nullableField(fields, 'closureProvenance');
    const closureActorId = nullableField(fields, 'closureActorId');
    if (status === 'CLOSED') {
      if (closureReason === null || closedAt === null || closureProvenance !== 'ADMIN' || closureActorId === null || !isUuid(closureActorId)) return invalid();
      timeKey(closedAt);
    } else if (closureReason !== null || closedAt !== null || closureProvenance !== null || closureActorId !== null) invalid();
    const platform = stringField(fields, 'platform');
    if (platform !== 'ANDROID' && platform !== 'IOS') return invalid();
    const item: ParsedComplaintAdminItem = Object.freeze({
      ...common, kind, status, ownership: 'INSTALLATION', ownerReference, type, subject, body, actionTag,
      appVersion: nullableField(fields, 'appVersion'), platform, osVersion: stringField(fields, 'osVersion'),
      manufacturer: stringField(fields, 'manufacturer'), deviceModel: stringField(fields, 'deviceModel'),
      closureReason, replyToId, closedAt, closureProvenance: status === 'CLOSED' ? 'ADMIN' : null, closureActorId,
      ...(noticeKey === undefined ? {} : { noticeKey }),
    });
    const contentSnapshot: ComplaintContentSnapshot = noticeKey === undefined
      ? Object.freeze({ variant: 'ordinary' as const, kind, id, actionTag, content: Object.freeze({ type, subject: stringField(fields, 'subject'), body }) })
      : Object.freeze({ variant: 'notice-reply' as const, kind: 'REPLY' as const, id, actionTag, content: Object.freeze({ body }) });
    return Object.freeze({
      item, contentSnapshot, moderationTarget: Object.freeze({ id, kind, ownership: 'INSTALLATION' as const, actionTag }),
    });
  } catch {
    // Never expose parser diagnostics, original bytes, identifiers or any nested cause.
    return invalid();
  }
}

/** Only the closed detail object's scalar fields. No recursion, arrays or generic JSON AST. */
function readFlatDetail(raw: string): Map<string, string | null> {
  let offset = 0;
  const fields = new Map<string, string | null>();
  const whitespace = () => {
    while (offset < raw.length && (raw[offset] === ' ' || raw[offset] === '\t' || raw[offset] === '\r' || raw[offset] === '\n')) offset++;
  };
  const string = (): string => {
    const start = offset;
    if (raw[offset++] !== '"') return invalid();
    while (offset < raw.length) {
      const code = raw.charCodeAt(offset++);
      if (code === 0x22) {
        const value: unknown = JSON.parse(raw.slice(start, offset)); // Strings only: version never enters JSON.parse.
        if (typeof value !== 'string') return invalid();
        requireWellFormed(value);
        return value;
      }
      if (code === 0x5c) offset++; // Skip the escaped character; JSON.parse checks the complete escape.
      else if (code <= 0x1f) return invalid();
    }
    return invalid();
  };
  whitespace();
  if (raw[offset++] !== '{') return invalid();
  whitespace();
  if (raw[offset] !== '}') {
    while (true) {
      const name = string();
      if (!knownFields.has(name) || fields.has(name)) return invalid();
      whitespace();
      if (raw[offset++] !== ':') return invalid();
      whitespace();
      let value: string | null;
      if (name === 'version') {
        const start = offset;
        while (offset < raw.length && raw[offset] >= '0' && raw[offset] <= '9') offset++;
        value = raw.slice(start, offset);
        if (!value || value[0] === '0' || value.length > maximumLong.length ||
            value.length === maximumLong.length && value > maximumLong) return invalid();
      } else if (raw.startsWith('null', offset)) {
        value = null;
        offset += 4;
      } else {
        value = string();
      }
      fields.set(name, value);
      whitespace();
      if (raw[offset] === '}') break;
      if (raw[offset++] !== ',') return invalid();
      whitespace();
    }
  }
  if (raw[offset++] !== '}') return invalid();
  whitespace();
  if (offset !== raw.length) return invalid();
  return fields;
}

function requireFields(fields: Map<string, string | null>, names: readonly string[]): void {
  if (fields.size !== names.length || names.some((name) => !fields.has(name))) invalid();
}

function stringField(fields: Map<string, string | null>, name: string): string {
  const value = fields.get(name);
  return typeof value === 'string' ? value : invalid();
}

function nullableField(fields: Map<string, string | null>, name: string): string | null {
  const value = fields.get(name);
  return value === null || typeof value === 'string' ? value : invalid();
}

function isUuid(value: string): boolean {
  return value.length === 36 && uuid.test(value);
}

function isV4(value: string): boolean {
  return isUuid(value) && value[14] === '4' && '89ab'.includes(value[19]);
}

function requireNoticeKey(value: string): void {
  if (value.length < 1 || value.length > 96 || /[^a-z0-9._-]/.test(value)) invalid();
}

function requireWellFormed(value: string): void {
  for (let index = 0; index < value.length; index++) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(++index);
      if (!(next >= 0xdc00 && next <= 0xdfff)) invalid();
    } else if (unit >= 0xdc00 && unit <= 0xdfff) invalid();
  }
}

/** Backend Instant.toString UTC form at PostgreSQL microsecond precision; keep the original string. */
function timeKey(value: string): string {
  const match = /^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{3}(?:[0-9]{3})?))?Z$/.exec(value);
  if (!match || match[0] !== value) return invalid();
  // Only small calendar components use Number; neither the Long nor timestamp becomes a JS number/Date.
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > days[month - 1] ||
      Number(match[4]) > 23 || Number(match[5]) > 59 || Number(match[6]) > 59) return invalid();
  return match.slice(1, 7).join('') + (match[7] ?? '').padEnd(6, '0');
}

function invalid(): never {
  throw new ComplaintReadWireError();
}
