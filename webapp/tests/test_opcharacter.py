"""gm-assistant#4: `GET /api/op-character`, an Obsidian Portal character's raw facts."""

from __future__ import annotations

import http.cookies
import json
from typing import Any

import cherrypy
import pytest

from l7r import opcharacter
from l7r.app import NamesApi

#: Shaped like a real record (Tsuruchi Fumitake, 2026-10-26), with OP's CRLF line endings.
GM_INFO = (
    'XP: 140\r\nHonor: 2.5\r\n\r\ncontemptuous\r\nfat\r\n'
    'personally hated by an enemy - the Mantis, whom he has targeted\r\n\r\n'
    'From lowborn to "fat cat".\r\n\r\nNPC numbers:\r\n- Air 3\r\n- sincerity 5\r\n\r\n'
    'Hidden rolls:\r\n- 2026-09-19 sincerity 48'
)
DESCRIPTION = 'Kanji notes.\r\n\r\nmale Yasuki Merchant\r\n\r\nWasp Clan\r\n'
ROSTER = [
    {'id': '7', 'slug': 'tsuruchi-fumitake', 'name': 'Tsuruchi Fumitake', 'tags': ['Wasp']},
    {'id': '8', 'slug': 'tsuruchi-kyoma', 'name': 'Tsuruchi Kyoma', 'tags': []},
    {'id': '9', 'slug': 'hida-kyoma', 'name': 'Hida Kyoma', 'tags': []},
]
BODIES: dict[str, dict[str, Any]] = {
    '7': {'game_master_info': GM_INFO, 'description': DESCRIPTION, 'tags': ['Wasp', 'Yasuki']},
    '8': {'game_master_info': '', 'description': ''},
}


def _facts(ref: str, roster: list[dict[str, Any]] = ROSTER) -> dict[str, Any]:
    return opcharacter.facts(ref, characters=lambda: roster, get_body=BODIES.get)


def test_the_facts_come_back_as_written() -> None:
    assert _facts('Fumitake') == {
        'name': 'Tsuruchi Fumitake',
        'slug': 'tsuruchi-fumitake',
        'school_line': 'male Yasuki Merchant',
        'tags': ['Wasp', 'Yasuki'],
        'earned_xp': 140,
        'trait_lines': [
            'contemptuous',
            'fat',
            'personally hated by an enemy - the Mantis, whom he has targeted',
        ],
        'stat_lines': ['- Air 3', '- sincerity 5'],
    }


def test_a_url_and_a_slug_name_the_same_record() -> None:
    url = 'https://waspbountyhunters.obsidianportal.com/characters/tsuruchi-fumitake'
    assert _facts(url)['name'] == 'Tsuruchi Fumitake'
    assert _facts('tsuruchi-fumitake')['name'] == 'Tsuruchi Fumitake'


def test_missing_parts_are_null_or_empty() -> None:
    found = _facts('Tsuruchi Kyoma')
    assert found['school_line'] is None
    assert found['earned_xp'] is None
    assert found['trait_lines'] == []
    assert found['stat_lines'] == []
    assert found['tags'] == []


def test_an_ambiguous_name_lists_the_candidates_and_never_guesses() -> None:
    with pytest.raises(opcharacter.Ambiguous) as caught:
        _facts('Kyoma')
    assert caught.value.candidates == ['Tsuruchi Kyoma', 'Hida Kyoma']


@pytest.mark.parametrize(
    'ref', ['Nobody', 'https://waspbountyhunters.obsidianportal.com/characters/nobody']
)
def test_an_unknown_ref_is_not_found(ref: str) -> None:
    with pytest.raises(opcharacter.NotFound):
        _facts(ref)


def test_an_unreadable_portal_is_a_lookup_error() -> None:
    with pytest.raises(LookupError, match='could not list'):
        _facts('Fumitake', roster=[])
    with pytest.raises(LookupError, match='could not read'):
        opcharacter.facts('Fumitake', characters=lambda: ROSTER, get_body=lambda _id: None)


def test_traits_need_the_xp_header_and_stop_at_npc_numbers() -> None:
    assert opcharacter.trait_lines('just prose\nmore') == []
    assert opcharacter.trait_lines('\n\nHonor: 3.0\nWealthy\nNPC numbers:\n- Air 2') == ['Wealthy']
    assert opcharacter.trait_lines('XP: 3') == []


def test_the_npc_numbers_block_ends_at_the_text_end() -> None:
    assert opcharacter.stat_lines('NPC numbers:\n- Air 2  ') == ['- Air 2']


# --- the route -----------------------------------------------------------------------


@pytest.fixture
def api() -> NamesApi:
    cherrypy.request.headers = {}
    cherrypy.response.headers = {}
    cherrypy.response.cookie = http.cookies.SimpleCookie()
    cherrypy.response.status = 200
    return NamesApi(lambda: 's3cret', {'characters': lambda: ROSTER, 'get_body': BODIES.get})


def _get(api: NamesApi, ref: str | None, auth: str = 'Bearer s3cret') -> tuple[int, Any]:
    cherrypy.request.headers = {'Authorization': auth}
    out = api.op_character(ref=ref)
    assert cherrypy.response.headers['Content-Type'] == 'application/json'
    return int(str(cherrypy.response.status).split()[0]), json.loads(out)


def test_the_route_answers_the_facts(api: NamesApi) -> None:
    status, body = _get(api, 'Fumitake')
    assert status == 200
    assert body['earned_xp'] == 140


def test_the_route_refuses_before_reading_anything(api: NamesApi) -> None:
    status, body = _get(api, 'Fumitake', auth='Bearer wrong')
    assert status == 401


@pytest.mark.parametrize(
    ('ref', 'status'), [(None, 400), ('  ', 400), ('Nobody', 404), ('Kyoma', 409)]
)
def test_the_route_errors(api: NamesApi, ref: str | None, status: int) -> None:
    got, body = _get(api, ref)
    assert got == status
    assert body['error']
    if status == 409:
        assert body['candidates'] == ['Tsuruchi Kyoma', 'Hida Kyoma']


def test_an_unreadable_portal_is_a_502() -> None:
    cherrypy.response.headers = {}
    api = NamesApi(lambda: 's3cret', {'characters': lambda: [], 'get_body': BODIES.get})
    status, body = _get(api, 'Fumitake')
    assert status == 502
