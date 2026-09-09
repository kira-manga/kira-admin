import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv('KIRA_ADMIN_TRUSTED_INGRESS', 'false');
  vi.stubEnv('KIRA_BACKEND_URL', undefined);
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('canonical numeric client identity shared with Backend', () => {
  it.each([
    ['192.0.2.1', '192.0.2.1'],
    ['0.0.0.0', '0.0.0.0'],
    ['255.255.255.255', '255.255.255.255'],
    ['2001:0DB8:0:0:0001::0001', '2001:db8:0:0:1:0:0:1'],
    ['::', '0:0:0:0:0:0:0:0'],
    ['::1', '0:0:0:0:0:0:0:1'],
    ['::ffff:192.0.2.1', '192.0.2.1'],
    ['::FFFF:c000:0201', '192.0.2.1'],
    ['0:0:0:0:0:FFFF:C000:201', '192.0.2.1'],
    ['::192.0.2.1', '0:0:0:0:0:0:c000:201'],
    ['::ffff:0:192.0.2.1', '0:0:0:0:ffff:0:c000:201'],
    ['2001:db8::192.0.2.1', '2001:db8:0:0:0:0:c000:201'],
    ['ffff:ffff:ffff:ffff:ffff:ffff:255.255.255.255', 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'],
  ])('normalizes %s to the stable key %s', async (input, expected) => {
    const { canonicalNumericIp } = await import('./server-client-ip');

    expect(canonicalNumericIp(input)).toBe(expected);
    expect(canonicalNumericIp(expected)).toBe(expected);
  });

  it.each([
    null,
    '',
    '192.0.2',
    '192.0.2.256',
    '192.0.02.1',
    '0xC0.0.2.1',
    '3221225985',
    '192.0.2.1.',
    '-1.0.0.1',
    ':',
    '1:2:3:4:5:6:7',
    '1:2:3:4:5:6:7:8:9',
    '1:2:3:4:5:6:7:8::',
    '2001:::1',
    '2001::db8::1',
    '2001:db8::gggg',
    '2001:db8::10000',
    '::ffff:192.0.02.1',
    '::ffff:192.0.2.256',
    '192.0.2.1::',
    'fe80::1%eth0',
    'fe80::1%1',
    'fe80::1%25eth0',
    '[::1]',
    '[2001:db8::1]:443',
    '192.0.2.1:443',
    '192.0.2.1, 198.51.100.1',
    '192.0.2.1, 192.0.2.1',
    '192.0.2.1 198.51.100.1',
    '192.0.2.1;for=198.51.100.1',
    'for=192.0.2.1',
    '"192.0.2.1"',
    'localhost',
    'attacker.example.test',
    'https://192.0.2.1',
    'unknown',
    '_hidden',
    ' 192.0.2.1',
    '192.0.2.1 ',
    '\t::1',
    '::1\n',
    '::1\r\nX-Injected: 1',
    '::1\u0000',
    '::1\u007f',
    '::1\u00a0',
    'é::1',
    '２００１:db8::1',
    '1'.repeat(46),
    'ffff:ffff:ffff:ffff:ffff:ffff:255.255.255.2550',
  ])('rejects nonliteral, ambiguous or out-of-budget input %j without trimming', async (input) => {
    const { canonicalNumericIp } = await import('./server-client-ip');
    expect(canonicalNumericIp(input)).toBeNull();
  });

  it('enforces the 45-character limit before any normalization', async () => {
    const { canonicalNumericIp } = await import('./server-client-ip');
    const maximum = 'ffff:ffff:ffff:ffff:ffff:ffff:255.255.255.255';

    expect(maximum).toHaveLength(45);
    expect(canonicalNumericIp(maximum)).toBe('ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff');
    expect(canonicalNumericIp(maximum + ' ')).toBeNull();
  });

  it('does not even read caller metadata when ingress trust is off', async () => {
    const { authenticationIdentityHeaders } = await import('./server-client-ip');
    const request = new Request('https://admin.example.test/api/auth/login');
    Object.defineProperty(request, 'headers', {
      get() { throw new Error('Disabled ingress must not inspect forwarding metadata.'); },
    });

    expect(authenticationIdentityHeaders(request)).toEqual({});
  });
});
