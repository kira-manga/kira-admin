import { describe, expect, it } from 'vitest';
import { createComplaintContentDraft, prepareComplaintContentEdit, type PreparedComplaintContentEdit } from './complaint-content-editor';
import { ComplaintContentWireError, decodeComplaintContentApplied, prepareComplaintContentRequest } from './complaint-content-wire';

const id = '12345678-1234-5234-8234-123456789abc';
const scope = 'a9439d39-0ef2-4d30-8eb6-324486a9d36e';
const key = 'd9439d39-0ef2-4d30-8eb6-324486a9d36e';
const tag = (version: string) => `"complaint-${id}-v${version}"`;
const bytes = (text: string) => new TextEncoder().encode(text);

function capture(version = '9007199254740992', variant: 'REPORT' | 'REPLY' | 'notice-reply' = 'REPORT') {
  const draft = createComplaintContentDraft(variant === 'notice-reply'
    ? { variant: 'notice-reply', kind: 'REPLY', id, actionTag: tag(version), content: { body: 'Edited reply' } }
    : { variant: 'ordinary', kind: variant, id, actionTag: tag(version), content: { type: 'CUSTOM', subject: 'Edited subject', body: 'Edited body' } });
  if (!draft) throw new Error('Missing draft.');
  return prepareComplaintContentEdit(draft, key);
}

function response(version = '9007199254740993') {
  return { status: 200, contentType: 'application/json', contract: '1', etag: tag(version), body: bytes(`{"id":"${id}","version":${version}}`) };
}

function rejects(action: () => unknown, reason: 'INVALID_CAPTURE' | 'UNCONFIRMED_RESPONSE') {
  try {
    action();
  } catch (error) {
    expect(error).toBeInstanceOf(ComplaintContentWireError);
    expect(error).toMatchObject({ reason });
    expect(String(error)).toBe(`ComplaintContentWireError: Complaint content: ${reason}.`);
    expect(error).not.toHaveProperty('cause');
    return;
  }
  throw new Error('Expected refusal.');
}

