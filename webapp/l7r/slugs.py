"""Relic lookup helpers.

Pure functions over an in-memory list of Relic objects. The list is the
single source of truth; these helpers are O(N) on a 42-element list and
that's fine.
"""

from __future__ import annotations

from l7r.pool import Relic


def find_relic_by_slug(relics: list[Relic], slug: str) -> Relic | None:
    """Return the Relic with this slug, or None if absent."""
    for relic in relics:
        if relic.slug == slug:
            return relic
    return None


def relics_for_fortune(relics: list[Relic], fortune: str) -> list[Relic]:
    """Return relics belonging to this Fortune, sorted by slug."""
    filtered = [r for r in relics if r.fortune == fortune]
    filtered.sort(key=lambda r: r.slug)
    return filtered


def neighbors_in_fortune(
    relics: list[Relic],
    slug: str,
) -> tuple[Relic | None, Relic | None]:
    """Return (previous, next) relics in the same Fortune.

    Wraps around at the ends so the user can cycle through a Fortune's relics.
    Returns (None, None) if the relic is the only one in its Fortune, or if
    the slug is not found.
    """
    target = find_relic_by_slug(relics, slug)
    if target is None:
        return (None, None)

    same_fortune = relics_for_fortune(relics, target.fortune)
    if len(same_fortune) <= 1:
        return (None, None)

    idx = same_fortune.index(target)
    prev_idx = (idx - 1) % len(same_fortune)
    next_idx = (idx + 1) % len(same_fortune)
    return (same_fortune[prev_idx], same_fortune[next_idx])
