import { NextResponse } from 'next/server';

import { adminTokenCookie } from '@/lib/server-config';

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(adminTokenCookie);
  return response;
}
