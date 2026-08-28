"""The conversation: open, collect, close, write.

Every boundary is injected, so nothing here touches Discord, the character-sheet
app, or Obsidian Portal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import discord as discord_mod
from l7r.repl.rolls import sheet
from l7r.repl.rolls.skills import load_skills

OPENED = datetime(2026, 8, 12, 1, 53, tzinfo=UTC)
CAST = [
    {'id': 'otsuki-id', 'name': 'Otsuki'},
    {'id': 'sakura-id', 'name': 'Hida no Reiji Sakura'},
    {'id': 'rei-id', 'name': 'Hida no Reiji Rei'},
]


@pytest.fixture(autouse=True)
def closed() -> Any:
    """No conversation leaks between tests."""
    conv._open = None
    yield
    conv._open = None


@pytest.fixture(scope='module')
def words() -> tuple[str, ...]:
    return load_skills()


def message(
    mid: str,
    author: str,
    content: str = '',
    minute: int = 54,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        'id': mid,
        'timestamp': f'2026-08-12T01:{minute:02d}:00+00:00',
        'author': {'id': author, 'global_name': f'player{author}'},
        'content': content,
        'attachments': attachments or [],
    }


def open_one(channel: str | None = 'tuesday') -> Any:
    return conv.begin_conversation('Otsuki', channel, characters=lambda: CAST, now=lambda: OPENED)


def collect_with(
    messages: list[dict[str, Any]],
    words: tuple[str, ...],
    rolls: tuple[sheet.RecordedRoll, ...] = (),
    reason: str = '',
    who: dict[str, sheet.SheetCharacter] | None = None,
) -> Any:
    return conv.collect(
        fetch=lambda cid, cursor, **k: messages,
        recorded=lambda *a, **k: sheet.SheetResult(rolls=rolls, reason=reason),
        roster=lambda *a, **k: sheet.SheetResult(characters=who or {}),
        vocabulary=words,
    )


PLAYERS = {
    '1': sheet.SheetCharacter(name='Jimen', discord_id='1'),
    '2': sheet.SheetCharacter(name='Tetsuro', discord_id='2'),
}


class TestBeginConversation:
    def test_opens_against_a_uniquely_named_npc(self) -> None:
        opened = open_one()
        assert opened.npc_name == 'Otsuki'
        assert opened.channels == ('832075722516201492',)
        assert opened.opened_at == OPENED

    def test_accepts_a_raw_channel_id(self) -> None:
        assert open_one('832075590726844436').channels == ('832075590726844436',)

    def test_refuses_an_ambiguous_name_and_lists_the_candidates(self) -> None:
        with pytest.raises(ValueError, match='matches several characters'):
            conv.begin_conversation('Reiji', 'tuesday', characters=lambda: CAST)
        assert conv._open is None

    def test_refuses_an_unknown_name(self) -> None:
        with pytest.raises(ValueError, match='no character called'):
            conv.begin_conversation('Nobody', 'tuesday', characters=lambda: CAST)

    def test_refuses_a_second_conversation_and_names_the_open_one(self) -> None:
        open_one()
        with pytest.raises(conv.AlreadyOpen, match='already talking to Otsuki'):
            open_one()

    def test_no_channel_watches_every_monitored_channel(self) -> None:
        """The GM asked for one argument: begin_conversation("Otsuki")."""
        opened = conv.begin_conversation('Otsuki', characters=lambda: CAST, now=lambda: OPENED)
        assert set(opened.channels) == set(discord_mod.CHANNELS.values())
        assert len(opened.channels) > 1

    def test_an_empty_channel_string_is_refused(self) -> None:
        with pytest.raises(ValueError, match='name a channel'):
            conv.begin_conversation('Otsuki', '  ', characters=lambda: CAST)


class TestCollect:
    def test_reads_typed_rolls_and_attributes_them(self, words: tuple[str, ...]) -> None:
        open_one()
        got = collect_with([message('1', '1', '38 Etiquette @3')], words, who=PLAYERS)
        assert [(r.character, r.skill, r.total) for r in got.rolls] == [('Jimen', 'etiquette', 38)]

    def test_advances_the_cursor(self, words: tuple[str, ...]) -> None:
        open_one()
        got = collect_with(
            [message('1', '1', '38 Etiquette @3'), message('7', '2', '24 eti')], words, who=PLAYERS
        )
        assert set(got.last_seen.values()) == {'7'}

    def test_reports_a_roll_it_cannot_attribute(self, words: tuple[str, ...]) -> None:
        open_one()
        got = collect_with([message('1', '99', '38 Etiquette @3')], words, who=PLAYERS)
        assert got.rolls == []
        assert any('no character known' in u for u in got.unresolved)

    def test_an_image_joins_to_a_recorded_roll(self, words: tuple[str, ...]) -> None:
        open_one()
        recorded = (
            sheet.RecordedRoll(
                character='Jimen',
                skill='etiquette',
                total=38,
                actor_discord_id='1',
                at=datetime(2026, 8, 12, 1, 54, tzinfo=UTC),
                rank=3,
            ),
        )
        got = collect_with(
            [message('1', '1', attachments=[{'content_type': 'image/png'}])],
            words,
            rolls=recorded,
            who=PLAYERS,
        )
        assert [(r.character, r.total, r.source) for r in got.rolls] == [('Jimen', 38, 'recorded')]

    def test_the_nearest_recorded_roll_wins(self, words: tuple[str, ...]) -> None:
        open_one()
        recorded = (
            sheet.RecordedRoll(
                'Jimen', 'etiquette', 11, '1', datetime(2026, 8, 12, 1, 50, tzinfo=UTC)
            ),
            sheet.RecordedRoll(
                'Jimen', 'etiquette', 38, '1', datetime(2026, 8, 12, 1, 54, tzinfo=UTC)
            ),
        )
        got = collect_with(
            [message('1', '1', attachments=[{'content_type': 'image/png'}])],
            words,
            rolls=recorded,
            who=PLAYERS,
        )
        assert got.rolls[0].total == 38

    def test_an_unmatched_image_is_silently_ignored(self, words: tuple[str, ...]) -> None:
        # A meme, not a roll. The join IS the detector (research.md R1).
        open_one()
        got = collect_with(
            [message('1', '1', attachments=[{'content_type': 'image/png'}])],
            words,
            rolls=(sheet.RecordedRoll('Someone', 'law', 20, 'other-person', OPENED),),
            who=PLAYERS,
        )
        assert got.rolls == []
        assert got.unresolved == []

    def test_a_recorded_roll_supersedes_the_same_typed_roll(self, words: tuple[str, ...]) -> None:
        open_one()
        recorded = (
            sheet.RecordedRoll(
                'Jimen', 'etiquette', 38, '1', datetime(2026, 8, 12, 1, 54, tzinfo=UTC), 3
            ),
        )
        got = collect_with(
            [message('1', '1', '38 Etiquette @3', attachments=[{'content_type': 'image/png'}])],
            words,
            rolls=recorded,
            who=PLAYERS,
        )
        assert len(got.rolls) == 1
        assert got.rolls[0].source == 'recorded'

    def test_without_the_endpoint_typed_rolls_still_land(self, words: tuple[str, ...]) -> None:
        """FR-018: the typed path works with no character-sheet endpoint at all."""
        open_one()
        got = collect_with(
            [
                message('1', '1', '38 Etiquette @3'),
                message('2', '2', attachments=[{'content_type': 'image/png'}]),
            ],
            words,
            reason='the character-sheet roll endpoint returned 404',
            who=PLAYERS,
        )
        assert [(r.character, r.total) for r in got.rolls] == [('Jimen', 38)]
        assert any('404' in u for u in got.unresolved)
        assert any('could not be resolved' in u for u in got.unresolved)

    def test_the_unavailable_note_is_not_repeated_across_polls(
        self, words: tuple[str, ...]
    ) -> None:
        open_one()
        for _ in range(3):
            got = collect_with([], words, reason='endpoint down', who=PLAYERS)
        assert sum('endpoint down' in u for u in got.unresolved) == 1

    def test_discord_being_unreachable_is_reported_not_raised(self, words: tuple[str, ...]) -> None:
        open_one()

        def boom(cid: str, cursor: Any, **kwargs: Any) -> Any:
            raise discord_mod.DiscordUnavailable('403 Missing Access')

        got = conv.collect(
            fetch=boom,
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(),
            vocabulary=words,
        )
        assert got.rolls == []
        assert any('403' in u for u in got.unresolved)

    def test_requires_an_open_conversation(self, words: tuple[str, ...]) -> None:
        with pytest.raises(conv.NoConversation, match='no conversation open'):
            collect_with([], words)

    def test_loads_the_real_vocabulary_when_none_is_given(self) -> None:
        open_one()
        got = conv.collect(
            fetch=lambda *a, **k: [message('1', '1', '38 Etiquette @3')],
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(characters=PLAYERS),
        )
        assert got.rolls[0].skill == 'etiquette'


class TestManyChannels:
    def test_reads_every_watched_channel(self, words: tuple[str, ...]) -> None:
        conv.begin_conversation('Otsuki', characters=lambda: CAST, now=lambda: OPENED)
        per_channel = {
            '832075590726844436': [message('1', '1', '38 Etiquette @3', minute=54)],
            '832075722516201492': [message('2', '2', '28 Etiquette @2', minute=55)],
        }
        got = conv.collect(
            fetch=lambda cid, cursor, **k: per_channel.get(cid, []),
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(characters=PLAYERS),
            vocabulary=words,
        )
        assert {(r.character, r.total) for r in got.rolls} == {('Jimen', 38), ('Tetsuro', 28)}

    def test_each_channel_keeps_its_own_cursor(self, words: tuple[str, ...]) -> None:
        conv.begin_conversation('Otsuki', characters=lambda: CAST, now=lambda: OPENED)
        per_channel = {
            '832075590726844436': [message('11', '1', '38 Etiquette @3', minute=54)],
            '832075722516201492': [message('22', '2', '28 Etiquette @2', minute=55)],
        }
        got = conv.collect(
            fetch=lambda cid, cursor, **k: per_channel.get(cid, []),
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(characters=PLAYERS),
            vocabulary=words,
        )
        assert got.last_seen['832075590726844436'] == '11'
        assert got.last_seen['832075722516201492'] == '22'

    def test_one_unreadable_channel_does_not_hide_another(self, words: tuple[str, ...]) -> None:
        conv.begin_conversation('Otsuki', characters=lambda: CAST, now=lambda: OPENED)

        def fetch(cid: str, cursor: Any, **k: Any) -> Any:
            if cid == '832075590726844436':
                raise discord_mod.DiscordUnavailable('403 Missing Access')
            # Only the Tuesday channel has anything; the conversation watches every
            # monitored channel, so an unconditional return would double the roll.
            if cid == '832075722516201492':
                return [message('2', '2', '28 Etiquette @2')]
            return []

        got = conv.collect(
            fetch=fetch,
            recorded=lambda *a, **k: sheet.SheetResult(),
            roster=lambda *a, **k: sheet.SheetResult(characters=PLAYERS),
            vocabulary=words,
        )
        assert [(r.character, r.total) for r in got.rolls] == [('Tetsuro', 28)]
        assert any('#monday' in u and '403' in u for u in got.unresolved)


class TestResolveChannels:
    def test_none_means_all(self) -> None:
        assert set(conv.resolve_channels(None)) == set(discord_mod.CHANNELS.values())

    def test_a_name_resolves(self) -> None:
        assert conv.resolve_channels('tuesday') == ('832075722516201492',)

    def test_a_name_is_case_insensitive(self) -> None:
        assert conv.resolve_channels('TUESDAY') == ('832075722516201492',)

    def test_an_unknown_string_is_taken_as_an_id(self) -> None:
        assert conv.resolve_channels('999') == ('999',)

    def test_blank_is_refused(self) -> None:
        with pytest.raises(ValueError, match='name a channel'):
            conv.resolve_channels('   ')


class TestChannelLabel:
    def test_known_channels_get_their_name(self) -> None:
        assert conv._label('832075722516201492') == '#tuesday'

    def test_an_unknown_id_is_shown_as_is(self) -> None:
        assert conv._label('999') == 'channel 999'


class TestPlayerMap:
    def test_prefers_the_sheet_app(self) -> None:
        found = conv._players(sheet.SheetResult(characters=PLAYERS))
        assert found == {'1': 'Jimen', '2': 'Tetsuro'}

    def test_falls_back_to_the_secrets_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secrets = tmp_path / 's.ini'
        secrets.write_text('[discord_players]\n1 = Jimen\n2 = Tetsuro\n')
        monkeypatch.setattr(sheet, 'SECRETS', secrets)
        assert conv._players(sheet.SheetResult()) == {'1': 'Jimen', '2': 'Tetsuro'}

    def test_no_map_anywhere_is_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secrets = tmp_path / 's.ini'
        secrets.write_text('[other]\nx = 1\n')
        monkeypatch.setattr(sheet, 'SECRETS', secrets)
        assert conv._players(sheet.SheetResult()) == {}


class TestEndConversation:
    def test_writes_the_line_under_the_portrait(self, words: tuple[str, ...]) -> None:
        open_one()
        collect_with(
            [message('1', '1', '38 Etiquette @3'), message('2', '2', '28 Etiquette @2')],
            words,
            who=PLAYERS,
        )
        written: dict[str, Any] = {}
        line = conv.end_conversation(
            get_body=lambda cid: {'bio': '[[File:1 | p.png]]\r\n\r\nProse.'},
            update=lambda cid, **kw: written.update({'id': cid, **kw}),
            collector=lambda c: c,
        )
        assert line == 'Jimen / Tetsuro etiquette: 35 / 25'
        assert written['id'] == 'otsuki-id'
        assert line in str(written['bio'])
        assert 'Prose.' in str(written['bio'])
        assert conv._open is None

    def test_writes_nothing_when_no_rolls_were_collected(self) -> None:
        open_one()
        calls: list[Any] = []
        assert (
            conv.end_conversation(
                get_body=lambda cid: {'bio': ''},
                update=lambda cid, **kw: calls.append(kw),
                collector=lambda c: c,
            )
            == ''
        )
        assert calls == []
        assert conv._open is None

    def test_tolerates_a_record_with_no_body(self, words: tuple[str, ...]) -> None:
        open_one()
        collect_with([message('1', '1', '38 Etiquette @3')], words, who=PLAYERS)
        written: dict[str, Any] = {}
        conv.end_conversation(
            get_body=lambda cid: None,
            update=lambda cid, **kw: written.update(kw),
            collector=lambda c: c,
        )
        assert written['bio'] == 'Jimen etiquette: 35'

    def test_requires_an_open_conversation(self) -> None:
        with pytest.raises(conv.NoConversation):
            conv.end_conversation()


class TestAbandonAndStatus:
    def test_abandon_writes_nothing_and_closes(self, words: tuple[str, ...]) -> None:
        open_one()
        collect_with([message('1', '1', '38 Etiquette @3')], words, who=PLAYERS)
        conv.abandon_conversation()
        assert conv._open is None

    def test_abandon_requires_an_open_conversation(self) -> None:
        with pytest.raises(conv.NoConversation):
            conv.abandon_conversation()

    def test_status_when_nothing_is_open(self) -> None:
        assert conv.conversation_status() is None

    def test_status_previews_the_line(self, words: tuple[str, ...], capsys: Any) -> None:
        open_one()
        collect_with([message('1', '1', '38 Etiquette @3')], words, who=PLAYERS)
        assert conv.conversation_status() is not None
        assert 'Jimen etiquette: 35' in capsys.readouterr().out

    def test_status_reports_what_could_not_be_resolved(
        self, words: tuple[str, ...], capsys: Any
    ) -> None:
        open_one()
        collect_with(
            [message('1', '99', '38 Etiquette @3')],
            words,
            reason='the character-sheet roll endpoint returned 404',
            who=PLAYERS,
        )
        conv.conversation_status()
        out = capsys.readouterr().out
        assert '! ' in out
        assert '404' in out

    def test_status_with_no_rolls_yet(self, capsys: Any) -> None:
        open_one()
        conv.conversation_status()
        assert 'no rolls yet' in capsys.readouterr().out
