"""FIND a spot and commit to it: the spiral searches, the two compaction slides, the nucleated garden-side choice, the legacy per-house solver.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import Indexed, Pt

if TYPE_CHECKING:
    from ..core import Settlement


class PlacerMixin:
    def headman(self: Settlement, x: float, y: float, w: float = 92, h: float = 56) -> Any:  # type: ignore[misc]
        # `w`, `h` are in FEET (drawn at the map's ftpx, px(92) = 46px at 2 ft/px). A nanushi/shoya house is
        # the grandest in the village but still a house - ~92x56 ft, clearly larger than a plain 46x28 ft
        # farmhouse without the old fortress-sized 216x136 ft. headman_is_largest holds.
        if self._toscale():
            # the headman is just a LARGER PLAIN farmhouse - placed through the standard collision-checked
            # bundle path with a tunable SIZE, so it gets its yard + garden and cannot overlap a neighbor.
            # BOTH homestead styles route here (GM 2026-07-21, caught on Hikari no Sato): this guard used to
            # test _nucleated, so a DISPERSED to-scale village's headman fell through to the legacy rec below,
            # which _farmsteads_bundle draws as a LONE house (the abandoned-ruin path) - the grandest
            # farmstead in the village with no threshing yard and no garden. In the dispersed style the
            # bundle also brings the per-house grove when room allows; the solver drops it gracefully in a
            # dense cluster (neighbor tree cover shelters the house), which is the wanted behavior.
            # NO special reservation or "big"-glyph storeroom wing (that wing was drawn outside
            # the reserved footprint and overlapped the north neighbor's yard).
            return self.try_place(x, y, "plain", role="headman", size=(w, h))
        # non-to-scale tiers have no headman (a hamlet falls under the district headman, towns are run by
        # the magistrate - the *_has_no_headman checks), so the old legacy rec branch here was dead code
        # once the Hikari fix routed every to-scale style through the bundle; removed 2026-07-21.
        raise ValueError("headman() is a to-scale village feature - this map is not toscale")

    @staticmethod
    def _closest_on_seg(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> Pt:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return ax, ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        return ax + t * dx, ay + t * dy

    def _nearest_field_point(self: Settlement, cx: float, cy: float) -> Pt | None:  # type: ignore[misc]
        """The closest point on any paddy outline to (cx, cy) - the bund the grove will hug."""
        best: Pt | None = None
        bd = float("inf")
        for poly in self.field_polys:
            n = len(poly)
            for i in range(n):
                qx, qy = self._closest_on_seg(cx, cy, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1])
                d = (qx - cx) ** 2 + (qy - cy) ** 2
                if d < bd:
                    bd, best = d, (qx, qy)
        return best

    def _nearest_placed_point(self: Settlement, cx: float, cy: float) -> Pt | None:  # type: ignore[misc]
        """The center of the nearest already-placed homestead/house - the neighbor to pack against."""
        best: Pt | None = None
        bd = float("inf")
        for px, py, _pw, _ph, *_ in self.placed:
            d = (px - cx) ** 2 + (py - cy) ** 2
            if d < bd:
                bd, best = d, (px, py)
        return best

    def _slide(self: Settlement, cx: float, cy: float, hw: float, hh: float, target_fn: Any, grove_off_field: bool) -> Pt:  # type: ignore[misc]
        """Greedily shove the bundle toward target_fn (a field bund, then a neighbor) in small steps, as
        far as it still fits - the 'pack as close as the rules allow' step."""
        for _ in range(48):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if self._bundle_fits(self._bundle_geom(ncx, ncy, hw, hh), grove_off_field=grove_off_field):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle(self: Settlement, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:  # type: ignore[misc]
        """Place a homestead bundle one-at-a-time: find the nearest fitting spot to the seed, then COMPACT it
        - shove the grove up against the nearest paddy bund (without entering it), then pack the whole
        complex against its nearest neighbor, each as far as the rules allow. `shed` reserves a north kura in
        the bundle. Returns (cx, cy, geom) or None."""
        if getattr(self, "_nucleated", False):
            return self._place_bundle_nucleated(x, y, hw, hh, shed)
        offsets = [(0, 0)]
        for r in range(7, 92, 7):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._bundle_fits(self._bundle_geom(x + nx, y + ny, hw, hh)):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_field_point, grove_off_field=True)  # grove hugs the bund
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_placed_point, grove_off_field=True)  # pack against neighbor
        return cx, cy, self._bundle_geom(cx, cy, hw, hh)

    _NUC_SIDES = ("SE", "SW", "E", "W")  # garden-side preference: sunny south strip first, walls as fallback

    def _field_dist(self: Settlement, cx: float, cy: float) -> float:  # type: ignore[misc]
        """Distance from a point to the nearest paddy edge (inf if there are no fields)."""
        p = self._nearest_field_point(cx, cy)
        return math.hypot(cx - p[0], cy - p[1]) if p else float("inf")

    def _slide_nuc(self: Settlement, cx: float, cy: float, hw: float, hh: float, target_fn: Any, keep_field: bool = False) -> Pt:  # type: ignore[misc]
        """Shove a nucleated bundle toward target_fn as far as SOME garden side still fits - the tight-pack
        step (the garden side is re-chosen at the final spot, so the slide only needs one side to work).
        With keep_field, a move is ALSO rejected if it would drift the bundle FURTHER from the paddy than
        where it started: so the neighbor-pack runs ALONG the field edge (tangentially) and never pulls the
        cluster off the paddy - the village glues its field side to the paddy and builds outward in rows."""
        fd_cap: Any = self._field_dist(cx, cy) + 3 if keep_field else None
        for _ in range(80):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if keep_field and self._field_dist(ncx, ncy) > fd_cap:
                break
            if self._fits_any_side(ncx, ncy, hw, hh):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle_nucleated(self: Settlement, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:  # type: ignore[misc]
        """Nucleated placement: find the nearest spot where SOME garden side fits, pack it hard against the
        field bund then its neighbors, then pick the garden side that is UNSHADED and sunniest. The compact
        (grove-less) bundle lets the cluster nucleate; the adaptive garden gives sun + variety. `shed` reserves
        a north kura in every candidate bundle so a neighbor never lands on it."""
        offsets = [(0, 0)]
        for r in range(5, 80, 5):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._fits_any_side(x + nx, y + ny, hw, hh, shed):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide_nuc(cx, cy, hw, hh, self._nearest_field_point)  # hug the paddy edge
        cx, cy = self._slide_nuc(
            cx,
            cy,
            hw,
            hh,
            self._nearest_placed_point,  # then pack ALONG it (never off it),
            keep_field=True,
        )  # so the cluster glues to the paddy
        best: Any = None
        for rank, side in enumerate(self._NUC_SIDES):
            geom = self._bundle_geom(cx, cy, hw, hh, side, shed)
            if not self._bundle_fits(geom):
                continue
            score = (sum(self._garden_shaded(g) for g in geom["gardens"]), rank)  # fewest shaded beds first, then preference
            if best is None or score < best[0]:
                best = (score, geom)
        if best is None:  # pragma: no cover - the slide only rests where some garden side fits, so best is set
            return None
        return cx, cy, best[1]

    def _solve_homestead(self: Settlement, rec: Any) -> Any:  # type: ignore[misc]
        """Find the best position for a farmhouse so its WHOLE homestead fits - threshing yard + dooryard
        garden + room for a windward grove. Searches the placed spot first, then a widening spiral, and stops
        as soon as the home spot already leaves grove-room (no churn). Prefers a spot WITH grove-room, then the
        least displacement; falls back to a yard+garden-only spot if no grove-room is reachable nearby. Updates
        rec's position + reservation. Returns (yard_spot, garden_spot), or None if even yard+garden won't fit."""
        x0, y0, w, h = rec["x"], rec["y"], rec["w"], rec["h"]
        self.placed: list[Any] = Indexed(
            p for p in self.placed if p != (x0, y0, w, h)
        )  # lift own reservation while searching (Indexed, not a plain list - a rebind must not silently drop _fits' index into the uncached fallback)
        best: Any = None  # (has_grove_room, -displacement, cx, cy, spot)
        for nx, ny in self._farmstead_nudges():
            cx, cy = x0 + nx, y0 + ny
            if not self._fits(cx, cy, w, h) or not self._field_adjacent(cx, cy):
                continue
            spot = self._find_appurtenances(cx, cy, w, h, rec["rot"], rec["kind"], rec["shed"], rec["wealth"])
            if spot is None:
                continue
            wf = rec["wealth"]  # the grove is drawn at the WEALTH size, so reserve room for THAT
            cand = (self._grove_room(cx, cy, w * wf, h * wf), -(abs(nx) + abs(ny)), cx, cy, spot)
            if best is None or cand[:2] > best[:2]:
                best = cand
            if cand[0] and nx == 0 and ny == 0:
                break  # already perfect at the home spot
        cx, cy = (best[2], best[3]) if best else (x0, y0)
        rec["x"], rec["y"] = cx, cy
        self.placed.append((cx, cy, w, h))  # re-reserve at the chosen (or original) spot
        return best[4] if best else None
