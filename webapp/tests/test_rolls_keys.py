"""Feature 207: the two-press undo, read off the terminal before readline."""

from __future__ import annotations

import os
import pty
import termios
import tty
from collections.abc import Callable
from typing import Any

import pytest

from l7r.repl.rolls import keys


def source(data: bytes) -> tuple[Callable[[], bytes], Callable[[], bool]]:
    queue = [bytes([b]) for b in data]
    return (lambda: queue.pop(0) if queue else b''), (lambda: bool(queue))


def decode(data: bytes) -> str:
    return keys.decode(*source(data))


class TestDecode:
    def test_a_plain_character(self) -> None:
        assert decode(b'a') == 'a'

    def test_backspace_and_left_arrow_whole(self) -> None:
        assert decode(b'\x7f') in keys.UNDO_KEYS
        assert decode(b'\x1b[D') == '\x1b[D'
        assert decode(b'\x1bOD') == '\x1bOD'
        assert decode(b'\x1b[1;5D') == '\x1b[1;5D'

    def test_a_lone_escape(self) -> None:
        assert decode(b'\x1b') == '\x1b'

    def test_multibyte_characters_arrive_whole(self) -> None:
        for char in ('é', '星', '🎲'):
            assert decode(char.encode()) == char

    def test_an_exhausted_source_is_ctrl_d(self) -> None:
        assert decode(b'') == keys.CTRL_D


def first(*pressed: str) -> tuple[tuple[bool, str], int]:
    queue = list(pressed)
    hints: list[int] = []
    return keys.first_key(lambda: queue.pop(0), lambda: hints.append(1)), len(hints)


class TestFirstKey:
    def test_two_presses_undo(self) -> None:
        assert first('\x7f', '\x7f') == ((True, ''), 1)
        assert first('\x1b[D', '\x08') == ((True, ''), 1)

    def test_one_press_then_a_letter_just_starts_the_note(self) -> None:
        assert first('\x7f', 'a') == ((False, 'a'), 1)

    def test_an_ordinary_key_is_handed_back(self) -> None:
        assert first('w') == ((False, 'w'), 0)

    def test_other_arrows_are_ignored(self) -> None:
        assert first('\x1b[C', '\x1b', 'w') == ((False, 'w'), 0)

    def test_ctrl_d_is_eof(self) -> None:
        with pytest.raises(EOFError):
            first(keys.CTRL_D)


class FakeReadline:
    def __init__(self) -> None:
        self.hooks: list[Any] = []
        self.inserted: list[str] = []

    def set_startup_hook(self, hook: Any) -> None:
        self.hooks.append(hook)

    def insert_text(self, text: str) -> None:
        self.inserted.append(text)


class TestPrefilled:
    def test_the_first_key_is_put_back_on_the_line_and_the_hook_cleared(self) -> None:
        fake = FakeReadline()

        def ask(question: str) -> str:
            fake.hooks[-1]()
            return 'what he owed'

        assert keys.prefilled(ask, '> ', 'w', readline=fake) == 'what he owed'
        assert fake.inserted == ['w']
        assert fake.hooks[-1] is None

    def test_the_hook_is_cleared_even_on_ctrl_c(self) -> None:
        fake = FakeReadline()

        def ask(question: str) -> str:
            raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            keys.prefilled(ask, '> ', 'w', readline=fake)
        assert fake.hooks[-1] is None

    def test_the_real_readline_is_the_default(self) -> None:
        assert keys.prefilled(lambda q: 'typed', '> ', 'w') == 'typed'


class Terminal:
    """A real pseudo-terminal, so the termios half is exercised and not mocked."""

    def __init__(self, typed: bytes) -> None:
        self.master, self.slave = pty.openpty()
        # Already in cbreak BEFORE the bytes are written: in canonical mode the line
        # discipline eats a queued Backspace as an erase, and the read would block
        # forever (measured - it hung the suite). A real GM presses the key after the
        # prompt is up, by which time `ask_with_undo` has switched modes itself.
        tty.setcbreak(self.slave, termios.TCSANOW)
        os.write(self.master, typed)

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        return self.slave

    def close(self) -> None:
        os.close(self.master)
        os.close(self.slave)


class TestAskWithUndo:
    def run(self, typed: bytes) -> tuple[tuple[bool, str], str, list[str]]:
        terminal = Terminal(typed)
        written: list[str] = []
        fake = FakeReadline()
        asked: list[str] = []

        def ask(question: str) -> str:
            asked.append(question)
            fake.hooks[-1]()
            return ''.join(fake.inserted) + 'hat he owed'

        try:
            result = keys.ask_with_undo(
                '  open > ', ask, stream=terminal, out=written.append, readline=fake
            )
        finally:
            terminal.close()
        return result, ''.join(written), asked

    def test_backspace_twice_undoes_the_selection(self) -> None:
        result, written, asked = self.run(b'\x7f\x7f')
        assert result == (True, '')
        assert asked == []
        assert keys.HINT in written
        assert written.endswith('\n')

    def test_left_arrow_twice_too(self) -> None:
        assert self.run(b'\x1b[D\x1b[D')[0] == (True, '')

    def test_a_letter_becomes_the_start_of_an_ordinary_line(self) -> None:
        result, written, asked = self.run(b'w')
        assert result == (False, 'what he owed')
        assert asked == ['  open > ']
        assert written == '  open > \r\x1b[K'

    def test_enter_alone_is_a_blank_answer(self) -> None:
        result, _, asked = self.run(b'\n')
        assert result == (False, '')
        assert asked == []

    def test_without_a_terminal_the_question_is_just_asked(self) -> None:
        assert keys.ask_with_undo('> ', lambda q: 'c') == (False, 'c')

    def test_a_stream_that_cannot_say(self) -> None:
        assert not keys.has_terminal(object())

    def test_the_default_writer_writes(self, capsys: pytest.CaptureFixture[str]) -> None:
        keys._write('  open > ')
        assert capsys.readouterr().out == '  open > '
