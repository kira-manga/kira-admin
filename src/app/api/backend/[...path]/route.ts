import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { adminRouteAllowed, isMutatingMethod, routeNeedsStepUp } from '@/lib/admin-route-policy';
import { adminStepUpCookie, adminTokenCookie, backendUrl } from '@/lib/server-config';
import { requireCsrf } from '@/lib/server-security';

const upstreamTimeoutMs = 65_000;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || !adminRouteAllowed(path, request.method)) {
    return Response.json({ detail: 'Admin route is not allowed.' }, { status: 404 });
  }
  if (isMutatingMethod(request.method)) {
    const rejected = await requireCsrf(request);
    if (rejected) return rejected;
  }
  const cookieStore = await cookies();
  const token = cookieStore.get(adminTokenCookie)?.value;
  if (!token) return Response.json({ detail: 'Not signed in.' }, { status: 401 });

  const incomingUrl = new URL(request.url);
  const upstreamUrl = `${backendUrl}/api/v1/admin/${path.map(encodeURIComponent).join('/')}${incomingUrl.search}`;
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
    Accept: 'application/json, application/problem+json',
  });
  for (const name of ['content-type', 'if-match']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (routeNeedsStepUp(path)) {
    const proof = cookieStore.get(adminStepUpCookie)?.value;
    if (proof) headers.set('X-Kira-Admin-Step-Up', proof);
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(upstreamTimeoutMs)]),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError';
    console.error('Admin API proxy request failed.', {
      method: request.method,
      routeRoot: path[0],
      errorName: error instanceof Error ? error.name : 'UnknownError',
    });
    return Response.json(
      { detail: timedOut ? 'The production API timed out while processing the request.' : 'The production API could not be reached.' },
      { status: timedOut ? 504 : 502 },
    );
  }

  const responseHeaders = new Headers();
  for (const name of ['content-type', 'etag', 'cache-control']) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  const response = new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  if (routeNeedsStepUp(path)) response.cookies.delete(adminStepUpCookie);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
