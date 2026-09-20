import { NextResponse } from 'next/server';

import { backendUrl } from '@/lib/server-config';
import { readAdminSession, retireCapturedCookies, sessionFailure } from '@/lib/server-session';

export async function GET(request: Request) {
  let session;
  try { session = readAdminSession(request.headers); } catch (error) { return sessionFailure(error); }
  try {
    const signal = AbortSignal.any([request.signal, AbortSignal.timeout(15_000)]);
    const upstream = await fetch(`${backendUrl}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${session.token}`, Accept: 'application/json' }, cache: 'no-store', redirect: 'manual',
      signal,
    });
    if (upstream.status === 401 || upstream.status === 403) {
      void upstream.body?.cancel().catch(() => {});
      const response = NextResponse.json({ detail: 'Your admin session has expired.' }, { status: 401, headers: { 'Cache-Control': 'no-store' } });
      retireCapturedCookies(response, session.cookies, session.generation);
      return response;
    }
    if (upstream.status !== 200 || upstream.redirected) {
      void upstream.body?.cancel().catch(() => {});
      return sessionFailure(null);
    }
    const reader = upstream.body?.getReader();
    if (!reader) return sessionFailure(null);
    const cancel = () => { void reader.cancel().catch(() => {}); };
    signal.addEventListener('abort', cancel, { once: true });
    const bytes = new Uint8Array(4096);
    let length = 0;
    try {
      while (true) {
        signal.throwIfAborted();
        const next = await reader.read();
        signal.throwIfAborted();
        if (next.done) break;
        if (next.value.byteLength > bytes.length - length) throw new Error('Session profile exceeds its bound.');
        bytes.set(next.value, length);
        length += next.value.byteLength;
      }
    } finally {
      signal.removeEventListener('abort', cancel);
      cancel();
      reader.releaseLock();
    }
    const me = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes.subarray(0, length))) as { id?: unknown; email?: unknown; role?: unknown; createdAt?: unknown };
    if (me.role !== 'ADMIN') return NextResponse.json({ detail: 'Administrator access is required.' }, { status: 403, headers: { 'Cache-Control': 'no-store' } });
    if (typeof me.id !== 'string' || me.id.length > 36 || typeof me.email !== 'string' || me.email.length > 320
      || typeof me.createdAt !== 'string' || me.createdAt.length > 30 || session.expiresAt <= Date.now()) return sessionFailure(null);
    return NextResponse.json({ id: me.id, email: me.email, role: me.role, createdAt: me.createdAt,
      generation: session.generation, csrfToken: session.csrfToken, expiresAt: new Date(session.expiresAt).toISOString(),
    }, { headers: { 'Cache-Control': 'no-store, no-transform' } });
  } catch { return sessionFailure(null); }
}
