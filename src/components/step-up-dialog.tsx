'use client';

import { FormEvent, useState } from 'react';

import { authenticatedFetch } from '@/lib/client-api';
import { Button, Field, Input } from './ui';

export function StepUpDialog({ action, onCancel, onApproved }: { action: string; onCancel: () => void; onApproved: () => Promise<void> }) {
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const response = await authenticatedFetch('/api/auth/step-up', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) {
        const problem = await response.json().catch(() => ({})) as { detail?: string };
        throw new Error(problem.detail ?? 'Password verification failed.');
      }
      setPassword('');
      await onApproved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The protected action failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-layer" role="dialog" aria-modal="true" aria-label="Confirm protected action">
      <button className="modal-scrim" type="button" onClick={onCancel} aria-label="Cancel" />
      <form className="modal-card compact" onSubmit={submit}>
        <div className="modal-heading"><div><span>SECURITY CHECK</span><h3>Confirm {action}</h3></div></div>
        <p className="modal-copy">Enter your administrator password. The one-time approval expires quickly and is never exposed to browser JavaScript.</p>
        <Field label="Administrator password"><Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></Field>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <div className="modal-actions"><Button type="button" onClick={onCancel}>Cancel</Button><Button type="submit" tone="primary" disabled={busy}>{busy ? 'Verifying…' : 'Verify and continue'}</Button></div>
      </form>
    </div>
  );
}
