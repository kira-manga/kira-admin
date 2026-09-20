import { NextResponse } from 'next/server';

import { authenticationIdentityHeaders } from '@/lib/server-client-ip';
import { backendUrl } from '@/lib/server-config';
import { requireCsrf, requireSameOrigin } from '@/lib/server-security';
import { issueAdminProof, readAdminSession, requireCookieCapacity, sessionFailure, setAuthenticationCookie } from '@/lib/server-session';
import { isFutureExpiry, isSessionSelector } from '@/lib/session-contract';
import { isStepUpScope } from '@/lib/step-up-contract';

export const dynamic = 'force-dynamic';
const timeoutMs = 15_000;
const jsonMedia = /^application\/json(?:[ \t]*;[ \t]*charset=utf-8)?$/i;
// 32 bytes, canonical unpadded base64url (including the final two zero padding bits).
const opaqueProof = /^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$/;

function failure(status: number, detail = 'Password verification is temporarily unavailable.', challenge?: string) {
  return NextResponse.json({ detail }, { status, headers: {
    'Content-Type': 'application/problem+json', 'Cache-Control': 'no-store, no-transform',
    ...(challenge ? { 'WWW-Authenticate': challenge } : {}),
  } });
}

/** Only the two flat string-valued step-up messages; reject duplicate decoded keys, not last-key-wins. */
function stepUpFields(bytes: Uint8Array): Record<string, string> {
  const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
  const fields: Record<string, string> = Object.create(null);
  let offset = 0;
  const invalid = (): never => { throw new Error('Invalid step-up message.'); };
  const whitespace = () => { while (offset < raw.length && /[ \t\r\n]/.test(raw[offset])) offset++; };
  const string = (): string => {
    const start = offset;
    if (raw[offset++] !== '"') return invalid();
    while (offset < raw.length) {
      const next = raw[offset++];
      if (next === '\\') offset++;
      else if (next === '"') return JSON.parse(raw.slice(start, offset)) as string;
    }
    return invalid();
  };
  whitespace();
  if (raw[offset++] !== '{') invalid();
  whitespace();
  if (raw[offset] !== '}') {
    while (true) {
      const key = string();
      if (Object.hasOwn(fields, key) || Object.keys(fields).length === 3) invalid();
      whitespace();
      if (raw[offset++] !== ':') invalid();
      whitespace();
      fields[key] = string();
      whitespace();
      if (raw[offset] !== ',') break;
      offset++;
      whitespace();
    }
  }
  if (raw[offset++] !== '}') invalid();
  whitespace();
  if (offset !== raw.length) invalid();
  return fields;
}

