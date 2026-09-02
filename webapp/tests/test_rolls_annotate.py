"""Feature 202: holding rolls until the GM says what they were for.

The rule and its one exemption, in the GM's words: *"we should not record most
rolls unless they are annotated. Now we have not bothered to do this with etiquette
because etiquette rolls are presumed to be about making an introduction."*

And the two OPPOSITE rules for closing, which are the part most easily got wrong:
a manual `end_conversation()` RAISES, the interpreter-exit path SAVES.
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

#: `annotate` the function shadows `l7r.repl.rolls.annotate` the module on the
#: package, the same way `names` already does - reach the module explicitly.
ann = importlib.import_module('l7r.repl.rolls.annotate')

W = datetime(2026, 8, 29, 1, 0, tzinfo=UTC)
BIO = '[[File:1 | class=media-item-align-none | Otsuki.png]]\r\n\r\nA silk merchant.\r\n'


def roll(
    name: str, skill: str, total: int, *, rank: int | None = None, minute: int = 0, note: str = ''
) -> Roll:
    return Roll(
        character=name,
        skill=skill,
        total=total,
        source='recorded',
        message_id='1',
        at=datetime(2026, 8, 29, 1, minute, tzinfo=UTC),
        rank=rank,
        note=note,
    )


def conversation(*rolls: Roll) -> Conversation:
    c = Conversation(npc={'id': 'otsuki-id', 'name': 'Otsuki'}, opened_at=W, channels=('c',))
    c.rolls.extend(rolls)
    return c


@pytest.fixture(autouse=True)
def clean() -> Any:
    conv._open = None
    gmrolls.stop()
    yield
    conv._open = None
    gmrolls.stop()


class TestWhatNeedsAnnotating:
    def test_etiquette_never_does(self) -> None:
        assert not rules.needs_annotation(roll('A', 'etiquette', 28))

    def test_etiquette_is_case_insensitive(self) -> None:
        assert not rules.needs_annotation(roll('A', 'Etiquette', 28))

    def test_every_other_skill_does(self) -> None:
        for skill in ('precepts', 'law', 'sincerity', 'investigation'):
            assert rules.needs_annotation(roll('A', skill, 30)), skill

    def test_an_annotated_roll_no_longer_does(self) -> None:
        assert not rules.needs_annotation(roll('A', 'law', 30, note='the warrant'))

    def test_whitespace_is_not_an_annotation(self) -> None:
        assert rules.needs_annotation(roll('A', 'law', 30, note='   '))

    def test_the_exemption_is_one_entry_of_data(self) -> None:
        """Another exempt skill should be a data change, not a code change."""
        assert frozenset({'etiquette'}) == rules.EXEMPT_FROM_ANNOTATION


class TestRenderAnnotated:
    def test_an_open_roll_is_rounded_and_carries_its_note(self) -> None:
        line = rules.render_annotated(
            roll('Jimen', 'law', 44, note='assessing whether the arrest was lawful'), 'Otsuki'
        )
        assert line == '40 law: Jimen assessing whether the arrest was lawful'

    def test_the_number_leads_and_the_note_follows_the_name(self) -> None:
        """The GM's own worked example (2026-09-02): `{roll} {skill}: {name} {annotation}`."""
        line = rules.render_annotated(
            roll('Tsuruchi Jimen', 'tact', 10, note='asking how much money Fumitake owed'),
            'Otsuki',
        )
        assert line == '10 tact: Jimen asking how much money Fumitake owed'

    def test_a_bare_open_roll_is_the_same_line_without_the_note(self) -> None:
        """What the forced close on interpreter exit writes rather than losing it."""
        line = rules.render_annotated(roll('Tsuruchi Jimen', 'tact', 10), 'Otsuki')
        assert line == '10 tact: Jimen'

    def test_a_contested_roll_keeps_both_totals_raw(self) -> None:
        line = rules.render_annotated(
            replace(
                roll('Jimen', 'sincerity', 41, note='claiming he never met the man'),
                opposed_total=28,
            ),
            'Otsuki',
        )
        assert line == (
            'Jimen vs Otsuki sincerity: 41 vs 28, Jimen by >=10 - claiming he never met the man'
        )

    def test_the_npc_can_win(self) -> None:
        line = rules.render_annotated(
            replace(roll('Jimen', 'sincerity', 20, note='the lie'), opposed_total=44), 'Otsuki'
        )
        assert 'Otsuki by >=20' in line

    def test_the_npcs_own_family_name_is_stripped_too(self) -> None:
        line = rules.render_annotated(
            replace(roll('Tsuruchi Jimen', 'sincerity', 41, note='the lie'), opposed_total=28),
            'Bayushi Otsuki',
        )
        assert line == 'Jimen vs Otsuki sincerity: 41 vs 28, Jimen by >=10 - the lie'

    def test_a_contested_line_keeps_its_own_word_order(self) -> None:
        """Deliberately NOT harmonized with the open line: `41 vs 28` means nothing
        until you know who the two sides were, so the pairing leads."""
        line = rules.render_annotated(
            replace(roll('Jimen', 'sincerity', 41, note='the lie'), opposed_total=28), 'Otsuki'
        )
        assert line.startswith('Jimen vs Otsuki sincerity:')

    def test_a_tie(self) -> None:
        line = rules.render_annotated(
            replace(roll('Jimen', 'sincerity', 30, note='the lie'), opposed_total=30), 'Otsuki'
        )
        assert 'tied' in line


