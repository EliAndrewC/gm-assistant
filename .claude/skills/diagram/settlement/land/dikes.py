"""The polder PERIMETER DIKE, and the village that stands on its crest.

One subject in two halves. `perimeter_dike` draws the earthwork itself - an irregular hand-piled
band whose OUTER face follows the natural water edge in gentle curves (the fish-scale polder form;
the dead-straight right-angled rectangle is a post-1949 industrial shape), planted with a willow row
on the water face and a mulberry row on the inner one, and NOTCHED where a channel crosses it.
`dike_top_houses` puts a single file of farmhouses ON the crest, each on its own widened platform -
the settlement form for an islet polder where the dike's raised earth is the only dry ground there
is.

They are one module because the second reads the `crest` centerline the first records. Change the
dike's geometry and the village on it moves; that coupling is the reason to keep them together and
the reason a session loading one wants the other in front of it.

Split from settlement/land.py by feature 120 - see settlement/land/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Poly, Pt, point_in_poly, smooth_closed, smooth_points

if TYPE_CHECKING:
    from ..core import Settlement


class DikeMixin:
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
