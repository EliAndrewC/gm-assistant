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
from l7r.repl.dice import DiceTotal
from l7r.repl.names import warm_caches
from l7r.repl.rolls import console, npcskills
from l7r.repl.rolls.conversation import close_open_conversation
from l7r.repl.rolls.members import use_namespace

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
    ns['help_l7r'] = lambda full=True: print(help_text(full))
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


class SettlingPrompt(str):
    """`sys.ps1` that settles the GM's last statement before the prompt is drawn.

    Feature 230: in a conversation with several NPCs, `xky(5, 3) - tact` waits until
    the END of the statement for its NPC (`npcskills.settle_pending`), because `- souma`
    may still follow. An expression statement ends at the displayhook; an assignment
    (`r = xky(5, 3) - tact`) never reaches it, and the next prompt is the first moment
    that is certainly after it. A `str` subclass, so everything that reads the prompt
    as text still can - but only the MAIN thread settles: the watcher redraws the
    prompt too (`console.print_above`), and settling can ask the GM a question.
    """

    def __str__(self) -> str:
        if threading.current_thread() is threading.main_thread():
            try:
                npcskills.settle_pending()
            except Exception as exc:  # noqa: BLE001 - the prompt must still be drawn
                print(f'  ! {exc}')
        return str.__str__(self)


def install_prompt_hooks() -> None:
    """Settle bare tags at the end of each statement (feature 230). Idempotent.

    The displayhook settles BEFORE the value is echoed, so a raise (`PrimaryLeft`) is
    a traceback the GM sees, and the echo is rebuilt from the recorded roll so it shows
    the total after any oppose penalty the settling took off. It chains to the
    displayhook it replaced, which is what keeps `_` - and `_ + 15` - working.
    """
    previous = sys.displayhook
    if getattr(previous, 'l7r_settles', False):
        return

    def settle_then_echo(value: object) -> None:
        try:
            npcskills.settle_pending()
        except Exception:
            # Echo anyway: `_` must be THIS roll, or the `_ - souma` the error tells the
            # GM to type would mark the previous statement's value instead.
            previous(value)
            raise
        if isinstance(value, DiceTotal) and int(value) != value.entry.total:
            value = DiceTotal(value.entry.total, value.entry)
        previous(value)

    settle_then_echo.l7r_settles = True  # type: ignore[attr-defined]
    sys.displayhook = settle_then_echo
    sys.ps1 = SettlingPrompt(str(getattr(sys, 'ps1', '>>> ')))


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
    # Feature 230: a conversation member's handle (`souma`) goes into THIS namespace,
    # and a bare tag is settled at the end of each statement, one-shot or at the prompt.
    use_namespace(ns)
    install_prompt_hooks()
    if args:
        run_snippet(' '.join(args), ns)
        npcskills.settle_pending()  # an assignment statement never reaches the displayhook
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
