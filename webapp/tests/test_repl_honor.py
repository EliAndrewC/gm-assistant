"""The Discern Honor knack (l7r.repl.honor): pure logic plus the OP flow with
injected boundaries (no network)."""

from collections.abc import Mapping
from typing import Any

import pytest

from l7r.repl.honor import (
    HEADING,
    Record,
    advance,
    describe,
    discern_honor,
    first_guess,
    parse_honor,
    parse_records,
    perceived,
    render,
)

GM = 'XP: 65\r\nHonor: 3.0\r\n\r\nUnconventional\r\nboisterous\r\n'


class TestParse:
    def test_honor_line(self) -> None:
        assert parse_honor(GM) == 3.0
        assert parse_honor('Honor: 2.5\n') == 2.5
        assert parse_honor('no honor here; honor is mentioned in prose 4.0') is None

    def test_records_roundtrip(self) -> None:
        recs = {
            'jimen': Record('Jimen', 2, 4.5, 1),
            'kaede': Record('Kaede', 1, 3.0, 4, locked=True),
        }
        text = render(GM, recs)
        assert text.endswith(
            f'boisterous\n\n{HEADING}\n- Jimen (rank 2): told 4.5 after 1 conversation\n'
            '- Kaede (rank 1): told 3.0 after 4 conversations - locked in'
        )
        assert parse_records(text) == recs
        assert parse_records(GM) == {}

    def test_render_replaces_an_existing_block_in_place(self) -> None:
        text = render(GM, {'jimen': Record('Jimen', 2, 4.5, 1)}) + '\n\ntrailing prose'
        again = render(text, {'jimen': Record('Jimen', 2, 4.3, 2)})
        assert again.count(HEADING) == 1
        assert '- Jimen (rank 2): told 4.3 after 2 conversations' in again
        assert 'told 4.5' not in again
        assert again.endswith('trailing prose')

    def test_malformed_line_is_ignored(self) -> None:
        assert parse_records(f'{HEADING}\n- garbage\n') == {}


class TestMath:
    def test_first_guess_range(self) -> None:
        assert first_guess(3.0, 1) == 1.0
        assert first_guess(3.0, 5) == 3.0
        assert first_guess(3.0, 10) == 5.5

    def test_unconventional_reads_low_and_virtue_reads_high(self) -> None:
        assert first_guess(3.0, 10, 'low') == 0.5
        assert first_guess(3.0, 1, 'low') == 1.0
        assert first_guess(3.0, 5, 'low') == 3.0
        assert first_guess(3.0, 1, 'high') == 5.0
        assert first_guess(3.0, 10, 'high') == 5.5
        assert perceived('XP: 65\nHonor: 3.0\n\nUnconventional\nboisterous\n') == 'low'
        assert perceived('Honor: 3.0\n\nVirtue\nscarred\n') == 'high'
        assert perceived('Honor: 3.0\nan unconventional fellow of virtue\n') == 'normal'
        assert advance(None, 'Jimen', 3.0, 2, 10, 'low').told == 0.5

    def test_advance_first_needs_rank(self) -> None:
        with pytest.raises(ValueError, match='pass rank='):
            advance(None, 'Jimen', 3.0, None, 7)
        rec = advance(None, 'Jimen', 3.0, 2, 8)
        assert rec == Record('Jimen', 2, 4.5, 1)
        assert advance(None, 'Jimen', 3.0, 2, 5).locked is True

    def test_advance_later_keeps_or_updates_rank(self) -> None:
        rec = Record('Jimen', 2, 4.5, 1)
        assert advance(rec, 'Jimen', 3.0, None, 1) == Record('Jimen', 2, 4.3, 2)
        assert advance(rec, 'Jimen', 3.0, 5, 1) == Record('Jimen', 5, 4.0, 2)
        locked = advance(Record('Jimen', 2, 3.1, 3), 'Jimen', 3.0, None, 1)
        assert locked == Record('Jimen', 2, 3.0, 4, locked=True)

    def test_describe(self) -> None:
        first = describe('Otsuki', 3.0, None, Record('Jimen', 2, 4.5, 1))
        assert 'first conversation: tell them 4.5' in first
        later = describe(
            'Otsuki', 3.0, Record('Jimen', 2, 4.5, 1), Record('Jimen', 2, 3.0, 2, True)
        )
        assert 'was told 4.5 after 1 conversation\n' in later
        assert 'conversation 2: tell them 3.0' in later
        assert 'locked in' in later


