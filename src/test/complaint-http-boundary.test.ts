// @vitest-environment node
import { spawn, type ChildProcess } from 'node:child_process';
import { mkdtemp, readFile, readdir, realpath, rm } from 'node:fs/promises';
import { createServer, request, type ClientRequest, type IncomingHttpHeaders, type IncomingMessage, type Server, type ServerResponse } from 'node:http';
import type { Socket } from 'node:net';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { decodeComplaintAdminStats } from '@/lib/complaint-stats-wire';
import { complaintId, complaintScope } from '@/test/complaint-mutation-fixture';
import { searchContent, searchPage, searchVersion } from '@/test/complaint-search-fixture';
import { statsDocument, statsTotal } from '@/test/complaint-stats-fixture';
import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';

// Opt-in only: build THIS checkout first, then select only this file with
// KIRA_ADMIN_HTTP_BOUNDARY=loopback-only on Linux/Node24. No build/install happens here.
// Actual standalone Next + native Fetch + Node HTTP sockets, not direct route calls or a browser.
// This qualifies acquisition/cancellation, not container/ingress memory, browser cookies,
// backend authorization/activation, or custody after Next has buffered downstream output.
const qualify = process.env.KIRA_ADMIN_HTTP_BOUNDARY === 'loopback-only' ? describe.sequential : describe.skip;
const maximum = 2_097_152;
const operationMs = 10_000;
type ReadKind = 'search' | 'stats' | 'detail';
const mixedReads: ReadKind[] = ['stats', 'search', 'detail', 'stats', 'search', 'detail', 'stats', 'search'];

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

async function bounded<T>(pending: Promise<T>, milliseconds: number, label: string): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([pending, new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new Error(label)), milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}

type Reply = { status: number; headers: IncomingHttpHeaders; body: Buffer };
type Client = { request: ClientRequest; result: Promise<Reply>; closed: Promise<void>; sawHeaders: boolean };
type Exchange = { response: ServerResponse; closed: Promise<void>; socketClosed: Promise<void>; isClosed: boolean };
type Planned = { kind: ReadKind; arrived: ReturnType<typeof deferred<Exchange>> };
type Held = { client: Client; upstream: Exchange; body: Buffer; prefixLength: number };

