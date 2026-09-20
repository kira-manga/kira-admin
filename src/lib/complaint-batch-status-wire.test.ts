import { describe, expect, it } from 'vitest';

import { batchAck, batchRequest, batchResponse, batchSecondId, batchTarget, deleteBatchAck, deleteBatchRequest, deleteBatchResponse } from '@/test/complaint-batch-status-fixture';
import { complaintId, complaintKey, complaintScope, problemResponse } from '@/test/complaint-mutation-fixture';
import { captureComplaintBatchStatusRequest, complaintBatchStatusDestination, ComplaintBatchStatusBodyError, decodeComplaintBatchStatusOutcome, prepareComplaintBatchStatusRequest, type ComplaintBatchStatusRequest } from './complaint-batch-status-wire';
import { captureComplaintBatchDeleteRequest, captureComplaintBatchRequest, complaintBatchDestination, ComplaintBatchBodyError, decodeComplaintBatchOutcome, prepareComplaintBatchDeleteRequest, type ComplaintBatchRequest } from './complaint-batch-wire';

const bytes = (raw: string) => new TextEncoder().encode(raw);
const body = (targets: unknown, change: Record<string, unknown> = {}) => JSON.stringify({ action: 'STATUS', status: 'RESOLVED', targets, ...change });
const pair = () => ({ id: complaintId, actionTag: batchTarget().actionTag });
const capture = (raw: string) => captureComplaintBatchStatusRequest(raw, complaintScope, complaintKey);
async function metadata(response = batchResponse()) {
  return { status: response.status, contentType: response.headers.get('content-type'), contract: response.headers.get('X-Kira-Complaint-Contract'),
    etag: response.headers.get('etag'), consumed: response.headers.get('X-Kira-Admin-Step-Up-Consumed'), challenge: response.headers.get('www-authenticate'),
    retryAfter: response.headers.get('retry-after'), location: response.headers.get('location'), body: new Uint8Array(await response.arrayBuffer()) };
}

