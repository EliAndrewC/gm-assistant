"""The draft-animal byre (ox / water-buffalo shed) standing among the homesteads.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING

from .._geom import (
    Pt,
    edge_dist,
    point_in_poly,
)

if TYPE_CHECKING:
    from ..core import Settlement


class DraftByresMixin:
    def _draw_byre(self: Settlement, cx: float, cy: float, w: float, h: float, rot: float = 0) -> None:  # type: ignore[misc]
        """A small OPEN-FRONTED draft-animal shed (ox / water-buffalo byre): a plank-and-thatch roof with a
        dark stall mouth along the front, distinct from the solid gray kura storehouse and from a dwelling."""
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.6" fill="#B0905E" stroke="#59431F" stroke-width="1.1"/>')  # thatch/plank roof
        g.append(f'<rect x="{-w / 2 + 2:.1f}" y="{h * 0.02:.1f}" width="{w - 4:.1f}" height="{h * 0.4:.1f}" rx="1" fill="#33291C"/>')  # the shaded open stall mouth
        g.append(f'<line x1="{-w / 2 + 2:.1f}" y1="{-h * 0.08:.1f}" x2="{w / 2 - 2:.1f}" y2="{-h * 0.08:.1f}" stroke="#59431F" stroke-width="0.8" opacity="0.6"/>')  # roof ridge
        g.append('</g>')
        self.add(''.join(g))

    def draft_byres(self: Settlement, fraction: float = 0.2, gap: float = 64) -> list[Pt]:  # type: ignore[misc]
        """DRAFT-ANIMAL BYRES (ox / water-buffalo sheds) standing in the courtyards among the homesteads.
        Wet-rice plowing and puddling turns on a draft animal, but a buffalo was a costly asset that poorer
        households SHARED or hired, so a village keeps only a MINORITY of byres (~one per 4-5 households ->
        `fraction`) - shared sheds, not one per farm. HOUSE-DRIVEN: for the wealthier homesteads (buffalo
        owners) in turn, spiral outfrom the house to find the nearest clear gap just past its reserved
        footprint (off every other footprint, lane, block, crop, via `_fits`), keeping byres `gap` px apart so
        they read as scattered, not clumped; a homestead boxed in on all sides is skipped. Call AFTER
        farmsteads() (homesteads fixed) and BEFORE the grove (which then skips the byres). Records M['byres']."""
        bs = self.bscale
        # SIZE: a shared byre houses ~1-2 draft animals (an ox / water-buffalo stall is ~2x3 m) plus fodder ->
        # ~16 x 11 ft ~ 15 m2, well under the ~120 m2 farmhouse. To-scale tiers carry it in FEET (drawn at ftpx);
        # legacy tiers scale it with the urban glyph grain (bscale).
        if self._toscale():
            bw, bh = round(self.px(16.12), 1), round(self.px(10.92), 1)
        else:
            bw, bh = round(15.5 * bs, 1), round(10.5 * bs, 1)
        houses = [h for h in self.M.get("houses", []) if h.get("kind") == "plain"]
        ranked = sorted(houses, key=lambda h: (-h.get("wealth", 1.0), h["x"], h["y"]))  # buffalo owners = the wealthier
        target = max(1, round(len(houses) * fraction))
        out: list[Pt] = []
        for h in ranked:
            if len(out) >= target:
                break
            rr = math.hypot(h["w"], h["h"]) / 2 + bh
            done = False
            while rr < math.hypot(h["w"], h["h"]) / 2 + bh + 70 and not done:
                for a in range(0, 360, 30):
                    cx = h["x"] + rr * math.cos(math.radians(a))
                    cy = h["y"] + rr * math.sin(math.radians(a))
                    if (
                        self._fits(cx, cy, bw + 6, bh + 6)
                        and not any(point_in_poly(cx, cy, ff) or edge_dist(cx, cy, ff) < bh for ff in self.field_polys)
                        and all((bx - cx) ** 2 + (by - cy) ** 2 > gap * gap for bx, by in out)
                    ):
                        self._draw_byre(cx, cy, bw, bh)
                        self.placed.append((cx, cy, bw, bh))
                        self.M["byres"].append({"x": round(cx, 1), "y": round(cy, 1), "w": bw, "h": bh, "rot": 0})
                        out.append((cx, cy))
                        done = True
                        break
                rr += 16
        return out
