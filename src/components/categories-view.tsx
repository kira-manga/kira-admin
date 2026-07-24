'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';

import { apiFetch } from '@/lib/client-api';
import type { AdminCategory, CategoryRevision } from '@/lib/types';
import { Icon } from './icons';
import { Button, EmptyState, Field, Input, Spinner, StatusBadge, formatDate } from './ui';

export function CategoriesView() {
  const [categories, setCategories] = useState<AdminCategory[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<CategoryRevision[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [revisionOpen, setRevisionOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const result = await apiFetch<AdminCategory[]>('tutorial-categories');
      setCategories(result.sort((a, b) => a.position - b.position));
      setSelectedId((current) => current ?? result[0]?.id ?? null);
    } catch (caught) { setError((caught as Error).message); }
  }, []);

  useEffect(() => {
    // Data is applied only after the admin API request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  useEffect(() => {
    if (!selectedId) return;
    apiFetch<CategoryRevision[]>(`tutorial-categories/${selectedId}/revisions`).then(setRevisions).catch((caught: Error) => setError(caught.message));
  }, [selectedId]);

  const selected = categories.find((item) => item.id === selectedId) ?? null;

  async function mutate(action: () => Promise<unknown>, success: string) {
    setBusy(true); setError(''); setMessage('');
    try {
      await action();
      await load();
      if (selectedId) setRevisions(await apiFetch<CategoryRevision[]>(`tutorial-categories/${selectedId}/revisions`));
      setMessage(success);
    } catch (caught) { setError((caught as Error).message); } finally { setBusy(false); }
  }

  async function createCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await mutate(() => apiFetch('tutorial-categories', { method: 'POST', body: JSON.stringify({ slug: data.get('slug'), position: categories.length }) }), 'Category created. Add its first revision to publish it.');
    setCreateOpen(false);
  }

  async function createRevision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    await mutate(() => apiFetch(`tutorial-categories/${selected.id}/revisions`, {
      method: 'POST',
      body: JSON.stringify({ label: { en: data.get('labelEn'), ar: data.get('labelAr') }, iconCode: data.get('iconCode') }),
    }), 'Category revision saved.');
    setRevisionOpen(false);
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= categories.length) return;
    const reordered = [...categories];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    setCategories(reordered);
    await mutate(() => apiFetch('tutorial-categories/reorder', { method: 'POST', body: JSON.stringify({ items: reordered.map((item, position) => ({ id: item.id, position })) }) }), 'Category order updated.');
  }

  return (
    <div className="view-stack">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="categories" /> LIBRARY STRUCTURE</span><h2>Organize the learning path.</h2><p>Categories group guides on the public site. Every label revision remains available for safe rollback.</p></div><Button tone="primary" icon="plus" onClick={() => setCreateOpen(true)}>New category</Button></section>
      {message ? <div className="notice notice-success"><Icon name="check" />{message}</div> : null}
      {error ? <div className="notice notice-error">{error}</div> : null}
      {!categories.length && !error ? <Spinner label="Loading categories" /> : (
        <section className="manager-grid">
          <div className="manager-list panel">
            <div className="panel-heading"><div><span>{categories.length} TOTAL</span><h3>Categories</h3></div></div>
            <div className="entity-list">
              {categories.map((category, index) => (
                <div className={`entity-row${selectedId === category.id ? ' selected' : ''}`} key={category.id}>
                  <button type="button" className="entity-select" onClick={() => setSelectedId(category.id)}>
                    <span className="entity-icon"><Icon name="categories" /></span>
                    <div><strong>{category.slug}</strong><small>Position {category.position + 1} · Revision {category.publishedRevision ?? '—'}</small></div>
                    <StatusBadge status={category.status} />
                  </button>
                  <span className="reorder-buttons"><button type="button" aria-label="Move up" disabled={index === 0 || busy} onClick={() => void move(index, -1)}><Icon name="chevronUp" /></button><button type="button" aria-label="Move down" disabled={index === categories.length - 1 || busy} onClick={() => void move(index, 1)}><Icon name="chevronDown" /></button></span>
                </div>
              ))}
            </div>
          </div>
          <div className="manager-detail panel">
            {selected ? <>
              <div className="detail-hero"><div><span>CATEGORY</span><h3>{selected.slug}</h3><p>Created {formatDate(selected.createdAt)}</p></div><StatusBadge status={selected.status} /></div>
              <div className="detail-actions"><Button tone="primary" icon="edit" onClick={() => setRevisionOpen(true)}>New revision</Button>{selected.status === 'ARCHIVED' ? <Button icon="restore" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorial-categories/${selected.id}/restore`, { method: 'POST' }), 'Category restored.')}>Restore</Button> : <Button tone="quiet" icon="archive" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorial-categories/${selected.id}/archive`, { method: 'POST' }), 'Category archived.')}>Archive</Button>}</div>
              <div className="revision-heading"><div><span>REVISION HISTORY</span><h4>{revisions.length} saved versions</h4></div></div>
              <div className="revision-list">
                {revisions.length ? [...revisions].sort((a, b) => b.revision - a.revision).map((revision) => (
                  <article key={revision.id} className={selected.publishedRevision === revision.revision ? 'current' : ''}>
                    <span className="revision-number">v{revision.revision}</span><div><strong>{revision.label.en}</strong><small dir="rtl">{revision.label.ar}</small><p>{revision.iconCode} · {formatDate(revision.createdAt)}</p></div>
                    <div className="revision-actions">{selected.publishedRevision === revision.revision ? <span className="current-label"><Icon name="check" /> Live</span> : <><Button tone="primary" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorial-categories/${selected.id}/revisions/${revision.revision}/publish`, { method: 'POST' }), `Revision ${revision.revision} published.`)}>Publish</Button>{selected.publishedRevision ? <Button tone="quiet" disabled={busy} onClick={() => void mutate(() => apiFetch(`tutorial-categories/${selected.id}/revisions/${revision.revision}/rollback`, { method: 'POST' }), `Rolled back to revision ${revision.revision}.`)}>Rollback</Button> : null}</>}</div>
                  </article>
                )) : <EmptyState icon="history" title="No revisions yet" copy="Create a bilingual label revision before publishing this category." />}
              </div>
            </> : <EmptyState icon="categories" title="Choose a category" copy="Select a category to manage revisions and publication." />}
          </div>
        </section>
      )}

      {createOpen ? <div className="modal-layer"><button className="modal-scrim" onClick={() => setCreateOpen(false)} /><form className="modal-card compact" onSubmit={createCategory}><div className="modal-heading"><div><span>NEW CATEGORY</span><h3>Create a category</h3></div><button type="button" onClick={() => setCreateOpen(false)}><Icon name="close" /></button></div><Field label="Stable slug" hint="Lowercase letters, numbers, and hyphens. This cannot be renamed later."><Input name="slug" placeholder="reading-basics" pattern="[a-z0-9-]+" required autoFocus /></Field><div className="modal-actions"><Button type="button" onClick={() => setCreateOpen(false)}>Cancel</Button><Button tone="primary" icon="plus" type="submit" disabled={busy}>Create category</Button></div></form></div> : null}
      {revisionOpen && selected ? <div className="modal-layer"><button className="modal-scrim" onClick={() => setRevisionOpen(false)} /><form className="modal-card" onSubmit={createRevision}><div className="modal-heading"><div><span>NEW REVISION · {selected.slug}</span><h3>Bilingual category label</h3></div><button type="button" onClick={() => setRevisionOpen(false)}><Icon name="close" /></button></div><div className="form-grid"><Field label="English label"><Input name="labelEn" defaultValue={revisions.at(-1)?.label.en} placeholder="Getting started" required /></Field><Field label="Arabic label"><Input name="labelAr" defaultValue={revisions.at(-1)?.label.ar} placeholder="البدء" dir="rtl" required /></Field><Field label="Icon code" wide hint="Supported public icons: book, search, download, settings"><select className="input" name="iconCode" defaultValue={revisions.at(-1)?.iconCode ?? 'book'}><option value="book">Book</option><option value="search">Search</option><option value="download">Download</option><option value="settings">Settings</option></select></Field></div><div className="modal-actions"><Button type="button" onClick={() => setRevisionOpen(false)}>Cancel</Button><Button tone="primary" icon="check" type="submit" disabled={busy}>Save revision</Button></div></form></div> : null}
    </div>
  );
}
