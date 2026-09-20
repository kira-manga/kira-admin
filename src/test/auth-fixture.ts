import { loginSession } from '../lib/client-api';
import type { StepUpScope } from '../lib/step-up-contract';

// Public synthetic identities only. No real account, password, JWT or backend proof.
export const fixtureGeneration = '12345678-1234-4234-8234-123456789abc';
export const otherGeneration = '87654321-1234-4234-8234-123456789abc';
export const fixtureProofId = 'abcdefab-1234-4234-8234-123456789abc';
export const otherProofId = 'abcdefab-1234-4234-9234-123456789abc';
export const fixtureCsrf = 'A'.repeat(43);

export function sessionAcknowledgement(generation = fixtureGeneration) {
  return { generation, csrfToken: fixtureCsrf, expiresAt: new Date(Date.now() + 3_600_000).toISOString() };
}

export function stepUpAcknowledgement(scope: StepUpScope = 'source-admin-mutation', proofId = fixtureProofId, generation = fixtureGeneration) {
  return { scope, proofId, generation, expiresAt: new Date(Date.now() + 300_000).toISOString() };
}

/** Seed through the real login ACK validator, not a product test-only state setter. */
export async function seedClientSession(generation = fixtureGeneration) {
  const original = globalThis.fetch;
  globalThis.fetch = async () => Response.json(sessionAcknowledgement(generation));
  try { await loginSession({ email: 'synthetic@example.test', password: 'fixture-only' }, () => true); }
  finally { globalThis.fetch = original; }
}
