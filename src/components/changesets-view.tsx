'use client';

import { useCallback, useEffect, useState } from 'react';

import { apiFetch, apiFetchWithMeta } from '@/lib/client-api';
import type { SourceChange, SourceChangeset, SourceHead } from '@/lib/types';
import { Icon } from './icons';
import { StepUpDialog } from './step-up-dialog';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, Textarea, formatDate } from './ui';

type OpenChangeset = { value: SourceChangeset; etag: string; operationsText: string };

export function ChangesetsView() {
  const [items, setItems] = useState<SourceChangeset[] | null>(null);
  const [sources, setSources] = useState<SourceHead[]>([]);
  const [open, setOpen] = useState<OpenChangeset | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmApply, setConfirmApply] = useState(false);

  const load = useCallback(async () => {
    try {
      const [changesets, catalog] = await Promise.all([
        apiFetch<SourceChangeset[]>('source-changesets'),
        apiFetch<SourceHead[]>('sources'),
      ]);
      setItems(changesets);
      setSources(catalog);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load changesets.');
    }
  }, []);
  useEffect(() => {
    // State changes only after the external requests resolve.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function select(id: string) {
    try {
      const result = await apiFetchWithMeta<SourceChangeset>(`source-changesets/${id}`);
      if (!result.etag) throw new Error('The backend did not return a changeset ETag.');
      setOpen({ value: result.data, etag: result.etag, operationsText: JSON.stringify(result.data.operations, null, 2) });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not open changeset.');
    }
  }

  async function create() {
    setBusy(true);
    try {
      const result = await apiFetchWithMeta<SourceChangeset>('source-changesets', {
        method: 'POST',
        body: JSON.stringify({ name: `Catalog update ${new Date().toLocaleDateString()}` }),
      });
      if (!result.etag) throw new Error('The backend did not return a changeset ETag.');
      setOpen({ value: result.data, etag: result.etag, operationsText: '[]' });
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not create changeset.');
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!open) return;
    setBusy(true);
    try {
      const operations = parseOperations(open.operationsText);
      const result = await apiFetchWithMeta<SourceChangeset>(`source-changesets/${open.value.id}`, {
        method: 'PUT',
        headers: { 'If-Match': open.etag },
        body: JSON.stringify({ name: open.value.name, description: open.value.description, operations }),
      });
      if (!result.etag) throw new Error('The backend did not return the updated changeset ETag.');
      setOpen({ value: result.data, etag: result.etag, operationsText: JSON.stringify(result.data.operations, null, 2) });
      setMessage('Changeset saved. No public source was changed.');
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not save changeset.');
    } finally {
      setBusy(false);
    }
  }

  async function validate() {
    if (!open) return;
    setBusy(true);
    try {
      const result = await apiFetch<{ valid: boolean; operationCount: number; affectedApis: string[] }>(
        `source-changesets/${open.value.id}/validate`,
        { method: 'POST', headers: { 'If-Match': open.etag } },
      );
      setMessage(`Validation passed for ${result.operationCount} operation(s) affecting ${result.affectedApis.length} source(s).`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Validation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function apply() {
    if (!open) return;
    setBusy(true);
    try {
      const result = await apiFetch<{ documentRevision: number; affectedApis: string[] }>(
        `source-changesets/${open.value.id}/apply`,
        { method: 'POST', headers: { 'If-Match': open.etag } },
      );
      setConfirmApply(false);
      setMessage(`Applied atomically as catalog revision ${result.documentRevision}; ${result.affectedApis.length} source(s) affected.`);
      setOpen(null);
      await load();
    } finally {
      setBusy(false);
    }
  }

  function addOperation(type: SourceChange['type']) {
    if (!open) return;
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
      <section className="view-heading"><div><span className="eyebrow"><Icon name="changesets" /> ATOMIC RELEASES</span><h2>Catalog changesets</h2><p>Stage related publishes, lifecycle changes, and ordering updates. Apply validates everything first and commits one complete catalog revision—or nothing.</p></div><Button icon="plus" tone="primary" onClick={create} disabled={busy}>New changeset</Button></section>
      {message ? <div className="notice notice-success">{message}</div> : null}
      {error ? <div className="notice notice-error">{error}</div> : null}
      <section className="manager-grid">
        <div className="panel manager-list"><div className="entity-list">{items.map((item) => <button type="button" className={`source-row${open?.value.id === item.id ? ' selected' : ''}`} key={item.id} onClick={() => select(item.id)}><span className="source-position"><Icon name="changesets" /></span><div><strong>{item.name}</strong><small>{item.operations.length} operations · {formatDate(item.updatedAt)}</small></div><StatusBadge status={item.status} /></button>)}</div></div>
        <div className="panel changeset-editor">
          {open ? <><div className="detail-hero"><div><span className="eyebrow">{open.etag}</span><h3>{open.value.name}</h3><p>Last changed {formatDate(open.value.updatedAt)}</p></div><StatusBadge status={open.value.status} /></div>
            <div className="changeset-form"><Field label="Name"><Input value={open.value.name} disabled={open.value.status !== 'open'} onChange={(event) => setOpen({ ...open, value: { ...open.value, name: event.target.value } })} /></Field><Field label="Description"><Input value={open.value.description ?? ''} disabled={open.value.status !== 'open'} onChange={(event) => setOpen({ ...open, value: { ...open.value, description: event.target.value || null } })} /></Field>
              <div className="operation-toolbar"><span>Add operation</span>{(['publish', 'disable', 'enable', 'retire', 'remove', 'reorder'] as const).map((type) => <button type="button" key={type} onClick={() => addOperation(type)} disabled={open.value.status !== 'open'}>{type}</button>)}</div>
              <Field label="Operations JSON" hint="Use source IDs exactly as shown in the source catalog. Reorder must include every source once." wide><Textarea className="changeset-code" spellCheck={false} value={open.operationsText} disabled={open.value.status !== 'open'} onChange={(event) => setOpen({ ...open, operationsText: event.target.value })} /></Field>
              {open.value.status === 'open' ? <div className="detail-actions"><Button onClick={save} disabled={busy}>Save</Button><Button onClick={validate} disabled={busy}>Validate</Button><Button tone="primary" onClick={() => setConfirmApply(true)} disabled={busy}>Apply atomically</Button></div> : null}
            </div></> : <EmptyState icon="changesets" title="Choose or create a changeset" copy="Group catalog changes here when they must become visible together." action={<Button icon="plus" onClick={create}>New changeset</Button>} />}
        </div>
      </section>
      {confirmApply ? <StepUpDialog action="this atomic catalog changeset" onCancel={() => setConfirmApply(false)} onApproved={apply} /> : null}
    </div>
  );
}

function parseOperations(value: string, tolerateInvalid = false): SourceChange[] {
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) throw new Error('Operations must be a JSON array.');
    return parsed as SourceChange[];
  } catch (caught) {
    if (tolerateInvalid) return [];
    throw caught;
  }
}
