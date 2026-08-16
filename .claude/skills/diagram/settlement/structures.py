"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ._geom import (
    WARD_BARRED_KINDS,
    Poly,
    Pt,
    _aabb_gap,
    label_aabb,
    label_tilt,
    organic_bbox,
    organic_poly,
    point_in_poly,
    poly_gap,
    rects_overlap,
    rot_rect,
    seg_closest,
    seg_dist,
    smooth_closed,
    smooth_points,
    tilt_caption_seat,
    way_beds,
)
from ._knobs import KOSATSUBA_MARKER_MIN_PX, MERCHANT_ESTATE_WEIGHTS, PUNISHMENT_SPOT_FT, roll_merchant_estate_count

if TYPE_CHECKING:
    from .core import Settlement


class StructuresMixin:
    def manor(  # type: ignore[misc]
        self: Settlement,
        x: float,
        y: float,
        w: float,
        h: float,
        label: Any,
        sublabel: str = "",
        gate_dir: str = "south",
        rot: float = 0,
        gate_ft: float = 12.0,
        label_xy: Pt | None = None,
        ink: str | None = None,
        label_inside: bool = False,
    ) -> None:
        """A walled samurai compound (e.g. a magistrate's manor / hunting lodge) shown
        as a feature on a settlement map: ONLY the walls + gate + empty court. The
        interior is deliberately not drawn here - it is the subject of its own Mode A
        diagram, and drawing speculative interior buildings here would contradict it.

        THE MANOR IS A GLYPH, NOT A SCALE DRAWING (GM 2026-07-27). It is ALWAYS a box, and
        the box is a simplification: the compound may be a different shape entirely on its
        own Mode A sheet. So a Mode B manor is NOT required to match its Mode A plan in
        footprint, proportion, or size, and features the Mode A sheet draws OUTSIDE the
        walls - gate boards, an approach fork, a bounty board - need not appear here at all.
        The manor glyph is PRESUMED to include everything the detailed sheet shows. Read a
        difference between the two artifacts as the convention working, not as a defect.
        gate_dir (north/south/east/west) is the wall the main gate opens through - face it
        toward whatever the compound fronts (the town / road it sits at the edge of). There
        is no universal default direction (it depends where the town is), but SOUTH is the
        auspicious/formal fallback. `rot` TILTS the whole compound (degrees) so it can parallel
        a diagonal road or river it fronts. Blocks houses.
        TO SCALE (GM 2026-07-19): the gate opening is `gate_ft` real feet (default 12 - a
        nagayamon/yakuimon passes a cart and palanquin; a grand yamen passes gate_ft=18-24),
        the wall draws ~2 ft thick (true-width-or-floored at 2px), and the gate posts are
        ~2 ft squares (floored ~3px). The blank court is DELIBERATE - the interior is the
        subject of its own Mode A diagram when the PCs visit; the wall + gate carry the
        realism, so they are the parts that must be honest. Records gate_w/wall_w (px).
        `ink` recolors the walls and gate (recorded in the manifest): feature 020 uses it for the
        Imperial Magistrate's compound, which is FOREIGN SOVEREIGN ground and must not read as
        another domain office - the manor form, in its own ink, the way state violet marks the
        ministries (settlements/capitals.md, "Compounds with no provincial equivalent")."""
        hw, hh = w / 2, h / 2
        wall = ink or '#2D2A24'
        gg = max(self.px(gate_ft) / 2, 2.0)  # gate HALF-gap: real feet, floored so the opening stays visible
        ww = max(self.px(2), 2.0)  # wall thickness: ~2 ft dobei, 2px cartographic floor
        gp = max(self.px(2), 3.0)  # gate post: ~2 ft square, floored for visibility
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)

        def absol(px: float, py: float) -> Pt:  # a compound-local point -> absolute map coords (after tilt)
            return (x + px * ca - py * sa, y + px * sa + py * ca)

        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">', f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="{h}" fill="#E7D9B4"/>']
        sides = {
            "north": ((-hw, -hh), (hw, -hh), (0, -hh), (0, -1)),
            "south": ((-hw, hh), (hw, hh), (0, hh), (0, 1)),
            "west": ((-hw, -hh), (-hw, hh), (-hw, 0), (-1, 0)),
            "east": ((hw, -hh), (hw, hh), (hw, 0), (1, 0)),
        }
        gcl = sides[gate_dir][2]
        for name, (pa, pb, (gx, gy), outv) in sides.items():
            if name != gate_dir:
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
            elif outv[1] == 0:  # vertical wall (west/east) - gap in y
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pa[0]:.0f}" y2="{gy - gg:.1f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                g.append(f'<line x1="{pb[0]:.0f}" y1="{gy + gg:.1f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                for py in (gy - gg, gy + gg):
                    g.append(f'<rect x="{gx - gp / 2:.1f}" y="{py - gp / 2:.1f}" width="{gp:.1f}" height="{gp:.1f}" fill="{wall}"/>')
            else:  # horizontal wall (north/south) - gap in x
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{gx - gg:.1f}" y2="{pa[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                g.append(f'<line x1="{gx + gg:.1f}" y1="{pb[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="{ww:.1f}"/>')
                for px in (gx - gg, gx + gg):
                    g.append(f'<rect x="{px - gp / 2:.1f}" y="{gy - gp / 2:.1f}" width="{gp:.1f}" height="{gp:.1f}" fill="{wall}"/>')
        g.append('</g>')
        self.add(''.join(g))
        # interior intentionally left blank: the buildings inside (hall, stables, etc.)
        # belong to a separate Mode A diagram of the manor, not the town/settlement map
        gctr = absol(*gcl)
        corners = [absol(-hw, -hh), absol(hw, -hh), absol(hw, hh), absol(-hw, hh)]
        # an axis-aligned manor whose wall abuts a neighborhood (ward) fence yields that wall to the
        # fence (re-stamped on top), exactly like the mausoleum; tilted manors are left untouched
        ward_walls: list[str] = []
        if rot == 0:
            msides = {
                "north": ((x - hw, y - hh), (x + hw, y - hh)),
                "south": ((x - hw, y + hh), (x + hw, y + hh)),
                "west": ((x - hw, y - hh), (x - hw, y + hh)),
                "east": ((x + hw, y - hh), (x + hw, y + hh)),
            }
            ward_walls = [name for name, (a, b) in msides.items() if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        self.M["manors"].append(
            {
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "rot": rot,
                "label": label,
                "gate": [round(gctr[0], 1), round(gctr[1], 1)],
                "gate_dir": gate_dir,
                "ward_walls": ward_walls,
                "gate_w": round(2 * gg, 2),
                "wall_w": round(ww, 2),
            }
        )
        if ink is not None:
            self.M["manors"][-1]["ink"] = ink  # only when passed, so every old manifest stays byte-identical
        self._assert_walls_clear_of_torii("the manor wall")
        m = max(
            36 * self.bscale, 26
        )  # a building-half margin at the map's grain, floored so a standard dwelling's corner keeps the 14px office-abut clearance (a samurai_large needs seed luck - the sweep handles it)
        blk = [absol(-hw - m, -hh - m), absol(hw + m, -hh - m), absol(hw + m, hh + m), absol(-hw - m, hh + m)]
        self.block_polys.append([(round(px, 1), round(py, 1)) for px, py in blk])
        ys = [c[1] for c in corners]
        _t = label_tilt(rot)
        if label:
            # the caption hangs above the walls by default; `label_xy` moves it when something
            # legitimately occupies that band - a ROTATED manor swings its corner up into the
            # text, and a punishment ground sited at the gate (which is where it belongs) sits
            # under it (GM 2026-07-26, Hoshizora). Same escape as s.martial_hall. A DIAGONAL
            # compound's caption tilts with it (label_tilt), at the hand seat or the default.
            if label_inside:
                # A CITY estate's caption lives INSIDE the walls (GM 2026-08-09): the court is
                # BLANK by doctrine - its contents belong to the Mode A sheet - so the empty
                # court is the label's natural ground. SPLIT over two lines (GM, same day) so
                # the face runs bigger: the width constraint binds per-line, and "Nio" over
                # "Estate" carries an 11 where the one-line form managed an 8.
                _words = str(label).split()
                if len(_words) >= 2:
                    _top, _bot = " ".join(_words[:-1]), _words[-1]
                    _fs = max(7.0, min(11.0, (w * 0.8) / (max(len(_top), len(_bot), 1) * 0.55)))
                    self.label(x, y - h * 0.12, _top, _fs, weight="bold", rot=_t)
                    self.label(x, y + h * 0.16, _bot, _fs, weight="bold", rot=_t)
                else:
                    _fs = max(6.5, min(14.0, (w * 0.82) / (max(len(str(label)), 1) * 0.55)))
                    self.label(x, y, label, _fs, weight="bold", rot=_t)
            else:
                _seat = label_xy or (tilt_caption_seat(x, y, rot, _t, w / 2, h / 2, 12, above=True) if _t else (x, min(ys) - 12))
                self.label(*_seat, label, 14, weight="bold", rot=_t)
        if sublabel:
            _s2 = tilt_caption_seat(x, y, rot, _t, w / 2, h / 2, 18) if _t else (x, max(ys) + 18)
            self.label(*_s2, sublabel, 9, italic=True, rot=_t)

    def _estate_wall_clear(self: Settlement, x: float, y: float, w: float, h: float, marg: float = 2.5) -> bool:  # type: ignore[misc]
        """Whether a walled compound's PERIMETER at (x,y,w,h) stays off recorded water (canals,
        docks, moat, river, pond), fire towers, AND the street net (streets, alleys, roads, the
        ring road - a compound wall may LINE a street, never stand IN its cleared band), with
        `marg` px of daylight. A fire tower ENCLOSED inside the court is refused too (the watch
        reaches its tower from public ground). Mirrors the merchant_estate_wall_clear_of_* gate
        geometry (which enforces 1.5px; the engine demands a little more so placement never sits
        at the check's edge)."""
        ex0, ey0, ex1, ey1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        if any(abs(t["x"] - x) < w / 2 and abs(t["y"] - y) < h / 2 for t in self.M.get("fire_towers", []) if "w" in t):
            return False  # tower walled inside the private court
        edges = [((ex0, ey0), (ex1, ey0)), ((ex1, ey0), (ex1, ey1)), ((ex1, ey1), (ex0, ey1)), ((ex0, ey1), (ex0, ey0))]
        lines: list[tuple[Any, float]] = [(cc["poly"], cc.get("w", 12) / 2 + marg) for cc in self.M.get("canals", [])]
        if self.M.get("moat"):
            lines.append((self.M["moat"], self.M.get("moat_width", 22) / 2 + marg))
        rv = self.M.get("river")
        if rv:
            lines.append((rv["pts"], rv.get("w", 40) / 2 + marg))
        lines += [(st["pts"], st.get("w", 12) / 2 + marg) for st in self.M.get("town_streets", [])]
        lines += [(al["pts"], al.get("w", 8) / 2 + marg) for al in self.M.get("alleys", [])]
        lines += [(rd["pts"], rd["w"] / 2 + marg) for rd in self.M.get("roads", [])]
        if self.M.get("road"):
            lines.append((self.M["road"], self.M.get("road_width", 26) / 2 + marg))
        if self.M.get("ring_road"):
            lines.append((self.M["ring_road"], self.M.get("ring_road_width", 7) / 2 + marg))
        boxes = [(dk["x"], dk["y"], dk["w"] / 2 + marg, dk["h"] / 2 + marg) for dk in self.M.get("docks", [])]
        boxes += [(t["x"], t["y"], t["w"] / 2 + marg, t["h"] / 2 + marg) for t in self.M.get("fire_towers", []) if "w" in t]
        pond = self.M.get("pond")
        for p0, p1 in edges:
            steps = max(2, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 3))
            for si in range(steps + 1):
                px_, py_ = p0[0] + (p1[0] - p0[0]) * si / steps, p0[1] + (p1[1] - p0[1]) * si / steps
                if any(abs(px_ - bx) < bw and abs(py_ - by) < bh for bx, by, bw, bh in boxes):
                    return False
                if any(any(seg_dist(px_, py_, pts[k], pts[k + 1]) < hw for k in range(len(pts) - 1)) for pts, hw in lines):
                    return False
                if pond and ((px_ - pond[0]) / (pond[2] + marg)) ** 2 + ((py_ - pond[1]) / (pond[3] + marg)) ** 2 <= 1:
                    return False
        return True

    def merchant_estate(self: Settlement, x: float, y: float, w: Any = None, h: Any = None, gate_dir: str = "south") -> None:  # type: ignore[misc]
        """A walled merchant compound - a VERY-rich merchant's estate within the merchant quarter: a
        light perimeter wall around a court with the merchant's large house inside (one large dwelling).
        Recorded in M['merchant_estates'] (NOT M['manors'], which are the samurai country estates
        outside the wall). The inner house is a normal merchant_large building, so it counts as housing.
        gate_dir is the side the courtyard gate opens through - it is fine for the walls to ABUT a
        neighboring building, but point the GATE at open ground, never into another building.
        SITING RULE (GM 2026-07-19): the compound wall must stand on dry, private ground - never
        through a canal/dock/moat/river/pond (the waterfront is working quay) or a fire tower
        (the municipal watch cannot be embedded in a private wall). Draw those features BEFORE
        the estate; if the requested spot violates, a small candidate fan slides the estate to
        the nearest clear seat, and if none exists within ~36px this raises rather than drawing
        a wall the gate will reject."""
        if w is None:
            w, h = 186 * self.bscale, 138 * self.bscale  # ~230x170 ft very-rich urban compound, scaled with the building grain
        # ring-ordered fan: near seats first, then wider; includes half-steps so the estate can
        # land in a narrow clear corridor (streets + water can leave windows only a few px wide)
        fan = [(0, 0)] + [(dx, dy) for r in (4, 8, 12, 16, 24, 36, 48) for dx, dy in ((-r, 0), (r, 0), (0, -r), (0, r), (-r, -r), (r, -r), (-r, r), (r, r))]
        for dx, dy in fan:
            if self._estate_wall_clear(x + dx, y + dy, w, h):
                x, y = x + dx, y + dy
                break
        else:
            raise ValueError(
                f"merchant_estate at ({x:.0f},{y:.0f}) {w:.0f}x{h:.0f}: no seat within the slide fan keeps the compound wall clear of water/fire towers - resite it (or the tower) in the gen"
            )
        x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        mww = max(self.px(2), 1.6)  # wall ~2 ft (a merchant's lighter wall), floored for visibility
        mgg = max(self.px(10), 3.5)  # gate opening ~10 real ft (a cart gate), floored
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#EAD9B0" stroke="#5A4326" stroke-width="{mww:.1f}"/>')  # walled court
        # the gate gap (erases a slot of the wall stroke on the chosen side); gate point on that edge
        gates = {"south": (x, y1, mgg, mww + 2), "north": (x, y0, mgg, mww + 2), "east": (x1, y, mww + 2, mgg), "west": (x0, y, mww + 2, mgg)}
        gx, gy, gw, gh = gates[gate_dir]
        self.add(f'<rect x="{gx - gw / 2:.1f}" y="{gy - gh / 2:.1f}" width="{gw:.1f}" height="{gh:.1f}" fill="#EAD9B0"/>')
        self.building(x, y - 2, *self._dims("merchant_large"), "merchant_large")  # the large house inside the court
        self.M.setdefault("merchant_estates", []).append(
            {"x": round(x, 1), "y": round(y, 1), "w": w, "h": h, "gate": [round(gx, 1), round(gy, 1)], "gate_dir": gate_dir, "gate_w": round(mgg, 2), "wall_w": round(mww, 2)}
        )
        self._assert_walls_clear_of_torii("the merchant estate wall")
        m = 18 * self.bscale  # a building-half margin at the map's grain
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
        # ... and register the court in self.placed (2026-07-23): block_polys tests only a candidate's
        # CENTER, and at the city grain the block margin (18 real ft = 6px) is thinner than half a pack
        # house - so a later pack could seat a house whose center cleared the block but whose BODY lapped
        # the court wall (caught by city_merchant_estates_clear_of_buildings on the Tango seat-3 vet).
        # self.placed is the SAT-distance registry every _fits candidate keeps real clearance from.
        self.placed.append((x, y, w, h))

    def merchant_estates(self: Settlement, seats: Sequence[tuple[float, float, str]], count: int | None = None) -> int:  # type: ignore[misc]
        """Place the city's walled merchant compounds: ROLL the count (30/40/30 for 1/2/3 at city
        scale, MERCHANT_ESTATE_WEIGHTS - a gated compound is an explicitly GRANTED privilege, see
        the table's reasoning), then seat the first n from `seats`, a hand-vetted ordered list of
        (x, y, gate_dir) candidates. Provide at least 3 seats so ANY roll can land - each is only
        used if rolled, and merchant_estate's slide fan + the estate-wall gate checks do the
        micro-siting safety work. `count=` pins the roll (the torii_count= analog). The resolved
        target is recorded as meta['merchant_estate_roll'] and gated by merchant_estates_match_roll,
        so a stale hand count can never ship again (the pre-roll state: both cities hand-placed
        exactly 1, a copied pattern with no recorded reasoning). The roll consumes NO main-stream
        RNG (dedicated Random seeded on the map seed), so a map that rolls its old count stays
        byte-identical."""
        scale = str(self.M.get("meta", {}).get("scale", "village"))
        n = int(count) if count is not None else roll_merchant_estate_count(scale, random.Random(self.seed * 1201 + 89))
        if n > len(seats):
            raise ValueError(
                f"merchant_estates rolled {n} compounds but only {len(seats)} vetted seats were provided - add candidate seats (the roll can ask for up to {max(c for c, _ in MERCHANT_ESTATE_WEIGHTS[scale])})"
            )
        for ex, ey, gd in seats[:n]:
            self.merchant_estate(ex, ey, gate_dir=gd)
        self.M["meta"]["merchant_estate_roll"] = n
        return n

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

    # urban building palette and default footprints, keyed by town caste/role
    URBAN = {
        "shop": ('#D8C49A', '#6B4F2A', 48, 32),  # merchant shophouse (modest)
        "merchant": ('#DDB87A', '#5A3F1E', 54, 36),  # merchant house+shop (the storefront, fronts the street)
        "merchant_house": ('#DDB87A', '#5A3F1E', 50, 34),  # a small/average merchant home (behind the storefront)
        "merchant_large": ('#E2BE7E', '#5A3F1E', 86, 60),  # a rich merchant's large home
        "laborer": ('#C2B190', '#6B5A3A', 34, 24),  # laborer dwelling (the standard ~87% - poorer hinin)
        "laborer_large": ('#CBB684', '#6B5A3A', 50, 34),  # a 'master' (rich) laborer's larger home (~12.5% of laborers, budgets.md) - the wealthier hinin who line the back streets
        "servant": ('#CDBE9C', '#6B5A3A', 30, 22),  # servant quarters (small)
        "monk_house": (
            '#C2B190',
            '#6B5A3A',
            34,
            24,
        ),  # an adept-monk household's home in a temple neighborhood (GM 2026-07-24) - DELIBERATELY identical to a laborer dwelling on the sheet (no label, no glyph of its own); the distinct kind exists for the checks, the budget, and the population math, not the eye
        "barn": ('#C9A57A', '#6B4F2A', 84, 56),
        "samurai": ('#DDB87A', '#5A3F1E', 56, 40),  # a junior samurai's small city house (most of the neighborhood)
        "samurai_large": ('#E0BC80', '#5A3F1E', 82, 58),  # a senior samurai's large city house (a minority; walled estates are OUTSIDE the walls)
        "civic": ('#CDB890', '#5A4326', 66, 46),
        "burakumin": ('#BCB29C', '#7A7058', 38, 26),
    }

    def building(self: Settlement, cx: float, cy: float, w: float, h: float, kind: str = "shop", rot: float = 0, of: Any = None) -> bool:  # type: ignore[misc]
        """An urban building (shophouse, laborer dwelling, samurai house, etc.) -
        boxier than a farmhouse, oriented to the street not the sun. Blocks placement.

        Returns False - and places NOTHING - for a commoner dwelling/business (WARD_BARRED_KINDS)
        whose center lies inside a declared samurai ward (GM 2026-08-02, on Minami: 2 laborer
        houses and a merchant row inside the ward fence, leaked in by whole-interior top-up sweeps
        whose rectangles overlap the ward). The refusal lives HERE, at the one seat every pack,
        frontage and gen-side top-up funnels through, rather than in each gen's region arithmetic -
        a refused candidate simply seats elsewhere on a later pass. Gated by
        city_samurai_ward_residents_only."""
        if self._samurai_ward_interiors and any(point_in_poly(cx, cy, rg) for rg in self._samurai_ward_interiors):
            if kind in WARD_BARRED_KINDS:
                return False
            # ...and a SERVANT inside the ward must be service accommodation BOUND to a samurai
            # household (`of`), never a freestanding cottage. Barring the commoner kinds alone just
            # handed their ground to the servant packs, and a servant glyph IS a laborer glyph with
            # a 4 ft trim - so the ward came back reading MORE commoner, not less (GM 2026-08-02).
            # Placed via servant_ranges(); see settlements/cities/government.md and its research.
            if kind == "servant" and of is None:
                return False
        fill, edge = self.URBAN.get(kind, self.URBAN["shop"])[:2]
        x0, y0 = -w / 2, -h / 2
        dash = ' stroke-dasharray="5,3"' if kind == "burakumin" else ''
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})">']
        # THE COSMETICS SCALE WITH THE THIN DIMENSION (settlement-review 2026-08-03). The fixed
        # rx=2 / stroke=1.6 / 0.60-length ridge were tuned on a squarish house and become absurd on
        # a LONG THIN footprint: at the servant range's 5 px depth the rounding is 40% of the depth
        # and the stroke 32% of it, so the fill is nearly eaten and the glyph reads as a pill - a
        # rail or a kerb, the sheet's vocabulary for small gray fixtures - rather than as a long
        # roof. A long rectangle with a full-length ridge reads as a nagaya; a capsule with a
        # center dash does not. Keyed off min(w, h), so every squarish building on every existing
        # map is untouched (min(w,h)/4 >= 2 and min(w,h)*0.22 >= 1.6 for anything 8 px or thicker).
        thin = min(w, h)
        rx = min(2.0, thin / 4.0)
        sw = min(1.6, thin * 0.22)
        ridge = 0.30 if max(w, h) < 2.5 * thin else 0.45  # half-extent: a range gets a ridge down its length, not a dash in its middle
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="{rx:.2f}" fill="{fill}" stroke="{edge}" stroke-width="{sw:.2f}"{dash}/>')
        g.append(f'<line x1="{-w * ridge:.1f}" y1="0" x2="{w * ridge:.1f}" y2="0" stroke="{edge}" stroke-width="0.8" opacity="0.6"/>')
        if kind in ("shop", "merchant"):
            # a BUSINESS: a striped awning along the street frontage + a hanging sign, so
            # commerce reads as visually distinct from plain housing.
            # TRUE SCALE with a legibility floor (GM 2026-07-23; was a fixed 6.5px strip + 11x9px
            # sign, which read as a ~20 ft awning and a 33x27 ft sign at the city's 3 ft/px): a
            # machiya storefront awning / deep eave runs a real ~3-6 ft, so the strip is 5 ft
            # scaled with the glyph grain (bscale) exactly like the footprint, floored at 2.4px so
            # it stays a visible band at city grain (true-or-floored, never inflated past the
            # floor). Stripe spacing/width scale with the depth to keep the town-tuned proportions.
            aw = max(5.0 * self.bscale, 2.4)
            ay = h / 2 - aw  # flush with the front wall - a real awning's street overhang is sub-pixel at every grain
            g.append(f'<rect x="{-w * 0.5:.1f}" y="{ay:.1f}" width="{w}" height="{aw:.1f}" fill="#A8472E" opacity="0.95"/>')
            sx = -w * 0.5 + 0.45 * aw
            while sx < w * 0.5:
                g.append(f'<rect x="{sx:.1f}" y="{ay:.1f}" width="{0.7 * aw:.1f}" height="{aw:.1f}" fill="#E8D2A8" opacity="0.55"/>')
                sx += 1.4 * aw
            # the hanging sign is a LOCATION MARKER, not a to-scale footprint (same doctrine as
            # the well, GM 2026-07-21): a real kanban is ~2-4 ft and would vanish at any grain, so
            # it scales with bscale but floors at a legible 6x5px, and it straddles the frontage
            # line rather than jutting a scaled 20+ ft into an 18-26 ft street.
            sgw, sgh = max(11 * self.bscale, 6.0), max(9 * self.bscale, 5.0)
            g.append(f'<rect x="{-sgw / 2:.1f}" y="{h / 2 - sgh / 2:.1f}" width="{sgw:.1f}" height="{sgh:.1f}" rx="1" fill="#E8D9A8" stroke="#6B4A22" stroke-width="0.8"/>')  # hanging sign
        else:
            # door stub: scales with the glyph grain like the awning, floored for visibility
            dh = max(3.2 * self.bscale, 1.6)
            g.append(f'<rect x="{-w * 0.16:.1f}" y="{h / 2 - dh:.1f}" width="{w * 0.32:.1f}" height="{dh:.1f}" fill="{edge}" opacity="0.8"/>')  # door
        g.append('</g>')
        self.add(''.join(g))
        rec: dict[str, Any] = {"x": cx, "y": cy, "w": w, "h": h, "kind": kind, "rot": rot}
        if of is not None:
            rec["of"] = [round(of["x"], 1), round(of["y"], 1)]  # the household this is service accommodation FOR
        self.M["buildings"].append(rec)
        self.placed.append((cx, cy, w, h))
        return True

    SERVANT_RANGE_DEPTH_FT = 15.0  # the measured nagayamon depth (Omura Yahei 2.5 ken; the Tokyo ICP gate 4.7 m)
    _OFFICE_STANDOFF = 15.0  # city_government_offices_dont_abut wants 14px of daylight; a px of margin over it

    def _solid_records(self: Settlement) -> list[dict[str, Any]]:  # type: ignore[misc]
        """Every drawn record on the map carrying a footprint, swept from the manifest rather than
        named in a list - so a feature added later is visible to placement without being remembered
        into it (the lesson `place_punishment_spot`'s caption probe paid for: skill CLAUDE.md,
        'the same disease turns up in PLACEMENT PROBES')."""
        out: list[dict[str, Any]] = []
        for key, recs in self.M.items():
            if key in ("labels", "title", "scalebar"):
                continue
            if isinstance(recs, dict) and "x" in recs and "w" in recs:
                out.append(recs)  # the singletons (governor_mansion, theater_stage)
            elif isinstance(recs, list):
                out += [r for r in recs if isinstance(r, dict) and "x" in r and "w" in r]
        return out

    def _blocks_any_door(self: Settlement, quad: Poly) -> bool:  # type: ignore[misc]
        """Would a footprint at `quad` stand in some building's DOORWAY?

        Mirrors `city_house_doors_unblocked`'s own geometry sample for sample - the door face
        centre, three lateral offsets, three depths - because placement and its check must read the
        same geometry, not merely the same data (skill CLAUDE.md). A rear service range is the seat
        that needs this: the ground behind a house is often the roji the row BEHIND it faces."""
        dc = 7.0 / self.ftpx  # DOOR_CLEAR_FT, the check's own constant
        qx = sum(p[0] for p in quad) / 4.0
        qy = sum(p[1] for p in quad) / 4.0
        qr = max(math.hypot(p[0] - qx, p[1] - qy) for p in quad)
        for o in self.M["buildings"]:
            if "w" not in o or math.hypot(o["x"] - qx, o["y"] - qy) > qr + math.hypot(o["w"], o["h"]) / 2 + dc + 2:
                continue
            th = math.radians(o.get("rot", 0.0))
            ux, uy = -math.sin(th), math.cos(th)  # the door face's outward normal
            vx, vy = -uy, ux
            fx, fy = o["x"] + ux * o["h"] / 2, o["y"] + uy * o["h"] / 2
            for d in (0.8, dc * 0.55, dc):
                for t in (-0.3 * o["w"], 0.0, 0.3 * o["w"]):
                    if point_in_poly(fx + ux * d + vx * t, fy + uy * d + vy * t, quad):
                        return True
        return False

    def _door_is_clear(self: Settlement, cx: float, cy: float, w: float, h: float, rot: float, skip: Any = None) -> bool:  # type: ignore[misc]
        """Does a footprint placed here have an unobstructed DOORWAY of its own?

        The mirror of `_blocks_any_door`, and sampled at exactly the same points the check uses -
        an earlier version approximated the door band with a small rect and let a blocker sitting
        between 2.0 and 2.33 px of the face slip through, which the gate then reported."""
        dc = 7.0 / self.ftpx
        th = math.radians(rot)
        ux, uy = -math.sin(th), math.cos(th)
        vx, vy = -uy, ux
        fx, fy = cx + ux * h / 2, cy + uy * h / 2
        near = [o for o in self._solid_records() if o is not skip and math.hypot(o["x"] - cx, o["y"] - cy) < math.hypot(w, h) / 2 + dc + math.hypot(o["w"], o.get("h", o["w"])) / 2 + 2]
        corners = [rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0)) for o in near]
        for d in (0.8, dc * 0.55, dc):
            for t in (-0.3 * w, 0.0, 0.3 * w):
                px_, py_ = fx + ux * d + vx * t, fy + uy * d + vy * t
                if any(point_in_poly(px_, py_, c) for c in corners):
                    return False
        return True

    def _office_records(self: Settlement) -> list[dict[str, Any]]:  # type: ignore[misc]
        """The government offices, which keep a standoff rather than merely not overlapping."""
        offices = list(self.M.get("ministries", []))
        gov = self.M.get("governor_mansion")
        return offices + ([gov] if gov else [])

    def servant_ranges(self: Settlement, hosts: Any = None) -> int:  # type: ignore[misc]
        """Attach each ward samurai household's SERVANT RANGE - the *nagaya* - to its own house.

        A samurai household's domestics lived inside the master's plot: in the perimeter nagaya
        that forms the street boundary itself, in the nagayamon gate rooms, or in nando off the
        kitchen. They never held a freestanding house in the buke-chi, and a Chinese elite compound
        says the same thing from the other side (servants in the daozuofang, the south row whose
        blank back IS the street wall). Ranks of small uniform dwellings are a real castle-town
        texture, but they are ashigaru kumi-yashiki on the town FRINGE - never inside the fence.
        Full findings + measured examples: research/cities/government.md.

        So the range is drawn as a LONG THIN building (15 real ft deep, running the length of its
        master's frontage) laid against the house's side and flush with its front plane - reading
        as that household's street range rather than as a cottage. It is recorded as an ordinary
        `servant` dwelling carrying `of`, so the population and caste arithmetic are untouched: a
        servant family is a property-holding, taxed household in budgets.md (a provincial city's
        120 servant families include 72 attached to its 60 samurai households - about one per
        junior house, two per senior), and this changes where they are DRAWN, never how many exist.

        LATERAL, not in front, because our in-city samurai houses are unwalled: history put the
        range on the plot boundary with the house set back behind it, but with no wall to hide
        behind, a range across the frontage would stand in its own master's doorway
        (`city_house_doors_unblocked`). Beside-and-flush keeps both doors on the open side.

        ORDERING: call AFTER every samurai house in the ward is placed (the census fills seat some)
        and AFTER s.ward, which is what defines the interior; but BEFORE the exact-population fill,
        so it can top the servant count up elsewhere. Returns the number attached."""
        if not self._samurai_ward_interiors:
            return 0
        depth = self.px(self.SERVANT_RANGE_DEPTH_FT)
        beds = [(st["pts"], st.get("w", 18) / 2) for st in self.M.get("town_streets", [])]
        beds += [(al["pts"], al.get("w", 10) / 2) for al in self.M.get("alleys", [])]
        if self.M.get("road"):
            beds.append((self.M["road"], self.M.get("road_width", 26) / 2))
        if self.M.get("ring_road"):
            beds.append((self.M["ring_road"], self.M.get("ring_road_width", 15) / 2))
        in_ward = [b for b in self.M["buildings"] if any(point_in_poly(b["x"], b["y"], rg) for rg in self._samurai_ward_interiors)]
        if hosts is None:
            hosts = [b for b in in_ward if b["kind"] in ("samurai", "samurai_large")]
        # IDEMPOTENT: count what each household already has, so the pass can be run again after a
        # late household top-up without giving anyone a second (or third) range over its quota.
        had: dict[tuple[float, float], int] = {}
        for r in self.M["buildings"]:
            if r["kind"] == "servant" and "of" in r:
                k = (round(r["of"][0], 1), round(r["of"][1], 1))
                had[k] = had.get(k, 0) + 1
        placed = 0
        for b in hosts:
            want = (2 if b["kind"] == "samurai_large" else 1) - had.get((round(b["x"], 1), round(b["y"], 1)), 0)  # budgets.md: 2 servant families to a senior house, 1 to a junior
            th = math.radians(b.get("rot", 0.0))
            ux, uy = math.cos(th), math.sin(th)  # the house's LOCAL +x (along its frontage)
            fx, fy = -math.sin(th), math.cos(th)  # its LOCAL +y - the door/front side
            # SEATS, in the order the sources put them. The nagaya on a FLANK, flush with the
            # frontage, is the first choice - that is the range that forms the plot's street
            # boundary. Where a terraced neighbor leaves no flank, the REAR service row is the
            # attested fallback (China's houzhaofang; Japan's service wing behind the house), and a
            # SHORTER range is tried before giving up, since a nagayamon need not span the whole
            # frontage. A household with no seat at all simply has no separate servant dwelling -
            # which is itself attested: below ~100-300 koku the domestics slept in nando off the
            # master's kitchen, with no building of their own.
            _lens = (b["w"], b["w"] * 0.78)  # a nagayamon need not span the whole frontage; shorten before giving up
            # SEAT ORDER, and it is a LEGIBILITY rule as much as a historical one
            # (settlement-review 2026-08-03). A single appendage stuck to one corner of a ROTATED
            # box stops reading as a plot and starts reading as an implement - the reviewer read
            # four of these as a paintbrush and a meat cleaver before reading them as households.
            # So: take both flanks at full length first (a house with ranges to either side reads
            # as a frontage, not a handle), and for the two-range senior house prefer the SAME
            # side, giving a doubled range rather than one flank plus one rear stub.
            seats = [(sd, ln, False) for ln in _lens for sd in (1, -1)]
            seats += [(sd, ln, True) for ln in _lens for sd in (1, -1)]
            for side, length, rear in seats:
                if want <= 0:
                    break
                if length < 3.0 * depth:
                    continue  # below ~3x depth it stops reading as a range and starts reading as a blob (settlement-review
                    # 2026-08-03 found the 2.3x floor's 35x15 ft seats doing exactly that). A household with no seat this
                    # long simply goes without, which the docstring already justifies.
                rrot = (b.get("rot", 0.0) + 180.0) if rear else b.get("rot", 0.0)  # a rear range turns its door away from the house
                if rear:
                    off = b["h"] / 2 + depth / 2 + 0.6  # tucked behind the back wall, like the merchant kura
                    ox, oy = b["x"] - fx * off, b["y"] - fy * off
                else:
                    off = b["w"] / 2 + length / 2 + 0.6  # a hair of daylight: sat_overlap ignores touching, but never risk it
                    fo = (b["h"] - depth) / 2  # flush with the house's front plane
                    ox, oy = b["x"] + ux * off * side + fx * fo, b["y"] + uy * off * side + fy * fo
                quad = rot_rect(ox, oy, length, depth, rrot)
                if not all(any(point_in_poly(qx, qy, rg) for rg in self._samurai_ward_interiors) for qx, qy in quad):
                    continue  # the whole range stays inside the fence
                # ...and CLEAR of the fence's own ink. "Inside the interior polygon" is the fence
                # LINE, and the palisade is stroked 5px wide, so a range flush to the boundary is
                # geometrically inside it and still drawn through it (city_ward_fence_clear_of_structures).
                if any(seg_dist(ox, oy, wb[i], wb[i + 1]) < max(length, depth) / 2 + self._WARD_STROKE for wd in self.M.get("wards", []) for wb in [wd["boundary"]] for i in range(len(wb) - 1)):
                    continue
                if self.bound and not all(point_in_poly(qx, qy, self.bound) for qx, qy in quad):
                    continue
                if any(seg_dist(ox, oy, pts[k], pts[k + 1]) < half + max(length, depth) / 2 + 2 for pts, half in beds for k in range(len(pts) - 1)):
                    continue  # a range is a building on the verge, not an obstruction in the roadbed
                # CLEAR OF EVERY SOLID THING, found by SWEEPING the manifest rather than by a hand
                # list of keys. The first cut here tested only `buildings` and `houses`, and the
                # ranges promptly landed on the martial hall, a dojo and four ministry aprons - the
                # same defect the punishment-ground caption probe had (skill CLAUDE.md: a probe must
                # iterate any manifest list of dicts carrying w/h, or the next feature is invisible
                # to it). Offices additionally keep their 14px standoff
                # (`city_government_offices_dont_abut`), so they are tested against an inflated range.
                if any(rects_overlap(quad, rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0))) for o in self._solid_records() if o is not b):
                    continue
                # THE OFFICE STANDOFF, MEASURED THE WAY THE CHECK MEASURES IT - AABB to AABB.
                # `city_government_offices_dont_abut` compares axis-aligned BOUNDS, while this
                # probe used to inflate the range's ROTATED rect and test that: for a range drawn
                # at its host's frontage angle the two disagree by up to the difference between its
                # half-depth and its half-diagonal, so Nagahara seated a -109 deg servant range
                # 13.96px off the Ministry of Works - clear on the probe's measure, abutting on the
                # gate's (2026-08-08). Same rule as the punishment-ground caption probe: a probe
                # must measure the box the CHECK will measure (skill CLAUDE.md).
                if any(_aabb_gap(quad, rot_rect(o["x"], o["y"], o["w"], o["h"], o.get("rot", 0))) < self._OFFICE_STANDOFF for o in self._office_records()):
                    continue
                _hostgap = min(poly_gap(quad, rot_rect(b["x"], b["y"], b["w"], b["h"], b.get("rot", 0))), 1e9)
                if any(poly_gap(quad, rot_rect(o["x"], o["y"], o["w"], o.get("h", o["w"]), o.get("rot", 0))) < _hostgap for o in self.M["buildings"] if o is not b):
                    continue  # it must read as ITS OWN household's range: nothing may touch it more closely than its host
                if self._blocks_any_door(quad):
                    continue  # a range is service accommodation on the household's own ground, never a wall across a neighbor's entrance
                if not self._door_is_clear(ox, oy, length, depth, rrot, skip=b):
                    continue  # ...and its OWN door has to open onto open ground
                if self.building(ox, oy, length, depth, "servant", rrot, of=b):
                    placed += 1
                    want -= 1
        return placed

    def _dims(self: Settlement, kind: str) -> tuple[float, float]:  # type: ignore[misc]
        w, h = self.URBAN.get(kind, self.URBAN["shop"])[2:]
        return w * self.bscale, h * self.bscale

    def try_building(self: Settlement, cx: float, cy: float, kind: str, rot: float = 0) -> bool:  # type: ignore[misc]
        w, h = self._dims(kind)
        if self._fits(cx, cy, w, h):
            return self.building(cx, cy, w, h, kind, rot)
        return False

    def _face_street_rot(self: Settlement, x: float, y: float) -> tuple[float | None, float]:  # type: ignore[misc]
        """Rotation that turns a building's frontage toward the nearest street/road, and
        the distance to it. (None, inf) if there are no streets."""
        lines = [st["pts"] for st in self.M.get("town_streets", [])]
        if self.M.get("road"):
            lines.append(self.M["road"])
        best: Any = None
        bd = 1e18
        for sp in lines:
            for k in range(len(sp) - 1):
                cx, cy = seg_closest(x, y, sp[k], sp[k + 1])
                d = math.hypot(cx - x, cy - y)
                if d < bd:
                    bd, best = d, (cx, cy)
        if best is None:
            return None, 1e18
        dx, dy = best[0] - x, best[1] - y
        dl = math.hypot(dx, dy) or 1
        return math.degrees(math.atan2(-dx / dl, dy / dl)), bd

    def open_face_rot(self: Settlement, cx: float, cy: float, w: float, h: float, clear_ft: float = 8.0, prefer: Any = (0, 180, 270, 90)) -> float | None:  # type: ignore[misc]
        """The rotation whose DOOR side (the local +h/2 face) opens onto clear ground - or None
        if every cardinal is walled in. GM doctrine (2026-07-18): a farmhouse always faces SOUTH
        (its garden and threshing ground need the sun), but a CITY house has no sun constraint
        and must instead have an UNBLOCKED entrance - the door faces open space (street, roji,
        court), never the back of another building an eave-gap away. Tries `prefer` in order and
        returns the first whose door-front band (`clear_ft` real feet deep) contains no placed
        footprint; conservative AABB test against self.placed (rotated neighbors are close
        enough to axis-aligned at row scales for a placement-time choice - the gate check does
        the exact geometry)."""
        clear = self.px(clear_ft)
        for rot in prefer:
            th = math.radians(rot)
            ux, uy = -math.sin(th), math.cos(th)
            fx, fy = cx + ux * h / 2, cy + uy * h / 2
            ok = True
            for ox, oy, ow, oh in self.placed:
                if abs(ox - cx) > (w + ow) / 2 + clear + 2 or abs(oy - cy) > (h + oh) / 2 + clear + 2:
                    continue
                for d in (1.0, clear * 0.55, clear):
                    for t in (-0.3 * w, 0.0, 0.3 * w):
                        px_, py_ = fx + ux * d - uy * t, fy + uy * d + ux * t
                        if abs(px_ - ox) < ow / 2 and abs(py_ - oy) < oh / 2:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                return float(rot)
        return None

    def rowpack(self: Settlement, bbox: Any, items: Any, court_every: int = 2, court_ft: float = 21, eave_ft: float = 4, seam: float = 0.4, fill: bool = False) -> int:  # type: ignore[misc]
        """CITY row housing - the machiya/nagaya fabric (GM row-packing doctrine, 2026-07):
        urban commoners did not build detached-with-yard; street frontage was taxed and precious,
        back-lot nagaya were literally one roof over a row of family units, and Chinese county-seat
        housing shared party walls in continuous street walls. So dwellings go down as CONTIGUOUS
        TERRACES, not a scatter:
          - rows run E-W; houses TOUCH within a row (a hairline `seam` of 0.4px keeps the SAT
            overlap gate honest - independent structures grown together, outlines merging into
            a terrace strip);
          - rows come in BACK-TO-BACK PAIRS with both doors facing OUTWARD (GM doctrine
            2026-07-18): the first row of a pair faces UP (rot 180), the second DOWN (rot 0),
            their backs sharing the ~3-6 ft eave/drainage gap (`eave_ft` - rain drip, gutter,
            night-soil access - NOT an entrance). A city house has no farmhouse-style
            south-facing sun constraint; what it must have is an unblocked entrance;
          - after every pair a WALKABLE gap opens - a roji lane (~12 ft) by default, widening
            to a COURT (`court_ft`, ~15-25 ft, the idobata courtyard) every ~`court_every`
            rows - so rows never stack more than TWO deep and no household is trapped behind
            another (the city_house_doors_unblocked / city_rows_max_two_deep gates);
          - rows front the caller's roji/alleys TIGHTLY (a real roji had walls you could touch
            from its centerline) but stand a frontage-band back from real streets and the road,
            where the shop rows live. Draw the zone's alleys BEFORE calling this.
        Streets/roads/prior placements break a row naturally (the odd firebreak gap is
        historically honest). Dwelling sizes come from URBAN kinds via bscale, with mild
        per-house jitter so the terrace reads grown-up-over-time, not stamped.
        Returns the number placed."""
        # SCOPED (2026-08-08) - see pack(): same stream jitter, same cascade, same bbox key.
        with self.rng_scope("rowpack", *bbox):
            x0, y0, x1, y1 = bbox
            items = list(items)
            n0 = len(self.placed)  # obstacle snapshot: everything placed BEFORE this call
            court_px, eave_px = self.px(court_ft), max(self.px(eave_ft), 1.2)
            roji_px = max(self.px(12), 4.5)  # the walkable between-pairs lane: >= ~12 real ft, floored for legibility (vs the ~7 ft door-clear line the checks enforce)
            # linework the rows must respect: tight against alleys (roji), a frontage band off
            # streets/roads (the shop rows own that ground)
            lines = [(al["pts"], al.get("w", 10) / 2 + max(self.px(3), 2.5)) for al in self.M.get("alleys", [])]  # 2.5 >= the overlap gate's +2 margin
            lines += [(st["pts"], st.get("w", 18) / 2 + self.px(28)) for st in self.M.get("town_streets", [])]
            if self.M.get("road"):
                lines.append((self.M["road"], self.M.get("road_width", 26) / 2 + self.px(28)))
            if self.M.get("ring_road"):
                lines.append((self.M["ring_road"], self.M.get("ring_road_width", 7) / 2 + max(self.px(3), 2.5)))

            def seg_hits_rect(a: Any, b: Any, rx0: float, ry0: float, rx1: float, ry1: float) -> bool:
                # slab-clip the segment against the rect (exact for axis-aligned rects)
                (ax, ay), (bx, by) = a, b
                dx, dy = bx - ax, by - ay
                t0, t1 = 0.0, 1.0
                for p, q in ((-dx, ax - rx0), (dx, rx1 - ax), (-dy, ay - ry0), (dy, ry1 - ay)):
                    if p == 0:
                        if q < 0:
                            return False
                    else:
                        t = q / p
                        if p < 0:
                            if t > t1:
                                return False
                            t0 = max(t0, t)
                        else:
                            if t < t0:
                                return False
                            t1 = min(t1, t)
                return True

            def rect_ok(cx: float, cy: float, w: float, h: float) -> bool:
                corners = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
                for px_, py_ in corners + [(cx, cy)]:
                    if px_ < 55 or px_ > self.W - 55 or py_ < 88 or py_ > self.H - 26:
                        return False
                    if self.bound and not point_in_poly(px_, py_, self.bound):
                        return False
                    if self._in_blocked(px_, py_):
                        return False
                for pts, half in lines:  # exact rect-vs-polyline clearance (a corner
                    ex0, ey0 = cx - w / 2 - half, cy - h / 2 - half  # sample would miss a lane crossing
                    ex1, ey1 = cx + w / 2 + half, cy + h / 2 + half  # between two corners)
                    for k in range(len(pts) - 1):
                        if seg_hits_rect(pts[k], pts[k + 1], ex0, ey0, ex1, ey1):
                            return False
                r = math.hypot(w, h) / 2
                return all(math.hypot(cx - ox, cy - oy) >= r + math.hypot(ow, oh) / 2 + 1 for ox, oy, ow, oh in self.placed[:n0])

            n, idx, row = 0, 0, 0
            ytop = y0
            while items and idx < len(items):
                rowmax = 0.0
                x = x0 + self._hjit(x0, ytop, 0.7) * 4  # ragged row starts (not a stamped grid)
                while x < x1 and idx < len(items):
                    kind = items[idx]
                    bw, bh = self._dims(kind)
                    bw *= 0.94 + self._hjit(x, ytop, 1.3) * 0.24  # grown-over-time variation, still touching
                    bh *= 0.95 + self._hjit(x, ytop, 2.1) * 0.15
                    if x + bw > x1:
                        break
                    cx, cy = x + bw / 2, ytop + bh / 2
                    # pair-facing doctrine: first row of each pair faces UP (door at its top
                    # edge, onto the walkable gap above), second faces DOWN - backs meet
                    # across the eave gap, every door opens outward onto roji/court ground.
                    # building() may REFUSE the seat (a commoner unit inside a samurai ward) -
                    # the terrace then breaks there and the scan steps past, same as an obstacle.
                    if rect_ok(cx, cy, bw, bh) and self.building(cx, cy, bw, bh, kind, 180 if row % 2 == 0 else 0):
                        n += 1
                        idx += 1
                        rowmax = max(rowmax, bh)
                        x += bw + seam  # party wall: the next unit starts AT this one's gable
                    else:
                        x += 5  # an obstacle breaks the terrace; scan past it
                if rowmax == 0.0:
                    rowmax = self._dims("laborer")[1]  # an entirely-blocked row still advances
                row += 1
                if row % 2 == 1:
                    gap = eave_px  # inside a pair: the back-to-back eave/drainage gap
                elif (row // 2) % max(1, round(court_every / 2)) == 0:
                    gap = court_px  # a full idobata court every ~court_every rows
                else:
                    gap = roji_px  # between pairs: a walkable roji so both pair-fronts have entrance ground
                ytop += rowmax + gap
                if ytop + self._dims("laborer")[1] > y1:
                    break
            # RECORD THE SHORTFALL, like pack and frontage (settlement-review, 2026-08-11):
            # rowpack was the ONE placer that dropped what did not fit in silence, so
            # placement_runs_meet_their_ask - the check written to make exactly this visible - was
            # blind to it on the very map it was written for. Two monzen flanks drew 1 and 0 of 40
            # and another row 4 of 24, all behind a green gate.
            if not fill:  # fill=True declares the ask a capacity BUDGET ("row this ground out"), as in pack/frontage
                # items[idx:], NOT items: rowpack walks an INDEX where pack and frontage POP, so
                # handing the whole list over reported every run as asking exactly double what it
                # was given - and a run that seated half its ask looked like one that seated a
                # quarter, forever, because trimming to the reported figure just halved it again.
                self._shortfall("rowpack", bbox, n, list(items[idx:]))
            return n

    def pack(self: Settlement, bbox: Any, items: Any, rot: float = 0, step: float = 46, face_streets: Any = False, fill: bool = False, footpaths: int = 0) -> int:  # type: ignore[misc]
        """Densely fill a district bbox with a list of building kinds (one building
        each), grid-scan + jitter, skipping the road, blocked regions, and occupied
        spots. With face_streets, each building rotates to face its nearest street.
        Returns the number placed. Leftovers WARN via _shortfall unless fill=True
        declares the request a capacity BUDGET ("place up to N") rather than an exact
        count - the city gens' 600-samurai district fills are the idiom.

        `footpaths=N` lays a worn TRODDEN PATH across the district every N*step of its
        depth - before the scan, so `_fits` refuses any spot on the tread - and the quarter
        then reads as BLOCKS rather than a scatter of boxes.
        WHY (GM 2026-07-27, after settlement-review found the warrens had no circulation
        at all): a dense commoner quarter is served by narrow TRODDEN FOOTPATHS between
        the house rows - not paved streets, which were far beyond a quarter's means. The
        cities already carry `alleys` + `town_streets`; it was the UNWALLED TOWNS whose
        warrens hung straight off the trunk road with nothing between them (Hoshizora and
        Ubame both recorded zero lanes, zero alleys and zero streets).

        The path is laid FIRST rather than threaded between placed buildings, which is the
        whole point: clearance is then true by construction, instead of a path dodging
        jittered footprints and clipping one every few maps. It costs a little capacity
        (a ~30px no-build band), so a district that was exactly full may need a slightly
        bigger bbox. Default 0 keeps every existing map bit-identical - no corridor, and
        no RNG draw that could shift a single downstream spot."""
        # SCOPED (2026-08-08). The per-seat jitter below is a stream draw, so any upstream change
        # that consumed a different number of random numbers moved every building this pack seats -
        # and one moved building cascades into the gardens, groves, wells and crowns around it. This
        # was the first divergence left in a town once the pasture outline was scoped. Keyed on the
        # BBOX with rng_scope's per-key counter, so a quarter re-rolls when you move THAT quarter,
        # a second pack over the same ground still draws its own numbers, and adding a pack in one
        # quarter cannot renumber another.
        with self.rng_scope("pack", *bbox):
            x0, y0, x1, y1 = bbox
            items = list(items)
            n = 0
            gy = y0 + step / 2
            if footpaths:
                # Lay the paths BEFORE the scan, so `_fits` refuses any spot on the tread and the
                # clearance is true by construction. The first design reserved every Nth GRID ROW
                # instead, which was depth-dependent and therefore useless here: under the exact-
                # population rule these quarters are only two or three rows deep, so the reserved row
                # was never reached and the pack drew no path at all. Spacing off the bbox rather than
                # off the row counter makes the paths independent of how many houses are requested.
                _spacing = footpaths * step
                _py = y0 + _spacing
                while _py < y1 - step * 0.5:
                    # TRIM THE PATH TO GROUND THAT IS ACTUALLY FREE. A corridor only refuses spots taken
                    # AFTER it exists, so anything already standing - a district bbox routinely overlaps
                    # the road frontage placed earlier in the gen - is immune to it and the tread would be
                    # drawn straight through a shopfront. So walk the span, keep the longest clear run,
                    # and emit only if enough of it survives to read as a path rather than a stub.
                    # Clearance is scaled to the STEP because `_near_corridor` tests a building's CENTER:
                    # at a flat 15 a house sat 15px off the tread and put its footprint through it (the
                    # centre-vs-footprint family again - see the skill CLAUDE.md).
                    _clr = max(20.0, step * 0.62)
                    _run: list[float] = []
                    _best: list[float] = []
                    _px = x0 + 4
                    while _px <= x1 - 4:
                        if self._fits(_px, _py, step * 0.5, step * 0.5, corridors=False):
                            _run.append(_px)
                        else:
                            if len(_run) > len(_best):
                                _best = _run
                            _run = []
                        _px += 10
                    if len(_run) > len(_best):
                        _best = _run
                    if _best and (_best[-1] - _best[0]) >= 0.4 * (x1 - x0):
                        self.lane([(_best[0], _py), (_best[-1], _py)], width=5, clearance=_clr, worn=True)
                    _py += _spacing
            while gy < y1 and items:
                gx = x0 + step / 2
                while gx < x1 and items:
                    jx, jy = random.uniform(-step * 0.28, step * 0.28), random.uniform(-step * 0.28, step * 0.28)
                    if face_streets:
                        fr, fd = self._face_street_rot(gx + jx, gy + jy)
                        if face_streets == "core":
                            if fr is not None and fd <= 76:
                                gx += step  # leave the street-facing band for shop frontage; dwellings pack the INTERIOR
                                continue
                            r = rot + random.uniform(-6, 6)  # ONLY the deep block core, set back behind the frontage line
                        elif fr is not None and fd <= 92:
                            r = fr + random.uniform(-4, 4)  # near a street: face it
                        elif face_streets == "fill":
                            r = rot + random.uniform(-6, 6)  # deep block core (e.g. tenement housing)
                        else:
                            gx += step  # businesses only line the frontage
                            continue
                    else:
                        r = rot + random.uniform(-6, 6)
                    # a scattered (non-street-facing) house still needs an UNBLOCKED door: keep the
                    # street-facing rotation when one was chosen, else pick the cardinal whose door
                    # side opens onto clear ground (doctrine 2026-07-18; skip a spot walled on all 4).
                    # RNG-NEUTRAL by construction: the prefer order starts at the pack's own base
                    # rotation and the already-drawn jitter is REUSED (no extra random draws), so a
                    # map whose scatter never actually blocks a door regenerates bit-identically to
                    # the pre-doctrine engine - the doctrine only perturbs the spots it must.
                    if not (face_streets and fr is not None and fd <= 92):
                        w_, h_ = self._dims(items[0])
                        base = (round(rot / 90) * 90) % 360
                        orot = self.open_face_rot(gx + jx, gy + jy, w_, h_, prefer=(base, (base + 180) % 360, (base + 270) % 360, (base + 90) % 360))
                        if orot is None:
                            gx += step
                            continue
                        r = orot + (r - rot)
                    if self.try_building(gx + jx, gy + jy, items[0], r):
                        items.pop(0)
                        n += 1
                    gx += step
                gy += step
            if not fill:
                self._shortfall("pack", bbox, n, items)
            return n

    def _shortfall(self: Settlement, fn: str, where: Any, placed: int, left: list[Any]) -> None:  # type: ignore[misc]
        """A placement helper SILENTLY dropping what does not fit is how authored-vs-landed
        drift happens (the 2026-07-24 town audit: Hirameki's gate market authored 12
        businesses, landed 4, and nothing said so - the "no silent caps" principle applied
        to pack/frontage). Loudly report any shortfall; the gen author decides whether to
        make room, trim the request to the ground truth, or mark the call fill=True when
        the request is deliberately a capacity budget. An unmarked warning is a standing
        TODO to make that call."""
        if left:
            want = placed + len(left)
            kinds = ", ".join(f"{k} x{c}" for k, c in Counter(left).items())
            print(f"{fn.upper()} SHORTFALL at {where}: placed {placed}/{want} (dropped {kinds})")
            # ...and RECORD it (GM 2026-08-05: "we definitely want that to be visible"). Printing
            # alone sends the one number that measures authored-vs-landed drift to a terminal
            # nobody keeps: a map shipping 88 of its 118 merchant households read exactly like one
            # that met its budget, and the only reason it was ever noticed was a perf investigation.
            # Recorded, it is reviewable after the fact and gateable in future. Deliberately NO
            # geometry key names (x/pts/poly/outline/boundary) - this is a diagnostic, not a drawn
            # feature, and every_feature_classified_for_overlap keys off exactly those names.
            self.M.setdefault("shortfalls", []).append(
                {
                    "by": fn,
                    "at": [round(float(v), 1) for v in (where if not isinstance(where[0], (list, tuple)) else [c for p in where for c in p])],
                    "placed": placed,
                    "wanted": want,
                    "dropped": kinds,
                }
            )

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

    def theater_stage(self: Settlement, cx: float, cy: float, w: Any = None, h: Any = None, rot: float = 0, label: Any = None, kind: str = "monzen") -> None:  # type: ignore[misc]
        """A public THEATER STAGE: a roofed raised stage facing an open viewing ground - the troupe-and-
        festival venue of a Rokugani town/city (the East Asian analog of a Greco-Roman amphitheater: a
        temple OPERA STAGE / shrine NOH-kagura stage). It belongs to a temple/monastery precinct, the
        audience gathering in the open ground between the stage and the hall. (cx,cy) is the center of the
        w x h viewing ground; the roofed stage sits at the -y (north) end facing +y into it; `rot` turns the
        whole feature (point it so the ground opens toward the temple). Records M['theater_stage'] - a LIST
        since 2026-08-10: the singleton dict write meant a second stage clobbered the first, so Shiro
        Daika's labeled entertainment-quarter theater existed as ink only, invisible to the overlap
        matrix in both directions (settlement-review). `kind` says which siting doctrine the stage owes:
        "monzen" (default) is a temple/shrine performance stage and must sit at its hall;
        "machi" is a commercial quarter theater and sits in the fabric. Reserves its footprint so
        packing avoids it."""
        if w is None:
            w, h = self.px(150), self.px(105)  # stage + viewing ground ~150x105 ft (town-calibrated)
        hw, hh = w / 2, h / 2
        sw, sh = w * 0.5, h * 0.26  # the roofed stage at the north end
        sy = -hh - sh * 0.5  # straddling the ground's north edge
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w:.0f}" height="{h:.0f}" rx="4" fill="#E4D6B0" stroke="#A98E54" stroke-width="1.5"/>')  # the swept earthen viewing ground
        g.append(f'<rect x="{-hw + 5:.0f}" y="{-hh + 5:.0f}" width="{w - 10:.0f}" height="{h - 10:.0f}" rx="3" fill="none" stroke="#C9B484" stroke-width="0.7" opacity="0.6"/>')
        for i in range(3):  # a few faint rows of standing crowd in the ground
            ry = -hh + h * (0.40 + 0.17 * i)
            for k in range(7):
                px = -hw + 14 + (w - 28) * (k + 0.5) / 7
                g.append(f'<circle cx="{px:.0f}" cy="{ry:.0f}" r="1.7" fill="#8A7A56" opacity="0.5"/>')
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh:.0f}" rx="2" fill="#C9A57A" stroke="#5A3F1E" stroke-width="1.8"/>')  # stage platform
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy:.0f}" width="{sw:.0f}" height="{sh * 0.36:.0f}" fill="#7A5A30"/>')  # its roof
        # NO painted-pine roundel. The kagami-ita's pine is painted on the VERTICAL back board, so a
        # plan view cannot see it at all - and drawn as a green disc it used the sheet's own
        # vegetation idiom and read as a bush growing on the stage (settlement-review, Ubame).
        g.append(f'<rect x="{-sw / 2:.0f}" y="{sy + sh - 2.5:.0f}" width="{sw:.0f}" height="2.5" fill="#5A3F1E" opacity="0.6"/>')  # stage-front lip onto the ground
        g.append('</g>')
        self.add(''.join(g))
        self.M.setdefault("theater_stage", []).append({"x": cx, "y": cy, "w": w, "h": h, "rot": rot, "kind": kind})
        R = math.hypot(hw, hh) + sh * 0.5  # rotation-safe covering radius (stage + ground)
        self.ellipses.append((cx, cy, R, R))
        if label:
            # Offset from the ROTATED extent, not the raw half-height. At rot=90 the ground's reach
            # along +y is hw, not hh, so the caption landed INSIDE the ground it names, with the
            # outline stroke running through the text (settlement-review, Ubame, 2026-07-26).
            # Identical to the old expression at rot=0, so unrotated stages are untouched.
            # Seat by the STANDOFF LADDER against the stage's ROTATED extent, hinted at the historical
            # spot. Two bugs, one fix: the old `cy + hh + 16` used the unrotated half-height, so a
            # rot=90 stage captioned INSIDE its own ground (Ubame); and a hand seat has no idea what
            # else is there, so simply correcting the reach dropped Tango's caption onto a monk house.
            # The hint keeps every UNROTATED stage exactly where it was whenever that seat is clear.
            _a = math.radians(rot)
            _rx = abs(hw * math.cos(_a)) + abs(hh * math.sin(_a))
            _ry = abs(hw * math.sin(_a)) + abs(hh * math.cos(_a))
            self.place_caption(label, (cx - _rx, cy - _ry, cx + _rx, cy + _ry), 11, italic=True, hint=(cx, cy + _ry + 16), rot=rot)

    def fire_tower(self: Settlement, x: float, y: float, tw: float | None = None, rot: float = 0.0, label: str = "fire tower") -> int:  # type: ignore[misc]
        """A HINOMI-YAGURA (fire-watch tower): a tall, slender braced-timber tower with a lookout
        platform and an alarm bell (hansho), standing in the dense COMMONER quarter of a walled
        town or city where packed wooden rooftops make fire catastrophic. It is a CIVILIAN interior
        structure - the magistrate's fire-watch - distinct from a wall guard tower (military, on the
        rampart): drawn as an OPEN braced frame (not the guard tower's solid block) with a red bell.
        The watchman strikes the bell in a cadence that tells the town how near the fire is. Records
        M['fire_towers'] (an overlap-checked struct: it must stand clear of the wall, roads, and
        buildings) and reserves a small no-build block (it needs clear sightlines). Place it among the
        laborer/merchant blocks. See the settlements.md 'Fire towers' historical grounding."""
        if tw is None:
            tw = self.px(26)  # a real hinomi-yagura frame is ~26 ft square (town-calibrated glyph)
        h = tw / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-h - 2:.0f}" y="{-h - 5:.0f}" width="{tw + 4}" height="5" rx="1" fill="#7A5A30"/>')  # the little roof cap over the lookout platform
        g.append(f'<rect x="{-h:.0f}" y="{-h:.0f}" width="{tw}" height="{tw}" fill="#EFE6CC" fill-opacity="0.45" stroke="#7A5A30" stroke-width="2"/>')  # the open braced-timber frame
        g.append(f'<line x1="{-h:.0f}" y1="{-h:.0f}" x2="{h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')  # cross-braces (an X)
        g.append(f'<line x1="{h:.0f}" y1="{-h:.0f}" x2="{-h:.0f}" y2="{h:.0f}" stroke="#7A5A30" stroke-width="1.1"/>')
        g.append(f'<circle cx="0" cy="0" r="{tw * 0.2:.1f}" fill="#B0462F" stroke="#5A3F1E" stroke-width="0.8"/>')  # the alarm bell (hansho)
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M["fire_towers"].append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": round(rot, 1), "z": z, "label": label})
        self.placed.append((x, y, tw, tw))
        bm = 16
        self.block_polys.append([(x - h - bm, y - h - bm), (x + h + bm, y - h - bm), (x + h + bm, y + h + bm), (x - h - bm, y + h + bm)])
        if label:
            _t = label_tilt(rot)
            _lx, _ly = tilt_caption_seat(x, y, rot, _t, h, h, 14) if _t else (x, y + h + 14)
            self.label(_lx, _ly, label, 9, italic=True, color="#7A5A30", rot=_t)
        return z

    def kosatsuba(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "notice board", label_above: bool = False, label_xy: Pt | None = None) -> int:  # type: ignore[misc]
        """The KOSATSUBA - the settlement's official notice board: a small roofed frame posting
        the state's STANDING LAW (edicts, porter/packhorse rate tables, ban lists). Sited at the
        most TRAFFICKED public point - the highway frontage, the main street by the gate, a
        bridgehead or market corner - because it is the state talking at everyone who passes
        (Edo's principal board stood at Nihonbashi, the bridgehead). NEVER defaulted to the
        magistrate's manor gate: the manor's own board (Mode A program, buildings.md) posts the
        bench's OUTPUT (verdicts, bounties) for people who come to court, and the manor sits at
        the settlement edge where feet do not pass. True size ~12x5 ft (a 7x3 ft board under a
        small roof); the label carries the read.

        `rot` IS THE ROAD'S BEARING, not a free choice. The glyph's long axis is the board's
        FACE, so a board must stand square to the way it fronts - broadside to the traffic that
        reads it. Turned perpendicular, the face goes edge-on to everyone approaching and the
        institution fails while the siting checks stay green (that is exactly how Nagahara's
        third board shipped, GM 2026-07-27). Hand placements must pass the fronted route's
        bearing; `place_kosatsuba` derives it. Held by `kosatsuba_faces_the_road`. Records M['kosatsuba'] (an overlap-checked
        struct). WHY: settlements.md 'Notice board (kosatsuba)'. Place LAST, on a clear verge
        beside the road, like the fire tower.

        The DRAWN glyph is a LOCATION MARKER at the coarse tiers (GM call 2026-07-24, taking the
        escape settlements.md documented): the true 12x5 ft frame draws 6x2.5 px at village grain
        and 4x1.7 px at city grain - at city scale, rotated upright, that is a 1.7 px sliver that
        reads as gate hardware, not a feature (Nagahara: two of its three boards were invisible
        until the GM went looking, and the one that read did so only by its label). So the glyph
        is floored at KOSATSUBA_MARKER_MIN_PX on its long axis with the 12:5 aspect preserved -
        the wells' doctrine exactly (SKILL.md 'to scale'): the marker denotes the board's
        TO-SCALE LOCATION with legible pixels that are not themselves claimed to be to scale. The
        floor NEVER shrinks a board, so hamlets and towns (1 ft/px) still draw the true 12x5 px;
        only village and city grain lift. The manifest keeps the TRUE w/h (so a size audit reads
        real feet) and records the drawn box as vw/vh, which is what the overlap checks and the
        placement reservation use - the pixels that can actually collide."""
        w, h = self.px(12), self.px(5)
        k = max(1.0, KOSATSUBA_MARKER_MIN_PX / w)  # marker floor, aspect preserved
        vw, vh = w * k, h * k
        hw, hh = vw / 2, vh / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hw:.1f}" y="{-hh:.1f}" width="{vw:.1f}" height="{vh:.1f}" rx="1" fill="#7A5A30" stroke="#5A3F1E" stroke-width="0.8"/>')  # the little tiled roof, seen from above
        g.append(f'<line x1="{-hw:.1f}" y1="0" x2="{hw:.1f}" y2="0" stroke="#EFE6CC" stroke-width="0.9"/>')  # the ridge
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M["kosatsuba"].append({"x": round(x, 1), "y": round(y, 1), "w": w, "h": h, "vw": round(vw, 1), "vh": round(vh, 1), "rot": round(rot, 1), "z": z, "label": label})
        self.placed.append((x, y, vw, vh))
        bm = 6
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])
        if label:
            # label_above: for a board standing just inside a gate, the default below-label
            # would hang over the gate structure (labels_clear_of_other_buildings).
            # label_xy: a HAND seat for the caption when BOTH bands are taken - the forcing
            # case was Nagahara's principal board at the market-bend junction, where the
            # below band holds the drum tower, the above band abuts the samurai ward gate's
            # glyph and its caption (settlement-review 2026-08-02: the two stacked captions
            # read as one label on the gate), and the clear ground is diagonal, east along
            # the road edge. Same escape the punishment ground and execution ground carry
            # (label_xy there) and for the same reason: a deferred/derived seat cannot be
            # probed from a gen, so the last resort is an explicit one. Direct-labeled, so
            # label_hugs_its_referent does not govern it - keep a hand seat close enough to
            # read as the board's own. A hand seat keeps its SPOT but the text still tilts
            # with a diagonal board (angled captions, GM 2026-08-02) - same merge as
            # punishment_spot's label_xy.
            _t = label_tilt(rot)
            if label_xy:
                _lx, _ly = label_xy
            elif _t:
                _lx, _ly = tilt_caption_seat(x, y, rot, _t, hw, hh, 11, above=label_above)
            else:
                _lx, _ly = (x, y - hh - 11) if label_above else (x, y + hh + 11)
            self.label(_lx, _ly, label, 8, italic=True, color="#7A5A30", rot=_t)
        return z

    def label_blockers(self: Settlement, skip_key: str | None = None) -> list[tuple[float, float, float, float]]:  # type: ignore[misc]
        """Every axis-aligned box a caption must miss: any manifest list of dicts carrying w/h, plus
        every caption already placed.

        DERIVED, never hand-listed. This was a list of nine keys and it fell behind exactly the way
        the CAPTION and KEEP-CLEAR registries did before they became registries (CLAUDE.md, "the
        KEEP-CLEAR CONTRACT"): `dye_yards` was never in it, so when a reflow put Minami\'s punishment
        ground beside the dye works the probe reported a clear box and the gate reported a caption on
        a dye works (2026-07-27). A probe that cannot see a feature looks exactly like a probe that
        passes. Nothing here needs to know WHICH lists exist, so a new feature is covered the day it
        is drawn; `skip_key` drops the captioned feature\'s own glyph.

        ROTATION-AWARE, because `labels_clear_of_other_buildings` tests each building\'s AABB and a
        rotated shopfront\'s AABB is much larger than its w/h - probing the unrotated rect passes here
        and still fails the gate."""
        boxes: list[tuple[float, float, float, float]] = []
        for key, recs in self.M.items():
            if key == skip_key or not isinstance(recs, list):
                continue
            for o in recs:
                if not (isinstance(o, dict) and all(isinstance(o.get(f), (int, float)) for f in ("x", "y", "w", "h"))):
                    continue
                a = math.radians(o.get("rot", 0) or 0)
                ca, sa = math.cos(a), math.sin(a)
                hw2, hh2 = o["w"] / 2, o["h"] / 2
                cs = ((-hw2, -hh2), (hw2, -hh2), (hw2, hh2), (-hw2, hh2))
                xs = [o["x"] + dx * ca - dy * sa for dx, dy in cs]
                ys = [o["y"] + dx * sa + dy * ca for dx, dy in cs]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
        boxes += [label_aabb(lb) for lb in self.M["labels"] if len(lb) > 3]  # AABB: a tilted caption blocks the ground its rotated run can reach
        return boxes

    def label_caption_hw(self: Settlement, label: str, size: float) -> float:  # type: ignore[misc]
        """A caption\'s half-width AS RECORDED. `_record_label` writes len(text) * size * 0.55, and
        that is what `labels_clear_of_other_buildings` tests - so probing the PIL-measured glyph box
        (~2px narrower per side at caption size) is the same class of bug as a hand-written victim
        list: the probe reports clear and the gate reports a collision on the 2px it could not see
        (Minami, 2026-07-27). Placement and its check read the SAME geometry."""
        return len(label) * size * 0.55 / 2

    def label_seat_clear(self: Settlement, lx: float, ly: float, tw: float, size: float = 9.0, boxes: list[tuple[float, float, float, float]] | None = None, tilt: float = 0.0) -> bool:  # type: ignore[misc]
        """Is a caption box centered at (lx, ly) clear of every blocker? `boxes` lets a caller that
        probes many seats build the blocker list once. A TILTED caption probes its rotated AABB -
        conservative against these axis-aligned blockers, so the probe stays at least as strict as
        the quad the gate tests."""
        bx = self.label_blockers() if boxes is None else boxes
        b: tuple[float, float, float, float] = (lx - tw, ly - size * 0.8, lx + tw, ly + size * 0.25)
        if tilt:
            b = label_aabb([*b, 0, "", None, tilt])
        return not any(b[0] < x1 and x0 < b[2] and b[1] < y1 and y0 < b[3] for x0, y0, x1, y1 in bx)

    def clear_label_seat(self: Settlement, x: float, y: float, w: float, h: float, label: str, size: float = 9.0, skip_key: str | None = None) -> Pt | None:  # type: ignore[misc]
        """A caption seat for a verge-hugging feature: below, above, then left and right, walking
        OUTWARD, first clear box wins; None when nothing is clear.

        A feature that hugs the frontage puts its default below-label ON that frontage - not bad luck
        but what "hugging the frontage" means, and it fired on all three maps that first used this
        probe. SIXTEEN rings, not nine: these features are sited at the BUSIEST node by definition, so
        the ground around them is the most crowded on the map, and nine ran out on Minami - at which
        point the caption fell back to its default seat, on top of three dwellings. A probe that gives
        up silently is worse than no probe, so callers must handle None rather than inherit a seat."""
        tw = self.label_caption_hw(label, size)
        boxes = self.label_blockers(skip_key)
        for ring in range(16):
            d = ring * 14
            for lx, ly in ((x, y + h / 2 + 11 + d), (x, y - h / 2 - 9 - d), (x - tw - w / 2 - 6 - d, y + 3), (x + tw + w / 2 + 6 + d, y + 3)):
                if self.label_seat_clear(lx, ly, tw, size, boxes):
                    return (lx, ly)
        return None

    def place_kosatsuba(self: Settlement, label: str = "notice board") -> Pt | None:  # type: ignore[misc]
        """AUTO-SITE the settlement kosatsuba on a lane/road verge at the busiest clear node -
        the village/hamlet tiers' procedural sibling of the town/city hand placement (GM
        2026-07-24: EVERY settlement tier carries the board; the ofuregaki circulars reached
        the peasantry through it via the settlement's one required-literate reader - the
        headman, or a hamlet's senior farmer answering to the village headman - and officials
        also read notices aloud, so even a 50-inhabitant hamlet's board works). Deterministic:
        draws NO RNG, so calling it inside `roll_village` cannot perturb a rolled map's seed
        stream. Reads the SAME manifest route fields the validator's siting checks read (the
        dev-loop same-source doctrine): MAIN ways only (`roads`/`M['road']` + `main: True`
        town streets - kosatsuba_on_a_main_way, GM 2026-08-02) when the map declares any,
        else the whole network (`M['lane']` + `M['lanes']` + `town_streets`), and probes
        candidate verge spots with `_fits`, scoring for the most dwellings within ~260 px
        (siting is a TRAFFIC decision - the state talks at everyone who passes) while
        hugging the verge. Call AFTER the lanes, homesteads, and wells and BEFORE the crop, so
        the frame contains the board. No-op under meta(kosatsuba=False); returns the spot, or
        None when no verge inside the validator's ~60-real-ft siting band fits (the
        settlement-tier check would then fire - place by hand or widen the lane network)."""
        if not self.M["meta"].get("kosatsuba", True):
            return None
        ftpx = float(self.M["meta"].get("ftpx") or 1)
        lim = 60.0 / ftpx  # kosatsuba_by_the_road: ~60 REAL feet from a route, in px
        # probe with the DRAWN marker box, not the true footprint (village grain floors the glyph
        # to ~11x4.6 px - see kosatsuba): the spot has to hold the pixels that get drawn there
        w = max(self.px(12), KOSATSUBA_MARKER_MIN_PX)
        h = w * 5 / 12
        # (pts, tread width) per route; road/lane manifest fields carry no width, so assume
        # a generous tread for the bed-avoidance test below.
        # MAIN WAYS ONLY, where the map declares any (GM 2026-08-02, from Ubame: the siter put
        # the board a legal 49 ft off a side lane while the high street ran 200 ft away - "it
        # should be along the main road, in order to be more noticed"). The candidate tiers
        # mirror kosatsuba_on_a_main_way exactly (the same-source doctrine): every road and
        # every main: True town street is a MAIN way, and when the map has at least one, ONLY
        # main-way verges are sampled - a side lane's busiest node is still a side lane, so
        # scoring must never see it. A map with no declared hierarchy (village/hamlet lane
        # webs, towns whose streets are all unflagged) falls back to the whole network, where
        # the busiest-node scoring below stands in for "main". The fallback still needs TOWN
        # STREETS TOO: this probe was written for the lane/lanes tiers, and the omission was
        # invisible until Hirameki - no road, no lanes, all town_streets - gave it not one
        # candidate seat and it returned None (GM 2026-07-27).
        routes: list[tuple[list[Pt], float]] = []
        if self.M.get("road"):
            routes.append(([(p[0], p[1]) for p in self.M["road"]], 18.0))
        routes.extend(([(p[0], p[1]) for p in r["pts"]], 18.0) for r in (self.M.get("roads") or [])[1:])
        routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [] if st.get("main"))
        if not routes:
            if self.M.get("lane"):
                routes.append(([(p[0], p[1]) for p in self.M["lane"]], 8.0))
            routes.extend(([(p[0], p[1]) for p in ln["pts"]], float(ln.get("w", 8))) for ln in self.M.get("lanes") or [])
            routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [])
        spots = [(b["x"], b["y"]) for b in self.M["houses"]] + [(b["x"], b["y"]) for b in self.M["buildings"]]

        beds = way_beds(self.M)  # EVERY way bed, not just the routes candidates were sampled from

        def off_every_bed(x: float, y: float) -> bool:
            # the board hugs the verge, so the lane corridor's no-build clearance (a HOUSE
            # setback: homesteads must not crowd the tread) is deliberately bypassed
            # (_fits corridors=False) - but the board must still stand off the TREAD of
            # every route, including ones it was not sampled from (a junction spot offset
            # from lane A can land on lane B, or on a town street or alley this tier's
            # candidate list does not carry at all - see way_beds)
            return all(seg_dist(x, y, bp[k], bp[k + 1]) >= bhw + h / 2 + 3 for bp, bhw in beds for k in range(len(bp) - 1))

        tw_lab = self.label_caption_hw(label, 8.0) if label else 0.0  # the caption half-width the seat must also hold, as RECORDED
        kb_boxes = self.label_blockers("kosatsuba")  # built once: the probe tests many seats against the same map
        cands: list[tuple[int, float, float, float, float, int | None]] = []  # (busy, score, x, y, rot, label_above|None)
        for pts, _rw in routes:
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                seg = math.hypot(bx - ax, by - ay)
                if not seg:
                    continue
                ux, uy = -(by - ay) / seg, (bx - ax) / seg  # verge normal
                # long axis ALONG the route: the board's face is broadside to the traffic that
                # reads it, never edge-on (kosatsuba_faces_the_road; see kosatsuba's docstring)
                rot = math.degrees(math.atan2(by - ay, bx - ax))
                for t in range(int(seg // 12) + 1):
                    f = t * 12 / seg
                    mx, my = ax + (bx - ax) * f, ay + (by - ay) * f
                    for side in (1.0, -1.0):
                        off = _rw / 2 + h / 2 + 4
                        while off <= lim:
                            x, y = mx + ux * off * side, my + uy * off * side
                            if off_every_bed(x, y) and self._fits(x, y, w, h, corridors=False):
                                busy = sum(1 for sx, sy in spots if math.hypot(x - sx, y - sy) < 260)
                                # THE CAPTION IS PART OF THE SEAT (GM 2026-07-27). The glyph is 11 px
                                # and fits almost anywhere; its caption does not, and the busiest
                                # frontage is exactly where there is least room for one - so a siter
                                # that hunts for ground big enough to hold BOTH walks away from the
                                # traffic and out to the quiet end of the road, which is how Ubame's
                                # board came to stand across the bridge from its own town.
                                lab = 0 if self.label_seat_clear(x, y + h / 2 + 11, tw_lab, 8.0, kb_boxes) else (1 if self.label_seat_clear(x, y - h / 2 - 11, tw_lab, 8.0, kb_boxes) else None)
                                cands.append((busy, busy * 10 - off / 3, x, y, rot, lab))
                            off += 5.0
        if not cands:
            return None
        # ON THE TRAFFIC IS THE RULE; A FITTING CAPTION IS ONLY THE PREFERENCE WITHIN IT. Scoring the
        # caption as a flat bonus large enough to outrank traffic was tried first and re-committed the
        # original sin at one remove: where no seat on a tight village frontage has a clear caption,
        # EVERY caption-clear seat is out in the fields, so all three village boards walked off the
        # frontage and their captions ran off the cropped frame. Open ground for a caption is abundant
        # exactly where nobody is - the same trap as open verge for the board. So the busiest node
        # sets a floor (60% of the best count available), and the caption chooses only among the seats
        # that already stand on the traffic. A board with nowhere to put its caption is still placed,
        # so labels_clear_of_other_buildings reports it rather than the siter hiding it.
        floor = 0.6 * max(c[0] for c in cands)
        _b, _s, x, y, rot, lab = max((c for c in cands if c[0] >= floor), key=lambda c: (c[5] is not None, c[1]))
        self.kosatsuba(x, y, rot, label=label, label_above=bool(lab))
        return (x, y)

    def _under_a_caption(self: Settlement, x: float, y: float, w: float, h: float, rot: float = 0.0, pad: float = 2.0) -> bool:  # type: ignore[misc]
        """Whether a footprint at (x, y, w, h, rot) would land under a caption ALREADY on the map.

        A label may cover only the thing it labels (`labels_clear_of_other_buildings`), and a
        feature sited LATE can walk under a caption placed early: Minami's punishment ground
        auto-sited onto the burakumin quarter's caption when a reflow moved the busiest traffic
        node 24px north (2026-08-08). The existing probe cannot catch this - it seats the
        feature's OWN caption clear of the buildings, and this is the offense the other way
        round, the feature walking under someone else's caption. Reads `label_aabb`, the same
        geometry the check reads, per the same-source doctrine."""
        hw = (abs(w * math.cos(math.radians(rot))) + abs(h * math.sin(math.radians(rot)))) / 2 + pad
        hh = (abs(w * math.sin(math.radians(rot))) + abs(h * math.cos(math.radians(rot)))) / 2 + pad
        return any(x - hw < a1 and a0 < x + hw and y - hh < b1 and b0 < y + hh for a0, b0, a1, b1 in (label_aabb(L) for L in self.M.get("labels", [])))

    def place_punishment_spot(self: Settlement, label: str | None = "punishment ground", label_xy: Pt | None = None) -> Pt | None:  # type: ignore[misc]
        """AUTO-SITE the punishment ground on a street verge at the busiest clear node - the notice
        board's sibling, and for the same reason: both institutions are sited by FOOT TRAFFIC, so
        both want the same probe rather than a hand-picked rect. (Hand rects were tried first on
        three maps and all three failed `punishment_spot_by_the_traffic` the same way: `open_seat`
        ties toward the rect's CENTER, which is the open ground behind the frontage, precisely where
        this feature must not be.) Deterministic - draws no RNG.

        Reads the SAME manifest route fields the validator reads (the dev-loop same-source doctrine),
        including `town_streets`, which the board's village-tier probe does not need. Keeps the spot
        inside the rampart where there is one - the display faces the town, not the road out; that is
        the execution ground's job. No-op under meta(punishment_spot=False). Returns the spot, or
        None when no verge fits (the presence check then fires - place by hand)."""
        if not self.M["meta"].get("punishment_spot", True):
            return None
        ftpx = float(self.M["meta"].get("ftpx") or 1)
        lim = 60.0 / ftpx  # punishment_spot_by_the_traffic: ~60 REAL feet from a street
        w, h = self.px(PUNISHMENT_SPOT_FT[0]), self.px(PUNISHMENT_SPOT_FT[1])
        routes: list[tuple[list[Pt], float]] = []
        if self.M.get("road"):
            routes.append(([(p[0], p[1]) for p in self.M["road"]], float(self.M.get("road_width") or 18)))
        routes.extend(([(p[0], p[1]) for p in st["pts"]], float(st.get("w", 18))) for st in self.M.get("town_streets") or [])
        routes.extend(([(p[0], p[1]) for p in ln["pts"]], float(ln.get("w", 8))) for ln in self.M.get("lanes") or [])
        if not routes:
            return None
        wall = self.M.get("wall")
        spots = [(b["x"], b["y"]) for b in self.M["houses"]] + [(b["x"], b["y"]) for b in self.M["buildings"]]
        beds = way_beds(self.M)  # see way_beds: EVERY bed, including the alleys and the ring road
        # this list does not sample candidates from - a display bypasses the lane CORRIDOR
        # deliberately (it is a house setback), never the roadbed itself

        def off_every_bed(x: float, y: float) -> bool:
            return all(seg_dist(x, y, bp[k], bp[k + 1]) >= bhw + h / 2 + 3 for bp, bhw in beds for k in range(len(bp) - 1))

        best: tuple[float, float, float, float] | None = None  # (score, x, y, rot)
        # ...and the best seat that is ALSO out from under the captions already on the map. A
        # PREFERENCE, not a filter (2026-08-08): landing under someone else's caption is a real
        # defect - Minami's ground auto-sited onto the burakumin quarter's label when a reflow moved
        # the busiest node 24px north - but it is the caption's problem to solve, and refusing the
        # seat outright would let a densely-captioned quarter drive the whole probe to None, i.e.
        # turn "the label wants moving" into "the city has no punishment ground at all". So: take a
        # clear seat when one exists at any score, and fall back to the busiest seat when none does.
        best_clear: tuple[float, float, float, float] | None = None
        for pts, _rw in routes:
            for i in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                seg = math.hypot(bx - ax, by - ay)
                if not seg:
                    continue
                ux, uy = -(by - ay) / seg, (bx - ax) / seg
                rot = math.degrees(math.atan2(by - ay, bx - ax))
                for t in range(int(seg // 12) + 1):
                    f = t * 12 / seg
                    mx, my = ax + (bx - ax) * f, ay + (by - ay) * f
                    for side in (1.0, -1.0):
                        off = _rw / 2 + h / 2 + 4
                        while off <= lim:
                            x, y = mx + ux * off * side, my + uy * off * side
                            if (not wall or len(wall) < 3 or point_in_poly(x, y, wall)) and off_every_bed(x, y) and self._fits(x, y, w, h, corridors=False):
                                busy = sum(1 for sx, sy in spots if math.hypot(x - sx, y - sy) < 260)
                                score = busy * 10 - off / 3
                                if best is None or score > best[0]:
                                    best = (score, x, y, rot)
                                if not self._under_a_caption(x, y, w, h, rot) and (best_clear is None or score > best_clear[0]):
                                    best_clear = (score, x, y, rot)
                            off += 5.0
        best = best_clear or best
        if best is None:
            return None
        _, x, y, rot = best
        if label and label_xy is None:
            # A verge-hugging feature's DEFAULT below-label lands on the frontage it hugs - that is
            # not bad luck, it is what "hugging the frontage" means, and it fired on all three maps.
            # So probe the label too: below, above, then left/right, first clear box wins.
            label_xy = self.clear_label_seat(x, y, w, h, label, skip_key="punishment_spots")
        self.punishment_spot(x, y, rot, label=label, label_xy=label_xy)
        return (x, y)

    def drum_tower(self: Settlement, x: float, y: float, tw: float | None = None, label: str = "drum tower") -> int:  # type: ignore[misc]
        """A combined BELL-AND-DRUM TOWER (zhonggulou) - the timekeeping/curfew institution of a
        WALLED seat (GM 2026-07-24). Morning bell, evening drum: dawn gate-opening, the dusk
        gate-closing that starts the street curfew, the five night watches, alarm and ceremony.
        Part of the standard county-seat kit (yamen, temples, drum tower); a county seat had ONE
        combined tower - the paired gulou/zhonglou on an axis is capital grammar (Pingyao, a
        wealthy county seat, has exactly one Market Tower, ~60 ft). Distinct from the fire towers:
        fire watch was a SEPARATE institution in both reference cultures (Song Kaifeng ran
        dedicated fire-lookout towers; Edo split the licensed toki-no-kane time bell from the
        hinomi-yagura). Drawn as a heavy masonry platform (county tier ~60-80 ft square) carrying
        a timber pavilion with the drum and the bell - visibly heavier-built than the skeletal
        braced-frame fire towers. Stands at the main street crossing, near (not inside) the yamen.
        Records M['drum_towers'] (an overlap-checked struct) and reserves a no-build block."""
        if tw is None:
            tw = self.px(
                36
            )  # county-tier footprint RE-VERIFIED (GM eye + research 2026-07-24): Pingyao's Market Tower - the wealthy-county showpiece - is ATTESTED at 133.4 m^2 plan (~38 ft square); these towers dominate by HEIGHT (50-60 ft), not plan, so ~36 ft = one rowhouse width reads correctly. The first-draft 70 ft was contaminated by garrison street-arch platforms (Dingbian 52 ft, Xingcheng 66 ft) - that variant is prefecture/garrison tier, never a 3,000-person seat
        h = tw / 2
        hi = tw * 0.31  # the pavilion atop the platform
        g = [f'<g transform="translate({x:.0f},{y:.0f})">']
        g.append(f'<rect x="{-h:.1f}" y="{-h:.1f}" width="{tw:.1f}" height="{tw:.1f}" rx="1.5" fill="#E3D7B8" stroke="#4A3318" stroke-width="2.4"/>')  # the masonry platform
        g.append(f'<rect x="{-hi:.1f}" y="{-hi:.1f}" width="{hi * 2:.1f}" height="{hi * 2:.1f}" rx="1" fill="#C9A57A" stroke="#4A3318" stroke-width="1.5"/>')  # the timber pavilion
        g.append(f'<line x1="{-hi:.1f}" y1="0" x2="{hi:.1f}" y2="0" stroke="#4A3318" stroke-width="0.9" opacity="0.7"/>')  # the pavilion roof ridge
        g.append(
            f'<circle cx="{-tw * 0.155:.1f}" cy="0" r="{max(tw * 0.105, 1.2):.1f}" fill="#8A4A2A" stroke="#4A3318" stroke-width="0.8"/>'
        )  # the great drum (radius floored - legible at the corrected 12px platform)
        g.append(f'<circle cx="{tw * 0.155:.1f}" cy="0" r="{max(tw * 0.08, 0.9):.1f}" fill="#6B5A3A" stroke="#4A3318" stroke-width="0.8"/>')  # the bell
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("drum_towers", []).append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": 0.0, "z": z, "label": label})
        self.placed.append((x, y, tw, tw))
        bm = 12
        # the block reserves the caption band below too, AT THE CAPTION'S WIDTH - the corrected
        # 36 ft platform is narrower than the "drum tower" text, so a footprint-width band let
        # rowpack houses slide under the caption's ends (GM tower-resize ripple, 2026-07-24)
        self.block_polys.append([(x - h - bm, y - h - bm), (x + h + bm, y - h - bm), (x + h + bm, y + h + bm), (x - h - bm, y + h + bm)])
        cb_ = max(h + bm, 2.9 * len(label) + 10)
        self.block_polys.append([(x - cb_, y + h), (x + cb_, y + h), (x + cb_, y + h + 40), (x - cb_, y + h + 40)])
        # the caption is TWO LINES, "drum/bell" over "tower" (GM 2026-07-24): the county tower is
        # genuinely the combined zhonggulou - both instruments in one building, and both are drawn
        self.label(x, y + h + 12, "drum/bell", 9, italic=True, color="#4A3318")
        self.label(x, y + h + 24, "tower", 9, italic=True, color="#4A3318")
        return z
