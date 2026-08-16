"""Non-rice features the paddy tiles around (feature 012), and every standing-water glyph.

Split from settlement/fields.py by feature 112 - see settlement/fields/CLAUDE.md for the index.
"""

import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .._geom import (
    Poly,
    Pt,
    point_in_poly,
    seg_in_ellipse_core,
)
from .._knobs import CITY_TIER_SCALES, _centroid

if TYPE_CHECKING:
    from ..core import Settlement


class FieldFeaturesMixin:
    def pond(self: Settlement, cx: float, cy: float, rx: float, ry: float, stream_curve: Any = None) -> None:  # type: ignore[misc]
        """A pond / irrigation reservoir. Routed through the WATER block (not drawn inline) so a stream or
        channel MEETING it JOINS at the rim instead of the rim cutting across its mouth: the RIM is an EDGE
        below every water bed (a feeder's bed covers it at the junction -> a clean gap), the FILL joins the
        shared bed group as the TOPMOST bed (`pond_fill=True`) - so it paints OVER any feeder's inside-the-rim
        overshoot (an irrigation channel's round end-cap bulging past the rim, whichever order it was drawn),
        while the shore rim still shows and the mouths stay clean; the inner highlight is a sheen."""
        if stream_curve:
            # the pond's feeder runs at the lateral/ditch tier - a thin line near the channel weight,
            # NOT the heftier natural-stream weight (see the water-width ladder in settlements.md).
            self._water(f'<path d="{stream_curve}" fill="none" stroke="#9CB4C8" stroke-width="5"/>', {})
        self._water(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#9CB4C8"/>',  # FILL -> shared bed group (topmost bed)
            self.M.setdefault("pond_layer", {"late": False}),  # flush records the fill's bedz/sheenz here, and flips
            # `late` if it relocates the fill to the late block. bedz values are offsets within their OWN splice
            # block, so cross-block draw order is carried by the (late, bedz) PAIR - the late block always renders
            # after the whole shared block (pond_fill_covers_channel_mouths compares the pairs lexicographically)
            sheen=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - 12}" ry="{ry - 10}" fill="none" stroke="#B6CAD8" stroke-width="1"/>',  # inner highlight
            edge=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#5C7488" stroke-width="2.4"/>',  # RIM -> edge layer, below beds
            pond_fill=True,
        )
        self._pond_entry: dict[str, Any] | None = self.water[-1]  # so flush can relocate the fill+sheen into the late block (see finish)
        self.M["pond"] = [cx, cy, rx, ry]
        self.ellipses.append((cx, cy, rx, ry))

    # ---- feature 012: deliberate non-rice features the paddy tiles around --------------------------------
    # Placed automatically from the field geometry per the ARCHETYPE MATRIX (specs/012-.../research.md). Only
    # the genuinely NEW in-field glyphs live here - a low-pocket POND, a bedrock ROCK outcrop, and (a disclosed
    # CALIBRATED LIBERTY the GM approved) a rare in-field GRAVE island. The matrix's MARGIN graves + feng-shui
    # knolls are already the village burial ground + back-grove (the research warns a standalone knoll usually
    # IS the back-grove), so they are not redrawn here. Seeded from self.seed so it never ripples other RNG.
    _PADDY_POND_KINDS = ("valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley")
    _PADDY_ROCK_KINDS = ("contour_terraces", "ribbon_valley")  # bedrock ground; alluvial valley/polder + delta dike-pond have none
    _PADDY_GRAVE_KINDS = ("valley_paddy", "contour_terraces", "ribbon_valley")

    def _paddy_features(self: Settlement, net: dict[str, Any]) -> None:  # type: ignore[misc]
        if self.M.get("meta", {}).get("scale") in ("town", *CITY_TIER_SCALES):
            # the in-field flourishes (low-pocket pond, rock outcrop, rare grave island) are VILLAGE-scale
            # features from the feature-012 archetype matrix. On a town/city map the combs are a SLICE of
            # county farmland, and at the 1 ft/px grain the glyphs read literally - the GM read the grave
            # island as a pauper ossuary on the paddy and the pocket pond as a pond overlapping the rice
            # (Hoshizora, 2026-07) - so a town/city comb stays plain.
            return
        arch = self.M.get("meta", {}).get("field_archetype") or "valley_paddy"
        if arch == "mulberry_dike_fishpond":
            return  # open water IS its fabric - no obstacle tiles among it (research D4)
        rng = random.Random((self.seed ^ 0x9AD1) & 0xFFFFFFFF)
        plots = net["plots"]
        if not plots:  # pragma: no cover - a drawn field always has plots
            return
        low = [p for p in plots if p.get("low")]
        # POND: a low pocket held as open water - and it is the ONE in-field feature the feature-012
        # research puts in the flat wet MIDDLE rather than at the margin. Its organizing finding:
        # "these features live at the paddy-to-slope MARGIN ... not free-floating in the flat wet
        # center. The one thing that genuinely belongs in the flat wet middle is an open-water POND
        # (a low pocket too deep for rice)." That is why a rock outcrop or grave island mid-paddy is
        # a defect on flat valley ground while this is not (research D4 + the matrix).
        #
        # THE ~55% IS NOT RESEARCHED, and saying so is the point (GM 2026-08-16, asking whether the
        # pond belongs at all): D4's only hard quantitative anchor is tameike density in Japan, and
        # its own honesty flags call every per-map count interpolated. So the prevalence is a
        # disclosed calibrated liberty (constitution XII) - chosen so a pocket pond reads as an
        # occasional feature of a valley floor rather than a fixture of every field. The SITING is
        # the researched half and it is enforced: `field_ponds_on_low_ground` demands the host plot
        # be one the field pass independently recorded as low/wet.
        #
        # Tried across the low plots in random order until one takes a legible pond, because a plot
        # can REFUSE (a comb fan toe is all thin wedges; Inashiro 2026-08-16). A field whose low
        # pockets are all wedges honestly carries none.
        # NOTE a disclosed coupling (settlement-review, Mizuguchi 2026-08-16): rng.sample consumes
        # a different number of draws than the old rng.choice, so the rock/grave rolls below sit
        # on a shifted stream and re-rolled once. Accepted - the blast radius is this one field's
        # own flourishes, nothing map-level. If it ever bites again, the refinement is one
        # sub-stream per sub-feature: random.Random(seed ^ 0x9AD1 ^ <per-feature salt>) for pond,
        # rock and grave each, at the cost of one more pool-wide flourish re-roll.
        if arch in self._PADDY_POND_KINDS and low and rng.random() < 0.55:
            # the ring list the gate's check will scan: plot_rings is recorded from net["plots"]
            # and drain_hem is a SUBSET of those same polys, so this list is exactly the check's
            # coverage. Rings can OVERLAP each other at the fan/grid seams, so fitting against the
            # host plot alone is not enough (cohort seeds 5/19/21, 2026-08-16).
            rings: list[Poly] = [p["poly"] for p in net["plots"]]
            for cand in rng.sample(low, len(low)):
                if self._plot_pond(cand, rings):
                    break
        # ROCK: bedrock outcrops the risers/bunds wrap around (research D3) - terraces always, ribbon ~half.
        if arch == "contour_terraces" or (arch == "ribbon_valley" and rng.random() < 0.5):
            for _ in range(rng.randint(1, 3)):
                self._plot_rock(rng.choice(plots), rng)
        # GRAVE ISLAND: calibrated liberty (GM 2026-07-20), RARE - the "graves among the paddy" look.
        if arch in self._PADDY_GRAVE_KINDS and rng.random() < 0.3:
            self._plot_grave_island(rng.choice(plots), rng)

    @staticmethod
    def _plot_center_span(poly: Sequence[Pt]) -> tuple[float, float, float, float]:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return (sum(xs) / len(xs), sum(ys) / len(ys), (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2)

    def _plot_pond(self: Settlement, plot: dict[str, Any], rings: list[Poly]) -> bool:  # type: ignore[misc]
        """A small OPEN-WATER pond sunk into one low plot - a low pocket / header tameike the paddy rings.
        Distinct from the reed/lotus BOG (blue-green, choked) and from the main village reservoir at the
        source. Drawn OVER the plot (so it carries no bund grid) with a reed fringe; recorded in
        M['field_ponds']. Returns False - drawing and recording nothing - when no legible pond fits."""
        poly = [(float(x), float(y)) for x, y in plot["poly"]]
        _, _, hx, hy = self._plot_center_span(poly)
        cx, cy = _centroid(poly)
        # capped so a wide TERRACE band gives a POND, not a field-spanning lake (a low pocket, not a reservoir)
        rx, ry = min(max(10.0, hx * 0.82), 46.0), min(max(7.0, hy * 0.82), 32.0)
        # FIT TO THE PLOT POLYGON, NOT ITS BBOX (Inashiro 2026-08-16). A comb fan's toe plots are
        # WEDGES whose bounding box is several times the wedge itself, so a bbox-sized ellipse
        # spilled across three neighboring plots and the drain hem, spoke bunds drawn straight
        # through open water. Center on the CENTROID (a wedge's bbox center can sit outside it) and
        # shrink until every rim point sits inside the plot and NO ring in `rings` cuts the pond's
        # core - `seg_in_ellipse_core` is the same predicate the gate's
        # `field_ponds_sunk_into_one_plot` runs, and `rings` is every ring that check will scan
        # (rings can OVERLAP at the fan/grid seams, so testing the host plot alone is not enough -
        # cohort seeds 5/19/21). Placement tests a LARGER core (inset 3 vs the check's 4) so the
        # manifest's 0.1 px rounding can never flip a verdict the siting cleared. Below the legible
        # floor (10 x 7 px) the plot takes no pond and the caller tries another low plot.
        rim = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
        boxed = [(min(q[0] for q in r), min(q[1] for q in r), max(q[0] for q in r), max(q[1] for q in r), r) for r in rings]
        while rx >= 10.0 and ry >= 7.0:
            ok = all(point_in_poly(cx + rx * ux, cy + ry * uy, poly) for ux, uy in rim)
            if ok:
                for bx0, by0, bx1, by1, ring in boxed:
                    if bx1 < cx - rx or bx0 > cx + rx or by1 < cy - ry or by0 > cy + ry:
                        continue  # bbox prefilter only - the exact test below decides
                    rn = len(ring)
                    if any(seg_in_ellipse_core(ring[i], ring[(i + 1) % rn], cx, cy, rx, ry, inset=3.0) for i in range(rn)):
                        ok = False
                        break
            if ok:
                break
            rx, ry = rx * 0.9, ry * 0.9
        else:
            return False
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#9CB4C8" stroke="#5C7488" stroke-width="1.8"/>')
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx - 5:.1f}" ry="{ry - 4:.1f}" fill="none" stroke="#B6CAD8" stroke-width="0.9"/>')
        reeds = "".join(
            f'<line x1="{cx + rx * math.cos(a):.1f}" y1="{cy + ry * math.sin(a):.1f}" x2="{cx + rx * math.cos(a):.1f}" y2="{cy + ry * math.sin(a) - 5:.1f}" stroke="#7C9A4E" stroke-width="1.1"/>'
            for a in [i * math.pi / 4 for i in range(8)]
        )
        self.add(f'<g opacity="0.8">{reeds}</g>')
        self.M.setdefault("field_ponds", []).append({"x": round(cx, 1), "y": round(cy, 1), "rx": round(rx, 1), "ry": round(ry, 1)})
        return True

    def _plot_rock(self: Settlement, plot: dict[str, Any], rng: random.Random) -> None:  # type: ignore[misc]
        """A bedrock OUTCROP the terrace risers wrap around - a cluster of gray boulders. Recorded in
        M['field_rocks']. Small (a few plot-fractions), off-center so it reads as a natural obstacle."""
        cx, cy, hx, hy = self._plot_center_span(plot["poly"])
        cx += rng.uniform(-hx * 0.3, hx * 0.3)
        cy += rng.uniform(-hy * 0.3, hy * 0.3)
        boulders = ""
        for _ in range(rng.randint(2, 4)):
            bx, by = cx + rng.uniform(-7, 7), cy + rng.uniform(-5, 5)
            r = rng.uniform(3.5, 6.5)
            boulders += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{r:.1f}" fill="#9C948A" stroke="#5C544A" stroke-width="1"/>'
            boulders += f'<path d="M{bx - r * 0.5:.1f},{by - r * 0.2:.1f} q{r * 0.4:.1f},{-r * 0.5:.1f} {r:.1f},{-r * 0.1:.1f}" fill="none" stroke="#C6BEB2" stroke-width="0.8"/>'  # a lit crown
        self.add(f'<g>{boulders}</g>')
        self.M.setdefault("field_rocks", []).append({"x": round(cx, 1), "y": round(cy, 1)})

    def _plot_grave_island(self: Settlement, plot: dict[str, Any], rng: random.Random) -> None:  # type: ignore[misc]
        """A RARE in-field grave island (calibrated liberty) - a small raised earthen mound with a couple of
        stone markers, the flat paddy tiling around it. Recorded in M['field_graves']."""
        cx, cy, hx, hy = self._plot_center_span(plot["poly"])
        rx, ry = max(9.0, hx * 0.55), max(6.0, hy * 0.55)
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.2" opacity="0.9"/>')
        markers = ""
        for i in range(rng.randint(2, 3)):
            mx = cx + (i - 1) * 6
            markers += f'<rect x="{mx - 1.3:.1f}" y="{cy - 7:.1f}" width="2.6" height="7" rx="1" fill="#9AA1A4" stroke="#5A584F" stroke-width="0.5"/>'
        self.add(f'<g>{markers}</g>')
        self.M.setdefault("field_graves", []).append({"x": round(cx, 1), "y": round(cy, 1)})

    @staticmethod
    def _rounded_pond(poly: Sequence[Pt], inset: float, reach: float, rng: random.Random) -> tuple[str, Poly]:
        """A dug fish-pond within its mulberry-dike parcel: homothetically INSET the parcel (so a green bank
        shows all round - the pond never reaches the parcel edge) and ROUND every corner with a quadratic
        fillet of slightly irregular reach (erosion). Returns (svg path `d`, sampled water polygon) - the
        sample carries the rounding into the manifest so the checks can see the pond is inset + rounded."""
        n = len(poly)
        cx = sum(q[0] for q in poly) / n
        cy = sum(q[1] for q in poly) / n
        mids = [((poly[i][0] + poly[(i + 1) % n][0]) / 2, (poly[i][1] + poly[(i + 1) % n][1]) / 2) for i in range(n)]
        apo = sum(math.hypot(mx - cx, my - cy) for mx, my in mids) / n  # centroid->edge-midpoint (the apothem)
        scale = max(0.4, 1.0 - inset / max(1.0, apo))
        ins = [(cx + (q[0] - cx) * scale, cy + (q[1] - cy) * scale) for q in poly]

        def toward(frm: Pt, to: Pt, dist: float) -> Pt:
            vx, vy = to[0] - frm[0], to[1] - frm[1]
            ln = math.hypot(vx, vy) or 1.0
            dd = min(dist, ln * 0.45)
            return (frm[0] + vx / ln * dd, frm[1] + vy / ln * dd)

        a_in: Poly = []
        b_out: Poly = []
        for i in range(n):
            r = reach * rng.uniform(0.8, 1.15)
            a_in.append(toward(ins[i], ins[(i - 1) % n], r))
            b_out.append(toward(ins[i], ins[(i + 1) % n], r))
        d = f"M {b_out[0][0]:.1f} {b_out[0][1]:.1f} "
        sample: Poly = [b_out[0]]
        for i in range(1, n + 1):
            j = i % n
            d += f"L {a_in[j][0]:.1f} {a_in[j][1]:.1f} Q {ins[j][0]:.1f} {ins[j][1]:.1f} {b_out[j][0]:.1f} {b_out[j][1]:.1f} "
            mid = (0.25 * a_in[j][0] + 0.5 * ins[j][0] + 0.25 * b_out[j][0], 0.25 * a_in[j][1] + 0.5 * ins[j][1] + 0.25 * b_out[j][1])
            sample += [a_in[j], mid, b_out[j]]
        return d + "Z", sample

    def crescent_pond(self: Settlement, cx: float, cy: float, r: float, facing_deg: float = 270.0) -> None:  # type: ignore[misc]
        """A fengshui CRESCENT / half-moon pond (半月塘), a focal feature of Huizhou / Hakka single-lineage
        villages (feature 005): a half-disk of water IN FRONT of the cluster, its flat diameter facing the
        houses and the arc bulging away, DISTINCT from the irrigation pond.

        WHAT IT IS (GM asked, 2026-07-21 - labeled "geomantic pond" at his direction): GEOMANTIC, not
        religious - no deity, no rites; cosmological engineering, the same category as orienting a house
        south. The village wants "mountain behind, water in front" (背山面水): the back half is the hill +
        fengshui grove (the windbreak belt these maps already draw), and where no river obliges, the village
        DIGS the front half. Still water gathers and holds qi/wealth where flowing water carries it away;
        the HALF shape leaves the lineage room to grow (a full circle is complete, and what is complete can
        only wane). Grove-arc behind + water-arc in front cradle the village as ONE system. It also earns
        its keep practically - roof/yard runoff retention (hence UNCONNECTED to the irrigation network: it
        is rain-fed by design), fire water beside thatch, fish/ducks/washing, and the flat-side bank doubles
        as the open threshing/ceremony forecourt. The shrine is where religion happens; this is just how a
        well-sited village should be shaped.

        `facing_deg` is the screen direction the FLAT edge faces (toward the village); default 270 = up / N.
        Draws through the shared water block (so it composites cleanly), records the footprint + the
        `crescent_pond` focal feature on the manifest, and reserves a placement keep-out - so call it BEFORE
        `farmsteads()` and the cluster packs around it."""
        fa = math.radians(facing_deg)
        fx, fy = math.cos(fa), math.sin(fa)  # unit vector toward the village (the flat side)
        perp = (-fy, fx)  # along the flat diameter
        n = 26
        pts = []
        for i in range(n + 1):
            t = math.pi * i / n  # sweep the arc across the diameter, bulging AWAY from the village
            px = cx + r * (math.cos(t) * perp[0] - math.sin(t) * fx)
            py = cy + r * (math.cos(t) * perp[1] - math.sin(t) * fy)
            pts.append((round(px, 1), round(py, 1)))
        poly = " ".join(f"{x},{y}" for x, y in pts)
        self._water(
            f'<polygon points="{poly}" fill="#9CB4C8"/>',
            {},
            sheen=f'<polygon points="{poly}" fill="none" stroke="#B6CAD8" stroke-width="1" opacity="0.6"/>',
            edge=f'<polygon points="{poly}" fill="none" stroke="#5C7488" stroke-width="2.4"/>',
            pond_fill=True,
        )
        self.M.setdefault("crescent_ponds", []).append({"cx": cx, "cy": cy, "r": r, "facing": facing_deg, "poly": [[x, y] for x, y in pts]})
        self.note_focal("crescent_pond")
        # keep-out over the bulge half-disk (its centroid sits ~0.42r off center, away from the village)
        self.ellipses.append((cx - fx * r * 0.45, cy - fy * r * 0.45, r * 0.95, r * 0.95))
        # LABELED (GM 2026-07-21): the pond is a culturally specific feature that does not read by
        # itself (the GM asked "what is that?" of an unlabeled one - the don't-label-the-obvious rule cuts the
        # OTHER way here). Placed off the arc side, away from the village (crescent_pond_labeled gates it).
        self.label(cx - fx * (r + 16), cy - fy * (r + 16) + 4, "geomantic pond", 11, italic=True, color="#4C6478")
