import { isIP } from 'node:net';

import { adminTrustedIngress } from './server-config';

/** Numeric-only shared identity format: no DNS, endpoints, zones, lists or surrounding whitespace. */
export function canonicalNumericIp(value: string | null): string | null {
  if (!value || value.length > 45 || /[^0-9A-Fa-f:.]/.test(value)) return null;
  const family = isIP(value);
  if (family === 4) return value; // isIP requires strict dotted decimal without leading zeroes.
  if (family !== 6) return null;

  let address = value;
  if (address.includes('.')) {
    const tail = address.lastIndexOf(':') + 1;
    const octets = address.slice(tail).split('.').map(Number);
    address = address.slice(0, tail) + ((octets[0] << 8) | octets[1]).toString(16) + ':' +
      ((octets[2] << 8) | octets[3]).toString(16);
  }
  const halves = address.split('::');
  const left = halves[0] ? halves[0].split(':').map((group) => parseInt(group, 16)) : [];
  const right = halves[1] ? halves[1].split(':').map((group) => parseInt(group, 16)) : [];
  const groups = halves.length === 1 ? left : [...left, ...Array<number>(8 - left.length - right.length).fill(0), ...right];
  if (groups.slice(0, 5).every((group) => group === 0) && groups[5] === 0xffff) {
    return [groups[6] >> 8, groups[6] & 255, groups[7] >> 8, groups[7] & 255].join('.');
  }
  return groups.map((group) => group.toString(16)).join(':');
}

/** Origin/CSRF do not authenticate ingress: only the explicitly isolated deployment may opt in. */
export function authenticationIdentityHeaders(request: Request): Record<string, string> {
  if (!adminTrustedIngress) return {};
  const identity = canonicalNumericIp(request.headers.get('x-real-ip'));
  // Missing/invalid metadata remains a degraded shared-peer fallback, never a caller-supplied XFF chain.
  return identity ? { 'X-Forwarded-For': identity } : {};
}
