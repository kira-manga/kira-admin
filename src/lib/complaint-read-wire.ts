import type { ComplaintContentSnapshot, ComplaintContentType } from './complaint-content-editor';
import type { ComplaintModerationTarget, ComplaintStatusTarget } from './complaint-moderation-wire';
import { isComplaintSearchCursor } from './complaint-search-wire';

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

export type ParsedComplaintAdminPage = Readonly<{ items: readonly ParsedComplaintAdminItem[]; nextCursor: string | null }>;

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
    const item = readAdminItem(readFlatDetail(raw), { id: expectedId, etag: response.etag });
    if (item.kind === 'NOTICE') return Object.freeze({
      item, contentSnapshot: Object.freeze({ variant: 'notice' as const, kind: 'NOTICE' as const, id: item.id }),
      moderationTarget: null, // NOTICE has no actionTag: never manufacture one from its version.
    });
    const { id, kind, type, subject, body, actionTag } = item;
    const contentSnapshot: ComplaintContentSnapshot = item.noticeKey === undefined
      ? Object.freeze({ variant: 'ordinary' as const, kind, id, actionTag, content: Object.freeze({ type, subject: subject!, body }) })
      : Object.freeze({ variant: 'notice-reply' as const, kind: 'REPLY' as const, id, actionTag, content: Object.freeze({ body }) });
    return Object.freeze({ item, contentSnapshot, moderationTarget: Object.freeze({ id, kind, ownership: 'INSTALLATION' as const, actionTag }) });
  } catch {
    // Never expose parser diagnostics, original bytes, identifiers or any nested cause.
    return invalid();
  }
}

/** Backend's exact search envelope. Parsed rows/cursor have no independent scope/freshness authority. */
export function decodeComplaintAdminPage(
  limit: number,
  response: { status: number; contentType: string | null; contract: string | null; etag: string | null; body: Uint8Array },
): ParsedComplaintAdminPage {
  try {
    if (!Number.isInteger(limit) || limit < 1 || limit > 50 || response.status !== 200 || response.contract !== '1'
      || response.etag !== null || response.body.byteLength < 1 || response.body.byteLength > 2_097_152
      || !response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType)
      || !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) return invalid();
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body);
    let offset = 0;
    const names = new Set<string>();
    const items: ParsedComplaintAdminItem[] = [];
    let nextCursor: string | null = null;
    const space = () => { while (offset < raw.length && /[ \t\r\n]/.test(raw[offset])) offset++; };
    const string = (): string => {
      const start = offset;
      if (raw[offset++] !== '"') return invalid();
      while (offset < raw.length) {
        const next = raw[offset++];
        if (next === '\\') offset++;
        else if (next === '"') {
          const value: unknown = JSON.parse(raw.slice(start, offset)); // Envelope strings only.
          return typeof value === 'string' ? value : invalid();
        }
        if (offset - start > 12_300) return invalid(); // Max escaped cursor2048, plus quotes.
      }
      return invalid();
    };
    const item = () => {
      const start = offset;
      if (raw[offset++] !== '{') return invalid();
      let quoted = false;
      while (offset < raw.length && offset - start <= 32_768) {
        const next = raw[offset++];
        if (quoted && next === '\\') offset++;
        else if (next === '"') quoted = !quoted;
        else if (!quoted && (next === '{' || next === '[')) return invalid();
        else if (!quoted && next === '}') {
          const scalarObject = raw.slice(start, offset);
          if (new TextEncoder().encode(scalarObject).byteLength > 32_768) return invalid();
          return readAdminItem(readFlatDetail(scalarObject)); // Numeric version tokens never enter JSON.parse.
        }
      }
      return invalid();
    };
    space();
    if (raw[offset++] !== '{') return invalid();
    space();
    while (raw[offset] !== '}') {
      const name = string();
      if (!['items', 'nextCursor'].includes(name) || names.has(name)) return invalid();
      names.add(name); space();
      if (raw[offset++] !== ':') return invalid();
      space();
      if (name === 'items') {
        if (raw[offset++] !== '[') return invalid();
        space();
        while (raw[offset] !== ']') {
          if (items.length >= limit) return invalid();
          items.push(item()); space();
          if (raw[offset] !== ',') break;
          offset++; space();
          if (raw[offset] === ']') return invalid();
        }
        if (raw[offset++] !== ']') return invalid();
      } else if (raw.startsWith('null', offset)) offset += 4;
      else { nextCursor = string(); if (!isComplaintSearchCursor(nextCursor)) return invalid(); }
      space();
      if (raw[offset] !== ',') break;
      offset++; space();
      if (raw[offset] === '}') return invalid();
    }
    if (raw[offset++] !== '}' || names.size !== 2) return invalid();
    space();
    if (offset !== raw.length || nextCursor !== null && items.length === 0 || new Set(items.map((row) => row.id)).size !== items.length) return invalid();
    for (let index = 1; index < items.length; index++) {
      const previous = items[index - 1], current = items[index];
      const before = timeKey(previous.updatedAt), after = timeKey(current.updatedAt);
      // Canonical UUID spelling has PostgreSQL's unsigned-byte lexical order.
      if (before < after || before === after && previous.id <= current.id) return invalid();
    }
    return Object.freeze({ items: Object.freeze(items), nextCursor });
  } catch { return invalid(); }
}

