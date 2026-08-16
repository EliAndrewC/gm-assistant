"""The land-use overlay pass (mulberry-and-fishpond, lotus, hill tea) and its row helpers.

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
    seg_dist,
)
from .._knobs import _centroid

if TYPE_CHECKING:
    from ..core import Settlement


class LandUseMixin:
    def apply_land_use(self: Settlement, net: dict[str, Any], overlay: str, rng: random.Random, fraction: float = 0.55, eligible: str = "wet") -> int:  # type: ignore[misc]
        """Overlay a LAND-USE archetype (feature 005 US4 `land_use_overlay`) onto an already-drawn comb field:
        recolor a FRACTION of the paddy plots (or, for tea, a hill-margin fringe) as the overlay crop, so a
        village growing mulberry-and-fishpond, lotus, or hill-tea reads distinctly from a plain-rice one.
        Records M['land_use'] + meta.land_use_overlay. Returns the number of plots/rows overlaid.

        GROUNDING (feature 010 research.md, China-first). Every value obeys ONE two-term rule:

            TOPOGRAPHY sets which plots are ELIGIBLE; ECONOMY decides how many of them CONVERT.

        The original implementation had only the second term (this `fraction`, applied by uniform random
        sample over ALL plots) and no topographic filter at all - so it drew ponds and lotus on ordinary
        upper-field rice ground. `fraction` now applies to the ELIGIBLE set:

        - `mulberry_fishpond` (桑基魚塘): dug out of 低洼易有洪患之处, the low flood-prone hollows - a
          flood adaptation that drained the hollow while raising the dike. Eligible = FLOODED plots, and
          CLUSTERED (see `_pick_overlay_plots`). NOTE this value was very nearly deleted on the false
          premise that the dike-pond system was only ever a whole-landscape conversion; in fact a scatter
          among rice was its NORMAL state (Shunde county ~4.6% dike-pond in 1581; at Lake Tai mulberry sat
          on the tang banks with rice remaining the polder's main crop permanently). The wall-to-wall
          landscape is the rare end state, which is what the `mulberry_dike_fishpond` ARCHETYPE is for.
          Do not delete this value; the two are different scales of the same system, not duplicates.
        CALIBRATED LIBERTY (constitution XII, GM 2026-07-19) - disclosed, not hidden. Eligibility keys off
        the plot's `low` flag, and `low` is the bottom TWO levels of each field sector rather than only the
        one hemming the drain. Two things drove that. (1) Correctness: `FLOODED` is a random 45% tint over
        the bottom level for visual texture, so keying off it made eligibility an accident of RENDERING.
        (2) A liberty: how wide a valley bottom's wet backswamp ran is not recorded, and the research puts a
        lotus-growing village anywhere from a few percent to ~10-15% of field area - itself an interpolation,
        the weakest number in that report. Binding to the single drain-side hem put lotus at ~2%, technically
        inside the range but so sparse the knob stopped doing its job of making villages look distinct. We
        therefore chose the UPPER part of a plausible range for a stated non-historical reason (legibility).
        What this does NOT do is invent a range: lotus stays on genuinely low ground, and the overlay still
        cannot touch the upper field.

        - `lotus` (藕田): models DEEP-WATER lotus (深水藕, 30-50cm, tolerating ~1m) against paddy rice's
          ~5-9cm optimum - it physically cannot sit on high ground, so eligible = FLOODED plots. Shallow-
          water lotus (浅水藕) in ordinary paddy is real but is NOT modeled: it is an economic choice
          rotating with rice, and drawing it would be indistinguishable from the uniform-random bug this
          replaced. See research.md D1 before "restoring" it.
        - `tea_fringe` (茶): unchanged - already correct. Tea took the LOWER-to-mid FERTILE hillside, never
          the low lands and never the barren upper slope (Fortune, 1843). The boundary rule is exactly
          "the line is the highest irrigation ditch", which is what `net['dry_plots']` already is.
          Two anachronisms to avoid: neat contour-TERRACED tea is post-1949 (terrace the paddy, not the
          tea), and bund-margin tea (畦畔茶) is a JAPANESE practice with no Chinese equivalent.
        - `rape` (油菜): REMOVED and must not return. Rice and rape are two halves of ONE seasonally-
          synchronized rotation in the SAME plot, so they are never both standing - at any percentage and
          in any pattern. Do not re-add it here."""
        if overlay not in ("none", "mulberry_fishpond", "lotus", "tea_fringe"):
            raise ValueError(f"unknown land_use_overlay {overlay!r}")
        self.M["meta"]["land_use_overlay"] = overlay
        if overlay == "none":
            self.M.setdefault("land_use", []).append({"overlay": "none", "count": 0})
            return 0
        plots = list(net["plots"])
        n = 0
        if overlay == "tea_fringe":  # tea BUSH rows along the field's dry HIGH margin (not plot-based)
            return self._landuse_tea_fringe(net, overlay)
        colors = {"mulberry_fishpond": "#93B7AC", "lotus": "#8FA9A0"}
        # TOPOGRAPHIC FILTER (feature 010). Eligibility is the LOW/WET ground, never the whole field.
        # `fraction` is the ECONOMIC term and applies to the eligible set, not to all plots.
        # `eligible="all"` is the WHOLESALE-CONVERSION escape hatch, used by the mulberry_dike_fishpond
        # ARCHETYPE. At that scale the ponds really have engulfed the ordinary ground too - Shunde county
        # went from ~4.6% dike-pond in 1581 to rice under one-tenth of land by c. 1900 on the same terrain.
        # It is a deliberate, named opt-out, NOT the default, because the mixed patchwork is the norm.
        elig = list(plots) if eligible == "all" else [p for p in plots if p.get("low")]
        # `fraction` is the ECONOMIC term: the share of the ELIGIBLE ground that actually converted, NOT a
        # share of the whole field. Keeping it a share of the field made it inert - the eligible set is
        # always smaller than fraction*all, so every village converted 100% of its low ground and the
        # economic term decided nothing. As a share of eligible it varies independently of topography,
        # which is the whole point: Shunde was ~5% dike-pond county-wide while containing townships past
        # 50% the same year, on identical terrain.
        take = min(len(elig), max(2, round(len(elig) * fraction)))
        chosen = self._pick_overlay_plots(elig, take, clustered=(overlay == "mulberry_fishpond" and eligible != "all"), rng=rng)
        # LEFTOVERS of a WHOLESALE conversion read as STANDING RICE, not as bare outlines (GM 2026-07-23;
        # settlements.md 'Polder fourth pass'). Under eligible="all" the base polder drew every parcel as a
        # flat bund-outlined rectangle, so the few unconverted plots floated as tan outlines around ground
        # indistinguishable from the floor green (and a FLOODED leftover read as "a pond with no dike").
        # Repaint them as textured paddy - the transplant mottle is what distinguishes crop from floor -
        # and erase the bund outline with a same-color covering stroke: inside a dike-pond block the
        # neighbors' raised banks bound a rice parcel, so its own drawn bund is noise. Painted BEFORE the
        # ponds so an expanded pond bank overlaps the repaint, never the reverse. Scoped to the archetype
        # case only: a partial overlay's unconverted plots are ordinary textured comb paddies already.
        leftover_plots = self._landuse_repaint_leftovers(elig, chosen, overlay, eligible, rng)
        dikeponds: list[dict[str, Any]] = []
        # channel centerline segments, for the bush-vs-canal clearance filter in _mulberry_rows (the crowns
        # are coppiced BUSHES on the dike, not canopy - they cannot arch over the open water at the toe)
        crown_q: list[tuple[Poly, str, float, float]] = []  # deferred _mulberry_rows args - crowns draw LAST, above the channel strokes
        chansegs: list[tuple[Pt, Pt]] = []
        for ch in net.get("channels", []):
            cpp = ch["pts"]
            chansegs += [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for a, b in zip(cpp, cpp[1:], strict=False)]
        for p in chosen:
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
            cx = sum(v[0] for v in p["poly"]) / len(p["poly"])
            cy = sum(v[1] for v in p["poly"]) / len(p["poly"])
            self._landuse_draw_plot(p, pts, cx, cy, overlay, colors, chansegs, rng, dikeponds, crown_q)
            n += 1
        if dikeponds:
            self.M["dikeponds"] = dikeponds
            self._landuse_dikepond_sluices(net, dikeponds)
        # the recolored plots (ponds / lotus) are FIELD GROUND, so the ditch net must draw OVER them: re-anchor
        # the LATE water block past this overlay. Without it a MEANDERING mosaic lateral, whose midpoint drifts
        # onto a pond parcel painted here (after the channels were queued), vanishes under it (test_villages
        # z-order audit). No-op when no late block exists or nothing was overlaid.
        if n and self._late_water_idx is not None:
            self._late_water_idx: int | None = len(self.out)
            self.out.append("")  # PLACEHOLDER - the flush splice REPLACES the element at the anchor index
            # (self.out[idx:idx+1] = block), so a re-anchor without a placeholder makes the splice EAT
            # whatever element lands there next. This one was missing from the start; it went unnoticed
            # while the next element was inert, until the deferred crown pass below put a pond's entire
            # crown group in the slot and a bald pond shipped (GM 2026-07-24). Abandoned placeholders
            # are empty strings, inert in the final SVG - same convention as the late=True anchor.
        # ...but the channels draw UNDER the mulberry canopies (GM 2026-07-24): the canal runs BETWEEN the
        # bushes at ground level, so a crown's leaves may overhang and partly cover the channel stroke -
        # never the channel slicing across a crown. The crown groups are drawn AFTER the late-water anchor
        # above, so the channel block inserted there at flush time lands beneath them; the bank/water/rice
        # FILLS stay before the anchor (ground the channels must cover).
        for cq_poly, cq_bd, cq_cx, cq_cy in crown_q:
            self._mulberry_rows(cq_poly, cq_bd, cq_cx, cq_cy, rng, chansegs)
        self.M.setdefault("land_use", []).append(
            {"overlay": overlay, "count": n, "eligible": eligible, "plots": [_centroid(p["poly"]) for p in chosen], "leftover_plots": [_centroid(p["poly"]) for p in leftover_plots]}
        )
        return n

    def _landuse_tea_fringe(self: Settlement, net: dict[str, Any], overlay: str) -> int:  # type: ignore[misc]
        """Tea bush rows along the field's dry HIGH margin - the one overlay that is not plot-based.

        The boundary rule is literally 'the line is the highest irrigation ditch', which is what
        net['dry_plots'] already is."""
        n = 0
        for dp in net["dry_plots"]:
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in dp["poly"])
            cid = self._cid("tea")
            self.add(f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>')
            xs = [p[0] for p in dp["poly"]]
            ys = [p[1] for p in dp["poly"]]
            rows = "".join(
                f'<line x1="{min(xs):.1f}" y1="{y:.1f}" x2="{max(xs):.1f}" y2="{y:.1f}" stroke="#5C7A3E" stroke-width="2.4" opacity="0.75"/>'
                for y in [min(ys) + 6 + i * 8 for i in range(int((max(ys) - min(ys)) / 8))]
            )
            self.add(f'<g clip-path="url(#{cid})">{rows}</g>')
            n += 1
        self.M.setdefault("land_use", []).append({"overlay": overlay, "count": n})
        return n

    def _landuse_repaint_leftovers(self: Settlement, elig: list[Any], chosen: list[Any], overlay: str, eligible: str, rng: random.Random) -> list[Any]:  # type: ignore[misc]
        """Repaint the unconverted plots of a WHOLESALE conversion as standing rice rather than bare outlines.

        Returns the leftover plots, which the land_use record reports."""
        leftover_plots: list[Any] = []
        if overlay == "mulberry_fishpond" and eligible == "all":
            chosen_ids = {id(c) for c in chosen}
            leftover_plots = [p for p in elig if id(p) not in chosen_ids]
            _lst = random.getstate()  # the decorative mottle must not shift downstream placement
            for p in leftover_plots:
                pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["poly"])
                lfill = p.get("fill", "#A6C398")
                random.seed(int(sum(x for x, _ in p["poly"]) * 7 + sum(y for _, y in p["poly"]) * 13))
                if lfill == "#93B7AC":
                    # a FLOODED leftover reads with a ROUNDED, slightly IRREGULAR waterline (GM 2026-07-23):
                    # bund corners silt round and a hand-piled bund toe wanders, so standing water in a
                    # bunded field never holds a drafting-square corner. Erase the base parcel back to floor
                    # green, then draw the water a hair inside the bunds with jittered erosion fillets (the
                    # same _rounded_pond the dug ponds use - smaller inset, and NO water-edge stroke, so a
                    # flooded field never reads as dug infrastructure). The thin green rim left showing is
                    # the bund top the water cannot overtop.
                    self.add(f'<polygon points="{pts}" fill="#A6C398" stroke="#A6C398" stroke-width="3" stroke-linejoin="round"/>')
                    fd, fpoly = self._rounded_pond(p["poly"], inset=2.5, reach=12.0, rng=rng)
                    self.add(f'<path d="{fd}" fill="{lfill}"/>')
                    fpts = " ".join(f"{x:.1f},{y:.1f}" for x, y in fpoly)
                    self._paddy_surface(fpoly, fpts, flooded=True, pitch=4.5)
                else:
                    self.add(f'<polygon points="{pts}" fill="{lfill}" stroke="{lfill}" stroke-width="3" stroke-linejoin="round"/>')
                    self._paddy_surface(p["poly"], pts, flooded=False, pitch=4.5)  # jittered-grid mottle, ~3-6 px between shoots (GM 2026-07-23)
            random.setstate(_lst)
        return leftover_plots

    def _landuse_draw_plot(  # type: ignore[misc]
        self: Settlement,
        p: dict[str, Any],
        pts: str,
        cx: float,
        cy: float,
        overlay: str,
        colors: dict[str, str],
        chansegs: list[tuple[Pt, Pt]],
        rng: random.Random,
        dikeponds: list[dict[str, Any]],
        crown_q: list[tuple[Poly, str, float, float]],
    ) -> None:
        """Draw ONE converted plot: a dike-pond unit (bank, water, deferred crowns, record) or a lotus field.

        `dikeponds` and `crown_q` are appended to in place - the caller needs both after the loop."""
        if overlay == "mulberry_fishpond":
            # 桑基魚塘: a raised MULBERRY DIKE (基, planted) surrounds an inset fish POND (塘, water) whose
            # dug corners are ROUNDED - an earthen pond erodes to a rounded outline, never the poured-
            # concrete right angle a premodern village had no way to make (GM 2026-07-22, issues 3 + 5).
            # Fourth pass (GM 2026-07-23, settlements.md 'Polder fourth pass'): the dike draws as PLANTED
            # GROUND, not a flat green band - the perimeter dike's own treatment (mottled earthen bank)
            # carrying two planted ROWS of coppiced mulberry crowns (_mulberry_rows). Its corners ease
            # with small erosion fillets but the dike KEEPS its rectangular character - straight dikes
            # are attested (see settlements.md 'Polder mosaic'). The bank sits at the TRUE parcel line
            # (inset 0), because the canal at its toe bounds it: an early +5 px expansion put banks over
            # the wavering laterals in 72 places on Kuwabata (mulberry_banks_clear_of_channels caught
            # it). The base parcel's tan bund stroke is erased by a floor-color UNDERLAY instead - the
            # floor, the base parcels, and the cover all share _RICE_GREEN, so it vanishes into both;
            # the corner fillets expose that same cover, reading as floor.
            _dm = min(
                math.hypot((p["poly"][i][0] + p["poly"][(i + 1) % len(p["poly"])][0]) / 2 - cx, (p["poly"][i][1] + p["poly"][(i + 1) % len(p["poly"])][1]) / 2 - cy) for i in range(len(p["poly"]))
            )
            _sc = 1.0 + 2.5 / max(1.0, _dm)
            cover = " ".join(f"{cx + (x - cx) * _sc:.1f},{cy + (y - cy) * _sc:.1f}" for x, y in p["poly"])
            self.add(f'<polygon points="{cover}" fill="#A6C398"/>')
            # THE CANAL AT THE TOE BOUNDS THE BANK (settlements.md 'Mulberry bushes keep clear of the
            # canals'): where a mosaic-bent lateral rides INSIDE the parcel line (Kuwabata: two west-edge
            # ponds, up to 3.6 px), the whole pond unit is DUG BACK - shrunk about its centroid until the
            # bank clears the canal by >= 1 px - rather than drawing bank earth over open water. The
            # cover above still spans the ORIGINAL parcel, so the base bund stroke stays erased and the
            # dug-back margin reads as floor. The shrunk outline is what `dikeponds` records, so
            # mulberry_banks_clear_of_channels and dikepond_water_within_banks read the drawn truth.
            qpoly: Poly = [(float(qx), float(qy)) for qx, qy in p["poly"]]
            pen = 0.0
            qx0, qx1 = min(q[0] for q in qpoly) - 2, max(q[0] for q in qpoly) + 2
            qy0, qy1 = min(q[1] for q in qpoly) - 2, max(q[1] for q in qpoly) + 2
            for ca, cb in chansegs:
                if max(ca[0], cb[0]) < qx0 or min(ca[0], cb[0]) > qx1 or max(ca[1], cb[1]) < qy0 or min(ca[1], cb[1]) > qy1:
                    continue
                csteps = max(1, int(math.hypot(cb[0] - ca[0], cb[1] - ca[1]) / 4))
                for ck in range(csteps + 1):
                    qpx = ca[0] + (cb[0] - ca[0]) * ck / csteps
                    qpy = ca[1] + (cb[1] - ca[1]) * ck / csteps
                    if point_in_poly(qpx, qpy, qpoly):
                        pen = max(pen, min(seg_dist(qpx, qpy, qpoly[j], qpoly[(j + 1) % len(qpoly)]) for j in range(len(qpoly))))
            if pen > 0.0:
                _s2 = max(0.7, 1.0 - (pen + 1.0) / max(1.0, _dm))
                qpoly = [(cx + (qx - cx) * _s2, cy + (qy - cy) * _s2) for qx, qy in qpoly]
            bd, bpoly = self._rounded_pond(qpoly, inset=0.0, reach=8.0, rng=rng)
            self.add(f'<path d="{bd}" fill="#C2A772" stroke="#9C8558" stroke-width="1.2" stroke-linejoin="round" opacity="0.95"/>')
            wd, wpoly = self._rounded_pond(qpoly, inset=11.0, reach=16.0, rng=rng)
            self.add(f'<path d="{wd}" fill="{colors[overlay]}" stroke="#6C9CBE" stroke-width="1.4"/>')
            crown_q.append((qpoly, bd, cx, cy))  # crowns drawn after the late-water anchor (see below)
            # `bank` = the planted band's outer edge, recorded so mulberry_banks_clear_of_channels has
            # manifest teeth: the crowns fill the bank, so "no canal runs inside a bank" bounds the bushes
            dikeponds.append(
                {
                    "parcel": [[round(x, 1), round(y, 1)] for x, y in qpoly],
                    "water": [[round(x, 1), round(y, 1)] for x, y in wpoly],
                    "bank": [[round(x, 1), round(y, 1)] for x, y in bpoly],
                }
            )
        else:  # lotus - a DEEP-WATER lotus field (teal plot body + a few lily pads / blooms)
            self.add(f'<polygon points="{pts}" fill="{colors[overlay]}" stroke="#6C9CBE" stroke-width="1.6" stroke-linejoin="round"/>')
            self.add("".join(f'<circle cx="{cx + rng.uniform(-14, 14):.1f}" cy="{cy + rng.uniform(-10, 10):.1f}" r="{rng.uniform(2.5, 4):.1f}" fill="#C98BA6" opacity="0.85"/>' for _ in range(3)))

    def _landuse_dikepond_sluices(self: Settlement, net: dict[str, Any], dikeponds: list[dict[str, Any]]) -> None:  # type: ignore[misc]
        """Plumb each pond inlet-HIGH and outlet-LOW: a feeder from uphill, a drain to downhill, so the
        whole dike-pond net runs in series down the slope from the high intake to the low outfall."""
        # FEED + DRAIN SLUICES (GM 2026-07-22): a pond on a slope is plumbed inlet-HIGH, outlet-LOW so water
        # flows DOWNHILL through it - so each pond gets TWO gates: a FEEDER from an uphill point on the creek
        # network (water runs down INTO the pond at its uphill corner) and a separate DRAIN to a downhill
        # point (water runs down OUT of it at its downhill corner). Each connects to the nearest channel OR
        # neighbor pond that lies in the right fall direction, so the whole dike-pond net runs in series
        # down the slope from the high intake to the low outfall. Drawn as `<line>` culverts (the channel
        # z-order audit ignores them). Validated by dikeponds_fed_and_drained; see settlements.md.
        dd = float(self.M["meta"].get("down_deg", 90))
        _dx, _dy = math.cos(math.radians(dd)), math.sin(math.radians(dd))

        def _fall(q: Pt) -> float:
            return q[0] * _dx + q[1] * _dy

        _cpts: Poly = []  # densified channel points - the creek-network connection candidates
        for ch in net["channels"]:
            cpp = ch["pts"]
            for a, b in zip(cpp, cpp[1:], strict=False):
                steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 8))
                for k in range(steps + 1):
                    _cpts.append((a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps))
        waters = [dp["water"] for dp in dikeponds]
        _reach, _margin = 62.0, 8.0

        def _target(anchor: Pt, i: int, uphill: bool) -> Pt | None:
            # nearest connection point (a channel point OR another pond's edge) strictly up/down-hill of it
            af = _fall(anchor)
            best: Pt | None = None
            bd = _reach * _reach
            cands = _cpts + [q for j, w2 in enumerate(waters) if j != i for q in w2]
            for q in cands:
                qf = _fall(q)
                if (qf < af - _margin) if uphill else (qf > af + _margin):
                    d = (anchor[0] - q[0]) ** 2 + (anchor[1] - q[1]) ** 2
                    if d < bd:
                        bd, best = d, (q[0], q[1])
            return best

        sluices: list[dict[str, Any]] = []
        for i, w in enumerate(waters):
            top = min(w, key=_fall)  # the pond's uphill corner - fed here (water runs down in)
            bot = max(w, key=_fall)  # the pond's downhill corner - drained here (water runs down out)
            for anchor, uphill, kind in ((top, True, "feed"), (bot, False, "drain")):
                tp = _target((anchor[0], anchor[1]), i, uphill)
                if tp is not None:
                    self.add(f'<line x1="{anchor[0]:.1f}" y1="{anchor[1]:.1f}" x2="{tp[0]:.1f}" y2="{tp[1]:.1f}" stroke="#6C9CBE" stroke-width="2.4" stroke-linecap="round" opacity="0.95"/>')
                    sluices.append({"a": [round(anchor[0], 1), round(anchor[1], 1)], "b": [round(tp[0], 1), round(tp[1], 1)], "kind": kind})
        self.M["dikepond_sluices"] = sluices

    def _mulberry_rows(self: Settlement, poly: Sequence[Pt], bank_d: str, cx: float, cy: float, rng: random.Random, channels: Sequence[tuple[Pt, Pt]] | None = None) -> None:  # type: ignore[misc]
        """The 桑基 (mulberry-dike) half of a dike-pond unit rendered as what it is: PLANTED ground. Sparse
        earth mottle (patch-repairs, the perimeter dike's look) under two planted ROWS of coppiced mulberry
        crowns. TRUE SCALE (settlements.md 'Polder fourth pass'): silkworm mulberry was coppiced into low
        bushes with ~4-6 ft crowns in dense rows (~1 bush per 10-20 sq ft - hundreds per pond), so at
        1 px = 1 ft honest "actual trees" ARE a packed dot band; the crowns here are r 2.2-3.6 px at ~6 px
        in-row spacing (the loose end of the attested 3-5 ft, for pixel separation), never inflated glyphs.
        Rows are homothetic loops between the water inset (11 px) and the bank edge (the true parcel line);
        everything clips to the bank path, so a crown may overhang the water edge (organic) but never
        spills onto the polder floor. BUSHES KEEP CLEAR OF THE CANALS (GM 2026-07-23, refined 2026-07-24):
        the bush TRUNK stays off the canal - any crown whose CENTER lies within 3.5 px of a channel
        centerline in `channels` is dropped - but the crown EDGE may overhang the water, and the caller
        draws these crown groups AFTER the late-water anchor, so an overhanging leaf edge covers the
        channel stroke rather than the channel slicing across a crown (the canal runs BETWEEN the bushes
        at ground level). The paired manifest teeth are `mulberry_banks_clear_of_channels`, which reads
        the recorded per-pond `bank` outline. The dots themselves stay unrecorded (decorative)."""
        n = len(poly)
        mids = [((poly[i][0] + poly[(i + 1) % n][0]) / 2, (poly[i][1] + poly[(i + 1) % n][1]) / 2) for i in range(n)]
        apo = sum(math.hypot(mx - cx, my - cy) for mx, my in mids) / n
        if apo <= 12.0:
            return  # a parcel too small to hold the water inset has no bank to plant
        s_w = max(0.4, 1.0 - 11.0 / apo)  # the water-edge homothety (matches _rounded_pond's inset=11)
        s_b = 1.0  # the bank edge is the TRUE parcel line (the canal at the toe bounds the bank)
        cid = self._cid("mb")
        g = [f'<clipPath id="{cid}"><path d="{bank_d}"/></clipPath>', f'<g clip-path="url(#{cid})">']

        def walk(scale: float, step: float) -> list[Pt]:
            loop = [(cx + (q[0] - cx) * scale, cy + (q[1] - cy) * scale) for q in poly]
            out: list[Pt] = []
            for a, b in zip(loop, loop[1:] + loop[:1], strict=True):
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                for k in range(int(seg / step)):
                    f = (k + 0.5) * step / seg
                    out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            return out

        # only channel segments near THIS parcel matter (the parcel bbox padded by the bank + crown reach)
        px0, px1 = min(q[0] for q in poly) - 20, max(q[0] for q in poly) + 20
        py0, py1 = min(q[1] for q in poly) - 20, max(q[1] for q in poly) + 20
        near = [(a, b) for a, b in (channels or []) if max(a[0], b[0]) >= px0 and min(a[0], b[0]) <= px1 and max(a[1], b[1]) >= py0 and min(a[1], b[1]) <= py1]

        def chan_dist(qx: float, qy: float) -> float:
            best = 1e9
            for a, b in near:
                vx, vy = b[0] - a[0], b[1] - a[1]
                ln2 = vx * vx + vy * vy
                u = 0.0 if ln2 == 0 else max(0.0, min(1.0, ((qx - a[0]) * vx + (qy - a[1]) * vy) / ln2))
                best = min(best, math.hypot(qx - (a[0] + u * vx), qy - (a[1] + u * vy)))
            return best

        for mx, my in walk(s_w + 0.5 * (s_b - s_w), 30.0):  # earth mottle: packed / dried patches of different ages
            mcol = rng.choice(("#A8895A", "#B79B68", "#D2BC8C", "#9C8150"))
            g.append(f'<ellipse cx="{mx + rng.uniform(-3, 3):.1f}" cy="{my + rng.uniform(-3, 3):.1f}" rx="{rng.uniform(4, 8):.1f}" ry="{rng.uniform(3, 6):.1f}" fill="{mcol}" opacity="0.35"/>')
        for t in (0.30, 0.72):  # two planted rows across the band
            # in-row step 4.4 px: adjacent 4.4-7.2 ft crowns TOUCH but stay non-concentric (the GM's `oo`
            # not `o o`, 2026-07-23), with bank tan showing in the notches. Measured density lands at
            # ~1 bush per 23 sq ft (the old 6 px step sat at ~1/31; attested is 1 per 10-20 - still shy of
            # the low end because only 2 rows fit legibly, but the touching-crown READ now matches a real
            # planted dike row)
            for x, y in walk(s_w + t * (s_b - s_w), 4.4):
                jx, jy = x + rng.uniform(-1.3, 1.3), y + rng.uniform(-1.3, 1.3)
                r = rng.uniform(2.2, 3.6)
                ccol = rng.choice(("#6E8B4A", "#7C9A54", "#5E7C40"))
                # the bush TRUNK stays off the canal (center > 3.5 px from the centerline), but the crown
                # EDGE may overhang the water (GM 2026-07-24): crowns draw ABOVE the channel strokes, so an
                # overhanging leaf edge covers the channel - never the channel slicing across a crown
                if near and chan_dist(jx, jy) < 3.5:
                    continue
                g.append(f'<circle cx="{jx:.1f}" cy="{jy:.1f}" r="{r:.1f}" fill="{ccol}" opacity="0.85"/>')
        g.append("</g>")
        self.add("".join(g))

    @staticmethod
    def _pick_overlay_plots(eligible: list[Any], take: int, clustered: bool, rng: random.Random) -> list[Any]:
        """Choose which eligible plots convert.

        CLUSTERED (the dike-pond case): grow PATCHES from a few seed plots outward by nearest-neighbor.
        The 桑基魚塘 conversion was 挖塘培基 - dig one low plot into a pond, pile the spoil into a dike
        around it - a single-plot job one household did in one dry season. It therefore spread as a
        patchwork radiating from where someone started, not as an even sprinkle over the district.
        (research.md D2; Shunde grew 40,084 -> 58,094 mu over 61 years, plot by plot.)

        UNCLUSTERED (lotus): the wet bottom is already contiguous by nature, so an even draw from the
        eligible set lands contiguously without extra help.
        """
        if take >= len(eligible):
            return list(eligible)
        if not clustered:
            return rng.sample(eligible, take)
        cents = [_centroid(p["poly"]) for p in eligible]
        n_seeds = max(1, round(take / 9))  # a handful of households started digging, not everyone at once
        picked = set(rng.sample(range(len(eligible)), min(n_seeds, len(eligible))))
        while len(picked) < take:
            # grow the patch: take the unpicked plot nearest to anything already converted
            best = min(
                (i for i in range(len(eligible)) if i not in picked),
                key=lambda i: min(math.dist(cents[i], cents[j]) for j in picked),
            )
            picked.add(best)
        return [eligible[i] for i in sorted(picked)]