describe('closed atomic STATUS batch wire', () => {
  it('captures sorted intact pairs and a detached frozen body while BFF validation preserves valid original formatting', () => {
    const source = [batchTarget(batchSecondId, '7'), batchTarget()];
    const request = prepareComplaintBatchStatusRequest(source, 'RESOLVED', complaintScope, complaintKey);
    expect(request.body).toBe(body([pair(), { id: batchSecondId, actionTag: batchTarget(batchSecondId, '7').actionTag }]));
    expect(request.targets.map((target) => [target.id, target.baseVersion])).toEqual([[complaintId, '9007199254740992'], [batchSecondId, '7']]);
    Object.assign(source[0], { id: complaintId, actionTag: batchTarget(complaintId, '1').actionTag }); source.reverse();
    expect(request.targets[1].actionTag).toBe(batchTarget(batchSecondId, '7').actionTag);
    for (const value of [request, request.headers, request.targets, ...request.targets]) expect(Object.isFrozen(value)).toBe(true);
    expect(Object.keys(request.headers).sort()).toEqual(['Content-Type', 'X-Kira-Complaint-Contract', 'X-Kira-Idempotency-Key']);
    expect(complaintBatchStatusDestination(request)).toBe(`/api/backend/complaints/batch?dataScopeId=${complaintScope}`);
    const raw = ` \n${body([{ id: batchSecondId, actionTag: batchTarget(batchSecondId, '7').actionTag }, pair()])}\t`;
    expect(capture(raw).body).toBe(raw);
    expect(capture(raw).targets).toEqual(request.targets);
  });

  it('bounds the capture to1–50 distinct ordinary targets and rejects scope, action and descriptor widening', () => {
    const fifty = Array.from({ length: 50 }, (_, index) => batchTarget(`${index.toString(16).padStart(8, '0')}-1111-4111-8111-111111111111`, '1'));
    expect(prepareComplaintBatchStatusRequest(fifty, 'OPEN', complaintScope, complaintKey).targets).toHaveLength(50);
    for (const targets of [[], [...fifty, batchTarget()], [batchTarget(), batchTarget()], [{ ...batchTarget(), kind: 'NOTICE' as const }], [{ ...batchTarget(), ownership: 'SYSTEM' as const }]]) {
      expect(() => prepareComplaintBatchStatusRequest(targets, 'RESOLVED', complaintScope, complaintKey)).toThrow('INVALID_CAPTURE');
    }
    const request = batchRequest();
    for (const wrong of [
      { ...request, path: 'https://outside.example.test/' }, { ...request, path: request.path + '&cascade=true' }, { ...request, method: 'DELETE' },
      { ...request, dataScopeId: complaintScope.toUpperCase().replace('22222222', 'AAAAAAAA') }, { ...request, status: 'CLOSED' },
      { ...request, targets: [...request.targets].reverse() }, { ...request, targets: request.targets.slice(1) },
      { ...request, headers: { ...request.headers, 'If-Match': batchTarget().actionTag } },
      { ...request, body: request.body.replace('RESOLVED', 'OPEN') },
    ]) expect(() => complaintBatchStatusDestination(wrong as ComplaintBatchStatusRequest)).toThrow('INVALID_CAPTURE');
  });

  it('keeps missing-tag428 and invalid-string-tag412 separate from complete schema400 including duplicate decoded fields', () => {
    const cases: [string, number][] = [
      [body([{ id: complaintId }]), 428], [body([{ ...pair(), actionTag: `W/${pair().actionTag}` }]), 412],
      [body([{ ...pair(), actionTag: 'bad' }, { id: batchSecondId }]), 428],
      [body([{ id: batchSecondId }, { ...pair(), actionTag: 'bad' }]), 428],
      [body([{ ...pair(), actionTag: batchTarget(batchSecondId).actionTag }]), 412], [body([{ ...pair(), actionTag: batchTarget(complaintId, '9223372036854775808').actionTag }]), 412],
      [body([{ ...pair(), actionTag: null }]), 400], [body([{ ...pair(), actionTag: 7 }]), 400], [body([pair(), pair()]), 400],
      [body([]), 400], [body([pair()], { action: 'DELETE' }), 400], [body([pair()], { status: 'CLOSED' }), 400],
      [body([pair()], { actor: 'caller' }), 400], [body([{ ...pair(), version: 7 }]), 400],
      [body([{ id: complaintId }]).replace('"status":', '"status":"OPEN","statu\\u0073":'), 400],
      [body([pair()]).replace('"actionTag":', '"actionTag":"bad","action\\u0054ag":'), 400],
      [body([pair()]).replace('"RESOLVED"', '"\\ud800"'), 400], [body([pair()]).slice(0, -1) + ',}', 400],
      ['\uFEFF' + body([pair()]), 400], [body([pair()]) + '{}', 400],
    ];
    for (const [raw, status] of cases) {
      try { capture(raw); throw new Error('Accepted malformed fixture.'); }
      catch (error) { expect(error).toBeInstanceOf(ComplaintBatchStatusBodyError); expect((error as ComplaintBatchStatusBodyError).status).toBe(status); }
    }
    const raw = body([pair()]);
    expect(capture(raw.padEnd(32_768, ' ')).body.length).toBe(32_768);
    expect(() => capture(raw.padEnd(32_769, ' '))).toThrow(ComplaintBatchStatusBodyError);
  });

  it('verifies every exact numeric Long successor in canonical target order, independently of receipt metadata', async () => {
    const request = batchRequest();
    const valid = await metadata();
    for (const consumed of [null, 'true']) {
      const result = decodeComplaintBatchStatusOutcome(request, { ...valid, consumed });
      expect(result).toEqual({ kind: 'batch-applied', items: [{ id: complaintId, version: '9007199254740993' }, { id: batchSecondId, version: '9223372036854775807' }] });
      expect(Object.isFrozen(result)).toBe(true);
      if (result.kind === 'batch-applied') { expect(Object.isFrozen(result.items)).toBe(true); expect(result.items.every(Object.isFrozen)).toBe(true); }
    }
    const reordered = batchAck().replace(/\{"id":"([^"]+)","version":([0-9]+)\}/g, '{"version":$2,"id":"$1"}');
    expect(decodeComplaintBatchStatusOutcome(request, { ...valid, body: bytes(reordered) }).kind).toBe('batch-applied');
  });

  it('never confirms missing, extra, duplicate, reordered, stale or rounded members or partial/alternate success envelopes', async () => {
    const request = batchRequest(), valid = await metadata(), raw = batchAck();
    const first = `{"id":"${complaintId}","version":9007199254740993}`;
    const second = `{"id":"${batchSecondId}","version":9223372036854775807}`;
    for (const wrong of [
      '{"items":[]}', `{"items":[${first}]}`, `{"items":[${first},${first}]}`, `{"items":[${second},${first}]}`,
      `{"items":[${first},${second},${second}]}`, raw.replace(complaintId, complaintKey), raw.slice(0, -1),
      raw.replace('9007199254740993', '9007199254740992'), raw.replace('9007199254740993', '"9007199254740993"'),
      raw.replace('9007199254740993', '9.007199254740993e15'), raw.replace('9007199254740993', '01'),
      raw.replace('9223372036854775807', '9223372036854775808'), raw.replace('"version":', '"version":1,"ver\\u0073ion":'),
      raw.replace('"items":', '"items":[],"item\\u0073":'), raw.slice(0, -1) + ',"partial":true}', '\uFEFF' + raw,
    ]) expect(() => decodeComplaintBatchStatusOutcome(request, { ...valid, body: bytes(wrong) })).toThrow('UNCONFIRMED_RESPONSE');
    for (const response of [
      { ...valid, status: 207 }, { ...valid, status: 202 }, { ...valid, status: 204, body: new Uint8Array() },
      { ...valid, etag: batchTarget().actionTag }, { ...valid, location: '/partial' }, { ...valid, contract: '1, 1' },
      { ...valid, consumed: 'true, true' }, { ...valid, contentType: 'text/plain' }, { ...valid, body: new Uint8Array(32_769) },
    ]) expect(() => decodeComplaintBatchStatusOutcome(request, response)).toThrow('UNCONFIRMED_RESPONSE');
  });

  it('uses the existing terminal-receipt and unknown503 rules without inventing partial status results', async () => {
    const request = batchRequest();
    expect(decodeComplaintBatchStatusOutcome(request, await metadata(problemResponse('PRECONDITION_FAILED', 412)))).toEqual({ kind: 'unknown' });
    expect(decodeComplaintBatchStatusOutcome(request, await metadata(problemResponse('PRECONDITION_FAILED', 412, { 'X-Kira-Admin-Step-Up-Consumed': 'true' })))).toEqual({ kind: 'rejected', code: 'PRECONDITION_FAILED' });
    expect(decodeComplaintBatchStatusOutcome(request, await metadata(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true' })))).toEqual({ kind: 'unknown' });
  });
});

describe('closed atomic DELETE batch wire alongside strict STATUS', () => {
  const deletionBody = (targets: unknown, extra: Record<string, unknown> = {}) => JSON.stringify({ action: 'DELETE', targets, ...extra });
  const captureDelete = (raw: string) => captureComplaintBatchDeleteRequest(raw, complaintScope, complaintKey);

  it('captures paired sorted DELETE targets including Long.MAX_VALUE and keeps one-target DELETE a body-bearing POST', async () => {
    const source = [batchTarget(batchSecondId, '9223372036854775807'), batchTarget()];
    const request = prepareComplaintBatchDeleteRequest(source, complaintScope, complaintKey);
    const original = request.body;
    expect(request.action).toBe('DELETE'); expect('status' in request).toBe(false);
    expect(request.targets.map(({ id, baseVersion }) => [id, baseVersion])).toEqual([[complaintId, '9007199254740992'], [batchSecondId, '9223372036854775807']]);
    expect(original).toBe(deletionBody([pair(), { id: batchSecondId, actionTag: batchTarget(batchSecondId, '9223372036854775807').actionTag }]));
    Object.assign(source[0], batchTarget(complaintId, '1')); source.reverse();
    expect(request.body).toBe(original);
    for (const value of [request, request.headers, request.targets, ...request.targets]) expect(Object.isFrozen(value)).toBe(true);
    const raw = ` \n${deletionBody([...request.targets].reverse().map(({ id, actionTag }) => ({ actionTag, id })))}\t`;
    expect(captureComplaintBatchRequest(raw, complaintScope, complaintKey)).toMatchObject({ action: 'DELETE', body: raw, targets: request.targets });
    expect(complaintBatchDestination(request)).toBe(`/api/backend/complaints/batch?dataScopeId=${complaintScope}`);
    const one = prepareComplaintBatchDeleteRequest([batchTarget('12345678-1234-1234-1234-123456789abc', '9223372036854775807')], complaintScope, complaintKey);
    expect(one.method).toBe('POST'); expect(one.targets).toHaveLength(1); expect(one.headers).not.toHaveProperty('If-Match');
    expect(decodeComplaintBatchOutcome(one, await metadata(deleteBatchResponse(one)))).toEqual({ kind: 'batch-deleted', items: [{ id: one.targets[0].id }] });
    expect(() => capture(one.body)).toThrow(ComplaintBatchStatusBodyError);
    expect(() => captureDelete(batchRequest().body)).toThrow(ComplaintBatchBodyError);
    for (const wrong of [
      { ...request, action: 'STATUS' }, { ...request, status: 'RESOLVED' }, { ...request, method: 'DELETE' },
      { ...request, body: batchRequest().body }, { ...request, targets: [...request.targets].reverse() },
      { ...request, headers: { ...request.headers, 'If-Match': request.targets[0].actionTag } },
    ]) expect(() => complaintBatchDestination(wrong as ComplaintBatchRequest)).toThrow('INVALID_CAPTURE');
  });

  it('keeps DELETE1–50 and complete structural400 before missing428 or invalid-tag412 without widening STATUS', () => {
    const fifty = Array.from({ length: 50 }, (_, index) => batchTarget(`${index.toString(16).padStart(8, '0')}-1111-1111-1111-111111111111`, '1'));
    expect(prepareComplaintBatchDeleteRequest(fifty, complaintScope, complaintKey).targets).toHaveLength(50);
    for (const targets of [[], [...fifty, batchTarget()], [batchTarget(), batchTarget()], [{ ...batchTarget(), kind: 'NOTICE' as const }], [{ ...batchTarget(), ownership: 'SYSTEM' as const }]]) {
      expect(() => prepareComplaintBatchDeleteRequest(targets, complaintScope, complaintKey)).toThrow('INVALID_CAPTURE');
    }
    const cases: [string, number][] = [
      [deletionBody([{ id: complaintId }]), 428], [deletionBody([{ ...pair(), actionTag: 'bad' }, { id: batchSecondId }]), 428],
      [deletionBody([{ id: batchSecondId }, { ...pair(), actionTag: 'bad' }]), 428],
      [deletionBody([{ ...pair(), actionTag: `W/${pair().actionTag}` }]), 412],
      [deletionBody([{ ...pair(), actionTag: batchTarget(batchSecondId).actionTag }]), 412],
      [deletionBody([{ ...pair(), actionTag: batchTarget(complaintId, '9223372036854775808').actionTag }]), 412],
      [deletionBody([{ ...pair(), actionTag: null }]), 400], [deletionBody([pair(), pair()]), 400],
      [deletionBody([{ id: complaintId }], { status: 'RESOLVED' }), 400], [deletionBody([{ id: complaintId }], { cascade: true }), 400],
      [deletionBody([{ ...pair(), ownerId: complaintScope }]), 400], [deletionBody([pair()], { action: 'STATUS' }), 400],
      [deletionBody([{ id: complaintId }]).replace('"action":', '"action":"DELETE","acti\\u006fn":'), 400],
      [deletionBody([pair()]).replace('"actionTag":', '"actionTag":"bad","action\\u0054ag":'), 400],
      [deletionBody([pair()]) + '{}', 400], ['\uFEFF' + deletionBody([pair()]), 400],
    ];
    for (const [raw, status] of cases) {
      try { captureDelete(raw); throw new Error('Accepted malformed fixture.'); }
      catch (error) { expect(error).toBeInstanceOf(ComplaintBatchBodyError); expect((error as ComplaintBatchBodyError).status).toBe(status); }
    }
    // A strict STATUS entrypoint rejects the other action structurally, before that action's missing tags.
    try { capture(deletionBody([{ id: complaintId }])); throw new Error('Accepted DELETE through STATUS.'); }
    catch (error) { expect(error).toBeInstanceOf(ComplaintBatchBodyError); expect((error as ComplaintBatchBodyError).status).toBe(400); }
    const raw = deletionBody([pair()]);
    expect(captureDelete(raw.padEnd(32_768, ' ')).body).toHaveLength(32_768);
    expect(() => captureDelete(raw.padEnd(32_769, ' '))).toThrow(ComplaintBatchBodyError);
  });

  it('requires a complete canonical ID-only200 ACK and never substitutes STATUS versions, single204 or a partial result', async () => {
    const request = deleteBatchRequest(), valid = await metadata(deleteBatchResponse()), raw = deleteBatchAck();
    const result = decodeComplaintBatchOutcome(request, valid);
    expect(result).toEqual({ kind: 'batch-deleted', items: [{ id: complaintId }, { id: batchSecondId }] });
    expect(Object.isFrozen(result)).toBe(true);
    if (result.kind === 'batch-deleted') { expect(Object.isFrozen(result.items)).toBe(true); expect(result.items.every(Object.isFrozen)).toBe(true); }
    const first = `{"id":"${complaintId}"}`, second = `{"id":"${batchSecondId}"}`;
    for (const wrong of [
      '{"items":[]}', `{"items":[${first}]}`, `{"items":[${first},${first}]}`, `{"items":[${second},${first}]}`,
      `{"items":[${first},${second},${second}]}`, raw.replace(complaintId, complaintKey), batchAck(),
      raw.replace('"id":', '"id":"bad","i\\u0064":'), raw.replace('"items":', '"items":[],"item\\u0073":'),
      raw.slice(0, -1) + ',"partial":true}', raw + '{}', '\uFEFF' + raw,
    ]) expect(() => decodeComplaintBatchOutcome(request, { ...valid, body: bytes(wrong) })).toThrow('UNCONFIRMED_RESPONSE');
    expect(() => decodeComplaintBatchStatusOutcome(batchRequest(), valid)).toThrow('UNCONFIRMED_RESPONSE');
    expect(() => decodeComplaintBatchStatusOutcome(request as unknown as ComplaintBatchStatusRequest, valid)).toThrow('UNCONFIRMED_RESPONSE');
    for (const response of [
      { ...valid, status: 204, contentType: null, body: new Uint8Array() }, { ...valid, status: 207 }, { ...valid, status: 202 },
      { ...valid, etag: '"aggregate"' }, { ...valid, location: '/partial' }, { ...valid, body: new Uint8Array(32_769) },
    ]) expect(() => decodeComplaintBatchOutcome(request, response)).toThrow('UNCONFIRMED_RESPONSE');
    expect(decodeComplaintBatchOutcome(request, await metadata(problemResponse('SERVICE_UNAVAILABLE', 503, { 'X-Kira-Admin-Step-Up-Consumed': 'true' })))).toEqual({ kind: 'unknown' });
    expect(decodeComplaintBatchOutcome(request, await metadata(problemResponse('PRECONDITION_FAILED', 412, { 'X-Kira-Admin-Step-Up-Consumed': 'true' })))).toEqual({ kind: 'rejected', code: 'PRECONDITION_FAILED' });
  });
});
