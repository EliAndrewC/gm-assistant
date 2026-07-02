"""Rootdir pytest setup.

Importing ``l7r`` first fully loads the toolkit (which mounts and imports the
chargen sub-app in the correct order), resolving a pre-existing circular import
in chargen's package ``__init__``. This rootdir conftest runs before pytest
imports the chargen package to collect its tests, so chargen.* is already in
sys.modules by then.
"""

import l7r  # noqa: F401  (imported for its import-time side effect)