class TestWhatGetsWritten:
    def test_etiquette_writes_while_the_rest_wait(self) -> None:
        c = conversation(roll('Jimen', 'etiquette', 28), roll('Jimen', 'precepts', 25, minute=5))
        assert rules.render_lines(c.rolls, c.npc_name) == ['Jimen etiquette: 25']

    def test_an_annotated_roll_joins_the_record(self) -> None:
        c = conversation(
            roll('Jimen', 'etiquette', 28),
            roll('Jimen', 'precepts', 25, minute=5, note='reading the room'),
        )
        assert rules.render_lines(c.rolls, c.npc_name) == [
            'Jimen etiquette: 25',
            '25 precepts: Jimen reading the room',
        ]

    def test_annotated_rolls_keep_the_order_they_were_made(self) -> None:
        """The GM's reason for wanting annotation: reading the conversation back."""
        c = conversation(
            roll('A', 'law', 40, minute=9, note='third'),
            roll('B', 'precepts', 30, minute=2, note='first'),
            roll('C', 'sincerity', 35, minute=5, note='second'),
        )
        notes = [line.rsplit(' ', 1)[1] for line in rules.render_lines(c.rolls, c.npc_name)]
        assert notes == ['third', 'first', 'second'], 'collection order, not sorted'

    def test_etiquette_stays_one_line_highest_first(self) -> None:
        c = conversation(
            roll('A', 'etiquette', 19), roll('B', 'etiquette', 38), roll('C', 'etiquette', 28)
        )
        assert rules.render_lines(c.rolls, c.npc_name) == ['B / C / A etiquette: 35 / 25 / 15']


class TestClosing:
    """The two opposite rules. Manual raises; the exit path saves."""

    def test_a_manual_close_raises_and_names_the_rolls(self) -> None:
        c = conversation(roll('Jimen', 'precepts', 25), roll('Tetsuro', 'law', 44, minute=4))
        conv._open = c
        with pytest.raises(conv.NotAnnotated) as caught:
            conv.end_conversation(
                get_body=lambda cid: {'bio': BIO},
                update=lambda cid, **kw: None,
                collector=lambda x: x,
            )
        message = str(caught.value)
        assert 'Jimen precepts 25' in message
        assert 'Tetsuro law 44' in message
        assert 'annotate()' in message

    def test_the_conversation_is_still_open_after_the_raise(self) -> None:
        c = conversation(roll('Jimen', 'precepts', 25))
        conv._open = c
        with pytest.raises(conv.NotAnnotated):
            conv.end_conversation(
                get_body=lambda cid: {'bio': BIO},
                update=lambda cid, **kw: None,
                collector=lambda x: x,
            )
        assert conv._open is c, 'the conversation is NOT over'

    def test_nothing_is_written_by_the_refused_close(self) -> None:
        c = conversation(roll('Jimen', 'precepts', 25))
        conv._open = c
        seen: dict[str, Any] = {}
        with pytest.raises(conv.NotAnnotated):
            conv.end_conversation(
                get_body=lambda cid: {'bio': BIO},
                update=lambda cid, **kw: seen.update(kw),
                collector=lambda x: x,
            )
        assert seen == {}

    def test_only_etiquette_closes_normally(self) -> None:
        c = conversation(roll('Jimen', 'etiquette', 28))
        conv._open = c
        seen: dict[str, Any] = {}
        conv.end_conversation(
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: seen.update(kw),
            collector=lambda x: x,
        )
        assert 'Jimen etiquette: 25' in str(seen['bio'])
        assert conv._open is None

    def test_the_exit_path_SAVES_unannotated_rolls(self) -> None:
        """The opposite ruling: better recorded bare than lost."""
        c = conversation(roll('Jimen', 'precepts', 25))
        conv._open = c
        seen: dict[str, Any] = {}
        conv.close_open_conversation(
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: seen.update(kw),
            collector=lambda x: x,
        )
        assert '25 precepts: Jimen' in str(seen['bio'])
        assert conv._open is None

    def test_the_exit_path_says_it_saved_bare_rolls(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'precepts', 25))
        conv._open = c
        conv.close_open_conversation(
            get_body=lambda cid: {'bio': BIO},
            update=lambda cid, **kw: None,
            collector=lambda x: x,
        )
        assert 'unannotated' in capsys.readouterr().out


