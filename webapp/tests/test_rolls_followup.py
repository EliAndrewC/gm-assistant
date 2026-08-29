"""Feature 202 follow-up: pre-conversation rolls, discard, per-side contest bonuses."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl import gmrolls
from l7r.repl.dice import DiceTotal, xky
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')

W = datetime(2026, 8, 29, 2, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def clean() -> Any:
    conv._open = None
    gmrolls.clear()
    yield
    conv._open = None
    gmrolls.clear()


def roll(name: str, skill: str, total: int, **kw: Any) -> Roll:
    return Roll(
        character=name, skill=skill, total=total, source='recorded', message_id='1', at=W, **kw
    )


def conversation(*rolls: Roll) -> Conversation:
    c = Conversation(npc={'id': 'x', 'name': 'Otsuki'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    return c


class TestPreConversationRolls:
    """The GM rolls the NPC's side FIRST - "that is actually the most common workflow"."""

    def test_a_roll_with_no_conversation_open_is_still_recorded(self) -> None:
        total = xky(7, 4, print_dice=False) + 8
        assert len(gmrolls.recent()) == 1
        assert gmrolls.recent()[0].total == int(total)

    def test_opening_a_conversation_does_not_discard_it(self) -> None:
        xky(7, 4, print_dice=False)
        gmrolls.start()
        assert len(gmrolls.recent()) == 1, 'the roll made just before opening is the point'

    def test_closing_does_not_discard_it_either(self) -> None:
        xky(7, 4, print_dice=False)
        gmrolls.stop()
        assert len(gmrolls.recent()) == 1

    def test_xky_always_returns_the_recording_total_now(self) -> None:
        assert isinstance(xky(6, 3, print_dice=False), DiceTotal)

    def test_the_buffer_is_bounded(self) -> None:
        for _ in range(gmrolls.BUFFER + 5):
            xky(2, 1, print_dice=False)
        assert len(gmrolls.recent()) == gmrolls.BUFFER

    def test_clear_empties_it(self) -> None:
        xky(2, 1, print_dice=False)
        gmrolls.clear()
        assert gmrolls.recent() == ()


class TestSkillInference:
    """A skill roll is (Ring + skill)k(Ring), so 7k4 implies skill 3."""

    def test_infers_from_the_pool(self) -> None:
        xky(7, 4, print_dice=False)
        assert gmrolls.recent()[0].skill == 3

    def test_uses_the_pool_the_gm_ASKED_for_not_the_capped_one(self) -> None:
        """Above ten dice, actual_xky turns the excess into a flat bonus.

        Inferring from the dice actually rolled would give the wrong skill on every
        large pool, which is the case the GM warned about.
        """
        xky(14, 4, print_dice=False)
        assert gmrolls.recent()[0].skill == 10, 'from 14k4 as asked, not the capped pool'

    def test_a_roll_with_no_recorded_pool_falls_back_to_the_dice(self) -> None:
        entry = gmrolls.record((10, 9, 8), 2, 19)
        assert entry.skill == 1


class TestFreeRaises:
    """rules/02-skills.md:64 - one free raise per point of skill difference, +5 each."""

    def test_the_higher_skill_gets_the_raises(self) -> None:
        assert rules.free_raises(4, 2) == (10, 0)

    def test_the_gms_own_example(self) -> None:
        """ "one character has two points... a different character has four points...
        that character will get a plus ten"."""
        mine, theirs = rules.free_raises(2, 4)
        assert (mine, theirs) == (0, 10)

    def test_equal_skills_give_nothing(self) -> None:
        assert rules.free_raises(3, 3) == (0, 0)

    def test_an_unknown_skill_infers_nothing(self) -> None:
        assert rules.free_raises(None, 3) == (0, 0)
        assert rules.free_raises(3, None) == (0, 0)

    def test_a_raise_is_five(self) -> None:
        assert rules.FREE_RAISE == 5


class TestPerSideBonuses:
    """The GM: a player's own total must not drop because their opponent got raises."""

    def test_a_bonus_to_the_npc_raises_the_npc(self) -> None:
        r = roll('Jimen', 'law', 30, note='the argument', opposed_total=30, bonus_opposed=10)
        line = rules.render_annotated(r, 'Otsuki')
        assert '30 vs 40' in line, "Jimen's own 30 survives"
        assert 'Otsuki by 10' in line

    def test_a_bonus_to_the_player_raises_the_player(self) -> None:
        r = roll('Jimen', 'law', 30, note='the argument', opposed_total=30, bonus_self=10)
        assert '40 vs 30' in rules.render_annotated(r, 'Otsuki')

    def test_bonuses_are_never_netted(self) -> None:
        """Same margin either way, but the recorded totals differ - which is the point."""
        theirs = roll('J', 'law', 30, note='x', opposed_total=30, bonus_opposed=10)
        netted = roll('J', 'law', 20, note='x', opposed_total=30)
        assert rules.render_annotated(theirs, 'O') != rules.render_annotated(netted, 'O')

    def test_an_open_roll_still_takes_its_own_bonus(self) -> None:
        r = roll('Jimen', 'law', 38, note='the argument', bonus_self=5)
        assert rules.render_annotated(r, 'Otsuki') == 'Jimen law: 40 - the argument'


