import { complaintScope } from './complaint-mutation-fixture';

// Independent synthetic contract fixture. Numeric tokens are emitted as original decimal text, never Number.
export type StatsFixture = {
  dataScopeId: string; total: string;
  byStatus: Array<{ status: string; count: string }>;
  byType: Array<{ type: string | null; count: string }>;
  byOwnership: Array<{ ownership: string; count: string }>;
  appVersions: { buckets: Array<{ appVersion: string | null; count: string }>; otherCount: string };
};
export const statsTotal = '9007199254740993';

export function statsFixture(total = statsTotal): StatsFixture {
  return { dataScopeId: complaintScope, total,
    byStatus: ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'PLANNED', 'PINNED', 'NOT_PLANNED'].map((status, index) => ({ status, count: index === 0 ? total : '0' })),
    byType: ['TECHNICAL', 'LANGUAGES', 'SITES_ADD', 'SITE_ERROR', 'FEATURES', 'CUSTOM', null].map((type, index) => ({ type, count: index === 0 ? total : '0' })),
    byOwnership: [{ ownership: 'INSTALLATION', count: total }, { ownership: 'SYSTEM', count: '0' }],
    appVersions: { buckets: total === '0' ? [] : [{ appVersion: 'Synthetic version', count: total }], otherCount: '0' },
  };
}

export function statsDocument(value = statsFixture()): string {
  return `{"dataScopeId":${JSON.stringify(value.dataScopeId)},"total":${value.total},`
    + `"byStatus":[${value.byStatus.map((row) => `{"status":${JSON.stringify(row.status)},"count":${row.count}}`).join(',')}],`
    + `"byType":[${value.byType.map((row) => `{"type":${JSON.stringify(row.type)},"count":${row.count}}`).join(',')}],`
    + `"byOwnership":[${value.byOwnership.map((row) => `{"ownership":${JSON.stringify(row.ownership)},"count":${row.count}}`).join(',')}],`
    + `"appVersions":{"buckets":[${value.appVersions.buckets.map((row) => `{"appVersion":${JSON.stringify(row.appVersion)},"count":${row.count}}`).join(',')}],"otherCount":${value.appVersions.otherCount}}}`;
}

export function statsResponse(body: BodyInit | null = statsDocument(), status = 200, headers: HeadersInit = {}): Response {
  const selected = new Headers({ 'Content-Type': 'application/json;charset=UTF-8', 'X-Kira-Complaint-Contract': '1' });
  new Headers(headers).forEach((value, name) => selected.set(name, value));
  return new Response(body, { status, headers: selected });
}
