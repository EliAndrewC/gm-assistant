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


_BORROW_REACH = 120.0  # a neighbour this close can walk over and borrow the team (see draft_byres)

# HOW FAR A COURTYARD-FORM BYRE MAY STAND FROM THE HOUSE IT BELONGS TO. In that form the shed is the
# homestead's own stable wing, not common property, so it gets its owner's yard and no more: the
# spiral is allowed 18 px past the first seat that clears the wall, where the shared form gets 70.
# Exported because `byres_stand_in_their_declared_form` measures the same span - the placer and its
# check read ONE source, which is the standing rule here.
COURTYARD_REACH = 18.0


def courtyard_annex_span(hw: float, hh: float, bh: float) -> float:
    """The farthest a courtyard-form byre's CENTER may stand from its owner farmhouse's center.

    `max(hw, hh) / 2` is the house's own half-extent on its longest side (the spiral is circular, so
    it must clear the worst case), `bh * 0.55` steps just past the byre's own half-depth, and
    `COURTYARD_REACH` is the search budget past that. A byre farther out than this is not an annex of
    anybody's homestead, whatever the manifest declares."""
    return max(hw, hh) / 2 + bh * 0.55 + COURTYARD_REACH


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
        # WHICH OF THE TWO ATTESTED FORMS THIS SETTLEMENT USES (knob `byre_form`, 2026-08-18).
        # `courtyard` = the stable wing of its owner's own homestead (magariya / sanheyuan); the shed
        # follows the WEALTH, so the owners are taken straight down the wealth ranking with no spread
        # objective, the search is held to the owner's own yard, and two byres may stand near each
        # other because their houses do. `detached_commons` = the shared shed on the ground between
        # homesteads, unchanged and still the default: spread by minimax, separated by `gap`, allowed
        # 70 px of spiral. The reasoning for having a knob at all is at the registration in
        # `_knobs.py`; the DECLARATION is written to meta so the gate can hold the drawing to it,
        # because a form nobody records is a form nothing can check.
        form = self.resolve("byre_form")
        self.M["meta"]["byre_form"] = form
        _courtyard = form == "courtyard"
        _reach = COURTYARD_REACH if _courtyard else 70.0
        _sep = 0.0 if _courtyard else gap
        houses = [h for h in self.M.get("houses", []) if h.get("kind") == "plain"]
        ranked = sorted(houses, key=lambda h: (-h.get("wealth", 1.0), h["x"], h["y"]))  # buffalo owners = the wealthier
        target = max(1, round(len(houses) * fraction))
        out: list[Pt] = []
        # SPREAD THE BYRES ACROSS THE SETTLEMENT, do not drain toward one end (settlement-review on
        # Kashikawa and Sawada, 2026-08-17). Walking the wealth ranking in order and taking the first
        # clear gap sends every byre to whichever flank still has open verge: measured along each
        # cluster's own principal axis, all four byres occupied the SW 143 ft of a 993 ft settlement
        # on Kashikawa (14%), 160 of 810 ft on Sawada (20%), and every map put them in one half.
        # These are SHARED sheds - the whole point is that a household too poor for its own team
        # borrows or hires one (`settlements/homesteads.md`) - so a byre quarter at one end defeats
        # the sharing the feature exists to depict, leaving most households several hundred feet from
        # the nearest.
        #
        # The fix is the MINIMAX idiom the well siting already uses: after the first, take the
        # wealthiest candidate that stands FURTHEST from every byre already placed. Deterministic (no
        # RNG - the key is a distance, then wealth, then position), and it only changes WHICH owners
        # get one, never how many or how the spiral seats them.
        _pool = list(ranked)
        while len(out) < target and _pool:
            if out and not _courtyard:
                # SPREAD, THEN SHARE. Farthest-point alone minimises the worst walk, which is the
                # right coverage objective - but with every house at wealth 1.0 the tie-break
                # collapses to pure distance, so it picks the most ISOLATED homestead and the shed
                # reads as that household's private one. That is the inverse of the doctrine: a byre
                # is shared precisely so a household owning no team can borrow from a neighbour
                # (settlements/homesteads.md), and the neighbour has to be there to borrow from.
                # So: take the spread score, then among the candidates within a quarter of the best
                # prefer the one with the most households in borrowing distance.
                _best = max(min(math.hypot(q["x"] - bx, q["y"] - by) for bx, by in out) for q in _pool)
                _near = [q for q in _pool if min(math.hypot(q["x"] - bx, q["y"] - by) for bx, by in out) >= _best * 0.75]
                h = max(_near, key=lambda q: (sum(1 for o in houses if o is not q and math.hypot(o["x"] - q["x"], o["y"] - q["y"]) <= _BORROW_REACH), q.get("wealth", 1.0), -q["x"], -q["y"]))
            else:
                h = _pool[0]
            _pool.remove(h)
            # The courtyard form starts its spiral at the owner's OWN half-extent (the same span
            # `courtyard_annex_span` states, and the same one the gate measures), the shared form at
            # the house's diagonal - a shed on the commons should clear the homestead entirely.
            rr0 = (courtyard_annex_span(h["w"], h["h"], bh) - COURTYARD_REACH) if _courtyard else (math.hypot(h["w"], h["h"]) / 2 + bh)
            rr = rr0
            done = False
            while rr < rr0 + _reach and not done:
                for a in range(0, 360, 30):
                    cx = h["x"] + rr * math.cos(math.radians(a))
                    cy = h["y"] + rr * math.sin(math.radians(a))
                    if (
                        self._fits(cx, cy, bw + 6, bh + 6)
                        and not any(point_in_poly(cx, cy, ff) or edge_dist(cx, cy, ff) < bh for ff in self.field_polys)
                        and all((bx - cx) ** 2 + (by - cy) ** 2 > _sep * _sep for bx, by in out)
                    ):
                        self._draw_byre(cx, cy, bw, bh)
                        self.placed.append((cx, cy, bw, bh))
                        self.M["byres"].append({"x": round(cx, 1), "y": round(cy, 1), "w": bw, "h": bh, "rot": 0})
                        out.append((cx, cy))
                        done = True
                        break
                rr += 16
        return out
