import type { ComplaintModerationTarget, ComplaintStatusTarget } from './complaint-moderation-wire';
import { complaintActionVersion, ComplaintMutationWireError, decodeComplaintMutationProblem, validateComplaintMutationResponse, type ComplaintMutationOutcome, type ComplaintMutationResponse } from './complaint-mutation-wire';
import { readComplaintJsonString, readComplaintLongToken } from './complaint-read-wire';
import { isSessionSelector } from './session-contract';

export const complaintBatchStatuses: readonly ComplaintStatusTarget[] = ['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
type Target = Readonly<{ id: string; actionTag: string; baseVersion: string }>;
type StatusItem = Readonly<{ id: string; version: string }>;
type DeleteItem = Readonly<{ id: string }>;
type BatchRequest = Readonly<{
  method: 'POST'; path: string; dataScopeId: string; targets: readonly Target[];
  headers: Readonly<{ 'Content-Type': 'application/json'; 'X-Kira-Complaint-Contract': '1'; 'X-Kira-Idempotency-Key': string }>;
  body: string;
}>;

/** One detached, closed description, never N single-item operations or mutation authority. */
export type ComplaintBatchStatusRequest = BatchRequest & Readonly<{ action: 'STATUS'; status: ComplaintStatusTarget }>;
export type ComplaintBatchDeleteRequest = BatchRequest & Readonly<{ action: 'DELETE' }>;
export type ComplaintBatchRequest = ComplaintBatchStatusRequest | ComplaintBatchDeleteRequest;
type BatchFailure = Exclude<ComplaintMutationOutcome, { kind: 'applied' | 'deleted' }>;
export type ComplaintBatchStatusOutcome = BatchFailure | Readonly<{ kind: 'batch-applied'; items: readonly StatusItem[] }>;
export type ComplaintBatchDeleteOutcome = BatchFailure | Readonly<{ kind: 'batch-deleted'; items: readonly DeleteItem[] }>;
export type ComplaintBatchOutcome = ComplaintBatchStatusOutcome | ComplaintBatchDeleteOutcome;

/** Closed request classification only; never includes IDs, tags, prose or parser diagnostics. */
export class ComplaintBatchBodyError extends Error {
  constructor(readonly status: 400 | 412 | 428) { super('Complaint batch request refused.'); this.name = 'ComplaintBatchBodyError'; }
}
function malformed(): never { throw new ComplaintBatchBodyError(400); }

/** The existing schema-owned STATUS reader, shared without JSON-number conversion or trial parsing. */
class BatchJson {
  private offset = 0;
  constructor(private readonly raw: string) {}
  private space() { while (this.offset < this.raw.length && /[ \t\r\n]/.test(this.raw[this.offset])) this.offset++; }
  private take(token: string) { this.space(); if (this.raw[this.offset] !== token) return false; this.offset++; return true; }
  private need(token: string) { if (!this.take(token)) malformed(); }
  string() { this.space(); const token = readComplaintJsonString(this.raw, this.offset); this.offset = token.end; return token.value; }
  long() { this.space(); const token = readComplaintLongToken(this.raw, this.offset); this.offset = token.end; return token.value; }
  object(allowed: readonly string[], read: (name: string) => void) {
    this.need('{');
    const names = new Set<string>();
    if (this.take('}')) return names;
    do {
      const name = this.string();
      if (!allowed.includes(name) || names.has(name)) malformed();
      names.add(name); this.need(':'); read(name);
      if (this.take('}')) return names;
      this.need(',');
    } while (true);
  }
  array<T>(read: () => T): T[] {
    this.need('[');
    const values: T[] = [];
    if (this.take(']')) return values;
    do {
      if (values.length >= 50) malformed();
      values.push(read());
      if (this.take(']')) return values;
      this.need(',');
    } while (true);
  }
  finish() { this.space(); if (this.offset !== this.raw.length) malformed(); }
}

function parseBody(body: string, expectedAction?: ComplaintBatchRequest['action']): Readonly<{ action: 'STATUS'; status: ComplaintStatusTarget; targets: readonly Target[] }>
  | Readonly<{ action: 'DELETE'; targets: readonly Target[] }> {
  try {
    const bytes = new TextEncoder().encode(body);
    if (bytes.length < 1 || bytes.length > 32_768 || new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes) !== body) malformed();
    const reader = new BatchJson(body);
    let action = '', status = '';
    let targets: { id: string; actionTag?: string }[] = [];
    const names = reader.object(['action', 'status', 'targets'], (name) => {
      if (name === 'action') action = reader.string();
      else if (name === 'status') status = reader.string();
      else targets = reader.array(() => {
        let id = '', actionTag: string | undefined;
        const fields = reader.object(['id', 'actionTag'], (field) => {
          if (field === 'id') id = reader.string(); else actionTag = reader.string();
        });
        if (!fields.has('id') || id.length !== 36 || !uuid.test(id)) malformed();
        return { id, actionTag };
      });
    });
    reader.finish();
    // Complete structural400 precedes missing-tag428, which precedes malformed-string-tag412.
    if (!names.has('action') || !names.has('targets') || targets.length < 1
      || new Set(targets.map((target) => target.id)).size !== targets.length) malformed();
    if (action === 'STATUS' ? names.size !== 3 || !complaintBatchStatuses.includes(status as ComplaintStatusTarget)
      : action !== 'DELETE' || names.size !== 2 || names.has('status')) malformed();
    if (expectedAction !== undefined && action !== expectedAction) malformed();
    if (targets.some((target) => target.actionTag === undefined)) throw new ComplaintBatchBodyError(428);
    const checked = Object.freeze(targets.map(({ id, actionTag }) => {
      try { return Object.freeze({ id, actionTag: actionTag!, baseVersion: complaintActionVersion(id, actionTag!) }); }
      catch { throw new ComplaintBatchBodyError(412); }
    }).sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
    return action === 'STATUS' ? { action, status: status as ComplaintStatusTarget, targets: checked } : { action: 'DELETE', targets: checked };
  } catch (error) {
    if (error instanceof ComplaintBatchBodyError) throw error;
    return malformed();
  }
}

/** BFF/capture validation preserves the original valid body bytes, including order/formatting. */
function captureBatch(body: string, dataScopeId: string, idempotencyKey: string, expectedAction?: ComplaintBatchRequest['action']): ComplaintBatchRequest {
  if (!isSessionSelector(dataScopeId) || !isSessionSelector(idempotencyKey)) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  const parsed = parseBody(body, expectedAction);
  return Object.freeze({ method: 'POST', path: `/api/v1/admin/complaints/batch?dataScopeId=${dataScopeId}`, dataScopeId, ...parsed, body,
    headers: Object.freeze({ 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Idempotency-Key': idempotencyKey }),
  });
}

export function captureComplaintBatchRequest(body: string, dataScopeId: string, idempotencyKey: string): ComplaintBatchRequest {
  return captureBatch(body, dataScopeId, idempotencyKey);
}
export function captureComplaintBatchStatusRequest(body: string, dataScopeId: string, idempotencyKey: string): ComplaintBatchStatusRequest {
  const request = captureBatch(body, dataScopeId, idempotencyKey, 'STATUS');
  if (request.action !== 'STATUS') malformed();
  return request;
}
export function captureComplaintBatchDeleteRequest(body: string, dataScopeId: string, idempotencyKey: string): ComplaintBatchDeleteRequest {
  const request = captureBatch(body, dataScopeId, idempotencyKey, 'DELETE');
  if (request.action !== 'DELETE') malformed();
  return request;
}

/** Current-page UI rows only; no fabricated NOTICE tags or cross-page accumulation. */
function selectedPairs(targets: readonly ComplaintModerationTarget[]) {
  if (!Array.isArray(targets) || targets.length < 1 || targets.length > 50
    || targets.some((target) => !['REPORT', 'REPLY'].includes(target.kind) || target.ownership !== 'INSTALLATION')) malformed();
  return targets.map(({ id, actionTag }) => ({ id, actionTag })).sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
}
export function prepareComplaintBatchStatusRequest(targets: readonly ComplaintModerationTarget[], status: ComplaintStatusTarget,
  dataScopeId: string, idempotencyKey: string): ComplaintBatchStatusRequest {
  try {
    return captureComplaintBatchStatusRequest(JSON.stringify({ action: 'STATUS', status, targets: selectedPairs(targets) }), dataScopeId, idempotencyKey);
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}
export function prepareComplaintBatchDeleteRequest(targets: readonly ComplaintModerationTarget[], dataScopeId: string, idempotencyKey: string): ComplaintBatchDeleteRequest {
  try {
    return captureComplaintBatchDeleteRequest(JSON.stringify({ action: 'DELETE', targets: selectedPairs(targets) }), dataScopeId, idempotencyKey);
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}

/** Reconstruct only the fixed BFF destination, validating action as well as the retained bytes. */
export function complaintBatchDestination(request: ComplaintBatchRequest): string {
  try {
    if (Object.keys(request.headers).sort().join(',') !== 'Content-Type,X-Kira-Complaint-Contract,X-Kira-Idempotency-Key'
      || request.headers['Content-Type'] !== 'application/json' || request.headers['X-Kira-Complaint-Contract'] !== '1') malformed();
    const checked = captureComplaintBatchRequest(request.body, request.dataScopeId, request.headers['X-Kira-Idempotency-Key']);
    if (request.action === 'STATUS') {
      if (checked.action !== 'STATUS' || request.status !== checked.status) malformed();
    } else if (request.action !== 'DELETE' || checked.action !== 'DELETE' || Object.hasOwn(request, 'status')) malformed();
    if (request.method !== 'POST' || request.path !== checked.path || request.targets.length !== checked.targets.length
      || request.targets.some((target, index) => Object.keys(target).sort().join(',') !== 'actionTag,baseVersion,id'
        || target.id !== checked.targets[index].id || target.actionTag !== checked.targets[index].actionTag || target.baseVersion !== checked.targets[index].baseVersion)) malformed();
    return `/api/backend/complaints/batch?dataScopeId=${checked.dataScopeId}`;
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}
export function complaintBatchStatusDestination(request: ComplaintBatchStatusRequest): string {
  if (request.action !== 'STATUS') throw new ComplaintMutationWireError('INVALID_CAPTURE');
  return complaintBatchDestination(request);
}

/** Complete canonical target set and every exact Long successor; no partial-success inference. */
export function isCompleteComplaintBatchStatusResult(request: ComplaintBatchStatusRequest, items: readonly StatusItem[]): boolean {
  try {
    return request.action === 'STATUS' && items.length === request.targets.length && items.length >= 1 && items.length <= 50 && items.every((item, index) => {
      const target = request.targets[index];
      const version = readComplaintLongToken(item.version, 0);
      return Object.keys(item).sort().join(',') === 'id,version' && item.id === target.id && version.end === item.version.length
        && BigInt(version.value) === BigInt(target.baseVersion) + BigInt(1);
    });
  } catch { return false; }
}
export function isCompleteComplaintBatchDeleteResult(request: ComplaintBatchDeleteRequest, items: readonly DeleteItem[]): boolean {
  try {
    return request.action === 'DELETE' && items.length === request.targets.length && items.length >= 1 && items.length <= 50
      && items.every((item, index) => Object.keys(item).join(',') === 'id' && item.id === request.targets[index].id);
  } catch { return false; }
}

export function decodeComplaintBatchOutcome(request: ComplaintBatchStatusRequest, response: ComplaintMutationResponse): ComplaintBatchStatusOutcome;
export function decodeComplaintBatchOutcome(request: ComplaintBatchDeleteRequest, response: ComplaintMutationResponse): ComplaintBatchDeleteOutcome;
export function decodeComplaintBatchOutcome(request: ComplaintBatchRequest, response: ComplaintMutationResponse): ComplaintBatchOutcome;
export function decodeComplaintBatchOutcome(request: ComplaintBatchRequest, response: ComplaintMutationResponse): ComplaintBatchOutcome {
  try {
    complaintBatchDestination(request);
    validateComplaintMutationResponse(response);
    if (response.etag !== null || response.location !== null) throw new Error();
    if (response.status !== 200) return decodeComplaintMutationProblem(response);
    if (!response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType)
      || !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) throw new Error();
    const reader = new BatchJson(new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body));
    let statusItems: StatusItem[] = [], deleteItems: DeleteItem[] = [];
    const names = reader.object(['items'], () => {
      if (request.action === 'STATUS') statusItems = reader.array(() => {
        let id = '', version = '';
        const fields = reader.object(['id', 'version'], (name) => { if (name === 'id') id = reader.string(); else version = reader.long(); });
        if (fields.size !== 2) malformed();
        return Object.freeze({ id, version });
      });
      else deleteItems = reader.array(() => {
        let id = '';
        const fields = reader.object(['id'], () => { id = reader.string(); });
        if (fields.size !== 1) malformed();
        return Object.freeze({ id });
      });
    });
    reader.finish();
    if (names.size !== 1) throw new Error();
    if (request.action === 'STATUS') {
      if (!isCompleteComplaintBatchStatusResult(request, statusItems)) throw new Error();
      return Object.freeze({ kind: 'batch-applied', items: Object.freeze(statusItems) });
    }
    if (!isCompleteComplaintBatchDeleteResult(request, deleteItems)) throw new Error();
    return Object.freeze({ kind: 'batch-deleted', items: Object.freeze(deleteItems) });
  } catch { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); }
}

/** Existing STATUS entrypoint stays STATUS-only even though both actions use POST /batch. */
export function decodeComplaintBatchStatusOutcome(request: ComplaintBatchStatusRequest, response: ComplaintMutationResponse): ComplaintBatchStatusOutcome {
  if (request.action !== 'STATUS') throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE');
  return decodeComplaintBatchOutcome(request, response);
}
