"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any

from ._geom import _union_area, boxed_seg_hit, edge_dist, point_in_poly, seg_dist

if TYPE_CHECKING:
    from .core import Settlement


class HomesteadPartsMixin:
    def _draw_threshing_yard(self: Settlement, cx: float, cy: float, w: float, h: float, poly: Any) -> None:  # type: ignore[misc]
        """Draw one small tamped earthen threshing/drying yard (a straw mat + a little hazakake rack). The
        outer footprint is a slightly-irregular quad (`poly`, absolute corner coords) - a swept work surface
        stays NEAR-square; interior detail is laid out in the local (w,h) frame."""
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        pts = " ".join(f"{px - cx:.1f},{py - cy:.1f}" for px, py in poly)
        g.append(f'<polygon points="{pts}" fill="#D2BE94" stroke="#A98E54" stroke-width="1.5"/>')  # tamped earthen floor
        g.append(f'<rect x="{x0 + 3:.0f}" y="{y0 + 3:.0f}" width="{w - 6:.0f}" height="{h - 6:.0f}" rx="1.5" fill="none" stroke="#BBA06E" stroke-width="0.7" opacity="0.6"/>')  # swept rim
        g.append('<rect x="-7" y="-6" width="14" height="9" rx="1" fill="#E2D2A2" stroke="#A98E54" stroke-width="0.6" opacity="0.9"/>')  # a straw drying mat
        ry = h / 2 - 3  # a little drying rack (hazakake) along the floor's lower edge
        g.append(f'<line x1="{x0 + 4:.1f}" y1="{ry:.1f}" x2="{-x0 - 4:.1f}" y2="{ry:.1f}" stroke="#7A5A30" stroke-width="1.2"/>')
        g.append(f'<line x1="{x0 + 4:.1f}" y1="{ry - 3:.1f}" x2="{-x0 - 4:.1f}" y2="{ry - 3:.1f}" stroke="#7A5A30" stroke-width="1.0"/>')
        for px in (x0 + 4, 0.0, -x0 - 4):  # posts + a few hung sheaves
            g.append(f'<line x1="{px:.1f}" y1="{ry - 5:.1f}" x2="{px:.1f}" y2="{ry + 3:.1f}" stroke="#5A3F1E" stroke-width="1.2"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _yard_fits(self: Settlement, x: float, y: float, w: float, h: float, hx: float, hy: float) -> bool:  # type: ignore[misc]
        """A threshing yard fits where it is in-bounds, on DRY ground (clear of paddies / blocks),
        off any lane, and clear of every placed footprint EXCEPT its own farmhouse (it abuts that)."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        if self._rect_hits((x, y, w, h), self.dry_polys):  # hem strips / garden tracts are cropland too -
            return False  # the yard footprint stays off them, same as the house test in _fits (GM, Tango hems)
        r = math.hypot(w, h) / 2
        for poly in self.field_polys:  # keep the whole DRY footprint out of every paddy
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < r + 4:
                return False
        # ...AND ASK THE QUESTION THE CHECK ASKS, OF THE SOURCE THE CHECK READS (cohort seed 31,
        # 2026-08-18). The loop above is a CENTRE-and-circle test against `field_polys`, which holds
        # the smoothed ENVELOPE; `harvest_yards_clear_of_paddies` is a CORNER test against each
        # paddy's own recorded `outline`. Two sources and two geometries, so they can disagree - and
        # on seed 31 they did: a yard cleared the envelope by its circle and still put a corner at
        # (2024, 1908) inside a drawn basin. This is the same defect shape as the woodland scan
        # mirroring its check's formula but not its window, fixed earlier the same day; the standing
        # rule is that placement and its check read ONE source.
        _fo = [f["outline"] for f in self.M.get("fields", []) if f.get("kind") == "paddy" and f.get("outline")]
        if _fo:
            _cn = [(x + sx * w / 2, y + sy * h / 2) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]
            for _ol in _fo:
                if any(point_in_poly(_px, _py, _ol) for _px, _py in _cn):
                    return False
                if any(-w / 2 <= _vx - x <= w / 2 and -h / 2 <= _vy - y <= h / 2 for _vx, _vy in _ol):
                    return False  # ...and the other direction: a basin vertex inside the yard, which the check also tests
        for px, py, pw, ph, *_ in self.placed:
            if px == hx and py == hy:  # the yard abuts its OWN farmhouse - allowed
                continue
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 2:
                return False
        return True

    def _yard_dims(self: Settlement, hw: float, hh: float) -> tuple[float, float]:  # type: ignore[misc]
        """PREVIEW: yard scaled to the (now smaller) house, capped so the big headman keeps an ordinary yard."""
        return min(0.73 * hw, 32 * self.bscale), min(0.69 * hh, 20 * self.bscale)

    def _find_yard_spot(self: Settlement, hx: float, hy: float, hw: float, hh: float) -> tuple[float, float, float, float] | None:  # type: ignore[misc]
        """The first fitting threshing-yard position for a farmhouse: the sunny SOUTH/front side (+y) is
        the maeniwa; fall back to the E/W sides if the paddy blocks due-south, but NEVER the shady north
        back. Returns (ox, oy, yw, yh) or None if the farmstead is boxed in on all three sides."""
        yw, yh = self._yard_dims(hw, hh)
        for dx, dy in ((0, 1), (1, 0), (-1, 0)):
            ox = hx + dx * (hw / 2 + yw / 2 - 2)
            oy = hy + dy * (hh / 2 + yh / 2 - 2)
            if self._yard_fits(ox, oy, yw, yh, hx, hy):
                return ox, oy, yw, yh
        return None

    def _attach_yard(self: Settlement, hx: float, hy: float, spot: Any) -> None:  # type: ignore[misc]
        """Draw a farmstead's threshing/drying yard (it is drawn BEFORE its house, so the house renders on
        top of the overlap) and record it. The work yard was UNIVERSAL, so every farmhouse gets one. Its
        footprint is a SLIGHTLY-irregular quad (a swept work surface stays near-square: small jitter),
        inscribed in the reserved rect so it can never breach the collision the rect already cleared."""
        ox, oy, yw, yh = spot
        poly = self._quad(ox, oy, yw, yh, 0.10, 41.0)
        self._draw_threshing_yard(ox, oy, yw, yh, poly)
        self.M["threshing_yards"].append({"x": round(ox, 1), "y": round(oy, 1), "w": yw, "h": yh, "rot": 0, "of": [hx, hy], "poly": [[round(px, 1), round(py, 1)] for px, py in poly]})
        self.placed.append((ox, oy, yw, yh))

    def _draw_garden(self: Settlement, cx: float, cy: float, w: float, h: float, poly: Any) -> None:  # type: ignore[misc]
        """Draw one small dooryard KITCHEN GARDEN (saien): a tilled earthen bed with tidy planted rows
        of greens. Distinct from the tan threshing yard (bare swept earth) and the blue-green paddy quilt.
        The bed's outer footprint is an irregular quad (`poly`, absolute corner coords) - a hand-worked plot
        bent to paths and soil, not surveyed square; the rows are laid out in the local (w,h) frame."""
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        pts = " ".join(f"{px - cx:.1f},{py - cy:.1f}" for px, py in poly)
        g.append(f'<polygon points="{pts}" fill="#B49A62" stroke="#6E5A30" stroke-width="1.3"/>')  # tilled bed
        nrows = 3
        for i in range(nrows):  # rows of greens running along the bed
            ry = y0 + h * (i + 0.5) / nrows
            g.append(f'<line x1="{x0 + 3:.1f}" y1="{ry:.1f}" x2="{-x0 - 3:.1f}" y2="{ry:.1f}" stroke="#6E9A40" stroke-width="2.4" stroke-linecap="round"/>')
            for k in range(3):  # a few leafy plants dotted along each row
                px = x0 + 4 + (w - 8) * (k + 0.5) / 3
                g.append(f'<circle cx="{px:.1f}" cy="{ry:.1f}" r="1.7" fill="#83B255"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _garden_dims(self: Settlement, hw: float, hh: float) -> tuple[float, float]:  # type: ignore[misc]
        """PREVIEW: garden scaled to the (now smaller) house, capped."""
        return min(0.55 * hw, 24 * self.bscale), min(0.55 * hh, 16 * self.bscale)

    def _farm_shed_rect(self: Settlement, hx: float, hy: float, hw: float, hh: float, rot: float, kind: str, shed: Any) -> tuple[float, float, float, float] | None:  # type: ignore[misc]
        """The footprint of a plain farmhouse's attached STOREHOUSE/shed (kura), drawn as a sub-glyph on
        the house's WEST side (local -x), or None if it has none. Derived here (the shed is not a separate
        recorded struct) so the garden can be kept OFF it - shed and garden sit on opposite sides."""
        if not (shed and kind == "plain"):
            return None
        th = math.radians(rot)
        lx = -0.64 * hw  # shed center in the house's local frame (west side)
        return (hx + lx * math.cos(th), hy + lx * math.sin(th), 0.32 * hw, 0.56 * hh)

    def _garden_fits(self: Settlement, x: float, y: float, w: float, h: float, hx: float, hy: float, yard: Any, shed_rect: Any = None) -> bool:  # type: ignore[misc]
        """A garden fits where it is in-bounds, on DRY ground (clear of paddies / blocks), off any lane,
        clear of every placed footprint EXCEPT its own farmhouse, clear of that farmhouse's YARD, and clear
        of its SHED (the yard, shed, and garden all sit on different sides of the house, never overlapping)."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        r = math.hypot(w, h) / 2
        for poly in self.field_polys:  # a kitchen garden is dry ground, off the paddies
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < r + 4:
                return False
        if math.hypot(x - yard[0], y - yard[1]) < r + math.hypot(yard[2], yard[3]) / 2 + 2:
            return False  # not on top of this house's own threshing yard
        if shed_rect and math.hypot(x - shed_rect[0], y - shed_rect[1]) < r + math.hypot(shed_rect[2], shed_rect[3]) / 2 + 2:
            return False  # not on top of this house's own storehouse/shed (its west side)
        for px, py, pw, ph, *_ in self.placed:
            if px == hx and py == hy:  # the garden abuts its OWN farmhouse - allowed
                continue
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 2:
                return False
        return True

    def _find_garden_spot(self: Settlement, hx: float, hy: float, hw: float, hh: float, yard: Any, shed_rect: Any = None, wealth: float = 1.0) -> tuple[float, float, float, float] | None:  # type: ignore[misc]
        """The first fitting kitchen-garden position: a sunny SIDE, preferring the EAST (the kitchen/doma
        end, where the cook steps out to it), then the sunny SE/SW corners, and the windward WALL itself
        LAST - NEVER the shady north back, and never the south front (the threshing yard's apron) nor the west
        shed. The grove's belt sits on the windward WALL (the W face for the default NW wind), so the garden
        takes that wall only as a last resort - the windward CORNER (SW) is still fine, it tucks below the
        grove's arm. Keeping the garden off the windward wall is what frees it for the grove (a garden there
        was the #1 reason a windward arm went missing - e.g. a farm whose EAST faces the paddy). Spot or None."""
        gw, gh = self._garden_dims(hw * wealth, hh * wealth)  # PREVIEW: richer farm -> bigger garden
        wx = self._windward_x()  # windward horizontal sign (-1 W / +1 E / 0)
        wall = (wx, 0) if wx else None  # the windward wall the grove's belt wants
        sides = [(1, 0), (-1, 0), (1, 1), (-1, 1)]
        # try EVERY non-windward-wall side first - flush AND a little further out (to slip the garden past the
        # south yard into the windward CORNER) - and the windward wall itself only as a last resort, so an
        # E-paddy farm puts its garden in the SW corner and leaves the W wall free for the grove
        cands = [(dx, dy, e) for dx, dy in sides if (dx, dy) != wall for e in (0, 15 * self.bscale, 30 * self.bscale)]
        if wall:
            cands += [(wall[0], wall[1], e) for e in (0, 15 * self.bscale)]
        for dx, dy, extra in cands:
            ox = hx + dx * (hw / 2 + gw / 2 - 2 + extra)
            oy = hy + dy * (hh / 2 + gh / 2 - 2)
            if self._garden_fits(ox, oy, gw, gh, hx, hy, yard, shed_rect):
                return ox, oy, gw, gh
        return None

    def _attach_garden(self: Settlement, hx: float, hy: float, beds: Any) -> None:  # type: ignore[misc]
        """Draw a farmstead's dooryard kitchen garden BED(S) (before its house, so the house wins any abutment)
        and record them. The kitchen garden was a household staple, so every farmhouse gets one - but the plot
        is occasionally FRAGMENTED into two beds (`_garden_beds` decides where: flanking opposite walls, stacked,
        or side-by-side). `beds` is the reserved-and-collision-checked list of (cx,cy,w,h) rects from the bundle
        geometry; all beds of one house carry the same `of` parent, so `gardens_present` counts one garden per
        house and `garden_area_within_norms` sums their areas. Each bed is drawn as a slightly-irregular hand-
        worked quad (real dooryard beds were bent to paths and soil, not surveyed square); a lone bed can be more
        irregular than a split strip."""
        jit = 0.18 if len(beds) == 1 else 0.13
        for i, (bx, by, bw, bh) in enumerate(beds):
            poly = self._quad(bx, by, bw, bh, jit, 71.0 + i * 5.0)
            self._draw_garden(bx, by, bw, bh, poly)
            self.M["gardens"].append({"x": round(bx, 1), "y": round(by, 1), "w": bw, "h": bh, "rot": 0, "of": [hx, hy], "poly": [[round(px, 1), round(py, 1)] for px, py in poly]})
            self.placed.append((bx, by, bw, bh))

    # the windward faces a homestead grove (yashikirin) shelters, by where the prevailing cold wind comes
    # FROM (its compass key). The grove is an L-BELT: a deep stand on each windward face (for a diagonal
    # like NW, an N arm + a W arm wrapping the corner; for a cardinal, one deep band). Default NW - the
    # East Asian winter monsoon (the Siberian high) blows NW across China AND Japan, so N+W is windward and
    # the S/E is the sheltered, sunny side. A map keys it off its geography with meta(windward=...). Each
    # arm is (face, perp): `face` is the cardinal it sits on; `perp` is the sign the N/S arm extends along
    # to wrap the corner (0 for a lone cardinal arm). See settlements.md 'Homestead groves'.
    _GROVE_ARMS = {
        "NW": [((0, -1), -1), ((-1, 0), 0)],
        "NE": [((0, -1), 1), ((1, 0), 0)],
        "SW": [((0, 1), -1), ((-1, 0), 0)],
        "SE": [((0, 1), 1), ((1, 0), 0)],
        "N": [((0, -1), 0)],
        "S": [((0, 1), 0)],
        "E": [((1, 0), 0)],
        "W": [((-1, 0), 0)],
    }

    def _windward(self: Settlement) -> str:  # type: ignore[misc]
        """The map's prevailing-wind compass key (where the cold wind blows FROM), default NW."""
        w = str(self.M["meta"].get("windward", "NW")).upper().strip()
        return w if w in self._GROVE_ARMS else "NW"

    def _windward_x(self: Settlement) -> int:  # type: ignore[misc]
        """The horizontal sign of the windward direction: -1 if the wind is from the W (NW/W/SW), +1 if from
        the E (NE/E/SE), 0 for a due N/S wind. Used to keep the garden off the windward wall (the grove's side)."""
        wk = self._windward()
        return -1 if "W" in wk else (1 if "E" in wk else 0)

    def _grove_candidate(self: Settlement, hx: float, hy: float) -> bool:  # type: ignore[misc]
        """Whether this farmhouse is a grove candidate. UNIVERSAL by default (the yashikirin ringed every
        dispersed farmstead, so a grove is drawn wherever there is windward room); meta(grove_prevalence=N<1)
        dials it down for an atypical/sheltered microclimate. Deterministic in the house position (stable
        across regenerations, RNG-independent)."""
        rate = float(self.M["meta"].get("grove_prevalence", 1.0))
        return rate >= 1.0 or int(abs(hx) * 31 + abs(hy) * 17) % 100 < rate * 100

    def _grove_arm_rect(self: Settlement, hx: float, hy: float, hw: float, hh: float, fdx: float, fdy: float, perp: float, d: float, gap: float, lf: float = 1.0) -> tuple[float, float, float, float]:  # type: ignore[misc]
        """One belt ARM's footprint (cx, cy, w, h), depth `d`, just outside the house wall it shelters. An
        N/S arm runs E-W as wide as the house plus `d` (extending `perp` toward the windward corner so the
        two arms wrap it); an E/W arm runs N-S as tall as the house. The depth `d` is how many trees deep the
        stand is - sized so the whole grove is the LARGEST homestead appurtenance (bigger than the house);
        `lf` shortens the arm's run to slip a partial belt past a close neighbor. See settlements.md 'Homestead
        groves' (Historical scale)."""
        if fdy:  # N or S arm (runs E-W); wraps `perp` toward the windward corner
            return hx + perp * d / 2, hy + fdy * (hh / 2 + d / 2 + gap), (hw + d) * lf, d
        return hx + fdx * (hw / 2 + d / 2 + gap), hy, d, hh * lf  # E or W arm (runs N-S)

    def _grove_fits(self: Settlement, x: float, y: float, w: float, h: float, own: Any) -> bool:  # type: ignore[misc]
        """A grove fits where it is in-bounds, on DRY ground (trees do not grow IN a flooded paddy - but a real
        homestead grove HUGS the paddy bund, so the footprint may abut a field, it just may not overlap it),
        off any lane, and clear of every placed footprint EXCEPT its OWN house. Axis-aligned, so an exact AABB
        test serves - not the conservative half-diagonal circle, which would over-reject the elongated bands."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._near_corridor(x, y):  # NOT `_in_blocked`: a grove may sit right at the
            return False  # paddy edge (the 14px field set-back is for buildings, not the windbreak)
        if self._rect_hits((x, y, w, h), self.field_polys):  # the whole grove stays OUT of the flooded paddy
            return False  # (same corner/vertex/edge test, with the bbox pre-filter)
        if self._rect_hits((x, y, w, h), self.dry_polys):  # ...and out of the dry crop strips (hems / garden
            return False  # tracts): trees do not grow in the barley either
        for px, py, pw, ph, *_ in self.placed:  # clear of every footprint but its OWN homestead
            if any(abs(px - ox) < 1.5 and abs(py - oy) < 1.5 for ox, oy in own):
                continue
            if abs(x - px) < (w + pw) / 2 + 2 and abs(y - py) < (h + ph) / 2 + 2:
                return False
        # the town RAMPART blocks a belt arm at the FOOTPRINT level: the corridor test above is
        # center-only, so a wide arm centered clear of the wall could still lap the stroke
        # (first hit: a Hirameki farm's west arm crossing the east face, 2026-07)
        wallp = self.M.get("wall")
        if wallp and any(
            seg_dist(gx, gy, wallp[k], wallp[k + 1]) < 12 for gx, gy in ((x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)) for k in range(len(wallp) - 1)
        ):
            return False
        # a threshing yard needs clear sky to its SOUTH (the drying sun); a grove squarely in that sun-corridor
        # would shade it, so keep the grove out of the narrow strip directly south of any yard. (Its OWN grove
        # is N/W, far from its own yard's southern corridor, so this only steers it off a NEIGHBOR's yard.)
        for yd in self.M.get("threshing_yards", []):
            cyx, cyy = yd["x"], yd["y"] + yd["h"] / 2 + 11  # corridor center: a ~22px-deep strip south of the yard
            if abs(x - cyx) < (w + yd["w"]) / 2 and abs(y - cyy) < (h + 22) / 2:
                return False
        return True

    GROVE_RATIO = 6.0  # target grove footprint as a multiple of the house (~6:1 - see settlements.md Historical scale)

    def _find_grove_arms(self: Settlement, hx: float, hy: float, hw: float, hh: float) -> list[Any]:  # type: ignore[misc]
        """The windward grove's belt arms, AREA-TARGETED to ~GROVE_RATIO x the house footprint (the historical
        ~6:1). Each windward face (N + W for an NW wind) is grown to the deepest belt that fits; if the total
        still falls short of target - because a paddy or neighbor blocks one face - the OTHER, open arm is
        deepened to compensate, so a typical farm's grove still reaches the full ~6:1 and reads as ~40 trees.
        A farm boxed in on BOTH windward faces gets only what fits (a small grove - the genuinely cramped
        minority). Arms are NOT in `placed`, so adjacent groves abut into one continuous windbreak. Returns a
        list of (cx, cy, w, h, face)."""
        target = self.GROVE_RATIO * hw * hh
        own = [(hx, hy)]
        d0 = 1.4 * hh  # base belt depth; the loop deepens to hit the area target
        dcap = 3.6 * hh  # an open arm may deepen this far to cover a blocked one
        dmin = 12 * self.bscale
        step = max(2.0, 0.16 * hh)
        depths: list[Any] = []  # [[(fdx,fdy), perp, depth], ...]
        for (fdx, fdy), perp in self._GROVE_ARMS[self._windward()]:
            d = d0
            placed_arm = False
            while d >= dmin:  # deepest full-width arm <= d0 that fits this face
                cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5)
                if self._grove_fits(cx, cy, w, h, own):
                    depths.append([(fdx, fdy), perp, d, 1.0])
                    placed_arm = True
                    break
                d -= step
            if not placed_arm:  # tight face: a NARROW clump still reads as a windbreak
                d = d0
                while d >= dmin:
                    cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, 0.55)
                    if self._grove_fits(cx, cy, w, h, own):
                        depths.append([(fdx, fdy), perp, d, 0.55])
                        break
                    d -= step

        def total_area() -> float:
            rects = [self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, lf) for (fdx, fdy), perp, d, lf in depths]
            return _union_area([(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2) for cx, cy, w, h in rects])

        guard = 0
        while depths and total_area() < target and guard < 300:  # compensate: deepen the open arm(s)
            grew = False
            for arm in depths:
                if arm[2] >= dcap:
                    continue
                nd = min(dcap, arm[2] + step)
                cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, arm[0][0], arm[0][1], arm[1], nd, 1.5, arm[3])
                if self._grove_fits(cx, cy, w, h, own):
                    arm[2] = nd
                    grew = True
                    if total_area() >= target:
                        break
            if not grew:
                break
            guard += 1
        return [(*self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, d, 1.5, lf), (fdx, fdy)) for (fdx, fdy), perp, d, lf in depths]

    def _grove_room(self: Settlement, hx: float, hy: float, hw: float, hh: float) -> bool:  # type: ignore[misc]
        """Whether at least a MINIMAL grove clump fits on the windward side - used by the homestead solver to
        prefer a house position that leaves room for a grove (the actual, possibly larger, grove is placed in
        the second pass). Mirrors the minimal footprint the `_find_grove_arms` ladder falls back to."""
        for (fdx, fdy), perp in self._GROVE_ARMS[self._windward()]:
            cx, cy, w, h = self._grove_arm_rect(hx, hy, hw, hh, fdx, fdy, perp, 13 * self.bscale, 1.5, 0.5)
            if self._grove_fits(cx, cy, w, h, [(hx, hy)]):
                return True
        return False

    def _draw_grove(self: Settlement, cx: float, cy: float, w: float, h: float, face: Any, mix: str = "windbreak") -> None:  # type: ignore[misc]
        """Draw one windbreak/grove clump as a DENSE MIXED STAND - overlapping canopies packed into a real
        grove (not a few scattered trees), of three species: tall EVERGREEN conifer (dark, dense apex - the
        windbreak backbone, cedar/pine), DECIDUOUS broadleaf (mid green - timber and fruit, zelkova/persimmon),
        and a BAMBOO clump (take - fine culms with leafy tops). `mix` picks the species blend: 'windbreak' is
        conifer-backed (the sheltering wall - the yashikirin and the fengshui back belt); 'dooryard' is bamboo
        + fruit broadleaf with NO conifer (the leafy bamboo/fruit greenery scattered among village houses).
        Distinct from the big s.forest area feature and the striped kitchen-garden bed. Species and placement
        are seeded by position (stable across regenerations). Canopy count scales with footprint area."""
        # SCOPED (2026-08-08): a homestead grove's crowns are decoration keyed to the grove itself.
        with self.rng_scope("grove", cx, cy, w, h):
            bs = self.bscale / 0.82  # render scale relative to the town grain
            st = random.getstate()
            random.seed(int(abs(cx) * 5 + abs(cy) * 3 + round(w)))
            n = max(5, min(28, round(w * h / (bs * bs * 48))))  # ~ one crown per ~48 px^2 at 2 ft/px (a ~5 m crown); ~40 across the 6:1 L-grove
            b_th, c_th = (0.20, 0.58) if mix == "windbreak" else (0.45, 0.45)  # dooryard = bamboo + fruit, no conifer
            items: list[Any] = []
            for _ in range(n):
                px = random.uniform(-w / 2 + 2, w / 2 - 2)
                py = random.uniform(-h / 2 + 2, h / 2 - 2)
                roll = random.random()
                kind = "bamboo" if roll < b_th else ("conifer" if roll < c_th else "broadleaf")
                size = random.uniform(1.25, 1.7) if random.random() < 0.25 else random.uniform(0.72, 1.05)  # a few emergent crowns over many small
                items.append((px, py, kind, size))
            # ORDER-SENSITIVE: this reads M, so it can only avoid structures that ALREADY EXIST when the
            # grove is drawn. That is why the yashikirin arms draw after their farmstead's house and why
            # village_grove() is called late in a gen (see "DRAW ORDER" in CLAUDE.md before moving either).
            # NO CROWN ON A ROOF OR A WELLHEAD (GM 2026-07-25). A yashikirin belt is drawn hard against the
            # house it shelters and a village copse threads between the dwellings, so the stand is filtered
            # tree-by-tree rather than pushed back as a whole: it THINS where it would cover a building and
            # keeps its shape everywhere else. Crown centers below are relative to (cx, cy); keep-outs absolute.
            krect, kcirc = self._canopy_keepouts((cx - w / 2 - 9 * bs, cy - h / 2 - 9 * bs, cx + w / 2 + 9 * bs, cy + h / 2 + 9 * bs))
            drawn: list[tuple[float, float, float]] = []
            g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
            # Draw back-to-front so the stand layers with depth. Each CROWN is one tree at real size (~5-6 m; a few
            # emergents larger) - that is the to-scale reading, and it is unchanged. We deliberately DROP two kinds
            # of detail that cost ~half the stand's SVG elements without buying scale accuracy: the per-tree trunk
            # (hidden under the closed canopy anyway), and the 6-culm bamboo clump - a real *take* is DOZENS of
            # culms, so any handful is already symbolic, and one compact culm+top reads the same. See the foliage
            # comparison (the 'to scale, compact bamboo' option) for the before/after; groves stay to scale, the
            # SVG + rsvg raster roughly halve.
            for px, py, kind, s in sorted(items, key=lambda t: t[1]):
                if kind == "bamboo":  # one compact culm + leafy top (symbolic, was 6)
                    if self._crown_covers(cx + px, cy + py - 4 * bs, 3.0 * bs, krect, kcirc, self.CANOPY_PAD):
                        continue
                    drawn.append((cx + px, cy + py - 4 * bs, 3.0 * bs))
                    g.append(f'<line x1="{px:.1f}" y1="{py + 4 * bs:.1f}" x2="{px:.1f}" y2="{py - 4 * bs:.1f}" stroke="#88A646" stroke-width="{1.4 * bs:.2f}"/>')
                    g.append(f'<circle cx="{px:.1f}" cy="{py - 4 * bs:.1f}" r="{3.0 * bs:.1f}" fill="#BBD06A"/>')
                    continue
                rr = (4.6 if kind == "conifer" else 4.0) * s * bs  # one crown = one tree, sized to a real ~5-6 m canopy
                col = "#496733" if kind == "conifer" else random.choice(["#7C9A4E", "#6E8B43"])
                if self._crown_covers(cx + px, cy + py - 3 * bs, rr, krect, kcirc, self.CANOPY_PAD):
                    continue
                drawn.append((cx + px, cy + py - 3 * bs, rr))
                g.append(f'<circle cx="{px:.1f}" cy="{py - 3 * bs:.1f}" r="{rr:.1f}" fill="{col}" stroke="#3C5526" stroke-width="0.8"/>')
                if kind == "conifer":
                    g.append(f'<circle cx="{px:.1f}" cy="{py - 3 * bs:.1f}" r="{rr * 0.4:.1f}" fill="#364D22" opacity="0.55"/>')  # dense dark apex
            g.append('</g>')
            self.add(''.join(g))
            self._record_crowns(drawn)
            random.setstate(st)

    def village_grove(self: Settlement, poly: Any, role: str = "windbreak", dense: bool = True, within: tuple[float, float, float, float] | None = None) -> int:  # type: ignore[misc]
        """A COMMUNAL village grove - the Chinese *fengshui* forest (风水林). Unlike the per-house *yashikirin*,
        a NUCLEATED village shelters behind ONE village-scale grove, in three roles (see settlements.md 'Village
        windbreak'):
          - `windbreak` - the dense belt on the WINDWARD/high BACK edge (后龙林 back-village grove); the winter-
            monsoon wall and the LARGEST vegetation feature. Nestles against and EMBRACES the cluster.
          - `water_mouth` - a smaller cluster of big old trees at the LOW entrance / water-mouth (水口林);
          - `copse` - the leafy bamboo / fruit-tree greenery scattered through the OPEN gaps among the houses.
        `poly` is the grove's FOOTPRINT - an IRREGULAR, terrain-following outline, NOT a rectangle (real groves
        hug the land and wrap the settlement, they are not ruled walls). It is FILLED with dense mixed-stand
        clumps on a jittered grid; a clump is SKIPPED wherever it would land on a HOUSE / threshing YARD /
        GARDEN / PADDY (so the wood settles into the open ground and hugs the cluster without ever drawing trees
        on a building or out in the crops - this is what lets the belt nestle right up to the village edge).
        `dense=True` packs overlapping clumps into a continuous belt/cluster; `dense=False` scatters them for the
        leafy fringe among houses. role tunes the species mix (windbreak/water_mouth = conifer-backed forest;
        copse = bamboo + fruit, no conifer). Recorded in M['village_groves'] (bbox + role + poly) IF any clump
        is drawn (a footprint entirely over houses/crops draws nothing and records nothing). Returns the count."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        mix = "windbreak" if role in ("windbreak", "water_mouth") else "dooryard"
        bs = self.bscale
        step = (20 if dense else 52) * bs
        clump = (28 if dense else 22) * bs
        # never draw a clump ON a home/yard/garden/byre/kura: keep the clump CENTER clear by the footprint's
        # circumscribing radius PLUS the clump's own drawn radius (clump/2) and a hair - so the tree blob settles
        # BESIDE the building, touching at most (grove_clumps_clear_of_structures gates it). (A grove may still hug
        # the eaves visually; the blob edge just may not cross the wall.) Was 0.35*clump - too small by ~0.15*clump,
        # which let a blob corner clip a small house.
        occ = [(o["x"], o["y"], 0.5 * math.hypot(o["w"], o["h"]) + clump * 0.5 + 2) for k in ("houses", "threshing_yards", "gardens", "byres", "farm_sheds") for o in self.M.get(k, [])]
        # a WELL is a clean draw-point: no tree CANOPY may reach the wellhead (a well lost under the grove reads
        # wrong - wells_clear_of_trees gates it). Keep-out = the well's DRAWN half-size (vr) + the canopy reach
        # (~0.9*clump, as for a shrine), NOT the tight 0.35*clump a homestead eave gets. (o["r"] is the recorded
        # clearance radius; the DRAWN wellhead is vr, which is what a crown must not overhang.)
        occ += [(o["x"], o["y"], o.get("vr", o["r"]) + clump * 0.90) for o in self.M.get("wells", [])]
        # ...and the NOTICE BOARD with its caption band (settlement-review, Sawada 2026-08-16: a
        # copse clump seated 10 px from the kosatsuba swallowed the board outright and pierced its
        # caption mid-word - the board is a 12x5 point fixture nothing in this list covered). 30 ft
        # reaches past the glyph and the ~54 ft tilted caption box's half-length from the center.
        occ += [(o["x"], o["y"], 30.0 + clump * 0.90) for o in self.M.get("kosatsuba", [])]
        # A SHRINE and its TORII sit in a CLEAN clearing: no tree CANOPY may reach them (a hall/arch lost in the
        # wood reads wrong - shrine_clear_of_grove_trees / torii_clear_of_grove_trees gate it). The DRAWN canopy
        # overhangs the nominal clump radius (crowns spill past clump/2), reaching ~0.85*clump from the clump
        # center - so the keep-out uses that reach + a hair (0.90*clump), NOT the 0.35*clump a homestead uses
        # (there a grove may hug the eaves). A torii is recorded as [x, y, z]; glyph spans x +/-19, y -10..+18.
        occ += [(o["x"], o["y"], 0.5 * math.hypot(o["w"], o["h"]) + clump * 0.90) for k in ("religious", "shrines") for o in self.M.get(k, [])]
        occ += [(t[0], t[1] + 4, math.hypot(19, 14) + clump * 0.90) for t in self.M.get("torii", [])]
        # ... and OFF the fengshui CRESCENT POND (GM 2026-07-21): no tree canopy may cross the half-moon
        # pond's water (trees_clear_of_fengshui_ponds gates it). The keep-out circle spans the FULL disk
        # (radius r + canopy reach) even though the water is only the away-facing half - the flat side toward
        # the village is the pond's open FORECOURT (the banyuetang fronted the settlement's ceremony/work
        # ground), so keeping the copse fringe off that band too is the historically right reading, not slack.
        occ += [(cp["cx"], cp["cy"], cp["r"] + clump * 0.90) for cp in self.M.get("crescent_ponds", [])]
        # ... and OFF A GROVE THAT IS ALREADY PLANTED (settlement-review x1, 2026-08-19). Nothing here
        # kept one grove out of another, and the copse is seated AFTER the windbreak, so it simply
        # planted itself in the belt: measured on Inashiro, clump-to-nearest-belt-clump distances of
        # 9, 8, 6, 4, 6, 4, 11, 9, 26, 30 and 83 ft against a belt clump radius of 14 - **10 of 11
        # copse clumps inside the belt's own canopy**, spanning x 1096-1188 while the houses span
        # 1108-1331. So the dooryards east of the front rank got no greenery at all and a whole
        # feature was invisible, while `settlements/vegetation.md` says outright that "the copse, not
        # the belt, fills the inner gaps".
        #
        # Sum of the two canopy reaches, so neither stand's ink laps the other. This also protects the
        # reverse order (a belt seated after a copse) without needing to know which ran first, and it
        # is why the keep-out is built from the RECORDED clumps rather than the grove's bbox - a belt's
        # bbox is a long rectangle whose corners are open ground the copse may legitimately use.
        # (the radius lives on the GROVE record, not the clump - a clump is a bare [x, y] pair)
        # Kept in its OWN list, not folded into `occ`, because `_reseat` has to tell this blocker
        # apart from the others - see the note there. (the radius lives on the GROVE record, not the
        # clump - a clump is a bare [x, y] pair)
        occ_grove = [(cl[0], cl[1], float(g.get("r") or 0.0) + clump * 0.90) for g in self.M.get("village_groves", []) for cl in (g.get("clumps") or [])]
        occ += occ_grove
        corr = self._corridor_buffers(clump * 0.45 + 4)  # ... and keep trees OFF the lanes / streets / road
        cr = clump / 2
        # ... and OUT of the SOUTHERN sun-corridor of every threshing yard + garden (a tree just south of them
        # blocks the drying/growing sun - +y is south). A touch wider than the check so it stays strictly clear.
        sun = [(o["x"], o["y"] + o["h"] / 2, o["w"] / 2 + cr + 2) for k in ("threshing_yards", "gardens") for o in self.M.get(k, [])]
        # ... and OUT of the EASTERN sun-lane of every kitchen GARDEN: a tree just east blocks the MORNING sun
        # (the sun rises in the E; +x is east), so a garden on a house's lee/E side keeps clear sky to its east.
        # Entry = (garden east edge, garden cy, half-height + reach). See gardens_unshaded_from_east.
        east = [(o["x"] + o["w"] / 2, o["y"], o["h"] / 2 + cr + 2) for o in self.M.get("gardens", [])]
        water_lines = [(st_["poly"], st_.get("w", 9) / 2) for st_ in self.M.get("streams", [])]
        water_lines += [(c_["poly"], c_.get("w", 2.5) / 2) for c_ in self.M.get("channels", [])]
        if self.M.get("moat"):
            water_lines.append((self.M["moat"], self.M.get("moat_width", 22) / 2))

        def _hard_blocked(qx: float, qy: float) -> bool:
            """Reasons a clump may not stand here that MOVING IT A FEW FEET DOES NOT CHANGE - the crop,
            open water, the dike bank. These are the edges a belt is supposed to stop at, so a clump
            refused for one of them is simply dropped; it never re-seats."""
            return (
                any(point_in_poly(qx, qy, f) or edge_dist(qx, qy, f) < 12 + cr for f in self.field_polys)
                or any(point_in_poly(qx, qy, d) or edge_dist(qx, qy, d) < 12 for d in self.dry_polys)
                or any(point_in_poly(qx, qy, dk["outline"]) for dk in self.M.get("dikes", []))
                or any(seg_dist(qx, qy, wl[k], wl[k + 1]) < whw + cr for wl, whw in water_lines for k in range(len(wl) - 1))
            )

        def _lane_blocked(qx: float, qy: float) -> bool:
            """A LANE only. Kept apart from the other local obstacles because the interior test below
            exists for exactly this case and for no other: a lane that ENDS at the belt is an edge the
            belt stops at, while one that RUNS THROUGH it is an obstacle to plant around, and
            interior-vs-rim is what separates them."""
            return any(seg_dist(qx, qy, lp[k], lp[k + 1]) < buf for lp, buf in corr for k in range(len(lp) - 1))

        def _local_blocked(qx: float, qy: float) -> bool:
            """LOCAL obstacles standing in the belt's line - a house, a yard, a wellhead's wide keep-out,
            a lane, a threshing yard's southern sun corridor, a garden's eastern light lane. A real
            planted belt is planted AROUND these, so an interior clump refused by one re-seats."""
            return (
                any((qx - ox) ** 2 + (qy - oy) ** 2 < rr * rr for ox, oy, rr in occ)
                or any(abs(qx - sx) < shw and se - cr - 2 < qy < se + 24 + cr for sx, se, shw in sun)
                or any(ex - cr - 2 < qx < ex + 24 + cr and abs(qy - ey) < ehh for ex, ey, ehh in east)
            )

        def _reseat(qx: float, qy: float, placed: list[Any], require_interior: bool) -> tuple[float, float] | None:
            """A DENSE belt flows around a local obstacle instead of losing the column.

            Which obstacles, and why this is not "re-seat around everything": a clump refused by the
            CROP, by open WATER or by a lane it merely abuts is refused for a reason that moving it a
            few feet does not change, and those are the edges where a belt is supposed to stop. What
            it DOES flow around is a local keep-out standing IN its line - a house, a yard, a
            wellhead (whose keep-out is the widest of the lot), a lane that CROSSES rather than
            abuts, and a threshing yard's southern sun corridor.

            The sun corridor is the case that motivated folding these three ad-hoc nudges into one
            helper (cohort seed 10, 2026-08-19). A yard's no-tree strip ran straight through the
            belt and left a 40 ft hole with a farmhouse directly downwind of it - the wall breached
            at the one place it was sheltering someone. It is not a crop edge and not a page edge;
            it is a local obstacle, and a real planted belt is planted around it. NOTE the earlier
            ledger entry blamed a pinch in `belt_polygon`; that was wrong - the band is a
            constant-depth ribbon, and the clumps were being filtered out, not left outside.

            Interior-only: a clump blocked near the polygon's own rim is at the belt's edge, where
            stopping is correct."""
            # INTERIOR ONLY FOR A LANE, and this cost seed 10 a round. The rule reads "a clump blocked
            # near the polygon's own rim is at the belt's edge, where stopping is correct" - true of a
            # lane, false of everything else. A belt is 110 px deep and a clump is 28, so demanding
            # `edge_dist > clump` leaves only the middle 54 px eligible: measured on seed 10, every
            # sun-corridor clump sat 2-27 px from a face and the search never ran. A yard's sun
            # corridor crosses the whole depth of the belt; where in that depth a given clump sits
            # says nothing about whether the belt should plant around it.
            # A SPARSE GROVE RE-SEATS TOO (settlement-review, Inashiro 2026-08-20). This used to read
            # `if not dense or (...)`, so only a belt flowed around an obstacle and a scatter's blocked
            # clump was dropped. That guard was written FOR the belt - the docstring above says so, "a
            # DENSE belt flows around a local obstacle instead of losing the column" - and the sparse
            # case was never considered. It is also backwards for what a copse is: the copse fills the
            # open gaps among the houses, so a clump refused because a house is there should try the
            # next gap. Finding the next gap IS the job; dropping the clump is the one response that
            # defeats the feature.
            #
            # Measured cost of the old behavior: Inashiro's copse collapsed to ONE clump inside a
            # declared 255 x 741 ft footprint once gate 0616 reserved ground around the belt's 227
            # clumps, and Mizuguchi's went 11 -> 4 earlier for the same reason (homesteads.py:248).
            # `village_groves_visibly_stocked` now fails a grove in that state.
            #
            # ONLY local obstacles reach here. `_hard_blocked` (crop, open water, the dike bank) still
            # drops the clump outright and must - those are the edges a stand is supposed to stop at,
            # and moving a few feet does not change them.
            # A SPARSE GROVE RE-SEATS ONLY WHEN ANOTHER STAND DISPLACED IT, and the narrowness is the
            # point. Blanket `not dense` re-seating was tried first and OVERSHOT badly: Inashiro's
            # copse went 1 -> 55 clumps and density across the four hamlets jumped to 10-15 per 100k
            # against a historical 3.9-4.4, which turns a dooryard scatter into a stand and defeats
            # the `dense` flag's whole purpose. A scatter is SUPPOSED to leave gaps; a clump refused
            # because a house is there has found one of them.
            #
            # What is NOT a gap is ground another grove's canopy is standing on. That blocker did not
            # exist until gate 0616's keep-out added it, and it deletes clumps for a reason that has
            # nothing to do with the settlement's own texture - measured, it cost Inashiro 10 of its
            # 11 copse clumps. So exactly that class relocates, and every other refusal still drops.
            # This repairs the harm the keep-out did without redesigning the scatter.
            if not dense and not any((qx - ox) ** 2 + (qy - oy) ** 2 < rr * rr for ox, oy, rr in occ_grove):
                return None
            if require_interior and edge_dist(qx, qy, poly) <= clump:
                return None
            # THE RADII REACH PAST THE WIDEST LOCAL OBSTACLE, which is the sun corridor: a yard's
            # no-tree strip is ~25 px half-width across and ~31 px deep, so a search capped at
            # step*1.4 = 28 px could not clear one and seed 10 kept its hole. step*2.2 = 44 px can.
            for _nr in (step * 0.6, step * 1.0, step * 1.4, step * 1.8, step * 2.2):
                for _na in range(0, 360, 45):
                    ax, ay = qx + _nr * math.cos(math.radians(_na)), qy + _nr * math.sin(math.radians(_na))
                    if not point_in_poly(ax, ay, poly):
                        continue
                    if within is not None and (ax + clump * 0.9 < within[0] or ax - clump * 0.9 > within[2] or ay + clump * 0.9 < within[1] or ay - clump * 0.9 > within[3]):
                        continue
                    if _hard_blocked(ax, ay) or _local_blocked(ax, ay) or _lane_blocked(ax, ay):
                        continue
                    if any((ax - qx2) ** 2 + (ay - qy2) ** 2 < (step * 0.55) ** 2 for qx2, qy2 in placed):
                        continue
                    return (ax, ay)
            return None

        nx, ny = max(1, round((x1 - x0) / step)), max(1, round((y1 - y0) / step))
        clumps: list[Any] = []
        for iy in range(ny + 1):
            for ix in range(nx + 1):
                gx = x0 + ix * (x1 - x0) / nx
                gy = y0 + iy * (y1 - y0) / ny
                jx = gx + (self._hjit(gx, gy, 21.0) - 0.5) * step  # jitter the grid so the stand + its edge read ragged
                jy = gy + (self._hjit(gx, gy, 22.0) - 0.5) * step
                if not point_in_poly(jx, jy, poly):
                    continue
                # ...AND NOT WHOLLY OFF THE PAGE, when the caller gives a `within`. ONLY wholly - a
                # clump whose crown merely CROSSES the frame edge is kept, and that is doctrine, not
                # leniency: `settlements/presentation.md` (GM 2026-07-20) says the belt CLIPS at the
                # view edge and "a partially visible belt reads as 'the wood continues'", which is
                # why `hard_features_within_frame` demands partial visibility of a village grove
                # rather than containment. Only a clump with NO visible ink is waste.
                #
                # THE FIRST VERSION INSET THE WINDOW INSTEAD, AND THAT WAS BACKWARDS - recorded
                # because it shipped and two independent reviews caught it. Requiring the whole crown
                # inside (`within[2] - 0.9*clump`) deleted every clump the edge merely touched, and on
                # Mizuguchi that traded 3 invisible clumps for 40 dropped ones - 37 of them at least
                # partly visible, 12 not touching the frame at all - punching a ~100 ft bare channel
                # through the middle of the wind wall on the windward side. Sawada lost 46% of its
                # canopy the same way. The earlier review that asked for "58 clumps touching the
                # frame" to be fixed was itself against the presentation doctrine above; the only
                # real defect was the 23 with no ink on the page.
                if within is not None and (jx + clump * 0.9 < within[0] or jx - clump * 0.9 > within[2] or jy + clump * 0.9 < within[1] or jy - clump * 0.9 > within[3]):
                    continue
                # A DENSE BELT FLOWS AROUND AN OBSTACLE INSTEAD OF LOSING THE COLUMN (settlement-review,
                # Inashiro 2026-08-18). `occ` keeps a clump off a house, a yard, a byre and - the case
                # that bit - a WELLHEAD, whose keep-out is the widest of the lot (`vr + 0.9*clump`,
                # because a well lost under the canopy reads wrong). A wellhead seated inside the belt
                # therefore deleted every clump around it, and the belt acquired a zero-canopy latitude
                # on its WINDWARD side - a hole straight through the wind wall, which is the one thing
                # a windbreak exists not to have. Measured on Inashiro: the 40 ft band at y1360-1400
                # went 8 clumps -> 1, in a 930 ft run that had never had a gap.
                #
                # Fixing it at the WELL was tried first and is the wrong lever - recorded because it
                # shipped for a moment. Ranking "not in the belt" ahead of coverage in the well
                # tie-break closed Inashiro's hole and cost Mizuguchi 61 ft of worst walk, on a map
                # whose own belt hole turned out not to be well-caused at all. The belt is what should
                # give: a real planted windbreak is not laid out on a grid and abandoned where a shed
                # stands, it is planted around the shed.
                #
                # So a blocked clump in a DENSE grove gets a short re-seat search before it is
                # dropped, and only for `occ` - a clump refused by the CROP, open WATER or a LANE is
                # refused for a reason that re-seating does not change, and those are the edges where
                # a belt is supposed to stop. The nudge re-asks every other test, and keeps its
                # distance from the clumps already down so a re-seat cannot just pile up on its
                # neighbor.
                # ONE rejection chain, three nudge blocks folded into it (2026-08-19). A HARD blocker
                # (crop, water, dike) drops the clump - those are edges a belt stops at. A LOCAL one
                # (a house, a yard, a wellhead, a lane, a sun corridor) gets a short re-seat search,
                # because a planted belt is planted AROUND a shed rather than abandoned at it. Three
                # separate causes have now punched holes in a wind wall here - a wellhead inside the
                # belt, a peer session's lane crossing it, and a threshing yard's sun corridor - and
                # each was fixed with its own ad-hoc nudge until the third made the pattern obvious.
                if _hard_blocked(jx, jy):
                    continue
                if _local_blocked(jx, jy) or _lane_blocked(jx, jy):
                    _alt = _reseat(jx, jy, clumps, require_interior=not _local_blocked(jx, jy))
                    if _alt is None:
                        continue
                    jx, jy = _alt
                self._draw_grove(jx, jy, clump, clump, face=(0, -1), mix=mix)
                clumps.append([round(jx, 1), round(jy, 1)])
        if clumps:
            # A COPSE IS RECORDED AT THE SIZE IT WAS DRAWN, not at the size it was asked for.
            #
            # The copse's requested footprint is the bounding box of the whole house cloud, and the
            # clumps inside it are skipped wherever they would land on a house, yard, garden or
            # crop - so the DECLARED area and the PLANTED area are two different things, and the
            # gap between them widens whenever the cluster spreads. Feature 126 spread it (houses
            # are no longer seated against pre-laid lanes), and `village_groves_visibly_stocked`
            # started firing: "copse 307x443px holds 1 clump (0.73/100k), floor 1.5". The trees had
            # not gone anywhere; the box around them had grown.
            #
            # The check is right and the record was wrong - a map that declares a feature it did not
            # draw is the defect, which is the same rule `M["lane"]` breaks when it keeps an untrimmed
            # spine. So a COPSE reports the extent of its own clumps. The WINDBREAK deliberately does
            # not: its position IS its meaning (`village_windbreak_on_windward_side` judges the
            # recorded center) and shrinking it to the leaves would walk that center off the windward
            # side - a defect this file already records having caused on cohort seeds 19 and 28.
            if role == "copse":
                _cxs = [cl[0] for cl in clumps]
                _cys = [cl[1] for cl in clumps]
                _pad = clump / 2 + 4.0
                x0, x1 = min(_cxs) - _pad, max(_cxs) + _pad
                y0, y1 = min(_cys) - _pad, max(_cys) + _pad
                poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            self.M["village_groves"].append(
                {
                    "x": round((x0 + x1) / 2, 1),
                    "y": round((y0 + y1) / 2, 1),
                    "w": round(x1 - x0, 1),
                    "h": round(y1 - y0, 1),
                    "rot": 0,
                    "role": role,
                    "r": round(clump / 2, 1),
                    "clumps": clumps,  # actual drawn clump centers + radius, for groves_clear_of_lanes
                    "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
                }
            )
        return len(clumps)

    def _corridor_buffers(self: Settlement, extra: float = 0) -> list[Any]:  # type: ignore[misc]
        """Lane / town-street / road centerlines with their (half-width + `extra`) keep-out - the corridors that
        trees, scrub, and other vegetation must not be drawn ON. Returns [(polyline, buffer), ...]."""
        corr = [([tuple(p) for p in ln["pts"]], ln.get("w", 6) / 2 + extra) for ln in self.M.get("lanes", [])]
        corr += [([tuple(p) for p in s["pts"]], s.get("w", 10) / 2 + extra) for s in self.M.get("town_streets", [])]
        # alleys + the city ring road are ways too (GM 2026-07-24: yard furniture kept off "roads"
        # must mean EVERY tread - a rail tip on an alley is the same defect as one on the road)
        corr += [([tuple(p) for p in a["pts"]], a.get("w", 4) / 2 + extra) for a in self.M.get("alleys", [])]
        if self.M.get("ring_road"):
            corr.append(([tuple(p) for p in self.M["ring_road"]], self.M.get("ring_road_width", 20) / 2 + extra))
        if self.M.get("road"):
            corr.append(([tuple(p) for p in self.M["road"]], self.M.get("road_width", 26) / 2 + extra))
        return corr

    def _watercourse_segs(self: Settlement, pad: float = 2.0, channel_margin: float = 0.0) -> list[tuple[Any, float]]:  # type: ignore[misc]
        """Every drawn watercourse as (polyline, half-width + pad) pairs in boxed_segs shape: streams,
        channels, and the comb laterals' drawn truth (M['drawn_channels'] - added 2026-08-16, GM,
        Inashiro: grass tufts stood ON the head-race, because the scatter knew only the hairline
        topology record in M['channels'], w 2.5, while the drawn lateral ran ~14 wide on its own
        filleted post-clip polyline - the "same manifest source" trap, settlements.md 'PLANK
        BRIDGES'). A tapered lateral is split by `waterfields.taper_pieces` - ONE piece per SEGMENT
        at its arc-correct width, the very same call `field_channel` inks it with, so the corridor
        and the stroke it protects cannot disagree. Factored so the per-point test (_on_watercourse) and the
        ground-cover scatters' pre-boxed grids provably test the same geometry. `channel_margin`
        widens the IRRIGATION courses only (channels + drawn laterals, never streams) - the commons
        scatter passes the cut-bank margin here (_BANK_MARGIN_FT says why banks are bare and why a
        natural stream bank is not)."""
        out: list[tuple[Any, float]] = [(wc["poly"], wc.get("w", 6) / 2 + pad) for wc in self.M.get("streams", [])]
        out += [(wc["poly"], wc.get("w", 6) / 2 + pad + channel_margin) for wc in self.M.get("channels", [])]
        for ch in self.M.get("drawn_channels", []):
            p, w0, w1 = ch["pts"], ch["w0"], ch["w1"]
            if len(p) < 2:
                continue
            if abs(w1 - w0) < 0.2:  # drawn as ONE stroke at w0 (field_channel's uniform branch)
                out.append((p, w0 / 2 + pad + channel_margin))
            else:  # drawn per SEGMENT at its arc-correct width - the SAME ladder field_channel inks
                from l7r.diagram.waterfields import taper_pieces  # local: the engine packages are peers, imported lazily

                for piece, wk in taper_pieces(p, w0, w1):
                    out.append((piece, wk / 2 + pad + channel_margin))
        return out

    def _on_watercourse(self: Settlement, px: float, py: float, pad: float = 2.0, near: Any = None) -> bool:  # type: ignore[misc]
        """True if (px, py) lies ON a drawn watercourse - a stream, an irrigation channel, or a comb
        lateral (within its drawn half-width + `pad`; _watercourse_segs says which registries and
        why). Decorative ground-cover (scrub, reeds) skips it: vegetation never draws OVER open
        water, the same reason it skips the lane tread and the pond. `near` is an optional
        pre-boxed accessor (boxed_grid(boxed_segs(self._watercourse_segs())).near) for callers that
        test per scatter POINT - the same hoist-the-invariant discipline as their other keep-outs
        (fld_b / cor_b); verdicts are identical either way (the grid prunes, it never decides)."""
        if near is not None:
            if boxed_seg_hit(px, py, near(px, py)):
                return True
        else:
            for p, half in self._watercourse_segs(pad):
                if any(seg_dist(px, py, p[i], p[i + 1]) < half for i in range(len(p) - 1)):
                    return True
        # ... and the fengshui crescent pond's open water (found 2026-07-21: scrub tufts drew ON the
        # half-moon pond - the skip knew M['pond'] and the linear courses but not this water body)
        return any(math.hypot(px - cp["cx"], py - cp["cy"]) < cp["r"] + pad for cp in self.M.get("crescent_ponds", []))

    # THE URBAN-CLEARANCE HALO (GM 2026-07-21, Hoshizora): loose ground-cover (scrub, reeds) stays out of
    # the swept/trodden ground AROUND every occupied structure, not merely off its footprint. WHY: the daily
    # foot traffic, sweeping, and fuel/fodder-gathering pressure of the residents strips brush from the
    # ground nearest the dwellings first - dooryards are packed earth, the alleys between packed town houses
    # are walked bare, and a settlement's whole built-up fabric reads CLEARED; scrub survives only past this
    # halo, on the outskirts. 30 ft around structures (a working dooryard's depth; also closes the gaps in
    # packed districts, whose ~40-48 ft house spacing leaves no strip wider than two halos), 20 ft around a
    # wellhead (the most-trodden, spill-puddled ground in any settlement), 8 ft around tended ground plots
    # (a garden's or threshing yard's maintained edge). Constants are REAL FEET, converted at the map grain.
    _CROP_MARGIN_FT = 6.0
    # CROP MARGIN (GM 2026-08-15: scrub was overlapping dry crop plots and crowding crop edges).
    # Scrub stands OFF the crops: the scatter skips every paddy AND dry plot, plus this margin of
    # real feet around every crop edge. WHY 6 ft - the bund plus one cut swath: a paddy levee
    # (keihan/aze; Chinese tian'geng) is a ~1-2 ft earthen ridge (~3 ft where it carries a footpath,
    # azemichi), and the levee grass and the strip beside the crop were CUT several times a season
    # for fodder/green manure, so woody scrub never establishes within about a scythe's swath
    # (~1-2 m) of the field edge - the same ~1 m clean strip that separates crop from boundary
    # vegetation in traditional field-margin practice. Land hunger keeps East Asian margins NARROW,
    # so 6 ft (~1.8 m) total, not a wide verge. Tall glyphs (scraggly pines, woodland crowns) add
    # their own drawn reach on top so no tip leans over the crop. Grass-tuft blade TIPS are the
    # deliberate exception (settlement-review, 2026-08-16): a blade is 2.4-4.2*bs px, so at the
    # coarser tiers a tip can lean up to a few real feet over the margin line - accepted, because
    # grass leaning over a bund is real; bases and tall-glyph reach are what the rule enforces.
    # Full grounding: settlements/vegetation.md "Scrub stands off the crops".
    _BANK_MARGIN_FT = 6.0
    # CUT-BANK MARGIN (GM 2026-08-16, Inashiro second pass: tufts seeded in the 10-16 ft berm
    # strip between the dry hem plots and the supply channels - legal under the drawn-width water
    # skip + the crop margin, which between them left a bare sliver mid-strip). The commons scatter
    # stands its bases this many real feet off the drawn water EDGE of every IRRIGATION channel
    # (M['channels'] + M['drawn_channels']). WHY 6 ft, and why channels only: a supply channel's
    # bank is MAINTAINED ground - walked for sluice work and bund upkeep, and its grass scythed for
    # fodder on the same rotation as the field margins - so established scrub tufts/brush there are
    # as wrong as on a bund; one scythe swath (~1.8 m) is the same figure the crop margin rests on
    # (_CROP_MARGIN_FT above). STREAMS and the reed marsh deliberately take NO margin: a natural
    # bank is vegetated to the water's edge, and the 2026-08-16 settlement-review pass explicitly
    # praised the absence of a sterile halo on the brooks. Full grounding:
    # research/vegetation.md "The cut bank".
    _HALO_STRUCT_FT = 30.0
    _HALO_WELL_FT = 20.0
    _HALO_PLOT_FT = 8.0
    # occupied structures (people live/work in them: full dooryard halo) vs tended ground plots (kept clear
    # to their edge, but nobody sweeps a 30 ft apron around a vegetable bed)
    _HALO_STRUCT_KEYS = ("houses", "buildings", "storehouses", "flophouses", "byres", "farm_sheds", "religious", "shrines", "manors", "ministries", "inspection_stations", "theater_stage")
    # `theater_stage` added 2026-07-26: hinterland scrub was drawn ON the stage's roof, and it took an
    # independent reviewer's eye to see it because SCRUB IS NOT RECORDED IN THE MANIFEST - no gate check
    # and no manifest audit can reach this class of defect at all. (This halo is deliberately NARROWER
    # than the canopy rule below: it sweeps a 30 ft dooryard apron, so every key added here also strips
    # ground cover for 30 ft around it and moves `town_margins_clothed`. Roofed civic/trade premises are
    # therefore NOT bulk-added here - they are handled by the canopy contract, which is about ink on a
    # roof rather than about how much of the sheet reads as worked.)
    _HALO_PLOT_KEYS = ("gardens", "threshing_yards")
    # NO TREE IS DRAWN ON A ROOF OR A WELLHEAD (GM 2026-07-25). Every ROOFED structure on the map,
    # plus the wellheads - the keep-out that every canopy crown is tested against (_crown_covers).
    # Open-air work grounds (threshing yards, kitchen gardens, tanning/dye yards, cremation grounds)
    # are deliberately NOT here: they have their own sun-corridor and clearance rules, and a tree
    # overhanging the CORNER of a yard is a real thing, while a tree drawn on a roof is just a
    # building you can no longer see.
    # OPEN-AIR WORKING GROUND - deliberately NOT a canopy keep-out. These records are a patch of
    # ground, not a roof: a tree overhanging the corner of a yard is a real thing, and each of these
    # has its own clearance and sun-corridor rules. Every OTHER solid feature is a keep-out by
    # default (below), so this tuple is the only place a new feature can legitimately opt out - and
    # `test_every_roofed_feature_is_a_canopy_keepout` fails if a key is in neither.
    _CANOPY_OPEN_AIR_KEYS = (
        "gardens",  # a dooryard bed; a bough over its edge is normal
        "threshing_yards",  # a swept work floor abutting its own farmhouse
        "tanning_yards",  # a pit yard on a bank - open ground by definition
        "dye_yards",  # drying racks in the open
        "lumber_yards",  # stacked timber in the open
        "charcoal_yards",  # a cart yard whose roofed sheds are interior detail, not the record
        "refining_forges",  # an open-sided works; the record is its whole working ground
        "cremation_grounds",  # open ground with a pyre platform
        "execution_grounds",  # bare, unfenced waste ground - the bareness IS the feature
        "punishment_spots",  # a patch of tamped earth on a verge
        "boundary_markers",  # a stone
        "ossuaries",  # a low earth mound
        "cemeteries",  # an open burial ground; trees among graves are correct
        "kosatsuba",  # a board on a post at the verge
    )
    # NO TREE IS DRAWN ON A ROOF OR A WELLHEAD (GM 2026-07-25; DERIVED 2026-07-26). Every roofed
    # structure plus the wellheads - the keep-out every canopy crown is tested against (_crown_covers).
    # This was a HAND LIST until a reviewer found scrub on a theater stage; the list is now the overlap
    # registry minus the open-air exemptions above, so a new roofed feature is covered by default and
    # forgetting is impossible. Same move that retired `ring_road_kept_clear`'s hand list.
    # Features that are not in check_village's _OVERLAP_STRUCTS at all (they are targets or exempt
    # there) but are still roofed things a crown must not cover.
    _CANOPY_EXTRA_KEYS = ("merchant_estates", "wall_towers", "gate_structs", "theater_stage")
    # Every ROOFED premises from the overlap registry. settlement.py cannot import check_village
    # (circular), so this tuple is written out - and
    # `test_every_roofed_feature_is_a_canopy_keepout` holds it against the real registry, failing
    # with the offending key by name if a new feature is in neither this nor _CANOPY_OPEN_AIR_KEYS.
    # The TEST is the ratchet; the tuple is just the data.
    _CANOPY_ROOFED_KEYS = (
        "precinct_halls",  # the sovereign precinct program - roofed halls (021)
        "terraces",  # a retainer terrace is one continuous roof over its household cells
        "granaries",  # the capital's wharf granaries - kura rows, roofed like the town's dict-recorded one
        "mausoleums",
        "fire_towers",
        "drum_towers",
        "breweries",
        "oil_presses",
        "pawnshops",
        "bathhouses",
        "kilns",
        "farriers",
        "martial_halls",
        "dojos",
        "castles",  # a walled compound like a manor - its court is blank by doctrine, not open ground
        "castle_towers",  # yagura are roofed buildings
    )
    _CANOPY_STRUCT_KEYS = _HALO_STRUCT_KEYS + _CANOPY_EXTRA_KEYS + _CANOPY_ROOFED_KEYS

    def _canopy_keepouts(self: Settlement, bbox: tuple[float, float, float, float]) -> tuple[list[tuple[float, float, float, float]], list[tuple[float, float, float]]]:  # type: ignore[misc]
        """Every drawn BUILDING footprint (as x, y, half-w, half-h) and WELLHEAD (as x, y, r) near `bbox` -
        the keep-out a tree CROWN may not cover. Distinct from _urban_keepouts, the 30 ft swept halo the
        ground-cover scatters honor: a tree may stand hard against a wall (real groves hug the eaves), it
        may only not be DRAWN ON the roof - so the halo here is zero. A rotated structure is covered
        conservatively by its half-diagonal square. Prefiltered to `bbox`, since the caller tests every
        crown of a stand against this list."""
        bx0, by0, bx1, by1 = bbox
        rects: list[tuple[float, float, float, float]] = []
        for k in self._CANOPY_STRUCT_KEYS:
            for o in self._reclist(k):
                # the DRAWN box (a location marker like the kosatsuba draws at a legibility floor
                # above its true footprint, and overlap here is about drawn pixels - same reason the
                # wells use vr over r)
                hw, hh = o.get("vw", o["w"]) / 2, o.get("vh", o["h"]) / 2
                if o.get("rot"):
                    hw = hh = math.hypot(hw, hh)
                if o["x"] + hw >= bx0 and o["x"] - hw <= bx1 and o["y"] + hh >= by0 and o["y"] - hh <= by1:
                    rects.append((o["x"], o["y"], hw, hh))
        circles = [(o["x"], o["y"], o.get("vr", o["r"])) for o in self.M.get("wells", []) if bx0 <= o["x"] <= bx1 and by0 <= o["y"] <= by1]
        return rects, circles

    @staticmethod
    def _crown_covers(x: float, y: float, r: float, rects: Sequence[tuple[float, float, float, float]], circles: Sequence[tuple[float, float, float]], pad: float = 0.0) -> bool:
        """Whether a canopy crown of radius `r` centered at (x, y) would cover any keep-out from
        _canopy_keepouts - i.e. whether drawing this one tree would hide a building or a wellhead.
        `pad` is a placement-side margin ONLY: the manifest rounds crown coordinates to 0.1 px, so a
        crown drawn exactly TANGENT to a wall can round to a hair of overlap and fire the check that
        re-reads it. Drawing passes a small pad so a kept crown is unambiguously clear; the check
        itself stays exact (pad 0), which is what keeps its teeth."""
        for cx, cy, hw, hh in rects:
            dx, dy = max(abs(x - cx) - hw, 0.0), max(abs(y - cy) - hh, 0.0)
            if dx * dx + dy * dy < (r + pad) ** 2:
                return True
        return any((x - wx) ** 2 + (y - wy) ** 2 < (r + pad + wr) ** 2 for wx, wy, wr in circles)

    def _record_crowns(self: Settlement, crowns: Sequence[tuple[float, float, float]]) -> None:  # type: ignore[misc]
        """Record drawn canopy crowns as a flat [x, y, r, ...] run in M['tree_crowns'] - the manifest
        record of EVERY tree this map draws, which is what structures_clear_of_trees / wells_clear_of_trees
        test. Flat rather than per-tree dicts because a to-scale map draws thousands of them (see
        settlements.md, 'No tree is drawn on a roof')."""
        for x, y, r in crowns:
            self.M["tree_crowns"] += [round(x, 1), round(y, 1), round(r, 1)]

    def _reclist(self: Settlement, key: str) -> list[dict[str, Any]]:  # type: ignore[misc]
        """Records under `key`, whether the manifest stores a LIST of them or a single dict.

        A few features are singletons stored as a bare dict (`theater_stage`, `governor_mansion`) -
        which is why their keys are singular. Iterating one of those blindly yields its string KEYS,
        and `o["w"]` then raises `TypeError: string indices must be integers`. check_village has the
        same shape in `_OVERLAP_SINGLETONS`; this is the settlement-side counterpart.
        """
        rec = self.M.get(key)
        if isinstance(rec, dict):
            return [rec]
        return [r for r in (rec or []) if isinstance(r, dict)]

    def _urban_keepouts(self: Settlement, bbox: tuple[float, float, float, float]) -> tuple[list[tuple[float, float, float, float]], list[tuple[float, float, float]]]:  # type: ignore[misc]
        """Axis-aligned keep-out rects + wellhead keep-out circles for the urban-clearance halo (see the
        constants above), built from every structure/plot/well recorded in M so far. A rotated structure is
        covered conservatively by its half-diagonal square. Prefiltered to `bbox` (the cover poly's extent) -
        a keep-out that cannot touch the scatter region would only slow the per-point loop (a to-scale town
        carries ~200 structures and each cover poly samples thousands of points). Returned as (rects,
        circles) for the ground-cover scatters' per-point tests."""
        bx0, by0, bx1, by1 = bbox
        rects: list[tuple[float, float, float, float]] = []
        for keys, halo_ft in ((self._HALO_STRUCT_KEYS, self._HALO_STRUCT_FT), (self._HALO_PLOT_KEYS, self._HALO_PLOT_FT)):
            halo = halo_ft * self.bscale
            for k in keys:
                for o in self._reclist(k):
                    hw, hh = o["w"] / 2, o["h"] / 2
                    if o.get("rot"):
                        hw = hh = math.hypot(hw, hh)  # conservative: the rotated rect fits in its half-diagonal square
                    rx0, ry0, rx1, ry1 = o["x"] - hw - halo, o["y"] - hh - halo, o["x"] + hw + halo, o["y"] + hh + halo
                    if rx1 >= bx0 and rx0 <= bx1 and ry1 >= by0 and ry0 <= by1:
                        rects.append((rx0, ry0, rx1, ry1))
        wh = self._HALO_WELL_FT * self.bscale
        circles = [(o["x"], o["y"], o.get("vr", o["r"]) + wh) for o in self.M.get("wells", []) if bx0 - 40 <= o["x"] <= bx1 + 40 and by0 - 40 <= o["y"] <= by1 + 40]
        return rects, circles

    def _attach_grove(self: Settlement, hx: float, hy: float, arms: Any) -> None:  # type: ignore[misc]
        """Draw a farmstead's windbreak grove (its belt arms) and record each arm under its parent house.
        Arms go into `grove_rects` (NOT `placed`) so a neighbor's grove may MERGE with it and the wells
        still avoid it. Drawn in the farmsteads() second pass, after every house/yard/garden is set."""
        for cx, cy, w, h, face in arms:
            self._draw_grove(cx, cy, w, h, face)
            self.M["groves"].append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": 0, "of": [hx, hy], "face": list(face)})
            self.grove_rects.append((cx, cy, w, h))

    def _find_appurtenances(self: Settlement, hx: float, hy: float, hw: float, hh: float, rot: float = 0, kind: str = "plain", shed: Any = False, wealth: float = 1.0) -> tuple[Any, Any] | None:  # type: ignore[misc]
        """A farmstead needs room for BOTH its threshing yard (south/front, then a side) AND its dooryard
        kitchen garden (a DIFFERENT sunny side, kept off the west-side shed). Returns (yard_spot, garden_spot)
        or None if either can't fit."""
        yard = self._find_yard_spot(hx, hy, hw, hh)
        if yard is None:
            return None
        shed_rect = self._farm_shed_rect(hx, hy, hw, hh, rot, kind, shed)
        garden = self._find_garden_spot(hx, hy, hw, hh, yard, shed_rect, wealth)
        if garden is None:
            return None
        return yard, garden

    def _farmstead_nudges(self: Settlement) -> Iterator[tuple[float, float]]:  # type: ignore[misc]
        """Offsets to try for a farmhouse so the whole homestead (house + yard + garden + grove-room) fits:
        the ring's own spot first, then a widening spiral of shifts. The solver stops as soon as the home
        spot already works, so the wider rings only cost time for a genuinely crowded homestead."""
        yield 0, 0
        for d in (11 * self.bscale, 21 * self.bscale, 32 * self.bscale):
            yield from ((0, d), (d, 0), (-d, 0), (0, -d), (d, d), (-d, d), (d, -d), (-d, -d))
