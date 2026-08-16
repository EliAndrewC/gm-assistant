"""The city's defensive shell: the wall, its towers and walk, and the patrol road inside it.

Split from settlement/city.py by feature 113 - see settlement/city/CLAUDE.md for the index.
"""

import math
from typing import TYPE_CHECKING, Any

from .._geom import (
    Pt,
    seg_dist,
    segments_cross,
)
from .._knobs import KIDO_TOWER_KEEPCLEAR, WALL_DEFENSE, wall_tower_spacing_px

if TYPE_CHECKING:
    from ..core import Settlement


class WallsMixin:
    def _gapped_ring(self: Settlement, ring: Any, gates: Any, gap: float = 38, closed: bool = True, water_gates: Any = (), water_gap: float = 24) -> str:  # type: ignore[misc]
        """An SVG path for a wall (closed ring or open arc) with a genuine OPENING (~2*gap wide) at each
        gate, so the rampart can render OVER the ground lanes yet still let the road show THROUGH the gate
        - rather than painting a land rect over the wall (which would erase the road too, once on top).
        `water_gates` open NARROWER gaps (~2*water_gap) where a cargo canal passes the rampart under
        a water-gate arch (the Suzhou shuimen; the canal shows through exactly like a road at a gate)."""
        gpts = [(g[0], g[1]) for g in gates]
        wpts = [(g[0], g[1]) for g in water_gates]

        def isg(p: Any) -> bool:
            return any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in gpts) or any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in wpts)

        def gapof(p: Any) -> float:
            return water_gap if any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in wpts) else gap

        def lerp(a: Any, b: Any, d: float) -> Pt:
            length = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            return (a[0] + (b[0] - a[0]) * d / length, a[1] + (b[1] - a[1]) * d / length)

        subs: list[Any] = []
        cur: list[Any] = []
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            s = lerp(a, b, gapof(a)) if isg(a) else a
            e = lerp(b, a, gapof(b)) if isg(b) else b
            if not cur:  # start a fresh run (the first edge, or just after a gate)
                cur = [s]
            cur.append(e)
            if isg(b):  # this edge ends at a gate - close the run (a gap follows)
                subs.append(cur)
                cur = []
        if cur:
            subs.append(cur)
        if closed and len(subs) >= 2 and not isg(ring[0]):  # closed ring, ring[0] not a gate: last run continues into the first
            subs[0] = subs[-1] + subs[0][1:]
            subs.pop()
        return ' '.join('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in sp) for sp in subs)

    def ring_road(self: Settlement, wall_pts: Any, inset: float = 34, width: float | None = None) -> list[Pt]:  # type: ignore[misc]
        """A patrol/access ROAD just inside the city wall - the Chinese 'follow-the-wall street'
        (順城街) - a closed loop offset `inset` px in from the rampart, leaving the wall-clear zone
        a fortified city keeps for moving troops along the wall. Records M['ring_road']; returns the
        loop polygon to use as s.bound (so the quarters pack INSIDE it, off the wall). It is NOT a
        town_street: a fortification road is exempt from the must-be-built-up rule (its wall side is
        bare by design, and stretches run behind fields/compounds), but the grid still connects to it."""
        if width is None:
            width = self.lw(20)  # the ring/patrol street ~20 ft wide
        cx = sum(p[0] for p in wall_pts) / len(wall_pts)
        cy = sum(p[1] for p in wall_pts) / len(wall_pts)
        ring: list[Pt] = []
        for x, y in wall_pts:
            d = math.hypot(x - cx, y - cy) or 1.0
            f = (d - inset) / d
            ring.append((cx + (x - cx) * f, cy + (y - cy) * f))
        loop = ring + [ring[0]]
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in loop)
        self._ground(
            width,
            self.M,
            "ring_road_z",
            edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.85" stroke-linejoin="round"/>',
            bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width - 6}" opacity="1" stroke-linejoin="round"/>',
        )
        self.corridors.append((loop, width / 2 + 21))  # buildings keep WELL off the ring road (even a large/rotated footprint's corner stays off its bed)
        self.M["ring_road"] = [[round(x, 1), round(y, 1)] for x, y in loop]
        self.M["ring_road_width"] = width
        return ring

    def _tower(self: Settlement, x: float, y: float, rot: float = 0.0, wc: str = '#3A352C', along_ft: float = 62, deep_ft: float = 40) -> int:  # type: ignore[misc]
        """A wall MAMIAN BASTION (马面/敌台) drawn TO SCALE (GM 2026-07-22, was a fixed-pixel 38 px SQUARE =
        ~114 ft at 3 ft/px). A mamian is a rectangular spur PROJECTING from the wall face - Xi'an's run
        ~20 m wide x ~12 m out (~66 x 40 ft) - carrying the enemy-tower building (~30-40 ft) and the stair
        to the parapet, so it is drawn as a rectangle LONGER along the wall (`along_ft`) than it is deep
        (`deep_ft`), with the tower building inset. `rot` is the wall's local tangent, so the long axis
        runs along the wall and the depth projects across it (the caller berm-nudges so the outer part sits
        on the berm, not in the moat). A GATE tower (chenglou) passes a smaller ~52 x 30 ft. Strokes keep
        their legibility floor (the stroke convention); the footprint takes no license. Records
        M['wall_towers'] (w = along, h = deep) and reserves a no-build block. See settlements.md grounding."""
        al, dp = self.px(along_ft), self.px(deep_ft)
        tb = self.px(min(34, along_ft * 0.55))  # the enemy-tower building on the spur (~30-40 ft, inset)
        z = self.add_top(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">'
            f'<rect x="{-al / 2:.1f}" y="{-dp / 2:.1f}" width="{al:.1f}" height="{dp:.1f}" rx="1" fill="#9C8A66" stroke="{wc}" stroke-width="2.0"/>'
            f'<rect x="{-tb / 2:.1f}" y="{-tb * 0.34:.1f}" width="{tb:.1f}" height="{tb * 0.68:.1f}" rx="1" fill="#6B5A3A"/></g>'
        )
        self.M.setdefault("wall_towers", []).append({"x": round(x, 1), "y": round(y, 1), "w": round(al, 1), "h": round(dp, 1), "rot": round(rot, 1), "z": z})
        bm = 12 * max(self.bscale, 0.5)  # a modest half-margin at the map's grain
        hx, hy = al / 2 + bm, dp / 2 + bm
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        self.block_polys.append([(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))])
        return z

    def _wall_walk(self: Settlement, pts: Any, g_idx: int, arc: float, west: bool = True) -> tuple[float, float, float]:  # type: ignore[misc]
        """From wall vertex g_idx, walk `arc` px ALONG the wall (toward the WEST neighbor - smaller x -
        if west, else EAST), returning (x, y, edge_angle_deg) at that arc-distance. Lets gate furniture
        follow the curving wall and pick up its LOCAL tangent, instead of a flat offset + the gate
        vertex's tangent (which mismatch once the wall has curved away from the gate)."""
        n = len(pts)
        step_to_east = 1 if pts[(g_idx + 1) % n][0] >= pts[(g_idx - 1) % n][0] else -1
        step = -step_to_east if west else step_to_east
        i, rem = g_idx, arc
        while True:
            j = (i + step) % n
            ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            seg = math.hypot(ex, ey) or 1.0
            if seg >= rem:
                t = rem / seg
                return pts[i][0] + ex * t, pts[i][1] + ey * t, math.degrees(math.atan2(ey, ex))
            rem -= seg
            i = j

    @staticmethod
    def _wall_perimeter(pts: Any) -> float:
        n = len(pts)
        return sum(math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1]) for i in range(n))

    @staticmethod
    def _wall_point_at_arc(pts: Any, arc: float) -> tuple[float, float, float]:
        """The (x, y, tangent_deg) at arc-length `arc` measured from vertex 0, walking the ring forward
        (increasing index). Wraps. Used to seat mural towers at even spacing along the wall."""
        from ..core import Settlement  # lazy: runtime class-attr read; top-level import would cycle

        n = len(pts)
        arc = arc % Settlement._wall_perimeter(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ex, ey = b[0] - a[0], b[1] - a[1]
            seg = math.hypot(ex, ey) or 1.0
            if seg >= arc:
                t = arc / seg
                return a[0] + ex * t, a[1] + ey * t, (math.degrees(math.atan2(ey, ex)) + 90) % 180 - 90
            arc -= seg
        return pts[0][0], pts[0][1], 0.0  # pragma: no cover - defensive: arc is taken mod perimeter and the segments sum to the perimeter, so the loop always returns first

    @staticmethod
    def _wall_arc_of(pts: Any, pt: Any) -> float:
        """Arc-length (from vertex 0) of the point on the ring closest to `pt` - to locate a gate tower as
        an anchor when filling mural towers between anchors."""
        n = len(pts)
        best = (1e18, 0.0)
        acc = 0.0
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ex, ey = b[0] - a[0], b[1] - a[1]
            seg = math.hypot(ex, ey) or 1.0
            t = max(0.0, min(1.0, ((pt[0] - a[0]) * ex + (pt[1] - a[1]) * ey) / (seg * seg)))
            cx, cy = a[0] + ex * t, a[1] + ey * t
            d = math.hypot(pt[0] - cx, pt[1] - cy)
            if d < best[0]:
                best = (d, acc + t * seg)
            acc += seg
        return best[1]

    def city_wall(self: Settlement, pts: Any, gates: Any = (), ring_inset: float = 34, guard_east: Any = (), tower_skip: Any = (), water_gates: Any = ()) -> None:  # type: ignore[misc]
        """A CLOSED city rampart (a full ring, unlike the town's open hill-anchored arc), with a
        gap at each gate in `gates` (each (x,y) on the ring, where the wall runs ~horizontal -
        the N and S gates the Imperial road passes through). Each gate gets a GUARD HOUSE with an
        attached INSPECTION STATION (tariff audit) and a GUARD TOWER, all in the top layer so the
        road passes under them. Gates listed in `guard_east` put the guard house + inspection on
        the EAST side of the gate (tower west) instead of the default west - so the furniture can
        fill whichever flank of the road has the ground to spare. `tower_skip` lists keep-clear
        points (e.g. where a ward fence will later meet the wall and hang its kido gate - the
        gate cannot move, it gates a fixed crossing, so the TOWER yields): a mural tower whose
        vertex falls within ~62px of one SLIDES a short way along the wall until clear (both
        directions tried, shortest slide wins - a full vertex jump left a bare stretch of
        rampart, a defensive hole).
        Records M['wall'], M['gates'], M['gate'], M['gate_structs'] (the guard houses + towers),
        and M['inspection_stations']."""
        wc = '#3A352C'
        ring = list(pts) + [pts[0]]
        # the rampart renders in the WALL layer (over the ground lanes - a street running into the wall
        # passes UNDER it) with a GENUINE gap at each gate, so the road shows through the opening
        # TRUE SCALE for the gate THROAT (GM 2026-07-27, closing bookend on Minami). The 2026-07-22
        # pass converted the gate furniture's FOOTPRINTS to real feet but left the OFFSETS that
        # POSITION them as fixed pixels, so at a city's 1 px = 3 ft everything stood three times too
        # far apart: the wall opened a 2*38 = 76 px = 228 ft hole, the piers stood +-35 px = +-105 ft
        # apart, and the guard buildings were set back from a "26" roadway that was really 78 ft wide.
        # A 228 ft opening is not a gate - no leaf spans it, it cannot be shut, and it forces none of
        # the single file an inspection barrier exists to create. On the render it read as a plain
        # breach in the rampart, which is what sent us looking; every check still passed, because the
        # posts existed, flanked the road symmetrically and cleared the moat. Anchors, China first: a
        # Ming provincial city's gate tunnel runs ~13-23 ft clear (Nanjing Zhonghua ~23 ft, Xi'an
        # ~20 ft), and an Edo castle-town koraimon is narrower again. The trunk road entering is 26 ft,
        # and a gate NARROWS its road rather than widening for it, so the throat passes the road and no
        # more. Sizes in FEET through px(), so a town at 1 px = 1 ft is unaffected.
        gate_clear, pier_ft = 30.0, 15.0  # clear opening; masonry pier across (matches the pier footprint below)
        gate_gap = self.px(gate_clear) / 2 + self.px(pier_ft)  # HALF the wall opening: the clear throat plus one pier each side
        pier_off = self.px(gate_clear) / 2 + self.px(pier_ft) / 2  # pier centre, inner face landing on the jamb
        # A cargo canal is wider than a road - Minami's is 36 ft - and a Suzhou-pattern shuimen sets its
        # arch INTO the wall with a pier to either side, so the opening is the canal plus ~12 ft a side.
        dd = self._gapped_ring(ring, gates, gate_gap, water_gates=water_gates, water_gap=self.px(60.0) / 2)
        # the rampart's drawn width is RECORDED, because city_ward_fence_joins_wall_not_crosses judges
        # a ward fence's overshoot against this band - placement and check reading the same source
        ww = self.M["wall_stroke"] = 11.0
        self.M["wall_z"] = self.add_wall(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="{ww:g}" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add_wall(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        # the wall's TANGENT angle at each vertex (the chord through its two neighbors) - towers rotate
        # to sit square to the wall, so a tower on a slanted stretch slants with it
        tang = [math.degrees(math.atan2(pts[(i + 1) % n][1] - pts[i - 1][1], pts[(i + 1) % n][0] - pts[i - 1][0])) for i in range(n)]

        # towers straddle the wall but their FOOTING stays on the BERM: centered on the wall line, a
        # 38-40px tower pokes its outer face into a close-set moat's bed, so every tower is nudged
        # INWARD (toward the ring's centroid) until only ~8px of its outer face projects past the
        # wall centerline - the horse-face bastion's stride, standing dry whatever gap the moat is
        # later drawn at (city_wall runs before s.moat, so it cannot measure the bed; 8px clears
        # the tightest gap in the pool, Tango's 24 - moat half 11 = 13px berm, with ~4px to spare).
        # Gated by city_wall_furniture_clear_of_moat.
        def _berm_nudge(x: float, y: float, tw_: float) -> Pt:
            ux, uy = cx - x, cy - y
            ul = math.hypot(ux, uy) or 1.0
            d = tw_ / 2 - 6  # 6px projection: on a slanted stretch the square's rotation swings a corner ~2px closer than the face
            return x + ux / ul * d, y + uy / ul * d

        self.M["gate_structs"] = []
        for gx, gy in gates:
            g_idx = next(i for i, p in enumerate(pts) if p[0] == gx and p[1] == gy)  # the gate's wall vertex
            # gateposts frame the opening, standing ON the wall line to either side, ORIENTED TO
            # THE WALL'S LOCAL TANGENT - so an E/W gate's posts stand N and S of the opening (not
            # the old hard-coded N/S layout, which floated the posts parallel to an E/W wall). Each
            # post is offset +-35px along the tangent and straddles the wall: ~5px onto the berm
            # (never the moat) and ~26px inward. Recorded as gate_structs so
            # city_wall_furniture_clear_of_moat covers them (GM, 2026-07).
            _tg = math.radians(tang[g_idx])
            _tx, _ty = math.cos(_tg), math.sin(_tg)  # unit tangent along the wall
            _rox, _roy = gx - cx, gy - cy
            _rl = math.hypot(_rox, _roy) or 1.0
            _rox, _roy = _rox / _rl, _roy / _rl  # unit radial OUTWARD
            for _side in (-1, 1):
                _pcx = gx + _tx * pier_off * _side - _rox * self.px(31.5)  # offset along the wall, shifted inward so
                _pcy = gy + _ty * pier_off * _side - _roy * self.px(31.5)  # the post projects ~5 ft out / ~78 ft in
                _pw, _ph = self.px(15), self.px(24)  # TRUE SCALE (was 14x31 px = ~42x93 ft): a gate masonry pier ~15 ft across x ~24 ft along the opening
                self.add_wall(
                    f'<g transform="translate({_pcx:.1f},{_pcy:.1f}) rotate({tang[g_idx]:.1f})"><rect x="{-_pw / 2:.1f}" y="{-_ph / 2:.1f}" width="{_pw:.1f}" height="{_ph:.1f}" fill="{wc}"/></g>'
                )
                self.M["gate_structs"].append({"x": round(_pcx, 1), "y": round(_pcy, 1), "w": round(_pw, 1), "h": round(_ph, 1), "rot": round(tang[g_idx], 1), "kind": "gatepost"})
            # the GUARD HOUSE and INSPECTION STATION FLANK THE ROAD at the gate throat - one on each
            # side, facing each other across the entering roadway (the Hakone-sekisho pattern: the
            # inspection office and the guard barracks stand OPPOSITE each other just inside the gate,
            # so all arriving traffic passes BETWEEN them). Historically decisive (GM 2026-07-22, was
            # both stacked on ONE flank and walked 80/144 px = 240/432 ft along the wall, reading as
            # furniture pushed far from the gate): an inspection/tax barrier only works where traffic
            # is forced single-file, and the gate passage is that one chokepoint in the whole wall -
            # set the station back along the wall and arrivals disperse into the streets before ever
            # reaching it, defeating its purpose. So each sits ~20-100 ft inside the opening, right at
            # the roadway, NOT a few hundred feet along the wall. See settlements.md 'Historical
            # grounding'. Each is WALKED a SHORT arc to its own flank (so it picks up the wall's LOCAL
            # tangent and sits SQUARE to the wall, the ring road running lengthwise through it) then
            # pulled in radially to the ring road centerline - the two end up just off either verge of
            # the road at the gate, the road passing between them.
            g_east = any(abs(gx - ex) < 2 and abs(gy - ey) < 2 for (ex, ey) in guard_east)
            gh_west = not g_east  # guard house on the WEST flank by default; guard_east flips it east (inspection takes the other verge)
            # px(26): city_wall runs before s.road, so this falls back to the Imperial-road default -
            # which is a width in FEET and must be converted, or a city sets its guard buildings back
            # from a roadway three times wider than the one that will actually be drawn (GM 2026-07-27).
            road_half = self.M.get("road_width", self.px(26)) / 2
            # TRUE SCALE (GM 2026-07-22, was fixed-pixel 66x44 / 60x44 = ~198x132 / 180x132 ft at 3 ft/px -
            # a guardhouse drawn bigger than a temple): footprints in REAL FEET via px(). A gate guard duty
            # room is a small 1-3 bay building (~34x20 ft, upper end of the 15-35 ft attested range); a gate
            # inspection hall (sekisho/lijin bansho) ~44x22 ft. Strokes keep their legibility floor (the
            # stroke convention, SKILL.md 'to scale'); the footprint takes no license. See settlements.md
            # 'Historical grounding' for the anchors.
            for kind, west_side, fw_ft, fh_ft, fill in (("guardhouse", gh_west, 34, 20, "#C9A57A"), ("inspection", not gh_west, 44, 22, "#D8C49A")):
                fw, fh = self.px(fw_ft), self.px(fh_ft)
                # a SHORT arc to this building's flank: just past the road verge (road half-width) plus
                # the building's own half-length plus a small gap, so it stands hard by the roadway at
                # the gate rather than walked out along the wall
                arc = road_half + fw / 2 + 6
                wx, wy, ang = self._wall_walk(pts, g_idx, arc, west=west_side)
                d = math.hypot(wx - cx, wy - cy) or 1.0
                f = (d - ring_inset) / d  # radial inset to the ring road centerline
                fx, fy = cx + (wx - cx) * f, cy + (wy - cy) * f
                a = (ang + 90) % 180 - 90  # local wall tangent, folded to (-90, 90]
                trim = (
                    f'<line x1="{-fw / 2:.0f}" y1="0" x2="{fw / 2:.0f}" y2="0" stroke="#5A4326" stroke-width="0.8"/>'
                    if kind == "guardhouse"
                    else f'<rect x="{-fw / 2:.0f}" y="{-fh / 2:.0f}" width="{fw:.1f}" height="{max(fh * 0.18, 2.2):.1f}" fill="#8A6E3E"/>'
                )
                z = self.add_top(
                    f'<g transform="translate({fx:.0f},{fy:.0f}) rotate({a:.1f})">'
                    f'<rect x="{-fw / 2:.0f}" y="{-fh / 2:.0f}" width="{fw:.1f}" height="{fh:.1f}" rx="1.5" fill="{fill}" stroke="#5A4326" stroke-width="1.2"/>'
                    f'{trim}</g>'
                )
                self.M["gate_structs"].append({"x": fx, "y": fy, "w": round(fw, 1), "h": round(fh, 1), "rot": round(a, 1), "kind": kind, "z": z})
                if kind == "inspection":
                    self.M["inspection_stations"].append({"x": fx, "y": fy, "w": round(fw, 1), "h": round(fh, 1), "rot": round(a, 1), "label": "inspection station"})
            # the gate guard TOWER straddles the WALL beside the gate, tilted to the wall there and NUDGED
            # INWARD so its footing stands on the berm (below). It belongs AT the gate: try the near-gate
            # spot on the PRIMARY flank first, then the OTHER flank at the SAME short arc, and only THEN
            # step outward - so a kido or the gate furniture blocking one flank sends the tower to the
            # gate's OTHER side (still at the opening), not marooned far out among the mural bastions (GM
            # 2026-07-22: the S gate's tower had walked to arc 118 to dodge a ward-gate kido, stranding a
            # small gate tower mid-curtain while a mamian seated at the gate). Gated by
            # city_gate_tower_at_its_gate. The tower must clear BOTH any kido spot AND this gate's guard
            # house / inspection footprints (they sit on opposite flanks but converge near the opening on a
            # tight ring - city_gate_towers_clear_of_gate_furniture, GM 2026-07).
            _gfurn = [(f["x"], f["y"], f["w"], f["h"]) for f in self.M["gate_structs"] if f.get("kind") in ("guardhouse", "inspection")][-2:]

            def _tower_blocked(tx: float, ty: float, _gfurn: Any = _gfurn) -> bool:  # bind loop var (used within this iteration)
                if any(math.hypot(tx - kx_, ty - ky_) < KIDO_TOWER_KEEPCLEAR for kx_, ky_ in tower_skip):
                    return True
                return any(abs(tx - fx) < (self.px(62) + fw) / 2 + 3 and abs(ty - fy) < (self.px(62) + fh) / 2 + 3 for fx, fy, fw, fh in _gfurn)

            _cands = [(a, wf) for a in range(78, 241, 20) for wf in (g_east, not g_east)]  # near-gate first, BOTH flanks per arc; step out only as a last resort
            twx = twy = tang_e = 0.0
            for _ci, (_a, _wf) in enumerate(_cands):
                twx, twy, tang_e = self._wall_walk(pts, g_idx, _a, west=_wf)
                if not _tower_blocked(twx, twy) or _ci == len(_cands) - 1:
                    break
            ta = (tang_e + 90) % 180 - 90
            twx, twy = _berm_nudge(twx, twy, self.px(30))
            tz = self._tower(twx, twy, ta, wc, along_ft=52, deep_ft=30)
            self.M["gate_structs"].append({"x": twx, "y": twy, "w": round(self.px(52), 1), "h": round(self.px(30), 1), "rot": round(ta, 1), "kind": "tower", "z": tz})
            # ONE label for the pair, centered on the road just inside the gate and pushed far enough
            # INWARD (along the gate's radial) to clear BOTH flanking buildings - the wide italic text
            # runs across the roadway between them, so it covers neither footprint (GM 2026-07-22: the
            # old label was centered on the inspection station and painted over the guard house)
            _rix, _riy = cx - gx, cy - gy
            _rl = math.hypot(_rix, _riy) or 1.0
            _ltext = "guard / inspection stations"
            # The push must clear the label's OWN extent along the radial, not just the ring
            # inset: this caption is ~134px wide, so a gate whose radial runs along x had the
            # box straddling the rampart however far the CENTER was pushed (GM 2026-08-10, the
            # capital's east and southwest gates - captions_clear_of_the_defenses).
            _lhw0 = len(_ltext) * 9 * 0.55 / 2
            _lhh0 = 9 * 0.8
            # ADAPTIVE: step the caption inward only as far as its own box needs to clear the
            # wall and moat bands. A fixed extra push moved every gate caption on every map -
            # including the ones already correct, which cost Nagahara's notice board its seat -
            # while a fixed SMALL push left wide captions straddling the rampart on an east or
            # west gate, because the box's reach along the radial was never counted (GM
            # 2026-08-10, captions_clear_of_the_defenses).
            # NB: read the wall from the ARGUMENT, not the manifest - city_wall records
            # M["wall"] after this loop, so self.M["wall"] is still empty here and the clash
            # test silently passed at step 0 (2026-08-10)
            _wpts = [(float(q[0]), float(q[1])) for q in pts]
            _wl = [(_wpts + [_wpts[0]], 9.0)] if len(_wpts) >= 3 else []
            if self.M.get("moat"):
                _wl.append((list(self.M["moat"]) + [self.M["moat"][0]], float(self.M.get("moat_width", 22)) / 2))
            _reach = ring_inset + self.px(50)
            for _lstep in range(24):
                _lx = gx + _rix / _rl * (_reach + _lstep * 6)
                _ly = gy + _riy / _rl * (_reach + _lstep * 6)
                _q = [(_lx - _lhw0, _ly - _lhh0), (_lx + _lhw0, _ly - _lhh0), (_lx + _lhw0, _ly + _lhh0), (_lx - _lhw0, _ly + _lhh0)]
                _clash = False
                for _wp, _hw in _wl:
                    if any(min(seg_dist(_qx, _qy, _wp[_i], _wp[_i + 1]) for _i in range(len(_wp) - 1)) < _hw for _qx, _qy in _q) or any(
                        segments_cross(_q[_e], _q[(_e + 1) % 4], _wp[_i], _wp[_i + 1]) for _e in range(4) for _i in range(len(_wp) - 1)
                    ):
                        _clash = True
                        break
                if not _clash:
                    break
            self.label(_lx, _ly, _ltext, 9, italic=True, color="#5A4326")
            # RESERVE the label's ground so no later pack lands a building under the text. city_wall runs
            # BEFORE the quarters pack, so the label cannot be auto-placed AROUND the buildings the way a
            # post-pack label is - it must claim its box up front (like the gate furniture above). Without
            # this a quarter that crowds right up to the gate drops a house under the caption
            # (nagahara's N-gate laborer terraces - labels_clear_of_other_buildings). The +14 margin is a
            # building half-width, so no footprint edge pokes into the text either.
            _lhw = len(_ltext) * 9 * 0.55 / 2 + 14
            _lhh = 9 * 0.8 + 14
            self.block_polys.append([(_lx - _lhw, _ly - _lhh), (_lx + _lhw, _ly - _lhh), (_lx + _lhw, _ly + _lhh), (_lx - _lhw, _ly + _lhh)])
            for gs in self.M["gate_structs"][-3:]:
                # the tower keeps a wide keep-clear apron; the guard house / inspection are now TRUE
                # SCALE (~14x7 px) and sit hard by the road at the gate, where the road corridor
                # already fends packs off one flank - so their oversized 30px apron (calibrated for the
                # old 66x44 furniture) reserved far more ground than the footprint and squeezed a
                # gate-side quarter's packing (nagahara's E-gate merchant blocks). A modest apron keeps
                # packs from abutting the actual footprint without over-reserving (GM 2026-07-22).
                bm = 30 if gs.get("kind") == "tower" else 12
                self.block_polys.append(
                    [
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                        (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                        (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm),
                    ]
                )
        # GUARD TOWERS (mamian) around the rampart, in addition to the gate towers, for enfilading
        # flanking fire along the wall face. SPACING is set by the city's DEFENSE POSTURE (GM 2026-07-22,
        # meta wall_defense=): a border/besieged city (`siege`) packs them to the aimed-lethal bowshot so
        # every stretch of wall is under crossfire from >=2 towers; a long-peaceful city (`peaceful`) runs
        # the sparser Xi'an spacing. The gate towers are fixed ANCHORS; mural towers fill each gap between
        # anchors so no gap exceeds the tier's max spacing. Gated by city_wall_tower_coverage.
        self.M.setdefault("wall_towers", [])  # the gate towers were already added above (via _tower)
        gate_towers = [(gs["x"], gs["y"]) for gs in self.M.get("gate_structs", []) if gs.get("kind") == "tower"]
        # a mural tower must also clear each gate's INSPECTION / GUARD HOUSE (they sit INWARD from the
        # gate, so the 130px gate-vertex filter alone misses them - city_gate_towers_clear_of_gate_furniture)
        gate_furn = [(gs["x"], gs["y"]) for gs in self.M.get("gate_structs", []) if gs.get("kind") in ("guardhouse", "inspection")]
        tier = self.M["meta"].get("wall_defense", "garrison")
        max_spacing = wall_tower_spacing_px(1.0 / self.ftpx, tier) * 0.85  # margin so a slide off a kido does not push a neighbor gap past the range
        perim = self._wall_perimeter(pts)
        placed_tw = list(gate_towers)  # every tower placed so far (min-separation + coverage anchors)

        def _seat_mural(arc: float) -> None:
            vx, vy, ta_i = self._wall_point_at_arc(pts, arc)
            if any(math.hypot(vx - gx, vy - gy) < 45 for gx, gy in gates) or any(math.hypot(vx - wx2, vy - wy2) < 40 for wx2, wy2 in water_gates):
                return  # sits IN the gate / water-gate opening itself - the gate tower owns that spot

            # SLIDE off a kido spot (a ward gate on the wall - avoid OVERLAP only, ~32px), the gate furniture,
            # or too-close to an existing tower. At siege density a mural sits happily beside a kido.
            def _blocked(px: float, py: float) -> bool:
                # tower-to-tower separation floors at 0.75x the tier's spacing cap (was a flat 28px,
                # which let a coverage-remediation seat land 32px from a 55px-rhythm neighbor - the
                # Tango doubled-tower artifact, GM 2026-07-23). 0.75x cap stays strictly tighter than
                # the wall_towers_evenly_spaced gate (0.7x median; the median never exceeds the cap),
                # and never blocks a genuine hole-fill: a coverage-thin run only exists in a span
                # wider than 2x the arrow radius, whose midpoint clears the floor at every tier. The
                # 28px floor survives for extreme-dense postures. Rejected seats fall to the slide
                # fan, which walks them toward the local span midpoint - restoring the rhythm.
                return (
                    # 32, NOT the even-fill's KIDO_TOWER_KEEPCLEAR (62): a remediation seat exists
                    # because that run is coverage-thin, and widening this band to 62 was tried
                    # (2026-07-26) - it dropped a legitimate tower 45px from Nagahara's SW ward
                    # junction, which cleared the kido glyph by ~9px, and left a curtain point just
                    # OUTSIDE the exempt band uncovered. The kido's own glyph is what a tower must
                    # not sit on, and s.kido enforces that from its side by seating the guard box on
                    # whichever flank of the opening is clear of the towers already standing.
                    any(math.hypot(px - kx_, py - ky_) < 32 for kx_, ky_ in tower_skip)
                    or any(math.hypot(px - fx_, py - fy_) < 40 for fx_, fy_ in gate_furn)
                    or any(math.hypot(px - tx_, py - ty_) < max(28.0, 0.75 * max_spacing) for tx_, ty_ in placed_tw)
                )

            if _blocked(vx, vy):
                for da in (22, -22, 34, -34, 46, -46):
                    sx_, sy_, se_ = self._wall_point_at_arc(pts, arc + da)
                    if not _blocked(sx_, sy_) and all(math.hypot(sx_ - gx, sy_ - gy) >= 45 for gx, gy in gates):
                        vx, vy, ta_i = sx_, sy_, se_
                        break
                else:
                    return  # boxed in - drop this one (the coverage check tolerates a rare short gap; posture is a floor, not a mandate to force a bad tower)
            nvx, nvy = _berm_nudge(vx, vy, self.px(40))
            self._tower(nvx, nvy, ta_i, wc)
            placed_tw.append((vx, vy))

        if gate_towers:
            anchors = sorted(self._wall_arc_of(pts, gt) for gt in gate_towers)
        else:
            anchors = [0.0]  # no gate towers (unusual) - start the even ring at vertex 0
            _seat_mural(0.0)
        for gi in range(len(anchors)):
            a0 = anchors[gi]
            a1 = anchors[(gi + 1) % len(anchors)] + (perim if gi == len(anchors) - 1 else 0.0)
            gap = a1 - a0
            k = max(0, math.ceil(gap / max_spacing) - 1)  # mural towers to insert so each sub-gap <= max_spacing
            for j in range(1, k + 1):
                _seat_mural(a0 + gap * j / (k + 1))
        # COVERAGE REMEDIATION: a slide off a kido can leave a NEIGHBOURING gap just over range; sweep the
        # curtain and drop an extra mural into the middle of any run of points still short of the tier's
        # coverage. This is what turns "spacing <= range" into "coverage >= min everywhere" even after slides.
        _rng_ft, _mincov = WALL_DEFENSE.get(tier, WALL_DEFENSE["garrison"])
        _Rpx = _rng_ft / self.ftpx + 12.0  # +12 px: a mamian's half-footprint - an archer shoots from the tower's span, not its center point (matches the coverage check)
        for _pass in range(5):
            _nst = max(8, int(perim / 10))  # finer than the check's 18px sampling, so remediation catches every point the check would flag
            _step = perim / _nst
            _thin = []
            for _si in range(_nst):
                _ra = perim * _si / _nst
                _px, _py, _junk = self._wall_point_at_arc(pts, _ra)
                if any(math.hypot(_px - gx, _py - gy) < 130 for gx, gy in gates) or any(math.hypot(_px - fx_, _py - fy_) < 55 for fx_, fy_ in gate_furn):
                    continue  # inside the gate BARBICAN (gate + guard house + inspection) - a defended complex, exempt from the open-curtain rule
                if sum(1 for tx_, ty_ in placed_tw if math.hypot(_px - tx_, _py - ty_) <= _Rpx + 1) < _mincov:
                    _thin.append(_ra)
            if not _thin:
                break
            _runs: list[list[float]] = []
            for _ra in _thin:
                if _runs and _ra - _runs[-1][-1] <= 2.5 * _step:
                    _runs[-1].append(_ra)
                else:
                    _runs.append([_ra])
            _before = len(placed_tw)
            for _run in _runs:
                # try the midpoint, then quarters, then near the ends - the first that seats widens coverage
                for _frac in (0.5, 0.34, 0.66, 0.2, 0.8):
                    _n0 = len(placed_tw)
                    _seat_mural(_run[0] + (_run[-1] - _run[0]) * _frac)
                    if len(placed_tw) > _n0:
                        break
            if len(placed_tw) == _before:
                break  # nothing placeable this pass - a genuinely blocked stretch (the check will report it)
        self.M["wall"] = [[x, y] for x, y in pts]
        # record the ward-junction keep-clears so the coverage check can exempt the same band
        # placement refuses to tower (see KIDO_TOWER_KEEPCLEAR's why-comment)
        self.M["wall_tower_keepclears"] = [[float(kx), float(ky)] for kx, ky in tower_skip]
        self.M["gates"] = [[gx, gy] for gx, gy in gates]
        if gates:
            self.M["gate"] = [gates[0][0], gates[0][1]]
        self.corridors.append(([(x, y) for x, y in ring], 46))
