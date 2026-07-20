"""Behavior tests for ``chargen.opsynth`` (pure logic, 100% covered).

No network and no OP transport mocks - the tagline parse runs against a saved
real-structure HTML fixture; every other function is pure.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from chargen import opsynth

_PAGE = (Path(__file__).resolve().parent / 'fixtures' / 'op_character_page.html').read_text(
    encoding='utf-8'
)

_CAST: list[dict[str, object]] = [
    {'id': '1', 'slug': 'daidoji-no-etsuko-jitsuyo', 'name': 'Daidoji no Etsuko Jitsuyo'},
    {'id': '2', 'slug': 'tsuruchi-kyoma', 'name': 'Tsuruchi Kyoma'},
    {'id': '3', 'slug': 'doji-ami', 'name': 'Doji Ami'},
]


# --- match_character ---


@pytest.mark.parametrize(
    'query',
    ['Daidoji Jitsuyo', 'jitsuyo', 'DAIDOJI   jitsuyo', 'Etsuko'],
)
def test_match_character_resolves_partial_or_approximate_name(query: str) -> None:
    result = opsynth.match_character(query, _CAST)
    assert result.kind == 'unique'
    assert result.character['name'] == 'Daidoji no Etsuko Jitsuyo'


def test_match_character_ambiguous_lists_all_candidates() -> None:
    # "Tsuruchi" is not present; use a token shared by two names.
    cast = [
        {'id': '1', 'name': 'Doji Ami'},
        {'id': '2', 'name': 'Doji Ayako'},
    ]
    result = opsynth.match_character('Doji', cast)
    assert result.kind == 'ambiguous'
    assert len(result.matches) == 2


def test_match_character_no_match_offers_nearest_names() -> None:
    result = opsynth.match_character('Bayushi Zzzz', _CAST)
    assert result.kind == 'none'
    assert result.matches == ()
    assert len(result.nearest) >= 1


def test_match_character_empty_query_is_no_match() -> None:
    assert opsynth.match_character('   ', _CAST).kind == 'none'


def test_match_result_character_raises_when_not_unique() -> None:
    with pytest.raises(ValueError, match='no unique match'):
        _ = opsynth.MatchResult('none').character


# --- infer_caste ---


@pytest.mark.parametrize(
    ('tags', 'gm_info', 'expected'),
    [
        (['Order of Jurojin'], 'Country Monk', 'Monk'),
        (['Crab Clan'], 'a sohei of the mountain', 'Monk'),
        (['MONASTERY guest'], '', 'Monk'),
        (['Farmer'], 'poor ashigaru levy', 'Peasant'),
        (['Crane Clan', 'Daidoji Family'], 'Vain\nProud', 'Samurai'),
        ([], '', 'Samurai'),
        (['Order of Something', 'peasant'], '', 'Monk'),  # Monk precedence over Peasant
    ],
)
def test_infer_caste(tags: list[str], gm_info: str, expected: str) -> None:
    assert opsynth.infer_caste(tags, gm_info) == expected


# --- parse_tagline ---


def test_parse_tagline_reads_populated_body_tagline_not_empty_banner() -> None:
    assert opsynth.parse_tagline(_PAGE) == 'drinking companion of Kyoma'


@pytest.mark.parametrize(
    'html',
    ['<div>no tagline here</div>', "<h5 class='tagline'></h5>", ''],
)
def test_parse_tagline_returns_empty_when_absent_or_blank(html: str) -> None:
    assert opsynth.parse_tagline(html) == ''


# --- build_synthesis_character ---


def test_build_synthesis_character_maps_op_body() -> None:
    body: dict[str, object] = {
        'name': 'Daidoji no Etsuko Jitsuyo',
        'tags': ['Crane Clan'],
        'description': 'public prose',
        'game_master_info': 'XP: 160',
    }
    out = opsynth.build_synthesis_character(body, 'drinking companion of Kyoma')
    assert out == {
        'full_name': 'Daidoji no Etsuko Jitsuyo',
        'tags': ['Crane Clan'],
        'summary': 'drinking companion of Kyoma',
        'public': 'public prose',
        'private': 'XP: 160',
    }


def test_build_synthesis_character_coalesces_missing_fields() -> None:
    out = opsynth.build_synthesis_character({'tags': None}, '')
    assert out == {'full_name': '', 'tags': [], 'summary': '', 'public': '', 'private': ''}


# --- related_by_tagline ---


def test_related_by_tagline_finds_others_linked_to_same_npc() -> None:
    cast_names = ['Tsuruchi Kyoma', 'Doji Ami', 'Hida Tetsuo']
    cast_taglines = {
        'Doji Ami': 'sparring partner of Kyoma',
        'Hida Tetsuo': 'rival of Toturi',
    }
    related = opsynth.related_by_tagline('drinking companion of Kyoma', cast_taglines, cast_names)
    assert related == ['Doji Ami']


def test_related_by_tagline_empty_when_no_cast_member_named() -> None:
    assert (
        opsynth.related_by_tagline(
            'a lonely wanderer', {'X': 'friend of Kyoma'}, ['Tsuruchi Kyoma']
        )
        == []
    )


# --- refresh_taglines ---


def _fetch(ch: Mapping[str, object]) -> str:
    return f'tagline-for-{ch.get("id")}'


def test_refresh_taglines_fetches_new_entries() -> None:
    chars: list[dict[str, object]] = [{'id': '1', 'updated_at': 'a'}]
    cache, stats = opsynth.refresh_taglines({}, chars, _fetch)
    assert cache == {'1': {'tagline': 'tagline-for-1', 'updated_at': 'a'}}
    assert stats == {'fetched': 1, 'kept': 0, 'dropped': 0}


def test_refresh_taglines_keeps_unchanged_refetches_changed_drops_absent() -> None:
    base = {
        '1': {'tagline': 'old1', 'updated_at': 'a'},
        '2': {'tagline': 'old2', 'updated_at': 'b'},
    }
    chars: list[dict[str, object]] = [
        {'id': '1', 'updated_at': 'a'},  # unchanged -> kept
        {'id': '2', 'updated_at': 'CHANGED'},  # changed -> refetched
        {'id': '3', 'updated_at': 'c'},  # new -> fetched
        {'name': 'no id'},  # skipped
    ]
    cache, stats = opsynth.refresh_taglines(base, chars, _fetch)
    assert cache['1'] == {'tagline': 'old1', 'updated_at': 'a'}
    assert cache['2'] == {'tagline': 'tagline-for-2', 'updated_at': 'CHANGED'}
    assert cache['3'] == {'tagline': 'tagline-for-3', 'updated_at': 'c'}
    assert stats == {'fetched': 2, 'kept': 1, 'dropped': 0}  # id '2' and '3' fetched, '1' kept


# --- merge_backstory ---


def test_merge_backstory_appends_bare_prose_preserving_notes() -> None:
    out = opsynth.merge_backstory('XP: 160\nHonor: 1', 'A grounded life.')
    assert out == 'XP: 160\nHonor: 1\n\nA grounded life.'


def test_merge_backstory_into_empty_notes() -> None:
    assert opsynth.merge_backstory('', 'Prose.') == 'Prose.'


def test_merge_backstory_replaces_legacy_block_dropping_markers() -> None:
    legacy = (
        f'XP: 160\n\n{opsynth.BACKSTORY_START}\nFirst version.\n{opsynth.BACKSTORY_END}'
        '\n\nManual note added later.'
    )
    out = opsynth.merge_backstory(legacy, 'Second version.')
    assert 'Second version.' in out
    assert 'First version.' not in out
    assert opsynth.BACKSTORY_START not in out
    assert opsynth.BACKSTORY_END not in out
    assert 'XP: 160' in out
    assert 'Manual note added later.' in out


def test_merge_backstory_rerun_appends_second_copy() -> None:
    once = opsynth.merge_backstory('XP: 160', 'Prose.')
    twice = opsynth.merge_backstory(once, 'Prose.')
    assert twice == 'XP: 160\n\nProse.\n\nProse.'


# --- strip_backstory_markers ---


def test_strip_backstory_markers_unwraps_block() -> None:
    legacy = (
        f'XP: 160\n\n{opsynth.BACKSTORY_START}\nThe prose.\n{opsynth.BACKSTORY_END}\n\nManual note.'
    )
    assert opsynth.strip_backstory_markers(legacy) == 'XP: 160\n\nThe prose.\n\nManual note.'


def test_strip_backstory_markers_block_only() -> None:
    legacy = f'{opsynth.BACKSTORY_START}\nThe prose.\n{opsynth.BACKSTORY_END}'
    assert opsynth.strip_backstory_markers(legacy) == 'The prose.'


def test_strip_backstory_markers_without_markers_is_passthrough() -> None:
    assert opsynth.strip_backstory_markers('XP: 160\nplain notes') == 'XP: 160\nplain notes'


def test_strip_backstory_markers_malformed_left_untouched() -> None:
    reversed_markers = f'{opsynth.BACKSTORY_END}\noops\n{opsynth.BACKSTORY_START}'
    assert opsynth.strip_backstory_markers(reversed_markers) == reversed_markers
    start_only = f'{opsynth.BACKSTORY_START}\ndangling'
    assert opsynth.strip_backstory_markers(start_only) == start_only


def test_strip_backstory_markers_unwraps_multiple_blocks() -> None:
    legacy = (
        f'{opsynth.BACKSTORY_START}\nOne.\n{opsynth.BACKSTORY_END}\n\n'
        f'{opsynth.BACKSTORY_START}\nTwo.\n{opsynth.BACKSTORY_END}'
    )
    assert opsynth.strip_backstory_markers(legacy) == 'One.\n\nTwo.'
