"""Feature 207: `xky(5, 3) - tact`, `tact()`, `tact(vp)` - and what they remember."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import npcskills as ns
from l7r.repl.rolls.models import Conversation

ann = importlib.import_module('l7r.repl.rolls.annotate')
W = datetime(2026, 9, 19, 1, 0, tzinfo=UTC)
TAGS = ns.build_tags()
tact, sincerity, acting, history, law = (
    TAGS['tact'],
    TAGS['sincerity'],
    TAGS['acting'],
    TAGS['history'],
    TAGS['law'],
)


@pytest.fixture(autouse=True)
def clean(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    monkeypatch.setattr(dice, 'd10', lambda reroll=True: 5)
    yield
    conv._open = None
    gmrolls.clear()


def talking(**numbers: int) -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    c.numbers.update(numbers)
    conv._open = c
    return c


def answers(monkeypatch: pytest.MonkeyPatch, *replies: Any) -> list[str]:
    """Feed the quiet prompt; an exception instance is raised instead of returned."""
    asked: list[str] = []
    queue = list(replies)

    def fake(question: str) -> str:
        asked.append(question)
        reply = queue.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return str(reply)

    monkeypatch.setattr(ann, 'ask_quietly', fake)
    return asked


class TestTagging:
    def test_the_gm_s_example_records_ring_and_rank(self, capsys: pytest.CaptureFixture[str]) -> None:
        c = talking()
        total = dice.xky(5, 3) - tact
        assert int(total) == 15
        assert c.numbers == {'air': 3, 'tact': 2}
        assert 'recorded for Fumitake: Air 3, tact 2' in capsys.readouterr().out
        assert gmrolls.recent()[-1].tagged == 'tact'

    def test_a_flat_bonus_changes_the_total_and_nothing_else(self) -> None:
        c = talking()
        total = dice.xky(8, 3) + 10 - sincerity
        assert int(total) == 25
        assert c.numbers == {'air': 3, 'sincerity': 5}
        assert int(total + 5) == 30

    def test_a_school_die_comes_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        c = talking()
        c.schools = ('merchant',)
        dice.xky(8, 3) - sincerity
        assert c.numbers['sincerity'] == 4
        assert 'merchant school' in capsys.readouterr().out

    def test_a_second_agreeing_roll_says_nothing_new(self, capsys: pytest.CaptureFixture[str]) -> None:
        talking(air=3, tact=2)
        dice.xky(5, 3) - tact
        assert 'recorded' not in capsys.readouterr().out

    def test_no_conversation_marks_the_roll_and_records_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dice.xky(5, 3) - tact
        assert gmrolls.recent()[-1].tagged == 'tact'
        assert 'nothing is recorded' in capsys.readouterr().out

    def test_a_second_tag_is_an_error(self) -> None:
        talking()
        total = dice.xky(5, 3) - tact
        with pytest.raises(ValueError, match='already tagged tact'):
            total - sincerity

    def test_a_plain_number_cannot_be_tagged(self) -> None:
        with pytest.raises(TypeError, match='only a roll can be tagged'):
            15 - tact  # type: ignore[operator]

    def test_ordinary_subtraction_still_works(self) -> None:
        assert int(dice.xky(5, 3) - 5) == 10

    def test_more_than_ten_dice_reads_the_pool_as_asked(self) -> None:
        c = talking()
        dice.xky(12, 4) - law
        assert c.numbers == {'water': 4, 'law': 5} or c.numbers['law'] == 8
        assert c.numbers['water'] == 4


class TestDisagreement:
    def test_the_record_was_wrong(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(air=3, tact=2)
        asked = answers(monkeypatch, 'x', 'r')
        dice.xky(6, 3) - tact
        assert c.numbers == {'air': 3, 'tact': 3}
        assert len(asked) == 2
        assert not gmrolls.recent()[-1].mistake

    def test_the_roll_was_a_mistake(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, 'm')
        dice.xky(6, 3) - tact
        assert c.numbers == {'air': 3, 'tact': 2}
        assert gmrolls.recent() == ()

    @pytest.mark.parametrize('interrupt', [KeyboardInterrupt(), EOFError()])
    def test_ctrl_c_is_caught_and_means_a_mistake(
        self, monkeypatch: pytest.MonkeyPatch, interrupt: BaseException
    ) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, interrupt)
        total = dice.xky(6, 3) - tact
        assert int(total) == 15
        assert c.numbers == {'air': 3, 'tact': 2}
        assert total.entry.mistake

    def test_no_void_answer_when_it_is_not_a_void_point_shape(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        talking(air=3, tact=2)
        answers(monkeypatch, 'v', 'm')
        dice.xky(6, 3) - tact
        assert '[v]' not in capsys.readouterr().out

    def test_this_roll_spent_a_void_point(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, 'v')
        total = dice.xky(6, 4) - tact
        assert '[v] This roll spent a void point' in capsys.readouterr().out
        assert c.numbers == {'air': 3, 'tact': 2}
        assert total.entry.void_points == 1 and not total.entry.mistake

    def test_this_roll_s_void_point_still_records_an_unknown_rank(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = talking(air=3)
        answers(monkeypatch, 'v')
        dice.xky(9, 4) - sincerity
        assert c.numbers == {'air': 3, 'sincerity': 5}

    def test_the_previous_roll_spent_two(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking(air=5, tact=2)
        answers(monkeypatch, 'v')
        dice.xky(5, 3) - tact
        assert '[v] The previous roll spent 2 void points' in capsys.readouterr().out
        assert c.numbers == {'air': 3, 'tact': 2}


class TestCalling:
    def test_from_the_record(self) -> None:
        talking(air=3, tact=2)
        total = tact()
        assert total is not None
        assert total.entry.asked == (5, 3) and total.entry.tagged == 'tact'

    def test_a_missing_rank_is_asked_for_within_bounds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(air=3)
        asked = answers(monkeypatch, '6', 'lots', '5')
        total = sincerity()
        assert total is not None and total.entry.asked == (8, 3)
        assert c.numbers['sincerity'] == 5
        assert '[0-5]' in asked[0]

    def test_a_stated_rank_and_a_missing_ring(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking()
        asked = answers(monkeypatch, '7', '3')
        total = sincerity(2)
        assert total is not None and total.entry.asked == (5, 3)
        assert c.numbers == {'sincerity': 2, 'air': 3}
        assert '[2-6]' in asked[0]

    def test_a_pool_is_the_tag_form(self) -> None:
        c = talking()
        total = tact(5, 3)
        assert total is not None and total.entry.asked == (5, 3)
        assert c.numbers == {'air': 3, 'tact': 2}

    def test_a_void_point_is_known_about(self) -> None:
        c = talking(air=3, tact=2)
        one, two = tact(ns.vp), tact(ns.vp * 2)
        assert one is not None and two is not None
        assert one.entry.asked == (6, 4) and two.entry.asked == (7, 5)
        assert one.entry.void_points == 1 and two.entry.void_points == 2
        assert c.numbers == {'air': 3, 'tact': 2}

    def test_vp_combines_with_a_rank_and_with_a_pool(self) -> None:
        c = talking(air=3)
        ranked = tact(2, ns.vp)
        pooled = tact(5, 3, 2 * ns.vp)
        assert ranked is not None and ranked.entry.asked == (6, 4)
        assert pooled is not None and pooled.entry.asked == (7, 5)
        assert c.numbers == {'air': 3, 'tact': 2}

    def test_a_school_die_goes_into_the_pool(self) -> None:
        c = talking(air=3, sincerity=4)
        c.schools = ('merchant',)
        total = sincerity()
        assert total is not None and total.entry.asked == (8, 3)

    def test_a_stated_rank_that_disagrees(self, monkeypatch: pytest.MonkeyPatch) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, '?', 'r')
        assert tact(3) is not None
        assert c.numbers['tact'] == 3

    @pytest.mark.parametrize('reply', ['m', KeyboardInterrupt(), EOFError()])
    def test_a_stated_rank_taken_back_rolls_nothing(
        self, monkeypatch: pytest.MonkeyPatch, reply: Any
    ) -> None:
        c = talking(air=3, tact=2)
        answers(monkeypatch, reply)
        assert tact(3) is None
        assert c.numbers['tact'] == 2 and gmrolls.recent() == ()

    def test_rank_zero_does_not_reroll_and_advanced_takes_ten(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seen: list[bool] = []
        monkeypatch.setattr(dice, 'd10', lambda reroll=True: seen.append(reroll) or 5)
        talking(air=3, tact=0, manipulation=0)
        plain = tact()
        advanced = TAGS['manipulation']()
        assert plain is not None and int(plain) == 15 and plain.entry.asked == (3, 3)
        assert advanced is not None and int(advanced) == 5
        assert seen == [False] * 6
        assert '-10: an advanced skill at rank 0' in capsys.readouterr().out

    def test_no_conversation(self) -> None:
        with pytest.raises(RuntimeError, match='no NPC to roll tact for'):
            tact()

    def test_too_many_numbers_and_a_bad_rank(self) -> None:
        talking(air=3)
        with pytest.raises(TypeError):
            tact(1, 2, 3)
        with pytest.raises(ValueError, match='from 0 to 5'):
            tact(9)


class TestRecordedNotRolled:
    def test_acting_records_and_never_rolls(self, capsys: pytest.CaptureFixture[str]) -> None:
        c = talking()
        assert acting(2) is None
        assert c.numbers == {'acting': 2} and gmrolls.recent() == ()
        assert 'recorded for Fumitake: acting 2' in capsys.readouterr().out

    def test_with_no_argument_it_reports_or_asks(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = talking(history=3)
        history()
        assert 'Fumitake: history 3' in capsys.readouterr().out
        answers(monkeypatch, '1')
        acting()
        assert c.numbers['acting'] == 1

    def test_a_pool_or_a_void_point_is_refused(self) -> None:
        talking()
        with pytest.raises(TypeError, match='recorded, never rolled'):
            acting(6, 3)
        with pytest.raises(TypeError, match='recorded, never rolled'):
            history(ns.vp)

    def test_it_can_still_tag_a_real_roll(self) -> None:
        c = talking()
        dice.xky(6, 3) - history
        assert c.numbers == {'water': 3, 'history': 3}


class TestAutomaticRaises:
    def test_the_called_form_adds_them_and_says_so(self, capsys: pytest.CaptureFixture[str]) -> None:
        talking(air=3, sincerity=5, acting=2)
        total = sincerity()
        assert total is not None and int(total) == 25
        assert '+10 acting 2' in capsys.readouterr().out

    def test_the_pool_form_adds_them_too(self) -> None:
        talking(acting=2)
        total = sincerity(8, 3)
        assert total is not None and int(total) == 25

    def test_a_tagged_xky_never_gets_them(self) -> None:
        talking(acting=2)
        assert int(dice.xky(8, 3) - sincerity) == 15

    def test_history_on_law_but_not_heraldry(self) -> None:
        talking(water=3, law=2, heraldry=2, history=3)
        a, b = law(), TAGS['heraldry']()
        assert a is not None and b is not None
        assert int(a) == 30 and int(b) == 15


class TestSmallThings:
    def test_vp_reads_like_what_was_typed(self) -> None:
        assert repr(ns.vp) == 'vp' and repr(ns.vp * 2) == 'vp * 2'
        with pytest.raises(ValueError):
            ns.VoidPoints(0)

    def test_a_tag_explains_itself(self) -> None:
        assert 'tags a roll' in repr(tact)

    def test_one_tag_per_rules_skill(self) -> None:
        assert len(TAGS) == 18 and TAGS['tact'].ring_name == 'air'
        assert TAGS['history'].advanced and not TAGS['tact'].advanced

    def test_no_rules_mount_means_no_tags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def gone() -> dict[str, str]:
            raise FileNotFoundError

        monkeypatch.setattr(ns, 'skill_rings', gone)
        assert ns.build_tags() == {}

    def test_an_unlisted_school_adds_nothing(self) -> None:
        assert ns.extra_dice('tact', ('no such school',)) == (0, '')


def test_stating_the_recorded_rank_just_rolls() -> None:
    talking(air=3, tact=2)
    total = tact(2)
    assert total is not None and total.entry.asked == (5, 3)
