"""Print from a background thread without stomping on the REPL prompt.

The watcher runs in a daemon thread and prints whenever it sees a roll, so its
output lands wherever the cursor happens to be - in the middle of the `>>> ` the
GM is looking at, or halfway through something they are typing. What they saw:

    >>>   + Roll Tester: etiquette 28 @1
    [29/Aug/2026:00:24:10]  Updated character eb7c70a9...: ['bio']
      -> Hatsu: Roll Tester etiquette: 25

    >>>

with no prompt after the last line until they pressed Enter.

The fix is the standard readline dance, and it is worth spelling out because it
looks like magic: `\\r` returns the cursor to column 0 and `\\x1b[K` erases the line
the prompt was drawn on, so the message can be written where the prompt was; then
the prompt is REDRAWN underneath it along with whatever the GM had already typed,
which readline still holds in its line buffer. The net effect is that output
appears ABOVE the prompt and the prompt never moves.

Two deliberate limits. The cursor lands at the end of the redrawn buffer, so if the
GM had moved left mid-line they lose their column (they keep every character). And
none of this happens unless stdout is a terminal - piped output must not carry
escape codes, the same rule `shell.set_title` follows.
"""

from __future__ import annotations

import contextlib
import sys
import threading
from collections.abc import Callable, Iterator
from typing import Any, Protocol

#: One writer at a time. Two threads interleaving escape sequences would leave the
#: terminal in a state neither of them intended.
_lock = threading.Lock()

#: What the prompt looks like when `sys.ps1` is not set (it is set by
#: `code.interact`, but a non-interactive caller may not have it).
DEFAULT_PROMPT = '>>> '

CLEAR_LINE = '\r\x1b[K'


class Overlay(Protocol):
    """Something drawn BELOW the scrollback that an announcement must not wreck - an
    arrow-key menu (`menu.Picker`, feature 210). `erase` removes it from wherever the
    cursor was left; `render` draws it again."""

    def erase(self) -> str: ...

    def render(self) -> str: ...


#: The menu currently on screen, if any. `print_above` assumed a ONE-LINE prompt; a
#: list is several, so while one is open an announcement erases all of it, prints, and
#: redraws it - with the highlight where it was, since the overlay holds its own state.
_overlay: Overlay | None = None

#: The question a typed roll prompt is asking right now, '' at the Python prompt.
#: Feature 210 found this while reading the redraw: with `annotate()` waiting on
#: "What was it for? > ", an announcement redrew `>>> ` in its place, because `sys.ps1`
#: was the only prompt this module knew about.
_asking = ''


@contextlib.contextmanager
def overlay(view: Overlay) -> Iterator[None]:
    """`view` is on screen for the length of the block."""
    global _overlay
    with _lock:
        _overlay = view
    try:
        yield
    finally:
        with _lock:
            _overlay = None


@contextlib.contextmanager
def asking(question: str) -> Iterator[None]:
    """A typed prompt showing `question` is open for the length of the block."""
    global _asking
    before, _asking = _asking, question
    try:
        yield
    finally:
        _asking = before


def write(text: str) -> None:
    """Write to the terminal under the same lock the watcher's announcements take."""
    with _lock:
        sys.stdout.write(text)
        sys.stdout.flush()


def _line_buffer() -> str:
    """Whatever the GM has typed at the prompt but not yet entered."""
    try:
        import readline
    except ImportError:  # pragma: no cover - readline is present on this platform
        return ''
    return readline.get_line_buffer()


def print_above(
    text: str,
    *,
    stream: Any = None,
    line_buffer: Callable[[], str] = _line_buffer,
) -> bool:
    """Write `text` above the prompt, leaving the prompt and its buffer intact.

    Returns True when the prompt was redrawn, False when it fell back to a plain
    print (not a terminal). Multi-line text is written as-is; only the first line
    needs the cursor moved.
    """
    out = stream if stream is not None else sys.stdout
    if not getattr(out, 'isatty', lambda: False)():
        print(text, file=out)
        return False
    buffered = line_buffer()
    prompt = _asking or str(getattr(sys, 'ps1', DEFAULT_PROMPT))
    with _lock:
        if _overlay is not None:
            out.write(_overlay.erase() + text + '\r\n' + _overlay.render())
        else:
            out.write(CLEAR_LINE + text + '\n' + prompt + buffered)
        out.flush()
    return True
