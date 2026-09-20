import { isCsrfToken, isFutureExpiry, isSessionAcknowledgement, isSessionSelector, mediaGenerationQuery, sessionGenerationHeader, stepUpProofIdHeader, type SessionAcknowledgement } from './session-contract';
import { isStepUpApproval, type StepUpApproval } from './step-up-contract';
import type { AdminSession } from './types';

type Problem = { detail?: string; title?: string; message?: string; fieldErrors?: Array<{ message?: string }> };
export type UploadProgress = { loaded: number; total: number; percent: number };
const selectorStorageKey = 'kira-admin-session-generation';
let selected: Partial<SessionAcknowledgement> | null | undefined;
let sessionVersion = 0;
let refreshVersion = 0;

function selection() {
  if (selected === undefined) {
    let generation: string | null = null;
    try { generation = globalThis.sessionStorage?.getItem(selectorStorageKey) ?? null; } catch { /* Memory-only selection; reload requires login. */ }
    selected = isSessionSelector(generation) ? { generation } : null;
  }
  return selected;
}

function select(value: SessionAcknowledgement | null) {
  selected = value;
  try {
    if (value) globalThis.sessionStorage?.setItem(selectorStorageKey, value.generation);
    else globalThis.sessionStorage?.removeItem(selectorStorageKey);
  } catch { /* Do not fall back to another tab's cookies or browser-readable credentials. */ }
}

/** Client lifetime only. The signed HttpOnly envelope, never this selector, authenticates the BFF. */
export function captureAdminSession() {
  const captured = selection();
  const version = sessionVersion;
  if (!captured || !isSessionSelector(captured.generation) || !isCsrfToken(captured.csrfToken) || !isFutureExpiry(captured.expiresAt)) {
    throw new ApiError('Sign in again before continuing.', 401);
  }
  return { generation: captured.generation, csrfToken: captured.csrfToken,
    isCurrent: () => sessionVersion === version && selection()?.generation === captured.generation
      && selection()?.csrfToken === captured.csrfToken && isFutureExpiry(captured.expiresAt),
  };
}

function sessionHeaders(init: RequestInit) {
  const captured = captureAdminSession();
  const headers = new Headers(init.headers);
  const explicit = headers.get(sessionGenerationHeader);
  if (explicit !== null && explicit !== captured.generation) throw new ApiError('This action belongs to a previous admin session.', 401);
  headers.set(sessionGenerationHeader, captured.generation);
  headers.set('X-Kira-CSRF', captured.csrfToken);
  return headers;
}

export function sourceApprovalInit(approval: StepUpApproval, init: RequestInit = {}): RequestInit {
  const captured = captureAdminSession();
  if (!isStepUpApproval(approval, 'source-admin-mutation') || approval.generation !== captured.generation) {
    throw new ApiError('Verify your password again for this action.', 403);
  }
  const headers = new Headers(init.headers);
  headers.set(sessionGenerationHeader, approval.generation);
  headers.set(stepUpProofIdHeader, approval.proofId);
  return { ...init, headers };
}

// Only an opaque G is in the URL: <img> cannot supply our selection header.
export function adminMediaUrl(id: string) {
  return `/api/media/${encodeURIComponent(id)}?${mediaGenerationQuery}=${selection()?.generation ?? ''}`;
}

