"""Feature 207: `annotate()` asks what each skill's MODE leaves to ask."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')
W = datetime(2026, 9, 19, 1, 0, tzinfo=UTC)
KIND_PROMPT = 'Open, contested, discard, or open with bonus?'


def roll(name: str, skill: str, total: int, *, rank: int | None = None, minute: int = 0) -> Roll:
    return Roll(
        name, skill, total, 'recorded', f'{name}{minute}', W + timedelta(minutes=minute), rank
    )


def conversation(*rolls: Roll, **numbers: int) -> Conversation:
    c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    c.numbers.update(numbers)
    return c


def gm(total: int, asked: tuple[int, int], *, tagged: str = '', minute: int = 0) -> gmrolls.GmRoll:
    entry = gmrolls.record((9,) * asked[0], asked[1], total, asked=asked)
    entry.tagged = tagged
    entry.at = W + timedelta(minutes=minute)
    return entry


@pytest.fixture(autouse=True)
def clean() -> Iterator[None]:
    conv._open = None
    gmrolls.clear()
    yield
    conv._open = None
    gmrolls.clear()


class Script:
    """Scripted answers. `UNDO` stands for the two-press keystroke; an exception
    instance is raised instead of returned."""

    UNDO = object()

    def __init__(self, *answers: Any) -> None:
        self.answers = list(answers)
        self.asked: list[str] = []

    def __call__(self, question: str) -> str:
        self.asked.append(question)
        reply = self.answers.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        assert reply is not Script.UNDO, f'the keystroke was sent to a plain prompt: {question}'
        return str(reply)

    def undoable(self, question: str, ask: Any) -> tuple[bool, str]:
        if self.answers and self.answers[0] is Script.UNDO:
            self.asked.append(question)
            self.answers.pop(0)
            return True, ''
        return False, self(question)

    def was_asked(self, fragment: str) -> bool:
        return any(fragment in q for q in self.asked)


def run(c: Conversation, *answers: Any) -> Script:
    script = Script(*answers)
    ann.annotate(c, ask=script, undoable=script.undoable, mine=gmrolls.recent)
    return script


class TestAlwaysOpen:
    def test_pontificate_is_asked_only_what_it_was_for(self) -> None:
        c = conversation(roll('Jimen', 'pontificate', 31))
        script = run(c, 'lecturing on the Tao')
        assert len(script.asked) == 1
        assert not script.was_asked(KIND_PROMPT)
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            '30 pontificate: Jimen - lecturing on the Tao'
        ]

    def test_contested_is_refused_but_a_bonus_and_discard_are_not(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'athletics', 25), roll('Moriko', 'athletics', 20, minute=1))
        run(c, '1', 'c', 'ob', '5', 'climbing the wall', 'd')
        assert 'athletics is never rolled that way' in capsys.readouterr().out
        assert c.rolls[0].bonus_self == 5
        assert c.rolls[0].note == 'climbing the wall'
        assert c.rolls[1].discarded

    def test_blank_finishes(self) -> None:
        c = conversation(roll('Jimen', 'athletics', 25))
        run(c, '')
        assert c.rolls[0].note == ''


class TestDefaultOpen:
    def test_open_is_already_selected(self) -> None:
        c = conversation(roll('Jimen', 'history', 44))
        script = run(c, 'the fall of the Snake Clan')
        assert len(script.asked) == 1
        assert 'backspace twice' in script.asked[0]
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            '40 history: Jimen - the fall of the Snake Clan'
        ]

    def test_the_keystroke_reaches_the_full_menu(self) -> None:
        gm(28, (5, 3))
        c = conversation(roll('Jimen', 'history', 44, rank=2))
        script = run(c, Script.UNDO, 'c', '1', '', '', 'arguing the precedent')
        assert script.was_asked(KIND_PROMPT)
        assert c.rolls[0].opposed_total == 28

    def test_blank_at_the_full_menu_after_an_undo_finishes(self) -> None:
        c = conversation(roll('Jimen', 'history', 44))
        run(c, Script.UNDO, '')
        assert c.rolls[0].note == ''

    def test_a_bare_c_does_the_same_without_a_terminal(self) -> None:
        gm(28, (5, 3))
        c = conversation(roll('Jimen', 'investigation', 44, rank=2))
        run(c, 'c', '1', '', '', 'spotting the tail')
        assert c.rolls[0].opposed_total == 28

    def test_investigation_behaves_as_history_does(self) -> None:
        c = conversation(roll('Jimen', 'investigation', 44))
        script = run(c, 'searching the room')
        assert len(script.asked) == 1

    def test_ctrl_c_at_the_keystroke_abandons_the_run(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'history', 44))

        def undoable(question: str, ask: Any) -> tuple[bool, str]:
            raise KeyboardInterrupt

        ann.annotate(c, ask=Script(), undoable=undoable)
        assert 'nothing saved' in capsys.readouterr().out
        assert c.rolls[0].note == ''


class TestManipulation:
    def test_a_tagged_tact_roll_is_paired_and_only_the_note_is_asked(self, capsys: Any) -> None:
        entry = gm(28, (5, 3), tagged='tact')
        c = conversation(roll('Tsuruchi Jimen', 'manipulation', 41, rank=3), tact=2)
        script = run(c, 'twisting his words about the escort')
        assert len(script.asked) == 1
        assert not script.was_asked(KIND_PROMPT)
        out = capsys.readouterr().out
        assert 'Paired with your tact roll' in out
        assert 'manipulation 3 vs your tact 2' in out
        assert (c.rolls[0].opposed_total, c.rolls[0].bonus_self, c.rolls[0].bonus_opposed) == (
            28,
            5,
            0,
        )
        assert entry.paired
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            'Jimen vs Fumitake manipulation vs tact: 46 vs 28, Jimen wins by >=10 '
            'twisting his words about the escort'
        ]

    def test_an_unrecorded_rank_is_read_off_the_paired_roll(self) -> None:
        gm(28, (7, 3), tagged='tact')
        c = conversation(roll('Jimen', 'manipulation', 41, rank=2))
        run(c, 'x')
        assert (c.rolls[0].bonus_self, c.rolls[0].bonus_opposed) == (0, 10)

    def test_the_nearest_unused_tagged_roll_is_chosen(self) -> None:
        far, near = gm(20, (5, 3), tagged='tact', minute=0), gm(30, (5, 3), tagged='tact', minute=9)
        c = conversation(
            roll('Jimen', 'manipulation', 41, minute=10),
            roll('Moriko', 'manipulation', 35, minute=11),
        )
        run(c, '1', 'first', 'second')
        assert [r.opposed_total for r in c.rolls] == [30, 20]
        assert far.paired
        assert near.paired

    def test_a_paired_roll_is_not_offered_to_a_later_run(self) -> None:
        gm(28, (5, 3), tagged='tact').paired = True
        c = conversation(roll('Jimen', 'manipulation', 41, rank=3))
        script = run(c, 'f', '', '', 'x')
        assert script.was_asked('Opposed by which tact roll?')

    def test_fifteen_presumes_a_tact_of_zero(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'manipulation', 41, rank=3))
        script = run(c, 'f', '', '', 'x')
        assert 'f for 15 - no roll made' in script.asked[0]
        assert 'number' not in script.asked[0]
        assert 'Bonus to Jimen? [15]' in script.asked[1]
        assert (c.rolls[0].opposed_total, c.rolls[0].bonus_self, c.rolls[0].bonus_opposed) == (
            15,
            15,
            0,
        )
        assert 'vs your tact 0' in capsys.readouterr().out

    def test_open_and_nobody_are_never_offered(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'manipulation', 41, rank=3))
        script = run(c, 'n', 'o', 'f', '', '', 'x')
        assert 'nobody' not in script.asked[0]
        assert capsys.readouterr().out.count('  ? ') == 2
        assert c.rolls[0].opposed_total == 15

    def test_the_undo_reaches_the_picker_and_an_untagged_roll(self) -> None:
        gm(28, (5, 3), tagged='tact')
        gm(33, (6, 3))
        c = conversation(roll('Jimen', 'manipulation', 41, rank=2))
        script = run(c, Script.UNDO, '2', '', '', 'x')
        assert script.was_asked('number, f for 15')
        assert c.rolls[0].opposed_total == 33

    def test_a_typed_total(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'manipulation', 41))
        run(c, 't', '23', '', '', 'x')
        assert c.rolls[0].opposed_total == 23
        assert 'no recorded rank' in capsys.readouterr().out

    def test_a_typed_total_with_a_known_player_rank_but_no_tact_on_record(
        self, capsys: Any
    ) -> None:
        c = conversation(roll('Jimen', 'manipulation', 41, rank=2))
        run(c, 't', '23', '', '', 'x')
        assert 'No rank known for your tact' in capsys.readouterr().out

    def test_discard_and_finish(self) -> None:
        gm(28, (5, 3), tagged='tact')
        c = conversation(
            roll('Jimen', 'manipulation', 41),
            roll('Moriko', 'manipulation', 30, minute=1),
            roll('Tetsuro', 'manipulation', 30, minute=2),
        )
        run(c, '1', 'd', '1', 'd', '')
        assert c.rolls[0].discarded
        assert c.rolls[1].discarded
        assert c.rolls[2].note == ''

    def test_blank_at_the_paired_prompt_finishes(self) -> None:
        gm(28, (5, 3), tagged='tact')
        c = conversation(roll('Jimen', 'manipulation', 41))
        run(c, '')
        assert c.rolls[0].note == ''

    def test_a_roll_marked_a_mistake_is_never_paired(self) -> None:
        gm(28, (5, 3), tagged='tact').mistake = True
        c = conversation(roll('Jimen', 'manipulation', 41))
        script = run(c, '')
        assert script.was_asked('Opposed by which tact roll?')


class TestSneaking:
    def test_nobody_opposed_it_is_written_like_an_open_line(self) -> None:
        c = conversation(roll('Tsuruchi Jimen', 'sneaking', 28))
        script = run(c, 'n', 'blending into the crowd')
        assert 'n for nobody opposed it' in script.asked[0]
        assert 'f for 15' not in script.asked[0]
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            '25 sneaking: Jimen - blending into the crowd'
        ]

    def test_a_tagged_investigation_roll_is_paired(self) -> None:
        gm(30, (6, 3), tagged='investigation')
        c = conversation(roll('Jimen', 'sneaking', 30, rank=3), investigation=3)
        run(c, 'slipping past the gate guard')
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            'Jimen vs Fumitake sneaking vs investigation: 30 vs 30, Fumitake wins by <5 '
            'slipping past the gate guard'
        ]


class TestThePickersLettersWorkAtAPairedPrompt:
    """A scripted session found `n` being taken as the NOTE of a pre-paired sneaking
    roll, which wrote a contest that never happened."""

    def test_n_at_a_paired_sneaking_prompt_means_nobody(self) -> None:
        entry = gm(23, (6, 3), tagged='investigation')
        c = conversation(roll('Tsuruchi Jimen', 'sneaking', 28))
        run(c, 'n', 'blending into the crowd')
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            '25 sneaking: Jimen - blending into the crowd'
        ]
        assert not entry.paired

    def test_f_at_a_paired_manipulation_prompt_means_fifteen(self) -> None:
        gm(28, (5, 3), tagged='tact')
        c = conversation(roll('Jimen', 'manipulation', 41, rank=3))
        run(c, 'f', '', '', 'x')
        assert c.rolls[0].opposed_total == 15

    def test_t_types_a_total_and_n_is_refused_where_it_cannot_apply(self, capsys: Any) -> None:
        gm(28, (5, 3), tagged='tact')
        c = conversation(roll('Jimen', 'manipulation', 41, rank=3))
        run(c, 'n', 't', '19', '', '', 'x')
        assert 'manipulation is never rolled that way' in capsys.readouterr().out
        assert c.rolls[0].opposed_total == 19


class TestActing:
    def test_the_opposing_roll_is_taken_and_never_written(self) -> None:
        gm(27, (5, 3), tagged='investigation')
        c = conversation(roll('Tsuruchi Jimen', 'acting', 32, rank=1), investigation=2)
        script = run(c, 'posing as a rice factor', '')
        assert script.was_asked('What did they get? [no signs of the persona being seen through]')
        assert not script.was_asked(KIND_PROMPT)
        assert (c.rolls[0].opposed_total, c.rolls[0].bonus_opposed) == (27, 5)
        assert rules.render_lines(c.rolls, 'Fumitake') == [
            'acting: 32@1 Jimen - posing as a rice factor: '
            'no signs of the persona being seen through'
        ]

    def test_a_typed_outcome_and_a_missing_rank(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'acting', 32))
        run(c, 't', '40', '', '', 'posing as a monk', '2', 'the abbot looked twice')
        assert 'staged: acting: 32@2 Jimen - posing as a monk: the abbot looked twice' in (
            capsys.readouterr().out
        )
        assert c.rolls[0].rank == 2
        assert c.rolls[0].opposed_total == 40

    def test_open_nobody_and_fifteen_are_never_offered(self) -> None:
        c = conversation(roll('Jimen', 'acting', 32, rank=1))
        script = run(c, '')
        assert 'nobody' not in script.asked[0]
        assert 'f for 15' not in script.asked[0]
        assert 'investigation' in script.asked[0]

    def test_discard(self) -> None:
        c = conversation(roll('Jimen', 'acting', 32, rank=1))
        run(c, 'd')
        assert c.rolls[0].discarded


class TestFullMenuIsUnchanged:
    def test_a_recorded_rank_now_sets_the_default_raises(self, capsys: Any) -> None:
        gm(28, (9, 3))
        c = conversation(roll('Jimen', 'law', 44, rank=3), law=1)
        run(c, 'c', '1', '', '', 'the warrant')
        assert c.rolls[0].bonus_self == 10
        assert 'vs your law 1' in capsys.readouterr().out