class TestAnnotateMenu:
    def test_nothing_waiting(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'etiquette', 28))
        assert ann.annotate(c, ask=lambda q: '') == 0
        assert 'Nothing waiting' in capsys.readouterr().out

    def test_one_waiting_roll_skips_the_which_prompt(self) -> None:
        c = conversation(roll('Jimen', 'precepts', 25))
        asked: list[str] = []

        def ask(question: str) -> str:
            # Match on substance, not the exact prompt text: an exact-string fake
            # silently loops forever the moment the wording changes, which is how
            # this test hung when the o/c prompt gained "blank to finish".
            asked.append(question)
            return 'o' if 'contested' in question else 'reading the room'

        assert ann.annotate(c, ask=ask) == 1
        assert not any('Which roll?' in q for q in asked)
        assert c.rolls[0].note == 'reading the room'

    def test_choosing_among_several(self) -> None:
        c = conversation(roll('Jimen', 'precepts', 25), roll('Tetsuro', 'law', 44, minute=4))
        answers = iter(['2', 'o', 'the warrant', '', ''])
        assert ann.annotate(c, ask=lambda q: next(answers)) == 1
        assert c.rolls[1].note == 'the warrant'
        assert c.rolls[0].note == '', 'the unchosen roll is untouched'

    def test_a_contested_annotation_uses_one_of_the_gms_rolls(self) -> None:
        c = conversation(roll('Jimen', 'sincerity', 41))
        gmrolls.clear()
        entry = gmrolls.record((10, 9, 8, 1), 3, 20, asked=(4, 3))
        entry.bonus = 8
        # two blanks accept the inferred per-side bonuses added by the follow-up
        answers = iter(['c', '1', '', '', 'claiming he never met the man'])
        ann.annotate(c, ask=lambda q: next(answers), mine=gmrolls.recent)
        assert c.rolls[0].opposed_total == 28
        assert c.rolls[0].contested
        assert 'Jimen by >=10' in rules.render_annotated(c.rolls[0], 'Otsuki')

    def test_contested_with_no_gm_rolls_falls_back_to_open(self, capsys: Any) -> None:
        c = conversation(roll('Jimen', 'sincerity', 41))
        answers = iter(['c', 'the lie'])
        ann.annotate(c, ask=lambda q: next(answers), mine=lambda: ())
        assert c.rolls[0].opposed_total is None
        assert 'no recent rolls' in capsys.readouterr().out

    def test_ctrl_c_discards_everything_staged(self, capsys: Any) -> None:
        """Four annotated then Ctrl-C loses all four - the literal reading."""
        c = conversation(
            roll('A', 'law', 40),
            roll('B', 'precepts', 30, minute=2),
            roll('C', 'sincerity', 35, minute=4),
        )

        answers = iter(['1', 'o', 'first note', '1', 'o', 'second note'])

        def ask(question: str) -> str:
            try:
                return next(answers)
            except StopIteration:
                raise KeyboardInterrupt from None

        assert ann.annotate(c, ask=ask) == 0
        assert all(r.note == '' for r in c.rolls), 'nothing at all is saved'
        assert 'nothing saved' in capsys.readouterr().out

    def test_ctrl_d_is_the_same_as_ctrl_c(self) -> None:
        c = conversation(roll('A', 'law', 40))

        def ask(question: str) -> str:
            raise EOFError

        assert ann.annotate(c, ask=ask) == 0
        assert c.rolls[0].note == ''

    def test_a_blank_line_finishes_and_commits_what_is_done(self) -> None:
        c = conversation(roll('A', 'law', 40), roll('B', 'precepts', 30, minute=2))
        answers = iter(['1', 'o', 'kept this one', ''])
        assert ann.annotate(c, ask=lambda q: next(answers)) == 1
        assert c.rolls[0].note == 'kept this one'
        assert c.rolls[1].note == ''

    def test_a_blank_at_the_WHICH_prompt_finishes_and_commits(self) -> None:
        """Distinct from finishing at the open/contested prompt.

        With two or more rolls left the menu asks which one; blank there must also
        finish and KEEP what is already staged, rather than doing nothing or
        discarding. Ctrl-C is the discard path, and it is deliberately the only one.
        """
        c = conversation(
            roll('A', 'law', 40),
            roll('B', 'precepts', 30, minute=2),
            roll('C', 'sincerity', 35, minute=4),
        )
        answers = iter(['1', 'o', 'the one I did', ''])
        assert ann.annotate(c, ask=lambda q: next(answers)) == 1
        assert c.rolls[0].note == 'the one I did'
        assert c.rolls[1].note == ''
        assert c.rolls[2].note == ''

    def test_a_bad_menu_answer_is_re_asked(self, capsys: Any) -> None:
        c = conversation(roll('A', 'law', 40), roll('B', 'precepts', 30, minute=2))
        answers = iter(['nine', '99', '1', 'x', 'o', 'the note', ''])
        assert ann.annotate(c, ask=lambda q: next(answers)) == 1
        assert 'enter a number from 1 to 2' in capsys.readouterr().out

    def test_an_empty_description_is_re_asked(self) -> None:
        c = conversation(roll('A', 'law', 40))
        answers = iter(['o', '', '   ', 'finally a note'])
        ann.annotate(c, ask=lambda q: next(answers))
        assert c.rolls[0].note == 'finally a note'

    def test_it_requires_an_open_conversation(self) -> None:
        with pytest.raises(conv.NoConversation):
            ann.annotate(ask=lambda q: '')

    def test_unattributed_rolls_are_not_offered(self) -> None:
        c = conversation(roll('', 'law', 40))
        assert ann.pending(c) == []
