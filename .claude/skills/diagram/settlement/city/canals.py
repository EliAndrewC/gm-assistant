"""Water carried for transport and irrigation rather than defense, and the farmland ring it feeds.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
)
from .._knobs import _below_drain, _poly_centroid, _seg_point, moat_swept_tap

if TYPE_CHECKING:
    from ..core import Settlement


class CanalsMixin:
    def canal(self: Settlement, pts: Any, width: float | None = None, flow: str = "level") -> float:  # type: ignore[misc]
        """A navigable CARGO CANAL - the one way water legitimately enters a walled city (through
        a water gate; the trunk river never does - the Kaifeng lesson). A middle tier on the
        water-width ladder: clearly heavier than an irrigation hairline, clearly lighter than the
        moat/river. Drawn through the shared water block (it merges with the moat/river/dock and
        passes UNDER the rampart at the gate); records M['canals'] + a no-build corridor."""
        if width is None:
            width = self.px(36)  # a poling barge canal ~36 ft
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        rec = {"poly": [[round(x, 1), round(y, 1)] for x, y in pts], "w": width}
        self._flow_record(rec, pts, flow)
        self.M.setdefault("canals", []).append(rec)
        self._water(
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            rec,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{max(2, width * 0.35):.0f}" stroke-linejoin="round" stroke-linecap="round"/>',
        )
        self.corridors.append(([(x, y) for x, y in pts], width / 2 + 16))
        return width

    def towpath(self: Settlement, pts: Any, width: float | None = None) -> None:  # type: ignore[misc]
        """A TOWPATH (the Chinese qiandao) - the beaten haulage path on a navigated river's bank.

        WHY IT EXISTS, AND WHY IT IS NOT A ROAD (GM 2026-08-08; research/cities/capitals.md, "A
        river gets a TOWPATH, not a road"). Water carried bulk far more cheaply than carts, so no
        trunk road shadows a navigable river - the roads leave in the directions the water does
        not serve (capital_no_road_parallels_river holds that line). What the bank carries is the
        path the haulage teams walk when boats must be pulled UPSTREAM: Shaoxing's qiandao dates
        to 815 CE and runs 40+ km, and Marco Polo saw barges hauled along it by teams of horses.
        It exists BECAUSE of the boats - upstream haulage - so it SUPPLEMENTS water transport
        rather than competing with it, and it runs to the wharf it serves and no further.

        Drawn deliberately UNLIKE a road: no roadbed fill, no dashed centerline, one hairline at
        the linework floor. Records M['towpaths'] (a list) and reserves a narrow corridor so the
        packs keep off the bank."""
        if width is None:
            width = max(self.px(8), 2.4)  # an 8 ft beaten path, floored at the linework floor
        dd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="#A9885A" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="round" opacity="0.9"/>')
        self.M.setdefault("towpaths", []).append({"pts": [[round(px_, 1), round(py_, 1)] for px_, py_ in pts], "w": round(width, 2)})
        self.corridors.append(([(px_, py_) for px_, py_ in pts], width / 2 + 8))

    def _ring_upslope(self: Settlement, env: Any, down_deg: float, drain: Any, gaps: Any) -> int:  # type: ignore[misc]
        """Seat farmsteads along the UPSLOPE perimeter of a field, at several standoffs.

        WHY NOT `s.ring` (GM 2026-08-12, migrating the capital): the ring walks the WHOLE envelope
        and projects each seat outward, so on the low edge it throws households into the wet toe
        below the drainage collector - 38 of them on the capital, which is the wettest ground in the
        valley and the one place nobody builds (`dwellings_above_field_drain`). Clipping the polygon
        does not help either: the cut edge still projects outward. So the perimeter is walked here
        and the low side skipped. The provincial cities never meet this because their drains march
        off-view, which is why the plain ring served them for a year.

        The cropland boxes are snapshotted ONCE - rebuilding them per candidate is the
        per-candidate scan of unchanging geometry this skill's CLAUDE.md warns about, and it took a
        gen from 11 seconds to over ten minutes."""
        boxes = [(min(q[0] for q in pp), min(q[1] for q in pp), max(q[0] for q in pp), max(q[1] for q in pp)) for f in self.M.get("fields") or [] for pp in (f.get("plot_polys") or ())] + [
            (min(q[0] for q in pp), min(q[1] for q in pp), max(q[0] for q in pp), max(q[1] for q in pp))
            for d in self.M.get("dry_plots") or []
            for pp in ([d.get("poly") or d.get("outline")] if (d.get("poly") or d.get("outline")) else [])
        ]
        fx, fy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        cx = sum(q[0] for q in env) / len(env)
        cy = sum(q[1] for q in env) / len(env)
        span = max(max(q[0] for q in env) - min(q[0] for q in env), max(q[1] for q in env) - min(q[1] for q in env))
        berth = max(18.0, min(64.0, span * 0.22))
        placed = 0
        for gap in gaps:
            for k in range(len(env)):
                ax, ay = env[k]
                bx, by = env[(k + 1) % len(env)]
                seg = math.hypot(bx - ax, by - ay) or 1.0
                for t in range(max(1, int(seg // 26))):
                    f_ = (t + 0.5) / max(1, int(seg // 26))
                    px_, py_ = ax + (bx - ax) * f_, ay + (by - ay) * f_
                    ox, oy = px_ - cx, py_ - cy
                    ol = math.hypot(ox, oy) or 1.0
                    if (ox / ol) * fx + (oy / ol) * fy > 0.34:
                        continue  # this stretch faces DOWNslope
                    sx, sy = px_ + ox / ol * gap, py_ + oy / ol * gap
                    if drain and _below_drain(sx, sy, drain, fx, fy, berth=berth):
                        continue
                    if any(x0 - 18.0 <= sx <= x1 + 18.0 and y0 - 18.0 <= sy <= y1 + 18.0 for x0, y0, x1, y1 in boxes):
                        continue  # a farmstead stands BESIDE the cropland it works, never on it
                    if self.try_place(sx, sy, "plain"):
                        placed += 1
        return placed

    def farmland_ring(  # type: ignore[misc]
        self: Settlement,
        specs: Any,
        comb: Any,
        topo: Any,
        water: Any,
        city_center: Pt,
        rings: Any = ((26, 15), (20, 40)),
        standoff: float = 30.0,
        source_point: Any = None,
        tap_choices: Any = None,
        drain_points: Any = None,
        open_bound: bool = False,
        outward: Any = None,
        tap_on_segment: bool = False,
        upslope: bool = False,
        upslope_gaps: Any = None,
    ) -> list[Any]:
        """RING A CITY WITH ITS FARMLAND - the belt of comb fields and the households that work them.

        WHY THIS EXISTS AS ONE CALL (GM 2026-08-11/12, after ringing one capital took the better
        part of a working day): "farmland ringing a city is the DEFAULT which should always happen",
        and the pool had settled HOW long before it was written down - Tango farms 3.8% of its sheet
        over 11 fields, Minami 3.0% over 6, Nagahara 2.3% over 7. But all three gens carry their own
        byte-for-byte copy of this loop, so the next city reads as new work when it is not, and the
        numbers those copies already tuned get re-derived by hand one gate failure at a time.

        THE ALGORITHM IS THEIRS, unchanged, because it is the proven one:

          - the tap is the nearest moat/river VERTEX to the hint (not the nearest point on a
            segment - the vertex is what the pool's fields were sited against)
          - the sluice sits `standoff` px OUTWARD from the city center, so a fan falls down the
            slope the moat sits on top of rather than back over the rampart
          - a MOAT tap is then swept downstream (`moat_swept_tap`), turning a square offtake into
            the acute downstream one canal practice calls for. The sluice does not move, so the
            field does not move: only the moat-side end walks upstream
          - the source topology ends where `source_point(net, centroid)` says - the gen's own
            expression, because each one insets and filters differently and a near-miss there moves
            the declared chain and ripples houses off the map
          - the households ring the envelope at each (n, gap) in `rings`

        `comb` builds one fan and returns (net, envelope, centroid) - each gen still owns its copy
        of that carve, which is the other half of this job. `topo` is the gen's topology recorder.

        A field whose ground cannot carry a fan is WITHDRAWN WHOLE: comb_field records the field
        before its water is declared, so a half-built one would sit on the map with no source, no
        drain and no farmhouses - drawn, recorded, and invisible to every rule that reads water."""
        out: list[Any] = []
        for name, hint, down_deg, seed, fall, canal_a, canal_b, offtakes, src in specs:
            wpts = water(src)
            # `tap_choices` narrows which vertices may be tapped before the nearest is taken -
            # Tango only taps the arc UPSTREAM of each hint, because its moat runs southward and a
            # tap below the hint would feed the field against the current.
            cand = list(tap_choices(wpts, hint)) if tap_choices else list(wpts)
            mp: Any = min(cand or wpts, key=lambda q: (q[0] - hint[0]) ** 2 + (q[1] - hint[1]) ** 2)
            if tap_on_segment:
                # the nearest POINT on the polyline, not its nearest VERTEX. A dense moat ring makes
                # the two the same; a river drawn with five vertices does not, and the vertex can be
                # hundreds of px from where the gen meant to tap.
                mp = min(
                    (_seg_point(hint, wpts[k], wpts[k + 1]) for k in range(len(wpts) - 1)),
                    key=lambda q: (q[0] - hint[0]) ** 2 + (q[1] - hint[1]) ** 2,
                )
            # OUTWARD is radial from the city center by default - a fan must fall down the slope
            # the moat sits on top of, not back over the rampart. A city whose water is not a ring
            # around that center (the capital's river runs past one flank) supplies its own bearing.
            ux, uy = outward[name](mp, city_center) if isinstance(outward, dict) else outward(name, mp, city_center) if outward else ((mp[0] - city_center[0]), (mp[1] - city_center[1]))
            ol = math.hypot(ux, uy) or 1.0
            sl = (round(mp[0] + standoff * ux / ol), round(mp[1] + standoff * uy / ol))
            if src == "moat" and self.M.get("moat_flow"):
                mf = self.M["moat_flow"]
                mp = moat_swept_tap(wpts, mf["inlet"], mf["outlet"], sl, mp)
            self.field_channel([mp, sl], "#9CB4C8", 7, 7)
            self.sluice_gate(sl[0], sl[1], rot=math.degrees(math.atan2(sl[1] - mp[1], sl[0] - mp[0])) + 90)
            try:
                net, env, cen = comb(name, sl, down_deg, seed, fall, canal_a, canal_b, offtakes)
            except (ValueError, IndexError) as exc:
                self.M["fields"] = [f for f in self.M.get("fields") or [] if f.get("name") != name]
                self.M["field_ditches"] = [d for d in self.M.get("field_ditches") or [] if d.get("field") != name]
                print(f"{name}: NO FIELD ({exc}) - withdrawn")
                continue
            # the SOURCE point is the gen's own expression, passed in like `comb` and `topo`.
            # Reimplementing it here was wrong twice over: each gen's plot_centroid insets toward
            # the mean of its plot centroids and filters which plots count, and getting that subtly
            # different moved the declared chain AND rippled four houses off the map.
            if source_point is not None:
                pd = source_point(net, cen)
            else:
                cs = [_poly_centroid(pl["poly"]) for pl in net["plots"]]
                pd0 = max(cs, key=lambda q: q[1])
                pd = (round(pd0[0], 1), round(pd0[1], 1))
            topo([(mp[0], mp[1]), sl, pd], {"kind": src}, {"kind": "field", "name": name})
            dr = next((c["pts"] for c in net["channels"] if c["role"] == "drain"), None)
            if dr:
                # the sink chord is the gen's: Tango walks back ~52 px so the declared bend has room
                # to stay obtuse, where its siblings take the drain's last segment
                topo(drain_points(dr) if drain_points else [tuple(dr[-2]), tuple(dr[-1])], {"kind": "drain", "name": name}, {"kind": "offmap"})
            # `open_bound` widens the placement bound around the field while its households are
            # seated. A CITY bound refuses every seat out on the paddy, so a map that sets one (the
            # capital does; the provincial cities do not at this point in their gens) rings NOTHING
            # without it - the fields come out as scenery. Default off keeps the pool byte-identical.
            keep = self.bound
            if upslope and open_bound:
                xs0 = [q[0] for q in env]
                ys0 = [q[1] for q in env]
                self.bound = [[min(xs0) - 260, min(ys0) - 260], [max(xs0) + 260, min(ys0) - 260], [max(xs0) + 260, max(ys0) + 260], [min(xs0) - 260, max(ys0) + 260]]
                # its OWN standoffs, not the ring's: a ring's first band sits inside the dry hem,
                # which is cropland - a farmstead there stands on the field it works
                self._ring_upslope(env, down_deg, dr, upslope_gaps or (30, 52, 74, 96))
                self.bound = keep
                out.append((net, env, cen))
                continue
            if open_bound:
                xs = [q[0] for q in env]
                ys = [q[1] for q in env]
                self.bound = [[min(xs) - 260, min(ys) - 260], [max(xs) + 260, min(ys) - 260], [max(xs) + 260, max(ys) + 260], [min(xs) - 260, max(ys) + 260]]
            for n_, gap in rings:
                self.ring(("poly", env), n_, gap, ["plain"])
            self.bound = keep
            out.append((net, env, cen))
        return out
