"""Walled compounds shown as a glyph on a settlement map: the samurai manor and the merchant estate.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    label_tilt,
    seg_dist,
    tilt_caption_seat,
)
from .._knobs import MERCHANT_ESTATE_WEIGHTS, roll_merchant_estate_count

if TYPE_CHECKING:
    from ..core import Settlement


class CompoundsMixin:
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
