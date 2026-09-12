'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { apiFetch, apiFetchWithMeta } from '@/lib/client-api';
import { editorDraftSnapshot, finalizeEditorDraft, prepareDraftPublish, publishSavedEditorDraft, saveAndAdoptEditorDraft, validateEditorDraft, type DraftEditorAction, type PreparedDraftPublish, type SourceDraftEditorSnapshot } from '@/lib/source-draft-publish';
import type { SourceCapabilities, SourceDraft, SourceHead, SourceOperationalMode, SourceOperationalModeResult, SourceRevision, ValidationResult } from '@/lib/types';
import { Icon } from './icons';
import { StepUpDialog } from './step-up-dialog';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, Textarea, formatDate } from './ui';

type EditorTarget = { api: string; displayName: string };
type EditorState = SourceDraftEditorSnapshot & { target: EditorTarget; validation: ValidationResult | null };
type PendingPublish = PreparedDraftPublish & { target: EditorTarget; ticket: ActionTicket };
type PendingMode = { target: EditorTarget; mode: SourceOperationalMode; ticket: ActionTicket };
type PreviewOperation = 'home' | 'featured' | 'search';
// Each request object is a generation, even when retrying/resetting the same URL.
type HistoryRequest = { api: string; beforeRevision: string | null };
type HistoryWindow = { request: HistoryRequest } & (
  | { status: 'ready'; revisions: SourceRevision[]; nextBefore: string | null }
  | { status: 'error'; message: string }
);
type RevisionTarget = { request: HistoryRequest; revisionNumber: number };

