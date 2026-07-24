import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { adminCsrfCookie, adminTokenCookie, backendUrl } from '@/lib/server-config';

export async function GET() {
  const store = await cookies();
  const token = store.get(adminTokenCookie)?.value;
  const csrfToken = store.get(adminCsrfCookie)?.value;
  if (!token || !csrfToken) return NextResponse.json({ detail: 'Not signed in.' }, { status: 401 });
  const upstream = await fetch(`${backendUrl}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
    cache: 'no-store',
  });
  if (!upstream.ok) {
    const response = NextResponse.json({ detail: 'Your admin session has expired.' }, { status: 401 });
    response.cookies.delete(adminTokenCookie);
    return response;
  }
  const me = await upstream.json() as { role: string };
  if (me.role !== 'ADMIN') return NextResponse.json({ detail: 'Administrator access is required.' }, { status: 403 });
  return NextResponse.json({ ...me, csrfToken });
}
