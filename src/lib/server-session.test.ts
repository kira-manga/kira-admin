import { createHmac } from 'node:crypto';

import { NextResponse } from 'next/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';
import { otherGeneration, otherProofId } from '@/test/auth-fixture';
import { sessionGenerationHeader, stepUpProofIdHeader } from './session-contract';
import { capturedComplaintProofs, captureSessionCookies, cookieHeaderLimit, issueAdminProof, issueAdminSession, proofCookieLimit, readAdminProof, readAdminSession, readOptionalComplaintProof, requireCookieCapacity,
  retireCapturedCookies, retireProofCookie, sessionCookieLimit, sessionCookiePrefix, setAuthenticationCookie, type AdminSessionCookie } from './server-session';

const proofToken = 'A'.repeat(43);
const expiry = () => new Date(Date.now() + 300_000).toISOString();
const proofFor = (session: AdminSessionCookie) => issueAdminProof(session, proofToken, 'source-admin-mutation', expiry(), null);

function replaceEnvelope(value: string, change: (fields: unknown[]) => void, key = Buffer.from(fixtureSigningSecret, 'hex'), domain = 'session') {
  const fields = JSON.parse(Buffer.from(value.split('.')[0], 'base64url').toString('utf8')) as unknown[];
  change(fields);
  const body = Buffer.from(JSON.stringify(fields)).toString('base64url');
  const signature = createHmac('sha256', key).update(`kira-admin-${domain}.v1\0${body}`).digest('base64url');
  return `${body}.${signature}`;
}

beforeEach(() => {
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  vi.stubEnv('NODE_ENV', 'production');
  vi.useFakeTimers();
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });

