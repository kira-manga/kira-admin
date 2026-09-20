'use client';

import { FormEvent, useState } from 'react';

import { useActionOwner } from '@/lib/action-owner';
import { ApiError } from '@/lib/client-api';
import { verifyProtectedAction } from '@/lib/step-up';
import type { StepUpApproval, StepUpScope } from '@/lib/step-up-contract';
import { Button, Field, Input } from './ui';

type StepUpDialogProps = { action: string; scope?: StepUpScope; onCancel: () => void; onApproved: (approval: StepUpApproval) => Promise<void>; onSessionExpired?: () => void };

export function StepUpDialog({ scope = 'source-admin-mutation', ...props }: StepUpDialogProps) {
  // A changed scope retires the old confirmation/password and its pending continuation.
  return <StepUpDialogSession key={scope} {...props} scope={scope} />;
}

function StepUpDialogSession({ action, scope, onCancel, onApproved, onSessionExpired }: StepUpDialogProps & { scope: StepUpScope }) {
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const owner = useActionOwner();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const ticket = owner.acquire();
    if (!ticket) return;
    setBusy(true);
    setError('');
    try {
      await verifyProtectedAction({
        password,
        scope,
        isCurrent: ticket.isCurrent,
        clearPassword: () => setPassword(''),
        onApproved,
      });
    } catch (caught) {
      if (ticket.isCurrent()) {
        if (caught instanceof ApiError && caught.status === 401 && onSessionExpired) onSessionExpired();
        else setError(caught instanceof Error ? caught.message : 'The protected action failed.');
      }
    } finally {
      if (owner.release(ticket)) {
        setPassword('');
        setBusy(false);
      }
    }
  }

  function cancel() {
    // Claim cancellation synchronously too: a same-turn submit must not start
    // verification while the parent's dismissal is waiting to commit.
    if (owner.acquire()) onCancel();
  }

  return (
    <div className="modal-layer" role="dialog" aria-modal="true" aria-label="Confirm protected action">
      <button className="modal-scrim" type="button" onClick={cancel} disabled={busy} aria-label="Cancel" />
      <form className="modal-card compact" onSubmit={submit}>
        <div className="modal-heading"><div><span>SECURITY CHECK</span><h3>Confirm {action}</h3></div></div>
        <p className="modal-copy">Enter your administrator password. The one-time approval expires quickly and is never exposed to browser JavaScript.</p>
        <Field label="Administrator password"><Input type="password" value={password} disabled={busy} onChange={(event) => { if (!owner.isLocked()) setPassword(event.target.value); }} autoComplete="current-password" required /></Field>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <div className="modal-actions"><Button type="button" onClick={cancel} disabled={busy}>Cancel</Button><Button type="submit" tone="primary" disabled={busy}>{busy ? 'Verifying…' : 'Verify and continue'}</Button></div>
      </form>
    </div>
  );
}
