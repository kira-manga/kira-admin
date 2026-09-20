'use client';

import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';

import { useActionOwner, type ActionTicket } from '@/lib/action-owner';
import { ApiError, captureAdminSession } from '@/lib/client-api';
import { prepareComplaintContentRequest } from '@/lib/complaint-content-wire';
import { sendComplaintMutation, type ComplaintOperation } from '@/lib/complaint-mutation-client';
import type { ComplaintMutationRequest } from '@/lib/complaint-mutation-wire';
import { visibleComplaintText } from '@/lib/complaint-text';
import { ComplaintReadClientError, fetchComplaintAdminDetail } from '@/lib/complaint-read-client';
import type { ParsedComplaintAdminDetail } from '@/lib/complaint-read-wire';
import type { StepUpApproval } from '@/lib/step-up-contract';
import { ComplaintContentEditor } from './complaint-content-editor';
import { ComplaintModerationEditor } from './complaint-moderation-editor';
import { ComplaintSearchView } from './complaint-search-view';
import { StepUpDialog } from './step-up-dialog';
import { Button, Field, Input, Spinner, StatusBadge } from './ui';

const messages = {
  UNAVAILABLE: 'Complaint detail unavailable or not found. The backend may not support complaint reads yet.',
  SESSION_EXPIRED: 'Your session has expired. Sign out and sign in again.',
  UNAUTHORIZED: 'This complaint read was not authorized. It does not confirm local session expiry; any retained operation is unchanged.',
  FORBIDDEN: 'You do not have permission to read this complaint.',
  INVALID_RESPONSE: 'The complaint request or response is invalid. Check the IDs before trying again.',
  NETWORK: 'The complaint could not be loaded. Check the connection and try again.',
};

type LoadedDetail = { detail: ParsedComplaintAdminDetail; dataScopeId: string; generation: string | null };
export type ComplaintDetailControls = {
  generation: string;
  operation: ComplaintOperation | null;
  changeOperation: (expected: ComplaintOperation | null, next: ComplaintOperation | null) => boolean;
  onSessionExpired: () => void;
};

function complaintText(value: string) {
  return <bdi dir="auto" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' }}>{visibleComplaintText(value)}</bdi>;
}

function terminal(operation: ComplaintOperation | null | undefined) {
  return operation?.outcome?.kind === 'applied' || operation?.outcome?.kind === 'rejected';
}

function operationMessage(operation: ComplaintOperation) {
  if (operation.phase === 'prepared') return 'Prepared only. No mutation has been sent.';
  if (operation.phase === 'sending') return 'Submitting the original operation. Leaving this view cannot cancel backend work.';
  switch (operation.outcome?.kind) {
    case 'applied': return 'Applied response verified. Reload the target before another intent.';
    case 'rejected': return 'Terminal rejection verified. The original draft is retained; reload and review before a new intent.';
    case 'step-up-required': return 'The backend requires complaint password approval. The original operation is retained.';
    case 'key-reused': return 'The backend refused this key as reused. The original operation is retained; do not silently replace it.';
    case 'unauthorized': return 'The backend did not authorize this request. This is not a local session-expiry response or password-approval request. The original operation remains unconfirmed.';
    case 'forbidden': return 'The backend denied permission. The original operation remains unconfirmed; no new intent or authority is inferred.';
    default: return 'Outcome unknown or unavailable. The original key, target, scope, tag and body are retained. No automatic retry occurs.';
  }
}

