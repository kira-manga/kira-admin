import { authenticatedFetch } from './client-api';
import { isStepUpApproval, isStepUpScope, type StepUpScope } from './step-up-contract';

export async function verifyProtectedAction(
  action: { password: string; scope?: StepUpScope; isCurrent: () => boolean; clearPassword: () => void; onApproved: () => Promise<void> },
  request: typeof authenticatedFetch = authenticatedFetch,
) {
  if (!action.isCurrent()) return;
  const scope = action.scope === undefined ? 'source-admin-mutation' : action.scope;
  if (!isStepUpScope(scope)) throw new Error('Invalid password verification scope.');
  const response = await request('/api/auth/step-up', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: action.password, ...(scope === 'complaint-moderation-mutation' ? { scope } : {}) }),
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(problem.detail ?? 'Password verification failed.');
  }
  if (!action.isCurrent()) return;
  const approval: unknown = await response.json().catch(() => null);
  if (!action.isCurrent()) return;
  if (response.status !== 200 || !isStepUpApproval(approval, scope)) throw new Error('Password verification could not be confirmed.');
  action.clearPassword();
  await action.onApproved();
}
