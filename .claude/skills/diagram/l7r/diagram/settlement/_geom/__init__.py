"""The pure geometry / spatial helpers of the Mode B settlement engine.

Split from the 1,303-line settlement/_geom.py by feature 117 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

The file was the most widely imported module in the engine - 41 of the 47 files under settlement/,
plus check_village, hamletgen and two tools/ scripts - and its `no self, just geometry` calling
convention hid the fact that it held eight unrelated populations: coordinate math, collision
predicates, spatial indexes, a placement memo, caption typography, manifest readers, curve
generation, and three things that are not geometry at all. Every one of those readers paid for all
eight. The submodules are grouped by what a session comes here to CHANGE, and are deliberately
uneven in size.

THE SURFACE IS DERIVED, NOT MAINTAINED (Principle X clause 14, feature 027's idiom): the star
imports below re-export every submodule's public names - mypy treats star-imported public names as
explicitly exported even under strict's no_implicit_reexport, so no __all__ is needed. `import *`
does NOT carry underscore names, so the six with consumers by name are re-exported by the aliased
block. tests/settlement/test_geom.py guards the two properties this design rests on: the whole
pre-split surface still resolves, and no public name is bound in two submodules (a star-import
collision is silent - no MRO to catch it, and neither ruff nor mypy reports one).

Layering, so the package stays acyclic: base <- primitives <- overlap <- everything else; seatmemo
and village import nothing from the package. Respect it when adding a member.
"""

from .base import *
from .base import _assert_not_main_tree as _assert_not_main_tree
from .curves import *
from .extents import *
from .indexes import *
from .labels import *
from .overlap import *
from .overlap import _aabb_gap as _aabb_gap
from .overlap import _rect_ring as _rect_ring
from .overlap import _union_area as _union_area
from .primitives import *
from .primitives import _signed_area as _signed_area
from .seatmemo import *
from .village import *
from .village import _VILLAGE_POP_DIST as _VILLAGE_POP_DIST
from .walls import *
from .walls import _box_hits_run as _box_hits_run
from .ways import *
