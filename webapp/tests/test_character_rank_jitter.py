"""Tests for Samurai rank/recognition jitter.

Holding a rank's named office (post == '') pins the rank to its lower (x.0) or
upper (x.5) half, 50/50. A lesser posting (clerk/yoriki/magistrate/unposted)
keeps the wider jitter, up to a full rank either way. Recognition varies up to
2.0 around the resolved rank, clamped to [1, 15].
"""

from __future__ import annotations

from typing import Any

import pytest

import l7r  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen.character import Samurai

_Samurai: Any = Samurai
# A vassal house (Reiji), so the ruling-house rank bonus never applies and
# these tests isolate the jitter itself.
BASE = {'clan': 'crab', 'family': 'hida', 'house': 'reiji', 'lineage': 'reiji'}


def _ranks(*, base_rank: int, post: str = '', n: int = 300) -> set[float]:
    return {_Samurai(**BASE, base_rank=base_rank, post=post).rank for _ in range(n)}


@pytest.mark.parametrize('base_rank', [5, 8, 11])
def test_named_office_is_only_lower_or_upper_half(base_rank: int) -> None:
    assert _ranks(base_rank=base_rank) == {float(base_rank), base_rank + 0.5}


@pytest.mark.parametrize('base_rank', [3, 4])
def test_low_rank_magistrate_default_uses_wider_jitter(base_rank: int) -> None:
    # The low rank-3/4 "Magistrate" designators are street magistrates, not a
    # senior office, so they keep the wider jitter even with no posting.
    observed = _ranks(base_rank=base_rank, n=600)
    assert observed <= {
        base_rank - 1.0,
        base_rank - 0.5,
        float(base_rank),
        base_rank + 0.5,
        base_rank + 1.0,
    }
    assert observed - {float(base_rank), base_rank + 0.5}  # wider than a named office


def test_posting_keeps_wider_jitter() -> None:
    observed = _ranks(base_rank=5, post='clerk', n=600)
    assert observed <= {4.0, 4.5, 5.0, 5.5, 6.0}  # within a full rank either way
    assert observed - {5.0, 5.5}  # genuinely wider than the named-office case


@pytest.mark.parametrize('post', ['clerk', 'yoriki', 'magistrate', 'unposted'])
def test_all_postings_use_wider_jitter(post: str) -> None:
    assert _ranks(base_rank=7, post=post, n=400) <= {6.0, 6.5, 7.0, 7.5, 8.0}


def test_recognition_within_two_of_rank() -> None:
    for _ in range(500):
        s = _Samurai(**BASE, base_rank=8)
        assert abs(s.recognition - s.rank) <= 2.0
        assert 1 <= s.recognition <= 15


def test_recognition_clamped_to_scale_bounds() -> None:
    # Low rank cannot drop below 1; high rank cannot exceed 15.
    assert all(_Samurai(**BASE, base_rank=2).recognition >= 1 for _ in range(200))
    assert all(_Samurai(**BASE, base_rank=11).recognition <= 15 for _ in range(200))


def test_recognition_uses_the_full_two_point_spread() -> None:
    # Over many rolls a mid-rank character should reach near both +2 and -2.
    deltas = set()
    for _ in range(800):
        s = _Samurai(**BASE, base_rank=8)
        deltas.add(s.recognition - s.rank)
    assert max(deltas) >= 1.5
    assert min(deltas) <= -1.5
