'use client';

import { ChangeEvent, DragEvent, useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';

import { apiFetch, apiUpload, type UploadProgress } from '@/lib/client-api';
import type { TutorialMedia } from '@/lib/types';
import { Icon } from './icons';
import { Button, EmptyState, Spinner, formatDate } from './ui';

export function MediaView() {
  const [media, setMedia] = useState<TutorialMedia[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try { setMedia((await apiFetch<TutorialMedia[]>('tutorial-media')).sort((a, b) => b.createdAt.localeCompare(a.createdAt))); }
    catch (caught) { setError((caught as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => {
    // Data is applied only after the admin API request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function upload(file?: File) {
    if (!file || uploading) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) { setError('Choose a JPEG or PNG image.'); return; }
    if (file.size > 4 * 1024 * 1024) { setError('Images must be 4 MiB or smaller.'); return; }
    setUploading(true); setUploadProgress({ loaded: 0, total: file.size, percent: 0 }); setUploadName(file.name); setError(''); setMessage('');
    const body = new FormData(); body.append('file', file);
    try { await apiUpload('/api/tutorial-media-upload', body, setUploadProgress); setMessage(`${file.name} uploaded and sanitized.`); await load(); }
    catch (caught) { setError((caught as Error).message); }
    finally { setUploading(false); setUploadProgress(null); setUploadName(''); if (inputRef.current) inputRef.current.value = ''; }
  }

  async function remove(item: TutorialMedia) {
    if (!window.confirm(`Delete media ${item.id}? Referenced media cannot be deleted.`)) return;
    setError(''); setMessage('');
    try { await apiFetch(`tutorial-media/${item.id}`, { method: 'DELETE' }); setMessage('Media deleted.'); await load(); }
    catch (caught) { setError((caught as Error).message); }
  }

  function drop(event: DragEvent) { event.preventDefault(); setDragging(false); void upload(event.dataTransfer.files[0]); }
  function choose(event: ChangeEvent<HTMLInputElement>) { void upload(event.target.files?.[0]); }

  return (
    <div className="view-stack">
      <section className="view-heading"><div><span className="eyebrow"><Icon name="media" /> VISUAL LIBRARY</span><h2>Every screen, ready for every guide.</h2><p>Upload sanitized JPEG or PNG screenshots, then assign them as default, English, Arabic, light, or dark variants.</p></div><Button tone="primary" icon="upload" onClick={() => inputRef.current?.click()} disabled={uploading}>{uploading ? uploadProgress?.percent === 100 ? 'Processing…' : `Uploading ${uploadProgress?.percent ?? 0}%` : 'Upload media'}</Button></section>
      <input ref={inputRef} className="visually-hidden" type="file" accept="image/jpeg,image/png" onChange={choose} />
      {message ? <div className="notice notice-success"><Icon name="check" />{message}</div> : null}
      {error ? <div className="notice notice-error">{error}</div> : null}
      <section className={`upload-zone${dragging ? ' dragging' : ''}${uploading ? ' uploading' : ''}`} onDragEnter={(event) => { event.preventDefault(); if (!uploading) setDragging(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={drop}>
        <span><Icon name="upload" /></span><div><strong>{uploading ? uploadName : 'Drop a screenshot here'}</strong><p>{uploading ? uploadProgress?.percent === 100 ? 'Upload complete · sanitizing and saving the image' : 'Uploading securely to Kira' : 'JPEG or PNG · maximum 4 MiB · maximum 4096 × 4096'}</p></div><Button onClick={() => inputRef.current?.click()} disabled={uploading}>Browse files</Button>
        {uploading && uploadProgress ? <div className={`upload-progress${uploadProgress.percent === 100 ? ' processing' : ''}`} role="status" aria-live="polite">
          <div><strong>{uploadProgress.percent === 100 ? 'Processing image…' : 'Uploading…'}</strong><span>{uploadProgress.percent}%</span></div>
          <progress max="100" value={uploadProgress.percent} aria-label={`Upload progress: ${uploadProgress.percent}%`}>{uploadProgress.percent}%</progress>
        </div> : null}
      </section>
      <section className="panel media-panel">
        <div className="panel-heading"><div><span>{media.length} ASSETS</span><h3>Screenshot library</h3></div><p>{media.filter((item) => item.published).length} currently published</p></div>
        {loading ? <Spinner label="Loading media" /> : media.length ? <div className="media-grid">{media.map((item) => (
          <article key={item.id} className="media-card">
            <div className="media-preview"><Image src={`/api/media/${item.id}`} alt="Tutorial media preview" width={item.width} height={item.height} unoptimized /><span className={item.published ? 'media-live' : 'media-draft'}>{item.published ? 'IN USE' : 'AVAILABLE'}</span></div>
            <div className="media-info"><div><strong>{item.width} × {item.height}</strong><span>{item.contentType.replace('image/', '').toUpperCase()} · {(item.byteSize / 1024).toFixed(0)} KB</span></div><code title={item.id}>{item.id.slice(0, 8)}</code></div>
            <div className="media-foot"><small>{formatDate(item.createdAt)}</small><button type="button" onClick={() => void remove(item)} title="Delete media"><Icon name="trash" /></button></div>
          </article>
        ))}</div> : <EmptyState icon="media" title="No screenshots yet" copy="Upload the first visual asset for your tutorial library." action={<Button tone="primary" icon="upload" onClick={() => inputRef.current?.click()}>Upload media</Button>} />}
      </section>
    </div>
  );
}
