"""The land-surface subsystem of the Mode B settlement engine.

Split from the 1,187-line settlement/land.py by feature 120 (constitution Principle X clause 13),
the LAST un-split file in this package. See CLAUDE.md in this directory for which submodule holds
what.

This package was a RESIDUE BUCKET, not a chain. `land.py` was cut positionally out of the
16,016-line settlement.py by feature 025, so what it held was four unrelated land subsystems that
happened to be adjacent - a polder dike, wet ground, dry ground cover, and near-ring farmland - plus
three farmstead helpers that belonged in homestead_parts.py all along and moved there with this
split. The partition is therefore by SUBJECT, and the test of it is that a real task stays inside one
module: re-siting the wet toe is wet.py alone, changing what scrub looks like is cover.py alone,
re-shaping the dike is dikes.py alone.

`LandMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. cover.py is the one real
caller: `hinterland` composes `commons` (its own) with `toe_band` and `marsh` (wet.py).

The base order below is source order and is behaviorally irrelevant - no name is defined twice,
which is what the composed-surface guard's second assertion exists to keep true.
"""

from .cover import GroundCoverMixin
from .dikes import DikeMixin
from .nearring import NearRingMixin
from .wet import WetGroundMixin
from .wet import surface_water_dist as surface_water_dist


class LandMixin(
    DikeMixin,
    WetGroundMixin,
    GroundCoverMixin,
    NearRingMixin,
):
    """The composed land surface. No members of its own by design - see the module docstring."""
