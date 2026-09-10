"""Feature 206: interrogation rolls, written alone, exact, and grouped by line of questioning.

The leak this closes, in the GM's words (2026-09-10): *"contested interrogation rolls
are never displayed; if someone knows how high the NPC rolled on sincerity, then they
would know whether the 'doesn't seem to be holding anything back' result represents
truthfulness or if that is simply because the interrogator didn't roll high enough."*
So an interrogation roll is never paired with the GM's Sincerity roll, is written
exactly as rolled with the interrogator's rank attached, and rolls on one line of
questioning share one written line.
"""

from __future__ import annotations

import importlib
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest

from l7r.repl import gmrolls
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls import rules
from l7r.repl.rolls.models import Conversation, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')

W = datetime(2026, 9, 10, 1, 0, tzinfo=UTC)
BIO = '[[File:1 | class=media-item-align-none | Otsuki.png]]\r\n\r\nA silk merchant.\r\n'


def roll(
    name: str,
    skill: str = 'interrogation',
    total: int = 37,
    *,
    rank: int | None = None,
    minute: int = 0,
    note: str = '',
    line: int | None = None,
    grilling: bool = False,
) -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='recorded',
        message_id=f'{name}-{minute}',
        at=datetime(2026, 9, 10, 1, minute, tzinfo=UTC),
        rank=rank,
        note=note,
        line=line,
        grilling=grilling,
    )


