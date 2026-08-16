"""Wet and dry field bodies, and the plot geometry they quilt themselves from.

Split from settlement/fields.py by feature 112 - see settlement/fields/CLAUDE.md for the index.
"""

import math
import random
from typing import TYPE_CHECKING, Any

from .._geom import (
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
    smooth_closed,
    smooth_points,
)

if TYPE_CHECKING:
    from ..core import Settlement


class PaddyMixin:
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