export function SourcesView() {
  const [sources, setSources] = useState<SourceHead[] | null>(null);
  const [capabilities, setCapabilities] = useState<SourceCapabilities | null>(null);
  const [selectedApi, setSelectedApi] = useState('');
  const [historyRequest, setHistoryRequest] = useState<HistoryRequest | null>(null);
  const [historyWindow, setHistoryWindow] = useState<HistoryWindow | null>(null);
  const historyRequestRef = useRef<HistoryRequest | null>(null);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [pendingPublish, setPendingPublish] = useState<PendingPublish | null>(null);
  const [pendingMode, setPendingMode] = useState<PendingMode | null>(null);
  const [previewFixture, setPreviewFixture] = useState('');
  const [previewOutput, setPreviewOutput] = useState('');
  const [previewOperation, setPreviewOperation] = useState<PreviewOperation>('home');
  const [previewQuery, setPreviewQuery] = useState('');
  const [previewPage, setPreviewPage] = useState(1);
  const owner = useActionOwner();

  const requestHistory = useCallback((api: string, beforeRevision: string | null = null) => {
    const request = { api, beforeRevision };
    // Invalidate continuations/actions synchronously, before passive effect cleanup.
    historyRequestRef.current = request;
    setHistoryRequest(request);
  }, []);

  const load = useCallback(async () => {
    const isCurrent = owner.captureLifetime();
    // Authoring refresh invalidates an outstanding older window immediately, even
    // while the independent source-head/capability refresh is still in flight.
    const api = historyRequestRef.current?.api;
    if (api) requestHistory(api);
    try {
      const [items, vocabulary] = await Promise.all([
        apiFetch<SourceHead[]>('sources'),
        apiFetch<SourceCapabilities>('source-studio/capabilities'),
      ]);
      if (!isCurrent()) return;
      setSources(items);
      setCapabilities(vocabulary);
      if (!historyRequestRef.current && items[0]) {
        setSelectedApi(items[0].api);
        requestHistory(items[0].api);
      }
    } catch (caught) {
      if (isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not load sources.');
    }
  }, [owner, requestHistory]);

  useEffect(() => {
    // The initial catalog response selects the first source/history window.
    void load();
  }, [load]);
  useEffect(() => {
    if (!historyRequest) return;
    const isMounted = owner.captureLifetime();
    const controller = new AbortController();
    let active = true;
    const isCurrent = () => active && isMounted() && historyRequestRef.current === historyRequest;
    const before = historyRequest.beforeRevision === null ? '' : `&beforeRevision=${encodeURIComponent(historyRequest.beforeRevision)}`;
    void apiFetchWithMeta<SourceRevision[]>(`sources/${encodeURIComponent(historyRequest.api)}/revisions?size=20${before}`, { signal: controller.signal })
      .then((result) => {
        if (!isCurrent()) return;
        setHistoryWindow({ request: historyRequest, status: 'ready', revisions: result.data, nextBefore: result.historyNextBefore ?? null });
      })
      .catch((caught: unknown) => {
        if (!isCurrent()) return;
        setHistoryWindow({ request: historyRequest, status: 'error', message: caught instanceof Error ? caught.message : 'Could not load source revisions.' });
      });
    // Loading is derived from request identity, so there is no unscoped finally
    // that can end the loading state of a newer request.
    return () => { active = false; controller.abort(); };
  }, [historyRequest, owner]);

  const selected = sources?.find((source) => source.api === selectedApi) ?? null;
  const currentHistory = historyRequest?.api === selectedApi && historyWindow?.request === historyRequest ? historyWindow : null;
  const historyLoading = selected !== null && currentHistory === null;
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (sources ?? []).filter((source) => !needle || `${source.api} ${source.displayName} ${source.language} ${source.status} ${source.operationalMode ?? ''}`.toLowerCase().includes(needle));
  }, [query, sources]);
  const counts = useMemo(() => ({
    enabled: sources?.filter((source) => source.operationalMode === 'enabled').length ?? 0,
    maintenance: sources?.filter((source) => source.operationalMode === 'under_maintenance').length ?? 0,
    disabled: sources?.filter((source) => source.operationalMode === 'disabled').length ?? 0,
  }), [sources]);
  const locked = busy || pendingPublish !== null || pendingMode !== null;
  const backgroundLocked = locked || editor !== null;

  function beginAction() {
    const ticket = owner.acquire();
    if (!ticket) return null;
    setBusy(true);
    setError('');
    setMessage('');
    setEditor((current) => current ? { ...current, validation: null } : null);
    return ticket;
  }

  function finishAction(ticket: ActionTicket, retainConfirmation = false) {
    if (!ticket.isCurrent()) return;
    if (!retainConfirmation) owner.release(ticket);
    setBusy(false);
  }

  function beginEditorAction() {
    if (!editor) return null;
    const ticket = beginAction();
    if (!ticket) return null;
    const target = editor.target;
    const action: DraftEditorAction = {
      api: target.api,
      current: editor,
      isCurrent: ticket.isCurrent,
      adopt: (saved) => setEditor({ ...saved, target, validation: null }),
    };
    return { ticket, target, action };
  }

  async function openEditor(from?: RevisionTarget) {
    if (!selected || editor || historyRequestRef.current?.api !== selected.api) return;
    if (from && (historyRequestRef.current !== from.request || from.request.api !== selected.api)) return;
    const target = { api: from?.request.api ?? selected.api, displayName: selected.displayName };
    const ticket = beginAction();
    if (!ticket) return;
    try {
      const result = await apiFetchWithMeta<SourceDraft>(`sources/${encodeURIComponent(target.api)}/editor-draft`, {
        method: 'POST',
        body: JSON.stringify(from === undefined ? {} : { fromRevision: from.revisionNumber }),
      });
      if (!result.etag) throw new Error('The backend did not return the required draft ETag.');
      if (!ticket.isCurrent()) return;
      setEditor({ ...editorDraftSnapshot(result.data, result.etag), target, validation: null });
    } catch (caught) {
      if (ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not open editor.');
    } finally {
      finishAction(ticket);
    }
  }

  async function saveDraft() {
    const work = beginEditorAction();
    if (!work) return;
    try {
      const saved = await saveAndAdoptEditorDraft(work.action);
      if (!saved || !work.ticket.isCurrent()) return;
      setMessage('Draft saved without changing the public catalog.');
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Draft save failed.');
    } finally {
      finishAction(work.ticket);
    }
  }

  async function validateDraft() {
    const work = beginEditorAction();
    if (!work) return;
    try {
      const result = await validateEditorDraft(work.action);
      if (!result || !work.ticket.isCurrent()) return;
      setEditor({ ...result.snapshot, target: work.target, validation: result.validation });
      setMessage(result.validation.valid ? 'Validation passed.' : 'Validation found blocking issues.');
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Validation failed.');
    } finally {
      finishAction(work.ticket);
    }
  }

  async function finalizeDraft() {
    const work = beginEditorAction();
    if (!work) return;
    try {
      const result = await finalizeEditorDraft(work.action);
      if (!result || !work.ticket.isCurrent()) return;
      setMessage('Immutable revision created. It is not published.');
      await load();
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Finalize failed.');
    } finally {
      finishAction(work.ticket);
    }
  }

  async function previewDraft() {
    if (!editor) return;
    const ticket = beginAction();
    if (!ticket) return;
    try {
      const result = await apiFetch<{ success: boolean; output: unknown; error: string | null; request: unknown }>('source-preview', {
        method: 'POST',
        body: JSON.stringify({
          sourceJson: editor.content,
          operation: previewOperation,
          page: previewPage,
          query: previewQuery,
          responseStatus: 200,
          responseBody: previewFixture,
        }),
      });
      if (!ticket.isCurrent()) return;
      setPreviewOutput(JSON.stringify(result, null, 2));
      setMessage(result.success ? 'Shared-engine preview completed.' : `Preview failed: ${result.error ?? 'unknown error'}`);
    } catch (caught) {
      if (ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Preview failed.');
    } finally {
      finishAction(ticket);
    }
  }

  async function preparePublish() {
    const work = beginEditorAction();
    if (!work) return;
    let prepared = false;
    try {
      const pending = await prepareDraftPublish(work.action);
      if (!pending || !work.ticket.isCurrent()) return;
      setPendingPublish({ ...pending, target: work.target, ticket: work.ticket });
      prepared = true;
    } catch (caught) {
      if (work.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Draft save failed.');
    } finally {
      finishAction(work.ticket, prepared);
    }
  }

  async function publishDraft() {
    const pending = pendingPublish;
    if (!pending || !pending.ticket.isCurrent()) throw new Error('This publication confirmation is no longer current.');
    let completed = false;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const publication = await publishSavedEditorDraft(pending, {
        isCurrent: pending.ticket.isCurrent,
        adopt: (saved) => setEditor({ ...saved, target: pending.target, validation: null }),
      });
      if (!publication || !pending.ticket.isCurrent()) return;
      completed = true;
      setPendingPublish(null);
      setMessage(`Published atomically in catalog revision ${publication.documentRevision}.`);
      await load();
    } finally {
      // A failed protected request leaves the saved confirmation available for a
      // deliberate retry, which the dialog verifies with a fresh password request.
      finishAction(pending.ticket, !completed);
    }
  }

  function prepareOperationalMode(mode: SourceOperationalMode) {
    if (!selected || editor || historyRequestRef.current?.api !== selected.api || selected.operationalMode === mode) return;
    const ticket = owner.acquire();
    if (!ticket) return;
    setError('');
    setMessage('');
    setPendingMode({ target: { api: selected.api, displayName: selected.displayName }, mode, ticket });
  }

  async function applyOperationalMode() {
    const pending = pendingMode;
    if (!pending || !pending.ticket.isCurrent()) throw new Error('This source mode confirmation is no longer current.');
    let completed = false;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await apiFetch<SourceOperationalModeResult>(
        `sources/${encodeURIComponent(pending.target.api)}/operational-mode`,
        { method: 'PUT', body: JSON.stringify({ mode: pending.mode }) },
      );
      if (!pending.ticket.isCurrent()) return;
      setMessage(result.noOp
        ? `${pending.target.displayName} is already ${modeLabel(result.mode).toLowerCase()}.`
        : `${pending.target.displayName} is now ${modeLabel(result.mode).toLowerCase()} in catalog revision ${result.documentRevision}.`);
      completed = true;
      setPendingMode(null);
      await load();
    } catch (caught) {
      if (pending.ticket.isCurrent()) setError(caught instanceof Error ? caught.message : 'Could not change the source mode.');
      throw caught;
    } finally {
      finishAction(pending.ticket, !completed);
    }
  }

  function cancelPublish() {
    if (pendingPublish && owner.release(pendingPublish.ticket)) setPendingPublish(null);
  }

  function cancelMode() {
    if (pendingMode && owner.release(pendingMode.ticket)) setPendingMode(null);
  }

  function selectSource(api: string) {
    if (editor || owner.isLocked() || historyRequestRef.current?.api === api) return;
    setSelectedApi(api);
    requestHistory(api);
  }

  function olderHistory() {
    if (editor || owner.isLocked() || currentHistory?.status !== 'ready' || !currentHistory.nextBefore
      || historyRequestRef.current !== currentHistory.request) return;
    requestHistory(currentHistory.request.api, currentHistory.nextBefore);
  }

  function latestHistory() {
    if (editor || owner.isLocked() || !historyRequest || historyRequest.beforeRevision === null
      || historyRequestRef.current !== historyRequest) return;
    requestHistory(historyRequest.api);
  }

  function retryHistory() {
    if (editor || owner.isLocked() || currentHistory?.status !== 'error'
      || historyRequestRef.current !== currentHistory.request) return;
    requestHistory(currentHistory.request.api, currentHistory.request.beforeRevision);
  }

  function closeEditor() {
    if (!owner.isLocked()) setEditor(null);
  }

  function updateContent(content: string) {
    if (!editor || owner.isLocked()) return;
    setEditor({ ...editor, content, validation: null });
  }

  function updateTopLevel(field: string, value: string | number) {
    if (!editor || owner.isLocked()) return;
    try {
      const parsed = JSON.parse(editor.content) as Record<string, unknown>;
      parsed[field] = value;
      setEditor({ ...editor, content: JSON.stringify(parsed, null, 2), validation: null });
    } catch {
      setError('Fix the JSON syntax before using the guided fields.');
    }
  }

  if (!sources || !capabilities) return error ? <div className="notice notice-error">{error}</div> : <Spinner label="Loading source catalog" />;

  return (
    <div className="view-stack source-studio">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="sources" /> SOURCE CONTROL</span><h2>Catalog sources</h2><p>Edit generic source definitions with server-side drafts. Bundled and legacy engines are visible as history only and cannot be published through this studio.</p></div><Button icon="edit" tone="primary" onClick={() => void openEditor()} disabled={!selected || backgroundLocked}>Edit selected source</Button></section>
      <section className="source-kpis">
        <div><small>Enabled</small><strong>{counts.enabled}</strong><span>available to apps</span></div>
        <div><small>Maintenance</small><strong>{counts.maintenance}</strong><span>visible, requests blocked</span></div>
        <div><small>Disabled</small><strong>{counts.disabled}</strong><span>removed from active app catalog</span></div>
        <div><small>Contract</small><strong>v{capabilities.sourceSchemaVersion}</strong><span>{capabilities.canonicalization}</span></div>
      </section>
      {!editor && message ? <div className="notice notice-success">{message}</div> : null}
      {!editor && error ? <div className="notice notice-error">{error}</div> : null}
      <section className="manager-grid">
        <div className="panel manager-list">
          <div className="source-search"><Input value={query} disabled={backgroundLocked} onChange={(event) => { if (!editor && !owner.isLocked()) setQuery(event.target.value); }} placeholder="Search source, language, status…" /></div>
          <div className="entity-list">
            {filtered.map((source) => <button className={`source-row${selectedApi === source.api ? ' selected' : ''}`} type="button" key={source.api} disabled={backgroundLocked} onClick={() => selectSource(source.api)}><span className="source-position">{source.position + 1}</span><div><strong>{source.displayName}</strong><small>{source.api} · {source.language}</small></div><StatusBadge status={source.operationalMode ? modeLabel(source.operationalMode) : source.status} /></button>)}
          </div>
        </div>
        <div className="panel manager-detail">
          {selected ? <><div className="detail-hero"><div><span className="eyebrow">{selected.engine.toUpperCase()} ENGINE</span><h3>{selected.displayName}</h3><p>{selected.baseUrl}</p></div><StatusBadge status={selected.operationalMode ? modeLabel(selected.operationalMode) : selected.status} /></div>
            <div className="operational-control"><div><span>APP AVAILABILITY</span><strong>Operational mode</strong><small>Publishes one signed catalog update. Foreground apps revalidate immediately and poll while active.</small></div>{selected.operationalMode ? <div className="mode-switch" role="radiogroup" aria-label={`Operational mode for ${selected.displayName}`}>{OPERATIONAL_MODES.map((mode) => <button type="button" role="radio" aria-checked={selected.operationalMode === mode} className={`mode-${mode}${selected.operationalMode === mode ? ' active' : ''}`} disabled={backgroundLocked || selected.operationalMode === mode} onClick={() => prepareOperationalMode(mode)} key={mode}>{modeLabel(mode)}</button>)}</div> : <span className="mode-unavailable">Managed through the advanced lifecycle workflow</span>}</div>
            <div className="detail-meta"><div><span>PUBLISHED REVISION</span><strong>{selected.currentPublishedRevisionNumber ?? '—'}</strong></div><div><span>LATEST REVISION</span><strong>{selected.latestRevisionNumber ?? '—'}</strong></div><div><span>UPDATED</span><strong>{formatDate(selected.updatedAt)}</strong></div></div>
            <div className="revision-heading"><div><span className="eyebrow">IMMUTABLE HISTORY</span><h4>Source revisions</h4></div><Button icon="edit" onClick={() => void openEditor()} disabled={backgroundLocked}>Open editor</Button></div>
            <nav className="detail-actions" aria-label="Source revision history">
              <Button onClick={olderHistory} disabled={backgroundLocked || currentHistory?.status !== 'ready' || !currentHistory.nextBefore}>Older</Button>
              <Button onClick={latestHistory} disabled={backgroundLocked || !historyRequest || historyRequest.beforeRevision === null}>Latest</Button>
            </nav>
            <div className="revision-list" aria-busy={historyLoading}>
              {historyLoading ? <Spinner label="Loading source revisions" /> : null}
              {currentHistory?.status === 'error' ? <div className="notice notice-error" role="alert">{currentHistory.message}<Button onClick={retryHistory} disabled={backgroundLocked}>Retry history</Button></div> : null}
              {currentHistory?.status === 'ready' ? currentHistory.revisions.length ? currentHistory.revisions.map((revision) => (
                <article className={revision.status === 'published' ? 'current' : ''} key={revision.revisionNumber}>
                  <span className="revision-number">r{revision.revisionNumber}</span>
                  <div><strong>{revision.status}</strong><small>{revision.checksum.slice(0, 16)}…</small><p>{formatDate(revision.createdAt)}</p></div>
                  <div className="revision-actions"><StatusBadge status={revision.valid === false ? 'invalid' : revision.status} />{revision.status === 'draft' ? <Button type="button" onClick={() => void openEditor({ request: currentHistory.request, revisionNumber: revision.revisionNumber })} disabled={backgroundLocked}>Open draft</Button> : null}</div>
                </article>
              )) : <EmptyState icon="history" title="No source revisions" copy={historyRequest?.beforeRevision ? 'There are no revisions before this window. Return to Latest to see recent history.' : 'This source has no immutable revisions yet.'} /> : null}
            </div></> : <EmptyState icon="sources" title="Select a source" copy="Choose a catalog source to inspect its immutable history." />}
        </div>
      </section>

      {editor ? <div className="editor-layer"><section className="source-editor">
        <header><div><span>SERVER DRAFT · {editor.etag}</span><h2>{editor.target.displayName}</h2></div><div><Button onClick={saveDraft} disabled={locked}>Save draft</Button><Button onClick={validateDraft} disabled={locked}>Validate</Button><Button onClick={finalizeDraft} disabled={locked}>Create revision</Button><Button tone="primary" onClick={preparePublish} disabled={locked}>Quick publish</Button><button className="editor-close" type="button" onClick={closeEditor} disabled={locked} aria-label="Close editor"><Icon name="close" /></button></div></header>
        {message ? <div className="notice notice-success">{message}</div> : null}
        {error ? <div className="notice notice-error">{error}</div> : null}
        <div className="source-editor-grid">
          <aside><h3>Guided fields</h3><p>These edit the same JSON shown on the right.</p>
            <Field label="Display name"><Input value={readTopLevel(editor.content, 'displayName')} disabled={locked} onChange={(event) => updateTopLevel('displayName', event.target.value)} /></Field>
            <Field label="Base URL"><Input value={readTopLevel(editor.content, 'baseUrl')} disabled={locked} onChange={(event) => updateTopLevel('baseUrl', event.target.value)} /></Field>
            <Field label="Language"><Input value={readTopLevel(editor.content, 'language')} disabled={locked} onChange={(event) => updateTopLevel('language', event.target.value)} /></Field>
            <Field label="Source revision"><Input type="number" min="1" value={readTopLevel(editor.content, 'sourceRevision')} disabled={locked} onChange={(event) => updateTopLevel('sourceRevision', Number(event.target.value))} /></Field>
            <div className="contract-card"><strong>Backend vocabulary</strong><small>{capabilities.transforms.length} transforms · {capabilities.paginationStrategies.length} pagination strategies</small><small>Max draft {Math.round(capabilities.editorDraftMaxBytes / 1024)} KiB · {capabilities.publicEnginePolicy}</small></div>
            <Field label="Preview operation"><select className="input" value={previewOperation} disabled={locked} onChange={(event) => { if (!owner.isLocked()) setPreviewOperation(event.target.value as PreviewOperation); }}><option value="home">Home</option><option value="featured">Featured</option><option value="search">Search</option></select></Field>
            {previewOperation === 'search' ? <Field label="Search query"><Input value={previewQuery} maxLength={500} disabled={locked} onChange={(event) => { if (!owner.isLocked()) setPreviewQuery(event.target.value); }} /></Field> : null}
            <Field label="Preview page"><Input type="number" min="1" max="10000" value={previewPage} disabled={locked} onChange={(event) => { if (!owner.isLocked()) setPreviewPage(Math.max(1, Number(event.target.value) || 1)); }} /></Field>
            <Field label={`${previewOperation} response fixture`} hint="Paste a saved HTML/JSON response. Preview never performs server-side network access."><Textarea value={previewFixture} disabled={locked} onChange={(event) => { if (!owner.isLocked()) setPreviewFixture(event.target.value); }} /></Field>
            <Button onClick={previewDraft} disabled={locked || !previewFixture}>Run shared-engine preview</Button>{previewOutput ? <pre className="preview-output">{previewOutput}</pre> : null}
          </aside>
          <main><div className="code-heading"><div><span>RAW SOURCE JSON</span><small>{new TextEncoder().encode(editor.content).length.toLocaleString()} bytes</small></div></div><Textarea className="source-code" spellCheck={false} value={editor.content} disabled={locked} onChange={(event) => updateContent(event.target.value)} />
            {editor.validation ? <div className={`validation-panel ${editor.validation.valid ? 'valid' : 'invalid'}`}><strong>{editor.validation.valid ? 'Validation passed' : `${editor.validation.errors.length} blocking issue(s)`}</strong>{[...editor.validation.errors, ...editor.validation.warnings].map((finding) => <p key={`${finding.code}-${finding.path}`}><code>{finding.code}</code> {finding.path}: {finding.message}</p>)}</div> : null}
          </main>
        </div>
      </section></div> : null}
      {pendingPublish ? <StepUpDialog action={`publishing ${pendingPublish.api}`} onCancel={cancelPublish} onApproved={publishDraft} /> : null}
      {pendingMode ? <StepUpDialog action={`setting ${pendingMode.target.api} to ${modeLabel(pendingMode.mode).toLowerCase()}`} onCancel={cancelMode} onApproved={applyOperationalMode} /> : null}
    </div>
  );
}

const OPERATIONAL_MODES: SourceOperationalMode[] = ['enabled', 'under_maintenance', 'disabled'];

function modeLabel(mode: SourceOperationalMode) {
  if (mode === 'under_maintenance') return 'Under maintenance';
  return mode[0].toUpperCase() + mode.slice(1);
}

function readTopLevel(content: string, key: string): string {
  try { return String((JSON.parse(content) as Record<string, unknown>)[key] ?? ''); } catch { return ''; }
}
