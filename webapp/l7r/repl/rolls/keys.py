"""The two-press undo: a real keystroke, read before readline gets the line.

Feature 207. Some answers arrive already selected - "open" for a history roll, the
GM's tact roll for a player's manipulation - and the GM asked for a KEY that undoes
the selection rather than a letter to type (2026-09-19): *"I don't want something
pre-entered such that I only have to hit enter in order to accept it. I would like
it to already be selected but maybe if I hit the left arrow twice, or if I hit the
backspace key twice in a row, while there is no text on the current line, then that
undoes the selection"*, and later: *"I would really like to have keystrokes
detected ... I know that we're using readline now but in theory we don't have to."*

READLINE CANNOT DO THIS - Python's binding has no way to call back into Python on a
key - and it does not need to. The prompt is printed, ONE KEY is read with the
terminal in cbreak mode, and then either the selection is undone or that key is
handed to readline as the first character of an ordinary line (a startup hook that
inserts it). So the note keeps full line editing, and `ask_quietly` still keeps the
answer out of the history.

ACCEPTED LIMIT, recorded so it is not taken for a bug: the undo is recognized only
while NOTHING has been typed - which is the GM's own condition (*"while there is no
text on the current line"*). Once a character is in, the line is readline's, and
deleting back to empty and pressing Backspace again does nothing. Lifting that means
replacing readline for these prompts with a full line editor (prompt_toolkit), which
was priced and declined as far more machinery than the case deserves.

TWO presses, because that is what the GM said, twice. One constant.

With no terminal (a pipe, the test suite) there is no key to read: the question is
simply asked, and the typed forms `annotate()` accepts (`c`, `ob`, `d` as the whole
answer) do the undo's work.
"""

from __future__ import annotations

import contextlib
import os
import select
import sys
from collections.abc import Callable, Iterator
from typing import Any

Ask = Callable[[str], str]

#: How many presses undo a selection.
UNDO_PRESSES = 2

#: Backspace as terminals send it (DEL, or BS on some), and Left Arrow in both the
#: normal and the application cursor-key encodings.
UNDO_KEYS = frozenset({'\x7f', '\x08', '\x1b[D', '\x1bOD'})

ENTER = frozenset({'\r', '\n'})
CTRL_D = '\x04'
ESCAPE = '\x1b'

HINT = '  (again to undo the selection) '


def decode(read: Callable[[], bytes], pending: Callable[[], bool]) -> str:
    """One KEY from a byte source: a whole UTF-8 character, or a whole escape sequence.

    `read` returns one byte; `pending` says whether another is already waiting, which
    is how a lone Escape is told from the start of an arrow key. An exhausted source
    reads as Ctrl-D.
    """
    first = read()
    if not first:
        return CTRL_D
    if first == ESCAPE.encode():
        sequence = first
        while pending():
            sequence += read()
            # CSI (`ESC [`) and SS3 (`ESC O`) sequences end on a byte in 0x40-0x7E
            # that is not the introducer itself.
            if len(sequence) > 2 and 0x40 <= sequence[-1] <= 0x7E:
                break
        return sequence.decode('ascii', 'replace')
    lead = first[0]
    extra = 3 if lead >= 0xF0 else 2 if lead >= 0xE0 else 1 if lead >= 0xC0 else 0
    data = first + b''.join(read() for _ in range(extra))
    return data.decode('utf-8', 'replace')


def first_key(read_key: Callable[[], str], hint: Callable[[], None]) -> tuple[bool, str]:
    """`(undone, key)`: two undo presses, or the first key that is anything else.

    After one undo press any ordinary key simply starts the answer. Stray escape
    sequences (the other arrows) are ignored rather than typed into the note.
    """
    presses = 0
    while True:
        key = read_key()
        if key in UNDO_KEYS:
            presses += 1
            if presses >= UNDO_PRESSES:
                return True, ''
            hint()
        elif key == CTRL_D:
            raise EOFError
        elif not key.startswith(ESCAPE):
            return False, key


@contextlib.contextmanager
def cbreak(fd: int) -> Iterator[None]:
    """The terminal one key at a time, restored whatever happens. Ctrl-C still
    raises: cbreak leaves signal keys alone, unlike raw mode."""
    import termios
    import tty

    saved = termios.tcgetattr(fd)
    # TCSANOW, not the default TCSAFLUSH: a flush throws away whatever the GM typed
    # ahead of the prompt, and they type ahead constantly.
    tty.setcbreak(fd, termios.TCSANOW)
    try:
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def key_reader(fd: int) -> Callable[[], str]:
    """Keys off a file descriptor, UNBUFFERED - `sys.stdin.read(1)` would pull a
    whole paste into Python's buffer, where readline never sees the rest of it."""

    def pending() -> bool:
        return bool(select.select([fd], [], [], 0.05)[0])

    return lambda: decode(lambda: os.read(fd, 1), pending)


def prefilled(ask: Ask, question: str, text: str, *, readline: Any = None) -> str:
    """Ask with `text` already on the line, editable - the key that was read first."""
    if readline is None:
        try:
            import readline as module
        except ImportError:  # pragma: no cover - Windows, or a stripped build
            return text + ask(question)
        readline = module
    readline.set_startup_hook(lambda: readline.insert_text(text))
    try:
        return ask(question)
    finally:
        readline.set_startup_hook(None)


def has_terminal(stream: Any = None) -> bool:
    source = sys.stdin if stream is None else stream
    try:
        return bool(source.isatty())
    except AttributeError, ValueError:
        return False


def ask_with_undo(
    question: str,
    ask: Ask,
    *,
    stream: Any = None,
    out: Callable[[str], None] | None = None,
    readline: Any = None,
) -> tuple[bool, str]:
    """Ask a question whose answer was pre-selected. `(undone, answer)`.

    At a terminal the first key is read directly; anywhere else the question is just
    asked, and the caller's typed fallbacks apply.
    """
    source = sys.stdin if stream is None else stream
    if not has_terminal(source):
        return False, ask(question)
    write = out or _write
    fd = source.fileno()
    write(question)
    with cbreak(fd):
        undone, key = first_key(key_reader(fd), lambda: write(HINT))
    if undone:
        write('\n')
        return True, ''
    if key in ENTER:
        write('\n')
        return False, ''
    # Redraw the line from its start: readline prints the question itself, and the
    # hint (if one was shown) must not be left stranded to its right.
    write('\r\x1b[K')
    return False, prefilled(ask, question, key, readline=readline)


def _write(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()
