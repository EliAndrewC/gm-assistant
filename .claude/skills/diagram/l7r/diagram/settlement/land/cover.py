"""The DRY ground cover, the layout that lays it, and the swept verge it must skip.

`commons` is the feathered scatter - coarse grass and brush with a few scraggly pines, open grazing
grass, or a spaced coppice canopy, by `role`. `hinterland` is the COMPOSER: it decides which frame
sides carry scrub, which side is the downhill toe, and fills the interior voids an irregular field
leaves inside its own bbox; it asks wet.py for the toe band and hands it to `commons` as a keep-out
so the two never overlap. `_clear_ground` / `reserve_clearing` reserve the swept ground around a
sacred or funerary feature.

The verge belongs in THIS module rather than with the features it protects, because the scatters are
what must skip it: `clearings` is a keep-out registry this module both writes and reads, and a
clearing registered after its scatter has run does nothing at all (`scatter_respects_swept_
clearings` checks exactly that ordering).

NO SOLID FILL is the rule the scatters are built on. A filled polygon always has a crisp geometric
EDGE, so each land type is defined PURELY by cover that thins to nothing at its margin - the ground
has no boundary, just its cover petering out.

Split from settlement/land.py by feature 120 - see settlement/land/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import Poly, boxed_grid, boxed_hit, boxed_polys, boxed_seg_hit, boxed_segs, edge_dist, point_in_poly

if TYPE_CHECKING:
    from ..core import Settlement


class GroundCoverMixin:
    def commons(self: Settlement, poly: Any, role: str = "commons", avoid: Any = (), render: str = "scrub") -> None:  # type: ignore[misc]
        """FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far (upslope / windward) side,
        BEYOND the fengshui back-grove: coarse grass, low brush, and a FEW scattered SCRAGGLY pines, kept
        cropped bare by constant firewood + grass gathering. Deliberately drawn OPEN and SPARSE on drier,
        poorer ground so it is VISUALLY DISTINCT from the dense, dark, closed-canopy village grove - this is a
        COMMONS (not anyone's field), non-arable. WHY (south China's hills were stripped for fuel/timber over a
        millennium - open pine + grass + erosion; the protected grove is the green EXCEPTION; the back slope
        also carried the graves + dry hill-crops): settlements.md 'Village windbreak' / back-slope land use. Recorded
        in M['commons']. `role` picks the glyph (woodland / pasture / commons); `avoid` is a list of KEEP-OUT
        polygons (e.g. the hamlet cluster) the scatter stays out of, so ground-cover never creeps onto them."""
        # SCOPED (2026-08-08): the tuft/brush scatter is decoration keyed to the common it fills.
        if render == "bare":
            # CLAIMED but UNDRAWN ground (GM 2026-08-10, on the capital's ring bands reading as
            # weeds): the record still claims the ground for the empty-space detector and names
            # its role, but nothing is scattered - kept working ground reads as clean parchment,
            # not scrub. The default stays "scrub" so every village commons is byte-identical.
            xs0 = [q[0] for q in poly]
            ys0 = [q[1] for q in poly]
            self.M.setdefault("commons", []).append(
                {
                    "x": round(sum(xs0) / len(xs0), 1),
                    "y": round(sum(ys0) / len(ys0), 1),
                    "w": round(max(xs0) - min(xs0), 1),
                    "h": round(max(ys0) - min(ys0), 1),
                    "rot": 0,
                    "role": role,
                    "seq": len(self.M.get("commons", [])) + 1,
                    "poly": [list(q) for q in poly],
                }
            )
            return
        with self.rng_scope("commons", len(poly), poly[0][0], poly[0][1]):
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            bs = self.bscale
            area = (x1 - x0) * (y1 - y0)
            st = random.getstate()
            random.seed(int(abs(x0) * 7 + abs(y0) * 3 + round(x1 - x0)))
            feather = 42 * bs  # scrub THINS toward the boundary (a soft, ragged edge, not a hard line)

            pond = self.M.get("pond")
            halo_rects, halo_circles = self._urban_keepouts((x0, y0, x1, y1))  # the urban-clearance halo (see _urban_keepouts)
            corridors = self._corridor_buffers(
                3 * bs
            )  # lanes AND town streets AND the road: every trodden/maintained tread stays bare (the old skip knew only lanes, so scrub drew on the Imperial Road bed - GM 2026-07-21, Hoshizora)
            # PRE-BOX every static keep-out ONCE (see boxed_hit): _sparse below runs per SCATTER POINT,
            # and these lists do not change while a region scatters
            # INDEXED (2026-08-04): boxing alone dropped the cost per keep-out but still VISITED every
            # one per scatter point - 948k boxed_hit calls iterating 25M items on Kikuta, whose gen was
            # still 81% ground cover. The grids narrow each point to its own cell; the exact tests below
            # are the same ones, run on what `near` returns.
            # CROP MARGIN (see _CROP_MARGIN_FT): the crop keep-out is every PADDY (field_polys) plus
            # every DRY PLOT (dry_polys - block_polys also carries them, but reading the crop registry
            # directly is what the grove/lane skips do, and it survives a gen that registers only one),
            # padded by the margin. Boxes carry the WORST-CASE pad - margin plus the tallest glyph's
            # drawn reach, a pine tip at 14*bs - because the bbox prefilter must never reject a point
            # the exact edge test wants (boxed_hit's contract); the exact test gets the per-glyph lean.
            crop_pad = self.px(self._CROP_MARGIN_FT)
            fld_b = boxed_grid(boxed_polys(list(self.field_polys) + list(self.dry_polys), pad=crop_pad + 14 * bs))
            blk_b = boxed_grid(boxed_polys(self.block_polys))
            clr_b, avd_b, cor_b = boxed_grid(boxed_polys(self.clearings)), boxed_grid(boxed_polys(avoid)), boxed_grid(boxed_segs(corridors))
            # drawn water pre-boxed once (see _watercourse_segs); irrigation channels additionally
            # carry the CUT-BANK margin (_BANK_MARGIN_FT - a maintained bank is scythed like a field
            # margin), streams stay at drawn width so the brook's natural bank keeps its grass
            wat_b = boxed_grid(boxed_segs(self._watercourse_segs(channel_margin=self.px(self._BANK_MARGIN_FT))))

            def _sparse(
                px: float, py: float, drop: float, lean: float = 0.0
            ) -> bool:  # skip a scatter point outside the poly, on/near a crop, on a corridor/water, in the urban halo, in a keep-out, or (probabilistically) near the edge; `lean` = the glyph's drawn reach, so a tall glyph stands its own height back from the crop margin
                if (
                    not point_in_poly(px, py, poly)
                    or boxed_hit(px, py, fld_b.near(px, py), edge_pad=crop_pad + lean)
                    or boxed_seg_hit(px, py, cor_b.near(px, py))  # keep scrub off every trodden tread (lane/street/road) so no path reads overgrown
                    or self._on_watercourse(px, py, near=wat_b.near)  # ... and OFF the pond + streams/channels (scrub never draws over open water)
                    or (pond and ((px - pond[0]) / pond[2]) ** 2 + ((py - pond[1]) / pond[3]) ** 2 <= 1.0)
                    or any(
                        x0r <= px <= x1r and y0r <= py <= y1r for x0r, y0r, x1r, y1r in halo_rects
                    )  # ... and OUT of the urban-clearance halo: the swept/trodden ground around every structure, not just its footprint
                    or any((px - hx) ** 2 + (py - hy) ** 2 <= hr * hr for hx, hy, hr in halo_circles)  # ... and clear of every wellhead's trodden apron
                    or boxed_hit(px, py, blk_b.near(px, py))  # ... and OFF any building/shrine/torii footprint (a commons that OVERLAPS the shrine must not scatter scrub over the hall + arch)
                    or boxed_hit(px, py, clr_b.near(px, py))  # ... and off the swept sacred/funerary verge (tended precinct, sando, grave collar)
                    or boxed_hit(px, py, avd_b.near(px, py))
                ):  # ... and OUT of any keep-out (the hamlet cluster stays clear of cover)
                    return True
                ed = edge_dist(px, py, poly)
                return ed < feather and random.random() > (ed / feather) ** drop

            # NO solid fill: a filled polygon always has a crisp geometric EDGE (that read as a rhombus). Each land
            # type is defined PURELY by its feathered scatter, which thins to nothing at the margin - so the ground
            # has no boundary at all, just its cover petering out onto the open slope. THREE distinct looks so land
            # types read apart at a glance (the GM's rule - grass and woods must NOT look the same):
            #   role="woodland"  -> a COPPICE WOOD: individual, spaced tree CROWNS, an OPEN canopy (gaps show) - the
            #                       upland/ridge wood the hamlet coppices. Clearly TREES, but lighter and more open
            #                       than the dense DARK closed-canopy fengshui village grove (they stay distinct too).
            #   role="pasture"   -> OPEN GRAZING GRASS: grass tufts + the odd brush dot, NO trees at all - reads as
            #                       open pasture, unmistakably NOT woodland.
            #   role="commons"/"grazing" (default) -> the cut-over fuel/fodder scrub: grass + a FEW scraggly pines.
            # SVG-size: the grass BLADES are ~98% of a to-scale map's <line> elements and all share ONE constant
            # style, so they go in a bucket emitted ONCE inside a styled <g> (bare coords per line), not one full
            # stroke=...stroke-width=... string each - ~30% off the file, content-lossless (same lines, grouped),
            # render is visually identical (only the z-order of overlapping scrub texture shifts, in the margins;
            # the fields/buildings are pixel-identical). The sparse dots/pines keep their inline styles.
            g: list[str] = []
            blades: list[str] = []
            _wd_crowns = 0
            if role == "woodland":
                # A TARGET, NOT AN ATTEMPT COUNT (settlement-review x3, 2026-08-18 round 2 - Inashiro,
                # Sawada and Mizuguchi found it independently). `int(area / 540)` looks like a density
                # and is not: it is the number of THROWS, and `_sparse` rejects a share of them, so the
                # realized spacing depends on how much of a parcel lies near a keep-out. Small parcels
                # are proportionally more edge, so they came out both smaller AND thinner - measured
                # 691-768 sq ft per crown on the big stands against 981 on Sawada's and 1101 on
                # Inashiro's smallest, which at ~31% canopy reads as scattered trees on grass rather
                # than a wood. The size-variance work made that worse rather than better: growing
                # Sawada's parcel 125 -> 136 ft added no crowns at all, so the sparsest object on the
                # sheet got sparser.
                #
                # A coppice is a worked thicket cut on rotation, and the sources describe the SMALL
                # parcels near a settlement as the intensively worked ones - so density must not fall
                # away with size. Throwing until the target is MET (capped, so a parcel that genuinely
                # cannot hold its quota still terminates) makes the realized density the stated one on
                # every parcel. The draws stay inside this function's `random.setstate` scope, so the
                # extra throws cannot ripple into anything drawn later.
                _wd_target = int(area / (540 * bs * bs))
                for _ in range(_wd_target * 6):
                    if _wd_crowns >= _wd_target:
                        break
                    cx, cy = random.uniform(x0, x1), random.uniform(y0, y1)
                    if _sparse(cx, cy, 0.6, 11.5 * bs):  # lean = the largest crown radius, so no canopy overhangs a crop
                        continue
                    r = random.uniform(6.5, 11.5) * bs
                    col = random.choice(("#6E8B4A", "#7C9856", "#87A45C"))
                    # RECORD the crown (known-open ledger 2026-08-16, both review rounds
                    # independently): these used to be SVG ink only, so no manifest check could
                    # count a stand's canopy - which is how a zero-crown "woodland" parcel could
                    # ship green. Same flat [x, y, r] run the homestead groves use.
                    self.M["tree_crowns"] += [round(cx, 1), round(cy, 1), round(r, 1)]
                    _wd_crowns += 1
                    g.append(f'<ellipse cx="{cx:.1f}" cy="{cy + 2 * bs:.1f}" rx="{r:.1f}" ry="{r * 0.72:.1f}" fill="#59703E" fill-opacity="0.30"/>')  # soft ground shadow
                    g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{col}" stroke="#4C6234" stroke-width="0.7"/>')  # the crown
                    g.append(f'<circle cx="{cx - r * 0.32:.1f}" cy="{cy - r * 0.32:.1f}" r="{r * 0.42:.1f}" fill="#A6BA79" fill-opacity="0.55"/>')  # sun highlight
            else:
                for _ in range(int(area / (74 * bs * bs))):  # coarse grass tufts + the odd low brush dot
                    gx, gy = random.uniform(x0, x1), random.uniform(y0, y1)
                    if _sparse(gx, gy, 0.7):
                        continue
                    if random.random() < 0.14:  # a low brush dot
                        g.append(f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="{random.uniform(1.5, 2.4) * bs:.1f}" fill="#94A063" fill-opacity="0.85"/>')
                    else:  # a grass tuft: a few short diverging blades (bucketed - see the note at `blades`)
                        for _ in range(3):
                            a, bl = random.uniform(-0.45, 0.45), random.uniform(2.4, 4.2) * bs
                            blades.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{gx + math.sin(a) * bl:.1f}" y2="{gy - math.cos(a) * bl:.1f}"/>')
                if role != "pasture":  # the SCRAGGLY pines belong to cut-over scrub, NOT to open pasture
                    for _ in range(max(2, int(area / (6000 * bs * bs)))):  # a few SCRAGGLY hill pines (sparse, individual, open)
                        px, py = random.uniform(x0 + 6, x1 - 6), random.uniform(y0 + 6, y1 - 6)
                        if _sparse(px, py, 0.5, 14 * bs):  # lean = the tallest pine's tip reach, so no pine leans over a crop
                            continue
                        th = random.uniform(9, 14) * bs
                        g.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py - th:.1f}" stroke="#7A6A48" stroke-width="{1.1 * bs:.1f}"/>')  # thin trunk
                        for k in range(3):  # sparse open branches - a scraggly wind-cropped pine, NOT a dense crown
                            ly, sp = py - th * (0.45 + 0.25 * k), (3.6 - k) * bs
                            g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px - sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
                            g.append(f'<line x1="{px:.1f}" y1="{ly:.1f}" x2="{px + sp:.1f}" y2="{ly + 2 * bs:.1f}" stroke="#6E8452" stroke-width="{1.0 * bs:.1f}"/>')
            self.add(f'<g stroke="#A7A860" stroke-width="0.8">{"".join(blades)}</g>')  # bucketed blades (empty group when none - harmless)
            self.add(''.join(g))
            random.setstate(st)
            self._cover_n += 1
            if role == "woodland":
                # ...and the parcel is a KEEP-OUT placers actually honor (the Sawada merged-roll
                # review's placer-side ask): nothing packs after the woodland today, but a future
                # placer reading crown records rather than the commons poly would otherwise seat
                # a structure under this canopy with nothing firing. Center-tested by _fits like
                # every block poly.
                self.block_polys.append([(float(px0), float(py0)) for px0, py0 in poly])
            self.M["commons"].append(
                {
                    "x": round((x0 + x1) / 2, 1),
                    "y": round((y0 + y1) / 2, 1),
                    "w": round(x1 - x0, 1),
                    "h": round(y1 - y0, 1),
                    "rot": 0,
                    "role": role,
                    "seq": self._cover_n,
                    **({"crowns": _wd_crowns} if role == "woodland" else {}),
                    "poly": [[round(px, 1), round(py, 1)] for px, py in poly],
                }
            )

    def hinterland(  # type: ignore[misc]
        self: Settlement,
        down_deg: Any = None,
        *,
        marsh: bool = True,
        commons: bool = True,
        interior_fill: bool = True,
        pad: float = 90,
        marsh_role: str = "toe",
        scrub_role: str = "grazing",
        skip_sides: Any = (),
    ) -> None:
        """Lay out a settlement's non-arable HINTERLAND: a reed MARSH at the downhill TOE (below the paddy's
        drainage line, where wet-rice reclamation stops and the valley floor stays reed wetland) and the
        cut-over SCRUB commons (coarse grass + a few scraggly pines) filling the surrounding non-arable margins.
        CHINA-FIRST: the south-China rice hills were stripped for fuel/timber over ~1,000 years, so the DOMINANT
        cover past the settlement is denuded scrub/rough grazing, NOT forest - the protected fengshui grove is
        the green exception, and the managed WOODLAND (coppice / bamboo / tung / tea-oil 'economic forest') is a
        FEW discrete PATCHES the gen adds by hand on the higher / farther ground (`s.commons([...],
        role='woodland')`), set back from the sun-needing crops by the scrub between. So hinterland lays the
        scrub + marsh; the woodland patches are per-map. The scrub bands are frame-margin strips OUTSIDE the
        CULTIVATED bbox (paddy + dry hatake), so each recorded centroid clears the paddy (`commons_clear_of_
        paddies` is a centroid test). All scatters skip fields/pond/lanes/buildings AND a **hamlet keep-out**
        (the cluster bbox, so no cover creeps among the houses), and NONE is a crop anchor (`_CROP_HARD`), so
        they BLEED off the frame and the crop stays tight. Call AFTER fields + cluster + pond + dry fields,
        BEFORE crop_to_content. `down_deg` (defaults to meta's) picks which frame side the scrub ring OMITS
        (the toe side) AND orients the marsh itself: the toe is a CONTOUR BAND perpendicular to the fall, so it
        rotates with the map like every other feature (see the comment at the marsh block); the scrub ring is
        radial. A comb-FAN field leaves the opposite bbox corner open -> the gen fills it (scrub +
        woodland patches). See settlements.md 'Hinterland (water-flow-keyed)'."""
        if down_deg is None:
            down_deg = self.M.get("meta", {}).get("down_deg", 90)
        polys = self.field_polys
        if not polys:
            return
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        for dp in self.M.get("dry_plots", []):  # the CULTIVATED extent includes the dry hatake plots
            xs += [p[0] for p in dp["poly"]]
            ys += [p[1] for p in dp["poly"]]
        fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
        W, H = self.W, self.H
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        # SETTLEMENT KEEP-OUT, so cover never scatters among the dwellings. Its SHAPE depends on the form:
        avoid: list[Any] = []
        hs = self.M.get("houses", [])
        m = 44
        if hs and self.M.get("meta", {}).get("nucleated", True):
            # NUCLEATED: the houses are one tight blob, so the bbox of their positions IS the built footprint.
            hxs, hys = [h["x"] for h in hs], [h["y"] for h in hs]
            avoid.append([(min(hxs) - m, min(hys) - m), (max(hxs) + m, min(hys) - m), (max(hxs) + m, max(hys) + m), (min(hxs) - m, max(hys) + m)])
        elif hs:
            # DISPERSED: the farmsteads RING the settlement, so a bbox of their positions is not their footprint
            # - it is the WHOLE MAP, and using it forbids ground cover everywhere inside the ring. That is what
            # left Akagahara's fan void as bare clay (GM: "a ton of empty space between the ditch and the
            # marsh"): the void fell inside this blanket, so neither the scrub ring nor anything else could
            # clothe it. Keep out each HOMESTEAD individually instead - house plus its bundle (yard, garden,
            # grove) - so the open ground BETWEEN the strewn farms is free to carry rough grazing, as it should.
            for key in ("houses", "gardens", "threshing_yards", "groves"):
                for r in self.M.get(key, []):
                    hw, hh = r.get("w", 40) / 2 + m, r.get("h", 30) / 2 + m
                    avoid.append([(r["x"] - hw, r["y"] - hh), (r["x"] + hw, r["y"] - hh), (r["x"] + hw, r["y"] + hh), (r["x"] - hw, r["y"] + hh)])
        # which frame side is the downhill TOE (marsh) - the other three carry the scrub commons
        toe_side = ("bottom" if dy >= 0 else "top") if abs(dy) >= abs(dx) else ("right" if dx >= 0 else "left")

        BLEED = 120  # a band reaches the canvas edge + this bleed, NOT `outer` beyond it
        # (clamping the OUTER extent to the canvas avoids scattering a huge off-canvas apron of scrub that only
        #  bloats the SVG node count - the frame clips it anyway; the on-canvas cover is unchanged)

        def ring(inner: float, outer: float) -> list[Any]:
            """The four picture-frame side-strips between the cultivated bbox grown by `inner` and by `outer`
            (outer clamped to the canvas + bleed), MINUS the toe side (marsh) and any `skip_sides` (e.g. a forest
            flank). Each strip lies outside the bbox -> centroid clears the paddy."""
            ox0, oy0 = max(-BLEED, fx0 - outer), max(-BLEED, fy0 - outer)
            ox1, oy1 = min(W + BLEED, fx1 + outer), min(H + BLEED, fy1 + outer)
            ix0, iy0, ix1, iy1 = fx0 - inner, fy0 - inner, fx1 + inner, fy1 + inner
            sides = {
                "top": [(ox0, oy0), (ox1, oy0), (ox1, iy0), (ox0, iy0)],
                "bottom": [(ox0, iy1), (ox1, iy1), (ox1, oy1), (ox0, oy1)],
                "left": [(ox0, iy0), (ix0, iy0), (ix0, iy1), (ox0, iy1)],
                "right": [(ix1, iy0), (ox1, iy0), (ox1, iy1), (ix1, iy1)],
            }
            return [v for k, v in sides.items() if k != toe_side and k not in skip_sides]

        def toe_strip(inner: float, outer: float) -> list[Any]:
            """The one strip `ring` leaves out - the toe side - for the scrub that flanks the reeds."""
            ox0, oy0 = max(-BLEED, fx0 - outer), max(-BLEED, fy0 - outer)
            ox1, oy1 = min(W + BLEED, fx1 + outer), min(H + BLEED, fy1 + outer)
            ix0, iy0, ix1, iy1 = fx0 - inner, fy0 - inner, fx1 + inner, fy1 + inner
            return {
                "top": [(ox0, oy0), (ox1, oy0), (ox1, iy0), (ox0, iy0)],
                "bottom": [(ox0, iy1), (ox1, iy1), (ox1, oy1), (ox0, oy1)],
                "left": [(ox0, iy0), (ix0, iy0), (ix0, iy1), (ox0, iy1)],
                "right": [(ix1, iy0), (ox1, iy0), (ox1, iy1), (ix1, iy1)],
            }[toe_side]

        # THE TOE SIDE IS NOT ALL MARSH ANY MORE, so the scrub has to finish the job (settlement-review,
        # 2026-08-12). `ring()` drops the whole toe-side strip, which was right while the toe ran edge
        # to edge - the reeds covered every inch below the crop. Now the band is only as wide as the
        # ground the fan waters, so the ground past its lateral ends was covered by NEITHER, and
        # Ikegami shipped a ~267 x 193 ft corner of blank parchment with the connector crossing it
        # (measured 2.2% ink against 23.7% in the scrub band immediately above). Rough grazing is
        # exactly what stands on a dry footslope beside a reed flat, so the toe side gets the same
        # scrub as the other three - handed the marsh as a keep-out, so it stops where the reeds start
        # and the two never overlap. Computed BEFORE the commons pass for that reason.
        toe_poly = self.toe_band(down_deg, pad) if marsh else []
        if commons:
            for p in ring(0, max(W, H)):  # the cut-over SCRUB commons: the DOMINANT denuded-hill cover
                self.commons(p, role=scrub_role, avoid=avoid)  # (managed woodland is added as a FEW patches by the gen)
            if toe_poly and toe_side not in skip_sides:
                self.commons(toe_strip(0, max(W, H)), role=scrub_role, avoid=[*avoid, toe_poly])
            # ...and the INTERIOR. The ring lays strips only OUTSIDE the cultivated bbox, but an irregular field
            # (a comb FAN) does not fill its own bbox: it leaves open VOIDS INSIDE it that nothing else clothes
            # - the strips are outside them and the marsh is a contour band below them - so they render as BARE
            # ground, the only uncovered land on the map. That is what read as "empty space" on Akagahara. This
            # patch covers the cultivated bbox; since the scatter already skips every field, lane, watercourse,
            # building and keep-out, it can only land in those voids, clothing them as the rough grazing they
            # are. Ground the crop does not use is still ground, and it is grazed. A SOLID field (a polder grid
            # fills its whole bbox, no voids) has nothing to clothe here, so `interior_fill=False` skips it.
            if interior_fill:
                self.commons([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], role=scrub_role, avoid=avoid)
        if marsh:
            # The toe is a CONTOUR BAND, not an axis-aligned box. Wet ground is defined by HEIGHT, and every
            # other feature here (field, comb, drain, the marsh_on_low_ground check) resolves height by
            # projecting onto the `down_deg` vector - so the marsh's inner edge must be PERPENDICULAR to that
            # vector too. It was previously a bbox-keyed rectangle, which is only an honest contour when the
            # fall is axis-aligned (0/90/180/270); it was the ONE feature that did not rotate with the map.
            # At a diagonal fall that rectangle slices across the slope: on Kikuta/Hoshigaoka (down=45) its
            # inner edge spanned 205/219px of height and its uphill corner reached ABOVE their entire drain,
            # so it swallowed the ditch and painted reeds over ground that is still at rice height. That made
            # the reeds appear to abut the collector on the diagonal maps but not on due-S Akagahara - a pure
            # artifact of the rotation, which read as a real difference between the maps (GM, 2026-07).
            # Since EVERY collector descends ~19-20 degrees across the contours to reach its tameike, there is
            # genuinely ground below the ditch that is still crop-height on every map; the band now shows that
            # consistently instead of hiding it on two maps out of three.
            self.marsh(toe_poly, role=marsh_role, avoid=avoid)  # reed wetland: the low, undrained downhill toe

    def _clear_ground(self: Settlement, x: float, y: float, w: float, h: float, extra: float) -> None:  # type: ignore[misc]
        """Reserve a swept verge around a sacred/funerary feature: the w x h footprint grown by `extra`,
        added to `self.clearings` so the loose hinterland scatter (commons scrub, marsh reeds) skips it.
        Scaled by the map grain (bscale), so the cleared collar reads at the same real size on any scale.
        The verge's OUTLINE is ORGANIC (irregular bays carved into the padded rectangle), never the
        rectangle itself (GM 2026-07-23): swept ground is PRODUCED by tending - brooms, feet, the sando's
        traffic - radiating from the feature, and its edge sits wherever the tending peters out into the
        scrub; a surveyed straight line belongs to walls and paddy bunds, never to clearage (settlements.md
        'Swept ground around sacred + funerary features'). The bays are INWARD-ONLY, so the blob always
        stays INSIDE the old padded rect: a collar is a maintenance CLAIM, and making it irregular means
        the sweeping falls short of the surveyed ideal - it never annexes ground (an outward lobe could
        newly overlap a cover that legitimately predates the clearing and flip
        scatter_respects_swept_clearings on a previously-clean map). A bay cuts at most ~55% of the collar,
        so the verge still generously CONTAINS its feature. The blob is seeded from the footprint (the
        saved RNG state keeps the map's stream untouched, so only collar shapes changed pool-wide), and a
        SAME-CENTER duplicate registration (within 4px: the reserve_clearing-then-feature pattern) REUSES
        the first blob verbatim, so guard and late collar can never disagree. Also recorded in
        M['clearings'] with the current cover ordinal, so the checks can verify ORDER: a scatter only
        skips clearings that exist when it runs (scatter_respects_swept_clearings)."""

        def record(poly: Poly) -> None:
            self.M.setdefault("clearings", []).append({"poly": [[round(px, 1), round(py, 1)] for px, py in poly], "seq": self._cover_n})

        for (ocx, ocy), opoly in zip(self._verge_centers, self.clearings, strict=True):
            if abs(ocx - x) <= 4 and abs(ocy - y) <= 4:  # the documented duplicate-registration pattern: reuse the reserved blob
                self.clearings.append(opoly)
                self._verge_centers.append((x, y))
                record(opoly)
                return
        e = extra * self.bscale
        st = random.getstate()
        random.seed(int(abs(x) * 3 + abs(y) * 7 + w * 11 + h * 13 + e))
        x0, y0, x1, y1 = x - w / 2 - e, y - h / 2 - e, x + w / 2 + e, y + h / 2 + e
        amp = 0.55 * e
        edges = [((x0, y0), (x1, y0), (0, 1)), ((x1, y0), (x1, y1), (-1, 0)), ((x1, y1), (x0, y1), (0, -1)), ((x0, y1), (x0, y0), (1, 0))]  # normals point INWARD
        verge = []
        for sa, sb, (nx, ny) in edges:
            for i in range(4):
                t = i / 4
                bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
                off = random.uniform(0.05, 1.0) * amp * (0.35 if i == 0 else 1.0)  # inward-only bay; damped at the corner so the collar keeps its reach there
                jt = random.uniform(-0.18, 0.18) * amp  # tangential jitter (along the edge)
                vx, vy = bx + nx * off + jt * (1 - abs(nx)), by + ny * off + jt * (1 - abs(ny))
                verge.append(
                    (min(max(vx, x0), x1), min(max(vy, y0), y1))
                )  # clamp: corner-sample jitter must not poke past the padded rect (the blob-is-a-subset guarantee is what makes this pool-safe)
        random.setstate(st)
        self.clearings.append(verge)
        self._verge_centers.append((x, y))
        record(verge)

    def reserve_clearing(self: Settlement, x: float, y: float, w: float, h: float, extra: float = 46) -> None:  # type: ignore[misc]
        """Pre-register a swept-ground clearing for a sacred/funerary feature a gen draws LATER (e.g. a
        precinct dropped in after crop_to_content, or placed after the hinterland scatter). The scrub/marsh
        scatter only skips clearings that already exist when it runs, so a late precinct must reserve its
        ground FIRST or the scrub covers it. The later shrine_hall/cemetery registers its own clearing too;
        the overlap is harmless. Pass roughly the footprint you will draw (a slightly generous `extra` is
        fine - over-clearing by a few px reads the same)."""
        self._clear_ground(x, y, w, h, extra)
