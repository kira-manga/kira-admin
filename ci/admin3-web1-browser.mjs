#!/usr/bin/env node
// PRIVATE DRAFT, NOT EXECUTED. Requires primary-authorized, exact-source production builds.
// Actual Admin UI/BFF + Web missing-detail 404; only upstream services are synthetic. No builds here.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { openSync, closeSync } from 'node:fs';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';

const { values } = parseArgs({ options: { 'app-root': { type: 'string' }, 'web-root': { type: 'string' }, 'output-root': { type: 'string' } } });
for (const option of ['app-root', 'web-root', 'output-root']) assert(values[option], 'Required: --' + option);
const app = resolve(values['app-root']), web = resolve(values['web-root']), out = resolve(values['output-root']); let runtime;
assert.notEqual(app, web); assert.equal(process.versions.node.split('.')[0], '24', 'Use Node 24');
const result = { status: 'FAIL', scope: 'ADMIN3_ACTUAL_UI_BFF_AND_WEB1_RENDERED_404_SYNTHETIC_UPSTREAM', cases: [], cleanup: false };
const events = [], browserRequests = [], browserStarts = new Map(), children = [], active = new Map(), proofs = new Map(), gates = new Set();
let fatal, closing = false, socket, fixture, fault, blocked, expired = false, proofNumber = 0, networkAt = 0, pageOrigin, product = 'admin';
const email = 'admin3@example.invalid', password = 'Synthetic-admin3-only!', session = 'fixture-session-admin3';
const stamp = '2026-09-09T00:00:00Z', actor = '11111111-1111-4111-8111-111111111111';
const meta = { createdBy: actor, updatedBy: actor, createdAt: stamp, updatedAt: stamp };
const apis = ['fixture-alpha', 'fixture-beta'];
const ids = ['22222222-2222-4222-8222-222222222222', '33333333-3333-4333-8333-333333333333'];
const sourceText = (label, api = apis[0]) => JSON.stringify({ api, displayName: label, engine: 'generic', language: 'en', baseUrl: 'https://fixture.invalid', sourceRevision: 1 });
const drafts = new Map(apis.map((api, i) => [api, { ...meta, id: ids[i], basedOnRevisionNumber: 1, version: 1, content: sourceText('persisted old ' + api, api) }]));
const sets = new Map(ids.map((id, i) => [id, { ...meta, id, name: 'Fixture set ' + (i + 1), description: null, operations: [], version: 1, status: 'open', appliedDocumentRevision: null, appliedAt: null }]));
const heads = apis.map((api, position) => ({ api, displayName: api, language: 'en', engine: 'generic', status: 'active', operationalMode: 'enabled', position, baseUrl: 'https://fixture.invalid', adult: false, currentPublishedRevisionNumber: 1, latestRevisionNumber: 1, createdAt: stamp, updatedAt: stamp, publishedAt: stamp }));
const prefix = '/api/v1/admin/', draftPath = prefix + 'sources/' + apis[0] + '/editor-draft';
const setPath = prefix + 'source-changesets/' + ids[0], stepPath = prefix + 'step-up';
const key = (method, path) => method + ' ' + path, tag = (kind, value) => `"${kind}-${value.version}"`;
const mutations = start => events.slice(start).filter(e => e.method !== 'GET');
function mark() { const start = events.length; browserStarts.set(start, browserRequests.length); return start; }
const q = JSON.stringify, delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(check, label, milliseconds = 8000) {
  const deadline = Date.now() + milliseconds;
  do { if (fatal) throw fatal; if (await check()) return; await delay(40); } while (Date.now() < deadline);
  throw new Error('Timed out: ' + label);
}
function hold(method, path) {
  const gate = { key: key(method, path) };
  gate.promise = new Promise(resolve => { gate.release = () => { resolve(); gates.delete(gate); if (blocked === gate) blocked = null; }; });
  blocked = gate; gates.add(gate); return gate;
}
async function backend(req, res) {
  const path = new URL(req.url, 'http://127.0.0.1').pathname, method = req.method;
  const chunks = []; let size = 0;
  for await (const chunk of req) { size += chunk.length; assert(size < 262144, 'Fixture body limit'); chunks.push(chunk); }
  const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : null;
  const event = { method, path, ifMatch: req.headers['if-match'] ?? null, status: null };
  if (method === 'PUT') event.body = body; // Never retain login/password/bearer/proof bytes.
  events.push(event);
  const send = (status, data, etag) => { event.status = status; event.etag = etag ?? null; if (!res.destroyed) { res.writeHead(status, { 'Content-Type': 'application/json', ...(etag ? { ETag: etag } : {}) }); res.end(JSON.stringify(data)); } };
  const reject = status => send(status, { detail: `Fixture rejection ${status}` });
  const pause = blocked?.key === key(method, path) ? blocked : null;
  if (pause) await pause.promise;
  if (closing) return reject(503);
  if (method === 'GET' && path.startsWith('/api/v1/tutorial')) {
    assert(!req.headers.authorization && !req.headers.cookie && !req.headers['x-kira-admin-step-up'], 'Credentials reached public fixture');
    if (path === '/api/v1/tutorials/cold-missing') return reject(404);
    if (path === '/api/v1/tutorials' || path === '/api/v1/tutorial-categories') return send(200, []); // Empty lists also satisfy same-origin link prefetches.
    throw new Error('Unexpected public fixture route: ' + path);
  }
  if (path === '/api/v1/auth/login' && method === 'POST') return body?.email === email && body?.password === password ? send(200, { accessToken: session, expiresInSeconds: 3600, role: 'ADMIN' }) : reject(401);
  if (expired || req.headers.authorization !== 'Bearer ' + session) return reject(401);
  if (path === '/api/v1/auth/me' && method === 'GET') return send(200, { id: actor, email, role: 'ADMIN', createdAt: stamp });
  if (path === stepPath && method === 'POST') {
    if (body?.password !== password) return reject(401);
    const number = ++proofNumber, token = 'fixture-proof-' + number;
    proofs.set(token, number); event.proofNumber = number;
    return send(200, { token, expiresAt: new Date(Date.now() + 60000).toISOString(), scope: 'source-admin-mutation' });
  }
  if (method === 'GET' && path === prefix + 'sources') return send(200, heads);
  if (method === 'GET' && path === prefix + 'source-changesets') return send(200, [...sets.values()]);
  if (method === 'GET' && path === prefix + 'audit') return send(200, { items: [], total: 0 });
  if (method === 'GET' && path === prefix + 'source-studio/capabilities') return send(200, {
    sourceSchemaVersion: 1, catalogSchemaVersion: 1, canonicalization: 'kcj-1', authorableEngines: ['generic'], serverLifecycleStates: ['active'],
    transforms: [], dateStrategies: [], imageStrategies: [], paginationStrategies: [], endpointMethods: ['GET'], endpointFormats: ['html'],
    editorDraftMaxBytes: 262144, optimisticLocking: 'If-Match', publicEnginePolicy: 'fixture',
  });
  if (method === 'GET' && new RegExp('^' + prefix + 'sources/(fixture-alpha|fixture-beta)/revisions$').test(path)) return send(200, []);
  const source = path.match(/\/sources\/(fixture-alpha|fixture-beta)\/editor-draft(?:\/(validate|finalize|publish))?$/);
  const change = path.match(/\/source-changesets\/([0-9a-f-]+)(?:\/(validate|apply))?$/);
  assert(source || change, 'Unexpected fixture route: ' + key(method, path));
  const value = source ? drafts.get(source[1]) : sets.get(change[1]), action = (source ?? change)[2];
  assert(value, 'Unknown fixture target'); const kind = source ? 'draft' : 'changeset';
  if ((source && !action && method === 'POST') || (change && !action && method === 'GET')) return send(200, value, tag(kind, value));
  assert(method === 'PUT' && !action || method === 'POST' && action, 'Unsupported fixture mutation');
  if (action === 'publish' || action === 'apply') {
    const proof = req.headers['x-kira-admin-step-up']; event.proofNumber = proofs.get(proof) ?? null;
    if (!proofs.delete(proof)) return reject(403); // Consume before version/action failure, like controllers.
  } else assert(!req.headers['x-kira-admin-step-up'], 'Proof leaked onto unprotected route');
  if (event.ifMatch !== tag(kind, value) || change && value.status !== 'open') return reject(409);
  const failure = fault?.key === key(method, path) ? fault : null;
  if (failure) fault = null;
  if (failure?.status) return reject(failure.status);
  if (method === 'PUT') {
    if (source) { assert.equal(typeof body.content, 'string'); value.content = body.content; }
    else { assert(Array.isArray(body.operations)); Object.assign(value, body); }
    value.version++; return send(200, value, failure?.omitEtag ? undefined : tag(kind, value));
  }
  event.stored = source ? value.content : { name: value.name, description: value.description, operations: structuredClone(value.operations) };
  if (source) { try { JSON.parse(value.content); } catch { return reject(400); } } // Strict parsing precedes validation reports/finalization.
  if (action === 'validate') return send(200, source ? { valid: true, errors: [], warnings: [] } : { valid: true, operationCount: value.operations.length, affectedApis: apis });
  value.version++;
  if (source) { value.content = JSON.stringify(JSON.parse(value.content)); value.basedOnRevisionNumber++; return send(200, { draft: value, revision: { api: source[1], revisionNumber: value.basedOnRevisionNumber, checksum: 'f'.repeat(64) }, publication: { documentRevision: 2, checksum: 'f'.repeat(64) } }, tag(kind, value)); }
  value.status = 'applied'; value.appliedDocumentRevision = 2; value.appliedAt = stamp;
  return send(200, { documentRevision: 2, checksum: 'f'.repeat(64), affectedApis: apis });
}

