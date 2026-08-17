"""The wet defense and every opening through it - water gates, sluices, the inwall drain.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    seg_closest,
    seg_dist,
)

if TYPE_CHECKING:
    from ..core import Settlement


class MoatMixin:
    def moat(  # type: ignore[misc]
        self: Settlement,
        ring: Any,
        gap: float = 42,
        width: float | None = None,
        river: Any = None,
        river_cut: float = 150,
        river_inlet_tilt: float = 10.0,
        river_outlet_tilt: float = 22.0,
    ) -> list[Pt]:
        """A water moat encircling the city wall - the wall RING pushed outward from its centroid
        by `gap`. Records M['moat']. Feed it from off-map with a stream (AS WIDE as the moat, by
        conservation of flow) and tap it for irrigation channels to the outside fields. A no-build
        corridor. Width ~26 px: a provincial-city defensive moat is the heaviest watercourse on the
        map (Himeji-tier ~20-35 m real, ~70x a field ditch); see the settlements.md water-width ladder.
        `river=<pts>` makes it an OPEN moat for a river-bank city: the arc facing the river (moat
        vertices within `river_cut` of the river centerline) is dropped and both open ends extend
        ONTO the river, which closes the water ring itself - inlet upstream, outlet downstream,
        so the current flushes the moat (the historical norm; see settlements.md river-city entry).
        CONVENTION: `river` pts run UPSTREAM-FIRST (source before mouth) - the junction tilts and
        the city_moat_junction_angles check both key on it. The two junction feet are NOT square
        perpendicular tees (that was an rfoot artifact): the INLET (upstream end) shifts upstream
        by `river_inlet_tilt` degrees off square, the OUTLET sweeps downstream by
        `river_outlet_tilt` - see settlements.md "junction angles follow the current" for the
        hydrology (confluences merge at downstream angles; intakes stay near-square for sediment)."""
        if width is None:
            width = self.px(66)  # a provincial-seat moat ~66 ft across (26px at the old 2.55 ft/px grain)
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        mo: list[Pt] = []
        for x, y in ring:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) or 1.0
            mo.append((x + dx / d * gap, y + dy / d * gap))
        if river:

            def rdist(q: Any) -> float:
                return min(seg_dist(q[0], q[1], river[i], river[i + 1]) for i in range(len(river) - 1))

            def rfoot(q: Any) -> Pt:
                k = min(range(len(river) - 1), key=lambda i: seg_dist(q[0], q[1], river[i], river[i + 1]))
                return seg_closest(q[0], q[1], river[k], river[k + 1])

            keep = [q for q in mo if rdist(q) >= river_cut]
            # rotate so the kept arc is CONTIGUOUS (the cut can straddle the list seam)
            n0 = len(mo)
            start = next(i for i in range(n0) if rdist(mo[i]) < river_cut and rdist(mo[(i + 1) % n0]) >= river_cut)
            keep = []
            i = (start + 1) % n0
            while rdist(mo[i]) >= river_cut:
                keep.append(mo[i])
                i = (i + 1) % n0
            # THE JUNCTION FEET TILT WITH THE CURRENT (GM 2026-07-24 hydrology review; see
            # settlements.md river-cities "junction angles follow the current"). The perpendicular
            # rfoot projection gave both arms identical square tees - an algorithm artifact, not a
            # decision. Real waterworks are ASYMMETRIC: the OUTLET sweeps visibly downstream
            # (confluence hydraulics - a square tee drives the exit jet across the river; natural
            # tributaries and drainage returns join pointing downstream) while the INLET stays
            # near-square with only a slight upstream tilt, never smoothly flow-aligned (an offtake
            # aligned with the current drinks the river's bedload and silts the ring - classical
            # headworks kept intakes near-square under a sluice). Shift = arm length * tan(tilt),
            # so each end sits exactly its tilt off square regardless of arm length.
            cum = [0.0]
            for i2 in range(len(river) - 1):
                cum.append(cum[-1] + math.hypot(river[i2 + 1][0] - river[i2][0], river[i2 + 1][1] - river[i2][1]))

            def r_arc(q: Any) -> float:
                k2 = min(range(len(river) - 1), key=lambda i3: seg_dist(q[0], q[1], river[i3], river[i3 + 1]))
                fx, fy = seg_closest(q[0], q[1], river[k2], river[k2 + 1])
                return cum[k2] + math.hypot(fx - river[k2][0], fy - river[k2][1])

            def r_at(sa: float) -> Pt:
                sa = max(0.0, min(cum[-1], sa))
                k3 = next(i4 for i4 in range(len(river) - 1) if cum[i4 + 1] >= sa)
                t = (sa - cum[k3]) / ((cum[k3 + 1] - cum[k3]) or 1.0)
                return (river[k3][0] + (river[k3 + 1][0] - river[k3][0]) * t, river[k3][1] + (river[k3 + 1][1] - river[k3][1]) * t)

            arc_a, arc_b = r_arc(keep[0]), r_arc(keep[-1])
            arm_a = math.hypot(keep[0][0] - rfoot(keep[0])[0], keep[0][1] - rfoot(keep[0])[1])
            arm_b = math.hypot(keep[-1][0] - rfoot(keep[-1])[0], keep[-1][1] - rfoot(keep[-1])[1])
            t_in, t_out = math.tan(math.radians(river_inlet_tilt)), math.tan(math.radians(river_outlet_tilt))
            if arc_a <= arc_b:  # keep[0]'s end is the upstream INLET (river pts run upstream-first)
                end_a, end_b = r_at(arc_a - arm_a * t_in), r_at(arc_b + arm_b * t_out)
                in_pt, out_pt = end_a, end_b
            else:
                end_a, end_b = r_at(arc_a + arm_a * t_out), r_at(arc_b - arm_b * t_in)
                in_pt, out_pt = end_b, end_a
            mo = [end_a] + keep + [end_b]  # both open ends join the river centerline, tilted with the current
            # an OPEN moat knows its own flow: the two junction feet ARE the inlet and outlet, and
            # which is which already fell out of the upstream-first river convention above.
            inlet, outlet = [round(in_pt[0], 1), round(in_pt[1], 1)], [round(out_pt[0], 1), round(out_pt[1], 1)]
        else:
            mo.append(mo[0])
        dd = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in mo)
        self.M["moat"] = [[round(x, 1), round(y, 1)] for x, y in mo]
        self.M["moat_width"] = width
        # WHICH WAY THE MOAT FLUSHES (GM 2026-07-24). A moat is a ring, so it has no upstream end -
        # its water enters at one point and leaves at another, running BOTH ways around the circuit.
        # Recording the two points is what lets a check ask "is this feature downstream?" of a moated
        # city at all; a closed moat's gen passes them (it dug the feeder and the outfall itself).
        if river is not None:
            self.M["moat_flow"] = {"inlet": inlet, "outlet": outlet}
        ml: dict[str, Any] = {}  # records the moat's bed/sheen draw positions
        self.M["moat_layer"] = ml
        self._water(  # routed through the shared water groups so a feeder stream merges into it cleanly
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            ml,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{width * 0.4:.0f}" stroke-linejoin="round" stroke-linecap="round"/>',
        )  # lighter mid-water sheen (NOT a dashed lane line)
        self.corridors.append(([(x, y) for x, y in mo], 28))
        return [(round(x, 1), round(y, 1)) for x, y in mo]

    def water_gate(self: Settlement, x: float, y: float, rot: float = 0.0) -> int:  # type: ignore[misc]
        """A WATER GATE (shuimen) - the masonry arch where a cargo canal passes the rampart (the
        Suzhou Pan Gate pattern: a paired land-and-water city, the water passage under a grated
        arch with a sluice). Drawn in the TOP layer so the canal flows visibly beneath it; the
        wall itself must be drawn with a matching gap (city_wall(water_gates=[...])). Records
        M['water_gates'] and reserves a small no-build block."""
        wc = '#3A352C'
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="-17" y="-9" width="8" height="18" fill="#9C8A66" stroke="{wc}" stroke-width="1.6"/>')  # piers
        g.append(f'<rect x="9" y="-9" width="8" height="18" fill="#9C8A66" stroke="{wc}" stroke-width="1.6"/>')
        g.append(f'<path d="M-14,-9 C-8,-19 8,-19 14,-9" fill="none" stroke="{wc}" stroke-width="3.4"/>')  # the arch
        for gx_ in (-6, -1, 4):
            g.append(f'<line x1="{gx_}" y1="-8" x2="{gx_}" y2="6" stroke="{wc}" stroke-width="1.1" opacity="0.7"/>')  # the grate/sluice bars
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("water_gates", []).append({"x": round(x, 1), "y": round(y, 1), "w": 36, "h": 22, "rot": round(rot, 1), "z": z})
        bm = 16
        self.block_polys.append([(x - 18 - bm, y - 11 - bm), (x + 18 + bm, y - 11 - bm), (x + 18 + bm, y + 11 + bm), (x - 18 - bm, y + 11 + bm)])
        return z

    def sluice_gate(self: Settlement, x: float, y: float, rot: float = 0.0, label: str | None = None, label_xy: Pt | None = None, span: float | None = None) -> int:  # type: ignore[misc]
        """A field-channel SLUICE GATE (the intake/outfall control board the comb doctrine's "sluice-fed
        head-race" always implied but no map drew - GM 2026-07-23, the mouths-are-confluences pass): two
        timber posts flanking the channel and a lifted board between them. Drawn wherever a channel
        CHANGES WATER - a moat/river tap handing off to the comb's own canal (the palette seam sits
        exactly here, and the gate is what makes it read as engineered rather than two strokes crossing)
        or a field drain handing off to its outfall culvert. `rot` degrees turns the board ACROSS the
        channel (pass the channel's heading + 90). ~8px span = a true-scale ~16-24 ft timber intake
        structure with wing posts at the village/city grains. Top layer, above the water. Records
        M['sluice_gates'] for `channel_gates_at_water_junctions`."""
        wc = '#3A352C'
        # `span` stretches the frame ACROSS its channel so the posts stand on the BANKS (GM
        # 2026-08-09: on the capital's 66 ft leats the default field-channel frame floated
        # mid-water, reading as detached - a real frame spans abutment to abutment, and the
        # operator walks the crossbeam). Default None keeps the original field-channel geometry
        # byte-identical for every existing map.
        _sk = 1.0 if span is None else max(1.0, span / 10.8)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-4.6 * _sk:.1f}" y="-1.4" width="{9.2 * _sk:.1f}" height="2.8" fill="#8A7050" stroke="{wc}" stroke-width="1.0"/>')  # the lifted board
        g.append(f'<rect x="{-5.4 * _sk:.1f}" y="-2.0" width="2.0" height="4.0" fill="{wc}"/>')  # posts, ON the banks when span is given
        g.append(f'<rect x="{5.4 * _sk - 2.0:.1f}" y="-2.0" width="2.0" height="4.0" fill="{wc}"/>')
        # THE LIFTING FRAME (GM 2026-08-09, researched): a hi/suimon board was raised by hand -
        # or by windlass on the larger gates - from a timber crossbeam spanning the posts ABOVE
        # the water, the operator standing on the beam walkway or the bank abutment. The beam
        # and its windlass drum are real above-water structure, drawn at the glyph floor (the
        # wells' vr convention): the crossbeam bridges the posts and the drum sits at its center.
        g.append(f'<line x1="{-4.4 * _sk:.1f}" y1="-3.1" x2="{4.4 * _sk:.1f}" y2="-3.1" stroke="{wc}" stroke-width="1.2"/>')  # the crossbeam walkway
        g.append(f'<rect x="-1.1" y="-4.2" width="2.2" height="2.2" fill="#B0905E" stroke="{wc}" stroke-width="0.8"/>')  # the windlass drum
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("sluice_gates", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "z": z})
        if label:
            # a sluice reads as a bare black bar at fit zoom (GM 2026-08-09) - most of a real
            # gate IS in the water, so the word does the explaining, not the drawing
            lx_, ly_ = label_xy if label_xy else (x, y - 13)
            self.label(lx_, ly_, label, 9, italic=True, color="#3A352C")
        return z

    def inwall_drain_outfall(self: Settlement, drain_pts: Any, moat_bias: Pt = (0.0, 0.0), field_name: str = "") -> list[Pt]:  # type: ignore[misc]
        """A walled city's IN-WALL drain handoff (GM 2026-07-23, generalizing Tango's nw1; gated by
        inwall_drains_gated_at_cutoff): the visible runoff ditch CUTS OFF short of the patrol ring
        road and drops through a SLUICE GATE into an implied underground stone culvert beneath road,
        rampart and moat - never draw a ditch running through the city wall (the water gate itself
        is underground and invisible; the control gate at the drop is the one visible piece of the
        plumbing, and is what tells the reader the water drains into engineered works connected to
        the moat). Takes the drain polyline BEFORE it is drawn, TRIMS its moat-side end back to
        half the ring-road width + 10px clear of the ring-road centerline (the glyph's ~5.4px
        half-span + the check's 4px margin, so the gate itself stays off the road bed), places the
        gate ACROSS the ditch at the cut, and records the undrawn drain->moat conduit (cut point ->
        the moat vertex nearest cut+`moat_bias`, with the standard gentle wind channel_winds_gently
        expects) plus its no-build corridor. Returns the trimmed polyline in the caller's original
        orientation - assign it back BEFORE drawing, so the drawn ditch, the field_ditches record,
        and the conduit all share the same cut geometry (placement and check read the same source)."""
        ring = self.M.get("ring_road") or []
        moat = self.M.get("moat") or []
        pts: list[Pt] = [(float(p[0]), float(p[1])) for p in drain_pts]
        rev = False
        if moat:

            def moatd(q: Pt) -> float:
                return min(math.hypot(q[0] - p[0], q[1] - p[1]) for p in moat)

            if moatd(pts[0]) < moatd(pts[-1]):  # normalize: the outfall (moat-side) end LAST
                pts, rev = pts[::-1], True
        cl = self.M.get("ring_road_width", 20) / 2 + 10.0
        if ring:

            def ringd(q: Pt) -> float:
                return min(seg_dist(q[0], q[1], ring[i], ring[i + 1]) for i in range(len(ring) - 1))

            i = len(pts) - 1
            while i > 0 and ringd(pts[i]) < cl:
                i -= 1  # walk back off the road's clearance zone
            if ringd(pts[i]) >= cl and i < len(pts) - 1:
                a, b = pts[i], pts[i + 1]  # the clearance crossing lies on this segment - bisect it
                lo, hi = 0.0, 1.0
                for _ in range(24):
                    m = (lo + hi) / 2
                    lo, hi = (m, hi) if ringd((a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)) >= cl else (lo, m)
                pts = pts[: i + 1] + [(round(a[0] + (b[0] - a[0]) * lo, 1), round(a[1] + (b[1] - a[1]) * lo, 1))]
            # else: the whole drain hugs the road - leave it untrimmed and let the check flag it
        cut = pts[-1]
        prev = pts[-2] if len(pts) > 1 else cut
        self.sluice_gate(cut[0], cut[1], rot=math.degrees(math.atan2(cut[1] - prev[1], cut[0] - prev[0])) + 90)
        if moat:
            tx, ty = cut[0] + moat_bias[0], cut[1] + moat_bias[1]
            mv = min(moat, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)
            ux, uy = mv[0] - cut[0], mv[1] - cut[1]
            ul = math.hypot(ux, uy) or 1.0
            mid = ((cut[0] + mv[0]) / 2 - 12 * uy / ul, (cut[1] + mv[1]) / 2 + 12 * ux / ul)
            poly = [[round(cut[0], 1), round(cut[1], 1)], [round(mid[0], 1), round(mid[1], 1)], [round(mv[0], 1), round(mv[1], 1)]]
            _frm: dict[str, Any] = {"kind": "drain"}
            if field_name:  # NAME the field so the drain->outfall attribution is exact, not by proximity
                _frm["name"] = field_name
            self.M["channels"].append({"poly": poly, "frm": _frm, "to": {"kind": "moat"}, "w": 2.5, "drawn": False})
            self.corridors.append(([(p[0], p[1]) for p in poly], 33))
        return pts[::-1] if rev else pts

    def moat_flow(self: Settlement, inlet: Pt, outlet: Pt) -> None:  # type: ignore[misc]
        """Declare a CLOSED moat's circulation: where its water enters the ring and where it leaves.

        An open (river-cut) moat derives this itself - its two junction feet ARE the inlet and
        outlet. A closed moat cannot: the ring is dug first and its feeder and outfall are drawn
        afterward, so the gen names the two points. Water runs BOTH ways around the circuit from
        inlet to outlet, which is why a moated city has no single "downstream" side and a rule
        about downstream siting has to reason from these two points."""
        self.M["moat_flow"] = {"inlet": [round(inlet[0], 1), round(inlet[1], 1)], "outlet": [round(outlet[0], 1), round(outlet[1], 1)]}
