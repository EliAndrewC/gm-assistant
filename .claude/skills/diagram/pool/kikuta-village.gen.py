#!/usr/bin/env python3
"""Kikuta village plan (diagram skill, Mode B) - iteration 4.

GM feedback addressed:
- fields get terrain-following organic outlines (lobes/indentations off a
  semi-rectangular core), cells clipped to them
- houses face south (historical minka sun orientation): ridge E-W, entry south
- lane + irrigation channels are no-build corridors (no roads/water through houses)
- irrigation rerouted clear of the headman's house; pond renamed "irrigation pond"
- shrine seated on the summit contour (no longer overhanging the hill edge)
"""
import json
import math
import os
import random

random.seed(23)

W, H = 1820, 1180
out = []
_clip = [0]
M = {"houses": [], "fields": [], "channels": [], "lane": [], "taxfree": [], "torii": [],
     "pond": None, "hill": None, "summit": None, "shrine": None}


def add(s):
    out.append(s)


# ---------------------------------------------------------------- header / defs
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'font-family="Georgia, \'Times New Roman\', serif">')
add('<defs>')
add('<pattern id="drycrop" width="12" height="12" patternUnits="userSpaceOnUse">'
    '<rect width="12" height="12" fill="#CDB57E"/>'
    '<line x1="0" y1="3" x2="12" y2="3" stroke="#A98E54" stroke-width="0.7"/>'
    '<line x1="0" y1="8" x2="12" y2="8" stroke="#A98E54" stroke-width="0.7"/></pattern>')
add('<pattern id="fallow" width="14" height="14" patternUnits="userSpaceOnUse">'
    '<rect width="14" height="14" fill="#D7C49A"/>'
    '<circle cx="3" cy="4" r="0.9" fill="#A89464"/>'
    '<circle cx="9" cy="9" r="0.9" fill="#A89464"/>'
    '<circle cx="11" cy="3" r="0.7" fill="#B7A06C"/></pattern>')
add('</defs>')
add(f'<rect width="{W}" height="{H}" fill="#EFE3C2"/>')

# ---------------------------------------------------------------- regions
WEST_FIELD = (235, 460, 700, 740)    # long E-W
EAST_FIELD = (860, 478, 1165, 942)   # long N-S, staggered lower-right
MIDNORTH = (715, 185, 900, 320)      # small healthy field, middle-north
SW_FIELD = (250, 858, 452, 1010)     # fallow
SE_FIELD = (1262, 910, 1470, 1058)   # fallow
POND = (378, 220, 96, 58)            # cx, cy, rx, ry
HILL = (1600, 605, 198, 152)         # cx, cy, rx, ry
HEADMAN = (1006, 430)
blocked_rects = [WEST_FIELD, EAST_FIELD, MIDNORTH, SW_FIELD, SE_FIELD]


# ---------------------------------------------------------------- geometry helpers
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
    """Sample the actual rendered (Catmull-Rom) boundary so the manifest matches
    what's drawn - the smoothed curve bows inward of the raw vertices."""
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


def organic_outline(bbox, amp):
    """Semi-rectangular core with lobes (outgrowths) and bays (indentations)."""
    x0, y0, x1, y1 = bbox
    per_side = 4
    edges = [((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)),
             ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))]
    pts = []
    for (sa, sb, (nx, ny)) in edges:
        for i in range(per_side):
            t = i / per_side
            bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
            off = random.uniform(-amp * 0.5, amp)
            if i == 0:
                off *= 0.35  # keep corners near the rectangle
            jt = random.uniform(-amp * 0.18, amp * 0.18)
            pts.append((bx + nx * off + jt, by + ny * off + jt))
    return pts


