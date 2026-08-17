"""Where travelers and their animals stop: the beds, the stalls, and the deferred draw that puts
the yards on the map last.

Split from settlement/civic_grounds.py by feature 115 - see settlement/civic_grounds/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    seg_dist,
)
from .._knobs import CITY_TIER_SCALES

if TYPE_CHECKING:
    from ..core import Settlement


class LodgingMixin:
    def _way_bearing_near(self: Settlement, x: float, y: float) -> tuple[float, float]:  # type: ignore[misc]
        """(distance, bearing-in-degrees) of the nearest WAY to (x, y) - road, street, lane or
        alley, including the primary road under its own manifest key. A roadside work is defined by
        the way it stands on, so its angle is DERIVED from that way at draw time rather than pinned:
        re-route the road and the flophouse turns with it (GM 2026-08-11, after every flophouse on
        every map came out level while the roads ran at 138-167 degrees)."""
        return self._way_seat_near(x, y)[2:]

    def _way_seat_near(self: Settlement, x: float, y: float) -> tuple[float, float, float, float]:  # type: ignore[misc]
        """(seat_x, seat_y, distance, bearing) of the nearest point on the nearest WAY. The seat is
        what lets a roadside work SNAP: a gen names roughly where the doss-house belongs and the
        engine puts it on the road, which is the only way the two stay together when the road moves."""
        best = (float("inf"), 0.0)
        seat = (x, y)
        lists: list[Any] = [self.M.get(k) or [] for k in ("roads", "streets", "town_streets", "lanes", "alleys")]
        polys = [r["pts"] for lst in lists for r in lst if isinstance(r, dict) and r.get("pts")]
        if self.M.get("road"):
            polys.append(self.M["road"])
        for pts in polys:
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                d = seg_dist(x, y, a, b)
                if d < best[0]:
                    best = (d, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
                    _dx, _dy = b[0] - a[0], b[1] - a[1]
                    _t = 0.0 if _dx == _dy == 0 else max(0.0, min(1.0, ((x - a[0]) * _dx + (y - a[1]) * _dy) / (_dx * _dx + _dy * _dy)))
                    seat = (a[0] + _t * _dx, a[1] + _t * _dy)
        return (seat[0], seat[1], best[0], best[1])

    def flophouse(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, label: str = "flophouse", label_below: bool = False, rot: Any = None) -> None:  # type: ignore[misc]
        """Real size ~104x46 ft (town-calibrated), converted at the map's ftpx.
        A large, plain communal lodging - a kichin-yado / market flophouse - where peasants
        who travel a long way to market day sleep on straw under a roof for a sen a night. It is
        BIGGER and PLAINER than a shophouse (no awning, a long dormitory of plain doorways), set
        where travelers arrive: the gate market of a walled town, the road of an unwalled one.
        Default-on for a town (town_has_flophouse); meta(flophouses=N) requires more. Records to
        M['flophouses'] and blocks houses - place it BEFORE any nearby pack/ring."""
        if w is None:
            w, h = self.px(104), self.px(46)
        if rot is None:
            # a doss-house FRONTS the road travelers arrive on - it exists to catch them - so it
            # lies along that road, and it SNAPS to it when the gen's hint lands adrift (GM
            # 2026-08-11: "the flophouse near the southwest gate is absurdly far from the road...
            # about three hundred feet, which seems absurd"). The gen says roughly where; the way
            # says exactly where, and the two cannot drift apart when the road is re-routed.
            # ROTATION ONLY - no snapping. Moving the seat here was tried and reverted: this method
            # runs before any collision test and has none of its own, so a pulled seat walked
            # doss-houses into streets, into standing terraces, and one into a quarter its own
            # siting rule forbids. The gen chooses the SPOT (with open_seat, which asks the
            # placer); the way chooses the ANGLE, which cannot collide with anything. A work with
            # no way within ~500 ft is not a roadside work and keeps its square default.
            _fd, _fb = self._way_bearing_near(x, y)
            rot = _fb if _fd < self.px(500) else 0.0
        rot = float(rot)
        if rot:
            self.add(f'<g transform="rotate({rot:.1f} {x:.1f} {y:.1f})">')
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#CDBE96" stroke="#5A4A30" stroke-width="2"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="10" fill="#7A6038"/>')  # long roof ridge
        self.add(f'<line x1="{x0:.0f}" y1="{y:.0f}" x2="{x0 + w:.0f}" y2="{y:.0f}" stroke="#5A4A30" stroke-width="0.7"/>')
        for dx in range(int(x0) + 14, int(x0 + w) - 10, 26):  # a row of plain doorways (a long dormitory)
            self.add(f'<rect x="{dx}" y="{y + h / 2 - 7:.0f}" width="9" height="7" fill="#5A4A30" opacity="0.8"/>')
        if rot:
            self.add("</g>")
        self.M["flophouses"].append({"x": x, "y": y, "w": w, "h": h, "rot": rot, "label": label})
        self.placed.append((x, y, w, h))
        bm = 30  # block a RECT + a building-half margin so dwellings keep clear, like the manor
        self.block_polys.append([(x0 - bm, y0 - bm), (x0 + w + bm, y0 - bm), (x0 + w + bm, y0 + h + bm), (x0 - bm, y0 + h + bm)])
        if label:
            self.label(x, y0 + h + 19 if label_below else y0 - 10, label, 11, italic=True, color="#5A4A30")

    def inn(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0) -> None:  # type: ignore[misc]
        """A prominent caravan INN - larger and grander than a flophouse, lodging the merchants, drivers
        and guards of the wagon-trains. Recorded in M['buildings'] (kind 'inn', non-residential). It
        FRONTS the road, so `rot` tilts it to lie PARALLEL to a diagonal road with its noren entrance
        (the +y front) FACING the roadbed. Blocks placement - place BEFORE any nearby pack.
        Real size ~66x48 ft (a large 2-story post-road inn), converted at the map's ftpx - as a
        fixed-px glyph it read 2.5x too big on a city map."""
        if w is None:
            w, h = self.px(66), self.px(48)
        hw, hh = w / 2, h / 2
        sf = h / 48  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#D9B98C" stroke="#5A3F1E" stroke-width="{max(2.2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{11 * sf:.1f}" fill="#7A5A30"/>',  # roof ridge
            f'<rect x="{-hw:.1f}" y="{hh - 4 * sf:.1f}" width="{w:.1f}" height="{4 * sf:.1f}" fill="#7A5A30" opacity="0.55"/>',
        ]  # lower eave (2-story)
        for i in range(3):  # upper-story lattice windows
            wx = -hw + w * (0.2 + 0.3 * i)
            g.append(f'<rect x="{wx:.1f}" y="{-hh + 14 * sf:.1f}" width="{10 * sf:.1f}" height="{7 * sf:.1f}" fill="#9A7E4E" stroke="#5A3F1E" stroke-width="0.6"/>')
            g.append(f'<line x1="{wx + 5 * sf:.1f}" y1="{-hh + 14 * sf:.1f}" x2="{wx + 5 * sf:.1f}" y2="{-hh + 21 * sf:.1f}" stroke="#D6C49A" stroke-width="0.6"/>')
        nx, nw = -w * 0.19, w * 0.38  # NOREN entrance curtain on the +y front
        g.append(f'<rect x="{nx:.1f}" y="{hh:.1f}" width="{nw:.1f}" height="{9 * sf:.1f}" rx="1" fill="#2E4A6B" stroke="#1E3450" stroke-width="0.6"/>')
        for k in (1, 2):
            g.append(f'<line x1="{nx + nw * k / 3:.1f}" y1="{hh:.1f}" x2="{nx + nw * k / 3:.1f}" y2="{hh + 9 * sf:.1f}" stroke="#C9D4E0" stroke-width="0.7"/>')
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "inn", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    def stables(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, rot: float = 0, yard: bool = True) -> None:  # type: ignore[misc]
        """A large STABLES - long rows of stalls for a wagon-train's many draft animals (oxen, horses).
        Recorded in M['buildings'] (kind 'stables', non-residential). Wants OPEN GROUND around it. `rot`
        tilts it to sit parallel to its inn / the road. Place BEFORE any nearby pack, but AFTER its
        cluster's inn + flophouse (so the yard, `yard=True`, skips them). Real size ~92x44 ft (stall rows
        for a full wagon-train), converted at the map's ftpx."""
        if w is None:
            w, h = self.px(92), self.px(44)
        hw, hh = w / 2, h / 2
        sf = h / 44  # glyph detail scales with the footprint
        g = [
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#B79A6E" stroke="#5A4326" stroke-width="{max(2 * sf, 1.0):.1f}"/>',
            f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{w:.1f}" height="{9 * sf:.1f}" fill="#6B4F2A"/>',
        ]  # roof ridge
        sx, step = -hw + 12 * sf, max(16 * sf, 6)  # stall divisions
        while sx < hw - 8 * sf:
            g.append(f'<line x1="{sx:.1f}" y1="{-hh + 9 * sf:.1f}" x2="{sx:.1f}" y2="{hh:.1f}" stroke="#6B4F2A" stroke-width="1.4" opacity="0.7"/>')
            sx += step
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "stables", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])
        # the working YARD is CITY-scope for now (its disk radius + furniture are calibrated for city
        # ftpx=3): a town's single caravan stables keeps its plain open ground until the yard is made
        # scale-aware. `yard=False` also suppresses it.
        if yard and self.M.get("meta", {}).get("scale") in CITY_TIER_SCALES:
            # QUEUED, not drawn (GM 2026-07-24): the yard scatter keeps its furniture off every
            # way and footprint it can SEE, but a stables placed early could not see the streets
            # drawn after it - so a heap landed on a later street (Nagahara wharf yard). Yards now
            # draw at crop time (flush_stable_yards, auto-run by crop_city), when the map is
            # complete - the same-data-as-the-checks doctrine (settlements.md, PLANK BRIDGES).
            self._pending_yards.append((x, y, w, h, 72.0, None))

    def animal_ground(self: Settlement, cx: float, cy: float, r: float = 68.0, label: Any = None) -> None:  # type: ignore[misc]
        """EXTRA interior ANIMAL / CARAVAN GROUND - a standalone stable-yard scatter (beaten earth,
        hitching rails, a trough, dung heaps) that CLAIMS an open pocket as
        deliberate working ground. This is the standing EASY REMEDY when city_no_large_empty_space
        flags unclaimed ground (GM 2026-07-23): where the bare pocket sits near a gate or the
        stables, more tie-up room for wagon-trains is the natural use - first applied to Tango's
        north gate, whose Phoenix-border traffic wants marshalling space for caravans coming down
        from (or departing toward) Phoenix lands. Draws the s._stable_yard scatter at (cx, cy) - it
        auto-avoids roads, streets, fields, water, the rampart, and every drawn footprint, so it
        fills only the genuinely open ground - and records M['stable_yards'], which the empty-space
        detector counts as claimed. The label (e.g. "caravan ground") is optional; the rails
        usually read on their own."""
        self._pending_yards.append((cx, cy, 0.0, 0.0, r, label))  # queued like the stables yards - drawn at crop time when every way exists (GM 2026-07-24)

    def flush_stable_yards(self: Settlement) -> None:  # type: ignore[misc]
        """Draw every queued stable-yard scatter (stables() gate yards + animal_ground() pockets).
        Runs at CROP time - crop_city calls it first - so the yard sees the COMPLETE map: every
        street/alley/ring road and every footprint, not just what happened to be drawn before the
        stables call (GM 2026-07-24: a wharf-yard dung heap landed on a street drawn later). The
        scatter's own seeded RNG makes the deferral ripple-free for every other feature; a late
        flush also means the watering point sees every real well, so the dig-your-own fallback
        fires only when the neighborhood genuinely has none in reach. Idempotent (drains the queue);
        unit tests call it directly after stables()/animal_ground()."""
        pending = self._pending_yards
        self._pending_yards: list[tuple[float, float, float, float, float, Any]] = []
        for sx, sy, sw, sh, r, label in pending:
            self._stable_yard(sx, sy, sw, sh, r=r)
            if label:
                self.label(sx, sy, label, 11, italic=True, color="#6B5A3C")
