import { NextResponse } from 'next/server';

import { authenticationIdentityHeaders } from '@/lib/server-client-ip';
import { backendUrl } from '@/lib/server-config';
import { requireSameOrigin } from '@/lib/server-security';
import { captureSessionCookies, issueAdminSession, requireCookieCapacity, retireCapturedCookies, sessionFailure, setAuthenticationCookie } from '@/lib/server-session';

export async function POST(request: Request) {
  const rejected = await requireSameOrigin(request);
  if (rejected) return rejected;
  let captured;
  try {
    captured = captureSessionCookies(request.headers);
    requireCookieCapacity(captured, 'session');
  } catch (error) { return sessionFailure(error); }

  const signal = AbortSignal.any([request.signal, AbortSignal.timeout(15_000)]);
  let upstream: Response | undefined;
  let started = false;
  // The complete request/fetch/body shares one finite deadline; no private upstream errors are relayed.
  const read = async (message: Request | Response, maximum: number) => {
    signal.throwIfAborted();
    const reader = message.body?.getReader();
    if (!reader) throw new Error('Missing authentication body.');
    const bytes = new Uint8Array(maximum);
    let length = 0;
    const cancel = () => { void reader.cancel().catch(() => {}); };
    signal.addEventListener('abort', cancel, { once: true });
    try {
      while (true) {
        signal.throwIfAborted();
        const next = await reader.read();
        signal.throwIfAborted();
        if (next.done) return new TextDecoder('utf-8', { fatal: true }).decode(bytes.subarray(0, length));
        if (next.value.byteLength > maximum - length) throw new Error('Authentication body exceeds its bound.');
        bytes.set(next.value, length);
        length += next.value.byteLength;
      }
    } finally {
      signal.removeEventListener('abort', cancel);
      cancel();
      reader.releaseLock();
    }
  };
  try {
    const body = await read(request, 4096);
    started = true;
    upstream = await fetch(`${backendUrl}/api/v1/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...authenticationIdentityHeaders(request) },
      body, cache: 'no-store', redirect: 'manual', signal,
    });
    if (upstream.redirected || upstream.status >= 300 && upstream.status < 400) throw new Error('Unexpected authentication redirect.');
    const payload = await read(upstream, 32_768);
    if (!upstream.ok) return NextResponse.json({ detail: 'Sign in failed.' }, {
      status: upstream.status >= 400 && upstream.status <= 599 ? upstream.status : 502,
      headers: { 'Cache-Control': 'no-store, no-transform' },
    });
    if (upstream.status !== 200) throw new Error('Invalid authentication status.');
    const login = JSON.parse(payload) as { accessToken?: unknown; expiresInSeconds?: unknown; role?: unknown } | null;
    if (!login || typeof login !== 'object') throw new Error('Invalid authentication response.');
    if (login.role !== 'ADMIN') return NextResponse.json({ detail: 'This dashboard requires an administrator account.' }, { status: 403, headers: { 'Cache-Control': 'no-store' } });
    const session = issueAdminSession(login.accessToken, login.expiresInSeconds, captured);
    signal.throwIfAborted();
    const response = NextResponse.json({ generation: session.generation, csrfToken: session.csrfToken, expiresAt: new Date(session.expiresAt).toISOString() }, {
      headers: { 'Cache-Control': 'no-store, no-transform' },
    });
    retireCapturedCookies(response, captured);
    setAuthenticationCookie(response, session);
    return response;
  } catch {
    return NextResponse.json({ detail: 'Sign in is temporarily unavailable.' }, {
      status: signal.aborted && signal.reason instanceof DOMException && signal.reason.name === 'TimeoutError' ? 504 : started ? 502 : 400,
      headers: { 'Cache-Control': 'no-store, no-transform' },
    });
  } finally {
    if (!request.bodyUsed) void request.body?.cancel().catch(() => {});
    if (upstream && !upstream.bodyUsed) void upstream.body?.cancel().catch(() => {});
  }
}
