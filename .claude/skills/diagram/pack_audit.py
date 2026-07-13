#!/usr/bin/env python3
"""pack_audit.py - packing / whitespace report for a Mode A compound plan.

Read-only. Parses a hand-authored compound SVG and reports the numbers that make
"is there too much empty space?" objective, WITHOUT the misleading ones:

  - building-COVERAGE % of the walled interior (the historical anchor; a jin'ya
    runs ~37-42% built, the rest intentional courtyard - see buildings.md
    grounding "Packing: consolidate, don't shrink"). Coverage, NOT "total empty
    %", is the realism signal: a courtyard compound is SUPPOSED to be mostly open.
  - the largest genuinely-VACANT rectangle (+ its H/V orientation and location):
    the real "a whole region sits empty" signal. Distinguish the intentional
    forecourt / oshirasu (a feature, keep it) from undifferentiated slack.
  - ALIGNED BUILDING GAPS: pairs of buildings stacked on a shared edge with empty
    ground between them. A ~6 ft fire-gap around a plaster KURA is correct; a
    12-16 ft gap between ordinary wooden service buildings is loose slack that
    should tighten or abut into a range.

"Empty %" and "largest empty CONNECTED region" are deliberately NOT headline
numbers: the open ground is one connected blob (courtyard network), so a
connected-component count is degenerate, and a high open % is expected, not a
defect. Coverage + largest vacant RECTANGLE + aligned gaps are the actionable set.

Usage:  python3 pack_audit.py pool/<subject>.svg
"""
import re
import sys

FTPX = 3.0  # 3 px = 1 ft
INTERIOR_FILL = "url(#court-earth)"
# solid building fills
BUILDING_FILLS = {"#DDB87A", "#C9A57A", "#E8D2A8", "#F2EFE4", "#C9876C", "#B89868", "#8C6F3E"}
BUILDING_PATTERNS = {"url(#granary-slats)", "url(#colonnade-hatch)"}
KURA_FILLS = {"#F2EFE4"}  # fireproof plaster kura - a modest fire-gap IS correct here
# purposeful open features (a court/garden, NOT empty slack)
OPEN_PATTERNS = {"url(#garden-stipple)", "url(#oshirasu-sand)"}
# fills too small / incidental to be a "building" footprint (hearth, dais, clerk mats)
MIN_BLDG_AREA = 900  # px^2 = 100 sqft; below this it's furniture, not a building mass


def parse_rects(svg):
    out = []
    for m in re.finditer(
        r'<rect x="([\-\d.]+)" y="([\-\d.]+)" width="([\d.]+)" height="([\d.]+)"[^>]*?fill="([^"]+)"',
        svg,
    ):
        x, y, w, h, fill = float(m[1]), float(m[2]), float(m[3]), float(m[4]), m[5]
        out.append((x, y, w, h, fill))
    return out


def _maxrect(empty, H, W, C, minx, miny):
    """Largest all-empty axis-aligned rectangle (histogram method)."""
    height = [0] * W
    best = (0, 0, 0, 0, 0)
    for y in range(H):
        for x in range(W):
            height[x] = height[x] + 1 if empty[y][x] else 0
        st = []
        x = 0
        while x <= W:
            h = height[x] if x < W else 0
            if not st or h >= height[st[-1]]:
                st.append(x)
                x += 1
            else:
                top = st.pop()
                width = x if not st else x - st[-1] - 1
                area = height[top] * width
                if area > best[0]:
                    left = (st[-1] + 1) if st else 0
                    best = (area, left, y - height[top] + 1, width, height[top])
    a, gx, gy, gw, gh = best
    return a * C * C, gx * C + minx, gy * C + miny, gw * C, gh * C


def aligned_gaps(buildings):
    """Pairs of buildings stacked on a shared edge, with the empty gap between them.
    Returns (gap_ft, orient, mid_x, mid_y, a_is_kura, b_is_kura), largest first,
    skipping pairs whose gap-band is blocked by a third building."""
    gaps = []
    n = len(buildings)
    for i in range(n):
        ax, ay, aw, ah, af = buildings[i]
        for j in range(n):
            if i == j:
                continue
            bx, by, bw, bh, bf = buildings[j]
            # vertical stack: x-ranges overlap >= 10 ft, B below A
            ox = min(ax + aw, bx + bw) - max(ax, bx)
            if ox >= 30 and by >= ay + ah:
                g = by - (ay + ah)
                if 15 <= g <= 90:  # 5-30 ft; beyond ~30 ft it is a court, not a gap
                    xl, xr = max(ax, bx), min(ax + aw, bx + bw)
                    if not _blocked(buildings, i, j, xl, xr, ay + ah, by, vert=True):
                        gaps.append((g / FTPX, "V", (xl + xr) / 2, (ay + ah + by) / 2,
                                     af in KURA_FILLS, bf in KURA_FILLS))
            # horizontal stack: y-ranges overlap, B right of A
            oy = min(ay + ah, by + bh) - max(ay, by)
            if oy >= 30 and bx >= ax + aw:
                g = bx - (ax + aw)
                if 15 <= g <= 90:
                    yl, yr = max(ay, by), min(ay + ah, by + bh)
                    if not _blocked(buildings, i, j, ax + aw, bx, yl, yr, vert=False):
                        gaps.append((g / FTPX, "H", (ax + aw + bx) / 2, (yl + yr) / 2,
                                     af in KURA_FILLS, bf in KURA_FILLS))
    gaps.sort(reverse=True)
    # de-dup near-identical gaps (same location within ~15px)
    out = []
    for g in gaps:
        if not any(abs(g[2] - o[2]) < 15 and abs(g[3] - o[3]) < 15 for o in out):
            out.append(g)
    return out


