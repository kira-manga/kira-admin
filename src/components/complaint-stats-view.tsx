'use client';

import { useLayoutEffect, useRef, useState } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { ApiError, captureAdminSession } from '@/lib/client-api';
import { ComplaintReadClientError, fetchComplaintAdminStats } from '@/lib/complaint-read-client';
import type { ParsedComplaintAdminStats } from '@/lib/complaint-stats-wire';
import { visibleComplaintText } from '@/lib/complaint-text';
import { Button, Spinner } from './ui';

type Props = { generation: string; dataScopeId: string; disabled: boolean; onSessionExpired: () => void };
const messages = {
  UNAVAILABLE: 'Statistics are unavailable. The backend may not support this read yet; no zero total is inferred.',
  SESSION_EXPIRED: 'Your session has expired. Sign in again.',
  UNAUTHORIZED: 'This statistics read was not authorized. It does not confirm local session expiry.',
  FORBIDDEN: 'You do not have permission to read complaint statistics.',
  INVALID_RESPONSE: 'The statistics request or response is invalid. Check the TEST scope before trying again.',
  NETWORK: 'Statistics could not be loaded. Retry explicitly to request a new snapshot.',
};
const textStyle = { whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' } as const;

/** User-triggered snapshot, keyed by the parent to G/scope and removed during retained operations. */
export function ComplaintStatsView({ generation, dataScopeId, disabled, onSessionExpired }: Props) {
  const [stats, setStats] = useState<ParsedComplaintAdminStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const heading = useRef<HTMLHeadingElement>(null);
  const owner = useActionOwner();
  const active = useRef<{ ticket: ActionTicket; controller: AbortController } | null>(null);

  useLayoutEffect(() => () => { active.current?.controller.abort(); active.current = null; }, []);
  useLayoutEffect(() => { if (stats) heading.current?.focus(); }, [stats]);

  function cancel() {
    const pending = active.current;
    active.current = null;
    if (pending) { owner.release(pending.ticket); pending.controller.abort(); }
    setStats(null); setLoading(false); setError('');
  }

  async function load() {
    if (disabled) return;
    const ticket = owner.acquire();
    if (!ticket) return;
    const controller = new AbortController();
    active.current = { ticket, controller };
    setStats(null); setError(''); setLoading(true);
    let session: ReturnType<typeof captureAdminSession> | undefined;
    try {
      session = captureAdminSession();
      if (session.generation !== generation) return;
      const value = await fetchComplaintAdminStats({ dataScopeId, signal: controller.signal });
      if (!ticket.isCurrent()) return;
      if (!session.isCurrent()) { onSessionExpired(); return; }
      setStats(value);
    } catch (caught) {
      // Ticket first: an obsolete read cannot expire a replacement view/session or disturb its P.
      if (!ticket.isCurrent()) return;
      const reason = session && !session.isCurrent() || caught instanceof ApiError && caught.status === 401 ? 'SESSION_EXPIRED'
        : caught instanceof ComplaintReadClientError ? caught.reason : 'NETWORK';
      setError(messages[reason]);
      if (reason === 'SESSION_EXPIRED') onSessionExpired();
    } finally {
      if (ticket.isCurrent()) { active.current = null; owner.release(ticket); setLoading(false); }
    }
  }

  return <section className="panel" aria-label="Complaint statistics">
    <div className="panel-heading"><div><h3>Scope statistics</h3>
      <p>Unfiltered snapshot of currently visible complaints in the TEST scope above, not the current search page or filters. Loading statistics does not activate backend APIs.</p>
    </div></div>
    <div style={{ padding: '1.25rem' }}>
      <Button type="button" tone="primary" disabled={disabled || loading} onClick={() => { void load(); }}>Load scope statistics</Button>
      {loading ? <Button type="button" onClick={cancel}>Cancel statistics</Button> : null}
      <div aria-live="polite" aria-atomic="true">
        {loading ? <Spinner label="Loading complaint statistics" /> : null}
        {error ? <p role="alert" className="notice notice-error">{error}</p> : null}
      </div>
      {stats ? <section aria-label="Complaint statistics result">
        <h4 ref={heading} tabIndex={-1}>Total visible rows: {stats.total}</h4>
        <p>Snapshot scope: <bdi>{stats.dataScopeId}</bdi>. Load again explicitly to refresh; counts are not ongoing estimates or permission to moderate.</p>
        {stats.total === '0' ? <p>No currently visible complaints in this scope.</p> : null}
        <div className="form-grid">
          <section aria-label="Counts by status"><h4>By status</h4><dl>{stats.byStatus.map(({ status, count }) => <div key={status}><dt>{status}</dt><dd>{count}</dd></div>)}</dl></section>
          <section aria-label="Counts by type"><h4>By type</h4><dl>{stats.byType.map(({ type, count }) => <div key={type ?? 'notice-not-applicable'}><dt>{type ?? 'Not applicable (NOTICE)'}</dt><dd>{count}</dd></div>)}</dl></section>
          <section aria-label="Counts by ownership"><h4>By ownership</h4><dl>{stats.byOwnership.map(({ ownership, count }) => <div key={ownership}><dt>{ownership}</dt><dd>{count}</dd></div>)}</dl></section>
        </div>
        <section aria-label="Counts by app version">
          <h4>Top app versions</h4>
          <p>At most 50 observed keys, ranked by row count then null first and UTF-8 byte order. Unreported may be in the remainder; it is distinct from every literal string.</p>
          <dl>{stats.appVersions.buckets.map(({ appVersion, count }) => <div key={appVersion === null ? 'null-key' : `string:${appVersion}`} style={{ minWidth: 0 }}>
            <dt>{appVersion === null ? 'Unreported (null key)' : <>String “<bdi dir="auto" style={textStyle}>{visibleComplaintText(appVersion)}</bdi>”{appVersion === '' ? ' (empty)' : ''}</>}</dt><dd>{count}</dd>
          </div>)}
            <div><dt>Other versions (rows, not groups)</dt><dd>{stats.appVersions.otherCount}</dd></div>
          </dl>
        </section>
      </section> : null}
    </div>
  </section>;
}
