'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';

import { apiFetch } from '@/lib/client-api';
import { buildFeaturedToggleItems } from '@/lib/tutorial-featured-order';
import type { AdminCategory, AdminTutorial, TutorialMedia, TutorialRevision } from '@/lib/types';
import { Icon } from './icons';
import { TutorialEditor } from './tutorial-editor';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, formatDate } from './ui';

export function TutorialsView() {
  const [tutorials, setTutorials] = useState<AdminTutorial[]>([]);
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [media, setMedia] = useState<TutorialMedia[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<TutorialRevision[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    try {
      const [tutorialData, categoryData, mediaData] = await Promise.all([apiFetch<AdminTutorial[]>('tutorials'), apiFetch<AdminCategory[]>('tutorial-categories'), apiFetch<TutorialMedia[]>('tutorial-media')]);
      setTutorials(tutorialData.sort((a, b) => a.position - b.position)); setCategories(categoryData); setMedia(mediaData);
      setSelectedId((current) => current ?? tutorialData[0]?.id ?? null);
    } catch (caught) { setError((caught as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    // Data is applied only after the admin API request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  useEffect(() => {
    if (!selectedId) return;
    apiFetch<TutorialRevision[]>(`tutorials/${selectedId}/revisions`).then(setRevisions).catch((caught: Error) => setError(caught.message));
  }, [selectedId]);
  const selected = tutorials.find((item) => item.id === selectedId) ?? null;
  const latestRevision = [...revisions].sort((a, b) => b.revision - a.revision)[0];

  async function refreshSelected() {
    await load();
    if (selectedId) setRevisions(await apiFetch<TutorialRevision[]>(`tutorials/${selectedId}/revisions`));
  }
  async function mutate(action: () => Promise<unknown>, success: string) {
    setBusy(true); setError(''); setMessage('');
    try { await action(); await refreshSelected(); setMessage(success); }
    catch (caught) { setError((caught as Error).message); throw caught; }
    finally { setBusy(false); }
  }

  async function createTutorial(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true); setError('');
    try {
      const created = await apiFetch<AdminTutorial>('tutorials', { method: 'POST', body: JSON.stringify({ slug: data.get('slug'), position: tutorials.length, featuredPosition: data.get('featured') === 'on' ? tutorials.filter((item) => item.featuredPosition !== null).length : null }) });
      await load(); setSelectedId(created.id); setCreateOpen(false); setMessage('Tutorial created. Add its first revision when you are ready.');
    } catch (caught) { setError((caught as Error).message); }
    finally { setBusy(false); }
  }

  async function saveRevision(draft: Omit<TutorialRevision, 'id' | 'revision' | 'createdBy' | 'createdAt'>, publish: boolean) {
    if (!selected) return;
    try {
      await mutate(async () => {
        const revision = await apiFetch<TutorialRevision>(`tutorials/${selected.id}/revisions`, { method: 'POST', body: JSON.stringify(draft) });
        if (publish) await apiFetch(`tutorials/${selected.id}/revisions/${revision.revision}/publish`, { method: 'POST' });
      }, publish ? 'Revision saved and published.' : 'Draft revision saved.');
      setEditorOpen(false);
    } catch { /* mutation already surfaces the API message */ }
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction; if (target < 0 || target >= tutorials.length) return;
    const reordered = [...tutorials]; [reordered[index], reordered[target]] = [reordered[target], reordered[index]]; setTutorials(reordered);
    try { await mutate(() => apiFetch('tutorials/reorder', { method: 'POST', body: JSON.stringify({ items: reordered.map((item, position) => ({ id: item.id, position, featuredPosition: item.featuredPosition })) }) }), 'Tutorial order updated.'); } catch { /* shown above */ }
  }

  async function toggleFeatured() {
    if (!selected) return;
    const next = buildFeaturedToggleItems(tutorials, selected);
    try { await mutate(() => apiFetch('tutorials/reorder', { method: 'POST', body: JSON.stringify({ items: next }) }), selected.featuredPosition === null ? 'Tutorial added to the homepage.' : 'Tutorial removed from the homepage.'); } catch { /* shown above */ }
  }

  return (
    <div className="view-stack">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="tutorials" /> GUIDE WORKSPACE</span><h2>Write once. Guide everyone.</h2><p>Build complete English and Arabic walkthroughs, connect the right screenshots, then publish or roll back safely.</p></div><Button tone="primary" icon="plus" onClick={() => setCreateOpen(true)}>New tutorial</Button></section>
      {message ? <div className="notice notice-success"><Icon name="check" />{message}</div> : null}{error ? <div className="notice notice-error">{error}</div> : null}
      {loading ? <Spinner label="Loading tutorials" /> : tutorials.length ? <section className="manager-grid tutorial-manager">
        <div className="manager-list panel"><div className="panel-heading"><div><span>{tutorials.length} TOTAL</span><h3>Tutorials</h3></div></div><div className="entity-list">{tutorials.map((tutorial, index) => (
          <div className={`entity-row${selectedId === tutorial.id ? ' selected' : ''}`} key={tutorial.id}><button type="button" className="entity-select" onClick={() => setSelectedId(tutorial.id)}><span className="entity-icon"><Icon name="tutorials" /></span><div><strong>{tutorial.slug}</strong><small>{tutorial.featuredPosition !== null ? `Featured ${tutorial.featuredPosition + 1}` : `Position ${tutorial.position + 1}`} · v{tutorial.publishedRevision ?? '—'}</small></div><StatusBadge status={tutorial.status} /></button><span className="reorder-buttons"><button type="button" aria-label="Move up" disabled={index === 0 || busy} onClick={() => void move(index, -1)}><Icon name="chevronUp" /></button><button type="button" aria-label="Move down" disabled={index === tutorials.length - 1 || busy} onClick={() => void move(index, 1)}><Icon name="chevronDown" /></button></span></div>
        ))}</div></div>
        <div className="manager-detail panel">{selected ? <><div className="detail-hero"><div><span>TUTORIAL</span><h3>{selected.slug}</h3><p>Updated {formatDate(selected.updatedAt)}</p></div><StatusBadge status={selected.status} /></div><div className="detail-meta"><div><span>LIVE REVISION</span><strong>{selected.publishedRevision ? `v${selected.publishedRevision}` : 'Not published'}</strong></div><div><span>LIBRARY POSITION</span><strong>{selected.position + 1}</strong></div><div><span>HOMEPAGE</span><strong>{selected.featuredPosition === null ? 'Hidden' : `Featured ${selected.featuredPosition + 1}`}</strong></div></div><div className="detail-actions"><Button tone="primary" icon="edit" disabled={!categories.length || !media.length} onClick={() => setEditorOpen(true)}>{latestRevision ? 'Create revision' : 'Write first revision'}</Button><Button icon="spark" disabled={busy} onClick={() => void toggleFeatured()}>{selected.featuredPosition === null ? 'Feature on home' : 'Remove feature'}</Button>{selected.status === 'ARCHIVED' ? <Button icon="restore" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorials/${selected.id}/restore`, { method: 'POST' }), 'Tutorial restored.').catch(() => undefined)}>Restore</Button> : <Button tone="quiet" icon="archive" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorials/${selected.id}/archive`, { method: 'POST' }), 'Tutorial archived.').catch(() => undefined)}>Archive</Button>}</div>{!media.length ? <div className="notice notice-warning">Upload at least one screenshot before writing a revision.</div> : null}{!categories.length ? <div className="notice notice-warning">Create a category before writing a revision.</div> : null}<div className="revision-heading"><div><span>REVISION HISTORY</span><h4>{revisions.length} saved versions</h4></div></div><div className="revision-list tutorial-revisions">{revisions.length ? [...revisions].sort((a, b) => b.revision - a.revision).map((revision) => (
          <article key={revision.id} className={selected.publishedRevision === revision.revision ? 'current' : ''}><span className="revision-number">v{revision.revision}</span><div><strong>{revision.title.en}</strong><small dir="rtl">{revision.title.ar}</small><p>{revision.steps.length} steps · {formatDate(revision.createdAt)}</p></div><div className="revision-actions">{selected.publishedRevision === revision.revision ? <span className="current-label"><Icon name="check" /> Live</span> : <><Button tone="primary" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorials/${selected.id}/revisions/${revision.revision}/publish`, { method: 'POST' }), `Revision ${revision.revision} published.`).catch(() => undefined)}>Publish</Button>{selected.publishedRevision ? <Button tone="quiet" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorials/${selected.id}/revisions/${revision.revision}/rollback`, { method: 'POST' }), `Rolled back to revision ${revision.revision}.`).catch(() => undefined)}>Rollback</Button> : null}</>}</div></article>
        )) : <EmptyState icon="history" title="No revisions yet" copy="Open the editor to write the first bilingual version of this tutorial." />}</div></> : <EmptyState icon="tutorials" title="Choose a tutorial" copy="Select a guide to manage its content and publishing state." />}</div>
      </section> : <EmptyState icon="tutorials" title="Your tutorial library is ready" copy="Create the first guide identity, then write its bilingual revision." action={<Button tone="primary" icon="plus" onClick={() => setCreateOpen(true)}>Create tutorial</Button>} />}

      {createOpen ? <div className="modal-layer"><button className="modal-scrim" onClick={() => setCreateOpen(false)} /><form className="modal-card compact" onSubmit={createTutorial}><div className="modal-heading"><div><span>NEW TUTORIAL</span><h3>Create a guide identity</h3></div><button type="button" onClick={() => setCreateOpen(false)}><Icon name="close" /></button></div><Field label="Stable slug" hint="This becomes /tutorials/your-slug and cannot be renamed later."><Input name="slug" placeholder="organize-your-library" pattern="[a-z0-9-]+" required autoFocus /></Field><label className="check-row"><input type="checkbox" name="featured" /><span><strong>Feature on the homepage</strong><small>Add this guide to the home tutorial browser.</small></span></label><div className="modal-actions"><Button type="button" onClick={() => setCreateOpen(false)}>Cancel</Button><Button tone="primary" icon="plus" type="submit" disabled={busy}>Create tutorial</Button></div></form></div> : null}
      {editorOpen && selected ? <TutorialEditor slug={selected.slug} base={latestRevision} categories={categories} media={media} busy={busy} onClose={() => setEditorOpen(false)} onSave={saveRevision} /> : null}
    </div>
  );
}
