'use client';

import { useEffect, useState } from 'react';

import { apiFetch } from '@/lib/client-api';
import type { AdminCategory, AdminTutorial, NavView, TutorialMedia } from '@/lib/types';
import { Icon } from './icons';
import { Button, Spinner, StatusBadge, formatDate } from './ui';

type OverviewData = { tutorials: AdminTutorial[]; categories: AdminCategory[]; media: TutorialMedia[] };

export function OverviewView({ onNavigate }: { onNavigate: (view: NavView) => void }) {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiFetch<AdminTutorial[]>('tutorials'),
      apiFetch<AdminCategory[]>('tutorial-categories'),
      apiFetch<TutorialMedia[]>('tutorial-media'),
    ]).then(([tutorials, categories, media]) => setData({ tutorials, categories, media })).catch((caught: Error) => setError(caught.message));
  }, []);

  if (error) return <div className="notice notice-error">{error}</div>;
  if (!data) return <Spinner label="Loading workspace" />;
  const published = data.tutorials.filter((item) => item.status === 'PUBLISHED').length;
  const drafts = data.tutorials.filter((item) => item.status === 'DRAFT').length;
  const recent = [...data.tutorials].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 4);

  return (
    <div className="view-stack">
      <section className="welcome-panel">
        <div><span className="eyebrow"><Icon name="spark" /> CONTENT CONTROL</span><h2>Your tutorial library,<br /><em>beautifully under control.</em></h2><p>Create bilingual guides, arrange the learning journey, and publish without rebuilding the public website.</p><div className="welcome-actions"><Button tone="primary" icon="plus" onClick={() => onNavigate('tutorials')}>Create tutorial</Button><Button icon="upload" onClick={() => onNavigate('media')}>Upload screenshots</Button></div></div>
        <div className="welcome-orbit"><div><strong>{published}</strong><span>live guides</span></div><i /><i /><i /></div>
      </section>

      <section className="stat-grid">
        <button type="button" onClick={() => onNavigate('tutorials')}><span className="stat-icon coral"><Icon name="tutorials" /></span><div><small>Total tutorials</small><strong>{data.tutorials.length}</strong><p>{published} published · {drafts} draft</p></div><Icon name="arrow" /></button>
        <button type="button" onClick={() => onNavigate('categories')}><span className="stat-icon amber"><Icon name="categories" /></span><div><small>Categories</small><strong>{data.categories.length}</strong><p>{data.categories.filter((item) => item.status === 'PUBLISHED').length} visible on the site</p></div><Icon name="arrow" /></button>
        <button type="button" onClick={() => onNavigate('media')}><span className="stat-icon mint"><Icon name="media" /></span><div><small>Media assets</small><strong>{data.media.length}</strong><p>{data.media.filter((item) => item.published).length} currently referenced</p></div><Icon name="arrow" /></button>
      </section>

      <section className="split-grid">
        <div className="panel">
          <div className="panel-heading"><div><span>RECENT ACTIVITY</span><h3>Latest tutorial updates</h3></div><button type="button" onClick={() => onNavigate('tutorials')}>View all <Icon name="arrow" /></button></div>
          <div className="activity-list">
            {recent.map((tutorial) => <button type="button" key={tutorial.id} onClick={() => onNavigate('tutorials')}><span className="activity-number">{String(tutorial.position + 1).padStart(2, '0')}</span><div><strong>{tutorial.slug}</strong><small>Updated {formatDate(tutorial.updatedAt)}</small></div><StatusBadge status={tutorial.status} /></button>)}
          </div>
        </div>
        <div className="panel workflow-panel">
          <div className="panel-heading"><div><span>WORKFLOW</span><h3>From idea to live</h3></div></div>
          <ol className="workflow-list">
            <li><span>1</span><div><strong>Upload visual assets</strong><small>Add the EN/AR and light/dark screenshots.</small></div></li>
            <li><span>2</span><div><strong>Write a revision</strong><small>Keep both languages together in one draft.</small></div></li>
            <li><span>3</span><div><strong>Publish with confidence</strong><small>The website refreshes its content automatically.</small></div></li>
          </ol>
        </div>
      </section>
    </div>
  );
}
