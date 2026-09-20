'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { useActionOwner } from '@/lib/action-owner';
import { logoutSession, sessionFetch } from '@/lib/client-api';
import type { AdminSession, NavView } from '@/lib/types';
import { AdminShell } from './admin-shell';
import { AuditView } from './audit-view';
import { CategoriesView } from './categories-view';
import { ChangesetsView } from './changesets-view';
import { ComplaintDetailView } from './complaint-detail-view';
import { LoginScreen } from './login-screen';
import { MediaView } from './media-view';
import { OverviewView } from './overview-view';
import { SourcesView } from './sources-view';
import { TutorialsView } from './tutorials-view';
import { Spinner } from './ui';

export function AdminApp() {
  const [session, setSession] = useState<AdminSession | null | undefined>(undefined);
  const [view, setView] = useState<NavView>('overview');
  const [notice, setNotice] = useState('');
  const owner = useActionOwner();
  const transition = useRef(0);

  const refreshSession = useCallback(async () => {
    const version = ++transition.current;
    const mounted = owner.captureLifetime();
    const current = () => mounted() && version === transition.current;
    try {
      const result = await sessionFetch(current);
      if (current() && result !== undefined) { setSession(result); setNotice(''); }
    } catch (error) {
      if (current()) { setSession(null); setNotice(error instanceof Error ? error.message : 'Session check failed.'); }
    }
  }, [owner]);
  useEffect(() => {
    // The state update happens after the external session request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshSession();
  }, [refreshSession]);

  function logout() {
    const version = ++transition.current;
    const mounted = owner.captureLifetime();
    const work = logoutSession();
    setSession(null);
    setNotice('');
    void work.catch(() => {
      if (mounted() && transition.current === version) setNotice('Signed out locally; server sign-out could not be confirmed.');
    });
  }

  if (session === undefined) return <main className="boot-screen"><div className="brand-mark">K</div><Spinner label="Opening Admin Studio" /></main>;
  if (!session) return <LoginScreen onSuccess={refreshSession} notice={notice} />;

  return (
    <AdminShell key={session.generation} session={session} view={view} onView={setView} onLogout={logout}>
      {view === 'overview' ? <OverviewView onNavigate={setView} /> : null}
      {view === 'sources' ? <SourcesView /> : null}
      {view === 'changesets' ? <ChangesetsView /> : null}
      {view === 'audit' ? <AuditView /> : null}
      {view === 'tutorials' ? <TutorialsView /> : null}
      {view === 'categories' ? <CategoriesView /> : null}
      {view === 'media' ? <MediaView /> : null}
      {view === 'complaints' ? <ComplaintDetailView /> : null}
    </AdminShell>
  );
}
