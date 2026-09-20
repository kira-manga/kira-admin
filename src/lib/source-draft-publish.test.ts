import { describe, expect, it, vi } from 'vitest';

import { createActionOwner } from './action-owner';
import { ApiError } from './client-api';
import type { SourceDraft, ValidationResult } from './types';
import { finalizeEditorDraft, persistEditorDraft, prepareDraftPublish, publishSavedEditorDraft, saveAndAdoptEditorDraft, validateEditorDraft, type DraftEditorAction, type SourceDraftEditorSnapshot } from './source-draft-publish';
import { verifyProtectedAction } from './step-up';

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

const visibleContent = '{\n  "api": "Azora",\n  "displayName": "Visible change"\n}';
const savedEtag = '"draft-5"';
const canonicalEtag = '"draft-6"';
const canonicalDraft: SourceDraft = { ...draft, basedOnRevisionNumber: 3, version: 6, content: '{"api":"Azora","displayName":"Canonical change","sourceRevision":3}' };
const validation: ValidationResult = { valid: false, errors: [{ code: 'TEST', path: '$', message: 'Visible source needs work.' }], warnings: [] };
type DraftResponse = { data: SourceDraft; etag: string | null };

function draftAction(content = visibleContent) {
  const owner = createActionOwner();
  const unmount = owner.mount();
  const ticket = owner.acquire()!;
  const events: string[] = [];
  let current: SourceDraftEditorSnapshot = { draft, etag: '"draft-4"', content };
  const adopt = vi.fn((saved: SourceDraftEditorSnapshot) => {
    current = saved;
    events.push(`adopt ${saved.etag}`);
  });
  const action: DraftEditorAction = { api: 'Azora', current, adopt, isCurrent: ticket.isCurrent };
  const response: DraftResponse = { data: { ...draft, content, version: 5 }, etag: savedEtag };
  const save = vi.fn(async (): Promise<DraftResponse> => { events.push('PUT'); return response; });
  return { action, save, response, adopt, events, owner, ticket, unmount, get current() { return current; } };
}

function expectVisiblePut(view: ReturnType<typeof draftAction>) {
  expect(view.save).toHaveBeenCalledExactlyOnceWith('sources/Azora/editor-draft', {
    method: 'PUT', headers: { 'If-Match': '"draft-4"' }, body: JSON.stringify({ content: view.action.current.content }),
  });
}

