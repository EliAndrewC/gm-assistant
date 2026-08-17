"""Where the candidate house seats COME FROM - the settlement-form seed generators and the perimeter ring.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Pt, _signed_area, segments_cross

if TYPE_CHECKING:
    from ..core import Settlement


class SeedFormsMixin:
    def line_seeds(self: Settlement, p0: Pt, p1: Pt, n: int, half_band: float, rng: random.Random, form: str = "linear", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds strung ALONG a line (feature 005 `settlement_form` = 'linear'): a RIBBON of homesteads
        fronting a road / field-margin / dike instead of a nucleated blob - historically the cheapest big
        structural difference between two same-region villages (research.md D5; a levee, a valley-edge track,
        or a canal bank strings the houses out). Distributes `n` seeds along the segment `p0`->`p1` (uniform
        along its length) with a perpendicular jitter up to +/-`half_band`; the bundle solver then hugs each
        homestead to the field edge as usual. Records `meta.settlement_form` when `record=True`."""
        if record:
            self.M["meta"]["settlement_form"] = form
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length  # unit perpendicular to the line
        out: list[Pt] = []
        for _ in range(n):
            t = rng.random()
            b = rng.uniform(-1.0, 1.0) * half_band
            out.append((x0 + dx * t + px * b, y0 + dy * t + py * b))
        return out

    def scatter_seeds(self: Settlement, cx: float, cy: float, rx: float, ry: float, n: int, rng: random.Random, form: str = "dispersed", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds scattered LOOSELY and evenly over a BROAD area (feature 005 `settlement_form`
        = 'dispersed'): scattered farmsteads, each its own yashikirin-groved homestead, rather than a tight
        nucleus - the kainyo / Tonami dispersed-farmstead pattern of the well-watered plains. Area-uniform
        over the ellipse so the farms spread out; `try_place`'s field-adjacency + no-build blockers then
        filter them onto the dry margins, leaving them dotted along the field edges instead of clumped.
        Records `meta.settlement_form`. Pair with `s._nucleated = False` so each farm draws its OWN grove."""
        if record:
            self.M["meta"]["settlement_form"] = form
        out: list[Pt] = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.random() ** 0.5  # area-uniform: an even scatter, not center-clumped
            out.append((cx + math.cos(a) * r * rx, cy + math.sin(a) * r * ry))
        return out

    def waterfront_seeds(self: Settlement, canal: Any, n: int, offset: float, rng: random.Random, form: str = "water_town", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds strung along BOTH banks of a canal (feature 005 `settlement_form` = 'water_town'): a
        Jiangnan-style water town where the houses FRONT the water, offset `offset` px to either side of the
        canal polyline. Records `meta.settlement_form`. (Per GM canon canals are a Lion-lands feature, so this
        form is typing-gated to Lion lands / a declared canal.) `try_place` then keeps each seed field-adjacent
        and off blockers, so the row packs cleanly along the waterfront."""
        if record:
            self.M["meta"]["settlement_form"] = form
        segs = [(canal[i], canal[i + 1]) for i in range(len(canal) - 1)]
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1.0
        out: list[Pt] = []
        for k in range(n):
            d = total * (k + 0.5) / n
            acc = 0.0
            for a, b in segs:
                ln = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + ln >= d:
                    t = (d - acc) / (ln or 1.0)
                    px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    nx, ny = -(b[1] - a[1]) / (ln or 1.0), (b[0] - a[0]) / (ln or 1.0)  # canal normal
                    side = 1.0 if k % 2 == 0 else -1.0  # alternate banks
                    out.append((px + nx * offset * side + rng.uniform(-10, 10), py + ny * offset * side + rng.uniform(-10, 10)))
                    break
                acc += ln
        return out

    def _perim_bbox(self: Settlement, bbox: Any, n: int, gap: float) -> list[Pt]:  # type: ignore[misc]
        x0, y0, x1, y1 = bbox
        bw, bh = x1 - x0, y1 - y0
        per = 2 * (bw + bh)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.18, 0.82)) / n * per
            if d < bw:
                x, y, nx, ny = x0 + d, y0, 0, -1
            elif d < bw + bh:
                x, y, nx, ny = x1, y0 + (d - bw), 1, 0
            elif d < 2 * bw + bh:
                x, y, nx, ny = x1 - (d - bw - bh), y1, 0, 1
            else:
                x, y, nx, ny = x0, y1 - (d - 2 * bw - bh), -1, 0
            g = gap + random.uniform(4, gap * 0.85)
            pts.append((x + nx * g + random.uniform(-10, 10), y + ny * g + random.uniform(-10, 10)))
        return pts

    def _perim_poly(self: Settlement, poly: Any, n: int, gap: float) -> list[Pt]:  # type: ignore[misc]
        area = _signed_area(poly)
        seglen = [math.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))]
        per = sum(seglen)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.2, 0.8)) / n * per
            acc: float = 0
            for i, sl in enumerate(seglen):
                if acc + sl >= d:
                    f = (d - acc) / sl if sl else 0
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % len(poly)]
                    px, py = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
                    dx, dy = x2 - x1, y2 - y1
                    L = math.hypot(dx, dy) or 1
                    nx, ny = (dy / L, -dx / L) if area > 0 else (-dy / L, dx / L)
                    gg = gap + random.uniform(4, gap * 0.85)
                    pts.append((px + nx * gg + random.uniform(-10, 10), py + ny * gg + random.uniform(-10, 10)))
                    break
                acc += sl
        return pts

    def ring(self: Settlement, shape: Any, n: int, gap: float, kinds: Any, max_big: int = 4) -> None:  # type: ignore[misc]
        """Ring a field with houses. shape: bbox tuple, or ('poly', smoothed_outline)."""
        # SCOPED (2026-08-08): _perim_bbox / _perim_poly jitter the ring's candidate SEATS from the
        # stream, so an upstream change moved every farmhouse a town rings its fields with - and the
        # yards, gardens, sheds and groves that hang off them. Keyed on the shape being ringed.
        with self.rng_scope("ring", *(shape[1][0] if isinstance(shape, tuple) and shape and shape[0] == "poly" else shape)):
            cand = self._perim_poly(shape[1], n, gap) if isinstance(shape, tuple) and shape and shape[0] == 'poly' else self._perim_bbox(shape, n, gap)
            # A ring farm must REACH the field it rings without crossing a ROAD (drives
            # farmsteads_reach_their_fields_unsevered; hoshizora's lone south-of-road farmhouse inside
            # the merchant block, GM 2026-08-02). ROADS only - a stream is crossed by footbridges (the
            # NW-bank farms are deliberate) and lanes/streets are village grain. FAMILY: association/
            # reach, deliberately center-based - the question is which side of the highway the steading
            # lives on, not a clearance. Reads the same M["roads"] record as the check.
            outline = shape[1] if isinstance(shape, tuple) and shape and shape[0] == 'poly' else [(shape[0], shape[1]), (shape[2], shape[1]), (shape[2], shape[3]), (shape[0], shape[3])]
            ring_roads = [r["pts"] for r in self.M.get("roads", [])]

            def _severed(hx: float, hy: float) -> bool:
                px, py = min(outline, key=lambda p: (p[0] - hx) ** 2 + (p[1] - hy) ** 2)
                return any(segments_cross((hx, hy), (px, py), rp[i], rp[i + 1]) for rp in ring_roads for i in range(len(rp) - 1))

            for x, y in cand:
                # POSITION-SEEDED, not a stream draw (2026-08-08). This one line was the whole reason a
                # town re-rolled when something unrelated changed upstream: the kind decides the
                # footprint, the footprint decides whether the homestead fits, and one different fit
                # cascades into every house, garden, yard, grove, well and tree crown on the map (13 of
                # hoshizora's 71 manifest keys, from ONE extra random draw at the top of the gen). Drawn
                # off the position, the ring is a function of where the field is, full stop. The ordering
                # note that used to sit above - keep the severed test AFTER this draw so the stream stays
                # identical - is moot now and has been deleted rather than maintained.
                k = kinds[int(self._hjit(x, y, 7.0) * len(kinds))]
                if ring_roads and _severed(x, y):
                    continue
                if k == "big":
                    if self._nbig >= max_big:
                        k = "plain"
                    else:
                        self._nbig += 1
                if not self.try_place(x, y, k) and k == "big":
                    self._nbig -= 1
