'use client';

import { useCallback, useEffect, useState } from 'react';

import { sessionFetch } from '@/lib/client-api';
import type { AdminSession, NavView } from '@/lib/types';
import { AdminShell } from './admin-shell';
import { CategoriesView } from './categories-view';
import { LoginScreen } from './login-screen';
import { MediaView } from './media-view';
import { OverviewView } from './overview-view';
import { TutorialsView } from './tutorials-view';
import { Spinner } from './ui';

export function AdminApp() {
  const [session, setSession] = useState<AdminSession | null | undefined>(undefined);
  const [view, setView] = useState<NavView>('overview');

  const refreshSession = useCallback(async () => setSession(await sessionFetch()), []);
  useEffect(() => {
    // The state update happens after the external session request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshSession();
  }, [refreshSession]);

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    setSession(null);
  }

  if (session === undefined) return <main className="boot-screen"><div className="brand-mark">K</div><Spinner label="Opening Tutorial Studio" /></main>;
  if (!session) return <LoginScreen onSuccess={refreshSession} />;

  return (
    <AdminShell session={session} view={view} onView={setView} onLogout={logout}>
      {view === 'overview' ? <OverviewView onNavigate={setView} /> : null}
      {view === 'tutorials' ? <TutorialsView /> : null}
      {view === 'categories' ? <CategoriesView /> : null}
      {view === 'media' ? <MediaView /> : null}
    </AdminShell>
  );
}
