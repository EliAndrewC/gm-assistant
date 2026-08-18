"""The draft-animal byre (ox / water-buffalo shed) standing among the homesteads.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import math
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    edge_dist,
    point_in_poly,
)

if TYPE_CHECKING:
    from ..core import Settlement


_BORROW_REACH = 120.0  # a neighbor this close can walk over and borrow the team (see draft_byres)

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
    def _courtyard_byre_seat(self: Settlement, h: Mapping[str, Any], bw: float, bh: float) -> tuple[float, float, float, float, float] | None:  # type: ignore[misc]
        """A courtyard-form byre's seat: the magariya's short arm, ABUTTING a free side wall of its owner.

        WHY THIS EXISTS AT ALL - all four settlement-reviews, 2026-08-18, same day the knob shipped.
        The first cut of the courtyard form changed the FORM in the manifest and left the PLACEMENT
        IDIOM alone: it ran the shared shed's first-fit spiral with a shorter leash. Measured, that
        put Sawada's three byres 8.9 / 8.9 / 23.0 ft off their owners' BACK corners at `rot: 0`
        against houses raked -0.1 to -3.6 deg, on the opposite side of the house from that
        household's work yard - and the 23.0 ft one is indistinguishable from Kashikawa's detached
        22.7 ft and Inashiro's 22.8 ft. The two forms' distance ranges OVERLAPPED. That is a degree,
        not a form, and constitution Principle XII says liberty covers a degree while a knob must be
        a form; the knob was buying nothing it was added to buy. It also under-seated badly, because
        a first-fit spiral in a yard the appurtenances already fill mostly finds nothing: over 24
        cohort seeds the courtyard form seated 8 of 16 asked byres against detached's 18 of 18, and
        on Mizuguchi it seated NONE, silently deleting three byres from a shipped map.
        (`byres_meet_their_target` now catches that class.)

        THE SHEET ALREADY HAD THE RIGHT VOCABULARY and the byre was not using it. The attached kura
        (`houses.house`, `_farm_shed_rect`) is drawn INSIDE the house's own transform group, shares
        its rake exactly, abuts its wall, and records an `of` back-reference. Both named precedents
        want that: the Nambu magariya's *umaya* is one L-shaped structure joined to the dwelling
        through the doma, and the sanheyuan's *xiangfang* are connected ranges bounding the court.
        So the arm is seated in the owner's LOCAL frame, on a side wall, rotated with the house, and
        offset along that wall toward the yard so house-plus-arm make the L that frames the working
        court. Side walls because the kura takes the back wall on a nucleated cluster and the yard
        and garden take the sunny front.

        Returns `(x, y, rot, aabb_w, aabb_h)` or None if neither wall is free - the caller then falls
        back to the shared form's spiral rather than dropping the byre, because a byre in the wrong
        place still beats a hamlet that plows without one."""
        hw, hh, rot = float(h["w"]), float(h["h"]), float(h.get("rot", 0.0) or 0.0)
        th = math.radians(rot)
        # WHICH WAY THE HOMESTEAD FACES, derived rather than assumed: the sign of the local-y offset
        # to this house's own work yard. Deriving it from the yard means the arm keeps framing the
        # court when a later change moves the yard, which pinning a compass side would not.
        _yards = self.M.get("threshing_yards") or []
        sy = 1.0
        if _yards:
            yx, yy = min(((float(y["x"]), float(y["y"])) for y in _yards), key=lambda p: math.hypot(p[0] - h["x"], p[1] - h["y"]))
            sy = 1.0 if (-(yx - h["x"]) * math.sin(th) + (yy - h["y"]) * math.cos(th)) >= 0 else -1.0
        for lyc in (sy * max(0.0, hh / 2.0 - bw / 2.0), 0.0):  # reach toward the court first, then sit centered on the wall
            for sx in (-1.0, 1.0):
                # ABUTTING, NOT OVERLAPPING - a 3 ft drip line rather than the kura's shared wall.
                # The first cut overlapped by 1.5 px to read as literally joined, the way the kura
                # is drawn inside the house's own transform, and that cost `no_structure_overlaps`
                # exactly one failing pair per byre. The kura gets away with it because it is drawn
                # as part of the house rather than as a structure in its own right; a byre is a
                # first-class overlap struct and has to keep its own footprint. At 1 ft/px a 3 ft
                # gap is 3 px - the two roofs still read as one L-shaped building, and the gap is
                # the eaves drip between them, which is what the space between a magariya's arms
                # actually is.
                lx = sx * (hw / 2.0 + bh / 2.0 + 3.0)
                cx = h["x"] + lx * math.cos(th) - lyc * math.sin(th)
                cy = h["y"] + lx * math.sin(th) + lyc * math.cos(th)
                brot = rot + (90.0 if sx < 0 else -90.0)  # long axis along the wall; the stall mouth opens OUTWARD, away from the house
                _c, _s = abs(math.cos(math.radians(brot))), abs(math.sin(math.radians(brot)))
                aw, ah = bw * _c + bh * _s, bw * _s + bh * _c
                if self._byre_clear_of_all_but(cx, cy, aw, ah, h):
                    return cx, cy, brot, aw, ah
        return None

    def _byre_clear_of_all_but(self: Settlement, cx: float, cy: float, aw: float, ah: float, h: Mapping[str, Any]) -> bool:  # type: ignore[misc]
        """Collision test for an ATTACHED annex: clear of everything placed EXCEPT its own farmhouse.

        `_fits` cannot answer this - it inflates the box and tests it against every placed footprint
        including the owner, so an abutting seat is refused by construction, which is precisely why
        the first cut had to stand the byre off in the open.

        THE OWNER IS A BUNDLE, NOT A POINT, and getting that wrong is why the first version of this
        method never returned a seat. `_garden_fits` exempts the owner by matching `px == hx and
        py == hy`, so I mirrored it - but the garden runs DURING `farmsteads()`, when the house is
        its own entry in `placed`, while byres run after, when `placed` holds one merged HOMESTEAD
        BUNDLE per farm (house + yard + garden, e.g. 100 x 52 px centered off the house). Measured:
        zero entries at the house center, and the owner's own bundle refusing every wall seat. So
        the owner is identified by CONTAINMENT - the placed rect the house center falls inside - and
        the arm is allowed inside that bundle, which is what being an annex means.

        Inside the bundle it must still keep off the things it shares the yard with, so the
        appurtenance records are tested individually: its own house is exempt (the arm joins that
        wall), everything else is not. Those tests are AABB rather than the center-distance circles
        `_garden_fits` uses, because a circle round a 100 x 52 bundle reserves ground the bundle does
        not occupy, and this engine's standing rule is that gap verdicts read footprints."""
        hx, hy = float(h["x"]), float(h["y"])
        if self._in_blocked(cx, cy) or self._near_corridor(cx, cy):
            return False
        r = math.hypot(aw, ah) / 2
        for poly in self.field_polys:  # a byre stands on dry ground, off the paddies
            if point_in_poly(cx, cy, poly) or edge_dist(cx, cy, poly) < r:
                return False
        for px, py, pw, ph, *_ in self.placed:
            if abs(hx - px) <= pw / 2 + 0.5 and abs(hy - py) <= ph / 2 + 0.5:
                continue  # the owner's own homestead bundle - the arm belongs INSIDE it
            if abs(cx - px) < (aw + pw) / 2 + 2 and abs(cy - py) < (ah + ph) / 2 + 2:
                return False
        for _key in ("houses", "threshing_yards", "gardens", "farm_sheds", "byres"):
            for _o in self.M.get(_key) or []:
                if _key == "houses" and abs(float(_o["x"]) - hx) < 0.05 and abs(float(_o["y"]) - hy) < 0.05:
                    continue  # its OWN wall: the arm joins the house, it does not clear it
                if abs(cx - float(_o["x"])) < (aw + float(_o["w"])) / 2 + 2 and abs(cy - float(_o["y"])) < (ah + float(_o["h"])) / 2 + 2:
                    return False
        return True

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
        # THE WEALTH KEY WAS A NO-OP, AND THE REAL SORT WAS LONGITUDE (settlement-review x2, Kashikawa
        # and Sawada, 2026-08-18 round 2 - found independently on two maps). This read
        # `key=(-wealth, x, y)` and called it "buffalo owners = the wealthier", but EVERY plain house
        # in a scripted hamlet records `wealth: 1.0`, so the first term is constant and the ranking
        # collapses to smallest x - the cluster's WEST EDGE. Measured: Sawada's four oxen went to the
        # four westernmost houses, 230 ft of an 810 ft cluster with the whole SE lobe oxless, and by
        # the only wealth signal a reader can actually see - footprint - those owners rank 4th, 6th,
        # 17th and 18th of 19, with the three largest houses on the map owning no ox. Kashikawa's
        # first byre went to a west-edge outlier with ZERO households inside borrowing distance, and
        # the borrower floor added earlier that day could not reach it because the first byre never
        # enters the branch the floor lives in.
        #
        # FOOTPRINT IS THE WEALTH SIGNAL THE SHEET ACTUALLY CARRIES. `wealth` and house size were
        # decoupled at some point - the sizes here vary 1,040-1,688 sq ft while `wealth` stays 1.0 -
        # so the ranking was reading the dead one. Area is what a reader judges wealth by, and it is
        # what `farmhouse_sizes_vary` already makes meaningful. `wealth` stays first so a tier that
        # DOES set it still wins; area breaks the tie it leaves behind; position only breaks an exact
        # tie between two identical houses.
        ranked = sorted(houses, key=lambda h: (-h.get("wealth", 1.0), -(float(h["w"]) * float(h["h"])), h["x"], h["y"]))
        target = max(1, round(len(houses) * fraction))
        self.M["meta"]["byre_target"] = target  # the ASK, recorded so a silent shortfall is visible (byres_meet_their_target)
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

        def _borrowers(q: Mapping[str, Any]) -> int:
            """Households close enough to walk over and borrow this homestead's team."""
            return sum(1 for o in houses if o is not q and math.hypot(o["x"] - q["x"], o["y"] - q["y"]) <= _BORROW_REACH)

        while len(out) < target and _pool:
            if not out and not _courtyard:
                # THE FIRST SHARED BYRE NEEDS THE BORROWER FLOOR TOO (settlement-review, Kashikawa
                # 2026-08-18 round 2). The floor below lives inside `if out and ...`, so the FIRST
                # byre took `_pool[0]` unconditionally - and the floor had been written for exactly
                # that byre. Measured on the shipped sheet: Kashikawa's byre 0 stood 53 ft from one
                # farmhouse and 239 ft from the next, ONE household inside 200 ft against the other
                # three sheds' 3, 5 and 5, unmoved by the fix meant to cure it. Same shape on
                # Inashiro (2 within 200 ft) and Akagahara (1). A shared shed nobody can reach is
                # the private-stable read, on a map that declares the shared form.
                h = next((q for q in _pool if _borrowers(q)), _pool[0])
            elif out and not _courtyard:
                # SPREAD, THEN SHARE. Farthest-point alone minimizes the worst walk, which is the
                # right coverage objective - but with every house at wealth 1.0 the tie-break
                # collapses to pure distance, so it picks the most ISOLATED homestead and the shed
                # reads as that household's private one. That is the inverse of the doctrine: a byre
                # is shared precisely so a household owning no team can borrow from a neighbor
                # (settlements/homesteads.md), and the neighbor has to be there to borrow from.
                # So: take the spread score, then among the candidates within a quarter of the best
                # prefer the one with the most households in borrowing distance.
                _best = max(min(math.hypot(q["x"] - bx, q["y"] - by) for bx, by in out) for q in _pool)

                # A BORROWER IS A FLOOR, NOT ONLY A TIE-BREAK (settlement-review, Kashikawa
                # 2026-08-18). Preferring the best-connected owner AMONG the near-best spread was
                # already the fix for "spread alone picks the most isolated homestead" - but it can
                # only choose between the candidates the spread tier offers, and when every one of
                # them is isolated it still seats a shared shed where nobody can share it. Measured:
                # Kashikawa's first byre stands 53 ft from one farmhouse and 239 ft from the next,
                # with ONE household inside 200 ft while the other three sheds serve 3, 5 and 5. On a
                # map that rolled `detached_commons` that byre reads as a private stable, which is
                # the other form - so it also makes the knob illegible.
                #
                # So the spread tier WIDENS until it contains an owner somebody can actually borrow
                # from. Relaxing the tier costs a little coverage spread; seating a communal shed
                # out of everyone's reach costs the feature its whole meaning.
                _near = [q for q in _pool if min(math.hypot(q["x"] - bx, q["y"] - by) for bx, by in out) >= _best * 0.75]
                for _tier in (0.5, 0.25, 0.0):
                    if any(_borrowers(q) for q in _near):
                        break
                    _near = [q for q in _pool if min(math.hypot(q["x"] - bx, q["y"] - by) for bx, by in out) >= _best * _tier]
                h = max(_near, key=lambda q: (sum(1 for o in houses if o is not q and math.hypot(o["x"] - q["x"], o["y"] - q["y"]) <= _BORROW_REACH), q.get("wealth", 1.0), -q["x"], -q["y"]))
            else:
                h = _pool[0]
            _pool.remove(h)
            if _courtyard:  # the arm on its owner's wall; the spiral below is only the fallback
                _seat = self._courtyard_byre_seat(h, bw, bh)
                if _seat is not None:
                    _cx, _cy, _brot, _aw, _ah = _seat
                    self._draw_byre(_cx, _cy, bw, bh, _brot)
                    self.placed.append((_cx, _cy, _aw, _ah))
                    self.M["byres"].append({"x": round(_cx, 1), "y": round(_cy, 1), "w": bw, "h": bh, "rot": round(_brot, 1), "of": [round(h["x"], 1), round(h["y"], 1)]})
                    out.append((_cx, _cy))
                    continue
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