function launch(name, executable, args, env) {
  const fd = openSync(join(out, name + '.log'), 'wx', 0o600);
  const child = spawn(executable, args, { detached: true, env, stdio: ['ignore', fd, fd] }); closeSync(fd);
  const owned = { child, name, joined: false }; children.push(owned);
  child.on('error', error => { fatal = error; });
  child.on('close', (code, signal) => { owned.joined = true; if (!closing) fatal = new Error(`${name} exited early: ${code ?? signal}`); });
  return child;
}
function groupAlive(pid) { try { process.kill(-pid, 0); return true; } catch (error) { if (error.code === 'ESRCH') return false; throw error; } }
async function stopOwned(owned) {
  if (!owned.child.pid) return owned.joined;
  for (const signal of ['SIGTERM', 'SIGKILL']) {
    if (groupAlive(owned.child.pid)) process.kill(-owned.child.pid, signal);
    const deadline = Date.now() + 5000;
    while (Date.now() < deadline) { if (owned.joined && !groupAlive(owned.child.pid)) return true; await delay(50); }
  }
  return false; // Never delete runtime/profile beneath an unproved live owned group.
}
let serial = 0; const calls = new Map();
function cdp(method, params = {}) {
  return new Promise((resolve, reject) => {
    if (socket?.readyState !== WebSocket.OPEN) return reject(new Error('CDP socket not open'));
    const id = ++serial, timer = setTimeout(() => { calls.delete(id); reject(new Error('CDP timeout: ' + method)); }, 8000);
    calls.set(id, { resolve, reject, timer }); socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const reply = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true, userGesture: true });
  assert(!reply.exceptionDetails, reply.exceptionDetails?.text); return reply.result.value;
}
const uiWait = expression => until(() => evaluate(expression), expression);
async function settle() {
  await until(() => active.size === 0 && Date.now() - networkAt >= 200, 'browser API quiet');
  await evaluate('new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))');
  await until(() => active.size === 0 && Date.now() - networkAt >= 200, 'browser API quiet after rendering');
}
function button(name, scope = '') { return `[...document.querySelectorAll(${q((scope ? scope + ' ' : '') + 'button')})].find(e => (e.querySelector('strong')?.textContent ?? e.textContent).trim() === ${q(name)} || e.getAttribute('aria-label') === ${q(name)})`; }
async function click(name, scope) { await evaluate(`(() => { const e = ${button(name, scope)}; if (!e || e.matches(':disabled')) throw Error('Missing/disabled button'); e.click(); })()`); }
async function input(selector, value) {
  await evaluate(`(() => { const e = document.querySelector(${q(selector)}); if (!e || e.matches(':disabled')) throw Error('Missing/disabled input'); Object.getOwnPropertyDescriptor(e instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value').set.call(e, ${q(value)}); e.dispatchEvent(new Event('input', {bubbles:true})); })()`);
}
async function locks(selector) { assert(await evaluate(`(() => { const es = [...document.querySelectorAll(${q(selector)})]; return es.length > 0 && es.every(e => e.matches(':disabled')); })()`), 'Controls not locked: ' + selector); }
const dialog = '[aria-label="Confirm protected action"]';
const sourceLocks = '.source-editor input,.source-editor textarea,.source-editor select,.source-editor button,.source-studio .source-row,.source-studio .source-search input,.source-studio .mode-switch button,.source-studio .revision-heading button,.source-studio .view-heading button';
const setLocks = '.changeset-editor input,.changeset-editor textarea,.changeset-editor button,.manager-list .source-row,.view-heading button';
async function submit(secret = password, twice = false) {
  await input(dialog + ' input[type=password]', secret);
  await evaluate(`document.querySelector(${q(dialog + ' form')}).requestSubmit();${twice ? `document.querySelector(${q(dialog + ' form')}).requestSubmit();` : ''}`);
}
// Real connected, painted, hit-testable DOM in its actual foreground container; never body/stream text.
const visible = `(e => { if (!e?.isConnected || e.closest('[inert]') || !e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true})) return false; const r=e.getBoundingClientRect(); return r.width>0 && r.height>0 && e.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)); })`;
async function notice(text, selector) {
  assert(selector, 'A foreground notice scope is required');
  await uiWait(`(() => { const e=document.querySelector(${q(selector)}); if (!e?.textContent.includes(${q(text)})) return false; e.scrollIntoView({block:'center'}); return ${visible}(e); })()`); await settle();
}
async function screenshot(name) { const shot = await cdp('Page.captureScreenshot'); await writeFile(join(out, name + '.png'), Buffer.from(shot.data, 'base64'), { flag: 'wx' }); }
async function retained(selector, value, etag, root) {
  assert.equal(await evaluate(`document.querySelector(${q(selector)}).value`), value);
  assert(await evaluate(`document.querySelector(${q(root)}).textContent.includes(${q(etag)})`), 'Saved ETag not adopted');
}
async function noConfirmation(start, expected = 1) {
  await settle(); assert.equal(mutations(start).length, expected);
  assert(!browserRequests.slice(browserStarts.get(start)).some(e => e.path === '/api/auth/step-up'), 'Unexpected browser step-up request');
  assert.equal(await evaluate(`!!document.querySelector(${q(dialog)})`), false);
}
function cycle(start, path, action, body, original) {
  const rows = mutations(start); assert.deepEqual(rows.map(e => key(e.method, e.path)), [key('PUT', path), key('POST', path + '/' + action)]);
  assert.equal(rows[0].ifMatch, original); assert.deepEqual(rows[0].body, body); assert.equal(rows[0].status, 200);
  assert(rows[0].etag && rows[0].etag !== original); assert.equal(rows[1].ifMatch, rows[0].etag);
  assert.deepEqual(rows[1].stored, path === draftPath ? body.content : body); return rows;
}
async function scenario(name, run) {
  const row = { name, status: 'RUNNING', eventStart: events.length }; result.cases.push(row);
  try { await run(); await settle(); row.status = 'PASS'; } catch (error) { row.status = 'FAIL'; throw error; }
  finally { row.eventEnd = events.length; }
}

