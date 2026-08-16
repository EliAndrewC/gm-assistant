"""The one civic BUILDING the city tier draws.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

from typing import TYPE_CHECKING, Any

from .._geom import (
    GOVERNOR_CAPTION_FS,
)

if TYPE_CHECKING:
    from ..core import Settlement


class CityCivicMixin:
    def governor_mansion(self: Settlement, x: float, y: float, w: float = 320, h: float = 210, label: str = "Governor's Mansion", gate_dir: str = "west") -> Any:  # type: ignore[misc]
        """The provincial governor's walled mansion - a large compound, grander than a county
        magistrate's manor. Reuses the manor glyph (walls + gate + empty court; the interior is
        a separate Mode A diagram) and moves the record to M['governor_mansion'].

        THE CAPTION GOES INSIDE THE COURT, not above the walls like a manor's (GM 2026-08-08).
        The court is deliberately blank - its buildings are a separate Mode A sheet - so it is the
        one patch of guaranteed clear ground on a packed city map, while the band above the walls
        is prime housing: Tango's gen had already worked this out by hand and said so in a comment
        (its reserved caption box "was eating a full housing row"), and Nagahara and Minami took
        the manor default and hung the caption over their samurai quarters. Doing it here makes
        the three cities agree and leaves no hand seat to re-place every time the yamen moves.
        The size is GOVERNOR_CAPTION_FS, which is what makes the caption fit between the walls."""
        self.manor(x, y, w, h, "", gate_dir=gate_dir, gate_ft=18.0)  # a yamen's formal gatehouse passes ~18 real ft; caption below, not manor's
        self.M["governor_mansion"] = self.M["manors"].pop()  # not an outside samurai estate
        self.M["governor_mansion"]["label"] = label
        if label:
            # ~0.36 x the font size below the compound's center puts the glyphs' OPTICAL middle on
            # it (a baseline sits under the x-height, so centering the baseline rides high).
            self.label(x, y + GOVERNOR_CAPTION_FS * 0.36, label, GOVERNOR_CAPTION_FS, weight="bold")
        return self.M["governor_mansion"]
