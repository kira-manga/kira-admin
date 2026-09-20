import { prepareComplaintMutationRequest, type ComplaintMutationOperation, type ComplaintMutationRequest } from '../lib/complaint-mutation-wire';

// Synthetic TEST identities and exact existing backend encodings; never an activated target/account.
export const complaintId = '11111111-1111-4111-8111-111111111111';
export const complaintScope = '22222222-2222-4222-8222-222222222222';
export const complaintKey = '33333333-3333-4333-8333-333333333333';
export const grantA = 'aaaaaaaa-1111-4111-8111-111111111111';
export const grantB = 'bbbbbbbb-1111-4111-8111-111111111111';

export function mutationRequest(operation: ComplaintMutationOperation = 'status', body = operation === 'delete' ? '' : '{"status":"RESOLVED"}') {
  return prepareComplaintMutationRequest(operation, complaintId, complaintScope, complaintKey, `"complaint-${complaintId}-v9007199254740992"`, body);
}

export function deletedResponse(extra: HeadersInit = {}) {
  const headers = new Headers({ 'X-Kira-Complaint-Contract': '1', 'X-Kira-Admin-Step-Up-Consumed': 'true', 'Cache-Control': 'no-store, no-transform' });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return new Response(null, { status: 204, headers });
}

export function appliedResponse(request: ComplaintMutationRequest = mutationRequest(), extra: HeadersInit = {}) {
  const version = (BigInt(request.baseVersion) + BigInt(1)).toString();
  const headers = new Headers({
    'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1',
    ETag: `"complaint-${request.targetId}-v${version}"`, 'X-Kira-Admin-Step-Up-Consumed': 'true',
  });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return new Response(`{"id":"${request.targetId}","version":${version}}`, { headers });
}

export function problemResponse(code: string, status: number, extra: HeadersInit = {}) {
  const titles: Record<number, string> = { 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 409: 'Conflict', 412: 'Precondition Failed', 413: 'Payload Too Large', 415: 'Unsupported Media Type', 428: 'Precondition Required', 429: 'Too Many Requests', 500: 'Internal Server Error', 503: 'Service Unavailable' };
  const headers = new Headers({ 'Content-Type': 'application/problem+json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1',
    ...(status === 401 ? { 'WWW-Authenticate': 'Bearer realm="kira-complaints"' } : {}),
  });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return new Response(JSON.stringify({ type: 'about:blank', title: titles[status], status,
    errors: [{ code, message: 'Complaint request refused.' }],
  }), { status, headers });
}
