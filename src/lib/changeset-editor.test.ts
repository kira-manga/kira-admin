import { beforeEach, describe, expect, it, vi } from 'vitest';

import { seedClientSession, stepUpAcknowledgement } from '@/test/auth-fixture';
import { createActionOwner } from './action-owner';
import { applySavedChangeset, parseOperations, prepareChangesetApply, saveAndAdoptChangeset, validateChangeset, type ChangesetEditorAction, type ChangesetEditorSnapshot } from './changeset-editor';
import { ApiError } from './client-api';
import { verifyProtectedAction } from './step-up';
import type { SourceChange, SourceChangeset } from './types';

const changeset: SourceChangeset = {
  id: 'changeset-a', name: 'Persisted name', description: 'Persisted description',
  operations: [{ type: 'disable', api: 'Azora' }], status: 'open', version: 8,
  appliedDocumentRevision: null, createdBy: 'admin-id', updatedBy: 'admin-id',
  createdAt: '2026-09-09T00:00:00Z', updatedAt: '2026-09-09T00:00:00Z', appliedAt: null,
};

beforeEach(async () => { await seedClientSession(); });
const visibleOperations: SourceChange[] = [{ type: 'enable', api: 'Beta' }];
const operationsText = JSON.stringify(visibleOperations, null, 2);
const savedEtag = '"changeset-9"';
const validation = { valid: true, operationCount: 1, affectedApis: ['Beta'] };
const application = { documentRevision: 12, affectedApis: ['Beta'] };
type ChangesetResponse = { data: SourceChangeset; etag: string | null };

function changesetAction(text = operationsText) {
  const owner = createActionOwner();
  const unmount = owner.mount();
  const ticket = owner.acquire()!;
  const events: string[] = [];
  let current: ChangesetEditorSnapshot = {
    value: { ...changeset, name: ' Visible name ', description: ' Visible description ' },
    etag: '"changeset-8"', operationsText: text,
  };
  const adopt = vi.fn((saved: ChangesetEditorSnapshot) => { current = saved; events.push('adopt'); });
  const action: ChangesetEditorAction = { id: changeset.id, current, adopt, isCurrent: ticket.isCurrent };
  const response: ChangesetResponse = {
    data: { ...changeset, name: 'Visible name', description: 'Visible description', operations: visibleOperations, version: 9 }, etag: savedEtag,
  };
  const save = vi.fn(async (): Promise<ChangesetResponse> => { events.push('PUT'); return response; });
  return { action, save, response, adopt, events, owner, ticket, unmount, get current() { return current; } };
}

function expectVisiblePut(view: ReturnType<typeof changesetAction>) {
  expect(view.save).toHaveBeenCalledExactlyOnceWith('source-changesets/changeset-a', {
    method: 'PUT', headers: { 'If-Match': '"changeset-8"' },
    body: JSON.stringify({ name: ' Visible name ', description: ' Visible description ', operations: visibleOperations }),
  });
}

describe('visible changeset actions', () => {
  it('saves visible metadata and operations and adopts the backend-normalized snapshot', async () => {
    const view = changesetAction();
    const saved = await saveAndAdoptChangeset(view.action, view.save);
    expectVisiblePut(view);
    expect(saved).toBe(view.current);
    expect(view.current).toEqual({ value: view.response.data, etag: savedEtag, operationsText });
  });

  it('adopts all saved fields before validation with the returned ETag', async () => {
    const view = changesetAction();
    const validate = vi.fn(async () => {
      expect(view.current.value.name).toBe('Visible name');
      expect(view.current.value.description).toBe('Visible description');
      expect(view.current.operationsText).toBe(operationsText);
      expect(view.current.etag).toBe(savedEtag);
      view.events.push('validate');
      return validation;
    });
    expect(await validateChangeset(view.action, { save: view.save, validate })).toEqual(validation);
    expectVisiblePut(view);
    expect(validate).toHaveBeenCalledExactlyOnceWith('source-changesets/changeset-a/validate', { method: 'POST', headers: { 'If-Match': savedEtag } });
    expect(view.events).toEqual(['PUT', 'adopt', 'validate']);
  });

  it('retains saved metadata/operations/ETag when later validation rejects', async () => {
    const view = changesetAction();
    const validate = vi.fn(async () => validation).mockRejectedValue(new ApiError('Catalog validation failed.', 400));
    await expect(validateChangeset(view.action, { save: view.save, validate })).rejects.toThrow('Catalog validation failed.');
    expectVisiblePut(view);
    expect(view.current).toEqual({ value: view.response.data, etag: savedEtag, operationsText });
    expect(view.adopt).toHaveBeenCalledTimes(1);
  });

  it('prepares before confirmation, and cancellation leaves the exact saved snapshot', async () => {
    const view = changesetAction();
    const pending = await prepareChangesetApply(view.action, view.save);
    expectVisiblePut(view);
    expect(pending).toEqual({ id: 'changeset-a', snapshot: view.current });
    expect(pending?.snapshot).toBe(view.current);
    view.events.push('confirmation');
    expect(view.events).toEqual(['PUT', 'adopt', 'confirmation']);
    expect(view.owner.acquire()).toBeNull();
    expect(view.owner.release(view.ticket)).toBe(true);
    const apply = vi.fn(async () => application);
    expect(await applySavedChangeset(pending!, view.ticket.isCurrent, apply)).toBeNull();
    expect(apply).not.toHaveBeenCalled();
    expect(view.current).toEqual({ value: view.response.data, etag: savedEtag, operationsText });
  });

  it('applies the prepared target after each fresh verification, without another PUT or a made-up ETag', async () => {
    const view = changesetAction();
    const pending = await prepareChangesetApply(view.action, view.save);
    expectVisiblePut(view);
    // An approval must not reread the previous editor/selection context.
    view.action.id = 'different-changeset';
    view.action.current = { ...view.action.current, etag: '"changeset-999"' };
    const verify = vi.fn(async () => {
      view.events.push('verify');
      return Response.json(stepUpAcknowledgement());
    });
    let attempts = 0;
    const apply = vi.fn(async () => {
      view.events.push('apply');
      if (++attempts === 1) throw new ApiError('Catalog changed after save.', 409);
      return application;
    });
    const approval = {
      password: 'fixture-only', isCurrent: view.ticket.isCurrent, clearPassword: vi.fn(),
      onApproved: async () => { expect(await applySavedChangeset(pending!, view.ticket.isCurrent, apply)).toEqual(application); },
    };
    await expect(verifyProtectedAction(approval, verify)).rejects.toThrow('Catalog changed after save.');
    expect(view.current).toEqual({ value: view.response.data, etag: savedEtag, operationsText });
    expect(view.owner.isLocked()).toBe(true);
    await verifyProtectedAction(approval, verify);
    expect(verify).toHaveBeenCalledTimes(2);
    expect(apply).toHaveBeenCalledTimes(2);
    for (const call of apply.mock.calls) expect(call).toEqual(['source-changesets/changeset-a/apply', { method: 'POST', headers: { 'If-Match': savedEtag } }]);
    expect(view.save).toHaveBeenCalledTimes(1);
    expect(view.events).toEqual(['PUT', 'adopt', 'verify', 'apply', 'verify', 'apply']);
  });

  it('preserves the existing tolerant add-operation parser without using it for saves', () => {
    expect(parseOperations('{', true)).toEqual([]);
    expect(() => parseOperations('{')).toThrow();
  });
});

