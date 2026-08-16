"""The comb-field builder, its base fill, its bund junctions, and its furrows.

Split from settlement/fields.py by feature 112 - see settlement/fields/CLAUDE.md for the index.
"""

import hashlib
import math
import random
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from .._geom import (
    Poly,
    Pt,
    point_in_poly,
    point_quad_dist,
    quad_hits_seg,
    seg_closest,
    seg_dist,
)
from .._knobs import _centroid, _sharp_corners, _toward

if TYPE_CHECKING:
    from ..core import Settlement


class CombMixin:
    def comb_base_fill(self: Settlement, net: dict[str, Any], name: str, color: str = "", full_envelope: bool = False) -> None:  # type: ignore[misc]
        """Draw a FIELD FLOOR under a build_comb net's plots and record it (M['comb_floors'][name]),
        so the parchment BACKGROUND never shows through as bare 'white' at the canal junctions the
        carve cannot tessellate (the head-race fork, the outfall corner where a supply canal dies at
        the drain, the confluence wedges - the 'blank bits on the paddies' the GM circled repeatedly,
        2026-07-22). Call BEFORE drawing the plots. `full_envelope` fills the whole envelope (cities:
        tight crop, no surrounding scrub, so edge junctions must be covered too); otherwise the fill is
        clipped to the PLOTS' union bbox (villages/hamlets: hides the nucleated map's harmless phantom
        tail - the over-declared field_fall - and the scrub matrix covers the rest). Gated by
        paddy_fan_has_floor. Villages default to a paddy-green floor, cities pass a soil tan."""
        from waterfields import _RICE_GREEN

        pv = [v for p in net["plots"] for v in p["poly"]]
        if not pv:
            return
        env = net["envelope"]
        epts = " ".join(f"{x:.1f},{y:.1f}" for x, y in env)
        col = color or _RICE_GREEN
        # a POLDER supplies an explicit `floor` = the ring-canal INTERIOR (the outermost irrigated channels),
        # so the green greenery is bounded exactly by the ring rather than by the dike-boundary envelope
        # rectangle that drifts in and out of the wavering ring (GM 2026-07-22). Fill it as-is; the ring canal
        # draws on top. Comb nets carry no `floor`, so they keep the envelope/bbox behavior byte-for-byte.
        floor = net.get("floor")
        if floor:
            fpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in floor)
            self.add(f'<polygon points="{fpts}" fill="{col}" stroke="none"/>')
            self.M.setdefault("comb_floors", {})[name] = [[round(x, 1), round(y, 1)] for x, y in floor]
            return
        if full_envelope:
            self.add(f'<polygon points="{epts}" fill="{col}" stroke="none"/>')
        else:
            cid = self._cid("padbase")
            px0, px1 = min(v[0] for v in pv), max(v[0] for v in pv)
            py0, py1 = min(v[1] for v in pv), max(v[1] for v in pv)
            self.add(f'<clipPath id="{cid}"><rect x="{px0:.1f}" y="{py0:.1f}" width="{px1 - px0:.1f}" height="{py1 - py0:.1f}"/></clipPath>')
            self.add(f'<polygon points="{epts}" fill="{col}" clip-path="url(#{cid})"/>')
        self.M.setdefault("comb_floors", {})[name] = [[round(x, 1), round(y, 1)] for x, y in env]

    def bund_junctions(self: Settlement, plots: Sequence[Mapping[str, Any]], name: str) -> None:  # type: ignore[misc]
        """Pile earth into every bund CROSSING (GM 2026-07-25). Same rule as the polder's organic parcels -
        hand-piled mud has no sharp corners - but a SHARED-BARRIER field needs the opposite operation to
        express it. A polder's parcels are separate polygons with a real gap between them, so rounding is
        SUBTRACTIVE: each parcel gives up its corners and the bund, being the space between, just widens.
        A comb/terrace/ribbon carve has no gap - the bund IS the shared line, and the carve is required to
        tessellate (`paddy_fan_gapless`) - so shrinking the cells would tear holes in the field. The
        correct operation is ADDITIVE: leave the carve untouched and pile material into the junction, so
        the crossing stops being two hairlines meeting at a point and becomes a lumpy node of bund, and
        the four basin corners read rounded because the earth has taken them.

        This is the truest part of the whole rule. A bund junction is the most-worked point in a field:
        four basins push water at it, it carries the crossing foot traffic, it is where someone stands to
        open and close the water, and it is the first thing to slump and get re-piled - so it genuinely
        carries more earth than the runs between. TRUE SCALE: a plain aze runs ~1.5 ft (`AZE_FT`) and a
        junction node widens to ~4-6 ft, which is 4-6 px at hamlet scale and honestly sub-2 px at city
        scale. It is floored at the stroke width so it never disappears, but never inflated past the
        attested node - a legibility-sized dot here would be a fake 15 ft earthwork at every crossing.

        A junction is found from the DRAWN geometry, not declared: wherever >=3 plot corners coincide,
        bunds cross. That makes the pass self-selecting - a polder's parcels are inset away from each
        other and share no corner at all, so nothing is drawn on the archetype that must not get it.

        NOT A DISC AT THE CROSSING (GM 2026-07-25, on the first version): a blob centered on the node
        reads as a stamped circle, and a stamp is LESS natural than the sharp cross it replaced - at
        4-6 px no amount of jitter on a 7-gon's radius survives rasterization, and every junction gets
        the same mark. Earth does not arrive symmetrically anyway. So the node is built the way it is
        actually piled: as a separate FILLET IN EACH QUADRANT - one per plot corner meeting here, each
        with its own two independently-drawn legs and its own outward bulge, and roughly a quarter of
        quadrants left bare (nobody re-piles all four corners of a crossing in the same season). The
        irregularity is then structural rather than cosmetic: a junction can be piled heavily on one
        side and untouched on the other, and no two crossings on a map carry the same mark."""
        from waterfields import AZE, aze_w

        cells: dict[tuple[int, int], list[list[tuple[float, float] | list[tuple[int, int]]]]] = {}
        for pi, p in enumerate(plots):
            for vi, (x, y) in enumerate(p["poly"]):
                node = None
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for cand in cells.get((int(x // 1) + dx, int(y // 1) + dy), []):
                            cxy = cast("tuple[float, float]", cand[0])
                            if abs(cxy[0] - x) < 0.75 and abs(cxy[1] - y) < 0.75:
                                node = cand
                                break
                        if node:
                            break
                    if node:
                        break
                if node:
                    cast("list[tuple[int, int]]", node[1]).append((pi, vi))
                else:
                    cells.setdefault((int(x // 1), int(y // 1)), []).append([(x, y), [(pi, vi)]])
        rng = random.Random(int(hashlib.md5(name.encode()).hexdigest()[:8], 16))  # str hash() is salted per process - a map must redraw identically
        base = max(2.5 / self.ftpx, aze_w(self.ftpx) * 1.1)  # ~5 ft of piled earth, floored at the drawn aze
        out = []
        for bucket in cells.values():
            for _xy, members in bucket:
                corners = cast("list[tuple[int, int]]", members)
                if len(corners) < 3:
                    continue  # a run, a T-stub, or a field-edge corner - only real crossings get piled
                for pi, vi in corners:
                    if rng.random() < 0.25:
                        continue  # this quadrant has not been re-piled lately
                    poly = plots[pi]["poly"]
                    n = len(poly)
                    v = poly[vi]
                    a = _toward(v, poly[(vi - 1) % n], base * rng.uniform(0.5, 2.0))  # each leg of the fillet
                    b = _toward(v, poly[(vi + 1) % n], base * rng.uniform(0.5, 2.0))  # is piled on its own
                    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    bulge = rng.uniform(0.15, 0.45)  # how far the pile swells past the chord into the basin
                    cx_, cy_ = mx + (mx - v[0]) * bulge, my + (my - v[1]) * bulge
                    arc = " ".join(
                        f"{(1 - f) ** 2 * a[0] + 2 * (1 - f) * f * cx_ + f * f * b[0]:.1f},{(1 - f) ** 2 * a[1] + 2 * (1 - f) * f * cy_ + f * f * b[1]:.1f}" for f in (0.0, 0.25, 0.5, 0.75, 1.0)
                    )
                    out.append(f'<polygon points="{arc} {v[0]:.1f},{v[1]:.1f}"/>')
        if out:
            self.add(f'<g fill="{AZE}" stroke="none">{"".join(out)}</g>')

    def draw_comb_field(self: Settlement, net: dict[str, Any], name: str, source: dict[str, Any], inwall_drain_moat_bias: Pt | None = None, join_head: bool = False) -> list[Pt]:  # type: ignore[misc]
        """Draw a `build_comb` net (dry hem + flooded paddies + bunds + channels) AND register the field's
        manifest + water topology, in one call - the ~50 lines every comb gen otherwise repeats inline. Feeds
        the roll-from-seed entrypoint (which cannot hand-place any of it) but is reusable by any comb gen.
        `source` describes where the water comes from: {"kind":"pond", "pond":(cx,cy,rx,ry)} draws a tameike at
        the sluice and feeds from it; {"kind":"stream", "stream":[(x,y),...]} runs a brook in from a canvas edge
        to the sluice. Records the field envelope/bbox/vis_bbox, every channel as a field_ditch, and a hairline
        SOURCE->field feed channel so the water-topology checks (fields_show_water_source, field_ditches_reach_
        source_and_sink) see a source. Returns the field envelope polygon. `inwall_drain_moat_bias` marks an
        IN-WALL city fan: the drain is trimmed through inwall_drain_outfall (cut off short of the ring road,
        sluice-gated, underground conduit to the moat) before anything is drawn or recorded."""
        from waterfields import AZE, BEAN_GREEN, aze_w, hem_on_paddy

        if inwall_drain_moat_bias is not None:
            _idr = next(c for c in net["channels"] if c["role"] == "drain")
            _idr["pts"] = self.inwall_drain_outfall(_idr["pts"], moat_bias=inwall_drain_moat_bias, field_name=name)
            _idr["trimmed"] = True  # a TRIMMED in-wall drain is a conduit stub, not a contour collector - drain_runs_cross_slope exempts it

        # BASE FILL (feature 012, now via the shared helper): a paddy-green wash under the plots so the
        # imperfect tessellation never shows the parchment background as bare "white" gaps (research.md D5).
        self.comb_base_fill(net, name)

        # a fan's hem is generated blind to the OTHER fans on a multi-fan map, so drop any hem plot
        # that lands on a previously recorded fan's rice (this fan's own field record is appended
        # below, AFTER this loop, so a hem's legitimate berm-kiss against its own envelope never
        # tests). Same predicate as the dry_plots_clear_of_paddies gate - see hem_on_paddy's
        # docstring (waterfields.py) for the why and the motivating Tango incident.
        _prior_paddies = [fld["outline"] for fld in self.M["fields"] if fld.get("kind") == "paddy"]
        # WHAT IS ALREADY ON THE MAP (GM go-ahead 2026-07-26). build_comb lays the fan from pure
        # geometry, and draw_comb_field used to render it blind - it was the ONLY placer that
        # consulted nothing - so a hem plot could be drawn straight across a watercourse that had
        # been authored earlier (Ubame's stream). Now the hem yields to standing water. Maps whose
        # hems touch no water are unaffected, byte for byte, because nothing is skipped there.
        _wet: list[tuple[Any, float]] = []
        for _wk, _wdw in (("streams", 9.0), ("channels", 2.5), ("canals", 14.0)):
            for _wr in self.M.get(_wk, []) or []:
                _wpl = _wr.get("poly") or _wr.get("pts")
                if _wpl:
                    _wet.append((_wpl, float(_wr.get("w") or _wdw) / 2))
        _wpond = self.M.get("pond")

        def _hem_on_water(poly: Poly) -> bool:
            if any(quad_hits_seg(poly, pl_[i], pl_[i + 1], hw_) for pl_, hw_ in _wet for i in range(len(pl_) - 1)):
                return True
            return _wpond is not None and point_quad_dist(_wpond[0], _wpond[1], poly) < max(_wpond[2], _wpond[3])

        for p in net["dry_plots"]:  # the dry upslope hem
            if any(hem_on_paddy(p["poly"], _pol) for _pol in _prior_paddies):
                continue
            if _hem_on_water(p["poly"]):
                continue  # standing water was here first - the crop stops at the bank
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
            self._draw_furrows(p["poly"], p["furrow"], p["theta"])
            self.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in p["poly"]], "crop": p["crop"], "theta": round(p["theta"], 3)})
            # A HEM PLOT GOES IN BOTH REGISTRIES, and the second one is the fix (2026-08-11).
            # `block_polys` is the no-build list, which keeps a farmstead off the crop. `dry_polys`
            # is the list the GROVE clump filter, the lane/tree fringe, the threshing-yard and
            # garden nudges and the ground-cover scatters read - so a map that registered only the
            # first had hem plots that stopped a house and not a tree. Every hand-authored comb gen
            # compensates with its own `s.dry_polys.append(...)` line (hoshigaoka, ueda, hikari,
            # hoshizora, hirameki, ubame all carry one); the maps built THROUGH this method never
            # did, and passed only because their clusters happened to sit away from the hem. Found
            # by the scripted-generation experiment, whose clusters do not (hamletgen.md).
            # Registering here is the same discipline as everywhere else in this file: placement and
            # its check must read the SAME source, and the source is what was actually drawn.
            self.block_polys.append(p["poly"])
            self.dry_polys.append(p["poly"])
        from waterfields import FLOODED as _WF_FLOODED  # the tint constant, for the picture record below

        for p in net["plots"]:  # the flooded paddies
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{AZE}" stroke-width="{aze_w(self.ftpx):.2f}" stroke-linejoin="round"/>')
            # Record the LOW/WET plots (feature 010). This is the topographic ELIGIBILITY set the
            # plot-based land-use overlays draw from. It is written HERE, by the field pass, so that
            # `overlays_on_wet_ground_only` compares two INDEPENDENTLY-produced records rather than
            # reading back the overlay's own self-report - a check that reads one source has no teeth.
            if p.get("low"):
                self.M.setdefault("wet_plots", []).append(_centroid(p["poly"]))
            if p["fill"] == _WF_FLOODED:
                # ...and the PAINTED tint (2026-08-16): `wet_plots` is the topography record
                # (which plots are LOW), this is the picture record (which are BLUE) - the
                # flooded-wedge check judges what the paint reads as, and a check that cannot
                # see the paint cannot judge it (the azemame water-honesty precedent).
                self.M.setdefault("flooded_plots", []).append(_centroid(p["poly"]))
        self.bund_junctions(net["plots"], name)
        # WATER-HONEST BEADS, the draw-site half (GM 2026-08-15: "fix the water-buried beads so
        # the record stays honest"; settlement-review found 40 of Inashiro's 727 recorded beads
        # invisible under water paint). `_bund_beans` already drops plot-buried beads and beads
        # under the ditch net's late strokes; the POND paint is only known here. The flavor pass
        # runs first (moved up from the tail of this method - its pocket ponds paint over a plot's
        # interior, so their geometry must exist before the bead line commits; it draws from its
        # own seeded rng, so the move ripples no stream), then every bead inside the source pond
        # or a pocket pond is dropped BEFORE drawing and recording, so dots and manifest agree.
        self._paddy_features(net)
        _bw: list[tuple[float, float, float, float]] = []
        if source.get("kind") == "pond":
            _bwx, _bwy, _bwrx, _bwry = source["pond"]
            _bw.append((_bwx, _bwy, _bwrx + 3.0, _bwry + 3.0))  # +3: the rim stroke and a bead radius
        _bw += [(fp["x"], fp["y"], fp["rx"] + 3.0, fp["ry"] + 3.0) for fp in self.M.get("field_ponds") or []]
        if _bw:
            net["bund_beans"] = [q for q in net["bund_beans"] if all(((q[0] - _wx) / _wrx) ** 2 + ((q[1] - _wy) / _wry) ** 2 > 1.0 for _wx, _wy, _wrx, _wry in _bw)]
        beads = "".join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
        self.add(f'<g opacity="0.85">{beads}</g>')
        sluice = net["channels"][0]["pts"][0]
        pond_rec: Any = None
        if source.get("kind") == "pond":
            pcx, pcy, prx, pry = source["pond"]
            self.stream([(sluice[0], sluice[1]), (pcx, pcy)], frm={"kind": "offmap"}, to={"kind": "pond"}, width=6) if source.get("feeder") else None
            self.pond(pcx, pcy, prx, pry)
            ring = [(pcx + (prx + 40) * math.cos(a), pcy + (pry + 40) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
            self.marsh(ring, role="pond_fringe")
            self.block_polys.append([(pcx - prx - 10, pcy - pry - 10), (pcx + prx + 10, pcy - pry - 10), (pcx + prx + 10, pcy + pry + 10), (pcx - prx - 10, pcy + pry + 10)])  # no build on the pond
            pond_rec = (pcx, pcy)
        elif source.get("kind") == "stream" and source.get("stream"):
            # no "stream" polyline = an existing on-map stream already runs at the sluice (the town
            # pattern: the comb taps the map's stream via a weir); nothing extra is drawn, the
            # hairline topology channel below still anchors to that stream
            self.stream(source["stream"], frm={"kind": "offmap"}, width=7)
        # The ditch net ALWAYS goes to the LATE water block (GM 2026-07-21: Hoshizora's canals
        # "rendering below the rice paddies"). In the shared block - anchored at the FIRST water
        # call - the net composites UNDER any plots painted after that anchor: a town/city stream
        # or moat drawn before the field anchors it early (the whole net invisible), and even on
        # a village a SECOND comb's plots covered the first comb's net (Hikari-no-sato). The late
        # block re-anchors at every call (see _water), so the net lands after the LAST field's
        # plots and draws OVER every paddy, exactly as the hand-drawn maps intend. The cities
        # discovered the early-anchor half of this and patched it per-gen (tango/nagahara
        # `late=True`); this makes it automatic and closes their residual multi-fan hole too.
        # the POLDER RING trunk (feeder / drain / toe collectors) draws LAST, ON TOP of the laterals that feed
        # it, so every lateral-to-trunk junction is a clean T covered by the trunk - not a lateral end poking a
        # stub past the trunk into the dike corridor (GM 2026-07-22). Comb nets set no `seg`, so their draw
        # order (widest-first) is unchanged and byte-identical; only the polder ring re-sorts.
        _ring_last = {"feeder", "drain", "e_toe", "w_toe"}
        for c in sorted(net["channels"], key=lambda c: (c.get("seg") in _ring_last, -c["w"])):
            self.field_channel(c["pts"], "#7C9EB0" if c["role"] == "drain" else "#6C9CBE", c["w"], c.get("w_tail", c["w"]), late=True)
        if net["brook"]:
            # the drain-outfall brook shoots STRAIGHT downhill off-map (a fan field's own wiggly brook can
            # re-enter the paddy and trip streams_avoid_fields; a straight downhill exit never does)
            ddb = self.M["meta"].get("down_deg", 90)
            bdx, bdy = math.cos(math.radians(ddb)), math.sin(math.radians(ddb))
            b0 = net["brook"][0]
            b1 = net["brook"][1] if len(net["brook"]) > 1 else (b0[0] + bdx, b0[1] + bdy)
            ex, ey = b1[0] - b0[0], b1[1] - b0[1]  # the drain's own exit direction (smooth junction)
            el = math.hypot(ex, ey) or 1.0
            mid = (b0[0] + ex / el * 70, b0[1] + ey / el * 70)  # a short smooth continuation, THEN turn downhill
            # (first segment = drain direction -> smooth junction; then straight downhill AWAY from the field ->
            # clears a fan envelope's concave lobe without an acute turn, since the drain already runs downhill)
            self.stream([b0, mid, (mid[0] + bdx * 520, mid[1] + bdy * 520)], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)
        env = [[round(x, 1), round(y, 1)] for x, y in net["envelope"]]
        exs, eys = [p[0] for p in env], [p[1] for p in env]
        pvx = [v[0] for p in net["plots"] for v in p["poly"]]
        pvy = [v[1] for p in net["plots"] for v in p["poly"]]
        # Per-plot [along-fall span, cross-fall span, centroid x, centroid y, vertex count, count of
        # still-square corners], so parcel-fabric checks (polder_parcels_vary, polder_parcels_front_water,
        # polder_parcels_are_organic) measure the DRAWN geometry from the manifest rather than trusting
        # a builder self-report. The last two are the OUTLINE shape: a ruled quad is 4 vertices with all
        # 4 corners square, while a hand-piled parcel carries a densely sampled, wandering outline on
        # which most - not all - corners have eased. The pair separates earth from CAD without recording
        # every vertex (the full outlines would roughly double a polder manifest for no extra teeth).
        ddp = float(self.M["meta"].get("down_deg", 90))
        pdx, pdy = math.cos(math.radians(ddp)), math.sin(math.radians(ddp))
        pdims = []
        for p in net["plots"]:
            al = [vx * pdx + vy * pdy for vx, vy in p["poly"]]
            cr = [vx * pdy - vy * pdx for vx, vy in p["poly"]]
            pcx, pcy = _centroid(p["poly"])
            pdims.append([round(max(al) - min(al), 1), round(max(cr) - min(cr), 1), round(pcx, 1), round(pcy, 1), len(p["poly"]), _sharp_corners(p["poly"])])
        # THE BUNDS ALONG THE COLLECTOR, recorded so the gate can actually see them (2026-08-08).
        # `pdims` above is extents-and-a-centroid: it cannot express "this bund is drawn ACROSS the
        # drainage ditch", which is precisely the defect the GM caught on Hoshizora - the hem plots
        # were laid on the contour while the collector runs at up to ~19 deg to it, so every hem
        # bund started above the ditch and ended below it. `paddy_bunds_clear_the_collector` needs
        # the real outlines to judge that, so the SMALL SET of plots that actually border this fan's
        # drain carries its polygon into the manifest - a dozen-odd rings per fan, not a second copy
        # of the field. Band is generous (a plot merely NEAR the ditch is cheap to record and a plot
        # the band misses is invisible to the check, which is the failure that matters).
        _dch = next((c for c in net["channels"] if c["role"] == "drain" and len(c["pts"]) >= 2), None)
        _hem_rings: list[list[list[float]]] = []
        if _dch is not None:
            _dpp = _dch["pts"]
            _band = 30.0 + max(_dch["w"], _dch.get("w_tail", _dch["w"]))
            _dx0, _dy0 = min(q[0] for q in _dpp) - _band, min(q[1] for q in _dpp) - _band
            _dx1, _dy1 = max(q[0] for q in _dpp) + _band, max(q[1] for q in _dpp) + _band
            for p in net["plots"]:
                if any(_dx0 <= vx <= _dx1 and _dy0 <= vy <= _dy1 for vx, vy in p["poly"]) and any(
                    min(seg_dist(vx, vy, _dpp[i], _dpp[i + 1]) for i in range(len(_dpp) - 1)) <= _band for vx, vy in p["poly"]
                ):
                    _hem_rings.append([[round(vx, 1), round(vy, 1)] for vx, vy in p["poly"]])
        _fld: dict[str, Any] = {
            "name": name,
            "kind": "paddy",
            "outline": env,
            "bbox": [min(exs), min(eys), max(exs), max(eys)],
            "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)],
            "plots": pdims,
            "drain_hem": _hem_rings,
            # THE PLOT RINGS, IN DRAW ORDER, plus the azemame bead points (GM 2026-08-15). `pdims`
            # above deliberately compacts each plot to extents-and-a-centroid, but that record
            # cannot express "this plot is painted OVER that one's bund" - `_fill_wedges`' fillers
            # lap up to ~12 real ft onto a neighbor and paint last, and the bead line laid along
            # the buried stretch surfaced as green dots floating mid-paddy on Inashiro. A check can
            # only judge bead-on-visible-bund from the real rings in paint order, so they are
            # recorded in full (bund_beans_on_bunds reads both; draw order IS list order).
            "plot_rings": [[[round(vx, 1), round(vy, 1)] for vx, vy in p["poly"]] for p in net["plots"]],
            "bund_beans": [[round(bx, 1), round(by, 1)] for bx, by in net["bund_beans"]],
        }
        if net.get("down_deg") is not None:
            _fld["down_deg"] = net["down_deg"]  # this fan's LOCAL fall (see build_comb)
        if net.get("fork") is not None:
            # the bunsuiguchi division point (build_comb only - a polder net records none), read by
            # comb_supply_commands_both_flanks; legacy manifests lack it, so the check skips them
            _fld["fork"] = [round(net["fork"][0], 1), round(net["fork"][1], 1)]
        self.M["fields"].append(_fld)
        for c in net["channels"]:
            rec = {"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]], "role": c["role"], "field": name, "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)}
            if c.get("trimmed"):  # a TRIMMED in-wall drain is a conduit stub, not a contour collector
                rec["trimmed"] = True
            if c.get("seg"):  # a polder ring-side tag (feeder/e_toe/w_toe/drain/lateral), so footbridge placement can be side-aware
                rec["seg"] = c["seg"]
            self.M["field_ditches"].append(rec)
        # a hairline SOURCE -> field feed carrying the topology (winds a little into the paddy interior). It
        # STARTS at the source (the pond center, or the sluice for a stream) so channel_source_anchored /
        # pond_connected_to_field see it, and carries a gentle perpendicular KINK so channel_winds_gently passes.
        # source kind "cascade" = the field is fed plot-to-plot from an UPSTREAM field (the caller
        # records its own connector channel with to={"kind":"field",...}), so no hairline is added -
        # its frm={"kind":"stream"} anchor would dangle with no stream at the sluice.
        if source.get("kind") != "cascade":
            hr = net["channels"][0]["pts"]
            fork = hr[-1]
            dd = self.M["meta"].get("down_deg", 90)
            dx, dy = math.cos(math.radians(dd)), math.sin(math.radians(dd))
            din = (fork[0] + dx * 70, fork[1] + dy * 70)
            # ...AND IT MUST LAND INSIDE THE CROP, whatever the field's shape (2026-08-15).
            #
            # `channel_field_anchored` wants this end inside the outline and >= 10 px clear of its
            # edge, "so the field paints over the end". Stepping 70 px downhill from the main
            # channel's last point is a COMB's geometry: a head-race ends at the field's head, so
            # downhill goes into the crop. A POLDER's main is the perimeter ring running ALONG the
            # high edge, so its last point is a corner and the same step skims the boundary - the
            # mouth landed 2.6 px inside on two scripted seeds in three, and no amount of moving the
            # SLUICE changed it, because this end is constructed here rather than taken from the
            # anchor. Fixed by asking the envelope: if the downhill step is already well inside,
            # nothing moves (every comb map is byte-identical); otherwise the end is pulled in along
            # the nearest edge's inward normal until it clears.
            _env_in = net.get("envelope") or []
            if len(_env_in) >= 3:
                _n_in = len(_env_in)
                _din_d = min(seg_dist(din[0], din[1], _env_in[_k], _env_in[(_k + 1) % _n_in]) for _k in range(_n_in))
                if not point_in_poly(din[0], din[1], _env_in) or _din_d < 12.0:
                    _best_in = min(
                        ((seg_closest(din[0], din[1], _env_in[_k], _env_in[(_k + 1) % _n_in]), _env_in[_k], _env_in[(_k + 1) % _n_in]) for _k in range(_n_in)),
                        key=lambda t: math.hypot(t[0][0] - din[0], t[0][1] - din[1]),
                    )
                    _q_in, _a_in, _b_in = _best_in
                    _ex_in, _ey_in = -(_b_in[1] - _a_in[1]), _b_in[0] - _a_in[0]
                    _el_in = math.hypot(_ex_in, _ey_in) or 1.0
                    _nx_in, _ny_in = _ex_in / _el_in, _ey_in / _el_in
                    _cx_in = sum(q[0] for q in _env_in) / _n_in
                    _cy_in = sum(q[1] for q in _env_in) / _n_in
                    if _nx_in * (_q_in[0] - _cx_in) + _ny_in * (_q_in[1] - _cy_in) > 0:  # point it INWARD
                        _nx_in, _ny_in = (
                            -_nx_in,
                            -_ny_in,
                        )  # pragma: no cover - the winding-order guard. `build_polder` winds its envelope so the raw edge normal already points inward (measured: dot -324 and -355 on the two seeds that need the pull), but a ring wound the other way would send the mouth OUT of the field, so the orientation is asserted rather than assumed
                    din = (_q_in[0] + _nx_in * 14.0, _q_in[1] + _ny_in * 14.0)
            start = pond_rec if pond_rec else (sluice[0], sluice[1])
            frm = {"kind": "pond"} if pond_rec else {"kind": "stream"}
            if not pond_rec:
                # snap the intake's START onto the nearest stream centerline (within the 30px anchor
                # band): an offtake JOINS its stream at a confluence like any junction - the symmetric
                # case of the drain-culvert rule (channels_join_streams_at_confluence) - rather than
                # beginning in the grass beside it. A comb fed by its OWN feeder brook ending AT the
                # sluice is already joined (distance ~0) and is left alone.
                nearest: Any = None
                for st_ in self.M.get("streams", []):
                    sp_ = st_["poly"]
                    for si_ in range(len(sp_) - 1):
                        fq = seg_closest(start[0], start[1], sp_[si_], sp_[si_ + 1])
                        dq = math.hypot(start[0] - fq[0], start[1] - fq[1])
                        if nearest is None or dq < nearest[0]:
                            nearest = (dq, fq)
                if nearest and 0.5 < nearest[0] <= 30:
                    start = nearest[1]
            vx, vy = din[0] - start[0], din[1] - start[1]
            vl = math.hypot(vx, vy) or 1.0
            midx, midy = (start[0] + din[0]) / 2 - vy / vl * 20, (start[1] + din[1]) / 2 + vx / vl * 20
            # THE RING HEAD IS TOUCHED, not merely passed near (2026-08-15).
            #
            # `watercourse_ends_reach_water` lets a main/drain end outside the crop stand only if it
            # JOINS another watercourse, within ~12 px. On a comb that is free: the sluice IS the
            # head-race's end, so this channel starts on it. On a POLDER the ring canal's end is a
            # corner of the block and the reservoir sits uphill of it, so the run passes NEAR the
            # head - measured 17.6 px - and the ring's end reads as dangling. The bow is what does
            # it: the polyline kinks 20 px off the chord at its midpoint, and the head lies ON the
            # chord, so the drawn line bends away from exactly the point it needs to meet.
            #
            # Straightening the bow is not available - `channel_winds_gently` requires 5-50 px of
            # deviation, and a dead-straight cut fails it. So the head is INSERTED as a vertex when
            # the drawn run does not already reach it. On every comb map the run starts on the head,
            # the distance is ~0, and nothing is inserted: the pool is byte-identical.
            _ch_poly = [[round(start[0], 1), round(start[1], 1)], [round(midx, 1), round(midy, 1)], [round(din[0], 1), round(din[1], 1)]]
            _fk = (float(fork[0]), float(fork[1]))
            _fk_d = min(seg_dist(_fk[0], _fk[1], (_ch_poly[_i][0], _ch_poly[_i][1]), (_ch_poly[_i + 1][0], _ch_poly[_i + 1][1])) for _i in range(len(_ch_poly) - 1))
            # `join_head` is passed by the POLDER path and by nothing else. Conditioning this on
            # the check's own clauses was tried three times and each attempt missed one - distance
            # alone moved Ubame and four others, "outside the envelope" moved Honda and Shimizu, and
            # replicating the vis_bbox/edge/junction trio still moved them, because the check reads
            # the CROP bounds and per-field bboxes that do not exist yet at draw time. Replicating a
            # check inside the code it governs is the trap this skill's notes name repeatedly; an
            # explicit flag from the one caller that needs it cannot drift.
            if join_head and _fk_d > 10.0:
                _ch_poly.insert(len(_ch_poly) - 1, [round(_fk[0], 1), round(_fk[1], 1)])
            self.M["channels"].append(
                {
                    "poly": _ch_poly,
                    "frm": frm,
                    "to": {"kind": "field", "name": name},
                    "w": 2.5,
                }
            )
        return cast("list[Pt]", net["envelope"])

    def _draw_furrows(self: Settlement, poly: Any, color: str, theta: float) -> None:  # type: ignore[misc]
        """Stylised ridge/furrow lines within a dry-field plot (dry crops are row-cultivated)."""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
        dx, dy = math.cos(theta), math.sin(theta)
        nx, ny = -dy, dx
        cid = self._cid("dry")
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
        g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
        t = -diag / 2
        while t <= diag / 2:
            mx, my = cx + nx * t, cy + ny * t
            g.append(
                f'<line x1="{mx - dx * diag / 2:.1f}" y1="{my - dy * diag / 2:.1f}" x2="{mx + dx * diag / 2:.1f}" y2="{my + dy * diag / 2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>'
            )
            t += 5
        g.append("</g>")
        self.add("".join(g))
