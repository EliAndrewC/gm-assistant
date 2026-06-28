"""Tests for Samurai government-posting tags driven by the Rank dropdown.

A samurai's rank is seniority, not job, so the Rank dropdown lets the GM pick an
actual posting (Unposted / Yoriki / Magistrate / Clerk) that overrides the
default rank designator when generating tags.
"""

from __future__ import annotations

from typing import Any

import pytest

import l7r  # noqa: F401  -- force l7r to load first (chargen<->l7r circular import)
from chargen import constants as c
from chargen.character import Samurai

# chargen is on the Principle X grace period (untyped to mypy); cast the class
# to Any so constructing it isn't a no-untyped-call under strict.
_Samurai: Any = Samurai


def _tags(post: str = '', ministry: str = '', base_rank: int = 8) -> list[str]:
    tags: list[str] = _Samurai(base_rank=base_rank, post=post, ministry=ministry).tags
    return tags


def test_default_designator_tag() -> None:
    # No posting chosen: the rank designator (Governor at rank 8) is tagged.
    assert 'Governor' in _tags(base_rank=8)


def test_unposted_has_no_posting_tag() -> None:
    tags = _tags(post='unposted', base_rank=8)
    assert 'Governor' not in tags
    assert not ({'Yoriki', 'Clerk', 'Magistrate'} & set(tags))


def test_magistrate_defaults_to_ministry_of_justice() -> None:
    tags = _tags(post='magistrate', base_rank=8)
    assert 'Magistrate' in tags
    assert 'Ministry of Justice' in tags
    assert 'Governor' not in tags  # posting replaces the designator


def test_yoriki_carries_its_ministry() -> None:
    tags = _tags(post='yoriki', ministry='Ministry of War', base_rank=8)
    assert 'Yoriki' in tags
    assert 'Ministry of War' in tags
    assert 'Governor' not in tags


def test_clerk_carries_its_ministry() -> None:
    tags = _tags(post='clerk', ministry='Ministry of Revenue', base_rank=10)
    assert 'Clerk' in tags
    assert 'Ministry of Revenue' in tags
    assert 'Minister' not in tags


def test_unknown_ministry_is_ignored() -> None:
    tags = _tags(post='clerk', ministry='Ministry of Nonsense', base_rank=8)
    assert 'Clerk' in tags
    assert 'Ministry of Nonsense' not in tags


@pytest.mark.parametrize('ministry', c.MINISTRIES)
def test_every_ministry_is_accepted(ministry: str) -> None:
    assert ministry in _tags(post='yoriki', ministry=ministry, base_rank=8)


@pytest.mark.parametrize('base_rank', [3, 4])
def test_magistrate_default_ranks(base_rank: int) -> None:
    # Ranks 3 and 4 default to the Magistrate posting (designator is
    # "Magistrate"), even with no explicit post - e.g. random or roster
    # generation.
    tags = _tags(base_rank=base_rank)
    assert 'Magistrate' in tags
    assert 'Ministry of Justice' in tags


@pytest.mark.parametrize('base_rank', [3, 4])
def test_magistrate_default_ranks_can_be_overridden(base_rank: int) -> None:
    tags = _tags(post='clerk', ministry='Ministry of Works', base_rank=base_rank)
    assert 'Clerk' in tags
    assert 'Ministry of Works' in tags
    assert 'Magistrate' not in tags  # posting replaces the magistrate default
    tags_unposted = _tags(post='unposted', base_rank=base_rank)
    assert 'Magistrate' not in tags_unposted
