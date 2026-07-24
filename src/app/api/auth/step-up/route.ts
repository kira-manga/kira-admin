import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { adminStepUpCookie, adminTokenCookie, backendUrl } from '@/lib/server-config';
import { requireCsrf } from '@/lib/server-security';

type StepUpResponse = { token: string; expiresAt: string; scope: string };

export async function POST(request: Request) {
  const rejected = await requireCsrf(request);
  if (rejected) return rejected;
  const token = (await cookies()).get(adminTokenCookie)?.value;
  if (!token) return NextResponse.json({ detail: 'Not signed in.' }, { status: 401 });
  const upstream = await fetch(`${backendUrl}/api/v1/admin/step-up`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      Accept: 'application/json, application/problem+json',
    },
    body: await request.text(),
    cache: 'no-store',
    signal: AbortSignal.timeout(15_000),
  });
  if (!upstream.ok) {
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: { 'Content-Type': upstream.headers.get('content-type') ?? 'application/problem+json' },
    });
  }
  const proof = await upstream.json() as StepUpResponse;
  const ttl = Math.max(1, Math.min(900, Math.floor((Date.parse(proof.expiresAt) - Date.now()) / 1000)));
  const response = NextResponse.json({ expiresAt: proof.expiresAt, scope: proof.scope });
  response.cookies.set(adminStepUpCookie, proof.token, {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/api/backend',
    maxAge: ttl,
  });
  response.headers.set('Cache-Control', 'no-store');
  return response;
}
