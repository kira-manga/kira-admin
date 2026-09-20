'use client';

import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { ComplaintReadClientError, fetchComplaintAdminDetail } from '@/lib/complaint-read-client';
import type { ParsedComplaintAdminDetail } from '@/lib/complaint-read-wire';
import { Button, Field, Input, Spinner, StatusBadge } from './ui';

const messages = {
  UNAVAILABLE: 'Complaint detail unavailable or not found. The backend may not support complaint reads yet.',
  SESSION_EXPIRED: 'Your session has expired. Sign out and sign in again.',
  FORBIDDEN: 'You do not have permission to read this complaint.',
  INVALID_RESPONSE: 'The complaint request or response is invalid. Check the IDs before trying again.',
  NETWORK: 'The complaint could not be loaded. Check the connection and try again.',
};

/** Read-only TEST lookup. Entered IDs and parsed data never confer moderation authority. */
export function ComplaintDetailView() {
  const [id, setId] = useState('');
  const [scope, setScope] = useState('');
  const [detail, setDetail] = useState<ParsedComplaintAdminDetail | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const owner = useActionOwner();
  const active = useRef<{ ticket: ActionTicket; controller: AbortController } | null>(null);

  useLayoutEffect(() => () => {
    active.current?.controller.abort();
    active.current = null;
  }, []);

  function invalidate() {
    const pending = active.current;
    active.current = null;
    if (pending) {
      owner.release(pending.ticket);
      pending.controller.abort();
    }
    setDetail(null);
    setError('');
    setLoading(false);
  }

  async function lookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ticket = owner.acquire();
    if (!ticket) return;
    const controller = new AbortController();
    active.current = { ticket, controller };
    setDetail(null);
    setError('');
    setLoading(true);
    try {
      const loaded = await fetchComplaintAdminDetail({ id: id.trim(), dataScopeId: scope.trim(), signal: controller.signal });
      if (ticket.isCurrent()) setDetail(loaded);
    } catch (caught) {
      if (ticket.isCurrent()) {
        setError(messages[caught instanceof ComplaintReadClientError ? caught.reason : 'NETWORK']);
      }
    } finally {
      if (ticket.isCurrent()) {
        active.current = null;
        owner.release(ticket);
        setLoading(false);
      }
    }
  }

  const item = detail?.item;
  return (
    <div className="view-stack">
      <section className="view-heading"><div><h2>Complaint detail</h2><p>Read-only TEST lookup. Use the configured TEST scope and a known complaint ID. Availability and access are enforced by the backend; this screen does not enable complaint APIs or moderation.</p></div></section>
      <form className="panel" onSubmit={(event) => { void lookup(event); }}>
        <Field label="TEST data scope ID" hint="Canonical UUID v4 supplied by the TEST environment owner.">
          <Input name="dataScopeId" value={scope} required maxLength={36} autoComplete="off" autoCapitalize="none" spellCheck={false} onChange={(event) => { invalidate(); setScope(event.target.value); }} />
        </Field>
        <Field label="Complaint ID">
          <Input name="complaintId" value={id} required maxLength={36} autoComplete="off" autoCapitalize="none" spellCheck={false} onChange={(event) => { invalidate(); setId(event.target.value); }} />
        </Field>
        <Button type="submit" tone="primary" disabled={loading}>Load detail</Button>
      </form>
      <div aria-live="polite" aria-atomic="true">
        {loading ? <Spinner label="Loading complaint detail" /> : null}
        {error ? <p role="alert" className="notice notice-error">{error}</p> : null}
      </div>
      {item ? <article className="panel" aria-label="Complaint detail result">
        <h3>{item.kind === 'NOTICE' ? 'System notice' : item.subject ?? 'Notice reply'}</h3>
        <StatusBadge status={item.status} />
        <dl>
          <dt>ID</dt><dd>{item.id}</dd>
          <dt>Kind</dt><dd>{item.kind}</dd>
          <dt>Version</dt><dd>{item.version}</dd>
          <dt>Ownership</dt><dd>{item.ownership}</dd>
          <dt>Created</dt><dd><time dateTime={item.createdAt}>{item.createdAt}</time></dd>
          <dt>Updated</dt><dd><time dateTime={item.updatedAt}>{item.updatedAt}</time></dd>
          {item.kind === 'NOTICE' ? <><dt>Notice key</dt><dd>{item.noticeKey}</dd></> : <>
            <dt>Type</dt><dd>{item.type}</dd>
            <dt>Installation reference</dt><dd>{item.ownerReference}</dd>
            <dt>App version</dt><dd>{item.appVersion ?? 'Not supplied'}</dd>
            <dt>Platform</dt><dd>{item.platform}</dd>
            <dt>OS version</dt><dd>{item.osVersion}</dd>
            <dt>Manufacturer</dt><dd>{item.manufacturer}</dd>
            <dt>Device model</dt><dd>{item.deviceModel}</dd>
            {item.replyToId ? <><dt>Reply to</dt><dd>{item.replyToId}</dd></> : null}
            {item.noticeKey ? <><dt>Notice key</dt><dd>{item.noticeKey}</dd></> : null}
            {item.closedAt ? <><dt>Closed</dt><dd><time dateTime={item.closedAt}>{item.closedAt}</time></dd><dt>Closure actor</dt><dd>{item.closureActorId}</dd></> : null}
          </>}
        </dl>
        {item.kind !== 'NOTICE' ? <>
          <h4>Body</h4><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{item.body}</pre>
          {item.closureReason !== null ? <><h4>Closure reason</h4><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{item.closureReason}</pre></> : null}
        </> : null}
        <p>Read-only. Editing, status changes and closure are not available.</p>
      </article> : null}
    </div>
  );
}
