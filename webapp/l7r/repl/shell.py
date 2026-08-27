"""Start the GM REPL: readline, tab completion, a history file, the banner.

``main(argv)``: with no arguments, an interactive prompt; with arguments,
they are joined and run as a script in the same namespace and the process
exits - ``repl.py 'xky(6, 3)'`` echoes the value, a multi-line quoted
script just runs. ``-i`` after a snippet stays interactive afterwards.
"""

from __future__ import annotations

import ast
import code
import contextlib
import os
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from l7r.repl import help_text, namespace
from l7r.repl.names import warm_caches

HISTORY = Path(os.environ.get('L7R_REPL_HISTORY', Path.home() / '.l7r_repl_history'))


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
    # Roster caches warm in the background so the prompt appears at once
    # (GM 2026-08-27); a pick before it finishes waits on the refresh lock.
    threading.Thread(target=warm_caches, name='l7r-cache-warm', daemon=True).start()
    interact(banner=help_text(), local=ns, exitmsg='')
    return 0
