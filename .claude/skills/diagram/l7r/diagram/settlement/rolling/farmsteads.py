"""The deferred farmstead flush: what actually gets DRAWN, and in what order. This is the module the DRAW ORDER contract is about.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any, cast

from .._geom import Indexed, point_in_poly
from .._knobs import CITY_TIER_SCALES

if TYPE_CHECKING:
    from ..core import Settlement


class FarmsteadFlushMixin:
    def farmsteads(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every farmstead. The to-scale tiers (villages/hamlets/towns) draw the reserved homestead
        BUNDLES; cities use the shipped house-first path. Call LAST in the gen so every obstacle is known. Returns the farmhouse count."""
        with self.rng_scope("farmsteads"):
            # ONE scope for the whole rural flush: yards, gardens, groves and kura sides are one
            # phase, and splitting them would only make a change to one perturb the others.
            if self._toscale():
                return self._farmsteads_bundle()
            return self._farmsteads_legacy()

    def _farmsteads_bundle(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every reserved homestead bundle: grove (back) -> yard -> garden -> house (on top). The hard
        work (fitting each whole bundle without overlap) already happened in try_place, one at a time, so
        this pass is pure drawing. Abandoned ruins (no bundle) draw as a lone house. Call LAST. Returns the
        farmhouse count.
        Two sub-passes so the garden EAST-shade nudge can see every neighbor's grove: (1) draw all per-house
        GROVES (the back layer), (2) after a south-nudge relaxation, draw the yards/gardens/houses on top."""
        survivors: list[Any] = []
        bundled: list[Any] = []
        arms: list[tuple[float, float, float, float, tuple[int, int]]] = []
        for rec in self._pending_farmsteads:
            geom = rec.get("geom")
            if geom is None:  # abandoned ruin / dispersed headman: lone house
                self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"])
                survivors.append(rec)
                continue
            for key, face in (("grove_n", (0, -1)), ("grove_w", (-1, 0))):
                if key not in geom:  # nucleated bundle: no per-house grove
                    continue
                cx, cy, w, h = geom[key]
                arms.append((cx, cy, w, h, face))
                self.M["groves"].append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": 0, "of": [rec["x"], rec["y"]], "face": list(face)})
                self.grove_rects.append((cx, cy, w, h))
            bundled.append(rec)
            survivors.append(rec)
        self._relax_gardens_south(bundled)  # nudge east-shaded gardens a little S (all groves now known)
        for rec in bundled:
            geom = rec["geom"]
            self._attach_yard(rec["x"], rec["y"], geom["yard"])
            self._attach_garden(rec["x"], rec["y"], geom["gardens"])
            self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"], shed=rec["shed"], shed_side=rec.get("shed_side", "W"))
        # The yashikirin arms DRAW LAST, after every house/shed of this pass is down (GM 2026-07-25).
        # They used to draw first, as a back layer the house painted over - which hid the overlap
        # rather than preventing it, and left crowns geometrically under roofs. Drawing them after
        # means _draw_grove's keep-out sees the houses, so the belt THINS off the walls instead: no
        # tree is drawn over a building anywhere on the map, by one rule rather than by z-order.
        # (The arm rects themselves are recorded above, before _relax_gardens_south, which needs them.)
        for cx, cy, w, h, face in arms:
            self._draw_grove(cx, cy, w, h, face)
        self.M["houses"] = [h for h in self.M["houses"] if h.get("on_dike")] + survivors  # dike-top houses (dike_top_houses) are not pending farmsteads - keep them
        return len(survivors)

    def _east_trees(self: Settlement, gx1: float, own: Any) -> list[Any]:  # type: ignore[misc]
        """The y-intervals (y0, y1) of every per-house grove arm standing hard against a garden's EAST - west
        edge within a shade band east of the garden's east edge `gx1`. `own` is the garden's OWN grove arms
        (which sit N/W, never east), excluded. The garden's x is fixed as it shifts S, so this set is stable."""
        band = 22 * self.bscale
        out: list[Any] = []
        for tx, ty, tw, th in self.grove_rects:
            if any(abs(tx - ox) < 1.5 and abs(ty - oy) < 1.5 for ox, oy, _, _ in own):
                continue  # skip the garden's own grove arms
            west = tx - tw / 2
            if gx1 - 2 <= west < gx1 + band:
                out.append((ty - th / 2, ty + th / 2))
        return out

    def _garden_beds_clear(self: Settlement, beds: Any, others: Any) -> bool:  # type: ignore[misc]
        """Whether a set of shifted garden beds land on clear ground: each bed off blocks/fields/water/lanes
        (`_rect_blocked`), and clear of every ACTUAL footprint in `others` (neighbors' houses/yards/gardens/
        groves + the garden's own house + yard). Tests real footprints, NOT the loose reserved bundle bboxes -
        a garden may shift into a neighbor's empty bbox margin, it just may not touch a drawn structure."""

        def hit(a: Any, b: Any) -> bool:
            return cast(bool, abs(a[0] - b[0]) < (a[2] + b[2]) / 2 and abs(a[1] - b[1]) < (a[3] + b[3]) / 2)

        for bed in beds:
            if self._rect_blocked(bed, fields=True):
                return False
            if any(hit(bed, r) for r in others):
                return False
        return True

    def _relax_gardens_south(self: Settlement, recs: Any) -> None:  # type: ignore[misc]
        """OPTION (villages where each house has its own windward grove and the garden goes on the E/lee side):
        once every yashikirin is drawn, a garden left with a NEIGHBOR'S grove hard against its EAST loses the
        morning sun. Where there is open ground, nudge that garden a little SOUTH so the tree falls to its NE
        and the eastern sky opens - the GM's 'move it a bit south' remedy. Best-effort: a garden boxed in to the
        south stays put (gardens_unshaded_from_east flags only the AVOIDABLE ones). See settlements.md 'gardens'."""
        step = 4 * self.bscale

        def footprints(exclude: int) -> list[Any]:
            """Every homestead's real house/yard/garden/grove rects, minus the rec at index `exclude`."""
            out: list[Any] = []
            for j, r in enumerate(recs):
                if j == exclude:
                    continue
                g = r["geom"]
                out.append(tuple(g["house"]))
                out.append(tuple(g["yard"]))
                out += [tuple(b) for b in g.get("gardens", [])]
                out += [tuple(g[k]) for k in ("grove_n", "grove_w") if k in g]
            return out

        def overlaps(a: Any, b: Any) -> bool:
            return cast(bool, a[0] < b[1] and b[0] < a[1])

        for i, rec in enumerate(recs):
            geom = rec["geom"]
            beds = geom.get("gardens")
            if not beds:
                continue
            own = [geom[k] for k in ("grove_n", "grove_w") if k in geom]
            gx1 = max(b[0] + b[2] / 2 for b in beds)
            gcy = sum(b[1] for b in beds) / len(beds)
            gh = max(b[1] + b[3] / 2 for b in beds) - min(b[1] - b[3] / 2 for b in beds)
            trees = self._east_trees(gx1, own)
            if not any(overlaps((gcy - gh / 2, gcy + gh / 2), t) for t in trees):
                continue  # not currently east-shaded - nothing to do
            maxshift = gh + rec["h"] + 6  # 'a little' - stays a dooryard garden near the house
            others = footprints(i) + [tuple(geom["house"]), tuple(geom["yard"])]
            dy = step
            while dy <= maxshift:
                lane = (gcy + dy - gh / 2, gcy + dy + gh / 2)  # clear of EVERY east tree (a small shift can slip INTO a taller arm)
                if not any(overlaps(lane, t) for t in trees):
                    shifted = [(b[0], b[1] + dy, b[2], b[3]) for b in beds]
                    if self._garden_beds_clear(shifted, others):
                        geom["gardens"] = shifted
                        break
                dy += step

    def _kura_side(self: Settlement, rec: dict[str, Any], w: float, h: float) -> str:  # type: ignore[misc]
        """Which wall a LEGACY farmstead's kura stands against - "W" (the dispersed-farm default in
        `house()`) or "N" (the shaded back wall a nucleated farm uses).

        WHY THIS IS DECIDED AT DRAW TIME (Minami 2026-08-08, a farm shed drawn on a neighbor's
        garden). A legacy farmhouse reserves only its own base rect, while the west kura is drawn
        reaching 0.30 x the house's width PAST that rect - the standing "placement tests a
        different footprint than the one drawn" debt (dev-loop CLAUDE.md, CENTER vs FOOTPRINT item
        3). The nucleated bundle answers it by RESERVING the kura's ground; the legacy path cannot,
        because it places one house at a time against ground whose gardens and yards are not drawn
        yet. But by the flush every appurtenance IS drawn, so the side can simply be CHOSEN here,
        with no placement change and so no reflow of the belt. If both walls are fouled the west
        stands and the overlap matrix reports it - the engine does not get to hide a homestead with
        no room for its own storehouse."""
        th = math.radians(rec.get("rot", 0))
        ca, sa = math.cos(th), math.sin(th)
        # the two kura footprints, in the house's local frame - MUST match house()'s _sox/_soy/_ssw/_ssh
        sides = {"W": (-0.64 * w, 0.0, 0.32 * w, 0.56 * h), "N": (0.0, -0.60 * h, 0.46 * w, 0.30 * h)}
        # every DRAWN appurtenance of every farmstead, this one's included: the check does not care
        # whose garden a kura laps, and a house's own bed is as much a collision as a neighbor's
        near = [o for k in ("gardens", "threshing_yards", "farm_sheds", "byres") for o in (self.M.get(k) or []) if abs(o["x"] - rec["x"]) < 3 * w and abs(o["y"] - rec["y"]) < 3 * w]
        near += [o for o in self.M.get("houses") or [] if o is not rec and abs(o["x"] - rec["x"]) < 3 * w and abs(o["y"] - rec["y"]) < 3 * w]
        for side, (ox, oy, kw, kh) in sides.items():
            kx, ky = rec["x"] + ox * ca - oy * sa, rec["y"] + ox * sa + oy * ca
            khw, khh = (abs(kw * ca) + abs(kh * sa)) / 2, (abs(kw * sa) + abs(kh * ca)) / 2
            if not any(abs(kx - o["x"]) < khw + o["w"] / 2 and abs(ky - o["y"]) < khh + o["h"] / 2 for o in near):
                return side
        return "W"

    def _farmsteads_legacy(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every deferred farmhouse WITH its threshing/drying YARD (south/front apron) AND its dooryard
        kitchen GARDEN (a sunny side, preferring the east) - both were universal to a farmstead, so every
        farmhouse has one of each. Find spots for both; if they don't fit, nudge the house a little; draw
        garden + yard then the house so the house wins any abutment. A house that cannot host BOTH anywhere
        nearby is dropped (rare) so the 100% invariants hold. Call LAST in the gen. Returns the count."""
        survivors: list[Any] = []
        for rec in self._pending_farmsteads:
            spot = self._solve_homestead(rec)  # shift the homestead to fit yard+garden+grove-room
            if spot is None:
                fp = (rec["x"], rec["y"], rec["w"], rec["h"])
                # ANNOTATED `list[Any]` to agree with core.py's declaring assignment. Feature 118
                # split this method and `_solve_homestead` (which already carried the annotation)
                # into different mixins, so each class now declares `placed` independently and mypy
                # inferred `Indexed` here against core's `list[Any]`. Annotation only - no runtime
                # effect, and Indexed IS a list subclass, so the two were never really in conflict.
                self.placed: list[Any] = Indexed(p for p in self.placed if p != fp)  # drop the un-appurtenanced farmhouse (rare); Indexed for the same reason as the lift above
                continue
            yard_spot, garden_spot = spot
            self._attach_garden(rec["x"], rec["y"], [garden_spot])  # legacy farms keep ONE bed (multi-bed split is nucleated)
            self._attach_yard(rec["x"], rec["y"], yard_spot)
            survivors.append(rec)
        # SECOND PASS FOR THE HOUSES THEMSELVES, so every yard and garden on the belt is drawn and
        # recorded before the first roof goes down (2026-08-08). It buys two things and costs no
        # geometry - `house()` only DRAWS, the footprint was reserved back in `_try_place_legacy`:
        # `_kura_side` can see the neighbors it has to dodge (in one pass it saw only the farmsteads
        # flushed before it, and Minami's kura duly landed on a garden drawn two houses later), and
        # a roof now paints over EVERY garden it abuts rather than only the ones already down -
        # which is the "draw garden + yard then the house so the house wins any abutment" rule this
        # loop always intended, applied across the belt instead of per homestead.
        for rec in survivors:
            # DRAW the house at its WEALTH size - a modest +/-~10% on the rendered glyph only. The manifest keeps
            # w,h at the BASE footprint (what the reservation, the yard/garden, and the overlap checks use, so
            # the variation never causes a drop or a shed/garden clash); the `wealth` factor records the render
            # scale and the grove (below) scales with it.
            wf = rec["wealth"]
            side = self._kura_side(rec, rec["w"] * wf, rec["h"] * wf) if rec["shed"] else "W"
            if rec["shed"]:
                rec["shed_side"] = side
            self.house(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf, rec["kind"], rec["rot"], shed=rec["shed"], shed_side=side)
        self.M["houses"] = [h for h in self.M["houses"] if h.get("on_dike")] + survivors  # dike-top houses (dike_top_houses) are not pending farmsteads - keep them
        # SECOND PASS - the windward homestead groves (yashikirin). Run AFTER every farmhouse + its yard +
        # garden is placed, so a grove (an optional flourish) can NEVER block a neighbor's MANDATORY yard/
        # garden and drop that house. Near-universal (meta.grove_prevalence), but OFF for a farm inside a
        # CITY wall (an intramural plot is not an isolated farmstead - it is sheltered by the urban fabric
        # and sits on land too precious for a tree belt; meta(inwall_groves=True) to override). A farm whose
        # windward side is boxed in goes without. Returns the farmhouse count.
        meta = self.M["meta"]
        wall: Any = self.M.get("wall")
        inwall_off = bool(wall) and meta.get("scale") in CITY_TIER_SCALES and not meta.get("inwall_groves", False)
        for rec in survivors:
            if inwall_off and point_in_poly(rec["x"], rec["y"], wall):
                continue
            if self._grove_candidate(rec["x"], rec["y"]):
                wf = rec["wealth"]  # a wealthier farm's bigger house carries a bigger grove
                arms = self._find_grove_arms(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf)
                if arms:
                    self._attach_grove(rec["x"], rec["y"], arms)
        return len(survivors)
