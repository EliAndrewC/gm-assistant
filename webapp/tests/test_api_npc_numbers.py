"""Feature 226: `POST /api/npc-numbers`, the character-sheet app's backport route."""

from __future__ import annotations

import http.cookies
import json
from types import SimpleNamespace
from typing import Any

import cherrypy
import pytest

from l7r.app import NamesApi

ROSTER = [{'id': '7', 'name': 'Tsuruchi Kyoma', 'character_url': 'https://op/kyoma'}]


class Portal:
    def __init__(self) -> None:
        self.notes = 'NPC numbers:\n- Air 4\n- sincerity 3'
        self.calls: list[str] = []

    def characters(self) -> list[dict[str, str]]:
        self.calls.append('characters')
        return ROSTER

    def get_body(self, char_id: str) -> dict[str, str]:
        self.calls.append('get_body')
        return {'game_master_info': self.notes}

    def update(self, char_id: str, **fields: Any) -> None:
        self.calls.append('update')
        self.notes = fields['game_master_info']


@pytest.fixture
def portal() -> Portal:
    cherrypy.request.headers = {}
    cherrypy.response.headers = {}
    cherrypy.response.cookie = http.cookies.SimpleCookie()
    cherrypy.response.status = 200
    return Portal()


def _post(
    portal: Portal,
    body: object,
    *,
    auth: str | None = 'Bearer s3cret',
    method: str = 'POST',
    token: str = 's3cret',
) -> tuple[int, dict[str, Any]]:
    api = NamesApi(
        lambda: token,
        {'characters': portal.characters, 'get_body': portal.get_body, 'update': portal.update},
    )
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    cherrypy.request.headers = {} if auth is None else {'Authorization': auth}
    cherrypy.request.method = method
    cherrypy.request.body = SimpleNamespace(read=lambda: raw)
    out = api.npc_numbers()
    assert cherrypy.response.headers['Content-Type'] == 'application/json'
    return int(str(cherrypy.response.status).split()[0]), json.loads(out)


def test_a_build_is_written_and_the_answer_says_what_changed(
    portal: Portal, monkeypatch: pytest.MonkeyPatch
) -> None:
    logged: list[str] = []
    monkeypatch.setattr(cherrypy, 'log', lambda msg, *a, **k: logged.append(msg))
    status, answer = _post(
        portal, {'name': 'Kyoma', 'stats': {'Air': 4, 'Earth': 3, 'sincerity': 3}, 'sheet_id': 41}
    )
    assert status == 200
    assert answer['status'] == 'written'
    assert answer['message'] == 'Tsuruchi Kyoma: added Earth 3; 2 unchanged'
    assert portal.notes == 'NPC numbers:\n- Air 4\n- Earth 3\n- sincerity 3'
    assert logged == ['npc-numbers: sheet 41 written: Tsuruchi Kyoma: added Earth 3; 2 unchanged']


def test_401_and_503_come_before_the_body_or_obsidian_portal(portal: Portal) -> None:
    assert _post(portal, b'not json', auth=None)[0] == 401
    assert _post(portal, b'not json', auth='Bearer wrong')[0] == 401
    assert cherrypy.response.headers['WWW-Authenticate'] == 'Bearer'
    assert _post(portal, b'not json', token='')[0] == 503
    assert portal.calls == []


def test_only_post(portal: Portal) -> None:
    status, answer = _post(portal, {'name': 'Kyoma', 'stats': {'Air': 4}}, method='GET')
    assert (status, answer['error']) == (405, 'POST the NPC as JSON')
    assert cherrypy.response.headers['Allow'] == 'POST'
    assert portal.calls == []


@pytest.mark.parametrize(
    ('body', 'error'),
    [
        (b'{', 'the body is not JSON'),
        (b'', 'the body must be a JSON object with "name" and "stats"'),
        ([1], 'the body must be a JSON object with "name" and "stats"'),
        ({'name': 'Kyoma', 'stats': {'Air': 4}, 'xp': 3}, 'unknown fields: xp'),
        ({'name': ' ', 'stats': {'Air': 4}}, '"name" must be the NPC\'s name'),
        ({'name': 'Kyoma', 'stats': {}}, '"stats" must be an object of stat names to ranks'),
        ({'name': 'Kyoma', 'stats': {'Air': 9}}, 'Air must be a whole number from 0 to 6'),
    ],
)
def test_a_broken_request_is_a_400_before_obsidian_portal(
    portal: Portal, body: object, error: str
) -> None:
    status, answer = _post(portal, body)
    assert (status, answer['error']) == (400, error)
    assert portal.calls == []


def test_without_a_portal_it_writes_through_chargen_op() -> None:
    from chargen import op

    api = NamesApi(lambda: 's3cret')
    calls = api._portal_calls()
    assert calls == {
        'characters': op.existing_characters,
        'get_body': op.get_character_body,
        'update': op.update_character,
    }
