import { describe, expect, it } from 'vitest';

import { createActionOwner } from './action-owner';

describe('synchronous action ownership', () => {
  it('rejects same-turn duplicates and holds ownership until explicitly released', () => {
    const owner = createActionOwner();
    expect(owner.acquire()).toBeNull();
    owner.mount();
    const ticket = owner.acquire()!;
    expect(ticket.isCurrent()).toBe(true);
    expect(owner.acquire()).toBeNull();
    expect(owner.isLocked()).toBe(true);
    // The same ticket stays owned between a save and an idle confirmation.
    expect(owner.acquire()).toBeNull();
    expect(owner.release(ticket)).toBe(true);
    expect(ticket.isCurrent()).toBe(false);
    expect(owner.isLocked()).toBe(false);
  });

  it('does not let stale or foreign tickets release another flight', () => {
    const owner = createActionOwner();
    const other = createActionOwner();
    owner.mount();
    other.mount();
    const old = owner.acquire()!;
    owner.release(old);
    const current = owner.acquire()!;
    expect(owner.release(old)).toBe(false);
    expect(owner.release(other.acquire()!)).toBe(false);
    expect(current.isCurrent()).toBe(true);
    expect(owner.acquire()).toBeNull();
  });

  it('revokes pending work synchronously and gives Strict Effects setup a fresh lifetime', () => {
    const owner = createActionOwner();
    const cleanup = owner.mount();
    const lifetime = owner.captureLifetime();
    const old = owner.acquire()!;
    cleanup();
    expect(old.isCurrent()).toBe(false);
    expect(lifetime()).toBe(false);
    expect(owner.acquire()).toBeNull();
    const newCleanup = owner.mount();
    const fresh = owner.acquire()!;
    expect(fresh.isCurrent()).toBe(true);
    expect(old.isCurrent()).toBe(false);
    expect(owner.release(old)).toBe(false);
    cleanup();
    expect(fresh.isCurrent()).toBe(true);
    newCleanup();
    expect(fresh.isCurrent()).toBe(false);
  });
});