/** Same item rules for detail and search; only real detail metadata supplies an HTTP ETag/expected ID. */
function readAdminItem(fields: Map<string, string | null>, expected?: { id: string; etag: string | null }): ParsedComplaintAdminItem {
  const id = stringField(fields, 'id');
  if (!isUuid(id) || expected && id !== expected.id) invalid();
  const kind = stringField(fields, 'kind');
  const version = stringField(fields, 'version'); // Original numeric token, never Number/JSON.parse.
  const createdAt = stringField(fields, 'createdAt');
  const updatedAt = stringField(fields, 'updatedAt');
  if (timeKey(createdAt) > timeKey(updatedAt)) invalid();
  const common = { id, version, createdAt, updatedAt };

  if (kind === 'NOTICE') {
    requireFields(fields, [...commonFields, 'noticeKey']);
    if (stringField(fields, 'ownership') !== 'SYSTEM' || stringField(fields, 'status') !== 'PINNED' ||
        nullableField(fields, 'ownerReference') !== null || expected && expected.etag !== null) invalid();
    const noticeKey = stringField(fields, 'noticeKey');
    requireNoticeKey(noticeKey);
    return Object.freeze({ ...common, kind: 'NOTICE' as const, status: 'PINNED' as const, ownership: 'SYSTEM' as const, ownerReference: null, noticeKey });
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
  if (actionTag !== `"complaint-${id}-v${version}"` || expected && expected.etag !== actionTag) invalid();
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
  return item;
}

/** Only the closed detail object's scalar fields. No recursion, arrays or generic JSON AST. */
function readFlatDetail(raw: string): Map<string, string | null> {
  let offset = 0;
  const fields = new Map<string, string | null>();
  const whitespace = () => {
    while (offset < raw.length && (raw[offset] === ' ' || raw[offset] === '\t' || raw[offset] === '\r' || raw[offset] === '\n')) offset++;
  };
  const string = (): string => {
    const token = readComplaintJsonString(raw, offset);
    offset = token.end;
    return token.value;
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
        const token = readComplaintLongToken(raw, offset);
        value = token.value;
        offset = token.end;
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

/** Shared scalar reader only; callers own the closed schema, duplicate checks and bounded UTF-8 body. */
export function readComplaintJsonString(raw: string, start: number, maximumLength = raw.length): { value: string; end: number } {
  let offset = start;
  if (raw[offset++] !== '"') return invalid();
  while (offset < raw.length && offset - start < maximumLength) {
    const code = raw.charCodeAt(offset++);
    if (code === 0x22) {
      const value: unknown = JSON.parse(raw.slice(start, offset)); // Strings only, never version/count tokens.
      if (typeof value !== 'string') return invalid();
      requireWellFormed(value);
      return { value, end: offset };
    }
    if (code === 0x5c) offset++; // JSON.parse checks the complete escape, including surrogate pairs above.
    else if (code <= 0x1f) return invalid();
  }
  return invalid();
}

/** Original Long digits, never Number/JSON.parse. Only stats' nonnegative fields permit literal zero. */
export function readComplaintLongToken(raw: string, start: number, allowZero = false): { value: string; end: number } {
  let end = start;
  while (end < raw.length && raw[end] >= '0' && raw[end] <= '9') {
    if (end - start >= maximumLong.length) return invalid();
    end++;
  }
  const value = raw.slice(start, end);
  if (!value || value[0] === '0' && (!allowZero || value !== '0') ||
      value.length === maximumLong.length && value > maximumLong) return invalid();
  return { value, end };
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