describe('visible source draft actions', () => {
  it('explicitly saves and adopts through the same persistence seam', async () => {
    const view = draftAction();
    const saved = await saveAndAdoptEditorDraft(view.action, view.save);
    expectVisiblePut(view);
    expect(saved).toBe(view.current);
    expect(view.current).toEqual({ draft: view.response.data, etag: savedEtag, content: visibleContent });
  });

  it('adopts the visible save before validating with its returned ETag', async () => {
    const view = draftAction();
    const validate = vi.fn(async () => {
      expect(view.current.content).toBe(visibleContent);
      expect(view.current.etag).toBe(savedEtag);
      view.events.push('validate');
      return validation;
    });
    const result = await validateEditorDraft(view.action, { save: view.save, validate });
    expectVisiblePut(view);
    expect(validate).toHaveBeenCalledExactlyOnceWith('sources/Azora/editor-draft/validate', { method: 'POST', headers: { 'If-Match': savedEtag } });
    expect(result).toEqual({ snapshot: view.current, validation });
    expect(view.events).toEqual(['PUT', `adopt ${savedEtag}`, 'validate']);
  });

  it('finalizes without a new semantic-validation gate and adopts the second canonical draft/ETag', async () => {
    const view = draftAction();
    const finalize = vi.fn(async () => {
      expect(view.current.etag).toBe(savedEtag);
      view.events.push('finalize');
      return { data: { draft: canonicalDraft, validation }, etag: canonicalEtag };
    });
    const result = await finalizeEditorDraft(view.action, { save: view.save, finalize });
    expectVisiblePut(view);
    expect(finalize).toHaveBeenCalledExactlyOnceWith('sources/Azora/editor-draft/finalize', { method: 'POST', headers: { 'If-Match': savedEtag } });
    expect(view.current).toEqual({ draft: canonicalDraft, etag: canonicalEtag, content: JSON.stringify(JSON.parse(canonicalDraft.content), null, 2) });
    expect(result).toBe(view.current);
    expect(view.events).toEqual(['PUT', `adopt ${savedEtag}`, 'finalize', `adopt ${canonicalEtag}`]);
  });

  it.each(['validate', 'finalize'] as const)('keeps a successful raw malformed-text save when strict %s rejects it', async (kind) => {
    const view = draftAction('{"api":');
    const validate = vi.fn(async () => validation).mockRejectedValue(new ApiError('Malformed source JSON.', 400));
    const finalize = vi.fn(async () => ({ data: { draft: canonicalDraft }, etag: canonicalEtag })).mockRejectedValue(new ApiError('Malformed source JSON.', 400));
    const work = kind === 'validate' ? validateEditorDraft(view.action, { save: view.save, validate }) : finalizeEditorDraft(view.action, { save: view.save, finalize });
    await expect(work).rejects.toThrow('Malformed source JSON.');
    expectVisiblePut(view);
    expect(view.current.content).toBe('{"api":');
    expect(view.current.etag).toBe(savedEtag);
    expect(view.adopt).toHaveBeenCalledTimes(1);
  });

  it('retains the first save if finalization succeeds without the required second ETag', async () => {
    const view = draftAction();
    const finalize = vi.fn(async () => ({ data: { draft: canonicalDraft }, etag: null }));
    await expect(finalizeEditorDraft(view.action, { save: view.save, finalize })).rejects.toThrow('updated draft ETag');
    expect(view.current.etag).toBe(savedEtag);
    expect(view.current.content).toBe(visibleContent);
  });

  it('prepares before confirmation, keeps ownership, and cancels without losing the saved editor', async () => {
    const view = draftAction();
    const pending = await prepareDraftPublish(view.action, view.save);
    expect(pending).toEqual({ api: 'Azora', snapshot: view.current });
    expect(pending?.snapshot).toBe(view.current);
    view.events.push('confirmation');
    expect(view.events).toEqual(['PUT', `adopt ${savedEtag}`, 'confirmation']);
    expect(view.owner.acquire()).toBeNull();
    expect(view.owner.release(view.ticket)).toBe(true);
    const publish = vi.fn(async () => ({ data: { draft: canonicalDraft, publication: { documentRevision: 12 } }, etag: canonicalEtag }));
    expect(await publishSavedEditorDraft(pending!, view.action, publish)).toBeNull();
    expect(publish).not.toHaveBeenCalled();
    expect(view.current.etag).toBe(savedEtag);
    expect(view.current.content).toBe(visibleContent);
  });

  it('publishes/retries the prepared target after fresh verification, never saving again', async () => {
    const view = draftAction();
    const pending = await prepareDraftPublish(view.action, view.save);
    expectVisiblePut(view);
    view.action.api = 'Different source';
    view.action.current = { ...view.action.current, etag: '"draft-999"' };
    const verify = vi.fn(async () => {
      view.events.push('verify');
      return Response.json({ scope: 'source-admin-mutation', expiresAt: new Date(Date.now() + 300_000).toISOString() });
    });
    let attempts = 0;
    const publish = vi.fn(async () => {
      view.events.push('publish');
      if (++attempts === 1) throw new ApiError('Version conflict after save.', 409);
      return { data: { draft: canonicalDraft, publication: { documentRevision: 12 } }, etag: canonicalEtag };
    });
    const approval = {
      password: 'fixture-only', isCurrent: view.ticket.isCurrent, clearPassword: vi.fn(),
      onApproved: async () => { await publishSavedEditorDraft(pending!, view.action, publish); },
    };
    await expect(verifyProtectedAction(approval, verify)).rejects.toThrow('Version conflict after save.');
    expect(view.current.etag).toBe(savedEtag);
    expect(view.current.content).toBe(visibleContent);
    expect(view.owner.isLocked()).toBe(true);
    await verifyProtectedAction(approval, verify);
    expect(verify).toHaveBeenCalledTimes(2);
    expect(publish).toHaveBeenCalledTimes(2);
    for (const call of publish.mock.calls) expect(call).toEqual(['sources/Azora/editor-draft/publish', { method: 'POST', headers: { 'If-Match': savedEtag } }]);
    expect(view.save).toHaveBeenCalledTimes(1);
    expect(view.current.draft).toBe(canonicalDraft);
    expect(view.current.etag).toBe(canonicalEtag);
    expect(view.current.content).toBe(JSON.stringify(JSON.parse(canonicalDraft.content), null, 2));
    expect(view.events).toEqual(['PUT', `adopt ${savedEtag}`, 'verify', 'publish', 'verify', 'publish', `adopt ${canonicalEtag}`]);
  });

  it('fails closed on missing publication metadata without discarding the prepared save', async () => {
    const view = draftAction();
    const pending = await prepareDraftPublish(view.action, view.save);
    const publish = vi.fn(async () => ({ data: { draft: canonicalDraft, publication: { documentRevision: 12 } }, etag: null }));
    await expect(publishSavedEditorDraft(pending!, view.action, publish)).rejects.toThrow('updated draft ETag');
    expect(view.current.etag).toBe(savedEtag);
    expect(view.current.content).toBe(visibleContent);
    expect(view.save).toHaveBeenCalledTimes(1);
  });
});

