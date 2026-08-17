"""Unit tests for `sitegen/` - the machinery the settlement tiers SHARE.

Mirrors the source layout like every other package here: a test for `sitegen/geom.py` lives in
`test_geom.py`. These tests moved out of `tests/hamletgen/` with their subjects in feature 119, and
they are deliberately self-contained - `tests/sitegen/` must not import from `tests/hamletgen/`,
for the same reason `sitegen` must not import `hamletgen`. A shared library whose TESTS depend on
one tier is only nominally shared.

`test_direction.py` is the guard for that rule on the source side.
"""

import os
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if SKILL not in sys.path:  # so the tests import the engine whatever the rootdir
    sys.path.insert(0, SKILL)  # pragma: no cover - under pytest the skill dir is already on the path
