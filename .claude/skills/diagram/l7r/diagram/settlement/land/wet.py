"""WET GROUND: the reed marsh, the contour band that decides where it lies, the trim that keeps a
way out of it, and the package's one surface-water distance predicate.

The BAND is the load-bearing idea. Wet ground is defined by HEIGHT, so `toe_band` returns a CONTOUR
band perpendicular to the fall rather than an axis-aligned box - a rectangle is only an honest
contour at a 0/90/180/270 fall, and at a diagonal it slices across the slope. Its WIDTH comes from
the ground the fan waters, never from the canvas: an alluvial fan's spring line follows the FAN's
toe, and a floodplain's backswamp is bounded by its natural levees, so wet ground is FEATURE-bounded
in both landforms (research/water.md, 'The wet toe is as wide as the FAN'). Both corrections are
argued at length in the members themselves; read them before changing either.

`surface_water_dist` is module-level rather than a mixin method: it takes a MANIFEST, not a
Settlement, and it is the ONE predicate shared by the gate's `settlement_dwellings_watered` and by
`hamletgen.place_wells` - written that way because the two had drifted into separate definitions of
"needs a well". It lives in this module because it is this package's water-distance question.
`settlement/__init__.py` re-exports it, so consumers import it from `settlement` and never from
here.

Split from settlement/land.py by feature 120 - see settlement/land/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Pt, boxed_grid, boxed_hit, boxed_polys, boxed_seg_hit, boxed_segs, edge_dist, point_in_poly, seg_dist

if TYPE_CHECKING:
    from ..core import Settlement


class WetGroundMixin:
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
        blades: list[str] = []  # SVG-size lever 2: bucket the constant-styled reed blades (see the note in cover.py's `commons`)
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


def surface_water_dist(M: Any, x: float, y: float) -> float:
    """Distance from (x, y) to the nearest SURFACE water - irrigation channel, stream, or moat
    polyline, or the pond's rim - reading exactly the manifest records
    `settlement_dwellings_watered` reads. ONE predicate, shared by that gate check and by
    `hamletgen.place_wells` (known-open ledger 2026-08-16: the well minimax objective counted
    stream-watered houses as needing a well while the check already treated them as watered -
    the objective and the check read two definitions of "needs a well"). Wells are deliberately
    NOT included: the caller asking "does this house need a well" must not have the answer
    pre-empted by the wells it is deciding to dig."""
    # AN IRRIGATION DITCH IS NOT DOMESTIC WATER (ruled 2026-08-18; settlement-review, Sawada, found
    # the mechanism and did the research pass). This used to count `channels` too, and that made the
    # answer depend on WHICH MANIFEST KEY a watercourse happened to be recorded under rather than on
    # what kind of water it is: on a comb-field map `channels` holds one short intake stub while the
    # thirteen real watercourses live in `drawn_channels`, so Sawada counted 13 of 19 houses as
    # watered by a stub, and Mizuguchi's well objective had **zero** clients - it was optimizing
    # nothing at all, silently. Had `drawn_channels` been the key read instead, every house on every
    # comb map would have been "watered" and no hamlet would ever have dug a well.
    #
    # The research says the exclusion is right and only the mechanism was accidental: domestic water
    # came from a well or a spring, while ditch water served washing at a dedicated *kawado* stand -
    # a field ditch is seasonal, silty and fouled by the paddies it feeds, and nobody drank from it.
    # So the predicate now names the water it means. A STREAM is a living watercourse a household
    # draws from; a MOAT and a CANAL are the town/city equivalents, permanent and open; a POND is a
    # tameike. An irrigation channel is field infrastructure, whichever key it is recorded under.
    #
    # Measured cost, and it is the point rather than a side effect: the houses that actually need a
    # well go 5 -> 8 on Inashiro, 3 -> 9 on Kashikawa, 0 -> 5 on Mizuguchi and 6 -> 9 on Sawada, so
    # the minimax objective and the coverage pass finally have the clients the doctrine says they
    # have. The GM may reverse this; it is recorded in `future-work/`.
    d = 1e9
    for ln in [c["poly"] for c in M.get("canals", []) if c.get("poly")] + [st["poly"] for st in M.get("streams", [])] + ([M["moat"]] if M.get("moat") else []):
        for i in range(len(ln) - 1):
            d = min(d, seg_dist(x, y, ln[i], ln[i + 1]))
    pond = M.get("pond")
    if pond:
        d = min(d, abs(math.hypot(x - pond[0], y - pond[1]) - max(pond[2], pond[3])))
    return d
