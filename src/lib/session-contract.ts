// Public selectors are routing metadata, never authentication credentials.
export const sessionGenerationHeader = 'X-Kira-Session-Generation';
export const stepUpProofIdHeader = 'X-Kira-Step-Up-Proof-Id';
export const mediaGenerationQuery = 'sessionGeneration';

export function isSessionSelector(value: unknown): value is string {
  return typeof value === 'string' && value.length === 36
    && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value);
}

export function isFutureExpiry(value: unknown): value is string {
  if (typeof value !== 'string' || value.length > 30 || !value.endsWith('Z')
    || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$/.test(value)) return false;
  const expiry = Date.parse(value);
  return Number.isFinite(expiry) && expiry > Date.now()
    && new Date(expiry).toISOString().slice(0, 19) === value.slice(0, 19);
}

export function isCsrfToken(value: unknown): value is string {
  return typeof value === 'string' && value.length === 43 && /^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$/.test(value);
}

export type SessionAcknowledgement = Readonly<{ generation: string; csrfToken: string; expiresAt: string }>;

export function isSessionAcknowledgement(value: unknown): value is SessionAcknowledgement {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return false;
  const fields = value as Partial<SessionAcknowledgement>;
  return Object.keys(value).length === 3 && isSessionSelector(fields.generation)
    && isCsrfToken(fields.csrfToken) && isFutureExpiry(fields.expiresAt);
}
