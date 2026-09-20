import { timingSafeEqual } from 'node:crypto';

import { adminOrigin } from './server-config';
import type { AdminSessionCookie } from './server-session';

const csrfHeader = 'x-kira-csrf';

export async function requireSameOrigin(request: Request) {
  const origin = request.headers.get('origin');
  const expected = adminOrigin || new URL(request.url).origin;
  if (!origin || origin !== expected || request.headers.get('sec-fetch-site') === 'cross-site') {
    return Response.json({ detail: 'Cross-site request rejected.' }, { status: 403 });
  }
  return null;
}

export async function requireCsrf(request: Request, session: AdminSessionCookie) {
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return originFailure;
  const expected = session.csrfToken;
  const supplied = request.headers.get(csrfHeader);
  if (!expected || !supplied || !constantTimeEqual(expected, supplied)) {
    return Response.json({ detail: 'Invalid request token.' }, { status: 403 });
  }
  return null;
}

function constantTimeEqual(left: string, right: string) {
  if (left.length !== right.length) return false;
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
