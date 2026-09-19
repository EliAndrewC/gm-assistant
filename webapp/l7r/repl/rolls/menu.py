"""Arrow-key menus: every CHOICE in the roll prompts, made with Up, Down and Enter.

Feature 210. The GM (2026-09-19): *"it's so much nicer to be able to use the arrow
keys to select between menu options than to have to type in a number ... instead of
having to type `o` or `c` or `ob` etc then I could just have something selected and
then move my arrow keys up and down and then hit enter."*

      Open, contested, discard, or open with bonus?
      > open  [o]
        contested  [c]
        discard  [d]
        open with a bonus  [ob]
        finish - keep what is staged

ONE HELPER, and every choice prompt calls it (`ask_choice`). What makes that cheap is
one rule: **an option's `key` is the answer the GM would have TYPED** (`o`, `ob`, `3`,
'' for the blank line that finishes). So a call site does not grow a second code
path - at a terminal it gets the key from the menu, anywhere else it gets the typed
answer from `ask`, and the same code below the call reads either.

TYPING MOVES THE HIGHLIGHT; ENTER CHOOSES. Typed characters accumulate (`o` then `b`
lands on `ob`; `1` then `2` lands on row 12) and restart when they stop matching.
Declined: a letter choosing instantly. It would save a keystroke and break `ob` (its
`o` would already have chosen "open") and every two-digit row - and `o` Enter is what
the GM's hands already do, so every answer typed before this feature still works
keystroke for keystroke.

WHEN IT IS A MENU AT ALL: only when the answers come from a REAL terminal - stdin and
stdout are both ttys AND the `ask` in use is one registered with `terminal_asker`
(the package's own quiet `input`). A test or a script that supplies its own `ask` is
always asked the typed question, even when pytest itself is run from a terminal.
Without that second condition a scripted test would sit waiting for an arrow key.

THE WATCHER. `console.print_above` assumed a one-line prompt. While a menu is open it
is registered as the console's OVERLAY, so an announcement erases the whole list,
prints above it, and redraws it with the highlight where it was. Every write here
goes through the console's lock for the same reason the watcher's does.

NOT CONVERTED, on purpose: free text (what a roll was for, a bonus, a typed total),
and the MIXED prompt - "what was it for?", which takes a note but also `c` / `ob` /
`d`. A list cannot hold a free-text row, and the GM approved leaving those typed.

The terminal is put back whatever happens (`keys.cbreak`, the cursor, the overlay):
Ctrl-C and Ctrl-D propagate as `KeyboardInterrupt` / `EOFError`, because what they
MEAN differs by prompt and is the caller's to say.
"""

from __future__ import annotations

import contextlib
import shutil
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

from l7r.repl.rolls import console, keys

Ask = Callable[[str], str]

UP = frozenset({'\x1b[A', '\x1bOA'})
DOWN = frozenset({'\x1b[B', '\x1bOB'})
BACKSPACE = frozenset({'\x7f', '\x08'})

HIDE_CURSOR, SHOW_CURSOR = '\x1b[?25l', '\x1b[?25h'
REVERSE, RESET = '\x1b[7m', '\x1b[0m'

#: Rows kept free around a list, so erasing it never has to move above the screen.
MARGIN = 3


@dataclass(frozen=True)
class Option:
    """One row. `key` is the answer typing would have given - see the module docstring."""

    key: str
    label: str
    #: Other spellings that land on this row (`b` for `ob`, a row's number).
    typed: tuple[str, ...] = ()

    @property
    def spellings(self) -> tuple[str, ...]:
        return tuple(text.lower() for text in (self.key, *self.typed) if text)


_terminal_askers: list[Ask] = []


def terminal_asker(ask: Ask) -> Ask:
    """Mark `ask` as reading from the real terminal. Usable as a decorator."""
    _terminal_askers.append(ask)
    return ask


def interactive(ask: Ask) -> bool:
    """True when a choice asked through `ask` should be an arrow-key menu."""
    known = any(ask is registered for registered in _terminal_askers)
    return known and keys.has_terminal(sys.stdin) and keys.has_terminal(sys.stdout)


