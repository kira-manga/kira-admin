import type { SourceChange, SourceChangeset } from '@/lib/types';

import { apiFetch, apiFetchWithMeta } from './client-api';

export type ChangesetEditorSnapshot = { value: SourceChangeset; etag: string; operationsText: string };
export type ChangesetEditorAction = {
  id: string;
  current: ChangesetEditorSnapshot;
  isCurrent: () => boolean;
  adopt: (saved: ChangesetEditorSnapshot) => void;
};
export type PreparedChangesetApply = { id: string; snapshot: ChangesetEditorSnapshot };

type ChangesetRequest = typeof apiFetchWithMeta<SourceChangeset>;
type ChangesetValidation = { valid: boolean; operationCount: number; affectedApis: string[] };
type ChangesetApplication = { documentRevision: number; affectedApis: string[] };

export function parseOperations(value: string, tolerateInvalid = false): SourceChange[] {
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) throw new Error('Operations must be a JSON array.');
    return parsed as SourceChange[];
  } catch (caught) {
    if (tolerateInvalid) return [];
    throw caught;
  }
}

export async function saveAndAdoptChangeset(
  action: ChangesetEditorAction,
  request: ChangesetRequest = apiFetchWithMeta<SourceChangeset>,
) {
  if (!action.isCurrent()) return null;
  // Only the unrelated add-operation toolbar tolerates incomplete JSON.
  const operations = parseOperations(action.current.operationsText);
  const result = await request(`source-changesets/${action.id}`, {
    method: 'PUT',
    headers: { 'If-Match': action.current.etag },
    body: JSON.stringify({ name: action.current.value.name, description: action.current.value.description, operations }),
  });
  if (!result.etag) throw new Error('The backend did not return the updated changeset ETag.');
  if (!action.isCurrent()) return null;
  const saved = { value: result.data, etag: result.etag, operationsText: JSON.stringify(result.data.operations, null, 2) };
  action.adopt(saved);
  return saved;
}

export async function validateChangeset(
  action: ChangesetEditorAction,
  requests = { save: apiFetchWithMeta<SourceChangeset>, validate: apiFetch<ChangesetValidation> },
) {
  const saved = await saveAndAdoptChangeset(action, requests.save);
  if (!saved || !action.isCurrent()) return null;
  const result = await requests.validate(`source-changesets/${action.id}/validate`, {
    method: 'POST',
    headers: { 'If-Match': saved.etag },
  });
  return action.isCurrent() ? result : null;
}

export async function prepareChangesetApply(
  action: ChangesetEditorAction,
  request: ChangesetRequest = apiFetchWithMeta<SourceChangeset>,
): Promise<PreparedChangesetApply | null> {
  const saved = await saveAndAdoptChangeset(action, request);
  return saved && action.isCurrent() ? { id: action.id, snapshot: saved } : null;
}

export async function applySavedChangeset(
  pending: PreparedChangesetApply,
  isCurrent: () => boolean,
  request = apiFetch<ChangesetApplication>,
) {
  if (!isCurrent()) return null;
  const result = await request(`source-changesets/${pending.id}/apply`, {
    method: 'POST',
    headers: { 'If-Match': pending.snapshot.etag },
  });
  // Apply closes the changeset; its outcome has no replacement changeset ETag.
  return isCurrent() ? result : null;
}
