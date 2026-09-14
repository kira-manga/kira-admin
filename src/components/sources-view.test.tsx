// @vitest-environment jsdom

import { act, Profiler } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { SourceCapabilities, SourceDraft, SourceHead, SourceRevision } from '@/lib/types';
import { SourcesView } from './sources-view';

// Real view, hooks, client metadata parsing and authoring helpers. Only fetch is
// replaced; this emulated DOM does not claim browser/BFF cookie or layout proof.
const stamp = '2026-09-11T00:00:00Z';
const sourceA: SourceHead = {
  api: 'Azora', displayName: 'Source Alpha', language: 'en', engine: 'generic', status: 'active',
  operationalMode: 'enabled', position: 0, baseUrl: 'https://alpha.example.test', adult: false,
  currentPublishedRevisionNumber: 119, latestRevisionNumber: 119, createdAt: stamp, updatedAt: stamp, publishedAt: stamp,
};
const sourceB: SourceHead = {
  ...sourceA, api: 'Beta +%', displayName: 'Source Beta', position: 1, baseUrl: 'https://beta.example.test',
  currentPublishedRevisionNumber: 219, latestRevisionNumber: 219,
};
const capabilities: SourceCapabilities = {
  sourceSchemaVersion: 1, catalogSchemaVersion: 2, canonicalization: 'kcj-1', authorableEngines: ['generic'],
  serverLifecycleStates: [], transforms: [], dateStrategies: [], imageStrategies: [], paginationStrategies: [],
  endpointMethods: ['GET'], endpointFormats: ['HTML'], editorDraftMaxBytes: 100_000,
  optimisticLocking: 'etag', publicEnginePolicy: 'generic',
};
const latestNumbers = Array.from({ length: 20 }, (_, index) => 100 + index);
const olderNumbers = Array.from({ length: 20 }, (_, index) => 60 + index);
const betaNumbers = Array.from({ length: 20 }, (_, index) => 200 + index);
const refreshedNumbers = Array.from({ length: 20 }, (_, index) => 101 + index);

function revisions(numbers: number[], published = 119): SourceRevision[] {
  return numbers.map((revisionNumber) => ({
    revisionNumber, status: revisionNumber === published ? 'published' : 'draft',
    checksum: String(revisionNumber).padStart(64, '0'), createdBy: 'fixture-admin', createdAt: stamp,
    publishedAt: revisionNumber === published ? stamp : null, valid: true,
  }));
}

function historyResponse(numbers: number[], nextBefore?: string, published = 119) {
  return Response.json(revisions(numbers, published), {
    headers: nextBefore ? { 'X-Kira-History-Next-Before': nextBefore } : {},
  });
}

function historyUrl(api = sourceA.api, before?: string) {
  return `/api/backend/sources/${encodeURIComponent(api)}/revisions?size=20${before ? `&beforeRevision=${before}` : ''}`;
}

function draftFor(source = sourceA, revision = source.latestRevisionNumber ?? 1, version = 4): SourceDraft {
  return {
    id: `fixture-draft-${source.api}`, basedOnRevisionNumber: revision,
    content: JSON.stringify({ api: source.api, displayName: source.displayName, baseUrl: source.baseUrl, language: 'en', sourceRevision: revision }),
    version, createdBy: 'fixture-admin', updatedBy: 'fixture-admin', createdAt: stamp, updatedAt: stamp,
  };
}

type RequestRecord = { url: string; method: string; init: RequestInit | undefined };
type PlannedRequest = {
  url: string; method: string; received: RequestRecord | null; settled: boolean; response: Promise<Response>;
  reply: (response: Response) => void; fail: (error: Error) => void;
};
type CommitSnapshot = { source: string | null; rows: string[]; draftRows: string[] };
let container: HTMLDivElement;
let root: Root | null;
let planned: PlannedRequest[];
let requests: RequestRecord[];
let unexpected: string[];
let commits: CommitSnapshot[];
const fetchMock = vi.fn<typeof fetch>();

function plan(method: string, url: string): PlannedRequest {
  let resolve!: (response: Response) => void;
  let reject!: (error: Error) => void;
  const response = new Promise<Response>((done, fail) => { resolve = done; reject = fail; });
  const request: PlannedRequest = {
    method, url, response, received: null, settled: false,
    reply: (value) => { request.settled = true; resolve(value); },
    fail: (error) => { request.settled = true; reject(error); },
  };
  planned.push(request);
  return request;
}

