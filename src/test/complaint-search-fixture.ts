import { complaintId, complaintScope } from './complaint-mutation-fixture';

// Synthetic encodings of backend e168 ComplaintAdminSearchParser/ComplaintAdminReadResponses.
// The opaque cursor has canonical syntax only, NOT a real backend MAC or activation authority.
export const searchCursor = `v1.AA.${'A'.repeat(43)}`;
export const searchVersion = '9007199254740993';
export const searchNoticeId = '12345678-1234-3234-8234-123456789abc';
type Fields = Record<string, string | null>;

function raw(fields: Fields) {
  return `{${Object.entries(fields).map(([name, value]) => `${JSON.stringify(name)}:${name === 'version' ? value : JSON.stringify(value)}`).join(',')}}`;
}

export function searchContent(overrides: Fields = {}) {
  const id = overrides.id ?? complaintId, version = overrides.version ?? searchVersion;
  return raw({ id, kind: 'REPORT', status: 'OPEN', createdAt: '2026-09-20T01:02:03Z', updatedAt: '2026-09-20T01:02:03Z', version,
    ownership: 'INSTALLATION', ownerReference: complaintScope, type: 'TECHNICAL', subject: 'Synthetic search subject', body: 'Synthetic search body',
    actionTag: `"complaint-${id}-v${version}"`, appVersion: null, platform: 'ANDROID', osVersion: '', manufacturer: '', deviceModel: '',
    closureReason: null, replyToId: null, closedAt: null, closureProvenance: null, closureActorId: null, ...overrides });
}

export function searchNotice(overrides: Fields = {}) {
  return raw({ id: searchNoticeId, kind: 'NOTICE', status: 'PINNED', createdAt: '2026-09-20T01:02:03Z', updatedAt: '2026-09-20T01:02:03Z',
    version: '9223372036854775807', ownership: 'SYSTEM', ownerReference: null, noticeKey: 'synthetic.search.notice', ...overrides });
}

export function searchPage(items = [searchContent()], nextCursor: string | null = null) {
  return `{"items":[${items.join(',')}],"nextCursor":${JSON.stringify(nextCursor)}}`;
}

export function searchResponse(body: BodyInit | null = searchPage(), status = 200, extra: HeadersInit = {}) {
  const headers = new Headers({ 'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1' });
  for (const [name, value] of new Headers(extra)) headers.set(name, value);
  return new Response(body, { status, headers });
}
