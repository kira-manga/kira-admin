import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

import { AdminShell } from './admin-shell';

describe('live catalog link', () => {
  it('renders the fixed same-origin manifest route in an isolated new tab', () => {
    const html = renderToStaticMarkup(
      <AdminShell
        session={{ id: 'test-admin', email: 'admin@example.test', role: 'ADMIN', createdAt: '2026-09-09T00:00:00Z', csrfToken: 'test-only', generation: '12345678-1234-4234-8234-123456789abc', expiresAt: '2099-01-01T00:00:00Z' }}
        view="overview"
        onView={vi.fn()}
        onLogout={vi.fn()}
      >
        <p>Workspace</p>
      </AdminShell>,
    );
    const anchor = html.match(/<a\b[^>]*>View live catalog[\s\S]*?<\/a>/)?.[0];
    expect(anchor).toBeDefined();
    expect(anchor).toContain('href="/api/catalog/manifest"');
    expect(anchor).toContain('target="_blank"');
    expect(anchor).toContain('rel="noopener noreferrer"');
    expect(html).not.toContain('api.kiramanga.me');
    expect(html).not.toContain('/api/v1/source-config/catalog');
  });
});
