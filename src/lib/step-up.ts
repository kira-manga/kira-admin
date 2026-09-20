import { ApiError, authenticatedFetch, captureAdminSession, readAuthAcknowledgement } from './client-api';
import { sessionGenerationHeader } from './session-contract';
import { isStepUpApproval, isStepUpScope, type StepUpApproval, type StepUpScope } from './step-up-contract';

export async function verifyProtectedAction(
  action: { password: string; scope?: StepUpScope; isCurrent: () => boolean; clearPassword: () => void; onApproved: (approval: StepUpApproval) => Promise<void> },
  request: typeof authenticatedFetch = authenticatedFetch,
) {
  if (!action.isCurrent()) return;
  const scope = action.scope === undefined ? 'source-admin-mutation' : action.scope;
  if (!isStepUpScope(scope)) throw new Error('Invalid password verification scope.');
  const session = captureAdminSession();
  const current = () => action.isCurrent() && session.isCurrent();
  const response = await request('/api/auth/step-up', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', [sessionGenerationHeader]: session.generation },
    body: JSON.stringify({ password: action.password, ...(scope === 'complaint-moderation-mutation' ? { scope } : {}) }),
  });
  if (!current()) { void response.body?.cancel().catch(() => {}); return; }
  if (response.status === 401 && response.headers.get('www-authenticate') === 'KiraSession realm="kira-admin-bff"') {
    void response.body?.cancel().catch(() => {});
    throw new ApiError('Your admin session has expired. Sign in again.', 401);
  }
  if (!response.ok) {
    const problem = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(problem.detail ?? 'Password verification failed.');
  }
  const approval = await readAuthAcknowledgement(response).catch(() => null);
  if (!current()) return;
  if (response.status !== 200 || !isStepUpApproval(approval, scope) || approval.generation !== session.generation) throw new Error('Password verification could not be confirmed.');
  action.clearPassword();
  await action.onApproved(Object.freeze(approval));
}
