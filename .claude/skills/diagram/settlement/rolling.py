"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

from ._geom import BUNDLE_PITCH_FT, Indexed, Pt, _signed_area, edge_dist, point_in_poly, seg_dist, segments_cross
from ._knobs import CITY_TIER_SCALES, knob_rng, roll_torii_count, skeleton_layout

if TYPE_CHECKING:
    from .core import Settlement


class RollingMixin:
    def roll_village(  # type: ignore[misc]
        self: Settlement,
        name: str,
        households: int,
        down_deg: float,
        water_kind: str = "pond",
        field_fall: float | None = None,
        offtakes_a: Sequence[float] = (0.22, 0.45, 0.68, 0.88),
        offtakes_b: Sequence[float] = (0.45, 0.8),
        civic_shrine: bool = True,
        frame: bool = True,
        lay_hinterland: bool = True,
    ) -> dict[str, Any]:
        """ROLL a whole gate-passing settlement from the seed (feature 005 US2, SC-004: zero hand-placed
        coordinates). Every unpinned knob is rolled from `self.seed` (pinned ones honored); the rolled values
        then DRIVE the geometry through the resolvers: the water source picks the sluice, plot_texture picks the
        paddy grain, cluster_position + cluster_shape place + shape the homestead cloud, lane_skeleton lays the
        lanes. Two different seeds roll different combinations; the same seed is byte-identical. Call after
        `s.meta(name=, scale=, ftpx=, toscale=True, ...)`. Returns the resolved knob dict. Scope: a nucleated
        HAMLET or VILLAGE (the to-scale tiers); a hamlet needs no headman/shrine/cemetery, a village adds them."""
        from waterfields import build_comb

        self.M["meta"]["water_kind"] = water_kind
        self.M["meta"]["down_deg"] = down_deg
        self.M["meta"]["nucleated"] = True  # a rolled village is a nucleated cluster (per-house-grove path is off; a communal windbreak is drawn below)
        scale = self.M["meta"].get("scale", "village")
        self._nucleated = True
        W, H = self.W, self.H
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # --- roll the knobs (pinned -> rolled -> default) ---
        cluster_position = self.resolve("cluster_position")
        cluster_shape = self.resolve("cluster_shape")
        lane_kind = self.resolve("lane_skeleton")
        plot_size = self.resolve("plot_size")
        plot_regularity = self.resolve("plot_regularity")
        grain_drift = self.resolve("grain_drift")
        if self.knob_pins.get("water_source_position") is not None:
            water_source = self.resolve("water_source_position")
        else:  # roll among the GRAVITY-VALID set (the typing rule defers gravity to placement)
            valid = sorted(self.water_sources_for(down_deg, water_kind))
            # don't put the intake DEAD-CENTER on the high margin where a high-seated village already sits - a
            # center source (mid_margin / chain) would fight the cluster for the narrow fan head, so prefer a
            # corner intake there (historically fine: a corner tank feeding the comb from one high shoulder).
            if cluster_position in ("high_margin", "valley_head", "mid_margin", "on_rise"):
                corner = [v for v in valid if v not in ("mid_margin", "chain")]
                valid = corner or valid
            wr = knob_rng(self.seed, "water_source_position")
            water_source = valid[wr.randrange(len(valid))]
            self._resolved_knobs["water_source_position"] = water_source
        self.M["meta"]["water_source"] = water_source
        # --- the field: sluice from the water source, then the comb ---
        mx, my = W * 0.16, H * 0.16
        # push the nominal field DOWNSLOPE, so its UPHILL margin keeps room for the things that crowd there -
        # the intake AND a high-seated village (a valley_head cluster on a diagonal fall otherwise lands on, or
        # past, the canvas edge, which starves the village and pushes its civic precinct off-frame)
        shift = 0.15 * min(W, H)
        sluice = self.water_source_anchor(water_source, (mx + dx * shift, my + dy * shift, W - mx + dx * shift, H - my + dy * shift), down_deg)
        across, step = self.plot_texture(plot_size, plot_regularity)
        net = build_comb(W, H, sluice, self.seed, down_deg=down_deg, field_fall=field_fall, plot_across=across, row_step=step, grain_drift=grain_drift, offtakes_a=offtakes_a, offtakes_b=offtakes_b)
        self.field_polys.append([(round(x, 1), round(y, 1)) for x, y in net["envelope"]])
        self.meta(dry_furrows_vary=net["furrows_vary"])
        if water_kind == "pond":
            source: dict[str, Any] = {"kind": "pond", "pond": (sluice[0] - dx * 66, sluice[1] - dy * 66, 88.0, 56.0)}
        else:
            source = {"kind": "stream", "stream": [(sluice[0] - dx * 380, sluice[1] - dy * 380), (sluice[0], sluice[1])]}
        # roll the ARCHETYPE knob BEFORE drawing (draw_comb_field reads it to place archetype-appropriate
        # in-field features): field_archetype (only valley_paddy is geometrically implemented, so a roll with
        # no declared terrain lands there by typing).
        self.M["meta"]["field_archetype"] = self.resolve("field_archetype")
        self.draw_comb_field(net, name + "-paddies", source)
        # a land-use OVERLAY drawn over the fresh paddy
        self.apply_land_use(net, self.resolve("land_use_overlay"), random.Random((self.seed ^ 0x1A7D) & 0xFFFFFFFF))
        # --- seat the cluster on the field edge, from the ACTUAL drawn plots (robust to a fan's narrow head) ---
        # The cluster_position gives the CHARACTER (which margin); the seat is computed constructively so it
        # always abuts + rings the field and never fights the water intake: the lateral lean is forced AWAY from
        # the sluice's side, and the seat sits just beyond the drawn rice's reach in that direction. This
        # replaces the earlier anchor+snap+nudge, whose post-hoc pushes destabilised placement roll-to-roll.
        env = net["envelope"]
        exs, eys = [p[0] for p in env], [p[1] for p in env]
        fb = (min(exs), min(eys), max(exs), max(eys))
        verts = [(v[0], v[1]) for p in net["plots"] for v in p["poly"]]
        fcx2 = sum(v[0] for v in verts) / len(verts)
        fcy2 = sum(v[1] for v in verts) / len(verts)
        ux, uy = -dy, dx  # lateral (cross-slope) unit
        away = -1.0 if ((sluice[0] - fcx2) * ux + (sluice[1] - fcy2) * uy) >= 0 else 1.0  # lean opposite the sluice
        along_bias = {"high_margin": -1.0, "valley_head": -1.0, "mid_margin": -1.0, "on_rise": -1.0, "flank": 0.0, "valley_mouth": 0.55}
        lat_bias = {"high_margin": 0.2, "valley_head": 0.6, "mid_margin": 0.6, "on_rise": 0.55, "flank": 1.0, "valley_mouth": 0.95}
        tdx = dx * along_bias[cluster_position] + ux * away * lat_bias[cluster_position]
        tdy = dy * along_bias[cluster_position] + uy * away * lat_bias[cluster_position]
        tl = math.hypot(tdx, tdy) or 1.0
        tdx, tdy = tdx / tl, tdy / tl  # the seat direction (away from the field)
        alx, aly = -tdy, tdx  # ALONG the margin (perpendicular to the seat direction)
        # The cluster is a shallow band in the MARGIN FRAME (along the margin x away from the field), NOT an
        # axis-aligned ellipse: at a diagonal fall the screen-axis extents collapse into a big circle, which
        # sprays seeds over the paddy and starves the village (Kikuta at down_deg=45 placed 3 of 55). Size the
        # band's LENGTH from the household count so a village gets the frontage it needs, and keep its DEPTH
        # shallow so the near rows ring the field.
        # GROUND PER HOUSEHOLD, and it is the BUNDLE's, not the farmhouse's (corrected 2026-08-11).
        #
        # The to-scale tiers do not place a farmhouse, they place a homestead BUNDLE - house (46 x 28
        # ft) plus its threshing yard below and its dooryard garden beside, ~71 x 57 ft of reserved
        # ground - and `_fits` then keeps bundles apart by circumscribed circles rather than real
        # footprints, which costs up to another ~2x in spacing. The old 56 ft pitch is the FARMHOUSE,
        # so the band was asked to hold roughly three times what fits in it.
        #
        # THE SYMPTOM IS NOT A SHORTFALL, which is what kept this hidden: the caller keeps drawing
        # seeds until the quota is met, so the household count comes out right and the cluster ends
        # up packed absolutely solid. It surfaces instead as a settlement with nowhere to put a
        # WELL - `open_seat(..., well=True)` refusing every probe in the cluster, and the map failing
        # `settlement_has_wells` for a reason that looks nothing like its cause. (Found by the
        # scripted-generation experiment, hamletgen.md; Honda seating 15 houses for 18 declared
        # households was the visible edge of it.)
        #
        # Still deliberately TIGHT - a nucleated village is a dense fabric, and an over-generous
        # pitch spreads the houses into a thin scatter and leaves the lanes overshooting into empty
        # ground. 92 ft is the bundle plus the circles' waste and no more.
        #
        # CONVERTED THROUGH `ftpx`, NOT `bscale`. They are the same number everywhere except the
        # village tier, which declares ftpx=2 but pins bscale=1.0 for legacy reasons (settlements.md)
        # - and a village bundle really is drawn at half a hamlet's pixel size (measured: house 25x14
        # px against 53x27). Sizing off bscale therefore asked a village band for twice the ground
        # its bundles occupy, which strung its cluster thin over a hollow hull and tripped
        # `village_cluster_compact`. Real feet in, this map's pixels out.
        need = max(1, households) * self.px(BUNDLE_PITCH_FT) ** 2
        # aim for a ~3:1 band (a nucleated village is a blob, not a hairline ribbon): pick the depth that gives
        # that aspect for the area needed, floored so a hamlet stays shallow and capped so it stays a margin band
        dep = max(112.0, min(math.sqrt(need / (3.0 * math.pi)), 240.0))
        lat = max(240.0, min(need / (math.pi * dep), 1500.0))
        reach = max((v[0] - fcx2) * tdx + (v[1] - fcy2) * tdy for v in verts)
        ccx, ccy = fcx2 + tdx * (reach + dep + 30.0), fcy2 + tdy * (reach + dep + 30.0)
        rng = random.Random((self.seed * 2654435761) & 0xFFFFFFFF)

        def to_screen(p: Any) -> Pt:  # margin-frame (along, away-from-field) -> screen
            return (ccx + alx * p[0] + tdx * p[1], ccy + aly * p[0] + tdy * p[1])

        # the lane skeleton is derived in the MARGIN FRAME too, then rotated onto the band - so its lanes run
        # along the margin and its DERIVED headman/gateway land inside the cluster at any fall direction
        layout = skeleton_layout(lane_kind, 0.0, 0.0, lat, dep)
        for lane_pts in layout["lanes"]:
            # ...and trimmed off any wet ground already drawn: the pond and its reed fringe are laid
            # before the skeleton, and a rolled arm reaching the water finished IN the fringe on
            # Shimizu (GM 2026-08-12). A lane stops at the reeds; it does not wade into them.
            self.lane(self.trim_off_marsh([to_screen(p) for p in lane_pts]), width=5, clearance=40, worn=True)
        self.M["meta"]["lane_skeleton"] = lane_kind
        sk = {"headman": to_screen(layout["headman"]), "gateway": to_screen(layout["gateway"])}
        placed = 0
        if scale == "village":
            # The headman takes the skeleton's prime spot - but that spot is the JUNCTION itself on a T/Y/cross,
            # and a lane is a no-build corridor, so the compound FRONTS the junction rather than sitting on it:
            # try the spot, then a ring of small offsets around it, taking the first that fits.
            hl = layout["headman"]
            for ox, oy in ((0.0, 0.0), (62.0, 44.0), (-62.0, 44.0), (62.0, -44.0), (-62.0, -44.0), (96.0, 0.0), (-96.0, 0.0)):
                hx, hy = to_screen((hl[0] + ox, hl[1] + oy))
                if self.headman(hx, hy):
                    placed = 1
                    break
        # seeds are shaped in the margin frame, then rotated onto it - so the band hugs the margin at any fall
        # The candidate pool is deliberately generous. `cluster_seeds` draws one seed at a time, so a
        # longer list only APPENDS candidates - the leading ones are unchanged, and any map that fills
        # its quota breaks out below and is byte-identical. The old 3x+18 left no headroom: Honda seated
        # exactly 15 houses for 18 households, the floor of the households_consistent band, so the small
        # geometry shift from the per-line bund wander (settlements.md 'Polder fifth pass', sixth) cost
        # it one house and failed the gate. A map should not sit one rejected candidate from failing.
        for lx, ly in self.cluster_seeds(cluster_shape, 0.0, 0.0, lat, dep, int(households * 6.0) + 30, rng):
            if placed >= households:
                break
            if self.try_place(ccx + alx * lx + tdx * ly, ccy + aly * lx + tdy * ly, "plain"):
                placed += 1
        self.farmsteads()
        hs = self.M["houses"]
        if hs:  # wells among the ACTUAL houses (BEFORE the grove, so the grove's canopy skips them)
            hxs, hys = [h["x"] for h in hs], [h["y"] for h in hs]
            # INSET, not grown. A well is a HARD crop feature with a ~16 px extent, so one seated
            # just past the outermost homestead drags the whole frame out after it and leaves a band
            # of empty ground on that side (`crop_not_held_open_by_one_feature`). The grid used to be
            # laid over the house bbox GROWN by 10 px, which invites exactly that. Insetting costs no
            # coverage - `settlement_dwellings_watered` reaches ~760 real feet and a cluster is a
            # fraction of that across - and the inset is skipped on a cluster too small to take it,
            # because an inset box that collapses yields no grid cells and hence no wells at all.
            wx0, wy0, wx1, wy1 = min(hxs), min(hys), max(hxs), max(hys)
            inset = 40.0 * self.bscale
            if wx1 - wx0 > 3 * inset and wy1 - wy0 > 3 * inset:
                wx0, wy0, wx1, wy1 = wx0 + inset, wy0 + inset, wx1 - inset, wy1 - inset
            self.place_wells((wx0, wy0, wx1, wy1), spacing=185, near=104)
        # --- a COMMUNAL windward windbreak BEHIND the cluster (a nucleated village shelters behind one grove,
        # not per-house belts): a belt in the MARGIN FRAME, spanning the band's length on its far-from-field side ---
        # the belt must sit on the WINDWARD (uphill) side in the FALL frame - that is what shelters the village
        # and what village_windbreak_on_windward_side checks - so project the band onto the fall/cross axes
        # THE BELT IS MEASURED OFF THE HOUSES, not off the band (corrected 2026-08-11).
        #
        # It used to be built from the band's requested extents - so it stood where the cluster was
        # ASKED to be rather than where it ended up, and the placer routinely seats a tighter, offset
        # cloud than the band it was handed. The gap is invisible while the two happen to agree and
        # fatal when they do not: `village_windbreak_embraces_cluster` wants a substantial belt
        # within 150 px of a farmhouse, and a belt built from a band that got bigger simply walks
        # away from the houses (measured at 179 and 198 px when the band's own sizing was corrected
        # above). A grove that shelters nothing is decoration. Derived from what landed, it cannot
        # drift - which is the project's derive-don't-pin rule applied to an aggregate.
        ux, uy = -dy, dx  # cross-slope
        hxs_, hys_ = [h["x"] for h in hs], [h["y"] for h in hs]
        bcx, bcy = sum(hxs_) / len(hxs_), sum(hys_) / len(hys_)
        reach_up = max((bcx - h["x"]) * dx + (bcy - h["y"]) * dy for h in hs)  # how far the cloud reaches UPHILL
        lat_half = max(abs((h["x"] - bcx) * ux + (h["y"] - bcy) * uy) for h in hs) + 46.0
        bc = (bcx - dx * (reach_up + 62), bcy - dy * (reach_up + 62))
        belt = [
            (bc[0] - ux * lat_half - dx * 34, bc[1] - uy * lat_half - dy * 34),
            (bc[0] + ux * lat_half - dx * 34, bc[1] + uy * lat_half - dy * 34),
            (bc[0] + ux * lat_half + dx * 34, bc[1] + uy * lat_half + dy * 34),
            (bc[0] - ux * lat_half + dx * 34, bc[1] - uy * lat_half + dy * 34),
        ]
        belt = [(max(6.0, min(self.W - 6.0, bx)), max(6.0, min(self.H - 6.0, by))) for bx, by in belt]  # keep the belt on-canvas
        self.village_grove(belt, role="windbreak")
        # --- village-only civic features (a hamlet has none) ---
        if scale == "village" and civic_shrine:
            gx, gy = sk["gateway"]
            sx_, sy_ = gx + dx * 46, gy + dy * 46
            self.shrine(sx_, sy_)
            # TORII, numerologically counted (GM 2026-07-21): roll 1/3/7 on the tier distribution
            # (pinnable as knob 'torii_count') and march the gates back up the approach toward the
            # gateway - the sando the worshiper walks in through. torii_count_canonical gates the set.
            _tn = self.knob_pins.get("torii_count")
            if _tn is None:
                _tn = roll_torii_count(scale, random.Random(self.seed * 977 + 13))
            for _ti in range(int(_tn)):
                self._torii(sx_ - dx * (34 + 30 * _ti), sy_ - dy * (34 + 30 * _ti))
            self.M["meta"]["torii_count"] = int(_tn)
        self.bridges()  # carry the lanes over any water they cross
        if self.M.get("field_ditches"):  # planks over the long irrigation ditches
            self.channel_footbridges(spacing=300)
        # the official notice board on a lane verge at the busiest node (GM 2026-07-24: every
        # tier posts the state's standing law; deterministic, so the seed stream is untouched)
        self.place_kosatsuba()
        # `lay_hinterland=False`: a caller that supplies its OWN sacred precinct AFTER roll_village (the
        # civic_shrine=False path) must defer the scrub/marsh scatter until its shrine/torii/graveyard have
        # registered their swept-ground clearings, or the scrub scatters over ground that should read tended.
        # Such a caller calls `s.hinterland()` itself, after placing the precinct.
        if lay_hinterland:
            self.hinterland()
        if frame:  # a caller adding its OWN civic features (a sacred precinct) crops+titles itself, AFTER them
            self.crop_to_content(margin=40)
            self.title(name)
        return {
            "cluster_position": cluster_position,
            "cluster_shape": cluster_shape,
            "lane_skeleton": lane_kind,
            "water_source_position": water_source,
            "plot_size": plot_size,
            "plot_regularity": plot_regularity,
            "grain_drift": grain_drift,
            "households": placed,
            # geometry the caller needs to site its OWN civic features (a sacred precinct, a burial ground)
            # relative to the rolled village, without re-deriving the cluster:
            "cluster": (round(ccx, 1), round(ccy, 1), round(lat, 1), round(dep, 1)),
            "gateway": (round(sk["gateway"][0], 1), round(sk["gateway"][1], 1)),
            "field_bbox": tuple(round(v, 1) for v in fb),
        }

    def line_seeds(self: Settlement, p0: Pt, p1: Pt, n: int, half_band: float, rng: random.Random, form: str = "linear", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds strung ALONG a line (feature 005 `settlement_form` = 'linear'): a RIBBON of homesteads
        fronting a road / field-margin / dike instead of a nucleated blob - historically the cheapest big
        structural difference between two same-region villages (research.md D5; a levee, a valley-edge track,
        or a canal bank strings the houses out). Distributes `n` seeds along the segment `p0`->`p1` (uniform
        along its length) with a perpendicular jitter up to +/-`half_band`; the bundle solver then hugs each
        homestead to the field edge as usual. Records `meta.settlement_form` when `record=True`."""
        if record:
            self.M["meta"]["settlement_form"] = form
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length  # unit perpendicular to the line
        out: list[Pt] = []
        for _ in range(n):
            t = rng.random()
            b = rng.uniform(-1.0, 1.0) * half_band
            out.append((x0 + dx * t + px * b, y0 + dy * t + py * b))
        return out

    def scatter_seeds(self: Settlement, cx: float, cy: float, rx: float, ry: float, n: int, rng: random.Random, form: str = "dispersed", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds scattered LOOSELY and evenly over a BROAD area (feature 005 `settlement_form`
        = 'dispersed'): scattered farmsteads, each its own yashikirin-groved homestead, rather than a tight
        nucleus - the kainyo / Tonami dispersed-farmstead pattern of the well-watered plains. Area-uniform
        over the ellipse so the farms spread out; `try_place`'s field-adjacency + no-build blockers then
        filter them onto the dry margins, leaving them dotted along the field edges instead of clumped.
        Records `meta.settlement_form`. Pair with `s._nucleated = False` so each farm draws its OWN grove."""
        if record:
            self.M["meta"]["settlement_form"] = form
        out: list[Pt] = []
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.random() ** 0.5  # area-uniform: an even scatter, not center-clumped
            out.append((cx + math.cos(a) * r * rx, cy + math.sin(a) * r * ry))
        return out

    def waterfront_seeds(self: Settlement, canal: Any, n: int, offset: float, rng: random.Random, form: str = "water_town", record: bool = True) -> list[Pt]:  # type: ignore[misc]
        """House seeds strung along BOTH banks of a canal (feature 005 `settlement_form` = 'water_town'): a
        Jiangnan-style water town where the houses FRONT the water, offset `offset` px to either side of the
        canal polyline. Records `meta.settlement_form`. (Per GM canon canals are a Lion-lands feature, so this
        form is typing-gated to Lion lands / a declared canal.) `try_place` then keeps each seed field-adjacent
        and off blockers, so the row packs cleanly along the waterfront."""
        if record:
            self.M["meta"]["settlement_form"] = form
        segs = [(canal[i], canal[i + 1]) for i in range(len(canal) - 1)]
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1.0
        out: list[Pt] = []
        for k in range(n):
            d = total * (k + 0.5) / n
            acc = 0.0
            for a, b in segs:
                ln = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + ln >= d:
                    t = (d - acc) / (ln or 1.0)
                    px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    nx, ny = -(b[1] - a[1]) / (ln or 1.0), (b[0] - a[0]) / (ln or 1.0)  # canal normal
                    side = 1.0 if k % 2 == 0 else -1.0  # alternate banks
                    out.append((px + nx * offset * side + rng.uniform(-10, 10), py + ny * offset * side + rng.uniform(-10, 10)))
                    break
                acc += ln
        return out

    def headman(self: Settlement, x: float, y: float, w: float = 92, h: float = 56) -> Any:  # type: ignore[misc]
        # `w`, `h` are in FEET (drawn at the map's ftpx, px(92) = 46px at 2 ft/px). A nanushi/shoya house is
        # the grandest in the village but still a house - ~92x56 ft, clearly larger than a plain 46x28 ft
        # farmhouse without the old fortress-sized 216x136 ft. headman_is_largest holds.
        if self._toscale():
            # the headman is just a LARGER PLAIN farmhouse - placed through the standard collision-checked
            # bundle path with a tunable SIZE, so it gets its yard + garden and cannot overlap a neighbor.
            # BOTH homestead styles route here (GM 2026-07-21, caught on Hikari no Sato): this guard used to
            # test _nucleated, so a DISPERSED to-scale village's headman fell through to the legacy rec below,
            # which _farmsteads_bundle draws as a LONE house (the abandoned-ruin path) - the grandest
            # farmstead in the village with no threshing yard and no garden. In the dispersed style the
            # bundle also brings the per-house grove when room allows; the solver drops it gracefully in a
            # dense cluster (neighbor tree cover shelters the house), which is the wanted behavior.
            # NO special reservation or "big"-glyph storeroom wing (that wing was drawn outside
            # the reserved footprint and overlapped the north neighbor's yard).
            return self.try_place(x, y, "plain", role="headman", size=(w, h))
        # non-to-scale tiers have no headman (a hamlet falls under the district headman, towns are run by
        # the magistrate - the *_has_no_headman checks), so the old legacy rec branch here was dead code
        # once the Hikari fix routed every to-scale style through the bundle; removed 2026-07-21.
        raise ValueError("headman() is a to-scale village feature - this map is not toscale")

    def _field_adjacent(self: Settlement, x: float, y: float) -> bool:  # type: ignore[misc]
        """A farmhouse must stay near the farmland (within the gate's ADJ=165), so a nudge cannot drift it
        off into the urban core or the void."""
        return any(edge_dist(x, y, poly) <= 165 for poly in self.field_polys) if self.field_polys else True

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

    def _rect_corners(self: Settlement, rect: Any) -> list[Pt]:  # type: ignore[misc]
        cx, cy, w, h = rect
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]

    def _poly_bboxes(self: Settlement, polys: Any) -> list[Any]:  # type: ignore[misc]
        """Cached (minx, miny, maxx, maxy) per polygon in `polys`. Rebuilt only when the list GROWS - the
        block-poly list accretes each placed homestead during the solve, but individual polys are never
        mutated - so a length change is a sufficient staleness signal. Lets _rect_hits reject a far polygon
        with 4 comparisons instead of the O(vertices) corner/segment tests. See `_bbox_cache`."""
        cached = self._bbox_cache.get(id(polys))
        if cached is None or cached[0] != len(polys):
            boxes: list[Any] = []
            for poly in polys:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
            cached = (len(polys), boxes)
            self._bbox_cache[id(polys)] = cached
        return cast(list[Any], cached[1])

    def _rect_hits(self: Settlement, rect: Any, polys: Any) -> bool:  # type: ignore[misc]
        """Whether an axis-aligned rect overlaps any polygon in `polys` (corner-in, vertex-in, or edge-cross).
        Bbox pre-filters carry the cost: a polygon whose bbox is disjoint from the rect is skipped outright,
        and within an overlapping polygon each EDGE is bbox-tested before the crossing check (this matters for
        the one huge field-envelope polygon, where the rect only ever meets a couple of its many edges). (A
        spatial grid was tried on top of this and measured NOISE-identical: the bbox reject already makes the
        far-poly scan cheap, and the residual cost is the genuine near-overlap math on polys a grid returns
        anyway - so it was not worth the caching complexity.)"""
        cx, cy, w, h = rect
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        gc = self._rect_corners(rect)
        for poly, (px0, py0, px1, py1) in zip(polys, self._poly_bboxes(polys), strict=False):
            if px1 < rx0 or px0 > rx1 or py1 < ry0 or py0 > ry1:
                continue  # bboxes disjoint -> cannot overlap
            n = len(poly)
            if any(point_in_poly(px, py, poly) for px, py in gc) or any(rx0 <= vx <= rx1 and ry0 <= vy <= ry1 and point_in_poly(vx, vy, gc) for vx, vy in poly):
                return True
            for k in range(n):  # edge-cross, each edge bbox-gated against the rect
                a, b = poly[k], poly[(k + 1) % n]
                if min(a[0], b[0]) > rx1 or max(a[0], b[0]) < rx0 or min(a[1], b[1]) > ry1 or max(a[1], b[1]) < ry0:
                    continue
                if any(segments_cross(gc[e], gc[(e + 1) % 4], a, b) for e in range(4)):
                    return True
        return False

    def _water_obstacles(self: Settlement) -> list[Any]:  # type: ignore[misc]
        """Cached (poly, keep-out half-width, bbox) for every irrigation LINE a solid bundle rect must avoid -
        feeder channels, in-field/drain ditches, streams. Rebuilt only when one of the three source lists
        changes length (all are laid before the homestead solve, then static). Lets _rect_on_water skip a
        whole course - and then an individual segment - whose neighborhood the rect cannot reach."""
        chans = self.M.get("channels", [])
        ditches = self.M.get("field_ditches", [])
        streams = self.M.get("streams", [])
        key = (len(chans), len(ditches), len(streams))
        if self._water_obs_cache is None or self._water_obs_cache[0] != key:
            obs: list[Any] = []
            for lst, base in ((chans, 2.5), (ditches, 7.0), (streams, 9.0)):
                for f in lst:
                    poly = f["poly"]
                    if len(poly) < 2:
                        continue
                    hw = f.get("w", base) / 2 + 5
                    xs = [p[0] for p in poly]
                    ys = [p[1] for p in poly]
                    obs.append((poly, hw, (min(xs), min(ys), max(xs), max(ys))))
            self._water_obs_cache = (key, obs)
        return cast(list[Any], self._water_obs_cache[1])

    def _rect_on_water(self: Settlement, rect: Any) -> bool:  # type: ignore[misc]
        """Whether a SOLID bundle rect (house/yard/garden/shed) lands on an irrigation LINE - a feeder
        channel, an in-field/drain ditch, or a stream. These are dry-ground structures, so a garden or
        yard in a running ditch is wrong (gardens_clear_of_channels), and this keeps the homestead solver
        off the drain outfall that threads the village margin. A hair wider than the check's keep-out so
        the solver leaves room the check then confirms. The GROVE is exempt (it may hug a bund). Bbox
        pre-filters (per course, then per segment) skip the seg_dist / crossing math for anything far off."""
        cx, cy, w, h = rect
        gc = self._rect_corners(rect)
        pts = gc + [(cx, cy)]
        rx0, ry0, rx1, ry1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        for poly, hw, (px0, py0, px1, py1) in self._water_obstacles():
            if px1 + hw < rx0 or px0 - hw > rx1 or py1 + hw < ry0 or py0 - hw > ry1:
                continue  # the whole course is out of reach
            for k in range(len(poly) - 1):
                a, b = poly[k], poly[k + 1]
                if min(a[0], b[0]) - hw > rx1 or max(a[0], b[0]) + hw < rx0 or min(a[1], b[1]) - hw > ry1 or max(a[1], b[1]) + hw < ry0:
                    continue  # this segment is out of reach
                if any(seg_dist(px, py, a, b) < hw for px, py in pts):
                    return True
                if any(segments_cross(a, b, gc[e], gc[(e + 1) % 4]) for e in range(4)):
                    return True
        return False

    def _rect_blocked(self: Settlement, rect: Any, fields: bool) -> bool:  # type: ignore[misc]
        """Whether a bundle sub-rect lands on forbidden ground: no-build blocks, lanes, hill/pond ellipses,
        irrigation lines, and (only when `fields=True`, i.e. the SOLID house/yard/garden) the flooded
        paddies. The GROVE (fields=False) may HUG a paddy bund, so it is tested against everything BUT the
        fields and the water lines."""
        if self._rect_hits(rect, self.block_polys):
            return True
        if fields and self._rect_hits(rect, self.field_polys):
            return True
        if fields and self._rect_on_water(rect):
            return True
        if fields and not self._hard_clear(rect[0], rect[1], rect[2], rect[3]):
            return True  # HARD ground read from the manifest (crop plots + a field's own ditches)
        cx, cy, w, h = rect
        for px, py in self._rect_corners(rect) + [(cx, cy)]:
            for ex, ey, rx, ry in self.ellipses:
                if rx > 0 and ry > 0 and ((px - ex) / rx) ** 2 + ((py - ey) / ry) ** 2 <= 1:
                    return True
        return self._near_corridor(cx, cy)

    def _bundle_fits(self: Settlement, geom: Any, grove_off_field: bool = True) -> bool:  # type: ignore[misc]
        """A homestead bundle fits where it is in-bounds, its SOLID parts (house/yard/garden) clear every
        paddy/block/lane/ellipse, its GROVE clears all of those (and may abut - but not enter - a paddy when
        `grove_off_field`, the test used while shoving the grove up against the bund), and the whole bbox
        does not overlap another already-placed homestead (a sliver of tolerance lets adjacent groves ABUT
        into one windbreak). Split into a side-INDEPENDENT half (house/yard/kura/grove/sun - identical for
        every garden side at a position) and a side-DEPENDENT half (the garden bed + the bbox it grows), so
        the nucleated placer can test the common half ONCE across all four sides (see `_fits_any_side`). The
        conjunction is order-independent, so the result is unchanged from the old single test."""
        return self._bundle_common_fits(geom, grove_off_field) and self._bundle_side_fits(geom)

    def _sun_corridor_ok(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """Does this homestead leave every threshing yard - its own and the neighbours' - its sun?

        THE RULE (GM 2026-08-13, researched in research/homesteads.md, "The threshing yard's sun"):
        rice is dried on the niwa, so a yard needs clear ground to its SOUTH. A thatched roof is
        pitched 45 deg or steeper, which puts our 46x28 ft minka's ridge ~20 ft up; at 38N in the
        10th month that throws 21 ft of shadow at noon and 39 ft by 9am. So a farmhouse standing
        within `sun_corridor` feet south of a yard takes the drying day away from it.

        OPT-IN, and deliberately so. `s.sun_corridor(39)` turns it on; it is OFF by default, because
        turning it on re-packs every nucleated map in the pool and the GM's decision (2026-08-13) is
        that the hand-authored maps keep their present packing and inherit the fix as each is
        converted to a generator script. The engine holds the rule; the scripted path asks for it.

        Both directions are tested, because a bundle is placed among bundles already standing: this
        house may not shade a yard already placed, and this yard may not be shaded by a house already
        standing. Testing only one direction leaves the defect to whichever homestead is seated
        second."""
        ft = getattr(self, "_sun_corridor_ft", 0.0)
        if not ft:
            return True
        # THE PLACER IS STRICTER THAN THE CHECK BY A HAIR, on purpose. It measures the bundle rects
        # it is about to commit; `yards_unshaded_by_neighbors` measures the yard record that
        # `farmsteads()` finally draws, and the two differ by fractions of a pixel. A seat at 39.0
        # ft therefore passed here and failed there on 2 of 36 cohort maps. Two feet of margin costs
        # nothing in packing and puts the disagreement where it cannot bite.
        reach = self.px(ft + 2.0)
        side = self.px(2.0)  # ...and the same margin ACROSS the corridor: the lateral overlap test is
        # `|dx| < (yard_w + house_w)/2`, and a seat that missed the placer's version by 0.35 px failed
        # the check's on a held-out cohort map. Both axes, or the disagreement just moves.
        hx, hy, hw, hh = geom["house"]
        yx, yy, yw, yh = geom["yard"]
        # THE NEIGHBOURS' YARDS ARE READ OFF THE PLACED BUNDLES, not off `M["threshing_yards"]`.
        # Yards are not drawn until `farmsteads()` flushes, long after every house is seated, so the
        # manifest list is EMPTY while placement runs - testing it caught nothing in the direction
        # that matters (a new house shading a yard already standing), and the first version of this
        # rule cleared only about half the shaded yards because of it. Each bundle's record carries
        # its own `geom`, so the yard is there to be read.
        for b in self.M.get("houses", []):
            g = b.get("geom")
            ty = g["yard"] if g else None
            if ty is None:
                continue
            if abs(ty[0] - hx) < (ty[2] + hw) / 2 + side and 0 < (hy - hh / 2) - (ty[1] + ty[3] / 2) < reach:
                return False
        # ...and this YARD must not sit in a standing house's shadow
        return not any(abs(b["x"] - yx) < (b["w"] + yw) / 2 + side and 0 < (b["y"] - b["h"] / 2) - (yy + yh / 2) < reach for b in self.M.get("houses", []))

    def sun_corridor(self: Settlement, feet: float) -> None:  # type: ignore[misc]
        """Ask the placer to keep `feet` of open ground SOUTH of every threshing yard (see
        `_sun_corridor_ok`). Off by default; a generator opts in."""
        self._sun_corridor_ft = float(feet)

    def _bundle_common_fits(self: Settlement, geom: Any, grove_off_field: bool = True) -> bool:  # type: ignore[misc]
        """The fit checks that do NOT depend on which side the garden is on - the house, the south threshing
        yard, a north kura, the windward grove (dispersed only), and the yard sun-corridor. Same for every
        garden side at a given position, so it is tested once per position."""
        if self._rect_blocked(geom["house"], fields=True) or self._rect_blocked(geom["yard"], fields=True) or ("shed" in geom and self._rect_blocked(geom["shed"], fields=True)):
            return False
        if "grove_n" in geom and any(self._rect_blocked(geom[k], fields=grove_off_field) for k in ("grove_n", "grove_w")):
            return False
        if not self._sun_corridor_ok(geom):
            return False
        return not self._yard_sun_conflict(geom)

    def _bundle_side_fits(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """The fit checks that DO move with the garden side (via the bundle bbox): in-bounds, inside any
        bounding ring, the garden bed(s) clear of every paddy/block/lane, and the whole bbox clear of every
        placed homestead."""
        cx, cy, W, H = geom["bbox"]
        if cx - W / 2 < 6 or cx + W / 2 > self.W - 6 or cy - H / 2 < 6 or cy + H / 2 > self.H - 6:
            return False
        if self.bound and any(not point_in_poly(vx, vy, self.bound) for vx, vy in self._rect_corners(geom["bbox"])):
            return False
        if any(self._rect_blocked(g, fields=True) for g in geom["gardens"]):
            return False
        return all(not (abs(cx - px) < (W + pw) / 2 + 2 and abs(cy - py) < (H + ph) / 2 + 2) for px, py, pw, ph in self.placed)

    def _yard_sun_conflict(self: Settlement, geom: Any) -> bool:  # type: ignore[misc]
        """A threshing yard dries rice in the southern sun, so no grove may sit in the ~22px strip directly
        SOUTH of any yard. Tests the candidate's grove against every placed yard's sun-corridor and the
        candidate's yard against every placed grove, so packing never stacks a windbreak over a neighbor's
        drying ground."""

        def shades(grove: Any, yard: Any) -> bool:
            cyx, cyy = yard[0], yard[1] + yard[3] / 2 + 11
            return cast(bool, abs(grove[0] - cyx) < (grove[2] + yard[2]) / 2 and abs(grove[1] - cyy) < (grove[3] + 22) / 2)

        new_groves = (geom["grove_n"], geom["grove_w"]) if "grove_n" in geom else ()
        new_yard = geom["yard"]
        for rec in self.M["houses"]:
            g = rec.get("geom")
            if not g:
                continue
            if any(shades(gv, g["yard"]) for gv in new_groves):
                return True
            other_groves = (g["grove_n"], g["grove_w"]) if "grove_n" in g else ()
            if any(shades(gv, new_yard) for gv in other_groves):
                return True
        return False

    @staticmethod
    def _closest_on_seg(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> Pt:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return ax, ay
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
        return ax + t * dx, ay + t * dy

    def _nearest_field_point(self: Settlement, cx: float, cy: float) -> Pt | None:  # type: ignore[misc]
        """The closest point on any paddy outline to (cx, cy) - the bund the grove will hug."""
        best: Pt | None = None
        bd = float("inf")
        for poly in self.field_polys:
            n = len(poly)
            for i in range(n):
                qx, qy = self._closest_on_seg(cx, cy, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1])
                d = (qx - cx) ** 2 + (qy - cy) ** 2
                if d < bd:
                    bd, best = d, (qx, qy)
        return best

    def _nearest_placed_point(self: Settlement, cx: float, cy: float) -> Pt | None:  # type: ignore[misc]
        """The center of the nearest already-placed homestead/house - the neighbor to pack against."""
        best: Pt | None = None
        bd = float("inf")
        for px, py, _pw, _ph in self.placed:
            d = (px - cx) ** 2 + (py - cy) ** 2
            if d < bd:
                bd, best = d, (px, py)
        return best

    def _slide(self: Settlement, cx: float, cy: float, hw: float, hh: float, target_fn: Any, grove_off_field: bool) -> Pt:  # type: ignore[misc]
        """Greedily shove the bundle toward target_fn (a field bund, then a neighbor) in small steps, as
        far as it still fits - the 'pack as close as the rules allow' step."""
        for _ in range(48):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if self._bundle_fits(self._bundle_geom(ncx, ncy, hw, hh), grove_off_field=grove_off_field):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle(self: Settlement, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:  # type: ignore[misc]
        """Place a homestead bundle one-at-a-time: find the nearest fitting spot to the seed, then COMPACT it
        - shove the grove up against the nearest paddy bund (without entering it), then pack the whole
        complex against its nearest neighbor, each as far as the rules allow. `shed` reserves a north kura in
        the bundle. Returns (cx, cy, geom) or None."""
        if getattr(self, "_nucleated", False):
            return self._place_bundle_nucleated(x, y, hw, hh, shed)
        offsets = [(0, 0)]
        for r in range(7, 92, 7):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._bundle_fits(self._bundle_geom(x + nx, y + ny, hw, hh)):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_field_point, grove_off_field=True)  # grove hugs the bund
        cx, cy = self._slide(cx, cy, hw, hh, self._nearest_placed_point, grove_off_field=True)  # pack against neighbor
        return cx, cy, self._bundle_geom(cx, cy, hw, hh)

    _NUC_SIDES = ("SE", "SW", "E", "W")  # garden-side preference: sunny south strip first, walls as fallback

    def _garden_shaded(self: Settlement, grect: Any) -> bool:  # type: ignore[misc]
        """A dooryard garden is SHADED when a farmhouse stands close to its SOUTH (the sun comes from the
        south), so a garden sandwiched with a neighbor's house just below it gets no light. Tested against
        every placed house - the nucleated placer prefers a side with open sky to the south."""
        gx, gy, gw, gh = grect
        for rec in self.M["houses"]:
            hx, hy, hw, hh = rec["x"], rec["y"], rec["w"], rec["h"]
            if hy > gy + gh / 2 - 3 and abs(hx - gx) < (hw + gw) / 2 and (hy - hh / 2) - (gy + gh / 2) < gh + 4:
                return True
        return False

    def _fits_any_side(self: Settlement, cx: float, cy: float, hw: float, hh: float, shed: bool = False) -> bool:  # type: ignore[misc]
        # The house/yard/kura/sun checks are the same for every garden side, so test that common half ONCE -
        # if it fails, no side can fit - then test only each side's garden (+ the bbox it grows). Identical
        # result to any(_bundle_fits(...) for side), but far fewer collision tests on the failing steps that
        # dominate the pack. Safe because the fit path is RNG-free: building fewer geoms cannot shift placement.
        g0 = self._bundle_geom(cx, cy, hw, hh, self._NUC_SIDES[0], shed)
        if not self._bundle_common_fits(g0):
            return False
        for i, side in enumerate(self._NUC_SIDES):
            geom = g0 if i == 0 else self._bundle_geom(cx, cy, hw, hh, side, shed)
            if self._bundle_side_fits(geom):
                return True
        return False

    def _field_dist(self: Settlement, cx: float, cy: float) -> float:  # type: ignore[misc]
        """Distance from a point to the nearest paddy edge (inf if there are no fields)."""
        p = self._nearest_field_point(cx, cy)
        return math.hypot(cx - p[0], cy - p[1]) if p else float("inf")

    def _slide_nuc(self: Settlement, cx: float, cy: float, hw: float, hh: float, target_fn: Any, keep_field: bool = False) -> Pt:  # type: ignore[misc]
        """Shove a nucleated bundle toward target_fn as far as SOME garden side still fits - the tight-pack
        step (the garden side is re-chosen at the final spot, so the slide only needs one side to work).
        With keep_field, a move is ALSO rejected if it would drift the bundle FURTHER from the paddy than
        where it started: so the neighbor-pack runs ALONG the field edge (tangentially) and never pulls the
        cluster off the paddy - the village glues its field side to the paddy and builds outward in rows."""
        fd_cap: Any = self._field_dist(cx, cy) + 3 if keep_field else None
        for _ in range(80):
            tgt = target_fn(cx, cy)
            if tgt is None:
                break
            dx, dy = tgt[0] - cx, tgt[1] - cy
            dist = math.hypot(dx, dy)
            if dist < 1.5:
                break
            ncx, ncy = cx + dx / dist * 2.0, cy + dy / dist * 2.0
            if keep_field and self._field_dist(ncx, ncy) > fd_cap:
                break
            if self._fits_any_side(ncx, ncy, hw, hh):
                cx, cy = ncx, ncy
            else:
                break
        return cx, cy

    def _place_bundle_nucleated(self: Settlement, x: float, y: float, hw: float, hh: float, shed: bool = False) -> Any:  # type: ignore[misc]
        """Nucleated placement: find the nearest spot where SOME garden side fits, pack it hard against the
        field bund then its neighbors, then pick the garden side that is UNSHADED and sunniest. The compact
        (grove-less) bundle lets the cluster nucleate; the adaptive garden gives sun + variety. `shed` reserves
        a north kura in every candidate bundle so a neighbor never lands on it."""
        offsets = [(0, 0)]
        for r in range(5, 80, 5):
            for k in range(12):
                a = k * math.pi / 6
                offsets.append((round(r * math.cos(a)), round(r * math.sin(a))))
        start: Pt | None = None
        for nx, ny in offsets:
            if self._fits_any_side(x + nx, y + ny, hw, hh, shed):
                start = (x + nx, y + ny)
                break
        if start is None:
            return None
        cx, cy = start
        cx, cy = self._slide_nuc(cx, cy, hw, hh, self._nearest_field_point)  # hug the paddy edge
        cx, cy = self._slide_nuc(
            cx,
            cy,
            hw,
            hh,
            self._nearest_placed_point,  # then pack ALONG it (never off it),
            keep_field=True,
        )  # so the cluster glues to the paddy
        best: Any = None
        for rank, side in enumerate(self._NUC_SIDES):
            geom = self._bundle_geom(cx, cy, hw, hh, side, shed)
            if not self._bundle_fits(geom):
                continue
            score = (sum(self._garden_shaded(g) for g in geom["gardens"]), rank)  # fewest shaded beds first, then preference
            if best is None or score < best[0]:
                best = (score, geom)
        if best is None:  # pragma: no cover - the slide only rests where some garden side fits, so best is set
            return None
        return cx, cy, best[1]

    def _solve_homestead(self: Settlement, rec: Any) -> Any:  # type: ignore[misc]
        """Find the best position for a farmhouse so its WHOLE homestead fits - threshing yard + dooryard
        garden + room for a windward grove. Searches the placed spot first, then a widening spiral, and stops
        as soon as the home spot already leaves grove-room (no churn). Prefers a spot WITH grove-room, then the
        least displacement; falls back to a yard+garden-only spot if no grove-room is reachable nearby. Updates
        rec's position + reservation. Returns (yard_spot, garden_spot), or None if even yard+garden won't fit."""
        x0, y0, w, h = rec["x"], rec["y"], rec["w"], rec["h"]
        self.placed: list[Any] = Indexed(
            p for p in self.placed if p != (x0, y0, w, h)
        )  # lift own reservation while searching (Indexed, not a plain list - a rebind must not silently drop _fits' index into the uncached fallback)
        best: Any = None  # (has_grove_room, -displacement, cx, cy, spot)
        for nx, ny in self._farmstead_nudges():
            cx, cy = x0 + nx, y0 + ny
            if not self._fits(cx, cy, w, h) or not self._field_adjacent(cx, cy):
                continue
            spot = self._find_appurtenances(cx, cy, w, h, rec["rot"], rec["kind"], rec["shed"], rec["wealth"])
            if spot is None:
                continue
            wf = rec["wealth"]  # the grove is drawn at the WEALTH size, so reserve room for THAT
            cand = (self._grove_room(cx, cy, w * wf, h * wf), -(abs(nx) + abs(ny)), cx, cy, spot)
            if best is None or cand[:2] > best[:2]:
                best = cand
            if cand[0] and nx == 0 and ny == 0:
                break  # already perfect at the home spot
        cx, cy = (best[2], best[3]) if best else (x0, y0)
        rec["x"], rec["y"] = cx, cy
        self.placed.append((cx, cy, w, h))  # re-reserve at the chosen (or original) spot
        return best[4] if best else None

    def farmsteads(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every farmstead. The to-scale tiers (villages/hamlets/towns) draw the reserved homestead
        BUNDLES; cities use the shipped house-first path. Call LAST in the gen so every obstacle is known. Returns the farmhouse count."""
        with self.rng_scope("farmsteads"):
            # ONE scope for the whole rural flush: yards, gardens, groves and kura sides are one
            # phase, and splitting them would only make a change to one perturb the others.
            if self._toscale():
                return self._farmsteads_bundle()
            return self._farmsteads_legacy()

    def _farmsteads_bundle(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every reserved homestead bundle: grove (back) -> yard -> garden -> house (on top). The hard
        work (fitting each whole bundle without overlap) already happened in try_place, one at a time, so
        this pass is pure drawing. Abandoned ruins (no bundle) draw as a lone house. Call LAST. Returns the
        farmhouse count.
        Two sub-passes so the garden EAST-shade nudge can see every neighbor's grove: (1) draw all per-house
        GROVES (the back layer), (2) after a south-nudge relaxation, draw the yards/gardens/houses on top."""
        survivors: list[Any] = []
        bundled: list[Any] = []
        arms: list[tuple[float, float, float, float, tuple[int, int]]] = []
        for rec in self._pending_farmsteads:
            geom = rec.get("geom")
            if geom is None:  # abandoned ruin / dispersed headman: lone house
                self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"])
                survivors.append(rec)
                continue
            for key, face in (("grove_n", (0, -1)), ("grove_w", (-1, 0))):
                if key not in geom:  # nucleated bundle: no per-house grove
                    continue
                cx, cy, w, h = geom[key]
                arms.append((cx, cy, w, h, face))
                self.M["groves"].append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": 0, "of": [rec["x"], rec["y"]], "face": list(face)})
                self.grove_rects.append((cx, cy, w, h))
            bundled.append(rec)
            survivors.append(rec)
        self._relax_gardens_south(bundled)  # nudge east-shaded gardens a little S (all groves now known)
        for rec in bundled:
            geom = rec["geom"]
            self._attach_yard(rec["x"], rec["y"], geom["yard"])
            self._attach_garden(rec["x"], rec["y"], geom["gardens"])
            self.house(rec["x"], rec["y"], rec["w"], rec["h"], rec["kind"], rec["rot"], shed=rec["shed"], shed_side=rec.get("shed_side", "W"))
        # The yashikirin arms DRAW LAST, after every house/shed of this pass is down (GM 2026-07-25).
        # They used to draw first, as a back layer the house painted over - which hid the overlap
        # rather than preventing it, and left crowns geometrically under roofs. Drawing them after
        # means _draw_grove's keep-out sees the houses, so the belt THINS off the walls instead: no
        # tree is drawn over a building anywhere on the map, by one rule rather than by z-order.
        # (The arm rects themselves are recorded above, before _relax_gardens_south, which needs them.)
        for cx, cy, w, h, face in arms:
            self._draw_grove(cx, cy, w, h, face)
        self.M["houses"] = [h for h in self.M["houses"] if h.get("on_dike")] + survivors  # dike-top houses (dike_top_houses) are not pending farmsteads - keep them
        return len(survivors)

    def _east_trees(self: Settlement, gx1: float, own: Any) -> list[Any]:  # type: ignore[misc]
        """The y-intervals (y0, y1) of every per-house grove arm standing hard against a garden's EAST - west
        edge within a shade band east of the garden's east edge `gx1`. `own` is the garden's OWN grove arms
        (which sit N/W, never east), excluded. The garden's x is fixed as it shifts S, so this set is stable."""
        band = 22 * self.bscale
        out: list[Any] = []
        for tx, ty, tw, th in self.grove_rects:
            if any(abs(tx - ox) < 1.5 and abs(ty - oy) < 1.5 for ox, oy, _, _ in own):
                continue  # skip the garden's own grove arms
            west = tx - tw / 2
            if gx1 - 2 <= west < gx1 + band:
                out.append((ty - th / 2, ty + th / 2))
        return out

    def _garden_beds_clear(self: Settlement, beds: Any, others: Any) -> bool:  # type: ignore[misc]
        """Whether a set of shifted garden beds land on clear ground: each bed off blocks/fields/water/lanes
        (`_rect_blocked`), and clear of every ACTUAL footprint in `others` (neighbors' houses/yards/gardens/
        groves + the garden's own house + yard). Tests real footprints, NOT the loose reserved bundle bboxes -
        a garden may shift into a neighbor's empty bbox margin, it just may not touch a drawn structure."""

        def hit(a: Any, b: Any) -> bool:
            return cast(bool, abs(a[0] - b[0]) < (a[2] + b[2]) / 2 and abs(a[1] - b[1]) < (a[3] + b[3]) / 2)

        for bed in beds:
            if self._rect_blocked(bed, fields=True):
                return False
            if any(hit(bed, r) for r in others):
                return False
        return True

    def _relax_gardens_south(self: Settlement, recs: Any) -> None:  # type: ignore[misc]
        """OPTION (villages where each house has its own windward grove and the garden goes on the E/lee side):
        once every yashikirin is drawn, a garden left with a NEIGHBOR'S grove hard against its EAST loses the
        morning sun. Where there is open ground, nudge that garden a little SOUTH so the tree falls to its NE
        and the eastern sky opens - the GM's 'move it a bit south' remedy. Best-effort: a garden boxed in to the
        south stays put (gardens_unshaded_from_east flags only the AVOIDABLE ones). See settlements.md 'gardens'."""
        step = 4 * self.bscale

        def footprints(exclude: int) -> list[Any]:
            """Every homestead's real house/yard/garden/grove rects, minus the rec at index `exclude`."""
            out: list[Any] = []
            for j, r in enumerate(recs):
                if j == exclude:
                    continue
                g = r["geom"]
                out.append(tuple(g["house"]))
                out.append(tuple(g["yard"]))
                out += [tuple(b) for b in g.get("gardens", [])]
                out += [tuple(g[k]) for k in ("grove_n", "grove_w") if k in g]
            return out

        def overlaps(a: Any, b: Any) -> bool:
            return cast(bool, a[0] < b[1] and b[0] < a[1])

        for i, rec in enumerate(recs):
            geom = rec["geom"]
            beds = geom.get("gardens")
            if not beds:
                continue
            own = [geom[k] for k in ("grove_n", "grove_w") if k in geom]
            gx1 = max(b[0] + b[2] / 2 for b in beds)
            gcy = sum(b[1] for b in beds) / len(beds)
            gh = max(b[1] + b[3] / 2 for b in beds) - min(b[1] - b[3] / 2 for b in beds)
            trees = self._east_trees(gx1, own)
            if not any(overlaps((gcy - gh / 2, gcy + gh / 2), t) for t in trees):
                continue  # not currently east-shaded - nothing to do
            maxshift = gh + rec["h"] + 6  # 'a little' - stays a dooryard garden near the house
            others = footprints(i) + [tuple(geom["house"]), tuple(geom["yard"])]
            dy = step
            while dy <= maxshift:
                lane = (gcy + dy - gh / 2, gcy + dy + gh / 2)  # clear of EVERY east tree (a small shift can slip INTO a taller arm)
                if not any(overlaps(lane, t) for t in trees):
                    shifted = [(b[0], b[1] + dy, b[2], b[3]) for b in beds]
                    if self._garden_beds_clear(shifted, others):
                        geom["gardens"] = shifted
                        break
                dy += step

    def _kura_side(self: Settlement, rec: dict[str, Any], w: float, h: float) -> str:  # type: ignore[misc]
        """Which wall a LEGACY farmstead's kura stands against - "W" (the dispersed-farm default in
        `house()`) or "N" (the shaded back wall a nucleated farm uses).

        WHY THIS IS DECIDED AT DRAW TIME (Minami 2026-08-08, a farm shed drawn on a neighbor's
        garden). A legacy farmhouse reserves only its own base rect, while the west kura is drawn
        reaching 0.30 x the house's width PAST that rect - the standing "placement tests a
        different footprint than the one drawn" debt (dev-loop CLAUDE.md, CENTER vs FOOTPRINT item
        3). The nucleated bundle answers it by RESERVING the kura's ground; the legacy path cannot,
        because it places one house at a time against ground whose gardens and yards are not drawn
        yet. But by the flush every appurtenance IS drawn, so the side can simply be CHOSEN here,
        with no placement change and so no reflow of the belt. If both walls are fouled the west
        stands and the overlap matrix reports it - the engine does not get to hide a homestead with
        no room for its own storehouse."""
        th = math.radians(rec.get("rot", 0))
        ca, sa = math.cos(th), math.sin(th)
        # the two kura footprints, in the house's local frame - MUST match house()'s _sox/_soy/_ssw/_ssh
        sides = {"W": (-0.64 * w, 0.0, 0.32 * w, 0.56 * h), "N": (0.0, -0.60 * h, 0.46 * w, 0.30 * h)}
        # every DRAWN appurtenance of every farmstead, this one's included: the check does not care
        # whose garden a kura laps, and a house's own bed is as much a collision as a neighbor's
        near = [o for k in ("gardens", "threshing_yards", "farm_sheds", "byres") for o in (self.M.get(k) or []) if abs(o["x"] - rec["x"]) < 3 * w and abs(o["y"] - rec["y"]) < 3 * w]
        near += [o for o in self.M.get("houses") or [] if o is not rec and abs(o["x"] - rec["x"]) < 3 * w and abs(o["y"] - rec["y"]) < 3 * w]
        for side, (ox, oy, kw, kh) in sides.items():
            kx, ky = rec["x"] + ox * ca - oy * sa, rec["y"] + ox * sa + oy * ca
            khw, khh = (abs(kw * ca) + abs(kh * sa)) / 2, (abs(kw * sa) + abs(kh * ca)) / 2
            if not any(abs(kx - o["x"]) < khw + o["w"] / 2 and abs(ky - o["y"]) < khh + o["h"] / 2 for o in near):
                return side
        return "W"

    def _farmsteads_legacy(self: Settlement) -> int:  # type: ignore[misc]
        """Draw every deferred farmhouse WITH its threshing/drying YARD (south/front apron) AND its dooryard
        kitchen GARDEN (a sunny side, preferring the east) - both were universal to a farmstead, so every
        farmhouse has one of each. Find spots for both; if they don't fit, nudge the house a little; draw
        garden + yard then the house so the house wins any abutment. A house that cannot host BOTH anywhere
        nearby is dropped (rare) so the 100% invariants hold. Call LAST in the gen. Returns the count."""
        survivors: list[Any] = []
        for rec in self._pending_farmsteads:
            spot = self._solve_homestead(rec)  # shift the homestead to fit yard+garden+grove-room
            if spot is None:
                fp = (rec["x"], rec["y"], rec["w"], rec["h"])
                self.placed = Indexed(p for p in self.placed if p != fp)  # drop the un-appurtenanced farmhouse (rare); Indexed for the same reason as the lift above
                continue
            yard_spot, garden_spot = spot
            self._attach_garden(rec["x"], rec["y"], [garden_spot])  # legacy farms keep ONE bed (multi-bed split is nucleated)
            self._attach_yard(rec["x"], rec["y"], yard_spot)
            survivors.append(rec)
        # SECOND PASS FOR THE HOUSES THEMSELVES, so every yard and garden on the belt is drawn and
        # recorded before the first roof goes down (2026-08-08). It buys two things and costs no
        # geometry - `house()` only DRAWS, the footprint was reserved back in `_try_place_legacy`:
        # `_kura_side` can see the neighbors it has to dodge (in one pass it saw only the farmsteads
        # flushed before it, and Minami's kura duly landed on a garden drawn two houses later), and
        # a roof now paints over EVERY garden it abuts rather than only the ones already down -
        # which is the "draw garden + yard then the house so the house wins any abutment" rule this
        # loop always intended, applied across the belt instead of per homestead.
        for rec in survivors:
            # DRAW the house at its WEALTH size - a modest +/-~10% on the rendered glyph only. The manifest keeps
            # w,h at the BASE footprint (what the reservation, the yard/garden, and the overlap checks use, so
            # the variation never causes a drop or a shed/garden clash); the `wealth` factor records the render
            # scale and the grove (below) scales with it.
            wf = rec["wealth"]
            side = self._kura_side(rec, rec["w"] * wf, rec["h"] * wf) if rec["shed"] else "W"
            if rec["shed"]:
                rec["shed_side"] = side
            self.house(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf, rec["kind"], rec["rot"], shed=rec["shed"], shed_side=side)
        self.M["houses"] = [h for h in self.M["houses"] if h.get("on_dike")] + survivors  # dike-top houses (dike_top_houses) are not pending farmsteads - keep them
        # SECOND PASS - the windward homestead groves (yashikirin). Run AFTER every farmhouse + its yard +
        # garden is placed, so a grove (an optional flourish) can NEVER block a neighbor's MANDATORY yard/
        # garden and drop that house. Near-universal (meta.grove_prevalence), but OFF for a farm inside a
        # CITY wall (an intramural plot is not an isolated farmstead - it is sheltered by the urban fabric
        # and sits on land too precious for a tree belt; meta(inwall_groves=True) to override). A farm whose
        # windward side is boxed in goes without. Returns the farmhouse count.
        meta = self.M["meta"]
        wall: Any = self.M.get("wall")
        inwall_off = bool(wall) and meta.get("scale") in CITY_TIER_SCALES and not meta.get("inwall_groves", False)
        for rec in survivors:
            if inwall_off and point_in_poly(rec["x"], rec["y"], wall):
                continue
            if self._grove_candidate(rec["x"], rec["y"]):
                wf = rec["wealth"]  # a wealthier farm's bigger house carries a bigger grove
                arms = self._find_grove_arms(rec["x"], rec["y"], rec["w"] * wf, rec["h"] * wf)
                if arms:
                    self._attach_grove(rec["x"], rec["y"], arms)
        return len(survivors)

    def _perim_bbox(self: Settlement, bbox: Any, n: int, gap: float) -> list[Pt]:  # type: ignore[misc]
        x0, y0, x1, y1 = bbox
        bw, bh = x1 - x0, y1 - y0
        per = 2 * (bw + bh)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.18, 0.82)) / n * per
            if d < bw:
                x, y, nx, ny = x0 + d, y0, 0, -1
            elif d < bw + bh:
                x, y, nx, ny = x1, y0 + (d - bw), 1, 0
            elif d < 2 * bw + bh:
                x, y, nx, ny = x1 - (d - bw - bh), y1, 0, 1
            else:
                x, y, nx, ny = x0, y1 - (d - 2 * bw - bh), -1, 0
            g = gap + random.uniform(4, gap * 0.85)
            pts.append((x + nx * g + random.uniform(-10, 10), y + ny * g + random.uniform(-10, 10)))
        return pts

    def _perim_poly(self: Settlement, poly: Any, n: int, gap: float) -> list[Pt]:  # type: ignore[misc]
        area = _signed_area(poly)
        seglen = [math.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))]
        per = sum(seglen)
        pts: list[Pt] = []
        for k in range(n):
            d = (k + random.uniform(0.2, 0.8)) / n * per
            acc: float = 0
            for i, sl in enumerate(seglen):
                if acc + sl >= d:
                    f = (d - acc) / sl if sl else 0
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % len(poly)]
                    px, py = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
                    dx, dy = x2 - x1, y2 - y1
                    L = math.hypot(dx, dy) or 1
                    nx, ny = (dy / L, -dx / L) if area > 0 else (-dy / L, dx / L)
                    gg = gap + random.uniform(4, gap * 0.85)
                    pts.append((px + nx * gg + random.uniform(-10, 10), py + ny * gg + random.uniform(-10, 10)))
                    break
                acc += sl
        return pts

    def ring(self: Settlement, shape: Any, n: int, gap: float, kinds: Any, max_big: int = 4) -> None:  # type: ignore[misc]
        """Ring a field with houses. shape: bbox tuple, or ('poly', smoothed_outline)."""
        # SCOPED (2026-08-08): _perim_bbox / _perim_poly jitter the ring's candidate SEATS from the
        # stream, so an upstream change moved every farmhouse a town rings its fields with - and the
        # yards, gardens, sheds and groves that hang off them. Keyed on the shape being ringed.
        with self.rng_scope("ring", *(shape[1][0] if isinstance(shape, tuple) and shape and shape[0] == "poly" else shape)):
            cand = self._perim_poly(shape[1], n, gap) if isinstance(shape, tuple) and shape and shape[0] == 'poly' else self._perim_bbox(shape, n, gap)
            # A ring farm must REACH the field it rings without crossing a ROAD (drives
            # farmsteads_reach_their_fields_unsevered; hoshizora's lone south-of-road farmhouse inside
            # the merchant block, GM 2026-08-02). ROADS only - a stream is crossed by footbridges (the
            # NW-bank farms are deliberate) and lanes/streets are village grain. FAMILY: association/
            # reach, deliberately center-based - the question is which side of the highway the steading
            # lives on, not a clearance. Reads the same M["roads"] record as the check.
            outline = shape[1] if isinstance(shape, tuple) and shape and shape[0] == 'poly' else [(shape[0], shape[1]), (shape[2], shape[1]), (shape[2], shape[3]), (shape[0], shape[3])]
            ring_roads = [r["pts"] for r in self.M.get("roads", [])]

            def _severed(hx: float, hy: float) -> bool:
                px, py = min(outline, key=lambda p: (p[0] - hx) ** 2 + (p[1] - hy) ** 2)
                return any(segments_cross((hx, hy), (px, py), rp[i], rp[i + 1]) for rp in ring_roads for i in range(len(rp) - 1))

            for x, y in cand:
                # POSITION-SEEDED, not a stream draw (2026-08-08). This one line was the whole reason a
                # town re-rolled when something unrelated changed upstream: the kind decides the
                # footprint, the footprint decides whether the homestead fits, and one different fit
                # cascades into every house, garden, yard, grove, well and tree crown on the map (13 of
                # hoshizora's 71 manifest keys, from ONE extra random draw at the top of the gen). Drawn
                # off the position, the ring is a function of where the field is, full stop. The ordering
                # note that used to sit above - keep the severed test AFTER this draw so the stream stays
                # identical - is moot now and has been deleted rather than maintained.
                k = kinds[int(self._hjit(x, y, 7.0) * len(kinds))]
                if ring_roads and _severed(x, y):
                    continue
                if k == "big":
                    if self._nbig >= max_big:
                        k = "plain"
                    else:
                        self._nbig += 1
                if not self.try_place(x, y, k) and k == "big":
                    self._nbig -= 1
