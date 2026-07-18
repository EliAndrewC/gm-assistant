#!/usr/bin/env python3
"""Scatter the ten faces of a d10 into a dream scene's bands.

The point is that the face-to-band map is fresh and unguessable every scene:
players must never be able to learn that "1-2 is no dream, 3-4 is noise". A 10
is always pinned to the meaningful band (a known anchor of certainty, which the
Coda of Understanding relies on); the other nine faces are shuffled into the
requested bands. See SKILL.md for the theology and craft this serves.

Usage:
    python3 randomize_bands.py --none 2 --unrelated 2
    python3 randomize_bands.py --none 3 --unrelated 2 --misleading 1

Any face count not assigned to none/unrelated/misleading falls to meaningful.
The printed table is for the GM's eyes only - never show it to the players.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence

# The label every scene guarantees, and the face pinned to it.
MEANINGFUL = 'meaningful'
PINNED_FACE = 10
DIE_FACES = tuple(range(1, 11))


def assign_bands(
    band_counts: dict[str, int],
    rng: random.Random,
    *,
    faces: Sequence[int] = DIE_FACES,
    pinned_face: int = PINNED_FACE,
    meaningful: str = MEANINGFUL,
) -> dict[int, str]:
    """Return a face-to-band mapping for a die.

    `band_counts` gives how many faces each non-meaningful band should claim
    (e.g. {'none': 2, 'unrelated': 2}). `pinned_face` is forced to the
    `meaningful` band and excluded from the shuffle; every face left over after
    the requested bands are filled also becomes `meaningful`. Raises ValueError
    if the counts do not fit the remaining faces.
    """
    if pinned_face not in faces:
        raise ValueError(f'pinned face {pinned_face} is not among the die faces')
    if any(count < 0 for count in band_counts.values()):
        raise ValueError('band counts must be non-negative')

    shufflable = [face for face in faces if face != pinned_face]
    requested = sum(band_counts.values())
    if requested > len(shufflable):
        raise ValueError(
            f'requested {requested} faces across bands but only '
            f'{len(shufflable)} are free (face {pinned_face} is pinned to {meaningful})'
        )

    pool = list(shufflable)
    rng.shuffle(pool)

    mapping: dict[int, str] = {pinned_face: meaningful}
    cursor = 0
    for band, count in band_counts.items():
        if band == meaningful:
            raise ValueError(f'do not pass the pinned band {meaningful!r} in band_counts')
        for face in pool[cursor : cursor + count]:
            mapping[face] = band
        cursor += count
    for face in pool[cursor:]:
        mapping[face] = meaningful
    return mapping


def format_table(mapping: dict[int, str]) -> str:
    """Render the face-to-band mapping as a face-ordered text table."""
    width = max((len(band) for band in mapping.values()), default=0)
    lines = ['face | band', '-----+-----']
    for face in sorted(mapping):
        lines.append(f'{face:>4} | {mapping[face]:<{width}}')
    return '\n'.join(lines)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Randomize a dream scene d10 band map.')
    parser.add_argument('--none', type=int, default=0, help='faces for the no-dream band')
    parser.add_argument('--unrelated', type=int, default=0, help='faces for the noise band')
    parser.add_argument(
        '--misleading', type=int, default=0, help='faces for the misleading band (optional)'
    )
    parser.add_argument(
        '--seed', type=int, default=None, help='optional seed (for reproducing a specific scene)'
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> str:
    args = _parse_args(argv)
    counts = {'none': args.none, 'unrelated': args.unrelated, 'misleading': args.misleading}
    counts = {band: n for band, n in counts.items() if n}
    mapping = assign_bands(counts, random.Random(args.seed))
    return format_table(mapping)


if __name__ == '__main__':  # pragma: no cover
    print(main())
