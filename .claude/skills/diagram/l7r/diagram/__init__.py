"""The `/diagram` engine - Mode A compound plans and Mode B settlement maps.

This is a REGULAR package (it has this file) sitting inside `l7r/`, which is a PEP 420 NAMESPACE
portion (it deliberately has no `__init__.py`). The asymmetry is the point of feature 119:

- `l7r/` has no `__init__.py`, so this directory's contents merge with the other `l7r` portion in
  `/gm-assistant/webapp/` under one parent package. `import l7r.app` and
  `import l7r.diagram.settlement` therefore work in the same interpreter, which is what makes it
  possible for the toolkit webapp to render a map without two colliding top-level packages both
  named `l7r`.
- `l7r/diagram/` DOES have this file, so the engine is one named package with one identity rather
  than a second namespace that some other tree could silently merge into.

**Never add `l7r/__init__.py`.** It would make that directory a regular package, terminate the
import search there, and make the webapp's portion stop existing - with no error at the point of
the mistake. `tests/test_namespace_portion.py` guards it.

The skill directory (three levels up) remains the `sys.path` root: `pool/`, `tests/`, the `Makefile`
and `pyproject.toml` all stay there, which is why every pool generator's bootstrap block
(`SKILL = dirname(dirname(HERE))`) is unchanged by the move. Modules are still run as modules from
that directory - `python3 -m l7r.diagram.check_village`, `python3 -m l7r.diagram.pipeline.regen`.

What is in here, and which index to load, is in the skill's `CLAUDE.md` "Where things live" table.
"""

from __future__ import annotations
