"""The wellhead glyph, and the four passes that put wells on a map.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import math
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from .._geom import (
    Indexed,
    Pt,
    point_in_poly,
)

if TYPE_CHECKING:
    from ..core import Settlement


class WellsMixin:
    def _well_vr(self: Settlement) -> float:  # type: ignore[misc]
        """The well-house ROOF square's half-size - a wellhead's full DRAWN extent (see well()).
        In FEET at this map's ftpx on a to-scale tier (a ~24.8 ft well-house); on the legacy tiers
        it scales with the urban glyph grain. Factored out of well() because PLACEMENT has to
        predict the glyph before it is drawn: the stable yard's dig-your-own-well fallback needs
        the head's size to keep it off a hitching rail or a neighboring yard's troughs
        (wellhead_quad / wells_troughs_rails_clear_of_each_other)."""
        return self.px(12.376) if self._toscale() else 11.9 * self.bscale

    def well(self: Settlement, x: float, y: float, r: float = 8, shrine: bool = False, private: bool = False, kind: str | None = None) -> None:  # type: ignore[misc]
        """A public NEIGHBORHOOD WELL (井戸) - a stone curb under an open-sided well-house roof, the
        shared draw-point and social hub (the idobata, where a tenement block's gossip happened). One
        served a courtyard / cluster of ~10-20 households. SMALLER than a house and sits in a block
        INTERIOR off the lanes. Records M['wells'] and blocks placement so the quarter's houses flow
        around it - place BEFORE the quarter's pack. The underground end of a city's water system
        (aqueducts, cisterns, rain barrels feeding the shaft) stays off the map; only the head shows."""
        # THE WELL IS A LOCATION MARKER, NOT A TO-SCALE FOOTPRINT (GM ruling 2026-07-21). A real stone
        # well curb is ~3-4 ft - sub-glyph at every map scale - so the wellhead denotes the well's
        # TO-SCALE LOCATION relative to its surroundings with a legible marker whose own pixels are NOT
        # claimed to be to scale. That places wells under the STROKE CONVENTION (same doctrine as the
        # linework floor, see SKILL.md "to scale"), not in violation of the everything-is-to-scale rule.
        # The marker SCALES WITH THE MAP GRAIN (bscale), exactly as the buildings do, so it keeps a
        # consistent ~0.55x a dwelling at every scale - fixed pixels would make it look right in the
        # dense city but far too small beside a village/town's larger houses. It stays SMALLER than a
        # house regardless of the larger COURTYARD footprint reserved for placement.
        vroof = self._well_vr()
        vcurb = self.px(9.36) if self._toscale() else 9.0 * self.bscale
        self.add(
            f'<rect x="{x - vroof:.1f}" y="{y - vroof:.1f}" width="{2 * vroof:.1f}" height="{2 * vroof:.1f}" rx="1.5" fill="#C7B084" stroke="#6B5836" stroke-width="1.1" opacity="0.55"/>'
        )  # the well-house roof, light so the curb reads through
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb:.1f}" fill="#9AA1A4" stroke="#43403A" stroke-width="1.1"/>')  # stone curb
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb * 0.47:.1f}" fill="#2E4C58"/>')  # dark water in the shaft
        _wrec: dict[str, Any] = {"x": round(x, 1), "y": round(y, 1), "r": r, "vr": round(vroof, 1), "shrine": shrine, "private": private}
        if kind is not None:
            # a josui-ido CISTERN-WELL taps the buried aqueduct main (research 021 item 4);
            # recorded only when declared, so every existing manifest stays byte-identical
            _wrec["kind"] = kind
        self.M["wells"].append(_wrec)  # shrine=True marks an ablution (temizu) well - wells_sized_to_population counts only the communal household draw-wells
        # reserve only a TIGHT courtyard around the small wellhead (not a whole house-plot): houses ring
        # it closely, as in a real tenement court, so a well costs roughly its own footprint, not several
        # dwellings. (`r` stays the recorded clearance radius the checks use; the reserved block is small.)
        self.placed.append((x, y, 2 * vroof, 2 * vroof))
        bm = 8
        self.block_polys.append([(x - vroof - bm, y - vroof - bm), (x + vroof + bm, y - vroof - bm), (x + vroof + bm, y + vroof + bm), (x - vroof - bm, y + vroof + bm)])

    def farm_wells(self: Settlement, reach_ft: float = 500.0, edge_ft: float = 150.0) -> int:  # type: ignore[misc]
        """Shared wells for the FARM BELT (town/city scale): the farmsteads outside the urban
        core drink daily too, and Rokugan's unusually well-run domains sink wells liberally
        (the same liberty behind the literal urban idobata count) - so no farmhouse stands
        more than ~500 real ft from a well. Call AFTER farmsteads(). Farmhouses within
        ~150 real ft of the view edge are exempt (their well is presumed just off the map,
        like the fields that run off-edge). Deterministic - no RNG draws, so a map whose
        farm belt is already covered (Hoshizora) is byte-identical with or without the call.
        Greedy cluster cover: seat a well near the densest uncovered cluster's centroid via
        well_at's clear-spot test, repeat. Gated by farm_wells_within_reach."""
        # SCOPED (2026-08-08): the rural well pass, keyed as one phase like farmsteads().
        with self.rng_scope("farm_wells", "belt"), self.frozen_terrain():  # as place_wells: the farm belt does not move rivers while it sinks wells
            return self._farm_wells(reach_ft, edge_ft)

    def _farm_wells(self: Settlement, reach_ft: float, edge_ft: float) -> int:  # type: ignore[misc]
        reach = self.px(reach_ft)
        edge = self.px(edge_ft)
        vx, vy, vw, vh = self.view if self.view else (0, 0, self.W, self.H)
        houses = [h for h in self.M["houses"] if min(h["x"] - vx, h["y"] - vy, vx + vw - h["x"], vy + vh - h["y"]) >= edge]

        def covered(h: Mapping[str, Any]) -> bool:
            return any((h["x"] - w["x"]) ** 2 + (h["y"] - w["y"]) ** 2 <= reach * reach for w in self.M["wells"])

        placed = 0
        for _ in range(60):
            todo = [h for h in houses if not covered(h)]
            if not todo:
                break
            best = max(todo, key=lambda h: sum(1 for o in todo if (h["x"] - o["x"]) ** 2 + (h["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2))
            cl = [o for o in todo if (best["x"] - o["x"]) ** 2 + (best["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2]
            # seat the well in a STEADING'S DOORYARD, not at the cluster centroid: a farm belt's
            # open ground is mostly CROP (where well_at rightly refuses to stand a wellhead), and
            # historically the rural well sat in a farmstead's own yard anyway - so walk the
            # cluster's members densest-first and ring each until a clear dooryard spot takes
            cl.sort(key=lambda h: -sum(1 for o in todo if (h["x"] - o["x"]) ** 2 + (h["y"] - o["y"]) ** 2 <= (0.9 * reach) ** 2))
            seated = False
            for h in cl:
                for r_, n_ in (
                    (20.0, 8),
                    (30.0, 12),
                    (42.0, 12),
                    (60.0, 16),
                    (80.0, 16),
                    (100.0, 20),
                    (125.0, 24),
                    (150.0, 24),
                ):  # rings widen to ~240 ft at city grain: a steading's inner yard is dense with its own appurtenances and the crop starts right past them, so the clear spot is often the open margin ground BETWEEN steadings
                    for k in range(n_):
                        a = 2 * math.pi * k / n_
                        if self.well_at(h["x"] + r_ * math.cos(a), h["y"] + r_ * math.sin(a)):
                            seated = True
                            placed += 1
                            break
                    if seated:
                        break
                if seated:
                    break
            if not seated:
                # FALLBACK: the cluster's open ground may all be field-ENVELOPE rim slack - the
                # smoothed outline claims more than the crop fills, and _fits rightly refuses the
                # envelope. A farm well standing on unplanted rim ground is fine (that IS the
                # steading's margin); standing on CROP is not. So retry with the envelope blocks
                # suspended and an explicit test against the DRAWN plots instead.
                crop: list[list[tuple[float, float]]] = [list(dp2) for dp2 in self.dry_polys]
                for frec in self.M.get("fields", []):
                    crop += [[(q[0], q[1]) for q in p2] for p2 in frec.get("plot_polys", [])]

                # Each plot's bbox (14 ft margin baked in) computed ONCE. PREFILTER family: the box
                # prunes, point_in_poly still decides, so verdicts are unchanged - proven by the
                # pool regenerating byte-identical. It used to be inline in the loop below, so every
                # candidate seat re-derived all ~1,000 plots' boxes from their vertices: 22.5M min()
                # + 17.2M max() calls, ~40% of Tango's gen (profiled 2026-08-03). Same disease as
                # the 45-minute well bug - static geometry re-scanned per candidate.
                crop_boxed: list[tuple[list[tuple[float, float]], float, float, float, float]] = [
                    (cp2, min(q[0] for q in cp2) - 14.0, min(q[1] for q in cp2) - 14.0, max(q[0] for q in cp2) + 14.0, max(q[1] for q in cp2) + 14.0) for cp2 in crop
                ]

                def on_crop(
                    x2: float, y2: float, boxed: list[tuple[list[tuple[float, float]], float, float, float, float]] = crop_boxed
                ) -> bool:  # bound as a default: the closure lives one loop iteration (B023)
                    return any(bx0 <= x2 <= bx1 and by0 <= y2 <= by1 and point_in_poly(x2, y2, cp2) for cp2, bx0, by0, bx1, by1 in boxed)

                save = self.field_polys
                self.field_polys = Indexed()  # Indexed, not [] - so the suspended pass keeps its own index (and the ORIGINAL object, restored below, keeps the one it already built)
                try:
                    for h in cl:
                        # a nearest-first GRID scan, not rings: the clear ground here is pinholes
                        # between steading footprints, and sparse ring angles walk right past them
                        cands = [(h["x"] + dx, h["y"] + dy) for dx in range(-156, 157, 6) for dy in range(-156, 157, 6) if 18 * 18 <= dx * dx + dy * dy <= 156 * 156]
                        cands.sort(key=lambda c: (c[0] - h["x"]) ** 2 + (c[1] - h["y"]) ** 2)
                        for wx2, wy2 in cands:
                            if not on_crop(wx2, wy2) and self.well_at(wx2, wy2):
                                seated = True
                                placed += 1
                                break
                        if seated:
                            break
                finally:
                    self.field_polys = save
            if not seated:
                houses = [h2 for h2 in houses if h2 is not best]  # nothing seats anywhere in this cluster - skip it rather than spin
        return placed

    def well_at(self: Settlement, x: float, y: float, r: float = 8, shrine: bool = False) -> bool:  # type: ignore[misc]
        """Place ONE well at (x, y), but only if the spot is clear (a block interior off lanes,
        compounds, the bound, and other placed things - the same `_fits` test place_wells uses).
        Returns True if it placed. For hand-seeding wells into cramped, lane-laced quarters the grid
        scatter can't reach - pass a generous candidate list and the blocked ones simply no-op.
        A spot inside a scrub/pasture/coppice COVER poly is refused too (2026-07-24, caught by
        scrub_clear_of_urban_fabric when a torii-count ripple reseated three Hirameki farm wells
        into the grazing commons): a wellhead stands in worked dooryard/margin ground, never out
        in the grazed waste - and the cover scatter is drawn long before the farm wells, so the
        well must yield, not the commons."""
        if self._in_scrub_cover(x, y) or not self._well_ground_clear(x, y):
            return False
        # THE 30x30 IS A FIXED-PIXEL CONSTANT IN A SCALE-AWARE FAMILY, AND IT NO LONGER MEANS ONE
        # THING (measured 2026-08-08). `2 * r + 14` is 30px for the default r=8 REGARDLESS of ftpx,
        # while the head this reserves ground for is `_well_vr()` = px(12.376), which DOES scale. So
        # the ratio of reserved ground to drawn glyph is exactly ftpx, and every pool map disagrees:
        #
        #     ftpx=1  hamlets, towns   head 24.8px   reservation 30px   1.21x   (~30 real ft)
        #     ftpx=2  villages         head 12.4px   reservation 30px   2.42x   (~60 real ft)
        #     ftpx=3  cities           head  8.0px   reservation 30px   3.75x   (~90 real ft)
        #
        # Same ~24.8 ft well-house, three different answers: the placer demands 30 real ft of
        # standing room around it on a hamlet and 90 real ft on a city. The constant was DERIVED at
        # 1px=1ft, where it is a sensible ~2.6px margin a side, and was never re-derived when the
        # scale ladder added the 2 ft and 3 ft tiers - the exact trap `well()`'s own glyph comment
        # warns about ("fixed pixels would make it look right in the dense city but far too small
        # beside a village/town's larger houses"), running the other way.
        #
        # IT IS NOT A DELIBERATE DRAWING APRON, though the intent behind `_place_wells`' "modest
        # footprint" comment reads like one. An apron would be RESERVED as well as demanded, and it
        # is not: `well()` registers only `(x, y, 2 * vroof, 2 * vroof)` in `placed`, so on a city
        # map this asks 30px of clearance at placement and then occupies 8px, and later features
        # pack right up to the head. Over-restrictive going in, under-reserving once in - which is
        # skill CLAUDE.md's item 3 ("placement tests a DIFFERENT footprint than the one drawn")
        # wearing a different hat, not a fourth kind of defect.
        #
        # COST, for whoever fixes it: on Tango, testing the TRUE drawn head instead of this box
        # accepts ~5x the ground the box does around a boxed-in steading (157 seats vs 32 in the
        # east-fan sweep), and wells are 131 of the 767 seats that whole gen loses to geometry
        # error. LEFT AS IS deliberately - changing it re-seats wells on every map in the pool and
        # re-rolls the packs that flow around them, so it belongs with the item 2/item 3 pass and
        # its re-baseline, not in a drive-by. See `_place_wells`, which computes the same box.
        if self._fits(x, y, 2 * r + 14, 2 * r + 14):
            self.well(x, y, r, shrine=shrine)
            return True
        return False

    def place_wells(self: Settlement, bbox: Any, spacing: float, r: float = 8, near: Any = None, coverage: bool = True, kind: str | None = None) -> list[Pt]:  # type: ignore[misc]
        """Scatter neighborhood wells across a residential bbox on a grid at ~`spacing` px, keeping
        each in a block INTERIOR: a candidate is dropped if it falls on a lane corridor, outside the
        city bound, on an existing compound (temple/estate/pond), or too near another well (all via
        `_fits`). For each grid cell the cell center is tried first, then a few small offsets, so a
        cell still gets a well when its exact center happens to land on a lane or compound - this keeps
        coverage even in the lane-laced warren. One well per ~spacing px serves the courtyards around
        it. Call BEFORE the quarter's house pack so the houses flow around the wells. Returns the
        placed (x, y) list. Pass coverage=False to keep `near` as a PER-CANDIDATE gate only - the
        coverage pass sweeps ALL dwellings map-wide, which a district-scoped call must not do (it
        would drop wells beside the samurai compounds, which keep no public wells)."""
        # SCOPED (2026-08-08): well siting jitters over a grid; keyed on the bbox it covers.
        with self.rng_scope("place_wells", *bbox), self.frozen_terrain():  # one well index for the whole scatter, not one revalidation per candidate seat
            return self._place_wells(bbox, spacing, r, near, coverage, kind)

    def _place_wells(self: Settlement, bbox: Any, spacing: float, r: float, near: Any, coverage: bool, kind: str | None = None) -> list[Pt]:  # type: ignore[misc]
        x0, y0, x1, y1 = bbox
        # a modest footprint => wells sit in the courtyards, not crammed on a lane. The SAME box
        # `well_at` computes, and it carries the same caveat: 30px is fixed while the drawn head
        # scales with ftpx, so this reserves 1.21x the glyph on a hamlet and 3.75x on a city. Read
        # the note in `well_at` before touching it - the two must move together.
        probe = 2 * r + 14
        d = spacing * 0.26
        offsets = [(0, 0), (d, d), (-d, -d), (d, -d), (-d, d)]
        # `near`: only place a well that has a DWELLING within `near` px - a well serves the households
        # around it, so it must sit AMONG the buildings, never out in open countryside. Pass it when the
        # houses are already placed (the rural tiers: place_wells runs AFTER the field rings); a city's
        # pack runs after place_wells and fills in around the wells, so the city omits it.
        dwell = self.M.get("buildings", []) + self.M.get("houses", []) if near is not None else None
        out: list[Pt] = []
        yy = y0 + spacing / 2
        while yy <= y1:
            xx = x0 + spacing / 2
            while xx <= x1:
                for ox, oy in offsets:
                    cx, cy = xx + ox, yy + oy
                    if (
                        not self._in_scrub_cover(cx, cy)
                        and self._well_ground_clear(cx, cy)
                        and self._fits(cx, cy, probe, probe)
                        and (dwell is None or any((b["x"] - cx) ** 2 + (b["y"] - cy) ** 2 < near * near for b in dwell))
                    ):
                        self.well(cx, cy, r, kind=kind)
                        out.append((cx, cy))
                        break
                xx += spacing
            yy += spacing
        if dwell is not None and coverage:
            # COVERAGE pass: the grid can leave an edge / outlier dwelling in a gap. Guarantee none is left
            # well-less: any dwelling with no well within `spacing` gets one dropped in a clear spot beside it.
            for b in dwell:
                if all((b["x"] - wx) ** 2 + (b["y"] - wy) ** 2 > spacing * spacing for wx, wy in out):
                    # SIX SEATS, deliberately not a wider walk (tried 2026-07-27 and reverted): a
                    # 64-candidate ring walk does find a seat for a dwelling boxed in by refused
                    # ground, but on a CITY it also seats wells the block-interior rule rejects -
                    # over a ministry, on a lane - because `_fits` and `_well_ground_clear` are not
                    # the whole of what a city well must satisfy. A dwelling this cannot reach is
                    # better reported by farm_wells_within_reach and hand-seeded with `well_at`,
                    # which is what the gens already do for cramped quarters.
                    for ox, oy in ((0, near * 0.6), (near * 0.6, 0), (-near * 0.6, 0), (0, -near * 0.6), (near * 0.45, near * 0.45), (-near * 0.45, near * 0.45)):
                        cx, cy = b["x"] + ox, b["y"] + oy
                        if not self._in_scrub_cover(cx, cy) and self._well_ground_clear(cx, cy) and self._fits(cx, cy, probe, probe):
                            self.well(cx, cy, r)
                            out.append((cx, cy))
                            break
        return out

    def shrine_well(self: Settlement, cx: float, cy: float, r: float = 8) -> Pt | None:  # type: ignore[misc]
        """Place a set-apart shrine's OWN ablution well (temizu) close beside the hall at (cx, cy): try
        positions on widening rings until one fits clear of the hall, torii, graveyard, lanes, and any other
        placed footprint (`well_at`'s test). A larger hall pushes its well onto an outer ring. Call AFTER the
        hall, houses, and village wells are placed. Returns the placed (x, y), or None if it is walled in.
        For a remote shrine that cannot use the village's shared wells (`remote_shrine_has_own_well`)."""
        for rr in (54, 66, 80, 96, 112):
            for a in range(0, 360, 30):
                x, y = cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))
                if self.well_at(x, y, r, shrine=True):
                    return (x, y)
        return None
