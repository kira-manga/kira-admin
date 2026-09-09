import { describe, expect, it } from 'vitest';

import type { AdminTutorial } from './types';
import { buildFeaturedToggleItems } from './tutorial-featured-order';

type TutorialOrderItem = Pick<AdminTutorial, 'id' | 'position' | 'featuredPosition'>;

const inventory: TutorialOrderItem[] = [
  { id: 'A', position: 2, featuredPosition: 2 },
  { id: 'H', position: 0, featuredPosition: null },
  { id: 'B', position: 3, featuredPosition: 0 },
  { id: 'C', position: 1, featuredPosition: 1 },
];
const onlyFeaturedInventory = inventory.map((item) => ({
  ...item,
  featuredPosition: item.id === 'B' ? 0 : null,
}));

function expectToggle(
  tutorials: readonly TutorialOrderItem[],
  selectedId: string,
  expectedFeaturedPositions: readonly (number | null)[],
): TutorialOrderItem[] {
  const before = tutorials.map((item) => ({ ...item }));
  tutorials.forEach((item) => Object.freeze(item));
  Object.freeze(tutorials);
  const selected = tutorials.find((item) => item.id === selectedId);
  if (!selected) throw new Error('Selected tutorial is missing from the test fixture.');

  const result = buildFeaturedToggleItems(tutorials, selected);

  expect(result).toEqual(before.map((item, index) => ({
    id: item.id,
    position: item.position,
    featuredPosition: expectedFeaturedPositions[index],
  })));
  expect(result.map((item) => item.id)).toEqual(before.map((item) => item.id));
  expect(new Set(result.map((item) => item.id)).size).toBe(before.length);
  expect(result.map((item) => item.position)).toEqual(before.map((item) => item.position));
  const featured = result.flatMap((item) => item.featuredPosition === null ? [] : [item.featuredPosition]);
  expect(featured.sort((a, b) => a - b)).toEqual(Array.from({ length: featured.length }, (_, index) => index));
  expect(tutorials).toEqual(before);
  expect(result).not.toBe(tutorials);
  result.forEach((item, index) => expect(item).not.toBe(tutorials[index]));
  return result;
}

describe('buildFeaturedToggleItems', () => {
  it.each([
    { name: 'first', tutorials: inventory, selectedId: 'B', expected: [1, null, null, 0] },
    { name: 'middle', tutorials: inventory, selectedId: 'C', expected: [1, null, 0, null] },
    { name: 'last', tutorials: inventory, selectedId: 'A', expected: [null, null, 0, 1] },
    { name: 'only', tutorials: onlyFeaturedInventory, selectedId: 'B', expected: [null, null, null, null] },
  ])('removes the $name featured tutorial with a complete contiguous order', ({ tutorials, selectedId, expected }) => {
    expectToggle(tutorials, selectedId, expected);
  });

  it('appends a hidden tutorial after removal without reintroducing gaps', () => {
    const afterRemoval = expectToggle(inventory, 'C', [1, null, 0, null]);
    expectToggle(afterRemoval, 'H', [1, 2, 0, null]);
  });
});
