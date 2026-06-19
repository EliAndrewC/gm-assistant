#!/usr/bin/env python3
"""Settlement-map library for the diagram skill (Mode B).

The TRULY COMMON machinery for drawing Rokugani village/hamlet plans lives here:
the palette, organic fields with irregular crop basins, south-facing house glyphs,
hills + shrines + torii, ponds/streams/channels, size-aware house placement, and
the JSON manifest that check_village.py validates.

A specific settlement (see kikuta-village.gen.py, hikari-no-sato.gen.py) is a thin
script: it instantiates Settlement, declares its fields/water/shrine/houses, and
calls finish(). What varies village to village - number and shape of fields, the
irrigation source (pond vs stream vs field-to-field), torii count, whether a hill
carries the shrine, whether blight left abandoned houses - is passed in, not baked
here. Those declarations are echoed into manifest["meta"] so the validator can
adapt its checks per village instead of assuming one village's specifics.
"""
import json
import math
import os
import random

LAND = '#EFE3C2'
PADDY_SHADES = ['#A7C49C', '#9FBE93', '#AECBA1', '#9BBA8F', '#B4CCA6']


def _signed_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2


def point_in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def seg_dist(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def edge_dist(px, py, poly):
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def smooth_closed(pts):
    n = len(pts)
    d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    return d + 'Z'


def smooth_points(pts, steps=10):
    """Sample the rendered (Catmull-Rom) boundary so the manifest matches what's
    drawn - the curve bows inward of the raw vertices (a hard-won lesson)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        for s in range(steps):
            t = s / steps
            mt = 1 - t
            x = mt**3 * p1[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p2[0]
            y = mt**3 * p1[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p2[1]
            out.append((round(x, 1), round(y, 1)))
    return out


def organic_bbox(bbox, amp):
    """Semi-rectangular core with lobes (outgrowths) and bays (indentations)."""
    x0, y0, x1, y1 = bbox
    edges = [((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)),
             ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))]
    pts = []
    for (sa, sb, (nx, ny)) in edges:
        for i in range(4):
            t = i / 4
            bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
            off = random.uniform(-amp * 0.5, amp)
            if i == 0:
                off *= 0.35
            jt = random.uniform(-amp * 0.18, amp * 0.18)
            pts.append((bx + nx * off + jt, by + ny * off + jt))
    return pts


def organic_poly(base, amp):
    """Organic-ize an arbitrary base polygon (handles concave shapes like a V):
    densify each edge and jitter the samples; smoothing rounds it."""
    pts = []
    n = len(base)
    for i in range(n):
        ax, ay = base[i]
        bx, by = base[(i + 1) % n]
        segs = max(1, int(math.hypot(bx - ax, by - ay) / 150))
        for s in range(segs):
            t = s / segs
            pts.append((ax + (bx - ax) * t + random.uniform(-amp, amp) * 0.5,
                        ay + (by - ay) * t + random.uniform(-amp, amp) * 0.5))
    return pts


def winding(start, end, amp=15, n=2):
    """A gently winding path from start to end (a shallow S, not a straight line)."""
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(float(sx), float(sy))]
    for k in range(1, n + 1):
        t = k / (n + 1)
        off = amp * (1 if k % 2 else -1)
        pts.append((round(sx + dx * t + nx * off, 1), round(sy + dy * t + ny * off, 1)))
    pts.append((float(ex), float(ey)))
    return pts


class Settlement:
    def __init__(self, W=1820, H=1180, seed=23):
        random.seed(seed)
        self.W, self.H = W, H
        self.out = []
        self.placed = []          # (x, y, w, h)
        self.corridors = []       # polylines houses must avoid
        self.field_polys = []     # smoothed outlines used for blocking
        self.ellipses = []        # (cx, cy, rx, ry) hill/pond - block houses
        self._clip = 0
        self._nbig = 0
        self.M = {"houses": [], "fields": [], "fallow_patches": [], "channels": [],
                  "lane": [], "taxfree": [], "torii": [], "shrines": [], "labels": [],
                  "pond": None, "hill": None, "summit": None, "shrine": None,
                  "meta": {"W": W, "H": H}}
        self._header()

    # ---- low level
    def add(self, s):
        self.out.append(s)

    def _cid(self, prefix):
        self._clip += 1
        return f'{prefix}{self._clip}'

    def _header(self):
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" '
                 f'font-family="Georgia, \'Times New Roman\', serif">')
        self.add('<defs>')
        self.add('<pattern id="drycrop" width="12" height="12" patternUnits="userSpaceOnUse">'
                 '<rect width="12" height="12" fill="#CDB57E"/>'
                 '<line x1="0" y1="3" x2="12" y2="3" stroke="#A98E54" stroke-width="0.7"/>'
                 '<line x1="0" y1="8" x2="12" y2="8" stroke="#A98E54" stroke-width="0.7"/></pattern>')
        self.add('<pattern id="fallow" width="14" height="14" patternUnits="userSpaceOnUse">'
                 '<rect width="14" height="14" fill="#D7C49A"/>'
                 '<circle cx="3" cy="4" r="0.9" fill="#A89464"/>'
                 '<circle cx="9" cy="9" r="0.9" fill="#A89464"/>'
                 '<circle cx="11" cy="3" r="0.7" fill="#B7A06C"/></pattern>')
        self.add('</defs>')
        self.add(f'<rect width="{self.W}" height="{self.H}" fill="{LAND}"/>')

    def meta(self, **kw):
        self.M["meta"].update(kw)

    # ---- fields
    def paddy_field(self, shape, label, name, amp=52, taxfree=0, fallow_patch=None, label_xy=None):
        """shape: a bbox (x0,y0,x1,y1) OR a list of base polygon vertices (e.g. a V)."""
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
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "paddy",
                                 "outline": [[x, y] for (x, y) in smoothed]})
        self.field_polys.append(smoothed)
        d = smooth_closed(outline)
        cid = self._cid('fld')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp

        def edges(lo, hi, target):
            e = [lo]
            while True:
                nxt = e[-1] + target * random.uniform(0.6, 1.7)
                if nxt >= hi - target * 0.4:
                    break
                e.append(nxt)
            e.append(hi)
            return e

        xs = edges(ex0, ex1, 76)
        ys = edges(ey0, ey1, 76)
        cols, rows = len(xs) - 1, len(ys) - 1
        P = {}
        for i in range(cols + 1):
            for j in range(rows + 1):
                wl = (xs[min(i + 1, cols)] - xs[max(i - 1, 0)]) / 2
                hl = (ys[min(j + 1, rows)] - ys[max(j - 1, 0)]) / 2
                jx = 0 if i in (0, cols) else random.uniform(-1, 1) * wl * 0.32
                jy = 0 if j in (0, rows) else random.uniform(-1, 1) * hl * 0.32
                P[(i, j)] = (xs[i] + jx, ys[j] + jy)
        self.add(f'<g clip-path="url(#{cid})">')
        self.add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1-ex0:.0f}" height="{ey1-ey0:.0f}" fill="#C2A772"/>')
        for i in range(cols):
            for j in range(rows):
                quad = [P[(i, j)], P[(i + 1, j)], P[(i + 1, j + 1)], P[(i, j + 1)]]
                pts = ' '.join(f'{p[0]:.0f},{p[1]:.0f}' for p in quad)
                r = random.random()
                crop = 'dry' if r < 0.16 else ('soy' if r < 0.30 else 'rice')
                fill = 'url(#drycrop)' if crop == 'dry' else ('#9CB36A' if crop == 'soy' else random.choice(PADDY_SHADES))
                self.add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="2.6" stroke-linejoin="round"/>')
                if crop in ('rice', 'soy'):
                    self._rows(quad, pts, crop)
        if label and taxfree:
            self._taxfree(P, cols, rows, taxfree, smoothed)
        if fallow_patch:
            self._fallow_patch(fallow_patch)
        self.add('</g>')
        self.add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')
        if label:
            lx, ly = label_xy if label_xy else ((x0 + x1) / 2, (y0 + y1) / 2)
            self._record_label(lx, ly, label, 15, "middle")
            self.add(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                     f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                     f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>')

    def _rows(self, quad, pts, crop):
        xq = [p[0] for p in quad]
        yq = [p[1] for p in quad]
        cx0, cx1, cy0, cy1 = min(xq), max(xq), min(yq), max(yq)
        ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        diag = math.hypot(cx1 - cx0, cy1 - cy0)
        theta = random.uniform(-0.6, 0.6)             # per-plot row angle
        dxu, dyu = math.cos(theta), math.sin(theta)
        nx, ny = -dyu, dxu
        rcid = self._cid('rc')
        self.add(f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>')
        if crop == 'rice':
            spacing, stroke, wdt, dash, op = 11, '#86AC90', 0.9, '', 0.7
        else:
            spacing, stroke, wdt, dash, op = 13, '#7E9B54', 0.8, ' stroke-dasharray="1,3"', 0.85
        g = [f'<g clip-path="url(#{rcid})">']
        s = -diag / 2
        while s <= diag / 2:
            mx_, my_ = ccx + nx * s, ccy + ny * s
            g.append(f'<line x1="{mx_-dxu*diag/2:.0f}" y1="{my_-dyu*diag/2:.0f}" '
                     f'x2="{mx_+dxu*diag/2:.0f}" y2="{my_+dyu*diag/2:.0f}" '
                     f'stroke="{stroke}" stroke-width="{wdt}"{dash} opacity="{op}"/>')
            s += spacing
        g.append('</g>')
        self.add(''.join(g))

    def _taxfree(self, P, cols, rows, taxfree, outline):
        # only cells whose centroid is INSIDE the field (so a V's empty notch never
        # gets an invisible, clipped-away plot); spread them out non-contiguously
        interior = []
        for ci in range(cols):
            for cj in range(rows):
                quad = [P[(ci, cj)], P[(ci + 1, cj)], P[(ci + 1, cj + 1)], P[(ci, cj + 1)]]
                cx = sum(p[0] for p in quad) / 4
                cy = sum(p[1] for p in quad) / 4
                if point_in_poly(cx, cy, outline):
                    interior.append((quad, cx, cy))
        n = len(interior)
        if not n:
            return
        idxs = sorted(set(min(n - 1, int(n * (k + 0.5) / (taxfree + 1))) for k in range(taxfree)))
        for i in idxs:
            quad, cx, cy = interior[i]
            pts = ' '.join(f'{p[0]:.0f},{p[1]:.0f}' for p in quad)
            self.add(f'<polygon points="{pts}" fill="#A03020" fill-opacity="0.22" stroke="#A03020" stroke-width="4"/>')
            self.M["taxfree"].append([round(cx, 1), round(cy, 1)])

    def _fallow_patch(self, base):
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
            self.add(f'<g transform="translate({mx:.0f},{my:.0f})" stroke="#9A3A2A" stroke-width="2.4">'
                     f'<line x1="-7" y1="-7" x2="7" y2="7"/><line x1="-7" y1="7" x2="7" y2="-7"/></g>')
        self.M["fallow_patches"].append({"outline": [[round(p[0], 1), round(p[1], 1)] for p in smooth_points(organic_poly(base, 16))]})

    def fallow_field(self, bbox, name, amp=34):
        outline = organic_bbox(bbox, amp)
        d = smooth_closed(outline)
        self.add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.8" stroke-dasharray="6,4"/>')
        sm = smooth_points(outline)
        self.M["fields"].append({"name": name, "bbox": list(bbox), "kind": "fallow",
                                 "outline": [[x, y] for (x, y) in sm]})
        self.field_polys.append(sm)

    # ---- water
    def pond(self, cx, cy, rx, ry, stream_curve=None):
        if stream_curve:
            self.add(f'<path d="{stream_curve}" fill="none" stroke="#9CB4C8" stroke-width="7" opacity="0.85"/>')
            self.add(f'<path d="{stream_curve}" fill="none" stroke="#5C7488" stroke-width="1" stroke-dasharray="2,4"/>')
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#9CB4C8" stroke="#5C7488" stroke-width="2.4"/>')
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx-12}" ry="{ry-10}" fill="none" stroke="#B6CAD8" stroke-width="1" opacity="0.7"/>')
        self.M["pond"] = [cx, cy, rx, ry]
        self.ellipses.append((cx, cy, rx, ry))

    def stream(self, pts):
        """A watercourse entering from off-map (a source channels can draw from)."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="9" opacity="0.85"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#5C7488" stroke-width="1.2" stroke-dasharray="2,5"/>')

    def channel(self, start, end, frm, to, amp=15):
        """frm/to are anchor dicts: {'kind':'pond'|'offmap'|'field','name':...}."""
        poly = winding(start, end, amp=amp)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="4.2" opacity="0.8"/>')
        self.M["channels"].append({"poly": [[x, y] for x, y in poly], "frm": frm, "to": to})
        self.corridors.append(poly)

    def lane(self, pts):
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="#CBB178" stroke-width="16" opacity="0.65"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6B4F2A" stroke-width="1.4" stroke-dasharray="8,8" opacity="0.7"/>')
        self.M["lane"] = [[x, y] for x, y in pts]
        self.corridors.append(pts)

    # ---- hill + shrine + torii
    def hill(self, cx, cy, rx, ry):
        rings = [(cx, cy + 28, rx, ry), (cx, cy, rx * 0.76, ry * 0.76),
                 (cx, cy - 26, rx * 0.52, ry * 0.52), (cx, cy - 44, rx * 0.30, ry * 0.32)]
        self.M["hill"] = [rings[0][0], rings[0][1], rings[0][2], rings[0][3]]
        self.M["summit"] = [rings[3][0], rings[3][1], rings[3][2], rings[3][3]]
        self.ellipses.append((rings[0][0], rings[0][1], rings[0][2], rings[0][3]))
        for (ax, ay, arx, ary), shade in zip(rings, ['#DFD0A2', '#D8C795', '#D0BD87', '#C8B37B']):
            self.add(f'<ellipse cx="{ax:.0f}" cy="{ay:.0f}" rx="{arx:.0f}" ry="{ary:.0f}" fill="{shade}" stroke="#A8995F" stroke-width="1"/>')
        ocx, ocy, orx, ory = rings[0]
        for k in range(30):
            a = 2 * math.pi * k / 30
            ex, ey = ocx + math.cos(a) * orx, ocy + math.sin(a) * ory
            self.add(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex+math.cos(a)*9:.0f}" y2="{ey+math.sin(a)*9:.0f}" stroke="#A8995F" stroke-width="0.9"/>')
        st = random.getstate()
        random.seed(4)
        for _ in range(15):
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0.4, 0.9)
            tx = cx + math.cos(a) * rx * rr
            ty = (cy + 12) + math.sin(a) * ry * rr
            self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{random.uniform(4,6):.1f}" fill="#7E9B5C" stroke="#52663C" stroke-width="0.8"/>')
            self.add(f'<circle cx="{tx-1:.0f}" cy="{ty-1:.0f}" r="1.6" fill="#9DB87A"/>')
        random.setstate(st)
        return (cx, cy - 40)   # summit point for the shrine

    def shrine(self, x, y, w=104, h=68):
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y+h/2-8:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<line x1="{x-w/2:.0f}" y1="{y:.0f}" x2="{x+w/2:.0f}" y2="{y:.0f}" stroke="#6B2A18" stroke-width="0.7"/>')
        self.M["shrine"] = [x - w / 2, y - h / 2, w, h]

    def torii_path(self, ascent):
        """Place one torii at each interior vertex of the ascent polyline; draw the
        winding path. Count is village-specific - pass as many points as torii+ends."""
        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for (tx, ty) in ascent[1:-1]:
            self.M["torii"].append([round(tx, 1), round(ty, 1)])
            self.add(f'<g transform="translate({tx:.0f},{ty:.0f})">'
                     f'<line x1="-16" y1="0" x2="16" y2="0" stroke="#A03020" stroke-width="3.6"/>'
                     f'<line x1="-19" y1="-7" x2="19" y2="-7" stroke="#A03020" stroke-width="3"/>'
                     f'<line x1="-12" y1="-7" x2="-12" y2="17" stroke="#A03020" stroke-width="3"/>'
                     f'<line x1="12" y1="-7" x2="12" y2="17" stroke="#A03020" stroke-width="3"/></g>')

    def torii_even(self, ascent, count):
        """Spread `count` torii by arc-length along an ascent polyline (Kikuta style)."""
        seg = [math.hypot(ascent[i + 1][0] - ascent[i][0], ascent[i + 1][1] - ascent[i][1]) for i in range(len(ascent) - 1)]
        tot = sum(seg)

        def along(t):
            target, acc = t * tot, 0
            for i, sl in enumerate(seg):
                if acc + sl >= target:
                    f = (target - acc) / sl
                    return (ascent[i][0] + (ascent[i + 1][0] - ascent[i][0]) * f,
                            ascent[i][1] + (ascent[i + 1][1] - ascent[i][1]) * f)
                acc += sl
            return ascent[-1]
        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for i in range(count):
            tx, ty = along(0.06 + 0.80 * i / (count - 1))
            self.M["torii"].append([round(tx, 1), round(ty, 1)])
            self.add(f'<g transform="translate({tx:.0f},{ty:.0f})">'
                     f'<line x1="-16" y1="0" x2="16" y2="0" stroke="#A03020" stroke-width="3.6"/>'
                     f'<line x1="-19" y1="-7" x2="19" y2="-7" stroke="#A03020" stroke-width="3"/>'
                     f'<line x1="-12" y1="-7" x2="-12" y2="17" stroke="#A03020" stroke-width="3"/>'
                     f'<line x1="12" y1="-7" x2="12" y2="17" stroke="#A03020" stroke-width="3"/></g>')

    def shrine_hall(self, x, y, label, sublabel="", w=120, h=82, torii=None, primary=False, edge="#6B2A18"):
        """A standalone village SHRINE building on flat ground (villages have shrines,
        not temples). A shrine need not sit on a hill - it is often central to the
        village. primary=True marks it the village's main shrine (sets M['shrine'])."""
        if torii:
            for (tx, ty) in torii:
                self.M["torii"].append([round(tx, 1), round(ty, 1)])
                self.add(f'<g transform="translate({tx:.0f},{ty:.0f})">'
                         f'<line x1="-15" y1="0" x2="15" y2="0" stroke="#A03020" stroke-width="3.4"/>'
                         f'<line x1="-18" y1="-7" x2="18" y2="-7" stroke="#A03020" stroke-width="2.8"/>'
                         f'<line x1="-11" y1="-7" x2="-11" y2="16" stroke="#A03020" stroke-width="2.8"/>'
                         f'<line x1="11" y1="-7" x2="11" y2="16" stroke="#A03020" stroke-width="2.8"/></g>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="{edge}" stroke-width="2"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y+h/2-9:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<line x1="{x-w/2:.0f}" y1="{y:.0f}" x2="{x+w/2:.0f}" y2="{y:.0f}" stroke="{edge}" stroke-width="0.7"/>')
        self.M["shrines"].append({"x": x, "y": y, "w": w, "h": h, "label": label})
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        self.ellipses.append((x, y, w / 2 + 18, h / 2 + 18))
        if label:
            self.label(x, y - h / 2 - 10, label, 13, weight="bold", color=edge)
        if sublabel:
            self.label(x, y + h / 2 + 16, sublabel, 9, italic=True, color=edge)

    # ---- houses
    def house(self, cx, cy, w, h, kind="plain", rot=0, shed=False):
        pal = {
            "plain": (random.choice(['#C6AC76', '#BEA26C', '#C2A672', '#B89A62']), '#A98C58', '#5A4326'),
            "big": ('#CFAB64', '#B08C4C', '#4E3A1E'),
            "abandoned": ('#B4AC96', '#9A917A', '#7A7058'),
        }
        light, dark, edge = pal[kind]
        ridge = '#E2CB98' if kind != "abandoned" else '#C7C0AA'
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})">']
        if shed and kind == "plain":
            g.append(f'<rect x="{x0-w*0.30:.1f}" y="{-h*0.28:.1f}" width="{w*0.32:.1f}" height="{h*0.56:.1f}" rx="2" fill="{dark}" stroke="{edge}" stroke-width="1.1"/>')
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h/2:.1f}" fill="{dark}"/>')
        g.append(f'<rect x="{x0:.1f}" y="0" width="{w}" height="{h/2:.1f}" fill="{light}"/>')
        dash = ' stroke-dasharray="5,3"' if kind == "abandoned" else ''
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="3" fill="none" stroke="{edge}" stroke-width="1.5"{dash}/>')
        g.append(f'<line x1="{-w*0.30:.1f}" y1="0" x2="{w*0.30:.1f}" y2="0" stroke="{ridge}" stroke-width="2"/>')
        if kind == "big":
            g.append(f'<rect x="{x0-1:.1f}" y="{y0-h*0.42:.1f}" width="{w*0.40:.1f}" height="{h*0.5:.1f}" rx="3" fill="{light}" stroke="{edge}" stroke-width="1.3"/>')
        if kind == "abandoned":
            g.append(f'<polygon points="{-w*0.16:.1f},{-h*0.16:.1f} {w*0.16:.1f},{-h*0.04:.1f} {-w*0.04:.1f},{h*0.2:.1f}" fill="#6E6452" opacity="0.7"/>')
        else:
            g.append(f'<rect x="-3.5" y="{h/2-2:.1f}" width="7" height="3.3" fill="{edge}" opacity="0.85"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _in_blocked(self, x, y):
        for poly in self.field_polys:
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < 14:
                return True
        for (cx, cy, rx, ry) in self.ellipses:
            if math.hypot((x - cx) / (rx + 12), (y - cy) / (ry + 12)) < 1.0:
                return True
        return False

    def _near_corridor(self, x, y, thresh=22):
        for poly in self.corridors:
            for k in range(len(poly) - 1):
                if seg_dist(x, y, poly[k], poly[k + 1]) < thresh:
                    return True
        return False

    def _fits(self, x, y, w, h):
        if x < 70 or x > self.W - 70 or y < 165 or y > self.H - 26:
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        r = math.hypot(w, h) / 2
        for (px, py, pw, ph) in self.placed:
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4:
                return False
        return True

    def try_place(self, x, y, kind, role=None):
        w, h = (60, 40) if kind == "big" else (44, 29)   # south-facing: long axis E-W
        if self._fits(x, y, w, h):
            rot = random.uniform(-5, 5)
            self.placed.append((x, y, w, h))
            self.house(x, y, w, h, kind, rot, shed=(random.random() < 0.3))
            self.M["houses"].append({"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": rot, "role": role})
            return True
        return False

    def headman(self, x, y, w=108, h=68):
        self.placed.append((x, y, w, h))
        self.house(x, y, w, h, "big", 0)
        self.M["houses"].append({"x": x, "y": y, "w": w, "h": h, "kind": "big", "rot": 0, "role": "headman"})

    def _perim_bbox(self, bbox, n, gap):
        x0, y0, x1, y1 = bbox
        bw, bh = x1 - x0, y1 - y0
        per = 2 * (bw + bh)
        pts = []
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

    def _perim_poly(self, poly, n, gap):
        area = _signed_area(poly)
        seglen = [math.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))]
        per = sum(seglen)
        pts = []
        for k in range(n):
            d = (k + random.uniform(0.2, 0.8)) / n * per
            acc = 0
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

    def ring(self, shape, n, gap, kinds, max_big=4):
        """Ring a field with houses. shape: bbox tuple, or ('poly', smoothed_outline)."""
        if isinstance(shape, tuple) and shape and shape[0] == 'poly':
            cand = self._perim_poly(shape[1], n, gap)
        else:
            cand = self._perim_bbox(shape, n, gap)
        for (x, y) in cand:
            k = random.choice(kinds)
            if k == "big":
                if self._nbig >= max_big:
                    k = "plain"
                else:
                    self._nbig += 1
            if not self.try_place(x, y, k) and k == "big":
                self._nbig -= 1

    # ---- annotation
    def _record_label(self, x, y, text, size, anchor):
        w = len(text) * size * 0.55          # rough serif advance; slightly generous so near-misses flag
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        self.M["labels"].append([round(x0, 1), round(y - size * 0.8, 1), round(x0 + w, 1), round(y + size * 0.25, 1)])

    def label(self, x, y, text, size=12, anchor="middle", italic=False, weight="normal", color="#2D2A24"):
        self._record_label(x, y, text, size, anchor)
        st = ' font-style="italic"' if italic else ''
        self.add(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
                 f'font-weight="{weight}"{st} fill="{color}" paint-order="stroke" stroke="{LAND}" stroke-width="3">{text}</text>')

    def title(self, name):
        # just the place name - no subtitle/summary; the map is self-evident
        self.add(f'<text x="{self.W/2}" y="52" text-anchor="middle" font-size="30" font-weight="bold" fill="#2D2A24">{name}</text>')

    def compass(self, x=None, y=128):
        x = x if x is not None else self.W - 72
        self.add(f'<g transform="translate({x},{y})">'
                 '<circle r="26" fill="#EFE3C2" stroke="#2D2A24" stroke-width="1.5"/>'
                 '<polygon points="0,-22 5,0 0,6 -5,0" fill="#2D2A24"/>'
                 '<polygon points="0,22 5,0 0,-6 -5,0" fill="#9C8C70"/>'
                 '<text x="0" y="-30" text-anchor="middle" font-size="12" font-weight="bold">N</text>'
                 '<text x="0" y="40" text-anchor="middle" font-size="11">S</text></g>')

    def finish(self, basepath):
        self.add('</svg>')
        with open(basepath + '.svg', 'w') as f:
            f.write('\n'.join(self.out))
        with open(basepath + '.json', 'w') as f:
            json.dump(self.M, f)
        return len(self.placed)