def conversation(*rolls: Roll) -> Conversation:
    c = Conversation(npc={'id': 'otsuki-id', 'name': 'Otsuki'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    return c


class Script:
    """A scripted `ask` that remembers every question it was asked."""

    def __init__(self, *answers: str) -> None:
        self.answers = iter(answers)
        self.asked: list[str] = []

    def __call__(self, question: str) -> str:
        self.asked.append(question)
        return next(self.answers)

    def was_asked(self, fragment: str) -> bool:
        return any(fragment in q for q in self.asked)


@pytest.fixture(autouse=True)
def clean() -> Any:
    conv._open = None
    gmrolls.stop()
    yield
    conv._open = None
    gmrolls.stop()


ESCORTS = 'what Fumitake ordered his escorts to do'
OPINION = 'what Fumitake thinks of Tsuruchi'


class TestTheGmsExamples:
    """The two lines from the GM's request, in the shape the GM accepted."""

    def test_two_interrogators_on_one_grilling_line(self) -> None:
        line = [
            roll('Tsuruchi Jimen', total=37, rank=2, note=ESCORTS, line=1, grilling=True),
            roll('Moriko', total=24, rank=1, minute=1, note=ESCORTS, line=1, grilling=True),
        ]
        assert rules.render_interrogation(line) == (
            f'interrogation (grilling): 37@2 Jimen / 24@1 Moriko - {ESCORTS}'
        )

    def test_one_interrogator_on_a_casual_line(self) -> None:
        line = [roll('Tsuruchi Jimen', total=25, rank=2, note=OPINION, line=2)]
        assert rules.render_interrogation(line) == f'interrogation: 25@2 Jimen - {OPINION}'


class TestLinesOfQuestioning:
    def test_rolls_sharing_an_id_are_one_line(self) -> None:
        a = roll('Jimen', note=ESCORTS, line=1)
        b = roll('Moriko', total=24, minute=1, note=ESCORTS, line=1)
        assert rules.lines_of_questioning([a, b]) == [[a, b]]

    def test_one_roller_on_two_topics_is_two_lines(self) -> None:
        a = roll('Jimen', note=ESCORTS, line=1)
        b = roll('Jimen', total=25, minute=5, note=OPINION, line=2)
        assert rules.lines_of_questioning([a, b]) == [[a], [b]]

    def test_lines_come_in_the_order_their_first_roll_was_made(self) -> None:
        a = roll('Jimen', note=ESCORTS, line=7)
        b = roll('Moriko', total=25, minute=1, note=OPINION, line=3)
        c = roll('Tetsuro', total=30, minute=2, note=ESCORTS, line=7)
        assert rules.lines_of_questioning([a, b, c]) == [[a, c], [b]]

    def test_a_discarded_roll_is_not_on_its_line(self) -> None:
        a = roll('Jimen', note=ESCORTS, line=1)
        b = replace(roll('Moriko', minute=1, note=ESCORTS, line=1), discarded=True)
        assert rules.lines_of_questioning([a, b]) == [[a]]

    def test_a_line_whose_only_roll_was_discarded_does_not_exist(self) -> None:
        b = replace(roll('Moriko', note=ESCORTS, line=1), discarded=True)
        assert rules.lines_of_questioning([b]) == []

    def test_an_unannotated_interrogation_roll_is_on_no_line(self) -> None:
        assert rules.lines_of_questioning([roll('Jimen')]) == []

    def test_other_skills_are_never_lines(self) -> None:
        assert rules.lines_of_questioning([roll('Jimen', 'law', note='x', line=1)]) == []

    def test_an_unattributed_roll_is_left_out(self) -> None:
        assert rules.lines_of_questioning([roll('', note=ESCORTS, line=1)]) == []


class TestRenderInterrogation:
    def test_the_total_is_exact_never_rounded(self) -> None:
        assert rules.render_interrogation([roll('Jimen', total=37, note='x', line=1)]) == (
            'interrogation: 37 Jimen - x'
        )

    def test_no_rank_means_no_at(self) -> None:
        assert '@' not in rules.render_interrogation([roll('Jimen', note='x', line=1)])

    def test_an_opposing_total_and_bonuses_are_ignored(self) -> None:
        """A pre-feature roll annotated as contested renders as if it never was."""
        plain = roll('Jimen', total=37, rank=2, note='x', line=1)
        contested = replace(plain, opposed_total=28, bonus_self=10, bonus_opposed=5)
        assert rules.render_interrogation([contested]) == rules.render_interrogation([plain])
        assert 'vs' not in rules.render_interrogation([contested])
        assert '47' not in rules.render_interrogation([contested])

    def test_highest_roll_first(self) -> None:
        low = roll('Moriko', total=24, rank=1, note='x', line=1)
        high = roll('Jimen', total=37, rank=2, minute=1, note='x', line=1)
        assert rules.render_interrogation([low, high]).startswith('interrogation: 37@2 Jimen / ')

    def test_a_tie_keeps_the_order_the_rolls_were_made(self) -> None:
        a = roll('Moriko', total=30, note='x', line=1)
        b = roll('Jimen', total=30, minute=1, note='x', line=1)
        assert rules.render_interrogation([a, b]) == 'interrogation: 30 Moriko / 30 Jimen - x'
        assert rules.render_interrogation([b, a]) == 'interrogation: 30 Jimen / 30 Moriko - x'

    def test_a_bare_roll_has_no_note_and_no_dash(self) -> None:
        """What the exit path writes for a roll the GM never annotated."""
        assert rules.render_interrogation([roll('Jimen', rank=2)]) == 'interrogation: 37@2 Jimen'

    def test_the_personal_name_only(self) -> None:
        line = rules.render_interrogation([roll('Tsuruchi Jimen', note='x', line=1)])
        assert 'Tsuruchi' not in line

    def test_nothing_to_render_is_an_error(self) -> None:
        with pytest.raises(ValueError, match='no rolls'):
            rules.render_interrogation([])


class TestRenderLines:
    def test_a_line_sits_where_its_first_roll_was_made(self) -> None:
        c = conversation(
            roll('Jimen', 'etiquette', 28),
            roll('Jimen', 'law', 44, minute=1, note='the warrant'),
            roll('Jimen', total=37, rank=2, minute=2, note=ESCORTS, line=1, grilling=True),
            roll('Tetsuro', 'precepts', 30, minute=3, note='the oath'),
            roll('Moriko', total=24, rank=1, minute=4, note=ESCORTS, line=1, grilling=True),
        )
        assert rules.render_lines(c.rolls, 'Otsuki') == [
            'Jimen etiquette: 25',
            '40 law: Jimen - the warrant',
            f'interrogation (grilling): 37@2 Jimen / 24@1 Moriko - {ESCORTS}',
            '30 precepts: Tetsuro - the oath',
        ]

    def test_an_unannotated_interrogation_roll_is_held(self) -> None:
        assert rules.render_lines([roll('Jimen')], 'Otsuki') == []

    def test_the_exit_path_writes_each_held_roll_bare_and_ungrouped(self) -> None:
        held = [roll('Jimen', rank=2), roll('Moriko', total=24, rank=1, minute=1)]
        assert rules.render_lines(held, 'Otsuki', include_unannotated=True) == [
            'interrogation: 37@2 Jimen',
            'interrogation: 24@1 Moriko',
        ]

    def test_an_annotated_roll_with_no_line_is_its_own_line(self) -> None:
        """A roll annotated before this feature: no line id, but a note."""
        old = replace(roll('Jimen', rank=2, note=ESCORTS), opposed_total=28)
        assert rules.render_lines([old], 'Otsuki') == [f'interrogation: 37@2 Jimen - {ESCORTS}']

    def test_the_contested_line_is_never_used_for_interrogation(self) -> None:
        old = replace(roll('Jimen', rank=2, note=ESCORTS), opposed_total=28)
        for line in rules.render_lines([old], 'Otsuki', include_unannotated=True):
            assert 'wins' not in line
            assert 'vs' not in line

    def test_other_skills_still_contest(self) -> None:
        c = conversation(replace(roll('Jimen', 'sincerity', 41, note='the lie'), opposed_total=28))
        assert rules.render_lines(c.rolls, 'Otsuki') == [
            'Jimen vs Otsuki sincerity vs interrogation: 41 vs 28, Jimen wins by >=10 the lie'
        ]


KIND_PROMPT = 'Open, contested, discard, or open with bonus?'


class TestTheMenu:
    """US2: join-or-new replaces the o/c/d/ob prompt for this one skill."""

    def test_the_first_interrogation_roll_is_offered_new_or_discard_only(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        script = Script('n', '', ESCORTS)
        ann.annotate(c, ask=script)
        assert script.was_asked('[n/d, blank to finish]')
        assert not script.was_asked('Lines of questioning so far')
        assert not script.was_asked('Join which line?')
        assert c.rolls[0].line is not None
        assert c.rolls[0].note == ESCORTS

    def test_the_kind_prompt_never_appears_for_interrogation(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        script = Script('n', '', ESCORTS)
        ann.annotate(c, ask=script)
        assert not script.was_asked(KIND_PROMPT)
        assert not script.was_asked('Bonus')

    def test_the_second_roll_sees_the_lines_and_joins_by_number(self, capsys: Any) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1, grilling=True),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        script = Script('1')
        ann.annotate(c, ask=script)
        out = capsys.readouterr().out
        assert 'Lines of questioning so far:' in out
        assert f'1. (grilling) {ESCORTS}' in out
        assert script.was_asked('Join which line?')
        assert not script.was_asked('Grilling?')
        assert not script.was_asked('line of questioning?')
        joined = c.rolls[1]
        assert (joined.line, joined.note, joined.grilling) == (1, ESCORTS, True)

    def test_n_starts_a_new_line_asking_grilling_then_the_note(self) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1, grilling=True),
            roll('Jimen', total=25, rank=2, minute=5),
        )
        script = Script('n', '', OPINION)
        ann.annotate(c, ask=script)
        grilling_at = next(i for i, q in enumerate(script.asked) if 'Grilling?' in q)
        note_at = next(i for i, q in enumerate(script.asked) if 'line of questioning?' in q)
        assert grilling_at < note_at
        new = c.rolls[1]
        assert new.line not in (None, 1)
        assert (new.note, new.grilling) == (OPINION, False)

    def test_the_staged_echo_shows_the_whole_line(self, capsys: Any) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1, grilling=True),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        ann.annotate(c, ask=Script('1'))
        assert (
            f'staged: interrogation (grilling): 37@2 Jimen / 24@1 Moriko - {ESCORTS}'
            in capsys.readouterr().out
        )

    def test_a_line_staged_in_this_run_is_offered_to_the_next_roll(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', rank=2), roll('Moriko', total=24, rank=1, minute=1))
        script = Script('1', 'n', 'y', ESCORTS, '1', '1')
        ann.annotate(c, ask=script)
        assert f'1. (grilling) {ESCORTS}' in capsys.readouterr().out
        assert c.rolls[0].line == c.rolls[1].line
        assert rules.render_lines(c.rolls, 'Otsuki') == [
            f'interrogation (grilling): 37@2 Jimen / 24@1 Moriko - {ESCORTS}'
        ]

    def test_the_gms_whole_example_end_to_end(self) -> None:
        c = conversation(
            roll('Tsuruchi Jimen', rank=2),
            roll('Moriko', total=24, rank=1, minute=1),
            roll('Tsuruchi Jimen', total=25, rank=2, minute=6),
        )
        script = Script('1', 'n', 'y', ESCORTS, '1', '1', 'n', '', OPINION)
        ann.annotate(c, ask=script)
        assert rules.render_lines(c.rolls, 'Otsuki') == [
            f'interrogation (grilling): 37@2 Jimen / 24@1 Moriko - {ESCORTS}',
            f'interrogation: 25@2 Jimen - {OPINION}',
        ]

    def test_a_bad_answer_at_the_join_prompt_is_re_asked(self, capsys: Any) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        script = Script('9', 'x', '1')
        ann.annotate(c, ask=script)
        assert c.rolls[1].line == 1
        assert '?' in capsys.readouterr().out

    def test_a_bad_answer_at_the_new_or_discard_prompt_is_re_asked(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        script = Script('1', 'x', 'n', '', ESCORTS)
        ann.annotate(c, ask=script)
        assert c.rolls[0].note == ESCORTS

    def test_blank_at_the_join_prompt_finishes(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        assert ann.annotate(c, ask=Script('')) is None
        assert c.rolls[0].line is None

    def test_an_empty_note_is_re_asked(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        ann.annotate(c, ask=Script('n', '', '', '   ', OPINION))
        assert c.rolls[0].note == OPINION

    def test_other_skills_still_get_the_kind_prompt(self) -> None:
        c = conversation(roll('Jimen', 'law', 44))
        script = Script('o', 'the warrant')
        ann.annotate(c, ask=script)
        assert script.was_asked(KIND_PROMPT)


class TestGrilling:
    @pytest.mark.parametrize('answer', ['y', 'Y', 'yes'])
    def test_yes_marks_the_line_grilling(self, answer: str) -> None:
        c = conversation(roll('Jimen', rank=2))
        ann.annotate(c, ask=Script('n', answer, ESCORTS))
        assert c.rolls[0].grilling
        assert rules.render_lines(c.rolls, 'Otsuki')[0].startswith('interrogation (grilling):')

    @pytest.mark.parametrize('answer', ['', 'n', 'no'])
    def test_blank_and_no_leave_it_casual(self, answer: str) -> None:
        c = conversation(roll('Jimen', rank=2))
        ann.annotate(c, ask=Script('n', answer, ESCORTS))
        assert not c.rolls[0].grilling
        assert rules.render_lines(c.rolls, 'Otsuki')[0].startswith('interrogation: ')

    def test_anything_else_is_re_asked(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', rank=2))
        ann.annotate(c, ask=Script('n', 'maybe', 'y', ESCORTS))
        assert c.rolls[0].grilling
        assert '?' in capsys.readouterr().out

    def test_joining_inherits_it_without_asking(self) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1, grilling=True),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        script = Script('1')
        ann.annotate(c, ask=script)
        assert c.rolls[1].grilling
        assert not script.was_asked('Grilling?')


class TestRank:
    def test_a_recorded_rank_is_not_asked_for(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        script = Script('n', '', ESCORTS)
        ann.annotate(c, ask=script)
        assert not script.was_asked('rank?')
        assert c.rolls[0].rank == 2

    def test_a_missing_rank_is_asked_for_after_the_join_prompt_and_before_grilling(self) -> None:
        c = conversation(roll('Jimen'))
        script = Script('n', '2', '', ESCORTS)
        ann.annotate(c, ask=script)
        assert script.was_asked("Jimen's interrogation rank? [none]")
        order = [
            next(i for i, q in enumerate(script.asked) if f in q)
            for f in ('[n/d', 'rank?', 'Grilling?', 'line of questioning?')
        ]
        assert order == sorted(order)
        assert c.rolls[0].rank == 2
        assert rules.render_lines(c.rolls, 'Otsuki') == [f'interrogation: 37@2 Jimen - {ESCORTS}']

    def test_blank_writes_the_roll_with_no_at(self) -> None:
        c = conversation(roll('Jimen'))
        ann.annotate(c, ask=Script('n', '', '', ESCORTS))
        assert c.rolls[0].rank is None
        assert rules.render_lines(c.rolls, 'Otsuki') == [f'interrogation: 37 Jimen - {ESCORTS}']

    def test_a_non_number_is_re_asked(self, capsys: Any) -> None:
        c = conversation(roll('Jimen'))
        ann.annotate(c, ask=Script('n', 'x', '-1', '2', '', ESCORTS))
        assert c.rolls[0].rank == 2
        assert '?' in capsys.readouterr().out

    def test_joining_still_asks_when_the_rank_is_missing(self) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1),
            roll('Moriko', total=24, minute=1),
        )
        script = Script('1', '1')
        ann.annotate(c, ask=script)
        assert script.was_asked("Moriko's interrogation rank?")
        assert c.rolls[1].rank == 1

    def test_no_other_skill_is_asked_for_a_rank(self) -> None:
        c = conversation(roll('Jimen', 'law', 44))
        script = Script('o', 'the warrant')
        ann.annotate(c, ask=script)
        assert not script.was_asked('rank?')


class TestEverythingElseStillHolds:
    """US5: what feature 202 established is untouched for this skill."""

    def test_end_conversation_refuses_while_one_is_unannotated(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        conv._open = c
        with pytest.raises(conv.NotAnnotated) as caught:
            conv.end_conversation(
                get_body=lambda cid: {'bio': BIO},
                update=lambda cid, **kw: None,
                collector=lambda x: x,
            )
        assert 'Jimen interrogation 37' in str(caught.value)
        assert conv._open is c

    def test_ctrl_c_abandons_every_staged_line(self, capsys: Any) -> None:
        c = conversation(
            roll('Jimen', rank=2),
            roll('Moriko', total=24, rank=1, minute=1),
            roll('Tetsuro', total=30, rank=1, minute=2),
        )
        answers = iter(['1', 'n', 'y', ESCORTS, '1', '1'])

        def ask(question: str) -> str:
            try:
                return next(answers)
            except StopIteration:
                raise KeyboardInterrupt from None  # at the third "which roll?"

        ann.annotate(c, ask=ask)
        assert all(r.line is None and r.note == '' and not r.grilling for r in c.rolls)
        assert 'nothing saved' in capsys.readouterr().out

    def test_discard_at_the_join_prompt(self) -> None:
        c = conversation(
            roll('Jimen', rank=2, note=ESCORTS, line=1),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        ann.annotate(c, ask=Script('d'))
        assert c.rolls[1].discarded
        assert rules.render_lines(c.rolls, 'Otsuki') == [f'interrogation: 37@2 Jimen - {ESCORTS}']

    def test_discard_at_the_new_or_discard_prompt(self) -> None:
        c = conversation(roll('Jimen', rank=2))
        ann.annotate(c, ask=Script('d'))
        assert c.rolls[0].discarded
        assert rules.render_lines(c.rolls, 'Otsuki', include_unannotated=True) == []

    def test_a_discarded_rolls_line_id_is_not_reused_for_a_live_one(self) -> None:
        """Harmless if it were - discarded rolls are on no line - but ids stay unique."""
        c = conversation(
            replace(roll('Jimen', rank=2, note='x', line=1), discarded=True),
            roll('Moriko', total=24, rank=1, minute=1),
        )
        ann.annotate(c, ask=Script('n', '', ESCORTS))
        assert c.rolls[1].line == 2

    def test_re_annotating_onto_another_line_moves_the_roll(self) -> None:
        """At the record level: a decision applied to an annotated roll replaces its line."""
        first = roll('Jimen', rank=2, note=ESCORTS, line=1)
        moved = ann._apply(first, ann.Decision(note=OPINION, line=2, rank=2))
        assert (moved.line, moved.note) == (2, OPINION)
        assert rules.render_lines([moved], 'Otsuki') == [f'interrogation: 37@2 Jimen - {OPINION}']

    def test_apply_never_sets_an_opposing_side(self) -> None:
        applied = ann._apply(roll('Jimen'), ann.Decision(note='x', line=1, grilling=True, rank=3))
        assert applied.opposed_total is None
        assert (applied.bonus_self, applied.bonus_opposed) == (0, 0)
        assert (applied.line, applied.grilling, applied.rank, applied.note) == (1, True, 3, 'x')

    def test_the_gms_own_sincerity_roll_is_never_offered(self, capsys: Any) -> None:
        gmrolls.clear()
        gmrolls.record((10, 9, 8, 1), 3, 20, asked=(4, 3))
        c = conversation(roll('Jimen', rank=2))
        script = Script('n', '', ESCORTS)
        ann.annotate(c, ask=script, mine=gmrolls.recent)
        assert not script.was_asked('Which of yours?')
        assert 'Your recent rolls' not in capsys.readouterr().out
        assert c.rolls[0].opposed_total is None

    def test_etiquette_in_the_same_conversation_is_unchanged(self) -> None:
        c = conversation(
            roll('Jimen', 'etiquette', 28),
            roll('Tetsuro', 'etiquette', 38, minute=1),
            roll('Jimen', rank=2, minute=2, note=ESCORTS, line=1),
        )
        assert rules.render_lines(c.rolls, 'Otsuki')[0] == 'Tetsuro / Jimen etiquette: 35 / 25'
