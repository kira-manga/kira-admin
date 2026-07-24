'use client';

import { useEffect, useState } from 'react';

import { apiFetch } from '@/lib/client-api';
import type { AuditEntry, NavView, SourceChangeset, SourceHead } from '@/lib/types';
import { Icon } from './icons';
import { Button, Spinner, StatusBadge, formatDate } from './ui';

type OverviewData = {
  sources: SourceHead[];
  changesets: SourceChangeset[];
  audit: { items: AuditEntry[]; total: number };
};

export function OverviewView({ onNavigate }: { onNavigate: (view: NavView) => void }) {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    Promise.all([
      apiFetch<SourceHead[]>('sources'),
      apiFetch<SourceChangeset[]>('source-changesets'),
      apiFetch<{ items: AuditEntry[]; total: number }>('audit?page=0&size=6'),
    ]).then(([sources, changesets, audit]) => setData({ sources, changesets, audit })).catch((caught: Error) => setError(caught.message));
  }, []);
  if (error) return <div className="notice notice-error">{error}</div>;
  if (!data) return <Spinner label="Loading source operations" />;

  const active = data.sources.filter((source) => source.status === 'active').length;
  const withheld = data.sources.filter((source) => source.status === 'withheld').length;
  const openChangesets = data.changesets.filter((item) => item.status === 'open').length;

  return (
    <div className="view-stack">
      <section className="welcome-panel">
        <div><span className="eyebrow"><Icon name="spark" /> SOURCE OPERATIONS</span><h2>Your catalog,<br /><em>safe and observable.</em></h2><p>Edit server-side drafts, validate against the live contract, and publish one source or a complete atomic changeset without rebuilding the apps.</p><div className="welcome-actions"><Button tone="primary" icon="sources" onClick={() => onNavigate('sources')}>Open source catalog</Button><Button icon="changesets" onClick={() => onNavigate('changesets')}>Prepare changeset</Button></div></div>
        <div className="welcome-orbit"><div><strong>{active}</strong><span>active sources</span></div><i /><i /><i /></div>
      </section>
      <section className="stat-grid">
        <button type="button" onClick={() => onNavigate('sources')}><span className="stat-icon coral"><Icon name="sources" /></span><div><small>Catalog sources</small><strong>{data.sources.length}</strong><p>{active} active · {withheld} withheld</p></div><Icon name="arrow" /></button>
        <button type="button" onClick={() => onNavigate('changesets')}><span className="stat-icon amber"><Icon name="changesets" /></span><div><small>Open changesets</small><strong>{openChangesets}</strong><p>Atomic multi-source releases</p></div><Icon name="arrow" /></button>
        <button type="button" onClick={() => onNavigate('audit')}><span className="stat-icon mint"><Icon name="audit" /></span><div><small>Audit events</small><strong>{data.audit.total}</strong><p>Identifiers-only operation history</p></div><Icon name="arrow" /></button>
      </section>
      <section className="split-grid">
        <div className="panel"><div className="panel-heading"><div><span>RECENT SOURCE ACTIVITY</span><h3>Verified operations</h3></div><button type="button" onClick={() => onNavigate('audit')}>View all <Icon name="arrow" /></button></div><div className="activity-list">{data.audit.items.map((entry) => <button type="button" key={entry.id} onClick={() => onNavigate('audit')}><span className="activity-number"><Icon name="audit" /></span><div><strong>{entry.action}</strong><small>{entry.entityType} · {formatDate(entry.createdAt)}</small></div><StatusBadge status="recorded" /></button>)}</div></div>
        <div className="panel workflow-panel"><div className="panel-heading"><div><span>SAFE WORKFLOW</span><h3>Draft to catalog</h3></div></div><ol className="workflow-list"><li><span>1</span><div><strong>Edit a server draft</strong><small>Autosave uses an optimistic ETag and never changes immutable history.</small></div></li><li><span>2</span><div><strong>Validate and review</strong><small>Strict schema and generic-engine rules run before publication.</small></div></li><li><span>3</span><div><strong>Step up and publish</strong><small>One-time password confirmation protects catalog mutations.</small></div></li></ol></div>
      </section>
    </div>
  );
}
