"""Feature 210: every choice in the roll prompts, made with Up, Down and Enter."""

from __future__ import annotations

import importlib
import io
import os
import pty
import sys
import termios
import tty
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from l7r.repl import dice, gmrolls
from l7r.repl.rolls import console, lines, menu, npcskills, rules
from l7r.repl.rolls import conversation as conv
from l7r.repl.rolls.menu import Option, Picker
from l7r.repl.rolls.models import Conversation, Roll

ann = importlib.import_module('l7r.repl.rolls.annotate')
W = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
UP, DOWN, ENTER = '\x1b[A', '\x1b[B', '\r'
KINDS = ann.KIND_OPTIONS
#: Taken before any test replaces it, so a test may script the keys more than once.
CHOOSE = menu.choose


def pick(options: Any, *pressed: str, selected: int = 0, size: tuple[int, int] = (80, 24)) -> Any:
    queue = list(pressed)
    drawn: list[str] = []
    key = menu.choose(
        '  Which?',
        options,
        selected=selected,
        read_key=lambda: queue.pop(0),
        write=drawn.append,
        size=size,
    )
    return key, ''.join(drawn)


class TestChoosing:
    def test_enter_takes_the_highlighted_row(self) -> None:
        assert pick(KINDS, ENTER)[0] == 'o'
        assert pick(KINDS, DOWN, ENTER)[0] == 'c'
        assert pick(KINDS, ENTER, selected=2)[0] == 'd'

    def test_the_highlight_wraps_both_ways(self) -> None:
        assert pick(KINDS, UP, ENTER)[0] == ''
        assert pick(KINDS, *[DOWN] * 5, ENTER)[0] == 'o'
        assert pick(KINDS, '\x1bOA', '\x1bOB', '\x1bOB', ENTER)[0] == 'c'

    def test_everything_typed_today_still_lands_on_its_row(self) -> None:
        """`o` Enter, `ob` Enter, `b` Enter, `contested` Enter - keystroke for keystroke."""
        assert pick(KINDS, 'o', ENTER)[0] == 'o'
        assert pick(KINDS, 'o', 'b', ENTER)[0] == 'ob'
        assert pick(KINDS, 'B', ENTER)[0] == 'ob'
        assert pick(KINDS, *'contested', ENTER)[0] == 'c'
        assert pick(KINDS, 'd', ENTER)[0] == 'd'

    def test_two_digit_rows(self) -> None:
        rows = [Option(str(n), f'roll {n}') for n in range(1, 15)]
        assert pick(rows, '1', '2', ENTER)[0] == '12'
        assert pick(rows, '1', '9', ENTER)[0] == '9'
        assert pick(rows, '3', ENTER)[0] == '3'

    def test_a_key_that_matches_nothing_and_backspace_forget_what_was_typed(self) -> None:
        assert pick(KINDS, 'o', 'z', 'b', ENTER)[0] == 'ob'
        assert pick(KINDS, 'o', '\x7f', 'b', ENTER)[0] == 'ob'
        assert pick(KINDS, 'z', ENTER)[0] == 'o'
        assert pick(KINDS, 'o', DOWN, 'b', ENTER)[0] == 'ob'

    def test_stray_keys_change_nothing_and_redraw_nothing(self) -> None:
        _, plain = pick(KINDS, ENTER)
        key, drawn = pick(KINDS, '\x1b[C', '\x1b', ENTER)
        assert key == 'o'
        assert drawn == plain

    def test_ctrl_c_and_ctrl_d_propagate_with_the_terminal_put_back(self) -> None:
        def interrupted() -> str:
            raise KeyboardInterrupt

        drawn: list[str] = []
        with pytest.raises(KeyboardInterrupt):
            menu.choose('  Which?', KINDS, read_key=interrupted, write=drawn.append, size=(80, 24))
        assert drawn[-1].endswith('  Which?\r\n' + menu.SHOW_CURSOR)
        with pytest.raises(EOFError):
            pick(KINDS, '\x04')
        assert console._overlay is None

    def test_a_menu_needs_options(self) -> None:
        with pytest.raises(ValueError, match='at least one option'):
            Picker('  Which?', [])


