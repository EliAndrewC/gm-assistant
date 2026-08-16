"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ._geom import Poly, Pt, boxed_grid, boxed_hit, boxed_polys, boxed_seg_hit, boxed_segs, edge_dist, point_in_poly, region_blocked, seg_dist, smooth_closed, smooth_points
from ._knobs import CITY_TIER_SCALES

if TYPE_CHECKING:
    from .core import Settlement


class LandMixin:
    def perimeter_dike(self: Settlement, inner_env: Any, seed: int = 0, label: str = "perimeter dike", width: tuple[float, float] = (14.0, 40.0), gaps: Any = ()) -> None:  # type: ignore[misc]
        """A reclaimed-polder PERIMETER DIKE, drawn as an irregular hand-piled EARTHWORK BAND (not a ruled
        tan line). China-first grounding (research 2026-07-22, recorded in settlements.md 'Perimeter dike'):
        a wei-tian 圩田 / dike-pond dike was dredged pond-mud heaped and packed (the 挖塘培基 dig-and-pile
        cycle that also made the ponds), trapezoidal in section, PLANTED with mulberry/willow to bind the
        soil, walked and lived on, and constantly breached-and-repaired. The SURVEYED interior grid stays
        rectilinear, but the OUTER dike FOLLOWED THE NATURAL WATER EDGE (lake/creek/marsh) in gentle curves
        and non-square bends - the 'fish-scale polder' 鱼鳞圩 form; the dead-straight right-angled rectangle
        is a POST-1949 industrial shape. So `inner_env` (the rectilinear grid boundary) is the dike's INNER
        face, and this draws the OUTER face as an organic curve bulging outward by a VARYING amount (the dike
        width varies - thicker on the exposed water side / at pressure points, pinched where repaired), with
        rounded non-square corners, filled as a mottled vegetated earthwork. TRUE SCALE: a perimeter dike ran
        ~6-10 m+ wide (wider than the ~6.7 m inter-pond mulberry dikes it rings, not the old under-scale
        4.4 px line), so the band is drawn to true width, not floored. Records M['dikes']; labeled (a polder
        dike is NOT an "obvious" feature - the GM asked for it named)."""
        from waterfields import BUND

        R = random.Random(seed)
        pts = list(inner_env)
        if pts and pts[0] == pts[-1]:
            pts = pts[:-1]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        wlo, whi = width
        m = len(pts)
        dense: list[tuple[float, float, int]] = []
        for i in range(m):
            a, b = pts[i], pts[(i + 1) % m]
            steps = max(3, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 34))
            for s in range(steps):
                t = s / steps
                dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, i))
        n = len(dense)
        ph0, ph1, ph2 = R.uniform(0, math.tau), R.uniform(0, math.tau), R.uniform(0, math.tau)
        inner_s: Poly = []
        outer_s: Poly = []
        w_seen: list[float] = []
        for k, (x, y, ei) in enumerate(dense):
            a, b = pts[ei], pts[(ei + 1) % m]
            ex, ey = b[0] - a[0], b[1] - a[1]
            eL = math.hypot(ex, ey) or 1.0
            nx, ny = -ey / eL, ex / eL  # outward edge normal (flip toward away-from-centroid)
            if nx * (x - cx) + ny * (y - cy) < 0:
                nx, ny = -nx, -ny
            u = k / n * math.tau
            # broad shoreline-following bulges (u*2) + mid + fine variation - the dike thickens along an old
            # water edge and pinches where it was repaired, so the outer face reads organic, not a ruled line
            wf = 0.5 + 0.26 * math.sin(u * 2 + ph0) + 0.22 * math.sin(u * 3 + ph1) + 0.16 * math.sin(u * 5 + ph2)
            w = wlo + (whi - wlo) * max(0.0, min(1.0, wf)) + R.uniform(-3, 3)
            w_seen.append(w)
            outer_s.append((x + nx * w, y + ny * w))
            # the inner face hugs the grid boundary and wobbles OUTWARD only (never intrudes past the
            # envelope into the field) - so the ring canal running just inside the envelope stays clear of
            # the dike, and water crosses the dike only at the sluices
            inner_s.append((x + nx * R.uniform(0.0, 3.0), y + ny * R.uniform(0.0, 3.0)))
        band = [*outer_s, *reversed(inner_s)]
        d = smooth_closed(band)
        # SLUICE GAPS (GM 2026-07-22): where a channel crosses the dike (the inlet + outfall sluices), the
        # earthwork is NOTCHED - a dug gap the water runs THROUGH - instead of the dike running unbroken under
        # the channel (which read as the water flowing OVER the top of the bank). Split the band into the runs
        # BETWEEN the gaps and draw each as its own capped strip; with no gaps this is the single full loop,
        # byte-identical to before. Keep-out, label, width and the recorded outline still use the FULL band.
        gap_pts = [(float(gx), float(gy)) for gx, gy in gaps]
        gap_hw = 15.0
        if gap_pts:
            keep = [all(math.hypot(x - gx, y - gy) > gap_hw for gx, gy in gap_pts) for x, y, _ei in dense]
            runs: list[list[int]] = []
            if all(keep):
                runs = [list(range(n))]
            else:
                start = next(i for i in range(n) if not keep[i])
                cur: list[int] = []
                for j in range(n):
                    i = (start + j) % n
                    if keep[i]:
                        cur.append(i)
                    elif cur:
                        runs.append(cur)
                        cur = []
                if cur:
                    runs.append(cur)
            run_paths = [smooth_closed([outer_s[i] for i in run] + [inner_s[i] for i in reversed(run)]) for run in runs if len(run) >= 2]
        else:
            run_paths = [d]
        for rp in run_paths:
            self.add(f'<path d="{rp}" fill="{BUND}" stroke="#9C8558" stroke-width="1.2" stroke-linejoin="round" opacity="0.95"/>')
        # MOTTLE + PLANTED ROWS (reworked GM 2026-07-24 - accuracy pass; settlements.md 'Perimeter dike'):
        # the old render scattered crowns at random over the band, but dike planting was ROW planting along
        # the alignment - a WILLOW row on the water face (wave-wash armor + withy supply; the Qing Willow
        # Palisade statute of one whip per 5 chi ~ 5.5 ft is the closest attested in-row figure, and willow-
        # fascine rows on erosive soil run 1-1.5 m apart, the same soil mechanics) and a MULBERRY row on the
        # inner face (the dike is prime sericulture ground - Lake Tai mulberry sat on the tang banks). Earth
        # mottle (patch-repairs of different ages) stays scattered - repairs, unlike planting, ARE haphazard.
        smoothed = smooth_points(band)
        bx0, bx1 = min(p[0] for p in smoothed), max(p[0] for p in smoothed)
        by0, by1 = min(p[1] for p in smoothed), max(p[1] for p in smoothed)
        cid = self._cid("dike")
        st = random.getstate()
        random.seed(seed ^ 0x1D)
        g = [f'<clipPath id="{cid}">' + "".join(f'<path d="{rp}"/>' for rp in run_paths) + "</clipPath>", f'<g clip-path="url(#{cid})">']
        for _ in range(int((bx1 - bx0 + by1 - by0) * 0.7)):
            px, py = random.uniform(bx0, bx1), random.uniform(by0, by1)
            if not point_in_poly(px, py, smoothed):
                continue
            col = random.choice(["#A8895A", "#B79B68", "#D2BC8C", "#9C8150"])  # earth mottle: darker packed / lighter dried patches
            rx, ry = random.uniform(5, 13), random.uniform(4, 9)
            g.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{col}" opacity="0.4"/>')
        # the two planted rows follow each band RUN (so they skip the sluice notches with the earthwork).
        # In-row spacings are drawn at the loose end (willow 8.5 px vs the attested ~5.5 ft; mulberry 4.4 px
        # at the loose end of 3-5 ft) so crowns read as touching runs, not a fused hedge - the same
        # legibility precedent as the pond banks (settlements.md 'Polder fourth pass', quantified departure).
        veg_runs = runs if gap_pts else [list(range(n))]

        def _row_walk(frac: float, step: float) -> list[Pt]:
            out2: list[Pt] = []
            for vrun in veg_runs:
                line = [(inner_s[i][0] + (outer_s[i][0] - inner_s[i][0]) * frac, inner_s[i][1] + (outer_s[i][1] - inner_s[i][1]) * frac) for i in vrun]
                for a2, b2 in zip(line, line[1:], strict=False):
                    seg = math.hypot(b2[0] - a2[0], b2[1] - a2[1])
                    for k2 in range(int(seg / step)):
                        f2 = (k2 + 0.5) * step / seg
                        out2.append((a2[0] + (b2[0] - a2[0]) * f2, a2[1] + (b2[1] - a2[1]) * f2))
            return out2

        for wx, wy in _row_walk(0.74, 8.5):  # the WILLOW row rides the outer (water) face - pollarded, larger crowns
            wcol = random.choice(("#7C9856", "#87A45C", "#6E8B4A"))
            g.append(f'<circle cx="{wx + random.uniform(-1.4, 1.4):.1f}" cy="{wy + random.uniform(-1.4, 1.4):.1f}" r="{random.uniform(3.5, 5.5):.1f}" fill="{wcol}" opacity="0.75"/>')
        for mx2, my2 in _row_walk(0.26, 4.4):  # the MULBERRY row on the inner face - coppiced, same form as the pond banks
            mcol2 = random.choice(("#6E8B4A", "#7C9A54", "#5E7C40"))
            g.append(f'<circle cx="{mx2 + random.uniform(-1.2, 1.2):.1f}" cy="{my2 + random.uniform(-1.2, 1.2):.1f}" r="{random.uniform(2.2, 3.6):.1f}" fill="{mcol2}" opacity="0.85"/>')
        g.append("</g>")
        self.add("".join(g))
        random.setstate(st)
        self.M.setdefault("dikes", []).append(
            {
                "outline": [[round(p[0], 1), round(p[1], 1)] for p in smoothed],
                # the CREST centerline (inner/outer midpoint at every densified point, a closed loop) - the
                # walkable top of the bank. Recorded so dike_top_houses can seat a dike-top village on it.
                "crest": [[round((inner_s[i][0] + outer_s[i][0]) / 2, 1), round((inner_s[i][1] + outer_s[i][1]) / 2, 1)] for i in range(n)],
                "label": label,
                "w_min": round(min(w_seen), 1),
                "w_max": round(max(w_seen), 1),
                "gaps": [[round(gx, 1), round(gy, 1)] for gx, gy in gap_pts],
            }
        )
        # the dike is a raised earthwork bank - NO-BUILD ground: houses and the windbreak grove keep OFF it
        # (GM 2026-07-22). Register the band as a placement keep-out so try_place / farmsteads / village_grove
        # flow around it (validated by structures_clear_of_dike).
        self.block_polys.append(smoothed)
        if label:
            # site the label on a clear stretch: the outward-most mid-edge point that is NOT near the village
            houses = self.M.get("houses", [])
            hx = sum(h["x"] for h in houses) / len(houses) if houses else cx
            best = max(outer_s, key=lambda p: (p[1] < cy) * 1000 - abs(p[0] - cx) - (200 if (p[0] - cx) * (hx - cx) > 0 else 0))
            self.label(best[0], best[1] - 8, label, 10, italic=True, color="#6B5836")

    def dike_top_houses(self: Settlement, count: int, seed: int = 0, dike: int = 0, span: tuple[float, float] = (0.0, 1.0), size: tuple[float, float] = (46.0, 28.0), gap_clear: float = 34.0) -> int:  # type: ignore[misc]
        """A DIKE-TOP VILLAGE: farmhouses in SINGLE FILE ON the perimeter dike crest (settlement_form
        'dike_top') - the settlement form for an ISLET polder with water on every flank and no landward
        shore to build on. Historical grounding (researched 2026-07-24, settlements.md 'Polder siting Q&A'):
        where a polder abuts the natural shore the village sits on the landward dry ground (the Enokida/
        Kuwabata configuration), but in the DEEP-water landscape the only dry ground is the polder's own
        raised earth, and settlement went up onto it - linear dike/canal-bank villages "taking advantage of
        the elevated typology" are attested in the Jiangnan polder lands from the 8th century on, and Fei
        Xiaotong's Kaixiangong shows the interior-stream variant of the same move. Each house stands on a
        PLATFORM - a locally widened stretch of crest (piled spoil, the same 挖塘培基 cycle that built the
        dike; the platform dimensions are a reasoned reconstruction, no pre-modern survey of house-pad sizes
        was found) - so the drawn band bulges at each homestead instead of the house overhanging the water.
        No homestead bundle up here: the crest IS the dooryard/lane, gardens live down on the parcels, so
        this places bare houses (wells/lanes/civic features remain the map's own job). Call AFTER
        perimeter_dike; houses draw immediately (platform under house) and are tagged `on_dike` in
        M['houses'], which exempts them from structures_clear_of_dike while dike_top_houses_on_the_dike
        verifies each actually sits on the band. `span` = (start, end) fractions of the crest loop's arc
        length, so a gen can line one flank rather than the full ring; sites within `gap_clear` px of a
        sluice gap are skipped (nobody builds over the sluice notch). Returns the number placed."""
        from waterfields import BUND

        dk = self.M["dikes"][dike]
        crest = [(float(px_), float(py_)) for px_, py_ in dk["crest"]]
        gaps = [(float(gx), float(gy)) for gx, gy in dk.get("gaps", [])]
        loop = crest + [crest[0]]
        seg = [math.hypot(loop[i + 1][0] - loop[i][0], loop[i + 1][1] - loop[i][1]) for i in range(len(loop) - 1)]
        cum = [0.0]
        for sg in seg:
            cum.append(cum[-1] + sg)
        total = cum[-1]

        def at(sa: float) -> tuple[float, float, float]:  # point + tangent angle (deg) at arc length sa
            sa = sa % total
            i = max(0, min(len(seg) - 1, next(j for j in range(len(seg)) if cum[j + 1] >= sa)))
            t = (sa - cum[i]) / max(1e-9, seg[i])
            a, b = loop[i], loop[i + 1]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))

        hw, hh = self.px(size[0]), self.px(size[1])
        pw, ph = hw + self.px(14.0), hh + self.px(10.0)  # the widened-crest platform pad
        s0, s1 = span[0] * total, span[1] * total
        step = (s1 - s0) / max(1, count)
        st = random.getstate()
        random.seed(seed ^ 0xD1E)
        placed_s: list[float] = []
        n_placed = 0
        for i in range(count):
            sa = s0 + (i + 0.5) * step + random.uniform(-0.18, 0.18) * step
            x, y, ang = at(sa)
            if any(math.hypot(x - gx, y - gy) < gap_clear for gx, gy in gaps):
                continue  # never build over a sluice notch
            if any(abs(sa - ps) < hw * 1.15 for ps in placed_s):
                continue  # single file with daylight between neighbors
            th = math.radians(ang)
            cs, sn = math.cos(th), math.sin(th)
            g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f})">']
            g.append(f'<rect x="{-pw / 2:.1f}" y="{-ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="6" fill="{BUND}" stroke="#9C8558" stroke-width="1.1" opacity="0.95"/>')
            for _ in range(3):  # patch-repair mottle, same treatment as the dike body
                mx, my = random.uniform(-pw * 0.32, pw * 0.32), random.uniform(-ph * 0.28, ph * 0.28)
                mcol = random.choice(["#A8895A", "#B79B68", "#D2BC8C"])
                g.append(f'<ellipse cx="{mx:.1f}" cy="{my:.1f}" rx="{random.uniform(4, 8):.1f}" ry="{random.uniform(3, 5):.1f}" fill="{mcol}" opacity="0.4"/>')
            g.append("</g>")
            self.add("".join(g))
            self.house(x, y, hw, hh, "plain", rot=ang)
            corners = [(x + cs * dx_ - sn * dy_, y + sn * dx_ + cs * dy_) for dx_, dy_ in ((-pw / 2, -ph / 2), (pw / 2, -ph / 2), (pw / 2, ph / 2), (-pw / 2, ph / 2))]
            self.block_polys.append(corners)
            self.placed.append((x, y, pw, ph))
            self.M["houses"].append(
                {
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "w": round(hw, 1),
                    "h": round(hh, 1),
                    "kind": "plain",
                    "rot": round(ang, 1),
                    "role": None,
                    "shed": False,
                    "wealth": 1.0,
                    "on_dike": True,
                    "platform": [round(pw, 1), round(ph, 1)],
                }
            )
            placed_s.append(sa)
            n_placed += 1
        random.setstate(st)
        self.M["meta"].setdefault("settlement_form", "dike_top")
        return n_placed

    def commons(self: Settlement, poly: Any, role: str = "commons", avoid: Any = (), render: str = "scrub") -> None:  # type: ignore[misc]
        """FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far (upslope / windward) side,
        BEYOND the fengshui back-grove: coarse grass, low brush, and a FEW scattered SCRAGGLY pines, kept
        cropped bare by constant firewood + grass gathering. Deliberately drawn OPEN and SPARSE on drier,
        poorer ground so it is VISUALLY DISTINCT from the dense, dark, closed-canopy village grove - this is a
        COMMONS (not anyone's field), non-arable. WHY (south China's hills were stripped for fuel/timber over a
        millennium - open pine + grass + erosion; the protected grove is the green EXCEPTION; the back slope
        also carried the graves + dry hill-crops): settlements.md 'Village windbreak' / back-slope land use. Recorded
        in M['commons']. `role` picks the glyph (woodland / pasture / commons); `avoid` is a list of KEEP-OUT
        polygons (e.g. the hamlet cluster) the scatter stays out of, so ground-cover never creeps onto them."""
        # SCOPED (2026-08-08): the tuft/brush scatter is decoration keyed to the common it fills.
        if render == "bare":
            # CLAIMED but UNDRAWN ground (GM 2026-08-10, on the capital's ring bands reading as
            # weeds): the record still claims the ground for the empty-space detector and names
            # its role, but nothing is scattered - kept working ground reads as clean parchment,
            # not scrub. The default stays "scrub" so every village commons is byte-identical.
            xs0 = [q[0] for q in poly]
            ys0 = [q[1] for q in poly]
            self.M.setdefault("commons", []).append(
                {
                    "x": round(sum(xs0) / len(xs0), 1),
                    "y": round(sum(ys0) / len(ys0), 1),
                    "w": round(max(xs0) - min(xs0), 1),
                    "h": round(max(ys0) - min(ys0), 1),
                    "rot": 0,
                    "role": role,
                    "seq": len(self.M.get("commons", [])) + 1,
                    "poly": [list(q) for q in poly],
                }
            )
            return
        with self.rng_scope("commons", len(poly), poly[0][0], poly[0][1]):
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            bs = self.bscale
            area = (x1 - x0) * (y1 - y0)
            st = random.getstate()
            random.seed(int(abs(x0) * 7 + abs(y0) * 3 + round(x1 - x0)))
            feather = 42 * bs  # scrub THINS toward the boundary (a soft, ragged edge, not a hard line)

            pond = self.M.get("pond")
            halo_rects, halo_circles = self._urban_keepouts((x0, y0, x1, y1))  # the urban-clearance halo (see _urban_keepouts)
            corridors = self._corridor_buffers(
                3 * bs
            )  # lanes AND town streets AND the road: every trodden/maintained tread stays bare (the old skip knew only lanes, so scrub drew on the Imperial Road bed - GM 2026-07-21, Hoshizora)
            # PRE-BOX every static keep-out ONCE (see boxed_hit): _sparse below runs per SCATTER POINT,
            # and these lists do not change while a region scatters
            # INDEXED (2026-08-04): boxing alone dropped the cost per keep-out but still VISITED every
            # one per scatter point - 948k boxed_hit calls iterating 25M items on Kikuta, whose gen was
            # still 81% ground cover. The grids narrow each point to its own cell; the exact tests below
            # are the same ones, run on what `near` returns.
            # CROP MARGIN (see _CROP_MARGIN_FT): the crop keep-out is every PADDY (field_polys) plus
            # every DRY PLOT (dry_polys - block_polys also carries them, but reading the crop registry
            # directly is what the grove/lane skips do, and it survives a gen that registers only one),
            # padded by the margin. Boxes carry the WORST-CASE pad - margin plus the tallest glyph's
            # drawn reach, a pine tip at 14*bs - because the bbox prefilter must never reject a point
            # the exact edge test wants (boxed_hit's contract); the exact test gets the per-glyph lean.
            crop_pad = self.px(self._CROP_MARGIN_FT)
            fld_b = boxed_grid(boxed_polys(list(self.field_polys) + list(self.dry_polys), pad=crop_pad + 14 * bs))
            blk_b = boxed_grid(boxed_polys(self.block_polys))
            clr_b, avd_b, cor_b = boxed_grid(boxed_polys(self.clearings)), boxed_grid(boxed_polys(avoid)), boxed_grid(boxed_segs(corridors))
            # drawn water pre-boxed once (see _watercourse_segs); irrigation channels additionally
            # carry the CUT-BANK margin (_BANK_MARGIN_FT - a maintained bank is scythed like a field
            # margin), streams stay at drawn width so the brook's natural bank keeps its grass
            wat_b = boxed_grid(boxed_segs(self._watercourse_segs(channel_margin=self.px(self._BANK_MARGIN_FT))))

            def _sparse(
                px: float, py: float, drop: float, lean: float = 0.0
            ) -> bool:  # skip a scatter point outside the poly, on/near a crop, on a corridor/water, in the urban halo, in a keep-out, or (probabilistically) near the edge; `lean` = the glyph's drawn reach, so a tall glyph stands its own height back from the crop margin
                if (
                    not point_in_poly(px, py, poly)
                    or boxed_hit(px, py, fld_b.near(px, py), edge_pad=crop_pad + lean)
                    or boxed_seg_hit(px, py, cor_b.near(px, py))  # keep scrub off every trodden tread (lane/street/road) so no path reads overgrown
                    or self._on_watercourse(px, py, near=wat_b.near)  # ... and OFF the pond + streams/channels (scrub never draws over open water)
                    or (pond and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.0)
                    or any(
                        x0r <= px <= x1r and y0r <= py <= y1r for x0r, y0r, x1r, y1r in halo_rects
                    )  # ... and OUT of the urban-clearance halo: the swept/trodden ground around every structure, not just its footprint
                    or any((px - hx) ** 2 + (py - hy) ** 2 <= hr * hr for hx, hy, hr in halo_circles)  # ... and clear of every wellhead's trodden apron
                    or boxed_hit(px, py, blk_b.near(px, py))  # ... and OFF any building/shrine/torii footprint (a commons that OVERLAPS the shrine must not scatter scrub over the hall + arch)
                    or boxed_hit(px, py, clr_b.near(px, py))  # ... and off the swept sacred/funerary verge (tended precinct, sando, grave collar)
                    or boxed_hit(px, py, avd_b.near(px, py))
                ):  # ... and OUT of any keep-out (the hamlet cluster stays clear of cover)
                    return True
                ed = edge_dist(px, py, poly)
                return ed < feather and random.random() > (ed / feather) ** drop

            # NO solid fill: a filled polygon always has a crisp geometric EDGE (that read as a rhombus). Each land
            # type is defined PURELY by its feathered scatter, which thins to nothing at the margin - so the ground
            # has no boundary at all, just its cover petering out onto the open slope. THREE distinct looks so land
            # types read apart at a glance (the GM's rule - grass and woods must NOT look the same):
            #   role="woodland"  -> a COPPICE WOOD: individual, spaced tree CROWNS, an OPEN canopy (gaps show) - the
            #                       upland/ridge wood the hamlet coppices. Clearly TREES, but lighter and more open
            #                       than the dense DARK closed-canopy fengshui village grove (they stay distinct too).
            #   role="pasture"   -> OPEN GRAZING GRASS: grass tufts + the odd brush dot, NO trees at all - reads as
            #                       open pasture, unmistakably NOT woodland.
            #   role="commons"/"grazing" (default) -> the cut-over fuel/fodder scrub: grass + a FEW scraggly pines.
            # SVG-size: the grass BLADES are ~98% of a to-scale map's <line> elements and all share ONE constant
            # style, so they go in a bucket emitted ONCE inside a styled <g> (bare coords per line), not one full
            # stroke=...stroke-width=... string each - ~30% off the file, content-lossless (same lines, grouped),
            # render is visually identical (only the z-order of overlapping scrub texture shifts, in the margins;
            # the fields/buildings are pixel-identical). The sparse dots/pines keep their inline styles.
            g: list[str] = []
            blades: list[str] = []
            _wd_crowns = 0
            if role == "woodland":
                for _ in range(int(area / (540 * bs * bs))):  # spaced crowns: an OPEN coppice canopy, gaps showing
                    cx, cy = random.uniform(x0, x1), random.uniform(y0, y1)
                    if _sparse(cx, cy, 0.6, 11.5 * bs):  # lean = the largest crown radius, so no canopy overhangs a crop
                        continue
                    r = random.uniform(6.5, 11.5) * bs
                    col = random.choice(("#6E8B4A", "#7C9856", "#87A45C"))
                    # RECORD the crown (known-open ledger 2026-08-16, both review rounds
                    # independently): these used to be SVG ink only, so no manifest check could
                    # count a stand's canopy - which is how a zero-crown "woodland" parcel could
                    # ship green. Same flat [x, y, r] run the homestead groves use.
                    self.M["tree_crowns"] += [round(cx, 1), round(cy, 1), round(r, 1)]
                    _wd_crowns += 1
                    g.append(f'<ellipse cx="{cx:.1f}" cy="{cy + 2 * bs:.1f}" rx="{r:.1f}" ry="{r * 0.72:.1f}" fill="#59703E" fill-opacity="0.30"/>')  # soft ground shadow
                    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col}" stroke="#4C6234" stroke-width="0.7"/>')  # the crown
                    g.append(f'<circle cx="{cx - r * 0.32:.1f}" cy="{cy - r * 0.32:.1f}" r="{r * 0.42:.1f}" fill="#A6BA79" fill-opacity="0.55"/>')  # sun highlight
            else:
                for _ in range(int(area / (74 * bs * bs))):  # coarse grass tufts + the odd low brush dot
                    gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
                    if _sparse(gx, gy, 0.7):
                        continue
                    if random.random() < 0.14:  # a low brush dot
                        g.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="{random.uniform(1.5, 2.4) * bs:.1f}" fill="#94A063" fill-opacity="0.85"/>')
                    else:  # a grass tuft: a few short diverging blades (bucketed - see the note at `blades`)
                        for _ in range(3):
                            a, bl = random.uniform(-0.45, 0.45), random.uniform(2.4, 4.2) * bs
                            blades.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx + math.sin(a) * bl:.1f}" y2="{gy - math.cos(a) * bl:.1f}"/>')
                if role != "pasture":  # the SCRAGGLY pines belong to cut-over scrub, NOT to open pasture
                    for _ in range(max(2, int(area / (6000 * bs * bs)))):  # a few SCRAGGLY hill pines (sparse, individual, open)
                        px, py = random.uniform(x0 + 6, x1 - 6), random.uniform(y0 + 6, y1 - 6)
                        if _sparse(px, py, 0.5, 14 * bs):  # lean = the tallest pine's tip reach, so no pine leans over a crop
                            continue
                        th = random.uniform(9, 14) * bs
                        g.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py - th:.1f}" stroke="#7A6A48" stroke-width="{1.1 * bs:.1f}"/>')  # thin trunk
                        for k in range(3):  # sparse open branches - a scraggly wind-cropped pine, NOT a dense crown
                            ly, sp = py - th * (0.45 + 0.25 * k), (3.6 - k) * bs
                            g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px - sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
                            g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px + sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
            self.add(f'<g stroke="#A7A860" stroke-width="0.8">{"".join(blades)}</g>')  # bucketed blades (empty group when none - harmless)
            self.add(''.join(g))
            random.setstate(st)
            self._cover_n += 1
            if role == "woodland":
                # ...and the parcel is a KEEP-OUT placers actually honor (the Sawada merged-roll
                # review's placer-side ask): nothing packs after the woodland today, but a future
                # placer reading crown records rather than the commons poly would otherwise seat
                # a structure under this canopy with nothing firing. Center-tested by _fits like
                # every block poly.
                self.block_polys.append([(float(px0), float(py0)) for px0, py0 in poly])
            self.M["commons"].append(
                {
                    "x": round((x0 + x1) / 2, 1),
                    "y": round((y0 + y1) / 2, 1),
                    "w": round(x1 - x0, 1),
                    "h": round(y1 - y0, 1),
                    "rot": 0,
                    "role": role,
                    "seq": self._cover_n,
                    **({"crowns": _wd_crowns} if role == "woodland" else {}),
                    "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
                }
            )

    def marsh(self: Settlement, poly: Any, role: str = "toe", avoid: Any = ()) -> None:  # type: ignore[misc]
        """REED MARSH / WET MEADOW - wet reed ground drawn WET and SPARSE, FEATHERED to nothing at the margin like
        the commons (no hard fill edge): a faint blue-green wet tint (soft translucent patches), reed / sedge tufts,
        and a few standing-water glints - a distinctly WET palette, unlike the dry tan scrub commons. Points falling
        IN a paddy or ON the open pond water are skipped, so a generous region ABUTS the field's low edge (the polder
        embankment) or the pond's shore and only fills the wet ground beyond. `role`: 'toe' (default) = the LOW,
        undrained valley toe below the managed paddy, where wet-rice cultivation stops (wet rice is reclaimed FROM
        marsh - polders diked out into marsh/lake; where reclamation stops it stays reed wetland; `marsh_on_low_ground`
        checks this sits downhill); 'pond_fringe' = the reedy shallow MARGIN of a pond (a water-edge fringe, exempt
        from the low-ground rule); 'defense' = an ENGINEERED defensive wet belt maintained outside a fortified
        perimeter (Song Hebei frontier marsh belt, numajiro "marsh castles", the flooded-paddy glacis) - it hugs
        the wall/moat wherever the circuit runs, so it is exempt from the low-ground rule and from
        `roads_clear_of_marsh` (an approach road through the belt is a CAUSEWAY - the corridor skip keeps its
        tread bare - and few, constricted approaches are the belt's military purpose); `defense_marsh_girds_the_walls`
        owns its placement instead; 'waterside' = the un-reclaimed wet WILD outside a polder's perimeter dike on its
        WATERWARD flanks (the fluctuating lake/creek/marsh the dike holds back - exempt from the low-ground rule
        because a polder floor sits BELOW the outside water level, so the wet fringe surrounds it regardless of the
        fall direction; `polder_waterward_flanks_wet` owns its placement, driven by `meta.waterward`). WHY:
        settlements.md 'Marsh' + 'Defensive marshland' + 'Polder siting Q&A'. Recorded M['marshes']."""
        if role not in ("toe", "pond_fringe", "defense", "waterside"):
            raise ValueError(f"unknown marsh role {role!r}; expected 'toe', 'pond_fringe', 'defense', or 'waterside'")
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bs = self.bscale
        area = (x1 - x0) * (y1 - y0)
        st = random.getstate()
        random.seed(int(abs(x0) * 5 + abs(y0) * 7 + round(x1 - x0)))
        feather = 46 * bs
        pond = self.M.get("pond")
        halo_rects, halo_circles = self._urban_keepouts((x0, y0, x1, y1))  # the urban-clearance halo (see _urban_keepouts): reeds no more belong in a dooryard than scrub does
        corridors = self._corridor_buffers(3 * bs)  # every trodden tread (lane/street/road), not just lanes
        # PRE-BOX every static keep-out ONCE (see boxed_hit) - the field boxes carry the SAME 10px
        # pad as the edge test below, so the prefilter can never reject a point that test wanted
        fld_b, blk_b = boxed_grid(boxed_polys(self.field_polys, 10.0)), boxed_grid(boxed_polys(self.block_polys))
        clr_b, avd_b, cor_b = boxed_grid(boxed_polys(self.clearings)), boxed_grid(boxed_polys(avoid)), boxed_grid(boxed_segs(corridors))
        wat_b = boxed_grid(boxed_segs(self._watercourse_segs()))  # drawn water (streams/channels/comb laterals), pre-boxed once - see _watercourse_segs

        def _sparse(
            px: float, py: float, drop: float
        ) -> bool:  # skip a point outside the poly, IN a paddy / ON the pond / on a corridor/building / in the urban halo / in a keep-out, or (probabilistically) near the edge
            if (
                not point_in_poly(px, py, poly)
                or boxed_hit(px, py, fld_b.near(px, py), 10.0)
                or boxed_seg_hit(px, py, cor_b.near(px, py))  # a causeway/path/road through the marsh stays bare, not reeded over
                or self._on_watercourse(px, py, near=wat_b.near)  # ... and OFF a stream/channel bed (reeds fringe water, they do not float on it)
                or any(x0r <= px <= x1r and y0r <= py <= y1r for x0r, y0r, x1r, y1r in halo_rects)  # ... and OUT of the urban-clearance halo (the swept/trodden ground around every structure)
                or any((px - hx) ** 2 + (py - hy) ** 2 <= hr * hr for hx, hy, hr in halo_circles)  # ... and clear of every wellhead's trodden apron
                or boxed_hit(px, py, blk_b.near(px, py))  # ... and OFF any building/shrine/torii footprint
                or boxed_hit(px, py, clr_b.near(px, py))  # ... and off the swept sacred/funerary verge
                or boxed_hit(px, py, avd_b.near(px, py))
            ):  # ... and OUT of any keep-out
                return True
            if pond and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 < 1.0:
                return True  # reeds fringe the shore, they do not float on open water
            ed = edge_dist(px, py, poly)
            return ed < feather and random.random() > (ed / feather) ** drop

        g: list[str] = []
        blades: list[str] = []  # SVG-size lever 2: bucket the constant-styled reed blades (see the note in `commons`)
        for _ in range(int(area / (360 * bs * bs))):  # faint WET TINT: soft translucent blue-green patches (feathered, no hard edge)
            gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
            if _sparse(gx, gy, 0.9):
                continue
            g.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="{random.uniform(15, 28) * bs:.1f}" fill="#9FBBAE" fill-opacity="0.14"/>')
        for _ in range(int(area / (150 * bs * bs))):  # SPARSE reed / sedge tufts + the odd standing-water glint (thin, not a solid reedbed)
            gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
            if _sparse(gx, gy, 0.7):
                continue
            if random.random() < 0.12:  # a standing-water glint
                g.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{random.uniform(2.6, 4.6) * bs:.1f}" ry="{random.uniform(1.2, 2.0) * bs:.1f}" fill="#C2D6CE" fill-opacity="0.85"/>')
            else:  # a reed tuft: a few fine near-VERTICAL blades, taller than dry grass
                for _ in range(4):
                    a, bl = random.uniform(-0.2, 0.2), random.uniform(4.0, 7.0) * bs
                    blades.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx + math.sin(a) * bl:.1f}" y2="{gy - math.cos(a) * bl:.1f}"/>')
        self.add(f'<g stroke="#6E9377" stroke-width="0.8">{"".join(blades)}</g>')  # bucketed blades (empty group when none - harmless)
        self.add(''.join(g))
        random.setstate(st)
        self._cover_n += 1
        self.M["marshes"].append(
            {
                "x": round((x0 + x1) / 2, 1),
                "y": round((y0 + y1) / 2, 1),
                "w": round(x1 - x0, 1),
                "h": round(y1 - y0, 1),
                "rot": 0,
                "role": role,
                "seq": self._cover_n,
                "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
            }
        )
        if role != "pond_fringe":  # the wet valley TOE (and the defensive belt) is UNBUILDABLE: register it as a no-build keep-out
            self.block_polys.append([(round(px, 1), round(py, 1)) for px, py in poly])  # so nothing is placed/dug on a bog (a thin pond-fringe shore ring is exempt)

    def trim_off_marsh(self: Settlement, pts: Any, margin: float = 6.0) -> Any:  # type: ignore[misc]
        """Shorten a way so neither END stands on drawn marshland (GM 2026-08-12).

        A path does not run into a reed bed: it stops on the dry side of it. Only the ENDS are
        walked back, because a way whose MIDDLE crosses wet ground has a routing problem that
        trimming cannot fix - that one has to be re-routed, and `roads_clear_of_marsh` says so.
        Marsh drawn so far is what is checked, so this only helps a way laid AFTER its water; the
        `defense` belt is exempt for the same reason it is exempt from the check (its approach IS a
        causeway, and few constricted approaches are the point of it)."""
        wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in self.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
        if not wet or len(pts) < 2:  # a caller may hand over an already-clipped stub; there is nothing to walk back
            return pts
        out = [(float(q[0]), float(q[1])) for q in pts]

        def soaked(q: Pt) -> bool:
            return any(point_in_poly(q[0], q[1], r) or min(seg_dist(q[0], q[1], r[k], r[(k + 1) % len(r)]) for k in range(len(r))) < margin for r in wet)

        # A skeleton arm is a TWO-point polyline, so the walk must be able to shorten the last leg
        # itself rather than only drop vertices - guarding on `len(out) > 2` trimmed nothing at all
        # on the very map this was written for.
        for _ in range(2):  # once from each end
            for _step in range(60):
                if not soaked(out[-1]):
                    break
                a, b = out[-2], out[-1]
                d = math.hypot(b[0] - a[0], b[1] - a[1])
                if d <= 30.0:  # this whole leg is wet: drop it, unless dropping it would leave no way at all
                    if len(out) > 2:
                        out.pop()
                        continue
                    break
                out[-1] = (b[0] - (b[0] - a[0]) / d * 24.0, b[1] - (b[1] - a[1]) / d * 24.0)
            out.reverse()
        return out

    def toe_band(self: Settlement, down_deg: Any = None, pad: float = 90.0) -> list[Pt]:  # type: ignore[misc]
        """The reed-marsh TOE: the contour band below the crop's lowest point, in canvas coordinates.

        FACTORED OUT so it can be asked for BEFORE it is drawn (2026-08-12). `hinterland()` lays the
        marsh late, after the structures, but a WAY has to be routed early - and the GM's rule is
        that a path does not pass through marshland, so the router has to know where the wet ground
        will be while it still has a choice. Deriving it in two places is the trap this skill's notes
        call "placement and its check must read the SAME source", so there is one derivation and both
        callers use it.

        It is a CONTOUR band, not a bbox: wet ground is defined by HEIGHT, so the inner edge is
        perpendicular to the `down_deg` vector like every other height-resolved feature here. An
        axis-aligned rectangle is only an honest contour at a 0/90/180/270 fall, and at a diagonal it
        slices across the slope - which is the bug this shape was given to fix."""
        if down_deg is None:
            down_deg = self.M.get("meta", {}).get("down_deg", 90)
        polys = self.field_polys
        if not polys:
            return []
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        ux, uy = -dy, dx  # cross-slope unit vector (the contour direction)
        cult = [p for poly in polys for p in poly] + [p for dp in self.M.get("dry_plots", []) for p in dp["poly"]]
        v_in = max(p[0] * dx + p[1] * dy for p in cult) - pad  # inner edge: `pad` ABOVE the crop's lowest point, so the reeds still tuck under the crop
        bleed = 120.0
        corners = [(-bleed, -bleed), (self.W + bleed, -bleed), (self.W + bleed, self.H + bleed), (-bleed, self.H + bleed)]
        v_out = max(c[0] * dx + c[1] * dy for c in corners)  # far enough downhill to leave the canvas
        # THE BAND IS AS WIDE AS THE GROUND THE FAN WATERS, not as wide as the canvas (GM 2026-08-12;
        # researched, see research/water.md 'The wet toe is as wide as the fan, not as wide as the
        # valley'). The cross-slope extent used to come from the CANVAS CORNERS, which drew the
        # valley wet from edge to edge - so a map falling toward its own frame had no dry exit
        # anywhere and every connector had to turn away over the settlement's back. That width was
        # never a rule; it arrived with the 2026-07 fix that made the toe a contour band so it would
        # rotate with the fall, and the rotation was the point.
        #
        # Real wet toes are FEATURE-bounded. On an alluvial fan the water that sinks in the dry
        # mid-fan re-emerges in a spring line at the fan's toe (扇端の湧水帯), and that line follows
        # the fan's own geometry - it is where the permeable fan gravels meet the impermeable floor
        # beneath - not the width of the valley it sits in. Our comb fans ARE that landform. The
        # `pad` shoulder each side is the seepage spreading a little past the watered ground.
        us = [p[0] * ux + p[1] * uy for p in cult]
        u_lo, u_hi = min(us) - pad, max(us) + pad
        cu = [c[0] * ux + c[1] * uy for c in corners]
        u0, u1 = max(min(cu), u_lo), min(max(cu), u_hi)
        return [(u * ux + v * dx, u * uy + v * dy) for u, v in ((u0, v_in), (u1, v_in), (u1, v_out), (u0, v_out))]

    def hinterland(  # type: ignore[misc]
        self: Settlement,
        down_deg: Any = None,
        *,
        marsh: bool = True,
        commons: bool = True,
        interior_fill: bool = True,
        pad: float = 90,
        marsh_role: str = "toe",
        scrub_role: str = "grazing",
        skip_sides: Any = (),
    ) -> None:
        """Lay out a settlement's non-arable HINTERLAND: a reed MARSH at the downhill TOE (below the paddy's
        drainage line, where wet-rice reclamation stops and the valley floor stays reed wetland) and the
        cut-over SCRUB commons (coarse grass + a few scraggly pines) filling the surrounding non-arable margins.
        CHINA-FIRST: the south-China rice hills were stripped for fuel/timber over ~1,000 years, so the DOMINANT
        cover past the settlement is denuded scrub/rough grazing, NOT forest - the protected fengshui grove is
        the green exception, and the managed WOODLAND (coppice / bamboo / tung / tea-oil 'economic forest') is a
        FEW discrete PATCHES the gen adds by hand on the higher / farther ground (`s.commons([...],
        role='woodland')`), set back from the sun-needing crops by the scrub between. So hinterland lays the
        scrub + marsh; the woodland patches are per-map. The scrub bands are frame-margin strips OUTSIDE the
        CULTIVATED bbox (paddy + dry hatake), so each recorded centroid clears the paddy (`commons_clear_of_
        paddies` is a centroid test). All scatters skip fields/pond/lanes/buildings AND a **hamlet keep-out**
        (the cluster bbox, so no cover creeps among the houses), and NONE is a crop anchor (`_CROP_HARD`), so
        they BLEED off the frame and the crop stays tight. Call AFTER fields + cluster + pond + dry fields,
        BEFORE crop_to_content. `down_deg` (defaults to meta's) picks which frame side the scrub ring OMITS
        (the toe side) AND orients the marsh itself: the toe is a CONTOUR BAND perpendicular to the fall, so it
        rotates with the map like every other feature (see the comment at the marsh block); the scrub ring is
        radial. A comb-FAN field leaves the opposite bbox corner open -> the gen fills it (scrub +
        woodland patches). See settlements.md 'Hinterland (water-flow-keyed)'."""
        if down_deg is None:
            down_deg = self.M.get("meta", {}).get("down_deg", 90)
        polys = self.field_polys
        if not polys:
            return
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        for dp in self.M.get("dry_plots", []):  # the CULTIVATED extent includes the dry hatake plots
            xs += [p[0] for p in dp["poly"]]
            ys += [p[1] for p in dp["poly"]]
        fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
        W, H = self.W, self.H
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # SETTLEMENT KEEP-OUT, so cover never scatters among the dwellings. Its SHAPE depends on the form:
        avoid: list[Any] = []
        hs = self.M.get("houses", [])
        m = 44
        if hs and self.M.get("meta", {}).get("nucleated", True):
            # NUCLEATED: the houses are one tight blob, so the bbox of their positions IS the built footprint.
            hxs, hys = [h["x"] for h in hs], [h["y"] for h in hs]
            avoid.append([(min(hxs) - m, min(hys) - m), (max(hxs) + m, min(hys) - m), (max(hxs) + m, max(hys) + m), (min(hxs) - m, max(hys) + m)])
        elif hs:
            # DISPERSED: the farmsteads RING the settlement, so a bbox of their positions is not their footprint
            # - it is the WHOLE MAP, and using it forbids ground cover everywhere inside the ring. That is what
            # left Akagahara's fan void as bare clay (GM: "a ton of empty space between the ditch and the
            # marsh"): the void fell inside this blanket, so neither the scrub ring nor anything else could
            # clothe it. Keep out each HOMESTEAD individually instead - house plus its bundle (yard, garden,
            # grove) - so the open ground BETWEEN the strewn farms is free to carry rough grazing, as it should.
            for key in ("houses", "gardens", "threshing_yards", "groves"):
                for r in self.M.get(key, []):
                    hw, hh = r.get("w", 40) / 2 + m, r.get("h", 30) / 2 + m
                    avoid.append([(r["x"] - hw, r["y"] - hh), (r["x"] + hw, r["y"] - hh), (r["x"] + hw, r["y"] + hh), (r["x"] - hw, r["y"] + hh)])
        # which frame side is the downhill TOE (marsh) - the other three carry the scrub commons
        toe_side = ("bottom" if dy >= 0 else "top") if abs(dy) >= abs(dx) else ("right" if dx >= 0 else "left")

        BLEED = 120  # a band reaches the canvas edge + this bleed, NOT `outer` beyond it
        # (clamping the OUTER extent to the canvas avoids scattering a huge off-canvas apron of scrub that only
        #  bloats the SVG node count - the frame clips it anyway; the on-canvas cover is unchanged)

        def ring(inner: float, outer: float) -> list[Any]:
            """The four picture-frame side-strips between the cultivated bbox grown by `inner` and by `outer`
            (outer clamped to the canvas + bleed), MINUS the toe side (marsh) and any `skip_sides` (e.g. a forest
            flank). Each strip lies outside the bbox -> centroid clears the paddy."""
            ox0, oy0 = max(-BLEED, fx0 - outer), max(-BLEED, fy0 - outer)
            ox1, oy1 = min(W + BLEED, fx1 + outer), min(H + BLEED, fy1 + outer)
            ix0, iy0, ix1, iy1 = fx0 - inner, fy0 - inner, fx1 + inner, fy1 + inner
            sides = {
                "top": [(ox0, oy0), (ox1, oy0), (ox1, iy0), (ox0, iy0)],
                "bottom": [(ox0, iy1), (ox1, iy1), (ox1, oy1), (ox0, oy1)],
                "left": [(ox0, iy0), (ix0, iy0), (ix0, iy1), (ox0, iy1)],
                "right": [(ix1, iy0), (ox1, iy0), (ox1, iy1), (ix1, iy1)],
            }
            return [v for k, v in sides.items() if k != toe_side and k not in skip_sides]

        def toe_strip(inner: float, outer: float) -> list[Any]:
            """The one strip `ring` leaves out - the toe side - for the scrub that flanks the reeds."""
            ox0, oy0 = max(-BLEED, fx0 - outer), max(-BLEED, fy0 - outer)
            ox1, oy1 = min(W + BLEED, fx1 + outer), min(H + BLEED, fy1 + outer)
            ix0, iy0, ix1, iy1 = fx0 - inner, fy0 - inner, fx1 + inner, fy1 + inner
            return {
                "top": [(ox0, oy0), (ox1, oy0), (ox1, iy0), (ox0, iy0)],
                "bottom": [(ox0, iy1), (ox1, iy1), (ox1, oy1), (ox0, oy1)],
                "left": [(ox0, iy0), (ix0, iy0), (ix0, iy1), (ox0, iy1)],
                "right": [(ix1, iy0), (ox1, iy0), (ox1, iy1), (ix1, iy1)],
            }[toe_side]

        # THE TOE SIDE IS NOT ALL MARSH ANY MORE, so the scrub has to finish the job (settlement-review,
        # 2026-08-12). `ring()` drops the whole toe-side strip, which was right while the toe ran edge
        # to edge - the reeds covered every inch below the crop. Now the band is only as wide as the
        # ground the fan waters, so the ground past its lateral ends was covered by NEITHER, and
        # Ikegami shipped a ~267 x 193 ft corner of blank parchment with the connector crossing it
        # (measured 2.2% ink against 23.7% in the scrub band immediately above). Rough grazing is
        # exactly what stands on a dry footslope beside a reed flat, so the toe side gets the same
        # scrub as the other three - handed the marsh as a keep-out, so it stops where the reeds start
        # and the two never overlap. Computed BEFORE the commons pass for that reason.
        toe_poly = self.toe_band(down_deg, pad) if marsh else []
        if commons:
            for p in ring(0, max(W, H)):  # the cut-over SCRUB commons: the DOMINANT denuded-hill cover
                self.commons(p, role=scrub_role, avoid=avoid)  # (managed woodland is added as a FEW patches by the gen)
            if toe_poly and toe_side not in skip_sides:
                self.commons(toe_strip(0, max(W, H)), role=scrub_role, avoid=[*avoid, toe_poly])
            # ...and the INTERIOR. The ring lays strips only OUTSIDE the cultivated bbox, but an irregular field
            # (a comb FAN) does not fill its own bbox: it leaves open VOIDS INSIDE it that nothing else clothes
            # - the strips are outside them and the marsh is a contour band below them - so they render as BARE
            # ground, the only uncovered land on the map. That is what read as "empty space" on Akagahara. This
            # patch covers the cultivated bbox; since the scatter already skips every field, lane, watercourse,
            # building and keep-out, it can only land in those voids, clothing them as the rough grazing they
            # are. Ground the crop does not use is still ground, and it is grazed. A SOLID field (a polder grid
            # fills its whole bbox, no voids) has nothing to clothe here, so `interior_fill=False` skips it.
            if interior_fill:
                self.commons([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], role=scrub_role, avoid=avoid)
        if marsh:
            # The toe is a CONTOUR BAND, not an axis-aligned box. Wet ground is defined by HEIGHT, and every
            # other feature here (field, comb, drain, the marsh_on_low_ground check) resolves height by
            # projecting onto the `down_deg` vector - so the marsh's inner edge must be PERPENDICULAR to that
            # vector too. It was previously a bbox-keyed rectangle, which is only an honest contour when the
            # fall is axis-aligned (0/90/180/270); it was the ONE feature that did not rotate with the map.
            # At a diagonal fall that rectangle slices across the slope: on Kikuta/Hoshigaoka (down=45) its
            # inner edge spanned 205/219px of height and its uphill corner reached ABOVE their entire drain,
            # so it swallowed the ditch and painted reeds over ground that is still at rice height. That made
            # the reeds appear to abut the collector on the diagonal maps but not on due-S Akagahara - a pure
            # artifact of the rotation, which read as a real difference between the maps (GM, 2026-07).
            # Since EVERY collector descends ~19-20 degrees across the contours to reach its tameike, there is
            # genuinely ground below the ditch that is still crop-height on every map; the band now shows that
            # consistently instead of hiding it on two maps out of three.
            self.marsh(toe_poly, role=marsh_role, avoid=avoid)  # reed wetland: the low, undrained downhill toe

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
        from waterfields import DRY_CROPS

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

    def _clear_ground(self: Settlement, x: float, y: float, w: float, h: float, extra: float) -> None:  # type: ignore[misc]
        """Reserve a swept verge around a sacred/funerary feature: the w x h footprint grown by `extra`,
        added to `self.clearings` so the loose hinterland scatter (commons scrub, marsh reeds) skips it.
        Scaled by the map grain (bscale), so the cleared collar reads at the same real size on any scale.
        The verge's OUTLINE is ORGANIC (irregular bays carved into the padded rectangle), never the
        rectangle itself (GM 2026-07-23): swept ground is PRODUCED by tending - brooms, feet, the sando's
        traffic - radiating from the feature, and its edge sits wherever the tending peters out into the
        scrub; a surveyed straight line belongs to walls and paddy bunds, never to clearage (settlements.md
        'Swept ground around sacred + funerary features'). The bays are INWARD-ONLY, so the blob always
        stays INSIDE the old padded rect: a collar is a maintenance CLAIM, and making it irregular means
        the sweeping falls short of the surveyed ideal - it never annexes ground (an outward lobe could
        newly overlap a cover that legitimately predates the clearing and flip
        scatter_respects_swept_clearings on a previously-clean map). A bay cuts at most ~55% of the collar,
        so the verge still generously CONTAINS its feature. The blob is seeded from the footprint (the
        saved RNG state keeps the map's stream untouched, so only collar shapes changed pool-wide), and a
        SAME-CENTER duplicate registration (within 4px: the reserve_clearing-then-feature pattern) REUSES
        the first blob verbatim, so guard and late collar can never disagree. Also recorded in
        M['clearings'] with the current cover ordinal, so the checks can verify ORDER: a scatter only
        skips clearings that exist when it runs (scatter_respects_swept_clearings)."""

        def record(poly: Poly) -> None:
            self.M.setdefault("clearings", []).append({"poly": [[round(px, 1), round(py, 1)] for px, py in poly], "seq": self._cover_n})

        for (ocx, ocy), opoly in zip(self._verge_centers, self.clearings, strict=True):
            if abs(ocx - x) <= 4 and abs(ocy - y) <= 4:  # the documented duplicate-registration pattern: reuse the reserved blob
                self.clearings.append(opoly)
                self._verge_centers.append((x, y))
                record(opoly)
                return
        e = extra * self.bscale
        st = random.getstate()
        random.seed(int(abs(x) * 3 + abs(y) * 7 + w * 11 + h * 13 + e))
        x0, y0, x1, y1 = x - w / 2 - e, y - h / 2 - e, x + w / 2 + e, y + h / 2 + e
        amp = 0.55 * e
        edges = [((x0, y0), (x1, y0), (0, 1)), ((x1, y0), (x1, y1), (-1, 0)), ((x1, y1), (x0, y1), (0, -1)), ((x0, y1), (x0, y0), (1, 0))]  # normals point INWARD
        verge = []
        for sa, sb, (nx, ny) in edges:
            for i in range(4):
                t = i / 4
                bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
                off = random.uniform(0.05, 1.0) * amp * (0.35 if i == 0 else 1.0)  # inward-only bay; damped at the corner so the collar keeps its reach there
                jt = random.uniform(-0.18, 0.18) * amp  # tangential jitter (along the edge)
                vx, vy = bx + nx * off + jt * (1 - abs(nx)), by + ny * off + jt * (1 - abs(ny))
                verge.append(
                    (min(max(vx, x0), x1), min(max(vy, y0), y1))
                )  # clamp: corner-sample jitter must not poke past the padded rect (the blob-is-a-subset guarantee is what makes this pool-safe)
        random.setstate(st)
        self.clearings.append(verge)
        self._verge_centers.append((x, y))
        record(verge)

    def reserve_clearing(self: Settlement, x: float, y: float, w: float, h: float, extra: float = 46) -> None:  # type: ignore[misc]
        """Pre-register a swept-ground clearing for a sacred/funerary feature a gen draws LATER (e.g. a
        precinct dropped in after crop_to_content, or placed after the hinterland scatter). The scrub/marsh
        scatter only skips clearings that already exist when it runs, so a late precinct must reserve its
        ground FIRST or the scrub covers it. The later shrine_hall/cemetery registers its own clearing too;
        the overlap is harmless. Pass roughly the footprint you will draw (a slightly generous `extra` is
        fine - over-clearing by a few px reads the same)."""
        self._clear_ground(x, y, w, h, extra)


def surface_water_dist(M: Any, x: float, y: float) -> float:
    """Distance from (x, y) to the nearest SURFACE water - irrigation channel, stream, or moat
    polyline, or the pond's rim - reading exactly the manifest records
    `settlement_dwellings_watered` reads. ONE predicate, shared by that gate check and by
    `hamletgen.place_wells` (known-open ledger 2026-08-16: the well minimax objective counted
    stream-watered houses as needing a well while the check already treated them as watered -
    the objective and the check read two definitions of "needs a well"). Wells are deliberately
    NOT included: the caller asking "does this house need a well" must not have the answer
    pre-empted by the wells it is deciding to dig."""
    d = 1e9
    for ln in [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])] + ([M["moat"]] if M.get("moat") else []):
        for i in range(len(ln) - 1):
            d = min(d, seg_dist(x, y, ln[i], ln[i + 1]))
    pond = M.get("pond")
    if pond:
        d = min(d, abs(math.hypot(x - pond[0], y - pond[1]) - max(pond[2], pond[3])))
    return d
