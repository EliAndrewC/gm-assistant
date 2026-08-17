"""May a bundle STAND here? Every keep-out and clearance predicate, plus the two spatial caches that make asking cheap.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any, cast

from .._geom import FARMHOUSE_EAVE_GAP_FT, Pt, edge_dist, point_in_poly, poly_gap, rot_rect, seg_dist, segments_cross

if TYPE_CHECKING:
    from ..core import Settlement


class BundleFitMixin:
    def _field_adjacent(self: Settlement, x: float, y: float) -> bool:  # type: ignore[misc]
        """A farmhouse must stay near the farmland (within the gate's ADJ=165), so a nudge cannot drift it
        off into the urban core or the void."""
        return any(edge_dist(x, y, poly) <= 165 for poly in self.field_polys) if self.field_polys else True

    def _rect_corners(self: Settlement, rect: Any) -> list[Pt]:  # type: ignore[misc]
        cx, cy, w, h = rect
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]

    def _poly_bboxes(self: Settlement, polys: Any) -> list[Any]:  # type: ignore[misc]
        """Cached (minx, miny, maxx, maxy) per polygon in `polys`. Rebuilt only when the list GROWS - the
        block-poly list accretes each placed homestead during the solve, but individual polys are never
        mutated - so a length change is a sufficient staleness signal. Lets _rect_hits reject a far polygon
        with 4 comparisons instead of the O(vertices) corner/segment tests. See `_bbox_cache`."""
        cached = self._bbox_cache.get(id(polys))
        if cached is None or cached[0] != len(polys):
            boxes: list[Any] = []
            for poly in polys:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
            cached = (len(polys), boxes)
            self._bbox_cache[id(polys)] = cached
        return cast(list[Any], cached[1])

    def _rect_hits(self: Settlement, rect: Any, polys: Any) -> bool:  # type: ignore[misc]
        """Whether an axis-aligned rect overlaps any polygon in `polys` (corner-in, vertex-in, or edge-cross).
        Bbox pre-filters carry the cost: a polygon whose bbox is disjoint from the rect is skipped outright,
        and within an overlapping polygon each EDGE is bbox-tested before the crossing check (this matters for
        the one huge field-envelope polygon, where the rect only ever meets a couple of its many edges). (A
        spatial grid was tried on top of this and measured NOISE-identical: the bbox reject already makes the
        far-poly scan cheap, and the residual cost is the genuine near-overlap math on polys a grid returns
        anyway - so it was not worth the caching complexity.)"""
        cx, cy, w, h = rect
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        gc = self._rect_corners(rect)
        for poly, (px0, py0, px1, py1) in zip(polys, self._poly_bboxes(polys), strict=False):
            if px1 < rx0 or px0 > rx1 or py1 < ry0 or py0 > ry1:
                continue  # bboxes disjoint -> cannot overlap
            n = len(poly)
            if any(point_in_poly(px, py, poly) for px, py in gc) or any(rx0 <= vx <= rx1 and ry0 <= vy <= ry1 and point_in_poly(vx, vy, gc) for vx, vy in poly):
                return True
            for k in range(n):  # edge-cross, each edge bbox-gated against the rect
                a, b = poly[k], poly[(k + 1) % n]
                if min(a[0], b[0]) > rx1 or max(a[0], b[0]) < rx0 or min(a[1], b[1]) > ry1 or max(a[1], b[1]) < ry0:
                    continue
                if any(segments_cross(gc[e], gc[(e + 1) % 4], a, b) for e in range(4)):
                    return True
        return False

    def _water_obstacles(self: Settlement) -> list[Any]:  # type: ignore[misc]
        """Cached (poly, keep-out half-width, bbox) for every irrigation LINE a solid bundle rect must avoid -
        feeder channels, in-field/drain ditches, streams. Rebuilt only when one of the three source lists
        changes length (all are laid before the homestead solve, then static). Lets _rect_on_water skip a
        whole course - and then an individual segment - whose neighborhood the rect cannot reach."""
        chans = self.M.get("channels", [])
        ditches = self.M.get("field_ditches", [])
        streams = self.M.get("streams", [])
        key = (len(chans), len(ditches), len(streams))
        if self._water_obs_cache is None or self._water_obs_cache[0] != key:
            obs: list[Any] = []
            for lst, base in ((chans, 2.5), (ditches, 7.0), (streams, 9.0)):
                for f in lst:
                    poly = f["poly"]
                    if len(poly) < 2:
                        continue
                    hw = f.get("w", base) / 2 + 5
                    xs = [p[0] for p in poly]
                    ys = [p[1] for p in poly]
                    obs.append((poly, hw, (min(xs), min(ys), max(xs), max(ys))))
            self._water_obs_cache = (key, obs)
        return cast(list[Any], self._water_obs_cache[1])

    def _rect_on_water(self: Settlement, rect: Any) -> bool:  # type: ignore[misc]
        """Whether a SOLID bundle rect (house/yard/garden/shed) lands on an irrigation LINE - a feeder
        channel, an in-field/drain ditch, or a stream. These are dry-ground structures, so a garden or
        yard in a running ditch is wrong (gardens_clear_of_channels), and this keeps the homestead solver
        off the drain outfall that threads the village margin. A hair wider than the check's keep-out so
        the solver leaves room the check then confirms. The GROVE is exempt (it may hug a bund). Bbox
        pre-filters (per course, then per segment) skip the seg_dist / crossing math for anything far off."""
        cx, cy, w, h = rect
        gc = self._rect_corners(rect)
        pts = gc + [(cx, cy)]
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        for poly, hw, (px0, py0, px1, py1) in self._water_obstacles():
            if px1 + hw < rx0 or px0 - hw > rx1 or py1 + hw < ry0 or py0 - hw > ry1:
                continue  # the whole course is out of reach
            for k in range(len(poly) - 1):
                a, b = poly[k], poly[k + 1]
                if min(a[0], b[0]) - hw > rx1 or max(a[0], b[0]) + hw < rx0 or min(a[1], b[1]) - hw > ry1 or max(a[1], b[1]) + hw < ry0:
                    continue  # this segment is out of reach
                if any(seg_dist(px, py, a, b) < hw for px, py in pts):
                    return True
                if any(segments_cross(a, b, gc[e], gc[(e + 1) % 4]) for e in range(4)):
                    return True
        return False

    def _rect_blocked(self: Settlement, rect: Any, fields: bool) -> bool:  # type: ignore[misc]
        """Whether a bundle sub-rect lands on forbidden ground: no-build blocks, lanes, hill/pond ellipses,
        irrigation lines, and (only when `fields=True`, i.e. the SOLID house/yard/garden) the flooded
        paddies. The GROVE (fields=False) may HUG a paddy bund, so it is tested against everything BUT the
        fields and the water lines."""
        if self._rect_hits(rect, self.block_polys):
            return True
        if fields and self._rect_hits(rect, self.field_polys):
            return True
        if fields and self._rect_on_water(rect):
            return True
        if fields and not self._hard_clear(rect[0], rect[1], rect[2], rect[3]):
            return True  # HARD ground read from the manifest (crop plots + a field's own ditches)
        cx, cy, w, h = rect
        for px, py in self._rect_corners(rect) + [(cx, cy)]:
            for ex, ey, rx, ry in self.ellipses:
                if rx > 0 and ry > 0 and ((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1:
                    return True
        return self._near_corridor(cx, cy)

    def _house_on_a_tread(self: Settlement, rect: Any) -> bool:  # type: ignore[misc]
        """Would this bundle's house, AS DRAWN, put a corner on a way's drawn tread?

        THE HALF OF THE FOOTPRINT DEBT THE BUNDLE PATH NEVER PAID (feature 121). `_fits` gained the
        footprint-vs-tread test on 2026-08-12, but a homestead BUNDLE is seated by `_bundle_fits`
        from its own geometry and never goes through `_fits` at all - so the only thing standing
        between a drawn steading and the lane was `_rect_blocked`'s closing `_near_corridor(cx, cy)`,
        a bare CENTRE test, plus enough corridor width to cover the difference by margin. Measured
        at a 32 px clearance: 10 of 24 cohort maps put a farmhouse corner on a lane.

        WHAT ACTUALLY DIVERGES IS THE RAKE, and only the rake. The bundle's house rect matches the
        drawn record's position and size exactly (four decimal places, measured across
        pool/hamlets/inashiro.json); `_house_rot` is what the renderer adds afterward, and an
        axis-aligned clearance ignores up to 2.56 px of corner bulge. Since the rake is
        position-seeded it is knowable at seat time, so this is an exact test and not an estimate.

        SURFACE, NOT CLEARANCE (this skill's dev/placement.md, and specs/121's contracts/placement.md
        C4). Only the drawn tread is tested this way. The soft corridor keeps its centre test above,
        deliberately: footprint-testing a clearance was tried once and reverted, because a clearance
        is slack a footprint routinely overhangs, and tightening it cost Nagahara a well and pushed
        Hoshizora's punishment ground off its street.

        THE HOUSE ONLY, and that is a decision rather than an oversight. The yard, garden and grove
        are drawn axis-aligned, so for them the rect already IS the drawn footprint and the corridor
        test they get is honest. Extending a tread test to them would be a new rule about where a
        threshing yard may lie - which no check currently makes and which would re-pack every
        nucleated map to enforce - so it is deliberately out of scope here."""
        cx, cy, w, h = rect
        return self._on_a_tread(cx, cy, w, h, rot=self._house_rot(cx, cy))

    def _house_too_near_a_neighbor(self: Settlement, rect: Any) -> bool:  # type: ignore[misc]
        """Would this house stand so close to one already placed that the two stop reading as two?

        TWO THATCHED ROOFS MUST SHED SEPARATELY (2026-08-17). A minka's kayabuki thatch is pitched
        45 deg or steeper, so each roof throws its own drip line; two set a couple of feet apart
        pool their runoff against each other's walls. `FARMHOUSE_EAVE_GAP_FT` carries the number and
        the grounding, and the gate reads the SAME constant (`farmhouses_shed_separately`).

        WHY IT WAS NEEDED. House-to-house separation had no rule at all - `no_structure_overlaps`
        only fires at zero, and bundles are kept apart by their whole-bundle BBOX, which knows
        nothing about either house's rake. So a re-pack that flipped one house's rake from -4.0 to
        +4.4 deg left a Mizuguchi pair 2.0 ft apart at the corners: two pixels between two dark roof
        strokes at 1 px = 1 ft, merging into one long building at fit zoom. Caught by
        settlement-review, not by the gate, because nothing measured it.

        THE PLACER IS STRICTER THAN THE CHECK BY A HAIR, the same convention `_sun_corridor_ok`
        states and for the same reason: the placer measures the bundle rects it is about to commit
        while the gate measures the records `farmsteads()` finally draws, and the two differ by
        fractions of a pixel. Two feet of margin costs nothing in packing and puts the disagreement
        where it cannot bite.

        GAP VERDICT family: real rotated corners via `poly_gap`, never centers, never a
        circumscribed radius (dev/placement.md, "CENTER vs FOOTPRINT"). The center-distance test in
        front of it is a PREFILTER - it over-states both extents, so it can only admit a pair the
        exact test then rejects."""
        lim = self.px(FARMHOUSE_EAVE_GAP_FT + 2.0)
        cx, cy, w, h = rect
        quad = rot_rect(cx, cy, w, h, self._house_rot(cx, cy))
        reach = lim + math.hypot(w, h) / 2
        for rec in self.M.get("houses", []):
            if rec.get("kind") == "abandoned":
                continue  # a derelict has no roof left to shed
            ow, oh = rec["w"], rec["h"]
            if math.hypot(cx - rec["x"], cy - rec["y"]) > reach + math.hypot(ow, oh) / 2:
                continue  # prefilter: prunes, never decides
            if poly_gap(quad, rot_rect(rec["x"], rec["y"], ow, oh, rec.get("rot", 0.0))) < lim:
                return True
        return False

    def _bundle_fits(self: Settlement, geom: Any, grove_off_field: bool = True) -> bool:  # type: ignore[misc]
        """A homestead bundle fits where it is in-bounds, its SOLID parts (house/yard/garden) clear every
        paddy/block/lane/ellipse, its GROVE clears all of those (and may abut - but not enter - a paddy when
        `grove_off_field`, the test used while shoving the grove up against the bund), and the whole bbox
        does not overlap another already-placed homestead (a sliver of tolerance lets adjacent groves ABUT
        into one windbreak). Split into a side-INDEPENDENT half (house/yard/kura/grove/sun - identical for
        every garden side at a position) and a side-DEPENDENT half (the garden bed + the bbox it grows), so
        the nucleated placer can test the common half ONCE across all four sides (see `_fits_any_side`). The
        conjunction is order-independent, so the result is unchanged from the old single test."""
        return self._bundle_common_fits(geom, grove_off_field) and self._bundle_side_fits(geom)

    def _sun_corridor_ok(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """Does this homestead leave every threshing yard - its own and the neighbours' - its sun?

        THE RULE (GM 2026-08-13, researched in research/homesteads.md, "The threshing yard's sun"):
        rice is dried on the niwa, so a yard needs clear ground to its SOUTH. A thatched roof is
        pitched 45 deg or steeper, which puts our 46x28 ft minka's ridge ~20 ft up; at 38N in the
        10th month that throws 21 ft of shadow at noon and 39 ft by 9am. So a farmhouse standing
        within `sun_corridor` feet south of a yard takes the drying day away from it.

        OPT-IN, and deliberately so. `s.sun_corridor(39)` turns it on; it is OFF by default, because
        turning it on re-packs every nucleated map in the pool and the GM's decision (2026-08-13) is
        that the hand-authored maps keep their present packing and inherit the fix as each is
        converted to a generator script. The engine holds the rule; the scripted path asks for it.

        Both directions are tested, because a bundle is placed among bundles already standing: this
        house may not shade a yard already placed, and this yard may not be shaded by a house already
        standing. Testing only one direction leaves the defect to whichever homestead is seated
        second."""
        ft = getattr(self, "_sun_corridor_ft", 0.0)
        if not ft:
            return True
        # THE PLACER IS STRICTER THAN THE CHECK BY A HAIR, on purpose. It measures the bundle rects
        # it is about to commit; `yards_unshaded_by_neighbors` measures the yard record that
        # `farmsteads()` finally draws, and the two differ by fractions of a pixel. A seat at 39.0
        # ft therefore passed here and failed there on 2 of 36 cohort maps. Two feet of margin costs
        # nothing in packing and puts the disagreement where it cannot bite.
        reach = self.px(ft + 2.0)
        side = self.px(2.0)  # ...and the same margin ACROSS the corridor: the lateral overlap test is
        # `|dx| < (yard_w + house_w)/2`, and a seat that missed the placer's version by 0.35 px failed
        # the check's on a held-out cohort map. Both axes, or the disagreement just moves.
        hx, hy, hw, hh = geom["house"]
        yx, yy, yw, yh = geom["yard"]
        # THE NEIGHBOURS' YARDS ARE READ OFF THE PLACED BUNDLES, not off `M["threshing_yards"]`.
        # Yards are not drawn until `farmsteads()` flushes, long after every house is seated, so the
        # manifest list is EMPTY while placement runs - testing it caught nothing in the direction
        # that matters (a new house shading a yard already standing), and the first version of this
        # rule cleared only about half the shaded yards because of it. Each bundle's record carries
        # its own `geom`, so the yard is there to be read.
        for b in self.M.get("houses", []):
            g = b.get("geom")
            ty = g["yard"] if g else None
            if ty is None:
                continue
            if abs(ty[0] - hx) < (ty[2] + hw) / 2 + side and 0 < (hy - hh / 2) - (ty[1] + ty[3] / 2) < reach:
                return False
        # ...and this YARD must not sit in a standing house's shadow
        return not any(abs(b["x"] - yx) < (b["w"] + yw) / 2 + side and 0 < (b["y"] - b["h"] / 2) - (yy + yh / 2) < reach for b in self.M.get("houses", []))

    def sun_corridor(self: Settlement, feet: float) -> None:  # type: ignore[misc]
        """Ask the placer to keep `feet` of open ground SOUTH of every threshing yard (see
        `_sun_corridor_ok`). Off by default; a generator opts in."""
        self._sun_corridor_ft = float(feet)

    def _bundle_common_fits(self: Settlement, geom: Any, grove_off_field: bool = True) -> bool:  # type: ignore[misc]
        """The fit checks that do NOT depend on which side the garden is on - the house, the south threshing
        yard, a north kura, the windward grove (dispersed only), and the yard sun-corridor. Same for every
        garden side at a given position, so it is tested once per position."""
        if self._rect_blocked(geom["house"], fields=True) or self._rect_blocked(geom["yard"], fields=True) or ("shed" in geom and self._rect_blocked(geom["shed"], fields=True)):
            return False
        if self._house_on_a_tread(geom["house"]):
            return False
        if self._house_too_near_a_neighbor(geom["house"]):
            return False
        if "grove_n" in geom and any(self._rect_blocked(geom[k], fields=grove_off_field) for k in ("grove_n", "grove_w")):
            return False
        if not self._sun_corridor_ok(geom):
            return False
        return not self._yard_sun_conflict(geom)

    def _bundle_side_fits(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """The fit checks that DO move with the garden side (via the bundle bbox): in-bounds, inside any
        bounding ring, the garden bed(s) clear of every paddy/block/lane, and the whole bbox clear of every
        placed homestead."""
        cx, cy, W, H = geom["bbox"]
        if cx - W / 2 < 6 or cx + W / 2 > self.W - 6 or cy - H / 2 < 6 or cy + H / 2 > self.H - 6:
            return False
        if self.bound and any(not point_in_poly(vx, vy, self.bound) for vx, vy in self._rect_corners(geom["bbox"])):
            return False
        if any(self._rect_blocked(g, fields=True) for g in geom["gardens"]):
            return False
        return all(not (abs(cx - px) < (W + pw) / 2 + 2 and abs(cy - py) < (H + ph) / 2 + 2) for px, py, pw, ph, *_ in self.placed)

    def _yard_sun_conflict(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """A threshing yard dries rice in the southern sun, so no grove may sit in the ~22px strip directly
        SOUTH of any yard. Tests the candidate's grove against every placed yard's sun-corridor and the
        candidate's yard against every placed grove, so packing never stacks a windbreak over a neighbor's
        drying ground."""

        def shades(grove: Any, yard: Any) -> bool:
            cyx, cyy = yard[0], yard[1] + yard[3] / 2 + 11
            return cast(bool, abs(grove[0] - cyx) < (grove[2] + yard[2]) / 2 and abs(grove[1] - cyy) < (grove[3] + 22) / 2)

        new_groves = (geom["grove_n"], geom["grove_w"]) if "grove_n" in geom else ()
        new_yard = geom["yard"]
        for rec in self.M["houses"]:
            g = rec.get("geom")
            if not g:
                continue
            if any(shades(gv, g["yard"]) for gv in new_groves):
                return True
            other_groves = (g["grove_n"], g["grove_w"]) if "grove_n" in g else ()
            if any(shades(gv, new_yard) for gv in other_groves):
                return True
        return False

    def _garden_shaded(self: Settlement, grect: Any) -> bool:  # type: ignore[misc]
        """A dooryard garden is SHADED when a farmhouse stands close to its SOUTH (the sun comes from the
        south), so a garden sandwiched with a neighbor's house just below it gets no light. Tested against
        every placed house - the nucleated placer prefers a side with open sky to the south."""
        gx, gy, gw, gh = grect
        for rec in self.M["houses"]:
            hx, hy, hw, hh = rec["x"], rec["y"], rec["w"], rec["h"]
            if hy > gy + gh / 2 - 3 and abs(hx - gx) < (hw + gw) / 2 and (hy - hh / 2) - (gy + gh / 2) < gh + 4:
                return True
        return False

    def _fits_any_side(self: Settlement, cx: float, cy: float, hw: float, hh: float, shed: bool = False) -> bool:  # type: ignore[misc]
        # The house/yard/kura/sun checks are the same for every garden side, so test that common half ONCE -
        # if it fails, no side can fit - then test only each side's garden (+ the bbox it grows). Identical
        # result to any(_bundle_fits(...) for side), but far fewer collision tests on the failing steps that
        # dominate the pack. Safe because the fit path is RNG-free: building fewer geoms cannot shift placement.
        g0 = self._bundle_geom(cx, cy, hw, hh, self._NUC_SIDES[0], shed)
        if not self._bundle_common_fits(g0):
            return False
        for i, side in enumerate(self._NUC_SIDES):
            geom = g0 if i == 0 else self._bundle_geom(cx, cy, hw, hh, side, shed)
            if self._bundle_side_fits(geom):
                return True
        return False
