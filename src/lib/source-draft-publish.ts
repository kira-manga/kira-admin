import type { SourceDraft } from '@/lib/types';

import { apiFetchWithMeta } from './client-api';

export type SourceDraftEditorSnapshot = {
  draft: SourceDraft;
  etag: string;
  content: string;
};

type DraftRequest = typeof apiFetchWithMeta<SourceDraft>;

/**
 * Persist exactly what is visible in the editor before a protected quick publish.
 * Publishing is a separate request because its one-time step-up proof must remain
 * single-use, while this save continues to use the draft's optimistic ETag.
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
