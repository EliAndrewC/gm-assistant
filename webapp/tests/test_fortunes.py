"""Tests for l7r.fortunes — Fortune and Clan registries."""

import pytest

from l7r.fortunes import CLANS, FORTUNES, clan_label


def test_seven_major_fortunes_present() -> None:
    expected = {'benten', 'bishamon', 'daikoku', 'ebisu', 'fukurokujin', 'hotei', 'jurojin'}
    assert set(FORTUNES.keys()) == expected


@pytest.mark.parametrize(
    ('slug', 'name', 'kanji'),
    [
        ('benten', 'Benten', '弁天'),
        ('bishamon', 'Bishamon', '毘沙門'),
        ('daikoku', 'Daikoku', '大黒'),
        ('ebisu', 'Ebisu', '恵比寿'),
        ('fukurokujin', 'Fukurokujin', '福禄寿'),
        ('hotei', 'Hotei', '布袋'),
        ('jurojin', 'Jurojin', '寿老人'),
    ],
)
def test_fortune_fields(slug: str, name: str, kanji: str) -> None:
    fortune = FORTUNES[slug]
    assert fortune.slug == slug
    assert fortune.name == name
    assert fortune.kanji == kanji
    assert fortune.domain.startswith('Fortune of')


def test_seven_great_clans_plus_minor_clans_and_any() -> None:
    assert 'any' in CLANS
    for great_clan in ('crab', 'crane', 'dragon', 'lion', 'phoenix', 'scorpion', 'unicorn'):
        assert great_clan in CLANS
    for minor_clan in ('fox', 'mantis', 'sparrow', 'wasp'):
        assert minor_clan in CLANS


def test_clan_label_returns_display_string() -> None:
    assert clan_label('crab') == 'Crab'
    assert clan_label('any') == 'Anywhere'


def test_clan_label_falls_back_to_capitalized_slug_for_unknown() -> None:
    assert clan_label('mystery') == 'Mystery'
