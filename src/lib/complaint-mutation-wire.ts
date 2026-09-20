import { prepareComplaintClosureReason, prepareComplaintEditedBody, prepareComplaintOrdinaryContent, type ComplaintContentType } from './complaint-content-editor';

const uuid = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
const canonicalUuid = new RegExp(`^${uuid}$`);
const maximumLong = '9223372036854775807';
const whitespace = '[ \\t\\r\\n]*';
const idField = `"id"${whitespace}:${whitespace}"(${uuid})"`;
const versionField = `"version"${whitespace}:${whitespace}([1-9][0-9]{0,18})`;
// The backend emits these two fixed fields, a canonical UUID and a decimal numeric Long.
// Do not feed that numeric token to JSON.parse/Number: values above 2^53 would be rounded.
const idFirst = new RegExp(`^${whitespace}\\{${whitespace}${idField}${whitespace},${whitespace}${versionField}${whitespace}\\}${whitespace}$`);
const versionFirst = new RegExp(`^${whitespace}\\{${whitespace}${versionField}${whitespace},${whitespace}${idField}${whitespace}\\}${whitespace}$`);

export class ComplaintMutationWireError extends Error {
  constructor(readonly reason: 'INVALID_CAPTURE' | 'UNCONFIRMED_RESPONSE') {
    super(`Complaint mutation: ${reason}.`);
    this.name = 'ComplaintMutationWireError';
  }
}

/** A local request description, not a fetch command, credential or mutation authority. */
export type ComplaintMutationRequest = Readonly<{
  method: 'PATCH' | 'DELETE';
  path: string;
  targetId: string;
  dataScopeId: string;
  baseVersion: string;
  headers: Readonly<{
    'Content-Type': 'application/json';
    'X-Kira-Complaint-Contract': '1';
    'X-Kira-Idempotency-Key': string;
    'If-Match': string;
  }>;
  /** DELETE uses exactly '' as a local absence marker, never a serialized request body. */
  body: string;
}>;

/** Build only a local immutable description; scope syntax is never mutation authority. */
export function prepareComplaintMutationRequest(
  operation: ComplaintMutationOperation,
  targetId: string,
  dataScopeId: string,
  idempotencyKey: string,
  actionTag: string,
  body: string,
): ComplaintMutationRequest {
  const invalid = (): never => { throw new ComplaintMutationWireError('INVALID_CAPTURE'); };
  if (operation !== 'content' && operation !== 'status' && operation !== 'closure' && operation !== 'delete') invalid();
  if (!isTestUuid(dataScopeId) || !isTestUuid(idempotencyKey) || !isUuid(targetId)) invalid();
  const baseVersion = complaintActionVersion(targetId, actionTag);
  if (new TextEncoder().encode(body).byteLength > 16_384 || operation === 'delete' && body !== '') invalid();
  const suffix = operation === 'delete' ? '' : `/${operation}`;
  return Object.freeze({
    method: operation === 'delete' ? 'DELETE' : 'PATCH',
    path: `/api/v1/admin/complaints/${targetId}${suffix}?dataScopeId=${dataScopeId}`,
    targetId, dataScopeId, baseVersion,
    headers: Object.freeze({
      'Content-Type': 'application/json',
      'X-Kira-Complaint-Contract': '1',
      'X-Kira-Idempotency-Key': idempotencyKey,
      'If-Match': actionTag,
    }),
    body,
  });
}

/** Shared scalar validation only: an action tag is not current authorization or a fresh read. */
export function complaintActionVersion(targetId: string, actionTag: string): string {
  if (!isUuid(targetId)) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  const tag = new RegExp(`^"complaint-${targetId}-v([1-9][0-9]{0,18})"$`).exec(actionTag);
  if (!tag || tag[0] !== actionTag || !isLong(tag[1])) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  return tag[1];
}

/**
 * Only decode a complete bounded200 success, including its exact ETag. Everything else is
 * unconfirmed, NOT "not committed"; keep the original intent. The caller owns bounded stream
 * acquisition and transport/status handling. This never interprets a step-up consumption marker.
 */
export function decodeComplaintMutationApplied(
  request: ComplaintMutationRequest,
  response: { status: number; contentType: string | null; contract: string | null; etag: string | null; body: Uint8Array },
): Readonly<{ id: string; version: string; actionTag: string }> {
  const unconfirmed = (): never => { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); };
  if (request.method !== 'PATCH' || response.status !== 200 || response.contract !== '1' || response.body.byteLength > 256 ||
      !response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType) ||
      !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) unconfirmed();
  let raw: string;
  try {
    raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body);
  } catch {
    return unconfirmed();
  }
  const first = idFirst.exec(raw);
  const second = first ? null : versionFirst.exec(raw);
  const matched = first ?? second;
  if (!matched || matched[0] !== raw) return unconfirmed();
  const id = first ? matched[1] : matched[2];
  const version = first ? matched[2] : matched[1];
  if (id !== request.targetId || !isLong(version) || !isLong(request.baseVersion) ||
      BigInt(version) !== BigInt(request.baseVersion) + BigInt(1)) unconfirmed();
  const actionTag = `"complaint-${id}-v${version}"`;
  if (response.etag !== actionTag) unconfirmed();
  return Object.freeze({ id, version, actionTag });
}