def _blocked(buildings, i, j, lo, hi, near, far, vert):
    """Is the gap-band between building i and j occupied by a third building?"""
    for k, (kx, ky, kw, kh, kf) in enumerate(buildings):
        if k in (i, j):
            continue
        if vert:
            if kx < hi and kx + kw > lo and ky < far and ky + kh > near:
                return True
        else:
            if ky < hi and ky + kh > lo and kx < far and kx + kw > near:
                return True
    return False


def analyze(path):
    svg = open(path).read()
    rs = parse_rects(svg)
    interior = [r for r in rs if r[4] == INTERIOR_FILL]
    if not interior:
        print(f"{path}: no court-earth interior rect found")
        return
    buildings = [r for r in rs if (r[4] in BUILDING_FILLS or r[4] in BUILDING_PATTERNS)
                 and r[2] * r[3] >= MIN_BLDG_AREA]
    openf = [r for r in rs if r[4] in OPEN_PATTERNS]

    minx = min(r[0] for r in interior)
    miny = min(r[1] for r in interior)
    maxx = max(r[0] + r[2] for r in interior)
    maxy = max(r[1] + r[3] for r in interior)
    C = 2
    W = int((maxx - minx) // C) + 1
    H = int((maxy - miny) // C) + 1
    inside = [[False] * W for _ in range(H)]
    occ = [[False] * W for _ in range(H)]

    def fm(mask, r):
        x, y, w, h = r[:4]
        for gy in range(max(0, int((y - miny) // C)), min(H, int((y - miny + h) // C) + 1)):
            for gx in range(max(0, int((x - minx) // C)), min(W, int((x - minx + w) // C) + 1)):
                mask[gy][gx] = True

    for r in interior:
        fm(inside, r)
    for r in buildings + openf:
        fm(occ, r)
    for m in re.finditer(r'<ellipse cx="([\d.]+)" cy="([\d.]+)" rx="([\d.]+)" ry="([\d.]+)"', svg):
        cx, cy, rx, ry = map(float, m.groups())
        fm(occ, (cx - rx, cy - ry, 2 * rx, 2 * ry))

    empty = [[inside[y][x] and not occ[y][x] for x in range(W)] for y in range(H)]
    tot_in = sum(sum(r) for r in inside) * C * C
    tot_bld = sum(r[2] * r[3] for r in buildings)
    tot_open = sum(r[2] * r[3] for r in openf)
    tot_empty = sum(sum(r) for r in empty) * C * C
    a, rx, ry, rw, rh = _maxrect(empty, H, W, C, minx, miny)
    gaps = aligned_gaps(buildings)

    f2 = FTPX * FTPX
    print(f"=== {path.split('/')[-1]} ===")
    print(f"walled interior: {(maxx-minx)/FTPX:.0f} x {(maxy-miny)/FTPX:.0f} ft = {tot_in/f2:,.0f} sqft")
    print(f"building coverage: {100*tot_bld/tot_in:.0f}%   (jin'ya band ~37-42%; <35% sparse, >50% cramped)")
    print(f"purposeful open (garden + hearing court + pond): {100*tot_open/tot_in:.0f}%   (forecourt/oshirasu are a FEATURE)")
    print(f"bare open ground: {100*tot_empty/tot_in:.0f}%   (NOT a defect by itself - courts are open)")
    print(f"largest VACANT rectangle: {rw/FTPX:.0f} x {rh/FTPX:.0f} ft ({a/f2:,.0f} sqft) [{'horizontal' if rw>rh else 'vertical'}] at svg({rx:.0f},{ry:.0f})")
    print(f"    ^ is this the forecourt/oshirasu (feature) or undifferentiated slack? judge by location.")
    print(f"aligned building gaps 5-30 ft (stacked buildings with empty between; largest first):")
    print(f"    (fire-gap around a plaster KURA is OK to ~10 ft; a wooden-to-wooden gap >8 ft is loose slack -> abut/tighten)")
    if not gaps:
        print("    (none in the 5-30 ft range)")
    for g, orient, mx, my, ak, bk in gaps[:12]:
        if ak or bk:
            tag = "fire-gap OK (kura)" if g <= 10 else "LOOSE (kura gap >10 ft)"
        else:
            tag = "tight" if g <= 8 else "LOOSE (wooden >8 ft)"
        print(f"    {g:4.1f} ft  {orient}  at svg({mx:.0f},{my:.0f})   {tag}")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["pool/ochiba-magistracy.svg", "pool/hayakawa-magistracy.svg"]:
        analyze(p)
        print()
