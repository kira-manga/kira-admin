import { describe, expect, it } from 'vitest';

import { adminRouteAllowed, isComplaintDetailQuery, isComplaintMutationPath, isMutatingMethod, routeNeedsStepUp } from './admin-route-policy';

describe('admin BFF route policy', () => {
  it('admits only the literal POST search path, with CSRF classification but no proof requirement', () => {
    const search = ['complaints', 'search'];
    expect(adminRouteAllowed(search, 'POST')).toBe(true);
    expect(isMutatingMethod('POST')).toBe(true);
    expect(routeNeedsStepUp(search, 'POST')).toBe(false);
    for (const method of ['GET', 'PUT', 'PATCH', 'DELETE', 'HEAD']) expect(adminRouteAllowed(search, method)).toBe(false);
    for (const path of [['complaints', 'stats'], ['complaints', 'batch'], ['complaints', 'search', ''], ['complaints', 'Search'], ['complaints', 'se%61rch']]) {
      expect(adminRouteAllowed(path, 'POST')).toBe(false);
    }
  });
  it('admits only the three non-deleting complaint PATCH shapes, classified for CSRF but not source proof', () => {
    const id = '12345678-1234-4234-8234-123456789abc';
    expect(isMutatingMethod('PATCH')).toBe(true);
    for (const action of ['content', 'status', 'closure']) {
      const path = ['complaints', id, action];
      expect(isComplaintMutationPath(path)).toBe(true);
      expect(adminRouteAllowed(path, 'PATCH')).toBe(true);
      expect(routeNeedsStepUp(path, 'PATCH')).toBe(false);
      for (const method of ['POST', 'PUT', 'DELETE', 'GET']) expect(adminRouteAllowed(path, method)).toBe(false);
    }
    for (const path of [['complaints', id], ['complaints', id, 'delete'], ['complaints', 'batch'],
      ['complaints', id.toUpperCase(), 'content'], ['complaints', id, 'content', ''], ['complaints', id + '\n', 'status']]) {
      expect(adminRouteAllowed(path, 'PATCH')).toBe(false);
    }
  });
  it('allows only a canonical complaint detail GET and one literal TEST scope query', () => {
    const id = '12345678-1234-3234-8234-123456789abc';
    const scope = '87654321-1234-4234-8234-123456789abc';
    expect(adminRouteAllowed(['complaints', id], 'GET')).toBe(true);
    expect(routeNeedsStepUp(['complaints', id], 'GET')).toBe(false);
    expect(isComplaintDetailQuery(`?dataScopeId=${scope}`)).toBe(true);
    for (const method of ['POST', 'PATCH', 'PUT', 'DELETE', 'HEAD']) {
      expect(adminRouteAllowed(['complaints', id], method)).toBe(false);
    }
    for (const path of [['complaints'], ['complaints', 'search'], ['complaints', id, 'content'], ['complaints', id, 'status'],
      ['complaints', id, 'closure'], ['complaints', id, ''], ['complaints', id.toUpperCase()], ['complaints', `${id}\n`]]) {
      expect(adminRouteAllowed(path, 'GET')).toBe(false);
    }
    for (const query of ['', `?dataScopeId=${id}`, '?dataScopeId=00000000-0000-0000-0000-000000000000',
      `?dataScopeId=${scope.toUpperCase()}`, `?dataScopeId=${scope}&dataScopeId=${scope}`, `?dataScopeId=${scope}&extra=1`,
      `?dataScopeId=%38${scope.slice(1)}`, `?dataScopeId=${scope}\n`]) {
      expect(isComplaintDetailQuery(query)).toBe(false);
    }
  });

  it('allows the source editor and changeset workflow', () => {
    expect(adminRouteAllowed(['sources'], 'GET')).toBe(true);
    expect(adminRouteAllowed(['sources', 'Azora', 'editor-draft'], 'PUT')).toBe(true);
    expect(adminRouteAllowed(['sources', 'Azora', 'editor-draft', 'publish'], 'POST')).toBe(true);
    expect(adminRouteAllowed(['sources', 'Azora', 'operational-mode'], 'PUT')).toBe(true);
    expect(adminRouteAllowed(['source-changesets', 'id', 'apply'], 'POST')).toBe(true);
    expect(adminRouteAllowed(['audit'], 'GET')).toBe(true);
    expect(adminRouteAllowed(['source-preview'], 'POST')).toBe(true);
  });

  it('denies operational escape hatches and direct lifecycle publication', () => {
    expect(adminRouteAllowed(['sources', 'import-bundled'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['sources', 'Azora', 'disable'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['sources', 'Azora', 'operational-mode'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['sources', 'Azora', 'revisions', '2', 'publish'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['documents', 'republish'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['source-catalog-v2', 'cutover'], 'POST')).toBe(false);
  });

  it('requires CSRF and one-time step-up at the correct boundaries', () => {
    expect(isMutatingMethod('POST')).toBe(true);
    expect(isMutatingMethod('GET')).toBe(false);
    const id = '12345678-1234-1234-8234-123456789abc';
    expect(routeNeedsStepUp(['source-changesets', id, 'apply'], 'POST')).toBe(true);
    expect(routeNeedsStepUp(['sources', 'Azora', 'editor-draft', 'publish'], 'POST')).toBe(true);
    expect(routeNeedsStepUp(['sources', 'Azora', 'operational-mode'], 'PUT')).toBe(true);
    for (const path of [['source-changesets', 'id', 'apply'], ['source-changesets', id.toUpperCase(), 'apply'],
      ['source-changesets', id, 'nested', 'apply'], ['source-changesets', id + '\n', 'apply'], ['sources', 'Azora', 'editor-draft', 'validate'],
      ['sources', 'Azora/editor-draft', 'publish'], ['tutorials', 'apply'], ['sources', '', 'operational-mode']]) {
      for (const method of ['GET', 'POST', 'PUT', 'DELETE']) expect(routeNeedsStepUp(path, method)).toBe(false);
    }
    expect(routeNeedsStepUp(['source-changesets', id, 'apply'], 'PUT')).toBe(false);
    expect(routeNeedsStepUp(['sources', 'Azora', 'editor-draft', 'publish'], 'DELETE')).toBe(false);
    expect(routeNeedsStepUp(['sources', 'Azora', 'operational-mode'], 'POST')).toBe(false);
  });
});