CHARS: list[dict[str, object]] = [
    {'id': '1', 'name': 'Otsuki', 'character_url': 'https://op/characters/otsuki'},
    {'id': '2', 'name': 'Hida no Reiji Sakura', 'character_url': 'https://op/characters/sakura'},
    {'id': '3', 'name': 'Hida no Reiji Rei', 'character_url': 'https://op/characters/rei'},
]


class FakeOP:
    def __init__(self, gm_info: str) -> None:
        self.gm_info = gm_info
        self.updates: list[tuple[str, dict[str, Any]]] = []

    def get_body(self, cid: str) -> Mapping[str, object] | None:
        return None if cid == '3' else {'game_master_info': self.gm_info}

    def update(self, cid: str, **fields: Any) -> None:
        self.updates.append((cid, fields))
        self.gm_info = fields['game_master_info']

    def run(self, npc: str, pc: object, rank: int | None = None, die: int = 8, **kw: Any) -> Record:
        return discern_honor(
            npc,
            pc,  # type: ignore[arg-type]
            rank,
            characters=lambda: CHARS,
            get_body=self.get_body,
            update=self.update,
            roll=lambda: die,
            rank_lookup=lambda pc: 4,
            **kw,
        )


class TestDiscernHonor:
    def test_first_then_second_conversation(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Kaede has no sheet, so rank= is given once and then remembered.
        fake = FakeOP('XP: 10\nHonor: 3.0\n')
        first = fake.run('Otsuki', 'Kaede', rank=2, die=8)
        assert first == Record('Kaede', 2, 4.5, 1)
        out = capsys.readouterr().out
        assert 'Otsuki - true Honor 3.0\n' in out
        assert 'recorded on https://op/characters/otsuki' in out
        assert fake.updates[0][0] == '1'
        assert '- Kaede (rank 2): told 4.5 after 1 conversation' in fake.gm_info
        second = fake.run('otsuki', 'kaede')  # case-insensitive PC, rank remembered
        assert second == Record('Kaede', 2, 4.3, 2)
        assert 'told 4.3 after 2 conversations' in fake.gm_info
        assert 'told 4.5' not in fake.gm_info

    def test_partial_names_resolve(self) -> None:
        fake = FakeOP('Honor: 2.5\n')
        for q in ('Sakura', 'Reiji Sakura', 'Hida Sakura', 'Hida no Reiji Sakura'):
            assert fake.run(q, 'Jimen', rank=1, die=5).told == 2.5

    def test_whole_token_beats_substring(self) -> None:
        # "Rei" is inside "Reiji": with substring matching this was ambiguous.
        with pytest.raises(RuntimeError, match='could not fetch Hida no Reiji Rei'):
            FakeOP(GM).run('Rei', 'Jimen', rank=1)

    def test_registered_pc_rank_comes_from_the_sheet(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from l7r.repl.sheets import PCS

        fake = FakeOP(GM)
        for form in ('Jimen', 'TSURUCHI_JIMEN', PCS[0]):
            rec = fake.run('Otsuki', form, die=10)
            assert rec.pc == 'Jimen'
            assert rec.rank == 4
        assert rec.conversations == 3
        assert rec.told == 0.5 + 0.4 + 0.4  # Unconventional first guess, then 0.4 closer twice
        out = capsys.readouterr().out
        assert 'Jimen: Discern Honor rank 4 (character sheet https://l7r-character-sheet' in out
        assert '(Unconventional: reads low)' in out
        assert fake.run('Otsuki', 'Jimen', rank=1).rank == 1  # explicit rank overrides

    def test_preview_does_not_upload(self, capsys: pytest.CaptureFixture[str]) -> None:
        fake = FakeOP(GM)
        fake.run('Otsuki', 'Jimen', rank=2, upload=False)
        assert fake.updates == []
        assert '(not uploaded)' in capsys.readouterr().out

    def test_errors(self) -> None:
        fake = FakeOP('no honor line')
        with pytest.raises(ValueError, match='several characters'):
            fake.run('Hida', 'Jimen', rank=1)
        with pytest.raises(ValueError, match='nearest'):
            fake.run('Zzz', 'Jimen', rank=1)
        with pytest.raises(RuntimeError, match='could not fetch'):
            fake.run('Rei', 'Jimen', rank=1)
        with pytest.raises(ValueError, match='no "Honor: X.Y" line'):
            fake.run('Otsuki', 'Jimen', rank=1)
