export type StepUpScope = 'source-admin-mutation' | 'complaint-moderation-mutation';

export function isStepUpScope(value: unknown): value is StepUpScope {
  return value === 'source-admin-mutation' || value === 'complaint-moderation-mutation';
}

/** Non-secret acknowledgement only. Neither a scope label nor an expiry is a proof. */
export function isStepUpApproval(value: unknown, scope: StepUpScope): value is { expiresAt: string; scope: StepUpScope } {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return false;
  const keys = Object.keys(value);
  if (keys.length !== 2 || !keys.includes('scope') || !keys.includes('expiresAt')) return false;
  const approval = value as { expiresAt?: unknown; scope?: unknown };
  if (approval.scope !== scope || typeof approval.expiresAt !== 'string'
    || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$/.test(approval.expiresAt) || !approval.expiresAt.endsWith('Z')) return false;
  const expiry = Date.parse(approval.expiresAt);
  return Number.isFinite(expiry) && expiry > Date.now()
    && new Date(expiry).toISOString().slice(0, 19) === approval.expiresAt.slice(0, 19);
}
