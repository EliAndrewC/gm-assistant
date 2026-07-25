"""Tests for Samurai location derivation and the Location tag.

A House may define `[locations]` (capital + provinces) and mark lineages as
provincial via `[provincial_lineages]`. The Location dropdown's auto-default,
mirrored here on the backend, is: explicit choice wins; else above Rank 8 ->
capital; else a provincial lineage at Rank <=8 -> its province; else blank.
The chosen location is tagged; the provincial/cosmopolitan distinction is not.
"""

from __future__ import annotations

from typing import Any

import pytest

import l7r  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen.character import Samurai

_Samurai: Any = Samurai

# All Fox lineages live under clan=fox, family=kitsune, house=kitsune.
FOX = {'clan': 'fox', 'family': 'kitsune', 'house': 'kitsune'}


def _make(**kw: Any) -> Any:
    return _Samurai(**FOX, **kw)


def test_provincial_lineage_at_or_below_rank_8_gets_its_province() -> None:
    for rank in (3, 5, 8):
        char = _make(lineage='nanke', base_rank=rank)
        assert char.location == 'Minami province'
        assert 'Minami province' in char.tags


def test_provincial_lineage_above_rank_8_gets_the_capital() -> None:
    char = _make(lineage='nanke', base_rank=9)
    assert char.location == 'Shinden Kitsune'
    assert 'Shinden Kitsune' in char.tags
    assert 'Minami province' not in char.tags


@pytest.mark.parametrize(
    ('lineage', 'province'),
    [
        ('toke', 'Higashi province'),
        ('hokke', 'Kita province'),
        ('saike', 'Nishi province'),
        ('nanke', 'Minami province'),
    ],
)
def test_each_provincial_lineage_maps_to_its_province(lineage: str, province: str) -> None:
    assert _make(lineage=lineage, base_rank=6).location == province


def test_cosmopolitan_lineage_at_or_below_rank_8_is_blank() -> None:
    char = _make(lineage='kitsune', base_rank=5)
    assert char.location == ''
    assert not any('province' in t.lower() or t == 'Shinden Kitsune' for t in char.tags)


def test_cosmopolitan_lineage_above_rank_8_gets_the_capital() -> None:
    assert _make(lineage='kitsune', base_rank=10).location == 'Shinden Kitsune'


def test_explicit_location_overrides_the_default() -> None:
    # Rank 9 would auto-derive the capital; the explicit choice wins.
    char = _make(lineage='nanke', base_rank=9, location='Higashi province')
    assert char.location == 'Higashi province'
    assert 'Higashi province' in char.tags
    assert 'Shinden Kitsune' not in char.tags


def test_provincial_annotation_is_never_a_tag() -> None:
    char = _make(lineage='nanke', base_rank=5)
    assert 'provincial' not in char.tags
    assert 'cosmopolitan' not in char.tags


REIJI = {'clan': 'crab', 'family': 'hida', 'house': 'reiji'}


@pytest.mark.parametrize(
    ('lineage', 'province'),
    [
        ('noriko', 'Nagahara province'),
        ('obana', 'Mutsu province'),
        ('sugino', 'Kuroiwa province'),
    ],
)
def test_reiji_provincial_lineages(lineage: str, province: str) -> None:
    assert _Samurai(**REIJI, lineage=lineage, base_rank=5).location == province


def test_reiji_ruling_lineage_is_cosmopolitan() -> None:
    assert _Samurai(**REIJI, lineage='reiji', base_rank=5).location == ''
    assert _Samurai(**REIJI, lineage='reiji', base_rank=10).location == 'Shiro Reiji'


def test_reiji_is_an_all_dynasty_domain() -> None:
    """Every Reiji province is a dynasty province.

    The Reiji domain is deliberately unusual (see l7r.md "The Reiji Domain"):
    the ruling lineage administers the capital and nothing else, and each of
    the other five lineages holds one province, so the domain has no
    cosmopolitan lineages and no stewardship provinces at all.
    """
    from chargen import config

    lineages = config['house']['reiji']
    provincial = config['provincial_lineages']['reiji']
    provinces = config['locations']['reiji']['provinces']

    assert len(lineages) == 6  # reiji + five provincial lineages
    # Every lineage but the ruling one is provincial - no cosmopolitan lineages.
    assert set(lineages) - {'reiji'} == set(provincial)
    # ...and between them they cover every province exactly once.
    assert sorted(provincial.values()) == sorted(provinces)
    # The five provincial lineages share one weight; the ruling lineage is bigger.
    provincial_weights = {lineages[name] for name in provincial}
    assert len(provincial_weights) == 1
    assert lineages['reiji'] > provincial_weights.pop()


def test_house_without_location_config_has_no_location() -> None:
    # A House with no [locations] entry generates fine with no location tag.
    char = _Samurai(clan='lion', family='matsu', house='zenji', lineage='zenji', base_rank=8)
    assert char.location == ''
    assert not any('province' in t.lower() for t in char.tags)
