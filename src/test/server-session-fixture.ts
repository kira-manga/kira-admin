import { captureSessionCookies, issueAdminSession, type AdminProofCookie, type AdminSessionCookie } from '../lib/server-session';
import { sessionGenerationHeader, stepUpProofIdHeader } from '../lib/session-contract';

// Isolated deterministic fixture signing authority. Never a default/runtime key.
export const fixtureSigningSecret = '19'.repeat(32);

export function createSessionFixture(token = 'fixture-only-session-jwt') {
  return issueAdminSession(token, 3600, captureSessionCookies(new Headers()));
}

export function signedRequestHeaders(session: AdminSessionCookie, proofs: readonly AdminProofCookie[] = [], extra: HeadersInit = {}) {
  const headers = new Headers({ Origin: 'https://admin.example.test', 'Sec-Fetch-Site': 'same-origin',
    'Content-Type': 'application/json', 'X-Kira-CSRF': session.csrfToken,
    [sessionGenerationHeader]: session.generation,
    Cookie: [session, ...proofs].map(({ name, value }) => `${name}=${value}`).join('; '),
    ...(proofs[0] ? { [stepUpProofIdHeader]: proofs[0].proofId } : {}),
  });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return headers;
}
