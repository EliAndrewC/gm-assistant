"""Guard: `l7r` must stay a PEP 420 namespace portion, and `l7r.diagram` a regular package.

Feature 119 put the engine under `l7r.diagram` so that it shares one parent package with the
toolkit webapp's `l7r.app` / `l7r.names` / ... in `/gm-assistant/webapp/l7r/`. That sharing works
only because NEITHER `l7r/` directory has an `__init__.py`: a regular package terminates the import
search, so the moment one portion becomes regular, the other silently stops existing.

Silently is the operative word - adding `l7r/__init__.py` raises nothing where the mistake is made.
It surfaces later as a `ModuleNotFoundError` somewhere that looks unrelated, which is why this is a
test rather than a note in a CLAUDE.md.

`__file__` is the discriminator: `None` for a namespace portion, the path of `__init__.py` for a
regular package. `l7r.diagram` is deliberately the opposite case - it HAS an `__init__.py`, so the
engine is one named package with one identity rather than a second namespace that another tree
could merge into by accident.
"""

from __future__ import annotations

import l7r
import l7r.diagram


def test_l7r_is_a_namespace_portion_not_a_regular_package() -> None:
    assert l7r.__file__ is None, (
        f'l7r.__file__ is {l7r.__file__!r}, so l7r is a REGULAR package again - something added '
        '.claude/skills/diagram/l7r/__init__.py. Delete that file rather than "fixing" this test: '
        'while it exists, the webapp cannot import l7r.app at all. See specs/119-l7r-diagram-namespace/.'
    )


def test_l7r_diagram_is_a_regular_package() -> None:
    assert l7r.diagram.__file__ is not None, (
        'l7r.diagram lost its __init__.py, so the engine is a namespace portion rather than a named package. Restore .claude/skills/diagram/l7r/diagram/__init__.py.'
    )


def test_the_skill_root_is_still_the_sys_path_root() -> None:
    """The engine moved two levels deeper; every module that computes the skill root moved with it.

    A wrong depth here is silent - the constant just points at `l7r/diagram/` and every path built
    from it lands one directory short of `pool/`.
    """
    import os

    from l7r.diagram.pipeline import gencache, pool_index, render_cache

    skill_root = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    for name, value in (
        ('gencache.HERE', gencache.HERE),
        ('pool_index.SKILL_DIR', pool_index.SKILL_DIR),
        ('render_cache.SKILL_DIR', render_cache.SKILL_DIR),
    ):
        assert os.path.realpath(value) == skill_root, f'{name} is {value!r}, not the skill root {skill_root!r}'
