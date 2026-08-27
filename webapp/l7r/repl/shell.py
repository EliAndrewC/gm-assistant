"""Start the GM REPL: readline, tab completion, a history file, the banner.

``main(argv)``: with no arguments, an interactive prompt; with arguments,
they are joined and run as one statement in the same namespace and the
process exits (``repl.py 'xky(6, 3)'``). ``-i`` after a snippet stays
interactive afterwards.
"""

from __future__ import annotations

import code
import contextlib
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from l7r.repl import help_text, namespace

HISTORY = Path(os.environ.get('L7R_REPL_HISTORY', Path.home() / '.l7r_repl_history'))


def build_namespace() -> dict[str, Any]:
    ns = namespace()
    ns['help_l7r'] = lambda: print(help_text())
    ns['__name__'] = '__l7r_repl__'
    return ns


def setup_readline(history: Path = HISTORY) -> bool:
    """Tab completion and persistent history; False when readline is absent."""
    try:
        import atexit
        import readline
        import rlcompleter  # noqa: F401 - registers the completer
    except ImportError:  # pragma: no cover - Windows, or a stripped build
        return False
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
    """Run ``source`` in ``ns``; an expression statement echoes its value
    the way the prompt would."""
    compiled = code.compile_command(source, symbol='single')
    if compiled is None:
        raise SyntaxError(f'incomplete statement: {source!r}')
    exec(compiled, ns)  # noqa: S102 - this IS the REPL


def main(
    argv: Sequence[str] = (),
    interact: Callable[..., Any] = code.interact,
    readline_setup: Callable[[], bool] = setup_readline,
) -> int:
    args = list(argv)
    stay = '-i' in args
    args = [a for a in args if a != '-i']
    ns = build_namespace()
    if args:
        run_snippet(' '.join(args), ns)
        if not stay:
            return 0
    readline_setup()
    interact(banner=help_text(), local=ns, exitmsg='')
    return 0
