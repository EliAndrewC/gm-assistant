"""The character-sheet roster cache (chargen.sheetroster) against a trimmed
copy of the real index page."""

import json
from pathlib import Path

import pytest

from chargen import sheetroster
from chargen.sheetroster import (
    cache_age,
    full_names,
    given_name,
    given_names,
    parse_index,
    refresh_if_stale,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'sheet-index.html'


def test_parse_index_takes_grouped_characters_only() -> None:
    names = parse_index(FIXTURE.read_text())
    assert names == ['Asako Tadashi', 'Tsuruchi Hidemasa', 'Kitsune Moriko', 'Tsuruchi Jimen']
    assert 'Loose Nobody' not in names  # the unassigned bucket has no group link
    assert parse_index('<html></html>') == []


def test_refresh_writes_and_respects_age(tmp_path: Path) -> None:
    cache = tmp_path / 'sheet.json'
    fetches = 0

    def fetch() -> str:
        nonlocal fetches
        fetches += 1
        return FIXTURE.read_text()

    assert cache_age(cache) is None
    assert refresh_if_stale(3600, cache, fetch) is True
    assert json.loads(cache.read_text())['names'][1] == 'Tsuruchi Hidemasa'
    assert refresh_if_stale(3600, cache, fetch) is False
    assert fetches == 1
    assert refresh_if_stale(0.0, cache, fetch) is True
    assert fetches == 2
    assert given_names(cache) == {'Tadashi', 'Hidemasa', 'Moriko', 'Jimen'}


def test_refresh_is_fail_soft(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    cache = tmp_path / 'sheet.json'

    def boom() -> str:
        raise OSError('down')

    assert refresh_if_stale(0.0, cache, boom) is False
    assert refresh_if_stale(0.0, cache, lambda: '<html>nothing</html>') is False
    assert not cache.exists()
    assert 'could not fetch' in caplog.text
    assert 'no characters parsed' in caplog.text


def test_default_fetch_is_offline_in_tests() -> None:
    with pytest.raises(RuntimeError, match='offline'):
        sheetroster.fetch_index()


def test_fetch_index_uses_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    class Resp:
        text = '<html/>'

        def raise_for_status(self) -> None:
            pass

    monkeypatch.undo()  # drop the offline guard for this one call
    monkeypatch.setattr(requests, 'get', lambda url, timeout: Resp())
    assert sheetroster.fetch_index() == '<html/>'


def test_given_name_is_the_last_latin_token() -> None:
    assert given_name('Tsuruchi Makoto 鶴知誠') == 'Makoto'
    assert given_name('Tsuruchi Yudai 勇大') == 'Yudai'
    assert given_name('Otsuki') == 'Otsuki'
    assert given_name('Tsuruchi Hidemasa') == 'Hidemasa'
    assert given_name('Otsuki') == 'Otsuki'
    assert given_name('鶴知誠') == ''


def test_default_fetch_is_resolved_at_call_time(tmp_path: Path) -> None:
    # The offline guard patches sheetroster.fetch_index; a default argument
    # would have bound the real function at import and hit the network.
    assert refresh_if_stale(0.0, tmp_path / 'sheet.json') is False


def test_bad_cache_reads_as_empty(tmp_path: Path) -> None:
    cache = tmp_path / 'sheet.json'
    assert full_names(cache) == []
    cache.write_text('[1, 2]')
    assert full_names(cache) == []
    cache.write_text('{"names": "x"}')
    assert given_names(cache) == frozenset()


# --- NPCs from the sheet's GET /api/characters (feature 213, FR-010) ---------------------

API_PAYLOAD = {
    'characters': [
        {'name': 'Tsuruchi Jimen', 'is_npc': False},
        {'name': 'Goro', 'is_npc': True},
        {'name': 'Bayushi Kagehisa 影久', 'is_npc': True},
        {'name': '', 'is_npc': True},
        'not a dict',
    ]
}


def test_parse_npcs_takes_flagged_characters_only() -> None:
    assert sheetroster.parse_npcs(API_PAYLOAD) == ['Goro', 'Bayushi Kagehisa 影久']
    assert sheetroster.parse_npcs({'characters': []}) == []
    bads: list[object] = [{}, [], {'characters': 'x'}]
    for bad in bads:
        with pytest.raises(ValueError, match='no characters list'):
            sheetroster.parse_npcs(bad)


def test_refresh_records_npcs_and_given_names_include_them(tmp_path: Path) -> None:
    cache = tmp_path / 'sheet.json'
    assert refresh_if_stale(0.0, cache, FIXTURE.read_text, lambda: ['Bayushi Kagehisa 影久'])
    assert sheetroster.npc_names(cache) == ['Bayushi Kagehisa 影久']
    assert full_names(cache)[0] == 'Asako Tadashi'  # the index names are unchanged
    assert 'Kagehisa' in given_names(cache)
    assert 'Hidemasa' in given_names(cache)


def test_failed_npc_fetch_keeps_the_cached_npcs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cache = tmp_path / 'sheet.json'
    refresh_if_stale(0.0, cache, FIXTURE.read_text, lambda: ['Goro'])

    def down() -> list[str]:
        raise OSError('api down')

    # the index still refreshes; the NPC list is carried forward, never emptied
    assert refresh_if_stale(0.0, cache, FIXTURE.read_text, down) is True
    assert sheetroster.npc_names(cache) == ['Goro']
    assert 'could not fetch NPCs' in caplog.text
    # an EMPTY answer is a real answer (no NPCs any more), unlike an empty index
    assert refresh_if_stale(0.0, cache, FIXTURE.read_text, list) is True
    assert sheetroster.npc_names(cache) == []


def test_npcs_are_not_fetched_when_the_index_fails(tmp_path: Path) -> None:
    cache = tmp_path / 'sheet.json'
    calls: list[int] = []

    def boom() -> str:
        raise OSError('down')

    def npcs() -> list[str]:
        calls.append(1)
        return []

    assert refresh_if_stale(0.0, cache, boom, npcs) is False
    assert calls == []
    assert not cache.exists()


def test_default_npc_fetch_is_offline_in_tests(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match='offline'):
        sheetroster.fetch_npc_names()
    # resolved at call time: the default refresh reaches the refusal, not the network
    cache = tmp_path / 'sheet.json'
    assert refresh_if_stale(0.0, cache, FIXTURE.read_text) is True
    assert sheetroster.npc_names(cache) == []


def test_npc_names_reads_a_bad_cache_as_empty(tmp_path: Path) -> None:
    cache = tmp_path / 'sheet.json'
    assert sheetroster.npc_names(cache) == []
    cache.write_text('{"names": [], "npcs": "x"}')
    assert sheetroster.npc_names(cache) == []


def test_fetch_npc_names_uses_the_read_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import requests

    seen: dict[str, object] = {}

    class Resp:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> object:
            return API_PAYLOAD

    def get(url: str, headers: dict[str, str], timeout: float) -> Resp:
        seen.update(url=url, headers=headers)
        return Resp()

    monkeypatch.undo()  # drop the offline guard for this one call
    monkeypatch.setattr(requests, 'get', get)
    secrets = tmp_path / 'development-secrets.ini'
    monkeypatch.setattr(sheetroster, 'SECRETS', secrets)
    with pytest.raises(RuntimeError, match='roll_query_token'):
        sheetroster.fetch_npc_names()
    secrets.write_text('[character_sheet]\nroll_query_token = r34d\n')
    assert sheetroster.fetch_npc_names() == ['Goro', 'Bayushi Kagehisa 影久']
    assert seen == {'url': sheetroster.API_URL, 'headers': {'Authorization': 'Bearer r34d'}}


def test_token_reader_agrees_with_the_repl_client(tmp_path: Path) -> None:
    """The sheet's read token is read in two places (this module must not import the whole
    REPL namespace to reach the other); this pins them to the same key."""
    from l7r.repl.rolls import sheet

    secrets = tmp_path / 'development-secrets.ini'
    secrets.write_text('[character_sheet]\nroll_query_token =  abc \nnames_token = other\n')
    assert sheetroster.query_token(secrets) == sheet.query_token(secrets) == 'abc'
