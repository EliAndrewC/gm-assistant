"""PC registry and character-sheet knack ranks (l7r.repl.sheets). The sheet
page is a saved fixture; nothing here reaches the network."""

import json
from pathlib import Path

import requests

import pytest

from l7r.repl import namespace
from l7r.repl.sheets import (
    PC,
    PCS,
    knack_rank,
    parse_knack_rank,
    parse_sheet_name,
    resolve_pc,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'sheets' / 'jimen.html'
JIMEN = PCS[0]


def test_registry_and_forms() -> None:
    assert PC('Tsuruchi Jimen', 3) == JIMEN
    assert JIMEN.given == 'Jimen'
    assert JIMEN.url == 'https://l7r-character-sheet.fly.dev/characters/3'
    for form in ('Jimen', 'jimen', 'Tsuruchi Jimen', 'TsuruchiJimen', 'JIMEN', 'TSURUCHI_JIMEN'):
        assert resolve_pc(form) is JIMEN
    assert resolve_pc(JIMEN) is JIMEN
    assert resolve_pc('Kaede') is None
    assert set(JIMEN.constants) == {'Jimen', 'TsuruchiJimen', 'JIMEN', 'TSURUCHI_JIMEN'}


def test_constants_are_in_the_repl_namespace() -> None:
    ns = namespace()
    assert ns['Jimen'] is ns['TSURUCHI_JIMEN'] is JIMEN
    assert ns['Makoto'].sheet_id == 16
    assert ns['PCS'] is PCS


def test_parse_real_page_fixture() -> None:
    html = FIXTURE.read_text()
    assert parse_sheet_name(html) == 'Tsuruchi Jimen'
    assert parse_knack_rank(html, 'Discern Honor') == 4  # dots BEFORE the label are ignored
    assert parse_knack_rank(html, 'Iaijutsu') is None
    assert (
        parse_knack_rank('<span class="font-medium">Discern Honor</span> no dots', 'Discern Honor')
        is None
    )
    assert parse_sheet_name('<title>other</title>') == ''


def test_knack_rank_caches_for_a_day(tmp_path: Path) -> None:
    cache = tmp_path / 'c.json'
    clock = [1_000.0]
    fetches: list[PC] = []

    def fetch(pc: PC) -> str:
        fetches.append(pc)
        return FIXTURE.read_text()

    def rank() -> int:
        return knack_rank(JIMEN, fetch=fetch, cache_path=cache, now=lambda: clock[0])

    assert rank() == 4
    assert rank() == 4
    assert len(fetches) == 1
    assert json.loads(cache.read_text())['3:Discern Honor']['name'] == 'Tsuruchi Jimen'
    clock[0] += 25 * 3600
    assert rank() == 4
    assert len(fetches) == 2


def test_fetch_sheet_uses_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    from l7r.repl import sheets

    class Resp:
        text = '<title>L7R - X</title>'

        def raise_for_status(self) -> None:
            pass

    seen: list[tuple[str, float]] = []

    def get(url: str, timeout: float) -> Resp:
        seen.append((url, timeout))
        return Resp()

    monkeypatch.setattr(requests, 'get', get)
    assert sheets.fetch_sheet(JIMEN) == '<title>L7R - X</title>'
    assert seen == [(JIMEN.url, 20)]


def test_knack_rank_missing_knack_and_bad_cache(tmp_path: Path) -> None:
    cache = tmp_path / 'c.json'
    cache.write_text('[not a dict]')
    with pytest.raises(ValueError, match='has no Iaijutsu on the sheet'):
        knack_rank(JIMEN, 'Iaijutsu', fetch=lambda pc: FIXTURE.read_text(), cache_path=cache)
