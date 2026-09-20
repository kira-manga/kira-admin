import { NextResponse } from 'next/server';

import { requireCsrf, requireSameOrigin } from '@/lib/server-security';
import { readAdminSession, retireCapturedCookies, sessionFailure } from '@/lib/server-session';

export async function POST(request: Request) {
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return originFailure;
  try {
    const session = readAdminSession(request.headers);
    const rejected = await requireCsrf(request, session);
    if (rejected) return rejected;
    const response = NextResponse.json({ ok: true }, { headers: { 'Cache-Control': 'no-store, no-transform' } });
    retireCapturedCookies(response, session.cookies, session.generation);
    return response;
  } catch (error) { return sessionFailure(error); }
}