class Picker:
    """The list's state and its drawing. Pure: no terminal, so it is tested directly.

    The drawn block is ALWAYS `height` lines with the cursor left at the end of the
    last one, which is what lets `erase` be a constant.
    """

    def __init__(
        self,
        title: str,
        options: Sequence[Option],
        selected: int = 0,
        size: tuple[int, int] = (80, 24),
    ) -> None:
        if not options:
            raise ValueError('a menu needs at least one option')
        self.title = title.rstrip()
        self.options = tuple(options)
        self.selected = min(max(selected, 0), len(self.options) - 1)
        self.columns, lines = size
        self.visible = min(len(self.options), max(1, lines - MARGIN))
        self.top = 0
        self.buffer = ''

    @property
    def height(self) -> int:
        return self.visible + 1

    @property
    def chosen(self) -> Option:
        return self.options[self.selected]

    def move(self, delta: int) -> None:
        """Up or down one row, wrapping - and forgetting whatever was typed."""
        self.selected = (self.selected + delta) % len(self.options)
        self.buffer = ''

    def typed(self, char: str) -> None:
        """A typed character MOVES the highlight; see the module docstring."""
        for attempt in (self.buffer + char.lower(), char.lower()):
            hit = self._match(attempt)
            if hit is not None:
                self.buffer, self.selected = attempt, hit
                return
        self.buffer = ''

    def _match(self, text: str) -> int | None:
        exact = [i for i, option in enumerate(self.options) if text in option.spellings]
        if exact:
            return exact[0]
        starts = [
            i
            for i, option in enumerate(self.options)
            if any(spelling.startswith(text) for spelling in option.spellings)
        ]
        return starts[0] if starts else None

    def _clip(self, text: str) -> str:
        return text[: max(1, self.columns - 1)]

    def render(self) -> str:
        """The whole block, scrolled so the highlighted row is on it."""
        if self.selected < self.top:
            self.top = self.selected
        elif self.selected >= self.top + self.visible:
            self.top = self.selected - self.visible + 1
        rows = [self._clip(self.title)]
        for index in range(self.top, self.top + self.visible):
            option = self.options[index]
            hint = f'  [{option.key}]' if option.key and option.key != option.label else ''
            if index == self.selected:
                rows.append(f'{REVERSE}{self._clip(f"  > {option.label}{hint}")}{RESET}')
            else:
                rows.append(self._clip(f'    {option.label}{hint}'))
        return '\r\n'.join(rows)

    def erase(self) -> str:
        """Back to the block's first column and line, clearing to the end of the screen."""
        return f'\r\x1b[{self.height - 1}A\x1b[J'

    def settled(self, chose: bool) -> str:
        """What the block collapses to: one line, the question and the answer."""
        answer = f' {self.chosen.label}' if chose else ''
        return self.erase() + self._clip(f'{self.title}{answer}') + '\r\n'


@contextlib.contextmanager
def _terminal_keys() -> Iterator[Callable[[], str]]:
    """Keys off the real terminal, one at a time."""
    fd = sys.stdin.fileno()
    with keys.cbreak(fd):
        yield keys.key_reader(fd)


def choose(
    title: str,
    options: Sequence[Option],
    *,
    selected: int = 0,
    read_key: Callable[[], str] | None = None,
    write: Callable[[str], None] | None = None,
    size: tuple[int, int] | None = None,
) -> str:
    """Show the list and return the chosen option's `key`.

    `read_key` / `write` / `size` are injected by the tests; at the prompt they are
    the terminal's. Raises `KeyboardInterrupt` / `EOFError` on Ctrl-C / Ctrl-D, with
    the terminal already put back.
    """
    put = write or console.write
    columns, lines = size or shutil.get_terminal_size()
    picker = Picker(title, options, selected, (columns, lines))
    source = contextlib.nullcontext(read_key) if read_key else _terminal_keys()
    chose = False
    put(HIDE_CURSOR + picker.render())
    try:
        with source as read, console.overlay(picker):
            while True:
                key = read()
                if key in keys.ENTER:
                    chose = True
                    break
                if key == keys.CTRL_D:
                    raise EOFError
                if key in UP or key in DOWN:
                    picker.move(-1 if key in UP else 1)
                elif key in BACKSPACE:
                    picker.buffer = ''
                elif len(key) == 1 and key.isprintable():
                    picker.typed(key)
                else:
                    continue  # the other arrows, a lone Escape: nothing to redraw
                put(picker.erase() + picker.render())
    finally:
        put(picker.settled(chose) + SHOW_CURSOR)
    return picker.chosen.key


def ask_choice(
    ask: Ask, question: str, title: str, options: Sequence[Option], *, selected: int = 0
) -> str:
    """One CHOICE: the menu at a terminal, the typed `question` anywhere else.

    Returns what the GM would have typed either way, so the caller's handling of the
    answer is written once.
    """
    if interactive(ask):
        return choose(title, options, selected=selected)
    return ask(question)