async function deliver(request: PlannedRequest, response: Response) {
  expect(request.received).not.toBeNull();
  await act(async () => { request.reply(response); });
}

function button(name: string, scope: ParentNode = container): HTMLButtonElement {
  const result = Array.from(scope.querySelectorAll<HTMLButtonElement>('button'))
    .find((item) => (item.getAttribute('aria-label') ?? item.textContent?.trim()) === name);
  if (!result) throw new Error(`Missing button: ${name}`);
  return result;
}

function sourceButton(source: SourceHead): HTMLButtonElement {
  const result = Array.from(container.querySelectorAll<HTMLButtonElement>('.source-row'))
    .find((item) => item.querySelector('strong')?.textContent === source.displayName);
  if (!result) throw new Error(`Missing source: ${source.api}`);
  return result;
}

function rowButton(revision: number) {
  const row = Array.from(container.querySelectorAll<HTMLElement>('.revision-list article'))
    .find((item) => item.querySelector('.revision-number')?.textContent === `r${revision}`);
  if (!row) throw new Error(`Missing revision row: ${revision}`);
  return button('Open draft', row);
}

function rows() {
  return Array.from(container.querySelectorAll('.revision-number')).map((item) => item.textContent ?? '');
}

function expectRows(numbers: number[]) {
  expect(rows()).toEqual(numbers.map((number) => `r${number}`));
}

function expectLoading() {
  expectRows([]);
  expect(container.querySelector('.revision-list')?.getAttribute('aria-busy')).toBe('true');
  expect(container.querySelector('.revision-list')?.textContent).toContain('Loading source revisions');
  expect(button('Older').disabled).toBe(true);
  expect(container.querySelector('.notice-error')).toBeNull();
}

function headPointers() {
  return Array.from(container.querySelectorAll('.detail-meta strong')).slice(0, 2).map((item) => item.textContent);
}

async function click(element: HTMLElement) {
  await act(async () => { element.click(); });
}

async function mountSources() {
  plan('GET', '/api/backend/sources').reply(Response.json([sourceA, sourceB]));
  plan('GET', '/api/backend/source-studio/capabilities').reply(Response.json(capabilities));
  const history = plan('GET', historyUrl());
  root = createRoot(container);
  await act(async () => {
    root!.render(<Profiler id="sources" onRender={() => {
      commits.push({
        source: container.querySelector('.detail-hero h3')?.textContent ?? null,
        rows: rows(),
        draftRows: Array.from(container.querySelectorAll('.revision-list article'))
          .filter((item) => item.querySelector('button'))
          .map((item) => item.querySelector('.revision-number')?.textContent ?? ''),
      });
    }}><SourcesView /></Profiler>);
  });
  expect(history.received).not.toBeNull();
  return history;
}

async function readySources() {
  const history = await mountSources();
  await deliver(history, historyResponse(latestNumbers, '100'));
  return history;
}

async function unmount() {
  const mounted = root;
  root = null;
  if (mounted) await act(async () => { mounted.unmount(); });
}