/** Tiny authentication ACKs are bounded while reading, not after an unbounded response.json(). */
export async function readAuthAcknowledgement(response: Response): Promise<unknown> {
  const reader = response.body?.getReader();
  if (!reader) return null;
  const bytes = new Uint8Array(4096);
  let length = 0;
  try {
    while (true) {
      const next = await reader.read();
      if (next.done) return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes.subarray(0, length))) as unknown;
      if (next.value.byteLength > bytes.length - length) throw new Error('Authentication acknowledgement exceeds its bound.');
      bytes.set(next.value, length);
      length += next.value.byteLength;
    }
  } finally {
    void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function readError(response: Response) {
  try {
    const problem = await response.json() as Problem;
    return problem.detail ?? problem.fieldErrors?.[0]?.message ?? problem.message ?? problem.title ?? `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

function readUploadError(request: XMLHttpRequest) {
  try {
    const problem = JSON.parse(request.responseText) as Problem;
    return problem.detail ?? problem.fieldErrors?.[0]?.message ?? problem.message ?? problem.title ?? `Request failed (${request.status})`;
  } catch {
    return `Request failed (${request.status})`;
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  return (await apiFetchWithMeta<T>(path, init)).data;
}

export async function apiFetchWithMeta<T>(path: string, init: RequestInit = {}): Promise<{ data: T; etag: string | null; historyNextBefore?: string }> {
  const headers = sessionHeaders(init);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`/api/backend/${path.replace(/^\//, '')}`, { ...init, headers, cache: 'no-store' });
  if (!response.ok) throw new ApiError(await readError(response), response.status);
  const historyNextBefore = response.headers.get('X-Kira-History-Next-Before');
  const metadata = { etag: response.headers.get('etag'), ...(historyNextBefore ? { historyNextBefore } : {}) };
  if (response.status === 204) return { data: undefined as T, ...metadata };
  return { data: await response.json() as T, ...metadata };
}

export function apiUpload<T>(endpoint: string, body: FormData, onProgress: (progress: UploadProgress) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    const captured = captureAdminSession();
    const request = new XMLHttpRequest();
    request.open('POST', endpoint);
    request.timeout = 70_000;
    request.setRequestHeader('Accept', 'application/json, application/problem+json');
    request.setRequestHeader('X-Kira-CSRF', captured.csrfToken);
    request.setRequestHeader(sessionGenerationHeader, captured.generation);
    request.upload.addEventListener('progress', (event) => {
      if (!event.lengthComputable || event.total <= 0) return;
      onProgress({ loaded: event.loaded, total: event.total, percent: Math.min(100, Math.round((event.loaded / event.total) * 100)) });
    });
    request.addEventListener('load', () => {
      if (request.status < 200 || request.status >= 300) {
        reject(new ApiError(readUploadError(request), request.status));
        return;
      }
      onProgress({ loaded: body.get('file') instanceof File ? (body.get('file') as File).size : 1, total: body.get('file') instanceof File ? (body.get('file') as File).size : 1, percent: 100 });
      if (request.status === 204 || !request.responseText) {
        resolve(undefined as T);
        return;
      }
      try {
        resolve(JSON.parse(request.responseText) as T);
      } catch {
        reject(new ApiError('The server returned an invalid response.', request.status));
      }
    });
    request.addEventListener('error', () => reject(new ApiError('Upload failed because the server could not be reached.', 0)));
    request.addEventListener('abort', () => reject(new ApiError('Upload was cancelled.', 0)));
    request.addEventListener('timeout', () => reject(new ApiError('The production API timed out while processing the upload.', 504)));
    request.send(body);
  });
}

export async function loginSession(credentials: { email: string; password: string }, isCurrent: () => boolean) {
  if (!isCurrent()) return false;
  const version = ++sessionVersion;
  const current = () => version === sessionVersion && isCurrent();
  const response = await fetch('/api/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(credentials), cache: 'no-store',
  });
  if (!current()) { void response.body?.cancel().catch(() => {}); return false; }
  if (!response.ok) throw new ApiError(await readError(response), response.status);
  const acknowledgement = await readAuthAcknowledgement(response).catch(() => null);
  if (!current()) return false;
  if (response.status !== 200 || !isSessionAcknowledgement(acknowledgement)) throw new ApiError('Sign in could not be confirmed.', 502);
  select(acknowledgement);
  return true;
}

export async function sessionFetch(isCurrent: () => boolean = () => true): Promise<AdminSession | null | undefined> {
  const generation = selection()?.generation;
  const version = sessionVersion;
  const refresh = ++refreshVersion;
  const current = () => isCurrent() && version === sessionVersion && refresh === refreshVersion && selection()?.generation === generation;
  if (!isSessionSelector(generation)) return current() ? null : undefined;
  const response = await fetch('/api/auth/session', { headers: { [sessionGenerationHeader]: generation }, cache: 'no-store' });
  if (!current()) { void response.body?.cancel().catch(() => {}); return undefined; }
  if (!response.ok) {
    if (response.status !== 401 && response.status !== 403) throw new ApiError('The admin session could not be checked. Try signing in again.', response.status);
    sessionVersion++;
    select(null);
    return null;
  }
  const session = await readAuthAcknowledgement(response).catch(() => null) as AdminSession | null;
  if (!current()) return undefined;
  if (!session || Object.keys(session).length !== 7 || session.generation !== generation || session.role !== 'ADMIN'
    || typeof session.id !== 'string' || typeof session.email !== 'string' || typeof session.createdAt !== 'string'
    || !isSessionAcknowledgement({ generation: session.generation, csrfToken: session.csrfToken, expiresAt: session.expiresAt })) {
    throw new ApiError('The admin session could not be confirmed.', 502);
  }
  select({ generation, csrfToken: session.csrfToken, expiresAt: session.expiresAt });
  return session;
}

export async function logoutSession() {
  let headers: Headers;
  try { headers = sessionHeaders({}); } finally {
    // Retire client ownership synchronously, not when a possibly delayed logout response arrives.
    sessionVersion++;
    select(null);
  }
  const response = await fetch('/api/auth/logout', { method: 'POST', headers, cache: 'no-store' });
  if (!response.ok) throw new ApiError('Signed out locally; server sign-out could not be confirmed.', response.status);
}

export async function authenticatedFetch(path: string, init: RequestInit = {}) {
  const headers = sessionHeaders(init);
  return fetch(path, { ...init, headers, cache: 'no-store' });
}
