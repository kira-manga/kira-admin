import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('NODE_ENV', 'production');
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', undefined);
  vi.stubEnv('KIRA_BACKEND_URL', undefined);
  vi.stubEnv('KIRA_ADMIN_ORIGIN', 'https://admin.example.test/');
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('server-only trusted ingress configuration', () => {
  it.each([undefined, 'false'])('defaults trust off in production with %s', async (setting) => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', setting);
    const config = await import('./server-config');

    expect(config.adminTrustedIngress).toBe(false);
    expect(config.backendUrl).toBe('https://api.kiramanga.me');
    expect(config.adminOrigin).toBe('https://admin.example.test');
    expect(config.adminTokenCookie).toBe('kira_admin_session');
    expect(config.adminCsrfCookie).toBe('kira_admin_csrf');
    expect(config.adminStepUpCookie).toBe('kira_admin_step_up');
  });

  it.each([undefined, 'false'])('preserves a configurable backend URL with trust %s', async (setting) => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', setting);
    vi.stubEnv('KIRA_BACKEND_URL', 'https://direct-api.example.test/custom/');
    const config = await import('./server-config');

    expect(config.adminTrustedIngress).toBe(false);
    expect(config.backendUrl).toBe('https://direct-api.example.test/custom');
  });

  it('does not infer trust from the internal backend URL', async () => {
    vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
    expect((await import('./server-config')).adminTrustedIngress).toBe(false);
  });

  it('accepts only the explicit opt-in paired with the exact internal URL', async () => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'true');
    vi.stubEnv('KIRA_BACKEND_URL', 'http://backend:8080');
    const config = await import('./server-config');

    expect(config.adminTrustedIngress).toBe(true);
    expect(config.backendUrl).toBe('http://backend:8080');
  });

  it.each(['', 'TRUE', 'True', 'FALSE', 'False', '1', '0', 'yes', ' true', 'true ', 'false\n', 'true,false'])
  ('rejects the ambiguous trust setting %j on config load without echoing values', async (setting) => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', setting);
    vi.stubEnv('KIRA_BACKEND_URL', 'https://fixture-user:fixture-secret@private.example.test/private-path');

    await expect(import('./server-config')).rejects.toMatchObject({
      name: 'Error',
      message: 'KIRA_ADMIN_TRUSTED_INGRESS must be true or false when set.',
    });
  });

  it.each([
    undefined,
    '',
    'http://backend:8080/',
    'HTTP://backend:8080',
    'http://BACKEND:8080',
    'https://backend:8080',
    'http://backend',
    'http://backend:08080',
    'http://backend.:8080',
    'http://127.0.0.1:8080',
    'http://backend:8080/private',
    'http://backend:8080?query=fixture-secret',
    'http://backend:8080#fragment',
    'http://fixture-user:fixture-secret@backend:8080',
    'http://backend:8080@elsewhere.example.test',
    ' http://backend:8080',
    'http://backend:8080 ',
  ])('rejects trusted ingress with the nonexact backend URL %j without echoing it', async (url) => {
    vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'true');
    vi.stubEnv('KIRA_BACKEND_URL', url);

    await expect(import('./server-config')).rejects.toMatchObject({
      name: 'Error',
      message: 'Trusted admin ingress requires KIRA_BACKEND_URL=http://backend:8080.',
    });
  });
});
