"""Place names in use per scale (chargen.placeuse)."""

import json
from pathlib import Path

from chargen.placeuse import (
    from_config,
    from_tags,
    lineage_names,
    normalize,
    used_lineage_names,
    used_place_names,
)

CACHE: dict[str, dict[str, object]] = {
    'a': {
        'name': 'Otsuki',
        'tags': ['Nagahara province', 'Hayakawa county', 'Hoshigaoka village', 'Reiji domain'],
    },
    'b': {'name': 'X', 'tags': ['Crab Clan', 'Mizu-no-sato Hamlet', 'daimyo']},
    'c': {'name': 'Y', 'tags': 'not a list'},
    'd': {'name': 'Z', 'tags': ['Obana Lineage', 'Wasp clan']},
}
CONFIG = {
    'locations': {
        'reiji': {'capital': 'Shiro Reiji', 'provinces': ['Nagahara province', 'Mutsu province']},
        'odd': {'provinces': 'Solo province'},
        'bare': {'provinces': ['Kasugai']},
        'junk': 'not a section',
    },
    'family': {'hida': {'hida': 20, 'reiji': 5}},
    'house': {'reiji': {'reiji': 50, 'noriko': 25}, 'junk': 3},
    'provincial_lineages': {'reiji': {'noriko': 'Nagahara province'}},
}


def test_from_tags_by_scale() -> None:
    got = from_tags(CACHE)
    assert got['province'] == {'Nagahara'}
    assert got['county'] == {'Hayakawa'}
    assert got['village'] == {'Hoshigaoka'}
    assert got['hamlet'] == {'Mizu-no-sato'}
    assert got['domain'] == {'Reiji'}


def test_from_config_provinces() -> None:
    got = from_config(CONFIG)
    assert got['province'] == {'Nagahara', 'Mutsu', 'Solo', 'Kasugai'}
    assert got['village'] == set()
    assert from_config({})['province'] == set()


def test_used_place_names_merges_both(tmp_path: Path) -> None:
    cache = tmp_path / 'characters.json'
    cache.write_text(json.dumps(CACHE))
    got = used_place_names(cache, CONFIG)
    assert got['province'] == {'Nagahara', 'Mutsu', 'Solo', 'Kasugai'}
    assert got['hamlet'] == {'Mizu-no-sato'}


def test_used_place_names_reads_the_chargen_config(tmp_path: Path) -> None:
    got = used_place_names(tmp_path / 'missing.json')
    assert 'Nagahara' in got['province']  # development-defaults.ini [locations]


def test_lineage_names_from_tags_and_config(tmp_path: Path) -> None:
    assert lineage_names(CACHE, CONFIG) == {'Obana', 'Hida', 'Reiji', 'Noriko', 'Junk'}
    assert lineage_names({}, {'house': 'not a section'}) == frozenset()
    cache = tmp_path / 'characters.json'
    cache.write_text(json.dumps(CACHE))
    assert 'Obana' in used_lineage_names(cache, CONFIG)
    real = used_lineage_names(tmp_path / 'missing.json')  # development-defaults.ini
    assert {'Obana', 'Tsuruchi', 'Kyoma', 'Toke'} <= real


def test_normalize() -> None:
    assert normalize('Mizu-no-sato') == normalize('Mizu no Sato') == 'mizunosato'
