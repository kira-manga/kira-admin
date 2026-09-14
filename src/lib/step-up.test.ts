import { describe, expect, it, vi } from 'vitest';

import { createActionOwner } from './action-owner';
import { verifyProtectedAction } from './step-up';

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
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: 'fixture-only' }),
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
    const request = vi.fn(async () => new Response(null, { status: 204 }));
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
    resolve(new Response(null, { status: 204 }));
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
    const request = vi.fn(async () => new Response(null, { status: 204 }));
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
    const request = vi.fn(async () => new Response(null, { status: 204 }));
    const work = verifyProtectedAction(view.action, request);
    await entered;
    view.unmount();
    const failure = expect(work).rejects.toThrow('Protected request failed after dispatch.');
    reject(new Error('Protected request failed after dispatch.'));
    await failure;
    expect(view.onApproved).toHaveBeenCalledTimes(1);
  });
});
