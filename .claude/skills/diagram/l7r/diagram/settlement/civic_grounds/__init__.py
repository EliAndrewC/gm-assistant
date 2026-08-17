"""The civic-grounds subsystem of the Mode B settlement engine.

Split from the 1,162-line settlement/civic_grounds.py by feature 115 (constitution Principle X
clause 13). See CLAUDE.md in this directory for which submodule holds what.

Like settlement/structures/ and unlike settlement/fields/ or settlement/city/, this package was never
ONE subsystem: civic_grounds.py held four unrelated ones - funerary ground, judicial ground, civic
and commercial works, and lodging with its livestock yards. So the submodules are grouped by what a
session comes here to CHANGE, and they are deliberately uneven in size.

`CivicGroundsMixin` exists ONLY to preserve settlement/core.py's single import and its position in
the `class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. Two such calls exist by
design: civic.precinct_interior -> funerary.cemetery, and lodging.flush_stable_yards ->
stable_yard._stable_yard.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .civic import CivicWorksMixin
from .funerary import FuneraryGroundsMixin
from .justice import JusticeGroundsMixin
from .lodging import LodgingMixin
from .stable_yard import StableYardMixin


class CivicGroundsMixin(
    FuneraryGroundsMixin,
    JusticeGroundsMixin,
    CivicWorksMixin,
    LodgingMixin,
    StableYardMixin,
):
    """The composed surface. Holds no members of its own - see the module docstring."""
