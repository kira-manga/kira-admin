import { NextResponse } from 'next/server';

import { adminCsrfCookie, adminStepUpCookie, adminTokenCookie } from '@/lib/server-config';
import { requireCsrf } from '@/lib/server-security';

export async function POST(request: Request) {
  const rejected = await requireCsrf(request);
  if (rejected) return rejected;
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(adminTokenCookie);
  response.cookies.delete(adminCsrfCookie);
  response.cookies.delete(adminStepUpCookie);
  return response;
}
