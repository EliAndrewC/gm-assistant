"""The urban building glyph, its palette, and the per-building helpers that seat ONE of them.

Split from settlement/structures.py by feature 114 - see settlement/structures/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    WARD_BARRED_KINDS,
    point_in_poly,
    seg_closest,
)

if TYPE_CHECKING:
    from ..core import Settlement


class UrbanBuildingMixin:
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
