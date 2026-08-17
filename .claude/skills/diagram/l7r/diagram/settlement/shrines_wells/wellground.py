"""One question - is this ground fit to sink a wellhead in? - and everything that makes asking it cheap.

Split from settlement/shrines_wells.py by feature 116 - see settlement/shrines_wells/CLAUDE.md for the index.
"""

import contextlib
import math
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from .._geom import (
    PointGrid,
    paddy_wet_rings,
    point_in_poly,
    ring_touches,
    seg_dist,
)

if TYPE_CHECKING:
    from ..core import Settlement


class WellGroundMixin:
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
