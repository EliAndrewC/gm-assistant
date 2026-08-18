"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import re
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

from ._geom import (
    WARD_BARRED_KINDS,
    Poly,
    Pt,
    fillet_polyline,
    kido_bar_deg,
    lane_runs,
    lane_through_gate,
    point_in_poly,
    sat_overlap,
    seg_closest,
    seg_dist,
    seg_intersect,
    segments_cross,
    stroke_quads,
    tower_quad,
    wall_runs,
    ward_interior,
    winding,
)
from ._knobs import machi_mouths

if TYPE_CHECKING:
    from .core import Settlement


_FRAY_DEG = 20.0  # below this the two ways are the same track fraying, not a junction (see trim_lane_stubs)


def _angle_between(run: Any, other: Any) -> float:
    """The acute angle in degrees between two segments, 0 = parallel (either direction)."""
    (ax, ay), (bx, by) = run
    (cx, cy), (dx, dy) = other
    u, v = (bx - ax, by - ay), (dx - cx, dy - cy)
    lu, lv = math.hypot(*u), math.hypot(*v)
    if lu < 1e-9 or lv < 1e-9:
        return 90.0
    cos = abs(u[0] * v[0] + u[1] * v[1]) / (lu * lv)
    return math.degrees(math.acos(max(0.0, min(1.0, cos))))


_LANE_MIN_FT = 71.0  # one homestead's frontage: below this a lane can front nobody (see trim_lane_stubs)


def _lane_len(pts: list[Pt]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))


def _pull_back(pts: list[Pt], reaches: Any, step: float = 8.0, keep_frac: float = 0.4, min_len: float = 0.0) -> list[Pt]:
    """Shorten a polyline from its LAST vertex until that end reaches something, or the guard stops it.

    Walks the final segment inward in `step` px, dropping a whole vertex when one is consumed and
    more than two remain. NEVER trims below `keep_frac` of the original length and never below two
    points: a lane whose whole run serves nothing is a siting problem, not something to delete - the
    map still needs the way it drew, and silently removing one would trade a visible stub for an
    invisible missing lane."""
    full = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))
    # `min_len` is the HARD floor a junction sets - see `_junction_floor`. It is a maximum with the
    # proportional guard rather than a replacement for it: a lane may not be trimmed past a way that
    # ties into it, whatever fraction of its length that leaves.
    floor = max(full * keep_frac, min_len)
    out = list(pts)
    best: list[Pt] | None = None  # the SHORTEST end seen that still reaches something
    while len(out) >= 2:
        a, b = out[-2], out[-1]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg <= step:
            if len(out) == 2:
                break
            out.pop()
            continue
        t = (seg - step) / seg
        cand = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        trial = [*out[:-1], cand]
        if sum(math.hypot(q[0] - r[0], q[1] - r[1]) for q, r in zip(trial, trial[1:], strict=False)) < floor:
            break
        out = trial
        # STOP AT THE LAST THING SERVED, not at the predicate's EDGE. Returning the first point that
        # reaches anything leaves the tread ending on the 90 ft radius of a farmhouse centre - i.e.
        # ~60 ft clear of that homestead's own footprint, petering out in grass (both the Kashikawa
        # and Sawada reviews raised it independently). Walking on while it STILL reaches, and keeping
        # the shortest such point, ends the lane at the homestead instead - and where the end also
        # ran alongside a sibling arm, it shortens that parallel run by the same amount.
        if reaches(cand):
            best = list(trial)
    return best if best is not None else out


