import type { AdminTutorial } from './types';

type TutorialOrderItem = Pick<AdminTutorial, 'id' | 'position' | 'featuredPosition'>;

export function buildFeaturedToggleItems(
  tutorials: readonly TutorialOrderItem[],
  selected: TutorialOrderItem,
): TutorialOrderItem[] {
  const featured = tutorials
    .filter((item) => item.featuredPosition !== null && item.id !== selected.id)
    .sort((a, b) => (a.featuredPosition ?? 0) - (b.featuredPosition ?? 0));
  if (selected.featuredPosition === null) featured.push(selected);

  // The complete reorder payload must have gap-free featured positions.
  const featuredPositions = new Map(featured.map((item, position) => [item.id, position]));
  return tutorials.map((item) => ({
    id: item.id,
    position: item.position,
    featuredPosition: featuredPositions.get(item.id) ?? null,
  }));
}
