"""Feature 214: the Isawa Ishi 3rd Dan boost, recorded with the roll it boosts.

The GM's example is the test that matters most: a 13 Etiquette boosted by 8 is a
21 and is written as 20 - never the already-written 10 plus 8 - whether the boost
lands before or after the first write (SC-001).
"""

from __future__ import annotations

import importlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import gmrolls
from l7r.repl.rolls import boost as boostmod
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import rules, sheet
from l7r.repl.rolls.models import Boost, Conversation, Line, Roll
from l7r.repl.rolls.skills import load_skills

ann = importlib.import_module('l7r.repl.rolls.annotate')

W = datetime(2026, 10, 3, 1, 0, tzinfo=UTC)
BOT = conv.SHEET_BOT_ID
LINK = 'https://discord.com/channels/745421621829042297/832075722516201492/'
PLAYERS = {
    '1': sheet.SheetCharacter(name='Tsuruchi Jimen', discord_id='1'),
    '2': sheet.SheetCharacter(name='Isawa Tadashi', discord_id='2'),
    '3': sheet.SheetCharacter(name='Tetsuro', discord_id='3'),
}
CAST = [{'id': 'otsuki-id', 'name': 'Otsuki'}]


@pytest.fixture(autouse=True)
def clean() -> Any:
    conv._open = None
    gmrolls.stop()
    gmrolls.clear()
    yield
    conv._open = None
    gmrolls.stop()
    gmrolls.clear()


@pytest.fixture(scope='module')
def words() -> tuple[str, ...]:
    return load_skills()


def message(
    mid: str,
    author: str,
    content: str = '',
    minute: int = 5,
    *,
    reply_to: str = '',
    image: bool = False,
    flags: int = 0,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        'id': mid,
        'timestamp': f'2026-10-03T01:{minute:02d}:00+00:00',
        'author': {'id': author, 'global_name': f'player{author}'},
        'content': content,
        'attachments': [{'content_type': 'image/png'}] if image else [],
        'flags': flags,
    }
    if reply_to:
        out['type'] = 19
        out['message_reference'] = {'type': 0, 'message_id': reply_to}
    return out


def roll(
    name: str, skill: str, total: int, mid: str = '10', *, note: str = '', line: int | None = None
) -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='typed',
        message_id=mid,
        at=W,
        note=note,
        line=line,
    )


