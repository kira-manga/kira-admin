import { beforeEach, describe, expect, it, vi } from 'vitest';

import { fixtureGeneration, seedClientSession, stepUpAcknowledgement } from '@/test/auth-fixture';
import { createActionOwner } from './action-owner';
import { verifyProtectedAction } from './step-up';
import type { StepUpScope } from './step-up-contract';

function approval(scope: StepUpScope = 'source-admin-mutation') {
  return Response.json(stepUpAcknowledgement(scope));
}

beforeEach(async () => { await seedClientSession(); });

function confirmation() {
  const owner = createActionOwner();
  const unmount = owner.mount();
  const ticket = owner.acquire()!;
  const clearPassword = vi.fn();
  const onApproved = vi.fn(async () => {});
  const action = { password: 'fixture-only', isCurrent: ticket.isCurrent, clearPassword, onApproved };
  return { owner, ticket, unmount, action, clearPassword, onApproved };
}

describe('protected-action verification', () => {
  it.each([401, 403])('never approves failed verification (%s)', async (status) => {
    const view = confirmation();
    const request = vi.fn(async () => new Response(JSON.stringify({ detail: 'Verify again.' }), { status }));
    await expect(verifyProtectedAction(view.action, request)).rejects.toThrow('Verify again.');
    expect(request).toHaveBeenCalledExactlyOnceWith('/api/auth/step-up', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Kira-Session-Generation': fixtureGeneration }, body: JSON.stringify({ password: 'fixture-only' }),
    });
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('propagates transport errors without approval', async () => {
    const view = confirmation();
    const request = vi.fn(async () => new Response()).mockRejectedValue(new TypeError('Verification transport failed.'));
    await expect(verifyProtectedAction(view.action, request)).rejects.toThrow('Verification transport failed.');
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('uses the existing fallback for unreadable verification problems', async () => {
    const view = confirmation();
    const request = vi.fn(async () => new Response('not JSON', { status: 401 }));
    await expect(verifyProtectedAction(view.action, request)).rejects.toThrow('Password verification failed.');
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('does not verify an already-dismissed confirmation', async () => {
    const view = confirmation();
    view.owner.release(view.ticket);
    const request = vi.fn(async () => approval());
    await verifyProtectedAction(view.action, request);
    expect(request).not.toHaveBeenCalled();
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('never approves a verification that resolves after committed unmount/remount', async () => {
    const view = confirmation();
    let resolve!: (value: Response) => void;
    const request = vi.fn(() => new Promise<Response>((done) => { resolve = done; }));
    const work = verifyProtectedAction(view.action, request);
    expect(view.owner.acquire()).toBeNull();
    view.unmount();
    view.owner.mount();
    resolve(approval());
    await work;
    expect(view.clearPassword).not.toHaveBeenCalled();
    expect(view.onApproved).not.toHaveBeenCalled();
    expect(view.owner.acquire()).not.toBeNull();
  });

  it('clears the password before approval and awaits the entire protected action', async () => {
    const view = confirmation();
    let started!: () => void;
    let complete!: () => void;
    const entered = new Promise<void>((done) => { started = done; });
    const submitted = new Promise<void>((done) => { complete = done; });
    view.onApproved.mockImplementation(async () => {
      expect(view.clearPassword).toHaveBeenCalledTimes(1);
      started();
      await submitted;
    });
    const request = vi.fn(async () => approval());
    let finished = false;
    const work = verifyProtectedAction(view.action, request).then(() => { finished = true; });
    await entered;
    expect(finished).toBe(false);
    expect(view.ticket.isCurrent()).toBe(true);
    expect(view.owner.acquire()).toBeNull();
    complete();
    await work;
    expect(view.onApproved).toHaveBeenCalledTimes(1);
    expect(view.owner.release(view.ticket)).toBe(true);
  });

  it('still propagates failure of an already-dispatched action after owner cleanup', async () => {
    const view = confirmation();
    let started!: () => void;
    let reject!: (error: Error) => void;
    const entered = new Promise<void>((done) => { started = done; });
    const submitted = new Promise<void>((_, fail) => { reject = fail; });
    view.onApproved.mockImplementation(async () => { started(); await submitted; });
    const request = vi.fn(async () => approval());
    const work = verifyProtectedAction(view.action, request);
    await entered;
    view.unmount();
    const failure = expect(work).rejects.toThrow('Protected request failed after dispatch.');
    reject(new Error('Protected request failed after dispatch.'));
    await failure;
    expect(view.onApproved).toHaveBeenCalledTimes(1);
  });

  it.each([undefined, 'source-admin-mutation', 'complaint-moderation-mutation'] as const)
  ('requires the exact scope acknowledgement for %s and never exposes a proof', async (scope) => {
    const view = confirmation();
    const selected = scope ?? 'source-admin-mutation';
    const request = vi.fn(async () => approval(selected));
    await verifyProtectedAction({ ...view.action, scope }, request);
    expect(request).toHaveBeenCalledExactlyOnceWith('/api/auth/step-up', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Kira-Session-Generation': fixtureGeneration },
      body: JSON.stringify({ password: 'fixture-only', ...(selected === 'complaint-moderation-mutation' ? { scope: selected } : {}) }),
    });
    expect(view.clearPassword).toHaveBeenCalledOnce();
    expect(view.onApproved).toHaveBeenCalledOnce();
  });

  it.each([
    { scope: 'complaint-moderation-mutation' }, { scope: 'SOURCE_CONFIG_WRITE' }, { scope: undefined },
    { expiresAt: '2000-01-01T00:00:00Z' }, { expiresAt: 'not-a-date' }, { expiresAt: undefined },
    { token: 'must-never-reach-browser-approval' }, { generation: undefined }, { proofId: undefined },
    { proofId: 'not-an-identity' }, { generation: '87654321-1234-4234-8234-123456789abc' },
  ])('does not approve invalid source acknowledgement %j', async (fields) => {
    const view = confirmation();
    const request = vi.fn(async () => Response.json({ ...stepUpAcknowledgement(), ...fields }));
    await expect(verifyProtectedAction(view.action, request)).rejects.toThrow('Password verification could not be confirmed.');
    expect(view.clearPassword).not.toHaveBeenCalled();
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('refuses an old source-only backend acknowledgement for a complaint confirmation', async () => {
    const view = confirmation();
    const request = vi.fn(async () => approval());
    await expect(verifyProtectedAction({ ...view.action, scope: 'complaint-moderation-mutation' }, request)).rejects.toThrow('could not be confirmed');
    expect(request).toHaveBeenCalledOnce();
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it.each(['unknown', null])('refuses invalid runtime scope %s before requesting a password proof', async (scope) => {
    const view = confirmation();
    const request = vi.fn(async () => approval());
    await expect(verifyProtectedAction({ ...view.action, scope: scope as StepUpScope }, request)).rejects.toThrow('Invalid password verification scope.');
    expect(request).not.toHaveBeenCalled();
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('does not treat an empty 204 as password approval', async () => {
    const view = confirmation();
    const request = vi.fn(async () => new Response(null, { status: 204 }));
    await expect(verifyProtectedAction(view.action, request)).rejects.toThrow('could not be confirmed');
    expect(view.onApproved).not.toHaveBeenCalled();
  });

  it('rechecks ownership after asynchronous acknowledgement decoding', async () => {
    const view = confirmation();
    let resolve!: (value: unknown) => void;
    let entered!: () => void;
    const started = new Promise<void>((done) => { entered = done; });
    const response = new Response(new ReadableStream({
      start(controller) { resolve = (value) => { controller.enqueue(new TextEncoder().encode(JSON.stringify(value))); controller.close(); }; },
      pull() { entered(); return new Promise<void>(() => {}); },
    }, { highWaterMark: 0 }));
    const work = verifyProtectedAction(view.action, vi.fn(async () => response));
    await started;
    view.unmount();
    view.owner.mount();
    resolve(stepUpAcknowledgement());
    await work;
    expect(view.onApproved).not.toHaveBeenCalled();
    expect(view.clearPassword).not.toHaveBeenCalled();
  });
});