function isUuid(value: string): boolean {
  return value.length === 36 && canonicalUuid.test(value);
}

function isLong(value: string): boolean {
  return value.length > 0 && value.length <= maximumLong.length && value[0] !== '0' && !/[^0-9]/.test(value) &&
    (value.length < maximumLong.length || value <= maximumLong);
}

function isTestUuid(value: string): boolean {
  return isUuid(value) && value[14] === '4' && '89ab'.includes(value[19]);
}

export type ComplaintMutationOperation = 'content' | 'status' | 'closure' | 'delete';
export const complaintReceiptHeader = 'X-Kira-Admin-Step-Up-Consumed';

/** Strict flat string object. Duplicate decoded names, arrays, nested objects and numeric tokens fail. */
function mutationFields(raw: string): Record<string, string> {
  const invalid = (): never => { throw new ComplaintMutationWireError('INVALID_CAPTURE'); };
  const fields: Record<string, string> = Object.create(null);
  let offset = 0;
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
  if (raw[offset++] !== '{') invalid();
  space();
  while (raw[offset] !== '}') {
    const name = string();
    if (Object.hasOwn(fields, name) || Object.keys(fields).length >= 3) invalid();
    space();
    if (raw[offset++] !== ':') invalid();
    space();
    fields[name] = string();
    space();
    if (raw[offset] !== ',') break;
    offset++;
    space();
    if (raw[offset] === '}') invalid();
  }
  if (raw[offset++] !== '}') invalid();
  space();
  if (offset !== raw.length) invalid();
  return fields;
}

/** Validate without rewriting retained bytes; the real backend still authenticates/normalizes. */
export function validateComplaintMutationBody(operation: ComplaintMutationOperation, body: string) {
  try {
    if (operation === 'delete') {
      if (body !== '') throw new Error();
      return;
    }
    const bytes = new TextEncoder().encode(body);
    if (bytes.length > 16_384 || new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes) !== body) throw new Error();
    const fields = mutationFields(body);
    const keys = Object.keys(fields).sort().join(',');
    if (operation === 'status') {
      if (keys !== 'status' || !['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'].includes(fields.status)) throw new Error();
    } else if (operation === 'closure') {
      if (keys !== 'reason') throw new Error();
      prepareComplaintClosureReason(fields.reason);
    } else if (operation === 'content') {
      if (keys === 'body') {
        prepareComplaintEditedBody(fields.body);
      } else if (keys === 'body,subject,type') {
        prepareComplaintOrdinaryContent({ type: fields.type as ComplaintContentType, subject: fields.subject, body: fields.body });
      } else throw new Error();
    } else throw new Error();
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}

/** Reconstruct a fixed BFF destination; the descriptor's backend path is never a fetch URL. */
export function complaintMutationDestination(request: ComplaintMutationRequest) {
  if (Object.keys(request.headers).sort().join(',') !== 'Content-Type,If-Match,X-Kira-Complaint-Contract,X-Kira-Idempotency-Key'
    || request.headers['Content-Type'] !== 'application/json' || request.headers['X-Kira-Complaint-Contract'] !== '1') throw new ComplaintMutationWireError('INVALID_CAPTURE');
  const operation = (['content', 'status', 'closure', 'delete'] as const).find((action) => request.path === `/api/v1/admin/complaints/${request.targetId}${action === 'delete' ? '' : `/${action}`}?dataScopeId=${request.dataScopeId}`);
  if (!operation) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  const checked = prepareComplaintMutationRequest(operation, request.targetId, request.dataScopeId, request.headers['X-Kira-Idempotency-Key'], request.headers['If-Match'], request.body);
  if (checked.method !== request.method || checked.baseVersion !== request.baseVersion) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  validateComplaintMutationBody(operation, request.body);
  return `/api/backend/complaints/${request.targetId}${operation === 'delete' ? '' : `/${operation}`}?dataScopeId=${request.dataScopeId}`;
}

