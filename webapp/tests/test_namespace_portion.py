"""Guard: `l7r` must stay a PEP 420 namespace portion (feature 119).

`l7r` is shared between two directories on two different `sys.path` roots - this webapp
(`l7r.app`, `l7r.names`, ...) and the diagram engine (`l7r.diagram.*`, under
`.claude/skills/diagram/l7r/`). That sharing works only because NEITHER directory has an
`__init__.py`: a regular package terminates the import search, so the moment one portion becomes
regular, the other silently stops existing.

Silently is the operative word. Adding `webapp/l7r/__init__.py` raises nothing at the point of the
mistake - it surfaces later as a `ModuleNotFoundError` somewhere that looks unrelated. Hence a test
rather than a convention.

`__file__` is the discriminator: `None` for a namespace portion, the path of `__init__.py` for a
regular package.
"""

from __future__ import annotations

import l7r


def test_l7r_is_a_namespace_portion_not_a_regular_package() -> None:
    assert l7r.__file__ is None, (
        f'l7r.__file__ is {l7r.__file__!r}, so l7r is a REGULAR package again - something re-added '
        'webapp/l7r/__init__.py. Delete that file rather than "fixing" this test: while it exists, '
        'the diagram engine cannot import l7r.diagram at all. See specs/119-l7r-diagram-namespace/.'
    )


def test_l7r_still_mounts_the_cherrypy_tree_when_app_is_imported() -> None:
    """The side effect that `__init__.py` used to carry now belongs to a module you name."""
    import l7r.app

    assert l7r.app.Root is not None