qualify('standalone Node24/Next16 complaint HTTP acquisition boundary (loopback synthetic only)', () => {
  const repository = fileURLToPath(new URL('../../', import.meta.url));
  const standalone = join(repository, '.next', 'standalone');
  const clients = new Set<Client>(), exchanges = new Set<Exchange>(), sockets = new Set<Socket>();
  const plans: Planned[] = [], fixtureErrors: string[] = [];
  let upstream: Server | undefined, reservation: Server | undefined, child: ChildProcess | undefined, home: string | undefined;
  let backendPort = 0, adminPort = 0, dispatched = 0, stopping = false, childExited = false;
  const childExit = deferred<void>();
  let session: ReturnType<typeof createSessionFixture>;

  function http(path: string, method = 'GET', headers: Record<string, string> = {}, body?: Buffer, timeoutMs = operationMs): Client {
    const closed = deferred<void>();
    let incoming: IncomingMessage | undefined, settled = false;
    let resolve!: (reply: Reply) => void, reject!: (error: Error) => void;
    const result = new Promise<Reply>((done, fail) => { resolve = done; reject = fail; });
    // Deliberately disconnected clients need not await a successful reply; never leave a rejection unowned.
    void result.catch(() => {});
    const fail = () => {
      if (!settled) { settled = true; clearTimeout(timer); reject(new Error('Loopback downstream HTTP exchange failed or exceeded its watchdog.')); }
      incoming?.destroy(); outgoing.destroy();
    };
    const outgoing = request({ hostname: '127.0.0.1', port: adminPort, path, method, agent: false,
      headers: { ...headers, Connection: 'close', 'Accept-Encoding': 'identity', ...(body ? { 'Content-Length': String(body.length) } : {}) },
    }, (response) => {
      incoming = response; client.sawHeaders = true;
      const chunks: Buffer[] = [];
      let size = 0;
      response.on('data', (chunk: Buffer) => {
        if (settled) return;
        if (chunk.length > maximum + 1 - size) { fail(); return; }
        size += chunk.length; chunks.push(chunk);
      });
      response.on('error', fail);
      response.on('aborted', fail);
      response.on('end', () => {
        if (settled) return;
        if (!response.complete || response.statusCode === undefined) { fail(); return; }
        settled = true; clearTimeout(timer);
        resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks, size) });
      });
    });
    const client: Client = { request: outgoing, result, closed: closed.promise, sawHeaders: false };
    clients.add(client);
    const timer = setTimeout(fail, timeoutMs);
    outgoing.on('error', fail);
    outgoing.on('close', () => { closed.resolve(); if (!settled) fail(); });
    outgoing.end(body);
    return client;
  }

  function read(kind: ReadKind, timeoutMs = operationMs) {
    const headers = signedRequestHeaders(session, [], { Origin: `http://127.0.0.1:${adminPort}`, 'X-Kira-Complaint-Contract': '1' });
    return http(`/api/backend/complaints/${kind === 'detail' ? complaintId : kind}${kind === 'search' ? '' : `?dataScopeId=${complaintScope}`}`,
      kind === 'search' ? 'POST' : 'GET', Object.fromEntries(headers),
      kind === 'search' ? Buffer.from(`{"dataScopeId":"${complaintScope}"}`) : undefined, timeoutMs);
  }

  function fixtureBody(kind: ReadKind) {
    return Buffer.from(kind === 'stats' ? statsDocument() : kind === 'search' ? searchPage() : searchContent());
  }

  function paddedStats(size: number) {
    const body = Buffer.alloc(size, ' ');
    Buffer.from(statsDocument()).copy(body);
    return body; // JSON whitespace, not invented fields or invalid finite-count buckets.
  }

  async function write(exchange: Exchange, bytes: Buffer, end = false) {
    if (exchange.response.destroyed) throw new Error('Synthetic upstream closed before its planned write.');
    await bounded(new Promise<void>((resolve, reject) => {
      const done = (error?: Error | null) => error ? reject(new Error('Synthetic upstream write failed.')) : resolve();
      if (end) exchange.response.end(bytes, done);
      else exchange.response.write(bytes, done);
    }), operationMs, 'Synthetic upstream write watchdog expired.');
  }

  async function hold(kind: ReadKind, body = fixtureBody(kind), prefixLength = 1, timeoutMs = operationMs): Promise<Held> {
    const arrived = deferred<Exchange>();
    plans.push({ kind, arrived });
    const client = read(kind, timeoutMs);
    const remote = await bounded(Promise.race([arrived.promise, client.result.then(() => {
      throw new Error('Downstream completed before the planned synthetic upstream dispatch.');
    })]), operationMs, 'Expected synthetic upstream dispatch was not observed.');
    await write(remote, body.subarray(0, prefixLength));
    return { client, upstream: remote, body, prefixLength };
  }

  async function complete(held: Held) {
    await write(held.upstream, held.body.subarray(held.prefixLength), true);
    const reply = await held.client.result;
    expect(reply.status).toBe(200);
    expect(reply.body.equals(held.body)).toBe(true); // Never dump an authenticated body in an assertion diff.
    boundaryHeaders(reply);
    return reply;
  }

  function boundaryHeaders(reply: Reply) {
    expect(reply.headers['cache-control'] === 'no-store, no-transform').toBe(true);
    for (const name of ['set-cookie', 'www-authenticate', 'authorization', 'x-kira-admin-step-up-consumed']) {
      expect(reply.headers[name] === undefined).toBe(true);
    }
  }

  function problem(reply: Reply, status: number) {
    expect(reply.status).toBe(status);
    expect(reply.body.length).toBeLessThan(32_768);
    expect(reply.body.equals(Buffer.from('{"detail":"Complaint statistics could not be loaded."}'))).toBe(true);
    boundaryHeaders(reply);
  }

  async function listen(server: Server): Promise<number> {
    return bounded(new Promise<number>((resolve, reject) => {
      server.once('error', () => reject(new Error('Loopback fixture listener failed.')));
      server.listen(0, '127.0.0.1', () => {
        const address = server.address();
        if (!address || typeof address === 'string') reject(new Error('Loopback fixture listener has no TCP port.'));
        else resolve(address.port);
      });
    }), operationMs, 'Loopback fixture listener watchdog expired.');
  }

  async function cleanCase() {
    const errors: Error[] = [];
    for (const client of clients) client.request.destroy();
    try { await bounded(Promise.all([...clients].map((client) => client.closed)), 5_000, 'Downstream cleanup did not close owned requests.'); }
    catch { errors.push(new Error('Downstream cleanup did not close owned requests.')); }
    try { await bounded(Promise.all([...exchanges].map((exchange) => exchange.closed)), 5_000, 'Upstream cleanup did not observe closure.'); }
    catch {
      // Disposal is not evidence of the product aborting: forced fixture closure makes this run fail.
      errors.push(new Error('Forced synthetic upstream disposal was required.'));
      for (const exchange of exchanges) if (!exchange.isClosed) exchange.response.destroy();
      try { await bounded(Promise.all([...exchanges].map((exchange) => exchange.closed)), 1_000, 'Forced upstream disposal did not close.'); }
      catch { errors.push(new Error('Forced synthetic upstream disposal did not finish.')); }
    }
    for (const message of fixtureErrors.splice(0)) errors.push(new Error(message));
    clients.clear(); exchanges.clear(); plans.length = 0;
    if (errors.length) throw new AggregateError(errors, 'HTTP case cleanup/fixture qualification failed.');
  }

  beforeAll(async () => {
    if (process.platform !== 'linux' || process.versions.node.split('.')[0] !== '24' || vi.isFakeTimers()) {
      throw new Error('This opt-in qualification requires Linux, actual Node24 and real timers.');
    }
    for (const directory of [repository, standalone]) {
      // Metadata only. Next must not load local secrets, including a copied standalone .env file.
      if ((await readdir(directory)).some((name) => (name === '.env' || name.startsWith('.env.')) && name !== '.env.example')) {
        throw new Error('Refusing a checkout/build containing runtime .env files.');
      }
    }
    const entry = join(standalone, 'server.js');
    if (await realpath(entry) !== join(await realpath(repository), '.next', 'standalone', 'server.js')) {
      throw new Error('Standalone entry must belong to this checkout, not an external build.');
    }
    const builtNext: { version?: unknown } = JSON.parse(await readFile(join(standalone, 'node_modules', 'next', 'package.json'), 'utf8'));
    if (builtNext.version !== '16.3.4') throw new Error('Expected the locked Next16.3.4 standalone build.');
    home = await mkdtemp(join(tmpdir(), 'kira-admin-http-boundary-'));
    vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
    session = createSessionFixture();
    upstream = createServer((incoming, response) => {
      dispatched++;
      const plan = plans.shift();
      const closed = deferred<void>(), socketClosed = deferred<void>();
      const exchange: Exchange = { response, closed: closed.promise, socketClosed: socketClosed.promise, isClosed: false };
      exchanges.add(exchange);
      response.on('close', () => { exchange.isClosed = true; closed.resolve(); });
      incoming.socket.once('close', () => socketClosed.resolve());
      // Expected cancellation can emit transport errors. Assertions own the observed closure/result,
      // never an uncaught event-listener throw or a raw authenticated request/error transcript.
      incoming.on('error', () => {}); response.on('error', () => {}); incoming.resume();
      const expectedPath = plan && `/api/v1/admin/complaints/${plan.kind === 'detail' ? complaintId : plan.kind}${plan.kind === 'search' ? '' : `?dataScopeId=${complaintScope}`}`;
      if (!plan || incoming.url !== expectedPath || incoming.method !== (plan.kind === 'search' ? 'POST' : 'GET')
        || incoming.headers.authorization !== `Bearer ${session.token}` || incoming.headers['x-kira-complaint-contract'] !== '1'
        || incoming.headers['accept-encoding'] !== 'identity' || incoming.headers.cookie !== undefined) {
        fixtureErrors.push('Unexpected synthetic upstream dispatch or read-header boundary.');
        response.writeHead(500); response.end(); return;
      }
      response.writeHead(200, { 'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1',
        'Transfer-Encoding': 'chunked', 'Set-Cookie': 'fixture-only-upstream=discard; HttpOnly',
        'WWW-Authenticate': 'KiraSession realm="kira-admin-bff"', 'X-Kira-Admin-Step-Up-Consumed': 'true',
        ...(plan.kind === 'detail' ? { ETag: `"complaint-${complaintId}-v${searchVersion}"` } : {}),
      });
      response.flushHeaders();
      plan.arrived.resolve(exchange);
    });
    upstream.on('connection', (socket) => { sockets.add(socket); socket.once('close', () => sockets.delete(socket)); });
    // Explicit loopback binding for both listeners, including the disposable port reservation.
    upstream.on('error', () => fixtureErrors.push('Synthetic upstream server reported an error.'));
    backendPort = await listen(upstream);
    reservation = createServer();
    reservation.on('connection', (socket) => socket.destroy());
    adminPort = await listen(reservation);
    await bounded(new Promise<void>((resolve) => reservation!.close(() => resolve())), 3_000, 'Port reservation cleanup failed.');
    reservation = undefined; // The afterAll owner retains it if startup fails before this point.
    child = spawn(process.execPath, [entry], { cwd: standalone, detached: true, stdio: 'ignore', env: {
      NODE_ENV: 'production', HOSTNAME: '127.0.0.1', PORT: String(adminPort),
      PATH: dirname(process.execPath), HOME: home, TMPDIR: home, TZ: 'UTC', NEXT_TELEMETRY_DISABLED: '1',
      KIRA_BACKEND_URL: `http://127.0.0.1:${backendPort}`, KIRA_ADMIN_ORIGIN: `http://127.0.0.1:${adminPort}`,
      KIRA_ADMIN_SESSION_SECRET: fixtureSigningSecret, KIRA_ADMIN_TRUSTED_INGRESS: 'false',
    } });
    child.once('error', () => { childExited = true; childExit.resolve(); fixtureErrors.push('Owned Next child failed to start.'); });
    child.once('exit', () => {
      childExited = true; childExit.resolve();
      if (!stopping) fixtureErrors.push('Owned Next child exited before planned cleanup.');
    });
    // Fixed allowlisted metadata only, so an external watchdog can identify this exact owned group.
    if (child.pid) console.info(`HTTP boundary fixture: Next group ${child.pid}; Node ${process.versions.node}; Next ${builtNext.version}; loopback-only.`);
    const startupDeadline = performance.now() + 30_000;
    while (performance.now() < startupDeadline) {
      if (childExited) throw new Error('Owned Next child exited during readiness.');
      const probe = http(`/api/backend/complaints/stats?dataScopeId=${complaintScope}`, 'GET', {}, undefined, 1_000);
      const reply = await probe.result.catch(() => null);
      probe.request.destroy();
      await bounded(probe.closed, 2_000, 'Readiness probe did not close.'); clients.delete(probe);
      if (reply) {
        if (reply.status !== 401 || dispatched !== 0) throw new Error('Readiness did not return the local unauthenticated boundary.');
        return;
      }
      await delay(50);
    }
    throw new Error('Owned Next child readiness watchdog expired.');
  }, 60_000);

  // Vitest retains test errors AND hook errors. A cleanup failure must not overwrite an earlier assertion.
  afterEach(cleanCase, 15_000);
  afterAll(async () => {
    const errors: Error[] = [];
    try { await cleanCase(); } catch { errors.push(new Error('Remaining HTTP case cleanup failed.')); }
    stopping = true;
    if (child?.pid) {
      const pid = child.pid; // Only the detached process group created by this fixture.
      const alive = () => {
        try { process.kill(-pid, 0); return true; }
        catch (error) { if ((error as NodeJS.ErrnoException).code === 'ESRCH') return false; throw new Error('Cannot inspect owned Next process group.'); }
      };
      try {
        if (alive()) process.kill(-pid, 'SIGTERM');
        const deadline = performance.now() + 5_000;
        while (alive() && performance.now() < deadline) await delay(50);
        if (alive()) {
          errors.push(new Error('Owned Next process group required forced SIGKILL disposal.'));
          process.kill(-pid, 'SIGKILL');
        }
        await bounded(childExit.promise, 3_000, 'Owned Next child exit was not observed.');
        const finalDeadline = performance.now() + 3_000;
        while (alive() && performance.now() < finalDeadline) await delay(50);
        if (alive()) errors.push(new Error('Owned Next process group remains after disposal.'));
      } catch { errors.push(new Error('Owned Next process group cleanup failed.')); }
    }
    for (const server of [reservation, upstream]) if (server) {
      try {
        const closed = new Promise<void>((resolve) => server.close(() => resolve()));
        server.closeAllConnections();
        for (const socket of sockets) socket.destroy();
        await bounded(closed, 3_000, 'Synthetic upstream server cleanup did not finish.');
      } catch { errors.push(new Error('Synthetic upstream server cleanup failed.')); }
    }
    vi.unstubAllEnvs();
    if (home) try { await rm(home, { recursive: true, force: true }); } catch { errors.push(new Error('Isolated runtime home cleanup failed.')); }
    if (errors.length) throw new AggregateError(errors, 'HTTP suite cleanup failed; this is not a qualified pass.');
  }, 30_000);

  it('withholds incomplete success, then preserves every byte of a valid exact2MiB stats document and its Long', async () => {
    const expected = paddedStats(maximum);
    const held = await hold('stats', expected, maximum - 1);
    // A bounded negative-observation window AFTER the real prefix write flushes, while EOF is withheld.
    await delay(250);
    expect(held.client.sawHeaders).toBe(false);
    expect(held.upstream.response.writableEnded).toBe(false);
    const reply = await complete(held);
    expect(reply.body.length).toBe(maximum);
    expect(decodeComplaintAdminStats(complaintScope, { status: reply.status, contentType: String(reply.headers['content-type']),
      contract: String(reply.headers['x-kira-complaint-contract']), etag: reply.headers.etag ?? null, body: reply.body }).total).toBe(statsTotal);
  }, 20_000);

  it('refuses a chunked2MiB+1 stats body during acquisition, without a Content-Length shortcut or successful prefix', async () => {
    const held = await hold('stats', paddedStats(maximum + 1), maximum);
    await delay(250);
    expect(held.client.sawHeaders).toBe(false);
    expect(held.upstream.response.getHeader('content-length') === undefined).toBe(true);
    await write(held.upstream, held.body.subarray(maximum)); // Keep HTTP EOF withheld even after overflow.
    problem(await held.client.result, 502);
    await bounded(held.upstream.socketClosed, operationMs, 'Overflow did not close the original upstream transport.');
    expect(held.upstream.response.writableEnded).toBe(false);
  }, 25_000);

  it('shares eight mixed in-flight slots, rejects the ninth before dispatch and refills only after observed disconnect propagation', async () => {
    const before = dispatched, held: Held[] = [];
    for (const kind of mixedReads) held.push(await hold(kind));
    expect(dispatched - before).toBe(8);
    problem(await read('stats').result, 503);
    expect(dispatched - before).toBe(8);
    held[0].client.request.destroy();
    await bounded(held[0].client.closed, operationMs, 'Disconnected downstream did not close.');
    await bounded(held[0].upstream.socketClosed, operationMs, 'Disconnect did not close its original upstream transport.');
    expect(held[0].upstream.response.writableEnded).toBe(false);
    const replacement = await hold('stats'); // No sleep-based assumption that the slot has been refunded.
    expect(dispatched - before).toBe(9);
    expect(held.slice(1).every((entry) => !entry.client.sawHeaders && !entry.upstream.isClosed)).toBe(true);
    problem(await read('stats').result, 503);
    expect(dispatched - before).toBe(9);
    await complete(replacement);
    for (const entry of held.slice(1)) await complete(entry);
  }, 30_000);

  it('uses the unchanged real65-second deadline, aborts the incomplete upstream and restores all eight admission slots', async () => {
    const started = performance.now();
    const held = await hold('stats', fixtureBody('stats'), 1, 75_000);
    const reply = await held.client.result;
    const elapsed = performance.now() - started;
    problem(reply, 504);
    expect(elapsed).toBeGreaterThanOrEqual(65_000);
    expect(elapsed).toBeLessThan(75_000);
    await bounded(held.upstream.socketClosed, operationMs, 'Deadline did not close its original upstream transport.');
    expect(held.upstream.response.writableEnded).toBe(false);
    // One successful request alone could hide a leaked slot: refill the entire aggregate owner.
    const replacements: Held[] = [], before = dispatched;
    for (const kind of mixedReads) replacements.push(await hold(kind));
    expect(dispatched - before).toBe(8);
    for (const replacement of replacements) await complete(replacement);
  }, 90_000);
});
