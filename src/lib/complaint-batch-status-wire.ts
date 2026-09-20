import type { ComplaintModerationTarget, ComplaintStatusTarget } from './complaint-moderation-wire';
import { complaintActionVersion, ComplaintMutationWireError, decodeComplaintMutationProblem, validateComplaintMutationResponse, type ComplaintMutationOutcome, type ComplaintMutationResponse } from './complaint-mutation-wire';
import { readComplaintJsonString, readComplaintLongToken } from './complaint-read-wire';
import { isSessionSelector } from './session-contract';

export const complaintBatchStatuses: readonly ComplaintStatusTarget[] = ['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
type Target = Readonly<{ id: string; actionTag: string; baseVersion: string }>;
type Item = Readonly<{ id: string; version: string }>;

/** One detached description, never N single-item operations, credentials or mutation authority. */
export type ComplaintBatchStatusRequest = Readonly<{
  method: 'POST'; path: string; dataScopeId: string; status: ComplaintStatusTarget;
  targets: readonly Target[];
  headers: Readonly<{ 'Content-Type': 'application/json'; 'X-Kira-Complaint-Contract': '1'; 'X-Kira-Idempotency-Key': string }>;
  body: string;
}>;
export type ComplaintBatchStatusOutcome = Exclude<ComplaintMutationOutcome, { kind: 'applied' | 'deleted' }>
  | Readonly<{ kind: 'batch-applied'; items: readonly Item[] }>;

/** Closed request classification only; never includes IDs, tags, prose or parser diagnostics. */
export class ComplaintBatchStatusBodyError extends Error {
  constructor(readonly status: 400 | 412 | 428) { super('Complaint status batch request refused.'); this.name = 'ComplaintBatchStatusBodyError'; }
}
function malformed(): never { throw new ComplaintBatchStatusBodyError(400); }

/** Tiny schema-owned reader. Only string/Long scalars are shared with existing complaint readers. */
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

function parseBody(body: string): { status: ComplaintStatusTarget; targets: readonly Target[] } {
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
    // Finish the entire closed JSON/schema first: duplicate/unknown fields always remain400.
    if (names.size !== 3 || action !== 'STATUS' || !complaintBatchStatuses.includes(status as ComplaintStatusTarget)
      || targets.length < 1 || new Set(targets.map((target) => target.id)).size !== targets.length) malformed();
    if (targets.some((target) => target.actionTag === undefined)) throw new ComplaintBatchStatusBodyError(428);
    const checked = targets.map(({ id, actionTag }) => {
      try { return Object.freeze({ id, actionTag: actionTag!, baseVersion: complaintActionVersion(id, actionTag!) }); }
      catch { throw new ComplaintBatchStatusBodyError(412); }
    }).sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    return { status: status as ComplaintStatusTarget, targets: Object.freeze(checked) };
  } catch (error) {
    if (error instanceof ComplaintBatchStatusBodyError) throw error;
    return malformed();
  }
}

/** BFF/capture validation preserves the original valid body bytes, including order/formatting. */
export function captureComplaintBatchStatusRequest(body: string, dataScopeId: string, idempotencyKey: string): ComplaintBatchStatusRequest {
  if (!isSessionSelector(dataScopeId) || !isSessionSelector(idempotencyKey)) throw new ComplaintMutationWireError('INVALID_CAPTURE');
  const parsed = parseBody(body);
  return Object.freeze({ method: 'POST', path: `/api/v1/admin/complaints/batch?dataScopeId=${dataScopeId}`, dataScopeId,
    status: parsed.status, targets: parsed.targets, body,
    headers: Object.freeze({ 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Idempotency-Key': idempotencyKey }),
  });
}

/** Current-page UI rows only; no fabricated NOTICE tags or cross-page accumulation. */
export function prepareComplaintBatchStatusRequest(targets: readonly ComplaintModerationTarget[], status: ComplaintStatusTarget,
  dataScopeId: string, idempotencyKey: string): ComplaintBatchStatusRequest {
  try {
    if (!Array.isArray(targets) || targets.length < 1 || targets.length > 50
      || targets.some((target) => !['REPORT', 'REPLY'].includes(target.kind) || target.ownership !== 'INSTALLATION')) malformed();
    const pairs = targets.map(({ id, actionTag }) => ({ id, actionTag })).sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    return captureComplaintBatchStatusRequest(JSON.stringify({ action: 'STATUS', status, targets: pairs }), dataScopeId, idempotencyKey);
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}

/** Reconstruct only the fixed BFF destination, validating the complete detached descriptor. */
export function complaintBatchStatusDestination(request: ComplaintBatchStatusRequest): string {
  try {
    if (Object.keys(request.headers).sort().join(',') !== 'Content-Type,X-Kira-Complaint-Contract,X-Kira-Idempotency-Key'
      || request.headers['Content-Type'] !== 'application/json' || request.headers['X-Kira-Complaint-Contract'] !== '1') malformed();
    const checked = captureComplaintBatchStatusRequest(request.body, request.dataScopeId, request.headers['X-Kira-Idempotency-Key']);
    if (request.method !== 'POST' || request.path !== checked.path || request.status !== checked.status || request.targets.length !== checked.targets.length
      || request.targets.some((target, index) => Object.keys(target).sort().join(',') !== 'actionTag,baseVersion,id'
        || target.id !== checked.targets[index].id || target.actionTag !== checked.targets[index].actionTag || target.baseVersion !== checked.targets[index].baseVersion)) malformed();
    return `/api/backend/complaints/batch?dataScopeId=${checked.dataScopeId}`;
  } catch { throw new ComplaintMutationWireError('INVALID_CAPTURE'); }
}

/** Complete canonical target set and every exact Long successor; no partial-success inference. */
export function isCompleteComplaintBatchStatusResult(request: ComplaintBatchStatusRequest, items: readonly Item[]): boolean {
  try {
    return items.length === request.targets.length && items.length >= 1 && items.length <= 50 && items.every((item, index) => {
      const target = request.targets[index];
      const version = readComplaintLongToken(item.version, 0);
      return item.id === target.id && version.end === item.version.length
        && BigInt(version.value) === BigInt(target.baseVersion) + BigInt(1);
    });
  } catch { return false; }
}

export function decodeComplaintBatchStatusOutcome(request: ComplaintBatchStatusRequest, response: ComplaintMutationResponse): ComplaintBatchStatusOutcome {
  try {
    complaintBatchStatusDestination(request);
    validateComplaintMutationResponse(response);
    if (response.etag !== null || response.location !== null) throw new Error();
    if (response.status !== 200) return decodeComplaintMutationProblem(response);
    if (!response.contentType || response.contentType.length > 128 || /[\r\n]/.test(response.contentType)
      || !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(response.contentType)) throw new Error();
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(response.body);
    const reader = new BatchJson(raw);
    let items: Item[] = [];
    const names = reader.object(['items'], () => {
      items = reader.array(() => {
        let id = '', version = '';
        const fields = reader.object(['id', 'version'], (name) => { if (name === 'id') id = reader.string(); else version = reader.long(); });
        if (fields.size !== 2) malformed();
        return Object.freeze({ id, version });
      });
    });
    reader.finish();
    if (names.size !== 1 || !isCompleteComplaintBatchStatusResult(request, items)) throw new Error();
    return Object.freeze({ kind: 'batch-applied', items: Object.freeze(items) });
  } catch { throw new ComplaintMutationWireError('UNCONFIRMED_RESPONSE'); }
}
