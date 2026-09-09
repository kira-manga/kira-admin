import { describe, expect, it } from 'vitest';

import type { CategoryRevision } from './types';
import { categoryRevisionDefaults } from './category-revision-defaults';

const original: CategoryRevision = {
  id: 'revision-1',
  revision: 1,
  label: { en: 'Original category', ar: 'التصنيف الأصلي' },
  iconCode: 'book',
  createdBy: null,
  createdAt: '2026-09-01T00:00:00Z',
};
const middle: CategoryRevision = {
  id: 'revision-2',
  revision: 2,
  label: { en: 'Revised category', ar: 'التصنيف المعدل' },
  iconCode: 'search',
  createdBy: null,
  createdAt: '2026-09-02T00:00:00Z',
};
const latest: CategoryRevision = {
  id: 'revision-3',
  revision: 3,
  label: { en: 'Latest category', ar: 'أحدث تصنيف' },
  iconCode: 'settings',
  createdBy: null,
  createdAt: '2026-09-03T00:00:00Z',
};
const latestDefaults = { labelEn: 'Latest category', labelAr: 'أحدث تصنيف', iconCode: 'settings' };

describe('categoryRevisionDefaults', () => {
  it.each([
    { name: 'descending', revisions: [latest, middle, original], expected: latestDefaults },
    { name: 'unsorted with an interior maximum', revisions: [original, latest, middle], expected: latestDefaults },
    { name: 'empty', revisions: [], expected: { labelEn: undefined, labelAr: undefined, iconCode: 'book' } },
  ])('returns the form defaults for $name history without mutation', ({ revisions, expected }) => {
    const before = structuredClone(revisions);
    revisions.forEach((revision) => {
      Object.freeze(revision.label);
      Object.freeze(revision);
    });
    Object.freeze(revisions);

    expect(categoryRevisionDefaults(revisions)).toStrictEqual(expected);
    expect(revisions).toStrictEqual(before);
  });
});
