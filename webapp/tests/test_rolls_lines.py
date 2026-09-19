"""Feature 207: lines of questioning declared by the GM, and the hidden Sincerity roll."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import hidden, lines, rules
from l7r.repl.rolls.models import Conversation, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')
W = datetime(2026, 9, 19, 1, 0, tzinfo=UTC)


def roll(name: str, total: int, *, rank: int | None = 2, minute: int = 0, skill: str = 'interrogation') -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='recorded',
        message_id=f'{name}-{minute}',
        at=W + timedelta(minutes=minute),
        rank=rank,
    )


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 6)
    yield
    conv._open = None
    gmrolls.clear()


def talking(*rolls: Roll) -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    conv._open = c
    return c


def declare(topic: str, sincerity: Any = None, *, minute: int = 0, replies: tuple[Any, ...] = (), **kw: Any) -> list[str]:
    asked: list[str] = []
    queue = list(replies)

    def ask(question: str) -> str:
        asked.append(question)
        reply = queue.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return str(reply)

    lines.new_line_of_questioning(
        topic,
        sincerity,
        ask=ask,
        collector=lambda c: None,
        now=lambda: W + timedelta(minutes=minute),
        **kw,
    )
    return asked


class TestDeclaring:
    def test_rolls_made_after_a_declaration_land_on_it(self) -> None:
        c = talking()
        declare("Chizuru's death", minute=1)
        got = conv.attach(c, roll('Tsuruchi Jimen', 37, minute=2))
        assert (got.line, got.note, got.grilling) == (1, "Chizuru's death", False)

    def test_each_roll_goes_to_the_line_current_when_it_was_made(self) -> None:
        c = talking()
        declare('the treasury', minute=1)
        declare('the escorts', minute=5, grilling=True)
        early = conv.attach(c, roll('Jimen', 30, minute=3))
        late = conv.attach(c, roll('Jimen', 31, minute=6))
        assert (early.line, late.line, late.grilling) == (1, 2, True)

    def test_a_roll_older_than_the_first_line_is_never_attached_silently(self) -> None:
        c = talking()
        declare('the treasury', minute=5)
        assert conv.attach(c, roll('Jimen', 30, minute=1)).line is None

    def test_other_skills_and_attached_rolls_pass_through(self) -> None:
        c = talking()
        declare('the treasury', minute=1)
        law = roll('Jimen', 30, minute=2, skill='law')
        assert conv.attach(c, law) is law

    def test_the_early_first_roll_is_asked_about_and_joins_by_default(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking(roll('Tsuruchi Jimen', 37, minute=0), roll('Moriko', 24, rank=1, minute=1))
        asked = declare("Chizuru's death", minute=2, replies=('', 'd'))
        assert len(asked) == 2 and 'Jimen 37@2' in asked[0] and '[P/d]' in asked[0]
        assert c.rolls[0].line == 1 and c.rolls[0].note == "Chizuru's death"
        assert c.rolls[1].discarded
        assert "Line of questioning: Chizuru's death" in capsys.readouterr().out

    def test_only_a_repeat_roll_on_the_line_being_left_is_asked_about(self) -> None:
        c = talking()
        declare('the treasury', minute=1)
        for r in (roll('Jimen', 30, minute=2), roll('Moriko', 20, minute=3), roll('Jimen', 35, minute=4)):
            c.rolls.append(conv.attach(c, r))
        asked = declare('the escorts', minute=5, replies=('p',))
        assert len(asked) == 1 and 'Jimen 35' in asked[0]
        assert [r.line for r in c.rolls] == [1, 1, 2]
        assert c.rolls[2].note == 'the escorts'

    def test_a_useless_answer_is_asked_again(self) -> None:
        c = talking(roll('Jimen', 37))
        asked = declare('the treasury', minute=2, replies=('x', 'p'))
        assert len(asked) == 2 and c.rolls[0].line == 1

    @pytest.mark.parametrize('interrupt', [KeyboardInterrupt(), EOFError()])
    def test_ctrl_c_abandons_the_declaration_whole(self, interrupt: BaseException) -> None:
        c = talking(roll('Jimen', 37))
        declare('the treasury', minute=2, replies=(interrupt,))
        assert c.lines == [] and c.rolls[0].line is None

    def test_it_collects_first(self) -> None:
        c = talking()
        seen: list[Conversation] = []
        lines.new_line_of_questioning('the treasury', collector=seen.append, ask=lambda q: '')
        assert seen == [c]

    def test_a_blank_topic_and_no_conversation(self) -> None:
        with pytest.raises(conv.NoConversation):
            declare('the treasury')
        talking()
        with pytest.raises(ValueError, match='what the line of questioning is about'):
            declare('   ')

    def test_ids_never_collide_with_a_roll_s_old_line(self) -> None:
        c = talking()
        c.rolls.append(Roll('Jimen', 'interrogation', 30, 'recorded', 'm', W, line=7, note='old'))
        declare('the treasury', minute=1, replies=())
        assert c.lines[0].id == 8


class TestTheSincerityRoll:
    def test_a_live_roll_is_tagged_and_its_numbers_recorded(self) -> None:
        c = talking()
        declare('the treasury', dice.xky(8, 3) + 10)
        assert c.numbers == {'air': 3, 'sincerity': 5}
        assert isinstance(c.lines[0].sincerity, gmrolls.GmRoll)
        assert c.lines[0].sincerity.total == 28 and c.lines[0].sincerity.tagged == 'sincerity'

    def test_an_already_tagged_roll_and_a_bare_number(self) -> None:
        c = talking()
        tagged = dice.xky(8, 3) - conv.npcskills.build_tags()['sincerity']
        declare('one', tagged)
        declare('two', 41, minute=1)
        assert c.lines[1].sincerity == 41

    def test_a_roll_tagged_something_else_is_refused(self) -> None:
        talking()
        wrong = dice.xky(5, 3) - conv.npcskills.build_tags()['tact']
        with pytest.raises(ValueError, match='tagged tact, not sincerity'):
            declare('the treasury', wrong)

    def test_a_roll_judged_a_mistake_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking()
        c.numbers.update(air=3, sincerity=2)
        monkeypatch.setattr(ann, 'ask_quietly', lambda q: 'm')
        with pytest.raises(ValueError, match='marked a mistake'):
            declare('the treasury', dice.xky(8, 3))
        assert c.lines == []

    def test_a_later_bonus_still_counts(self) -> None:
        c = talking()
        total = dice.xky(8, 3)
        declare('the treasury', total)
        total + 15
        found = hidden.compare(c, c.lines[0], roll('Jimen', 40, rank=5))
        assert found is not None and found.sincerity == 33


class TestComparison:
    def test_free_raises_and_the_casual_bonus(self) -> None:
        c = talking()
        declare('the treasury', dice.xky(5, 3))  # 18, sincerity 2
        found = hidden.compare(c, c.lines[0], roll('Tsuruchi Jimen', 20, rank=4))
        assert found is not None
        assert (found.bonus, found.casual, found.npc_bonus) == (10, 10, 0)
        assert found.detected
        assert found.describe() == 'Jimen 20 (+10) vs sincerity 18 (+10 not grilling): DETECTED'

    def test_the_npc_s_free_raises_and_a_tie(self) -> None:
        c = talking()
        declare('the treasury', dice.xky(8, 3), grilling=True)  # 18, sincerity 5
        found = hidden.compare(c, c.lines[0], roll('Jimen', 33, rank=2))
        assert found is not None and found.theirs == 33 and found.detected
        assert found.describe() == 'Jimen 33 vs sincerity 18 (+15 free raises): DETECTED'
        lost = hidden.compare(c, c.lines[0], roll('Jimen', 32, rank=2))
        assert lost is not None and not lost.detected

    def test_no_sincerity_roll_is_no_comparison(self) -> None:
        c = talking()
        declare('the treasury')
        assert hidden.compare(c, c.lines[0], roll('Jimen', 33)) is None

    def test_a_bare_number_infers_no_rank(self) -> None:
        c = talking()
        declare('the treasury', 30)
        found = hidden.compare(c, c.lines[0], roll('Jimen', 33, rank=3))
        assert found is not None and (found.bonus, found.npc_bonus) == (0, 0)

    def test_an_unrecorded_rank_is_read_off_the_dice_less_the_school_die(self) -> None:
        c = talking()
        c.schools = ('merchant',)
        entry = dice.xky(8, 3).entry
        assert hidden.sincerity_rank(c, entry) == 4

    def test_joining_rolls_are_compared_at_the_declaration(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        talking(roll('Jimen', 50, rank=5))
        declare('the treasury', dice.xky(8, 3), minute=1, replies=('',))
        assert '= Jimen 50 vs sincerity 18 (+10 not grilling): DETECTED' in capsys.readouterr().out

    def test_the_watcher_announces_it(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking()
        declare('the treasury', dice.xky(8, 3))
        said: list[str] = []
        monkeypatch.setattr(conv, 'say', said.append)
        attached = conv.attach(c, roll('Jimen', 20, minute=1))
        conv.announce_comparison(c, attached)
        conv.announce_comparison(c, roll('Jimen', 20, skill='law'))
        assert said == ['  = Jimen 20 vs sincerity 18 (+10 not grilling, +15 free raises): not detected']


class TestGrilling:
    def test_retroactive_and_public(self, capsys: pytest.CaptureFixture[str]) -> None:
        c = talking()
        declare('the treasury', dice.xky(8, 3))
        c.rolls.append(conv.attach(c, roll('Jimen', 40, rank=5, minute=1)))
        lines.grilling()
        assert c.lines[0].grilling and c.rolls[0].grilling
        assert '= Jimen 40 vs sincerity 18: DETECTED' in capsys.readouterr().out
        assert rules.render_lines(c.rolls, 'Fumitake')[0].startswith('interrogation (grilling):')

    def test_twice_changes_nothing_and_says_so(self, capsys: pytest.CaptureFixture[str]) -> None:
        talking()
        declare('the treasury', grilling=True)
        lines.grilling()
        assert 'already recorded' in capsys.readouterr().out

    def test_with_no_line(self) -> None:
        talking()
        with pytest.raises(ValueError, match='no line of questioning yet'):
            lines.grilling()


class TestDetected:
    def setup_rolls(self) -> Conversation:
        c = talking()
        declare('the treasury', minute=0)
        for r in (roll('Tsuruchi Jimen', 37, minute=1), roll('Moriko', 24, rank=1, minute=2)):
            c.rolls.append(conv.attach(c, r))
        return c

    def test_the_pc_gets_their_own_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        c = self.setup_rolls()
        lines.detected('jimen', 'he is lying about the amount')
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            'interrogation: 37@2 Jimen - the treasury: he is lying about the amount',
            'interrogation: 24@1 Moriko - the treasury: nothing hidden detected',
        ]
        assert 'he is lying about the amount' in capsys.readouterr().out

    def test_everyone_detecting_the_same_thing_stays_grouped(self) -> None:
        c = self.setup_rolls()
        lines.detected('Tsuruchi Jimen', 'he is lying')
        lines.detected('Moriko', 'he is lying')
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            'interrogation: 37@2 Jimen / 24@1 Moriko - the treasury: he is lying'
        ]

    def test_an_earlier_line_by_number(self) -> None:
        c = self.setup_rolls()
        declare('the escorts', minute=5)
        lines.detected('Moriko', 'a flicker of guilt', line=1)
        assert c.rolls[1].outcome == 'a flicker of guilt'
        with pytest.raises(ValueError, match='no line 3'):
            lines.detected('Moriko', 'x', line=3)

    def test_someone_with_no_roll_there(self) -> None:
        self.setup_rolls()
        with pytest.raises(ValueError, match='Rolls there: Jimen, Moriko'):
            lines.detected('Tetsuro', 'x')
        declare('the escorts', minute=5)
        with pytest.raises(ValueError, match='nobody yet'):
            lines.detected('Jimen', 'x')

    def test_it_needs_words(self) -> None:
        self.setup_rolls()
        with pytest.raises(ValueError, match='what they detected'):
            lines.detected('Jimen', '  ')


class TestLooseEnds:
    def test_the_default_prompt_is_the_quiet_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(roll('Jimen', 37))
        monkeypatch.setattr(ann, 'ask_quietly', lambda q: 'd')
        lines.new_line_of_questioning('the treasury', collector=lambda x: None)
        assert c.rolls[0].discarded

    def test_a_discarded_repeat_is_not_asked_about(self) -> None:
        c = talking()
        declare('the treasury', minute=1)
        c.rolls.append(conv.attach(c, roll('Jimen', 30, minute=2)))
        c.rolls.append(replace(conv.attach(c, roll('Jimen', 35, minute=3)), discarded=True))
        assert lines.candidates(c) == []