const problemStatus = {
  VALIDATION_FAILED: 400, UNAUTHORIZED: 401, ADMIN_STEP_UP_REQUIRED: 401, FORBIDDEN: 403, NOT_FOUND: 404,
  IDEMPOTENCY_KEY_REUSED: 409, IDEMPOTENCY_IN_PROGRESS: 409, PRECONDITION_FAILED: 412, PAYLOAD_TOO_LARGE: 413,
  UNSUPPORTED_MEDIA_TYPE: 415, PRECONDITION_REQUIRED: 428, RATE_LIMITED: 429, SERVICE_UNAVAILABLE: 503, INTERNAL_ERROR: 500,
  COMPLAINT_NOT_FOUND: 404, COMPLAINT_INVALID_TRANSITION: 409, COMPLAINT_NO_CHANGE: 409, COMPLAINT_DELETION_PENDING: 409,
} as const;
const titles: Record<number, string> = { 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 409: 'Conflict', 412: 'Precondition Failed', 413: 'Payload Too Large', 415: 'Unsupported Media Type', 428: 'Precondition Required', 429: 'Too Many Requests', 500: 'Internal Server Error', 503: 'Service Unavailable' };
const terminalCodes = new Set(['COMPLAINT_NOT_FOUND', 'COMPLAINT_INVALID_TRANSITION', 'COMPLAINT_NO_CHANGE', 'COMPLAINT_DELETION_PENDING', 'PRECONDITION_FAILED']);
export type ComplaintMutationOutcome = Readonly<
  | { kind: 'applied'; id: string; version: string; actionTag: string }
  | { kind: 'deleted'; id: string }
  | { kind: 'rejected'; code: string }
  | { kind: 'step-up-required' | 'session-expired' | 'unauthorized' | 'forbidden' | 'key-reused' | 'in-progress' | 'unavailable' | 'unknown' | 'stale-session' }
>;

export type ComplaintMutationResponse = Parameters<typeof decodeComplaintMutationApplied>[1] & {
  consumed: string | null; challenge: string | null; retryAfter: string | null; location: string | null;
};

/** Shared response metadata, never proof retirement or a success/receipt assertion by itself. */
export function validateComplaintMutationResponse(response: ComplaintMutationResponse): void {
  const invalid = (): never => { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); };
  if (response.contract !== '1' || response.body.length > 32_768 || response.consumed !== null && response.consumed !== 'true'
    || response.retryAfter !== null && (!/^[1-9][0-9]{0,5}$/.test(response.retryAfter) || ![409, 429, 503].includes(response.status))) invalid();
  if (response.status === 401 ? response.challenge !== 'Bearer realm="kira-complaints"' : response.challenge !== null) invalid();
}

/** Only actual fixed backend encodings; unknown/extra/duplicate JSON is never a confirmed result. */
export function decodeComplaintMutationOutcome(request: ComplaintMutationRequest, response: ComplaintMutationResponse): ComplaintMutationOutcome {
  const invalid = (): never => { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); };
  validateComplaintMutationResponse(response);
  if (response.status === 200) return Object.freeze({ kind: 'applied', ...decodeComplaintMutationApplied(request, response) });
  if (response.status === 204) {
    if (request.method !== 'DELETE' || response.body.length !== 0 || response.contentType !== null || response.etag !== null || response.location !== null) invalid();
    return Object.freeze({ kind: 'deleted', id: request.targetId });
  }
  return decodeComplaintMutationProblem(response);
}

/** Single and atomic status batch share only the existing closed refusal/receipt vocabulary. */
export function decodeComplaintMutationProblem(response: ComplaintMutationResponse): Exclude<ComplaintMutationOutcome, { kind: 'applied' | 'deleted' }> {
  const invalid = (): never => { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); };
  validateComplaintMutationResponse(response);
  if (response.etag !== null || !response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType)
    || !/^application\/problem\+json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) invalid();
  let raw: string;
  try { raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body); } catch { return invalid(); }
  if (response.status === 404 && raw === '{"type":"about:blank","title":"Not Found","status":404,"detail":"Not found."}' && response.consumed === null) return { kind: 'unavailable' };
  const code = Object.entries(problemStatus).find(([code, status]) => status === response.status && raw === JSON.stringify({
    type: 'about:blank', title: titles[status], status, errors: [{ code, message: 'Complaint request refused.' }],
  }))?.[0];
  if (!code || response.consumed === 'true' && !terminalCodes.has(code) && ![500, 503].includes(response.status)) return invalid();
  if (code === 'IDEMPOTENCY_IN_PROGRESS' && response.retryAfter !== '1') invalid();
  if (terminalCodes.has(code) && response.consumed === 'true') return { kind: 'rejected', code };
  if (code === 'ADMIN_STEP_UP_REQUIRED') return { kind: 'step-up-required' };
  if (code === 'UNAUTHORIZED') return { kind: 'unauthorized' };
  if (code === 'FORBIDDEN') return { kind: 'forbidden' };
  if (code === 'IDEMPOTENCY_KEY_REUSED') return { kind: 'key-reused' };
  if (code === 'IDEMPOTENCY_IN_PROGRESS') return { kind: 'in-progress' };
  return { kind: 'unknown' };
}
