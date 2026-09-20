import { backendUrl } from '@/lib/server-config';
import { readAdminSession, sessionFailure } from '@/lib/server-session';
import { isSessionSelector, mediaGenerationQuery, sessionGenerationHeader } from '@/lib/session-contract';

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) return Response.json({ detail: 'Invalid media id.' }, { status: 400 });
  const query = new URL(request.url).search;
  const header = request.headers.get(sessionGenerationHeader);
  const generation = query ? query.slice(`?${mediaGenerationQuery}=`.length) : header;
  if (query && (!isSessionSelector(generation) || query !== `?${mediaGenerationQuery}=${generation}` || header !== null && header !== generation)) {
    return Response.json({ detail: 'Invalid media session selector.' }, { status: 400 });
  }
  let session;
  try { session = readAdminSession(request.headers, generation); } catch (error) { return sessionFailure(error); }
  const upstream = await fetch(`${backendUrl}/api/v1/tutorial-media/${encodeURIComponent(id)}`, {
    headers: { Authorization: `Bearer ${session.token}` },
    cache: 'no-store', redirect: 'manual',
  });
  const headers = new Headers();
  for (const name of ['content-type', 'content-length', 'etag', 'cache-control']) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers });
}
