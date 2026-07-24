import { cookies } from 'next/headers';

import { adminTokenCookie, backendUrl } from '@/lib/server-config';

const allowedRoots = new Set(['tutorials', 'tutorial-categories', 'tutorial-media']);
const allowedMethods = new Set(['GET', 'POST', 'DELETE']);
const upstreamTimeoutMs = 65_000;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || !allowedRoots.has(path[0]) || !allowedMethods.has(request.method)) {
    return Response.json({ detail: 'Admin route is not allowed.' }, { status: 404 });
  }
  if (request.method === 'POST' && path[0] === 'tutorial-media') {
    return Response.json({ detail: 'Media uploads must use the dedicated upload route.' }, { status: 400 });
  }
  const token = (await cookies()).get(adminTokenCookie)?.value;
  if (!token) return Response.json({ detail: 'Not signed in.' }, { status: 401 });
  const incomingUrl = new URL(request.url);
  const upstreamUrl = `${backendUrl}/api/v1/admin/${path.map(encodeURIComponent).join('/')}${incomingUrl.search}`;
  const headers = new Headers({ Authorization: `Bearer ${token}`, Accept: 'application/json, application/problem+json' });
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('Content-Type', contentType);

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(upstreamTimeoutMs)]),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError';
    const cause = error instanceof Error && error.cause instanceof Error ? error.cause : null;
    console.error('Admin API proxy request failed.', {
      method: request.method,
      routeRoot: path[0],
      errorName: error instanceof Error ? error.name : 'UnknownError',
      errorMessage: error instanceof Error ? error.message : 'Unknown proxy error',
      causeName: cause?.name,
      causeMessage: cause?.message,
    });
    return Response.json(
      { detail: timedOut ? 'The production API timed out while processing the request.' : 'The production API could not be reached.' },
      { status: timedOut ? 504 : 502 },
    );
  }
  const responseHeaders = new Headers();
  const responseType = upstream.headers.get('content-type');
  if (responseType) responseHeaders.set('Content-Type', responseType);
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
