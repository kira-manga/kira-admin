'use client';

import { useLayoutEffect, useState } from 'react';

export type ActionTicket = { isCurrent: () => boolean };

/** Synchronous ownership, including the idle time while a confirmation is open. */
export function createActionOwner() {
  let lifetime: object | null = null;
  let current: ActionTicket | null = null;

  return {
    mount() {
      const mounted = {};
      lifetime = mounted;
      current = null;
      return () => {
        if (lifetime === mounted) {
          lifetime = null;
          current = null;
        }
      };
    },
    captureLifetime() {
      const captured = lifetime;
      return () => captured !== null && lifetime === captured;
    },
    isLocked: () => lifetime === null || current !== null,
    acquire(): ActionTicket | null {
      if (lifetime === null || current !== null) return null;
      const captured = lifetime;
      const ticket: ActionTicket = { isCurrent: () => lifetime === captured && current === ticket };
      current = ticket;
      return ticket;
    },
    release(ticket: ActionTicket) {
      if (current !== ticket || !ticket.isCurrent()) return false;
      current = null;
      return true;
    },
  };
}

export function useActionOwner() {
  const [owner] = useState(createActionOwner);
  // Layout cleanup revokes continuations at committed unmount, not at a later
  // passive cleanup. Each setup creates a fresh lifetime for Strict Effects too.
  useLayoutEffect(() => owner.mount(), [owner]);
  return owner;
}
