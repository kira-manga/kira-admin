'use client';

import { useId, useRef, useState, type FormEvent } from 'react';

import {
  ComplaintContentError,
  createComplaintContentDraft,
  prepareComplaintContentEdit,
  type ComplaintContentDraft,
  type ComplaintContentField,
  type ComplaintContentReason,
  type ComplaintContentSnapshot,
  type ComplaintContentType,
  type PreparedComplaintContentEdit,
} from '@/lib/complaint-content-editor';
import { copyComplaintSelection } from '@/lib/complaint-text';
import { Button, Field, Textarea } from './ui';

export type ComplaintContentEditorProps = Readonly<{
  snapshot: ComplaintContentSnapshot;
  /** The caller owns key uniqueness across full editor destruction/new sessions. */
  idempotencyKey: string;
  /** Synchronous local handoff only, not a request executor or persistence hook. */
  onPrepared: (edit: PreparedComplaintContentEdit) => void;
}>;

const contentTypes: readonly ComplaintContentType[] = ['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM'];
// Unicode Bidi_Control plus the deprecated directional controls U+206A–U+206F.
const directionalControls = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u206f]/g;
const fieldLabels: Record<ComplaintContentField, string> = {
  TARGET: 'Target', TYPE: 'Type', SUBJECT: 'Subject', BODY: 'Body', CLOSURE_REASON: 'Closure reason', SEARCH: 'Search', APP_VERSION: 'App version', IDEMPOTENCY_KEY: 'Idempotency key',
};
const reasonMessages: Record<ComplaintContentReason, string> = {
  READ_ONLY: 'is read-only.',
  VARIANT_MISMATCH: 'does not match the editable content variant.',
  UNSUPPORTED_TYPE: 'is not supported.',
  REQUIRED: 'is required.',
  TOO_LONG: 'exceeds its code-point or UTF-8 byte limit.',
  FORBIDDEN_CONTROL: 'contains a forbidden control character.',
  MALFORMED_UNICODE: 'contains malformed Unicode.',
  NON_CANONICAL_UUID: 'must be a canonical lowercase UUIDv4.',
  UUID_NOT_V4: 'must be a canonical lowercase UUIDv4.',
};
type PreparationError = { key: string; field: ComplaintContentField | null; message: string };

/**
 * Local preparation; the mounted parent owns confirmation/transport. Snapshots are not authority.
 * A different target/kind/tag starts a fresh draft/capture, but never releases a
 * consumed key. Key-only rotation preserves editing and re-arms only an unused
 * key. This fence lasts until the whole outer editor is destroyed, not beyond it.
 */
export function ComplaintContentEditor(props: ComplaintContentEditorProps) {
  const { snapshot, idempotencyKey } = props;
  const [consumedKeys, setConsumedKeys] = useState<ReadonlySet<string>>(() => new Set());
  const consumedKeyFence = useRef(consumedKeys);

  function consumeKey(key: string) {
    if (consumedKeyFence.current.has(key)) return false;
    const next = new Set(consumedKeyFence.current);
    next.add(key);
    // Event-time fence precedes React's next render and the external callback.
    // Never release it, including after a target change or a callback exception.
    consumedKeyFence.current = next;
    setConsumedKeys(next);
    return true;
  }

  const identity = JSON.stringify([
    snapshot.variant, snapshot.id, 'kind' in snapshot ? snapshot.kind : null,
    'actionTag' in snapshot ? snapshot.actionTag : null,
  ]);
  return <ComplaintContentEditorSession key={identity} {...props} keyConsumed={consumedKeys.has(idempotencyKey)} consumeKey={consumeKey} />;
}

