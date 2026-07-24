import { cookies } from 'next/headers';

import { adminTokenCookie, backendUrl } from '@/lib/server-config';

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) return Response.json({ detail: 'Invalid media id.' }, { status: 400 });
  const token = (await cookies()).get(adminTokenCookie)?.value;
  const upstream = await fetch(`${backendUrl}/api/v1/tutorial-media/${encodeURIComponent(id)}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    cache: 'no-store',
  });
  const headers = new Headers();
  for (const name of ['content-type', 'content-length', 'etag', 'cache-control']) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers });
}
