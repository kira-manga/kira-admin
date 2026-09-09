'use client';

import { useCallback, useEffect, useState } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { applySavedChangeset, parseOperations, prepareChangesetApply, saveAndAdoptChangeset, validateChangeset, type ChangesetEditorAction, type ChangesetEditorSnapshot, type PreparedChangesetApply } from '@/lib/changeset-editor';
import { apiFetch, apiFetchWithMeta } from '@/lib/client-api';
import type { SourceChange, SourceChangeset, SourceHead } from '@/lib/types';
import { Icon } from './icons';
import { StepUpDialog } from './step-up-dialog';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, Textarea, formatDate } from './ui';

type PendingApply = PreparedChangesetApply & { ticket: ActionTicket };

export function ChangesetsView() {
  const [items, setItems] = useState<SourceChangeset[] | null>(null);
  const [sources, setSources] = useState<SourceHead[]>([]);
  const [open, setOpen] = useState<ChangesetEditorSnapshot | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [pendingApply, setPendingApply] = useState<PendingApply | null>(null);
  const owner = useActionOwner();
  const locked = busy || pendingApply !== null;

  const load = useCallback(async () => {
    const isCurrent = owner.captureLifetime();
    try {
      const [changesets, catalog] = await Promise.all([
        apiFetch<SourceChangeset[]>('source-changesets'),
        apiFetch<SourceHead[]>('sources'),
      ]);
      if (!isCurrent()) return;
      setItems(changesets);
      setSources(catalog);
    } catch (caught) {
      if (isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not load changesets.');
    }
  }, [owner]);
  useEffect(() => {
    // State changes only after the external requests resolve.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  function beginAction() {
    const ticket = owner.acquire();
    if (!ticket) return null;
    setBusy(true);
    setError('');
    setMessage('');
    return ticket;
  }

  function finishAction(ticket: ActionTicket, retainConfirmation = false) {
    if (!ticket.isCurrent()) return;
    if (!retainConfirmation) owner.release(ticket);
    setBusy(false);
  }

  function beginEditorAction() {
    if (!open || open.value.status !== 'open') return null;
    const ticket = beginAction();
    if (!ticket) return null;
    const action: ChangesetEditorAction = { id: open.value.id, current: open, isCurrent: ticket.isCurrent, adopt: setOpen };
    return { ticket, action };
  }

  async function select(id: string) {
    const ticket = beginAction();
    if (!ticket) return;
    try {
      const result = await apiFetchWithMeta<SourceChangeset>(`source-changesets/${id}`);
      if (!result.etag) throw new Error('The backend did not return a changeset ETag.');
      if (!ticket.isCurrent()) return;
      setOpen({ value: result.data, etag: result.etag, operationsText: JSON.stringify(result.data.operations, null, 2) });
    } catch (caught) {
      if (ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not open changeset.');
    } finally {
      finishAction(ticket);
    }
  }

  async function create() {
    const ticket = beginAction();
    if (!ticket) return;
    try {
      const result = await apiFetchWithMeta<SourceChangeset>('source-changesets', {
        method: 'POST',
        body: JSON.stringify({ name: `Catalog update ${new Date().toLocaleDateString()}` }),
      });
      if (!result.etag) throw new Error('The backend did not return a changeset ETag.');
      if (!ticket.isCurrent()) return;
      setOpen({ value: result.data, etag: result.etag, operationsText: '[]' });
      await load();
    } catch (caught) {
      if (ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not create changeset.');
    } finally {
      finishAction(ticket);
    }
  }

  async function save() {
    const work = beginEditorAction();
    if (!work) return;
    try {
      const saved = await saveAndAdoptChangeset(work.action);
      if (!saved || !work.ticket.isCurrent()) return;
      setMessage('Changeset saved. No public source was changed.');
      await load();
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not save changeset.');
    } finally {
      finishAction(work.ticket);
    }
  }

  async function validate() {
    const work = beginEditorAction();
    if (!work) return;
    try {
      const result = await validateChangeset(work.action);
      if (!result || !work.ticket.isCurrent()) return;
      setMessage(`Validation passed for ${result.operationCount} operation(s) affecting ${result.affectedApis.length} source(s).`);
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Validation failed.');
    } finally {
      finishAction(work.ticket);
    }
  }

  async function prepareApply() {
    const work = beginEditorAction();
    if (!work) return;
    let prepared = false;
    try {
      const pending = await prepareChangesetApply(work.action);
      if (!pending || !work.ticket.isCurrent()) return;
      setPendingApply({ ...pending, ticket: work.ticket });
      prepared = true;
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not save changeset.');
    } finally {
      finishAction(work.ticket, prepared);
    }
  }

  async function apply() {
    const pending = pendingApply;
    if (!pending || !pending.ticket.isCurrent()) throw new Error('This changeset confirmation is no longer current.');
    let completed = false;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await applySavedChangeset(pending, pending.ticket.isCurrent);
      if (!result || !pending.ticket.isCurrent()) return;
      completed = true;
      setPendingApply(null);
      setMessage(`Applied atomically as catalog revision ${result.documentRevision}; ${result.affectedApis.length} source(s) affected.`);
      setOpen(null);
      await load();
    } finally {
      finishAction(pending.ticket, !completed);
    }
  }

  function cancelApply() {
    if (pendingApply && owner.release(pendingApply.ticket)) setPendingApply(null);
  }

  function updateMetadata(field: 'name' | 'description', value: string) {
    if (!open || open.value.status !== 'open' || owner.isLocked()) return;
    const metadata = field === 'name' ? { name: value } : { description: value || null };
    setOpen({ ...open, value: { ...open.value, ...metadata } });
  }

  function updateOperations(operationsText: string) {
    if (!open || open.value.status !== 'open' || owner.isLocked()) return;
    setOpen({ ...open, operationsText });
  }

  function addOperation(type: SourceChange['type']) {
    if (!open || open.value.status !== 'open' || owner.isLocked()) return;
    const first = sources.find((source) => source.engine === 'generic');
    const next: SourceChange = type === 'reorder'
      ? { type, orderedApis: [...sources].sort((a, b) => a.position - b.position).map((source) => source.api) }
      : { type, api: first?.api, ...(type === 'publish' ? { revisionNumber: first?.latestRevisionNumber ?? 1 } : {}), ...(type === 'remove' ? { confirm: first?.api } : {}) };
    const current = parseOperations(open.operationsText, true);
    setOpen({ ...open, operationsText: JSON.stringify([...current, next], null, 2) });
  }

  if (!items) return error ? <div className="notice notice-error">{error}</div> : <Spinner label="Loading changesets" />;

  return (
    <div className="view-stack">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="changesets" /> ATOMIC RELEASES</span><h2>Catalog changesets</h2><p>Stage related publishes, lifecycle changes, and ordering updates. Apply validates everything first and commits one complete catalog revision—or nothing.</p></div><Button icon="plus" tone="primary" onClick={create} disabled={locked}>New changeset</Button></section>
      {message ? <div className="notice notice-success">{message}</div> : null}
      {error ? <div className="notice notice-error">{error}</div> : null}
      <section className="manager-grid">
        <div className="panel manager-list"><div className="entity-list">{items.map((item) => <button type="button" className={`source-row${open?.value.id === item.id ? ' selected' : ''}`} key={item.id} disabled={locked} onClick={() => select(item.id)}><span className="source-position"><Icon name="changesets" /></span><div><strong>{item.name}</strong><small>{item.operations.length} operations · {formatDate(item.updatedAt)}</small></div><StatusBadge status={item.status} /></button>)}</div></div>
        <div className="panel changeset-editor">
          {open ? <><div className="detail-hero"><div><span className="eyebrow">{open.etag}</span><h3>{open.value.name}</h3><p>Last changed {formatDate(open.value.updatedAt)}</p></div><StatusBadge status={open.value.status} /></div>
            <div className="changeset-form"><Field label="Name"><Input value={open.value.name} disabled={locked || open.value.status !== 'open'} onChange={(event) => updateMetadata('name', event.target.value)} /></Field><Field label="Description"><Input value={open.value.description ?? ''} disabled={locked || open.value.status !== 'open'} onChange={(event) => updateMetadata('description', event.target.value)} /></Field>
              <div className="operation-toolbar"><span>Add operation</span>{(['publish', 'disable', 'enable', 'retire', 'remove', 'reorder'] as const).map((type) => <button type="button" key={type} onClick={() => addOperation(type)} disabled={locked || open.value.status !== 'open'}>{type}</button>)}</div>
              <Field label="Operations JSON" hint="Use source IDs exactly as shown in the source catalog. Reorder must include every source once." wide><Textarea className="changeset-code" spellCheck={false} value={open.operationsText} disabled={locked || open.value.status !== 'open'} onChange={(event) => updateOperations(event.target.value)} /></Field>
              {open.value.status === 'open' ? <div className="detail-actions"><Button onClick={save} disabled={locked}>Save</Button><Button onClick={validate} disabled={locked}>Validate</Button><Button tone="primary" onClick={prepareApply} disabled={locked}>Apply atomically</Button></div> : null}
            </div></> : <EmptyState icon="changesets" title="Choose or create a changeset" copy="Group catalog changes here when they must become visible together." action={<Button icon="plus" onClick={create} disabled={locked}>New changeset</Button>} />}
        </div>
      </section>
      {pendingApply ? <StepUpDialog action="this atomic catalog changeset" onCancel={cancelApply} onApproved={apply} /> : null}
    </div>
  );
}
