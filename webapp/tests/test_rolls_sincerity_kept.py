"""Every Sincerity roll made in a conversation reaches the GM-only notes (GM 2026-10-04).

Before this, only a roll HANDED to `new_line_of_questioning` was written; a
`sincerity()` or `xky(8, 3) - sincerity` made on its own went nowhere. Measured on
the live records: Tsuruchi Fumitake had two lines of questioning and `sincerity 0`
in his NPC numbers - so his Sincerity had been rolled - and no `Hidden rolls:` block.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import hidden, lines, npcskills
from l7r.repl.rolls.models import Conversation, Roll

W = datetime(2026, 9, 19, 1, 0, tzinfo=UTC)
TAGS = npcskills.build_tags()
sincerity = TAGS['sincerity']


def roll(name: str, total: int, *, minute: int = 1, **kw: Any) -> Roll:
    return Roll(
        name,
        'interrogation',
        total,
        'recorded',
        f'{name}{minute}',
        W + timedelta(minutes=minute),
        2,
        **kw,
    )


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 7)
    said: list[str] = []
    monkeypatch.setattr(conv, 'say', said.append)
    yield said
    conv._open = None
    gmrolls.clear()


def talking() -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    c.numbers.update(air=3, sincerity=5)
    conv._open = c
    return c


def declare(topic: str, secret: object = None, **kw: Any) -> None:
    lines.new_line_of_questioning(topic, secret, collector=lambda x: None, now=lambda: W, **kw)


def interrogated(c: Conversation, name: str, total: int, minute: int = 1) -> None:
    c.rolls.append(conv.attach(c, roll(name, total, minute=minute)))


class TestARollMadeOnItsOwn:
    def test_a_tagged_roll_after_the_declaration_opposes_the_line(self) -> None:
        c = talking()
        declare('debts to the Mantis', grilling=True)
        interrogated(c, 'Sadakichi', 57)
        dice.xky(8, 3) - sincerity
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 21 - debts to the Mantis: Sadakichi 57@2 DETECTED',
        )

    def test_the_called_form_too(self) -> None:
        c = talking()
        declare('debts to the Mantis', grilling=True)
        sincerity(8, 3)
        assert hidden.entries(c) == ('- 2026-09-19 sincerity 21 - debts to the Mantis',)

    def test_a_roll_before_any_line_belongs_to_the_first(self) -> None:
        c = talking()
        dice.xky(8, 3) - sincerity
        declare('the forest', grilling=True)
        declare('the monks', grilling=True)
        assert hidden.entries(c) == ('- 2026-09-19 sincerity 21 - the forest',)

    def test_a_second_roll_on_a_line_is_kept_and_says_what_it_followed(self) -> None:
        c = talking()
        declare('the monks', grilling=True)
        dice.xky(8, 3) - sincerity
        interrogated(c, 'Tsuruchi Jimen', 37)
        interrogated(c, 'Yudai', 7, minute=2)
        dice.xky(8, 3) + 3 - sincerity
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 21 - the monks: Jimen 37@2 DETECTED, Yudai 7@2 not detected',
            '- 2026-09-19 sincerity 24 - the monks (another sincerity roll on this line): '
            'after Yudai 7@2',
        )

    def test_a_roll_with_no_line_ever_declared_is_still_kept(self) -> None:
        c = talking()
        interrogated(c, 'Jimen', 30)
        dice.xky(8, 3) - sincerity
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 21 - before any line of questioning: after Jimen 30@2',
        )

    def test_a_roll_before_an_explicitly_rolled_first_line_is_extra(self) -> None:
        c = talking()
        dice.xky(8, 3) - sincerity
        declare('the forest', 40, grilling=True)
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 40 - the forest',
            '- 2026-09-19 sincerity 21 - before any line of questioning',
        )


class TestHandedToADeclaration:
    def test_it_is_that_line_s_and_not_the_previous_one_s(self) -> None:
        """`new_line_of_questioning("x", sincerity())` rolls while the OLD line is current."""
        c = talking()
        declare('the forest', grilling=True)
        declare('the monks', dice.xky(8, 3) - sincerity, grilling=True)
        assert c.sincerity_rolls == []
        assert hidden.entries(c) == ('- 2026-09-19 sincerity 21 - the monks',)

    def test_a_declaration_abandoned_with_ctrl_c_keeps_the_roll(self) -> None:
        c = talking()
        interrogated(c, 'Jimen', 30)

        def ctrl_c(question: str) -> str:
            raise KeyboardInterrupt

        declare('the monks', dice.xky(8, 3) - sincerity, ask=ctrl_c)
        assert c.lines == []
        assert hidden.entries(c) == (
            '- 2026-09-19 sincerity 21 - before any line of questioning: after Jimen 30@2',
        )


class TestNotHiddenRolls:
    def test_a_mistake_or_a_paired_roll_is_not_written(self) -> None:
        c = talking()
        declare('the monks', grilling=True)
        (dice.xky(8, 3) - sincerity).entry.mistake = True
        (dice.xky(8, 3) - sincerity).entry.paired = True
        assert hidden.entries(c) == ()
        conv.announce_sincerity(c)
        assert c.sincerity_announced == set()

    def test_nothing_is_kept_without_a_conversation(self) -> None:
        dice.xky(8, 3) - sincerity
        c = talking()
        assert c.sincerity_rolls == []

    def test_other_skills_are_not_kept(self) -> None:
        c = talking()
        dice.xky(5, 3) - TAGS['tact']
        assert c.sincerity_rolls == []


class TestAnnounced:
    def test_once_each_with_the_line_and_its_comparisons(self, clean: list[str]) -> None:
        c = talking()
        declare('the monks', grilling=True)
        interrogated(c, 'Jimen', 37)
        dice.xky(8, 3) - sincerity
        dice.xky(8, 3) - sincerity
        conv.announce_sincerity(c)
        conv.announce_sincerity(c)
        assert clean == [
            '  sincerity 21 kept in the GM-only notes against "the monks"',
            '  = Jimen 37 vs sincerity 21 (+15 free raises): DETECTED'
            ' - annotate() to say what they got',
            '  sincerity 21 kept in the GM-only notes - '
            'the monks (another sincerity roll on this line): after Jimen 37@2',
        ]

    def test_the_watcher_tick_announces_and_writes_them(self, clean: list[str]) -> None:
        c = talking()
        declare('the monks', grilling=True)
        dice.xky(8, 3) - sincerity
        record: dict[str, Any] = {'bio': '', 'game_master_info': ''}

        def update(npc_id: str, **fields: Any) -> None:
            record.update(fields)

        conv._tick(c, collector=lambda x: x, get_body=lambda i: record, update=update, debounce=0.0)
        assert '  sincerity 21 kept in the GM-only notes against "the monks"' in clean
        assert 'Hidden rolls:\n- 2026-09-19 sincerity 21 - the monks' in record['game_master_info']
