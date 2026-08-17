"""Roll a whole gate-passing settlement from the seed: the knobs, the field, the cluster band, the civic features.

Split from settlement/rolling.py by feature 118 - see settlement/rolling/CLAUDE.md for the index.
"""

import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .._geom import BUNDLE_PITCH_FT, Pt
from .._knobs import knob_rng, roll_torii_count, skeleton_layout

if TYPE_CHECKING:
    from ..core import Settlement


class RollVillageMixin:
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
