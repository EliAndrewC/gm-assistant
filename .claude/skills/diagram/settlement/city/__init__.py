"""The provincial-city subsystem of the Mode B settlement engine.

Split from the 1,582-line settlement/city.py by feature 113 (constitution Principle X clause 13).
See CLAUDE.md in this directory for which submodule holds what.

`CityMixin` exists ONLY to preserve settlement/core.py's single import and its position in the
`class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call
needs no import and the partition can be re-cut later without touching core.py. There is exactly
one such call today: farmland_ring (canals) -> sluice_gate (moat).

The base order below is source order and is behaviorally irrelevant - no name is defined twice,
which is what the composed-surface guard's second assertion exists to keep true.
"""

from .bridges import BridgesMixin
from .canals import CanalsMixin
from .civic import CityCivicMixin
from .moat import MoatMixin
from .walls import WallsMixin
from .waterfront import WaterfrontMixin


class CityMixin(WallsMixin, MoatMixin, CanalsMixin, WaterfrontMixin, BridgesMixin, CityCivicMixin):
    """The composed city surface. No members of its own by design - see the module docstring."""
