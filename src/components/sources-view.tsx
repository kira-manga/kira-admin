'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';

import { apiFetch, apiFetchWithMeta } from '@/lib/client-api';
import type { SourceCapabilities, SourceDraft, SourceHead, SourceRevision, ValidationResult } from '@/lib/types';
import { Icon } from './icons';
import { StepUpDialog } from './step-up-dialog';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, Textarea, formatDate } from './ui';

type EditorState = { draft: SourceDraft; etag: string; content: string; validation: ValidationResult | null };
type PreviewOperation = 'home' | 'featured' | 'search';

export function SourcesView() {
  const [sources, setSources] = useState<SourceHead[] | null>(null);
  const [capabilities, setCapabilities] = useState<SourceCapabilities | null>(null);
  const [selectedApi, setSelectedApi] = useState('');
  const [revisions, setRevisions] = useState<SourceRevision[]>([]);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmPublish, setConfirmPublish] = useState(false);
  const [previewFixture, setPreviewFixture] = useState('');
  const [previewOutput, setPreviewOutput] = useState('');
  const [previewOperation, setPreviewOperation] = useState<PreviewOperation>('home');
  const [previewQuery, setPreviewQuery] = useState('');
  const [previewPage, setPreviewPage] = useState(1);

  const load = useCallback(async () => {
    try {
      const [items, vocabulary] = await Promise.all([
        apiFetch<SourceHead[]>('sources'),
        apiFetch<SourceCapabilities>('source-studio/capabilities'),
      ]);
      setSources(items);
      setCapabilities(vocabulary);
      setSelectedApi((current) => current || items[0]?.api || '');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load sources.');
    }
  }, []);

  useEffect(() => {
    // State changes only after the external requests resolve.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  useEffect(() => {
    if (!selectedApi) return;
    void apiFetch<SourceRevision[]>(`sources/${encodeURIComponent(selectedApi)}/revisions`)
      .then(setRevisions)
      .catch((caught: Error) => setError(caught.message));
  }, [selectedApi, sources]);

  const selected = sources?.find((source) => source.api === selectedApi) ?? null;
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (sources ?? []).filter((source) => !needle || `${source.api} ${source.displayName} ${source.language} ${source.status}`.toLowerCase().includes(needle));
  }, [query, sources]);
  const counts = useMemo(() => ({
    active: sources?.filter((source) => source.status === 'active').length ?? 0,
    withheld: sources?.filter((source) => source.status === 'withheld').length ?? 0,
    generic: sources?.filter((source) => source.engine === 'generic').length ?? 0,
  }), [sources]);

  async function openEditor() {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      const result = await apiFetchWithMeta<SourceDraft>(`sources/${encodeURIComponent(selected.api)}/editor-draft`, {
        method: 'POST',
        body: '{}',
      });
      if (!result.etag) throw new Error('The backend did not return the required draft ETag.');
      setEditor({ draft: result.data, etag: result.etag, content: pretty(result.data.content), validation: null });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not open editor.');
    } finally {
      setBusy(false);
    }
  }

  async function saveDraft() {
    if (!editor || !selected) return;
    setBusy(true);
    setError('');
    try {
      const result = await apiFetchWithMeta<SourceDraft>(`sources/${encodeURIComponent(selected.api)}/editor-draft`, {
        method: 'PUT',
        headers: { 'If-Match': editor.etag },
        body: JSON.stringify({ content: editor.content }),
      });
      if (!result.etag) throw new Error('The backend did not return the updated draft ETag.');
      setEditor({ draft: result.data, etag: result.etag, content: editor.content, validation: null });
      setMessage('Draft saved without changing the public catalog.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Draft save failed.');
    } finally {
      setBusy(false);
    }
  }

  async function validateDraft() {
    if (!editor || !selected) return;
    setBusy(true);
    try {
      const validation = await apiFetch<ValidationResult>(`sources/${encodeURIComponent(selected.api)}/editor-draft/validate`, {
        method: 'POST',
        headers: { 'If-Match': editor.etag },
      });
      setEditor({ ...editor, validation });
      setMessage(validation.valid ? 'Validation passed.' : 'Validation found blocking issues.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Validation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function finalizeDraft() {
    if (!editor || !selected) return;
    setBusy(true);
    try {
      const result = await apiFetchWithMeta<{ draft: SourceDraft }>(`sources/${encodeURIComponent(selected.api)}/editor-draft/finalize`, {
        method: 'POST',
        headers: { 'If-Match': editor.etag },
      });
      if (!result.etag) throw new Error('The backend did not return the updated draft ETag.');
      setEditor({ draft: result.data.draft, etag: result.etag, content: pretty(result.data.draft.content), validation: null });
      setMessage('Immutable revision created. It is not published.');
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Finalize failed.');
    } finally {
      setBusy(false);
    }
  }

  async function previewDraft() {
    if (!editor) return;
    setBusy(true);
    setError('');
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
      setPreviewOutput(JSON.stringify(result, null, 2));
      setMessage(result.success ? 'Shared-engine preview completed.' : `Preview failed: ${result.error ?? 'unknown error'}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Preview failed.');
    } finally {
      setBusy(false);
    }
  }

  async function publishDraft() {
    if (!editor || !selected) return;
    setBusy(true);
    try {
      const result = await apiFetchWithMeta<{ draft: SourceDraft; publication: { documentRevision: number } }>(
        `sources/${encodeURIComponent(selected.api)}/editor-draft/publish`,
        { method: 'POST', headers: { 'If-Match': editor.etag } },
      );
      if (!result.etag) throw new Error('The backend did not return the updated draft ETag.');
      setEditor({ draft: result.data.draft, etag: result.etag, content: pretty(result.data.draft.content), validation: null });
      setConfirmPublish(false);
      setMessage(`Published atomically in catalog revision ${result.data.publication.documentRevision}.`);
      await load();
    } finally {
      setBusy(false);
    }
  }

  function updateTopLevel(field: string, value: string | number) {
    if (!editor) return;
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
      <section className="view-heading"><div><span className="eyebrow"><Icon name="sources" /> SOURCE CONTROL</span><h2>Catalog sources</h2><p>Edit generic source definitions with server-side drafts. Bundled and legacy engines are visible as history only and cannot be published through this studio.</p></div><Button icon="edit" tone="primary" onClick={openEditor} disabled={!selected || busy}>Edit selected source</Button></section>
      <section className="source-kpis">
        <div><small>Active</small><strong>{counts.active}</strong><span>available to apps</span></div>
        <div><small>Withheld</small><strong>{counts.withheld}</strong><span>unavailable to apps</span></div>
        <div><small>Generic</small><strong>{counts.generic}</strong><span>publishable engine</span></div>
        <div><small>Contract</small><strong>v{capabilities.sourceSchemaVersion}</strong><span>{capabilities.canonicalization}</span></div>
      </section>
      {message ? <div className="notice notice-success">{message}</div> : null}
      {error ? <div className="notice notice-error">{error}</div> : null}
      <section className="manager-grid">
        <div className="panel manager-list">
          <div className="source-search"><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search source, language, status…" /></div>
          <div className="entity-list">
            {filtered.map((source) => <button className={`source-row${selectedApi === source.api ? ' selected' : ''}`} type="button" key={source.api} onClick={() => setSelectedApi(source.api)}><span className="source-position">{source.position + 1}</span><div><strong>{source.displayName}</strong><small>{source.api} · {source.language}</small></div><StatusBadge status={source.status} /></button>)}
          </div>
        </div>
        <div className="panel manager-detail">
          {selected ? <><div className="detail-hero"><div><span className="eyebrow">{selected.engine.toUpperCase()} ENGINE</span><h3>{selected.displayName}</h3><p>{selected.baseUrl}</p></div><StatusBadge status={selected.status} /></div>
            <div className="detail-meta"><div><span>PUBLISHED REVISION</span><strong>{selected.currentPublishedRevisionNumber ?? '—'}</strong></div><div><span>LATEST REVISION</span><strong>{selected.latestRevisionNumber ?? '—'}</strong></div><div><span>UPDATED</span><strong>{formatDate(selected.updatedAt)}</strong></div></div>
            <div className="revision-heading"><div><span className="eyebrow">IMMUTABLE HISTORY</span><h4>Source revisions</h4></div><Button icon="edit" onClick={openEditor}>Open editor</Button></div>
            <div className="revision-list">{revisions.map((revision) => <article className={revision.status === 'published' ? 'current' : ''} key={revision.revisionNumber}><span className="revision-number">r{revision.revisionNumber}</span><div><strong>{revision.status}</strong><small>{revision.checksum.slice(0, 16)}…</small><p>{formatDate(revision.createdAt)}</p></div><StatusBadge status={revision.valid === false ? 'invalid' : revision.status} /></article>)}</div></> : <EmptyState icon="sources" title="Select a source" copy="Choose a catalog source to inspect its immutable history." />}
        </div>
      </section>

      {editor && selected ? <div className="editor-layer"><section className="source-editor">
        <header><div><span>SERVER DRAFT · {editor.etag}</span><h2>{selected.displayName}</h2></div><div><Button onClick={saveDraft} disabled={busy}>Save draft</Button><Button onClick={validateDraft} disabled={busy}>Validate</Button><Button onClick={finalizeDraft} disabled={busy}>Create revision</Button><Button tone="primary" onClick={() => setConfirmPublish(true)} disabled={busy}>Quick publish</Button><button className="editor-close" type="button" onClick={() => setEditor(null)} aria-label="Close editor"><Icon name="close" /></button></div></header>
        <div className="source-editor-grid">
          <aside><h3>Guided fields</h3><p>These edit the same JSON shown on the right.</p><Field label="Display name"><Input value={readTopLevel(editor.content, 'displayName')} onChange={(event) => updateTopLevel('displayName', event.target.value)} /></Field><Field label="Base URL"><Input value={readTopLevel(editor.content, 'baseUrl')} onChange={(event) => updateTopLevel('baseUrl', event.target.value)} /></Field><Field label="Language"><Input value={readTopLevel(editor.content, 'language')} onChange={(event) => updateTopLevel('language', event.target.value)} /></Field><Field label="Source revision"><Input type="number" min="1" value={readTopLevel(editor.content, 'sourceRevision')} onChange={(event) => updateTopLevel('sourceRevision', Number(event.target.value))} /></Field><div className="contract-card"><strong>Backend vocabulary</strong><small>{capabilities.transforms.length} transforms · {capabilities.paginationStrategies.length} pagination strategies</small><small>Max draft {Math.round(capabilities.editorDraftMaxBytes / 1024)} KiB · {capabilities.publicEnginePolicy}</small></div><Field label="Preview operation"><select className="input" value={previewOperation} onChange={(event) => setPreviewOperation(event.target.value as PreviewOperation)}><option value="home">Home</option><option value="featured">Featured</option><option value="search">Search</option></select></Field>{previewOperation === 'search' ? <Field label="Search query"><Input value={previewQuery} maxLength={500} onChange={(event) => setPreviewQuery(event.target.value)} /></Field> : null}<Field label="Preview page"><Input type="number" min="1" max="10000" value={previewPage} onChange={(event) => setPreviewPage(Math.max(1, Number(event.target.value) || 1))} /></Field><Field label={`${previewOperation} response fixture`} hint="Paste a saved HTML/JSON response. Preview never performs server-side network access."><Textarea value={previewFixture} onChange={(event) => setPreviewFixture(event.target.value)} /></Field><Button onClick={previewDraft} disabled={busy || !previewFixture}>Run shared-engine preview</Button>{previewOutput ? <pre className="preview-output">{previewOutput}</pre> : null}</aside>
          <main><div className="code-heading"><div><span>RAW SOURCE JSON</span><small>{new TextEncoder().encode(editor.content).length.toLocaleString()} bytes</small></div></div><Textarea className="source-code" spellCheck={false} value={editor.content} onChange={(event) => setEditor({ ...editor, content: event.target.value, validation: null })} />
            {editor.validation ? <div className={`validation-panel ${editor.validation.valid ? 'valid' : 'invalid'}`}><strong>{editor.validation.valid ? 'Validation passed' : `${editor.validation.errors.length} blocking issue(s)`}</strong>{[...editor.validation.errors, ...editor.validation.warnings].map((finding) => <p key={`${finding.code}-${finding.path}`}><code>{finding.code}</code> {finding.path}: {finding.message}</p>)}</div> : null}
          </main>
        </div>
      </section></div> : null}
      {confirmPublish ? <StepUpDialog action={`publishing ${selected?.api}`} onCancel={() => setConfirmPublish(false)} onApproved={publishDraft} /> : null}
    </div>
  );
}

function pretty(content: string) {
  try { return JSON.stringify(JSON.parse(content), null, 2); } catch { return content; }
}

function readTopLevel(content: string, key: string): string {
  try { return String((JSON.parse(content) as Record<string, unknown>)[key] ?? ''); } catch { return ''; }
}
