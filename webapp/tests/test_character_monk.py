"""Tests for Monk Order and paired-rank "seat" tags.

Each Monk is tagged with one of the 7 Fortunes of Good Luck (the Order dropdown,
random if unset) instead of a hard-coded Order of Bishamon. Ranks that pair two
roles (4: Senior Monk / Preceptor; 5: Adept Monk / Country Monk) tag the chosen
seat, or a random one of the pair if none was chosen.
"""

from __future__ import annotations

from typing import Any

import pytest

import l7r  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen import config
from chargen.character import Monk

_Monk: Any = Monk
ORDERS = config['monk_orders']


def _tags(**kw: Any) -> list[str]:
    tags: list[str] = _Monk(**kw).tags
    return tags


def test_order_is_used_when_given() -> None:
    assert _tags(base_rank=2, order='Order of Benten')[0] == 'Order of Benten'


def test_blank_order_yields_no_order_tag() -> None:
    # Unlike the other dropdowns, a blank Order is NOT randomized - it is left
    # off so the GM can hand-enter an uncommon order. A rank-2 monk with no
    # order is tagged only with its designator.
    assert _tags(base_rank=2) == ['Abbot']
    assert not any(o in _tags(base_rank=2) for o in ORDERS)


def test_custom_order_is_used_as_typed() -> None:
    # An order outside the seven (typed by the GM) is honored as-is.
    assert _tags(base_rank=2, order='Order of Inari') == ['Order of Inari', 'Abbot']


@pytest.mark.parametrize(
    ('base_rank', 'seat'),
    [(4, 'Senior Monk'), (4, 'Preceptor'), (5, 'Adept Monk'), (5, 'Country Monk')],
)
def test_paired_rank_uses_chosen_seat(base_rank: int, seat: str) -> None:
    tags = _tags(base_rank=base_rank, order='Order of Hotei', seat=seat)
    assert seat in tags
    # the combined label is never emitted as one tag
    assert not any(',' in t for t in tags)


@pytest.mark.parametrize(
    ('base_rank', 'pair'), [(4, {'Senior Monk', 'Preceptor'}), (5, {'Adept Monk', 'Country Monk'})]
)
def test_paired_rank_without_seat_picks_one_of_the_pair(base_rank: int, pair: set[str]) -> None:
    # No order tag here (blank order), so the designator is the last tag.
    seen = {_tags(base_rank=base_rank)[-1] for _ in range(200)}
    assert seen == pair


def test_single_rank_uses_its_label() -> None:
    assert 'Abbot' in _tags(base_rank=2)
    assert 'Grand Abbot' in _tags(base_rank=1)


def test_order_of_bishamon_is_not_hard_coded() -> None:
    # With a different Order chosen, Bishamon must not appear.
    assert 'Order of Bishamon' not in _tags(base_rank=3, order='Order of Jurojin')
