"""Feature 207: the hidden opposing rolls go to the GM-only notes and NEVER the bio."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import hidden, lines, npcskills, rules
from l7r.repl.rolls.models import Conversation, Roll

W = datetime(2026, 9, 19, 1, 0, tzinfo=UTC)
BIO = '[[File:1 | class=media-item-align-none | Fumitake.png]]\r\n\r\nAn inspector.\r\n'
NOTES = 'XP: 65\r\nHonor: 3.0'


def roll(
    name: str, skill: str, total: int, *, rank: int | None = 2, minute: int = 1, **kw: Any
) -> Roll:
    return Roll(
        name, skill, total, 'recorded', f'{name}{minute}', W + timedelta(minutes=minute), rank, **kw
    )


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 7)
    monkeypatch.setattr(conv, 'say', lambda text: None)
    yield
    conv._open = None
    gmrolls.clear()


def talking() -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    conv._open = c
    return c


def scene() -> Conversation:
    """A line with a hidden Sincerity roll and two interrogators, and a disguise."""
    c = talking()
    lines.new_line_of_questioning(
        "Chizuru's death", dice.xky(8, 3) + 10, collector=lambda x: None, now=lambda: W
    )
    c.rolls.append(conv.attach(c, roll('Tsuruchi Jimen', 'interrogation', 37)))
    c.rolls.append(conv.attach(c, roll('Moriko', 'interrogation', 24, rank=1, minute=2)))
    c.rolls.append(
        roll(
            'Jimen',
            'acting',
            32,
            rank=1,
            minute=3,
            note='posing as a rice factor',
            opposed_total=27,
            bonus_opposed=5,
        )
    )
    return c


class TestEntries:
    def test_the_gm_only_entries(self) -> None:
        assert hidden.entries(scene()) == (
            "- 2026-09-19 sincerity 31 (+10 not grilling) - Chizuru's death: "
            'Jimen 37@2 not detected, Moriko 24@1 not detected',
            '- 2026-09-19 investigation 32 vs Jimen acting 32@1 - posing as a rice factor: tied',
        )

    def test_a_line_with_no_sincerity_roll_has_no_entry(self) -> None:
        c = talking()
        lines.new_line_of_questioning('small talk', collector=lambda x: None, now=lambda: W)
        c.rolls.append(conv.attach(c, roll('Jimen', 'interrogation', 37)))
        assert hidden.entries(c) == ()

    def test_a_line_nobody_rolled_on_and_a_grilling_line(self) -> None:
        c = talking()
        lines.new_line_of_questioning('the treasury', 30, grilling=True, collector=lambda x: None)
        assert hidden.entries(c) == ('- 2026-09-19 sincerity 30 - the treasury',)

    def test_acting_both_ways_and_the_rolls_that_do_not_count(self) -> None:
        c = talking()
        c.rolls += [
            roll('Jimen', 'acting', 40, note='a', opposed_total=20),
            roll('Jimen', 'acting', 10, rank=None, opposed_total=20),
            roll('Jimen', 'acting', 10, opposed_total=20, discarded=True),
            roll('', 'acting', 10, opposed_total=20),
            roll('Jimen', 'acting', 10),
        ]
        assert hidden.entries(c) == (
            '- 2026-09-19 investigation 20 vs Jimen acting 40@2 - a: not seen through',
            '- 2026-09-19 investigation 20 vs Jimen acting 10: SEEN THROUGH',
        )

    def test_a_detection_the_tool_can_see(self) -> None:
        c = talking()
        lines.new_line_of_questioning(
            'the treasury', 20, grilling=True, collector=lambda x: None, now=lambda: W
        )
        c.rolls.append(conv.attach(c, roll('Jimen', 'interrogation', 37)))
        c.rolls.append(replace(conv.attach(c, roll('Moriko', 'interrogation', 50)), discarded=True))
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 20 - the treasury: Jimen 37@2 DETECTED',
        )


class TestNothingHiddenReachesTheBio:
    """SC-001. Both halves are rendered from the SAME conversation."""

    def test_no_hidden_total_in_any_public_line(self) -> None:
        c = scene()
        public = '\n'.join(rules.render_lines(c.rolls, 'Fumitake'))
        assert public == (
            "interrogation: 37@2 Jimen / 24@1 Moriko - Chizuru's death: nothing hidden detected\n"
            'acting: 32@1 Jimen - posing as a rice factor: '
            'no signs of the persona being seen through'
        )
        for secret in ('31', '27', 'sincerity', 'investigation', 'tied', 'wins'):
            assert secret not in public, secret

    def test_the_line_reads_the_same_with_and_without_a_sincerity_roll(self) -> None:
        with_roll = rules.render_lines(scene().rolls[:2], 'Fumitake')
        c = talking()
        lines.new_line_of_questioning("Chizuru's death", collector=lambda x: None, now=lambda: W)
        c.rolls.append(conv.attach(c, roll('Tsuruchi Jimen', 'interrogation', 37)))
        c.rolls.append(conv.attach(c, roll('Moriko', 'interrogation', 24, rank=1, minute=2)))
        assert rules.render_lines(c.rolls, 'Fumitake') == with_roll

    def test_a_held_acting_roll_is_written_bare(self) -> None:
        bare = roll('Jimen', 'acting', 32, rank=1)
        assert rules.render_lines([bare], 'Fumitake', include_unannotated=True) == [
            'acting: 32@1 Jimen'
        ]

    def test_a_typed_outcome_replaces_the_default(self) -> None:
        shown = rules.render_annotated(
            roll('Jimen', 'acting', 32, rank=None, note='a monk', outcome='he squinted'), 'Fumitake'
        )
        assert shown == 'acting: 32 Jimen - a monk: he squinted'


class TestRewrite:
    def test_a_new_block_is_appended(self) -> None:
        assert hidden.rewrite(NOTES, (), ('- a',)) == 'XP: 65\nHonor: 3.0\n\nHidden rolls:\n- a'
        assert hidden.rewrite('', (), ('- a',)) == 'Hidden rolls:\n- a'
        assert hidden.rewrite(NOTES, (), ()) == NOTES

    def test_this_conversation_s_entries_are_swapped_and_older_ones_kept(self) -> None:
        first = hidden.rewrite(NOTES, (), ('- old session',))
        second = hidden.rewrite(first, (), ('- a',)) + '\n\nBackstory follows.'
        third = hidden.rewrite(second, ('- a',), ('- a2', '- b'))
        assert 'Hidden rolls:\n- old session\n- a2\n- b\n\nBackstory follows.' in third
        assert third.count('Hidden rolls:') == 1

    def test_an_emptied_block_loses_its_heading(self) -> None:
        only = hidden.rewrite(NOTES, (), ('- a',))
        assert 'Hidden rolls:' not in hidden.rewrite(only, ('- a',), ())


class TestPersistence:
    def tick(self, c: Conversation, record: dict[str, Any], **kw: Any) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        def update(npc_id: str, **fields: Any) -> None:
            if kw.get('fail') and 'game_master_info' in fields:
                raise RuntimeError('OP is down')
            calls.append(fields)
            record.update(fields)

        conv._tick(
            c,
            collector=lambda x: x,
            get_body=lambda i: record,
            update=update,
            clock=kw.get('clock', lambda: 100.0),
            debounce=kw.get('debounce', 0.0),
        )
        return calls

    def test_the_numbers_and_the_hidden_rolls_go_to_the_gm_only_notes(self) -> None:
        c = scene()
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        calls = self.tick(c, record)
        assert [sorted(f) for f in calls] == [['bio'], ['game_master_info']]
        assert 'NPC numbers:\n- Air 3\n- sincerity 5' in record['game_master_info']
        assert 'Hidden rolls:\n- 2026-09-19 sincerity 31' in record['game_master_info']
        assert 'sincerity' not in record['bio']
        assert '31' not in record['bio']
        assert self.tick(c, record) == []

    def test_a_tagged_roll_alone_is_written_with_no_player_rolls(self) -> None:
        c = talking()
        dice.xky(5, 3) - npcskills.build_tags()['tact']
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        calls = self.tick(c, record)
        assert [sorted(f) for f in calls] == [['game_master_info']]
        assert c.numbers_written == {'air': 3, 'tact': 2}

    def test_a_second_gm_only_write_is_debounced(self) -> None:
        c = talking()
        tags = npcskills.build_tags()
        dice.xky(5, 3) - tags['tact']
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        assert len(self.tick(c, record, debounce=120.0)) == 1
        dice.xky(5, 3) - tags['sincerity']
        assert self.tick(c, record, debounce=120.0, clock=lambda: 150.0) == []
        assert len(self.tick(c, record, debounce=120.0, clock=lambda: 300.0)) == 1

    def test_a_failed_gm_only_write_never_costs_the_bio(self) -> None:
        c = scene()
        said: list[str] = []
        conv.say = said.append  # type: ignore[assignment]
        record: dict[str, Any] = {'bio': BIO, 'game_master_info': NOTES}
        calls = self.tick(c, record, fail=True)
        assert [sorted(f) for f in calls] == [['bio']]
        assert c.hidden_written == ()
        assert any('GM-only notes' in s for s in said)


class TestLoading:
    def test_numbers_and_school_come_off_the_record(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking()
        conv.load_numbers(
            c,
            lambda i: {
                'game_master_info': 'NPC numbers:\n- Air 3\n- tact 2',
                'tags': ['Merchant'],
                'description': '',
            },
        )
        assert c.numbers == {'air': 3, 'tact': 2}
        assert c.numbers_written == c.numbers
        assert c.schools == ('merchant',)
        assert 'on record for Fumitake: Air 3, tact 2' in capsys.readouterr().out

    def test_an_unreachable_record_is_an_empty_one(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking()
        conv.load_numbers(c, lambda i: None)
        assert c.numbers == {}
        assert c.schools == ()
        assert capsys.readouterr().out == ''

    def test_begin_conversation_loads_them(self) -> None:
        cast = [{'id': 'f', 'name': 'Fumitake'}]
        c = conv.begin_conversation(
            'Fumitake',
            'test',
            characters=lambda: cast,
            watch=False,
            get_body=lambda i: {'game_master_info': 'NPC numbers:\n- Air 4'},
        )
        assert c.numbers == {'air': 4}
