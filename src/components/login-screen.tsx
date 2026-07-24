'use client';

import { FormEvent, useState } from 'react';

import { ApiError } from '@/lib/client-api';
import { Icon } from './icons';
import { Button, Field, Input } from './ui';

export function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({})) as { detail?: string };
        throw new ApiError(payload.detail ?? 'Sign in failed.', response.status);
      }
      onSuccess();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Sign in failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-glow login-glow-one" />
      <div className="login-glow login-glow-two" />
      <section className="login-card">
        <div className="login-brand"><span>K</span><div><strong>Kira</strong><small>Tutorial Studio</small></div></div>
        <div className="login-copy">
          <span className="eyebrow"><Icon name="spark" /> PRIVATE WORKSPACE</span>
          <h1>Shape every guide from one calm place.</h1>
          <p>Write in English and Arabic, manage screenshots, review revisions, and publish directly to the Kira website.</p>
        </div>
        <form onSubmit={submit} className="login-form">
          <div className="login-form-heading"><h2>Welcome back</h2><p>Use your Kira administrator account.</p></div>
          <Field label="Email address"><Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="admin@kiramanga.me" autoComplete="username" required /></Field>
          <Field label="Password"><Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" autoComplete="current-password" required /></Field>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <Button tone="primary" type="submit" disabled={busy} icon="arrow">{busy ? 'Signing in…' : 'Open studio'}</Button>
        </form>
        <p className="login-footnote"><i /> Secure server session · credentials are never stored in the browser</p>
      </section>
    </main>
  );
}
