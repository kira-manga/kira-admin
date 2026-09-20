import { createHash, createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';

import type { NextResponse } from 'next/server';

import { isCsrfToken, isSessionSelector, sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';
import { isStepUpScope, type StepUpScope } from './step-up-contract';

export const sessionCookiePrefix = 'kira_admin_session_';
export const proofCookiePrefix = 'kira_admin_proof_';
export const proofCookiePath = '/api';
export const sessionCookieLimit = 4;
export const proofCookieLimit = 8;
export const cookieHeaderLimit = 16_384;
const envelopeLimit = 3_800;
const sessionLifetimeMs = 86_400_000;
const proofLifetimeMs = 900_000;
const legacyRootCookies = new Set(['kira_admin_session', 'kira_admin_csrf']);

export class SessionBoundaryError extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}

export function sessionFailure(error: unknown) {
  const known = error instanceof SessionBoundaryError;
  const status = known ? error.status : 503;
  return Response.json({ detail: known ? error.message : 'Admin authentication is temporarily unavailable.' }, {
    status, headers: { 'Cache-Control': 'no-store, no-transform', ...(status === 401 ? { 'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"' } : {}) },
  });
}

// Runtime-only, independent server authority. Shared across replicas/restarts; no fallback key.
export function requireSessionSecret() {
  const value = process.env.KIRA_ADMIN_SESSION_SECRET;
  if (!value || value.length < 64 || value.length > 128 || value.length % 2 !== 0 || /[^0-9a-f]/.test(value)) {
    throw new SessionBoundaryError(503, 'Admin authentication is temporarily unavailable.');
  }
  return Buffer.from(value, 'hex');
}

type CookieIdentity = { name: string; generation: string; kind: 'session' | 'proof' };
export type SessionCookies = { values: ReadonlyMap<string, string>; identities: readonly CookieIdentity[] };
export type AdminSessionCookie = Readonly<{
  generation: string; token: string; csrfToken: string; expiresAt: number;
  name: string; value: string; cookies: SessionCookies;
}>;
export type AdminProofCookie = Readonly<{
  generation: string; proofId: string; scope: StepUpScope; expiresAt: number;
  token: string; grantId: string | null; name: string; value: string;
}>;

function cookieIdentity(name: string): CookieIdentity | null {
  if (name.startsWith(sessionCookiePrefix)) {
    const generation = name.slice(sessionCookiePrefix.length);
    if (isSessionSelector(generation)) return { name, generation, kind: 'session' };
  }
  if (name.startsWith(proofCookiePrefix)) {
    const parts = name.slice(proofCookiePrefix.length).split('_');
    if (parts.length === 3 && isSessionSelector(parts[0]) && ['s', 'c'].includes(parts[1]) && isSessionSelector(parts[2])) {
      return { name, generation: parts[0], kind: 'proof' };
    }
  }
  return null;
}

/** Parse the raw header once: framework cookie maps silently lose duplicates. Never choose newest. */
export function captureSessionCookies(headers: Headers): SessionCookies {
  requireSessionSecret();
  const raw = headers.get('cookie') ?? '';
  if (raw.length > cookieHeaderLimit || /[^\x20-\x7e]/.test(raw)) {
    throw new SessionBoundaryError(431, 'Admin cookies exceed the supported request bound.');
  }
  const fields = raw ? raw.split(';') : [];
  if (fields.length > 128) throw new SessionBoundaryError(431, 'Too many request cookies.');
  const values = new Map<string, string>();
  const identities: CookieIdentity[] = [];
  for (const field of fields) {
    const part = field.trim();
    const separator = part.indexOf('=');
    if (separator < 1) throw new SessionBoundaryError(400, 'Invalid request cookies.');
    const name = part.slice(0, separator);
    const relevant = name.startsWith(sessionCookiePrefix) || name.startsWith(proofCookiePrefix) || legacyRootCookies.has(name);
    if (!relevant) continue;
    const value = part.slice(separator + 1);
    const identity = cookieIdentity(name);
    if (values.has(name) || value.length > envelopeLimit || /[\s,]/.test(value) || !identity && !legacyRootCookies.has(name)) {
      throw new SessionBoundaryError(400, 'Ambiguous or invalid admin cookies.');
    }
    values.set(name, value);
    if (identity) identities.push(identity);
  }
  if (identities.filter((cookie) => cookie.kind === 'session').length > sessionCookieLimit
    || identities.filter((cookie) => cookie.kind === 'proof').length > proofCookieLimit) {
    throw new SessionBoundaryError(409, 'Too many admin sessions or approvals. Clear this site’s cookies or wait for expiry, then sign in again.');
  }
  return { values, identities };
}

export function requireCookieCapacity(cookies: SessionCookies, kind: CookieIdentity['kind']) {
  if (cookies.identities.filter((cookie) => cookie.kind === kind).length >= (kind === 'session' ? sessionCookieLimit : proofCookieLimit)) {
    throw new SessionBoundaryError(409, 'Admin session or approval capacity reached. Sign out or wait for expiry before trying again.');
  }
}

function mac(domain: 'session' | 'proof', body: string) {
  return createHmac('sha256', requireSessionSecret()).update(`kira-admin-${domain}.v1\0${body}`).digest();
}

function seal(domain: 'session' | 'proof', fields: unknown[]) {
  const body = Buffer.from(JSON.stringify(fields), 'utf8').toString('base64url');
  const value = `${body}.${mac(domain, body).toString('base64url')}`;
  if (value.length > envelopeLimit) throw new SessionBoundaryError(502, 'Invalid authentication response.');
  return value;
}

function unseal(domain: 'session' | 'proof', value: string | undefined): unknown[] | null {
  if (!value || value.length > envelopeLimit) return null;
  const parts = value.split('.');
  if (parts.length !== 2 || !/^[A-Za-z0-9_-]+$/.test(parts[0]) || !isCsrfToken(parts[1])) return null;
  const supplied = Buffer.from(parts[1], 'base64url');
  if (!timingSafeEqual(mac(domain, parts[0]), supplied)) return null;
  const body = Buffer.from(parts[0], 'base64url');
  if (body.toString('base64url') !== parts[0]) return null;
  try {
    const fields: unknown = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(body));
    return Array.isArray(fields) ? fields : null;
  } catch { return null; }
}