async function smoke() {
  await scenario('login rejection then real BFF session; HttpOnly credentials', async () => {
    await uiWait('!!document.querySelector(".login-form")'); await input('input[type=email]', email);
    await input('.login-form input[type=password]', 'wrong'); await click('Open studio'); await notice('Fixture rejection 401', '.login-form .form-error');
    await input('.login-form input[type=password]', password); await click('Open studio'); await uiWait('!!document.querySelector(".admin-shell")');
    assert(await evaluate('!document.cookie.includes("kira_admin_session") && !document.cookie.includes("kira_admin_step_up") && localStorage.length === 0 && sessionStorage.length === 0'));
  });
  await click('Sources', '.sidebar nav'); await uiWait('!!document.querySelector(".source-studio")');
  await scenario('idle operational-mode confirmation locks selection/open and cancels without mutation', async () => {
    const start = mark(); await click('Under maintenance', '.mode-switch');
    await notice('Confirm setting fixture-alpha to under maintenance', dialog + ' h3');
    await locks('.source-studio .source-row,.source-studio .mode-switch button,.source-studio .revision-heading button,.source-studio .view-heading button');
    await evaluate(`document.querySelectorAll('.source-row')[1].click(); ${button('Edit selected source')}.click()`);
    assert.equal(await evaluate('document.querySelector(".source-row.selected strong").textContent'), apis[0]);
    assert.equal(await evaluate('!!document.querySelector(".source-editor")'), false);
    await click('Cancel', dialog + ' form'); await noConfirmation(start, 0);
  });
  await click('Edit selected source'); await uiWait('!!document.querySelector(".source-code")'); await settle();
  await scenario('source visible validate, save locks, new If-Match', async () => {
    const text = sourceText('visible validate'), original = tag('draft', drafts.get(apis[0])), start = mark();
    await input('.source-code', text); const gate = hold('PUT', draftPath); await click('Validate', '.source-editor');
    await until(() => mutations(start).length === 1, 'source save reached fixture'); await locks(sourceLocks);
    await evaluate('document.querySelector(".editor-close").click(); document.querySelectorAll(".source-row")[1].click()');
    assert(await evaluate('!!document.querySelector(".source-code")')); gate.release(); await notice('Validation passed', '.source-editor .notice-success');
    assert.equal(cycle(start, draftPath, 'validate', { content: text }, original)[1].status, 200);
  });
  await scenario('source finalize; malformed source save succeeds then strict finalize/validate400 retain text and ETag', async () => {
    for (const text of [sourceText('visible finalize'), '{ malformed visible source']) {
      const start = mark(), original = tag('draft', drafts.get(apis[0])); await input('.source-code', text); await click('Create revision', '.source-editor');
      await notice(text.startsWith('{ malformed') ? 'Fixture rejection 400' : 'Immutable revision created', '.source-editor .notice-' + (text.startsWith('{ malformed') ? 'error' : 'success'));
      const rows = cycle(start, draftPath, 'finalize', { content: text }, original);
      assert.equal(rows[1].status, text.startsWith('{ malformed') ? 400 : 200);
      if (rows[1].status === 400) await retained('.source-code', text, rows[0].etag, '.source-editor');
    }
    const start = mark(), original = tag('draft', drafts.get(apis[0])); await click('Validate', '.source-editor');
    await notice('Fixture rejection 400', '.source-editor .notice-error');
    const rows = cycle(start, draftPath, 'validate', { content: '{ malformed visible source' }, original);
    assert.equal(rows[1].status, 400);
    await retained('.source-code', '{ malformed visible source', rows[0].etag, '.source-editor');
  });
  await scenario('stale and missing-ETag save block dialog/auth/action', async () => {
    await input('.source-code', sourceText('visible publish'));
    for (const failure of [{ status: 409 }, { omitEtag: true }]) {
      const start = mark(); fault = { key: key('PUT', draftPath), ...failure }; await click('Quick publish', '.source-editor');
      await notice(failure.status ? 'Fixture rejection 409' : 'ETag', '.source-editor .notice-error'); await noConfirmation(start);
      if (failure.status) await screenshot('source-save-error');
      assert.equal(mutations(start)[0].path, draftPath); assert.equal(mutations(start)[0].method, 'PUT');
      assert.equal(await evaluate('document.querySelector(".source-code").value'), sourceText('visible publish'));
    }
    await click('Close editor'); await click('Edit selected source'); await uiWait('!!document.querySelector(".source-code")');
  });
  await scenario('publish saves before confirmation; cancel keeps saved snapshot', async () => {
    const text = sourceText('cancel keeps save'), start = mark(); await input('.source-code', text); await click('Quick publish', '.source-editor');
    await uiWait(`!!document.querySelector(${q(dialog)})`); await locks(sourceLocks); assert.equal(mutations(start).length, 1);
    await click('Cancel', dialog + ' form'); await noConfirmation(start); await retained('.source-code', text, mutations(start)[0].etag, '.source-editor');
  });
  await scenario('auth/action locks; consumed proof failure then fresh retry without hidden save', async () => {
    const start = mark(), text = sourceText('protected retry'); await input('.source-code', text); await click('Quick publish', '.source-editor');
    await uiWait(`!!document.querySelector(${q(dialog)})`); const auth = hold('POST', stepPath); await submit(password, true);
    await until(() => mutations(start).length === 2, 'held auth'); await locks(dialog + ' input,' + dialog + ' button');
    await evaluate(`document.querySelector(${q(dialog + ' .modal-scrim')}).click(); ${button('Cancel', dialog + ' form')}.click()`);
    assert(await evaluate(`!!document.querySelector(${q(dialog)})`)); assert.equal(mutations(start).length, 2);
    const action = hold('POST', draftPath + '/publish'); fault = { key: action.key, status: 422 }; auth.release(); // Forced protected-action failure, not malformed JSON status.
    await until(() => mutations(start).length === 3, 'held protected action'); await locks(dialog + ' input,' + dialog + ' button'); await locks(sourceLocks);
    // document.cookie at '/' cannot prove HttpOnly for this narrower path. Drop values before assertions/artifacts.
    const proofMetadata = (await cdp('Network.getCookies', { urls: [pageOrigin + '/api/backend/sources/' + apis[0] + '/editor-draft/publish'] })).cookies
      .map(({ name, httpOnly, path, secure }) => ({ name, httpOnly, path, secure })).filter(cookie => cookie.name === 'kira_admin_step_up');
    assert.deepEqual(proofMetadata, [{ name: 'kira_admin_step_up', httpOnly: true, path: '/api/backend', secure: true }]); result.stepUpCookieMetadata = proofMetadata;
    assert(await evaluate('!document.cookie.includes("kira_admin_step_up") && localStorage.length === 0 && sessionStorage.length === 0'));
    action.release(); await notice('Fixture rejection 422', dialog + ' .form-error'); await retained('.source-code', text, mutations(start)[0].etag, '.source-editor'); await locks(sourceLocks);
    assert.equal(await evaluate(`document.querySelector(${q(dialog + ' input')}).value`), ''); await screenshot('source-protected-error'); await submit(); await notice('Published atomically', '.source-editor .notice-success');
    const rows = mutations(start); assert.deepEqual(rows.map(e => key(e.method, e.path)), [key('PUT', draftPath), key('POST', stepPath), key('POST', draftPath + '/publish'), key('POST', stepPath), key('POST', draftPath + '/publish')]);
    assert.equal(rows[2].ifMatch, rows[0].etag); assert.equal(rows[4].ifMatch, rows[0].etag); assert.notEqual(rows[2].proofNumber, rows[4].proofNumber); assert.equal(rows[4].status, 200);
  });
  await scenario('same-document lifecycle injection: late auth after view unmount never posts protected action', async () => {
    await click('Quick publish', '.source-editor'); await uiWait(`!!document.querySelector(${q(dialog)})`);
    const start = mark(), auth = hold('POST', stepPath); await submit(); await until(() => mutations(start).length === 1, 'auth before unmount');
    const identity = await evaluate('({href:location.href,timeOrigin:performance.timeOrigin})');
    // Deliberate lifecycle injection through the real AdminApp navigation handler, not a pointer click through the modal or a reload.
    await click('Changesets', '.sidebar nav'); await uiWait(`!document.querySelector(${q(dialog)}) && !document.querySelector('.source-editor') && !!document.querySelector('.changeset-editor')`);
    assert.deepEqual(await evaluate('({href:location.href,timeOrigin:performance.timeOrigin})'), identity);
    auth.release(); await until(() => mutations(start)[0].status === 200 && browserRequests.slice(browserStarts.get(start)).some(e => e.path === '/api/auth/step-up' && e.status === 200 && e.completion === 'finished'), 'late verification completed successfully through BFF');
    await settle(); assert.equal(mutations(start).length, 1);
    assert(!browserRequests.slice(browserStarts.get(start)).some(e => e.path.endsWith('/publish') || e.path.endsWith('/apply')));
  });
  await scenario('changeset selection is single-flight and locks replacement/create', async () => {
    const start = mark(), gate = hold('GET', setPath); await click('Fixture set 1', '.manager-list');
    await until(() => events.slice(start).some(e => e.path === setPath), 'held selection'); await locks(setLocks);
    await evaluate('document.querySelectorAll(".manager-list .source-row")[1].click()'); gate.release(); await uiWait('!!document.querySelector(".changeset-code")');
    assert.equal(events.slice(start).filter(e => e.path === prefix + 'source-changesets/' + ids[1]).length, 0);
  });
  await scenario('malformed/non-array changeset JSON blocks before any save', async () => {
    for (const text of ['{ bad', '{}']) {
      const start = mark(); await input('.changeset-code', text); await click('Apply atomically');
      await notice(text === '{}' ? 'JSON array' : 'JSON', '.workspace-content .view-stack > .notice-error'); await noConfirmation(start, 0);
      assert.equal(await evaluate('document.querySelector(".changeset-code").value'), text);
    }
  });
  await scenario('visible changeset validate saves all fields and uses new ETag', async () => {
    const body = { name: 'Visible validated set', description: 'Visible description', operations: [{ type: 'disable', api: apis[0] }] };
    await input('.changeset-form input', body.name); await input('.changeset-form .field:nth-child(2) input', body.description); await input('.changeset-code', q(body.operations));
    const start = mark(), original = tag('changeset', sets.get(ids[0])), gate = hold('PUT', setPath); await click('Validate', '.changeset-editor');
    await until(() => mutations(start).length === 1, 'held changeset save'); await locks(setLocks); gate.release(); await notice('Validation passed for', '.workspace-content .view-stack > .notice-success'); assert.equal(cycle(start, setPath, 'validate', body, original)[1].status, 200);
  });
  await scenario('changeset apply saves before auth; password failure retains pending save', async () => {
    const start = mark(), body = { name: 'Visible applied set', description: 'Apply description', operations: [{ type: 'disable', api: apis[1] }] };
    await input('.changeset-form input', body.name); await input('.changeset-form .field:nth-child(2) input', body.description); await input('.changeset-code', q(body.operations)); await click('Apply atomically');
    await uiWait(`!!document.querySelector(${q(dialog)})`); assert.equal(mutations(start).length, 1); await locks(setLocks);
    await submit('wrong'); await notice('Fixture rejection 401', dialog + ' .form-error'); assert.equal(mutations(start).length, 2); await locks(setLocks);
    await retained('.changeset-code', JSON.stringify(body.operations, null, 2), mutations(start)[0].etag, '.changeset-editor'); await screenshot('changeset-protected-error'); await submit(); await notice('Applied atomically', '.workspace-content .view-stack > .notice-success');
    const rows = mutations(start); assert.deepEqual(rows.map(e => key(e.method, e.path)), [key('PUT', setPath), key('POST', stepPath), key('POST', stepPath), key('POST', setPath + '/apply')]);
    assert.deepEqual(rows[0].body, body); assert.equal(rows[3].ifMatch, rows[0].etag); assert.deepEqual(rows[3].stored, body); assert.equal(rows[3].status, 200);
  });
  await scenario('expired session blocks save/confirmation then returns login on reload', async () => {
    await click('Fixture set 2', '.manager-list'); await uiWait('!!document.querySelector(".changeset-code")'); await settle();
    const start = mark(); expired = true; await click('Apply atomically'); await notice('Fixture rejection 401', '.workspace-content .view-stack > .notice-error'); await noConfirmation(start);
    assert.equal(mutations(start)[0].status, 401); await cdp('Page.reload'); await uiWait('!!document.querySelector(".login-form")');
  });
}