/** A real TEST workflow. Neither an entered scope nor a decoded snapshot activates the backend. */
export function ComplaintDetailView({ controls }: { controls?: ComplaintDetailControls } = {}) {
  const [id, setId] = useState('');
  const [scope, setScope] = useState('');
  const [loaded, setLoaded] = useState<LoadedDetail | null>(null);
  const [editorBase, setEditorBase] = useState<LoadedDetail | null>(null);
  const [editorKey, setEditorKey] = useState('');
  const [editorRevision, setEditorRevision] = useState(0);
  const [reviewed, setReviewed] = useState<ComplaintOperation | null>(null);
  const [confirmation, setConfirmation] = useState<ComplaintOperation | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const owner = useActionOwner();
  const active = useRef<{ ticket: ActionTicket; controller: AbortController } | null>(null);
  const mutationOwner = useActionOwner();
  const attempt = useRef<{ operation: ComplaintOperation; controller: AbortController } | null>(null);
  const changeOperation = controls?.changeOperation;
  const operation = controls?.operation ?? null;
  const ownsOperation = operation !== null && operation.generation === controls?.generation;
  const selectionBlocked = useRef(Boolean(operation));
  const detailResult = useRef<HTMLElement>(null);
  const focusSelection = useRef(false);

  useLayoutEffect(() => {
    if (loaded && focusSelection.current) { focusSelection.current = false; detailResult.current?.focus(); }
  }, [loaded]);

  useLayoutEffect(() => () => {
    active.current?.controller.abort();
    active.current = null;
    const pending = attempt.current;
    attempt.current = null;
    if (pending) {
      pending.controller.abort();
      changeOperation?.(pending.operation, Object.freeze({ ...pending.operation, phase: 'settled', outcome: { kind: 'unknown' as const } }));
    }
  }, [changeOperation]);

  function invalidate() {
    focusSelection.current = false;
    const pending = active.current;
    active.current = null;
    if (pending) {
      owner.release(pending.ticket);
      pending.controller.abort();
    }
    setLoaded(null);
    setEditorBase(null);
    setReviewed(null);
    setError('');
    setLoading(false);
  }

  async function lookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (operation || selectionBlocked.current) return;
    await load(id.trim(), scope.trim());
  }

  async function load(targetId: string, dataScopeId: string, review?: ComplaintOperation) {
    const ticket = owner.acquire();
    if (!ticket) return;
    const controller = new AbortController();
    active.current = { ticket, controller };
    if (!review) { setLoaded(null); setEditorBase(null); }
    setError('');
    setLoading(true);
    try {
      const session = controls ? captureAdminSession() : null;
      if (session && session.generation !== controls?.generation) return;
      const detail = await fetchComplaintAdminDetail({ id: targetId, dataScopeId, signal: controller.signal });
      if (ticket.isCurrent()) {
        if (session && !session.isCurrent()) { controls?.onSessionExpired(); return; }
        const next = { detail, dataScopeId, generation: session?.generation ?? null };
        setLoaded(next);
        if (review) setReviewed(review);
        else {
          setEditorBase(next);
          if (controls) { setEditorKey(crypto.randomUUID()); setEditorRevision((value) => value + 1); }
        }
      }
    } catch (caught) {
      if (ticket.isCurrent()) {
        focusSelection.current = false;
        const expired = caught instanceof ComplaintReadClientError && caught.reason === 'SESSION_EXPIRED' || caught instanceof ApiError && caught.status === 401;
        setError(messages[expired ? 'SESSION_EXPIRED' : caught instanceof ComplaintReadClientError ? caught.reason : 'NETWORK']);
        if (expired) controls?.onSessionExpired();
      }
    } finally {
      if (ticket.isCurrent()) {
        active.current = null;
        owner.release(ticket);
        setLoading(false);
      }
    }
  }

  function prepare(request: ComplaintMutationRequest) {
    if (!controls || !editorBase || operation || owner.isLocked() || mutationOwner.isLocked()) return;
    try {
      const session = captureAdminSession();
      if (session.generation !== controls.generation || editorBase.generation !== session.generation
        || request.dataScopeId !== editorBase.dataScopeId || request.targetId !== editorBase.detail.item.id) return;
      const captured: ComplaintOperation = Object.freeze({ generation: session.generation, request, phase: 'prepared' });
      if (controls.changeOperation(null, captured)) { selectionBlocked.current = true; setConfirmation(captured); setReviewed(null); }
    } catch (caught) {
      setError('Sign in again before preparing a complaint operation.');
      if (caught instanceof ApiError && caught.status === 401) controls.onSessionExpired();
    }
  }

  async function send(captured: ComplaintOperation, approval?: StepUpApproval) {
    if (!controls || captured.generation !== controls.generation) return;
    const ticket = mutationOwner.acquire();
    if (!ticket) return;
    const sending: ComplaintOperation = Object.freeze({ ...captured, phase: 'sending', outcome: undefined });
    if (!controls.changeOperation(captured, sending)) { mutationOwner.release(ticket); return; }
    setConfirmation(null);
    const controller = new AbortController();
    attempt.current = { operation: sending, controller };
    try {
      const outcome = await sendComplaintMutation(sending, controller.signal, approval);
      if (ticket.isCurrent() && controls.changeOperation(sending, Object.freeze({ ...sending, phase: 'settled', outcome }))) {
        if (outcome.kind === 'session-expired') controls.onSessionExpired();
      }
    } catch {
      if (ticket.isCurrent()) controls.changeOperation(sending, Object.freeze({ ...sending, phase: 'settled', outcome: { kind: 'unknown' as const } }));
    } finally {
      if (ticket.isCurrent()) { attempt.current = null; mutationOwner.release(ticket); }
    }
  }

  function cancelPreparation(captured: ComplaintOperation) {
    if (captured.phase === 'prepared' && controls?.changeOperation(captured, null)) { selectionBlocked.current = false; setEditorKey(crypto.randomUUID()); }
    setConfirmation(null);
  }

  function startReviewedIntent() {
    if (!controls || !operation || !terminal(operation) || reviewed !== operation || !loaded
      || loaded.generation !== operation.generation || loaded.dataScopeId !== operation.request.dataScopeId
      || loaded.detail.item.id !== operation.request.targetId) return;
    if (controls.changeOperation(operation, null)) {
      selectionBlocked.current = false;
      setEditorBase(loaded);
      setEditorKey(crypto.randomUUID());
      setEditorRevision((value) => value + 1);
      setReviewed(null);
    }
  }

  const item = loaded && (!controls || loaded.generation === controls.generation) ? loaded.detail.item : undefined;
  return (
    <div className="view-stack">
      <section className="view-heading"><div><h2>Complaint detail</h2><p>{controls ? 'TEST search, detail and non-deleting moderation. ' : 'Read-only TEST lookup. '}Use the configured TEST scope and a known complaint ID{controls ? ', or search below' : ''}. The backend enforces availability and access; this screen does not activate complaint APIs.</p></div></section>
      <form className="panel" onSubmit={(event) => { void lookup(event); }}>
        <Field label="TEST data scope ID" hint="Canonical UUID v4 supplied by the TEST environment owner.">
          <Input name="dataScopeId" value={scope} required maxLength={36} disabled={Boolean(operation)} autoComplete="off" autoCapitalize="none" spellCheck={false} onChange={(event) => { if (!operation) { invalidate(); setScope(event.target.value); } }} />
        </Field>
        <Field label="Complaint ID">
          <Input name="complaintId" value={id} required maxLength={36} disabled={Boolean(operation)} autoComplete="off" autoCapitalize="none" spellCheck={false} onChange={(event) => { if (!operation) { invalidate(); setId(event.target.value); } }} />
        </Field>
        <Button type="submit" tone="primary" disabled={loading || Boolean(operation)}>Load detail</Button>
      </form>
      {controls && !operation ? <ComplaintSearchView key={`${controls.generation}:${scope}`} generation={controls.generation} dataScopeId={scope}
        disabled={loading} onSessionExpired={controls.onSessionExpired}
        onSelect={(target) => {
          if (selectionBlocked.current || owner.isLocked() || target.generation !== controls.generation || target.dataScopeId !== scope) return;
          invalidate(); setId(target.id); focusSelection.current = true;
          void load(target.id, target.dataScopeId);
        }} /> : null}
      <div aria-live="polite" aria-atomic="true">
        {loading ? <Spinner label="Loading complaint detail" /> : null}
        {error ? <p role="alert" className="notice notice-error">{error}</p> : null}
      </div>
      {operation ? <section className="panel" aria-label="Retained complaint operation">
        {!ownsOperation ? <p role="alert">{operation.phase === 'prepared'
          ? 'An unsent preparation from a previous session is non-sendable and is not rebound to this login.'
          : 'An operation from a previous session is retained and non-sendable. It is not canceled or rebound to this login. Tab loss cannot recover it; do not assume non-execution.'}</p> : <>
          <p role="status">{operationMessage(operation)}</p>
          {operation.phase === 'prepared' ? <>
            <Button onClick={() => setConfirmation(operation)}>Confirm original operation</Button>
            <Button onClick={() => cancelPreparation(operation)}>Cancel unsent preparation</Button>
          </> : operation.phase === 'settled' && !terminal(operation) ? <>
            <Button onClick={() => { void send(operation); }}>Retry original operation without new proof</Button>
            {operation.outcome?.kind === 'step-up-required' ? <Button onClick={() => setConfirmation(operation)}>Approve original operation</Button> : null}
          </> : null}
          {terminal(operation) ? <>
            <Button disabled={loading} onClick={() => { void load(operation.request.targetId, operation.request.dataScopeId, operation); }}>Reload target to review</Button>
            {reviewed === operation ? <Button onClick={startReviewedIntent}>Start new intent from reviewed detail (discard prior draft)</Button> : null}
          </> : null}
          <details><summary>Inspect retained original body</summary><pre dir="auto" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' }}>{visibleComplaintText(operation.request.body)}</pre></details>
          <p>Retained only in this application&apos;s memory. Signing out or losing the tab does not establish an outcome; no cross-session or durable recovery is provided.</p>
        </>}
      </section> : null}
      {item ? <article className="panel" aria-label="Complaint detail result" tabIndex={-1} ref={detailResult}>
        <h3>{complaintText(item.kind === 'NOTICE' ? 'System notice' : item.subject ?? 'Notice reply')}</h3>
        <StatusBadge status={item.status} />
        <dl>
          <dt>ID</dt><dd>{complaintText(item.id)}</dd>
          <dt>Kind</dt><dd>{item.kind}</dd>
          <dt>Version</dt><dd>{item.version}</dd>
          <dt>Ownership</dt><dd>{item.ownership}</dd>
          <dt>Created</dt><dd><time dateTime={item.createdAt}>{item.createdAt}</time></dd>
          <dt>Updated</dt><dd><time dateTime={item.updatedAt}>{item.updatedAt}</time></dd>
          {item.kind === 'NOTICE' ? <><dt>Notice key</dt><dd>{complaintText(item.noticeKey)}</dd></> : <>
            <dt>Type</dt><dd>{item.type}</dd>
            <dt>Installation reference</dt><dd>{item.ownerReference}</dd>
            <dt>App version</dt><dd>{complaintText(item.appVersion ?? 'Not supplied')}</dd>
            <dt>Platform</dt><dd>{item.platform}</dd>
            <dt>OS version</dt><dd>{complaintText(item.osVersion)}</dd>
            <dt>Manufacturer</dt><dd>{complaintText(item.manufacturer)}</dd>
            <dt>Device model</dt><dd>{complaintText(item.deviceModel)}</dd>
            {item.replyToId ? <><dt>Reply to</dt><dd>{item.replyToId}</dd></> : null}
            {item.noticeKey ? <><dt>Notice key</dt><dd>{complaintText(item.noticeKey)}</dd></> : null}
            {item.closedAt ? <><dt>Closed</dt><dd><time dateTime={item.closedAt}>{item.closedAt}</time></dd><dt>Closure actor</dt><dd>{item.closureActorId}</dd></> : null}
          </>}
        </dl>
        {item.kind !== 'NOTICE' ? <>
          <h4>Body</h4><pre dir="auto" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' }}>{visibleComplaintText(item.body)}</pre>
          {item.closureReason !== null ? <><h4>Closure reason</h4><pre dir="auto" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', unicodeBidi: 'isolate' }}>{visibleComplaintText(item.closureReason)}</pre></> : null}
        </> : null}
        {!controls || item.kind === 'NOTICE' ? <p>Read-only. Editing, status changes and closure are not available.</p> : null}
      </article> : null}
      {controls && editorBase?.generation === controls.generation && editorBase.detail.moderationTarget ? <fieldset key={editorRevision} disabled={Boolean(operation)} style={{ border: 0, padding: 0, minWidth: 0 }}>
        <ComplaintContentEditor snapshot={editorBase.detail.contentSnapshot} idempotencyKey={editorKey} onPrepared={(capture) => prepare(prepareComplaintContentRequest(capture, editorBase.dataScopeId))} />
        <ComplaintModerationEditor target={editorBase.detail.moderationTarget} dataScopeId={editorBase.dataScopeId} idempotencyKey={editorKey} onPrepared={prepare} />
      </fieldset> : null}
      {confirmation && ownsOperation && operation === confirmation ? <StepUpDialog key={confirmation.request.headers['X-Kira-Idempotency-Key']}
        action="complaint moderation" scope="complaint-moderation-mutation" onCancel={() => cancelPreparation(confirmation)}
        onSessionExpired={controls?.onSessionExpired}
        onApproved={(approval) => send(confirmation, approval)} /> : null}
    </div>
  );
}
