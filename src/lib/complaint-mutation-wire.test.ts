import { describe, expect, it } from 'vitest';

import { appliedResponse, complaintId, complaintScope, mutationRequest, problemResponse } from '@/test/complaint-mutation-fixture';
import { complaintMutationDestination, complaintReceiptHeader, decodeComplaintMutationOutcome, validateComplaintMutationBody, type ComplaintMutationOperation, type ComplaintMutationRequest } from './complaint-mutation-wire';

async function metadata(response: Response) {
  return { status: response.status, contentType: response.headers.get('content-type'), contract: response.headers.get('X-Kira-Complaint-Contract'),
    etag: response.headers.get('etag'), consumed: response.headers.get(complaintReceiptHeader), challenge: response.headers.get('www-authenticate'),
    retryAfter: response.headers.get('retry-after'), body: new Uint8Array(await response.arrayBuffer()),
  };
}

describe('ordinary complaint connection wire, beyond the existing request/Long matrices', () => {
  it('checks the closed body without replacing original bytes and reconstructs only the BFF destination', () => {
    const body = ' {"reason":"  original\\r\\nreason  "} ';
    const request = mutationRequest('closure', body);
    validateComplaintMutationBody('closure', body);
    expect(complaintMutationDestination(request)).toBe(`/api/backend/complaints/${complaintId}/closure?dataScopeId=${complaintScope}`);
    expect(request.body).toBe(body);
    expect(Object.isFrozen(request.headers)).toBe(true);
    for (const wrong of [
      { ...request, path: 'https://outside.example.test/' }, { ...request, path: request.path + '&extra=1' },
      { ...request, method: 'POST' }, { ...request, baseVersion: '3' },
      { ...request, headers: { ...request.headers, Authorization: 'caller override' } },
    ]) expect(() => complaintMutationDestination(wrong as ComplaintMutationRequest)).toThrow('INVALID_CAPTURE');
  });

  it.each([
    ['status', '{"status":"OPEN","statu\\u0073":"RESOLVED"}'], ['status', '{"status":"OPEN","actor":"caller"}'],
    ['closure', '{"reason":null}'], ['content', '{"type":"CUSTOM","subject":"s","body":"b","extra":"x"}'],
    ['content', '{"body":"\\ud800"}'], ['closure', '{"reason":"\\u000b"}'], ['status', '{"status":"OPEN",}'],
    ['status', '["OPEN"]'], ['content', '\uFEFF{"body":"b"}'],
  ] as const)('refuses an ambiguous or non-closed %s body', (operation, body) => {
    expect(() => validateComplaintMutationBody(operation as ComplaintMutationOperation, body)).toThrow('INVALID_CAPTURE');
  });

  it('confirms applied from a complete ACK independently of historical consumption metadata', async () => {
    for (const consumed of [null, 'true']) {
      const response = appliedResponse();
      if (consumed === null) response.headers.delete(complaintReceiptHeader);
      expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(response))).toEqual({
        kind: 'applied', id: complaintId, version: '9007199254740993', actionTag: `"complaint-${complaintId}-v9007199254740993"`,
      });
    }
  });

  it('requires a receipt marker for business rejection, and never turns a post-receipt failure into a terminal outcome', async () => {
    for (const [code, status] of [['PRECONDITION_FAILED', 412], ['COMPLAINT_INVALID_TRANSITION', 409], ['COMPLAINT_NOT_FOUND', 404]] as const) {
      expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(problemResponse(code, status)))).toEqual({ kind: 'unknown' });
      expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(problemResponse(code, status, { [complaintReceiptHeader]: 'true' })))).toEqual({ kind: 'rejected', code });
    }
    for (const [code, status] of [['INTERNAL_ERROR', 500], ['SERVICE_UNAVAILABLE', 503]] as const) {
      expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(problemResponse(code, status, { [complaintReceiptHeader]: 'true' })))).toEqual({ kind: 'unknown' });
    }
  });

  it.each([
    ['ADMIN_STEP_UP_REQUIRED', 401, 'step-up-required'], ['UNAUTHORIZED', 401, 'unauthorized'], ['FORBIDDEN', 403, 'forbidden'],
    ['IDEMPOTENCY_KEY_REUSED', 409, 'key-reused'], ['IDEMPOTENCY_IN_PROGRESS', 409, 'in-progress'],
  ] as const)('recognizes %s without conflating it with a local KiraSession challenge', async (code, status, kind) => {
    const response = problemResponse(code, status, code === 'IDEMPOTENCY_IN_PROGRESS' ? { 'Retry-After': '1' } : {});
    expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(response))).toEqual({ kind });
  });

  it('recognizes the disabled404 as unavailable rather than a terminal target rejection', async () => {
    const response = new Response('{"type":"about:blank","title":"Not Found","status":404,"detail":"Not found."}', {
      status: 404, headers: { 'Content-Type': 'application/problem+json', 'X-Kira-Complaint-Contract': '1' },
    });
    expect(decodeComplaintMutationOutcome(mutationRequest(), await metadata(response))).toEqual({ kind: 'unavailable' });
  });

  it('refuses mismatched metadata, duplicate/extra problem fields, private diagnostics and incomplete bodies', async () => {
    const valid = await metadata(problemResponse('ADMIN_STEP_UP_REQUIRED', 401));
    const raw = new TextDecoder().decode(valid.body);
    const bytes = (value: string) => new TextEncoder().encode(value);
    for (const response of [
      { ...valid, challenge: null }, { ...valid, challenge: 'KiraSession realm="kira-admin-bff"' },
      { ...valid, contract: '1, 1' }, { ...valid, etag: '"extra"' }, { ...valid, consumed: 'true' },
      { ...valid, retryAfter: '1' }, { ...valid, contentType: 'application/json' },
      { ...valid, body: bytes(raw.slice(0, -1)) }, { ...valid, body: bytes(raw.replace('"status":401', '"status":401,"status":401')) },
      { ...valid, body: bytes(raw.replace('Complaint request refused.', 'private backend diagnostic')) },
      { ...valid, body: bytes(raw.slice(0, -1) + ',"extra":"x"}') }, { ...valid, body: new Uint8Array(32_769) },
      { ...valid, body: new Uint8Array([0xff]) },
    ]) expect(() => decodeComplaintMutationOutcome(mutationRequest(), response)).toThrow('UNCONFIRMED_RESPONSE');
    const inProgress = await metadata(problemResponse('IDEMPOTENCY_IN_PROGRESS', 409));
    for (const retryAfter of [null, '0', '2', '1, 1', '9999999']) {
      expect(() => decodeComplaintMutationOutcome(mutationRequest(), { ...inProgress, retryAfter })).toThrow('UNCONFIRMED_RESPONSE');
    }
  });
});