def conversation(*rolls: Roll) -> Conversation:
    c = Conversation(npc={'id': 'otsuki-id', 'name': 'Otsuki'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    return c


def boost(total: int = 8, target: str = '10', who: str = 'Isawa Tadashi') -> Boost:
    return Boost(character=who, total=total, message_id='50', at=W, target_message_id=target)


def open_one() -> Conversation:
    return conv.begin_conversation(
        'Otsuki', channel='tuesday', characters=lambda: CAST, now=lambda: W
    )


def collect(
    messages: list[dict[str, Any]],
    words: tuple[str, ...],
    rows: tuple[sheet.RecordedRoll, ...] = (),
    reason: str = '',
) -> Conversation:
    return conv.collect(
        fetch=lambda cid, cursor, **k: messages,
        recorded=lambda *a, **k: sheet.SheetResult(rolls=rows, reason=reason),
        roster=lambda *a, **k: sheet.SheetResult(characters=PLAYERS),
        vocabulary=words,
        ceilings=lambda sheet_id: sheet.Ceilings(),
        now=lambda: datetime(2026, 10, 3, 1, 30, tzinfo=UTC),
    )


def recorded(
    character: str, total: int, minute: int, key: str = boostmod.ROLL_KEY, target: str = ''
) -> sheet.RecordedRoll:
    return sheet.RecordedRoll(
        character=character,
        skill=sheet.canonical_skill(key),
        total=total,
        actor_discord_id='2',
        at=datetime(2026, 10, 3, 1, minute, tzinfo=UTC),
        roll_key=key,
        target_message_id=target,
    )


class TestRecognition:
    def test_the_message_command_reply_carries_its_target(self) -> None:
        found = boostmod.from_bot(
            message('50', BOT, f'**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan, boosting {LINK}10'),
            W,
            bot_id=BOT,
        )
        assert found is not None
        assert (found.character, found.total, found.target_message_id) == (
            'Isawa Tadashi',
            8,
            '10',
        )

    def test_the_slash_command_reply_has_no_target(self) -> None:
        found = boostmod.from_bot(
            message('50', BOT, '**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan'), W, bot_id=BOT
        )
        assert found is not None
        assert found.target_message_id == ''

    def test_a_dm_jump_link_still_names_the_target(self) -> None:
        found = boostmod.from_bot(
            message(
                '50',
                BOT,
                '**T**: **8** Isawa Ishi 3rd Dan, boosting https://discord.com/channels/@me/1/77',
            ),
            W,
            bot_id=BOT,
        )
        assert found is not None
        assert found.target_message_id == '77'

    def test_only_the_sheet_bot_speaks_for_the_commands(self) -> None:
        fake = message('50', '2', '**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan')
        assert boostmod.from_bot(fake, W, bot_id=BOT) is None

    def test_an_ordinary_bot_roll_is_not_a_boost(self) -> None:
        assert (
            boostmod.from_bot(message('50', BOT, '**Jimen**: **23** Etiquette@1'), W, bot_id=BOT)
            is None
        )

    @pytest.mark.parametrize(
        ('text', 'total'),
        [
            ('8 ishi', 8),
            ('+8 Isawa Ishi', 8),
            ('Ishi 3rd Dan: 12', 12),
            ('ishi boost +7', 7),
            ('isawa ishi third dan 9', 9),
        ],
    )
    def test_typed_forms(self, text: str, total: int) -> None:
        found = boostmod.typed(message('50', '2', text), 'Isawa Tadashi', W)
        assert found is not None
        assert found.total == total

    @pytest.mark.parametrize(
        'text',
        ['ishi 3rd', '3rd Dan: 8', 'Ishikawa 8', '@8 ishi', 'the Ishi school', '38 etiquette'],
    )
    def test_not_a_typed_boost(self, text: str) -> None:
        assert boostmod.typed(message('50', '2', text), 'Isawa Tadashi', W) is None

    def test_a_typed_reply_is_aimed_by_the_reply(self) -> None:
        found = boostmod.typed(message('50', '2', '8 ishi', reply_to='10'), 'Isawa Tadashi', W)
        assert found is not None
        assert found.target_message_id == '10'

    def test_a_forward_is_not_a_reply(self) -> None:
        forwarded = message('50', '2', '8 ishi')
        forwarded['message_reference'] = {'type': 1, 'message_id': '10'}
        assert boostmod.reply_target(forwarded) == ''

    def test_a_recorded_row_target_wins_over_the_reply(self) -> None:
        found = boostmod.from_recorded('T', 8, '77', message('50', '2', reply_to='10'), W)
        assert found.target_message_id == '77'
        found = boostmod.from_recorded('T', 8, '', message('50', '2', reply_to='10'), W)
        assert found.target_message_id == '10'


class TestPlacing:
    def test_the_gms_example_13_plus_8(self) -> None:
        c = conversation(roll('Tsuruchi Jimen', 'etiquette', 13))
        said = boostmod.place(c, boost())
        assert said == "  + Tadashi's Ishi 3rd Dan +8 to Jimen etiquette (13 -> 21)"
        assert c.rolls[0].total == 21
        assert (c.rolls[0].boost, c.rolls[0].boosted_by) == (8, 'Isawa Tadashi')
        assert rules.render_lines(c.rolls, 'Otsuki') == ['Jimen etiquette: 20']

    @pytest.mark.parametrize(
        ('rolls', 'target', 'reason'),
        [
            ((), '', 'not aimed at a roll'),
            ((), '10', 'holds no roll from this conversation'),
            (
                (roll('Jimen', 'investigation', 30), roll('Jimen', 'interrogation', 36)),
                '10',
                'holds 2 rolls',
            ),
            ((roll('Isawa Tadashi', 'etiquette', 13),), '10', 'ANOTHER character'),
            ((roll('Tadashi', 'etiquette', 13),), '10', 'ANOTHER character'),
        ],
    )
    def test_held_with_its_reason(self, rolls: tuple[Roll, ...], target: str, reason: str) -> None:
        c = conversation(*rolls)
        held = boost(target=target)
        said = boostmod.place(c, held)
        assert reason in said
        assert 'annotate()' in said
        assert held.held
        assert reason in held.held_because
        assert boostmod.held(c) == [held]

    def test_two_characters_sharing_a_given_name_are_two_people(self) -> None:
        c = conversation(roll('Kakita Tadashi', 'etiquette', 13))
        boostmod.place(c, boost())
        assert c.rolls[0].total == 21
        assert boostmod.same_character('Tadashi', 'Isawa Tadashi')
        assert not boostmod.same_character('Roll Tester', 'Other Tester')

    def test_a_discarded_roll_is_not_a_target(self) -> None:
        c = conversation(roll('Jimen', 'etiquette', 13))
        c.rolls[0] = replace(c.rolls[0], discarded=True)
        assert 'holds no roll' in boostmod.place(c, boost())

    def test_once_per_roll(self) -> None:
        c = conversation(roll('Jimen', 'etiquette', 13))
        boostmod.place(c, boost())
        second = boost(total=5)
        assert 'Tadashi already boosted that roll (once per roll)' in boostmod.place(c, second)
        assert c.rolls[0].total == 21
        assert second.held

    def test_unapply_restores_the_raw_total_and_holds_it_again(self) -> None:
        c = conversation(roll('Jimen', 'etiquette', 13))
        b = boost()
        boostmod.place(c, b)
        restored = boostmod.unapply(c, b)
        assert (restored.total, restored.boost, restored.boosted_by) == (13, 0, '')
        assert b.held
        assert 'cancel_boost' in b.held_because

    def test_eligible_is_every_live_unboosted_roll_annotated_or_not(self) -> None:
        c = conversation(
            roll('Jimen', 'etiquette', 13),
            roll('Tetsuro', 'law', 25, '11', note='the warrant'),
            roll('Isawa Tadashi', 'precepts', 30, '12'),
            roll('', 'law', 25, '13'),
        )
        boostmod.place(c, boost())
        assert boostmod.eligible(c) == [1, 2]
        assert boostmod.eligible(c, exclude={1}) == [2]


class TestRounding:
    """SC-001, through the real watcher: the written line moves from 10 to 20."""

    def test_a_boost_after_the_first_write_rewrites_the_line(self, words: tuple[str, ...]) -> None:
        open_one()
        bios: list[str] = []
        body = {'bio': '[[File:1 | p.png]]\r\n\r\nProse.'}

        def update(cid: str, **kw: Any) -> None:
            if 'bio' in kw:
                body['bio'] = kw['bio']
                bios.append(kw['bio'])

        def tick(messages: list[dict[str, Any]]) -> None:
            conv._tick(
                conv._require(),
                collector=lambda c: collect(messages, words),
                get_body=lambda cid: body,
                update=update,
                debounce=0.0,
                announce=False,
                get_conversation=lambda group: sheet.ConversationResult(),
            )

        tick([message('10', '1', '13 etiquette')])
        assert 'Jimen etiquette: 10' in bios[-1]
        tick(
            [message('50', BOT, f'**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan, boosting {LINK}10')]
        )
        assert 'Jimen etiquette: 20' in bios[-1]
        assert 'etiquette: 10' not in bios[-1]


class TestCollect:
    def test_message_command(self, words: tuple[str, ...], capsys: Any) -> None:
        open_one()
        c = collect(
            [
                message('10', '1', '13 etiquette', minute=4),
                message(
                    '50', BOT, f'**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan, boosting {LINK}10'
                ),
            ],
            words,
        )
        assert [(r.skill, r.total) for r in c.rolls] == [('etiquette', 21)]
        assert '(13 -> 21)' in capsys.readouterr().out

    def test_a_typed_reply(self, words: tuple[str, ...]) -> None:
        open_one()
        c = collect(
            [
                message('10', '1', '13 etiquette', minute=4),
                message('50', '2', "8 ishi for Jimen's etiquette", reply_to='10'),
            ],
            words,
        )
        assert [(r.character, r.total) for r in c.rolls] == [('Tsuruchi Jimen', 21)]

    def test_a_pasted_sheet_card_posted_as_a_reply(self, words: tuple[str, ...]) -> None:
        open_one()
        c = collect(
            [
                message('10', '1', '13 etiquette', minute=4),
                message('50', '2', '', reply_to='10', image=True),
            ],
            words,
            rows=(recorded('Isawa Tadashi', 8, 5),),
        )
        assert [r.total for r in c.rolls] == [21]
        assert len(c.boosts) == 1

    def test_the_bot_card_backs_onto_the_rows_target(self, words: tuple[str, ...]) -> None:
        """A message-command card with no link in its text still finds its target via
        the recorded row - and only the technique's row, never the booster's own roll."""
        open_one()
        c = collect(
            [
                message('10', '1', '13 etiquette', minute=4),
                message('50', BOT, '**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan', image=True),
            ],
            words,
            rows=(
                recorded('Isawa Tadashi', 30, 5, key='skill:etiquette'),
                recorded('Isawa Tadashi', 8, 5, target='10'),
            ),
        )
        assert [r.total for r in c.rolls] == [21]

    def test_the_slash_command_is_held(self, words: tuple[str, ...], capsys: Any) -> None:
        open_one()
        c = collect(
            [
                message('10', '1', '13 etiquette', minute=4),
                message('50', BOT, '**Isawa Tadashi**: **8** Isawa Ishi 3rd Dan', image=True),
            ],
            words,
            reason='sheet app down',
        )
        assert [r.total for r in c.rolls] == [13]
        assert boostmod.held(c)[0].total == 8
        out = capsys.readouterr().out
        assert 'waiting for annotate()' in out
        assert not any('could not be resolved' in u for u in c.unresolved)

    def test_a_boost_message_contributes_no_roll(self, words: tuple[str, ...]) -> None:
        open_one()
        c = collect([message('50', '2', '8 ishi on the 30 etiquette')], words)
        assert c.rolls == []
        assert len(c.boosts) == 1

    def test_an_ordinary_pasted_card_still_joins(self, words: tuple[str, ...]) -> None:
        open_one()
        c = collect(
            [message('10', '2', '', image=True)],
            words,
            rows=(recorded('Isawa Tadashi', 30, 5, key='skill:etiquette'),),
        )
        assert [(r.skill, r.total) for r in c.rolls] == [('etiquette', 30)]
        assert c.boosts == []

    def test_an_unknown_poster_cannot_type_a_boost(self, words: tuple[str, ...]) -> None:
        open_one()
        c = collect([message('50', '99', '8 ishi')], words)
        assert c.boosts == []


class TestLoading:
    """The deferred-response defect found on the way (spec plan, Principle XIV)."""

    NOW = datetime(2026, 10, 3, 1, 10, tzinfo=UTC)

    def test_stops_at_a_message_still_loading(self) -> None:
        page = [message('1', '1', 'a'), message('2', BOT, flags=conv.LOADING), message('3', '1')]
        assert [m['id'] for m in conv.settled(page, self.NOW)] == ['1']

    def test_passes_a_loading_message_whose_edit_is_never_coming(self) -> None:
        page = [message('2', BOT, flags=conv.LOADING, minute=5), message('3', '1')]
        later = datetime(2026, 10, 3, 1, 30, tzinfo=UTC)
        assert [m['id'] for m in conv.settled(page, later)] == ['2', '3']

    def test_other_flags_do_not_stop_it(self) -> None:
        page = [message('2', BOT, flags=1 << 2), message('3', '1')]
        assert len(conv.settled(page, self.NOW)) == 2

    def test_the_cursor_waits_for_the_edit(self, words: tuple[str, ...]) -> None:
        open_one()
        stuck = message('60', BOT, flags=conv.LOADING, minute=29)
        c = collect([message('10', '1', '13 etiquette', minute=4), stuck], words)
        assert c.last_seen['832075722516201492'] == '10'


class TestSheetFields:
    def test_roll_key_and_target_are_read(self) -> None:
        row = sheet._as_roll(
            {
                'character_name': 'Isawa Tadashi',
                'roll_key': boostmod.ROLL_KEY,
                'total': 8,
                'target_message_id': '10',
                'created_at': '2026-10-03T01:05:00Z',
            }
        )
        assert (row.roll_key, row.target_message_id) == (boostmod.ROLL_KEY, '10')

    def test_absent_fields_are_empty(self) -> None:
        row = sheet._as_roll({'label': 'Etiquette', 'created_at': '2026-10-03T01:05:00Z'})
        assert (row.roll_key, row.target_message_id) == ('', '')


class TestClosing:
    def _held(self) -> Conversation:
        c = open_one()
        c.rolls.append(roll('Tsuruchi Jimen', 'etiquette', 13))
        boostmod.place(c, boost(target=''))
        return c

    def test_a_held_boost_keeps_the_conversation_open(self) -> None:
        self._held()
        with pytest.raises(
            conv.NotAnnotated, match="Tadashi's Ishi 3rd Dan \\+8: it was not aimed"
        ):
            conv.end_conversation(collector=lambda c: c)
        assert conv._open is not None

    def test_the_forced_close_names_what_it_drops(self, capsys: Any) -> None:
        self._held()
        written: dict[str, Any] = {}
        conv.end_conversation(
            force=True,
            get_body=lambda cid: {'bio': ''},
            update=lambda cid, **kw: written.update(kw),
            collector=lambda c: c,
            get_conversation=lambda group: sheet.ConversationResult(),
        )
        assert "Dropping Tadashi's Ishi 3rd Dan +8" in capsys.readouterr().out
        assert written['bio'] == 'Jimen etiquette: 10'


class TestCancelBoost:
    def test_takes_back_the_latest_and_holds_it(self, capsys: Any) -> None:
        c = open_one()
        c.rolls.extend([roll('Tsuruchi Jimen', 'etiquette', 13), roll('Tetsuro', 'law', 20, '11')])
        boostmod.place(c, boost())
        later = Boost('Isawa Tadashi', 5, '51', datetime(2026, 10, 3, 2, 0, tzinfo=UTC), '11')
        boostmod.place(c, later)
        conv.cancel_boost()
        assert [r.total for r in c.rolls] == [21, 20]
        assert later.held
        assert 'annotate() will ask' in capsys.readouterr().out

    def test_by_pc(self) -> None:
        c = open_one()
        c.rolls.append(roll('Tsuruchi Jimen', 'etiquette', 13))
        boostmod.place(c, boost())
        conv.cancel_boost('Tadashi')
        assert c.rolls[0].total == 13

    def test_nothing_to_take_back(self) -> None:
        open_one()
        with pytest.raises(ValueError, match='no boost has been applied'):
            conv.cancel_boost()
        with pytest.raises(ValueError, match='no boost by Jimen'):
            conv.cancel_boost('Jimen')


class TestKnockOn:
    def test_a_boosted_oppose_roll_re_prices(self, capsys: Any) -> None:
        c = open_one()
        c.rolls.append(roll('Tsuruchi Jimen', 'oppose social', 22))
        tact = gmrolls.record((9, 9, 9, 9, 9), 3, 22, asked=(5, 3))
        tact.tagged = 'tact'
        tact.at = W + timedelta(minutes=3)
        conv.after_boost(c, 0)
        priced = tact.penalty
        boostmod.place(c, boost())
        conv.after_boost(c, 0)
        assert tact.penalty > priced
        assert 'Otsuki tact' in capsys.readouterr().out

    def test_a_boosted_interrogation_roll_is_compared_again(self, capsys: Any) -> None:
        c = open_one()
        c.lines.append(Line(id=1, description='the hour', at=W, sincerity=20))
        c.rolls.append(roll('Tsuruchi Jimen', 'interrogation', 18, line=1))
        boostmod.place(c, boost())
        conv.after_boost(c, 0)
        assert 'Jimen' in capsys.readouterr().out


def answers(*said: str) -> Any:
    script = iter(said)
    return lambda question: next(script)


class TestAnnotate:
    def test_a_held_boost_is_placed_on_an_annotated_roll(self, capsys: Any) -> None:
        c = conversation(
            roll('Tsuruchi Jimen', 'etiquette', 13), roll('Tetsuro', 'law', 22, '11', note='writ')
        )
        boostmod.place(c, boost(target=''))
        ann.annotate(c, ask=answers('2'), mine=lambda: ())
        assert c.rolls[1].total == 30
        out = capsys.readouterr().out
        assert '2. Tetsuro law 22' in out
        assert '- writ' in out
        assert "Tadashi's Ishi 3rd Dan +8 on Tetsuro law: 22 -> 30." in out

    def test_discard(self) -> None:
        c = conversation(roll('Tsuruchi Jimen', 'etiquette', 13))
        held = boost(target='')
        boostmod.place(c, held)
        ann.annotate(c, ask=answers('x', 'd'), mine=lambda: ())
        assert held.discarded
        assert c.rolls[0].total == 13
        assert boostmod.held(c) == []

    def test_ctrl_c_saves_nothing(self) -> None:
        c = conversation(roll('Tsuruchi Jimen', 'etiquette', 13))
        held = boost(target='')
        boostmod.place(c, held)

        def interrupt(question: str) -> str:
            raise KeyboardInterrupt

        ann.annotate(c, ask=interrupt, mine=lambda: ())
        assert held.held
        assert c.rolls[0].total == 13

    def test_nothing_to_put_it_on(self, capsys: Any) -> None:
        c = conversation()
        held = boost(target='')
        boostmod.place(c, held)
        ann.annotate(c, ask=answers('1', 'd'), mine=lambda: ())
        assert 'only d' in capsys.readouterr().out
        assert held.discarded

    def test_beside_a_waiting_roll_and_two_boosts_cannot_share_a_roll(self, capsys: Any) -> None:
        c = conversation(roll('Tsuruchi Jimen', 'etiquette', 13), roll('Tetsuro', 'law', 22, '11'))
        first, second = boost(target=''), boost(total=4, target='')
        boostmod.place(c, first)
        boostmod.place(c, second)
        # rows: 1 = Tetsuro's law (waiting), 2 and 3 = the boosts. First boost onto
        # Jimen; the second's list no longer offers Jimen, so its "1" is Tetsuro.
        ann.annotate(c, ask=answers('2', '1', '2', '1', 'o', 'the writ', ''), mine=lambda: ())
        assert [r.total for r in c.rolls] == [21, 26]
        assert c.rolls[1].note == 'the writ'
        assert 'Annotated 1 roll(s).' in capsys.readouterr().out