async function web404(origin) {
  // New document and host, with all browser cookies cleared; the Admin lifecycle test above does neither.
  await cdp('Page.navigate', { url: 'about:blank' }); await cdp('Network.clearBrowserCookies');
  pageOrigin = origin; product = 'web';
  await scenario('Web1 missing detail: main-document HTTP404 and live rendered 404/back link only', async () => {
    const start = events.length, path = '/tutorials/cold-missing/';
    const navigation = await cdp('Page.navigate', { url: origin + path }); assert(!navigation.errorText, navigation.errorText);
    let document;
    await until(() => { document = browserRequests.find(e => e.product === 'web' && e.type === 'Document' && e.frameId === navigation.frameId && e.loaderId === navigation.loaderId && e.path === path); return document?.status !== null && document?.status !== undefined; }, 'Web main document response');
    assert.equal(document.status, 404); await uiWait('document.readyState === "complete"');
    await notice('404', '.notFound.shell .eyebrow');
    await notice('This page slipped between chapters.', '.notFound.shell h1');
    await notice('Back to Kira', '.notFound.shell a[href="/"]');
    const dom = await evaluate(`(() => { const e=document.querySelector('.notFound.shell'); return {eyebrow:e.querySelector('.eyebrow').innerText.trim(),heading:e.querySelector('h1').innerText.trim(),back:e.querySelector('a').innerText.trim(),href:e.querySelector('a').getAttribute('href'),url:location.href}; })()`);
    assert.deepEqual(dom, { eyebrow: '404', heading: 'This page slipped between chapters.', back: 'Back to Kira', href: '/', url: origin + path });
    assert(events.slice(start).some(e => e.method === 'GET' && e.path === '/api/v1/tutorials/cold-missing' && e.status === 404));
    assert(events.slice(start).some(e => e.method === 'GET' && e.path === '/api/v1/tutorials' && e.status === 200));
    result.web404 = { httpStatus: document.status, ...dom }; await screenshot('web-404');
  });
}
async function startNext(root, name, hostname, config, readyPath) {
  const standalone = join(root, '.next/standalone'), destination = join(runtime, name);
  result.buildIds[name] = (await readFile(join(root, '.next/BUILD_ID'), 'utf8')).trim();
  await cp(standalone, destination, { recursive: true, filter: file => !basename(file).startsWith('.env') && file !== join(standalone, '.next/cache') });
  await cp(join(root, '.next/static'), join(destination, '.next/static'), { recursive: true });
  const publicRoot = join(root, 'public');
  try { await cp(publicRoot, join(destination, 'public'), { recursive: true, force: false }); } // Preserve existing materialized Web associations.
  catch (error) { if (error.code !== 'ENOENT' || error.path !== publicRoot) throw error; } // Only absent Admin public root is optional.
  const reservation = createServer(); await new Promise((resolve, reject) => { reservation.once('error', reject); reservation.listen(0, '127.0.0.1', resolve); }); const port = reservation.address().port;
  await new Promise(resolve => reservation.close(resolve)); const origin = 'http://' + hostname + ':' + port;
  launch(name + '-next', process.execPath, [join(destination, 'server.js')], { PATH: process.env.PATH, HOME: runtime, TMPDIR: runtime, NODE_ENV: 'production', NEXT_TELEMETRY_DISABLED: '1', HOSTNAME: '127.0.0.1', PORT: String(port), ...config, ...(name === 'admin' ? { KIRA_ADMIN_ORIGIN: origin } : {}) });
  await until(async () => { try { return (await fetch('http://127.0.0.1:' + port + readyPath, { signal: AbortSignal.timeout(1000) })).ok; } catch { return false; } }, name + ' production Next start', 45000);
  return origin;
}