# ---------------------------------------------------------------- paddy field (organic, clipped)
def paddy_field(bbox, label, name, amp=52, taxfree=0):
    x0, y0, x1, y1 = bbox
    outline = organic_outline(bbox, amp)
    M["fields"].append({"name": name, "bbox": list(bbox), "kind": "paddy",
                        "outline": [[x, y] for (x, y) in smooth_points(outline)]})
    d = smooth_closed(outline)
    _clip[0] += 1
    cid = f'fld{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
    ex0, ey0, ex1, ey1 = x0 - amp, y0 - amp, x1 + amp, y1 + amp

    def edges(lo, hi, target):
        # irregular cell widths so the basins vary in size (not a uniform grid)
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
    shades = ['#A7C49C', '#9FBE93', '#AECBA1', '#9BBA8F', '#B4CCA6']
    add(f'<g clip-path="url(#{cid})">')
    add(f'<rect x="{ex0:.0f}" y="{ey0:.0f}" width="{ex1-ex0:.0f}" height="{ey1-ey0:.0f}" fill="#C2A772"/>')
    for i in range(cols):
        for j in range(rows):
            quad = [P[(i, j)], P[(i + 1, j)], P[(i + 1, j + 1)], P[(i, j + 1)]]
            pts = ' '.join(f'{p[0]:.0f},{p[1]:.0f}' for p in quad)
            r = random.random()
            crop = 'dry' if r < 0.16 else ('soy' if r < 0.30 else 'rice')
            fill = 'url(#drycrop)' if crop == 'dry' else ('#9CB36A' if crop == 'soy' else random.choice(shades))
            add(f'<polygon points="{pts}" fill="{fill}" stroke="#C2A772" stroke-width="2.6" stroke-linejoin="round"/>')
            # rows are regular WITHIN a plot but angled differently between plots
            if crop in ('rice', 'soy'):
                xq = [p[0] for p in quad]
                yq = [p[1] for p in quad]
                cx0, cx1, cy0, cy1 = min(xq), max(xq), min(yq), max(yq)
                ccx, ccy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
                diag = math.hypot(cx1 - cx0, cy1 - cy0)
                theta = random.uniform(-0.6, 0.6)            # per-plot row angle
                dxu, dyu = math.cos(theta), math.sin(theta)
                nx, ny = -dyu, dxu
                _clip[0] += 1
                rcid = f'rc{_clip[0]}'
                add(f'<clipPath id="{rcid}"><polygon points="{pts}"/></clipPath>')
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
                add(''.join(g))
    # tax-free plots: the country monk's allocation, set by law to ~2 households
    # worth (2-3 plots), scattered non-contiguously like everyone else's strips
    if label and taxfree:
        picks = [(1, max(1, rows // 4)),
                 (max(2, cols // 2), max(2, rows // 2)),
                 (max(1, cols - 2), max(1, rows - 3))][:taxfree]
        seen = set()
        for (ci, cj) in picks:
            ci, cj = min(ci, cols - 1), min(cj, rows - 1)
            if (ci, cj) in seen:
                continue
            seen.add((ci, cj))
            quad = [P[(ci, cj)], P[(ci + 1, cj)], P[(ci + 1, cj + 1)], P[(ci, cj + 1)]]
            pts = ' '.join(f'{p[0]:.0f},{p[1]:.0f}' for p in quad)
            add(f'<polygon points="{pts}" fill="#A03020" fill-opacity="0.22" stroke="#A03020" stroke-width="4"/>')
            M["taxfree"].append([round(sum(p[0] for p in quad) / 4, 1),
                                 round(sum(p[1] for p in quad) / 4, 1)])
    add('</g>')
    add(f'<path d="{d}" fill="none" stroke="#A98A52" stroke-width="3.5"/>')  # field bund / outer boundary
    if label:
        add(f'<text x="{(x0+x1)/2:.0f}" y="{(y0+y1)/2:.0f}" text-anchor="middle" '
            f'font-size="15" font-weight="bold" fill="#33301E" letter-spacing="1.5" '
            f'paint-order="stroke" stroke="#EFE3C2" stroke-width="3.5">{label}</text>')


def fallow_field(bbox, name, amp=34):
    outline = organic_outline(bbox, amp)
    d = smooth_closed(outline)
    add(f'<path d="{d}" fill="url(#fallow)" stroke="#9C7A40" stroke-width="1.8" stroke-dasharray="6,4"/>')
    M["fields"].append({"name": name, "bbox": list(bbox), "kind": "fallow",
                        "outline": [[x, y] for (x, y) in smooth_points(outline)]})


# ---------------------------------------------------------------- house glyph (south-facing)
def house(cx, cy, w, h, kind="plain", rot=0, shed=False):
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
    g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h/2:.1f}" fill="{dark}"/>')   # north slope
    g.append(f'<rect x="{x0:.1f}" y="0" width="{w}" height="{h/2:.1f}" fill="{light}"/>')          # south slope (sunlit)
    dash = ' stroke-dasharray="5,3"' if kind == "abandoned" else ''
    g.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="3" fill="none" stroke="{edge}" stroke-width="1.5"{dash}/>')
    g.append(f'<line x1="{-w*0.30:.1f}" y1="0" x2="{w*0.30:.1f}" y2="0" stroke="{ridge}" stroke-width="2"/>')
    if kind == "big":
        g.append(f'<rect x="{x0-1:.1f}" y="{y0-h*0.42:.1f}" width="{w*0.40:.1f}" height="{h*0.5:.1f}" rx="3" fill="{light}" stroke="{edge}" stroke-width="1.3"/>')
    if kind == "abandoned":
        g.append(f'<polygon points="{-w*0.16:.1f},{-h*0.16:.1f} {w*0.16:.1f},{-h*0.04:.1f} {-w*0.04:.1f},{h*0.2:.1f}" fill="#6E6452" opacity="0.7"/>')
    else:
        g.append(f'<rect x="-3.5" y="{h/2-2:.1f}" width="7" height="3.3" fill="{edge}" opacity="0.85"/>')  # entry on south
    g.append('</g>')
    add(''.join(g))


# ---------------------------------------------------------------- corridors (no-build: lane + channels)
LANE = [(845, 1175), (822, 1010), (800, 930), (760, 840), (706, 792)]


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


# Each channel runs from INSIDE the pond to a point WELL INSIDE its field (so the
# field paints over the end -> a visible connection at both ends), winding gently.
CH_MID = winding((450, 228), (788, 250))
CH_WEST = winding((388, 260), (470, 520))
CH_CENTRAL = winding((440, 248), (945, 548))
named_channels = [("midnorth", CH_MID), ("west", CH_WEST), ("central", CH_CENTRAL)]
corridors = [LANE, CH_MID, CH_WEST, CH_CENTRAL]


def seg_dist(px, py, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def near_corridor(x, y, thresh=22):
    for poly in corridors:
        for k in range(len(poly) - 1):
            if seg_dist(x, y, poly[k], poly[k + 1]) < thresh:
                return True
    return False


# ---------------------------------------------------------------- placement
def perimeter_outside(bbox, n, gap):
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    per = 2 * (bw + bh)
    pts = []
    for k in range(n):
        d = (k + random.uniform(0.18, 0.82)) / n * per
        if d < bw:
            x, y = x0 + d, y0 - 0
            nx, ny = 0, -1
        elif d < bw + bh:
            x, y = x1, y0 + (d - bw)
            nx, ny = 1, 0
        elif d < 2 * bw + bh:
            x, y = x1 - (d - bw - bh), y1
            nx, ny = 0, 1
        else:
            x, y = x0, y1 - (d - 2 * bw - bh)
            nx, ny = -1, 0
        g = gap + random.uniform(4, gap * 0.85)
        pts.append((x + nx * g + random.uniform(-10, 10), y + ny * g + random.uniform(-10, 10)))
    return pts


placed = []  # (x, y, w, h)


def in_field(x, y):
    for (x0, y0, x1, y1) in blocked_rects:
        if x0 - 16 < x < x1 + 16 and y0 - 16 < y < y1 + 16:
            return True
    cx, cy, rx, ry = HILL
    if math.hypot((x - cx) / (rx + 10), (y - cy) / (ry + 10)) < 1.0:
        return True
    cx, cy, rx, ry = POND
    if math.hypot((x - cx) / (rx + 16), (y - cy) / (ry + 16)) < 1.0:
        return True
    return False


def fits(x, y, w, h):
    if x < 70 or x > W - 70 or y < 165 or y > H - 26:
        return False
    if in_field(x, y) or near_corridor(x, y):
        return False
    r = math.hypot(w, h) / 2
    for (px, py, pw, ph) in placed:
        if math.hypot(x - px, y - py) < r + math.hypot(pw, ph) / 2 + 4:
            return False
    return True


def try_place(x, y, kind, role=None):
    w, h = (60, 40) if kind == "big" else (44, 29)   # all south-facing: long axis E-W
    if fits(x, y, w, h):
        rot = random.uniform(-5, 5)
        placed.append((x, y, w, h))
        house(x, y, w, h, kind, rot, shed=(random.random() < 0.3))
        M["houses"].append({"x": x, "y": y, "w": w, "h": h, "kind": kind, "rot": rot, "role": role})
        return True
    return False


# ---------------------------------------------------------------- water (pond + stream + channels)
pcx, pcy, prx, pry = POND
add(f'<path d="M{pcx},{pcy-pry} C{pcx-26},122 {pcx+30},80 {pcx-6},34" fill="none" stroke="#9CB4C8" stroke-width="7" opacity="0.85"/>')
add(f'<path d="M{pcx},{pcy-pry} C{pcx-26},122 {pcx+30},80 {pcx-6},34" fill="none" stroke="#5C7488" stroke-width="1" stroke-dasharray="2,4"/>')
add(f'<ellipse cx="{pcx}" cy="{pcy}" rx="{prx}" ry="{pry}" fill="#9CB4C8" stroke="#5C7488" stroke-width="2.4"/>')
add(f'<ellipse cx="{pcx}" cy="{pcy}" rx="{prx-12}" ry="{pry-10}" fill="none" stroke="#B6CAD8" stroke-width="1" opacity="0.7"/>')
for poly in (CH_MID, CH_WEST, CH_CENTRAL):
    dd = 'M' + ' L'.join(f'{x},{y}' for x, y in poly)
    add(f'<path d="{dd}" fill="none" stroke="#9CB4C8" stroke-width="4.2" opacity="0.8"/>')
M["channels"] = [{"target": nm, "poly": [[x, y] for x, y in poly]} for nm, poly in named_channels]
M["lane"] = [[x, y] for x, y in LANE]
M["pond"] = list(POND)

# ---------------------------------------------------------------- lane
dd = 'M' + ' L'.join(f'{x},{y}' for x, y in LANE)
add(f'<path d="{dd}" fill="none" stroke="#CBB178" stroke-width="16" opacity="0.65"/>')
add(f'<path d="{dd}" fill="none" stroke="#6B4F2A" stroke-width="1.4" stroke-dasharray="8,8" opacity="0.7"/>')

# ---------------------------------------------------------------- fields
paddy_field(WEST_FIELD, "WEST COMMON FIELD", "west", amp=54, taxfree=1)
paddy_field(EAST_FIELD, "CENTRAL COMMON FIELD", "central", amp=50, taxfree=2)
paddy_field(MIDNORTH, "", "midnorth", amp=30, taxfree=0)
fallow_field(SW_FIELD, "sw")
fallow_field(SE_FIELD, "se")

# ---------------------------------------------------------------- hill (grass, trees, shrine on summit, zig-zag torii)
hcx, hcy, hrx, hry = HILL
rings = [(hcx, hcy + 28, hrx, hry), (hcx, hcy, hrx * 0.76, hry * 0.76),
         (hcx, hcy - 26, hrx * 0.52, hry * 0.52), (hcx, hcy - 44, hrx * 0.30, hry * 0.32)]
M["hill"] = [rings[0][0], rings[0][1], rings[0][2], rings[0][3]]
M["summit"] = [rings[3][0], rings[3][1], rings[3][2], rings[3][3]]
for (cx, cy, rx, ry), shade in zip(rings, ['#DFD0A2', '#D8C795', '#D0BD87', '#C8B37B']):
    add(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="{shade}" stroke="#A8995F" stroke-width="1"/>')
ocx, ocy, orx, ory = rings[0]
for k in range(30):
    a = 2 * math.pi * k / 30
    ex, ey = ocx + math.cos(a) * orx, ocy + math.sin(a) * ory
    add(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex+math.cos(a)*9:.0f}" y2="{ey+math.sin(a)*9:.0f}" stroke="#A8995F" stroke-width="0.9"/>')
random.seed(4)
for _ in range(15):
    a = random.uniform(0, 2 * math.pi)
    rr = random.uniform(0.4, 0.9)
    tx = hcx + math.cos(a) * hrx * rr
    ty = (hcy + 12) + math.sin(a) * hry * rr
    add(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{random.uniform(4,6):.1f}" fill="#7E9B5C" stroke="#52663C" stroke-width="0.8"/>')
    add(f'<circle cx="{tx-1:.0f}" cy="{ty-1:.0f}" r="1.6" fill="#9DB87A"/>')
# shrine on the summit contour (innermost ring), Sister Baika's home
sx, sy = hcx, hcy - 40
add(f'<rect x="{sx-52}" y="{sy-34}" width="104" height="68" rx="3" fill="#C9876C" stroke="#6B2A18" stroke-width="2"/>')
add(f'<rect x="{sx-52}" y="{sy-34}" width="104" height="8" fill="#A03020"/>')
add(f'<rect x="{sx-52}" y="{sy+26}" width="104" height="8" fill="#A03020"/>')
add(f'<line x1="{sx-52}" y1="{sy}" x2="{sx+52}" y2="{sy}" stroke="#6B2A18" stroke-width="0.7"/>')
M["shrine"] = [sx - 52, sy - 34, 104, 68]
# winding S-curve ascent up the south face; 7 torii spread along it, none under the shrine
asc = [(1600, 748), (1470, 712), (1716, 672), (1486, 628), (1714, 600), (1556, 596), (sx, sy + 38)]


def along(pts, t):
    seg = [math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]
    tot = sum(seg)
    target, acc = t * tot, 0
    for i, sl in enumerate(seg):
        if acc + sl >= target:
            f = (target - acc) / sl
            return (pts[i][0] + (pts[i+1][0]-pts[i][0]) * f, pts[i][1] + (pts[i+1][1]-pts[i][1]) * f)
        acc += sl
    return pts[-1]


dstr = 'M' + ' L'.join(f'{x},{y}' for x, y in asc)
add(f'<path d="{dstr}" fill="none" stroke="#B89A6A" stroke-width="8" opacity="0.7"/>')
add(f'<path d="{dstr}" fill="none" stroke="#6B4F2A" stroke-width="1" stroke-dasharray="3,5"/>')
for i in range(7):
    tx, ty = along(asc, 0.06 + 0.80 * i / 6)
    M["torii"].append([round(tx, 1), round(ty, 1)])
    add(f'<g transform="translate({tx:.0f},{ty:.0f})">'
        f'<line x1="-16" y1="0" x2="16" y2="0" stroke="#A03020" stroke-width="3.6"/>'
        f'<line x1="-19" y1="-7" x2="19" y2="-7" stroke="#A03020" stroke-width="3"/>'
        f'<line x1="-12" y1="-7" x2="-12" y2="17" stroke="#A03020" stroke-width="3"/>'
        f'<line x1="12" y1="-7" x2="12" y2="17" stroke="#A03020" stroke-width="3"/></g>')

# ---------------------------------------------------------------- houses (every field ringed; all field-adjacent)
placed.append((HEADMAN[0], HEADMAN[1], 108, 68))
house(HEADMAN[0], HEADMAN[1], 108, 68, "big", 0)
M["houses"].append({"x": HEADMAN[0], "y": HEADMAN[1], "w": 108, "h": 68, "kind": "big", "rot": 0, "role": "headman"})

nbig = [0]


def ring(bbox, n, gap, kinds):
    for (x, y) in perimeter_outside(bbox, n, gap):
        k = random.choice(kinds)
        if k == "big":
            if nbig[0] >= 4:
                k = "plain"
            else:
                nbig[0] += 1
        if not try_place(x, y, k) and k == "big":
            nbig[0] -= 1


ring(WEST_FIELD, 18, 20, ["plain"] * 7 + ["big"])
ring(EAST_FIELD, 20, 20, ["plain"] * 7 + ["big"])
ring(MIDNORTH, 9, 16, ["plain"])
ring(SW_FIELD, 8, 16, ["abandoned"] * 4 + ["plain"])   # fallow -> mostly abandoned
ring(SE_FIELD, 8, 16, ["abandoned"] * 4 + ["plain"])


# ---------------------------------------------------------------- labels
def label(x, y, text, size=12, anchor="middle", italic=False, weight="normal", color="#2D2A24"):
    st = ' font-style="italic"' if italic else ''
    add(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" '
        f'font-weight="{weight}"{st} fill="{color}" paint-order="stroke" stroke="#EFE3C2" stroke-width="3">{text}</text>')


label(HEADMAN[0], 388, "Headman's House", 13, weight="bold")
label(807, 252, "small field (healthy)", 9, italic=True, color="#33301E")
label(sx, sy - 46, "Shrine to Benten", 13, weight="bold", color="#6B2A18")
label(sx, sy + 50, "Sister Baika's home", 9, italic=True, color="#6B2A18")
label(1500, 770, "7 torii - winding ascent", 11, italic=True, color="#6B2A18")
label(pcx, pcy - pry - 12, "irrigation pond", 11, italic=True, color="#5C7488")
label(pcx, pcy + 4, "(fed by the", 9, italic=True, color="#3A4A55")
label(pcx, pcy + 16, "northern stream)", 9, italic=True, color="#3A4A55")
label(345, 1030, "fallow - post-blight", 10, italic=True, color="#9C7A40")
label(1366, 1080, "fallow - post-blight", 10, italic=True, color="#9C7A40")
label(1006, 600, "Sister Baika's tax-free plots (vermillion)", 9, italic=True, color="#6B2A18")
label(305, 1120, "abandoned after the kumosaya", 10, "start", italic=True, color="#9A3A2A")

add(f'<text x="{W/2}" y="46" text-anchor="middle" font-size="30" font-weight="bold" fill="#2D2A24">Kikuta</text>')
add(f'<text x="{W/2}" y="68" text-anchor="middle" font-size="14" font-style="italic" fill="#4A4332">an average farming village - ~70 households, two common fields</text>')
add(f'<text x="{W/2}" y="86" text-anchor="middle" font-size="11" fill="#4A4332">village plan - irregular paddy basins, Benten shrine of Sister Baika on the eastern hill</text>')

add('<g transform="translate(1748,128)">'
    '<circle r="26" fill="#EFE3C2" stroke="#2D2A24" stroke-width="1.5"/>'
    '<polygon points="0,-22 5,0 0,6 -5,0" fill="#2D2A24"/>'
    '<polygon points="0,22 5,0 0,-6 -5,0" fill="#9C8C70"/>'
    '<text x="0" y="-30" text-anchor="middle" font-size="12" font-weight="bold">N</text>'
    '<text x="0" y="40" text-anchor="middle" font-size="11">S</text></g>')

# No legend: the map is self-evident, and the non-obvious things are labeled inline.

add('</svg>')
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'kikuta-village.svg'), 'w') as f:
    f.write('\n'.join(out))
with open(os.path.join(HERE, 'kikuta-village.json'), 'w') as f:
    json.dump(M, f)
print("placed houses:", len(placed))