describe('dormant Admin content wire boundary', () => {
  it('preserves the exact detached key, target, tag and canonical content for all editable variants', () => {
    for (const variant of ['REPORT', 'REPLY', 'notice-reply'] as const) {
      const saved = capture('9223372036854775806', variant);
      const before = JSON.stringify(saved);
      const request = prepareComplaintContentRequest(saved, scope);
      expect(request).toEqual({
        method: 'PATCH', path: `/api/v1/admin/complaints/${id}/content?dataScopeId=${scope}`,
        targetId: id, dataScopeId: scope, baseVersion: '9223372036854775806',
        headers: { 'Content-Type': 'application/json', 'X-Kira-Complaint-Contract': '1', 'X-Kira-Idempotency-Key': key, 'If-Match': tag('9223372036854775806') },
        body: JSON.stringify(saved.content),
      });
      expect(Object.isFrozen(request)).toBe(true);
      expect(Object.isFrozen(request.headers)).toBe(true);
      expect(JSON.stringify(saved)).toBe(before);
      expect(prepareComplaintContentRequest(saved, scope)).toEqual(request);
      expect(request.headers).not.toHaveProperty('X-Kira-Admin-Step-Up');
      expect(JSON.parse(request.body)).toEqual(saved.content);
    }
  });

  it('encodes legal escaped/Unicode content but never silently normalizes a saved intent', () => {
    const draft = createComplaintContentDraft({ variant: 'ordinary', kind: 'REPORT', id, actionTag: tag('1'), content: { type: 'CUSTOM', subject: '😀'.repeat(200), body: '\\"\n\t'.repeat(250) } });
    if (!draft) throw new Error('Missing draft.');
    const saved = prepareComplaintContentEdit(draft, key);
    const request = prepareComplaintContentRequest(saved, scope);
    expect(bytes(request.body).byteLength).toBeLessThanOrEqual(16_384);
    expect(JSON.parse(request.body)).toEqual(saved.content);
    const forged = { ...saved, content: { ...saved.content, body: ' silently normalized ' } } as PreparedComplaintContentEdit;
    rejects(() => prepareComplaintContentRequest(forged, scope), 'INVALID_CAPTURE');
  });

  it('refuses scope/path injection, LIVE scope, invalid keys and weak/wrong/overflowing preconditions', () => {
    const saved = capture();
    for (const invalid of [scope.toUpperCase(), `${scope}&other=true`, '00000000-0000-0000-0000-000000000000', id, `${scope}\n`]) {
      rejects(() => prepareComplaintContentRequest(saved, invalid), 'INVALID_CAPTURE');
    }
    for (const actionTag of [`W/${tag('1')}`, '*', tag('0'), tag('01'), tag('9223372036854775808'), `${tag('1')}\n`, tag('1').replace(id, key)]) {
      const forged = { ...saved, base: { ...saved.base, actionTag } } as PreparedComplaintContentEdit;
      rejects(() => prepareComplaintContentRequest(forged, scope), 'INVALID_CAPTURE');
    }
    rejects(() => prepareComplaintContentRequest({ ...saved, idempotencyKey: id }, scope), 'INVALID_CAPTURE');
    const forgedTarget = { ...saved, base: { ...saved.base, id: `${id}/status` } } as PreparedComplaintContentEdit;
    rejects(() => prepareComplaintContentRequest(forgedTarget, scope), 'INVALID_CAPTURE');
  });

  it('decodes numeric Longs exactly through Long.MAX_VALUE and binds target, next version and strong ETag', () => {
    for (const [previous, next] of [['1', '2'], ['9007199254740992', '9007199254740993'], ['9223372036854775806', '9223372036854775807']]) {
      const request = prepareComplaintContentRequest(capture(previous), scope);
      const decoded = decodeComplaintContentApplied(request, response(next));
      expect(decoded).toEqual({ id, version: next, actionTag: tag(next) });
      expect(Object.isFrozen(decoded)).toBe(true);
      expect(decodeComplaintContentApplied(request, { ...response(next), contentType: 'application/json; charset=UTF-8', body: bytes(` \n{ "version": ${next}, "id": "${id}" }\t`) })).toEqual(decoded);
      rejects(() => decodeComplaintContentApplied(request, { ...response(next), etag: tag(previous) }), 'UNCONFIRMED_RESPONSE');
      rejects(() => decodeComplaintContentApplied(request, { ...response(next), etag: `W/${tag(next)}` }), 'UNCONFIRMED_RESPONSE');
    }
    const request = prepareComplaintContentRequest(capture(), scope);
    rejects(() => decodeComplaintContentApplied(request, response('9007199254740992')), 'UNCONFIRMED_RESPONSE');
    rejects(() => decodeComplaintContentApplied(request, response('9007199254740994')), 'UNCONFIRMED_RESPONSE');
    rejects(() => decodeComplaintContentApplied(request, { ...response(), body: bytes(`{"id":"${key}","version":9007199254740993}`) }), 'UNCONFIRMED_RESPONSE');
  });

  it('never turns malformed, duplicate, oversized or non-success responses into confirmed applied results', () => {
    const request = prepareComplaintContentRequest(capture(), scope);
    const before = JSON.stringify(request);
    const malformed = [
      `{"id":"${id}","version":"9007199254740993"}`,
      `{"id":"${id}","version":9007199254740993,"version":9007199254740992}`,
      `{"id":"${id}","id":"${key}","version":9007199254740993}`,
      `{"id":"${id}","version":9007199254740993,"outcome":"APPLIED"}`,
      `{"id":"${id}","version":9.007199254740993e15}`,
      `{"id":"${id}","version":09007199254740993}`,
      `{"id":"${id}","version":9223372036854775808}`,
      `[{"id":"${id}","version":9007199254740993}]`,
      `{"id":"${id}","version":9007199254740993}null`,
      `{"id":"${id}","version":9007199254740993}${' '.repeat(256)}`,
      '\uFEFF{"id":"' + id + '","version":9007199254740993}',
    ];
    for (const raw of malformed) rejects(() => decodeComplaintContentApplied(request, { ...response(), body: bytes(raw) }), 'UNCONFIRMED_RESPONSE');
    rejects(() => decodeComplaintContentApplied(request, { ...response(), body: new Uint8Array([0xff]) }), 'UNCONFIRMED_RESPONSE');
    for (const status of [0, 201, 204, 400, 401, 403, 409, 412, 429, 503]) {
      rejects(() => decodeComplaintContentApplied(request, { ...response(), status }), 'UNCONFIRMED_RESPONSE');
    }
    for (const contract of [null, '2', '1, 1']) rejects(() => decodeComplaintContentApplied(request, { ...response(), contract }), 'UNCONFIRMED_RESPONSE');
    for (const contentType of [null, 'text/html', 'application/problem+json', 'application/json; charset=iso-8859-1', 'application/json\n', 'application/json; charset=utf-8\r\n']) {
      rejects(() => decodeComplaintContentApplied(request, { ...response(), contentType }), 'UNCONFIRMED_RESPONSE');
    }
    rejects(() => decodeComplaintContentApplied(request, { ...response(), etag: null }), 'UNCONFIRMED_RESPONSE');
    expect(JSON.stringify(request)).toBe(before); // No key rotation, retry or success on ambiguity.
  });
});
