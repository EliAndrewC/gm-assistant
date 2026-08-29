"""Start the GM REPL: readline, tab completion, a history file, the banner.

``main(argv)``: with no arguments, an interactive prompt; with arguments,
they are joined and run as a script in the same namespace and the process
exits - ``repl.py 'xky(6, 3)'`` echoes the value, a multi-line quoted
script just runs. ``-i`` after a snippet stays interactive afterwards.
"""

from __future__ import annotations

import ast
import atexit
import code
import contextlib
import logging
import os
import sys
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from l7r.repl import help_text, namespace
from l7r.repl.names import warm_caches
from l7r.repl.rolls import console
from l7r.repl.rolls.conversation import close_open_conversation

HISTORY = Path(os.environ.get('L7R_REPL_HISTORY', Path.home() / '.l7r_repl_history'))
TITLE = 'L7R repl >>>'


def set_title(title: str = TITLE, out: Any = None) -> bool:
    """Name the terminal tab/window (xterm OSC 0), only when stdout is a
    terminal - piped output must not carry escape codes. True when set."""
    stream = out if out is not None else sys.stdout
    if not getattr(stream, 'isatty', lambda: False)():
        return False
    stream.write(f'\033]0;{title}\007')
    stream.flush()
    return True


class PromptSafeHandler(logging.Handler):
    """A logging handler that writes above the REPL prompt instead of through it."""

    def emit(self, record: logging.LogRecord) -> None:
        console.print_above(f'  . {record.getMessage()}')


def route_cherrypy_logs() -> bool:
    """Send CherryPy's logger above the prompt rather than straight at the cursor.

    `chargen/op.py` reports through `cherrypy.log`, which is right for a running
    server and wrong for a prompt: the GM saw

        [29/Aug/2026:00:24:10]  Updated character eb7c70a9...: ['bio']

    land between the watcher's two lines, timestamped and un-prefixed. Silencing it
    outright would have been easier and worse - the same logger carries the
    fail-soft "Failed to fetch character body" messages, which matter. So the screen
    handler comes off and ours goes on, and everything CherryPy says now obeys the
    same prompt discipline as the watcher.

    False when CherryPy is not installed, which is not an error here.
    """
    try:
        import cherrypy
    except ImportError:  # pragma: no cover - cherrypy is a hard dependency of the webapp
        return False
    cherrypy.log.screen = False
    for existing in list(cherrypy.log.error_log.handlers):
        if isinstance(existing, PromptSafeHandler):
            return True
    cherrypy.log.error_log.addHandler(PromptSafeHandler())
    return True


def build_namespace() -> dict[str, Any]:
    ns = namespace()
    ns['help_l7r'] = lambda: print(help_text())
    ns['__name__'] = '__l7r_repl__'
    return ns


def setup_readline(history: Path = HISTORY, ns: dict[str, Any] | None = None) -> bool:
    """Tab completion over ``ns`` and persistent history; False when readline
    is absent. The completer MUST be built on ``ns``: rlcompleter's default
    completes against ``__main__``'s globals, and the prompt's names live in
    the dict handed to ``code.interact``, which is not that - so with the
    default, ``discern_hon<TAB>`` found nothing (GM 2026-08-27)."""
    try:
        import atexit
        import readline
        import rlcompleter
    except ImportError:  # pragma: no cover - Windows, or a stripped build
        return False
    readline.set_completer(rlcompleter.Completer(ns if ns is not None else {}).complete)
    readline.parse_and_bind('tab: complete')
    with contextlib.suppress(OSError):  # no history yet
        readline.read_history_file(history)
    readline.set_history_length(2000)
    atexit.register(_write_history, history)
    return True


def _write_history(history: Path) -> None:
    import readline

    with contextlib.suppress(OSError):  # unwritable home
        readline.write_history_file(history)


def run_snippet(source: str, ns: dict[str, Any]) -> None:
    """Run ``source`` in ``ns``. A lone expression echoes its value the way
    the prompt would; anything longer (several statements, a whole script
    with loops and defs) runs as a script."""
    tree = ast.parse(source)
    if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
        single = ast.Interactive(body=tree.body)
        exec(compile(single, '<repl>', 'single'), ns)  # noqa: S102 - this IS the REPL
        return
    exec(compile(tree, '<repl>', 'exec'), ns)  # noqa: S102


def main(
    argv: Sequence[str] = (),
    interact: Callable[..., Any] = code.interact,
    readline_setup: Callable[[Path, dict[str, Any]], bool] = setup_readline,
) -> int:
    args = list(argv)
    stay = '-i' in args
    args = [a for a in args if a != '-i']
    ns = build_namespace()
    if args:
        run_snippet(' '.join(args), ns)
        if not stay:
            return 0
    readline_setup(HISTORY, ns)
    set_title()
    # The roll watcher and CherryPy both print from outside the prompt's control.
    route_cherrypy_logs()
    # An open conversation holds collected rolls in memory and writes them only on a
    # debounce, so quitting without closing it discards real work. The watcher is a
    # daemon thread and simply dies with the process; this is what flushes.
    atexit.register(close_open_conversation)
    # Roster caches warm in the background so the prompt appears at once
    # (GM 2026-08-27); a pick before it finishes waits on the refresh lock.
    threading.Thread(target=warm_caches, name='l7r-cache-warm', daemon=True).start()
    interact(banner=help_text(), local=ns, exitmsg='')
    return 0
