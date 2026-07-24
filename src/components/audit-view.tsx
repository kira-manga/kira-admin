'use client';

import { useEffect, useState } from 'react';

import { apiFetch } from '@/lib/client-api';
import type { AuditEntry } from '@/lib/types';
import { Icon } from './icons';
import { Spinner, formatDate } from './ui';

type AuditPage = { items: AuditEntry[]; page: number; size: number; total: number };

export function AuditView() {
  const [page, setPage] = useState<AuditPage | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    void apiFetch<AuditPage>('audit?page=0&size=100').then(setPage).catch((caught: Error) => setError(caught.message));
  }, []);
  if (!page) return error ? <div className="notice notice-error">{error}</div> : <Spinner label="Loading audit history" />;
  return (
    <div className="view-stack">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="audit" /> IMMUTABLE EVIDENCE</span><h2>Audit history</h2><p>Identifiers, revision numbers, checksums, and outcomes are recorded here. Source bodies, credentials, headers, and passwords are deliberately excluded.</p></div></section>
      <section className="panel audit-table"><div className="audit-header"><span>ACTION</span><span>ENTITY</span><span>SAFE DETAILS</span><span>TIME</span></div>{page.items.map((entry) => <article key={entry.id}><div><Icon name="audit" /><strong>{entry.action}</strong></div><div><span>{entry.entityType}</span><code>{entry.entityId}</code></div><pre>{JSON.stringify(entry.detail, null, 2)}</pre><time dateTime={entry.createdAt}>{formatDate(entry.createdAt)}</time></article>)}</section>
    </div>
  );
}