async function enterPassword() {
  const input = container.querySelector<HTMLInputElement>('[role="dialog"] input[type="password"]');
  if (!input) throw new Error('Missing protected-action password input.');
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
  if (!setter) throw new Error('Missing native input value setter.');
  await act(async () => {
    setter.call(input, 'fixture-only-password');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
}

beforeEach(() => {
  container = document.createElement('div');
  document.body.append(container);
  root = null;
  planned = [];
  requests = [];
  unexpected = [];
  commits = [];
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  fetchMock.mockReset();
  fetchMock.mockImplementation((input, init) => {
    const record = { url: String(input), method: init?.method ?? 'GET', init };
    requests.push(record);
    const request = planned.find((item) => !item.received && item.url === record.url && item.method === record.method);
    if (!request) {
      const message = `Unexpected fixture request: ${record.method} ${record.url}`;
      unexpected.push(message);
      return Promise.reject(new Error(message));
    }
    request.received = record;
    // Deliberately do not settle on abort: completion identity, not cooperative
    // transport cancellation, must protect every success/error/loading state.
    return request.response;
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(async () => {
  try {
    await unmount();
    await act(async () => {
      for (const request of planned) {
        if (!request.settled) request.reply(new Response(null, { status: 204 }));
      }
    });
    expect(unexpected).toEqual([]);
    expect(planned.filter((request) => !request.received).map((request) => `${request.method} ${request.url}`)).toEqual([]);
  } finally {
    container.remove();
    vi.unstubAllGlobals();
  }
});

describe('mounted SourcesView history windows', () => {
  it('loads only requested Older/Latest windows, replaces rather than accumulates, and keeps head pointers independent', async () => {
    await readySources();
    expectRows(latestNumbers);
    expect(button('Latest').disabled).toBe(true);
    expect(requests.filter((request) => request.url.includes('/revisions?'))).toHaveLength(1);

    const older = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    expectLoading();
    expect(button('Latest').disabled).toBe(false);
    await click(button('Older'));
    await deliver(older, historyResponse(olderNumbers, '60'));
    expectRows(olderNumbers);
    expect(headPointers()).toEqual(['119', '119']);

    const terminal = plan('GET', historyUrl(sourceA.api, '60'));
    await click(button('Older'));
    await deliver(terminal, historyResponse([2, 5, 9]));
    expectRows([2, 5, 9]);
    expect(button('Older').disabled).toBe(true);
    expect(button('Latest').disabled).toBe(false);
    await click(button('Older'));

    const latest = plan('GET', historyUrl());
    await click(button('Latest'));
    expectLoading();
    await deliver(latest, historyResponse(refreshedNumbers, '101'));
    expectRows(refreshedNumbers);
    expect(headPointers()).toEqual(['119', '119']);
    expect(requests.filter((request) => request.url.includes('/revisions?')).map((request) => request.url)).toEqual([
      historyUrl(), historyUrl(sourceA.api, '100'), historyUrl(sourceA.api, '60'), historyUrl(),
    ]);
  });

  it('scopes a page error, retries exactly that bound, and does not leave stale rows or cursor actions', async () => {
    await readySources();
    const failed = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    await deliver(failed, Response.json({ detail: 'Fixture history failure.' }, { status: 503 }));
    expectRows([]);
    expect(container.querySelector('.revision-list')?.getAttribute('aria-busy')).toBe('false');
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('Fixture history failure.');
    expect(button('Older').disabled).toBe(true);
    expect(button('Latest').disabled).toBe(false);
    const retry = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Retry history'));
    expectLoading();
    await deliver(retry, historyResponse([2, 5, 9]));
    expectRows([2, 5, 9]);
    expect(container.querySelector('[role="alert"]')).toBeNull();
    expect(button('Older').disabled).toBe(true);
    expect(requests.filter((request) => request.url.includes('/revisions?'))).toHaveLength(3);
  });

  it('renders an empty terminal latest window without inventing navigation or revision actions', async () => {
    const history = await mountSources();
    await deliver(history, historyResponse([]));
    expectRows([]);
    expect(container.querySelector('.revision-list')?.textContent).toContain('No source revisions');
    expect(container.querySelector('.revision-list')?.getAttribute('aria-busy')).toBe('false');
    expect(button('Older').disabled).toBe(true);
    expect(button('Latest').disabled).toBe(true);
    expect(container.querySelector('.revision-list button')).toBeNull();
    expect(requests.filter((request) => request.url.includes('/revisions?'))).toHaveLength(1);
  });

  it('never commits Alpha rows/actions under Beta and posts the exact visible Beta revision target', async () => {
    await readySources();
    const staleRowAction = rowButton(100);
    const beta = plan('GET', historyUrl(sourceB.api));
    await act(async () => {
      sourceButton(sourceB).click();
      // A queued old-row click cannot repurpose its revision for the new source.
      // No disabled attribute or React handler is bypassed.
      staleRowAction.click();
    });
    expectLoading();
    const betaCommits = commits.filter((commit) => commit.source === sourceB.displayName);
    expect(betaCommits.length).toBeGreaterThan(0);
    for (const commit of betaCommits) {
      expect(commit.rows).toEqual([]);
      expect(commit.draftRows).toEqual([]);
    }
    expect(requests.filter((request) => request.method === 'POST')).toEqual([]);
    await deliver(beta, historyResponse(betaNumbers, '200', 219));
    expectRows(betaNumbers);
    expect(headPointers()).toEqual(['219', '219']);

    const draft = plan('POST', `/api/backend/sources/${encodeURIComponent(sourceB.api)}/editor-draft`);
    await act(async () => { rowButton(200).click(); rowButton(200).click(); });
    expect(draft.received?.init?.body).toBe(JSON.stringify({ fromRevision: 200 }));
    expect(requests.filter((request) => request.method === 'POST')).toHaveLength(1);
    expect(sourceButton(sourceA).disabled).toBe(true);
    expect(button('Older').disabled).toBe(true);
    await deliver(draft, Response.json(draftFor(sourceB, 200), { headers: { ETag: '"draft-4"' } }));
    expect(container.querySelector('.source-editor h2')?.textContent).toBe(sourceB.displayName);
    expect(button('Older').disabled).toBe(true);
    await click(sourceButton(sourceA));
    await click(button('Older'));
    expect(requests.filter((request) => request.url.includes('/revisions?'))).toHaveLength(2);
  });

  it.each(['success', 'error'] as const)('ignores delayed %s across A→B→A, including while the winning request is loading', async (outcome) => {
    const initialA = await mountSources();
    const beta = plan('GET', historyUrl(sourceB.api));
    await click(sourceButton(sourceB));
    const latestA = plan('GET', historyUrl());
    await click(sourceButton(sourceA));
    expect(initialA.received?.init?.signal?.aborted).toBe(true);
    expect(beta.received?.init?.signal?.aborted).toBe(true);
    await deliver(beta, outcome === 'success' ? historyResponse(betaNumbers, '200', 219)
      : Response.json({ detail: 'Stale Beta failure.' }, { status: 500 }));
    expectLoading();
    await deliver(latestA, historyResponse(latestNumbers, '100'));
    expectRows(latestNumbers);
    await deliver(initialA, outcome === 'success' ? historyResponse([2, 5, 9])
      : Response.json({ detail: 'Stale Alpha failure.' }, { status: 500 }));
    expectRows(latestNumbers);
    expect(button('Older').disabled).toBe(false);
    expect(container.querySelector('.notice-error')).toBeNull();
    expect(container.querySelector('.revision-list')?.getAttribute('aria-busy')).toBe('false');
  });

  it.each(['success', 'error'] as const)('lets Latest supersede an outstanding Older request without its late %s changing the window', async (outcome) => {
    await readySources();
    const older = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    const latest = plan('GET', historyUrl());
    await click(button('Latest'));
    expectLoading();
    expect(older.received?.init?.signal?.aborted).toBe(true);
    await deliver(older, outcome === 'success' ? historyResponse(olderNumbers, '60')
      : Response.json({ detail: 'Stale Older failure.' }, { status: 500 }));
    expectLoading();
    await deliver(latest, historyResponse(refreshedNumbers, '101'));
    expectRows(refreshedNumbers);
    expect(button('Latest').disabled).toBe(true);
    expect(requests.filter((request) => request.url.includes('/revisions?'))).toHaveLength(3);
  });

  it.each(['finalize', 'publish', 'operational mode'] as const)('resets history immediately after real %s success, before head refresh completes', async (action) => {
    await readySources();
    const older = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    let completed: PlannedRequest;
    const editorPath = `/api/backend/sources/${encodeURIComponent(sourceA.api)}/editor-draft`;
    if (action === 'operational mode') {
      await click(button('Disabled'));
      completed = plan('PUT', `/api/backend/sources/${encodeURIComponent(sourceA.api)}/operational-mode`);
    } else {
      const opened = plan('POST', editorPath);
      await click(button('Open editor'));
      expect(opened.received?.init?.body).toBe('{}');
      await deliver(opened, Response.json(draftFor(), { headers: { ETag: '"draft-4"' } }));
      const saved = plan('PUT', editorPath);
      if (action === 'finalize') completed = plan('POST', `${editorPath}/finalize`);
      else completed = plan('POST', `${editorPath}/publish`);
      const trigger = button(action === 'finalize' ? 'Create revision' : 'Quick publish');
      await act(async () => { trigger.click(); trigger.click(); });
      expect(new Headers(saved.received?.init?.headers).get('If-Match')).toBe('"draft-4"');
      expect(requests.filter((request) => request.method === 'PUT' && request.url === editorPath)).toHaveLength(1);
      await deliver(saved, Response.json(draftFor(sourceA, 119, 5), { headers: { ETag: '"draft-5"' } }));
    }
    if (action !== 'finalize') {
      expect(container.querySelector('[role="dialog"]')).not.toBeNull();
      expect(completed.received).toBeNull();
      await enterPassword();
      const proof = plan('POST', '/api/auth/step-up');
      await click(button('Verify and continue'));
      expect(proof.received?.init?.body).toBe(JSON.stringify({ password: 'fixture-only-password' }));
      await deliver(proof, new Response(null, { status: 204 }));
    }
    expect(completed.received).not.toBeNull();
    if (action === 'operational mode') expect(completed.received?.init?.body).toBe(JSON.stringify({ mode: 'disabled' }));
    else expect(new Headers(completed.received?.init?.headers).get('If-Match')).toBe('"draft-5"');
    expect(sourceButton(sourceB).disabled).toBe(true);
    expect(button('Older').disabled).toBe(true);
    expect(button('Latest').disabled).toBe(true);
    await click(sourceButton(sourceB));
    await click(button('Latest'));

    const heads = plan('GET', '/api/backend/sources');
    const vocabulary = plan('GET', '/api/backend/source-studio/capabilities');
    const latest = plan('GET', historyUrl());
    const finalized = draftFor(sourceA, 120, 6);
    const result = action === 'finalize' ? { draft: finalized }
      : action === 'publish' ? { draft: finalized, publication: { documentRevision: 99 } }
        : { api: sourceA.api, mode: 'disabled', sourceRevisionNumber: 120, documentRevision: 99, checksum: 'fixture-checksum', noOp: false };
    await deliver(completed, Response.json(result, { headers: { ETag: '"draft-6"' } }));
    expect(heads.received).not.toBeNull();
    expect(latest.received).not.toBeNull();
    expect(older.received?.init?.signal?.aborted).toBe(true);
    await deliver(older, historyResponse(olderNumbers, '60'));
    expectLoading();
    const published = action === 'finalize' ? 119 : 120;
    await deliver(latest, historyResponse(refreshedNumbers, '101', published));
    expectRows(refreshedNumbers);
    expect(headPointers()).toEqual(['119', '119']);
    await deliver(heads, Response.json([{
      ...sourceA, latestRevisionNumber: 120, currentPublishedRevisionNumber: published,
      operationalMode: action === 'operational mode' ? 'disabled' : sourceA.operationalMode,
    }, sourceB]));
    await deliver(vocabulary, Response.json(capabilities));
    if (action !== 'operational mode') await click(button('Close editor'));
    expect(headPointers()).toEqual([String(published), '120']);
    expect(button('Latest').disabled).toBe(true);
    expect(button('Older').disabled).toBe(false);
    expect(requests.filter((request) => request.url.includes('/revisions?')).map((request) => request.url)).toEqual([
      historyUrl(), historyUrl(sourceA.api, '100'), historyUrl(),
    ]);
  });

  it('locks history/source controls for an idle confirmation and releases them on cancel without fetching', async () => {
    await readySources();
    const older = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    await deliver(older, historyResponse(olderNumbers, '60'));
    await click(button('Disabled'));
    expect(button('Older').disabled).toBe(true);
    expect(button('Latest').disabled).toBe(true);
    expect(sourceButton(sourceB).disabled).toBe(true);
    const before = requests.length;
    await click(button('Older'));
    await click(button('Latest'));
    await click(sourceButton(sourceB));
    const dialog = container.querySelector('[role="dialog"] form');
    if (!dialog) throw new Error('Missing confirmation form.');
    await click(button('Cancel', dialog));
    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(button('Older').disabled).toBe(false);
    expect(button('Latest').disabled).toBe(false);
    expect(sourceButton(sourceB).disabled).toBe(false);
    expect(requests).toHaveLength(before);
  });

  it('revokes pending history and authoring continuations at real unmount without a follow-up refresh', async () => {
    await readySources();
    const older = plan('GET', historyUrl(sourceA.api, '100'));
    await click(button('Older'));
    const editorPath = `/api/backend/sources/${encodeURIComponent(sourceA.api)}/editor-draft`;
    const opened = plan('POST', editorPath);
    await click(button('Open editor'));
    await deliver(opened, Response.json(draftFor(), { headers: { ETag: '"draft-4"' } }));
    const saved = plan('PUT', editorPath);
    const finalized = plan('POST', `${editorPath}/finalize`);
    await click(button('Create revision'));
    await deliver(saved, Response.json(draftFor(sourceA, 119, 5), { headers: { ETag: '"draft-5"' } }));
    await unmount();
    const before = requests.length;
    expect(older.received?.init?.signal?.aborted).toBe(true);
    await deliver(finalized, Response.json({ draft: draftFor(sourceA, 120, 6) }, { headers: { ETag: '"draft-6"' } }));
    await act(async () => { older.fail(new Error('Late unmounted history failure.')); });
    expect(container.childElementCount).toBe(0);
    expect(requests).toHaveLength(before);
  });
});
