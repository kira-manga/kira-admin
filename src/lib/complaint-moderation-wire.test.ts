import { describe, expect, it } from 'vitest';
import { decodeComplaintModerationApplied, prepareComplaintModerationRequest, type ComplaintModerationChange, type ComplaintModerationTarget } from './complaint-moderation-wire';
import { ComplaintMutationWireError } from './complaint-mutation-wire';

const id = '12345678-1234-5234-8234-123456789abc';
const scope = 'a9439d39-0ef2-4d30-8eb6-324486a9d36e';
const key = 'd9439d39-0ef2-4d30-8eb6-324486a9d36e';
const tag = (version: string) => `"complaint-${id}-v${version}"`;
const target: ComplaintModerationTarget = { id, kind: 'REPORT', ownership: 'INSTALLATION', actionTag: tag('9007199254740992') };

describe('Admin status, closure and single-delete request capture', () => {
  it('captures REPORT/REPLY deletion without prose or a cascade, and rejects forged NOTICE/ownership/tag inputs', () => {
    for (const kind of ['REPORT', 'REPLY'] as const) {
      const original = { ...target, kind };
      const request = prepareComplaintModerationRequest(original, { operation: 'delete' }, scope, key);
      expect(request).toEqual({
        method: 'DELETE', path: `/api/v1/admin/complaints/${id}?dataScopeId=${scope}`,
        targetId: id, dataScopeId: scope, baseVersion: '9007199254740992', body: '',
        headers: { 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Idempotency-Key': key, 'If-Match': target.actionTag },
      });
      original.actionTag = tag('2');
      expect(request.headers['If-Match']).toBe(target.actionTag);
      expect(Object.isFrozen(request)).toBe(true);
      expect(Object.isFrozen(request.headers)).toBe(true);
    }
    for (const forged of [
      { ...target, kind: 'NOTICE' }, { ...target, ownership: 'SYSTEM' }, { ...target, actionTag: '' },
      { ...target, actionTag: '*' }, { ...target, actionTag: `${target.actionTag}, ${target.actionTag}` },
      { ...target, actionTag: `W/${target.actionTag}` }, { ...target, actionTag: tag('9223372036854775808') },
      { ...target, actionTag: tag('01') }, { ...target, actionTag: '"complaint-00000000-0000-0000-0000-000000000000-v1"' },
    ]) expect(() => prepareComplaintModerationRequest(forged as ComplaintModerationTarget, { operation: 'delete' }, scope, key)).toThrow('INVALID_CAPTURE');
    expect(prepareComplaintModerationRequest({ ...target, actionTag: tag('9223372036854775807') }, { operation: 'delete' }, scope, key).baseVersion).toBe('9223372036854775807');
  });

  it('uses only the five mutable status targets and exact field-scoped bodies', () => {
    for (const status of ['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'] as const) {
      for (const kind of ['REPORT', 'REPLY'] as const) {
        const request = prepareComplaintModerationRequest({ ...target, kind }, { operation: 'status', status }, scope, key);
        expect(request).toEqual({
          method: 'PATCH', path: `/api/v1/admin/complaints/${id}/status?dataScopeId=${scope}`,
          targetId: id, dataScopeId: scope, baseVersion: '9007199254740992', body: JSON.stringify({ status }),
          headers: { 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Idempotency-Key': key, 'If-Match': target.actionTag },
        });
      }
    }
    for (const status of ['CLOSED', 'PINNED', 'UNKNOWN', 'resolved', 'RESOLVED\n']) {
      expect(() => prepareComplaintModerationRequest(target, { operation: 'status', status } as ComplaintModerationChange, scope, key)).toThrow(ComplaintMutationWireError);
    }
  });

  it('normalizes closure once with backend Unicode and 500-codepoint/2000-byte bounds', () => {
    const capture = (reason: string) => prepareComplaintModerationRequest(target, { operation: 'closure', reason }, scope, key);
    const request = capture('\u00a0\tResolved\r\nwith explanation\u3000');
    expect(request.path).toBe(`/api/v1/admin/complaints/${id}/closure?dataScopeId=${scope}`);
    expect(request.body).toBe(JSON.stringify({ reason: 'Resolved\nwith explanation' }));
    expect(JSON.parse(capture('😀'.repeat(500)).body)).toEqual({ reason: '😀'.repeat(500) });
    expect(JSON.parse(capture('\uFEFF').body)).toEqual({ reason: '\uFEFF' }); // Not Kotlin whitespace.
    for (const reason of ['', '\t\n\u3000', '😀'.repeat(501), 'a'.repeat(501), '\u0000secret', 'reason\r', '\u0085reason', '\ud800', '\udc00']) {
      expect(() => capture(reason)).toThrow('Complaint mutation: INVALID_CAPTURE.');
    }
  });

  it('refuses immutable/legacy targets, invalid identifiers and preconditions before describing a request', () => {
    const change = { operation: 'status', status: 'RESOLVED' } as const;
    for (const forged of [
      { ...target, kind: 'NOTICE', ownership: 'SYSTEM' },
      { ...target, ownership: 'LEGACY_UNCLAIMED' },
      { ...target, kind: 'UNKNOWN' },
      { ...target, id: `${id}/closure` },
      { ...target, actionTag: `W/${target.actionTag}` },
      { ...target, actionTag: tag('9223372036854775808') },
      { ...target, actionTag: `${target.actionTag}\n` },
    ]) {
      expect(() => prepareComplaintModerationRequest(forged as ComplaintModerationTarget, change, scope, key)).toThrow(ComplaintMutationWireError);
    }
    for (const [invalidScope, invalidKey] of [['00000000-0000-0000-0000-000000000000', key], [scope, id], [`${scope}&extra=1`, key], [scope, `${key}\n`]]) {
      expect(() => prepareComplaintModerationRequest(target, change, invalidScope, invalidKey)).toThrow(ComplaintMutationWireError);
    }
  });

  it('detaches and freezes the original key/tag/body and shares exact Long applied decoding without repairing ambiguity', () => {
    const originalTarget = { ...target };
    const change: ComplaintModerationChange = { operation: 'closure', reason: 'Resolved after investigation' };
    const request = prepareComplaintModerationRequest(originalTarget, change, scope, key);
    const before = JSON.stringify(request);
    originalTarget.actionTag = tag('2');
    (change as { reason: string }).reason = 'Different intent';
    expect(Object.isFrozen(request)).toBe(true);
    expect(Object.isFrozen(request.headers)).toBe(true);
    const response = {
      status: 200, contract: '1', contentType: 'application/json', etag: tag('9007199254740993'),
      body: new TextEncoder().encode(`{"id":"${id}","version":9007199254740993}`),
    };
    expect(decodeComplaintModerationApplied(request, response)).toEqual({ id, version: '9007199254740993', actionTag: response.etag });
    for (const ambiguous of [{ ...response, status: 503 }, { ...response, etag: target.actionTag }, { ...response, body: new Uint8Array() }]) {
      expect(() => decodeComplaintModerationApplied(request, ambiguous)).toThrow('Complaint mutation: UNCONFIRMED_RESPONSE.');
    }
    expect(JSON.stringify(request)).toBe(before);
    expect(request.headers).not.toHaveProperty('Authorization');
    expect(request.headers).not.toHaveProperty('X-Kira-Admin-Step-Up');
  });
});
