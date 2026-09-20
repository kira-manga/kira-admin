'use client';

import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { ApiError, captureAdminSession } from '@/lib/client-api';
import { complaintBatchStatuses, prepareComplaintBatchDeleteRequest, prepareComplaintBatchStatusRequest, type ComplaintBatchRequest } from '@/lib/complaint-batch-wire';
import type { ComplaintStatusTarget } from '@/lib/complaint-moderation-wire';
import { ComplaintReadClientError, fetchComplaintAdminSearch } from '@/lib/complaint-read-client';
import type { ParsedComplaintAdminPage } from '@/lib/complaint-read-wire';
import { complaintSearchStatuses, complaintSearchTypes, prepareComplaintAdminSearch, type ComplaintAdminSearchQuery } from '@/lib/complaint-search-wire';
import { copyComplaintSelection, visibleComplaintText } from '@/lib/complaint-text';
import { Button, Field, Input, Spinner, StatusBadge } from './ui';

type Filters = { text: string; status: string; type: string; ownership: string; updatedFrom: string; updatedBefore: string; limit: string };
type LoadedPage = { value: ParsedComplaintAdminPage; query: ComplaintAdminSearchQuery; index: number; isCurrent: () => boolean };
type Props = {
  generation: string; dataScopeId: string; disabled: boolean;
  onSelect: (target: { id: string; dataScopeId: string; generation: string }) => void;
  onPrepareBatch?: (request: ComplaintBatchRequest, generation: string) => boolean;
  onSessionExpired: () => void;
};
const messages = {
  UNAVAILABLE: 'Search is unavailable. The backend may not support complaint searches yet; no empty result is inferred.',
  SESSION_EXPIRED: 'Your session has expired. Sign in again.',
  UNAUTHORIZED: 'This search was not authorized. It does not confirm local session expiry.',
  FORBIDDEN: 'You do not have permission to search complaints.',
  INVALID_RESPONSE: 'The search request, cursor or response is invalid. Check the filters and restart the search.',
  NETWORK: 'Search could not be completed. Restart explicitly to try again.',
};
const textStyle = { whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' } as const;

/** One in-memory page, one active read. The parent keys this owner by G/scope and removes it for retained operations. */
export function ComplaintSearchView({ generation, dataScopeId, disabled, onSelect, onPrepareBatch, onSessionExpired }: Props) {
  const [filters, setFilters] = useState<Filters>({ text: '', status: '', type: '', ownership: '', updatedFrom: '', updatedBefore: '', limit: '50' });
  const filterRef = useRef(filters);
  const [page, setPage] = useState<LoadedPage | null>(null);
  const pageRef = useRef<LoadedPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const owner = useActionOwner();
  const active = useRef<{ ticket: ActionTicket; controller: AbortController } | null>(null);
  const [selected, setSelected] = useState<readonly string[]>([]);
  const selectedRef = useRef<readonly string[]>([]);
  const [batchStatus, setBatchStatus] = useState<ComplaintStatusTarget>('RESOLVED');
  const batchStatusRef = useRef<ComplaintStatusTarget>('RESOLVED');
  const captured = useRef(false);

  useLayoutEffect(() => () => { active.current?.controller.abort(); active.current = null; }, []);
  useLayoutEffect(() => { if (page) resultHeading.current?.focus(); }, [page]);

  function invalidate() {
    const pending = active.current;
    active.current = null;
    if (pending) { owner.release(pending.ticket); pending.controller.abort(); }
    selectedRef.current = []; setSelected([]);
    pageRef.current = null; setPage(null); setError(''); setLoading(false);
  }

  function change(change: Partial<Filters>) {
    if (disabled || captured.current) return;
    invalidate();
    filterRef.current = { ...filterRef.current, ...change };
    setFilters(filterRef.current);
  }

  async function load(query: ComplaintAdminSearchQuery, index: number) {
    if (disabled || captured.current) return;
    const ticket = owner.acquire();
    if (!ticket) return;
    const controller = new AbortController();
    active.current = { ticket, controller };
    selectedRef.current = []; setSelected([]);
    pageRef.current = null; setPage(null); setError(''); setLoading(true);
    let session: ReturnType<typeof captureAdminSession> | undefined;
    try {
      session = captureAdminSession();
      if (session.generation !== generation) return;
      const value = await fetchComplaintAdminSearch(query, controller.signal);
      if (!ticket.isCurrent()) return;
      if (!session.isCurrent()) { onSessionExpired(); return; }
      const next = { value, query, index, isCurrent: session.isCurrent };
      pageRef.current = next; setPage(next);
    } catch (caught) {
      if (!ticket.isCurrent()) return;
      const reason = session && !session.isCurrent() || caught instanceof ApiError && caught.status === 401 ? 'SESSION_EXPIRED'
        : caught instanceof ComplaintReadClientError ? caught.reason : 'NETWORK';
      setError(messages[reason]);
      if (reason === 'SESSION_EXPIRED') onSessionExpired();
    } finally {
      if (ticket.isCurrent()) { active.current = null; owner.release(ticket); setLoading(false); }
    }
  }

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (disabled || captured.current || owner.isLocked()) return;
    try {
      const value = filterRef.current;
      const query = prepareComplaintAdminSearch({ dataScopeId, text: value.text,
        status: value.status === '' ? null : value.status as ComplaintAdminSearchQuery['status'],
        type: value.type === '' ? null : value.type as ComplaintAdminSearchQuery['type'],
        ownership: value.ownership === '' ? null : value.ownership as ComplaintAdminSearchQuery['ownership'],
        updatedFrom: value.updatedFrom || null, updatedBefore: value.updatedBefore || null, limit: Number(value.limit),
      });
      void load(query, 1);
    } catch { invalidate(); setError(messages.INVALID_RESPONSE); }
  }

  function nextPage() {
    const current = pageRef.current;
    if (disabled || captured.current || !current || !current.isCurrent() || !current.value.nextCursor) return;
    void load(Object.freeze({ ...current.query, cursor: current.value.nextCursor }), current.index + 1);
  }

  function select(id: string) {
    const current = pageRef.current;
    if (disabled || captured.current || owner.isLocked() || !current || !current.isCurrent() || !current.value.items.some((item) => item.id === id)) return;
    onSelect({ id, dataScopeId: current.query.dataScopeId, generation }); // Captured page scope, not later edited inputs.
  }

  function selectBatch(id: string, checked: boolean) {
    const current = pageRef.current;
    if (disabled || captured.current || owner.isLocked() || !current || !current.isCurrent()
      || !current.value.items.some((item) => item.id === id && item.kind !== 'NOTICE' && item.ownership === 'INSTALLATION')) return;
    const next = checked ? [...new Set([...selectedRef.current, id])] : selectedRef.current.filter((value) => value !== id);
    if (next.length > 50) return;
    selectedRef.current = next; setSelected(next);
  }

  function prepareBatch(action: ComplaintBatchRequest['action']) {
    const current = pageRef.current;
    if (disabled || captured.current || owner.isLocked() || !onPrepareBatch || !current || !current.isCurrent()) return;
    try {
      const targets = selectedRef.current.map((id) => {
        const item = current.value.items.find((item) => item.id === id);
        if (!item || item.kind === 'NOTICE') throw new Error();
        return { id: item.id, actionTag: item.actionTag, kind: item.kind, ownership: item.ownership };
      });
      const request = action === 'STATUS'
        ? prepareComplaintBatchStatusRequest(targets, batchStatusRef.current, current.query.dataScopeId, crypto.randomUUID())
        : prepareComplaintBatchDeleteRequest(targets, current.query.dataScopeId, crypto.randomUUID());
      // Synchronous parent CAS owns the complete immutable request above navigation before another event.
      if (onPrepareBatch(request, generation)) captured.current = true;
    } catch { setError('Select 1–50 current-page complaints and a valid batch action before preparing one atomic batch.'); }
  }

  return <section className="panel" aria-label="Complaint search">
    <div className="panel-heading"><div><h3>Search complaints</h3><p>Use the TEST scope above. Search text and cursors stay in memory, never URLs or browser storage.</p></div></div>
    <form onSubmit={search} method="post" action="/api/backend/complaints/search" autoComplete="off">
      <fieldset aria-label="Complaint search filters" disabled={disabled} className="form-grid" style={{ border: 0, margin: 0, padding: '1.25rem', minWidth: 0 }}>
        <Field label="Search text" hint="Up to 100 Unicode code points/400 UTF-8 bytes after normalization; empty searches all matching rows." wide>
          <Input type="search" name="complaintSearchText" value={filters.text} maxLength={400} dir="auto" style={textStyle}
            autoComplete="off" spellCheck={false} onCopy={copyComplaintSelection} onChange={(event) => change({ text: event.target.value })} />
        </Field>
        <Field label="Status filter"><select className="input" name="complaintSearchStatus" value={filters.status} onChange={(event) => change({ status: event.target.value })}>
          <option value="">All statuses</option>{complaintSearchStatuses.map((value) => <option key={value} value={value}>{value}</option>)}
        </select></Field>
        <Field label="Type filter"><select className="input" name="complaintSearchType" value={filters.type} onChange={(event) => change({ type: event.target.value })}>
          <option value="">All types</option>{complaintSearchTypes.map((value) => <option key={value} value={value}>{value}</option>)}
        </select></Field>
        <Field label="Ownership filter"><select className="input" name="complaintSearchOwnership" value={filters.ownership} onChange={(event) => change({ ownership: event.target.value })}>
          <option value="">All ownership</option><option value="INSTALLATION">INSTALLATION</option><option value="SYSTEM">SYSTEM</option>
        </select></Field>
        <Field label="Page size (1–50)"><Input type="number" name="complaintSearchLimit" min={1} max={50} step={1} value={filters.limit} onChange={(event) => change({ limit: event.target.value })} /></Field>
        <Field label="Updated from (inclusive, UTC)" hint="YYYY-MM-DDTHH:mm:ss[.ffffff]Z, or empty."><Input name="complaintSearchFrom" value={filters.updatedFrom} maxLength={27} placeholder="2026-09-20T00:00:00Z" onChange={(event) => change({ updatedFrom: event.target.value })} /></Field>
        <Field label="Updated before (exclusive, UTC)" hint="Must be later than Updated from."><Input name="complaintSearchBefore" value={filters.updatedBefore} maxLength={27} placeholder="2026-09-21T00:00:00Z" onChange={(event) => change({ updatedBefore: event.target.value })} /></Field>
        <p className="field-wide">Order: most recently updated first. Changing a filter discards the page/cursor; each search restarts at the first page.</p>
        {visibleComplaintText(filters.text) !== filters.text ? <p className="field-wide">Visible search controls: <bdi dir="auto" style={textStyle}>{visibleComplaintText(filters.text)}</bdi></p> : null}
        <Button type="submit" tone="primary" disabled={loading}>Search complaints</Button>
        {loading ? <Button type="button" onClick={invalidate}>Cancel search</Button> : null}
      </fieldset>
    </form>
    <div aria-live="polite" aria-atomic="true" style={{ padding: '0 1.25rem' }}>
      {loading ? <Spinner label="Searching complaints" /> : null}
      {error ? <p role="alert" className="notice notice-error">{error}</p> : null}
    </div>
    {page ? <section aria-label="Complaint search results" style={{ padding: '0 1.25rem 1.25rem' }}>
      <h4 tabIndex={-1} ref={resultHeading}>Page {page.index}: {page.value.items.length} results (not a total)</h4>
      {page.value.items.length === 0 ? <p>{page.index === 1 ? 'No complaints match these filters.' : 'No complaints on this page. Search again to refresh current results.'}</p> : <ul style={{ padding: 0, listStyle: 'none' }}>
        {page.value.items.map((item) => <li key={item.id} style={{ minWidth: 0, marginBlock: '1rem' }}>
          <h4><bdi dir="auto" style={textStyle}>{visibleComplaintText(item.kind === 'NOTICE' ? 'System notice' : item.subject ?? 'Notice reply')}</bdi></h4>
          <StatusBadge status={item.status} /><p>{item.kind} · {item.ownership} · Version {item.version}</p>
          <p>Updated <time dateTime={item.updatedAt}>{item.updatedAt}</time></p>
          {onPrepareBatch && item.kind !== 'NOTICE' && item.ownership === 'INSTALLATION' ? <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
            <Input type="checkbox" style={{ width: 'auto' }} aria-label={`Select complaint ${item.id} for atomic batch`}
              checked={selected.includes(item.id)} disabled={disabled || loading} onChange={(event) => selectBatch(item.id, event.target.checked)} />Select for atomic batch
          </label> : null}
          <Button type="button" style={{ maxWidth: '100%', overflowWrap: 'anywhere' }} disabled={disabled || loading} onClick={() => select(item.id)}>Open detail for {item.id}</Button>
        </li>)}
      </ul>}
      {onPrepareBatch && page.value.items.some((item) => item.kind !== 'NOTICE' && item.ownership === 'INSTALLATION') ? <form aria-label="Atomic complaint batch"
        onSubmit={(event) => { event.preventDefault(); prepareBatch('STATUS'); }} method="post" action="/api/backend/complaints/batch" autoComplete="off">
        <p>{selected.length} selected on this page only. Changing filters, scope or page clears selection. Each action is one all-or-none batch, never separate per-target requests.</p>
        <Field label="Status for selected complaints"><select className="input" name="complaintBatchStatus" value={batchStatus} disabled={disabled || loading}
          onChange={(event) => { if (!disabled && !captured.current) { batchStatusRef.current = event.target.value as ComplaintStatusTarget; setBatchStatus(batchStatusRef.current); } }}>
          {complaintBatchStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
        </select></Field>
        <p>Status changes include no deletion or closure. One invalid, unchanged or stale target rejects the entire status batch.</p>
        <Button type="submit" tone="primary" disabled={disabled || loading || selected.length === 0}>Prepare atomic status batch</Button>
        <p className="notice notice-warning">Permanent deletion applies only to selected reports/replies, never unselected children, installations or credentials. After authorization it cannot be undone or canceled. Review the complete capture before confirming.</p>
        <Button type="button" tone="danger" disabled={disabled || loading || selected.length === 0} onClick={() => prepareBatch('DELETE')}>Prepare permanent delete batch</Button>
      </form> : null}
      <Button type="button" disabled={disabled || loading || page.value.nextCursor === null} onClick={nextPage}>Next page</Button>
      {page.value.nextCursor === null ? <p>End of this search. Search again to restart.</p> : null}
    </section> : null}
  </section>;
}