class TestDrawing:
    def test_one_row_is_highlighted_and_keys_are_shown(self) -> None:
        block = Picker('  Which? ', KINDS, 1).render().split('\r\n')
        assert block[0] == '  Which?'
        assert block[1] == '    open  [o]'
        assert block[2] == f'{menu.REVERSE}  > contested  [c]{menu.RESET}'
        assert block[5] == '    finish - keep what is staged'
        assert len([row for row in block if menu.REVERSE in row]) == 1

    def test_a_row_whose_key_is_its_label_shows_no_key(self) -> None:
        assert (
            Picker('t', [Option('stoic', 'stoic')], 0).render().endswith('  > stoic' + menu.RESET)
        )

    def test_it_collapses_to_the_question_and_the_answer(self) -> None:
        _, drawn = pick(KINDS, DOWN, ENTER)
        assert drawn.endswith('\x1b[J  Which? contested\r\n' + menu.SHOW_CURSOR)
        assert drawn.startswith(menu.HIDE_CURSOR)

    def test_erase_covers_exactly_what_was_drawn(self) -> None:
        picker = Picker('t', KINDS)
        assert picker.height == picker.render().count('\r\n') + 1
        assert picker.erase() == '\r\x1b[5A\x1b[J'

    def test_a_long_list_scrolls_with_the_highlight(self) -> None:
        rows = [Option(str(n), f'roll {n}') for n in range(1, 21)]
        picker = Picker('t', rows, 0, (80, 8))
        assert picker.visible == 5
        assert 'roll 5' in picker.render()
        assert 'roll 6' not in picker.render()
        picker.move(-1)
        assert 'roll 20' in picker.render()
        assert 'roll 15' not in picker.render()
        picker.typed('3')
        assert 'roll 3  [3]' in picker.render()
        assert picker.height == 6

    def test_rows_are_clipped_to_the_terminal_and_a_tiny_one_still_works(self) -> None:
        picker = Picker('t', [Option('1', 'x' * 200)], 0, (20, 1))
        assert all(
            len(row.replace(menu.REVERSE, '').replace(menu.RESET, '')) <= 19
            for row in picker.render().split('\r\n')
        )
        assert picker.visible == 1
        assert Picker('t', KINDS, 99).selected == 4


class Terminal:
    """A real pseudo-terminal, already in cbreak before the keys are queued - see
    `tests/test_rolls_keys.py` for why (a queued Backspace is otherwise eaten)."""

    def __init__(self, typed: bytes) -> None:
        self.master, self.slave = pty.openpty()
        tty.setcbreak(self.slave, termios.TCSANOW)
        os.write(self.master, typed)

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return self.slave

    def close(self) -> None:
        os.close(self.master)
        os.close(self.slave)


class Screen(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.fixture
def at_a_terminal(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[bytes], Screen]]:
    opened: list[Terminal] = []

    def start(typed: bytes) -> Screen:
        terminal = Terminal(typed)
        opened.append(terminal)
        screen = Screen()
        monkeypatch.setattr(sys, 'stdin', terminal)
        monkeypatch.setattr(sys, 'stdout', screen)
        return screen

    yield start
    for terminal in opened:
        terminal.close()


class TestWhenItIsAMenu:
    def test_only_a_registered_asker_at_a_real_terminal(
        self, at_a_terminal: Callable[[bytes], Screen]
    ) -> None:
        def scripted(question: str) -> str:
            return 'c'

        assert not menu.interactive(ann.ask_quietly)
        at_a_terminal(b'')
        assert menu.interactive(ann.ask_quietly)
        assert menu.interactive(lines._ask)
        assert menu.interactive(npcskills._ask)
        assert not menu.interactive(scripted)
        assert menu.ask_choice(scripted, 'typed? ', 'title', KINDS) == 'c'

    def test_real_arrow_keys_off_a_real_terminal(
        self, at_a_terminal: Callable[[bytes], Screen]
    ) -> None:
        screen = at_a_terminal(b'\x1b[B\x1b[B\r')
        assert menu.ask_choice(ann.ask_quietly, 'typed? ', '  Which?', KINDS) == 'd'
        assert screen.getvalue().endswith('  Which? discard\r\n' + menu.SHOW_CURSOR)


class TestTheWatcher:
    def test_an_announcement_goes_above_the_list_which_is_redrawn_unmoved(self) -> None:
        picker = Picker('  Which?', KINDS, 2)
        screen = Screen()
        with console.overlay(picker):
            assert console.print_above('  + Jimen: law 30', stream=screen)
        assert screen.getvalue() == picker.erase() + '  + Jimen: law 30\r\n' + picker.render()
        assert picker.selected == 2
        assert console._overlay is None

    def test_a_typed_roll_prompt_is_redrawn_as_itself_not_as_the_python_prompt(self) -> None:
        screen = Screen()
        with console.asking('  What was it for? > '):
            console.print_above('  + Jimen: law 30', stream=screen, line_buffer=lambda: 'the arr')
        assert screen.getvalue().endswith('\n  What was it for? > the arr')
        assert console._asking == ''
        seen: list[str] = []

        def reader(question: str) -> str:
            seen.append(console._asking)
            return '5'

        ann.ask_quietly('  Bonus? > ', reader=reader)
        assert seen == ['  Bonus? > ']

    def test_the_default_writer_writes(self, capsys: pytest.CaptureFixture[str]) -> None:
        console.write('drawn')
        assert capsys.readouterr().out == 'drawn'


def roll(name: str, skill: str, total: int, *, rank: int | None = 2, minute: int = 0) -> Roll:
    return Roll(
        name, skill, total, 'recorded', f'{name}{minute}', W + timedelta(minutes=minute), rank
    )


