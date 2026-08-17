"""Rootdir pytest setup.

Importing ``l7r.app`` first fully loads the toolkit (which mounts and imports
the chargen sub-app in the correct order), resolving a pre-existing circular
import in chargen's package ``__init__``. This rootdir conftest runs before
pytest imports the chargen package to collect its tests, so chargen.* is already
in sys.modules by then.

It is ``l7r.app`` rather than ``l7r`` because ``l7r`` is a namespace portion
with no code in it (feature 119); the mount is a side effect of the module that
performs it.
"""

import l7r.app  # noqa: F401  (imported for its import-time side effect)
import mainguard  # noqa: F401  (import-time guard: gates never run from the MAIN tree)
