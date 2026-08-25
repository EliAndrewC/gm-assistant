"""Refuse to run the webapp gates from the MAIN checkout.

Main is the integration point, never a workspace (CLAUDE.md "Session clones"):
a test/gate run writing into main's tree races with another session's
mid-procedure push-to-checkout (the 2026-07-20 double-push post-mortem). The
rootdir conftest imports this module, so any pytest run in main aborts with
the reminder below; the Makefile carries the same guard for its targets.
The GM can deliberately override with GM_ASSISTANT_ALLOW_MAIN=1; a session
must not.

MAIN IS THE TREE THAT CONTAINS ``.clones/`` (feature 131, 2026-08-25). A
session clone or a detached worktree has no ``.clones/`` of its own (it is
gitignored), so the rule needs no hardcoded path and holds at /gm-assistant
and at /diagram alike.
"""

import os


def _git_top(path: str) -> str | None:
    """The nearest ancestor of `path` (inclusive) that holds a `.git` entry, or None."""
    d = path if os.path.isdir(path) else os.path.dirname(path)
    while True:
        if os.path.exists(os.path.join(d, '.git')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def is_main_tree(path: str) -> bool:
    """True when `path` is inside a checkout that holds `.clones/` and is not itself a clone."""
    p = os.path.realpath(path)
    if '/.clones/' in p:
        return False
    top = _git_top(p)
    return top is not None and os.path.isdir(os.path.join(top, '.clones'))


def assert_not_main_tree(path: str | None = None) -> None:
    p = path if path is not None else __file__
    if is_main_tree(p) and os.environ.get('GM_ASSISTANT_ALLOW_MAIN') != '1':
        raise SystemExit(
            'ERROR: this ran from the MAIN tree. Main is the integration point,\n'
            "never a workspace - every gate and test runs inside the session's own clone under\n"
            "<main>/.clones/. Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md\n"
            'if it has fallen out of your context window) for the procedure: create or reuse\n'
            ".clones/<kebab-cased-session-name>, sync it in with 'git pull origin main', and run\n"
            'this same command from inside that clone.\n'
            '(GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1)'
        )


assert_not_main_tree()
