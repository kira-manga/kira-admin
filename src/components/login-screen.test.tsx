// @vitest-environment jsdom

import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { captureAdminSession } from '@/lib/client-api';
import { fixtureGeneration, otherGeneration, seedClientSession, sessionAcknowledgement } from '@/test/auth-fixture';
import { LoginScreen } from './login-screen';

let container: HTMLDivElement;
let root: Root;
const fetchMock = vi.fn<typeof fetch>();

function deferred() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => { resolve = done; });
  return { promise, resolve };
}

async function fill() {
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!;
  await act(async () => {
    for (const [type, value] of [['email', 'synthetic@example.test'], ['password', 'fixture-only']]) {
      const input = container.querySelector<HTMLInputElement>(`input[type="${type}"]`)!;
      setter.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });
}

function submit() { container.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); }

beforeEach(async () => {
  await seedClientSession();
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(async () => {
  await act(async () => { root.unmount(); });
  container.remove();
  vi.unstubAllGlobals();
});

describe('mounted login action/session lifetime', () => {
  it('rejects same-turn double submit and clears the password after a valid bounded ACK', async () => {
    const reply = deferred();
    fetchMock.mockReturnValue(reply.promise);
    const onSuccess = vi.fn();
    await act(async () => { root.render(<LoginScreen onSuccess={onSuccess} />); });
    await fill();
    await act(async () => { submit(); submit(); });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(container.querySelector<HTMLInputElement>('input[type="password"]')!.disabled).toBe(true);
    await act(async () => { reply.resolve(Response.json(sessionAcknowledgement())); });
    expect(onSuccess).toHaveBeenCalledOnce();
    expect(container.querySelector<HTMLInputElement>('input[type="password"]')!.value).toBe('');
    expect(captureAdminSession().generation).toBe(fixtureGeneration);
  });

  it('never adopts an old successful login after committed screen replacement', async () => {
    const oldReply = deferred();
    const newReply = deferred();
    fetchMock.mockReturnValueOnce(oldReply.promise).mockReturnValueOnce(newReply.promise);
    const oldSuccess = vi.fn();
    const newSuccess = vi.fn();
    await act(async () => { root.render(<LoginScreen onSuccess={oldSuccess} />); });
    await fill();
    await act(async () => { submit(); });
    await act(async () => { root.unmount(); });
    root = createRoot(container);
    await act(async () => { root.render(<LoginScreen onSuccess={newSuccess} />); });
    await fill();
    await act(async () => { submit(); });
    await act(async () => { newReply.resolve(Response.json(sessionAcknowledgement(otherGeneration))); });
    expect(newSuccess).toHaveBeenCalledOnce();
    await act(async () => { oldReply.resolve(Response.json(sessionAcknowledgement(fixtureGeneration))); });
    expect(oldSuccess).not.toHaveBeenCalled();
    expect(newSuccess).toHaveBeenCalledOnce();
    expect(captureAdminSession().generation).toBe(otherGeneration);
    expect(container.querySelector<HTMLInputElement>('input[type="password"]')!.value).toBe('');
  });
});
