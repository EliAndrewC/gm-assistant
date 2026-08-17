"""What a homestead BUNDLE is: house, threshing yard, dooryard garden beds, kura, grove arms. Pure geometry - it places nothing and draws nothing.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core import Settlement


class BundleGeomMixin:
    @staticmethod
    def _bbox_of(rects: Any) -> tuple[float, float, float, float]:
        """The axis-aligned (cx, cy, w, h) bounding box enclosing a list of (cx, cy, w, h) rects."""
        xs = [r[0] - r[2] / 2 for r in rects] + [r[0] + r[2] / 2 for r in rects]
        ys = [r[1] - r[3] / 2 for r in rects] + [r[1] + r[3] / 2 for r in rects]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys))

    def _garden_beds(self: Settlement, hx: float, hy: float, hw: float, hh: float, gx: float, gy: float, gw: float, gh: float, side: str, gap: float) -> list[Any]:  # type: ignore[misc]
        """The dooryard garden BED(S) of one nucleated homestead. Usually ONE bed (the reserved plot at
        (gx, gy)). But ~1 in 4 households FRAGMENT the plot into two beds - soil and paths made a single
        clean plot impractical, so you work the good topsoil where it lies. Of the splits (all position-
        seeded, no RNG ripple): ~half FLANK the house on OPPOSITE walls (the E and W walls, or the two south
        corners) because the workable ground just fell on both sides; the rest share ONE side, either
        SIDE-BY-SIDE or - for a SOUTH garden, where the upper bed stays out of the house's shade - STACKED
        above/below. Every bed sits on a SUNNY band (never the cold north back), and because the beds are
        returned to `_bundle_geom` they are RESERVED and collision-checked as part of the whole bundle - so an
        opposite-side bed can never overlap a neighbor or a paddy. Splits only fire when each bed stays wide
        enough (~12 ft) to read as a real garden, so it is the larger (well-off / headman) plots that
        fragment. Total bed area stays in the saien band (`garden_area_within_norms`). Returns (cx,cy,w,h) rects."""
        bs = self.bscale
        if self._hjit(hx, hy, 8.0) >= 0.26:  # the common case: one undivided plot
            return [(gx, gy, gw, gh)]
        south = side in ("SE", "SW")
        # OPPOSITE-SIDE (flanking) split: a bed on each of the E and W walls (or the two south corners for a
        # south garden), each ~half width, the house standing between them
        if self._hjit(hx, hy, 9.0) < 0.5 and gw * 0.55 >= 6 * bs:
            pw = gw * 0.55
            return [(hx + hw / 2 + gap + pw / 2, gy, pw, gh), (hx - hw / 2 - gap - pw / 2, gy, pw, gh)]
        # SAME-SIDE STACKED (above/below): only for a south garden, so the upper bed does not fall into shade
        if south and self._hjit(hx, hy, 10.0) < 0.5 and (gh - gap) / 2 >= 6 * bs:
            ph = (gh - gap) / 2
            return [(gx, gy - (gap + ph) / 2, gw, ph), (gx, gy + (gap + ph) / 2, gw, ph)]
        # SAME-SIDE SIDE-BY-SIDE (the default fragmentation), both beds on the primary wall
        if (gw - gap) / 2 >= 6 * bs:
            pw = (gw - gap) / 2
            return [(gx - (gap + pw) / 2, gy, pw, gh), (gx + (gap + pw) / 2, gy, pw, gh)]
        return [(gx, gy, gw, gh)]  # reserved plot too small to split cleanly

    def _bundle_geom(self: Settlement, hx: float, hy: float, hw: float, hh: float, garden_side: str = "E", shed: bool = False) -> dict[str, Any]:  # type: ignore[misc]
        """The metric layout of one homestead BUNDLE around a house centered at (hx, hy). TWO forms:
        NUCLEATED (self._nucleated) = house + lee GARDEN (E) + south YARD only, compact so a cluster can
        pack tight (no per-house grove - a nucleus shelters itself); DISPERSED (default) also carries the
        windward GROVE as an L (an N band + a W band for the default NW wind), sized ~6x the house. The
        dooryard GARDEN tucks tight to the house's E (lee) wall, the threshing YARD sits on the sunny S
        front. Returns a dict of (cx, cy, w, h) rects keyed house/garden/yard (+ grove_n/grove_w when
        dispersed) plus the whole-bundle bbox. (NW windward; other winds are a later generalisation.)"""
        gap = self.px(3)  # 3 ft between a house and its yard/garden, at this map's ftpx
        gw, gh = 0.48 * hw, 0.85 * hh  # garden - tight to the house, scales with wealth
        yw, yh = 0.80 * hw, 0.92 * hh  # threshing/drying yard, ~house-sized
        if not getattr(self, "_nucleated", False):
            # CAP the DISPERSED appurtenances too, same doctrine as the nucleated branch below: a BIG house
            # (the 46x28 px headman) keeps an ORDINARY farm's garden/yard, not ones scaled to the grand
            # house. Found 2026-07-21 (Hikari, GM): the moment the dispersed headman started getting a real
            # bundle, its uncapped 0.48/0.85-scaled garden (~160+ m^2) breached garden_area_within_norms'
            # 140 m^2 ceiling. Garden caps sit BELOW the nucleated ones (42x30 ft vs 48x34) because this
            # path has no up-jitter to absorb - 21x15 px ~ 117 m^2 stays comfortably a garden. Plain
            # dispersed houses (garden ~11x12 px, yard ~25x14) sit far under every cap, so only the headman
            # is affected. Scoped OFF the nucleated path (which recomputes from these as inputs and applies
            # its own caps) so nucleated maps stay byte-identical - capping its inputs re-rolled
            # Hoshigaoka's packing and pushed its fixed-coordinate graveyard off-frame.
            gw, gh = min(gw, self.px(42)), min(gh, self.px(30))
            yw, yh = min(yw, self.px(68)), min(yh, self.px(44))
        east = hx + hw / 2 + gap + gw
        south = hy + hh / 2 + gap + yh
        base: dict[str, Any] = {
            "house": (hx, hy, hw, hh),
            "garden": (hx + hw / 2 + gap + gw / 2, hy, gw, gh),
            "yard": (hx, hy + hh / 2 + gap + yh / 2, yw, yh),
        }
        if getattr(self, "_nucleated", False):
            # NUCLEATED cluster (China-leaning default, per Knapp - and the Japanese shuson): the
            # houses stand close and SHELTER EACH OTHER, so there is NO per-house windbreak grove
            # (a full yashikirin is the DISPERSED-farmstead feature; a tight cluster of grove-bundles
            # cannot nucleate at all). The windbreak becomes a VILLAGE-EDGE belt placed in the second
            # pass. The bundle is house + south yard + a garden on an ADAPTIVE sunny side (chosen by
            # the placer for fit + no shading), so it packs into a real nucleus and the gardens vary
            # instead of all sitting east between houses. See settlements.md 'Settlement form'.
            # CAP the appurtenance dims so a big house (the headman) keeps an ORDINARY farm's yard/garden
            # (spanning ~its adjacent wall but not scaled up to the grand house - "not as tall / not as
            # wide"). A plain 23x14 house is well under these caps, so ordinary farms are unaffected.
            # SIZE variation (position-seeded, no RNG ripple): the garden's base is its MINIMUM (you need at
            # least this plot to feed a household) so it jitters UP - by a different amount in each dimension,
            # which also varies its proportions; the threshing yard's base is its MAXIMUM (a work apron sized
            # to the harvest) so it jitters DOWN. No two homesteads are identical. Both are CAPPED afterward so
            # the big headman still keeps an ordinary farm's yard/garden (the garden jitter can't breach it).
            yw = min(yw * (0.75 + self._hjit(hx, hy, 5.0) * 0.25), self.px(68))  # yard  [0.75,1.00]x, capped at 68 ft
            yh = min(yh * (0.75 + self._hjit(hx, hy, 6.0) * 0.25), self.px(44))
            gw = min(gw * (1.0 + self._hjit(hx, hy, 3.0) * 0.25), self.px(48))  # garden [1.00,1.25]x, capped at 48 ft
            gh = min(gh * (1.0 + self._hjit(hx, hy, 4.0) * 0.25), self.px(34))
            base["yard"] = (hx, hy + hh / 2 + gap + yh / 2, yw, yh)
            if garden_side == "SE":  # tucked beside the south yard (sunny, tight)
                gx, gy = hx + hw / 2 + gap + gw / 2, hy + hh / 2 + gap + gh / 2
            elif garden_side == "SW":
                gx, gy = hx - hw / 2 - gap - gw / 2, hy + hh / 2 + gap + gh / 2
            elif garden_side == "W":  # windward wall, house mid-height
                gx, gy = hx - hw / 2 - gap - gw / 2, hy
            else:  # "E" - lee wall, house mid-height
                gx, gy = hx + hw / 2 + gap + gw / 2, hy
            beds = self._garden_beds(hx, hy, hw, hh, gx, gy, gw, gh, garden_side, gap)
            base["gardens"] = beds  # 1 bed normally; 2 (flanking / stacked / side-by-side) when fragmented
            base["garden"] = beds[0]  # primary bed (kept for the shading score + back-compat)
            rects = [base["house"], base["yard"], *beds]
            if shed:  # a north-wall kura, reserved so a neighbor never lands on it
                base["shed"] = (hx, hy - 0.60 * hh, 0.46 * hw, 0.30 * hh)
                rects.append(base["shed"])
            base["bbox"] = self._bbox_of(rects)
            return base
        # DISPERSED farmstead (the shipped ring-village behavior): the windward GROVE as an L (an N
        # band + a W band, for the default NW wind), sized so the grove footprint is ~6x the house. The
        # multi-bed garden split is a NUCLEATED feature (clean E/W walls, no grove or shed in the way); a
        # dispersed farm keeps its single east garden (its west wall carries the windbreak grove).
        base["gardens"] = [base["garden"]]
        b = 1.57 * hh  # grove band depth -> grove ~= 6x house area
        west = hx - hw / 2 - gap - b
        north = hy - hh / 2 - gap - b
        base["grove_n"] = ((west + east) / 2, north + b / 2, east - west, b)
        base["grove_w"] = (west + b / 2, (north + b + south) / 2, b, south - (north + b))
        base["bbox"] = ((west + east) / 2, (north + south) / 2, east - west, south - north)
        return base
