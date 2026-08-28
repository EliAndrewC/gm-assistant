"""The character-sheet client.

The endpoints it wraps DO NOT EXIST YET, so the most important tests here are the
ones proving that their absence degrades cleanly rather than raising.
"""

from __future__ import annotations

import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from l7r.repl.rolls import sheet

SINCE = datetime(2026, 8, 12, 1, 0, tzinfo=UTC)

ROLLS_PAYLOAD = {
    'rolls': [
        {
            'id': 4711,
            'character_name': 'Bayushi Sadakichi',
            'label': 'Etiquette',
            'total': 38,
            'actor_discord_id': '123',
            'created_at': '2026-08-12T01:53:39+00:00',
            'skill_rank': 3,
        }
    ]
}

CHARACTERS_PAYLOAD = {
    'characters': [
        {
            'id': 17,
            'name': 'Bayushi Sadakichi',
            'owner_discord_id': '123',
            'gaming_group_name': 'Tuesday Group',
            'skills': {'Etiquette': 3, 'investigation': 2},
        },
        {'id': 18, 'name': 'Orphan', 'owner_discord_id': ''},
    ]
}


def token_file(tmp_path: Path, body: str) -> Path:
    path = tmp_path / 'secrets.ini'
    path.write_text(body)
    return path


class TestQueryToken:
    def test_reads_the_token(self, tmp_path: Path) -> None:
        path = token_file(tmp_path, '[character_sheet]\nroll_query_token = t0ken\n')
        assert sheet.query_token(path) == 't0ken'

    def test_absent_is_empty(self, tmp_path: Path) -> None:
        assert sheet.query_token(token_file(tmp_path, '[other]\nx = 1\n')) == ''


class TestRecordedRolls:
    def test_parses_a_good_response(self) -> None:
        result = sheet.recorded_rolls(SINCE, token='t', get=lambda *a: ROLLS_PAYLOAD)
        assert result.available
        (roll,) = result.rolls
        assert roll.character == 'Bayushi Sadakichi'
        assert roll.skill == 'etiquette'
        assert roll.total == 38
        assert roll.rank == 3
        assert roll.actor_discord_id == '123'

    def test_derives_the_skill_from_a_roll_key(self) -> None:
        payload = {
            'rolls': [
                {
                    'roll_key': 'skill:investigation',
                    'total': 30,
                    'created_at': '2026-08-12T01:00:00+00:00',
                }
            ]
        }
        result = sheet.recorded_rolls(SINCE, token='t', get=lambda *a: payload)
        assert result.rolls[0].skill == 'investigation'

    def test_a_missing_rank_stays_unknown(self) -> None:
        payload = {
            'rolls': [
                {
                    'label': 'Etiquette',
                    'total': 30,
                    'skill_rank': None,
                    'created_at': '2026-08-12T01:00:00+00:00',
                }
            ]
        }
        result = sheet.recorded_rolls(SINCE, token='t', get=lambda *a: payload)
        assert result.rolls[0].rank is None

    def test_no_token_degrades_with_a_reason(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sheet, 'SECRETS', token_file(tmp_path, '[x]\ny = 1\n'))
        result = sheet.recorded_rolls(SINCE)
        assert not result.available
        assert 'roll_query_token' in result.reason
        assert result.rolls == ()

    def test_a_404_says_the_endpoint_is_not_built_yet(self) -> None:
        def missing(*args: Any) -> Any:
            raise urllib.error.HTTPError('u', 404, 'Not Found', {}, None)  # type: ignore[arg-type]

        result = sheet.recorded_rolls(SINCE, token='t', get=missing)
        assert not result.available
        assert 'not built yet' in result.reason
        assert result.rolls == ()

    def test_another_status_is_reported(self) -> None:
        def boom(*args: Any) -> Any:
            raise urllib.error.HTTPError('u', 500, 'Server Error', {}, None)  # type: ignore[arg-type]

        assert '500' in sheet.recorded_rolls(SINCE, token='t', get=boom).reason

    def test_a_transport_failure_is_reported(self) -> None:
        def boom(*args: Any) -> Any:
            raise urllib.error.URLError('refused')

        result = sheet.recorded_rolls(SINCE, token='t', get=boom)
        assert 'could not reach' in result.reason

    def test_malformed_json_degrades_rather_than_raising(self) -> None:
        def boom(*args: Any) -> Any:
            raise ValueError('not json')

        assert not sheet.recorded_rolls(SINCE, token='t', get=boom).available


class TestCanonicalSkill:
    """The ring suffix is display, not identity - and carrying it through silently
    defeated the GM's Etiquette cap. Measured against the live endpoint."""

    @pytest.mark.parametrize(
        ('label', 'expected'),
        [
            ('etiquette (air)', 'etiquette'),
            ('underworld (water)', 'underworld'),
            ('commune (air)', 'commune'),
            ('attack', 'attack'),
            ('skill:investigation', 'investigation'),
            ('knack:discern_honor', 'discern_honor'),
            ('Etiquette (Air)', 'etiquette'),
            ('', ''),
        ],
    )
    def test_reduces_to_a_bare_skill_name(self, label: str, expected: str) -> None:
        assert sheet.canonical_skill(label) == expected

    def test_the_cap_fires_on_a_recorded_roll(self) -> None:
        from l7r.repl.rolls.rules import record

        payload = {
            'rolls': [
                {
                    'label': 'etiquette (air)',
                    'total': 68,
                    'created_at': '2026-08-12T01:00:00+00:00',
                }
            ]
        }
        (roll,) = sheet.recorded_rolls(SINCE, token='t', get=lambda *a: payload).rolls
        assert record(roll.total, roll.skill) == 40, 'the GM cap must fire on recorded rolls too'


class TestCharacters:
    def test_keys_by_discord_id_and_lowercases_skills(self) -> None:
        result = sheet.characters(token='t', get=lambda *a: CHARACTERS_PAYLOAD)
        assert set(result.characters) == {'123'}
        who = result.characters['123']
        assert who.name == 'Bayushi Sadakichi'
        assert who.group == 'Tuesday Group'
        assert who.skills == {'etiquette': 3, 'investigation': 2}

    def test_skips_characters_with_no_owner(self) -> None:
        result = sheet.characters(token='t', get=lambda *a: CHARACTERS_PAYLOAD)
        assert 'Orphan' not in {c.name for c in result.characters.values()}

    def test_no_token_degrades(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sheet, 'SECRETS', token_file(tmp_path, '[x]\ny = 1\n'))
        assert not sheet.characters().available

    def test_a_failure_degrades(self) -> None:
        def boom(*args: Any) -> Any:
            raise urllib.error.HTTPError('u', 404, 'Not Found', {}, None)  # type: ignore[arg-type]

        result = sheet.characters(token='t', get=boom)
        assert result.characters == {}
        assert not result.available


class TestGet:
    def test_sends_a_bearer_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        class Fake:
            def read(self) -> bytes:
                return b'{"ok": true}'

            def __enter__(self) -> Fake:
                return self

            def __exit__(self, *args: object) -> None:
                return None

        def fake_urlopen(request: Any, timeout: float = 0) -> Any:
            captured['auth'] = request.get_header('Authorization')
            return Fake()

        monkeypatch.setattr(urllib.request, 'urlopen', fake_urlopen)
        assert sheet._get('https://x', 'tok', 1.0) == {'ok': True}
        assert captured['auth'] == 'Bearer tok'


def test_an_empty_result_is_unavailable_only_when_a_reason_is_set() -> None:
    assert sheet.SheetResult().available
    assert not sheet.SheetResult(reason='down').available
