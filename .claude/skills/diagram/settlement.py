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


def segments_cross(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def seg_intersect(a, b, c, d):
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


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
        self.top = []             # deferred TOP layer (gate furniture, torii, kido) - over roads/buildings
        self.toplabels = []       # deferred LABEL layer - the very last thing drawn, so TEXT is never
        #                           covered by anything (a label must always be fully readable)
        self.walls = []           # deferred WALL layer (city rampart) - over the ground lanes + buildings,
        #                           under the TOP layer, so a street running INTO a wall passes beneath it
        self.ground = []          # deferred LINEAR ground features (alley < street < road): the wider
        self._ground_idx = None   # lane renders on top. Flushed as one ordered block (below buildings).
        self.water = []           # deferred WATERCOURSES (streams, channels, moat): all BEDS in one
        self._water_idx = None    # shared-opacity group, then all SHEENS in another, so crossings MERGE
        #                           into a continuous confluence instead of stacking opacity (a dark seam).
        self.bscale = 1.0         # urban-building footprint scale (a large town packs at a finer grain)
        self.placed = []          # (x, y, w, h)
        self.corridors = []       # polylines houses must avoid
        self.bound = None         # optional bounding polygon: placement stays inside it (city wall)
        self.view = None          # optional (ox,oy,w,h) viewBox crop - render/checks treat it as the map edge
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
                  "wells": [], "bridges": [], "threshing_yards": [], "cemeteries": [],
                  "mausoleums": [], "cremation_grounds": [], "ossuaries": [], "moat_layer": None,
                  "meta": {"W": W, "H": H}}
        self._header()

    # ---- low level
    # draw-order index (z): base-layer items keep their position; TOP-layer items get a
    # huge offset so they always render above the base (roads must pass UNDER them)
    TOPZ = 10_000_000
    LABELZ = 20_000_000      # the LABEL layer renders above even the TOP layer - text is never covered
    WALLZ = 1_000_000        # the WALL layer renders above every ground lane and building (which sit in
    #                          self.out, z < len(out)), below the TOP layer - so lanes pass UNDER walls

    def add(self, s):
        z = len(self.out)
        self.out.append(s)
        return z

    def add_wall(self, s):
        z = self.WALLZ + len(self.walls)
        self.walls.append(s)
        return z

    def add_label(self, s):
        z = self.LABELZ + len(self.toplabels)
        self.toplabels.append(s)
        return z

    def add_top(self, s):
        z = self.TOPZ + len(self.top)
        self.top.append(s)
        return z

    def _ground(self, zpri, rec, zkey, edge=None, bed=None, top=None):
        """Defer a linear ground feature (alley/street/road/ring road). The whole set renders as ONE
        block, in THREE sub-layers so crossings read as clean CROSSROADS: all EDGE strokes (the dark
        borders) at the bottom, then all BED strokes (the paved surfaces), then all TOP marks (centre
        dashes / gravel speckle). Because every edge sits below every bed, no edge line ever cuts across
        another lane's bed at a junction - the beds merge into a continuous crossroads. Within each
        sub-layer the wider lane (higher zpri = WIDTH) is on top, so the wider road still wins where two
        beds overlap (road 26 > avenue 22 > street 18 > alley 10). Each feature records its BED's final
        draw position (rec[zkey]) for the width-layering check."""
        if self._ground_idx is None:
            self._ground_idx = len(self.out)
            self.out.append("")          # placeholder, replaced by the sorted block at finish()
        self.ground.append({"zpri": zpri, "seq": len(self.ground), "edge": edge, "bed": bed, "top": top, "rec": rec, "zkey": zkey})

    def _water(self, bed, rec, sheen=None):
        """Defer a watercourse (stream / channel / moat) so the whole set renders as ONE block, in TWO
        sub-layers: all BEDS (the blue water bodies, same colour) inside one shared-opacity group, then
        all SHEENS (the lighter mid-current highlights) inside another above it. The shared group opacity
        means overlapping water does NOT stack opacity into a dark seam where two courses cross - the beds
        composite into a single continuous body (a confluence), exactly as the ground beds merge into a
        clean crossroads. Each course records its bed's / sheen's draw position on `rec` (bedz / sheenz)
        for waterways_merge_at_crossings. Spliced at the FIRST water call's position, so later fields still
        paint over a channel's end."""
        if self._water_idx is None:
            self._water_idx = len(self.out)
            self.out.append("")          # placeholder, replaced by the two-group block at finish()
        self.water.append({"bed": bed, "sheen": sheen, "rec": rec})

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

    def set_view(self, ox, oy, w, h):
        """Crop the rendered map to (ox,oy,w,h) instead of the full canvas. Placement still uses
        the full coordinate space, so off-view features (estates, farmland) simply run off the
        edge. The checks read meta['view'] and treat this crop - not the canvas - as the map edge.
        Used for city maps, which 'just barely encompass' the walled city and let the countryside
        run off the edge (a city map is about the city; a town map is about its surroundings)."""
        self.view = (ox, oy, w, h)
        self.M["meta"]["view"] = [ox, oy, w, h]

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
            z = self.add_label(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="15" '
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
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#9CB4C8" stroke="#5C7488" stroke-width="2.4"/>')
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx-12}" ry="{ry-10}" fill="none" stroke="#B6CAD8" stroke-width="1" opacity="0.7"/>')
        self.M["pond"] = [cx, cy, rx, ry]
        self.ellipses.append((cx, cy, rx, ry))

    def stream(self, pts, frm=None, to=None, width=9):
        """A natural watercourse. If frm/to anchors are given (e.g. a forest brook
        feeding a pond), it is recorded and the gate checks it actually connects
        them - just like an irrigation channel. `width` is the water's drawn width
        (a stream FEEDING A MOAT should be as wide as the moat, by conservation of flow)."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        # always recorded so the gate can check it (anchors optional - only some streams connect things)
        rec = {"poly": [[x, y] for x, y in pts], "frm": frm, "to": to, "w": width}
        self.M["streams"].append(rec)
        self._water(   # opacity comes from the shared bed/sheen groups, so crossings don't stack into a dark seam
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            rec,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{max(2, width*0.35):.0f}" stroke-linejoin="round" stroke-linecap="round"/>')   # lighter mid-current highlight (NOT a dashed lane line - this is water, not a road)
        self.corridors.append(([(x, y) for x, y in pts], max(30, width / 2 + 20)))   # no-build: keep houses off the stream

    def channel(self, start, end, frm, to, amp=15):
        """frm/to are anchor dicts: {'kind':'pond'|'offmap'|'field','name':...}."""
        poly = winding(start, end, amp=amp)
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
        rec = {"poly": [[x, y] for x, y in poly], "frm": frm, "to": to}
        self.M["channels"].append(rec)
        self._water(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="4.2"/>', rec)   # a channel is a thin bed, no sheen
        # 33 px keeps even a plain farmhouse's FOOTPRINT (half-diagonal ~26) clear of the
        # channel, not just its center - 22 left corners clipping the channel (see
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
        cross lane off it. Buildings front it; a no-build corridor runs down its center."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + 32))   # buildings front the street but their corners stay off the bed
        st = {"main": main, "w": width, "pts": [[x, y] for x, y in pts], "z": None}
        self.M.setdefault("town_streets", []).append(st)
        self._ground(width, st, "z",
                     edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>',
                     bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width-7}" opacity="1" stroke-linejoin="round" stroke-linecap="round"/>')
        if label:
            mid = pts[len(pts) // 2]
            self.label(mid[0] + 38, mid[1], label, 11, italic=True, color="#5A4326")

    def kido(self, x, y, horizontal=True, sw=18):
        """A kido - a wooden WARD GATE barring a street at a quarter boundary, manned and shut at
        night to keep the samurai quarter apart from the commoners. A small city seals its wards
        with GATES, not internal ramparts (the walled-ward / fang system was a great-capital, Tang-
        era thing). Drawn OVER the street (a roofed gateway + posts + a guard box); records M['kido'].
        horizontal=True for an E-W street (gate bars N-S), False for an N-S street."""
        hw = sw / 2 + 5
        if horizontal:                                  # street runs E-W; the gateway spans N-S
            roof = (x - 7, y - hw, 14, 2 * hw)
            posts = [(x - 8, y - hw - 1, 16, 4), (x - 8, y + hw - 3, 16, 4)]
            guard = (x + 12, y - hw - 13, 16, 15)
        else:                                           # street runs N-S; the gateway spans E-W
            roof = (x - hw, y - 7, 2 * hw, 14)
            posts = [(x - hw - 1, y - 8, 4, 16), (x + hw - 3, y - 8, 4, 16)]
            guard = (x - hw - 13, y + 12, 15, 16)
        g = ['<g>', f'<rect x="{roof[0]:.0f}" y="{roof[1]:.0f}" width="{roof[2]:.0f}" height="{roof[3]:.0f}" rx="1.5" '
             'fill="#8A6E3E" stroke="#3F3018" stroke-width="1.5"/>']
        for px, py, pw, ph in posts:
            g.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw}" height="{ph}" fill="#3F3018"/>')
        g.append(f'<rect x="{guard[0]:.0f}" y="{guard[1]:.0f}" width="{guard[2]}" height="{guard[3]}" rx="1" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        rects = [roof] + posts + [guard]                # the gate's full drawn footprint (for the labels-on-top check)
        bbox = [min(r[0] for r in rects), min(r[1] for r in rects),
                max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects)]
        self.M.setdefault("kido", []).append({"x": round(x, 1), "y": round(y, 1), "horizontal": horizontal, "z": z, "bbox": bbox})

    def ward(self, name, boundary, gates):
        """An internal WARD boundary - a light earthwork/palisade fence (NOT a city rampart) that
        SEALS a quarter (the samurai/government ward) off the commoner streets, so its kido gates
        cannot simply be walked around: the fence is continuous between the gates, its ends abut
        the city wall, and a street may pierce it ONLY at a gate. `boundary` is the fence polyline;
        `gates` are (x, y, horizontal) kido where a street crosses it. Records M['wards']."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in boundary)
        fz = self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="5" opacity="0.9" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')   # palisade
        self.corridors.append((boundary, 11))   # buildings keep off the fence line
        # the fence ends ABUT the city wall: lay a short wall-stroke CAP over each end so the rampart
        # renders ON TOP of the fence there (the fence runs UNDER the wall), not the fence over the wall.
        caps = []
        wall = self.M.get("wall")
        if wall:
            ring = list(wall) + [wall[0]]
            for ex, ey in (boundary[0], boundary[-1]):
                best = None
                for i in range(len(ring) - 1):
                    cx, cy = seg_closest(ex, ey, ring[i], ring[i + 1])
                    d = math.hypot(cx - ex, cy - ey)
                    if best is None or d < best[0]:
                        best = (d, (cx, cy), (ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]))
                if best and best[0] < 24:                  # the end abuts the wall - cap it
                    (px, py), (tx, ty) = best[1], best[2]
                    tl = math.hypot(tx, ty) or 1
                    ux, uy = tx / tl * 16, ty / tl * 16
                    cz = self.add(f'<path d="M{px-ux:.0f},{py-uy:.0f} L{px+ux:.0f},{py+uy:.0f}" fill="none" stroke="#3A352C" stroke-width="11" stroke-linecap="round"/>')
                    caps.append({"x": round(px, 1), "y": round(py, 1), "z": cz})
        self.M.setdefault("wards", []).append({"name": name, "boundary": [[round(x, 1), round(y, 1)] for x, y in boundary], "z": fz, "wall_caps": caps})
        for gx, gy, horiz in gates:
            self.kido(gx, gy, horizontal=horiz)

    def alley(self, pts, width=10):
        """An UNPAVED interior lane (gravel / wood planks, not the dressed earth of a street) that
        threads the packed block cores: the poor reach their jammed interior housing by alleys,
        not the paved street frontage. Thinner than a street, drawn as a pale gravel path with a
        plank/speckle dash, and a NARROW no-build corridor so the dense core leaves a gap for it."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + 11))   # setback keeps building CORNERS off the lane, not just centers
        al = {"pts": [[x, y] for x, y in pts], "w": width, "z": None}
        self.M.setdefault("alleys", []).append(al)
        self._ground(width, al, "z",   # an unpaved gravel lane: its surface IS the bed (no kerb/edge), plus a speckle
                     bed=f'<path d="{dd}" fill="none" stroke="#C7BB9C" stroke-width="{width}" opacity="0.85" stroke-linejoin="round" stroke-linecap="round"/>',
                     top=f'<path d="{dd}" fill="none" stroke="#9A8A68" stroke-width="1.4" stroke-dasharray="2,5" opacity="0.7"/>')

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

    def small_shrine(self, x, y, w=32, h=24):
        """A small wayside / neighborhood Shinto SHRINE - a vermilion-roofed shed with a little torii
        in front, the kind that dot a temple neighborhood. Non-residential: recorded in M['religious']
        as kind 'small_shrine' (so it is not housing and not a full temple - it needs no torii avenue
        and is not counted as a dwelling). Placed early so the dense packs flow around it."""
        x0, y0 = x - w / 2, y - h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" rx="2" fill="#C9876C" stroke="#6B2A18" stroke-width="1.4"/>')
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="5" fill="#A03020"/>')   # vermilion roof ridge
        ty = y + h / 2 + 8                                          # a little torii just in front (south)
        self.add(f'<g transform="translate({x:.0f},{ty:.0f})"><line x1="-7" y1="0" x2="7" y2="0" stroke="#A03020" stroke-width="2"/>'
                 f'<line x1="-8" y1="-4" x2="8" y2="-4" stroke="#A03020" stroke-width="1.6"/>'
                 f'<line x1="-5" y1="-4" x2="-5" y2="6" stroke="#A03020" stroke-width="1.6"/>'
                 f'<line x1="5" y1="-4" x2="5" y2="6" stroke="#A03020" stroke-width="1.6"/></g>')
        self.M["religious"].append({"kind": "small_shrine", "x": x, "y": y, "w": w, "h": h, "rot": 0})
        self.placed.append((x, y, w, h))
        bm = 16
        self.block_polys.append([(x0 - bm, y0 - bm), (x + w / 2 + bm, y0 - bm), (x + w / 2 + bm, y + h / 2 + bm + 16), (x0 - bm, y + h / 2 + bm + 16)])

    def well(self, x, y, r=8):
        """A public NEIGHBOURHOOD WELL (井戸) - a stone curb under an open-sided well-house roof, the
        shared draw-point and social hub (the idobata, where a tenement block's gossip happened). One
        served a courtyard / cluster of ~10-20 households. SMALLER than a house and sits in a block
        INTERIOR off the lanes. Records M['wells'] and blocks placement so the quarter's houses flow
        around it - place BEFORE the quarter's pack. The underground end of a city's water system
        (aqueducts, cisterns, rain barrels feeding the shaft) stays off the map; only the head shows."""
        # the DRAWN wellhead SCALES WITH THE MAP GRAIN (bscale), exactly as the buildings do, so it keeps
        # a consistent ~0.55x a dwelling at every scale - fixed pixels would make it look right in the
        # dense city but far too small beside a village/town's larger houses. It stays SMALLER than a
        # house (a wellhead is small) regardless of the larger COURTYARD footprint reserved for placement.
        vroof, vcurb = 11.9 * self.bscale, 9.0 * self.bscale
        self.add(f'<rect x="{x-vroof:.1f}" y="{y-vroof:.1f}" width="{2*vroof:.1f}" height="{2*vroof:.1f}" rx="1.5" '
                 f'fill="#C7B084" stroke="#6B5836" stroke-width="1.1" opacity="0.55"/>')   # the well-house roof, light so the curb reads through
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb:.1f}" fill="#9AA1A4" stroke="#43403A" stroke-width="1.1"/>')   # stone curb
        self.add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{vcurb*0.47:.1f}" fill="#2E4C58"/>')   # dark water in the shaft
        self.M["wells"].append({"x": round(x, 1), "y": round(y, 1), "r": r, "vr": round(vroof, 1)})
        # reserve only a TIGHT courtyard around the small wellhead (not a whole house-plot): houses ring
        # it closely, as in a real tenement court, so a well costs roughly its own footprint, not several
        # dwellings. (`r` stays the recorded clearance radius the checks use; the reserved block is small.)
        self.placed.append((x, y, 2 * vroof, 2 * vroof))
        bm = 8
        self.block_polys.append([(x - vroof - bm, y - vroof - bm), (x + vroof + bm, y - vroof - bm),
                                 (x + vroof + bm, y + vroof + bm), (x - vroof - bm, y + vroof + bm)])

    def well_at(self, x, y, r=8):
        """Place ONE well at (x, y), but only if the spot is clear (a block interior off lanes,
        compounds, the bound, and other placed things - the same `_fits` test place_wells uses).
        Returns True if it placed. For hand-seeding wells into cramped, lane-laced quarters the grid
        scatter can't reach - pass a generous candidate list and the blocked ones simply no-op."""
        if self._fits(x, y, 2 * r + 14, 2 * r + 14):
            self.well(x, y, r)
            return True
        return False

    def place_wells(self, bbox, spacing, r=8, near=None):
        """Scatter neighbourhood wells across a residential bbox on a grid at ~`spacing` px, keeping
        each in a block INTERIOR: a candidate is dropped if it falls on a lane corridor, outside the
        city bound, on an existing compound (temple/estate/pond), or too near another well (all via
        `_fits`). For each grid cell the cell centre is tried first, then a few small offsets, so a
        cell still gets a well when its exact centre happens to land on a lane or compound - this keeps
        coverage even in the lane-laced warren. One well per ~spacing px serves the courtyards around
        it. Call BEFORE the quarter's house pack so the houses flow around the wells. Returns the
        placed (x, y) list."""
        x0, y0, x1, y1 = bbox
        probe = 2 * r + 14   # a modest footprint => wells sit in the courtyards, not crammed on a lane
        d = spacing * 0.26
        offsets = [(0, 0), (d, d), (-d, -d), (d, -d), (-d, d)]
        # `near`: only place a well that has a DWELLING within `near` px - a well serves the households
        # around it, so it must sit AMONG the buildings, never out in open countryside. Pass it when the
        # houses are already placed (the rural tiers: place_wells runs AFTER the field rings); a city's
        # pack runs after place_wells and fills in around the wells, so the city omits it.
        dwell = self.M.get("buildings", []) + self.M.get("houses", []) if near is not None else None
        out = []
        yy = y0 + spacing / 2
        while yy <= y1:
            xx = x0 + spacing / 2
            while xx <= x1:
                for ox, oy in offsets:
                    cx, cy = xx + ox, yy + oy
                    if self._fits(cx, cy, probe, probe) and (dwell is None
                            or any((b["x"] - cx) ** 2 + (b["y"] - cy) ** 2 < near * near for b in dwell)):
                        self.well(cx, cy, r)
                        out.append((cx, cy))
                        break
                xx += spacing
            yy += spacing
        return out

    def torii_path(self, ascent):
        """Place one torii at each interior vertex of the ascent polyline; draw the
        winding path. Count is village-specific - pass as many points as torii+ends."""
        dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in ascent)
        self.add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
        self.add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
        for (tx, ty) in ascent[1:-1]:
            tz = self.add_top(f'<g transform="translate({tx:.0f},{ty:.0f})">'              # over any street it crosses
                              f'<line x1="-16" y1="0" x2="16" y2="0" stroke="#A03020" stroke-width="3.6"/>'
                              f'<line x1="-19" y1="-7" x2="19" y2="-7" stroke="#A03020" stroke-width="3"/>'
                              f'<line x1="-12" y1="-7" x2="-12" y2="17" stroke="#A03020" stroke-width="3"/>'
                              f'<line x1="12" y1="-7" x2="12" y2="17" stroke="#A03020" stroke-width="3"/></g>')
            self.M["torii"].append([round(tx, 1), round(ty, 1), tz])

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
            tz = self.add_top(f'<g transform="translate({tx:.0f},{ty:.0f})">'              # over any street it crosses
                              f'<line x1="-16" y1="0" x2="16" y2="0" stroke="#A03020" stroke-width="3.6"/>'
                              f'<line x1="-19" y1="-7" x2="19" y2="-7" stroke="#A03020" stroke-width="3"/>'
                              f'<line x1="-12" y1="-7" x2="-12" y2="17" stroke="#A03020" stroke-width="3"/>'
                              f'<line x1="12" y1="-7" x2="12" y2="17" stroke="#A03020" stroke-width="3"/></g>')
            self.M["torii"].append([round(tx, 1), round(ty, 1), tz])

    def shrine_hall(self, x, y, label, sublabel="", w=120, h=82, torii=None, primary=False, edge="#6B2A18", kind="shrine", graveyard=True, label_below=False):
        """A standalone religious hall on flat ground. The kind follows settlement
        scale: villages have shrines, towns have monasteries, cities have temples
        (hamlets have none). primary=True marks the settlement's main one (M['shrine'],
        used by the torii checks). A torii may stand in front (torii=[(x,y),...]).
        graveyard=False marks a temple that hosts NO burial ground (a new or special-purpose
        hall, e.g. one founded in a former samurai estate) - city_temples_have_graveyards
        then exempts it; every other temple is expected to have a graveyard in its precinct."""
        if torii:
            for (tx, ty) in torii:
                bm = 20   # block just the arch (footprint ~38x28 + a building-half margin) - kept SMALLER than a
                #           street corridor so torii on a street don't shove the frontage houses further off it
                self.block_polys.append([(tx - 19 - bm, ty - 10 - bm), (tx + 19 + bm, ty - 10 - bm),
                                         (tx + 19 + bm, ty + 18 + bm), (tx - 19 - bm, ty + 18 + bm)])
                tz = self.add_top(f'<g transform="translate({tx:.0f},{ty:.0f})">'           # over any street it crosses
                                  f'<line x1="-15" y1="0" x2="15" y2="0" stroke="#A03020" stroke-width="3.4"/>'
                                  f'<line x1="-18" y1="-7" x2="18" y2="-7" stroke="#A03020" stroke-width="2.8"/>'
                                  f'<line x1="-11" y1="-7" x2="-11" y2="16" stroke="#A03020" stroke-width="2.8"/>'
                                  f'<line x1="11" y1="-7" x2="11" y2="16" stroke="#A03020" stroke-width="2.8"/></g>')
                self.M["torii"].append([round(tx, 1), round(ty, 1), tz])
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="{h}" rx="3" fill="#C9876C" stroke="{edge}" stroke-width="2"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y-h/2:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<rect x="{x-w/2:.0f}" y="{y+h/2-9:.0f}" width="{w}" height="9" fill="#A03020"/>')
        self.add(f'<line x1="{x-w/2:.0f}" y1="{y:.0f}" x2="{x+w/2:.0f}" y2="{y:.0f}" stroke="{edge}" stroke-width="0.7"/>')
        self.M["shrines"].append({"x": x, "y": y, "w": w, "h": h, "label": label})
        self.M["religious"].append({"kind": kind, "x": x, "y": y, "w": w, "h": h, "label": label, "sublabel": sublabel, "graveyard": graveyard})
        if primary:
            self.M["shrine"] = [x - w / 2, y - h / 2, w, h]
        bm = 34   # block a RECT + a building-half margin (an ellipse undershot the hall corners)
        self.block_polys.append([(x - w / 2 - bm, y - h / 2 - bm), (x + w / 2 + bm, y - h / 2 - bm),
                                 (x + w / 2 + bm, y + h / 2 + bm), (x - w / 2 - bm, y + h / 2 + bm)])
        if label:
            self.label(x, y + h / 2 + 22 if label_below else y - h / 2 - 10, label, 13, weight="bold", color=edge)
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

    def manor(self, x, y, w, h, label, sublabel="", gate_dir="south", rot=0):
        """A walled samurai compound (e.g. a magistrate's manor / hunting lodge) shown
        as a feature on a settlement map: ONLY the walls + gate + empty court. The
        interior is deliberately not drawn here - it is the subject of its own Mode A
        diagram, and drawing speculative interior buildings here would contradict it.
        gate_dir (north/south/east/west) is the wall the main gate opens through - face it
        toward whatever the compound fronts (the town / road it sits at the edge of). There
        is no universal default direction (it depends where the town is), but SOUTH is the
        auspicious/formal fallback. `rot` TILTS the whole compound (degrees) so it can parallel
        a diagonal road or river it fronts. Blocks houses."""
        hw, hh = w / 2, h / 2
        wall = '#2D2A24'
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)

        def absol(px, py):                 # a compound-local point -> absolute map coords (after tilt)
            return (x + px * ca - py * sa, y + px * sa + py * ca)
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
             f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="{h}" fill="#E7D9B4"/>']
        sides = {"north": ((-hw, -hh), (hw, -hh), (0, -hh), (0, -1)),
                 "south": ((-hw, hh), (hw, hh), (0, hh), (0, 1)),
                 "west": ((-hw, -hh), (-hw, hh), (-hw, 0), (-1, 0)),
                 "east": ((hw, -hh), (hw, hh), (hw, 0), (1, 0))}
        gcl = sides[gate_dir][2]
        for name, (pa, pb, (gx, gy), outv) in sides.items():
            if name != gate_dir:
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
            elif outv[1] == 0:   # vertical wall (west/east) - gap in y
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{pa[0]:.0f}" y2="{gy-34:.0f}" stroke="{wall}" stroke-width="6"/>')
                g.append(f'<line x1="{pb[0]:.0f}" y1="{gy+34:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                for py in (gy - 34, gy + 34):
                    g.append(f'<rect x="{gx-7:.0f}" y="{py-7:.0f}" width="14" height="14" fill="{wall}"/>')
            else:                # horizontal wall (north/south) - gap in x
                g.append(f'<line x1="{pa[0]:.0f}" y1="{pa[1]:.0f}" x2="{gx-34:.0f}" y2="{pa[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                g.append(f'<line x1="{gx+34:.0f}" y1="{pb[1]:.0f}" x2="{pb[0]:.0f}" y2="{pb[1]:.0f}" stroke="{wall}" stroke-width="6"/>')
                for px in (gx - 34, gx + 34):
                    g.append(f'<rect x="{px-7:.0f}" y="{gy-7:.0f}" width="14" height="14" fill="{wall}"/>')
        g.append('</g>')
        self.add(''.join(g))
        # interior intentionally left blank: the buildings inside (hall, stables, etc.)
        # belong to a separate Mode A diagram of the manor, not the town/settlement map
        gctr = absol(*gcl)
        corners = [absol(-hw, -hh), absol(hw, -hh), absol(hw, hh), absol(-hw, hh)]
        # an axis-aligned manor whose wall abuts a neighborhood (ward) fence yields that wall to the
        # fence (re-stamped on top), exactly like the mausoleum; tilted manors are left untouched
        ward_walls = []
        if rot == 0:
            msides = {"north": ((x - hw, y - hh), (x + hw, y - hh)), "south": ((x - hw, y + hh), (x + hw, y + hh)),
                      "west": ((x - hw, y - hh), (x - hw, y + hh)), "east": ((x + hw, y - hh), (x + hw, y + hh))}
            ward_walls = [name for name, (a, b) in msides.items()
                          if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        self.M["manors"].append({"x": x, "y": y, "w": w, "h": h, "rot": rot, "label": label,
                                 "gate": [round(gctr[0], 1), round(gctr[1], 1)], "gate_dir": gate_dir, "ward_walls": ward_walls})
        m = 36   # block the (tilted) RECT + a building-half margin so houses keep clear of the walls
        blk = [absol(-hw - m, -hh - m), absol(hw + m, -hh - m), absol(hw + m, hh + m), absol(-hw - m, hh + m)]
        self.block_polys.append([(round(px, 1), round(py, 1)) for px, py in blk])
        ys = [c[1] for c in corners]
        if label:
            self.label(x, min(ys) - 12, label, 14, weight="bold")
        if sublabel:
            self.label(x, max(ys) + 18, sublabel, 9, italic=True)

    def merchant_estate(self, x, y, w=78, h=58, gate_dir="south"):
        """A walled merchant compound - a VERY-rich merchant's estate within the merchant quarter: a
        light perimeter wall around a court with the merchant's large house inside (one large dwelling).
        Recorded in M['merchant_estates'] (NOT M['manors'], which are the samurai country estates
        outside the wall). The inner house is a normal merchant_large building, so it counts as housing.
        gate_dir is the side the courtyard gate opens through - it is fine for the walls to ABUT a
        neighbouring building, but point the GATE at open ground, never into another building."""
        x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#EAD9B0" stroke="#5A4326" stroke-width="3.5"/>')   # walled court
        # the gate gap (erases a slot of the wall stroke on the chosen side); gate point on that edge
        gates = {"south": (x, y1, 24, 6), "north": (x, y0, 24, 6), "east": (x1, y, 6, 24), "west": (x0, y, 6, 24)}
        gx, gy, gw, gh = gates[gate_dir]
        self.add(f'<rect x="{gx-gw/2:.0f}" y="{gy-gh/2:.0f}" width="{gw}" height="{gh}" fill="#EAD9B0"/>')
        self.building(x, y - 2, *self._dims("merchant_large"), "merchant_large")   # the large house inside the court
        self.M.setdefault("merchant_estates", []).append({"x": round(x, 1), "y": round(y, 1), "w": w, "h": h,
                                                          "gate": [round(gx, 1), round(gy, 1)], "gate_dir": gate_dir})
        m = 18
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])

    def road(self, pts, label=None, width=26, label_xy=None):
        """A major road (e.g. an Imperial road) - a bordered roadbed. No-build corridor.
        label_xy overrides the label anchor (default: the polyline midpoint). For a city the
        midpoint is the city CENTER, but the road label names the *Imperial* road, which is an
        Imperial responsibility only OUTSIDE the walls - inside, the same roadway is a city
        street the city maintains - so a city must pass label_xy a point beyond the gates."""
        dd = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.corridors.append((pts, width / 2 + 32))   # wide road -> larger building setback
        self.M["road"] = [[x, y] for x, y in pts]
        self.M["road_width"] = width
        self.M["road_z"] = None
        self._ground(width, self.M, "road_z",
                     edge=f'<path d="{dd}" fill="none" stroke="#9C7A40" stroke-width="{width}" opacity="0.9"/>',
                     bed=f'<path d="{dd}" fill="none" stroke="#D8C49A" stroke-width="{width-8}" opacity="1"/>',
                     top=f'<path d="{dd}" fill="none" stroke="#8A6E3E" stroke-width="1.2" stroke-dasharray="12,10" opacity="0.6"/>')
        if label:
            mid = pts[len(pts) // 2]
            lx, ly = label_xy if label_xy else (mid[0] + 46, mid[1] - 22)
            self.label(lx, ly, label, 12, italic=True, weight="bold", color="#5A4326")
            self.M["road_label"] = [lx, ly]

    # urban building palette and default footprints, keyed by town caste/role
    URBAN = {
        "shop": ('#D8C49A', '#6B4F2A', 48, 32),        # merchant shophouse (modest)
        "merchant": ('#DDB87A', '#5A3F1E', 54, 36),    # merchant house+shop (the storefront, fronts the street)
        "merchant_house": ('#DDB87A', '#5A3F1E', 50, 34),   # a small/average merchant home (behind the storefront)
        "merchant_large": ('#E2BE7E', '#5A3F1E', 86, 60),   # a rich merchant's large home
        "laborer": ('#C2B190', '#6B5A3A', 34, 24),     # laborer dwelling (the standard ~87% - poorer hinin)
        "laborer_large": ('#CBB684', '#6B5A3A', 50, 34),   # a 'master' (rich) laborer's larger home (~12.5% of laborers, budgets.md) - the wealthier hinin who line the back streets
        "servant": ('#CDBE9C', '#6B5A3A', 30, 22),     # servant quarters (small)
        "barn": ('#C9A57A', '#6B4F2A', 84, 56),
        "samurai": ('#DDB87A', '#5A3F1E', 56, 40),         # a junior samurai's small city house (most of the neighborhood)
        "samurai_large": ('#E0BC80', '#5A3F1E', 82, 58),   # a senior samurai's large city house (a minority; walled estates are OUTSIDE the walls)
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
                    if face_streets == "core":
                        if fr is not None and fd <= 76:
                            gx += step                          # leave the street-facing band for shop frontage; dwellings pack the INTERIOR
                            continue
                        r = rot + random.uniform(-6, 6)         # ONLY the deep block core, set back behind the frontage line
                    elif fr is not None and fd <= 92:
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

    def _draw_threshing_yard(self, cx, cy, w, h):
        """Draw one small tamped earthen threshing/drying yard (a straw mat + a little hazakake rack)."""
        x0, y0 = -w / 2, -h / 2
        g = [f'<g transform="translate({cx:.0f},{cy:.0f})">']
        g.append(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" rx="2" fill="#D2BE94" stroke="#A98E54" stroke-width="1.5"/>')   # tamped earthen floor
        g.append(f'<rect x="{x0+3:.0f}" y="{y0+3:.0f}" width="{w-6:.0f}" height="{h-6:.0f}" rx="1.5" fill="none" stroke="#BBA06E" stroke-width="0.7" opacity="0.6"/>')   # swept rim
        g.append('<rect x="-7" y="-6" width="14" height="9" rx="1" fill="#E2D2A2" stroke="#A98E54" stroke-width="0.6" opacity="0.9"/>')   # a straw drying mat
        ry = h / 2 - 3                                        # a little drying rack (hazakake) along the floor's lower edge
        g.append(f'<line x1="{x0+4:.1f}" y1="{ry:.1f}" x2="{-x0-4:.1f}" y2="{ry:.1f}" stroke="#7A5A30" stroke-width="1.2"/>')
        g.append(f'<line x1="{x0+4:.1f}" y1="{ry-3:.1f}" x2="{-x0-4:.1f}" y2="{ry-3:.1f}" stroke="#7A5A30" stroke-width="1.0"/>')
        for px in (x0 + 4, 0.0, -x0 - 4):                    # posts + a few hung sheaves
            g.append(f'<line x1="{px:.1f}" y1="{ry-5:.1f}" x2="{px:.1f}" y2="{ry+3:.1f}" stroke="#5A3F1E" stroke-width="1.2"/>')
        g.append('</g>')
        self.add(''.join(g))

    def _yard_fits(self, x, y, w, h, hx, hy):
        """A threshing yard fits where it is in-bounds, on DRY ground (clear of paddies / blocks),
        off any lane, and clear of every placed footprint EXCEPT its own farmhouse (it abuts that)."""
        if x < 55 or x > self.W - 55 or y < 88 or y > self.H - 26:
            return False
        if self.bound and not point_in_poly(x, y, self.bound):
            return False
        if self._in_blocked(x, y) or self._near_corridor(x, y):
            return False
        r = math.hypot(w, h) / 2
        for poly in self.field_polys:                        # keep the whole DRY footprint out of every paddy
            if point_in_poly(x, y, poly) or edge_dist(x, y, poly) < r + 4:
                return False
        for (px, py, pw, ph) in self.placed:
            if px == hx and py == hy:                        # the yard abuts its OWN farmhouse - allowed
                continue
            if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 2:
                return False
        return True

    def threshing_yards(self, fraction=1 / 3, yw=36, yh=22):
        """Attach a small earthen THRESHING / DRYING YARD (the farmstead niwa) plus a little drying rack
        to a MINORITY (~`fraction`, default ~1/3) of farmhouses - the per-household harvest processing
        that replaces the single communal hiroba: each family threshes and dries its cut rice on its own
        tamped dry yard beside the house. Drawn AFTER the houses with a saved/restored RNG (perturbs no
        seeded placement); each yard tucks against its farmhouse on the side AWAY from the nearest paddy
        (dry ground), and a house is SKIPPED when that spot is not clear (in the water, on a lane, or
        against a neighbour) - the kura pattern, which self-selects the outer-ring farmsteads with open
        room. Independent of the ~30% that carry a shed, so a farmhouse may have neither, either, or both.
        Records M['threshing_yards'] (an annex abutting its own house, hence overlap-exempt against it).
        Returns the number attached."""
        homes = [h for h in self.M["houses"] if h.get("kind") == "plain"]
        if not homes:
            return 0
        target = math.ceil(len(self.M["houses"]) * fraction)
        cents = [(sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
                 for poly in self.field_polys]
        st = random.getstate()        # spread the picks without perturbing the main placement RNG
        random.seed(11)
        random.shuffle(homes)
        random.setstate(st)
        placed = 0
        for h in homes:
            if placed >= target:
                break
            hx, hy, hw, hh = h["x"], h["y"], h["w"], h["h"]
            if cents:
                fcx, fcy = min(cents, key=lambda c: math.hypot(c[0] - hx, c[1] - hy))
                ax, ay = hx - fcx, hy - fcy
            else:
                ax, ay = 0, -1
            if abs(ax) >= abs(ay):        # snap the away-from-field direction to a cardinal, tuck the yard there
                ox, oy = hx + (1 if ax >= 0 else -1) * (hw / 2 + yw / 2 - 2), hy
            else:
                ox, oy = hx, hy + (1 if ay >= 0 else -1) * (hh / 2 + yh / 2 - 2)
            if not self._yard_fits(ox, oy, yw, yh, hx, hy):
                continue
            self._draw_threshing_yard(ox, oy, yw, yh)
            self.M["threshing_yards"].append({"x": round(ox, 1), "y": round(oy, 1), "w": yw, "h": yh, "rot": 0, "of": [hx, hy]})
            self.placed.append((ox, oy, yw, yh))
            placed += 1
        return placed

    def cemetery(self, cx, cy, w, h, rot=0, label=None, label_above=False, parish=True):
        """A BURIAL GROUND - rows of grave markers (sotoba / stone stelae) with a couple of taller
        memorial stupas. Every settlement above a hamlet buries its dead: a Buddhist danka PARISH
        ground sits in a TEMPLE / MONASTERY precinct (death is the Buddhist clergy's business), while
        a Shinto SHRINE keeps death-pollution (kegare) at arm's length - so a graveyard sits well
        clear of any shrine. parish=False marks a NON-parish burial ground (a village-style plot not
        attached to a temple, e.g. one serving an in-wall farm quarter) - exempt from the temple-precinct
        rule. Records M['cemeteries'] and blocks placement. label_above puts the label
        over the plot (for a cramped intramural ground whose label would otherwise spill onto its temple)."""
        g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-w/2:.1f}" y="{-h/2:.1f}" width="{w:.0f}" height="{h:.0f}" rx="3" fill="#CFC6B4" stroke="#8C8470" stroke-width="1.3" opacity="0.75"/>')
        st = random.getstate()
        random.seed(int(abs(cx) + abs(cy) * 3 + w))
        yy = -h / 2 + 9
        while yy < h / 2 - 5:                                # rows of small upright grave markers
            xx = -w / 2 + 8
            while xx < w / 2 - 5:
                mh = random.choice([6, 7, 8])
                g.append(f'<rect x="{xx-1.4:.1f}" y="{yy-mh:.1f}" width="2.8" height="{mh}" rx="1" fill="#9AA1A4" stroke="#5A584F" stroke-width="0.5"/>')
                xx += 9
            yy += 9
        for sxp in (-w / 2 + 13, w / 2 - 13):               # a couple of taller memorial stupas
            g.append(f'<rect x="{sxp-2.2:.1f}" y="{-h/2+1:.1f}" width="4.4" height="13" rx="1.5" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
            g.append(f'<circle cx="{sxp:.1f}" cy="{-h/2+1:.1f}" r="2.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.7"/>')
        random.setstate(st)
        g.append('</g>')
        self.add(''.join(g))
        self.M.setdefault("cemeteries", []).append({"x": round(cx, 1), "y": round(cy, 1), "w": w, "h": h, "rot": round(rot, 1), "parish": parish})
        self.placed.append((cx, cy, w, h))
        bm = 8
        self.block_polys.append([(cx - w / 2 - bm, cy - h / 2 - bm), (cx + w / 2 + bm, cy - h / 2 - bm),
                                 (cx + w / 2 + bm, cy + h / 2 + bm), (cx - w / 2 - bm, cy + h / 2 + bm)])
        if label:
            ly = cy - h / 2 - 8 if label_above else cy + h / 2 + 14
            self.label(cx, ly, label, 11, italic=True, color="#6B5A3C")

    def _ward_fence_cap(self, a, b, tol=16):
        """If the axis-aligned wall segment a-b runs ALONG a neighborhood (ward) fence, re-stamp the
        fence stroke over it so the FENCE renders ON TOP - the compound's own wall runs underneath, and
        the fence IS that side of the compound (no doubled, clashing parallel walls). Mirrors how a
        ward's own ends run under the city rampart. Returns the cap's z if it stamped one, else None."""
        ax, ay = a
        bx, by = b
        horiz = abs(ax - bx) >= abs(ay - by)
        for w in self.M.get("wards", []):
            bnd = w["boundary"]
            for i in range(len(bnd) - 1):
                px, py = bnd[i]
                qx, qy = bnd[i + 1]
                if (abs(px - qx) >= abs(py - qy)) != horiz:   # fence segment must run the same way
                    continue
                if horiz:
                    if abs(py - ay) > tol:
                        continue
                    lo, hi = max(min(ax, bx), min(px, qx)), min(max(ax, bx), max(px, qx))
                    if hi - lo < 10:
                        continue
                    dd = f'M{lo:.0f},{ay:.0f} L{hi:.0f},{ay:.0f}'
                else:
                    if abs(px - ax) > tol:
                        continue
                    lo, hi = max(min(ay, by), min(py, qy)), min(max(ay, by), max(py, qy))
                    if hi - lo < 10:
                        continue
                    dd = f'M{ax:.0f},{lo:.0f} L{ax:.0f},{hi:.0f}'
                self.add(f'<path d="{dd}" fill="none" stroke="#9C8A5E" stroke-width="5" opacity="0.9" stroke-linecap="round"/>')
                z = self.add(f'<path d="{dd}" fill="none" stroke="#4A3A22" stroke-width="1.3" stroke-dasharray="2,7" opacity="0.85"/>')   # palisade dash
                return z
        return None

    def mausoleum(self, cx, cy, w, h, label="Ancestral Mausoleum", gate_dir="south", label_below=False):
        """A walled CRYPT PRECINCT - the ruling clan's ancestral mausoleum, where important samurai are
        interred in crypts and stone monuments after cremation. A prestige ground sited by the SAMURAI /
        government quarter (ancestor veneration is central to samurai identity), religiously staffed but a
        martial-clan monument distinct from the commoner temple graveyards. A walled court (like a manor)
        holding a stone crypt hall and a few tall memorial stupas. Records M['mausoleums']; blocks placement."""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        self.add(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{w}" height="{h}" fill="#E7DDC4"/>')   # the swept precinct court
        wall = '#3A352C'
        sides = {"north": ((x0, y0), (x1, y0), cx, y0), "south": ((x0, y1), (x1, y1), cx, y1),
                 "west": ((x0, y0), (x0, y1), x0, cy), "east": ((x1, y0), (x1, y1), x1, cy)}
        for name, (a, b, gx, gy) in sides.items():
            if name != gate_dir:
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="5"/>')
            elif name in ("west", "east"):                                  # vertical wall - gap in y
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{a[0]:.0f}" y2="{gy-26:.0f}" stroke="{wall}" stroke-width="5"/>')
                self.add(f'<line x1="{b[0]:.0f}" y1="{gy+26:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="5"/>')
            else:                                                          # horizontal wall - gap in x
                self.add(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{gx-26:.0f}" y2="{a[1]:.0f}" stroke="{wall}" stroke-width="5"/>')
                self.add(f'<line x1="{gx+26:.0f}" y1="{b[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{wall}" stroke-width="5"/>')
        # a wall that ABUTS a neighborhood (ward) fence yields to it: the fence is re-stamped over our
        # own wall there, so it renders ON TOP and IS that side of the precinct (recorded for the gate)
        ward_walls = [name for name, (a, b, gx, gy) in sides.items()
                      if name != gate_dir and self._ward_fence_cap(a, b) is not None]
        hw, hh = min(w * 0.42, 86), min(h * 0.34, 52)                       # the stone crypt hall, centered
        self.add(f'<rect x="{cx-hw/2:.0f}" y="{cy-hh/2:.0f}" width="{hw:.0f}" height="{hh:.0f}" rx="2" fill="#C9C0AE" stroke="#5A584F" stroke-width="2"/>')
        self.add(f'<rect x="{cx-hw/2:.0f}" y="{cy-hh/2:.0f}" width="{hw:.0f}" height="8" fill="#7A5A30"/>')   # the hall's roof band
        for sx in (x0 + 16, x1 - 16):                                       # tall memorial stupas flanking the hall
            self.add(f'<rect x="{sx-3:.0f}" y="{cy-9:.0f}" width="6" height="18" rx="2" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
            self.add(f'<circle cx="{sx:.0f}" cy="{cy-9:.0f}" r="3.4" fill="#B7B0A0" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["mausoleums"].append({"x": cx, "y": cy, "w": w, "h": h, "rot": 0, "label": label, "gate_dir": gate_dir, "ward_walls": ward_walls})
        self.placed.append((cx, cy, w, h))
        m = 30
        self.block_polys.append([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])
        if label:
            ly = y1 + 14 if label_below else y0 - 12
            self.label(cx, ly, label, 12, weight="bold", italic=True, color="#3A352C")

    def cremation_ground(self, cx, cy, label="cremation ground", label_above=False):
        """The CREMATORY (kasoba) - where the dead are burned before their bones are interred. Smoke, fire
        risk, and death-pollution put it OUTSIDE the walls; monks officiate with burakumin assistants (a
        religious order stands outside the caste system, so handling the dead does not pollute its caste).
        A cleared, scorched ground with a raised stone pyre platform, a wisp of smoke, and a small roofed
        shelter for the rite. Records M['cremation_grounds']; blocks placement."""
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="58" ry="40" fill="#C9BCA0" stroke="#8C7A56" stroke-width="1.5" opacity="0.85"/>')   # cleared scorched ground
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="22" fill="#9A8A6A" opacity="0.5"/>')                                        # the burned centre
        self.add(f'<rect x="{cx-18:.0f}" y="{cy-12:.0f}" width="36" height="24" rx="2" fill="#8C8470" stroke="#4A463C" stroke-width="1.5"/>')   # stone pyre platform
        self.add(f'<rect x="{cx-13:.0f}" y="{cy-7:.0f}" width="26" height="14" fill="#5A463A"/>')                                       # the ash bed
        self.add(f'<path d="M{cx:.0f},{cy-12} q -8,-14 2,-26 q 8,-10 -2,-24" fill="none" stroke="#B8B0A2" stroke-width="3" opacity="0.5" stroke-linecap="round"/>')   # a wisp of smoke
        self.add(f'<rect x="{cx+30:.0f}" y="{cy-8:.0f}" width="22" height="16" rx="1.5" fill="#CDB890" stroke="#5A4326" stroke-width="1.2"/>')   # the officiants' shelter
        self.add(f'<rect x="{cx+30:.0f}" y="{cy-8:.0f}" width="22" height="5" fill="#5A4326"/>')
        self.M["cremation_grounds"].append({"x": round(cx, 1), "y": round(cy, 1), "w": 116, "h": 80, "rot": 0})
        self.placed.append((cx, cy, 116, 80))
        m = 8
        self.block_polys.append([(cx - 58 - m, cy - 40 - m), (cx + 58 + m, cy - 40 - m),
                                 (cx + 58 + m, cy + 40 + m), (cx - 58 - m, cy + 40 + m)])
        if label:
            self.label(cx, cy - 40 - 8 if label_above else cy + 40 + 14, label, 11, italic=True, color="#6B5A3C")

    def ossuary(self, cx, cy, label="pauper ossuary mound"):
        """A PAUPER OSSUARY MOUND - a communal earthen mound where the bones of the poor and the
        'unconnected dead' (muenbotoke - those with no family or temple to inter them) are gathered, by
        the cremation ground outside the walls. A low rounded mound with a single weathered marker stupa.
        Records M['ossuaries']; blocks placement."""
        self.add(f'<ellipse cx="{cx}" cy="{cy+6}" rx="46" ry="28" fill="#BCA878" stroke="#8C7A52" stroke-width="1.5"/>')   # the earthen mound
        self.add(f'<ellipse cx="{cx}" cy="{cy-2}" rx="30" ry="16" fill="#C8B584" opacity="0.7"/>')                          # the crown (shading)
        self.add(f'<rect x="{cx-3:.0f}" y="{cy-22:.0f}" width="6" height="20" rx="2" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')   # a weathered marker stupa
        self.add(f'<circle cx="{cx:.0f}" cy="{cy-22:.0f}" r="4" fill="#A8A294" stroke="#5A584F" stroke-width="0.8"/>')
        self.M["ossuaries"].append({"x": round(cx, 1), "y": round(cy, 1), "w": 92, "h": 60, "rot": 0})
        self.placed.append((cx, cy, 92, 56))
        m = 8
        self.block_polys.append([(cx - 46 - m, cy - 28 - m), (cx + 46 + m, cy - 28 - m),
                                 (cx + 46 + m, cy + 34 + m), (cx - 46 - m, cy + 34 + m)])
        if label:
            self.label(cx, cy + 34 + 14, label, 11, italic=True, color="#6B5A3C")

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

    def flophouse(self, x, y, w=104, h=46, label="flophouse", label_below=False):
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
            self.label(x, y0 + h + 19 if label_below else y0 - 10, label, 11, italic=True, color="#5A4A30")

    def inn(self, x, y, w=66, h=48, rot=0):
        """A prominent caravan INN - larger and grander than a flophouse, lodging the merchants, drivers
        and guards of the wagon-trains. Recorded in M['buildings'] (kind 'inn', non-residential). It
        FRONTS the road, so `rot` tilts it to lie PARALLEL to a diagonal road with its noren entrance
        (the +y front) FACING the roadbed. Blocks placement - place BEFORE any nearby pack."""
        hw, hh = w / 2, h / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
             f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="{h}" rx="2" fill="#D9B98C" stroke="#5A3F1E" stroke-width="2.2"/>',
             f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="11" fill="#7A5A30"/>',                # roof ridge
             f'<rect x="{-hw:.0f}" y="{hh-4:.0f}" width="{w}" height="4" fill="#7A5A30" opacity="0.55"/>']  # lower eave (2-storey)
        for i in range(3):                                                                                # upper-storey lattice windows
            wx = -hw + w * (0.2 + 0.3 * i)
            g.append(f'<rect x="{wx:.0f}" y="{-hh+14:.0f}" width="10" height="7" fill="#9A7E4E" stroke="#5A3F1E" stroke-width="0.6"/>')
            g.append(f'<line x1="{wx+5:.0f}" y1="{-hh+14:.0f}" x2="{wx+5:.0f}" y2="{-hh+21:.0f}" stroke="#D6C49A" stroke-width="0.6"/>')
        nx, nw = -w * 0.19, w * 0.38                                                                      # NOREN entrance curtain on the +y front
        g.append(f'<rect x="{nx:.0f}" y="{hh:.0f}" width="{nw:.0f}" height="9" rx="1" fill="#2E4A6B" stroke="#1E3450" stroke-width="0.6"/>')
        for k in (1, 2):
            g.append(f'<line x1="{nx + nw*k/3:.0f}" y1="{hh:.0f}" x2="{nx + nw*k/3:.0f}" y2="{hh+9:.0f}" stroke="#C9D4E0" stroke-width="0.7"/>')
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "inn", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    def stables(self, x, y, w=92, h=44, rot=0):
        """A large STABLES - long rows of stalls for a wagon-train's many draft animals (oxen, horses).
        Recorded in M['buildings'] (kind 'stables', non-residential). Wants OPEN GROUND around it. `rot`
        tilts it to sit parallel to its inn / the road. Place BEFORE any nearby pack."""
        hw, hh = w / 2, h / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})">',
             f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="{h}" rx="2" fill="#B79A6E" stroke="#5A4326" stroke-width="2"/>',
             f'<rect x="{-hw:.0f}" y="{-hh:.0f}" width="{w}" height="9" fill="#6B4F2A"/>']                 # roof ridge
        for sx in range(int(-hw) + 12, int(hw) - 8, 16):                                                  # stall divisions
            g.append(f'<line x1="{sx}" y1="{-hh+9:.0f}" x2="{sx}" y2="{hh:.0f}" stroke="#6B4F2A" stroke-width="1.4" opacity="0.7"/>')
        g.append('</g>')
        self.add(''.join(g))
        self.M["buildings"].append({"x": x, "y": y, "w": w, "h": h, "kind": "stables", "rot": rot})
        self.placed.append((x, y, w, h))
        bm = 24
        self.block_polys.append([(x - hw - bm, y - hh - bm), (x + hw + bm, y - hh - bm), (x + hw + bm, y + hh + bm), (x - hw - bm, y + hh + bm)])

    # ---- provincial-city features (scale="city")
    def _gapped_ring(self, ring, gates, gap=38, closed=True):
        """An SVG path for a wall (closed ring or open arc) with a genuine OPENING (~2*gap wide) at each
        gate, so the rampart can render OVER the ground lanes yet still let the road show THROUGH the gate
        - rather than painting a land rect over the wall (which would erase the road too, once on top)."""
        gpts = [(g[0], g[1]) for g in gates]

        def isg(p):
            return any(math.hypot(p[0] - x, p[1] - y) < 6 for x, y in gpts)

        def lerp(a, b, d):
            length = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            return (a[0] + (b[0] - a[0]) * d / length, a[1] + (b[1] - a[1]) * d / length)
        subs, cur = [], []
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            s = lerp(a, b, gap) if isg(a) else a
            e = lerp(b, a, gap) if isg(b) else b
            if not cur:                         # start a fresh run (the first edge, or just after a gate)
                cur = [s]
            cur.append(e)
            if isg(b):                          # this edge ends at a gate - close the run (a gap follows)
                subs.append(cur)
                cur = []
        if cur:
            subs.append(cur)
        if closed and len(subs) >= 2 and not isg(ring[0]):   # closed ring, ring[0] not a gate: last run continues into the first
            subs[0] = subs[-1] + subs[0][1:]
            subs.pop()
        return ' '.join('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in sp) for sp in subs)

    def ring_road(self, wall_pts, inset=34, width=15):
        """A patrol/access ROAD just inside the city wall - the Chinese 'follow-the-wall street'
        (順城街) - a closed loop offset `inset` px in from the rampart, leaving the wall-clear zone
        a fortified city keeps for moving troops along the wall. Records M['ring_road']; returns the
        loop polygon to use as s.bound (so the quarters pack INSIDE it, off the wall). It is NOT a
        town_street: a fortification road is exempt from the must-be-built-up rule (its wall side is
        bare by design, and stretches run behind fields/compounds), but the grid still connects to it."""
        cx = sum(p[0] for p in wall_pts) / len(wall_pts)
        cy = sum(p[1] for p in wall_pts) / len(wall_pts)
        ring = []
        for x, y in wall_pts:
            d = math.hypot(x - cx, y - cy) or 1.0
            f = (d - inset) / d
            ring.append((cx + (x - cx) * f, cy + (y - cy) * f))
        loop = ring + [ring[0]]
        dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in loop)
        self._ground(width, self.M, "ring_road_z",
                     edge=f'<path d="{dd}" fill="none" stroke="#B49A66" stroke-width="{width}" opacity="0.85" stroke-linejoin="round"/>',
                     bed=f'<path d="{dd}" fill="none" stroke="#D9C8A0" stroke-width="{width-6}" opacity="1" stroke-linejoin="round"/>')
        self.corridors.append((loop, width / 2 + 17))   # buildings keep WELL off the ring road (even a large/rotated footprint's corner stays off its bed)
        self.M["ring_road"] = [[round(x, 1), round(y, 1)] for x, y in loop]
        self.M["ring_road_width"] = width
        return ring

    def _tower(self, x, y, rot=0.0, wc='#3A352C', tw=38):
        """A square guard tower straddling the wall (drawn OVER the rampart), ROTATED to sit square to
        the wall (rot = the wall's tangent angle there, so a tower on a slanted wall slants with it).
        Records M['wall_towers'] and reserves a no-build block so the packs leave it clear."""
        h = tw / 2
        z = self.add_top(f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">'
                         f'<rect x="{-h:.0f}" y="{-h:.0f}" width="{tw}" height="{tw}" fill="#9C8A66" stroke="{wc}" stroke-width="2.4"/>'
                         f'<rect x="{-h+7:.0f}" y="{-h+7:.0f}" width="{tw-14}" height="{tw-14}" fill="#6B5A3A"/></g>')
        self.M.setdefault("wall_towers", []).append({"x": round(x, 1), "y": round(y, 1), "w": tw, "h": tw, "rot": round(rot, 1), "z": z})
        bm = 24
        self.block_polys.append([(x - tw / 2 - bm, y - tw / 2 - bm), (x + tw / 2 + bm, y - tw / 2 - bm),
                                 (x + tw / 2 + bm, y + tw / 2 + bm), (x - tw / 2 - bm, y + tw / 2 + bm)])
        return z

    def _wall_walk(self, pts, g_idx, arc, west=True):
        """From wall vertex g_idx, walk `arc` px ALONG the wall (toward the WEST neighbour - smaller x -
        if west, else EAST), returning (x, y, edge_angle_deg) at that arc-distance. Lets gate furniture
        follow the curving wall and pick up its LOCAL tangent, instead of a flat offset + the gate
        vertex's tangent (which mismatch once the wall has curved away from the gate)."""
        n = len(pts)
        step_to_east = 1 if pts[(g_idx + 1) % n][0] >= pts[(g_idx - 1) % n][0] else -1
        step = -step_to_east if west else step_to_east
        i, rem = g_idx, arc
        while True:
            j = (i + step) % n
            ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            seg = math.hypot(ex, ey) or 1.0
            if seg >= rem:
                t = rem / seg
                return pts[i][0] + ex * t, pts[i][1] + ey * t, math.degrees(math.atan2(ey, ex))
            rem -= seg
            i = j

    def city_wall(self, pts, gates=(), ring_inset=34):
        """A CLOSED city rampart (a full ring, unlike the town's open hill-anchored arc), with a
        gap at each gate in `gates` (each (x,y) on the ring, where the wall runs ~horizontal -
        the N and S gates the Imperial road passes through). Each gate gets a GUARD HOUSE with an
        attached INSPECTION STATION (tariff audit) and a GUARD TOWER, all in the top layer so the
        road passes under them. Records M['wall'], M['gates'], M['gate'], M['gate_structs'] (the
        guard houses + towers), and M['inspection_stations']."""
        wc = '#3A352C'
        ring = list(pts) + [pts[0]]
        # the rampart renders in the WALL layer (over the ground lanes - a street running into the wall
        # passes UNDER it) with a GENUINE gap at each gate, so the road shows through the opening
        dd = self._gapped_ring(ring, gates, 38)
        self.M["wall_z"] = self.add_wall(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="11" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add_wall(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        # the wall's TANGENT angle at each vertex (the chord through its two neighbours) - towers rotate
        # to sit square to the wall, so a tower on a slanted stretch slants with it
        tang = [math.degrees(math.atan2(pts[(i + 1) % n][1] - pts[i - 1][1], pts[(i + 1) % n][0] - pts[i - 1][0])) for i in range(n)]
        self.M["gate_structs"] = []
        for gx, gy in gates:
            self.add_wall(f'<rect x="{gx-42:.0f}" y="{gy-26:.0f}" width="14" height="52" fill="{wc}"/>')      # gateposts (frame the opening)
            self.add_wall(f'<rect x="{gx+28:.0f}" y="{gy-26:.0f}" width="14" height="52" fill="{wc}"/>')
            g_idx = next(i for i, p in enumerate(pts) if p[0] == gx and p[1] == gy)   # the gate's wall vertex
            # the GUARD HOUSE + INSPECTION STATION sit ON the ring road just inside the gate, each one
            # WALKED along the curving wall (so it picks up the wall's LOCAL tangent there, not the gate
            # vertex's) and pulled in radially to the ring road's centerline (inset `ring_inset`, matching
            # s.ring_road) - so the patrol road runs lengthwise THROUGH each building, which sits SQUARE
            # to the wall like the towers, instead of the road slicing across an axis-aligned box.
            insp_xy = None
            for kind, arc, fw, fh, fill in (("guardhouse", 80, 66, 44, "#C9A57A"), ("inspection", 144, 60, 44, "#D8C49A")):
                wx, wy, ang = self._wall_walk(pts, g_idx, arc, west=True)
                d = math.hypot(wx - cx, wy - cy) or 1.0
                f = (d - ring_inset) / d                          # radial inset to the ring road centerline
                fx, fy = cx + (wx - cx) * f, cy + (wy - cy) * f
                a = (ang + 90) % 180 - 90                          # local wall tangent, folded to (-90, 90]
                trim = (f'<line x1="{-fw/2:.0f}" y1="0" x2="{fw/2:.0f}" y2="0" stroke="#5A4326" stroke-width="0.8"/>'
                        if kind == "guardhouse" else
                        f'<rect x="{-fw/2:.0f}" y="{-fh/2:.0f}" width="{fw}" height="8" fill="#8A6E3E"/>')
                z = self.add_top(f'<g transform="translate({fx:.0f},{fy:.0f}) rotate({a:.1f})">'
                                 f'<rect x="{-fw/2:.0f}" y="{-fh/2:.0f}" width="{fw}" height="{fh}" rx="2" fill="{fill}" stroke="#5A4326" stroke-width="1.8"/>'
                                 f'{trim}</g>')
                self.M["gate_structs"].append({"x": fx, "y": fy, "w": fw, "h": fh, "rot": round(a, 1), "kind": kind, "z": z})
                if kind == "inspection":
                    self.M["inspection_stations"].append({"x": fx, "y": fy, "w": fw, "h": fh, "rot": round(a, 1), "label": "inspection station"})
                    insp_xy = (fx, fy)
            # the gate guard TOWER straddles the WALL just east of the gate, likewise tilted to the wall there
            twx, twy, tang_e = self._wall_walk(pts, g_idx, 78, west=False)
            ta = (tang_e + 90) % 180 - 90
            tz = self._tower(twx, twy, ta, wc, tw=40)
            self.M["gate_structs"].append({"x": twx, "y": twy, "w": 40, "h": 40, "rot": round(ta, 1), "kind": "tower", "z": tz})
            self.label(insp_xy[0] + 14, insp_xy[1] + 45, "gate guard house + inspection", 9, italic=True, color="#5A4326")
            for gs in self.M["gate_structs"][-3:]:
                bm = 30
                self.block_polys.append([(gs["x"] - gs["w"] / 2 - bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] - gs["h"] / 2 - bm),
                                         (gs["x"] + gs["w"] / 2 + bm, gs["y"] + gs["h"] / 2 + bm),
                                         (gs["x"] - gs["w"] / 2 - bm, gs["y"] + gs["h"] / 2 + bm)])
        # GUARD TOWERS at regular intervals around the rampart, in addition to the gate towers: a
        # fortified city is towered for enfilading fire along the wall face (a bowshot apart), and the
        # towers also house the stairs up to the parapet. Even spacing at every other wall vertex,
        # skipping the gate vertices (those already have a tower).
        self.M.setdefault("wall_towers", [])   # the gate towers were already added above (via _tower)
        for i in range(0, n, 2):
            vx, vy = pts[i]
            if not any(math.hypot(vx - gx, vy - gy) < 130 for gx, gy in gates):
                self._tower(vx, vy, tang[i], wc)
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
        self.M["moat"] = [[round(x, 1), round(y, 1)] for x, y in mo]
        self.M["moat_width"] = width
        self.M["moat_layer"] = ml = {}                       # records the moat's bed/sheen draw positions
        self._water(   # routed through the shared water groups so a feeder stream merges into it cleanly
            f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>',
            ml,
            sheen=f'<path d="{dd}" fill="none" stroke="#B6CAD8" stroke-width="{width*0.4:.0f}" stroke-linejoin="round" stroke-linecap="round"/>')   # lighter mid-water sheen (NOT a dashed lane line)
        self.corridors.append(([(x, y) for x, y in mo], 28))
        return [(round(x, 1), round(y, 1)) for x, y in mo]

    def bridge(self, x, y, rot, span, deck_w):
        """A timber BRIDGE carrying a road (or town street) over a watercourse - a stream, an
        irrigation channel, or the city moat at a gate. Centered on the crossing (x, y); the deck
        runs along `rot` (the road's bearing, degrees) for `span` px (long enough to reach both
        banks) and is `deck_w` wide (the carried road's width). Drawn on the TOP layer so it sits
        ABOVE the water and the roadbed. Records M['bridges']."""
        hl, hw = span / 2, deck_w / 2
        g = [f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-hl:.1f}" y="{-hw:.1f}" width="{span:.1f}" height="{deck_w:.1f}" rx="2" '
                 f'fill="#B68D5A" stroke="#5A3F1E" stroke-width="1.6"/>')   # the planked timber deck
        step = max(7, span / 8)                                             # plank seams across the deck
        sx = -hl + step
        while sx < hl - 1:
            g.append(f'<line x1="{sx:.1f}" y1="{-hw:.1f}" x2="{sx:.1f}" y2="{hw:.1f}" stroke="#5A3F1E" stroke-width="0.7" opacity="0.55"/>')
            sx += step
        g.append(f'<rect x="{-hl:.1f}" y="{-hw-2.4:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')   # the two side rails
        g.append(f'<rect x="{-hl:.1f}" y="{hw-0.2:.1f}" width="{span:.1f}" height="2.6" fill="#5A3F1E"/>')
        g.append('</g>')
        z = self.add_top(''.join(g))
        self.M.setdefault("bridges", []).append({"x": round(x, 1), "y": round(y, 1), "rot": round(rot, 1),
                                                 "span": round(span, 1), "w": round(deck_w, 1), "z": z})
        return z

    def bridges(self):
        """Auto-span every place a road or town street CROSSES a watercourse with a s.bridge(),
        oriented along the road. Call AFTER all roads/streets AND all water (streams, channels,
        the moat) are placed - a watercourse added later would leave an unbridged crossing (which
        the `roads_bridge_water` check then flags). Returns the number of bridges drawn. Historically
        a walled city's approach road crossed the moat on a bridge at each gate, and a country road
        crossed a stream on a timber bridge."""
        carried = []
        if self.M.get("road"):
            carried.append((self.M["road"], self.M.get("road_width", 26)))
        for st in self.M.get("town_streets", []):
            carried.append((st["pts"], st["w"]))
        waters = []
        for s in self.M.get("streams", []):
            waters.append((s["poly"], s.get("w", 9)))
        for c in self.M.get("channels", []):
            waters.append((c["poly"], 4.2))
        if self.M.get("moat"):
            waters.append((self.M["moat"], self.M.get("moat_width", 22)))
        n = 0
        for rpts, rw in carried:
            for i in range(len(rpts) - 1):
                ra, rb = tuple(rpts[i]), tuple(rpts[i + 1])
                for wpts, ww in waters:
                    for j in range(len(wpts) - 1):
                        wa, wb = tuple(wpts[j]), tuple(wpts[j + 1])
                        if segments_cross(ra, rb, wa, wb):
                            # segments_cross is True only for a genuine (non-parallel) crossing, so
                            # seg_intersect always returns a point here
                            p = seg_intersect(ra, rb, wa, wb)
                            rot = math.degrees(math.atan2(rb[1] - ra[1], rb[0] - ra[0]))
                            self.bridge(p[0], p[1], rot, ww + max(28, rw), rw)   # span reaches both banks + abutments
                            n += 1
        return n

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
        neighborhood). Official violet roof so it reads apart from housing/commerce."""
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
        # the rampart renders in the WALL layer (over the ground lanes - a street running into it passes
        # UNDER it), with a genuine gap at the gate so the road shows through the opening
        dd = self._gapped_ring(pts, [gate] if gate else [], 36, closed=False)
        self.M["wall_z"] = self.add_wall(f'<path d="{dd}" fill="none" stroke="{wc}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>')
        self.add_wall(f'<path d="{dd}" fill="none" stroke="#6B5A3A" stroke-width="3" stroke-linejoin="round" opacity="0.5"/>')
        if gate:
            gx, gy = gate
            self.add_wall(f'<rect x="{gx-42:.0f}" y="{gy-24:.0f}" width="14" height="48" fill="{wc}"/>')         # gateposts (frame the opening)
            self.add_wall(f'<rect x="{gx+28:.0f}" y="{gy-24:.0f}" width="14" height="48" fill="{wc}"/>')
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
        # a farmhouse shares the MAP'S building grain (bscale): at village/hamlet scale bscale is
        # 1.0 (full size), but a town/city compresses its urban buildings, and a peasant farmhouse
        # must not render LARGER than the samurai and merchant houses inside the walls - so it
        # scales down by the same factor.
        bw, bh = (60, 40) if kind == "big" else (44, 29)   # south-facing: long axis E-W
        w, h = bw * self.bscale, bh * self.bscale
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
        # record the TEXT (element [5]) too, so the gate can verify a zone/neighborhood label actually
        # sits with the cluster it names (same side of the wall, among its buildings)
        self.M["labels"].append([round(x0, 1), round(y - size * 0.8, 1), round(x0 + w, 1), round(y + size * 0.25, 1), z, text])

    def label(self, x, y, text, size=12, anchor="middle", italic=False, weight="normal", color="#2D2A24"):
        esc = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        st = ' font-style="italic"' if italic else ''
        # labels live in the topmost LABEL layer so nothing - not a road, not a wall, not a kido or torii
        # - ever paints over the text (a label must always be fully readable)
        z = self.add_label(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
                         f'font-weight="{weight}"{st} fill="{color}" paint-order="stroke" stroke="{LAND}" stroke-width="3">{esc}</text>')
        self._record_label(x, y, text, size, anchor, z)

    def title(self, name):
        # just the place name - no subtitle/summary; the map is self-evident. On a cropped (city)
        # view, sit top-left inside the window, clear of the N-gate road that splits the top center.
        if self.view:
            self.add_label(f'<text x="{self.view[0] + 30}" y="{self.view[1] + 46}" font-size="30" '
                           f'font-weight="bold" fill="#2D2A24">{name}</text>')
        else:
            self.add_label(f'<text x="{self.W/2}" y="52" text-anchor="middle" font-size="30" font-weight="bold" fill="#2D2A24">{name}</text>')

    def compass(self, x=None, y=128):
        if self.view and x is None:                 # top-right corner inside the cropped window
            x, y = self.view[0] + self.view[2] - 70, self.view[1] + 76
        x = x if x is not None else self.W - 72
        self.M["compass"] = {"x": x, "y": y}   # recorded so the gate can keep it clear of the map (readability)
        self.add(f'<g transform="translate({x},{y})">'
                 '<circle r="26" fill="#EFE3C2" stroke="#2D2A24" stroke-width="1.5"/>'
                 '<polygon points="0,-22 5,0 0,6 -5,0" fill="#2D2A24"/>'
                 '<polygon points="0,22 5,0 0,-6 -5,0" fill="#9C8C70"/>'
                 '<text x="0" y="-30" text-anchor="middle" font-size="12" font-weight="bold">N</text>'
                 '<text x="0" y="40" text-anchor="middle" font-size="11">S</text></g>')

    def finish(self, basepath, render=True, png_width=2600):
        splices = []                                # (placeholder_idx, block) - spliced high-index-first below
        if self._ground_idx is not None:            # the ordered linear-ground block (alley<street<road)
            feats = sorted(self.ground, key=lambda g: (g["zpri"], g["seq"]))
            block, edge_zs, bed_zs = [], [], []
            for g in feats:                          # EDGES first (the dark borders), bottom of the block
                if g["edge"] is not None:
                    edge_zs.append(self._ground_idx + len(block))
                    block.append(g["edge"])
            for g in feats:                          # then BEDS (paved surfaces) - they merge at crossings
                if g["bed"] is not None:
                    g["rec"][g["zkey"]] = self._ground_idx + len(block)   # recorded z = the bed's draw position
                    bed_zs.append(self._ground_idx + len(block))
                    block.append(g["bed"])
            for g in feats:                          # then TOP marks (centre dashes / gravel speckle)
                if g["top"] is not None:
                    block.append(g["top"])
            if edge_zs:                              # every edge sits below every bed -> clean crossroads
                self.M["ground_edge_zmax"] = max(edge_zs)
            if bed_zs:
                self.M["ground_bed_zmin"] = min(bed_zs)
            splices.append((self._ground_idx, block))
        if self._water_idx is not None:             # the watercourse block: all BEDS (one opacity group),
            wblock, bedzs, sheenzs = [], [], []      # then all SHEENS above - so crossings MERGE, not stack
            wblock.append('<g opacity="0.85">')
            for w in self.water:
                w["rec"]["bedz"] = self._water_idx + len(wblock)
                bedzs.append(self._water_idx + len(wblock))
                wblock.append(w["bed"])
            wblock.append('</g>')
            wblock.append('<g opacity="0.55">')
            for w in self.water:
                if w["sheen"] is not None:
                    w["rec"]["sheenz"] = self._water_idx + len(wblock)
                    sheenzs.append(self._water_idx + len(wblock))
                    wblock.append(w["sheen"])
            wblock.append('</g>')
            if bedzs:                                # every bed sits below every sheen -> clean confluence
                self.M["water_bed_zmax"] = max(bedzs)
            if sheenzs:
                self.M["water_sheen_zmin"] = min(sheenzs)
            splices.append((self._water_idx, wblock))
        for idx, block in sorted(splices, key=lambda s: -s[0]):   # high index first so the lower stays valid
            self.out[idx:idx + 1] = block
        if self.view:                               # crop the viewBox to the requested window
            ox, oy, vw, vh = self.view
            self.out[0] = self.out[0].replace(f'viewBox="0 0 {self.W} {self.H}"',
                                              f'viewBox="{ox} {oy} {vw} {vh}"')
        body = self.out + self.walls + self.top + self.toplabels + ['</svg>']   # WALLS over lanes; TOP furniture; LABEL text topmost
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
