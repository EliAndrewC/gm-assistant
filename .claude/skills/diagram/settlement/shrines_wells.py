"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import contextlib
import math
import random
from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from ._geom import (
    HALL_CAPTION_FS,
    TORII_PITCH_FT,
    TORII_PITCH_MAX_SPANS,
    Indexed,
    PointGrid,
    Poly,
    Pt,
    edge_dist,
    paddy_wet_rings,
    point_in_poly,
    ring_touches,
    seg_dist,
    segments_cross,
    torii_halfbox,
    torii_seat_on_wall,
    torii_wall_conflicts,
    wall_runs,
)
from ._knobs import roll_torii_count

if TYPE_CHECKING:
    from .core import Settlement


class ShrinesWellsMixin:
    # ---- hill + shrine + torii
    def hill(self: Settlement, cx: float, cy: float, rx: float, ry: float, steep: bool = False) -> Pt:  # type: ignore[misc]
        rings = [(cx, cy + 28, rx, ry), (cx, cy, rx * 0.76, ry * 0.76), (cx, cy - 26, rx * 0.52, ry * 0.52), (cx, cy - 44, rx * 0.30, ry * 0.32)]
        self.M["hill"] = [rings[0][0], rings[0][1], rings[0][2], rings[0][3]]
        self.M["summit"] = [rings[3][0], rings[3][1], rings[3][2], rings[3][3]]
        self.ellipses.append((rings[0][0], rings[0][1], rings[0][2], rings[0][3]))
        for (ax, ay, arx, ary), shade in zip(rings, ['#DFD0A2', '#D8C795', '#D0BD87', '#C8B37B'], strict=False):
            self.add(f'<ellipse cx="{ax:.0f}" cy="{ay:.0f}" rx="{arx:.0f}" ry="{ary:.0f}" fill="{shade}" stroke="#A8995F" stroke-width="1"/>')
        ocx, ocy, orx, ory = rings[0]
        for k in range(30):
            a = 2 * math.pi * k / 30
            ex, ey = ocx + math.cos(a) * orx, ocy + math.sin(a) * ory
            self.add(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex + math.cos(a) * 9:.0f}" y2="{ey + math.sin(a) * 9:.0f}" stroke="#A8995F" stroke-width="0.9"/>')
        if steep:
            # emphasized downslope hachures over the steep north back and upper flanks:
            # closely-spaced, longer ticks read as a steep, undefendable-on-foot slope
            n = 52
            for k in range(n + 1):
                ang = math.radians(195 + (345 - 195) * k / n)
                ex, ey = ocx + math.cos(ang) * orx, ocy + math.sin(ang) * ory
                ln = 19 + 5 * math.sin(math.radians(195 + (345 - 195) * k / n) - math.pi / 2)
                self.add(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex + math.cos(ang) * ln:.1f}" y2="{ey + math.sin(ang) * ln:.1f}" stroke="#8F7E48" stroke-width="1.0"/>')
        st = random.getstate()
        random.seed(4)
        for _ in range(15):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0.4, 0.9)
            tx = cx + math.cos(a) * rx * rr
            ty = (cy + 12) + math.sin(a) * ry * rr
            self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{random.uniform(4, 6):.1f}" fill="#7E9B5C" stroke="#52663C" stroke-width="0.8"/>')
            self.add(f'<circle cx="{tx - 1:.0f}" cy="{ty - 1:.0f}" r="1.6" fill="#9DB87A"/>')
        random.setstate(st)
        return (cx, cy - 40)  # summit point for the shrine

    def shrine(self: Settlement, x: float, y: float, w_ft: float = 62, h_ft: float = 42, kind: str = "shrine") -> None:  # type: ignore[misc]
        """The legacy simple shrine glyph (the civic_shrine roll path + secondary_shrine). TRUE SCALE
        (GM 2026-07-21): dimensions are REAL FEET, converted through px() - an ordinary village
        tutelary hall ~62x42 ft (~240 m2, inside the 600 m2 village ceiling). The old signature took
        fixed PIXELS (104x68 default), a latent footgun that would have drawn a 208x136 ft
        monastery-sized hall on any village that used the default civic_shrine path."""
        w, h = self.px(w_ft), self.px(h_ft)
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 8:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="#6B2A18" stroke-width="0.7"/>')
        self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h})

    def small_shrine(self: Settlement, x: float, y: float, w: Any = None, h: Any = None) -> None:  # type: ignore[misc]
        """A small wayside / neighborhood Shinto SHRINE - a vermilion-roofed shed with a little torii
        in front, the kind that dot a temple neighborhood. Non-residential: recorded in M['religious']
        as kind 'small_shrine' (so it is not housing and not a full temple - it needs no torii avenue
        and is not counted as a dwelling). Placed early so the dense packs flow around it."""
        if w is None:
            w, h = self.px(32), self.px(24)  # ~32x24 ft wayside shrine (town-calibrated glyph)
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#C9876C" stroke="#6B2A18" stroke-width="1.4"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="5" fill="#A03020"/>')  # vermilion roof ridge
        ty = y + h / 2 + max(self.px(8), 3)  # a little torii just in front (south)
        m2 = self.px(9.0) / 2  # TRUE SCALE: a wayside-shrine torii spans ~9 ft (vs the shed's ~32 ft)
        self.add(
            f'<g transform="translate({x:.0f},{ty:.0f})"><line x1="{-m2 * 0.87:.1f}" y1="0" x2="{m2 * 0.87:.1f}" y2="0" stroke="#A03020" stroke-width="{max(self.px(1.2), 1.4):.2f}"/>'
            f'<line x1="{-m2:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2:.1f}" y2="{-m2 * 0.5:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{-m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{-m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/>'
            f'<line x1="{m2 * 0.62:.1f}" y1="{-m2 * 0.5:.1f}" x2="{m2 * 0.62:.1f}" y2="{m2 * 0.75:.1f}" stroke="#A03020" stroke-width="{max(self.px(1.0), 1.2):.2f}"/></g>'
        )
        self.M["religious"].append({"kind": "small_shrine", "x": x, "y": y, "w": w, "h": h, "rot": 0})
        self.placed.append((x, y, w, h))
        bm = 16
        self.block_polys.append([(x0 - bm, y0 - bm), (x + w / 2 + bm, y0 - bm), (x + w / 2 + bm, y + h / 2 + bm + 16), (x0 - bm, y + h / 2 + bm + 16)])

    def _build_well_index(self: Settlement) -> tuple[PointGrid, PointGrid, PointGrid]:  # type: ignore[misc]
        """The three grids `_well_ground_clear` queries - watercourse segments, dry plots, paddy
        wet rings - each item boxed so a query pads by the wellhead radius alone."""
        recs = {key: self.M.get(key, []) or [] for key in ("streams", "channels", "field_ditches", "canals", "dry_plots")}
        water = []
        for key, dw in (("streams", 9.0), ("channels", 2.5), ("field_ditches", 1.5), ("canals", 14.0)):
            for rec in recs[key]:
                pts = rec.get("poly") or rec.get("pts")
                if not pts:
                    continue  # pragma: no cover - defensive: every watercourse carries a path
                hw = float(rec.get("w") or dw) / 2
                for i in range(len(pts) - 1):
                    (ax, ay), (bx, by) = pts[i], pts[i + 1]
                    # box carries the course's own half-width, so a query pads by vr alone
                    water.append((hw, (ax, ay), (bx, by), min(ax, bx) - hw, min(ay, by) - hw, max(ax, bx) + hw, max(ay, by) + hw))
        dry = []
        for dp in recs["dry_plots"]:
            poly = dp.get("poly")
            if not poly:
                continue  # pragma: no cover - defensive: every dry plot carries an outline
            dry.append((poly, min(q[0] for q in poly), min(q[1] for q in poly), max(q[0] for q in poly), max(q[1] for q in poly)))
        wet = [(r, min(q[0] for q in r), min(q[1] for q in r), max(q[0] for q in r), max(q[1] for q in r)) for r in paddy_wet_rings(self.M)]
        grids = PointGrid(), PointGrid(), PointGrid()
        for grid, items in zip(grids, (water, dry, wet), strict=True):
            grid.extend(items)
        return grids

    def _terrain_fingerprint(self: Settlement) -> Any:  # type: ignore[misc]
        """Every point count of the geometry `_build_well_index` reads. Expensive on purpose - it
        runs TWICE PER PASS (see `frozen_terrain`), not once per candidate seat."""
        fields = self.M.get("fields") or []
        recs = [self.M.get(key, []) or [] for key in ("streams", "channels", "field_ditches", "canals", "dry_plots")]
        return (
            len(fields),
            sum(len(p) for fl in fields for p in (fl.get("plot_polys") or [])) + sum(len(fl.get("outline") or []) for fl in fields),
            tuple(len(rs) for rs in recs),
            sum(len(rec.get("poly") or rec.get("pts") or ()) for rs in recs for rec in rs),
        )

    @contextlib.contextmanager
    def frozen_terrain(self: Settlement) -> Iterator[None]:  # type: ignore[misc]
        """Declare that the water and crop geometry will not change for the duration, so the well
        index can be built ONCE instead of revalidated per candidate seat.

        WHY A SCOPE AND NOT A CACHE KEY. This started as a memo guarded by a fingerprint, and the
        fingerprint became the single hottest thing in Minami's gen: counting the points of 927
        rings on each of ~133k seats cost more than the scan it replaced (156M len() calls,
        ~8s of a 30s gen). Making the key CHEAPER was tried and was wrong - record counts miss an
        in-place same-length replacement, and a wellhead duly cleared to stand in a paddy. The way
        out is to stop guessing: a well pass does not move rivers or fields, so it states that, and
        the index is simply valid for the pass.

        THE ASSERTION IS THE POINT. On exit the terrain fingerprint is recomputed and compared, so
        a future change that DOES mutate terrain inside a pass fails loudly here instead of quietly
        siting wells against stale water. That costs two fingerprints per pass instead of 133k.
        Outside a pass the index is built per call - correct, and irrelevantly slow at the handful
        of hand-seeded `well_at` calls a gen makes. Nesting is refcounted, so a pass may call
        another."""
        if self._frozen_wells is None:
            self._frozen_wells: tuple[tuple[PointGrid, PointGrid, PointGrid], Any] | None = (self._build_well_index(), self._terrain_fingerprint())
            self._frozen_depth = 0
        self._frozen_depth += 1
        try:
            yield
        finally:
            self._frozen_depth -= 1
            if self._frozen_depth == 0:
                held = self._frozen_wells
                self._frozen_wells = None
                assert held is not None and held[1] == self._terrain_fingerprint(), (
                    "the water/crop geometry CHANGED inside a frozen_terrain scope, so wells in this pass were "
                    "sited against a stale index. Either move the terrain change out of the pass, or drop the "
                    "freeze around it - do not widen this assertion."
                )

    def _well_index(self: Settlement) -> tuple[PointGrid, PointGrid, PointGrid]:  # type: ignore[misc]
        frozen = self._frozen_wells
        return frozen[0] if frozen is not None else self._build_well_index()

    def _wet_toe_keepout(self: Settlement) -> Any:  # type: ignore[misc]
        """The reed toe BELOW all cultivation - ground no wellhead may be sunk in - or None.

        Derived rather than read back, because the marsh is drawn LATE (`hinterland()`, after the
        structures) and wells are placed EARLY, so by the time the reeds exist the well is already
        in them. `toe_band` is the same derivation the reeds themselves use, which is the point of
        its having been factored out. Memoized for the pass: this is consulted once per candidate
        seat and the band cannot move while a scatter runs (see `frozen_terrain`)."""
        if getattr(self, "_wt_cache", None) is None:
            # ONLY WHERE A TOE MARSH IS ACTUALLY DRAWN. `toe_band` is pure geometry and will happily
            # compute a band below the crop of a map that has no reeds anywhere - and TOWNS AND CITIES
            # HAVE NO TOE MARSH: their ditch discharge goes into an engineered moat/canal network and
            # their outskirts are premium intensively-worked land (the drainage-investment gradient,
            # research/water.md). Reserving that ground as imaginary bog cost Tango six farmhouses'
            # wells on the first run of this rule. The split is by SCALE because that is how the
            # doctrine states it.
            toe = self.toe_band() if self.M.get("meta", {}).get("scale") in ("hamlet", "village") else []
            cult = [p for poly in self.field_polys for p in poly] + [p for dp in self.M.get("dry_plots", []) for p in dp["poly"]]
            if not toe or not cult:
                self._wt_cache: Any = (None, 0.0, (0.0, 0.0), (0.0, 0.0), 0.0, 0.0)
            else:
                deg = self.M.get("meta", {}).get("down_deg", 90)
                dv = (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
                u = (-dv[1], dv[0])  # across the slope
                us = [p[0] * u[0] + p[1] * u[1] for p in cult]
                self._wt_cache = (toe, max(p[0] * dv[0] + p[1] * dv[1] for p in cult), dv, u, min(us), max(us))
        return self._wt_cache

    def _well_ground_clear(self: Settlement, cx: float, cy: float, vr: float | None = None) -> bool:  # type: ignore[misc]
        """Is this ground fit to sink a WELLHEAD in? You do not dig a well in a watercourse, you do
        not dig one in the middle of a crop plot, and you do not dig one in a BOG.

        Placement predicted everything else about a well site - lanes, compounds, the bound, its
        neighbors - but never the water or the crop, so the overlap matrix (feature 017) found four
        wells standing in ditches, a channel and a hatake plot across three maps. Tested against the
        DRAWN head (`_well_vr`), because what a reader sees is ink on ink.

        The wet-crop leg is the placement half of `wells_clear_of_paddies` (GM 2026-07-27: "wells
        on dry crops are okay, but not in rice paddies, surely") - a paddy is a puddled, bunded
        basin held under standing water, so a head sunk there stands in the water it is an
        alternative to. Both halves read `paddy_wet_rings` (see it for why the DRAWN basins, not
        the smoothed envelope, are the water), and the same strictness as the dry-plot rule
        applies: the drawn head may not lap the crop.

        THE BOG LEG (settlement-review 2026-08-12, Akagahara: a wellhead standing among the drawn reed
        glyphs ~50 ft from the drainage pond) is the placement half of `wells_off_the_wet_toe`, and it
        measures the same thing that check does - ground below the crop's LOWEST point, inside the toe
        band - rather than the band alone, because the band's uphill lip deliberately tucks under the
        field and carries no reeds. Placement never saw it before because the marsh is drawn after the
        wells; `toe_band` closes that by being derivable in advance.

        INDEXED, and the index is built ONCE PER PASS rather than validated per call - see
        `frozen_terrain`. This method runs once per CANDIDATE seat: place_wells
        alone probes ~133k candidates on Minami, and farm_wells' fallback ~2,700 per boxed-in
        steading, so re-scanning ~580 watercourse segments, every dry plot, and 927 paddy basins
        per candidate turned a ~5s gen into a >45-minute grind (2026-08-02, profiled: 95M
        seg_dist calls, ~90% of gen wall time). The memo is invalidated by a cheap fingerprint
        (record and point counts of everything scanned); the wells are placed long after the
        terrain is drawn, so the geometry is stable across the whole placement pass."""
        # THE CROP DATUM IS ONLY GOOD WHERE THE CROP IS, and the check says the same thing the same
        # way (`wells_off_the_wet_toe`) - the two must not measure differently or they will disagree
        # about a seat. The band's uphill lip carries no reeds only where it tucks UNDER the field;
        # out past the field's cross-slope span the lip is exposed and reeded from its edge.
        toe, low, dv, uv, u_lo, u_hi = self._wet_toe_keepout()
        if toe is not None and point_in_poly(cx, cy, toe):
            u = cx * uv[0] + cy * uv[1]
            if not (u_lo <= u <= u_hi) or cx * dv[0] + cy * dv[1] > low:
                return False
        vr = self._well_vr() if vr is None else vr
        water_g, dry_g, wet_g = self._well_index()
        for hw, pa, pb, bx0, by0, bx1, by1 in water_g.near(cx, cy, vr):
            if bx0 - vr <= cx <= bx1 + vr and by0 - vr <= cy <= by1 + vr and seg_dist(cx, cy, pa, pb) < hw + vr:
                return False
        pond = self.M.get("pond")
        if pond and ((cx - pond[0]) ** 2) / ((pond[2] + vr) ** 2) + ((cy - pond[1]) ** 2) / ((pond[3] + vr) ** 2) < 1.0:
            return False
        for poly, bx0, by0, bx1, by1 in dry_g.near(cx, cy, vr):
            if bx0 - vr <= cx <= bx1 + vr and by0 - vr <= cy <= by1 + vr and (point_in_poly(cx, cy, poly) or any(seg_dist(cx, cy, poly[i], poly[(i + 1) % len(poly)]) < vr for i in range(len(poly)))):
                return False
        return not any(bx0 - vr <= cx <= bx1 + vr and by0 - vr <= cy <= by1 + vr and ring_touches(cx, cy, vr, ring) for ring, bx0, by0, bx1, by1 in wet_g.near(cx, cy, vr))

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

    def _footprint_clear(self: Settlement, x: float, y: float, w: float, h: float) -> bool:  # type: ignore[misc]
        """Is the WHOLE `w` x `h` footprint at (x, y) inside the bound and off every block/corridor?

        `_fits` deliberately tests only a candidate's CENTER against `self.bound`, `block_polys` and
        the corridors (it is footprint-aware only for `placed` / `grove_rects`). That asymmetry is
        what lets a dense urban pack put a house's eaves over the edge of a block poly, and changing
        it wholesale would reflow every packed quarter in the pool - so this tightens exactly one
        thing: **the bound**.

        The distinction is soft reservation vs hard boundary. `block_polys` and corridors are
        RESERVATIONS - a label band, a civic apron, a fence standoff - and a footprint overhanging
        one by a few px is routine and invisible; demanding the whole footprint clear them cost
        Nagahara a well and pushed Hoshizora's punishment ground off its street when it was tried.
        `self.bound` is a HARD EDGE: the ring-road loop a city packs inside, or the wall. A footprint
        that crosses it is drawn on the patrol road, which is a defect at any overhang - and it is
        exactly how the martial hall got a seat whose SE corner crossed Tango's ring bed while its
        center sat comfortably inside the bound (GM 2026-07-25).

        Nine samples (four corners, four edge midpoints, the center) - enough for any bound bigger
        than a quarter of the footprint, and free at the scale open_seat is called at. Corridors and block
        polys stay center-tested here, deliberately - see above."""
        hw, hh = w / 2, h / 2
        pts = [(x + dx, y + dy) for dx in (-hw, 0.0, hw) for dy in (-hh, 0.0, hh)]
        return not self.bound or all(point_in_poly(px, py, self.bound) for px, py in pts)

    def open_seat(self: Settlement, rect: Any, w: float, h: float, step: float = 4.0, clear_of: Any = (), well: bool = False, footprint: bool = True, disc: bool = False) -> Pt | None:  # type: ignore[misc]
        """WHERE can a `w` x `h` feature actually stand inside `rect` (x0, y0, x1, y1)? Scans the
        rect and returns the best clear seat, or None if the ground is genuinely full.

        WHY THIS EXISTS (GM 2026-07-25, from a transcript profile): fitting one extra well into a
        packed quarter took THREE regenerate-and-check cycles - two batches of hand-picked
        coordinates, every one of them rejected - because the engine knows where a feature can go
        and nothing outside it could ask. Guessing from a manifest is worse than useless: a scan
        that sees only building rects recommends seats that `_fits` then refuses for reasons that
        never appear in the manifest at all (a ward fence's no-build corridor, a block poly, the
        bound ring). So this asks the SAME `_fits` the real placement path asks, at the same moment
        in the gen, and the answer is therefore the truth rather than a guess.

        `clear_of` is a list of (x, y) to stand away FROM - pass the existing wells/features of the
        same kind and the seat returned is the one that splits the catchment best (maximum distance
        to the nearest of them, ties broken toward the rect's center). `well=True` also applies the
        wellhead-specific refusal (`_in_scrub_cover`), so the seat it returns is one `well_at` will
        actually take. Call it right where the feature would be placed - what fits depends entirely
        on what has been drawn so far (see CLAUDE.md "DRAW ORDER").

        The seat returned is clear along its WHOLE FOOTPRINT, not merely at its center - see
        `_footprint_clear` for why that differs from `_fits` and why only this API tightens it.
        `footprint=False` falls back to the bare center test, i.e. exactly what a pack would take."""
        x0, y0, x1, y1 = (float(v) for v in rect)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(float(px), float(py)) for px, py in clear_of]
        best: tuple[float, float, Pt] | None = None
        gy = y0
        while gy <= y1:
            gx = x0
            while gx <= x1:
                # `disc=True` says the CANDIDATE is round, so min(w,h)/2 is its exact reach rather
                # than the probe box's half-diagonal. Opt-in, not implied by well=True: the derived
                # well GRID relies on the conservative radius as its padding, and making it exact
                # there put a wellhead on a building.
                if (not well or not self._in_scrub_cover(gx, gy)) and self._fits(gx, gy, w, h, disc=disc) and (not footprint or self._footprint_clear(gx, gy, w, h)):
                    apart = min((math.hypot(gx - px, gy - py) for px, py in pts), default=0.0)
                    central = -math.hypot(gx - cx, gy - cy)  # tie-break toward the middle of the rect
                    if best is None or (apart, central) > (best[0], best[1]):
                        best = (apart, central, (gx, gy))
                gx += step
            gy += step
        return best[2] if best else None

    def _in_scrub_cover(self: Settlement, x: float, y: float) -> bool:  # type: ignore[misc]
        """Is (x, y) inside a registered scrub/pasture/coppice/marsh COVER poly? Both well paths
        (well_at hand-seeding + the place_wells grid) refuse such ground - a wellhead stands in
        worked dooryard/margin ground, never out in the grazed waste (scrub_clear_of_urban_fabric).
        Only covers registered BEFORE the well call are visible, so gens draw their commons first."""
        for ck in ("commons", "pastures", "forest_patches", "marshes"):
            for o in self.M.get(ck, []) or []:
                p = o.get("poly") if isinstance(o, dict) else o
                if p is not None and len(p) >= 3 and point_in_poly(x, y, p):
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

    def _assert_walls_clear_of_torii(self: Settlement, what: str) -> None:  # type: ignore[misc]
        """Re-ask the torii/wall question the moment a WALL is on the page. A wall drawn AFTER an
        arch cannot be dodged by the arch (see CLAUDE.md "DRAW ORDER"), and neither feature can move
        once drawn - so the honest response is to fail the generator and let the author resite the
        geometry, exactly as the merchant-estate wall does when its slide fan runs out."""
        bad = torii_wall_conflicts(self.M)
        if bad:
            raise ValueError(
                f"{what} runs through torii arch(es) at {[(x, y) for x, y, _ in bad]} (in {bad[0][2]}) - a wall is a "
                f"continuous barrier and a torii is a freestanding gateway, so an arch never stands in one (a way "
                f"through a wall is a GATE: the city gate, a ward kido). Move the arch or the wall - or draw the wall "
                f"BEFORE the hall, and shrine_hall shortens its avenue to stop short of it automatically."
            )

    def _avenue_pitch(self: Settlement, seats: list[Pt]) -> list[Pt]:  # type: ignore[misc]
        """Hold a torii avenue to the house PITCH (see TORII_PITCH_FT / TORII_PITCH_MAX_SPANS). The gen
        authors the avenue's LINE; the engine owns its stride, the same division of labor as the COUNT
        (rolled, not authored). An avenue whose arches stand more than the cap apart is re-laid at the
        standard ~20 ft, resampled by arc length ALONG the authored line - so it keeps its direction and
        its curve, and its innermost arch keeps the seat the gen chose at the hall's threshold; only the
        stride changes. Within the band the gen's own spacing stands untouched (the village avenues at
        ~30 ft are deliberate), so this fires only on the over-wide city/town runs."""
        if len(seats) < 2:
            return seats
        gaps = [math.hypot(seats[i + 1][0] - seats[i][0], seats[i + 1][1] - seats[i][1]) for i in range(len(seats) - 1)]
        if max(gaps) <= self.px(16.0) * TORII_PITCH_MAX_SPANS:
            return seats

        def along(dist: float) -> Pt:
            d = dist
            for i in range(len(seats) - 1):
                if d <= gaps[i] or i == len(seats) - 2:  # the last segment also carries any run PAST the authored line
                    t = d / gaps[i] if gaps[i] else 0.0
                    return (seats[i][0] + (seats[i + 1][0] - seats[i][0]) * t, seats[i][1] + (seats[i + 1][1] - seats[i][1]) * t)
                d -= gaps[i]
            return seats[-1]  # pragma: no cover - unreachable: the i == len-2 branch always returns

        step = self.px(TORII_PITCH_FT)
        return [along(step * i) for i in range(len(seats))]

    def _avenue_at_threshold(self: Settlement, x: float, y: float, w: float, h: float, seats: list[Pt]) -> list[Pt]:  # type: ignore[misc]
        """Seat a sando's INNERMOST arch ONE PITCH off the hall's front, sliding the whole run in along
        the face it approaches. The gen authors the avenue's LINE; the engine already owned its COUNT
        (the tier roll) and its STRIDE (`_avenue_pitch`), and this hands it the THRESHOLD too.

        WHY (GM 2026-07-27): "torii arches appear to be a sensible distance apart from each other but
        appear to start a huge distance away from city temples. The distance from the front of the
        temple should be the same as the distance between each torii arch." The gens had been
        authoring the whole run by hand, and once `_avenue_pitch` took over the stride the two numbers
        stopped agreeing: Tango's Bishamon sando stood 139 ft off its hall with 20 ft between arches -
        three arches marooned up a street past a flophouse, reading as marks beside an unrelated
        building - and Nagahara's Ebisu avenue began 120 ft south of its temple, in the middle of a
        housing block with the caption and two rows of houses between hall and first gate. An approach
        that does not TOUCH its hall is not an approach.

        The correction is a TRANSLATION, never a re-shaping: the run keeps its direction, its curve and
        its stride, and only its distance from the hall changes. It slides along the outward normal from
        the hall's FOOTPRINT to the innermost arch (`pt_to_rect`'s geometry, per CLAUDE.md's "Gap VERDICT
        reads footprints, never centres") - so a run authored square in front of the hall walks straight
        in down its own axis, while one authored off to the side is pulled onto the flank it actually
        stands off, which is what makes the beside-the-hall gates read as that hall's. A run authored
        THROUGH the hall is left alone: that is `torii_clear_of_shrine`'s defect to report, not this
        method's to paper over."""
        if not seats:
            return seats
        pitch = math.hypot(seats[1][0] - seats[0][0], seats[1][1] - seats[0][1]) if len(seats) > 1 else self.px(TORII_PITCH_FT)
        nx = min(max(seats[0][0], x - w / 2), x + w / 2)  # the nearest point of the hall's footprint: the FRONT it stands off
        ny = min(max(seats[0][1], y - h / 2), y + h / 2)
        gap = math.hypot(seats[0][0] - nx, seats[0][1] - ny)
        if gap < 1e-6:  # the innermost arch is ON the hall - torii_clear_of_shrine's business
            return seats
        ux, uy, shift = (seats[0][0] - nx) / gap, (seats[0][1] - ny) / gap, pitch - gap
        return [(sx + ux * shift, sy + uy * shift) for sx, sy in seats]

    def _hall_caption_y(self: Settlement, x: float, y: float, w: float, h: float, label: str, label_below: bool, seats: list[Pt]) -> float:  # type: ignore[misc]
        """The baseline y of a hall's caption, kept OUT OF ITS OWN SANDO (GM 2026-07-27: an arch must
        "never be covered by the 'temple of X' label"). A hall's caption and its approach both want the
        ground at the hall's face, so the two collided the moment `_avenue_at_threshold` brought the
        arches in - and they were already colliding before it, three times in the shipped pool (Minami's
        'Temple of Bishamon' and Hoshizora's 'Monastery of Bishamon' each sat on their own arch, Kikuta's
        'Shrine to Benten' on its sando). The caption goes to the hall's BACK when its avenue owns the
        front: the gen's `label_below` is honored unless the arches are there, in which case the caption
        takes the other side. If both sides are fouled the requested side stands and
        `labels_clear_of_other_buildings` reports it - the engine does not get to hide a map that has no
        room for both.

        THREE candidate baselines, tried in a STRICT ORDER: the side the gen asked for, then that same
        side pushed clear PAST the far end of the avenue, and only then the opposite side. Arches veto a
        candidate; the first survivor wins. If all three are fouled the requested side stands and
        `labels_clear_of_other_buildings` reports it - the engine does not get to hide a map that has no
        room for both.

        WHY AN ORDER RATHER THAN A SCORE. The first version scored the survivors with `_label_hits`, the
        way `ministry` picks its label side, and it was wrong here for a DRAW ORDER reason: a hall goes
        in early, so at this point `_label_hits` can see almost nothing - Nagahara's fire tower, the
        graveyard's neighbors and the monk houses are all drawn later - and a blind score flipped
        Bishamon's caption to the hall's north side, onto a fire tower that did not exist yet. The gen
        author DOES know what is on each side, which is what `label_below` says; so honor it, and when
        the sando takes that ground, step past the sando rather than around the hall. Hoshizora is why
        stepping past has to exist at all: its monastery's parish graveyard sits deliberately at the
        BACK of the hall, so flipping the caption off the sando would just bury it in the cemetery.

        The label box measured here is `_record_label`'s recorded box, deliberately: placement and check
        must read the SAME geometry (CLAUDE.md, "Placement and its check must read the SAME manifest
        source"), or the engine congratulates itself on a clearance the gate does not see."""
        below, above = y + h / 2 + 22, y - h / 2 - 10
        want, alt = (below, above) if label_below else (above, below)
        if not seats:
            return want
        lhw = len(label) * HALL_CAPTION_FS * 0.55 / 2  # _record_label's box for a hall caption, half-width
        txh, tyu, tyd = torii_halfbox(self.ftpx)
        # past the far end of the sando, on whichever side the avenue actually runs
        beyond = max(ty + tyd for _, ty in seats) + 22 if sum(ty for _, ty in seats) / len(seats) > y else min(ty - tyu for _, ty in seats) - 10

        def fouled(ly: float) -> bool:
            top, bot = ly - HALL_CAPTION_FS * 0.8, ly + HALL_CAPTION_FS * 0.25  # ...and its vertical extent
            return any(abs(tx - x) < lhw + txh and top < ty + tyd and ty - tyu < bot for tx, ty in seats)

        return next((ly for ly in (want, beyond, alt) if not fouled(ly)), want)

    def _avenue_short_of_walls(self: Settlement, seats: list[Pt]) -> list[Pt]:  # type: ignore[misc]
        """Shorten a torii avenue so it stops SHORT of any wall (see wall_runs) - neither standing an
        arch in one nor marching the run across one, since a sando is a single approach and cannot
        continue on the far side of a barrier. It is a LINE of arches walking away from its hall, so
        the honest correction is to pull the whole run BACK - scale every seat's offset from the first
        arch by the largest factor that keeps the run clear - rather than shove one arch out of step
        with its neighbors (which would just straddle the wall). The first arch (nearest the hall)
        never moves, and the search floors out once the stride would close to one rail-span, since
        arches that touch are no avenue at all. Only walls ALREADY DRAWN are visible here (see
        CLAUDE.md "DRAW ORDER"); a wall laid later ACROSS an arch is caught by the wall methods'
        _assert_walls_clear_of_torii, and at the manifest by torii_clear_of_walls."""
        runs = wall_runs(self.M)

        def fit(f: float) -> list[Pt] | None:
            moved = [(seats[0][0] + (sx - seats[0][0]) * f, seats[0][1] + (sy - seats[0][1]) * f) for sx, sy in seats]
            if any(torii_seat_on_wall(self.M, mx, my, self.ftpx, runs) is not None for mx, my in moved):
                return None
            for _lbl, pts, _half in runs:  # ... and the WALK the arches stand on stays on ONE side of every wall
                if any(segments_cross(moved[i], moved[i + 1], pts[j], pts[j + 1]) for i in range(len(moved) - 1) for j in range(len(pts) - 1)):
                    return None
            return moved

        if not runs:
            return seats
        whole = fit(1.0)
        if whole is not None:
            return whole
        span = math.hypot(seats[-1][0] - seats[0][0], seats[-1][1] - seats[0][1])
        # The stride may tighten to just over ONE rail-span - the same floor torii_spread_out enforces,
        # so placement and check agree. (Measure it on the true 16 ft span, NOT torii_halfbox: that box
        # carries a 2 px stroke pad, which at 3 ft/px is nearly as wide as the arch itself and left a
        # 30 ft-pitch city avenue with almost no room to shorten.)
        floor_f = self.px(16.0) * 1.02 * (len(seats) - 1) / span if span else 1.0
        f = 1.0
        while f - 0.02 > floor_f:
            f -= 0.02
            if (short := fit(f)) is not None:
                return short
        raise ValueError(
            f"the torii avenue from ({seats[0][0]:.0f},{seats[0][1]:.0f}) cannot be shortened clear of "
            f"{torii_seat_on_wall(self.M, seats[0][0], seats[0][1], self.ftpx, runs) or 'a wall'} without closing the "
            f"arches up on each other - resite the hall or its approach in the gen so the sando has open ground to run in."
        )

    def _torii(self: Settlement, tx: float, ty: float, span_ft: float = 16.0) -> int:  # type: ignore[misc]
        """Draw ONE torii arch TRUE SCALE (GM 2026-07-21) and record it in M['torii']; returns the
        z-handle. `span_ft` is the TOP-RAIL span in real feet: a standard shrine/approach torii runs
        ~10-16 ft between its rail ends (grand landmark torii reach 30-50 ft, but none of our maps
        draws one). The old glyph was FIXED-PIXEL (38 px rail) - honest at 1 ft/px but 76 ft at
        village scale and 114 ft at city scale. Proportions keep the authored glyph's 38:24 rail:height
        ratio; STROKES keep a legibility floor (stroke convention - see SKILL.md "to scale"), never a
        footprint license."""
        wall = torii_seat_on_wall(self.M, tx, ty, self.ftpx)  # an arch never stands IN a barrier - see the wall_runs block
        if wall:
            raise ValueError(
                f"torii at ({tx:.0f},{ty:.0f}) would stand in {wall} - a torii is a freestanding gateway on open "
                f"ground, never set into a barrier (a way through a wall is a GATE). Move the arch clear; a shrine_hall "
                f"avenue shortens itself to fit, so a hand-placed arch is what lands here."
            )
        s2 = self.px(span_ft) / 2  # half the top-rail span; the glyph was authored at s2=19px
        c2, p2 = s2 * 16 / 19, s2 * 12 / 19  # crossbar half-span, post offset
        hz, hd = s2 * 7 / 19, s2 * 17 / 19  # rail rise above / post drop below the crossbar
        swr = max(self.px(1.4), 1.9)  # rail stroke (~1.4 ft beam, floored)
        swp = max(self.px(1.2), 1.6)  # post stroke (~1.2 ft post, floored)
        tz = self.add_top(
            f'<g transform="translate({tx:.0f},{ty:.0f})">'  # over any street it crosses
            f'<line x1="{-c2:.1f}" y1="0" x2="{c2:.1f}" y2="0" stroke="#A03020" stroke-width="{swr:.2f}"/>'
            f'<line x1="{-s2:.1f}" y1="{-hz:.1f}" x2="{s2:.1f}" y2="{-hz:.1f}" stroke="#A03020" stroke-width="{swr * 0.85:.2f}"/>'
            f'<line x1="{-p2:.1f}" y1="{-hz:.1f}" x2="{-p2:.1f}" y2="{hd:.1f}" stroke="#A03020" stroke-width="{swp:.2f}"/>'
            f'<line x1="{p2:.1f}" y1="{-hz:.1f}" x2="{p2:.1f}" y2="{hd:.1f}" stroke="#A03020" stroke-width="{swp:.2f}"/></g>'
        )
        self.M["torii"].append([round(tx, 1), round(ty, 1), tz])
        return tz

    def torii_path(self: Settlement, ascent: Any) -> None:  # type: ignore[misc]
        """Place one torii at each interior vertex of the ascent polyline; draw the
        winding path. Count is village-specific - pass as many points as torii+ends."""
        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for tx, ty in ascent[1:-1]:
            self._torii(tx, ty)

    def torii_even(self: Settlement, ascent: Any, count: int) -> None:  # type: ignore[misc]
        """Spread `count` torii by arc-length along an ascent polyline (Kikuta style)."""
        seg = [math.hypot(ascent[i + 1][0] - ascent[i][0], ascent[i + 1][1] - ascent[i][1]) for i in range(len(ascent) - 1)]
        tot = sum(seg)

        def along(t: float) -> Pt:
            target = t * tot
            acc: float = 0
            for i, sl in enumerate(seg):
                if acc + sl >= target:
                    f = (target - acc) / sl
                    return (ascent[i][0] + (ascent[i + 1][0] - ascent[i][0]) * f, ascent[i][1] + (ascent[i + 1][1] - ascent[i][1]) * f)
                acc += sl
            return cast(Pt, ascent[-1])  # pragma: no cover - defensive: t is capped at 0.86, never past the last segment

        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for i in range(count):
            tx, ty = along(0.06 + 0.80 * i / (count - 1))
            self._torii(tx, ty)

    def shrine_hall(  # type: ignore[misc]
        self: Settlement,
        x: float,
        y: float,
        label: Any,
        sublabel: str = "",
        w: float = 120,
        h: float = 82,
        torii: Any = None,
        primary: bool = False,
        edge: str = "#6B2A18",
        kind: str = "shrine",
        graveyard: bool = True,
        label_below: bool = False,
        torii_outlier: bool = False,
        torii_count: Any = None,
    ) -> None:
        """A standalone religious hall on flat ground. The kind follows settlement
        scale: villages have shrines, towns have monasteries, cities have temples
        (hamlets have none). primary=True marks the settlement's main one (M['shrine'],
        used by the torii checks). torii=[(x,y),...] defines the AVENUE LINE in front; the
        arch COUNT is rolled per temple on the tier's TORII_WEIGHTS column (seeded, so it is
        deterministic per map+hall), or pinned with torii_count=N - see the roll block below.
        graveyard=False marks a temple that hosts NO burial ground (a new or special-purpose
        hall, e.g. one founded in a former samurai estate) - city_temples_have_graveyards
        then exempts it; every other temple is expected to have a graveyard in its precinct.

        SCALE CONTRACT: `w`/`h` are DRAWN PIXELS, so at 1 ft/px (town) they equal real feet, but a
        coarser map MUST pass s.px(real_ft) - four city temples shipped as fixed 100x64 px = 300x192
        real ft before this was caught (audit 2026-07-21). The guard below refuses a hall whose
        implied real footprint exceeds any real main hall (the largest kondo runs ~150-190 ft;
        Tango's deliberate Daibutsuden-tier landmark is 200 ft) so unscaled px can't slip through."""
        if self.ftpx > 1 and max(w, h) * self.ftpx > 220:
            raise ValueError(f"shrine_hall {w}x{h}px at {self.ftpx} ft/px implies a {max(w, h) * self.ftpx:.0f} ft hall - pass s.px(real_ft), not raw pixels")
        n_t = 0
        seats_t: list[Pt] = []  # the DRAWN avenue - the caption below reads it to stay out of the sando
        if torii:
            # TORII COUNT IS ROLLED PER TEMPLE, the avenue list is GEOMETRY (GM 2026-07-23, the full
            # re-roll: the town/city gens hand-placed counts that predated the TORII_WEIGHTS table and
            # were never re-rolled - Tango/Nagahara sat at four 1s and a 3, a ~1%-likely draw under the
            # city column). `torii` now defines the avenue LINE (points marching AWAY from the hall);
            # the COUNT comes from a per-temple seeded roll on the tier table (deterministic in the map
            # seed + hall position), pinnable per temple via torii_count= (the per-hall analog of the
            # village 'torii_count' knob). Rolling more arches than points extends the avenue along its
            # own step (or away from the hall at a 44px stride for a single-point approach); rolling
            # fewer draws the first n. The resolved target is recorded on the religious rec as
            # 'torii_count' and gated by torii_match_roll, so a stale hand count can never ship again.
            n_t = (
                int(torii_count)
                if torii_count is not None
                else roll_torii_count(self.M.get("meta", {}).get("scale", "village"), random.Random(self.seed * 977 + int(round(x)) * 31 + int(round(y)) * 57))
            )
            pts_t = [(float(tpx), float(tpy)) for tpx, tpy in torii]
            if len(pts_t) < n_t:
                if len(pts_t) >= 2:
                    step_t = (pts_t[-1][0] - pts_t[-2][0], pts_t[-1][1] - pts_t[-2][1])
                else:
                    d_t = math.hypot(pts_t[0][0] - x, pts_t[0][1] - y) or 1.0
                    step_t = ((pts_t[0][0] - x) / d_t * self.px(TORII_PITCH_FT), (pts_t[0][1] - y) / d_t * self.px(TORII_PITCH_FT))
                while len(pts_t) < n_t:
                    pts_t.append((pts_t[-1][0] + step_t[0], pts_t[-1][1] + step_t[1]))
            # STRIDE, then THRESHOLD, then walls - and the threshold AGAIN. _avenue_short_of_walls
            # shortens a blocked run by scaling every seat's offset from the first arch, which pulls
            # the STRIDE in while leaving the threshold at the old, wider pitch; re-seating afterwards
            # is what keeps "the gap to the hall equals the gap between arches" true on a shortened
            # avenue too (Nagahara's Ebisu sando is the one that shortens). The second pass only ever
            # slides the run TOWARD the hall, over ground the first arch already stood clear of.
            seats_t = self._avenue_pitch(pts_t[:n_t])
            seats_t = self._avenue_short_of_walls(self._avenue_at_threshold(x, y, w, h, seats_t))
            seats_t = self._avenue_at_threshold(x, y, w, h, seats_t)
            for tx, ty in seats_t:
                s2 = self.px(16.0) / 2  # matches _torii's default true span
                # block the arch + a NEIGHBOR'S HALF-FOOTPRINT: packs test footprint centers, so the
                # margin must absorb half a house (~28 ft) + slack or a house's edge crosses the arch
                # (the old fixed 38px arch had this margin baked into its own oversize). Still kept
                # SMALLER than a street corridor so torii on a street don't shove the frontage houses.
                bm: float = self.px(28) + 4.0
                self.block_polys.append([(tx - s2 - bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty - s2 * 0.5 - bm), (tx + s2 + bm, ty + s2 + bm), (tx - s2 - bm, ty + s2 + bm)])
                self._torii(tx, ty)
                self._clear_ground(tx, ty + 2, max(2 * s2 + 4, 10), max(s2 * 1.3, 8), 30)  # a swept collar under the arch + its sando approach
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="{edge}" stroke-width="2"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<rect x="{x - w / 2:.0f}" y="{y + h / 2 - 9:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<line x1="{x - w / 2:.0f}" y1="{y:.0f}" x2="{x + w / 2:.0f}" y2="{y:.0f}" stroke="{edge}" stroke-width="0.7"/>')
        self.M["shrines"].append({"x": x, "y": y, "w": w, "h": h, "label": label})
        rec = {"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "sublabel": sublabel, "graveyard": graveyard, "torii_outlier": torii_outlier}
        if torii:
            rec["torii_count"] = n_t  # the resolved roll/pin target - torii_match_roll gates drawn == target
        self.M["religious"].append(rec)  # torii_outlier=True exempts this hall from torii_count_canonical (a deliberately non-numerological gate count, always with a recorded story)
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        # block a RECT + a building-half margin, at the map's grain (an ellipse undershot the hall
        # corners). The 22px FLOOR (added with the true-size halls, 2026-07-21): packs test footprint
        # CENTERS, so the margin must absorb the check's +4px pad plus half the largest urban neighbor
        # (~29px merchant_large) at ANY scale - at city grain the raw 34*bscale is only ~11px and let a
        # merchant seat its edge into the hall's pad.
        bm = max(34 * self.bscale, 22.0)
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm), (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        self._clear_ground(x, y, w, h, 58)  # the swept shrine precinct - scrub kept off the tended keidai (the grove, if any, is separate)
        if label:
            self.label(x, self._hall_caption_y(x, y, w, h, label, label_below, seats_t), label, HALL_CAPTION_FS, weight="bold", color=edge)
            # RESERVE the caption's own ground (GM 2026-07-27). Every gen that draws a hall had been
            # hand-writing a block_poly under its caption - Tango's Benten and Nagahara's Bishamon each
            # carry one, re-seated by hand every time the hall moved - and the moment _hall_caption_y
            # started choosing the side, those hand bands were reserving ground the caption had left.
            # A caption's band belongs to whoever knows where the caption went, which is here. The pad
            # absorbs half a dwelling, because block_polys is CENTRE-tested (CLAUDE.md, "CENTRE vs
            # FOOTPRINT"); the stale hand bands are now merely redundant, not wrong.
            _lb = self.M["labels"][-1]
            _lp = max(14 * self.bscale, 8.0)  # half a dwelling past the recorded box, which is already ~13% wider than the drawn glyphs
            self.block_polys.append([(_lb[0] - _lp, _lb[1] - _lp), (_lb[2] + _lp, _lb[1] - _lp), (_lb[2] + _lp, _lb[3] + _lp), (_lb[0] - _lp, _lb[3] + _lp)])
        if sublabel:
            self.label(x, y + h / 2 + 16, sublabel, 9, italic=True, color=edge)

    # ---- landscape / estate features
    def _tree_stand(self: Settlement, poly: Poly, seed: int, floor: Poly | None = None, outliers: bool = True) -> None:  # type: ignore[misc]
        """Fill `poly` with INDIVIDUAL TREES - the ONE way this engine draws a wood (GM 2026-07-25).

        A forest is NOT a terrain type here. It used to be drawn as a flat pale wash under a widely-
        spaced grid of identical dots, which read as patterned ground rather than as trees, and did
        not match how every other piece of vegetation on these maps is already drawn (the
        yashikirin, the fengshui belt, the dooryard copse - all real crowns, via _draw_grove). So a
        wood is now a STAND: every canopy tree is one drawn crown at true size and true spacing, and
        the polygon survives only as DATA (what it blocks, what it frames, where the brook comes
        from) - never as a shape you can see the outline of.

        DENSITY / SIZE - the why (research 2026-07-25; China-first per the setting's geography note,
        cross-checked against Japanese satoyama hill wood):
          - A closed premodern hill wood - the mixed broadleaf/conifer cover of a settled valley's
            back slope, cut over for fuel and timber on a rotation - carries roughly 500-800 CANOPY
            stems per hectare. 1 ha = 107,639 sq ft, so ~600 stems/ha is one canopy tree per ~180
            sq ft: a mean spacing near 13 ft. That is CANOPY_SPACING_FT.
          - Canopy crowns in such a stand run ~5-8 m across (16-26 ft), with occasional emergents
            wider. CANOPY_R_FT = 8.5 is the mean radius; each crown is jittered 0.75-1.4x, so drawn
            diameters land inside the real band, a few emergents over many smaller crowns.
          - Crowns of ~17 ft mean diameter on 13 ft centers OVERLAP, and that is the point: closure
            is what makes a wood a wood. Same finding as the mulberry rows (see _mulberry_rows) -
            at a to-scale grain the honest drawing of real planted density IS a packed mass of
            crowns, not sparse symbols spaced for the eye.
          - NOTHING is inflated for legibility. At 1 ft/px a crown is r ~6-12 px; at a coarser grain
            it shrinks with the map, exactly like the buildings do.
        The stand's EDGE is made by the trees themselves - there is no boundary stroke and the
        crowns are NOT clipped, so they break the outline the way a real wood does (a clipped stand
        reads as a ruled terrain boundary, which is the exact defect this replaced). `floor` is
        therefore drawn INSET from `poly` - its hard edge has to sit under the canopy - and
        `outliers` scatters a thinning fringe of advance growth on the cut-over margin outside.

        The FLOOR is drawn here; the CROWNS are QUEUED and drawn at crop time (flush_tree_stands),
        the same deferral the stable yards use. A wood is usually drawn EARLY - it is terrain, and
        the settlement is sited against it - but "no crown on a roof" can only be honored against
        buildings that already exist, and half the map is placed after the wood. Deferring the
        canopy alone (the litter floor stays down where it belongs, under everything) lets the
        filter see the COMPLETE map. Labels are unaffected: they live in the topmost layer."""
        # the FLOOR: shaded leaf litter and understory glimpsed between the crowns. Not a terrain
        # wash - under a closed canopy hardly any of it shows, and its outline is buried under the
        # trees whose centers stand inside it.
        d = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in (floor or poly)) + ' Z'
        self.add(f'<path d="{d}" fill="{self.FOREST_FLOOR}"/>')
        self._pending_stands.append((list(poly), seed, outliers))

    def flush_tree_stands(self: Settlement) -> None:  # type: ignore[misc]
        """Draw the canopy of every queued tree stand (see _tree_stand). Runs at CROP time, so each
        crown is tested against the COMPLETE map - every building and wellhead, not just the ones
        that happened to precede the wood - and a crown that would cover one is simply not drawn:
        the stand THINS around the structure instead of retreating from it. Deterministic (each
        stand re-seeds its own RNG, state saved/restored), so deferring ripples nothing. Idempotent;
        unit tests call it directly after forest()/forest_patch()."""
        pending = self._pending_stands
        self._pending_stands: list[tuple[Poly, int, bool]] = []
        for poly, seed, outliers in pending:
            self._draw_stand(poly, seed, outliers)

    def _draw_stand(self: Settlement, poly: Poly, seed: int, outliers: bool) -> None:  # type: ignore[misc]
        """One queued stand's canopy: the crowns inside `poly` plus (optionally) its fringe outside,
        each filtered so no tree is drawn on a roof or a wellhead."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        step = self.px(self.CANOPY_SPACING_FT)
        rad = self.px(self.CANOPY_R_FT)
        st = random.getstate()
        random.seed(seed)
        trees: list[tuple[float, float, float, str]] = []
        yy = min(ys)
        while yy <= max(ys) + step:
            xx = min(xs)
            while xx <= max(xs) + step:
                tx = xx + random.uniform(-step * 0.42, step * 0.42)
                ty = yy + random.uniform(-step * 0.42, step * 0.42)
                big = random.random() < 0.18
                kind = "conifer" if random.random() < 0.34 else "broadleaf"
                if point_in_poly(tx, ty, poly):
                    trees.append((tx, ty, rad * (random.uniform(1.05, 1.4) if big else random.uniform(0.75, 1.05)), kind))
                xx += step
            yy += step
        # no crown is drawn on a roof or a wellhead - and by flush time that means EVERY one of them
        reach = rad * 1.4
        krect, kcirc = self._canopy_keepouts((min(xs) - reach, min(ys) - reach, max(xs) + reach, max(ys) + reach))
        self.add(''.join(self._crowns([t for t in trees if not self._crown_covers(t[0], t[1], t[2], krect, kcirc, self.CANOPY_PAD)])))
        if outliers:
            self.add(''.join(self._crowns(self._stand_fringe(poly, step, rad, krect, kcirc))))
        random.setstate(st)

    def _stand_fringe(self: Settlement, poly: Poly, step: float, rad: float, krect: Any, kcirc: Any) -> list[tuple[float, float, float, str]]:  # type: ignore[misc]
        """The cut-over FRINGE of a wood: scattered advance growth thinning out past the tree line,
        kept off every bit of ground already spoken for. Advance growth comes in THICKETS, not as an
        even sprinkle, so a coarse position-seeded mask (~5 crowns across) decides which stretches of
        the margin have seeded at all and which have been kept clear by grazing and fuel-cutting.
        Each fringe tree becomes a block poly, so a later farmstead cannot land on it."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        band = step * 2.6
        out: list[tuple[float, float, float, str]] = []
        yy = min(ys) - band
        while yy <= max(ys) + band:
            xx = min(xs) - band
            while xx <= max(xs) + band:
                tx = xx + random.uniform(-step * 0.55, step * 0.55)
                ty = yy + random.uniform(-step * 0.55, step * 0.55)
                keep = random.random()
                kind = "conifer" if random.random() < 0.3 else "broadleaf"
                r = rad * random.uniform(0.55, 0.95)
                xx += step * 1.15
                if point_in_poly(tx, ty, poly):
                    continue
                gap = edge_dist(tx, ty, poly)
                thicket = 1.0 if self._hjit(round(tx / (step * 5)), round(ty / (step * 5)), 31.0) > 0.42 else 0.12
                if gap > band or keep > thicket * (1 - gap / band) ** 1.4:  # thins out with distance from the wood
                    continue
                if self._fringe_blocked(tx, ty, r) or self._crown_covers(tx, ty, r, krect, kcirc, self.CANOPY_PAD):
                    continue
                out.append((tx, ty, r, kind))
            yy += step * 1.7
        return out

    def _crowns(self: Settlement, trees: Sequence[tuple[float, float, float, str]]) -> list[str]:  # type: ignore[misc]
        """SVG for a set of (x, y, r, kind) canopy crowns, drawn back-to-front so the stand layers
        with depth. One circle per tree (plus a dark apex for a conifer) - the same two-tone crown
        the grove clumps use, so a wood and a windbreak read as the same kind of thing. Records every
        crown it emits (M['tree_crowns'])."""
        out: list[str] = []
        self._record_crowns([(t[0], t[1], t[2]) for t in trees])
        for tx, ty, r, kind in sorted(trees, key=lambda t: t[1]):
            col = "#4A6733" if kind == "conifer" else ("#6E8B43" if (int(tx) + int(ty)) % 2 else "#7C9A4E")
            out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{r:.1f}" fill="{col}" stroke="#3C5526" stroke-width="0.7"/>')
            if kind == "conifer":
                out.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{r * 0.4:.1f}" fill="#364D22" opacity="0.55"/>')
        return out

    def _fringe_blocked(self: Settlement, tx: float, ty: float, r: float) -> bool:  # type: ignore[misc]
        """Whether a fringe tree at (tx, ty) would land on ground already spoken for - anything
        blocking, a field or dry plot, open water, or a way. The wood's margin grows on waste
        ground, never in the crop or on the road."""
        if any(point_in_poly(tx, ty, b) for b in self.block_polys):
            return True
        if any(point_in_poly(tx, ty, f) or edge_dist(tx, ty, f) < r for f in self.field_polys + self.dry_polys):
            return True
        if self._on_watercourse(tx, ty, pad=r):
            return True
        return any(seg_dist(tx, ty, lp[k], lp[k + 1]) < buf + r for lp, buf in self._corridor_buffers() for k in range(len(lp) - 1))

    def forest(self: Settlement, west_edge: Any, label: str = "", label_xy: Any = None) -> None:  # type: ignore[misc]
        """A woodland filling east of an irregular tree-line to the canvas edge, drawn as a stand of
        INDIVIDUAL TREES (see _tree_stand for the density research). Blocks houses. Deterministic
        (RNG saved/restored) so it never perturbs house placement. The TREE LINE is recorded
        separately from the filled polygon because the frame reveals only a shallow band of wood
        past it (crop_to_content) - deeper in it is undifferentiated canopy, i.e. wasted image."""
        pts = list(west_edge) + [(self.W + 12, west_edge[-1][1]), (self.W + 12, west_edge[0][1])]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # the litter floor is pushed a crown's width BACK from the tree line (the canvas side stays
        # put) so its straight edge lies under the canopy and the trees alone make the wood's edge
        inset = self.px(self.CANOPY_R_FT)
        self._tree_stand(pts, seed=9, floor=[(x + inset, y) for x, y in west_edge] + pts[len(west_edge) :])
        self.block_polys.append(pts)
        self.M["forest"] = [[round(x, 1), round(y, 1)] for x, y in pts]
        self.M["forest_edge"] = [[round(x, 1), round(y, 1)] for x, y in west_edge]
        if label:
            lx, ly = label_xy if label_xy else (min(xs) + (self.W - min(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 14, italic=True, weight="bold", color="#22301A")
