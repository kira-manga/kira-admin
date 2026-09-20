import { NextResponse } from 'next/server';

import { adminRouteAllowed, isMutatingMethod, routeNeedsStepUp } from '@/lib/admin-route-policy';
import { proxyComplaintMutation } from '@/lib/server-complaint-mutation';
import { proxyComplaintRead } from '@/lib/server-complaint-read';
import { backendUrl } from '@/lib/server-config';
import { requireCsrf, requireSameOrigin } from '@/lib/server-security';
import { readAdminProof, readAdminSession, retireProofCookie, sessionFailure, type AdminProofCookie } from '@/lib/server-session';

const upstreamTimeoutMs = 65_000;
const historyCursorHeader = 'X-Kira-History-Next-Before';
export const dynamic = 'force-dynamic';

function historyCursorMaximum(path: string[]) {
  if (path.length === 1 && path[0] === 'documents') return '9223372036854775807';
  if (path.length === 3 && path[0] === 'sources' && path[1] && path[2] === 'revisions') return '2147483647';
  return null;
}

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || !adminRouteAllowed(path, request.method)) {
    return Response.json({ detail: 'Admin route is not allowed.' }, { status: 404 });
  }
  if (path[0] === 'complaints' && request.method === 'PATCH') return proxyComplaintMutation(request, path);
  if (path[0] === 'complaints') return proxyComplaintRead(request, path);
  const incomingUrl = new URL(request.url);
  if (isMutatingMethod(request.method)) {
    const rejected = await requireSameOrigin(request);
    if (rejected) return rejected;
  }
  let session;
  let proof: AdminProofCookie | undefined;
  const sourceMutation = routeNeedsStepUp(path, request.method);
  try {
    session = readAdminSession(request.headers);
    if (isMutatingMethod(request.method)) {
      const rejected = await requireCsrf(request, session);
      if (rejected) return rejected;
    }
    if (sourceMutation) proof = readAdminProof(request.headers, session, 'source-admin-mutation');
  } catch (error) { return sessionFailure(error); }

  const upstreamUrl = `${backendUrl}/api/v1/admin/${path.map(encodeURIComponent).join('/')}${incomingUrl.search}`;
  const headers = new Headers({
    Authorization: `Bearer ${session.token}`,
    Accept: 'application/json, application/problem+json',
  });
  for (const name of ['content-type', 'if-match']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (proof) headers.set('X-Kira-Admin-Step-Up', proof.token);

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(upstreamTimeoutMs)]),
      redirect: 'manual',
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
  if (request.method === 'GET' && upstream.ok) {
    const maximum = historyCursorMaximum(path);
    const cursor = upstream.headers.get(historyCursorHeader);
    // Length/lexical comparison is lossless for canonical decimals, including Long.
    // A repeated header is comma-combined by Headers.get and fails the scalar check.
    if (maximum && cursor && cursor.length <= maximum.length && /^[1-9][0-9]*$/.test(cursor)
      && (cursor.length < maximum.length || cursor <= maximum)) {
      responseHeaders.set(historyCursorHeader, cursor);
    }
  }
  const response = new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  // These exact backend handlers consume source approval before a direct 200. All other
  // outcomes (including ambiguous post-consumption failures) retain only the captured P.
  // Complaint historical consumed metadata is deliberately not a source-consumption signal.
  if (sourceMutation && proof && upstream.status === 200 && !upstream.redirected) retireProofCookie(response, proof);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
