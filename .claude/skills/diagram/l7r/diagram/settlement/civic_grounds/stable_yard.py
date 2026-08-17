"""The working yard around a gate stables: beaten earth, hitching rails, troughs and muck heaps.

Split from settlement/civic_grounds.py by feature 115 - see settlement/civic_grounds/CLAUDE.md for the index.

`_stable_yard` was a single 335-line method, the largest function in the engine. Feature 115 stage 2
decomposed it into `_YardCtx` (the shared state and the predicates every stage tests against, in
`_yardctx.py`) plus one method per stage. The stage ORDER in `_stable_yard` is the RNG order - read
the RNG contract on `_YardCtx` before moving anything here.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Pt, rail_quad, seg_closest, seg_dist, trough_quad, wellhead_quad
from ._yardctx import _YardCtx

if TYPE_CHECKING:
    from ..core import Settlement


class StableYardMixin:
    def _stable_yard(self: Settlement, sx: float, sy: float, sw: float, sh: float, r: float = 72.0) -> None:  # type: ignore[misc]
        """Draw the working YARD around a gate stables (GM 2026-07-22): the open ground where wagon-trains
        park, oxen are unyoked and tethered, teamsters wait between stages. Research (settlements.md 'Stable
        yard'): a beaten-earth forecourt - NO grass (trampled hard, animals hay-fed not grazed) - and NOT a
        fenced paddock (the least authentic option); its edges are the wall + flanking buildings, its "in
        active use" signal is carts, animals tethered at a hitching rail, and littered ground (the Qingming
        Shanghe Tu gate convention). Drawn as a feathered SCATTER (no solid fill, house style - a filled
        polygon reads as a crisp rhombus) that AUTO-AVOIDS every feature: the stables/inn/flophouse footprints,
        the road + streets, fields, and water - so it fills only the genuinely open pocket. It does NOT avoid
        block_polys (those RESERVED the pocket for exactly this) - only real drawn features. Glyph sizes are
        legibility-tuned for city scale (the wellhead-marker doctrine: a location read, not strict to-scale),
        so they stay legible where a true ~10 ft cart would be ~3 px. Records M['stable_yards'] linked to the
        stables so `stables_have_yards` can gate that no gate stables reverts to blank parchment.

        The stage order below IS the RNG order (feature 115): `_YardCtx(...)` draws nothing,
        `_yard_litter` draws, `seat_init` shuffles, and nothing after it draws at all."""
        st = random.getstate()
        random.seed(int(abs(sx) * 11 + abs(sy) * 7 + round(r)))
        ctx = _YardCtx(self, sx, sy, r)
        self._yard_litter(ctx)
        ctx.seat_init()
        self._yard_road_rail(ctx)
        self._yard_interior_rails(ctx)
        self._yard_watering(ctx)
        self._yard_dung_heaps(ctx)

        yard_rec: dict[str, Any] = {
            "x": round(sx, 1),
            "y": round(sy, 1),
            "r": round(r, 1),
            "of": [round(sx, 1), round(sy, 1)],
            "troughs": ctx.n_troughs if ctx.wp else 0,
            "rails": ctx.rails,  # recorded so stable_yard_furniture_clear_of_roads_walls can test the drawn extents
            "dung_heaps": ctx.heaps,
        }
        if ctx.wp:
            yard_rec["troughs_at"] = [round(ctx.wp[0], 1), round(ctx.wp[1], 1)]  # cluster center - stable_troughs_beside_well anchors on it
            yard_rec["troughs_box"] = ctx.troughs_box  # drawn extent - stable_troughs_clear_of_buildings tests it
        self.M.setdefault("stable_yards", []).append(yard_rec)
        random.setstate(st)

    def _yard_litter(self: Settlement, ctx: _YardCtx) -> None:  # type: ignore[misc]
        # 1. BEATEN-EARTH scuff + STRAW litter: a feathered scatter so the ground reads TRODDEN, not blank
        sx, sy, r = ctx.sx, ctx.sy, ctx.r
        g: list[str] = []
        feather = 22.0
        n = int(math.pi * r * r / 46.0)
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            rr = r * math.sqrt(random.random())
            px, py = sx + rr * math.cos(a), sy + rr * math.sin(a)
            if not ctx.clear(px, py):
                continue
            ed = r - rr  # feather to nothing at the disk rim (no hard edge)
            if ed < feather and random.random() > ed / feather:
                continue
            t = random.random()
            if t < 0.6:  # a scuff speck of beaten earth
                g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{random.uniform(0.7, 1.3):.1f}" fill="#A98C60" fill-opacity="0.7"/>')
            elif t < 0.82:  # a short hoof/cart-rut scuff
                aa, ln = random.uniform(0, math.pi), random.uniform(3, 6)
                g.append(
                    f'<line x1="{px - math.cos(aa) * ln / 2:.1f}" y1="{py - math.sin(aa) * ln / 2:.1f}" x2="{px + math.cos(aa) * ln / 2:.1f}" y2="{py + math.sin(aa) * ln / 2:.1f}" stroke="#9C7E52" stroke-width="0.9" opacity="0.5"/>'
                )
            else:  # spilled straw / fodder litter
                aa, ln = random.uniform(0, math.pi), random.uniform(2.5, 4.5)
                g.append(
                    f'<line x1="{px - math.cos(aa) * ln / 2:.1f}" y1="{py - math.sin(aa) * ln / 2:.1f}" x2="{px + math.cos(aa) * ln / 2:.1f}" y2="{py + math.sin(aa) * ln / 2:.1f}" stroke="#D8C176" stroke-width="0.9" opacity="0.8"/>'
                )
        self.add("".join(g))

    # HITCHING RAILS - the yard's active "edge" (rails + picket lines, NOT a paddock fence;
    # GM 2026-07-22). A wagon-train ties up MANY animals, so the yard shows two or three
    # rails: first a ROAD-PARALLEL rail set back from the nearest road/street (the yard's
    # road-side barrier so nothing strays onto the through-road), then one or two more at
    # clear interior spots. Rails draw as BARE posts - NO animal glyphs (GM 2026-07-25,
    # ending the "dung heaps at the hitching posts" saga: the drawn oxen kept reading as
    # muck piles no matter how the glyph was styled, and the standing doctrine is that
    # these maps render no humans, so they render no animals either; the rail itself plus
    # the beaten-earth litter carry the "in active use" signal).
    def _yard_road_rail(self: Settlement, ctx: _YardCtx) -> None:  # type: ignore[misc]
        # (1) the ROAD-PARALLEL edge rail: nearest road/street segment, rail set back into the yard
        sx, sy, r = ctx.sx, ctx.sy, ctx.r
        best_seg: Any = None
        for pl, hwid in ctx.corridors:
            for i in range(len(pl) - 1):
                cp = seg_closest(sx, sy, pl[i], pl[i + 1])
                sd = math.hypot(cp[0] - sx, cp[1] - sy)
                if best_seg is None or sd < best_seg[0]:
                    best_seg = (sd, cp, pl[i], pl[i + 1], hwid)
        if best_seg is not None and best_seg[0] < r:
            _d, (cpx, cpy), pa, pb, hwid = best_seg
            seglen = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) or 1.0
            tx, ty = (pb[0] - pa[0]) / seglen, (pb[1] - pa[1]) / seglen  # rail runs ALONG the road
            ndist = math.hypot(sx - cpx, sy - cpy) or 1.0
            nx, ny = (sx - cpx) / ndist, (sy - cpy) / ndist  # from road toward the stables (yard side)
            rcx, rcy = cpx + nx * (hwid + 11.0), cpy + ny * (hwid + 11.0)  # set back off the roadbed into the yard
            # probe the rail's FULL extent (tips + post reach = len/2 + 2.4), not just its center -
            # a tip on the roadbed or against the rampart is exactly what the rail exists to prevent
            # (GM 2026-07-24; stable_yard_furniture_clear_of_roads_walls)
            if all(ctx.clear(rcx + tx * e, rcy + ty * e, 8.0) for e in (-11.4, 0.0, 11.4)) and ctx.rail_clear_of_heaps(rcx, rcy, tx, ty) and ctx.glyph_free(rail_quad(ctx.rail_rec(rcx, rcy, tx, ty))):
                ctx.draw_hitch(rcx, rcy, tx, ty, nx, ny)
                ctx.used.append((rcx, rcy))

    def _yard_interior_rails(self: Settlement, ctx: _YardCtx) -> None:  # type: ignore[misc]
        # (2) one or two more rails at clear interior spots (a busy train needs the tie-up room);
        # tips probed like the road rail
        # bounded RETRIES, not two attempts: a candidate refused by the heap/glyph rules must not
        # COST the yard a rail - a wagon-train's tie-up room is the whole "in active use" signal, so
        # keep walking the candidate rings until two rails are seated or the ground is genuinely full
        seated = 0
        for _ in range(8):
            if seated >= 2:
                break
            spot = ctx.take(10.0, 24.0, probes=((-11.4, 0.0), (0.0, 0.0), (11.4, 0.0)))
            if not spot:
                break
            if not ctx.rail_clear_of_heaps(spot[0], spot[1], 1.0, 0.0) or not ctx.glyph_free(rail_quad(ctx.rail_rec(spot[0], spot[1], 1.0, 0.0))):
                continue
            ctx.draw_hitch(spot[0], spot[1], 1.0, 0.0, 0.0, 1.0)
            seated += 1

    def _yard_watering(self: Settlement, ctx: _YardCtx) -> None:  # type: ignore[misc]
        # the WATERING POINT (GM 2026-07-23, researched - settlements.md 'Stable yard' watering
        # paragraph): a working ox drinks ~10 gal/day, a buffalo more, so a wagon-train needs
        # 300-600 gal in one or two big sessions - one small trough is functionally undersized.
        # The historical form is 2-3 long troughs (~8-15 ft, ~2 ft of edge per drinking head)
        # CLUSTERED AT A WELL (animals are led to water in relays, not watered at the rail; the
        # bucket is poured straight from the wellhead, so the troughs sit BESIDE the well - GM
        # 2026-07-23: "otherwise you'd have to carry the water a long way"): the cluster hugs the
        # nearest recorded well within r + 40 - offset from the wellhead by just its visual radius
        # + a trough's half-length (~bucket-pour distance), on the yard side, even when that well
        # stands at or just past the disc rim. A
        # caravan-scale ground (r >= 76) gets 3 troughs, a plain stables yard 2. Drawn ~4.6x2 px
        # each (a ~14 ft trough at city scale, width floored at the 2px cartographic minimum so
        # the water reads). A yard with NO reachable well (or every wellhead flank blocked) digs
        # its OWN courtyard well instead of dropping the cluster at a random spot (GM 2026-07-23,
        # the Nagahara defect - both its yards fell back to 100/241 ft bucket-carries): the
        # caravanserai and the yizhan post-yard watered whole trains from their own courtyard
        # well, so "no well nearby" is a reason to sink one, never to carry water. Gated by
        # stable_troughs_beside_well.
        sx, sy, r = ctx.sx, ctx.sy, ctx.r
        n_troughs = 3 if r >= 76 else 2
        t_h, t_gap, t_len = 2.0, 1.6, 4.6
        t_total = n_troughs * t_h + (n_troughs - 1) * t_gap  # the stacked cluster's full height
        ctx.n_troughs = n_troughs

        def beside(wl: dict[str, Any]) -> Pt | None:
            # a clear cluster spot hugging THIS wellhead, preferring the yard side, then walking
            # around. The offset is DIRECTION-AWARE: the minimal center distance at which the
            # cluster BOX (t_len x t_total) clears the well-house roof square along this ray, + a
            # 1.5 step (~bucket-pour). A fixed `vr + t_len/2` only guarantees HORIZONTAL
            # clearance - the stack is taller than it is wide, so a near-vertical ray clipped the
            # roof corner (GM 2026-07-23, Tango's caravan ground). The box is then CORNER-checked
            # against everything clear() knows (buildings, roads, fields, water, the wall) - a
            # center-only point test let the rects themselves land on footprints - and passed
            # through _glyph_free, which keeps it off every OTHER wellhead roof, off every
            # hitching rail, and off any neighboring yard's cluster. Gated by
            # stable_troughs_clear_of_buildings + wells_troughs_rails_clear_of_each_other.
            vr = wl.get("vr", 4.0)
            w_ang0 = math.atan2(sy - wl["y"], sx - wl["x"])
            for w_da in (0.0, 0.7, -0.7, 1.4, -1.4, 2.1, -2.1, math.pi):
                ux, uy = math.cos(w_ang0 + w_da), math.sin(w_ang0 + w_da)
                w_off = 1.5 + min(
                    (vr + t_len / 2) / abs(ux) if abs(ux) > 1e-9 else math.inf,
                    (vr + t_total / 2) / abs(uy) if abs(uy) > 1e-9 else math.inf,
                )
                wcand = (wl["x"] + ux * w_off, wl["y"] + uy * w_off)
                bx0, by0, bx1, by1 = wcand[0] - t_len / 2, wcand[1] - t_total / 2, wcand[0] + t_len / 2, wcand[1] + t_total / 2
                if not all(ctx.clear(qx, qy, 2.0, rim=False) for qx, qy in ((wcand[0], wcand[1]), (bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1))):
                    continue
                if not ctx.glyph_free(trough_quad([bx0, by0, bx1, by1]), hug=wl):
                    continue
                return wcand
            return None

        wp: Pt | None = None
        for wl in sorted(self.M.get("wells", []) or [], key=lambda o: math.hypot(o["x"] - sx, o["y"] - sy)):
            if not 1 <= math.hypot(wl["x"] - sx, wl["y"] - sy) <= r + 40:
                continue
            wp = beside(wl)
            if wp:
                ctx.used.append(wp)
                break
        if wp is None:  # dig the yard's own well at a clear spot, cluster the troughs beside it
            # the dug well is a PUBLIC wellhead (visual r 8), so probe its head's reach - the well
            # checks test way-distance at half-width + 8, tighter than clear()'s corridor buffer
            spot = ctx.take(12.0, 24.0, probes=((0.0, 0.0), (8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0), (5.7, 5.7), (-5.7, 5.7), (5.7, -5.7), (-5.7, -5.7)))
            # the dug head is a GLYPH like any other: predict its roof square (_well_vr) and refuse
            # a seat that would put it on a rail, on another wellhead, or on a neighbor's troughs
            if spot and self._well_ground_clear(spot[0], spot[1]) and ctx.glyph_free(wellhead_quad({"x": spot[0], "y": spot[1], "vr": self._well_vr()})):
                self.well(spot[0], spot[1])
                wp = beside(self.M["wells"][-1])
                if wp:
                    ctx.used.append(wp)
        if wp:
            wpx, wpy = wp
            for t_i in range(n_troughs):
                t_y = wpy - t_total / 2 + t_i * (t_h + t_gap)
                self.add(f'<rect x="{wpx - t_len / 2:.1f}" y="{t_y:.1f}" width="{t_len:.1f}" height="{t_h:.1f}" rx="0.9" fill="#8FA6B0" stroke="#5A6B72" stroke-width="0.7"/>')
            ctx.troughs_box = [
                round(wp[0] - t_len / 2, 1),
                round(wp[1] - t_total / 2, 1),
                round(wp[0] + t_len / 2, 1),
                round(wp[1] + t_total / 2, 1),
            ]
        ctx.wp = wp

    def _yard_dung_heaps(self: Settlement, ctx: _YardCtx) -> None:  # type: ignore[misc]
        # 1-2 DUNG HEAPS - the little "someone works here" tell; the ellipse's EDGE points are
        # probed too (GM 2026-07-24: a heap must not foul the road tread or the rampart clearance),
        # and a heap keeps WELL clear of every RAIL LINE ON THE MAP (GM 2026-07-25, two rounds:
        # round 1 held 15px, which parks the heap's edge ~8 ft behind the tethered-animal row -
        # the GM still read that as "directly next to the hitching posts", blocking the tie-up
        # flank - and it tested only THIS yard's rails, so a heap could sit 22px from a
        # NEIGHBORING yard's rail with nothing measuring the pair, Nagahara's SE yards being the
        # live case. Round 2: check floor 24px / 72 ft from every rail on the map, placement
        # holds 25 for slack - the heap's edge ends ~38 ft past the animals' rumps, unambiguously
        # out of the working row while still close enough to read as the yard's muck pile)
        all_rails = ctx.rails + [r_ for yd_ in self.M.get("stable_yards", []) or [] for r_ in yd_.get("rails", []) or []]

        def _clear_of_rails(hpx: float, hpy: float) -> bool:
            for rl_ in all_rails:
                rh_ = rl_["len"] / 2
                if seg_dist(hpx, hpy, (rl_["x"] - rl_["tx"] * rh_, rl_["y"] - rl_["ty"] * rh_), (rl_["x"] + rl_["tx"] * rh_, rl_["y"] + rl_["ty"] * rh_)) < 25.0:
                    return False
            return True

        for _ in range(2):
            d = None
            for hcx, hcy in ctx.cand:
                if any((hcx - ux) ** 2 + (hcy - uy) ** 2 < 16 * 16 for ux, uy in ctx.used) or not _clear_of_rails(hcx, hcy):
                    continue
                if all(ctx.clear(hcx + ox_, hcy + oy_, 6.0) for ox_, oy_ in ((0.0, 0.0), (-2.5, 0.0), (2.5, 0.0), (0.0, -1.8), (0.0, 1.8))):
                    d = (hcx, hcy)
                    ctx.used.append(d)
                    break
            if not d:
                break
            dx, dy = d
            ctx.heaps.append({"x": round(dx, 1), "y": round(dy, 1), "rx": 2.5, "ry": 1.8})
            self.add(f'<ellipse cx="{dx:.1f}" cy="{dy:.1f}" rx="2.5" ry="1.8" fill="#6E5A3A" stroke="#4A3A22" stroke-width="0.5" opacity="0.9"/>')