function isBearer(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0 && value.length <= 2048 && !/[^A-Za-z0-9._-]/.test(value);
}

function isExpiry(value: unknown, maximum: number): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > Date.now() && value <= Date.now() + maximum;
}

export function readAdminSession(headers: Headers, generation = headers.get(sessionGenerationHeader), cookies = captureSessionCookies(headers)): AdminSessionCookie {
  if (!isSessionSelector(generation)) throw new SessionBoundaryError(401, 'Not signed in.');
  const name = sessionCookiePrefix + generation;
  const value = cookies.values.get(name);
  const fields = unseal('session', value);
  if (!fields || fields.length !== 4 || fields[0] !== generation || !isBearer(fields[1]) || !isCsrfToken(fields[2])
    || !isExpiry(fields[3], sessionLifetimeMs)) throw new SessionBoundaryError(401, 'Your admin session has expired. Sign in again.');
  return { generation, token: fields[1], csrfToken: fields[2], expiresAt: fields[3], name, value: value!, cookies };
}

export function issueAdminSession(token: unknown, expiresInSeconds: unknown, cookies: SessionCookies): AdminSessionCookie {
  requireCookieCapacity(cookies, 'session');
  if (!isBearer(token) || typeof expiresInSeconds !== 'number' || !Number.isSafeInteger(expiresInSeconds) || expiresInSeconds < 1) {
    throw new SessionBoundaryError(502, 'Invalid authentication response.');
  }
  const generation = randomUUID();
  const csrfToken = randomBytes(32).toString('base64url');
  const expiresAt = Date.now() + Math.min(expiresInSeconds * 1000, sessionLifetimeMs);
  const name = sessionCookiePrefix + generation;
  return { generation, token, csrfToken, expiresAt, name, value: seal('session', [generation, token, csrfToken, expiresAt]), cookies };
}