export async function POST(request: Request) {
  const originFailure = await requireSameOrigin(request);
  if (originFailure) return originFailure;
  let session;
  try {
    session = readAdminSession(request.headers);
    requireCookieCapacity(session.cookies, 'proof');
  } catch (error) { return sessionFailure(error); }
  const rejected = await requireCsrf(request, session);
  if (rejected) return rejected;

  const controller = new AbortController();
  const timeout = new DOMException('Password verification deadline exceeded.', 'TimeoutError');
  const deadline = performance.now() + timeoutMs;
  const onAbort = () => controller.abort();
  const timer = setTimeout(() => controller.abort(timeout), timeoutMs);
  request.signal.addEventListener('abort', onAbort, { once: true });
  const tooLarge = new Error('Step-up body exceeds its bound.');
  let upstream: Response | undefined;
  let upstreamStarted = false;
  let accepted = false;
  const checkActive = () => {
    if (performance.now() >= deadline) controller.abort(timeout);
    controller.signal.throwIfAborted();
  };
  // The existing local bounded-reader pattern, with one deadline across request, fetch and response.
  const read = async (message: Request | Response, maximum: number) => {
    const length = message.headers.get('content-length');
    if (length !== null && !/^[0-9]{1,20}$/.test(length)) throw new Error('Invalid step-up length.');
    if (length !== null && Number(length) > maximum) throw tooLarge;
    if (!message.body) throw new Error('Missing step-up body.');
    const reader = message.body.getReader();
    const bytes = new Uint8Array(maximum);
    let size = 0;
    let complete = false;
    const cancel = () => { void reader.cancel().catch(() => {}); };
    controller.signal.addEventListener('abort', cancel, { once: true });
    try {
      while (true) {
        checkActive();
        const next = await reader.read();
        checkActive();
        if (next.done) break;
        if (next.value.byteLength > maximum - size) throw tooLarge;
        bytes.set(next.value, size);
        size += next.value.byteLength;
      }
      if (length !== null && Number(length) !== size) throw new Error('Incorrect step-up length.');
      complete = true;
      return bytes.subarray(0, size);
    } finally {
      controller.signal.removeEventListener('abort', cancel);
      if (!complete) cancel();
      reader.releaseLock();
    }
  };

  try {
    if (request.signal.aborted) onAbort();
    checkActive();
    const media = request.headers.get('content-type');
    const encoding = request.headers.get('content-encoding');
    if (!media || media.length > 128 || /[\r\n]/.test(media) || !jsonMedia.test(media) || encoding !== null && encoding.toLowerCase() !== 'identity') {
      return failure(415, 'Password verification requires unencoded JSON.');
    }
    const transfer = request.headers.get('transfer-encoding');
    if (transfer !== null && (transfer.toLowerCase() !== 'chunked' || request.headers.has('content-length'))) {
      return failure(400, 'Invalid password verification request.');
    }
    const input = stepUpFields(await read(request, 4096));
    const scope = input.scope ?? 'source-admin-mutation';
    if (Object.keys(input).some((key) => key !== 'password' && key !== 'scope') || !input.password || input.password.length > 256 || !isStepUpScope(scope)) {
      return failure(400, 'Invalid password verification request.');
    }
    checkActive();
    upstreamStarted = true;
    upstream = await fetch(`${backendUrl}/api/v1/admin/step-up`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.token}`, 'Content-Type': 'application/json',
        Accept: 'application/json, application/problem+json', 'Accept-Encoding': 'identity',
        ...authenticationIdentityHeaders(request),
      },
      // Preserve the deployed password-only source endpoint; complaint scope never falls back to it.
      body: JSON.stringify({ password: input.password, ...(scope === 'complaint-moderation-mutation' ? { scope } : {}) }),
      cache: 'no-store', redirect: 'manual', signal: controller.signal,
    });
    checkActive();
    const upstreamEncoding = upstream.headers.get('content-encoding');
    if (upstream.redirected || upstream.status >= 300 && upstream.status < 400 || upstreamEncoding !== null && upstreamEncoding.toLowerCase() !== 'identity') {
      return failure(502);
    }
    const bytes = await read(upstream, 32_768);
    if (!upstream.ok) {
      // Never relay an upstream problem's prose, token fields, cookies or private headers.
      const response = failure(upstream.status, upstream.status === 429 ? 'Too many attempts. Try again later.' : 'Password verification failed.',
        upstream.status === 401 ? 'Bearer' : undefined);
      const retry = upstream.headers.get('retry-after');
      if ((upstream.status === 429 || upstream.status === 503) && retry !== null && /^[0-9]{1,6}$/.test(retry)) response.headers.set('Retry-After', retry);
      return response;
    }
    const upstreamMedia = upstream.headers.get('content-type');
    if (upstream.status !== 200 || !upstreamMedia || upstreamMedia.length > 128 || /[\r\n]/.test(upstreamMedia) || !jsonMedia.test(upstreamMedia)) return failure(502);
    const proof = stepUpFields(bytes);
    if (Object.keys(proof).length !== 3 || typeof proof.token !== 'string' || proof.token.length !== 43 || !opaqueProof.test(proof.token)
      || proof.scope !== scope || !isFutureExpiry(proof.expiresAt)) return failure(502);
    const grantId = upstream.headers.get('X-Kira-Admin-Step-Up-Grant-Id');
    // Association stays HttpOnly. Missing complaint association is unknown, never invented.
    if (grantId !== null && (scope !== 'complaint-moderation-mutation' || !isSessionSelector(grantId))) return failure(502);
    checkActive();
    const issued = issueAdminProof(session, proof.token, scope, proof.expiresAt, grantId);
    const approval = { expiresAt: new Date(issued.expiresAt).toISOString(), scope, generation: issued.generation, proofId: issued.proofId };
    const response = NextResponse.json(approval, { headers: { 'Cache-Control': 'no-store, no-transform' } });
    setAuthenticationCookie(response, issued);
    accepted = true;
    return response;
  } catch (error) {
    if (controller.signal.aborted) return failure(controller.signal.reason === timeout ? 504 : 502);
    return failure(upstreamStarted ? 502 : error === tooLarge ? 413 : 400,
      upstreamStarted ? undefined : 'Invalid password verification request.');
  } finally {
    clearTimeout(timer);
    request.signal.removeEventListener('abort', onAbort);
    if (!accepted) controller.abort();
    if (!request.bodyUsed) void request.body?.cancel().catch(() => {});
    if (upstream && !upstream.bodyUsed) void upstream.body?.cancel().catch(() => {});
  }
}
