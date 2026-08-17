"""One stable yard's shared state and the predicates its stages test against.

Split out of settlement/civic_grounds/stable_yard.py by feature 115 stage 2 - see
settlement/civic_grounds/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import (
    YARD_GLYPH_SLACK,
    Poly,
    Pt,
    point_in_poly,
    rail_quad,
    sat_overlap,
    seg_dist,
    trough_quad,
    wellhead_quad,
)

if TYPE_CHECKING:
    from ..core import Settlement


class _YardCtx:
    """One stable yard's shared state and the predicates every stage tests against.

    Before feature 115 these were eight closures inside a single 335-line `_stable_yard`, capturing
    a lattice of locals that made the method impossible to cut. Naming the lattice is the point of
    this class - the trough siter alone reads `clear` (built with the keep-outs) and `glyph_free`
    (which sees rails seated two stages earlier).

    **RNG CONTRACT - the one thing this refactor had to get right.** `_stable_yard` seeds the GLOBAL
    `random` stream and restores it at the end, and within a yard the output depends on the exact
    sequence of draws. There are only four draw sites in the whole yard: the seed, the litter
    scatter, `seat_init`'s shuffle, and the closing restore. Stages 4-7 (road rail, interior rails,
    watering, dung heaps) draw NOTHING - they consume candidates and map state.

    So: **`__init__` must consume zero RNG** (it is called before the litter scatter), and
    `seat_init` must be called at exactly one point - after the litter, before the first `take`.
    That single ordering fact is the whole hazard, and
    `test_yard_ctx_construction_draws_no_rng` pins the first half of it.
    """

    def __init__(self, s: Settlement, sx: float, sy: float, r: float) -> None:
        self.s = s
        self.sx, self.sy, self.r = sx, sy, r
        self.corridors = s._corridor_buffers(2.0)  # keep every glyph off the road/street tread
        # a TIGHT footprint keep-out (real drawn buildings only, ~3px margin so the beaten earth meets the
        # walls) - NOT the wide urban halo (which would leave a bare ring) and NOT block_polys (the reserved
        # pocket IS the yard). A rotated building is covered by its half-diagonal square.
        self.keep: list[tuple[float, float, float, float]] = []
        # "farriers" belongs here because the shoeing forge stands ON this yard by design (GM
        # 2026-07-25) - it is the one trade work sited INSIDE a stable yard, so without it the
        # scatter would speckle straw litter across the forge's apron and roof
        for k in (
            "buildings",
            "flophouses",
            "storehouses",
            "merchant_estates",
            "ministries",
            "religious",
            "manors",
            "cemeteries",
            "mausoleums",
            "cremation_grounds",
            "ossuaries",
            "houses",
            "farriers",
        ):
            for o in s.M.get(k, []) or []:
                ohw, ohh = o["w"] / 2, o["h"] / 2
                if o.get("rot"):
                    ohw = ohh = math.hypot(ohw, ohh)
                m = 3.0
                if o["x"] + ohw + m < sx - r - 50 or o["x"] - ohw - m > sx + r + 50 or o["y"] + ohh + m < sy - r - 50 or o["y"] - ohh - m > sy + r + 50:
                    continue  # +50 past the disc: the watering point may sit at a well just OUTSIDE the yard rim
                self.keep.append((o["x"] - ohw - m, o["y"] - ohh - m, o["x"] + ohw + m, o["y"] + ohh + m))

        self.wallp = s.M.get("wall")  # a yard near the rampart (a gate-side animal ground) must not speckle the wall or spill outside it
        # rails also seat SYMMETRICALLY clear of any EARLIER yard's dung heaps (GM 2026-07-25
        # round 2): the heap-vs-rail clearance below is map-wide, so a later yard must not lay
        # a rail into a neighboring yard's muck pile either - same 25px hold on the
        # heap-center-to-rail-line distance, measured against this candidate's drawn segment
        self.prior_heaps = [(h_["x"], h_["y"]) for yd_ in s.M.get("stable_yards", []) or [] for h_ in yd_.get("dung_heaps", []) or []]
        # WELLS, TROUGHS, AND HITCHING POSTS NEVER OVERLAP ONE ANOTHER (GM 2026-07-25; the full
        # reasoning sits with the quad builders at the top of this module and in settlements.md
        # 'Stable yard'). Each of the three is placed at a different moment, so every stage tests
        # the DRAWN extents of whatever already exists: a rail avoids every wellhead on the map,
        # the trough cluster avoids the rails, and the dug-your-own wellhead avoids both. Prior
        # yards count too - two yards can sit close enough to collide across the gap between them,
        # which is the same cross-yard lesson the dung-heap rule had to learn twice.
        self.prior_boxes = [yd_["troughs_box"] for yd_ in s.M.get("stable_yards", []) or [] if yd_.get("troughs_box")]
        self.prior_rails = [r_ for yd_ in s.M.get("stable_yards", []) or [] for r_ in yd_.get("rails", []) or []]

        self.cand: list[Pt] = []
        self.used: list[Pt] = []
        self.rails: list[dict[str, float]] = []
        self.heaps: list[dict[str, float]] = []
        self.wp: Pt | None = None
        self.n_troughs = 0
        self.troughs_box: list[float] | None = None

    def clear(self, px: float, py: float, pad: float = 0.0, rim: bool = True) -> bool:
        if rim and (px - self.sx) ** 2 + (py - self.sy) ** 2 > (self.r - pad) ** 2:
            return False  # rim=False for the well-side watering point, which may sit at/just past the disc edge
        wallp = self.wallp
        if wallp and (not point_in_poly(px, py, wallp) or any(seg_dist(px, py, wallp[i], wallp[i + 1]) < 9 for i in range(len(wallp) - 1))):
            return False
        if any(x0 <= px <= x1 and y0 <= py <= y1 for x0, y0, x1, y1 in self.keep):
            return False
        if any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hwid for i in range(len(pl) - 1)) for pl, hwid in self.corridors):
            return False
        if any(point_in_poly(px, py, ff) for ff in self.s.field_polys):
            return False
        return not self.s._on_watercourse(px, py)

    # 2. FURNITURE: greedily seated at clear spots on rings around the stables (deterministic order)
    def seat_init(self) -> None:
        """Build and SHUFFLE the furniture ring candidates.

        Called at exactly one point - after the litter scatter, before the first `take`. This is the
        yard's third and last RNG draw site; moving the call moves `random.shuffle` relative to the
        scatter's draws and changes every yard on every map. See the class docstring.
        """
        for rad in (32.0, 44.0, 56.0, 68.0):
            for i in range(12):
                aa = 2 * math.pi * i / 12 + rad  # per-ring phase offset so rings do not align
                self.cand.append((self.sx + rad * math.cos(aa), self.sy + rad * math.sin(aa)))
        random.shuffle(self.cand)

    def take(self, pad: float, minsep: float, probes: tuple[Pt, ...] = ((0.0, 0.0),)) -> Pt | None:
        # `probes` are offsets from the candidate that must ALL be clear - a rail or heap is
        # not a point, so its tips/edges are tested too (GM 2026-07-24: furniture off the
        # roads and the wall; a center-only test let an 18px rail lay its tip on the tread)
        for px, py in self.cand:
            if any((px - ux) ** 2 + (py - uy) ** 2 < minsep * minsep for ux, uy in self.used) or not all(self.clear(px + ox, py + oy, pad) for ox, oy in probes):
                continue
            self.used.append((px, py))
            return (px, py)
        return None

    def rail_rec(self, cx: float, cy: float, tx: float, ty: float) -> dict[str, float]:
        """The record a rail at this seat WOULD get - built before the rail is committed so a
        candidate can be tested at its true drawn extent (rail_quad) like everything else."""
        return {"x": round(cx, 1), "y": round(cy, 1), "tx": round(tx, 3), "ty": round(ty, 3), "len": 18.0, "reach": 2.4}

    def draw_hitch(self, cx: float, cy: float, tx: float, ty: float, nx: float, ny: float) -> None:
        length = 18.0
        self.rails.append(self.rail_rec(cx, cy, tx, ty))
        ex0, ey0 = cx - tx * length / 2, cy - ty * length / 2
        fg = [f'<line x1="{ex0:.1f}" y1="{ey0:.1f}" x2="{cx + tx * length / 2:.1f}" y2="{cy + ty * length / 2:.1f}" stroke="#6B4F2A" stroke-width="1.5"/>']
        for i in range(4):  # posts across the rail
            pxp, pyp = ex0 + tx * length * i / 3, ey0 + ty * length * i / 3
            fg.append(f'<line x1="{pxp - nx * 2.4:.1f}" y1="{pyp - ny * 2.4:.1f}" x2="{pxp + nx * 2.4:.1f}" y2="{pyp + ny * 2.4:.1f}" stroke="#5A4326" stroke-width="1.2"/>')
        self.s.add("".join(fg))

    def rail_clear_of_heaps(self, cx: float, cy: float, tx_: float, ty_: float) -> bool:
        return all(seg_dist(hx_, hy_, (cx - tx_ * 9.0, cy - ty_ * 9.0), (cx + tx_ * 9.0, cy + ty_ * 9.0)) >= 25.0 for hx_, hy_ in self.prior_heaps)

    def glyph_free(self, q: Poly, hug: Any = None) -> bool:
        """True when the drawn extent `q` overlaps no OTHER yard glyph (wellhead, trough
        cluster, hitching rail). Everything `q` is measured against is inflated by
        YARD_GLYPH_SLACK - except `hug`, the one wellhead a trough cluster deliberately stands
        beside, which is tested at TRUE extent: that bucket-pour gap is a deliberate ~1.5px and
        inflating it would shove the troughs away from the well they exist to be poured from."""
        if any(sat_overlap(q, wellhead_quad(w_, 0.0 if w_ is hug else YARD_GLYPH_SLACK)) for w_ in self.s.M.get("wells", []) or []):
            return False
        if any(sat_overlap(q, trough_quad(b_, YARD_GLYPH_SLACK)) for b_ in self.prior_boxes):
            return False
        return not any(sat_overlap(q, rail_quad(r_, YARD_GLYPH_SLACK)) for r_ in (*self.rails, *self.prior_rails))
