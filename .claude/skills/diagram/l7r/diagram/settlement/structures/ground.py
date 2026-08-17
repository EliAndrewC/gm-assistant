"""Unbuilt GROUND SURFACES that reserve placement rather than structures that occupy it.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import random
from typing import TYPE_CHECKING, Any

from .._geom import (
    organic_bbox,
    organic_poly,
    point_in_poly,
    smooth_closed,
    smooth_points,
)

if TYPE_CHECKING:
    from ..core import Settlement


class GroundMixin:
    def road(self: Settlement, pts: Any, label: Any = None, width: float | None = None, label_xy: Any = None) -> None:  # type: ignore[misc]
        """A major road (e.g. an Imperial road) - a bordered roadbed. No-build corridor.
        Default real width 26 ft (an Imperial trunk highway; the historical Tokaido ran
        ~18-24 ft), converted at the map's ftpx and linework-floored.
        label_xy overrides the label anchor (default: the polyline midpoint). For a city the
        midpoint is the city CENTER, but the road label names the *Imperial* road, which is an
        Imperial responsibility only OUTSIDE the walls - inside, the same roadway is a city
        street the city maintains - so a city must pass label_xy a point beyond the gates."""
        if width is None:
            width = self.lw(26)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + max(32 * self.bscale, 17)))  # wide road -> larger building setback (at the map's grain, floored)
        if "road" not in self.M or self.M["road"] is None:
            self.M["road"] = [[x, y] for x, y in pts]  # the FIRST road stays the main road (back-compat
            self.M["road_width"] = width  # for the single-road checks/projections)
        self.M.setdefault("roads", []).append({"pts": [[x, y] for x, y in pts], "w": width})
        self.M["road_z"] = None
        self._ground(
            width,
            self.M,
            "road_z",
            edge=f'<path d="{dd}" fill="none" stroke="#9C7A40" stroke-width="{width}" opacity="0.9"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D8C49A" stroke-width="{width - 8}" opacity="1"/>',
            top=f'<path d="{dd}" fill="none" stroke="#8A6E3E" stroke-width="1.2" stroke-dasharray="12,10" opacity="0.6"/>',
        )
        if label:
            mid = pts[len(pts) // 2]
            lx, ly = label_xy if label_xy else (mid[0] + 46, mid[1] - 22)
            # DEFERRED to finish(): the label picks its side of the road by what is actually
            # built around it, and at road-draw time the map is still empty (GM label doctrine:
            # a label that can sit in empty ground, should; otherwise cover as little as possible)
            self._road_label: Any = (label, lx, ly)

    def pasture(self: Settlement, shape: Any, label: Any = None, amp: float = 40, label_xy: Any = None) -> None:  # type: ignore[misc]
        """Hayfield / grazing land (pastureland, around the barns) - open grass with
        the odd hay bale, distinct from the cultivated paddy fields. Blocks placement."""
        # SCOPED (2026-08-08): the pasture OUTLINE is stream-drawn (organic_bbox), and the fill
        # block below re-seeds only itself - so an upstream change reshaped the paddock, which
        # moved which sample points land inside it, which changed the draw sequence for
        # everything after. It was the FIRST divergence in a town, at draw #70 of 24,615.
        # Keyed on the shape, so a pasture re-rolls when the GM moves it and never otherwise.
        with self.rng_scope("pasture", *(shape if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape) else (len(shape), shape[0][0], shape[0][1]))):
            outline = organic_bbox(shape, amp) if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape) else organic_poly(shape, amp)
            sm = smooth_points(outline)
            d = smooth_closed(outline)
            cid = self._cid('past')
            self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
            self.add(f'<path d="{d}" fill="#C8CF92" stroke="#9CA86A" stroke-width="2" stroke-dasharray="7,5"/>')
            xs, ys = [p[0] for p in sm], [p[1] for p in sm]
            st = random.getstate()
            random.seed(15)
            self.add(f'<g clip-path="url(#{cid})">')
            yy = min(ys) + 14
            while yy < max(ys):
                xx = min(xs) + 14
                while xx < max(xs):
                    tx, ty = xx + random.uniform(-7, 7), yy + random.uniform(-7, 7)
                    if point_in_poly(tx, ty, sm):
                        if random.random() < 0.10:
                            self.add(f'<rect x="{tx - 6:.0f}" y="{ty - 4:.0f}" width="12" height="8" rx="3" fill="#D8C47E" stroke="#A98E54" stroke-width="0.7"/>')
                        else:
                            self.add(f'<path d="M{tx - 3:.0f},{ty + 2:.0f} L{tx:.0f},{ty - 4:.0f} L{tx + 3:.0f},{ty + 2:.0f}" fill="none" stroke="#8FA05E" stroke-width="0.8"/>')
                    xx += 26
                yy += 24
            self.add('</g>')
            random.setstate(st)
            self.block_polys.append(sm)
            self.M.setdefault("pastures", []).append([[round(p[0], 1), round(p[1], 1)] for p in sm])
            if label:
                lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
                self.label(lx, ly, label, 12, italic=True, color="#5C6B3A")
