"""Tests for the ruling-house rank bonus.

At Deputy Minister (rank 9) and above, the main line of a ruling house outranks
its nominal office: +1.0 for the ruling house of an ordinary family, +2.0 for
the ruling house of a clan's ruling family (and all Imperial families). Below
rank 9, and for vassal/cadet houses, there is no bump.
"""

from __future__ import annotations

from typing import Any

import pytest

import l7r  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen.character import Samurai

_Samurai: Any = Samurai


def _rank_set(*, n: int = 200, **kw: Any) -> set[float]:
    return {_Samurai(**kw).rank for _ in range(n)}


def test_clan_ruling_family_main_line_gets_plus_two() -> None:
    # Doji is the Crane ruling family and has no vassal houses -> house=''.
    assert _rank_set(clan='crane', family='doji', base_rank=10) == {12.0, 12.5}


def test_clan_ruling_family_daimyo_becomes_clan_daimyo() -> None:
    # A house daimyo (12) of a clan's ruling family is bumped to Clan Daimyo (14).
    assert _rank_set(clan='crab', family='hida', house='hida', base_rank=12) == {14.0, 14.5}


def test_ordinary_family_main_line_gets_plus_one() -> None:
    # Kakita is a non-ruling Crane family; its main line gets +1.
    assert _rank_set(clan='crane', family='kakita', base_rank=9) == {10.0, 10.5}


def test_imperial_family_always_gets_plus_two() -> None:
    assert _rank_set(clan='imperial', family='seppun', base_rank=9) == {11.0, 11.5}


def test_vassal_house_gets_no_bonus() -> None:
    # A Reiji (vassal) house Hida is not the family's main line: no bump.
    assert _rank_set(clan='crab', family='hida', house='reiji', lineage='reiji', base_rank=10) == {
        10.0,
        10.5,
    }


@pytest.mark.parametrize(
    ('clan', 'family'),
    [('fox', 'kitsune'), ('wasp', 'tsuruchi'), ('sparrow', 'suzume')],
)
def test_minor_clan_ruling_family_gets_no_bonus(clan: str, family: str) -> None:
    # Minor clans get no bump, even though their sole family rules the clan.
    assert _rank_set(clan=clan, family=family, base_rank=10) == {10.0, 10.5}


def test_no_bonus_below_deputy_minister() -> None:
    # Governors (rank 8) and below are unchanged, even in a ruling family.
    assert _rank_set(clan='crab', family='hida', house='hida', base_rank=8) == {8.0, 8.5}
    assert _rank_set(clan='crane', family='doji', base_rank=5) == {5.0, 5.5}


def test_explicit_ruling_house_bonus_matches_family_table() -> None:
    # Passing house == family is the ruling house regardless of config presence.
    assert _rank_set(clan='crab', family='hida', house='hida', base_rank=10) == {12.0, 12.5}


def test_hida_main_line_is_generatable() -> None:
    # The Hida ruling house is in the family table, so a random Hida at Minister
    # rank reaches the +2 main-line rank (and sometimes the Reiji vassal house).
    ranks = {_Samurai(clan='crab', family='hida', base_rank=10).rank for _ in range(400)}
    assert ranks & {12.0, 12.5}  # main-line +2 occurs
    assert ranks & {10.0, 10.5}  # Reiji vassal (no bonus) also occurs


def test_rank_never_exceeds_fifteen() -> None:
    for _ in range(200):
        assert _Samurai(clan='crab', family='hida', house='hida', base_rank=14).rank <= 15.0