await mkdir(out, { mode: 0o700 }); // Fresh evidence only; never overwrite an earlier run.
const deadline = setTimeout(() => { fatal = new Error('Whole smoke deadline (180s)'); }, 180000);
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => { fatal = new Error('Cancelled: ' + signal); });
try {
  result.scriptSha256 = createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex');
  result.buildIds = {};
  runtime = await mkdtemp('/tmp/kira-browser-'); result.privateRuntime = runtime; // Keep Chromium Unix socket paths below 108 bytes.
  fixture = createServer((req, res) => { backend(req, res).catch(error => { fatal = error; if (!res.headersSent) res.writeHead(500); res.end(); }); });
  await new Promise((resolve, reject) => { fixture.once('error', reject); fixture.listen(0, '127.0.0.1', resolve); }); const backendPort = fixture.address().port;
  const origin = await startNext(app, 'admin', 'localhost', { KIRA_BACKEND_URL: 'http://127.0.0.1:' + backendPort }, '/'); pageOrigin = origin;
  const webOrigin = await startNext(web, 'web', '127.0.0.1', { KIRA_TUTORIAL_API_URL: 'http://127.0.0.1:' + backendPort, NEXT_PUBLIC_KIRA_API_URL: 'http://127.0.0.1:9', KIRA_WEB_PRODUCTION: 'false' }, '/robots.txt');
  const profile = join(runtime, 'chrome');
  launch('chrome', '/usr/bin/google-chrome', ['--headless=new', '--no-sandbox', '--window-size=1440,1000', '--disable-dev-shm-usage', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', '--user-data-dir=' + profile, '--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-pings', '--no-proxy-server', '--host-resolver-rules=MAP localhost 127.0.0.1, MAP * ~NOTFOUND, EXCLUDE 127.0.0.1', 'about:blank'], { PATH: process.env.PATH, HOME: runtime, TMPDIR: runtime });
  let debuggerPort;
  await until(async () => { try { debuggerPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); return debuggerPort > 0; } catch { return false; } }, 'private Chrome endpoint', 15000);
  const pages = await (await fetch(`http://127.0.0.1:${debuggerPort}/json/list`, { signal: AbortSignal.timeout(2000) })).json();
  const endpoint = new URL(pages.find(page => page.type === 'page').webSocketDebuggerUrl); assert.equal(endpoint.hostname, '127.0.0.1');
  socket = new WebSocket(endpoint);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('CDP connect timeout')), 8000);
    socket.onopen = () => { clearTimeout(timer); resolve(); }; socket.onerror = () => { clearTimeout(timer); reject(new Error('CDP connection failed')); };
  });
  socket.onerror = () => { if (!closing) fatal = new Error('CDP socket error'); };
  socket.onclose = () => { for (const call of calls.values()) { clearTimeout(call.timer); call.reject(new Error('CDP closed')); } calls.clear(); if (!closing) fatal = new Error('CDP closed early'); };
  socket.onmessage = event => {
    try {
    const message = JSON.parse(event.data), pending = calls.get(message.id);
    if (pending) { calls.delete(message.id); clearTimeout(pending.timer); message.error ? pending.reject(new Error(q(message.error))) : pending.resolve(message.result); return; }
    const p = message.params;
    if (message.method === 'Network.requestWillBeSent' && new URL(p.request.url).origin === pageOrigin && (p.type === 'Document' || new URL(p.request.url).pathname.startsWith('/api/'))) {
      const row = { product, type: p.type, method: p.request.method, path: new URL(p.request.url).pathname, status: null, completion: null, ...(p.type === 'Document' ? { frameId: p.frameId, loaderId: p.loaderId } : {}) };
      browserRequests.push(row); active.set(p.requestId, row); networkAt = Date.now();
    }
    if (message.method === 'Network.responseReceived' && active.has(p.requestId)) active.get(p.requestId).status = p.response.status;
    if (['Network.loadingFinished', 'Network.loadingFailed'].includes(message.method) && active.has(p.requestId)) {
      active.get(p.requestId).completion = message.method === 'Network.loadingFinished' ? 'finished' : 'failed'; active.delete(p.requestId); networkAt = Date.now();
    }
    if (message.method === 'Runtime.exceptionThrown') fatal = new Error('Uncaught browser exception: ' + p.exceptionDetails.text);
    if (message.method === 'Fetch.requestPaused') {
      const allowed = new URL(p.request.url).origin === pageOrigin;
      if (!allowed) fatal = new Error('Blocked off-origin page request: ' + new URL(p.request.url).origin);
      cdp(allowed ? 'Fetch.continueRequest' : 'Fetch.failRequest', { requestId: p.requestId, ...(!allowed ? { errorReason: 'BlockedByClient' } : {}) }).catch(error => { fatal = error; });
    }
    } catch (error) { fatal = error; }
  };
  await cdp('Page.enable'); await cdp('Runtime.enable'); await cdp('Network.enable'); await cdp('Fetch.enable', { patterns: [{ urlPattern: '*' }] });
  result.browser = await cdp('Browser.getVersion');
  await cdp('Page.navigate', { url: origin }); await smoke(); await web404(webOrigin); if (fatal) throw fatal; result.status = 'PASS';
} catch (error) { result.error = error.stack ?? String(error); }
finally {
  clearTimeout(deadline); closing = true;
  if (socket?.readyState === WebSocket.OPEN) {
    try { await screenshot('last-page'); } catch { /* best-effort diagnostic, not a passing assertion */ }
    try { await cdp('Browser.close'); } catch { /* process-group cleanup below is authoritative for disposal */ }
    socket.close();
  }
  for (const gate of gates) gate.release();
  const stopped = []; for (const owned of children.reverse()) { try { stopped.push({ name: owned.name, stopped: await stopOwned(owned) }); } catch (error) { stopped.push({ name: owned.name, stopped: false, error: error.message }); } }
  if (fixture) { fixture.closeAllConnections(); await new Promise(resolve => fixture.close(resolve)); }
  result.ownedGroups = stopped; result.cleanup = stopped.every(item => item.stopped);
  if (result.cleanup && runtime) { try { await rm(runtime, { recursive: true, force: true }); } catch (error) { result.cleanup = false; result.cleanupError = error.message; } }
  if (!result.cleanup) result.status = 'FAIL';
  await writeFile(join(out, 'events.json'), JSON.stringify(events, null, 2) + '\n', { flag: 'wx' });
  await writeFile(join(out, 'browser-requests.json'), JSON.stringify(browserRequests, null, 2) + '\n', { flag: 'wx' });
  await writeFile(join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: result.status, cases: result.cases.length, cleanup: result.cleanup, evidence: out }));
  process.exitCode = result.status === 'PASS' ? 0 : 1;
}