class WaterWaysMixin:
    def note_focal(self: Settlement, kind: str) -> None:  # type: ignore[misc]
        """Record an optional FOCAL feature (feature 005 catalog) on the manifest so the twin-detector reads
        it as a distinctiveness axis (meta.focal_features). Call it for a focus DRAWN via an existing method -
        a secondary shrine via `shrine_hall(primary=False)`, an ancestral hall, a market clearing - as well as
        from the dedicated focal methods (`crescent_pond`, `mill`). Idempotent per kind."""
        foc = self.M["meta"].setdefault("focal_features", [])
        if kind not in foc:
            foc.append(kind)

    def mill(self: Settlement, x: float, y: float, wheel_side: str = "E", w: float = 30, h: float = 24) -> None:  # type: ignore[misc]
        """A water MILL (水磨 / 水車), a focal feature: a small mill house with an undershot WATERWHEEL on its
        watercourse side, for hulling/grinding. Place it BESIDE a watercourse with fall (a drain outfall or a
        stream), never on still pond water. `wheel_side` (N/E/S/W) is the side the wheel faces the water. Draws
        the house + wheel, records the footprint (M['mills']) + the `mill` focal feature, and reserves the
        footprint as a placement keep-out (call it before `farmsteads()` if the cluster could reach it)."""
        pw, ph = self.px(w), self.px(h)
        dx, dy = {"E": (1.0, 0.0), "W": (-1.0, 0.0), "N": (0.0, -1.0), "S": (0.0, 1.0)}[wheel_side]
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#C9A57A" stroke="#6B4F2A" stroke-width="2" rx="2"/>')
        self.add(f'<line x1="{x - pw / 2:.1f}" y1="{y:.1f}" x2="{x + pw / 2:.1f}" y2="{y:.1f}" stroke="#6B4F2A" stroke-width="1" opacity="0.6"/>')  # ridge line
        wx, wy = x + dx * (pw / 2 + self.px(5)), y + dy * (ph / 2 + self.px(5))  # waterwheel center, on the water side
        wr = self.px(9)
        spokes = "".join(
            f'<line x1="{wx:.1f}" y1="{wy:.1f}" x2="{wx + wr * math.cos(a):.1f}" y2="{wy + wr * math.sin(a):.1f}" stroke="#5A3F1E" stroke-width="1"/>' for a in [i * math.pi / 4 for i in range(8)]
        )
        self.add(f'<circle cx="{wx:.1f}" cy="{wy:.1f}" r="{wr:.1f}" fill="none" stroke="#5A3F1E" stroke-width="1.8"/>{spokes}')
        self.M.setdefault("mills", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("mill")
        self.placed.append((x, y, pw, ph))

    def _focal_block(self: Settlement, x: float, y: float, pw: float, ph: float) -> None:  # type: ignore[misc]
        """Reserve a focal footprint as a placement keep-out (so a later farmstead can never overlap it)."""
        self.placed.append((x, y, pw, ph))
        self.block_polys.append([(x - pw / 2 - 6, y - ph / 2 - 6), (x + pw / 2 + 6, y - ph / 2 - 6), (x + pw / 2 + 6, y + ph / 2 + 6), (x - pw / 2 - 6, y + ph / 2 + 6)])

    def ancestral_hall(self: Settlement, x: float, y: float, w: float = 110, h: float = 74) -> None:  # type: ignore[misc]
        """A lineage ANCESTRAL HALL (祠堂), a focal feature: the grandest civic building of a single-lineage
        village - broader than any house, a double-eave hall on the auspicious axis fronting the pond/water.
        Draws the hall, records M['ancestral_halls'] + the focal feature, reserves the footprint. Grounding
        (research.md D2): the ancestral hall was the ritual + governance center of a Huizhou/Hakka lineage
        village, its single most prominent structure - so a village that HAS one reads unmistakably by it."""
        pw, ph = self.px(w), self.px(h)
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#DDB87A" stroke="#5A3F1E" stroke-width="2.4" rx="2"/>')
        self.add(
            f'<rect x="{x - pw / 2 + self.px(5):.1f}" y="{y - ph / 2 + self.px(5):.1f}" width="{pw - self.px(10):.1f}" height="{ph - self.px(10):.1f}" fill="none" stroke="#6B4F2A" stroke-width="1.2"/>'
        )  # inner eave
        self.add(f'<rect x="{x - self.px(9):.1f}" y="{y + ph / 2 - self.px(4):.1f}" width="{self.px(18):.1f}" height="{self.px(6):.1f}" fill="#5A3F1E"/>')  # entry porch on the water side
        self.M.setdefault("ancestral_halls", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("ancestral_hall")
        self._focal_block(x, y, pw, ph)

    def water_mouth(self: Settlement, x: float, y: float, r: float = 22) -> None:  # type: ignore[misc]
        """A fengshui WATER-MOUTH complex (水口), a focal feature: the guarded outlet where the village stream
        leaves, marked by a small hexagonal pavilion (and, per the gen, a screening grove) to 'lock in' the qi
        of the departing water. Draws the pavilion, records M['water_mouths'] + the focal feature. Grounding:
        the shuikou was a standard focal ensemble of south-China lineage villages, sited at the stream exit."""
        pr = self.px(r)
        pts = " ".join(f"{x + pr * math.cos(a):.1f},{y + pr * math.sin(a):.1f}" for a in [math.pi / 6 + i * math.pi / 3 for i in range(6)])
        self.add(f'<polygon points="{pts}" fill="#C9876C" stroke="#6B2A18" stroke-width="2" stroke-linejoin="round"/>')
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr * 0.42:.1f}" fill="none" stroke="#6B2A18" stroke-width="1.2"/>')
        self.M.setdefault("water_mouths", []).append({"x": round(x, 1), "y": round(y, 1), "w": pr * 2, "h": pr * 2, "rot": 0})
        self.note_focal("water_mouth")
        self._focal_block(x, y, pr * 2, pr * 2)

    def market(self: Settlement, x: float, y: float, w: float = 120, h: float = 84) -> None:  # type: ignore[misc]
        """A village MARKET clearing (墟/市), a focal feature: an open packed-earth space with a few stalls
        where a periodic market gathers - a widening in the lane fabric, not a building. Draws the open court +
        a row of stall marks, records M['markets'] + the focal feature. Grounding: a market node is exactly
        where a `cross` lane skeleton reads as a market village rather than a plain farming one."""
        pw, ph = self.px(w), self.px(h)
        cid = self._cid("mkt")
        self.add(f'<clipPath id="{cid}"><rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="3"/></clipPath>')
        self.add(f'<rect x="{x - pw / 2:.1f}" y="{y - ph / 2:.1f}" width="{pw:.1f}" height="{ph:.1f}" fill="#D8C7A0" stroke="#9C7A40" stroke-width="1.6" stroke-dasharray="5 4" rx="3"/>')
        stalls = "".join(
            f'<rect x="{x - pw / 2 + self.px(10) + i * self.px(22):.1f}" y="{y - self.px(6):.1f}" width="{self.px(14):.1f}" height="{self.px(12):.1f}" fill="#C9A57A" stroke="#6B4F2A" stroke-width="1"/>'
            for i in range(max(1, int(w / 34)))
        )
        self.add(f'<g clip-path="url(#{cid})">{stalls}</g>')
        self.M.setdefault("markets", []).append({"x": round(x, 1), "y": round(y, 1), "w": pw, "h": ph, "rot": 0})
        self.note_focal("market")
        self._focal_block(x, y, pw, ph)

    def secondary_shrine(self: Settlement, x: float, y: float, w_ft: float = 42, h_ft: float = 30) -> None:  # type: ignore[misc]
        """A SECONDARY tutelary/roadside shrine, a focal feature: a small second shrine besides the village's
        main one (a Benten by the pond, an Inari at a field corner). Records as a 'shrine' kind (so
        religious_matches_scale still sees only shrines) + the focal feature. Grounding: a village often kept a
        minor shrine in addition to its tutelary one; its PRESENCE + placement is a distinctiveness axis.
        TRUE SCALE: dimensions are real feet (a minor wayside hall ~42x30 ft, smaller than the tutelary)."""
        self.shrine(x, y, w_ft, h_ft, kind="shrine")
        self.note_focal("secondary_shrine")

    def _flow_record(self: Settlement, rec: dict[str, Any], pts: Any, flow: str) -> None:  # type: ignore[misc]
        """Tag one watercourse record with its flow direction and the derived downstream bearing.

        `flow_deg` is the bearing of the NET upstream->downstream vector, in the map's angle
        convention (the same one `down_deg` uses: 0 = east, 90 = south, y-down screen space). The
        net vector, not the last segment, because a winding stream's local heading says nothing
        about where its water is going - and every rule that cares ("is the tannery downstream of
        the town?") is about the net journey."""
        if flow not in ("forward", "reverse", "level"):
            raise ValueError(f"watercourse flow must be 'forward', 'reverse' or 'level', got {flow!r}")
        if flow == "level":
            # A NAVIGABLE cut (the cargo canal) is not a drainage course and gets NO bearing. It is
            # dug at the level of the water it joins - which is exactly what lets barges pole both
            # ways along it - so its gradient is nil, the water gate's sluice holds it at river
            # level, and a dead-end dock basin has no through-flow at all. Claiming a downstream
            # direction for it would be a fiction, so it declares "level" instead and the
            # drainage-bearing check skips it.
            rec["flow"] = flow
            rec["flow_deg"] = None
            return
        p = [(float(x), float(y)) for x, y in pts]
        ux, uy = (p[0], p[-1]) if flow == "forward" else (p[-1], p[0])
        vx, vy = ux[0] - uy[0], ux[1] - uy[1]
        rec["flow"] = flow
        # upstream -> downstream is (downstream - upstream); we built (upstream - downstream) above
        rec["flow_deg"] = round(math.degrees(math.atan2(-vy, -vx)) % 360, 1)

    def stream(self: Settlement, pts: Any, frm: Any = None, to: Any = None, width: float = 9, flow: str = "forward") -> None:  # type: ignore[misc]
        """A natural watercourse. If frm/to anchors are given (e.g. a forest brook
        feeding a pond), it is recorded and the gate checks it actually connects
        them - just like an irrigation channel. `width` is the water's drawn width
        (a stream FEEDING A MOAT should be as wide as the moat, by conservation of flow).

        FLOW DIRECTION (GM 2026-07-24). Every watercourse declares which way the water runs,
        because "downstream" is a real constraint on siting - tanneries, dyers' rinse water,
        the burakumin quarter, the moat's flushing current - and it was previously carried only
        in gen docstrings, where no check could read it. CANONICAL CONVENTION: `pts` is authored
        UPSTREAM-FIRST, so poly[0] is the source end. This formalizes the convention s.moat's
        `river=` already relied on. `flow="reverse"` marks a polyline stored the other way round
        (reversing point order renders identically, so the tag is for the rare case where the
        drawing code wants the other order). The derived bearing is recorded as `flow_deg`, so
        checks read ONE number rather than re-deriving direction from anchor semantics."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        # always recorded so the gate can check it (anchors optional - only some streams connect things)
        rec = {"poly": [[x, y] for x, y in pts], "frm": frm, "to": to, "w": width}
        self._flow_record(rec, pts, flow)
        self.M["streams"].append(rec)
        bed_t = f'<path d="{{dd}}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'
        # lighter mid-current highlight (NOT a dashed lane line - this is water, not a road)
        sheen_t = f'<path d="{{dd}}" fill="none" stroke="#B6CAD8" stroke-width="{max(2, width * 0.35):.0f}" stroke-linejoin="round" stroke-linecap="round"/>'
        clip = {"pts": [(x, y) for x, y in pts], "bed_t": bed_t, "sheen_t": sheen_t} if self._pond_anchored(frm, to) else None
        self._water(  # opacity comes from the shared bed/sheen groups, so crossings don't stack into a dark seam
            bed_t.format(dd=dd), rec, sheen=sheen_t.format(dd=dd), clip=clip
        )
        self.corridors.append(([(x, y) for x, y in pts], max(30, width / 2 + 20)))  # no-build: keep houses off the stream

    def river(self: Settlement, pts: Any, width: float | None = None, flow: str = "forward") -> float:  # type: ignore[misc]
        """A RIVER - the trunk waterway a river-bank city sits on (most provincial cities do;
        the moat taps it upstream and returns downstream, and the river itself serves as the
        water defense on its flank - Xiangyang/Pingyao/Okayama pattern, see settlements.md).
        Drawn as a wide stream (off-map to off-map) and recorded in M['river'] so the checks
        that compare watercourse weights know this one legitimately outweighs the dug moat."""
        if width is None:
            width = self.px(120)  # a serious provincial river ~120 ft across
        self.stream(pts, frm={"kind": "offmap"}, to={"kind": "offmap"}, width=width, flow=flow)
        self.M["river"] = {"pts": [[x, y] for x, y in pts], "w": width}
        self._flow_record(self.M["river"], pts, flow)  # the trunk river's own record carries it too
        return width

    def channel(self: Settlement, start: Any, end: Any, frm: Any, to: Any, amp: float = 15, width: float = 2.5, pts: Any = None) -> None:  # type: ignore[misc]
        """frm/to are anchor dicts: {'kind':'pond'|'offmap'|'field','name':...}. `width` is the drawn
        bed: a field-level irrigation ditch is the THINNEST line on the map (in reality ~0.3 m, ~1/300
        of the 1-cho paddy it feeds), so it sits at the legibility floor (~2.5 px) - a hairline, clearly
        finer than any natural watercourse. See the water-width ladder in settlements.md historical
        grounding. `pts` (optional): an explicit polyline used verbatim instead of the auto-winding -
        for culverts routed by hand (a drain outfall reaching its stream confluence, a field-to-field
        cascade connector) whose waypoints are load-bearing; drawing through THIS method (not a flat
        field_channel stroke) is what puts the bed in the shared water group at the standard bed hue,
        so the mouth merges into the receiving stream like any confluence (GM, Hirameki 2026-07)."""
        poly = [(p[0], p[1]) for p in pts] if pts else winding(start, end, amp=amp)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
        rec = {"poly": [[x, y] for x, y in poly], "frm": frm, "to": to, "w": width}
        self.M["channels"].append(rec)
        bed_t = f'<path d="{{dd}}" fill="none" stroke="#9CB4C8" stroke-width="{width}"/>'  # a channel is a thin bed, no sheen
        clip = {"pts": [(x, y) for x, y in poly], "bed_t": bed_t, "sheen_t": None} if self._pond_anchored(frm, to) else None
        self._water(bed_t.format(dd=dd), rec, clip=clip)
        # 33 px keeps even a plain farmhouse's FOOTPRINT (half-diagonal ~26) clear of the
        # channel, not just its center - 22 left corners clipping the channel (see
        # no_structure_on_channel). Matches the stream corridor's footprint-aware spacing.
        self.corridors.append((poly, 33))

    def _clip_to_pond(self: Settlement, pts: Any) -> Any:  # type: ignore[misc]
        """Snap a channel's leading endpoint ONTO the pond rim - trim a run that lies inside the pond, or
        extend one that sits just outside (the sluice foot) - so its bed straddles the rim and COVERS it at
        the mouth: a clean JOIN, without the channel drawing a colored line across the open water. No-op
        when there is no pond. (The rim renders in the water EDGE layer, below every bed, so the covering
        works.)"""
        p = self.M.get("pond")
        if not p:
            return pts
        ex, ey, erx, ery = p

        def rad(q: Pt) -> float:
            return cast(float, ((q[0] - ex) / erx) ** 2 + ((q[1] - ey) / ery) ** 2)  # <1 inside, 1 on the rim, >1 outside

        def rim(inside_pt: Pt, outside_pt: Pt) -> Pt:  # the rad==1 crossing on the segment
            lo, hi = 0.0, 1.0
            for _ in range(24):
                m = (lo + hi) / 2
                q = (inside_pt[0] + (outside_pt[0] - inside_pt[0]) * m, inside_pt[1] + (outside_pt[1] - inside_pt[1]) * m)
                lo, hi = (m, hi) if rad(q) < 1.0 else (lo, m)
            return (inside_pt[0] + (outside_pt[0] - inside_pt[0]) * hi, inside_pt[1] + (outside_pt[1] - inside_pt[1]) * hi)

        def snap_front(seq: Any) -> list[Any]:  # snap a leading endpoint that connects to the pond onto the rim
            out = list(seq)
            if rad(out[0]) < 1.0:  # inside: drop the run inside the pond, start AT the rim
                i = 0
                while i + 1 < len(out) and rad(out[i + 1]) < 1.0:
                    i += 1
                if i + 1 < len(out):
                    out = [rim(out[i], out[i + 1])] + out[i + 1 :]
            elif rad(out[0]) < 1.35:  # just outside (the sluice foot): prepend the rim point
                out = [rim((ex, ey), out[0])] + out
            return out

        out = snap_front(pts)  # a comb channel meets the pond at its head (leading end)...
        out = snap_front(out[::-1])[::-1]  # ...a feeder brook meets it at its mouth (trailing end): clip both
        return out

    def _clip_to_moat(self: Settlement, pts: Any, capr: float = 0.0) -> Any:  # type: ignore[misc]
        """Snap a channel endpoint that meets the MOAT onto the moat bed's edge - trim any run that
        lies within the bed, restarting the channel at the bed's rim with a ~3px inset so its mouth
        covers the rim stroke - the same clean JOIN `_clip_to_pond` gives a pond-fed channel, so a
        moat tap (or a drain emptying into the moat) never draws its bed as a colored line across
        the open moat water. `capr` is the stroke's CAP RADIUS (half the drawn width): the round
        linecap inks that far PAST the endpoint, so the inset must back off by it - without this a
        7px tap's mouth plunged to ~4px of the moat centerline and read as a foreign line crossing
        half the band (GM 2026-07-23, Tango). No-op when there is no moat."""
        moat = self.M.get("moat")
        if not moat or len(pts) < 2:
            return pts
        hw = self.M.get("moat_width", 22) / 2

        def foot(q: Pt) -> tuple[Any, Any]:
            best: Any = None
            bd: Any = None
            for i in range(len(moat) - 1):
                ax, ay = moat[i]
                bx, by = moat[i + 1]
                vx, vy = bx - ax, by - ay
                ll = vx * vx + vy * vy or 1.0
                t = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / ll))
                fx, fy = ax + vx * t, ay + vy * t
                d = math.hypot(q[0] - fx, q[1] - fy)
                if bd is None or d < bd:
                    bd, best = d, (fx, fy)
            return best, bd

        def snap_front(seq: Any) -> list[Any]:
            out = list(seq)
            if foot(out[0])[1] >= hw:
                return out  # the end is clear of the bed - nothing to snap
            i = 0  # drop any leading run inside the bed
            while i + 1 < len(out) and foot(out[i + 1])[1] < hw:
                i += 1
            if i + 1 >= len(out):
                return out  # the whole channel lies in the moat - leave it
            f, _d = foot(out[i])
            nxt = out[i + 1]
            ux, uy = nxt[0] - f[0], nxt[1] - f[1]
            ul = math.hypot(ux, uy) or 1.0
            return [(f[0] + ux / ul * (hw - 3 + capr), f[1] + uy / ul * (hw - 3 + capr))] + out[i + 1 :]

        out = snap_front(pts)
        out = snap_front(out[::-1])[::-1]
        return out

    def _clip_to_river(self: Settlement, pts: Any, capr: float = 0.0) -> Any:  # type: ignore[misc]
        """Snap a channel endpoint that meets the RIVER onto the river bed's edge - the same clean
        confluence `_clip_to_moat` gives a moat tap (added 2026-07-23 with the mouths-not-crossings
        rule: Nagahara's fne1 tap started ON the Hayakawa centerline and drew across the half-band).
        No-op when there is no river."""
        rv = self.M.get("river")
        if not rv or not rv.get("pts") or len(pts) < 2:
            return pts
        rp = rv["pts"]
        hw = rv.get("w", 40) / 2

        def foot(q: Pt) -> tuple[Any, Any]:
            best: Any = None
            bd: Any = None
            for i in range(len(rp) - 1):
                ax, ay = rp[i]
                bx, by = rp[i + 1]
                vx, vy = bx - ax, by - ay
                ll = vx * vx + vy * vy or 1.0
                t = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / ll))
                fx, fy = ax + vx * t, ay + vy * t
                d = math.hypot(q[0] - fx, q[1] - fy)
                if bd is None or d < bd:
                    bd, best = d, (fx, fy)
            return best, bd

        def snap_front(seq: Any) -> list[Any]:
            out = list(seq)
            if foot(out[0])[1] >= hw:
                return out
            i = 0
            while i + 1 < len(out) and foot(out[i + 1])[1] < hw:
                i += 1
            if i + 1 >= len(out):
                return out  # pragma: no cover - defensive: a tap never lies wholly in the river
            f, _d = foot(out[i])
            nxt = out[i + 1]
            ux, uy = nxt[0] - f[0], nxt[1] - f[1]
            ul = math.hypot(ux, uy) or 1.0
            return [(f[0] + ux / ul * (hw - 3 + capr), f[1] + uy / ul * (hw - 3 + capr))] + out[i + 1 :]

        out = snap_front(pts)
        out = snap_front(out[::-1])[::-1]
        return out

    def _clip_to_stream(self: Settlement, pts: Any) -> Any:  # type: ignore[misc]
        """Snap a channel endpoint that reaches INTO a stream bed onto the bed's edge (~2px inside
        the bank, so the mouth covers the bank stroke) - the same clean CONFLUENCE `_clip_to_pond`
        and `_clip_to_moat` give: a drain culvert JOINS the receiving stream without drawing its own
        bed as a colored tongue across the current. Trim-only: an end short of the bank is left
        alone (the `channels_join_streams_at_confluence` check requires the RECORDED polyline to
        reach the bed, so the gen extends the record to the centerline and this trims the DRAWING)."""
        streams = self.M.get("streams", [])
        if not streams or len(pts) < 2:
            return pts

        def foot(q: Pt) -> tuple[Any, float, float]:
            best: Any = None
            bd, bhw = 1e9, 4.5
            for st in streams:
                sp = st["poly"]
                hw = st.get("w", 9) / 2
                for i in range(len(sp) - 1):
                    ax, ay = sp[i]
                    bx, by = sp[i + 1]
                    vx, vy = bx - ax, by - ay
                    ll = vx * vx + vy * vy or 1.0
                    t = max(0.0, min(1.0, ((q[0] - ax) * vx + (q[1] - ay) * vy) / ll))
                    fx, fy = ax + vx * t, ay + vy * t
                    d = math.hypot(q[0] - fx, q[1] - fy)
                    if d < bd:
                        bd, best, bhw = d, (fx, fy), hw
            return best, bd, bhw

        def snap_front(seq: Any) -> list[Any]:
            out = list(seq)
            f0, d0, hw0 = foot(out[0])
            if f0 is None or d0 >= hw0 - 2:
                return out  # the end is clear of the bed (or right at its edge) - nothing to trim
            i = 0  # drop any leading run inside the bed
            while i + 1 < len(out):
                _fn, dn, hwn = foot(out[i + 1])
                if dn >= hwn - 2:
                    break
                i += 1
            if i + 1 >= len(out):
                return out  # the whole channel lies in the stream - leave it
            f, _d, hw = foot(out[i])
            nxt = out[i + 1]
            ux, uy = nxt[0] - f[0], nxt[1] - f[1]
            ul = math.hypot(ux, uy) or 1.0
            return [(f[0] + ux / ul * (hw - 2), f[1] + uy / ul * (hw - 2))] + out[i + 1 :]

        out = snap_front(pts)
        out = snap_front(out[::-1])[::-1]
        return out

    @staticmethod
    def _pond_anchored(frm: Any, to: Any) -> bool:
        """True if a watercourse connects TO the pond at either end (frm/to kind == 'pond') - the cue to snap
        that end onto the rim so it JOINS the open water instead of drawing its bed/sheen across it."""
        return any(a and a.get("kind") == "pond" for a in (frm, to))

    def field_channel(self: Settlement, pts: Any, col: str, w0: float, w1: float, late: bool = False) -> None:  # type: ignore[misc]
        """Draw a comb-net irrigation channel (from the waterfields engine) THROUGH the water block, so it
        JOINS the pond + the other channels cleanly: its bed sits in the shared bed group (composited as one
        confluence, no dark seam), OVER the pond's rim edge (so its bed covers the rim where it meets the
        pond -> a clean gap, not the rim cutting across). `col` is the bed color (supply vs drain); the width
        tapers `w0 -> w1` along the run (split into pieces). The sluice end is snapped onto the rim by
        `_clip_to_pond`, and an end meeting the MOAT is snapped onto the moat bed's edge by
        `_clip_to_moat` (the same clean-mouth join, for a moated city's taps and drain culverts).
        An end reaching into a STREAM bed is snapped onto that bed's edge by `_clip_to_stream`
        (the confluence mouth for a drain culvert emptying into a stream).
        The field_ditches are recorded separately (gen-side) for the topology checks; the DRAWN
        stroke - post-clip geometry, STROKE WIDTHS, bed draw position, late flag - is recorded in
        M['drawn_channels'] so pond_fill_covers_channel_mouths can verify the pond fill paints over
        every joining mouth (and finish() can see whether a LATE stroke joins the pond and relocate
        the fill). The widths ride along because water_channels_join_not_cross judges a junction by
        whether the joining stroke's tip lands inside the OTHER stroke's drawn band - which needs
        that band's width, and needs it from the post-clip record rather than the pre-clip
        field_ditches/channels (the two diverge wherever a mouth was snapped onto open water)."""
        pts = self._clip_to_stream(self._clip_to_river(self._clip_to_moat(self._clip_to_pond(pts), capr=max(w0, w1) / 2), capr=max(w0, w1) / 2))
        # ROUND THE BENDS: an earthen ditch turns on a swept curve, never a mitred corner (see
        # fillet_polyline for the why and the ~2.5-widths radius). Applied AFTER the mouth clips so a
        # snapped pond/moat/stream junction keeps its exact endpoint, and the DRAWN geometry recorded
        # below is the filleted line, which is what the mouth-cover and join checks measure.
        pts = fillet_polyline(pts, 2.5 * max(w0, w1))
        rec: dict[str, Any] = {"pts": [[round(x, 1), round(y, 1)] for x, y in pts], "late": late, "w0": round(w0, 2), "w1": round(w1, 2)}
        self.M.setdefault("drawn_channels", []).append(rec)  # ONE rec per call: flush writes bedz per piece, so the last (topmost) piece's z sticks
        if abs(w1 - w0) < 0.2:
            dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
            self._water(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{w0:.1f}" stroke-linejoin="round" stroke-linecap="round"/>', rec, late=late)
            return
        from l7r.diagram.waterfields import taper_pieces  # local: the engine packages are peers, imported lazily

        # One piece per SEGMENT, each at its arc-correct width - `taper_pieces` owns both halves of
        # that (the sqrt law, and arc-length rather than vertex-index parameterization) and is shared
        # with `_watercourse_segs`, so the drawn stroke and the corridor protecting it cannot drift.
        for piece, wk in taper_pieces(pts, w0, w1):
            dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in piece)
            self._water(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="{wk:.1f}" stroke-linejoin="round" stroke-linecap="round"/>', rec, late=late)

    def lane(self: Settlement, pts: Any, width: float = 16, clearance: float = 22, worn: bool = False, connector: bool = False) -> None:  # type: ignore[misc]
        """A village lane or connecting path. `worn=True` draws it as UNPAVED TRODDEN EARTH: a NARROW
        single track (China moved rural goods by WHEELBARROW + shoulder-pole porter + packhorse, not wide
        cart roads, so two carts could not pass), packed dirt with soft worn shoulders and NO center
        marking (a paved road was far beyond a village's means). `worn=False` keeps the legacy wide dashed
        lane (the dispersed pool maps until they are rebuilt). `clearance` is the no-build corridor
        half-width (keep houses off the tread). `connector=True` marks the trodden path that LEAVES the
        village for the wider world - it MUST run off the map edge (checked), never stop mid-landscape.
        See settlements.md 'Village lanes and connecting paths'."""
        _z = self._lane_ink_at(pts, width, worn)
        self.M.setdefault("lanes", []).append({"pts": [[x, y] for x, y in pts], "worn": worn, "w": width, "connector": connector})
        # THE INK'S OWN STREAM SLOTS, remembered so a later pass can TRIM this lane without moving it
        # in z (see `trim_lane_stubs`). `add` returns the index it wrote, and rewriting that index in
        # place is what lets the trim happen after the houses are down - which is the only moment the
        # engine knows what a lane actually serves - while the lane keeps the exact draw position it
        # has always had. Kept engine-side rather than on the record so no manifest byte moves.
        self._lane_ink.append(_z)
        self.M["lane"] = [[x, y] for x, y in pts]
        self.corridors.append((pts, clearance))
        self._record_tread(pts, width / 2)

    def _lane_ink_at(self: Settlement, pts: Any, width: float, worn: bool) -> tuple[int, int]:  # type: ignore[misc]
        """Emit a lane's two strokes and return the stream slots they landed in."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        if worn:
            z0 = self.add(f'<path d="{dd}" fill="none" stroke="#A98C58" stroke-width="{width + 2.5:.1f}" opacity="0.4" stroke-linejoin="round" stroke-linecap="round"/>')  # soft worn-earth shoulder
            z1 = self.add(f'<path d="{dd}" fill="none" stroke="#C9AE79" stroke-width="{width:.1f}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')  # packed-earth tread, no centerline
        else:
            z0 = self.add(f'<path d="{dd}" fill="none" stroke="#CBB178" stroke-width="{width}" opacity="0.65"/>')
            z1 = self.add(f'<path d="{dd}" fill="none" stroke="#6B4F2A" stroke-width="1.4" stroke-dasharray="8,8" opacity="0.7"/>')
        return (z0, z1)

    def trim_lane_stubs(self: Settlement, way_reach: float = 40.0, house_reach: float = 90.0, fan_spread: float = 60.0, fan_bearing: float = 25.0) -> int:  # type: ignore[misc]
        """Pull back any internal lane end that REACHES NOTHING. Returns how many ends were trimmed.

        A lane exists to be fronted. The engine already ends an arm where it meets crop or water
        ("shortening the arm is the honest fix: the lane simply ends where the crop starts"), but an
        arm that meets neither runs the full cluster band into open ground - and the thing that says
        where it should stop, namely where the houses actually landed, does not exist when the lanes
        are laid. Lanes must be laid FIRST: a lane is a no-build corridor the homesteads front. So
        the trim happens here instead, after the flush, by rewriting the ink in the stream slots the
        lane already owns - the lane keeps its exact draw position and nothing re-layers.

        MEASURED before it existed: five internal lane ends across the four live scripted hamlets
        (and honda, ubame x4, kikuta x2, tanada, hoshizora among the frozen ones) ended more than
        40 ft from any other way AND more than 90 ft from any farmhouse - a blunt tread stopping in
        bare grass, serving no house, reaching no field, connecting to nothing. On Sawada one such
        arm also ran 13 ft from and near-parallel to the lane it had already met, reading at fit zoom
        as one doubled track rather than a fork.

        TRIMMING ONLY EVER SHORTENS, which is what makes it safe to run after placement: a corridor
        that shrinks cannot invalidate a house already seated against it. The CONNECTOR is exempt and
        must stay whole - it is the track out of the settlement and `connector_lane_runs_off_edge`
        requires it to reach the frame; a path stopping mid-landscape is the defect, not the cure."""
        lanes = self.M.get("lanes") or []
        houses = self.M.get("houses") or []
        trimmed = 0
        _drop: set[int] = set()

        def _fan_rival(q: Pt, bearing: float, house: Pt, mine: float, me: int) -> bool:
            """Is another lane's end standing beside this one, pointing the same way, and NEARER the
            same house? If so this end is the spare tine of a fan and the house is not its to claim."""
            for k, other in enumerate(lanes):
                if k == me or k in _drop or other.get("connector") or len(other.get("pts") or []) < 2:
                    continue
                op = [(float(x), float(y)) for x, y in other["pts"]]
                for tip, prev in ((op[0], op[1]), (op[-1], op[-2])):
                    if math.dist(tip, q) > fan_spread or math.hypot(tip[0] - house[0], tip[1] - house[1]) >= mine:
                        continue
                    _b = math.degrees(math.atan2(tip[1] - prev[1], tip[0] - prev[0]))
                    if abs((bearing - _b + 180.0) % 360.0 - 180.0) <= fan_bearing:
                        return True
            return False

        for i, ln in enumerate(lanes):
            if ln.get("connector") or i >= len(self._lane_ink):
                continue
            pts = [(float(x), float(y)) for x, y in ln["pts"]]
            if len(pts) < 2:
                continue

            def _reaches(q: Pt, me: int = i, run: Any = None) -> bool:
                for k, other in enumerate(lanes):
                    if k == me or len(other["pts"]) < 2:
                        continue
                    op = [(float(x), float(y)) for x, y in other["pts"]]
                    _near = min(zip(op, op[1:], strict=False), key=lambda ab: seg_dist(q[0], q[1], ab[0], ab[1]))
                    if seg_dist(q[0], q[1], _near[0], _near[1]) > way_reach:
                        continue
                    # A LANE THAT MEETS ANOTHER CROSSES IT; ONE THAT FRAYS RUNS ALONGSIDE IT.
                    # Proximity alone is not arrival, and taking it as such made this predicate blind
                    # to the very arm the docstring above cites: Sawada's lane 0 ran 90 ft past its
                    # own T with lane 2 and died 13 ft from it on an 8 deg divergence, so it was
                    # "within 40 ft of another way" - the lane it had ALREADY met - and passed. The
                    # adjacency that constitutes the defect was satisfying the test for it.
                    if run is not None and _angle_between(run, _near) < _FRAY_DEG:
                        continue  # near-parallel: this is the same track fraying, not a junction
                    return True
                # A FARMHOUSE DISCHARGES ONE LANE END'S OBLIGATION, NOT THREE.
                #
                # Nothing said a house could only be claimed once, so three ends standing within 40
                # ft of each other, all fronting the same house at 66.9 / 55.1 / 40.0 ft, all passed
                # - and a settlement-review read the result at 3x zoom as a broom: not three ways,
                # one way drawn three times with the ends fanned. The end NEAREST the house keeps it;
                # any other end alongside it, pointing the same way, has to find its own reason to
                # exist or be trimmed back until it does.
                #
                # The bearing clause is what keeps a genuine CROSSROADS legal. Two lanes reaching one
                # house from opposite quarters is a house on a corner - a real thing that reads as
                # one. It is only ends arriving ALONGSIDE each other that the eye merges.
                _my = math.degrees(math.atan2(run[1][1] - run[0][1], run[1][0] - run[0][0])) if run else None
                for h in houses:
                    _d = math.hypot(q[0] - h["x"], q[1] - h["y"])
                    if _d > house_reach:
                        continue
                    if _my is None or not _fan_rival(q, _my, (h["x"], h["y"]), _d, me):
                        return True
                return False

            def _junction_floor(_p: list[Pt], me: int = i) -> float:
                """How much of this lane may NOT be trimmed away, because another way ties into it.

                AN END THAT CARRIES A JUNCTION IS NOT BLUNT - holding the network together is its own
                reason to exist. `_pull_back` keeps the SHORTEST end that reaches something, so
                without this it happily cuts past a tie point and orphans whatever was tied on.
                Measured on Mizuguchi: the trim cut 160 ft off a lane, taking its junction with it,
                the orphan-healer then re-laid the same alignment as a 3 ft web path, and the street
                came out stroked 5 / 3 / 5 with a round-cap knuckle at the step - a repair scar in
                open ground, which a review read at 2x as a lollipop knob mid-street."""
                _acc, _keep = 0.0, 0.0
                for _n in range(len(_p) - 1):
                    _acc += math.dist(_p[_n], _p[_n + 1])
                    _q = _p[_n + 1]
                    for _k, _o in enumerate(lanes):
                        if _k == me or _k in _drop or len(_o["pts"]) < 2:
                            continue
                        _op = [(float(x), float(y)) for x, y in _o["pts"]]
                        _seg = min(zip(_op, _op[1:], strict=False), key=lambda _ab: seg_dist(_q[0], _q[1], _ab[0], _ab[1]))
                        if seg_dist(_q[0], _q[1], _seg[0], _seg[1]) > way_reach:
                            continue
                        # AND IT HAS TO BE A CROSSING, NOT A NEIGHBOR - the `_FRAY_DEG` rule again.
                        # Counting proximity alone made every point of a near-parallel arm look like
                        # a tie, so the floor came out at the full length and nothing could be
                        # trimmed at all.
                        #
                        # A CONTINUATION - two lanes meeting end to end at a shallow angle - is
                        # deliberately NOT protected here, though it is a real tie. Protecting it
                        # was tried, and it deadlocks against the fan rule on a map where the two
                        # tines of the fan are themselves a continuation: the arm cannot be trimmed
                        # without cutting the street, and the fan cannot be cleared without trimming
                        # the arm. The repair scar that motivated the attempt was a WIDTH problem,
                        # not a trim problem, and is fixed where the width is chosen instead.
                        if _angle_between((_p[_n], _q), _seg) >= _FRAY_DEG:
                            _keep = _acc
                            break
                return _keep

            for _ in range(2):  # each end in turn; a 2-point lane can lose at most one
                if len(pts) >= 2 and not _reaches(pts[-1], run=(pts[-2], pts[-1])):
                    pts = _pull_back(pts, lambda q, _p=pts: _reaches(q, run=(_p[-2], _p[-1])), min_len=_junction_floor(pts))
                    trimmed += 1
                pts.reverse()
            # ...and a lane too SHORT to front anybody is not a lane at all, it is clipping debris.
            # An arm cut back by crop or water can be left as a stub, and a stub cannot be trimmed
            # into legitimacy - shortening it only moves the same unserved end closer in. A lane
            # exists to be fronted and one homestead's frontage is ~71 ft, so below that it fronts
            # nobody by construction. Measured: the shortest genuine internal lane in the whole pool
            # is 90 ft and the median is 361; cohort seed 5 carried a 33 ft fragment whose far end
            # stood 97 ft from the nearest farmhouse and which no amount of trimming could rescue.
            if _lane_len(pts) < _LANE_MIN_FT / max(float(self.M["meta"].get("ftpx", 1) or 1), 0.01):
                _drop.add(i)
                for _z in self._lane_ink[i]:
                    self.out[_z] = ""
                trimmed += 1
                continue
            if [list(p) for p in pts] == ln["pts"]:
                continue
            ln["pts"] = [[round(x, 1), round(y, 1)] for x, y in pts]
            z0, z1 = self._lane_ink[i]
            dd = 'M' + ' L'.join(f'{x},{y}' for x, y in ln["pts"])
            for z in (z0, z1):
                self.out[z] = re.sub(r'd="M[^"]*"', f'd="{dd}"', self.out[z], count=1)
        if _drop:  # rebuild record and ink together so their indices stay aligned
            self.M["lanes"] = [ln for k, ln in enumerate(lanes) if k not in _drop]
            self._lane_ink = [z for k, z in enumerate(self._lane_ink) if k not in _drop]
        return trimmed

    def street(self: Settlement, pts: Any, width: float | None = None, label: Any = None, main: bool = False) -> None:  # type: ignore[misc]
        """A town street (packed earth): the gate-to-yamen main avenue (main=True) or a
        cross lane off it. Buildings front it; a no-build corridor runs down its center.
        Default real width 24 ft (converted at the map's ftpx, linework-floored)."""
        if width is None:
            width = self.lw(24)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append(
            (pts, width / 2 + max(32 * self.bscale, 17))
        )  # buildings front the street but their corners stay off the bed (margin at the map's grain, floored at the largest dwelling's half-diagonal)
        st = {"main": main, "w": width, "pts": [[x, y] for x, y in pts], "z": None}
        self.M.setdefault("town_streets", []).append(st)
        self._ground(
            width,
            st,
            "z",
            edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width - 7}" opacity="1" stroke-linejoin="round" stroke-linecap="round"/>',
        )
        if label:
            mid = pts[len(pts) // 2]
            self.label(mid[0] + 38, mid[1], label, 11, italic=True, color="#5A4326")

    _Rect = tuple[float, float, float, float]

    def _kido_rects(self: Settlement, x: float, y: float, rot: float, guard_side: int, hw: float, fences: Sequence[Poly] = ()) -> tuple[_Rect, list[_Rect], _Rect, Callable[[_Rect], Poly]]:  # type: ignore[misc]
        """The local rects a kido glyph at (x, y) is built from - (roof, posts, guard, to_corners) -
        with the guard box already slid clear of the roadbed. Local frame: the gateway bar spans the
        X axis and rotate(rot) turns it onto the bar angle, so local +x is ACROSS the lane and local
        +y along it. Factored out because two callers need the SAME geometry: kido() draws it, and
        kido_reservation() reserves the ground it will stand on long before it is drawn."""
        roof = (-hw, -7.0, 2 * hw, 14.0)
        posts = [(-hw - 1, -8.0, 4.0, 16.0), (hw - 3, -8.0, 4.0, 16.0)]
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))

        def to_corners(rect: Settlement._Rect) -> Poly:
            """The rect's four corners in map coords, in WINDING order (so a caller may use the
            result as a polygon, not merely as a point cloud for a bbox)."""
            rx0, ry0, rw, rh = rect
            return [(x + a * cr - b * sr, y + a * sr + b * cr) for a, b in ((rx0, ry0), (rx0 + rw, ry0), (rx0 + rw, ry0 + rh), (rx0, ry0 + rh))]

        # THE GUARD BOX TAKES THE NEAREST CLEAR SPOT BESIDE THE OPENING, on the ward-interior flank
        # (the `guard_side` +/-y set by the caller). It starts just beyond the bar's end and walks
        # OUTWARD, trying the near side of the opening first and the far side at the same distance,
        # until it stands clear of two things:
        #   - every LANE BED, by a verge of ~12 real ft. Straight-line arithmetic is not enough: the
        #     ring road CURVES as it passes the gate, so a box set back along the road walks into a
        #     bed it started clear of (Tango's east ward gate, GM 2026-07-26).
        #   - every WALL TOWER already standing. The rampart is drawn long before s.ward, and the
        #     ward fence meets the wall exactly where the last kido hangs, so the box can slide onto
        #     a mural bastion (Nagahara's west ward gate). The kido cannot move and the tower will
        #     not (a coverage-thin curtain needs it), so the BOX is what yields - it simply stands on
        #     the other flank of its own gateway, which is as plausible a spot for a watch shack.
        #   - the RAMPART and any compound wall it could be pushed onto.
        #   - THE WARD FENCE ITSELF (GM 2026-07-27: "ward gates seem to sometimes overlap with
        #     neighborhood walls"). The gateway - roof and posts - stands ON the fence, because the
        #     gate IS the opening in it; the guard box does NOT. It is a small building on the verge
        #     beside the gate, and a fence line drawn through the middle of it reads as a mistake,
        #     which is what it is. This was excluded on the reasoning that "the fence runs through
        #     the gate by construction", which is true of the GATEWAY and was over-applied to its
        #     furniture. Perpendicular crossings were fine either way (the box sits along the lane,
        #     off the fence line); it is the OBLIQUE crossings that cut the box, and two of the
        #     pool's fourteen gates were cut. Tested with SAT against the stroked fence, not by
        #     corner distances: a line through the CENTRE of a 15x16 box leaves every corner ~8px
        #     clear, so the corner test the lane beds use would have reported it clear.
        y0 = 12.0 if guard_side >= 0 else -28.0
        verge = max(self.px(12), 4.0)
        runs = [(pts, half + verge) for pts, half in lane_runs(self.M)]
        runs += [(pts, half) for lbl, pts, half in wall_runs(self.M) if "ward fence" not in lbl]
        towers = [tower_quad(t) for t in list(self.M.get("wall_towers") or []) + [g for g in (self.M.get("gate_structs") or []) if g.get("kind") == "tower"]]
        # 4.0 = the fence's 2.5px drawn half-width plus a hair: the box may stand hard against its
        # own fence (that is where a gate watch belongs), it may not be cut by it
        fq = [q for f in fences for q in stroke_quads(f, 4.0)]
        guard: Settlement._Rect = (-hw - 13, y0, 15.0, 16.0)
        for step in range(24):  # bounded: 24 x 1.5px is far more walk than any real crossing needs
            for cand in ((-hw - 13 - 1.5 * step, y0, 15.0, 16.0), (hw - 2 + 1.5 * step, y0, 15.0, 16.0)):
                gc = to_corners(cand)
                blocked = any(seg_dist(cx, cy, pts[i], pts[i + 1]) < clear for pts, clear in runs for i in range(len(pts) - 1) for (cx, cy) in gc)
                if not blocked and not any(sat_overlap(gc, tq) for tq in towers) and not any(sat_overlap(gc, q) for q in fq):
                    return roof, posts, cand, to_corners
        return roof, posts, guard, to_corners  # pragma: no cover - nowhere clear within 36px of the opening on either flank; keep the traditional seat and let kido_guard_box_clear_of_lanes report it

    def kido_seat(self: Settlement, x: float, y: float, boundary: Any) -> tuple[float, int]:  # type: ignore[misc]
        """The (bar angle, guard flank) a kido seated at (x, y) on the ward fence `boundary` will
        take: square to the lane running through it, else along the local fence tangent, with the
        guard box on the ward-interior side. s.ward calls this for every gate it draws; a gen calls
        it (via kido_reservation) to reserve that ground BEFORE the packs run."""
        i = min(range(len(boundary) - 1), key=lambda j: seg_dist(x, y, boundary[j], boundary[j + 1]))
        fence = math.degrees(math.atan2(boundary[i + 1][1] - boundary[i][1], boundary[i + 1][0] - boundary[i][0]))
        lane = lane_through_gate(self.M, x, y, fence)
        rot = kido_bar_deg(lane[0], fence) if lane else fence
        nx, ny = -math.sin(math.radians(rot)), math.cos(math.radians(rot))  # the local +y flank, in map coords
        icx = sum(p[0] for p in boundary) / len(boundary)  # the fence polyline's centroid sits toward the ward interior
        icy = sum(p[1] for p in boundary) / len(boundary)
        return rot, (1 if (icx - x) * nx + (icy - y) * ny >= 0 else -1)

    def kido_reservation(self: Settlement, x: float, y: float, boundary: Any, margin: float = 17.0) -> Poly:  # type: ignore[misc]
        """The no-build rect a gen should `block_polys.append(...)` for a ward gate at (x, y), sized
        to the glyph that will actually be drawn there. THE ORDERING TRAP this solves (it is why the
        helper exists rather than a hand-written rect in each gen): s.ward runs near the END of a
        city gen, long after the packs, so the gates' ground must be reserved up front - but the
        glyph's extent is NOT symmetric (it reaches ~36px on the guard-box flank and ~10px on the
        other) and its angle now depends on the lane it bars, so a hand-tuned rect goes stale the
        moment a fence or a road moves, and a square big enough to be safe at any angle costs real
        housing (Tango lost its merchant band and a well to one). `margin` inflates the rect by a
        large dwelling's half-diagonal, since block_polys are CENTER-tested for urban packs.
        Call it AFTER the lanes through the gates are drawn, so kido_seat sees them."""
        rot, side = self.kido_seat(x, y, boundary)
        # the fence goes in explicitly: at reservation time s.ward has not run, so M['wards'] is
        # still empty and the drawn call's wall_runs lookup would find nothing to agree with
        roof, posts, guard, to_corners = self._kido_rects(x, y, rot, side, self.lw(18) / 2 + 5, fences=[[(float(p[0]), float(p[1])) for p in boundary]])
        cs = [c for rect in (roof, *posts, guard) for c in to_corners(rect)]
        x0, y0 = min(c[0] for c in cs) - margin, min(c[1] for c in cs) - margin
        x1, y1 = max(c[0] for c in cs) + margin, max(c[1] for c in cs) + margin
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def kido_mesh(self: Settlement) -> int:  # type: ignore[misc]
        """Bar every machi mouth with a kido (research 021 item 6: the ward MESH - Edo's
        machi-kido and Qing's zhalan; no ward walls, the block's own gate closes at night).
        Reads the SAME machi_mouths source the validator reads, so the two sides cannot
        disagree. Call AFTER streets + districts are declared and BEFORE the packs (each
        kido reserves its ground). The bar runs ACROSS its street. Returns the count."""
        n = 0
        for mx, my in machi_mouths(self.M):
            best, bd = 0.0, 1e9
            for st in self.M.get("town_streets", []):
                pts = st["pts"]
                for i in range(len(pts) - 1):
                    d = seg_dist(mx, my, tuple(pts[i]), tuple(pts[i + 1]))
                    if d < bd:
                        bd = d
                        best = math.degrees(math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0]))
            # reserve the gate + guard-box ground BEFORE the packs run (a kido drawn
            # without a reservation had rows seated against its guard box)
            self.block_polys.append([(mx - 30, my - 30), (mx + 30, my - 30), (mx + 30, my + 30), (mx - 30, my + 30)])
            self.placed.append((mx, my, 48, 48))  # the guard box hangs W/N of the bar; the frontage rows now GAP the mouths, so the reserve only needs the gate's own ground
            self.kido(mx, my, rot=best + 90)
            n += 1
        return n

    def kido(self: Settlement, x: float, y: float, horizontal: bool = True, sw: float | None = None, rot: float | None = None, guard_side: int | None = None) -> None:  # type: ignore[misc]
        """A kido - a wooden WARD GATE barring a street at a quarter boundary, manned and shut at
        night to keep the samurai quarter apart from the commoners. A small city seals its wards
        with GATES, not internal ramparts (the walled-ward / fang system was a great-capital, Tang-
        era thing). Drawn OVER the street (a roofed gateway + posts + a guard box); records M['kido'].
        THE GATE SQUARES TO WHAT IT BARS (GM 2026-07-26): a kido exists to shut a WAY, so where a
        street, alley, road or the ring road runs through the seat, the roofed bar stands SQUARE
        ACROSS THAT LANE and the fence meets it at whatever angle the fence happens to run; only
        where no lane passes through does the bar fall back to the LOCAL FENCE TANGENT (the earlier
        GM 2026-07-24 rule, which is still what a gate in open fence wants). The two agree wherever
        a lane meets its fence squarely, which is most crossings; they diverge on an oblique one -
        Tango's SW ring-road gate sat 38 degrees off square to the road it barred, and read as a
        stamp dropped on the roadbed. Pass `rot` (degrees) for the bar angle; s.ward computes it via
        lane_through_gate/kido_bar_deg, and kido_aligned_with_ward_fence grades it the same way.
        The guard box rotates with the group; `guard_side` (+1 = the local +y flank, -1 = the -y
        flank) picks which side it stands on - s.ward passes the WARD-INTERIOR side (the gate watch
        belongs to the ward it seals). It is then NUDGED clear of any lane bed it would otherwise
        stand in: the box is a small building on the verge, not an obstruction in the road, and a
        ring road that CURVES past the gate walks under a box placed on straight-line arithmetic
        (Tango's east ward gate, GM 2026-07-26). Legacy `horizontal` (True = an E-W street through
        a N-S fence) remains the fallback when rot is omitted, reproducing the old drawings."""
        if sw is None:
            sw = self.lw(18)  # the barred opening spans a real ~18 ft street
        hw = sw / 2 + 5
        if rot is None:
            rot = 90.0 if horizontal else 0.0
        if guard_side is None:
            guard_side = -1 if horizontal else 1  # the legacy flanks (E of a N-S gate, S of an E-W one)
        # the ward fences only, NOT their wall-caps: kido_reservation reserves ground against the
        # bare boundary polyline (the caps do not exist yet then), and the two must agree
        roof, posts, guard, _corners = self._kido_rects(x, y, rot, guard_side, hw, fences=[pts for lbl, pts, _hw in wall_runs(self.M) if lbl.endswith("ward fence")])
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{roof[0]:.0f}" y="{roof[1]:.0f}" width="{roof[2]:.0f}" height="{roof[3]:.0f}" rx="1.5" fill="#8A6E3E" stroke="#3F3018" stroke-width="1.5"/>')
        for px, py, pw, ph in posts:
            g.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw:.0f}" height="{ph:.0f}" fill="#3F3018"/>')
        g.append(f'<rect x="{guard[0]:.0f}" y="{guard[1]:.0f}" width="{guard[2]:.0f}" height="{guard[3]:.0f}" rx="1" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        corners = [c for rect in (roof, *posts, guard) for c in _corners(rect)]  # the gate's full drawn footprint, rotated (for the labels-on-top check)
        bbox = [round(min(c[0] for c in corners), 1), round(min(c[1] for c in corners), 1), round(max(c[0] for c in corners), 1), round(max(c[1] for c in corners), 1)]
        self.M.setdefault("kido", []).append(
            {
                "x": round(x, 1),
                "y": round(y, 1),
                "horizontal": abs(sr) >= abs(cr),
                "rot": round(rot % 180.0, 1),
                "z": z,
                "bbox": bbox,
                "guard": [
                    [round(cx, 1), round(cy, 1)] for cx, cy in _corners(guard)
                ],  # the watch box's own footprint, so kido_guard_box_clear_of_lanes can grade it (the bbox alone cannot tell box from bar)
                # ...and the TRUE (rotated) footprint of every part. The bbox is an axis-aligned box
                # round the whole group - honest while every kido was axis-aligned, badly overstated
                # now that they turn onto their lane: Nagahara's SW gate at 115deg has a bbox ~60%
                # larger than the glyph, and the keep-clear checks read it as overlapping a mural
                # tower the gate in fact clears (GM 2026-07-26). bbox stays for the label-occlusion
                # pass, where over-stating is the safe direction.
                "parts": [[[round(cx, 1), round(cy, 1)] for cx, cy in _corners(rect)] for rect in (roof, *posts, guard)],
            }
        )

    _WARD_STROKE = 5.0  # the fence's drawn width; recorded so check_village measures the ink, not the vertex

    def _ward_ends_on_wall(self: Settlement, boundary: Poly, reach: float = 24.0) -> Poly:  # type: ignore[misc]
        """JOIN, DON'T INTERSECT: snap each ward-fence END onto the city rampart's centerline.

        The placement half of the rule `city_ward_fence_joins_wall_not_crosses` gates (GM 2026-07-27,
        on Minami: "the neighborhood walls stick out the other side of the city walls"). A ward fence
        ENDS at the wall - the rampart is what seals the ward, so a palisade continuing out through it
        into the berm encloses nothing and draws as two walls crossing at an intersection. This is the
        wall member of the family the ways and the watercourses already had: a lane terminates at the
        through-lane it meets rather than poking a stub out the far side, and a watercourse joins at a
        T or a Y rather than crossing.

        A gen hand-places the fence's ends, and getting one onto the wall line by eye is hopeless -
        Minami's were 4.2-4.9px outside, Tango's 2.9-4.0px, none of it visible in a gen and all of it
        inside `city_ward_fence_meets_wall`'s 10px tolerance. So the engine puts them there instead:
        the end is EXTENDED (or trimmed) ALONG ITS OWN TERMINAL SEGMENT to where that line crosses the
        wall ring - the same "extend along its own axis, never diagonally to the nearest point" rule
        `city_streets_meet_through_lanes` states for a lane meeting a through-lane, because a
        perpendicular snap would swing the last stretch of fence off the line the gen drew. Where the
        terminal segment runs parallel to the wall and never meets it, the nearest point on the ring is
        the honest fallback. An end further than `reach` from the wall is left exactly as placed: that
        is not a junction at all but a fence that fails to reach the rampart, which is
        `city_ward_fence_meets_wall`'s defect to report, and silently dragging it 200px would hide it.
        """
        wall = self.M.get("wall")
        if not wall or len(boundary) < 2:
            return boundary
        ring: Poly = [(x, y) for x, y in wall]
        ring = ring + [ring[0]]
        out = list(boundary)
        for idx, inward in ((0, 1), (len(out) - 1, len(out) - 2)):
            end, prev = out[idx], out[inward]
            near = min((seg_closest(end[0], end[1], ring[i], ring[i + 1]) for i in range(len(ring) - 1)), key=lambda c: math.hypot(c[0] - end[0], c[1] - end[1]))
            if math.hypot(near[0] - end[0], near[1] - end[1]) > reach:
                continue  # not an abutting end - city_ward_fence_meets_wall reports that gap
            dx, dy = end[0] - prev[0], end[1] - prev[1]
            dl = math.hypot(dx, dy) or 1.0
            far = (end[0] + dx / dl * reach, end[1] + dy / dl * reach)
            back = (end[0] - dx / dl * reach, end[1] - dy / dl * reach)
            hits = [ip for i in range(len(ring) - 1) if segments_cross(back, far, ring[i], ring[i + 1]) and (ip := seg_intersect(back, far, ring[i], ring[i + 1])) is not None]
            out[idx] = min(hits, key=lambda p: math.hypot(p[0] - end[0], p[1] - end[1])) if hits else near
        return out

    def ward(self: Settlement, name: str, boundary: Any, gates: Any) -> None:  # type: ignore[misc]
        """An internal WARD boundary - a light earthwork/palisade fence (NOT a city rampart) that
        SEALS a quarter (the samurai/government ward) off the commoner streets, so its kido gates
        cannot simply be walked around: the fence is continuous between the gates, its ends abut
        the city wall, and a street may pierce it ONLY at a gate. `boundary` is the fence polyline;
        `gates` are (x, y) kido seats where a street crosses it (a legacy third element - the old
        horizontal flag - is accepted and ignored). PLACEMENT RULE (GM 2026-07-26, refining the
        2026-07-24 fence rule): each kido SQUARES TO THE LANE RUNNING THROUGH IT - a gate exists to
        shut a way, so the bar stands across the roadbed and the fence meets it obliquely if that is
        how the fence runs. Only a gate with no lane through it falls back to the LOCAL FENCE
        TANGENT (never an axis-aligned stamp on a slanted run). Its guard box stands on the
        WARD-INTERIOR flank (the gate watch belongs to the ward it seals), nudged clear of the
        roadbed by s.kido. Records M['wards']."""
        boundary = self._ward_ends_on_wall([(p[0], p[1]) for p in boundary])
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in boundary)
        fz = self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="{self._WARD_STROKE:g}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')  # palisade
        self.corridors.append((boundary, 11))  # buildings keep off the fence line
        # the fence ends ABUT the city wall: lay a short wall-stroke CAP over each end so the rampart
        # renders ON TOP of the fence there (the fence runs UNDER the wall), not the fence over the wall.
        # The cap FOLLOWS the wall (arc-length +/-16 px through any vertex in the span) rather than being a
        # single straight tangent: a fence that abuts AT a wall corner used to get a straight stub tangent to
        # one segment only, which juts past the bend and reads as a second wall section overlapping the first
        # (Nagahara SW, GM 2026-07). A wall-following cap stays flush at both corners and flat runs.
        caps: list[Any] = []
        wall = self.M.get("wall")
        if wall:
            pts_w = [(x, y) for x, y in wall]
            ring = pts_w + [pts_w[0]]
            perim = self._wall_perimeter(pts_w)
            n_w = len(pts_w)
            varcs = []  # cumulative arc of each wall vertex, to fold corners into the cap span
            _acc = 0.0
            for i in range(n_w):
                varcs.append(_acc)
                _acc += math.hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1])
            for ex, ey in (boundary[0], boundary[-1]):
                best: Any = None
                for i in range(len(ring) - 1):
                    cx, cy = seg_closest(ex, ey, ring[i], ring[i + 1])
                    d = math.hypot(cx - ex, cy - ey)
                    if best is None or d < best[0]:
                        best = (d, (cx, cy))
                if best and best[0] < 24:  # the end abuts the wall - cap it
                    px, py = best[1]
                    arc = self._wall_arc_of(pts_w, (px, py))
                    a0, a1 = arc - 16, arc + 16
                    span: list[tuple[float, tuple[float, float]]] = [
                        (a0, self._wall_point_at_arc(pts_w, a0)[:2]),
                        (arc, (px, py)),
                        (a1, self._wall_point_at_arc(pts_w, a1)[:2]),
                    ]
                    for vi in range(n_w):  # fold in any wall vertex the cap crosses, so the cap bends WITH the rampart
                        for va in (varcs[vi] - perim, varcs[vi], varcs[vi] + perim):
                            if a0 < va < a1:
                                span.append((va, (pts_w[vi][0], pts_w[vi][1])))
                    cappts = [(round(x, 1), round(y, 1)) for _, (x, y) in sorted(span, key=lambda s: s[0])]
                    dd_cap = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in cappts)
                    cz = self.add(f'<path d="{dd_cap}" fill="none" stroke="#3A352C" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>')
                    caps.append({"x": round(px, 1), "y": round(py, 1), "z": cz, "pts": [[x, y] for x, y in cappts]})
        # "stroke" is the fence's DRAWN width: the palisade is stroked with a round linecap, so its ink
        # runs half of this past the last recorded vertex, and city_ward_fence_joins_wall_not_crosses
        # has to test that tip rather than the coordinate to see an overshoot through the rampart
        self.M.setdefault("wards", []).append({"name": name, "boundary": [[round(x, 1), round(y, 1)] for x, y in boundary], "z": fz, "stroke": self._WARD_STROKE, "wall_caps": caps})
        # THE FENCE SEALS COMMONERS OUT, so from this moment s.building refuses their dwellings and
        # shops inside it (WARD_BARRED_KINDS; GM 2026-08-02, Minami). ORDERING-CRITICAL: only
        # placements AFTER s.ward are guarded - a commoner already standing inside when the fence
        # goes up is a gen-ordering bug (hoist s.ward ahead of every commoner pack), and it fails
        # LOUDLY here rather than shipping and waiting for the gate to notice.
        if name == "samurai":
            interior = ward_interior([(p[0], p[1]) for p in boundary], [(p[0], p[1]) for p in (wall or [])])
            if interior:
                self._samurai_ward_interiors.append(interior)
                early = [(b["kind"], round(b["x"]), round(b["y"])) for b in self.M.get("buildings", []) if b["kind"] in WARD_BARRED_KINDS and point_in_poly(b["x"], b["y"], interior)]
                if early:
                    raise ValueError(f"commoner building(s) already inside the {name} ward when its fence was declared - hoist s.ward ahead of the commoner packs: {early[:8]}")
        for gate in gates:
            gx, gy = gate[0], gate[1]
            grot, gside = self.kido_seat(gx, gy, boundary)  # square to the lane it bars (the fence only where no lane runs through); guard box toward the ward interior
            self.kido(gx, gy, rot=grot, guard_side=gside)
        self._assert_walls_clear_of_torii(f"the {name} ward fence")  # a fence laid across a standing arch (Nagahara 2026-07-25)

    _QUARTER_ZONES = ("residential", "civic", "mixed", "reserve", "castle", "samurai")
    # "castle" and "samurai" are CAPITAL vocabulary (feature 021): the citadel's own ground and
    # the senior-compound bands. Both are deliberately outside the residential density body
    # (a C_YASHIKI compound is ~0.24 dwellings/1000px^2, legitimately under the machi floor)
    # and outside the civic-openness and reserve-cap rules; the tiling check counts them like
    # any quarter, so the interior stays fully declared.
    _RESERVE_KINDS = ("drill_ground", "garden", "agricultural_district")

    def quarter(self: Settlement, poly: Any, zone: str, kind: Any = None, label: Any = None) -> None:  # type: ignore[misc]
        """Declare a city QUARTER as a first-class zoned region (feature 006). A walled city is a
        set of quarters tiling its interior, each with a ZONE - `residential`, `civic`, `mixed`, or
        `reserve` - so density is judged PER QUARTER (an empty block in a residential quarter is a
        defect; the same emptiness in a declared civic/reserve quarter is intentional). Purely
        DECLARATIVE: it records the region + zone into M['quarters'] and does NOT move or place any
        building. A `reserve` quarter also carries a `kind` and is DRAWN as that visible feature
        (so open ground reads as a deliberate drill ground / garden / farmland, not accidental
        emptiness). Declare reserves BEFORE the packs so the surface renders under later features
        (like fields and streets). `poly` is a list of (x, y); `label` is an optional map label."""
        if zone not in self._QUARTER_ZONES:
            raise ValueError(f"quarter zone must be one of {self._QUARTER_ZONES}, got {zone!r}")
        if zone == "reserve":
            if kind not in self._RESERVE_KINDS:
                raise ValueError(f"a reserve quarter needs kind in {self._RESERVE_KINDS}, got {kind!r}")
            self._draw_reserve(poly, kind)
        elif kind is not None:
            raise ValueError(f"only a reserve quarter may carry a kind (got zone={zone!r}, kind={kind!r})")
        self.M["quarters"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in poly], "zone": zone, "kind": kind, "name": label})
        if label:
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            self.label(sum(xs) / len(xs), sum(ys) / len(ys), label, 9, italic=True, color="#5A4326")

    def _draw_reserve(self: Settlement, poly: Any, kind: str) -> None:  # type: ignore[misc]
        """Render a reserve quarter's ground as its declared kind. A drill_ground is bare packed
        earth with a dashed muster perimeter; a garden is a planted green sward. An
        agricultural_district draws NOTHING here (GM 2026-07-22): its own combs, farmhouses, and
        label ARE the rendering - the faint dashed boundary this used to add read as a stray dotted
        line cutting through the in-wall farmhouses and across the Imperial road above the burakumin
        neighborhood. The quarter stays DECLARED in M['quarters'] either way (recorded by quarter(),
        not here), so per-quarter density judging is unaffected."""
        if kind == "agricultural_district":
            return  # no boundary line - the generator's fields carry the whole visual
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        if kind == "drill_ground":
            # a muster / archery field: flat swept earth, a dashed perimeter, a few faint rake lines
            self.add(f'<polygon points="{pts}" fill="#D6C79E" stroke="#A9925C" stroke-width="1.4" stroke-dasharray="6,4"/>')
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for k in range(1, 5):
                ry = y0 + (y1 - y0) * k / 5
                self.add(f'<line x1="{x0 + 6:.1f}" y1="{ry:.1f}" x2="{x1 - 6:.1f}" y2="{ry:.1f}" stroke="#BBA76E" stroke-width="0.8" opacity="0.6"/>')
        elif kind == "garden":
            # an ornamental / kitchen garden sward: soft green with planted rows
            self.add(f'<polygon points="{pts}" fill="#C4D3A0" stroke="#6E8A44" stroke-width="1.3"/>')
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            for k in range(1, 4):
                ry = y0 + (y1 - y0) * k / 4
                self.add(f'<line x1="{x0 + 6:.1f}" y1="{ry:.1f}" x2="{x1 - 6:.1f}" y2="{ry:.1f}" stroke="#6E9A40" stroke-width="2.0" stroke-linecap="round" opacity="0.75"/>')

    def alley(self: Settlement, pts: Any, width: float | None = None) -> None:  # type: ignore[misc]
        """An UNPAVED interior lane (gravel / wood planks, not the dressed earth of a street) that
        threads the packed block cores: the poor reach their jammed interior housing by alleys,
        not the paved street frontage. Thinner than a street, drawn as a pale gravel path with a
        plank/speckle dash, and a NARROW no-build corridor so the dense core leaves a gap for it.
        Real width ~10 ft (a generous roji is 3-6 ft; ours carries the access for a whole block
        core) - at city scale that lands on the 4px linework floor, which is the doctrine: a roji
        is drawn at the minimum visible width, never to (invisible) true scale."""
        if width is None:
            width = self.lw(10)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + 11))  # setback keeps building CORNERS off the lane, not just centers
        al = {"pts": [[x, y] for x, y in pts], "w": width, "z": None}
        self.M.setdefault("alleys", []).append(al)
        self._ground(
            width,
            al,
            "z",  # an unpaved gravel lane: its surface IS the bed (no curb/edge), plus a speckle
            bed=f'<path d="{dd}" fill="none" stroke="#C7BB9C" stroke-width="{width}" opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>',
            top=f'<path d="{dd}" fill="none" stroke="#9A8A68" stroke-width="1.4" stroke-dasharray="2,5" opacity="0.7"/>',
        )
