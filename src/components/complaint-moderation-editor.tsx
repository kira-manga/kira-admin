'use client';

import { useId, useRef, useState, type FormEvent } from 'react';

import {
  prepareComplaintModerationRequest,
  type ComplaintModerationChange,
  type ComplaintModerationTarget,
  type ComplaintStatusTarget,
} from '@/lib/complaint-moderation-wire';
import type { ComplaintMutationRequest } from '@/lib/complaint-mutation-wire';
import { Button, Field, Textarea } from './ui';

export type ComplaintModerationEditorProps = Readonly<{
  /** Local data only, not authentication, authorization or verified snapshot intake. */
  target: ComplaintModerationTarget;
  dataScopeId: string;
  /** The caller owns key uniqueness and original descriptions beyond this editor's lifetime. */
  idempotencyKey: string;
  /** Synchronous local handoff only, not a transport or persistence hook. */
  onPrepared: (request: ComplaintMutationRequest) => void;
}>;

const statusTargets: readonly ComplaintStatusTarget[] = ['OPEN', 'IN_PROGRESS', 'PLANNED', 'RESOLVED', 'NOT_PLANNED'];
// Match the content editor's inspection of Bidi_Control and deprecated directional controls.
const directionalControls = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u206f]/g;
type PreparationError = { key: string; statusRequired?: boolean; message: string };

/**
 * Deliberately unmounted. Target/tag/scope changes retire the draft and last capture,
 * not consumed keys. An unused key alone preserves editing; it is never a retry.
 * This event-time fence is local to the outer editor, not durable recovery state.
 */
export function ComplaintModerationEditor(props: ComplaintModerationEditorProps) {
  const [consumedKeys, setConsumedKeys] = useState<ReadonlySet<string>>(() => new Set());
  const consumedKeyFence = useRef(consumedKeys);

  function consumeKey(key: string) {
    if (consumedKeyFence.current.has(key)) return false;
    const next = new Set(consumedKeyFence.current);
    next.add(key);
    // Fence before React renders and before the external callback can reenter or throw.
    consumedKeyFence.current = next;
    setConsumedKeys(next);
    return true;
  }

  const { target, dataScopeId, idempotencyKey } = props;
  const identity = JSON.stringify([target.id, target.actionTag, target.kind, target.ownership, dataScopeId]);
  return <ComplaintModerationEditorSession key={identity} {...props} keyConsumed={consumedKeys.has(idempotencyKey)} consumeKey={consumeKey} />;
}

