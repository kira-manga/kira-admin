import { PassThrough } from 'node:stream';

import type { NextApiRequest, NextApiResponse } from 'next';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { createSessionFixture, fixtureSigningSecret, signedRequestHeaders } from '@/test/server-session-fixture';
import { sessionGenerationHeader } from './session-contract';

const transport = vi.hoisted(() => ({ http: vi.fn(), https: vi.fn() }));
vi.mock('node:http', () => ({ request: transport.http }));
vi.mock('node:https', () => ({ request: transport.https }));

function request(extra: HeadersInit = {}) {
  const session = createSessionFixture('fixture-upload-jwt');
  const headers = signedRequestHeaders(session, [], { 'Content-Type': 'multipart/form-data; boundary=fixture', 'Content-Length': '4', ...Object.fromEntries(new Headers(extra)) });
  const stream = Object.assign(new PassThrough(), {
    method: 'POST', headers: Object.fromEntries(headers), socket: {},
    // The legacy/framework cookie map is not a security authority, even when caller-controlled.
    cookies: { kira_admin_session: 'attacker-jwt', kira_admin_csrf: 'attacker-csrf' },
  }) as unknown as NextApiRequest & PassThrough;
  return { stream, session };
}

function response() {
  const stream = new PassThrough();
  const headers = new Map<string, unknown>();
  const parts: Buffer[] = [];
  stream.on('data', (part: Buffer) => parts.push(part));
  const output = Object.assign(stream, { statusCode: 200, headersSent: false });
  Object.assign(output, {
    setHeader: (name: string, value: unknown) => { headers.set(name.toLowerCase(), value); },
    status: (status: number) => { output.statusCode = status; return output; },
    json: (value: unknown) => { output.end(JSON.stringify(value)); return output; },
  });
  return { stream: output as unknown as NextApiResponse, headers, body: () => Buffer.concat(parts).toString('utf8') };
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', fixtureSigningSecret);
  vi.stubEnv('KIRA_ADMIN_ORIGIN', 'https://admin.example.test');
  vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'false');
  transport.http.mockReset();
  transport.https.mockReset();
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); });

describe('mounted Pages upload signed-session boundary', () => {
  it('streams using only the selected signed JWT, with the existing content length, type and deadline', async () => {
    const input = request();
    const output = response();
    const upstreamRequest = Object.assign(new PassThrough(), { setTimeout: vi.fn() });
    const upstreamResponse = Object.assign(new PassThrough(), { statusCode: 201, headers: { 'content-type': 'application/json' } });
    transport.http.mockReturnValue(upstreamRequest);
    const { default: handler, config } = await import('../pages/api/tutorial-media-upload');
    expect(config.api.bodyParser).toBe(false);
    const work = handler(input.stream, output.stream);
    expect(transport.http).toHaveBeenCalledOnce();
    expect(String(transport.http.mock.calls[0][0])).toBe('http://backend:8080/api/v1/admin/tutorial-media');
    expect(transport.http.mock.calls[0][1]).toEqual({ method: 'POST', headers: {
      Accept: 'application/json, application/problem+json', Authorization: 'Bearer fixture-upload-jwt',
      'Content-Type': 'multipart/form-data; boundary=fixture', 'Content-Length': 4,
    } });
    expect(upstreamRequest.setTimeout).toHaveBeenCalledWith(65_000, expect.any(Function));
    input.stream.end('data');
    transport.http.mock.calls[0][2](upstreamResponse);
    upstreamResponse.end('{"id":"synthetic-media"}');
    await work;
    expect(output.stream.statusCode).toBe(201);
    expect(output.body()).toBe('{"id":"synthetic-media"}');
    expect(output.body()).not.toContain(input.session.token);
    expect(transport.https).not.toHaveBeenCalled();
  });

  it.each([
    ['missing selector', 401], ['missing cookie', 401], ['duplicate cookie', 400],
    ['duplicate selector', 401], ['wrong CSRF', 403], ['wrong origin', 403], ['missing secret', 503],
    ['too large', 413], ['missing length', 411], ['wrong media', 415],
  ] as const)('refuses %s before allocating an upstream request', async (failure, status) => {
    const input = request();
    const headers = input.stream.headers;
    if (failure === 'missing selector') delete headers[sessionGenerationHeader.toLowerCase()];
    if (failure === 'missing cookie') delete headers.cookie;
    if (failure === 'duplicate cookie') headers.cookie += `; ${input.session.name}=${input.session.value}`;
    if (failure === 'duplicate selector') headers[sessionGenerationHeader.toLowerCase()] = [input.session.generation, input.session.generation];
    if (failure === 'wrong CSRF') headers['x-kira-csrf'] = 'attacker-csrf';
    if (failure === 'wrong origin') headers.origin = 'https://attacker.example.test';
    if (failure === 'missing secret') vi.stubEnv('KIRA_ADMIN_SESSION_SECRET', undefined);
    if (failure === 'too large') headers['content-length'] = String(5 * 1024 * 1024 + 1);
    if (failure === 'missing length') delete headers['content-length'];
    if (failure === 'wrong media') headers['content-type'] = 'application/json';
    const output = response();
    const { default: handler } = await import('../pages/api/tutorial-media-upload');
    await handler(input.stream, output.stream);
    expect(output.stream.statusCode).toBe(status);
    expect(transport.http).not.toHaveBeenCalled();
    expect(transport.https).not.toHaveBeenCalled();
    input.stream.destroy();
  });
});