describe.each(['save', 'validate', 'apply'] as const)('%s preparation boundaries', (kind) => {
  it.each(['{', '{}', 'null', '"not an array"'])('rejects malformed/non-array operations %s before PUT', async (text) => {
    const view = changesetAction(text);
    const validate = vi.fn(async () => validation);
    const work = kind === 'save' ? saveAndAdoptChangeset(view.action, view.save)
      : kind === 'validate' ? validateChangeset(view.action, { save: view.save, validate })
        : prepareChangesetApply(view.action, view.save);
    await expect(work).rejects.toThrow();
    expect(view.save).not.toHaveBeenCalled();
    expect(view.adopt).not.toHaveBeenCalled();
    expect(validate).not.toHaveBeenCalled();
    expect(view.current.operationsText).toBe(text);
  });

  it('permits an empty operations array to reach backend save/validation', async () => {
    const view = changesetAction('[]');
    view.save.mockResolvedValue({ data: { ...view.response.data, operations: [] }, etag: savedEtag });
    const validate = vi.fn(async () => ({ valid: true, operationCount: 0, affectedApis: [] }));
    const work = kind === 'save' ? saveAndAdoptChangeset(view.action, view.save)
      : kind === 'validate' ? validateChangeset(view.action, { save: view.save, validate })
        : prepareChangesetApply(view.action, view.save);
    await work;
    expect(view.save).toHaveBeenCalledExactlyOnceWith('source-changesets/changeset-a', {
      method: 'PUT', headers: { 'If-Match': '"changeset-8"' },
      body: JSON.stringify({ name: ' Visible name ', description: ' Visible description ', operations: [] }),
    });
    expect(view.current.operationsText).toBe('[]');
  });

  it.each([
    { label: 'stale 409', error: new ApiError('Stale changeset.', 409) },
    { label: 'expired session 401', error: new ApiError('Sign in again.', 401) },
    { label: 'transport error', error: new TypeError('Network unavailable.') },
    { label: 'missing save ETag', error: null },
  ])('does not act or confirm after $label', async ({ error }) => {
    const view = changesetAction();
    if (error) view.save.mockRejectedValue(error);
    else view.save.mockResolvedValue({ data: view.response.data, etag: null });
    const validate = vi.fn(async () => validation);
    const confirm = vi.fn();
    const work = kind === 'save' ? saveAndAdoptChangeset(view.action, view.save)
      : kind === 'validate' ? validateChangeset(view.action, { save: view.save, validate })
        : prepareChangesetApply(view.action, view.save).then((pending) => { if (pending) confirm(pending); });
    await expect(work).rejects.toThrow(error?.message ?? 'updated changeset ETag');
    expect(view.adopt).not.toHaveBeenCalled();
    expect(validate).not.toHaveBeenCalled();
    expect(confirm).not.toHaveBeenCalled();
    expect(view.current.etag).toBe('"changeset-8"');
    expect(view.current.value.name).toBe(' Visible name ');
    expect(view.current.value.description).toBe(' Visible description ');
    expect(view.current.operationsText).toBe(operationsText);
  });

  it('does not adopt or continue a delayed save after committed owner cleanup', async () => {
    const view = changesetAction();
    let resolve!: (value: ChangesetResponse) => void;
    view.save.mockImplementation(() => new Promise<ChangesetResponse>((done) => { resolve = done; }));
    const validate = vi.fn(async () => validation);
    const work = kind === 'save' ? saveAndAdoptChangeset(view.action, view.save)
      : kind === 'validate' ? validateChangeset(view.action, { save: view.save, validate })
        : prepareChangesetApply(view.action, view.save);
    expect(view.owner.acquire()).toBeNull();
    view.unmount();
    resolve(view.response);
    expect(await work).toBeNull();
    expect(view.adopt).not.toHaveBeenCalled();
    expect(validate).not.toHaveBeenCalled();
  });
});
