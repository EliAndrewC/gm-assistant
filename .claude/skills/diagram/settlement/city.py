"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
from typing import TYPE_CHECKING, Any, cast

from ._geom import (
    CARRIED_LANDING_FLOOR_FT,
    GOVERNOR_CAPTION_FS,
    LANDING_FT,
    PLANK_ABUTMENT,
    PLANK_BANK_REACH,
    PLANK_VILLAGE_REACH,
    Pt,
    point_in_poly,
    quad_hits_poly,
    quad_hits_seg,
    seg_closest,
    seg_dist,
    seg_intersect,
    segments_cross,
)
from ._knobs import KIDO_TOWER_KEEPCLEAR, WALL_DEFENSE, _below_drain, _poly_centroid, _seg_point, bridge_carried_ways, bridge_crossed_waters, moat_swept_tap, wall_tower_spacing_px

if TYPE_CHECKING:
    from .core import Settlement


class CityMixin:
    # ---- provincial-city features (scale="city")
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
        from .core import Settlement  # lazy: runtime class-attr read; top-level import would cycle

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

    def quay(self: Settlement, pts: Any, steps: int = 3, width: float | None = None) -> None:  # type: ignore[misc]
        """A REVETTED QUAY FACE - the bank cut back, faced with stone or timber cribbing, with
        STEPPED LANDINGS notched into it at intervals, and mooring posts along the top.

        WHY THIS AND NOT MORE PIERS (GM 2026-08-11, asking whether three piers was the right
        number for six granaries: "is there some sort of dock that is not a boardwalk... I don't
        know how this would have worked"). Research is in research/cities/river-cities.md, and it
        inverts what a modern marina suggests. **A river's level moves by many feet across the
        year**, so a fixed-height deck is at the right height for a few weeks and wrong the rest -
        unreachable in the dry season, awash in the wet. A flight of steps down a faced bank is
        correct at EVERY level, because the barge simply lies against a different tread. That is
        why the stepped quay is the norm on a river and the projecting pier the exception: the
        Chinese matou is characteristically a stone-stepped landing in a faced bank, and the
        Japanese kashi district uses the same arrangement with the steps called gangi. The pier
        exists for REACH, where the bank shelves too gently for a loaded hull to come alongside.

        So the working face is the BANK, continuous along the frontage, and its capacity is
        measured in feet of mooring rather than in piers - which is why three piers serve six
        granaries perfectly well while a wharf drawn WITHOUT its quay face reads as three fingers
        poking into an otherwise natural riverbank.

        `pts` is the bank line, `steps` how many landings are notched into it. Records M['quays']
        and reserves a shallow corridor so nothing packs onto the working face."""
        if width is None:
            width = max(self.px(10), 2.6)
        dd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        # the faced edge: a stone band, drawn heavier than a path and with a coursing tick every
        # few feet so it reads as revetment rather than as another way
        self.add(f'<path d="{dd}" fill="none" stroke="#8C8377" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="butt"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6E6558" stroke-width="{max(0.8, width * 0.18):.1f}" stroke-linejoin="round" stroke-linecap="butt" opacity="0.8"/>')
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
        total = sum(lens) or 1.0

        def at(d: float) -> tuple[float, float, float, float]:
            acc = 0.0
            for (a, b), sl in zip(segs, lens, strict=True):
                if sl and acc + sl >= d:
                    f = (d - acc) / sl
                    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / sl, (b[1] - a[1]) / sl)
                acc += sl
            a, b = segs[-1]  # pragma: no cover - defensive: every caller below asks for a
            sl = lens[-1] or 1.0  # pragma: no cover   fraction strictly inside the run, so the
            return (b[0], b[1], (b[0] - a[0]) / sl, (b[1] - a[1]) / sl)  # pragma: no cover  loop always matches

        landings = []
        posts = []
        for k in range(max(0, steps)):
            d = total * (k + 0.5) / max(1, steps)
            x, y, tx, ty = at(d)
            nx, ny = -ty, tx  # toward the water; the caller draws the bank with water on this side
            tread = self.px(20)  # a landing wide enough for two porters to pass
            run = self.px(22)
            g = []
            for t in range(4):  # four treads stepping down into the water
                off = width / 2 + run * t / 4.0
                x0, y0 = x + nx * off - tx * tread / 2, y + ny * off - ty * tread / 2
                x1, y1 = x + nx * off + tx * tread / 2, y + ny * off + ty * tread / 2
                g.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#665D50" stroke-width="{max(1.1, self.px(3)):.1f}" stroke-linecap="butt"/>')
            self.add("".join(g))
            landings.append([round(x, 1), round(y, 1)])
        for k in range(max(2, steps + 2)):  # mooring posts along the top of the face
            x, y, tx, ty = at(total * (k + 0.5) / max(2, steps + 2))
            nx, ny = ty, -tx  # landward side
            px_, py_ = x + nx * (width / 2 + self.px(3)), y + ny * (width / 2 + self.px(3))
            self.add(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="{max(0.9, self.px(2)):.1f}" fill="#5A5044"/>')
            posts.append([round(px_, 1), round(py_, 1)])
        self.M.setdefault("quays", []).append({"pts": [[round(x, 1), round(y, 1)] for x, y in pts], "w": round(width, 2), "landings": landings, "posts": posts})
        self.corridors.append(([(x, y) for x, y in pts], width / 2 + 6))

    def aqueduct(self: Settlement, pts: Any, width: float | None = None) -> None:  # type: ignore[misc]
        """The capital's water-supply channel: intake works on the river, an OPEN cut at grade
        outside the wall, terminating at a city gate - and buried beyond it.

        THE FORM IS SETTLED AND THE NEGATIVE IS EXPLICIT (GM 2026-08-08; research/cities/
        capitals.md, "The aqueduct is open outside the wall and buried inside it"). The East
        Asian vocabulary is Edo's Kanda and Tamagawa josui and Odawara's sosui: a gravity canal
        in a plain earth cut (the Kanda ran 43 km at grade), a buried pipe inside the town, and -
        only where water must CROSS water - a kakehi flume carried over on a bridge (Edo's
        Suidobashi, "aqueduct bridge", is named for one; none is needed where the route crosses
        nothing). NO ARCADED AQUEDUCT EXISTS in either anchor tradition: arches are the one form
        the possibility space excludes, so this glyph draws straight cuts only and takes no
        arcade parameter. Past the gate nothing is drawn - the in-wall conduit is honestly
        buried, and what a resident sees of it is its draw-basins (feature 021's, with the
        wells).

        `pts[0]` is the INTAKE on the river, drawn with the sluice vocabulary (paired head-posts
        and a lifted board) so it reads as engineered water rather than a stray stream. Records
        M['aqueducts'] (a list, with intake and terminus); the shared crossing source
        (bridge_crossed_waters) reads it, so any way crossing the cut demands a deck like any
        other watercourse."""
        if width is None:
            width = max(self.px(10), 3.0)  # a ~10 ft supply cut - far below the 36 ft cargo canal
        dd = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        # the bank lines first, then the water on top: a narrow cut reads from its earthwork
        # edges. GLYPH CONVENTION, not scale (GM 2026-08-09): the true berms of a 10 ft cut
        # would draw ~1 px of pale tan and vanish, so the banks render DARKER and WIDER than
        # life - masonry brown, ~2 px of reveal per side - exactly as a wellhead draws at `vr`
        # over its true `r`. The to-scale rule governs the WATER (the feature); the banks are
        # the glyph's legibility furniture.
        self.add(f'<path d="{dd}" fill="none" stroke="#7A6A48" stroke-width="{width + 4.4:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
        ia = math.degrees(math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0]))
        hp = max(self.px(3), 2.0)  # head-post ~3 ft square
        span = width / 2 + hp + 1
        g = [f'<g transform="translate({pts[0][0]:.1f},{pts[0][1]:.1f}) rotate({ia:.1f})">']
        for sy in (-span, span - hp):
            g.append(f'<rect x="{-hp / 2:.1f}" y="{sy:.1f}" width="{hp:.1f}" height="{hp:.1f}" fill="#6B5A3C"/>')
        g.append(f'<line x1="0" y1="{-span:.1f}" x2="0" y2="{span:.1f}" stroke="#6B5A3C" stroke-width="1.6"/>')
        g.append("</g>")
        self.add("".join(g))
        # the TERMINAL BASIN at the gate end: the settling tank where the open cut ends and the
        # buried in-wall pipe begins (Edo's josui ended in exactly such head-tanks). Without it
        # the cut just stops - or worse, reads as a brook spilling into the moat (GM 2026-08-09).
        tb = max(self.px(16), 5.0)
        ta = math.degrees(math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]))
        self.add(
            f'<g transform="translate({pts[-1][0]:.1f},{pts[-1][1]:.1f}) rotate({ta:.1f})">'
            f'<rect x="{-tb / 4:.1f}" y="{-tb / 2:.1f}" width="{tb:.1f}" height="{tb:.1f}" rx="1" fill="#9CB4C8" stroke="#6B5A3C" stroke-width="1.4"/>'
            f"</g>"
        )
        self.M.setdefault("aqueducts", []).append(
            {
                "poly": [[round(px_, 1), round(py_, 1)] for px_, py_ in pts],
                "w": round(width, 2),
                "intake": [round(pts[0][0], 1), round(pts[0][1], 1)],
                "to": [round(pts[-1][0], 1), round(pts[-1][1], 1)],
            }
        )
        self.corridors.append(([(px_, py_) for px_, py_ in pts], width / 2 + 10))

    def dock(self: Settlement, cx: float, cy: float, w: float, h: float) -> Pt:  # type: ignore[misc]
        """An in-city DOCK BASIN at the head of the cargo canal - a rectangular cut of open water
        with a stone quay lip, where the barges tie up (the Jiangnan water-city pattern). Records
        M['docks']; blocks placement so the merchant rows leave the quay clear."""
        self._water(
            f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="#9CB4C8"/>',
            {},
            sheen=f'<rect x="{cx - w / 2 + 4:.0f}" y="{cy - h / 2 + 4:.0f}" width="{w - 8}" height="{h - 8}" rx="2" fill="#B6CAD8" opacity="0.5"/>',
        )
        self.add(f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="3" fill="none" stroke="#7A6A48" stroke-width="2.2"/>')
        self.M.setdefault("docks", []).append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0})
        self.placed.append((cx, cy, w + 14, h + 14))
        return (cx, cy)

    def jetty(self: Settlement, x: float, y: float, rot: float = 0.0, length: float | None = None) -> int:  # type: ignore[misc]
        """A timber JETTY - a planked finger running out from the riverbank into the water, where
        the river craft moor (the wharf suburb outside a river city's water-side gate). Drawn in
        the TOP layer over the water; records M['jetties']."""
        if length is None:
            length = self.px(60)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="0" y="-3.2" width="{length:.0f}" height="6.4" fill="#B0905E" stroke="#59431F" stroke-width="1.1"/>')
        for px_ in range(6, int(length), 9):
            g.append(f'<line x1="{px_}" y1="-3" x2="{px_}" y2="3" stroke="#59431F" stroke-width="0.7" opacity="0.6"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("jetties", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "len": round(length, 1), "z": z})
        return z

    def log_boom(self: Settlement, x: float, y: float, rot: float = 0.0, length: float | None = None, width: float | None = None, label: str | None = "log boom", label_xy: Pt | None = None) -> int:  # type: ignore[misc]
        """A LOG BOOM - a shore-fast holding pen for rafted timber at a river port whose main trade
        is TIMBER: a cabled chain of floating logs anchored to the bank at both ends, enclosing a
        strip of water packed with raft-mats between the chain and the shore.

        WHY THIS EXISTS (GM 2026-07-26). A timber city drawn with only a lumber yard and jetties gets
        the same river vocabulary as any other river town: the yard says "someone sells wood", not
        "this is a timber river". Logs came DOWN the water loose or rafted and had to be held at the
        mill or yard until they were pulled out, and the holding pen is the boom - the one piece of
        river furniture that is specific to the trade. Minami is where it matters: l7r.md has Fox
        charcoal burners outnumbering farmers and "significantly more" timber going downriver than
        the ~10,000 koku/yr moved by cart, so the boom is not decoration but the largest working
        thing on the city's water.

        WHY IT IS A PEN AGAINST THE BANK, NOT A LINE IN THE STREAM (GM 2026-08-02, "it just looks
        like a bunch of logs in the middle of the river"; the research is in
        research/urban-features.md, "The log boom"). A boom is a floating FENCE - anchored to
        nothing it holds nothing. Attested booms anchor to fixed ground (bank abutments, stone-
        filled cribs, driven piles) and run ALONG a navigated river, the pen between chain and
        shore, with the fairway kept clear by law; only a loose-log CATCH boom on an unnavigated
        reach ever spans the water (the Kiso tsunaba at the gorge mouth), and that is upstream
        lore, not port furniture. And the held stock is MASS - attested pens are measured in
        thousands of logs packed edge to edge - so the pen draws as a near-solid mat of raft
        strips, never scattered sticks.

        Local frame: `length` runs along the bank (local x), the pen is `width` across (local y,
        default ~40 real ft - about a third of a 120 ft channel), and THE BANK LIES ON THE LOCAL
        +y SIDE - orient `rot` so +y faces the shore. The chain draws on the -y (offshore) edge,
        short end-booms close the pen, mooring posts sit at the bank corners and pile clusters at
        the chain. The checks (log_boom_moored_to_the_bank / log_boom_leaves_the_fairway /
        log_boom_serves_the_lumber_yard) derive the pen quad from the recorded x/y/rot/len/pen_w
        under this same convention. Drawn in the TOP layer OVER the water, like a jetty deck - it
        floats, so overlapping the river is the whole point (OVERLAP_CLASS FIXTURE,
        _OVERLAP_EXEMPT). Records M['log_booms']."""
        if length is None:
            length = self.px(330)
        if width is None:
            width = self.px(40)
        hl, hp = length / 2, width / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        # the held stock first, so the chain reads as holding it in: raft-mats packed nearly solid
        # between chain and shore (sparse sticks read as debris - the attested pens hold thousands)
        # each strip is drawn as an OUTLINED log - a dark underlay a hair wider than the lighter
        # log tone over it - so the dark rims and butt gaps resolve into individual timbers to the
        # eye (GM 2026-08-03: the first solid mat read as one brown mass, "hard to pick out
        # individual logs"); runs kept short (~18-36 real ft) for the same reason
        n_rows = max(4, round((width - 3.2) / 2.05) + 1)
        for r in range(n_rows):
            ry = -hp + 1.6 + r * (width - 3.2) / max(1, n_rows - 1)
            pos = -hl + 2.6 + 1.7 * ((r * 7) % 3)
            while pos < hl - 3.6:
                run = 9.0 + 3.0 * math.sin(r * 3.1 + pos * 0.13)
                end = min(pos + run, hl - 2.6)
                tone = "#7A5B33" if (r + int(pos)) % 2 else "#85643B"
                g.append(f'<line x1="{pos:.1f}" y1="{ry:.1f}" x2="{end:.1f}" y2="{ry:.1f}" stroke="#4A3A22" stroke-width="2.0" stroke-linecap="round" opacity="0.9"/>')
                g.append(f'<line x1="{pos + 0.4:.1f}" y1="{ry:.1f}" x2="{end - 0.4:.1f}" y2="{ry:.1f}" stroke="{tone}" stroke-width="1.2" stroke-linecap="round" opacity="0.95"/>')
                pos = end + 1.5

        # the pen fence: logs cabled end to end (stubby round-ended timbers over a cable line),
        # along the offshore edge and closing both short ends back to the bank
        def chain(x0: float, y0: float, x1: float, y1: float) -> None:
            n_seg = max(2, int(math.hypot(x1 - x0, y1 - y0) / 9.0))
            g.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#4A3A22" stroke-width="0.8" opacity="0.8"/>')
            for i in range(n_seg):
                t0, t1 = (i + 0.06) / n_seg, (i + 0.88) / n_seg
                g.append(
                    f'<line x1="{x0 + (x1 - x0) * t0:.1f}" y1="{y0 + (y1 - y0) * t0:.1f}" x2="{x0 + (x1 - x0) * t1:.1f}" y2="{y0 + (y1 - y0) * t1:.1f}" stroke="#8A6B42" stroke-width="4.2" stroke-linecap="round"/>'
                )
                g.append(
                    f'<line x1="{x0 + (x1 - x0) * t0:.1f}" y1="{y0 + (y1 - y0) * t0:.1f}" x2="{x0 + (x1 - x0) * t1:.1f}" y2="{y0 + (y1 - y0) * t1:.1f}" stroke="#59431F" stroke-width="0.7" opacity="0.55"/>'
                )

        chain(-hl, -hp, hl, -hp)
        chain(-hl, hp, -hl, -hp)
        chain(hl, hp, hl, -hp)
        # anchorage - a floating fence is only as strong as its fixed ground: mooring posts at the
        # bank corners, pile clusters at the chain's corners and mid-run
        for cx_, cy_ in ((-hl, hp), (hl, hp)):
            g.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="1.8" fill="#4A3A22"/>')
        for cx_ in (-hl, 0.0, hl):
            for dx_, dy_ in ((-1.6, 0.0), (1.4, -1.0), (0.6, 1.4)):
                g.append(f'<circle cx="{cx_ + dx_:.1f}" cy="{-hp + dy_:.1f}" r="1.1" fill="#59431F"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        # record TRUE unrotated dims (w = along-bank length, h = pen width) with rot, exactly as a
        # building does - the matrix extractor rotates x/w/h records by `rot` itself, so recording a
        # rotation-FOLDED bounding box here double-rotates into a phantom footprint (that phantom
        # put the pen "on" Minami's lumber yard 42px away, 2026-08-02)
        self.M.setdefault("log_booms", []).append(
            {"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "len": round(length, 1), "pen_w": round(width, 1), "w": round(length, 1), "h": round(width, 1), "z": z}
        )
        if label:
            th = math.radians(rot)
            aabb_h = abs(math.sin(th)) * length + abs(math.cos(th)) * width
            lx, ly = label_xy if label_xy else (x, y + aabb_h / 2 + 12)
            self.label(lx, ly, label, 9, italic=True, color="#5A4326")
        return z

    def bridge(self: Settlement, x: float, y: float, rot: float, span: float, deck_w: float) -> int:  # type: ignore[misc]
        """A timber BRIDGE carrying a road (or town street) over a watercourse - a stream, an
        irrigation channel, or the city moat at a gate. Centered on the crossing (x, y); the deck
        runs along `rot` (the road's bearing, degrees) for `span` px (long enough to reach both
        banks) and is `deck_w` wide (the carried road's width). Drawn on the TOP layer so it sits
        ABOVE the water and the roadbed. Records M['bridges']."""
        # ONE DECK PER CROSSING, enforced HERE so every caller is covered (GM 2026-07-26): the
        # road-crossing pass in bridges(), the plank pass in channel_footbridges(), and any gen that
        # hand-places a deck for a crossing one of those also finds. Minami carried two decks over the
        # Hayakawa 3px apart, and honda/hoshigaoka/kikuta each carried two footplanks at the SAME
        # point - a way that crosses a stream where a channel joins it is one bridge on the ground.
        # None of it was caught because bridges were invisible to the overlap matrix (FIXTURE was a
        # blanket permission); bridges x bridges is a violation now. Tolerance scales with the deck so
        # two genuinely distinct footplanks a few px apart still both draw.
        _btol = max(4.0, min(12.0, span * 0.5))
        for _b in self.M.get("bridges", []):
            if math.hypot(_b["x"] - x, _b["y"] - y) <= _btol:
                return int(_b["z"])
        hl, hw = span / 2, deck_w / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hl:.1f}" y="{-hw:.1f}" width="{span:.1f}" height="{deck_w:.1f}" rx="2" fill="#B68D5A" stroke="#5A3F1E" stroke-width="1.6"/>')  # the planked timber deck
        step = max(7, span / 8)  # plank seams across the deck
        sx = -hl + step
        while sx < hl - 1:
            g.append(f'<line x1="{sx:.1f}" y1="{-hw:.1f}" x2="{sx:.1f}" y2="{hw:.1f}" stroke="#5A3F1E" stroke-width="0.7" opacity="0.55"/>')
            sx += step
        g.append(f'<rect x="{-hl:.1f}" y="{-hw - 2.4:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')  # the two side rails
        g.append(f'<rect x="{-hl:.1f}" y="{hw - 0.2:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("bridges", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1), "span": round(span, 1), "w": round(deck_w, 1), "z": z})
        return z

    def bridges(self: Settlement) -> int:  # type: ignore[misc]
        """Auto-span every place a way CROSSES a watercourse with a s.bridge(), oriented ALONG the
        way. Call AFTER all ways (road, ring road, streets, lanes) AND all water (streams, channels,
        the cargo canal, the moat) are placed - a watercourse added later would leave an unbridged
        crossing (which the `roads_bridge_water` check then flags). Returns the number of bridges
        drawn. Historically a walled city's approach road crossed the moat on a bridge at each gate,
        and a country road crossed a stream on a timber bridge.

        SOLVE THE CROSSING, NEVER EYEBALL IT (GM 2026-07-27, Minami's cargo-basin bridge). A deck
        hand-placed at design coordinates goes crooked and slides off its crossing the moment the
        geometry around it is re-derived: Minami's canal bridge sat 17 px east of where the ring
        road actually met the canal and 39 deg off its bearing, so the road simply ran through the
        water beside it (Nagahara's was 15 px / 24 deg off, the same way). Both were hand-placed
        because this pass could not SEE the crossing - the RING ROAD was not a carried way here and
        the cargo CANAL was not a watercourse - so both are scanned now, and the checks
        `roads_bridge_water` + `bridges_align_with_their_way` re-derive the same crossings from the
        manifest. Anything this pass finds is aligned by construction; hand-place a deck only for a
        crossing this pass genuinely cannot see, and expect the alignment check to test it."""
        carried = bridge_carried_ways(self.M)
        waters = bridge_crossed_waters(self.M)
        n = 0
        for rpts, rw in carried:
            for i in range(len(rpts) - 1):
                ra, rb = tuple(rpts[i]), tuple(rpts[i + 1])
                for wpts, ww in waters:
                    for j in range(len(wpts) - 1):
                        wa, wb = tuple(wpts[j]), tuple(wpts[j + 1])
                        if segments_cross(ra, rb, wa, wb):
                            # segments_cross is True only for a genuine (non-parallel) crossing, so
                            # seg_intersect always returns a point here
                            p = cast(Pt, seg_intersect(ra, rb, wa, wb))
                            rot = math.degrees(math.atan2(rb[1] - ra[1], rb[0] - ra[0]))
                            # The span SOLVES the oblique crossing (GM 2026-08-09: the old flat
                            # +28px slack was eaten by obliquity and left deck CORNERS at the
                            # water's edge). Along the deck the water is ww/sin wide, the deck's
                            # own width adds rw*|cos|/sin before a corner clears the bank, and
                            # past that every corner runs LANDING_FT of real feet onto dry
                            # ground (see the constant for the research). sin is clamped:
                            # segments_cross guarantees a genuine crossing, but a near-parallel
                            # graze would otherwise ask for an absurd deck.
                            _rl = math.hypot(rb[0] - ra[0], rb[1] - ra[1]) or 1.0
                            _wl = math.hypot(wb[0] - wa[0], wb[1] - wa[1]) or 1.0
                            _cs = ((rb[0] - ra[0]) * (wb[0] - wa[0]) + (rb[1] - ra[1]) * (wb[1] - wa[1])) / (_rl * _wl)
                            _sn = max(math.sqrt(max(0.0, 1.0 - _cs * _cs)), 0.25)
                            _span = (ww + rw * abs(_cs)) / _sn + 2 * LANDING_FT / self.ftpx
                            # ...AND THE DECK IS GROWN UNTIL ITS CORNERS ACTUALLY CLEAR THE WATER
                            # (2026-08-12). The formula above solves the crossing against the ONE
                            # segment the way cuts, and clamps sin at 0.25 so a near-parallel graze
                            # cannot ask for an absurd deck. Both are reasonable and both under-size
                            # a deck where the watercourse BENDS near the crossing: the check
                            # (`bridges_span_their_water`) measures every corner against the whole
                            # crossed POLYLINE, so a neighbouring segment curving back toward a
                            # corner is water the formula never saw. Rather than model that, ask the
                            # same question the check asks and lengthen until the answer is yes.
                            _need = ww / 2 + CARRIED_LANDING_FLOOR_FT / self.ftpx  # the check's own carried-way floor
                            _rr = math.radians(rot)
                            _cu, _su = math.cos(_rr), math.sin(_rr)
                            for _grow in range(14):
                                _try = _span * (1.0 + 0.12 * _grow)
                                if all(
                                    min(
                                        seg_dist(p[0] + _qu * _cu * _try / 2 - _qv * _su * rw / 2, p[1] + _qu * _su * _try / 2 + _qv * _cu * rw / 2, wpts[k2], wpts[k2 + 1])
                                        for k2 in range(len(wpts) - 1)
                                    )
                                    >= _need
                                    for _qu, _qv in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                                ):
                                    _span = _try
                                    break
                            self.bridge(p[0], p[1], rot, _span, rw)
                            n += 1
        return n

    def channel_footbridges(self: Settlement, spacing: float = 320, min_len: float = 140, plank_w: float = 2.0, seg_caps: Any = None) -> int:  # type: ignore[misc]
        """Standalone plank FOOTBRIDGES across the irrigation channels, where field-workers cross a ditch while
        walking the paddy bunds - NOT carried by any lane (people reach them along the earthen bunds, so no
        path leads to them). Any ditch stretch longer than `min_len` gets a plank about MIDWAY; a long stretch
        gets one roughly every `spacing` px, evenly spaced along it. Each plank crosses PERPENDICULAR to the
        ditch, spanning its local width plus a short abutment. Call AFTER the field ditches are recorded. Bridges
        draw on the TOP layer (over the water). Records via `bridge()` into M['bridges'] (tagged 'foot'); returns
        the count. DECK WIDTH (1 px = 2 ft): a dobashi footplank is a single-file crossing (~3-4 ft), so
        `plank_w=2.0` (~4 ft, GM 2026-07-22: was 2.5) - kept just wide enough to read and NARROWER than a cart
        lane (~5-6 px); the wider `bridges()` carried-way deck matches the lane it carries, but a footplank does not.
        USEFULNESS: a plank is placed only where BOTH banks reach ground someone walks to - cultivated field,
        the village, or a dike (via _plank_reaches_useful_ground). A drain/toe stretch whose far bank opens onto
        marsh/scrub/off-map carries NO plank (GM 2026-07-22, Hikari no Sato: crossings into the reed marsh)."""

        def _at(pts: Any, seg: Any, s: float) -> Any:  # point + heading (deg) at arc-length s along the polyline
            acc = 0.0
            for i, sl in enumerate(seg):
                if acc + sl >= s or i == len(seg) - 1:
                    fr = (s - acc) / sl if sl else 0.0
                    ax, ay = pts[i]
                    bx, by = pts[i + 1]
                    return (ax + (bx - ax) * fr, ay + (by - ay) * fr, math.degrees(math.atan2(by - ay, bx - ax)))
                acc += sl

        def _corners(cx: float, cy: float, w: float, h: float, deg: float) -> list[Pt]:
            a = math.radians(deg)
            ca, sa = math.cos(a), math.sin(a)
            return [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

        def _sat(p: Any, q: Any) -> bool:  # separating-axis rect overlap (matches bridges_clear_of_houses)
            for poly in (p, q):
                for i in range(4):
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % 4]
                    nx, ny = -(y2 - y1), (x2 - x1)
                    pa = [nx * x + ny * y for x, y in p]
                    qa = [nx * x + ny * y for x, y in q]
                    if max(pa) < min(qa) or max(qa) < min(pa):
                        return False
            return True

        houses = [_corners(h["x"], h["y"], h["w"], h["h"], h.get("rot", 0)) for h in self.M.get("houses", [])]
        n0 = len(self.M.get("bridges", []))
        # THREE MORE THINGS A PLANK SLIDES AWAY FROM (2026-08-11, found by rolling cohorts of
        # scripted hamlets - the shipped maps' ditches happen to run clear of all three):
        #
        #  - a DRY CROP PLOT. The slide already avoids houses; a deck laid across a hem strip is a
        #    board lying on the barley, and it is the same rule (`groves_clear_of_dry_plots` states
        #    it for trees, `structures_clear_of_dry_plots` for buildings). This became checkable at
        #    all only once `draw_comb_field` started registering its hem in `dry_polys`.
        #  - ANOTHER BRIDGE. Two planks drawn on top of each other is a drawing error, and it
        #    happens where two ditches run close and each independently wants a crossing at the
        #    same slot. `features_do_not_overlap` reads it as a ('bridges', 'bridges') pair.
        #  - A CONFLUENCE, where the deck is instead made LONGER. The span is sized from THIS
        #    ditch's nominal width, but where another watercourse joins, the water under the deck is
        #    the WIDER one - so a nominal deck comes up short and its abutment stands in the water
        #    (`bridges_span_their_water`). Skipping such spots was tried first and is too strong: on
        #    a drain whose banks are reed marsh for all but one short stretch, the only point with
        #    useful ground on both banks IS a junction, so the map ended up with a long ditch and no
        #    crossing (`long_ditches_have_a_footbridge`) - two correct rules forbidding between them
        #    a plank that ought to exist. A plank at a junction is simply a longer plank, which is
        #    what a farmer would lay, so the deck is sized to the widest water actually beneath it.
        dry_quads = [list(poly) for poly in self.dry_polys]
        DEFAULT_W = {"streams": 9.0, "channels": 2.5, "field_ditches": 4.2}
        # ...including the OTHER FIELD DITCHES, which is where the confluences actually are: a comb's
        # branch takes off from a main, and the plank the branch wants at its own head sits over the
        # junction where the water is the main's width, not the branch's. Listing only streams and
        # channels missed every one of them.
        # NOT `drawn_channels`: it holds the filleted twin of every course including the one being
        # planked, and `wl is pts` cannot exclude a twin, so every candidate then reads as sitting at
        # a confluence with itself. Tried 2026-08-11; it made both footbridge checks fail at once.
        other_water = [(rec.get("poly") or rec.get("pts"), float(rec.get("w") or DEFAULT_W[key])) for key in ("streams", "channels", "field_ditches") for rec in self.M.get(key, []) or []]
        for d in self.M.get("field_ditches", []):
            pts = d["poly"]
            seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            total = sum(seg)
            if total < min_len:
                continue  # a short stub (e.g. the head-race) is stepped over, no plank
            n = max(1, round(total / spacing))
            # SIDE-AWARE crossings (research 2026-07-22): on a polder the ring-canal `seg` tag caps crossings
            # per side - they cluster on the SETTLEMENT (east) toe, sparse on the interior laterals, NONE on
            # the unsettled feeder / far toe / drain (people cross to the fields where they live, then walk the
            # bund network). `seg_caps` maps seg -> max planks (0 = none); an untagged ditch uses the spacing.
            if seg_caps is not None and d.get("seg") in seg_caps:
                cap = seg_caps[d["seg"]]
                if cap <= 0:
                    continue
                n = min(n, cap)
            w = d.get("w", 4.2)
            span = w + PLANK_ABUTMENT  # deck = local ditch width + a short abutment each bank
            for k in range(n):
                base = (k + 0.5) / n * total  # midway for n=1, evenly spaced otherwise
                # SLIDE along the ditch to a spot that (a) misses every home and (b) lands on
                # useful ground (field/village/dike) on BOTH banks. If no such spot is near this
                # slot - a marsh/scrub toe stretch with nothing to cross to - it carries NO plank.
                # THE SLIDE SAMPLES AT THE CHECK'S RESOLUTION, in arc length, not in fractions.
                #
                # `long_ditches_have_a_footbridge` decides a ditch needs a plank by walking it in
                # steps of max(8, length/40) and asking whether ANY point has useful ground on both
                # banks. The placer used a handful of fractional offsets, which on a long ditch is a
                # far coarser grid - so on a drain whose banks are marsh for all but one short
                # stretch, the check found the one good point and the placer stepped over it, and
                # the map failed for a plank that was legal and simply never tried. Same discipline
                # as reading the same manifest source: placement and its check must also LOOK at the
                # same resolution, or one of them is answering a different question.
                _step = max(8.0, total / 40)
                for frac in sorted((k * _step / total for k in range(-int(total / 2 / _step), int(total / 2 / _step) + 1)), key=abs):
                    px, py, ang = _at(pts, seg, max(0.0, min(total, base + frac * total)))
                    deck = ang + 90  # deck runs ACROSS the ditch (perpendicular)
                    quad = _corners(px, py, span, plank_w, deck)
                    # WIDEN the deck to the widest water actually under it, then re-cut the quad:
                    # a plank at a junction spans the junction. Tested as "another course runs UNDER
                    # this deck", not "another course passes within a deck's length" - the looser
                    # form catches a ditch merely running parallel to a neighbor.
                    _da = math.radians(deck)
                    _dux, _duy = math.cos(_da), math.sin(_da)
                    under = []
                    for wl, ow in other_water:
                        if wl is pts:
                            continue
                        for i2 in range(len(wl) - 1):
                            if not quad_hits_seg(quad, tuple(wl[i2]), tuple(wl[i2 + 1]), 3.0):
                                continue
                            _wx, _wy = wl[i2 + 1][0] - wl[i2][0], wl[i2 + 1][1] - wl[i2][1]
                            _wl = math.hypot(_wx, _wy) or 1.0
                            _sin = abs(_dux * _wy / _wl - _duy * _wx / _wl)  # deck-vs-course crossing angle
                            _cos = abs(_dux * _wx / _wl + _duy * _wy / _wl)
                            # THE CHECK'S OWN GEOMETRY, not the shorthand in its message. It requires
                            # every deck CORNER to stand at least `cw/2 + floor` from the crossed
                            # course's centerline (floor = 2 real ft for a footplank), so at a
                            # crossing angle t the deck's half-length must exceed that over sin(t) -
                            # i.e. the whole span is (cw + 2*floor + deck_w*|cos|) / sin. Deriving it
                            # from the message's "(width + deck_w*|cos|)/sin plus a landing" leaves
                            # the landing UNDIVIDED by sin and comes up short on a shallow crossing,
                            # which is precisely the case this exists for.
                            under.append((ow + 2.0 * (2.0 / self.ftpx) + plank_w * _cos) / max(_sin, 0.02) + 1.0)
                    span_here = max([span] + under)
                    if span_here > 3.0 * span:
                        continue  # too oblique to plank: widen where a longer deck is reasonable, but a
                        # crossing that needs three times the nominal span is a course running nearly
                        # ALONGSIDE this one, and the answer there is to cross somewhere else. (The fine
                        # arc-length slide above is what makes "somewhere else" reliably available.)
                    quad = _corners(px, py, span_here, plank_w, deck)
                    if any(_sat(quad, hc) for hc in houses):
                        continue
                    if any(quad_hits_poly(quad, dp) for dp in dry_quads):
                        continue  # no plank laid across the hem crop
                    if any(_sat(quad, _corners(b["x"], b["y"], b.get("span", 8.0), b.get("w", 4.0), b.get("rot", 0.0))) for b in self.M.get("bridges", [])):
                        continue  # ...nor on top of another deck
                    # ...tested on the EXACT numbers that will be recorded. `footbridges_reach_useful_ground`
                    # re-derives the bank points from the span and rot in the manifest, which `bridge()`
                    # rounds to 1 dp, while this used the unrounded values - and a bank sample sitting on
                    # the 55 px village reach flips between the two (a scripted-cohort hamlet, 2026-08-13:
                    # bank at 55.0 from the nearest house; placement said useful, the check said marsh).
                    # A MARGIN IS THE WRONG CURE HERE and was tried first: sampling further out is not
                    # strictly stricter, because past a strip of scrub the sample can land back INSIDE the
                    # field, so the wider test PASSED the very plank the check rejects. Rounding the inputs
                    # the same way the manifest does makes the two sides bit-identical, which is the only
                    # thing that actually settles a knife-edge. Measured on the plank that motivated it:
                    # bank-to-house 54.97 px at placement against 55.02 at the end, threshold 55.0 - and
                    # the 0.05 px came from `bridge()` rounding the deck's recorded POSITION, not its span.
                    if not self._plank_reaches_useful_ground(round(px, 1), round(py, 1), round(deck, 1), round(span_here, 1)):
                        continue
                    # AND EVERY CORNER LANDS PAST THE BANK - the exact test
                    # `bridges_span_their_water` will make, on the same geometry, before the deck is
                    # committed rather than after. A deck perpendicular to a STRAIGHT ditch clears by
                    # construction, which is why this was not needed for years; a deck at a BEND does
                    # not, because the polyline curves back toward one of its corners. (`w`/2 + 2 real
                    # ft is the check's own floor for a footplank.)
                    # Measured against `bridge_crossed_waters`, which is where the CHECK reads its
                    # geometry - the DRAWN, filleted polyline, not the recorded one `field_channel`
                    # was handed. Testing the recorded line looked right and rejected nothing,
                    # because the fillet is exactly what curves back toward the corner.
                    _seat = None
                    _cw = 0.0
                    for _wp, _ww in bridge_crossed_waters(self.M):
                        if min(seg_dist(px, py, _wp[i3], _wp[i3 + 1]) for i3 in range(len(_wp) - 1)) <= _ww / 2 + 2 and _ww > _cw:
                            _seat, _cw = _wp, _ww
                    if _seat is not None:
                        _need = _cw / 2 + 2.0 / self.ftpx
                        _dr = math.radians(deck)
                        _cux, _cuy = math.cos(_dr), math.sin(_dr)
                        if any(
                            min(
                                seg_dist(px + su * _cux * span_here / 2 - sv * _cuy * plank_w / 2, py + su * _cuy * span_here / 2 + sv * _cux * plank_w / 2, _seat[i3], _seat[i3 + 1])
                                for i3 in range(len(_seat) - 1)
                            )
                            < _need
                            for su, sv in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                        ):
                            continue  # pragma: no cover - the corner rejection. It fires on real geometry (a scripted-cohort hamlet's branch ditch, whose gentle curve brought a deck corner back within the water at the ditch's head) but no pool map and no synthetic bed reproduces it: every fixture tried either finds a clear offset first or fails the useful-ground test before reaching here. The guard stays - the case it prevents shipped.
                    self.bridge(px, py, deck, span_here, plank_w)
                    self.M["bridges"][-1]["foot"] = True  # a standalone footplank (checked by footbridges_reach_useful_ground)
                    break
        return len(self.M["bridges"]) - n0

    def _plank_reaches_useful_ground(self: Settlement, px: float, py: float, deck_deg: float, span: float) -> bool:  # type: ignore[misc]
        """A STANDALONE footplank is worth building only if BOTH banks reach ground someone walks to:
        cultivated field (wet paddy or dry crop), the village (a dwelling within a short reach), or a
        walked polder-dike crest. A crossing whose far bank opens onto reed marsh, scrub commons, forest,
        or off-map serves no one - field-workers cross a ditch to reach the FIELD, not to wade into the
        bog (GM 2026-07-22, Hikari no Sato: drain-toe planks that stepped straight into the reed marsh).
        The deck spans the ditch along `deck_deg`, so its two ends ARE the two banks; each is sampled a
        short reach past its abutment. See the footbridges_reach_useful_ground check in check_village.py."""
        a = math.radians(deck_deg)
        ux, uy = math.cos(a), math.sin(a)
        reach = span / 2 + PLANK_BANK_REACH
        # read the SAME cultivation source the footbridges_reach_useful_ground check reads (the manifest
        # field outlines + dry plots), so placement and check never disagree - self.field_polys is a
        # separate blocking-only list that some gens leave empty.
        crop = [f["outline"] for f in self.M.get("fields", []) if f.get("outline")]
        crop += [d["poly"] for d in self.M.get("dry_plots", [])]
        dikes = [dk["outline"] for dk in self.M.get("dikes", []) if dk.get("outline")]
        houses = self.M.get("houses", [])
        for sgn in (1.0, -1.0):
            bx, by = px + ux * reach * sgn, py + uy * reach * sgn
            if any(point_in_poly(bx, by, p) for p in crop):
                continue
            if any(point_in_poly(bx, by, p) for p in dikes):
                continue
            if any((bx - h["x"]) ** 2 + (by - h["y"]) ** 2 < PLANK_VILLAGE_REACH**2 for h in houses):
                continue
            return False
        return True

    def governor_mansion(self: Settlement, x: float, y: float, w: float = 320, h: float = 210, label: str = "Governor's Mansion", gate_dir: str = "west") -> Any:  # type: ignore[misc]
        """The provincial governor's walled mansion - a large compound, grander than a county
        magistrate's manor. Reuses the manor glyph (walls + gate + empty court; the interior is
        a separate Mode A diagram) and moves the record to M['governor_mansion'].

        THE CAPTION GOES INSIDE THE COURT, not above the walls like a manor's (GM 2026-08-08).
        The court is deliberately blank - its buildings are a separate Mode A sheet - so it is the
        one patch of guaranteed clear ground on a packed city map, while the band above the walls
        is prime housing: Tango's gen had already worked this out by hand and said so in a comment
        (its reserved caption box "was eating a full housing row"), and Nagahara and Minami took
        the manor default and hung the caption over their samurai quarters. Doing it here makes
        the three cities agree and leaves no hand seat to re-place every time the yamen moves.
        The size is GOVERNOR_CAPTION_FS, which is what makes the caption fit between the walls."""
        self.manor(x, y, w, h, "", gate_dir=gate_dir, gate_ft=18.0)  # a yamen's formal gatehouse passes ~18 real ft; caption below, not manor's
        self.M["governor_mansion"] = self.M["manors"].pop()  # not an outside samurai estate
        self.M["governor_mansion"]["label"] = label
        if label:
            # ~0.36 x the font size below the compound's center puts the glyphs' OPTICAL middle on
            # it (a baseline sits under the x-height, so centering the baseline rides high).
            self.label(x, y + GOVERNOR_CAPTION_FS * 0.36, label, GOVERNOR_CAPTION_FS, weight="bold")
        return self.M["governor_mansion"]
