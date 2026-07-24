import { timingSafeEqual } from 'node:crypto';

import { cookies } from 'next/headers';

import { adminCsrfCookie } from './server-config';
import { adminOrigin } from './server-config';

const csrfHeader = 'x-kira-csrf';

export async function requireSameOrigin(request: Request) {
  const origin = request.headers.get('origin');
  const expected = adminOrigin || new URL(request.url).origin;
  if (!origin || origin !== expected || request.headers.get('sec-fetch-site') === 'cross-site') {
    return Response.json({ detail: 'Cross-site request rejected.' }, { status: 403 });
  }
  return null;
}

export async function requireCsrf(request: Request) {
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return originFailure;
  const expected = (await cookies()).get(adminCsrfCookie)?.value;
  const supplied = request.headers.get(csrfHeader);
  if (!expected || !supplied || !constantTimeEqual(expected, supplied)) {
    return Response.json({ detail: 'Invalid request token.' }, { status: 403 });
  }
  return null;
}

function constantTimeEqual(left: string, right: string) {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}
