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