function ComplaintModerationEditorSession({ target, dataScopeId, idempotencyKey, onPrepared, keyConsumed, consumeKey }: ComplaintModerationEditorProps & {
  keyConsumed: boolean;
  consumeKey: (key: string) => boolean;
}) {
  const editorId = useId();
  const [base] = useState<ComplaintModerationTarget>(() => Object.freeze({
    id: target.id, actionTag: target.actionTag, kind: target.kind, ownership: target.ownership,
  }));
  const [operation, setOperation] = useState<ComplaintModerationChange['operation']>('status');
  const [status, setStatus] = useState<ComplaintStatusTarget | ''>('');
  const [reason, setReason] = useState('');
  const [prepared, setPrepared] = useState<ComplaintMutationRequest | null>(null);
  const [preparationError, setError] = useState<PreparationError | null>(null);
  const error = preparationError?.key === idempotencyKey ? preparationError : null;

  function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (keyConsumed) return;
    let request: ComplaintMutationRequest;
    try {
      if (operation === 'status') {
        if (!status) {
          setError({ key: idempotencyKey, statusRequired: true, message: 'Choose a status target before preparing.' });
          return;
        }
        request = prepareComplaintModerationRequest(base, { operation, status }, dataScopeId, idempotencyKey);
      } else {
        request = prepareComplaintModerationRequest(base, { operation, reason }, dataScopeId, idempotencyKey);
      }
    } catch {
      // The shared helper validates the complete description; never expose raw inputs/errors.
      setError({ key: idempotencyKey, message: 'The supplied target, TEST scope, key or change is invalid. Nothing was sent or saved.' });
      return;
    }
    if (!consumeKey(request.headers['X-Kira-Idempotency-Key'])) return;
    setError(null);
    setPrepared(request);
    // Nothing after the handoff: a caller can replace/unmount the editor or throw.
    onPrepared(request);
  }

  if ((base.kind !== 'REPORT' && base.kind !== 'REPLY') || base.ownership !== 'INSTALLATION') {
    return <section className="panel" aria-label="Complaint moderation editor">
      <div className="panel-heading"><div><h3>Complaint moderation</h3></div></div>
      <p className="notice notice-warning" role="note">This target is unsupported or read-only. No moderation description can be prepared.</p>
    </section>;
  }

  const hasDirectionalMarks = operation === 'closure' && Boolean(reason.match(directionalControls)?.length);
  const describedBy = [
    `${editorId}-help`, error ? `${editorId}-error` : null, hasDirectionalMarks ? `${editorId}-bidi-warning` : null,
  ].filter(Boolean).join(' ');

  return (
    <section className="panel" aria-label="Complaint moderation editor">
      <div className="panel-heading"><div><span>LOCAL PREPARATION ONLY</span><h3>{base.kind === 'REPORT' ? 'Report' : 'Reply'} moderation</h3></div></div>
      <div className="view-stack" style={{ padding: '1.25rem' }}>
        <form className="view-stack" onSubmit={prepare} noValidate aria-describedby={describedBy}>
          <p className="notice" id={`${editorId}-help`}>
            Prepare a local TEST-only description, not a request execution. Supplied target and scope are not authorization.
            The caller must retain original descriptions for recovery; a different key, tag or body is not a retry.
          </p>
          <div className="form-grid">
            <Field label="Operation"><select className="input" name="operation" value={operation} aria-describedby={describedBy} onChange={(event) => {
              setOperation(event.currentTarget.value as ComplaintModerationChange['operation']);
              setError(null);
            }}>
              <option value="status">Change status</option>
              <option value="closure">Close with reason</option>
            </select></Field>
            {operation === 'status' ? <Field label="Status target"><select className="input" name="status" value={status} aria-invalid={Boolean(error?.statusRequired)} aria-describedby={describedBy} onChange={(event) => {
              setStatus(event.currentTarget.value as ComplaintStatusTarget | '');
              setError(null);
            }}>
              <option value="" disabled>Choose a status target</option>
              {statusTargets.map((value) => <option key={value} value={value}>{value}</option>)}
            </select></Field> : operation === 'closure' ? <Field label="Closure reason" hint="1–500 code points; at most 2,000 UTF-8 bytes after normalization. Your visible draft is not rewritten." wide>
              <Textarea name="reason" rows={5} dir="auto" style={{ unicodeBidi: 'isolate' }} value={reason} aria-describedby={describedBy} onChange={(event) => {
                setReason(event.currentTarget.value);
                setError(null);
              }} />
            </Field> : null}
          </div>
          {hasDirectionalMarks ? <p className="notice notice-warning" role="note" id={`${editorId}-bidi-warning`}>
            Directional marks are present. Visual order can differ from stored order. They remain unchanged; prepared-body inspection escapes them as {'\\uXXXX'}.
          </p> : null}
          {error ? <p className="notice notice-error" role="alert" id={`${editorId}-error`}>{error.message}</p> : null}
          {keyConsumed ? <p className="notice" role="note" id={`${editorId}-key-help`}>
            This supplied key has already been used for a local handoff. Keep that original description on uncertainty; another key is not a retry. The draft remains editable.
          </p> : null}
          <div><Button type="submit" tone="primary" disabled={keyConsumed} aria-describedby={keyConsumed ? `${editorId}-key-help` : undefined}>Prepare description</Button></div>
        </form>
        {prepared ? <section className="view-stack" aria-label="Last prepared moderation">
          <p className="notice" role="status">Prepared locally. Nothing was sent or saved. Later draft edits do not change this description.</p>
          <details>
            <summary>Inspect last prepared body (not sent)</summary>
            <pre className="preview-output" aria-label="Last prepared body inspection" dir="ltr" style={{ unicodeBidi: 'isolate', overflowWrap: 'anywhere' }}>
              {prepared.body.replace(directionalControls, (mark) => `\\u${mark.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}`)}
            </pre>
          </details>
        </section> : null}
      </div>
    </section>
  );
}