function ComplaintContentEditorSession({ snapshot, idempotencyKey, onPrepared, keyConsumed, consumeKey }: ComplaintContentEditorProps & {
  keyConsumed: boolean;
  consumeKey: (key: string) => boolean;
}) {
  const editorId = useId();
  const [draft, setDraft] = useState<ComplaintContentDraft | null>(() => {
    try {
      return createComplaintContentDraft(snapshot);
    } catch {
      // An invalid local snapshot must not accidentally expose an editable form.
      return null;
    }
  });
  const [prepared, setPrepared] = useState<PreparedComplaintContentEdit | null>(null);
  const [preparationError, setError] = useState<PreparationError | null>(null);
  const error = preparationError?.key === idempotencyKey ? preparationError : null;

  function updateBody(body: string) {
    setDraft((current) => {
      if (!current) return null;
      return current.variant === 'ordinary'
        ? { ...current, content: { ...current.content, body } }
        : { ...current, content: { body } };
    });
    setError(null);
  }

  function updateSubject(subject: string) {
    setDraft((current) => current?.variant === 'ordinary' ? { ...current, content: { ...current.content, subject } } : current);
    setError(null);
  }

  function updateType(type: ComplaintContentType) {
    setDraft((current) => current?.variant === 'ordinary' ? { ...current, content: { ...current.content, type } } : current);
    setError(null);
  }

  function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (keyConsumed) return;
    let capture: PreparedComplaintContentEdit;
    try {
      capture = prepareComplaintContentEdit(draft, idempotencyKey);
    } catch (caught) {
      setError(caught instanceof ComplaintContentError
        ? { key: idempotencyKey, field: caught.field, message: `${fieldLabels[caught.field]} ${reasonMessages[caught.reason]}` }
        : { key: idempotencyKey, field: null, message: 'The edit could not be prepared locally.' });
      return;
    }
    // A disabled button/render snapshot is not a reentrant/direct-submit fence.
    // Invalid preparation above does not consume a key; successful capture does.
    if (!consumeKey(capture.idempotencyKey)) return;
    setError(null);
    setPrepared(capture);
    // No async work, effect, retry or deferred callback. Do not update state after
    // the local handoff: the caller may synchronously replace/unmount this editor.
    onPrepared(capture);
  }

  if (!draft) {
    return (
      <section className="panel" aria-label="Complaint content editor">
        <div className="panel-heading"><div><h3>Complaint content</h3></div></div>
        <p className="notice notice-warning" role="note">
          {snapshot.variant === 'notice' ? 'NOTICE content is read-only.' : 'This target is unsupported or read-only.'} No edit can be prepared.
        </p>
      </section>
    );
  }

  const hasDirectionalMarks = Boolean(draft.content.body.match(directionalControls)?.length
    || (draft.variant === 'ordinary' && draft.content.subject.match(directionalControls)?.length));
  const heading = draft.variant === 'notice-reply' ? 'Notice-thread reply content'
    : draft.base.kind === 'REPORT' ? 'Report content' : 'Reply content';

  function describedBy(field: ComplaintContentField) {
    return [
      `${editorId}-draft-help`, hasDirectionalMarks ? `${editorId}-bidi-warning` : null,
      error?.field === field ? `${editorId}-error` : null,
    ].filter(Boolean).join(' ');
  }

  return (
    <section className="panel" aria-label="Complaint content editor">
      <div className="panel-heading"><div><span>LOCAL PREPARATION ONLY</span><h3>{heading}</h3></div></div>
      <div className="view-stack" style={{ padding: '1.25rem' }}>
        <form className="view-stack" onSubmit={prepare} noValidate>
          <p className="notice" id={`${editorId}-draft-help`}>
            Prepare a detached local capture, not a request. Normalization applies only to the capture; your visible draft is not rewritten.
          </p>
          {hasDirectionalMarks ? <p className="notice notice-warning" role="note" id={`${editorId}-bidi-warning`}>
            Directional marks are present. Visual order can differ from stored order. The editor keeps these marks unchanged; inspect their codepoints below.
          </p> : null}
          <div className="form-grid">
            {draft.variant === 'ordinary' ? <>
              <Field label="Type"><select className="input" name="type" value={draft.content.type} aria-invalid={error?.field === 'TYPE'} aria-describedby={describedBy('TYPE')} onChange={(event) => updateType(event.currentTarget.value as ComplaintContentType)}>
                {contentTypes.map((type) => <option key={type} value={type}>{type}</option>)}
              </select></Field>
              <Field label="Subject" hint="1–200 code points; at most 800 UTF-8 bytes after normalization. Newlines are allowed.">
                <Textarea name="subject" rows={2} dir="auto" style={{ unicodeBidi: 'isolate' }} value={draft.content.subject} onCopy={copyComplaintSelection} aria-invalid={error?.field === 'SUBJECT'} aria-describedby={describedBy('SUBJECT')} onChange={(event) => updateSubject(event.currentTarget.value)} />
              </Field>
            </> : null}
            <Field label="Body" hint="1–1,000 code points; at most 4,000 UTF-8 bytes after normalization." wide>
              <Textarea name="body" rows={8} dir="auto" style={{ unicodeBidi: 'isolate' }} value={draft.content.body} onCopy={copyComplaintSelection} aria-invalid={error?.field === 'BODY'} aria-describedby={describedBy('BODY')} onChange={(event) => updateBody(event.currentTarget.value)} />
            </Field>
          </div>
          {error ? <p className="notice notice-error" role="alert" id={`${editorId}-error`}>{error.message}</p> : null}
          {keyConsumed ? <p className="notice" role="note" id={`${editorId}-key-help`}>
            This supplied key has already been used for a local handoff. Another capture requires a new unused key; the local draft is retained.
          </p> : null}
          <div><Button type="submit" tone="primary" disabled={keyConsumed} aria-describedby={keyConsumed ? `${editorId}-key-help` : undefined}>Prepare edit</Button></div>
        </form>
        <section className="view-stack" aria-label="Draft inspection">
          <p className="notice">
            Inspection only: JSON-quoted text with directional marks escaped as {'\\uXXXX'} and listed as U+XXXX. These previews are not replacement text or request payloads.
          </p>
          {draft.variant === 'ordinary' ? <TextInspection label="Draft subject" value={draft.content.subject} /> : null}
          <TextInspection label="Draft body" value={draft.content.body} />
        </section>
        {prepared ? <section className="view-stack" aria-label="Last prepared content">
          <p className="notice" role="status">Prepared locally. Preparation itself sends nothing; the parent workflow reports any submission separately. This detached capture does not change when you edit the draft.</p>
          <details>
            <summary>Inspect last prepared content (not a request)</summary>
            <div className="view-stack">
              {prepared.variant === 'ordinary' ? <>
                <p className="notice">Type: {prepared.content.type}</p>
                <TextInspection label="Prepared subject" value={prepared.content.subject} />
              </> : null}
              <TextInspection label="Prepared body" value={prepared.content.body} />
            </div>
          </details>
        </section> : null}
      </div>
    </section>
  );
}

function TextInspection({ label, value }: { label: string; value: string }) {
  const marks = Array.from(new Set(value.match(directionalControls) ?? []));
  const codepoint = (mark: string) => mark.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0');
  // Quote/escape the original first, so literal "\\u202E" text remains visibly
  // distinct from an actual U+202E. This representation never re-enters the draft.
  const escaped = JSON.stringify(value).replace(directionalControls, (mark) => `\\u${codepoint(mark)}`);
  return (
    <div className="field">
      <strong>{label} inspection</strong>
      {marks.length ? <small dir="ltr" style={{ unicodeBidi: 'isolate' }}>Directional codepoints: {marks.map((mark) => `U+${codepoint(mark)}`).join(', ')}</small> : null}
      <pre className="preview-output" aria-label={`${label} inspection`} dir="ltr" style={{ unicodeBidi: 'isolate', overflowWrap: 'anywhere' }}>{escaped}</pre>
    </div>
  );
}
