import type { CategoryRevision } from './types';

export function categoryRevisionDefaults(revisions: readonly CategoryRevision[]) {
  let latest: CategoryRevision | undefined;
  for (const revision of revisions) {
    if (latest === undefined || revision.revision > latest.revision) {
      latest = revision;
    }
  }

  return {
    labelEn: latest?.label.en,
    labelAr: latest?.label.ar,
    iconCode: latest?.iconCode ?? 'book',
  };
}
