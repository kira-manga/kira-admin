import { NextResponse } from 'next/server';

import { adminComplaintStepUpCookie, adminCsrfCookie, adminStepUpCookie, adminTokenCookie } from '@/lib/server-config';
import { requireCsrf } from '@/lib/server-security';

export async function POST(request: Request) {
  const rejected = await requireCsrf(request);
  if (rejected) return rejected;
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(adminTokenCookie);
  response.cookies.delete(adminCsrfCookie);
  for (const name of [adminStepUpCookie, adminComplaintStepUpCookie]) {
    response.cookies.set(name, '', {
      httpOnly: true, sameSite: 'strict', secure: process.env.NODE_ENV === 'production',
      path: '/api/backend', expires: new Date(0), maxAge: 0,
    });
  }
  return response;
}
