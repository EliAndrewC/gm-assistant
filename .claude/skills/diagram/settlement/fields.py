"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import hashlib
import math
import random
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast

from ._geom import (
    FLOODED_SHADES,
    LAND,
    PADDY_SHADES,
    RICE_GREENS,
    RIPE_SHADES,
    Poly,
    Pt,
    edge_dist,
    organic_bbox,
    organic_poly,
    point_in_poly,
    point_quad_dist,
    quad_hits_seg,
    seg_closest,
    seg_dist,
    seg_in_ellipse_core,
    smooth_closed,
    smooth_points,
)
from ._knobs import CITY_TIER_SCALES, _centroid, _sharp_corners, _toward

if TYPE_CHECKING:
    from .core import Settlement


class FieldsMixin:
    # ---- fields
    def paddy_field(  # type: ignore[misc]
        self: Settlement, shape: Any, label: Any, name: str, amp: float = 52, taxfree: int = 0, fallow_patch: Any = None, label_xy: Any = None, plot: float = 46, kind: str = "paddy"
    ) -> None:
        """shape: a bbox (x0,y0,x1,y1) OR a list of base polygon vertices (e.g. a V).
        `plot` is the target plot (sub-paddy) size in px: the field is quilted into jittered
        bunded plots at roughly this grain. Smaller -> a finer patchwork of more, smaller paddies.
        Default 46 is the fine grain that reads as intensively-worked premodern paddy (a 1-cho
        holding was subdivided into dozens of small irregular bunded plots). VERIFIED HONEST at the
        declared scales (audit 2026-07-21): the village grain (plot=34 at 2 ft/px -> ~435 m2) sits
        inside the real 130-600 m2 basin band, and the default (46 -> ~785 m2 at 2 ft/px) is within
        the real parcel range (mean ~1 mu = ~600 m2, merged holdings larger) - no legibility
        inflation is in play, and the houses are true-scale too. The bund stroke draws at near-true
        aze width for the map scale. See the "Paddy plot grain" entry in the settlements.md historical grounding."""
        from waterfields import AZE, aze_w

        bund = aze_w(self.ftpx)  # near-true-scale aze stroke (~1.5 real ft; the why lives at waterfields.AZE)
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            bbox = tuple(shape)
            outline = organic_bbox(bbox, amp)
        else:
            base = list(shape)
            outline = organic_poly(base, amp)
            xs = [p[0] for p in outline]
            ys = [p[1] for p in outline]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        x0, y0, x1, y1 = bbox
        smoothed = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": kind, "outline": [[x, y] for (x, y) in smoothed]})
        self.field_polys.append(smoothed)
        d = smooth_closed(outline)
        cid = self._cid('fld')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp

        # PADDY PATCHWORK: pre-modern paddies were an IRREGULAR patchwork of odd-sized bunded plots fitted
        # together by piecemeal reclamation and inheritance - NOT the regular grid of modern (Meiji/Showa)
        # land consolidation. Build it by recursively splitting the field with straight, slightly-angled aze
        # (bund) lines that cut the LONG axis of each plot at a jittered fraction, down to the target grain
        # (with size variation), so bunds meet at T-junctions like real cadastral paddy. See settlements.md.
        _fillstate = random.getstate()  # ISOLATE the paddy fill RNG: the patchwork, crop
        random.seed(int(abs(x0) * 7 + abs(y0) * 13 + abs(x1) * 3 + len(name)))  # roll, growth stage and mottle
        plots = self._paddy_plots((ex0, ey0, ex1, ey1), plot)  # are decorative and must NOT shift
        self.add(f'<g clip-path="url(#{cid})">')  # downstream house placement
        self.add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1 - ex0:.0f}" height="{ey1 - ey0:.0f}" fill="{AZE}"/>')
        interior: list[Any] = []
        for poly in plots:
            pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in poly)
            cx = sum(q[0] for q in poly) / len(poly)
            cy = sum(q[1] for q in poly) / len(poly)
            # CROP MIX: an irrigated valley exists to grow RICE (~85% of the watered common). Dry upland crops
            # (barley/veg, soy) cluster on the MARGINS - the higher, harder-to-water rim - while the well-watered
            # interior is all paddy. So dry/soy probability rises toward the field edge. See settlements.md 'Crop mix'.
            edge = max(0.0, 1.0 - edge_dist(cx, cy, smoothed) / (2.4 * plot))  # 1 at the rim, 0 deep interior
            r = random.random()
            dry_p, soy_p = 0.05 + 0.24 * edge, 0.03 + 0.11 * edge
            crop = 'dry' if r < dry_p else ('soy' if r < dry_p + soy_p else 'rice')
            if crop == 'rice':
                # a village transplants TOGETHER (shared water, exchanged labor), so its paddies are largely
                # ONE stage - here high-summer green - with only minor spread (early/late rice varieties, the odd
                # low flooded plot); NOT a rainbow of stages. See settlements.md 'Crop mix / paddy surface'.
                st = random.random()
                if st < 0.06:
                    fill, flooded = random.choice(FLOODED_SHADES), True
                elif st > 0.95:
                    fill, flooded = random.choice(RIPE_SHADES), False
                else:
                    fill, flooded = random.choice(PADDY_SHADES), False
                self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{AZE}" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                self._paddy_surface(poly, pts, flooded)
            else:
                fill = 'url(#drycrop)' if crop == 'dry' else '#9CB36A'
                self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{AZE}" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                self._rows(poly, pts, crop)  # dryland crops ARE ridge/row-cultivated
            if point_in_poly(cx, cy, smoothed):
                interior.append((poly, cx, cy))
        if label and taxfree:
            self._taxfree_plots(interior, taxfree)
        if fallow_patch:
            self._fallow_patch(fallow_patch)
        self.add('</g>')
        random.setstate(_fillstate)  # end fill-RNG isolation
        self.add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')
        if label:
            lx, ly = label_xy if label_xy else ((x0 + x1) / 2, (y0 + y1) / 2)
            z = self.add_label(
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>'
            )
            self._record_label(lx, ly, label, 15, "middle", z)

    @staticmethod
    def _split_convex(poly: Poly, px: float, py: float, nx: float, ny: float) -> tuple[Poly, Poly]:
        """Split a convex polygon by the line through (px, py) with normal (nx, ny) into (pos, neg) polygons."""

        def side(v: Pt) -> float:
            return (v[0] - px) * nx + (v[1] - py) * ny

        pos: Poly = []
        neg: Poly = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            sa, sb = side(a), side(b)
            if sa >= 0:
                pos.append(a)
            if sa <= 0:
                neg.append(a)
            if (sa > 0) != (sb > 0):
                t = sa / (sa - sb)
                pos.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                neg.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        return pos, neg

    def _paddy_plots(self: Settlement, bbox: Any, grain: float) -> list[Poly]:  # type: ignore[misc]
        """Recursively split a field into an irregular patchwork whose plots share a coherent GRAIN aligned to
        the water and slope - the bunds run along the CONTOUR (NE-SW, for the default NW-uphill tilt) and down
        the FALL LINE (NW-SE), with plots mildly elongated along-contour and stepping downhill - so the paddy
        reads as ORGANIZED BY THE WATER, not randomly diced. Still irregular (jittered split fractions +
        slightly non-parallel bunds), just coherent. Tiles the bbox; clipped to the field outline."""
        ux, uy = 0.7071, -0.7071  # contour (along-slope) = a plot's LONG axis
        fx, fy = 0.7071, 0.7071  # fall line (downhill SE) = a plot's SHORT axis
        aspect = 1.7
        tvf, tvu = grain * 0.78, grain * 0.78 * aspect  # target extents across the fall line / along the contour
        x0, y0, x1, y1 = bbox
        stack: list[Poly] = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
        out: list[Poly] = []
        guard = 0
        while stack and guard < 24000:
            guard += 1
            poly = stack.pop()
            cx = sum(q[0] for q in poly) / len(poly)
            cy = sum(q[1] for q in poly) / len(poly)
            us = [q[0] * ux + q[1] * uy for q in poly]
            fs = [q[0] * fx + q[1] * fy for q in poly]
            u_ext, f_ext = max(us) - min(us), max(fs) - min(fs)
            over_f = f_ext > tvf * random.uniform(0.72, 1.45)
            over_u = u_ext > tvu * random.uniform(0.78, 1.6)
            if not over_f and not over_u:
                out.append(poly)
                continue
            if over_f and (not over_u or f_ext / tvf >= u_ext / tvu):
                nx, ny, lo, hi, cen = fx, fy, min(fs), max(fs), cx * fx + cy * fy  # contour bund (normal = fall line)
            else:
                nx, ny, lo, hi, cen = ux, uy, min(us), max(us), cx * ux + cy * uy  # cross bund (normal = contour)
            d = lo + (hi - lo) * random.uniform(0.36, 0.64)  # jittered split position
            px, py = cx + (d - cen) * nx, cy + (d - cen) * ny  # a point on the cut line
            ang = random.uniform(-0.12, 0.12)  # slight wobble - bunds not ruler-parallel
            ca, sa = math.cos(ang), math.sin(ang)
            nnx, nny = nx * ca - ny * sa, nx * sa + ny * ca
            a, b = self._split_convex(poly, px, py, nnx, nny)
            if len(a) >= 3 and len(b) >= 3:
                stack.append(a)
                stack.append(b)
            else:
                out.append(poly)  # pragma: no cover - defensive: a line cutting a convex polygon yields two >=3-gons except the measure-zero exact-tangent case
        return out + stack

    def _taxfree_plots(self: Settlement, interior: Any, taxfree: int) -> None:  # type: ignore[misc]
        """Mark `taxfree` scattered interior paddy plots vermilion (a priestess's / temple's tax-free land)."""
        if not interior:
            return
        interior = sorted(interior, key=lambda t: (round(t[2] / 40), t[1]))  # spread them across the field
        n = len(interior)
        for i in sorted(set(min(n - 1, int(n * (k + 0.5) / (taxfree + 1))) for k in range(taxfree))):
            poly, cx, cy = interior[i]
            pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in poly)
            self.add(f'<polygon points="{pts}" fill="#A03020" fill-opacity="0.22" stroke="#A03020" stroke-width="4"/>')
            self.M["taxfree"].append([round(cx, 1), round(cy, 1)])

    def _paddy_surface(self: Settlement, poly: Poly, pts: str, flooded: bool, cap: int = 22, pitch: float | None = None) -> None:  # type: ignore[misc]
        """A WET paddy: a flooded, mottled sheet (irregular hand-transplanted shoots, plus a faint water sheen
        for a freshly-flooded plot) - NOT ruled rows. Premodern rice was transplanted irregularly; crisp
        checkrow planting (seijoue) is a Meiji improvement, so ruled rows on a paddy read as modern (the same
        era-tell as the consolidation grid). See settlements.md 'Crop mix / paddy surface'.

        Two mottle modes. Default (pitch=None): the sparse random scatter every comb map has always drawn
        (byte-stable). `pitch` (GM 2026-07-23, the polder-leftover repaint): a JITTERED GRID - dot centers
        ~pitch apart with alternate-row half-offset, +-pitch/3 jitter and ~10% dropout, so spacing lands
        irregular in the ~2/3..4/3 pitch band and no row or column ever rules through. That is the truer
        read of traditional transplanting (roughly EVEN density - density drives yield - but never ruled;
        real hills sit ~1/sq ft, one per PIXEL at 1 ft/px, so any drawable mottle is a sample regardless)."""
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        rcid = self._cid('ps')
        g = [f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{rcid})">']
        if flooded:  # faint sheen lines = standing water catching the light
            for _ in range(2):
                yy = random.uniform(y0 + 2, y1 - 2)
                g.append(f'<line x1="{x0:.0f}" y1="{yy:.0f}" x2="{x1:.0f}" y2="{yy:.0f}" stroke="#CFDFD3" stroke-width="1.5" opacity="0.4"/>')
        if pitch is None:
            n = min(cap, max(3, int((x1 - x0) * (y1 - y0) / 80)))  # sparse irregular shoots (the transplant mottle); cap=22 suits ~0.05-ac comb cells
            for _ in range(n):
                g.append(f'<circle cx="{random.uniform(x0, x1):.1f}" cy="{random.uniform(y0, y1):.1f}" r="1.0" fill="#6F9061" opacity="0.5"/>')
        else:
            row = 0
            yy2 = y0 + random.uniform(0, pitch)
            while yy2 < y1:
                xx = x0 + random.uniform(0, pitch) + (pitch / 2 if row % 2 else 0.0)
                while xx < x1:
                    if random.random() > 0.1:
                        g.append(f'<circle cx="{xx + random.uniform(-pitch / 3, pitch / 3):.1f}" cy="{yy2 + random.uniform(-pitch / 3, pitch / 3):.1f}" r="1.0" fill="#6F9061" opacity="0.5"/>')
                    xx += pitch
                yy2 += pitch
                row += 1
        g.append('</g>')
        self.add(''.join(g))

    def _rows(self: Settlement, quad: Poly, pts: str, crop: str) -> None:  # type: ignore[misc]
        xq = [p[0] for p in quad]
        yq = [p[1] for p in quad]
        cx0, cx1, cy0, cy1 = min(xq), max(xq), min(yq), max(yq)
        ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        diag = math.hypot(cx1 - cx0, cy1 - cy0)
        theta = random.uniform(-0.6, 0.6)  # per-plot row angle
        dxu, dyu = math.cos(theta), math.sin(theta)
        nx, ny = -dyu, dxu
        rcid = self._cid('rc')
        self.add(f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>')
        # _rows is only ever called for dry/soy plots (rice paddies get _paddy_surface, no rows), so the
        # styling here is the dryland one - dashed, olive, wider spacing
        spacing, stroke, wdt, dash, op = 13, '#7E9B54', 0.8, ' stroke-dasharray="1,3"', 0.85
        g = [f'<g clip-path="url(#{rcid})">']
        s = -diag / 2
        while s <= diag / 2:
            mx_, my_ = ccx + nx * s, ccy + ny * s
            g.append(
                f'<line x1="{mx_ - dxu * diag / 2:.0f}" y1="{my_ - dyu * diag / 2:.0f}" '
                f'x2="{mx_ + dxu * diag / 2:.0f}" y2="{my_ + dyu * diag / 2:.0f}" '
                f'stroke="{stroke}" stroke-width="{wdt}"{dash} opacity="{op}"/>'
            )
            s += spacing
        g.append('</g>')
        self.add(''.join(g))

    def _fallow_patch(self: Settlement, base: Poly) -> None:  # type: ignore[misc]
        """A blighted sub-region inside a field: fallow stipple + red X marks. No
        abandoned houses implied (that is a village-specific story, not universal)."""
        d = smooth_closed(organic_poly(base, 16))
        self.add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.6" stroke-dasharray="5,3"/>')
        xs = [p[0] for p in base]
        ys = [p[1] for p in base]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        for _ in range(4):
            mx = cx + random.uniform(-1, 1) * (max(xs) - min(xs)) * 0.28
            my = cy + random.uniform(-1, 1) * (max(ys) - min(ys)) * 0.28
            self.add(f'<g transform="translate({mx:.0f},{my:.0f})" stroke="#9A3A2A" stroke-width="2.4"><line x1="-7" y1="-7" x2="7" y2="7"/><line x1="-7" y1="7" x2="7" y2="-7"/></g>')
        self.M["fallow_patches"].append({"outline": [[round(p[0], 1), round(p[1], 1)] for p in smooth_points(organic_poly(base, 16))]})

    def water_field(  # type: ignore[misc]
        self: Settlement, shape: Any, label: Any, name: str, source: Any, drain: Any, amp: float = 52, taxfree: int = 0, plot: float = 34, label_xy: Any = None, drain_anchor: Any = None
    ) -> None:
        """A rice field built WATER-FIRST: the irrigation network is the generative skeleton, and the plots,
        crops, and colors are all DERIVED from it, so the map actually communicates the hydrology. Water
        enters from `source` (the high NW side, fed from the pond) and drains to `drain` (the low SE side). A
        HEAD ditch runs along the high edge; LATERALS run down the fall line, dividing the field into strips;
        paddies stack between them; a DRAIN ditch collects at the low edge and leaves toward `drain`. Crop
        FOLLOWS the water (rice hugging the ditches, dry upland crops where the network doesn't reach - wide-
        strip middles and the margins); the paddy is ~ONE green (a rice field, not a color mix). Records a
        feed channel (pond->field) and a drain channel (field->drain) so the checks see the supply. See
        settlements.md 'Water-first fields'."""
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            bbox = tuple(shape)
            outline = organic_bbox(bbox, amp)
        else:
            outline = organic_poly(list(shape), amp)
            xs = [q[0] for q in outline]
            ys = [q[1] for q in outline]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        x0, y0, x1, y1 = bbox
        smoothed = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "paddy", "outline": [[x, y] for (x, y) in smoothed]})
        self.field_polys.append(smoothed)
        d = smooth_closed(outline)
        cid = self._cid('fld')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        from waterfields import AZE, aze_w

        bund = aze_w(self.ftpx)

        # WATER FRAME: f = downhill (NW->SE, the fall line), u = contour. Orthonormal, so xy<->uf is exact.
        rt = 0.70710678

        def U(px: float, py: float) -> float:
            return rt * (px - py)

        def Ff(px: float, py: float) -> float:
            return rt * (px + py)

        def XY(u: float, f: float) -> Pt:
            return (rt * (u + f), rt * (f - u))

        ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp
        ous = [U(px, py) for px, py in smoothed]
        ofs = [Ff(px, py) for px, py in smoothed]
        umin, umax = min(ous) - plot, max(ous) + plot
        fmin, fmax = min(ofs) - plot, max(ofs) + plot
        fhi, flo = min(ofs), max(ofs)  # the field's real high (source) / low (drain) edges
        fh, fd = fhi + plot * 1.4, flo - plot * 1.4  # the MAIN canal (near the high edge) + DRAIN (near the low)

        stt = random.getstate()  # ISOLATE the fill RNG (decorative; must not shift houses)
        random.seed(int(abs(x0) * 7 + abs(y0) * 13 + abs(x1) * 3 + len(name)))

        # LATERALS: strip boundaries in u, spaced 1.4-3.2 plots apart (varied width). Each is a continuous
        # wobbly line down f (so both neighboring strips follow the SAME lateral -> a real ditch, T-junctions).
        # u-grid: plot-wide columns (all wobble down f). Every 2-4 columns carries a LATERAL DITCH; a plot is
        # watered from an adjacent lateral or by cascade from the plot above, so the plots FAR from any lateral
        # (wide-gap middles) and at the field MARGINS are the hard-to-water ground -> dry crops go there.
        ub = [umin]
        while ub[-1] < umax - plot * 0.55:
            ub.append(ub[-1] + plot * random.uniform(0.9, 1.35))
        ub.append(umax)
        phase = [random.uniform(0, 6.28) for _ in ub]

        def uline(i: int, f: float) -> float:
            if i == 0 or i == len(ub) - 1:
                return ub[i]
            return ub[i] + 5.0 * math.sin(f / 66.0 + phase[i]) + 3.0 * math.sin(f / 29.0 + phase[i] * 1.7)

        laterals: list[int] = []
        i = random.randint(1, 2)
        while i < len(ub) - 1:
            laterals.append(i)
            i += random.randint(4, 6)

        self.add(f'<g clip-path="url(#{cid})">')
        self.add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1 - ex0:.0f}" height="{ey1 - ey0:.0f}" fill="{AZE}"/>')
        interior: list[Any] = []
        ndry, nrice = 0, 0
        for k in range(len(ub) - 1):
            rows = [fmin]
            while rows[-1] < fmax - plot * 0.6:
                rows.append(rows[-1] + plot * random.uniform(0.85, 1.5))
            rows.append(fmax)
            for j in range(len(rows) - 1):
                fa, fb = rows[j], rows[j + 1]
                fm = (fa + fb) / 2
                quad = [XY(uline(k, fa), fa), XY(uline(k + 1, fa), fa), XY(uline(k + 1, fb), fb), XY(uline(k, fb), fb)]
                pts = ' '.join(f'{q[0]:.0f},{q[1]:.0f}' for q in quad)
                cx = sum(q[0] for q in quad) / 4
                cy = sum(q[1] for q in quad) / 4
                edgef = max(0.0, 1.0 - edge_dist(cx, cy, smoothed) / (1.4 * plot))
                un_irrig = fm < fh or fm > fd  # above the main canal / below the drain: gravity can't flood it
                if un_irrig or edgef + random.uniform(-0.08, 0.08) > 0.6:
                    crop = 'dry' if random.random() < 0.62 else 'soy'
                    fill = 'url(#drycrop)' if crop == 'dry' else '#9CB36A'
                    self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{AZE}" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                    self._rows(quad, pts, crop)
                    ndry += 1
                else:
                    near_ditch = abs(fm - fh) < plot * 1.4 or abs(fm - fd) < plot * 1.4  # water pools at the canal/drain
                    ro = random.random()
                    if near_ditch and ro < 0.3:
                        fill, flooded = random.choice(FLOODED_SHADES), True
                    elif ro > 0.975:
                        fill, flooded = random.choice(RIPE_SHADES), False
                    else:
                        fill, flooded = random.choice(RICE_GREENS), False
                    self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{AZE}" stroke-width="{bund:.1f}" stroke-linejoin="round"/>')
                    self._paddy_surface(quad, pts, flooded)
                    nrice += 1
                if point_in_poly(cx, cy, smoothed):
                    interior.append((quad, cx, cy))
        if label and taxfree:
            self._taxfree_plots(interior, taxfree)
        self.add('</g>')

        # THE WATER NETWORK, drawn ON TOP and clipped to the field: laterals down the fall line, a head ditch
        # along the high edge, a drain ditch along the low edge - the plots were carved to these, so they align.
        def polyline(pairs: Any, w: float) -> None:
            pts = ' '.join(f'{px:.0f},{py:.0f}' for px, py in pairs)
            self.add(f'<polyline points="{pts}" fill="none" stroke="#9CB4C8" stroke-width="{w}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')

        def bnd(u: float, lo: float, step: float) -> float | None:  # first f INSIDE the field scanning from lo; None if absent
            f = lo
            while f <= fmax if step > 0 else f >= fmin:
                if point_in_poly(XY(u, f)[0], XY(u, f)[1], smoothed):
                    return f
                f += step
            return None

        def ditch(pairs: Any, w: float, role: str) -> None:  # draw AND record, so the checks can validate it
            polyline(pairs, w)
            self.M["field_ditches"].append({"poly": [[round(px, 1), round(py, 1)] for px, py in pairs], "role": role, "field": name})

        # CONTINUOUS main + drain along the field's true HIGH / LOW boundaries - sampled only where the field
        # actually exists (bnd returns None otherwise), so no junk endpoints jutting outside. Then LATERALS
        # whose ends SNAP onto the nearest main / drain node - so every lateral provably meets both, and the
        # main/drain read as continuous canals (not a sparse dotted line). Paddies between laterals cascade.
        us = [min(ous) + i * 11 for i in range(int((max(ous) - min(ous)) / 11) + 1)] + [max(ous)]
        main_pts: list[Pt] = []
        drain_pts: list[Pt] = []
        for u in us:
            t, bt = bnd(u, fmin, 6), bnd(u, fmax, -6)
            if t is not None and bt is not None and bt - t > plot * 1.4:
                main_pts.append(XY(u, t + plot * 0.7))
                drain_pts.append(XY(u, bt - plot * 0.7))

        def smooth(pts: Poly) -> Poly:  # kill acute turns where the boundary bends sharply
            if len(pts) < 3:
                return pts  # pragma: no cover - defensive: a real field spans many u-columns, so main/drain always have >=3 sampled points
            for _ in range(3):
                pts = [pts[0]] + [((pts[i - 1][0] + pts[i][0] + pts[i + 1][0]) / 3, (pts[i - 1][1] + pts[i][1] + pts[i + 1][1]) / 3) for i in range(1, len(pts) - 1)] + [pts[-1]]
            return pts

        main_pts, drain_pts = smooth(main_pts), smooth(drain_pts)
        self.add(f'<g clip-path="url(#{cid})">')
        if len(main_pts) >= 2:
            ditch(main_pts, 3.3, "main")  # continuous MAIN canal along the high edge
            ditch(drain_pts, 3.0, "drain")  # continuous DRAIN along the low edge
            for li in laterals:
                if not (0 < li < len(ub) - 1):
                    continue  # pragma: no cover - defensive: laterals are built strictly inside (0, len(ub)-1)
                ut = ub[li]
                t, bt = bnd(ut, fmin, 6), bnd(ut, fmax, -6)
                if t is None or bt is None:
                    continue
                tf, bf = t + plot * 0.7, bt - plot * 0.7
                if bf - tf <= plot * 0.7:
                    continue
                mid = [XY(uline(li, f), f) for f in [tf + i * 14 for i in range(1, int((bf - tf) / 14) + 1)] if f < bf]
                ditch([XY(ut, tf)] + mid + [XY(ut, bf)], 2.0, "lateral")  # ends on the continuous main/drain line
        self.add('</g>')
        random.setstate(stt)

        # feed the MAIN at a single point from the pond; empty the DRAIN to the outlet (anchors safely inside).
        safe = [(t[1], t[2]) for t in interior if edge_dist(t[1], t[2], smoothed) >= 14] or [((x0 + x1) / 2, (y0 + y1) / 2)]
        msafe = [q for q in main_pts if edge_dist(q[0], q[1], smoothed) >= 11] or main_pts or safe
        dsafe = [q for q in drain_pts if edge_dist(q[0], q[1], smoothed) >= 11] or drain_pts or safe
        head_pt = min(msafe, key=lambda q: (q[0] - source[0]) ** 2 + (q[1] - source[1]) ** 2)
        drain_pt = min(dsafe, key=lambda q: (q[0] - drain[0]) ** 2 + (q[1] - drain[1]) ** 2)
        self.channel(source, head_pt, {"kind": "pond"}, {"kind": "field", "name": name}, amp=8, width=2.6)
        self.channel(drain_pt, drain, {"kind": "field", "name": name}, drain_anchor or {"kind": "offmap"}, amp=8, width=2.6)

        self.add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')
        if label:
            lx, ly = label_xy if label_xy else ((x0 + x1) / 2, (y0 + y1) / 2)
            z = self.add_label(
                f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>'
            )
            self._record_label(lx, ly, label, 15, "middle", z)

    def fallow_field(self: Settlement, bbox: Any, name: str, amp: float = 34) -> None:  # type: ignore[misc]
        outline = organic_bbox(bbox, amp)
        d = smooth_closed(outline)
        self.add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.8" stroke-dasharray="6,4"/>')
        sm = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "fallow", "outline": [[x, y] for (x, y) in sm]})
        self.field_polys.append(sm)

    # ---- water
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
        # POND: a low pocket held as open water (research D4). ~55% of eligible fields carry one -
        # tried across the low plots in random order until one takes a legible pond, because a plot
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
            n += 1
        if dikeponds:
            self.M["dikeponds"] = dikeponds
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
