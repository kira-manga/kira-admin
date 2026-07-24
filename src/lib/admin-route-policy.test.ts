import { describe, expect, it } from 'vitest';

import { adminRouteAllowed, isMutatingMethod, routeNeedsStepUp } from './admin-route-policy';

describe('admin BFF route policy', () => {
  it('allows the source editor and changeset workflow', () => {
    expect(adminRouteAllowed(['sources'], 'GET')).toBe(true);
    expect(adminRouteAllowed(['sources', 'Azora', 'editor-draft'], 'PUT')).toBe(true);
    expect(adminRouteAllowed(['sources', 'Azora', 'editor-draft', 'publish'], 'POST')).toBe(true);
    expect(adminRouteAllowed(['source-changesets', 'id', 'apply'], 'POST')).toBe(true);
    expect(adminRouteAllowed(['audit'], 'GET')).toBe(true);
  });

  it('denies operational escape hatches and direct lifecycle publication', () => {
    expect(adminRouteAllowed(['sources', 'import-bundled'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['sources', 'Azora', 'disable'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['sources', 'Azora', 'revisions', '2', 'publish'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['documents', 'republish'], 'POST')).toBe(false);
    expect(adminRouteAllowed(['source-catalog-v2', 'cutover'], 'POST')).toBe(false);
  });

  it('requires CSRF and one-time step-up at the correct boundaries', () => {
    expect(isMutatingMethod('POST')).toBe(true);
    expect(isMutatingMethod('GET')).toBe(false);
    expect(routeNeedsStepUp(['source-changesets', 'id', 'apply'])).toBe(true);
    expect(routeNeedsStepUp(['sources', 'Azora', 'editor-draft', 'publish'])).toBe(true);
    expect(routeNeedsStepUp(['sources', 'Azora', 'editor-draft', 'validate'])).toBe(false);
  });
});
