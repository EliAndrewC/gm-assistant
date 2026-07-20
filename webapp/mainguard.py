"""Refuse to run the webapp gates from the MAIN /gm-assistant checkout.

Main is the integration point, never a workspace (CLAUDE.md "Session clones"):
a test/gate run writing into main's tree races with another session's
mid-ritual push-to-checkout (the 2026-07-20 double-push post-mortem). The
rootdir conftest imports this module, so any pytest run in main aborts with
the reminder below; the Makefile carries the same guard for its targets.
The GM can deliberately override with GM_ASSISTANT_ALLOW_MAIN=1; a session
must not.
"""

import os


def assert_not_main_tree(path: str | None = None) -> None:
    p = os.path.realpath(path if path is not None else __file__)
    in_main = p.startswith('/gm-assistant/') and '/.clones/' not in p
    if in_main and os.environ.get('GM_ASSISTANT_ALLOW_MAIN') != '1':
        raise SystemExit(
            'ERROR: this ran from the MAIN /gm-assistant tree. Main is the integration point,\n'
            "never a workspace - every gate and test runs inside the session's own clone under\n"
            "/gm-assistant/.clones/. Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md\n"
            'if it has fallen out of your context window) for the procedure: create or reuse\n'
            ".clones/<kebab-cased-session-name>, sync it in with 'git pull origin main', and run\n"
            'this same command from inside that clone.\n'
            '(GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1)'
        )


assert_not_main_tree()
