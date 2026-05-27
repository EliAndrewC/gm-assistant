"""Tests for l7r.slugs — relic lookup helpers."""

from pathlib import Path

import pytest

from l7r.pool import Relic, load_relics
from l7r.slugs import (
    find_relic_by_slug,
    neighbors_in_fortune,
    relics_for_fortune,
)


@pytest.fixture
def relics(sample_pool_dir: Path) -> list[Relic]:
    return load_relics(sample_pool_dir)


def test_find_relic_by_slug_returns_match(relics: list[Relic]) -> None:
    relic = find_relic_by_slug(relics, 'sample-benten-stone')
    assert relic is not None
    assert relic.slug == 'sample-benten-stone'


def test_find_relic_by_slug_returns_none_when_missing(relics: list[Relic]) -> None:
    assert find_relic_by_slug(relics, 'no-such-slug') is None


def test_relics_for_fortune_returns_only_that_fortune(relics: list[Relic]) -> None:
    benten = relics_for_fortune(relics, 'benten')
    assert len(benten) == 2
    assert all(r.fortune == 'benten' for r in benten)


def test_relics_for_fortune_returns_empty_for_unknown_fortune(relics: list[Relic]) -> None:
    assert relics_for_fortune(relics, 'no-such-fortune') == []


def test_relics_for_fortune_is_stably_sorted(relics: list[Relic]) -> None:
    benten = relics_for_fortune(relics, 'benten')
    slugs = [r.slug for r in benten]
    assert slugs == sorted(slugs)


def test_neighbors_in_fortune_returns_prev_and_next(relics: list[Relic]) -> None:
    # benten fixtures: sample-benten-cup, sample-benten-stone (alphabetical)
    prev, nxt = neighbors_in_fortune(relics, 'sample-benten-stone')
    assert prev is not None
    assert prev.slug == 'sample-benten-cup'
    assert nxt is not None
    assert nxt.slug == 'sample-benten-cup'  # wraps with 2 items


def test_neighbors_in_fortune_wraps_at_ends(relics: list[Relic]) -> None:
    # cup is first alphabetically in benten; its prev should wrap to last (stone)
    prev, nxt = neighbors_in_fortune(relics, 'sample-benten-cup')
    assert prev is not None
    assert prev.slug == 'sample-benten-stone'
    assert nxt is not None
    assert nxt.slug == 'sample-benten-stone'


def test_neighbors_in_fortune_returns_none_for_only_item(relics: list[Relic]) -> None:
    # bishamon has only one fixture
    prev, nxt = neighbors_in_fortune(relics, 'sample-bishamon-sword')
    assert prev is None
    assert nxt is None


def test_neighbors_in_fortune_for_unknown_slug(relics: list[Relic]) -> None:
    prev, nxt = neighbors_in_fortune(relics, 'no-such-slug')
    assert prev is None
    assert nxt is None