describe.each(['validate', 'finalize', 'quick publish'] as const)('%s preparation failures', (kind) => {
  it.each([
    { label: 'stale 409', error: new ApiError('Stale draft.', 409) },
    { label: 'expired session 401', error: new ApiError('Sign in again.', 401) },
    { label: 'transport error', error: new TypeError('Network unavailable.') },
    { label: 'missing save ETag', error: null },
  ])('does not act or confirm after $label', async ({ error }) => {
    const view = draftAction();
    if (error) view.save.mockRejectedValue(error);
    else view.save.mockResolvedValue({ data: view.response.data, etag: null });
    const validate = vi.fn(async () => validation);
    const finalize = vi.fn(async () => ({ data: { draft: canonicalDraft }, etag: canonicalEtag }));
    const confirm = vi.fn();
    const work = kind === 'validate' ? validateEditorDraft(view.action, { save: view.save, validate })
      : kind === 'finalize' ? finalizeEditorDraft(view.action, { save: view.save, finalize })
        : prepareDraftPublish(view.action, view.save).then((pending) => { if (pending) confirm(pending); });
    await expect(work).rejects.toThrow(error?.message ?? 'updated draft ETag');
    expect(view.adopt).not.toHaveBeenCalled();
    expect(validate).not.toHaveBeenCalled();
    expect(finalize).not.toHaveBeenCalled();
    expect(confirm).not.toHaveBeenCalled();
    expect(view.current.etag).toBe('"draft-4"');
    expect(view.current.content).toBe(visibleContent);
  });

  it('does not adopt or continue a delayed save after owner unmount/remount', async () => {
    const view = draftAction();
    let resolve!: (value: DraftResponse) => void;
    view.save.mockImplementation(() => new Promise<DraftResponse>((done) => { resolve = done; }));
    const validate = vi.fn(async () => validation);
    const finalize = vi.fn(async () => ({ data: { draft: canonicalDraft }, etag: canonicalEtag }));
    const work = kind === 'validate' ? validateEditorDraft(view.action, { save: view.save, validate })
      : kind === 'finalize' ? finalizeEditorDraft(view.action, { save: view.save, finalize })
        : prepareDraftPublish(view.action, view.save);
    expect(view.owner.acquire()).toBeNull();
    view.unmount();
    view.owner.mount();
    resolve(view.response);
    expect(await work).toBeNull();
    expect(view.adopt).not.toHaveBeenCalled();
    expect(validate).not.toHaveBeenCalled();
    expect(finalize).not.toHaveBeenCalled();
    expect(view.owner.acquire()).not.toBeNull();
  });
});