class TestFinalTotals:
    def test_an_open_roll_has_no_opposing_total(self) -> None:
        assert roll('A', 'law', 40).final_opposed is None

    def test_each_side_carries_its_own_bonus(self) -> None:
        r = roll('A', 'law', 40, opposed_total=30, bonus_self=5, bonus_opposed=10)
        assert r.final_total == 45
        assert r.final_opposed == 40


class TestDiscard:
    def test_a_discarded_roll_needs_no_annotation(self) -> None:
        assert not rules.needs_annotation(roll('A', 'law', 40, discarded=True))

    def test_it_is_not_written(self) -> None:
        c = conversation(roll('A', 'law', 40, discarded=True, note='ignored'))
        assert rules.render_lines(c.rolls, c.npc_name) == []

    def test_it_is_not_written_even_by_the_forced_exit_path(self) -> None:
        c = conversation(roll('A', 'law', 40, discarded=True))
        assert rules.render_lines(c.rolls, c.npc_name, include_unannotated=True) == []

    def test_it_is_not_offered_again(self) -> None:
        c = conversation(roll('A', 'law', 40, discarded=True))
        assert ann.pending(c) == []

    def test_it_does_not_block_the_close(self) -> None:
        c = conversation(roll('A', 'law', 40, discarded=True))
        conv._open = c
        conv.end_conversation(
            get_body=lambda cid: {'bio': ''},
            update=lambda cid, **kw: None,
            collector=lambda x: x,
        )
        assert conv._open is None

    def test_the_menu_can_discard(self) -> None:
        c = conversation(roll('A', 'law', 40))
        assert ann.annotate(c, ask=lambda q: 'd') == 1
        assert c.rolls[0].discarded
        assert c.rolls[0].note == ''

    def test_ctrl_c_discards_the_discard_too(self) -> None:
        c = conversation(roll('A', 'law', 40), roll('B', 'precepts', 30))
        answers = iter(['1', 'd'])

        def ask(question: str) -> str:
            try:
                return next(answers)
            except StopIteration:
                raise KeyboardInterrupt from None

        assert ann.annotate(c, ask=ask) == 0
        assert not c.rolls[0].discarded, 'a staged discard is abandoned like an annotation'


class TestContestedMenu:
    def _npc_roll(self, asked: tuple[int, int] = (7, 4), base: int = 31) -> None:
        gmrolls.record((10, 9, 8, 4, 2, 1, 1), 4, base, asked=asked)

    def test_offers_a_pre_conversation_roll(self) -> None:
        self._npc_roll()
        c = conversation(roll('Jimen', 'law', 44, rank=4))
        answers = iter(['c', '1', '', '', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].opposed_total == 31

    def test_defaults_to_the_inferred_free_raises(self) -> None:
        self._npc_roll()  # implies skill 3
        c = conversation(roll('Jimen', 'law', 44, rank=4))  # skill 4, so +5 to Jimen
        answers = iter(['c', '1', '', '', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].bonus_self == 5
        assert c.rolls[0].bonus_opposed == 0

    def test_the_gm_can_override_either_side(self) -> None:
        self._npc_roll()
        c = conversation(roll('Jimen', 'law', 44, rank=4))
        answers = iter(['c', '1', '0', '20', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].bonus_self == 0
        assert c.rolls[0].bonus_opposed == 20

    def test_a_negative_override_is_accepted(self) -> None:
        self._npc_roll()
        c = conversation(roll('Jimen', 'law', 44, rank=4))
        answers = iter(['c', '1', '-6', '', 'oppose knowledge'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].bonus_self == -6

    def test_a_bad_bonus_is_re_asked(self, capsys: Any) -> None:
        self._npc_roll()
        c = conversation(roll('Jimen', 'law', 44, rank=4))
        answers = iter(['c', '1', 'lots', '3', '', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert 'whole number' in capsys.readouterr().out
        assert c.rolls[0].bonus_self == 3

    def test_no_rank_means_no_inferred_bonus(self, capsys: Any) -> None:
        self._npc_roll()
        c = conversation(roll('Jimen', 'law', 44))  # rank unknown
        answers = iter(['c', '1', '', '', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].bonus_self == 0
        assert 'no recorded rank' in capsys.readouterr().out

    def test_no_recent_rolls_falls_back_to_open(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'law', 44, rank=4))
        answers = iter(['c', 'the argument'])
        ann.annotate(c, ask=lambda q: next(answers), mine=lambda: ())
        assert c.rolls[0].opposed_total is None
        assert 'no recent rolls' in capsys.readouterr().out
