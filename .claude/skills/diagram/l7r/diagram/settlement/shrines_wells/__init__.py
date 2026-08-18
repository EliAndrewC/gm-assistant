"""The shrines/wells subsystem of the Mode B settlement engine.

Split from the 1,179-line settlement/shrines_wells.py by feature 116 (constitution Principle X
clause 13). See CLAUDE.md in this directory for which submodule holds what.

This package was never ONE subsystem, and its NAME concedes it - the only module in the engine joined
by an `and`. Feature 025 sliced the 16,016-line original by position, so six unrelated subsystems
ended up sharing a file: religious halls, torii avenues, the well subsystem, a general seat-finding
API, draft byres, and woodland stands. The seven submodules are therefore grouped by what a session
comes here to CHANGE, and they are deliberately uneven in size - a partition tuned for equal files
would have to cut a cluster that no task cuts.

`ShrinesWellsMixin` exists ONLY to preserve settlement/core.py's single import and its position in
the `class Settlement(...)` base list - the split is meant to be invisible above this line. Sub-mixin
methods reach each other through `self.` on the composed Settlement, so a cross-submodule call needs
no import and the partition can be re-cut later without touching core.py. wellground.py is the hub:
wells.py and seats.py call into it and it calls out to neither.

The base order below is source order and is behaviorally irrelevant - no name is defined twice, which
is what the composed-surface guard's second assertion exists to keep true.
"""

from .byres import COURTYARD_REACH as COURTYARD_REACH
from .byres import DraftByresMixin
from .byres import courtyard_annex_span as courtyard_annex_span
from .seats import OpenSeatMixin
from .shrines import ShrineHallsMixin
from .torii import ToriiAvenueMixin
from .wellground import WellGroundMixin
from .wells import WellsMixin
from .woods import TreeStandsMixin


class ShrinesWellsMixin(
    ShrineHallsMixin,
    ToriiAvenueMixin,
    WellGroundMixin,
    WellsMixin,
    OpenSeatMixin,
    DraftByresMixin,
    TreeStandsMixin,
):
    """The composed shrines/wells surface. No members of its own by design - see the module docstring."""
