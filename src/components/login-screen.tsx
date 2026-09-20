'use client';

import { FormEvent, useState } from 'react';

import { useActionOwner } from '@/lib/action-owner';
import { loginSession } from '@/lib/client-api';
import { Icon } from './icons';
import { Button, Field, Input } from './ui';

export function LoginScreen({ onSuccess, notice }: { onSuccess: () => void | Promise<void>; notice?: string }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const owner = useActionOwner();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const ticket = owner.acquire();
    if (!ticket) return;
    setBusy(true);
    setError('');
    try {
      if (!await loginSession({ email, password }, ticket.isCurrent) || !ticket.isCurrent()) return;
      setPassword('');
      await onSuccess();
    } catch (caught) {
      if (ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Sign in failed.');
    } finally {
      if (owner.release(ticket)) { setPassword(''); setBusy(false); }
    }
  }

  return (
    <main className="login-page">
      <div className="login-glow login-glow-one" />
      <div className="login-glow login-glow-two" />
      <section className="login-card">
        <div className="login-brand"><span>K</span><div><strong>Kira</strong><small>Admin Studio</small></div></div>
        <div className="login-copy">
          <span className="eyebrow"><Icon name="spark" /> PRIVATE WORKSPACE</span>
          <h1>Operate Kira from one calm place.</h1>
          <p>Edit generic sources, review immutable revisions, publish atomic catalogs, and manage the bilingual tutorial library.</p>
        </div>
        <form onSubmit={submit} className="login-form">
          <div className="login-form-heading"><h2>Welcome back</h2><p>Use your Kira administrator account.</p></div>
          <Field label="Email address"><Input type="email" value={email} disabled={busy} onChange={(event) => setEmail(event.target.value)} placeholder="admin@kiramanga.me" autoComplete="username" required /></Field>
          <Field label="Password"><Input type="password" value={password} disabled={busy} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" autoComplete="current-password" required /></Field>
          {error || notice ? <p className="form-error" role="alert">{error || notice}</p> : null}
          <Button tone="primary" type="submit" disabled={busy} icon="arrow">{busy ? 'Signing in…' : 'Open studio'}</Button>
        </form>
        <p className="login-footnote"><i /> Secure server session · credentials are never stored in the browser</p>
      </section>
    </main>
  );
}
