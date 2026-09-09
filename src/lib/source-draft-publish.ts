import type { SourceDraft, ValidationResult } from '@/lib/types';

import { apiFetch, apiFetchWithMeta } from './client-api';

export type SourceDraftEditorSnapshot = {
  draft: SourceDraft;
  etag: string;
  content: string;
};

type DraftRequest = typeof apiFetchWithMeta<SourceDraft>;
type DraftFinalization = { draft: SourceDraft };
type DraftPublication = { draft: SourceDraft; publication: { documentRevision: number } };

type DraftAdoption = {
  isCurrent: () => boolean;
  adopt: (saved: SourceDraftEditorSnapshot) => void;
};

export type DraftEditorAction = DraftAdoption & {
  api: string;
  current: SourceDraftEditorSnapshot;
};

export type PreparedDraftPublish = { api: string; snapshot: SourceDraftEditorSnapshot };

/**
 * Source PUT deliberately accepts raw text, including malformed JSON. Strict
 * parsing belongs to the later action; never discard a successful save for it.
 */
export async function persistEditorDraft(
  api: string,
  current: SourceDraftEditorSnapshot,
  request: DraftRequest = apiFetchWithMeta<SourceDraft>,
): Promise<SourceDraftEditorSnapshot> {
  const saved = await request(`sources/${encodeURIComponent(api)}/editor-draft`, {
    method: 'PUT',
    headers: { 'If-Match': current.etag },
    body: JSON.stringify({ content: current.content }),
  });
  if (!saved.etag) throw new Error('The backend did not return the updated draft ETag.');
  return { draft: saved.data, etag: saved.etag, content: current.content };
}

export function editorDraftSnapshot(draft: SourceDraft, etag: string): SourceDraftEditorSnapshot {
  let content = draft.content;
  try { content = JSON.stringify(JSON.parse(content), null, 2); } catch { /* Keep raw text editable. */ }
  return { draft, etag, content };
}

export async function saveAndAdoptEditorDraft(action: DraftEditorAction, request: DraftRequest = apiFetchWithMeta<SourceDraft>) {
  if (!action.isCurrent()) return null;
  const saved = await persistEditorDraft(action.api, action.current, request);
  if (!action.isCurrent()) return null;
  action.adopt(saved);
  return saved;
}

export async function validateEditorDraft(
  action: DraftEditorAction,
  requests = { save: apiFetchWithMeta<SourceDraft>, validate: apiFetch<ValidationResult> },
) {
  const saved = await saveAndAdoptEditorDraft(action, requests.save);
  if (!saved || !action.isCurrent()) return null;
  const validation = await requests.validate(`sources/${encodeURIComponent(action.api)}/editor-draft/validate`, {
    method: 'POST',
    headers: { 'If-Match': saved.etag },
  });
  return action.isCurrent() ? { snapshot: saved, validation } : null;
}

export async function finalizeEditorDraft(
  action: DraftEditorAction,
  requests = { save: apiFetchWithMeta<SourceDraft>, finalize: apiFetchWithMeta<DraftFinalization> },
) {
  const saved = await saveAndAdoptEditorDraft(action, requests.save);
  if (!saved || !action.isCurrent()) return null;
  const result = await requests.finalize(`sources/${encodeURIComponent(action.api)}/editor-draft/finalize`, {
    method: 'POST',
    headers: { 'If-Match': saved.etag },
  });
  if (!result.etag) throw new Error('The backend did not return the updated draft ETag.');
  if (!action.isCurrent()) return null;
  const finalized = editorDraftSnapshot(result.data.draft, result.etag);
  action.adopt(finalized);
  return finalized;
}

export async function prepareDraftPublish(
  action: DraftEditorAction,
  request: DraftRequest = apiFetchWithMeta<SourceDraft>,
): Promise<PreparedDraftPublish | null> {
  const saved = await saveAndAdoptEditorDraft(action, request);
  return saved && action.isCurrent() ? { api: action.api, snapshot: saved } : null;
}

/** Approval/retry uses only the already-saved target; it must not issue another PUT. */
export async function publishSavedEditorDraft(
  pending: PreparedDraftPublish,
  action: DraftAdoption,
  request = apiFetchWithMeta<DraftPublication>,
) {
  if (!action.isCurrent()) return null;
  const result = await request(`sources/${encodeURIComponent(pending.api)}/editor-draft/publish`, {
    method: 'POST',
    headers: { 'If-Match': pending.snapshot.etag },
  });
  if (!result.etag) throw new Error('The backend did not return the updated draft ETag.');
  if (!action.isCurrent()) return null;
  action.adopt(editorDraftSnapshot(result.data.draft, result.etag));
  return result.data.publication;
}