function proofName(generation: string, scope: StepUpScope, proofId: string) {
  return `${proofCookiePrefix}${generation}_${scope === 'source-admin-mutation' ? 's' : 'c'}_${proofId}`;
}

function sessionBinding(session: AdminSessionCookie) {
  return createHash('sha256').update(session.value).digest('base64url');
}

export function issueAdminProof(session: AdminSessionCookie, token: string, scope: StepUpScope, upstreamExpiry: string, grantId: string | null): AdminProofCookie {
  requireCookieCapacity(session.cookies, 'proof');
  const expiresAt = Math.min(Date.parse(upstreamExpiry), session.expiresAt, Date.now() + proofLifetimeMs);
  if (!isCsrfToken(token) || !isStepUpScope(scope) || !isExpiry(expiresAt, proofLifetimeMs) || expiresAt - Date.now() < 1000
    || grantId !== null && (!isSessionSelector(grantId) || scope !== 'complaint-moderation-mutation')) {
    throw new SessionBoundaryError(502, 'Invalid password verification response.');
  }
  const proofId = randomUUID();
  const name = proofName(session.generation, scope, proofId);
  return { generation: session.generation, proofId, scope, expiresAt, token, grantId, name,
    value: seal('proof', [session.generation, proofId, scope, expiresAt, token, sessionBinding(session), grantId]) };
}

export function readAdminProof(headers: Headers, session: AdminSessionCookie, scope: StepUpScope): AdminProofCookie {
  const proofId = headers.get(stepUpProofIdHeader);
  if (!isSessionSelector(proofId)) throw new SessionBoundaryError(403, 'Verify your password again for this action.');
  const name = proofName(session.generation, scope, proofId);
  const value = session.cookies.values.get(name);
  const fields = unseal('proof', value);
  if (!fields || fields.length !== 7 || fields[0] !== session.generation || fields[1] !== proofId || fields[2] !== scope
    || !isExpiry(fields[3], proofLifetimeMs) || fields[3] > session.expiresAt || !isCsrfToken(fields[4]) || fields[5] !== sessionBinding(session)
    || fields[6] !== null && (!isSessionSelector(fields[6]) || scope !== 'complaint-moderation-mutation')) {
    throw new SessionBoundaryError(403, 'Verify your password again for this action.');
  }
  return { generation: session.generation, proofId, scope, expiresAt: fields[3], token: fields[4], grantId: fields[6], name, value: value! };
}

export function setAuthenticationCookie(response: NextResponse, cookie: AdminSessionCookie | AdminProofCookie) {
  response.cookies.set(cookie.name, cookie.value, { httpOnly: true, sameSite: 'strict', secure: process.env.NODE_ENV === 'production',
    path: 'proofId' in cookie ? proofCookiePath : '/', expires: new Date(cookie.expiresAt) });
}

export function retireProofCookie(response: NextResponse, proof: AdminProofCookie) {
  retireCookie(response, proof.name, proofCookiePath);
}

function retireCookie(response: NextResponse, name: string, path: string) {
  response.cookies.set(name, '', { httpOnly: name !== 'kira_admin_csrf', sameSite: 'strict', secure: process.env.NODE_ENV === 'production',
    path, expires: new Date(0), maxAge: 0 });
}

/** Only identities actually present in this request. Late responses cannot erase newer G/P names. */
export function retireCapturedCookies(response: NextResponse, cookies: SessionCookies, generation?: string) {
  for (const cookie of cookies.identities) {
    if (generation === undefined || cookie.generation === generation) retireCookie(response, cookie.name, cookie.kind === 'proof' ? proofCookiePath : '/');
  }
  if (generation === undefined) for (const name of legacyRootCookies) if (cookies.values.has(name)) retireCookie(response, name, '/');
}