class TestAWholeRunWithTheArrowKeys:
    """Every call site, driven the way the GM will drive it: `interactive` forced on,
    the keys scripted, and the typed answers (notes, bonuses) still asked as lines."""

    @pytest.fixture(autouse=True)
    def clean(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        conv._open = None
        gmrolls.clear()
        monkeypatch.setattr(dice, 'd10', lambda reroll=True: 6)
        monkeypatch.setattr(menu, 'interactive', lambda ask: True)
        yield
        conv._open = None
        gmrolls.clear()

    def drive(self, monkeypatch: pytest.MonkeyPatch, *pressed: str) -> list[str]:
        queue = list(pressed)
        titles: list[str] = []

        def choose(title: str, options: Any, *, selected: int = 0) -> str:
            titles.append(title.strip())
            return CHOOSE(
                title,
                options,
                selected=selected,
                read_key=lambda: queue.pop(0),
                write=lambda text: None,
                size=(80, 24),
            )

        monkeypatch.setattr(menu, 'choose', choose)
        return titles

    def talking(self, *rolls: Roll, **numbers: int) -> Conversation:
        c = Conversation(npc={'id': 'f', 'name': 'Fumitake'}, opened_at=W, channels=('c',))
        c.rolls.extend(rolls)
        c.numbers.update(numbers)
        conv._open = c
        return c

    def typed(self, *answers: str) -> Callable[[str], str]:
        queue = list(answers)
        return lambda question: queue.pop(0)

    def test_which_roll_the_kind_the_opposing_roll_and_the_finish_row(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = self.talking(roll('Jimen', 'law', 41), roll('Moriko', 'precepts', 30, minute=1))
        gmrolls.record((9, 9, 9, 9, 9), 3, 28, asked=(5, 3))
        titles = self.drive(monkeypatch, DOWN, ENTER, 'c', ENTER, ENTER, UP, ENTER)
        ann.annotate(c, ask=self.typed('', '', 'arguing the point'))
        assert titles == [
            'Rolls waiting to be annotated for Fumitake:',
            'Open, contested, discard, or open with bonus?',
            'Which of your rolls?',
            # One roll left, so "which roll?" is skipped - Up from "open" is "finish".
            'Open, contested, discard, or open with bonus?',
        ]
        assert c.rolls[1].opposed_total == 28
        assert c.rolls[0].note == ''
        out = capsys.readouterr().out
        assert '1. ' not in out  # the menu IS the list; it is not printed as well

    def test_the_always_contested_picker_and_how_the_npc_appeared(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = self.talking(roll('Jimen', 'manipulation', 30), roll('Jimen', 'intimidation', 32))
        gmrolls.record((9, 9, 9, 9, 9), 3, 28, asked=(5, 3))
        titles = self.drive(monkeypatch, ENTER, 'f', ENTER, DOWN, DOWN, ENTER)
        ann.annotate(
            c,
            ask=self.typed('', '', 'pressing him', 'looming'),
            undoable=lambda q, ask: (False, ask(q)),
        )
        assert 'Opposed by which tact roll?' in titles
        assert titles[-1] == 'How did Fumitake appear?'
        assert c.rolls[0].opposed_total == 15
        assert c.rolls[1].outcome == 'rattled'

    def test_which_line_and_the_question_asked_when_there_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c = self.talking(roll('Jimen', 'interrogation', 37))
        self.drive(monkeypatch, ENTER)
        ann.annotate(c, ask=self.typed())
        assert not c.rolls[0].discarded  # Enter alone = today's blank: leave it for now
        self.drive(monkeypatch, ENTER)
        lines.new_line_of_questioning(
            'the treasury',
            ask=self.typed(),
            collector=lambda x: None,
            now=lambda: W + timedelta(minutes=5),
        )
        assert c.rolls[0].line == 1  # Enter alone = today's [P/d] default: it joins
        c.rolls.append(roll('Moriko', 'interrogation', 24, rank=None, minute=1))
        titles = self.drive(monkeypatch, ENTER)
        ann.annotate(c, ask=self.typed(''))
        assert titles == ['Which line of questioning?']
        assert c.rolls[1].line == 1

    def test_the_disagreement_prompts_open_on_mistake_and_ctrl_c_is_still_an_answer(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self.talking(air=3, tact=2)
        tact = npcskills.build_tags()['tact']
        self.drive(monkeypatch, ENTER, DOWN, ENTER, DOWN, ENTER)
        first = tact(6, 3, ask=npcskills._ask)
        assert first is not None
        assert first.entry.mistake
        second = tact(6, 3, ask=npcskills._ask)
        assert second is not None
        assert not second.entry.mistake
        assert tact(2, ask=npcskills._ask) is not None  # `_rank`: the record was wrong
        assert '[m]' not in capsys.readouterr().out

        def interrupted(title: str, options: Any, *, selected: int = 0) -> str:
            raise KeyboardInterrupt

        monkeypatch.setattr(menu, 'choose', interrupted)
        third = tact(7, 3, ask=npcskills._ask)
        assert third is not None
        assert third.entry.mistake

    def test_ctrl_c_in_a_list_abandons_the_whole_run(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        c = self.talking(roll('Jimen', 'law', 41))

        def interrupted(title: str, options: Any, *, selected: int = 0) -> str:
            raise KeyboardInterrupt

        monkeypatch.setattr(menu, 'choose', interrupted)
        ann.annotate(c, ask=self.typed())
        assert 'nothing saved' in capsys.readouterr().out
        assert rules.needs_annotation(c.rolls[0])
