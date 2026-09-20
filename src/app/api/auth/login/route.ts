import { randomBytes } from 'node:crypto';

import { NextResponse } from 'next/server';

import { authenticationIdentityHeaders } from '@/lib/server-client-ip';
import { adminComplaintStepUpCookie, adminCsrfCookie, adminStepUpCookie, adminTokenCookie, backendUrl } from '@/lib/server-config';
import { requireSameOrigin } from '@/lib/server-security';

type LoginResponse = { accessToken: string; expiresInSeconds: number; role: string };

export async function POST(request: Request) {
  const rejected = await requireSameOrigin(request);
  if (rejected) return rejected;
  const body = await request.text();
  const upstream = await fetch(`${backendUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...authenticationIdentityHeaders(request),
    },
    body,
    cache: 'no-store',
  });
  const payload = await upstream.text();
  if (!upstream.ok) {
    return new Response(payload, { status: upstream.status, headers: { 'Content-Type': upstream.headers.get('content-type') ?? 'application/problem+json' } });
  }
  const login = JSON.parse(payload) as LoginResponse;
  if (login.role !== 'ADMIN') {
    return NextResponse.json({ detail: 'This dashboard requires an administrator account.' }, { status: 403 });
  }
  const response = NextResponse.json({ role: login.role, expiresInSeconds: login.expiresInSeconds });
  response.cookies.set(adminTokenCookie, login.accessToken, {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: login.expiresInSeconds,
  });
  response.cookies.set(adminCsrfCookie, randomBytes(32).toString('base64url'), {
    httpOnly: false,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: login.expiresInSeconds,
  });
  for (const name of [adminStepUpCookie, adminComplaintStepUpCookie]) {
    response.cookies.set(name, '', {
      httpOnly: true, sameSite: 'strict', secure: process.env.NODE_ENV === 'production',
      path: '/api/backend', expires: new Date(0), maxAge: 0,
    });
  }
  return response;
}
