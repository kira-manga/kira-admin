'use client';

import { ReactNode, useState } from 'react';

import type { AdminSession, NavView } from '@/lib/types';
import { Icon, type IconName } from './icons';

const navigation: Array<{ id: NavView; label: string; detail: string; icon: IconName }> = [
  { id: 'overview', label: 'Overview', detail: 'Workspace pulse', icon: 'overview' },
  { id: 'sources', label: 'Sources', detail: 'Catalog & revisions', icon: 'sources' },
  { id: 'changesets', label: 'Changesets', detail: 'Atomic releases', icon: 'changesets' },
  { id: 'audit', label: 'Audit history', detail: 'Verified activity', icon: 'audit' },
  { id: 'tutorials', label: 'Tutorials', detail: 'Guides & revisions', icon: 'tutorials' },
  { id: 'categories', label: 'Categories', detail: 'Library structure', icon: 'categories' },
  { id: 'media', label: 'Media', detail: 'Screenshots & assets', icon: 'media' },
];

export function AdminShell({ session, view, onView, onLogout, children }: { session: AdminSession; view: NavView; onView: (view: NavView) => void; onLogout: () => void; children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const current = navigation.find((item) => item.id === view) ?? navigation[0];

  return (
    <div className="admin-shell">
      <aside className={`sidebar${mobileOpen ? ' sidebar-open' : ''}`}>
        <div className="brand"><span>K</span><div><strong>Kira</strong><small>Admin Studio</small></div></div>
        <button className="mobile-close" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><Icon name="close" /></button>
        <nav>
          <p>WORKSPACE</p>
          {navigation.map((item) => (
            <button key={item.id} type="button" className={view === item.id ? 'active' : ''} onClick={() => { onView(item.id); setMobileOpen(false); }}>
              <span><Icon name={item.icon} /></span><div><strong>{item.label}</strong><small>{item.detail}</small></div>
            </button>
          ))}
        </nav>
        <div className="sidebar-note"><Icon name="audit" /><div><strong>Safe publishing</strong><small>Optimistic drafts, password step-up, and atomic catalogs.</small></div></div>
        <div className="profile-card">
          <span>{session.email.slice(0, 1).toUpperCase()}</span>
          <div><strong>{session.email}</strong><small>Administrator</small></div>
          <button type="button" onClick={onLogout} title="Sign out"><Icon name="logout" /></button>
        </div>
      </aside>
      {mobileOpen ? <button className="sidebar-scrim" type="button" onClick={() => setMobileOpen(false)} aria-label="Close navigation" /> : null}
      <main className="workspace">
        <header className="topbar">
          <button className="menu-button" type="button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Icon name="menu" /></button>
          <div><span>{current.detail}</span><h1>{current.label}</h1></div>
          <a href="https://api.kiramanga.me/api/v1/source-config/catalog" target="_blank" rel="noreferrer">View live catalog <Icon name="arrow" /></a>
        </header>
        <div className="workspace-content">{children}</div>
      </main>
    </div>
  );
}
