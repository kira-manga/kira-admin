import { authenticatedFetch } from './client-api';

export async function verifyProtectedAction(
  action: { password: string; isCurrent: () => boolean; clearPassword: () => void; onApproved: () => Promise<void> },
  request: typeof authenticatedFetch = authenticatedFetch,
) {
  if (!action.isCurrent()) return;
  const response = await request('/api/auth/step-up', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: action.password }),
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(problem.detail ?? 'Password verification failed.');
  }
  if (!action.isCurrent()) return;
  action.clearPassword();
  await action.onApproved();
}