describe('stateless authenticated G/P envelopes', () => {
  it('authenticates two different random G values for the identical same-second JWT', () => {
    const first = createSessionFixture('same-jwt');
    const second = createSessionFixture('same-jwt');
    expect(first.generation).not.toBe(second.generation);
    expect(first.csrfToken).not.toBe(second.csrfToken);
    expect(first.expiresAt).toBe(second.expiresAt);
    expect(readAdminSession(signedRequestHeaders(first)).token).toBe('same-jwt');
    expect(readAdminSession(signedRequestHeaders(second)).token).toBe('same-jwt');
  });

  it('cannot authenticate a public selector, renamed envelope, or bearer-key self-signed generation', () => {
    const session = createSessionFixture();
    const headers = signedRequestHeaders(session);
    headers.delete('cookie');
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
    headers.set(sessionGenerationHeader, otherGeneration);
    headers.set('cookie', `${sessionCookiePrefix}${otherGeneration}=${session.value}`);
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
    const selfSigned = replaceEnvelope(session.value, (fields) => { fields[0] = otherGeneration; }, Buffer.from(session.token));
    headers.set('cookie', `${sessionCookiePrefix}${otherGeneration}=${selfSigned}`);
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
    const tampered = session.value.slice(0, -1) + (session.value.endsWith('A') ? 'E' : 'A');
    headers.set(sessionGenerationHeader, session.generation);
    headers.set('cookie', `${session.name}=${tampered}`);
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
  });

  it('works after module restart/on another replica with the same independent secret and fails after rotation', async () => {
    const session = createSessionFixture();
    const proof = proofFor(session);
    const headers = signedRequestHeaders(session, [proof]);
    vi.resetModules();
    const replica = await import('./server-session');
    const selected = replica.readAdminSession(headers);
    expect(replica.readAdminProof(headers, selected, 'source-admin-mutation').token).toBe(proofToken);
    vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', '27'.repeat(32));
    expect(() => replica.readAdminSession(headers)).toThrow('Sign in again');
  });

  it.each([undefined, '', 'short', '19'.repeat(31), '19'.repeat(65), 'A'.repeat(64), '1'.repeat(65), ' '.repeat(64), '1'.repeat(63) + '\n'])
  ('validates the secret lazily and fails closed without echoing configuration (%j)', async (secret) => {
    vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', secret);
    vi.resetModules();
    const helper = await import('./server-session'); // Builds/imports do not require a key.
    expect(() => helper.captureSessionCookies(new Headers())).toThrow('Admin authentication is temporarily unavailable.');
    try { helper.captureSessionCookies(new Headers()); } catch (error) {
      expect(helper.sessionFailure(error).status).toBe(503);
    }
  });

  it('binds proof to the exact signed session, not just an identical JWT or a public G', () => {
    const first = createSessionFixture('same-jwt');
    const second = createSessionFixture('same-jwt');
    const proof = proofFor(first);
    const wrongSession = signedRequestHeaders(second, [proof]);
    expect(() => readAdminProof(wrongSession, readAdminSession(wrongSession), 'source-admin-mutation')).toThrow('Verify your password');
    // Independently signed replacement session with the same G/JWT but another CSRF/expiry is not that proof's session.
    const changed = replaceEnvelope(first.value, (fields) => { fields[2] = 'E'.repeat(42) + 'A'; });
    const headers = signedRequestHeaders(first, [proof]);
    headers.set('cookie', `${first.name}=${changed}; ${proof.name}=${proof.value}`);
    expect(() => readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation')).toThrow('Verify your password');
  });

  it('authenticates optional complaint forwarding and captured association against the exact signed session too', () => {
    const session = createSessionFixture();
    const complaint = issueAdminProof(session, proofToken, 'complaint-moderation-mutation', expiry(), otherGeneration);
    const source = proofFor(session);
    const headers = signedRequestHeaders(session, [complaint, source]);
    let selected = readAdminSession(headers);
    expect(readOptionalComplaintProof(headers, selected)?.grantId).toBe(otherGeneration);
    expect(capturedComplaintProofs(selected)).toEqual([complaint]);
    headers.delete(stepUpProofIdHeader);
    expect(readOptionalComplaintProof(headers, selected)).toBeUndefined();
    expect(capturedComplaintProofs(selected)).toEqual([complaint]); // Proofless replay still has a bounded captured inventory.
    headers.set(stepUpProofIdHeader, `${complaint.proofId}, ${complaint.proofId}`);
    expect(() => readOptionalComplaintProof(headers, selected)).toThrow('Invalid approval selector');
    headers.set(stepUpProofIdHeader, complaint.proofId);
    const replacement = replaceEnvelope(session.value, (fields) => { fields[2] = 'E'.repeat(42) + 'A'; });
    headers.set('cookie', `${session.name}=${replacement}; ${complaint.name}=${complaint.value}`);
    selected = readAdminSession(headers);
    expect(readOptionalComplaintProof(headers, selected)).toBeUndefined();
    expect(capturedComplaintProofs(selected)).toEqual([]);
  });

  it('binds scope and P, and refuses ambiguous selectors or a missing selected proof rather than selecting another', () => {
    const session = createSessionFixture();
    const first = proofFor(session);
    const second = proofFor(session);
    const complaint = issueAdminProof(session, proofToken, 'complaint-moderation-mutation', expiry(), otherGeneration);
    const headers = signedRequestHeaders(session, [first, second, complaint]);
    const selected = readAdminSession(headers);
    expect(readAdminProof(headers, selected, 'source-admin-mutation').proofId).toBe(first.proofId);
    expect(() => readAdminProof(headers, selected, 'complaint-moderation-mutation')).toThrow('Verify your password');
    for (const selector of ['', otherProofId, `${first.proofId}, ${first.proofId}`]) {
      headers.set(stepUpProofIdHeader, selector);
      expect(() => readAdminProof(headers, selected, 'source-admin-mutation')).toThrow('Verify your password');
    }
    headers.set(stepUpProofIdHeader, second.proofId);
    headers.set('cookie', `${session.name}=${session.value}; ${second.name}=${first.value}`);
    expect(() => readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation')).toThrow('Verify your password');
    // Domain separation forbids treating the signed session envelope as a proof envelope.
    headers.set('cookie', `${session.name}=${session.value}; ${second.name}=${session.value}`);
    expect(() => readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation')).toThrow('Verify your password');
  });

  it('rejects legacy sessions and duplicate cookies even if both duplicate values are identical', () => {
    const session = createSessionFixture();
    const headers = signedRequestHeaders(session);
    headers.set('cookie', `kira_admin_session=${session.token}; kira_admin_csrf=${session.csrfToken}`);
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
    headers.set('cookie', `${session.name}=${session.value}; ${session.name}=${session.value}`);
    expect(() => readAdminSession(headers)).toThrow('Ambiguous');
    headers.set('cookie', `${session.name}=${session.value}`);
    headers.append(sessionGenerationHeader, session.generation);
    expect(() => readAdminSession(headers)).toThrow('Not signed in');
  });

  it('never refreshes lifetime on delivery and never falls back from an expired G/P', () => {
    const first = createSessionFixture();
    const oldProof = proofFor(first);
    const response = NextResponse.json({});
    setAuthenticationCookie(response, first);
    setAuthenticationCookie(response, oldProof);
    for (const cookie of response.headers.getSetCookie()) {
      expect(cookie).toContain('Expires=');
      expect(cookie).not.toContain('Max-Age=');
    }
    vi.advanceTimersByTime(300_000);
    const newProof = proofFor(first);
    const headers = signedRequestHeaders(first, [oldProof, newProof]);
    expect(() => readAdminProof(headers, readAdminSession(headers), 'source-admin-mutation')).toThrow('Verify your password');
    vi.advanceTimersByTime(3_300_000);
    const second = createSessionFixture();
    headers.set('cookie', `${first.name}=${first.value}; ${second.name}=${second.value}`);
    expect(() => readAdminSession(headers)).toThrow('Sign in again');
  });
});

describe('finite inventory and captured-only retirement', () => {
  it('bounds raw headers, cookie fields, envelope bytes and observed session/proof counts', () => {
    const session = createSessionFixture();
    for (const raw of ['other=' + 'x'.repeat(cookieHeaderLimit), Array(129).fill('other=x').join('; ')]) {
      expect(() => captureSessionCookies(new Headers({ Cookie: raw }))).toThrow(/bound|Too many/);
    }
    expect(() => captureSessionCookies(new Headers({ Cookie: `${session.name}=${'x'.repeat(3801)}` }))).toThrow('invalid admin');
    const sessions = Array.from({ length: sessionCookieLimit }, () => createSessionFixture());
    const headers = new Headers({ Cookie: sessions.map((item) => `${item.name}=${item.value}`).join('; ') });
    const captured = captureSessionCookies(headers);
    expect(() => issueAdminSession('same-jwt', 3600, captured)).toThrow('capacity');
    headers.set('cookie', headers.get('cookie') + `; ${session.name}=${session.value}`);
    expect(() => captureSessionCookies(headers)).toThrow('Too many admin');
    const proofs = Array.from({ length: proofCookieLimit }, () => proofFor(session));
    const atLimit = readAdminSession(signedRequestHeaders(session, proofs));
    expect(() => requireCookieCapacity(atLimit.cookies, 'proof')).toThrow('capacity');
    expect(() => issueAdminProof(atLimit, proofToken, 'source-admin-mutation', expiry(), null)).toThrow('capacity');
    expect(() => readAdminSession(signedRequestHeaders(session, [...proofs, proofFor(session)]))).toThrow('Too many admin');
  });

  it('retires only captured G or P at their exact original paths, never a shared current cookie', () => {
    const first = createSessionFixture();
    const oldProof = proofFor(first);
    const captured = readAdminSession(signedRequestHeaders(first, [oldProof]));
    const second = createSessionFixture();
    const newProof = proofFor(second);
    const logout = NextResponse.json({});
    retireCapturedCookies(logout, captured.cookies, first.generation);
    expect(logout.headers.getSetCookie()).toHaveLength(2);
    expect(logout.headers.getSetCookie()[0]).toContain(`${first.name}=; Path=/;`);
    expect(logout.headers.getSetCookie()[1]).toContain(`${oldProof.name}=; Path=/api;`);
    expect(logout.headers.get('set-cookie')).not.toContain(second.name);
    expect(logout.headers.get('set-cookie')).not.toContain(newProof.name);
    const mutation = NextResponse.json({});
    retireProofCookie(mutation, oldProof);
    expect(mutation.headers.getSetCookie()).toHaveLength(1);
    expect(mutation.headers.getSetCookie()[0]).toContain(`${oldProof.name}=; Path=/api;`);
  });
});
