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

import sys
import threading
from collections.abc import Callable
from typing import Any

#: One writer at a time. Two threads interleaving escape sequences would leave the
#: terminal in a state neither of them intended.
_lock = threading.Lock()

#: What the prompt looks like when `sys.ps1` is not set (it is set by
#: `code.interact`, but a non-interactive caller may not have it).
DEFAULT_PROMPT = '>>> '

CLEAR_LINE = '\r\x1b[K'


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
    prompt = str(getattr(sys, 'ps1', DEFAULT_PROMPT))
    with _lock:
        out.write(CLEAR_LINE + text + '\n' + prompt + buffered)
        out.flush()
    return True
