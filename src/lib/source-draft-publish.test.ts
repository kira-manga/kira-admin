import { describe, expect, it, vi } from 'vitest';

import type { SourceDraft } from './types';
import { persistEditorDraft } from './source-draft-publish';

const draft: SourceDraft = {
  id: 'draft-id',
  basedOnRevisionNumber: 2,
  content: '{"api":"Azora"}',
  version: 4,
  createdBy: 'admin-id',
  updatedBy: 'admin-id',
  createdAt: '2026-07-24T00:00:00Z',
  updatedAt: '2026-07-24T00:00:00Z',
};

describe('persistEditorDraft', () => {
  it('saves the visible editor content and returns the new optimistic ETag', async () => {
    const request = vi.fn(async () => ({
      data: { ...draft, content: '{"api":"Azora","displayName":"Updated"}', version: 5 },
      etag: '"draft-5"',
    }));

    const result = await persistEditorDraft(
      'Azora',
      { draft, etag: '"draft-4"', content: '{\n  "api": "Azora",\n  "displayName": "Updated"\n}' },
      request,
    );

    expect(request).toHaveBeenCalledWith('sources/Azora/editor-draft', {
      method: 'PUT',
      headers: { 'If-Match': '"draft-4"' },
      body: JSON.stringify({ content: '{\n  "api": "Azora",\n  "displayName": "Updated"\n}' }),
    });
    expect(result.etag).toBe('"draft-5"');
    expect(result.content).toContain('"displayName": "Updated"');
  });

  it('fails closed when the backend omits the new ETag', async () => {
    const request = vi.fn(async () => ({ data: draft, etag: null }));

    await expect(
      persistEditorDraft('Azora', { draft, etag: '"draft-4"', content: draft.content }, request),
    ).rejects.toThrow('updated draft ETag');
  });
});
