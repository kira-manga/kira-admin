import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

import { adminRouteAllowed, isComplaintDetailQuery, isMutatingMethod, routeNeedsStepUp } from '@/lib/admin-route-policy';
import { adminStepUpCookie, adminTokenCookie, backendUrl } from '@/lib/server-config';
import { requireCsrf } from '@/lib/server-security';

const upstreamTimeoutMs = 65_000;
const historyCursorHeader = 'X-Kira-History-Next-Before';
const complaintContractHeader = 'X-Kira-Complaint-Contract';

function complaintFailure(status: number) {
  return Response.json({ detail: 'Complaint detail could not be loaded.' }, { status, headers: { 'Cache-Control': 'no-store' } });
}

/** Detail-only bound, before returning any bytes; never parse/re-serialize a numeric Long. */
async function complaintDetailResponse(upstream: Response, signal: AbortSignal) {
  const discard = () => { void upstream.body?.cancel().catch(() => {}); };
  if (upstream.status !== 200) {
    discard();
    // Do not expose upstream problems, redirect locations, credentials or response cookies.
    return complaintFailure(upstream.status >= 400 && upstream.status <= 599 ? upstream.status : 502);
  }
  const contentType = upstream.headers.get('content-type');
  const contract = upstream.headers.get(complaintContractHeader);
  const etag = upstream.headers.get('etag');
  if (!upstream.body || upstream.redirected || !contentType || contentType.length > 128 || /[\r\n]/.test(contentType)
    || !/^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i.test(contentType) || contract !== '1'
    || etag !== null && (etag.length > 69 || /[\r\n]/.test(etag))) {
    discard();
    return complaintFailure(502);
  }
  const reader = upstream.body.getReader();
  const cancel = () => { void reader.cancel().catch(() => {}); };
  signal.addEventListener('abort', cancel, { once: true });
  try {
    const body = new Uint8Array(32_768);
    let length = 0;
    while (true) {
      if (signal.aborted) throw new Error('Complaint detail interrupted.');
      const next = await reader.read();
      if (signal.aborted) throw new Error('Complaint detail interrupted.');
      if (next.done) break;
      if (next.value.byteLength > body.length - length) throw new Error('Complaint detail exceeds its bound.');
      body.set(next.value, length);
      length += next.value.byteLength;
    }
    if (length === 0) throw new Error('Complaint detail is empty.');
    const headers = new Headers({ 'Content-Type': contentType, [complaintContractHeader]: contract, 'Cache-Control': 'no-store, no-transform' });
    if (etag !== null) headers.set('ETag', etag);
    return new Response(body.slice(0, length), { status: 200, headers });
  } catch {
    cancel();
    return complaintFailure(signal.aborted && signal.reason instanceof DOMException && signal.reason.name === 'TimeoutError' ? 504 : 502);
  } finally {
    signal.removeEventListener('abort', cancel);
    reader.releaseLock();
  }
}

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
  const complaintDetail = path[0] === 'complaints';
  const incomingUrl = new URL(request.url);
  if (complaintDetail && (!isComplaintDetailQuery(incomingUrl.search) || request.body !== null)) return complaintFailure(400);
  if (isMutatingMethod(request.method)) {
    const rejected = await requireCsrf(request);
    if (rejected) return rejected;
  }
  const cookieStore = await cookies();
  const token = cookieStore.get(adminTokenCookie)?.value;
  if (!token) return complaintDetail ? complaintFailure(401) : Response.json({ detail: 'Not signed in.' }, { status: 401 });

  const upstreamUrl = `${backendUrl}/api/v1/admin/${path.map(encodeURIComponent).join('/')}${incomingUrl.search}`;
  const headers = new Headers({
    Authorization: `Bearer ${token}`,
    Accept: 'application/json, application/problem+json',
  });
  for (const name of complaintDetail ? [] : ['content-type', 'if-match']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (complaintDetail) headers.set(complaintContractHeader, '1');
  if (routeNeedsStepUp(path)) {
    const proof = cookieStore.get(adminStepUpCookie)?.value;
    if (proof) headers.set('X-Kira-Admin-Step-Up', proof);
  }

  let upstream: Response;
  const complaintSignal = complaintDetail ? AbortSignal.any([request.signal, AbortSignal.timeout(upstreamTimeoutMs)]) : undefined;
  try {
    upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer(),
      cache: 'no-store',
      signal: complaintSignal ?? AbortSignal.any([request.signal, AbortSignal.timeout(upstreamTimeoutMs)]),
      ...(complaintDetail ? { redirect: 'manual' as const } : {}),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === 'TimeoutError';
    if (complaintDetail) return complaintFailure(timedOut ? 504 : 502);
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

  if (complaintSignal) return complaintDetailResponse(upstream, complaintSignal);

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
  if (routeNeedsStepUp(path)) response.cookies.delete(adminStepUpCookie);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
