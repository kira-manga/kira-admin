import { prepareComplaintContentEdit, type PreparedComplaintContentEdit } from './complaint-content-editor';

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

export class ComplaintContentWireError extends Error {
  constructor(readonly reason: 'INVALID_CAPTURE' | 'UNCONFIRMED_RESPONSE') {
    super(`Complaint content: ${reason}.`);
    this.name = 'ComplaintContentWireError';
  }
}

/** A local request description, not a fetch command, credential or mutation authority. */
export type ComplaintContentRequest = Readonly<{
  method: 'PATCH';
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
  body: string;
}>;

/** Retain this exact description on ambiguity; never replace its key or base tag on retry. */
export function prepareComplaintContentRequest(
  capture: PreparedComplaintContentEdit,
  dataScopeId: string,
): ComplaintContentRequest {
  const invalid = (): never => { throw new ComplaintContentWireError('INVALID_CAPTURE'); };
  // This dormant slice is TEST-only. A v4 scope is syntax, NOT authenticated run authority.
  if (!isUuid(dataScopeId) || dataScopeId[14] !== '4' || !'89ab'.includes(dataScopeId[19])) invalid();
  if (capture.operation !== 'content' || !isUuid(capture.base.id)) invalid();
  const targetId = capture.base.id;
  const tag = new RegExp(`^"complaint-${targetId}-v([1-9][0-9]{0,18})"$`).exec(capture.base.actionTag);
  if (!tag || tag[0] !== capture.base.actionTag || !isLong(tag[1])) return invalid();
  let body: string;
  try {
    const checked = capture.variant === 'ordinary'
      ? prepareComplaintContentEdit({ variant: 'ordinary', base: capture.base, content: { ...capture.content } }, capture.idempotencyKey)
      : capture.variant === 'notice-reply'
        ? prepareComplaintContentEdit({ variant: 'notice-reply', base: capture.base, content: { ...capture.content } }, capture.idempotencyKey)
        : invalid();
    // Preparation already normalized this content. Never change the meaning of a saved intent.
    if (checked.variant !== capture.variant || checked.content.body !== capture.content.body) invalid();
    if (checked.variant === 'ordinary' && capture.variant === 'ordinary' &&
        (checked.content.type !== capture.content.type || checked.content.subject !== capture.content.subject)) invalid();
    body = JSON.stringify(checked.content);
  } catch {
    return invalid();
  }
  if (new TextEncoder().encode(body).byteLength > 16_384) invalid();
  return Object.freeze({
    method: 'PATCH',
    path: `/api/v1/admin/complaints/${targetId}/content?dataScopeId=${dataScopeId}`,
    targetId, dataScopeId, baseVersion: tag[1],
    headers: Object.freeze({
      'Content-Type': 'application/json',
      'X-Kira-Complaint-Contract': '1',
      'X-Kira-Idempotency-Key': capture.idempotencyKey,
      'If-Match': capture.base.actionTag,
    }),
    body,
  });
}

/**
 * Only decode a complete bounded200 success, including its exact ETag. Everything else is
 * unconfirmed, NOT "not committed"; keep the original intent. The caller owns bounded stream
 * acquisition and transport/status handling. This never interprets a step-up consumption marker.
 */
export function decodeComplaintContentApplied(
  request: ComplaintContentRequest,
  response: { status: number; contentType: string | null; contract: string | null; etag: string | null; body: Uint8Array },
): Readonly<{ id: string; version: string; actionTag: string }> {
  const unconfirmed = (): never => { throw new ComplaintContentWireError('UNCONFIRMED_RESPONSE'); };
  if (response.status !== 200 || response.contract !== '1' || response.body.byteLength > 256 ||
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
