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
import shutil
import subprocess
import sys

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


def seg_closest(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px, py, a, b):
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


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


def organic_bbox(bbox, amp, flat_edges=()):
    """Semi-rectangular core with lobes (outgrowths) and bays (indentations).
    Edges listed in flat_edges (0=N, 1=E, 2=S, 3=W) are kept straight - e.g. a field
    that must run flush against a town wall flattens the abutting edge."""
    x0, y0, x1, y1 = bbox
    edges = [((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)),
             ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))]
    pts = []
    for ei, (sa, sb, (nx, ny)) in enumerate(edges):
        for i in range(4):
            t = i / 4
            bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
            off = random.uniform(-amp * 0.5, amp)
            jt = random.uniform(-amp * 0.18, amp * 0.18)   # consume RNG even when flat, to keep placement aligned
            if ei in flat_edges:
                pts.append((bx, by))
                continue
            if i == 0:
                off *= 0.35
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
        self.top = []             # deferred TOP layer (labels, gate furniture) - drawn last, over roads
        self.bscale = 1.0         # urban-building footprint scale (a large town packs at a finer grain)
        self.placed = []          # (x, y, w, h)
        self.corridors = []       # polylines houses must avoid
        self.bound = None         # optional bounding polygon: placement stays inside it (city wall)
        self.field_polys = []     # smoothed outlines used for blocking
        self.ellipses = []        # (cx, cy, rx, ry) hill/pond/manor - block houses
        self.block_polys = []     # arbitrary no-build polygons (e.g. forest)
        self._clip = 0
        self._nbig = 0
        self.M = {"houses": [], "fields": [], "fallow_patches": [], "channels": [],
                  "lane": [], "taxfree": [], "torii": [], "shrines": [], "manors": [],
                  "streams": [], "buildings": [], "pastures": [], "forest_patches": [],
                  "religious": [], "flower_fields": [], "labels": [], "pond": None,
                  "storehouses": [], "flophouses": [], "hill": None, "summit": None,
                  "shrine": None, "forest": None, "road": None,
                  "wall": None, "gate": None, "gates": [], "moat": None,
                  "governor_mansion": None, "ministries": [], "inspection_stations": [],
                  "meta": {"W": W, "H": H}}
        self._header()

    # ---- low level
    # draw-order index (z): base-layer items keep their position; TOP-layer items get a
    # huge offset so they always render above the base (roads must pass UNDER them)
    TOPZ = 10_000_000

    def add(self, s):
        z = len(self.out)
        self.out.append(s)
        return z

    def add_top(self, s):
        z = self.TOPZ + len(self.top)
        self.top.append(s)
        return z

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
            z = self.add_top(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
                             f'font-weight="bold" fill="#33301E" letter-spacing="1.5" '
                             f'paint-order="stroke" stroke="{LAND}" stroke-width="3.5">{label}</text>')
            self._record_label(lx, ly, label, 15, "middle", z)

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
            return   # pragma: no cover - defensive: a real field's single cell centroid is always inside
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

    def stream(self, pts, frm=None, to=None):
        """A natural watercourse. If frm/to anchors are given (e.g. a forest brook
        feeding a pond), it is recorded and the gate checks it actually connects
        them - just like an irrigation channel."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="9" opacity="0.85"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#5C7488" stroke-width="1.2" stroke-dasharray="2,5"/>')
        # always recorded so the gate can check it (anchors optional - only some streams connect things)
        self.M["streams"].append({"poly": [[x, y] for x, y in pts], "frm": frm, "to": to})
        self.corridors.append(([(x, y) for x, y in pts], 30))   # no-build: keep houses off the stream

    def channel(self, start, end, frm, to, amp=15):
        """frm/to are anchor dicts: {'kind':'pond'|'offmap'|'field','name':...}."""
        poly = winding(start, end, amp=amp)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="4.2" opacity="0.8"/>')
        self.M["channels"].append({"poly": [[x, y] for x, y in poly], "frm": frm, "to": to})
        # 33 px keeps even a plain farmhouse's FOOTPRINT (half-diagonal ~26) clear of the
        # channel, not just its centre - 22 left corners clipping the channel (see
        # no_structure_on_channel). Matches the stream corridor's footprint-aware spacing.
        self.corridors.append((poly, 33))

    def lane(self, pts):
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="#CBB178" stroke-width="16" opacity="0.65"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6B4F2A" stroke-width="1.4" stroke-dasharray="8,8" opacity="0.7"/>')
        self.M["lane"] = [[x, y] for x, y in pts]
        self.corridors.append((pts, 22))

    def street(self, pts, width=24, label=None, main=False):
        """A town street (packed earth): the gate-to-yamen main avenue (main=True) or a
        cross lane off it. Buildings front it; a no-build corridor runs down its centre."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        z = self.add(f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width-7}" opacity="1" stroke-linejoin="round" stroke-linecap="round"/>')
        self.corridors.append((pts, width / 2 + 32))   # buildings front the street but their corners stay off the bed
        self.M.setdefault("town_streets", []).append({"main": main, "w": width, "pts": [[x, y] for x, y in pts], "z": z})
        if label:
            mid = pts[len(pts) // 2]
            self.label(mid[0] + 38, mid[1], label, 11, italic=True, color="#5A4326")

    # ---- hill + shrine + torii
    def hill(self, cx, cy, rx, ry, steep=False):
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
        if steep:
            # emphasized downslope hachures over the steep north back and upper flanks:
            # closely-spaced, longer ticks read as a steep, undefendable-on-foot slope
            n = 52
            for k in range(n + 1):
                ang = math.radians(195 + (345 - 195) * k / n)
                ex, ey = ocx + math.cos(ang) * orx, ocy + math.sin(ang) * ory
                ln = 19 + 5 * math.sin(math.radians(195 + (345 - 195) * k / n) - math.pi / 2)
                self.add(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex+math.cos(ang)*ln:.1f}" y2="{ey+math.sin(ang)*ln:.1f}" stroke="#8F7E48" stroke-width="1.0"/>')
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

    def shrine(self, x, y, w=104, h=68, kind="shrine"):
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y+h/2-8:.0f}" width="{w}" height="8" fill="#A03020"/>')
        self.add(f'<line x1="{x-w/2:.0f}" y1="{y:.0f}" x2="{x+w/2:.0f}" y2="{y:.0f}" stroke="#6B2A18" stroke-width="0.7"/>')
        self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h})

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
            return ascent[-1]   # pragma: no cover - defensive: t is capped at 0.86, never past the last segment
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

    def shrine_hall(self, x, y, label, sublabel="", w=120, h=82, torii=None, primary=False, edge="#6B2A18", kind="shrine"):
        """A standalone religious hall on flat ground. The kind follows settlement
        scale: villages have shrines, towns have monasteries, cities have temples
        (hamlets have none). primary=True marks the settlement's main one (M['shrine'],
        used by the torii checks). A torii may stand in front (torii=[(x,y),...])."""
        if torii:
            for (tx, ty) in torii:
                self.M["torii"].append([round(tx, 1), round(ty, 1)])
                bm = 32   # block the arch from placement (footprint ~38x28 + a building-half margin)
                self.block_polys.append([(tx - 19 - bm, ty - 10 - bm), (tx + 19 + bm, ty - 10 - bm),
                                         (tx + 19 + bm, ty + 18 + bm), (tx - 19 - bm, ty + 18 + bm)])
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
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "sublabel": sublabel})
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        bm = 34   # block a RECT + a building-half margin (an ellipse undershot the hall corners)
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm),
                                 (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        if label:
            self.label(x, y - h / 2 - 10, label, 13, weight="bold", color=edge)
        if sublabel:
            self.label(x, y + h / 2 + 16, sublabel, 9, italic=True, color=edge)

    # ---- landscape / estate features
    def forest(self, west_edge, label="", label_xy=None):
        """A woodland filling east of an irregular tree-line to the canvas edge.
        Blocks houses. Deterministic tree scatter (RNG saved/restored) so it never
        perturbs house placement."""
        pts = list(west_edge) + [(self.W + 12, west_edge[-1][1]), (self.W + 12, west_edge[0][1])]
        cid = self._cid('forest')
        d = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in pts) + ' Z'
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#A9B98C"/>')
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        st = random.getstate()
        random.seed(9)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 16
        while yy < max(ys):
            xx = min(xs) + 16
            while xx < max(xs):
                tx, ty = xx + random.uniform(-9, 9), yy + random.uniform(-9, 9)
                if point_in_poly(tx, ty, pts):
                    r = random.uniform(6, 9)
                    self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{r:.1f}" fill="#6E8B4C" stroke="#4E6B3C" stroke-width="0.7"/>')
                    self.add(f'<circle cx="{tx-1.5:.0f}" cy="{ty-1.5:.0f}" r="{r*0.4:.1f}" fill="#8FA968"/>')
                xx += 34
            yy += 30
        self.add('</g>')
        random.setstate(st)
        de = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in west_edge)
        self.add(f'<path d="{de}" fill="none" stroke="#4E6B3C" stroke-width="2.5"/>')
        self.block_polys.append(pts)
        self.M["forest"] = [[round(x, 1), round(y, 1)] for x, y in pts]
        if label:
            lx, ly = label_xy if label_xy else (min(xs) + (self.W - min(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 14, italic=True, weight="bold", color="#3E5631")

    def manor(self, x, y, w, h, label, sublabel="", gate_dir="west"):
        """A walled samurai compound (e.g. a magistrate's manor / hunting lodge) shown
        as a feature on a settlement map: ONLY the walls + gate + empty court. The
        interior is deliberately not drawn here - it is the subject of its own Mode A
        diagram, and drawing speculative interior buildings here would contradict it.
        gate_dir (north/south/east/west) is the wall the main gate opens through - face it
        toward whatever the compound fronts (the town, for a manor on a hill). Blocks houses."""
        x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" fill="#E7D9B4"/>')
        wall = '#2D2A24'
        sides = {"north": ((x0, y0), (x1, y0), (cx, y0), (0, -1)),
                 "south": ((x0, y1), (x1, y1), (cx, y1), (0, 1)),
                 "west": ((x0, y0), (x0, y1), (x0, cy), (-1, 0)),
                 "east": ((x1, y0), (x1, y1), (x1, cy), (1, 0))}
        gctr = sides[gate_dir][2]
        for name, (a, b, (gx, gyy), outv) in sides.items():
            if name != gate_dir:
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
            elif outv[1] == 0:   # vertical wall (west/east) - gap in y
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{a[0]:.0f}" y2="{gyy-34:.0f}" stroke="{wall}" stroke-width="6"/>')
                self.add(f'<line x1="{b[0]:.0f}" y1="{gyy+34:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                for py in (gyy - 34, gyy + 34):
                    self.add(f'<rect x="{gx-7:.0f}" y="{py-7:.0f}" width="14" height="14" fill="{wall}"/>')
            else:                # horizontal wall (north/south) - gap in x
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{gx-34:.0f}" y2="{a[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                self.add(f'<line x1="{gx+34:.0f}" y1="{b[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                for px in (gx - 34, gx + 34):
                    self.add(f'<rect x="{px-7:.0f}" y="{gyy-7:.0f}" width="14" height="14" fill="{wall}"/>')
        # interior intentionally left blank: the buildings inside (hall, stables, etc.)
        # belong to a separate Mode A diagram of the manor, not the town/settlement map
        self.M["manors"].append({"x": x, "y": y, "w": w, "h": h, "label": label,
                                 "gate": [gctr[0], gctr[1]], "gate_dir": gate_dir})
        m = 36   # block a RECT (an ellipse undershoots the wall corners) + a building-half margin
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
        if label:
            self.label(x, y0 - 12, label, 14, weight="bold")
        if sublabel:
            self.label(x, y1 + 18, sublabel, 9, italic=True)

    def road(self, pts, label=None, width=26):
        """A major road (e.g. an Imperial road) - a bordered roadbed. No-build corridor."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.M["road_z"] = self.add(f'<path d="{dd}" fill="none" stroke="#9C7A40" stroke-width="{width}" opacity="0.9"/>')         # edges
        self.add(f'<path d="{dd}" fill="none" stroke="#D8C49A" stroke-width="{width-8}" opacity="1"/>')          # roadbed
        self.add(f'<path d="{dd}" fill="none" stroke="#8A6E3E" stroke-width="1.2" stroke-dasharray="12,10" opacity="0.6"/>')
        self.corridors.append((pts, width / 2 + 32))   # wide road -> larger building setback
        self.M["road"] = [[x, y] for x, y in pts]
        self.M["road_width"] = width
        if label:
            mid = pts[len(pts) // 2]
            self.label(mid[0] + 46, mid[1] - 22, label, 12, italic=True, weight="bold", color="#5A4326")

    # urban building palette and default footprints, keyed by town caste/role
    URBAN = {
        "shop": ('#D8C49A', '#6B4F2A', 48, 32),        # merchant shophouse (modest)
        "merchant": ('#DDB87A', '#5A3F1E', 54, 36),    # merchant house+shop
        "laborer": ('#C2B190', '#6B5A3A', 34, 24),     # laborer dwelling (poorer)
        "servant": ('#CDBE9C', '#6B5A3A', 30, 22),     # servant quarters (small)
        "barn": ('#C9A57A', '#6B4F2A', 84, 56),
        "samurai": ('#DDB87A', '#5A3F1E', 56, 40),
        "civic": ('#CDB890', '#5A4326', 66, 46),
        "burakumin": ('#BCB29C', '#7A7058', 38, 26),
    }

    def building(self, cx, cy, w, h, kind="shop", rot=0):
        """An urban building (shophouse, laborer dwelling, samurai house, etc.) -
        boxier than a farmhouse, oriented to the street not the sun. Blocks placement."""
        fill, edge = self.URBAN.get(kind, self.URBAN["shop"])[:2]
        x0, y0 = -w / 2, -h / 2
        dash = ' stroke-dasharray="5,3"' if kind == "burakumin" else ''
        g = [f'<g transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f})">']
        g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="{edge}" stroke-width="1.6"{dash}/>')
        g.append(f'<line x1="{-w*0.30:.1f}" y1="0" x2="{w*0.30:.1f}" y2="0" stroke="{edge}" stroke-width="0.8" opacity="0.6"/>')
        if kind in ("shop", "merchant"):
            # a BUSINESS: a striped awning along the street frontage + a hanging sign, so
            # commerce reads as visually distinct from plain housing
            g.append(f'<rect x="{-w*0.5:.1f}" y="{h/2-6:.1f}" width="{w}" height="6.5" fill="#A8472E" opacity="0.95"/>')
            for sx in range(int(-w * 0.5) + 3, int(w * 0.5), 9):
                g.append(f'<rect x="{sx:.1f}" y="{h/2-6:.1f}" width="4.5" height="6.5" fill="#E8D2A8" opacity="0.55"/>')
            g.append(f'<rect x="-5.5" y="{h/2-2:.1f}" width="11" height="9" rx="1" fill="#E8D9A8" stroke="#6B4A22" stroke-width="0.8"/>')  # hanging sign
        else:
            g.append(f'<rect x="{-w*0.16:.1f}" y="{h/2-3:.1f}" width="{w*0.32:.1f}" height="3.2" fill="{edge}" opacity="0.8"/>')  # door
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": cx, "y": cy, "w": w, "h": h, "kind": kind, "rot": rot})
        self.placed.append((cx, cy, w, h))

    def _dims(self, kind):
        w, h = self.URBAN.get(kind, self.URBAN["shop"])[2:]
        return w * self.bscale, h * self.bscale

    def try_building(self, cx, cy, kind, rot=0):
        w, h = self._dims(kind)
        if self._fits(cx, cy, w, h):
            self.building(cx, cy, w, h, kind, rot)
            return True
        return False

    def _face_street_rot(self, x, y):
        """Rotation that turns a building's frontage toward the nearest street/road, and
        the distance to it. (None, inf) if there are no streets."""
        lines = [st["pts"] for st in self.M.get("town_streets", [])]
        if self.M.get("road"):
            lines.append(self.M["road"])
        best, bd = None, 1e18
        for sp in lines:
            for k in range(len(sp) - 1):
                cx, cy = seg_closest(x, y, sp[k], sp[k + 1])
                d = math.hypot(cx - x, cy - y)
                if d < bd:
                    bd, best = d, (cx, cy)
        if best is None:
            return None, 1e18
        dx, dy = best[0] - x, best[1] - y
        dl = math.hypot(dx, dy) or 1
        return math.degrees(math.atan2(-dx / dl, dy / dl)), bd

    def pack(self, bbox, items, rot=0, step=46, face_streets=False):
        """Densely fill a district bbox with a list of building kinds (one building
        each), grid-scan + jitter, skipping the road, blocked regions, and occupied
        spots. With face_streets, each building rotates to face its nearest street.
        Returns the number placed (leftovers are 'off-map')."""
        x0, y0, x1, y1 = bbox
        items = list(items)
        n = 0
        gy = y0 + step / 2
        while gy < y1 and items:
            gx = x0 + step / 2
            while gx < x1 and items:
                jx, jy = random.uniform(-step * 0.28, step * 0.28), random.uniform(-step * 0.28, step * 0.28)
                if face_streets:
                    fr, fd = self._face_street_rot(gx + jx, gy + jy)
                    if fr is not None and fd <= 92:
                        r = fr + random.uniform(-4, 4)          # near a street: face it
                    elif face_streets == "fill":
                        r = rot + random.uniform(-6, 6)         # deep block core (e.g. tenement housing)
                    else:
                        gx += step                              # businesses only line the frontage
                        continue
                else:
                    r = rot + random.uniform(-6, 6)
                if self.try_building(gx + jx, gy + jy, items[0], r):
                    items.pop(0)
                    n += 1
                gx += step
            gy += step
        return n

    def pasture(self, shape, label=None, amp=40, label_xy=None):
        """Hayfield / grazing land (pastureland, around the barns) - open grass with
        the odd hay bale, distinct from the cultivated paddy fields. Blocks placement."""
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            outline = organic_bbox(shape, amp)
        else:
            outline = organic_poly(shape, amp)
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('past')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#C8CF92" stroke="#9CA86A" stroke-width="2" stroke-dasharray="7,5"/>')
        xs, ys = [p[0] for p in sm], [p[1] for p in sm]
        st = random.getstate()
        random.seed(15)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 14
        while yy < max(ys):
            xx = min(xs) + 14
            while xx < max(xs):
                tx, ty = xx + random.uniform(-7, 7), yy + random.uniform(-7, 7)
                if point_in_poly(tx, ty, sm):
                    if random.random() < 0.10:
                        self.add(f'<rect x="{tx-6:.0f}" y="{ty-4:.0f}" width="12" height="8" rx="3" fill="#D8C47E" stroke="#A98E54" stroke-width="0.7"/>')
                    else:
                        self.add(f'<path d="M{tx-3:.0f},{ty+2:.0f} L{tx:.0f},{ty-4:.0f} L{tx+3:.0f},{ty+2:.0f}" fill="none" stroke="#8FA05E" stroke-width="0.8"/>')
                xx += 26
            yy += 24
        self.add('</g>')
        random.setstate(st)
        self.block_polys.append(sm)
        self.M.setdefault("pastures", []).append([[round(p[0], 1), round(p[1], 1)] for p in sm])
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 12, italic=True, color="#5C6B3A")

    def amphitheater(self, cx, cy, r, label=None):
        rr = r
        while rr > 11:
            self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rr}" ry="{rr*0.82:.0f}" fill="none" stroke="#9C8C70" stroke-width="1.5" opacity="0.85"/>')
            rr -= 13
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="10" ry="8" fill="#C9A57A" stroke="#6B4F2A" stroke-width="1.2"/>')
        self.ellipses.append((cx, cy, r + 10, r * 0.82 + 10))
        self.M["amphitheater"] = {"x": cx, "y": cy, "r": r}
        if label:
            self.label(cx, cy + r * 0.82 + 18, label, 11, italic=True)

    def granary(self, x, y, n=3, w=58, h=34, gap=14, label="granary"):
        """A short row of fireproof storehouses (kura) - the tax-rice granary of a rice-TRANSIT
        town, where grain from many counties is gathered and forwarded up the kick-up chain.
        White-walled with a dark hip roof. Opt-in (meta(granary=True)): a standard county seat
        keeps its grain inside the magistrate's yamen, so it is NOT drawn separately. Records to
        M['granary'] (gated by town_has_granary) and blocks houses, like the manor."""
        stores = []
        x0 = x - (n * w + (n - 1) * gap) / 2
        for i in range(n):
            cx = x0 + i * (w + gap) + w / 2
            self.add(f'<rect x="{cx-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="2" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="2"/>')
            self.add(f'<rect x="{cx-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="9" fill="#5A4A30"/>')   # dark fireproof hip roof
            self.add(f'<line x1="{cx:.0f}" y1="{y-h/2+9:.0f}" x2="{cx:.0f}" y2="{y+h/2:.0f}" stroke="#6B5A3C" stroke-width="0.7"/>')
            stores.append({"x": cx, "y": y, "w": w, "h": h, "rot": 0})
            bm = 30   # block a RECT + a building-half margin so dwellings keep clear, like the manor
            self.block_polys.append([(cx - w / 2 - bm, y - h / 2 - bm), (cx + w / 2 + bm, y - h / 2 - bm),
                                     (cx + w / 2 + bm, y + h / 2 + bm), (cx - w / 2 - bm, y + h / 2 + bm)])
        self.M["granary"] = {"x": x, "y": y, "n": n, "stores": stores, "label": label}
        if label:
            self.label(x, y - h / 2 - 10, label, 11, italic=True, color="#6B5A3C")
        return stores

    def merchant_storehouses(self, count=6, kw=20, kh=14):
        """Attach a small fireproof storehouse (kura) to the BACK of several merchant houses.
        Because most Rokugani farmers are TENANTS, the rent-rice and bulk goods of their (often
        absentee) landlords are kept in town - over and above the ordinary inventory storeroom a
        shop already has - so a noticeable MINORITY of businesses run a deep lot with a kura
        behind the shopfront (the classic narrow-front / deep-lot merchant compound). The kura
        is drawn as an annex behind the building (opposite its street-facing awning), like the
        farmhouse shed: part of the premises, not a separately-sited structure, so it needs no
        open ground in the packed quarter. Records to M['storehouses']; call AFTER the
        businesses are placed. Returns the number attached."""
        biz = [b for b in self.M["buildings"] if b["kind"] in ("merchant", "shop")]
        st = random.getstate()        # spread the picks across the quarter without perturbing
        random.seed(7)                # the main placement RNG (saved/restored, like forest())
        random.shuffle(biz)
        random.setstate(st)
        placed = 0
        for b in biz:
            if placed >= count:
                break
            th = math.radians(b["rot"])
            bx, by = math.sin(th), -math.cos(th)            # the building's BACK direction (awning faces -back)
            off = b["h"] / 2 + kh / 2 - 2                   # tuck the kura just behind the shopfront
            ox, oy = b["x"] + bx * off, b["y"] + by * off
            if self._near_corridor(ox, oy):                 # never let a kura sit on a street/channel
                continue
            self.add(f'<g transform="translate({ox:.0f},{oy:.0f}) rotate({b["rot"]:.0f})">'
                     f'<rect x="{-kw/2:.0f}" y="{-kh/2:.0f}" width="{kw}" height="{kh}" rx="1.5" fill="#E8E0CE" stroke="#6B5A3C" stroke-width="1.4"/>'
                     f'<rect x="{-kw/2:.0f}" y="{-kh/2:.0f}" width="{kw}" height="4.5" fill="#5A4A30"/></g>')   # dark fireproof roof
            self.M["storehouses"].append({"x": ox, "y": oy, "w": kw, "h": kh, "of": [b["x"], b["y"]]})
            placed += 1
        return placed

    def flophouse(self, x, y, w=104, h=46, label="flophouse"):
        """A large, plain communal lodging - a kichin-yado / market flophouse - where peasants
        who travel a long way to market day sleep on straw under a roof for a sen a night. It is
        BIGGER and PLAINER than a shophouse (no awning, a long dormitory of plain doorways), set
        where travelers arrive: the gate market of a walled town, the road of an unwalled one.
        Default-on for a town (town_has_flophouse); meta(flophouses=N) requires more. Records to
        M['flophouses'] and blocks houses - place it BEFORE any nearby pack/ring."""
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#CDBE96" stroke="#5A4A30" stroke-width="2"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="10" fill="#7A6038"/>')   # long roof ridge
        self.add(f'<line x1="{x0:.0f}" y1="{y:.0f}" x2="{x0+w:.0f}" y2="{y:.0f}" stroke="#5A4A30" stroke-width="0.7"/>')
        for dx in range(int(x0) + 14, int(x0 + w) - 10, 26):   # a row of plain doorways (a long dormitory)
            self.add(f'<rect x="{dx}" y="{y+h/2-7:.0f}" width="9" height="7" fill="#5A4A30" opacity="0.8"/>')
        self.M["flophouses"].append({"x": x, "y": y, "w": w, "h": h, "rot": 0, "label": label})
        self.placed.append((x, y, w, h))
        bm = 30   # block a RECT + a building-half margin so dwellings keep clear, like the manor
        self.block_polys.append([(x0 - bm, y0 - bm), (x0 + w + bm, y0 - bm),
                                 (x0 + w + bm, y0 + h + bm), (x0 - bm, y0 + h + bm)])
        if label:
            self.label(x, y0 - 10, label, 11, italic=True, color="#5A4A30")

    # ---- provincial-city features (scale="city")
    def city_wall(self, pts, gates=()):
        """A CLOSED city rampart (a full ring, unlike the town's open hill-anchored arc), with a
        gap at each gate in `gates` (each (x,y) on the ring, where the wall runs ~horizontal -
        the N and S gates the Imperial road passes through). Each gate gets a GUARD HOUSE with an
        attached INSPECTION STATION (tariff audit) and a GUARD TOWER, all in the top layer so the
        road passes under them. Records M['wall'], M['gates'], M['gate'], M['gate_structs'] (the
        guard houses + towers), and M['inspection_stations']."""
        wc = '#3A352C'
        ring = list(pts) + [pts[0]]
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in ring)
        self.add(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="11" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        self.M["gate_structs"] = []
        for gx, gy in gates:
            self.add(f'<rect x="{gx-36:.0f}" y="{gy-22:.0f}" width="72" height="44" fill="{LAND}"/>')   # gap
            self.add(f'<rect x="{gx-42:.0f}" y="{gy-26:.0f}" width="14" height="52" fill="{wc}"/>')      # posts
            self.add(f'<rect x="{gx+28:.0f}" y="{gy-26:.0f}" width="14" height="52" fill="{wc}"/>')
            dy = 1 if gy < cy else -1                          # toward the inside of the wall
            iy = gy + dy * 56
            ghx, ghw, ghh = gx - 80, 66, 44                   # guard house (just inside, west of the road)
            gz = self.add_top(f'<rect x="{ghx-ghw/2:.0f}" y="{iy-ghh/2:.0f}" width="{ghw}" height="{ghh}" rx="2" fill="#C9A57A" stroke="#5A4326" stroke-width="1.8"/>')
            self.add_top(f'<line x1="{ghx-ghw/2:.0f}" y1="{iy:.0f}" x2="{ghx+ghw/2:.0f}" y2="{iy:.0f}" stroke="#5A4326" stroke-width="0.8"/>')
            self.M["gate_structs"].append({"x": ghx, "y": iy, "w": ghw, "h": ghh, "z": gz})
            isx, isw, ish = ghx - ghw / 2 - 31, 60, 44        # inspection station, ATTACHED west of the guard house
            iz = self.add_top(f'<rect x="{isx-isw/2:.0f}" y="{iy-ish/2:.0f}" width="{isw}" height="{ish}" rx="2" fill="#D8C49A" stroke="#5A4326" stroke-width="1.8"/>')
            self.add_top(f'<rect x="{isx-isw/2:.0f}" y="{iy-ish/2:.0f}" width="{isw}" height="8" fill="#8A6E3E"/>')
            self.add_top(f'<rect x="{isx-3:.0f}" y="{iy-ish/2-13:.0f}" width="11" height="8" fill="#A8472E"/>')   # tariff banner
            self.M["inspection_stations"].append({"x": isx, "y": iy, "w": isw, "h": ish, "label": "inspection station"})
            self.M["gate_structs"].append({"x": isx, "y": iy, "w": isw, "h": ish, "z": iz})
            tx, tw = gx + 78, 40                              # guard tower on the wall, east of the gate
            tz = self.add_top(f'<rect x="{tx-tw/2:.0f}" y="{gy-tw/2:.0f}" width="{tw}" height="{tw}" fill="#9C8A66" stroke="{wc}" stroke-width="2.4"/>')
            self.add_top(f'<rect x="{tx-tw/2+8:.0f}" y="{gy-tw/2+8:.0f}" width="{tw-16}" height="{tw-16}" fill="#6B5A3A"/>')
            self.M["gate_structs"].append({"x": tx, "y": gy, "w": tw, "h": tw, "z": tz})
            self.label(isx + 14, iy + ish / 2 + 13, "gate guard house + inspection", 9, italic=True, color="#5A4326")
            for gs in self.M["gate_structs"][-3:]:
                bm = 30
                self.block_polys.append([(gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                                         (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm)])
        self.M["wall"] = [[x, y] for x, y in pts]
        self.M["gates"] = [[gx, gy] for gx, gy in gates]
        if gates:
            self.M["gate"] = [gates[0][0], gates[0][1]]
        self.corridors.append(([(x, y) for x, y in ring], 46))

    def moat(self, ring, gap=42, width=22):
        """A water moat encircling the city wall - the wall RING pushed outward from its centroid
        by `gap`. Records M['moat']. Feed it from off-map with a stream and tap it for irrigation
        channels to the outside fields. A no-build corridor."""
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        mo = []
        for x, y in ring:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) or 1.0
            mo.append((x + dx / d * gap, y + dy / d * gap))
        mo.append(mo[0])
        dd = 'M' + ' L'.join(f'{x:.0f},{y:.0f}' for x, y in mo)
        self.add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#7C98AE" stroke-width="2" opacity="0.55" stroke-linejoin="round" stroke-dasharray="3,5"/>')
        self.M["moat"] = [[round(x, 1), round(y, 1)] for x, y in mo]
        self.corridors.append(([(x, y) for x, y in mo], 28))
        return [(round(x, 1), round(y, 1)) for x, y in mo]

    def governor_mansion(self, x, y, w=320, h=210, label="Governor's Mansion", gate_dir="west"):
        """The provincial governor's walled mansion - a large compound, grander than a county
        magistrate's manor. Reuses the manor glyph (walls + gate + empty court; the interior is
        a separate Mode A diagram) and moves the record to M['governor_mansion']."""
        self.manor(x, y, w, h, label, gate_dir=gate_dir)
        self.M["governor_mansion"] = self.M["manors"].pop()   # not an outside samurai estate
        return self.M["governor_mansion"]

    def ministry(self, x, y, name, w=88, h=58):
        """A provincial ministry office (one of the SIX). Records to M['ministries'] with its
        `name`; exactly one city-wide must be the Ministry of Rites (sited in the temple
        neighbourhood). Official violet roof so it reads apart from housing/commerce."""
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="2" fill="#BCA6C4" stroke="#463653" stroke-width="2"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="9" fill="#6A4A78"/>')
        self.add(f'<line x1="{x-w*0.3:.0f}" y1="{y:.0f}" x2="{x+w*0.3:.0f}" y2="{y:.0f}" stroke="#463653" stroke-width="0.7" opacity="0.6"/>')
        self.M["ministries"].append({"x": x, "y": y, "w": w, "h": h, "name": name})
        self.placed.append((x, y, w, h))
        bm = 30
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm),
                                 (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        self.label(x, y - h / 2 - 9, name, 9, italic=True, color="#463653")

    def forest_patch(self, base, label=None, label_xy=None):
        """A bounded copse (organic polygon), as opposed to forest() which fills to
        the canvas edge. Blocks houses; deterministic tree scatter."""
        outline = organic_poly(base, 22)
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('copse')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<path d="{d}" fill="#A9B98C" stroke="#4E6B3C" stroke-width="1.5"/>')
        xs = [p[0] for p in sm]
        ys = [p[1] for p in sm]
        st = random.getstate()
        random.seed(12)
        self.add(f'<g clip-path="url(#{cid})">')
        yy = min(ys) + 12
        while yy < max(ys):
            xx = min(xs) + 12
            while xx < max(xs):
                tx, ty = xx + random.uniform(-8, 8), yy + random.uniform(-8, 8)
                if point_in_poly(tx, ty, sm):
                    rr = random.uniform(6, 9)
                    self.add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{rr:.1f}" fill="#6E8B4C" stroke="#4E6B3C" stroke-width="0.7"/>')
                    self.add(f'<circle cx="{tx-1.5:.0f}" cy="{ty-1.5:.0f}" r="{rr*0.4:.1f}" fill="#8FA968"/>')
                xx += 30
            yy += 28
        self.add('</g>')
        random.setstate(st)
        self.block_polys.append(sm)
        self.M["forest_patches"].append([[round(x, 1), round(y, 1)] for x, y in sm])
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 12, italic=True, weight="bold", color="#3E5631")

    def wall(self, pts, gate=None, label=None, guardtower=True):
        """An irregular town rampart (thick polyline; may be an open arc anchored to a
        hill). gate=(x,y): a gap with posts, a guard station, and an optional guardtower.
        Recorded so the gate can check the wall and gate exist. No-build corridor."""
        wc = '#3A352C'
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.add(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        if gate:
            gx, gy = gate
            self.add(f'<rect x="{gx-36:.0f}" y="{gy-22:.0f}" width="72" height="44" fill="{LAND}"/>')          # gap
            self.add(f'<rect x="{gx-42:.0f}" y="{gy-24:.0f}" width="14" height="48" fill="{wc}"/>')             # posts
            self.add(f'<rect x="{gx+28:.0f}" y="{gy-24:.0f}" width="14" height="48" fill="{wc}"/>')
            # the gatehouse (guard station + tower) goes in the TOP layer: a street running
            # through the gate passes UNDER it, not over it
            gz = self.add_top(f'<rect x="{gx-48:.0f}" y="{gy+26:.0f}" width="96" height="46" rx="2" fill="#C9A57A" stroke="#5A4326" stroke-width="1.6"/>')  # guard station
            self.add_top(f'<line x1="{gx-48:.0f}" y1="{gy+49:.0f}" x2="{gx+48:.0f}" y2="{gy+49:.0f}" stroke="#5A4326" stroke-width="0.8"/>')
            self.M["gate_structs"] = [{"x": gx, "y": gy + 49, "w": 96, "h": 46, "z": gz}]   # guard station
            if guardtower:
                tz = self.add_top(f'<rect x="{gx+50:.0f}" y="{gy-44:.0f}" width="40" height="40" fill="#9C8A66" stroke="{wc}" stroke-width="2.4"/>')   # guardtower
                self.add_top(f'<rect x="{gx+58:.0f}" y="{gy-36:.0f}" width="24" height="24" fill="#6B5A3A"/>')
                self.M["gate_structs"].append({"x": gx + 70, "y": gy - 24, "w": 40, "h": 40, "z": tz})
            # block the guard station / tower from placement (rect + a building-half margin)
            for gs in self.M["gate_structs"]:
                bm = 32
                self.block_polys.append([(gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                                         (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm)])
            self.M["gate"] = [gx, gy]
        self.M["wall"] = [[x, y] for x, y in pts]
        # no-build clearance kept wide enough that even a large building's CORNER (not
        # just its center) stays off the rampart stroke (half-diagonal of a 60x40 ~36)
        self.corridors.append(([(x, y) for x, y in pts], 46))
        if label:
            self.label(pts[0][0], pts[0][1] - 16, label, 12, italic=True, weight="bold", color=wc)

    def flower_field(self, shape, label=None, amp=30, label_xy=None, kind="chrysanthemum", flat_west=False):
        """An ornamental flower field (e.g. chrysanthemums - the Imperial flower).
        Organic outline like a paddy, but rows of gold blooms instead of rice.
        flat_west keeps the west edge straight so it can run flush against a town wall."""
        if len(shape) == 4 and all(isinstance(v, (int, float)) for v in shape):
            outline = organic_bbox(shape, amp, flat_edges=({3} if flat_west else ()))
        else:
            outline = organic_poly(shape, amp)
        sm = smooth_points(outline)
        d = smooth_closed(outline)
        cid = self._cid('flower')
        self.add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        self.add(f'<g clip-path="url(#{cid})">')
        self.add(f'<rect x="{min(p[0] for p in sm):.0f}" y="{min(p[1] for p in sm):.0f}" '
                 f'width="{max(p[0] for p in sm)-min(p[0] for p in sm):.0f}" height="{max(p[1] for p in sm)-min(p[1] for p in sm):.0f}" fill="#B7C089"/>')
        xs, ys = [p[0] for p in sm], [p[1] for p in sm]
        st = random.getstate()
        random.seed(17)
        yy = min(ys) + 12
        while yy < max(ys):
            xx = min(xs) + 12
            while xx < max(xs):
                fx, fy = xx + random.uniform(-4, 4), yy + random.uniform(-4, 4)
                if point_in_poly(fx, fy, sm):
                    self.add(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="3.4" fill="#E8C84C" stroke="#B89A2E" stroke-width="0.5"/>')
                    self.add(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="1.2" fill="#FBF2C4"/>')
                xx += 15
            yy += 15
        self.add('</g>')
        random.setstate(st)
        self.add(f'<path d="{d}" fill="none" stroke="#8A8A4A" stroke-width="2.5"/>')
        self.field_polys.append(sm)
        self.M["flower_fields"].append({"kind": kind, "outline": [[round(p[0], 1), round(p[1], 1)] for p in sm]})
        if label:
            lx, ly = label_xy if label_xy else ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            self.label(lx, ly, label, 11, italic=True, weight="bold", color="#7A6A1A")

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
        for poly in self.block_polys:
            if point_in_poly(x, y, poly):
                return True
        for (cx, cy, rx, ry) in self.ellipses:
            if math.hypot((x - cx) / (rx + 12), (y - cy) / (ry + 12)) < 1.0:
                return True
        return False

    def _near_corridor(self, x, y, skip=None):
        for poly, clearance in self.corridors:
            if poly is skip:          # a frontage row may sit against the street it fronts
                continue
            for k in range(len(poly) - 1):
                if seg_dist(x, y, poly[k], poly[k + 1]) < clearance:
                    return True
        return False

    def _fits(self, x, y, w, h, skip=None):
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:   # keep clear of edges + title
            return False
        if self.bound and not point_in_poly(x, y, self.bound):       # stay inside a bounding ring (city wall)
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y, skip):
            return False
        r = math.hypot(w, h) / 2
        for (px, py, pw, ph) in self.placed:
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4:
                return False
        return True

    def frontage(self, street, items, width=24, setback=10, spacing=58, both=True, rows=1, rowgap=9, jitter=4, skip=None):
        """Place buildings in row(s) along a street, each rotated so its FRONTAGE faces the
        street (shophouses lining the road). rows>1 stacks deeper rows behind the front one
        (still facing the street). Sits against the fronted street (skips that street's own
        corridor - pass skip=<registered poly> when fronting a sub-stretch of a longer
        road) but respects walls, other streets, fields, and collisions."""
        skip = skip if skip is not None else street
        items = list(items)
        seg = [math.hypot(street[i + 1][0] - street[i][0], street[i + 1][1] - street[i][1]) for i in range(len(street) - 1)]
        total = sum(seg)
        sh = width / 2

        def at(d):
            acc = 0
            for i, sl in enumerate(seg):
                if sl and acc + sl >= d:
                    f = (d - acc) / sl
                    return (street[i][0] + (street[i + 1][0] - street[i][0]) * f,
                            street[i][1] + (street[i + 1][1] - street[i][1]) * f,
                            (street[i + 1][0] - street[i][0]) / sl, (street[i + 1][1] - street[i][1]) / sl)
                acc += sl
            i = len(seg) - 1                                                            # pragma: no cover
            sl = seg[i] or 1                                                            # pragma: no cover
            return (street[-1][0], street[-1][1], (street[-1][0] - street[-2][0]) / sl,  # pragma: no cover
                    (street[-1][1] - street[-2][1]) / sl)   # defensive: while-guard keeps d < total, so a segment always matches

        placed = 0
        d = spacing * 0.55
        sides = [1, -1] if both else [1]
        while d < total and items:
            x, y, tx, ty = at(d)
            for s in sides:
                nx, ny = -ty * s, tx * s                            # outward normal (street -> building)
                base_rot = math.degrees(math.atan2(nx, -ny))        # frontage faces the street
                depth = sh + setback
                for _ in range(rows):
                    if not items:
                        break
                    kind = items[0]
                    w, h = self._dims(kind)
                    off = depth + h / 2
                    bx, by = x + nx * off, y + ny * off
                    if self._fits(bx, by, w, h, skip=skip):
                        self.building(bx, by, w, h, kind, base_rot + random.uniform(-jitter, jitter))
                        items.pop(0)
                        placed += 1
                        depth = off + h / 2 + rowgap                # next row sits behind this one
                    else:
                        break
            d += spacing
        return placed

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
    def _record_label(self, x, y, text, size, anchor, z):
        w = len(text) * size * 0.55          # rough serif advance; slightly generous so near-misses flag
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        self.M["labels"].append([round(x0, 1), round(y - size * 0.8, 1), round(x0 + w, 1), round(y + size * 0.25, 1), z])

    def label(self, x, y, text, size=12, anchor="middle", italic=False, weight="normal", color="#2D2A24"):
        esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        st = ' font-style="italic"' if italic else ''
        # labels live in the TOP layer so a road/street can never paint over them
        z = self.add_top(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
                         f'font-weight="{weight}"{st} fill="{color}" paint-order="stroke" stroke="{LAND}" stroke-width="3">{esc}</text>')
        self._record_label(x, y, text, size, anchor, z)

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

    def finish(self, basepath, render=True, png_width=2600):
        body = self.out + self.top + ['</svg>']     # TOP layer (labels, gate furniture) renders last
        with open(basepath + '.svg', 'w') as f:
            f.write('\n'.join(body))
        with open(basepath + '.json', 'w') as f:
            json.dump(self.M, f)
        if render:
            self.render_png(basepath, png_width)    # keep the .png paired with the .svg automatically
        return len(self.placed)

    def render_png(self, basepath, width=2600):
        """Rasterize basepath.svg -> basepath.png via rsvg-convert.

        Called from finish() so the PNG can never drift from the SVG: there is no way to
        regenerate a map's SVG (by hand or via the test harness, which re-runs every gen)
        without also refreshing its PNG. Settlement maps need ~2600px for the small labels.
        A no-op (with a warning) when rsvg-convert is absent - the skill cannot render at all
        without it, so that is a host-setup problem, not a generation bug."""
        exe = shutil.which('rsvg-convert')
        if not exe:   # pragma: no cover - depends on the host toolchain, not on any code path
            sys.stderr.write(f'warning: rsvg-convert not found; {basepath}.png not refreshed\n')
            return
        subprocess.run([exe, '-w', str(width), basepath + '.svg', '-o', basepath + '.png'], check=True)
