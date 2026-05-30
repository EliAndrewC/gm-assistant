"""Tests for l7r.fortunes — Fortune and Clan registries."""

import pytest

from l7r.fortunes import CLANS, FORTUNES, clan_label, fortunes_in_category


def test_seven_major_fortunes_present() -> None:
    majors = {slug for slug, f in FORTUNES.items() if f.category == 'major'}
    expected = {'benten', 'bishamon', 'daikoku', 'ebisu', 'fukurokujin', 'hotei', 'jurojin'}
    assert majors == expected


def test_inari_is_a_minor_fortune() -> None:
    assert 'inari' in FORTUNES
    assert FORTUNES['inari'].category == 'minor'
    assert FORTUNES['inari'].name == 'Inari'
    assert FORTUNES['inari'].kanji == '稲荷'


def test_fortunes_in_category_partitions_correctly() -> None:
    majors = fortunes_in_category('major')
    minors = fortunes_in_category('minor')
    assert set(majors.keys()) | set(minors.keys()) == set(FORTUNES.keys())
    assert set(majors.keys()) & set(minors.keys()) == set()
    assert 'inari' in minors
    assert 'benten' in majors


@pytest.mark.parametrize(
    ('slug', 'name', 'kanji', 'category'),
    [
        ('benten', 'Benten', '弁天', 'major'),
        ('bishamon', 'Bishamon', '毘沙門', 'major'),
        ('daikoku', 'Daikoku', '大黒', 'major'),
        ('ebisu', 'Ebisu', '恵比寿', 'major'),
        ('fukurokujin', 'Fukurokujin', '福禄寿', 'major'),
        ('hotei', 'Hotei', '布袋', 'major'),
        ('jurojin', 'Jurojin', '寿老人', 'major'),
        ('inari', 'Inari', '稲荷', 'minor'),
    ],
)
def test_fortune_fields(slug: str, name: str, kanji: str, category: str) -> None:
    fortune = FORTUNES[slug]
    assert fortune.slug == slug
    assert fortune.name == name
    assert fortune.kanji == kanji
    assert fortune.category == category
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
