import { prepareComplaintSearchText, type ComplaintContentType } from './complaint-content-editor';
import { isCsrfToken, isSessionSelector } from './session-contract';

export const complaintSearchStatuses = ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'PLANNED', 'PINNED', 'NOT_PLANNED'] as const;
export const complaintSearchTypes: readonly ComplaintContentType[] = ['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM'];
export type ComplaintSearchStatus = typeof complaintSearchStatuses[number];
export type ComplaintAdminSearchQuery = Readonly<{
  dataScopeId: string; text: string; status: ComplaintSearchStatus | null; type: ComplaintContentType | null;
  ownership: 'INSTALLATION' | 'SYSTEM' | null; updatedFrom: string | null; updatedBefore: string | null;
  sort: 'UPDATED_DESC'; limit: number; cursor: string | null;
}>;
export type ComplaintAdminSearchInput = Pick<ComplaintAdminSearchQuery, 'dataScopeId'> & Partial<Omit<ComplaintAdminSearchQuery, 'dataScopeId'>>;

export class ComplaintSearchWireError extends Error {
  constructor() { super('Complaint search request is invalid.'); this.name = 'ComplaintSearchWireError'; }
}

const keys = new Set(['dataScopeId', 'text', 'status', 'type', 'ownership', 'updatedFrom', 'updatedBefore', 'sort', 'limit', 'cursor']);

/** Syntax only: the backend authenticates the opaque cursor's actor/filter/scope/expiry binding. */
export function isComplaintSearchCursor(value: unknown): value is string {
  if (typeof value !== 'string' || value.length > 2048 || !/^v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(value)) return false;
  const [, payload, signature] = value.split('.');
  const bytes = Math.floor(payload.length * 6 / 8);
  const remainder = payload.length % 4;
  return bytes >= 1 && bytes <= 512 && remainder !== 1 && isCsrfToken(signature)
    && (remainder !== 2 || /[AQgw]$/.test(payload)) && (remainder !== 3 || /[AEIMQUYcgkosw048]$/.test(payload));
}

/** Matches ComplaintAdminSearchParser's UTC calendar grammar (1–6 fractional digits), not Date rounding. */
function dateKey(value: string): string {
  const match = /^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?Z$/.exec(value);
  if (!match || match[0] !== value) return invalid();
  const year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > days[month - 1]
    || Number(match[4]) > 23 || Number(match[5]) > 59 || Number(match[6]) > 59) return invalid();
  return match.slice(1, 7).join('') + (match[7] ?? '').padEnd(6, '0');
}

/** Detached, bounded in-memory selection. It grants no TEST/ADMIN authority and contains no credentials. */
export function prepareComplaintAdminSearch(input: ComplaintAdminSearchInput): ComplaintAdminSearchQuery {
  try {
    if (!input || Object.keys(input).some((key) => !keys.has(key)) || !isSessionSelector(input.dataScopeId)) return invalid();
    const text = input.text === undefined ? '' : input.text;
    if (typeof text !== 'string' || text.length > 32_768) return invalid();
    const status = input.status ?? null, type = input.type ?? null, ownership = input.ownership ?? null;
    if (status !== null && !complaintSearchStatuses.includes(status) || type !== null && !complaintSearchTypes.includes(type)
      || ownership !== null && ownership !== 'INSTALLATION' && ownership !== 'SYSTEM') return invalid();
    const updatedFrom = input.updatedFrom ?? null, updatedBefore = input.updatedBefore ?? null;
    if (updatedFrom !== null && typeof updatedFrom !== 'string' || updatedBefore !== null && typeof updatedBefore !== 'string') return invalid();
    const from = updatedFrom === null ? null : dateKey(updatedFrom), before = updatedBefore === null ? null : dateKey(updatedBefore);
    if (from !== null && before !== null && from >= before) return invalid();
    const sort = input.sort === undefined ? 'UPDATED_DESC' : input.sort, limit = input.limit === undefined ? 50 : input.limit;
    const cursor = input.cursor ?? null;
    if (sort !== 'UPDATED_DESC' || !Number.isInteger(limit) || limit < 1 || limit > 50 || cursor !== null && !isComplaintSearchCursor(cursor)) return invalid();
    return Object.freeze({ dataScopeId: input.dataScopeId, text: prepareComplaintSearchText(text), status, type, ownership, updatedFrom, updatedBefore, sort, limit, cursor });
  } catch { return invalid(); }
}

/** Closed, duplicate-aware flat JSON, matching the existing backend search request; no generic AST. */
export function parseComplaintAdminSearchBody(bytes: Uint8Array): ComplaintAdminSearchQuery {
  try {
    if (bytes.byteLength < 1 || bytes.byteLength > 32_768) return invalid();
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
    let offset = 0;
    const fields: Record<string, string | number | null> = Object.create(null);
    const space = () => { while (offset < raw.length && /[ \t\r\n]/.test(raw[offset])) offset++; };
    const string = (): string => {
      const start = offset;
      if (raw[offset++] !== '"') return invalid();
      while (offset < raw.length) {
        const next = raw[offset++];
        if (next === '\\') offset++;
        else if (next === '"') return JSON.parse(raw.slice(start, offset)) as string;
      }
      return invalid();
    };
    space();
    if (raw[offset++] !== '{') return invalid();
    space();
    while (raw[offset] !== '}') {
      const name = string();
      if (!keys.has(name) || Object.hasOwn(fields, name)) return invalid();
      space();
      if (raw[offset++] !== ':') return invalid();
      space();
      if (name === 'limit') {
        const start = offset;
        while (offset < raw.length && /[0-9]/.test(raw[offset])) offset++;
        const value = raw.slice(start, offset);
        if (!/^(?:[1-9]|[1-4][0-9]|50)$/.test(value)) return invalid();
        fields[name] = Number(value); // Only the closed1–50 integer, never a version/count.
      } else if (raw.startsWith('null', offset)) {
        if (['dataScopeId', 'text', 'sort'].includes(name)) return invalid();
        fields[name] = null; offset += 4;
      } else fields[name] = string();
      space();
      if (raw[offset] !== ',') break;
      offset++; space();
      if (raw[offset] === '}') return invalid();
    }
    if (raw[offset++] !== '}') return invalid();
    space();
    if (offset !== raw.length || typeof fields.dataScopeId !== 'string') return invalid();
    return prepareComplaintAdminSearch(fields as ComplaintAdminSearchInput);
  } catch { return invalid(); }
}

function invalid(): never { throw new ComplaintSearchWireError(); }
