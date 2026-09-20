import { isFutureExpiry, isSessionSelector } from './session-contract';

export type StepUpScope = 'source-admin-mutation' | 'complaint-moderation-mutation';
export type StepUpApproval = Readonly<{ expiresAt: string; scope: StepUpScope; generation: string; proofId: string }>;

export function isStepUpScope(value: unknown): value is StepUpScope {
  return value === 'source-admin-mutation' || value === 'complaint-moderation-mutation';
}

/** Non-secret acknowledgement only. Neither a scope label nor an expiry is a proof. */
export function isStepUpApproval(value: unknown, scope: StepUpScope): value is StepUpApproval {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return false;
  const keys = Object.keys(value);
  if (keys.length !== 4) return false;
  const approval = value as Partial<StepUpApproval>;
  return approval.scope === scope && isFutureExpiry(approval.expiresAt)
    && isSessionSelector(approval.generation) && isSessionSelector(approval.proofId);
}
