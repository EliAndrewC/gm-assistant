"""NEAR-RING FARMLAND: the packed working ground immediately outside a town or a city.

Two tilers over one set of keep-outs, and the ORDER between them is part of the design - paddy runs
first and grain fills only what paddy did not. A market town sits in the middle of its best land and
the near ring is the part worked hardest (the von Thuenen intensity gradient), so the flat near ring
is cropland and the labor-limited fallow retreats to the far margins.

The rule both are built on: a basin is placed ONLY where it can be LEGITIMATELY WATERED. Ground with
no reachable water is SKIPPED rather than given conjured hydrology - where the near ring genuinely
lacks water, draw fewer basins, do not fake it.

Read `near_ring_cropland`'s `_blocked` / `_blocked_region` pair before changing either. The cheap
point test is a PREFILTER and the region test is what DECIDES: center-plus-corners sampling leaks,
because a small keep-out sitting against the middle of a cell EDGE touches neither the center nor
any corner, which is how a wellhead once ended up 1 px inside a hatake plot.

Split from settlement/land.py by feature 120 - see settlement/land/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Poly, boxed_grid, boxed_segs, point_in_poly, region_blocked, seg_dist
from .._knobs import CITY_TIER_SCALES

if TYPE_CHECKING:
    from ..core import Settlement


class NearRingMixin:
    def near_ring_cropland(  # type: ignore[misc]
        self: Settlement, bbox: tuple[float, float, float, float], density: str | None = None, *, seed: int = 0, garden_frac: float = 0.16, cell_ft: float = 60.0, avoid: Any = ()
    ) -> int:
        """Fill the flat, CLEAR ground in `bbox` with channel-free DRY-FIELD + GARDEN cropland, so a
        well-sited town/city NEAR RING reads as PACKED farmland instead of bare scrub (feature 013,
        settlements.md 'Near-ring farmland density'). A market town / county seat sits in the middle of
        its BEST land (site selection) and the near ring is the part worked HARDEST (the von Thünen
        intensity gradient); the labor-limited fallow lives at the FAR margins, not hugging the town. So
        the flat near ring is cropland, and the scrub retreats to the frame edge (`s.commons`) + the
        non-arable ground (hill, wet toe). This tiles a quilt of ridge-cultivated hatake + garden plots
        (grain/pulse/greens - the dryland SUPPORTING crops that historically flanked the paddy), each
        recorded to `M['dry_plots']` + `dry_polys` (no-build cropland the coverage checks count as cover)
        - NO channels, NO water: dry cropland is exempt from `fields_show_water_source`, so it packs the
        ring without inventing hydrology. It SKIPS every keep-out (existing fields + their corridors, the
        30-ft urban halo around every structure, roads/streets/lanes, watercourses + the pond, the hill,
        and - on a walled city - everything INSIDE the wall). Call it AFTER the paddy combs AND after the
        urban packs/farmsteads (so it sees every structure to skip). Intensity is `density` (`'dense'`
        default / `'medium'` / `'thin'`), or None to read `meta(near_ring_density=...)` - the
        calibrated-liberty knob (the DEGREE of near-ring density is region-dependent; dense is the
        well-sited default). Deterministic (own RNG, seeded), so it perturbs no other seeded pack.
        Returns the plot count. Gated by `near_ring_cultivated_fraction`."""
        from l7r.diagram.waterfields import DRY_CROPS

        tier = density if density is not None else self.M.get("meta", {}).get("near_ring_density", "dense")
        fill_by_tier = {
            "dense": 0.97,
            "medium": 0.70,
            "thin": 0.52,
        }  # fraction of CLEAR cells cropped; the rest stays scrub/fallow. thin/medium tile the AVAILABLE pockets fairly full (a marginal locale reads thin because it HAS little croppable ground, e.g. Hoshizora's pasture/relay frame, not because its few plots are patchy), so a thin map still clears its (low) floor with margin
        if tier not in fill_by_tier:
            raise ValueError(f"near_ring_density must be one of {sorted(fill_by_tier)}, got {tier!r}")
        fill_p = fill_by_tier[tier]
        garden_pal = [("#9FB86B", "#83A050"), ("#8FAE62", "#75954C")]  # intensively-worked garden greens mixed into the grain/pulse hatake
        dry_pal = list(DRY_CROPS.items())  # [(crop, (fill, furrow)), ...]

        bx0, by0, bx1, by1 = bbox
        bx0, by0 = max(bx0, 12.0), max(by0, 12.0)
        bx1, by1 = min(bx1, self.W - 12.0), min(by1, self.H - 12.0)
        if bx1 - bx0 < 10 or by1 - by0 < 10:
            return 0
        cell = self.px(cell_ft)
        rng = random.Random((seed & 0xFFFF) ^ 0x13A7 ^ (int(bx0) * 131) ^ (int(by0) * 17))

        halo_rects, halo_circles = self._urban_keepouts((bx0, by0, bx1, by1))
        corridors = self._corridor_buffers(3 * self.bscale)
        wat_b = boxed_grid(boxed_segs(self._watercourse_segs()))  # drawn water (streams/channels/comb laterals), pre-boxed once - see _watercourse_segs
        pond = self.M.get("pond")
        hill = self.M.get("hill")
        wall = self.M.get("wall")
        walled_city = self.M.get("meta", {}).get("scale") in CITY_TIER_SCALES and wall is not None and len(wall) >= 3
        grove_polys = [
            g["poly"] for g in self.M.get("village_groves", []) if g.get("poly") and len(g["poly"]) >= 3
        ]  # keep cropland off the windbreak/copse belts (a grove is committed non-arable cover; call this AFTER the groves)
        grove_rects = [(g["x"] - g["w"] / 2, g["y"] - g["h"] / 2, g["x"] + g["w"] / 2, g["y"] + g["h"] / 2) for g in self.M.get("groves", []) if "x" in g and "w" in g]
        # every DRAWN grove clump center - a plot must not cover one (groves_clear_of_dry_plots reads the clumps,
        # which can sit a little outside their loose belt poly); tested by plot BBOX in the loop, the precise guard
        grove_clumps = [(float(c[0]), float(c[1])) for g in self.M.get("village_groves", []) for c in g.get("clumps", [])]

        def _blocked_region(quad: Poly) -> bool:
            """The same keep-outs as `_blocked`, tested against the whole CELL rather than a few
            points on it. Only the keep-outs a cell can STRADDLE without touching a sample point need
            this; the rest are already caught by the cheap point test above."""
            water = [
                (pl_, float(rec_.get("w") or dw_) / 2)
                for key_, dw_ in (("streams", 9.0), ("channels", 2.5), ("field_ditches", 1.5), ("canals", 14.0))
                for rec_ in (self.M.get(key_, []) or [])
                for pl_ in [rec_.get("poly") or rec_.get("pts")]
                if pl_
            ]
            return region_blocked(
                quad,
                [(pond[0], pond[1], max(pond[2], pond[3]))] if pond is not None else [],
                list(halo_circles),
                list(corridors) + water,
                [gp for grp in (self.field_polys, self.block_polys, self.dry_polys, self.clearings, list(avoid), grove_polys) for gp in grp if len(gp) >= 3],
            )

        def _blocked(px: float, py: float) -> bool:
            return bool(
                any(point_in_poly(px, py, ff) for ff in self.field_polys)  # off the paddy envelopes
                or any(point_in_poly(px, py, b) for b in self.block_polys)  # off every reserved footprint / bog / pond block
                or any(point_in_poly(px, py, d) for d in self.dry_polys)  # off existing hem/garden cropland (and plots placed this pass)
                or any(point_in_poly(px, py, c) for c in self.clearings)  # off swept sacred/funerary verges
                or any(point_in_poly(px, py, a) for a in avoid)
                or any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hw for i in range(len(pl) - 1)) for pl, hw in corridors)  # off roads/streets/lanes
                or self._on_watercourse(px, py, near=wat_b.near)  # off streams/channels/moat
                or (pond is not None and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.0)  # off the pond
                or any(x0r <= px <= x1r and y0r <= py <= y1r for x0r, y0r, x1r, y1r in halo_rects)  # off the urban-clearance halo
                or any((px - hx) ** 2 + (py - hy) ** 2 <= hr * hr for hx, hy, hr in halo_circles)  # off wellhead aprons
                or (hill is not None and ((px - hill[0]) / (hill[2] * 1.35)) ** 2 + ((py - hill[1]) / (hill[3] * 1.35)) ** 2 <= 1.0)  # off the hill slope (paddy/field needs flat ground)
                or any(point_in_poly(px, py, gp) for gp in grove_polys)  # off the windbreak/copse belts
                or any(gx0 <= px <= gx1 and gy0 <= py <= gy1 for gx0, gy0, gx1, gy1 in grove_rects)
                or (walled_city and wall is not None and point_in_poly(px, py, wall))  # a city's near ring is OUTSIDE the wall
            )

        # Tile the bbox on a clean grid (shared cut lines -> plots ABUT, like an in-wall veg tract), then
        # keep only cells whose whole footprint is clear of every keep-out. A boundary cell abutting a
        # field/structure is dropped, leaving a baulk. `density` thins the KEPT cells (the rest stay
        # scrub/fallow), so a `'thin'` locale reads scrubbier than a packed `'dense'` basin.
        placed = 0
        rows = [by0]
        while rows[-1] < by1 - cell * 0.55:
            rows.append(min(by1, rows[-1] + cell * rng.uniform(0.85, 1.2)))
        rows[-1] = by1
        prev_crop = rng.choice(dry_pal)
        for ri in range(len(rows) - 1):
            ry0, ry1 = rows[ri], rows[ri + 1]
            ncol = max(1, round((bx1 - bx0) / cell))
            cuts = [bx0 + (bx1 - bx0) * j / ncol + (0.0 if j in (0, ncol) else rng.uniform(-6, 6)) for j in range(ncol + 1)]
            for cj in range(len(cuts) - 1):
                cx0, cx1 = cuts[cj], cuts[cj + 1]
                quad = [
                    (cx0 + rng.uniform(-2, 2), ry0 + rng.uniform(-2, 2)),
                    (cx1 + rng.uniform(-2, 2), ry0 + rng.uniform(-2, 2)),
                    (cx1 + rng.uniform(-2, 2), ry1 + rng.uniform(-2, 2)),
                    (cx0 + rng.uniform(-2, 2), ry1 + rng.uniform(-2, 2)),
                ]
                mx = sum(p[0] for p in quad) / 4
                my = sum(p[1] for p in quad) / 4
                # REGION test, not point sampling. Center-plus-corners was the old form and it leaks:
                # a small keep-out sitting against the middle of a cell EDGE touches neither the
                # center nor any corner, which is exactly how a wellhead ended up 1 px inside a
                # hatake plot (the overlap matrix found it; the sample points had all cleared the
                # well's 20 ft apron). The cheap point test runs first as a prefilter.
                if _blocked(mx, my) or any(_blocked(px, py) for px, py in quad) or _blocked_region(quad):
                    continue
                qx0, qy0 = min(p[0] for p in quad) - 12, min(p[1] for p in quad) - 12
                qx1, qy1 = max(p[0] for p in quad) + 12, max(p[1] for p in quad) + 12
                if any(qx0 <= cx <= qx1 and qy0 <= cy <= qy1 for cx, cy in grove_clumps):  # no plot covers a grove clump (groves_clear_of_dry_plots)
                    continue
                if rng.random() > fill_p:  # a clear cell left as scrub/fallow (the sub-saturation the tier allows)
                    continue
                if rng.random() < 0.42:  # holdings cluster: usually keep the last crop, sometimes switch
                    prev_crop = rng.choice(dry_pal)
                if rng.random() < garden_frac:
                    crop, (cfill, cfur) = "garden", rng.choice(garden_pal)
                else:
                    crop, (cfill, cfur) = prev_crop[0], prev_crop[1]
                theta = (ri * 0.9 + cj * 1.5 + rng.uniform(-0.15, 0.15)) % math.pi  # neighbors differ (fragmented family strips)
                pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in quad)
                self.add(f'<polygon points="{pts}" fill="{cfill}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
                self._draw_furrows(quad, cfur, theta)
                self.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in quad], "crop": crop, "theta": round(theta, 3)})
                self.dry_polys.append(quad)
                self.block_polys.append(quad)  # no-build cropland; also stops later cells this pass from overlapping
                placed += 1
        return placed

    def near_ring_paddy(self: Settlement, bbox: tuple[float, float, float, float], *, seed: int = 0, cell_ft: float = 150.0, ring_farms: int = 0, avoid: Any = ()) -> int:  # type: ignore[misc]
        """Fill the flat, CLEAR near-ring ground in `bbox` with WET-RICE PADDY basins - the DOMINANT crop of a
        wet-rice county seat's flat waterable near ring (feature 014, settlements.md 'Near-ring farmland density').
        A basin is placed ONLY where it can be LEGITIMATELY WATERED, so `fields_show_water_source` never fires:
        an outline vertex within ~18px of an `M['streams']` segment (the field bank abuts the stream, the stream
        NOT crossing the basin), OR in the pond's 1.0-1.10x ring, OR the basin runs OFF the map edge (exempt).
        Ground with no reachable water is SKIPPED - paddy is never conjured without water (the honest limit: where
        the near ring genuinely lacks water, draw fewer basins / a lower tier, don't fake it). Draws each basin
        via `paddy_field` (the true bunded flooded look, rice-dominant crop mix) and records it as a `kind='paddy'`
        field. Reuses `near_ring_cropland`'s keep-outs. `ring_farms` (city scale) rings each non-off-edge basin
        with that many farmhouses (`city_outside_fields_have_farmhouses`). Call AFTER the combs + structures so it
        skips them; call BEFORE the demoted `near_ring_cropland` so grain fills only what paddy did not. Basins
        stay < 80000px bbox so they are exempt from `common_fields_vary_orientation`. Deterministic own RNG.
        Returns the basin count. Gated by `near_ring_paddy_dominant`."""
        bx0, by0, bx1, by1 = bbox
        bx0, by0 = max(bx0, 12.0), max(by0, 12.0)
        bx1, by1 = min(bx1, self.W - 12.0), min(by1, self.H - 12.0)
        if bx1 - bx0 < 10 or by1 - by0 < 10:
            return 0
        cell = self.px(cell_ft)
        rng = random.Random((seed & 0xFFFF) ^ 0x5A17 ^ (int(bx0) * 131) ^ (int(by0) * 17))

        halo_rects, halo_circles = self._urban_keepouts((bx0, by0, bx1, by1))
        corridors = self._corridor_buffers(3 * self.bscale)
        wat_b = boxed_grid(boxed_segs(self._watercourse_segs()))  # drawn water (streams/channels/comb laterals), pre-boxed once - see _watercourse_segs
        pond = self.M.get("pond")
        hill = self.M.get("hill")
        wall = self.M.get("wall")
        walled_city = self.M.get("meta", {}).get("scale") in CITY_TIER_SCALES and wall is not None and len(wall) >= 3
        streams = [s["poly"] for s in self.M.get("streams", []) if s.get("poly") and len(s["poly"]) >= 2]
        moat = self.M.get("moat")  # a city moat is a reservoir: paddy CAN be moat-fed via a short intake channel
        moat_feed = bool(walled_city and moat and len(moat) >= 3)
        # If the moat is FED by a stream (it has a current), a moat intake must run WITH that current - tap
        # UPSTREAM of the basin (moat_channels_flow_with_current). Derive the flow exactly as the check does.
        moat_flow: tuple[float, float] | None = None
        if moat_feed and moat:
            for sp in streams:
                for entry, origin in ((sp[0], sp[-1]), (sp[-1], sp[0])):
                    if min((seg_dist(entry[0], entry[1], moat[i], moat[i + 1]) for i in range(len(moat) - 1)), default=1e9) <= 35:
                        dxx, dyy = entry[0] - origin[0], entry[1] - origin[1]
                        moat_flow = (0.0, 1.0 if dyy > 0 else -1.0) if abs(dyy) >= abs(dxx) else (1.0 if dxx > 0 else -1.0, 0.0)
                        break
                if moat_flow:
                    break
        # ROADS + FUNERARY are extra keep-outs a paddy basin must clear (fields_clear_of_road / funerary_
        # clear_of_fields), on top of near_ring_cropland's set. The moat itself gets a setback (city_fields_
        # clear_of_wall_moat). Roads also block a moat intake channel (roads_bridge_water wants a bridge at a
        # crossing - simpler to route the channel clear of roads).
        road_lines = []
        if self.M.get("road"):
            road_lines.append((self.M["road"], 34.0))
        road_lines += [(st["pts"], st.get("w", 20) / 2 + 20) for st in self.M.get("town_streets", [])]
        funerary = []
        for k in ("cemeteries", "cremation_grounds", "ossuaries"):
            for o in self.M.get(k, []) or []:
                p = o.get("poly") if isinstance(o, dict) else o
                if isinstance(o, dict) and "x" in o and "w" in o:
                    funerary.append((o["x"] - o["w"] / 2 - 60, o["y"] - o["h"] / 2 - 60, o["x"] + o["w"] / 2 + 60, o["y"] + o["h"] / 2 + 60))
                elif p and len(p) >= 3:
                    xs = [q[0] for q in p]
                    ys = [q[1] for q in p]
                    funerary.append((min(xs) - 60, min(ys) - 60, max(xs) + 60, max(ys) + 60))  # a flood-prone paddy sets back from graves (funerary_set_back_from_water)
        # structure footprints (center + half-diagonal) a moat intake channel must not cross (no_structure_on_channel)
        struct_cd = []
        for k in ("houses", "buildings", "manors", "merchant_estates", "storehouses", "religious", "ministries", "flophouses", "governor_mansion", "mausoleums"):
            for o in self.M.get(k, []) or []:
                if isinstance(o, dict) and "x" in o and "w" in o:
                    struct_cd.append((o["x"], o["y"], math.hypot(o["w"] / 2, o["h"] / 2) + 5))

        def _nearest_moat(px: float, py: float) -> tuple[float, float] | None:
            # the nearest moat vertex UPSTREAM of the basin, so the intake flows WITH the moat current. If the
            # moat has a current and NO vertex is upstream of the basin (it sits past the moat's headwater end),
            # there is no honest with-current tap - return None so the basin is skipped, not fed backwards.
            if not moat:  # pragma: no cover - only called under moat_feed (moat is truthy); guard is for the type-checker
                return None
            cand: Any = moat
            if moat_flow is not None:
                cand = [mp for mp in moat if (px - mp[0]) * moat_flow[0] + (py - mp[1]) * moat_flow[1] >= 4]
                if not cand:
                    return None
            best = min(cand, key=lambda mp: (mp[0] - px) ** 2 + (mp[1] - py) ** 2)
            return (best[0], best[1])

        def _channel_clear(a: tuple[float, float], b: tuple[float, float]) -> bool:
            if any(seg_dist(cx, cy, a, b) < cr for cx, cy, cr in struct_cd):
                return False  # pragma: no cover - defensive: basins are already kept off structures, so a moat intake to a placed basin rarely lines up to cross one
            if any((fx0 + fx1) / 2 >= min(a[0], b[0]) - 40 and _seg_near_rect(a, b, (fx0, fy0, fx1, fy1)) for fx0, fy0, fx1, fy1 in funerary):
                return False  # pragma: no cover - defensive: the basin funerary keep-out (60px) already holds channels off graves; this belts the channel line too
            return not any(any(seg_dist(rp[i][0], rp[i][1], a, b) < hw + 2 for i in range(len(rp))) for rp, hw in road_lines)

        def _seg_near_rect(a: tuple[float, float], b: tuple[float, float], r: tuple[float, float, float, float]) -> bool:
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            return seg_dist(cx, cy, a, b) < math.hypot((r[2] - r[0]) / 2, (r[3] - r[1]) / 2)

        def _blocked(px: float, py: float) -> bool:
            return bool(
                any(point_in_poly(px, py, ff) for ff in self.field_polys)
                or any(point_in_poly(px, py, b) for b in self.block_polys)
                or any(point_in_poly(px, py, d) for d in self.dry_polys)
                or any(point_in_poly(px, py, c) for c in self.clearings)
                or any(point_in_poly(px, py, a) for a in avoid)
                or any(any(seg_dist(px, py, pl[i], pl[i + 1]) < hw for i in range(len(pl) - 1)) for pl, hw in corridors)
                or self._on_watercourse(px, py, near=wat_b.near)
                or (pond is not None and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.0)
                or any(x0r <= px <= x1r and y0r <= py <= y1r for x0r, y0r, x1r, y1r in halo_rects)
                or any((px - hx) ** 2 + (py - hy) ** 2 <= hr * hr for hx, hy, hr in halo_circles)
                or (hill is not None and ((px - hill[0]) / (hill[2] * 1.35)) ** 2 + ((py - hill[1]) / (hill[3] * 1.35)) ** 2 <= 1.0)
                or (walled_city and wall is not None and point_in_poly(px, py, wall))
                or any(any(seg_dist(px, py, rp[i], rp[i + 1]) < hw for i in range(len(rp) - 1)) for rp, hw in road_lines)  # off roads/streets (fields_clear_of_road)
                or any(fx0 <= px <= fx1 and fy0 <= py <= fy1 for fx0, fy0, fx1, fy1 in funerary)  # off graves/cremation/ossuary (funerary_clear_of_fields)
                or (moat is not None and len(moat) >= 3 and _near_moat(px, py))  # setback off the moat itself (city_fields_clear_of_wall_moat)
                or _stream_dist(px, py) < 22  # off the streams entirely - a basin never straddles the current (streams_avoid_fields)
            )

        def _near_moat(px: float, py: float) -> bool:
            if not moat:  # pragma: no cover - only called when moat is set (the _blocked caller guards it); guard is for the type-checker
                return False
            return any(seg_dist(px, py, moat[i], moat[i + 1]) < self.M.get("moat_width", 22) / 2 + 15 for i in range(len(moat) - 1))

        def _stream_dist(px: float, py: float) -> float:
            return min((seg_dist(px, py, sp[i], sp[i + 1]) for sp in streams for i in range(len(sp) - 1)), default=1e9)

        def _watered(corners: list[tuple[float, float]]) -> bool:
            # a basin runs OFF the view edge (exempt) or sits in the pond's abut ring; else it needs the moat feed
            off_edge = any(px < 20 or px > self.W - 20 or py < 20 or py > self.H - 20 for px, py in corners)
            in_pond_ring = pond is not None and any(1.0 < ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.09 for px, py in corners)
            return off_edge or in_pond_ring

        # PASS 1: place every legitimately-watered basin (records field_polys) so PASS 2's wells + farm rings
        # can flow around ALL of them. A city basin the pond/edge does not water is MOAT-FED via a short intake
        # channel (the moat is a reservoir - historical, and what city_moat_irrigates_fields expects), but only
        # where that channel runs clear of structures/roads/funerary.
        blocks: list[tuple[float, float, float, float, float, float]] = []
        rows = [by0]
        while rows[-1] < by1 - cell * 0.55:
            rows.append(min(by1, rows[-1] + cell * rng.uniform(0.85, 1.2)))
        rows[-1] = by1
        for ri in range(len(rows) - 1):
            ry0, ry1 = rows[ri], rows[ri + 1]
            ncol = max(1, round((bx1 - bx0) / cell))
            cuts = [bx0 + (bx1 - bx0) * j / ncol for j in range(ncol + 1)]
            for cj in range(len(cuts) - 1):
                ix0, iy0, ix1, iy1 = cuts[cj] + 7, ry0 + 7, cuts[cj + 1] - 7, ry1 - 7  # inset -> basins abut with a baulk, never overlap
                if ix1 - ix0 < 24 or iy1 - iy0 < 24 or (ix1 - ix0) * (iy1 - iy0) >= 79000:  # < 80000px: exempt from common_fields_vary_orientation
                    continue
                corners = [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]
                mx, my = (ix0 + ix1) / 2, (iy0 + iy1) / 2
                edge_pts = corners + [(mx, iy0), (mx, iy1), (ix0, my), (ix1, my)]  # test EDGE midpoints too, so a stream/keep-out crossing an edge between corners is caught
                if any(_blocked(px, py) for px, py in edge_pts + [(mx, my)]):
                    continue
                if any(
                    ix0 - 22 <= vx <= ix1 + 22 and iy0 - 22 <= vy <= iy1 + 22 for sp in streams for vx, vy in sp
                ):  # pragma: no cover - defensive redundancy: _blocked's 9-point edge sampling already drops stream-adjacent cells; this catches a bare mid-edge vertex
                    continue  # no stream vertex near the basin -> the current never runs through it (streams_avoid_fields)
                moat_x = moat_y = None
                if not _watered(corners):
                    if moat_feed:
                        mp = _nearest_moat(mx, my)
                        if mp is not None and _channel_clear(mp, (mx, my)):
                            moat_x, moat_y = mp[0], mp[1]
                    if moat_x is None:
                        continue  # NO paddy without a legitimate water source (no with-current moat tap either)
                name_i = len(blocks)
                self.paddy_field((ix0, iy0, ix1, iy1), None, f"nrp_{name_i}", amp=6, plot=46)
                if moat_x is not None:  # draw the moat intake so the basin shows a real water source
                    self.channel((moat_x, moat_y), (mx, my), {"kind": "moat"}, {"kind": "field", "name": f"nrp_{name_i}"}, amp=6, width=2.5)
                blocks.append((ix0, iy0, ix1, iy1, mx, my))
        # PASS 2 (city only): each outside field needs >=2-3 farmhouses + a well (city_outside_fields_have_farmhouses,
        # field_ringed, farm_wells_within_reach). Wells first (they reserve ground the ring flows around), then rings.
        if walled_city:
            for ix0, iy0, ix1, iy1, _mx, _my in blocks:  # rings FIRST, so the well can then sit AMONG the farmhouses
                self.ring(("poly", [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]), max(ring_farms, 12), 13, ["plain"])
                self.ring(
                    ("poly", [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]), 8, 30, ["plain"]
                )  # a second, wider ring: fills the shown-edge density (outside_fields_farmhouse_density) where the tight inner ring dropped candidates
            houses = self.M.get("houses", [])
            for ix0, iy0, ix1, iy1, mx, my in blocks:  # up to TWO wells per basin (opposite sides) AND within 95px of a farmhouse (wells_among_dwellings + farm_wells_within_reach)
                dropped = 0
                for wx, wy in ((ix1 + 15, my), (ix0 - 15, my), (mx, iy1 + 15), (mx, iy0 - 15), (ix1 + 15, iy1 + 15), (ix0 - 15, iy0 - 15)):
                    if (
                        12 < wx < self.W - 12
                        and 12 < wy < self.H - 12
                        and not _blocked(wx, wy)
                        and self._well_ground_clear(wx, wy)
                        and any((h["x"] - wx) ** 2 + (h["y"] - wy) ** 2 < 90 * 90 for h in houses)
                    ):
                        self.well(wx, wy)
                        dropped += 1
                        if dropped >= 2:
                            break
        return len(blocks)
