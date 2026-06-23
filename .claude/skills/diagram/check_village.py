#!/usr/bin/env python3
"""Automated checks for a Mode B settlement-map manifest (diagram skill).

Reads the JSON manifest the generator emits and asserts the Mode B rules. The
UNIVERSAL invariants (no overlaps, houses off corridors and field-adjacent, every
field ringed, no cultivation on a hill, houses face south, headman largest,
channels anchored at both ends and gently winding) are always checked. The
VILLAGE-SPECIFIC expectations are read from manifest["meta"] and from each
channel's frm/to anchors, so this validator works for any village/hamlet rather
than assuming one village's layout. Exit 0 if all pass, 1 otherwise.

The skill's plain-English / persona review still applies on top of this gate -
and remember a green check on the wrong geometry is worse than no check, so the
manifest records the *rendered* (smoothed) boundary and you still eyeball a crop.
"""
import json
import math
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def rect_corners(h):
    a = math.radians(h["rot"])
    ca, sa = math.cos(a), math.sin(a)
    w, ht = h["w"], h["h"]
    return [(h["x"] + dx * ca - dy * sa, h["y"] + dx * sa + dy * ca)
            for dx, dy in [(-w / 2, -ht / 2), (w / 2, -ht / 2), (w / 2, ht / 2), (-w / 2, ht / 2)]]


def sat_overlap(p, q):
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


def seg_closest(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px, py, a, b):
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


# the 2 patron fortunes of each Great Clan - a town defaults to one monastery for each
CLAN_FORTUNES = {
    "crab": {"Bishamon", "Ebisu"}, "crane": {"Benten", "Daikoku"},
    "dragon": {"Hotei", "Ebisu"}, "lion": {"Bishamon", "Daikoku"},
    "phoenix": {"Fukurokujin", "Hotei"}, "scorpion": {"Benten", "Jurojin"},
    "unicorn": {"Fukurokujin", "Jurojin"},
}


def unit_dir(spec):
    """A cardinal name or [dx,dy] vector -> a unit vector in map coords (+y=south). None if bad."""
    DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0),
            "northeast": (0.7071, -0.7071), "northwest": (-0.7071, -0.7071),
            "southeast": (0.7071, 0.7071), "southwest": (-0.7071, 0.7071)}
    if spec is None:
        return None
    if isinstance(spec, str):
        return DIRS.get(spec.lower())
    dl = math.hypot(spec[0], spec[1]) or 1
    return (spec[0] / dl, spec[1] / dl)


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


def poly_dist(px, py, poly):
    if point_in_poly(px, py, poly):
        return 0.0
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def edge_dist(px, py, poly):
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def in_ellipse(px, py, e, scale=1.0):
    cx, cy, rx, ry = e
    return ((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0


def polyline_len(poly):
    return sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))


def clip_poly_rect(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a polygon to an axis rect; returns the clipped polygon (may be []).
    Used to find how much of an off-edge field actually shows inside the rendered map window."""
    def cl(pts, ins, isc):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            ia, ib = ins(a), ins(b)
            if ia:
                out.append(a)
            if ia != ib:
                out.append(isc(a, b))
        return out
    p = list(poly)
    for ins, isc in (
        (lambda q: q[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / ((b[0] - a[0]) or 1e-9))),
        (lambda q: q[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / ((b[0] - a[0]) or 1e-9))),
        (lambda q: q[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / ((b[1] - a[1]) or 1e-9), y0)),
        (lambda q: q[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / ((b[1] - a[1]) or 1e-9), y1)),
    ):
        if not p:
            return []
        p = cl(p, ins, isc)
    return p


def onmap_field_edge(poly, x0, y0, x1, y1, eps=8):
    """Length of a field's REAL boundary lying inside the map rect - EXCLUDING the segments that run
    along the rect edge (those are the off-map cut, where the field's farmhouses are off-screen).
    This is the on-map field frontage that ought to carry farmhouses."""
    cp = clip_poly_rect(poly, x0, y0, x1, y1)
    if len(cp) < 2:
        return 0.0
    total = 0.0
    for i in range(len(cp)):
        a, b = cp[i], cp[(i + 1) % len(cp)]
        on_rect = ((abs(a[0] - x0) < eps and abs(b[0] - x0) < eps) or (abs(a[0] - x1) < eps and abs(b[0] - x1) < eps)
                   or (abs(a[1] - y0) < eps and abs(b[1] - y0) < eps) or (abs(a[1] - y1) < eps and abs(b[1] - y1) < eps))
        if not on_rect:
            total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def footprint_on_line(sc, sp, hw):
    """True if closed polygon sc overlaps polyline sp within half-width hw - a corner near a
    segment, a polyline vertex inside the polygon, or an edge crossing. sc may be a 4-corner
    building footprint OR a field outline. Used to test a footprint/field against a barrier
    (city wall stroke, moat)."""
    if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
        return True
    if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
        return True
    return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % len(sc)])
               for k in range(len(sp) - 1) for e in range(len(sc)))


def empty_street_runs(M, w, maxgap=130):
    """Stretches of town/city street INSIDE the wall `w` longer than `maxgap` with no building
    FRONTING them. A building serves only the street it actually fronts (its nearest, within the
    frontage band), so one beside a perpendicular cross-street can't paper over an empty stub on
    the lane. Returns [(label, run_px), ...] - a street earns its length from what it serves."""
    streets = M.get("town_streets", [])
    if not (streets and len(w) >= 3):
        return []
    # houses and shops front streets, but so do the CIVIC buildings - a government avenue lined
    # with ministries (or the governor's yamen, a temple) is serving those, not running empty
    blds = M.get("buildings", []) + M.get("houses", []) + M.get("ministries", []) + M.get("religious", []) + M.get("flophouses", [])
    if M.get("governor_mansion"):
        blds = blds + [M["governor_mansion"]]
    lines = [st["pts"] for st in streets]
    # a building cannot FRONT a street it is walled off from: if a ward fence or the city wall lies
    # between the building and the point it would front, it serves some OTHER side, not this street.
    # (Without this, the gap-band housing across a ward fence papered over a bare government avenue -
    # the avenue read as "served by houses" that were actually on the far side of the fence.)
    barriers = [wd["boundary"] for wd in M.get("wards", [])] + [list(w)]

    def walled_off(bx, by, fx, fy):
        return any(segments_cross((bx, by), (fx, fy), tuple(bar[i]), tuple(bar[i + 1]))
                   for bar in barriers for i in range(len(bar) - 1))
    FRONT, COVER, STEP = 95, 105, 25
    fronts = {}
    for b in blds:
        best, bi, bfoot = FRONT, None, None
        for i, sp in enumerate(lines):
            for k in range(len(sp) - 1):
                dd = seg_dist(b["x"], b["y"], sp[k], sp[k + 1])
                if dd < best:
                    best, bi = dd, i
                    bfoot = seg_closest(b["x"], b["y"], sp[k], sp[k + 1])
        if bi is not None and not walled_off(b["x"], b["y"], bfoot[0], bfoot[1]):
            fronts.setdefault(bi, []).append(b)
    empty = []
    for si, st in enumerate(streets):
        pts = st["pts"]
        servers = fronts.get(si, [])
        run = worst = 0
        for k in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            steps = max(1, int(math.hypot(bx - ax, by - ay) // STEP))
            for j in range(steps):
                t = j / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                if not point_in_poly(x, y, w):
                    run = 0
                elif any((b["x"] - x) ** 2 + (b["y"] - y) ** 2 < COVER * COVER for b in servers):
                    run = 0
                else:
                    run += STEP
                    worst = max(worst, run)
        if worst > maxgap:
            empty.append(("main" if st.get("main") else f"@{pts[0]}", worst))
    return empty


def approach_span(mx, my, half, ux, uy, M, w, Wd, Hd):
    """March from a religious hall's front edge along (ux, uy) to the first HARD terminus - a
    town street, a field/flower-field, the rampart, or the map edge - and return the clear
    length. Buildings are deliberately NOT termini: a torii avenue is a cleared processional way
    (sando) that displaces dwellings, so its length is set by the public street or barrier it
    reaches, not by whatever housing it pushes aside. Used to size a monastery's torii avenue."""
    fields = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("flower_fields", [])]
    streets = [(st["pts"], st.get("w", 24)) for st in M.get("town_streets", [])]
    start = half + 12
    s = start
    while s < start + 600:
        px, py = mx + ux * s, my + uy * s
        if not (0 <= px <= Wd and 0 <= py <= Hd):
            break
        if w and not point_in_poly(px, py, w):
            break
        if any(point_in_poly(px, py, fp) for fp in fields):
            break
        if any(seg_dist(px, py, pts[k], pts[k + 1]) < sw / 2 + 4
               for pts, sw in streets for k in range(len(pts) - 1)):
            break
        s += 10
    return s - start


DEFAULT_MANIFEST = {
    "houses": [], "fields": [], "fallow_patches": [], "channels": [], "lane": [],
    "taxfree": [], "torii": [], "shrines": [], "manors": [], "streams": [],
    "buildings": [], "pastures": [], "forest_patches": [], "religious": [],
    "flower_fields": [], "labels": [], "town_streets": [], "gate_structs": [],
    "pond": None, "hill": None, "summit": None, "shrine": None, "forest": None,
    "storehouses": [], "flophouses": [], "road": None, "wall": None, "gate": None,
    "gates": [], "moat": None, "governor_mansion": None, "ministries": [],
    "inspection_stations": [], "amphitheater": None, "granary": None, "meta": {},
}


# a building's role for the population/frontage maths. A DWELLING houses one ~5-person household;
# a BUSINESS is a commercial frontage (the merchant's house+shop is BOTH - dual-use); everything
# else (civic, government, granary kura, barns, gate furniture) houses no one and fronts nothing.
DWELLING_KINDS = {"laborer", "servant", "burakumin", "samurai", "merchant", "merchant_house", "merchant_large"}
BUSINESS_KINDS = {"shop", "merchant"}
HOUSEHOLD = 5


def gate(M, verbose=True):
    """Run every check over a manifest dict M and return the list of FAILED check names.
    verbose prints the PASS/FAIL lines. Pass a synthetic M to unit-test a single check."""
    # tolerate sparse synthetic manifests (unit tests build only the keys a check needs)
    M = {**DEFAULT_MANIFEST, **M}
    meta = M.get("meta", {})
    scale = meta.get("scale", "village")
    houses, fields = M["houses"], M["fields"]
    field_by = {f["name"]: f for f in fields}
    Wd, Hd = meta.get("W", 1820), meta.get("H", 1180)
    # the "map edge" is the rendered window: the cropped view if one is set (city maps crop tight
    # to the walls and let the countryside run off), else the full canvas.
    _vw = meta.get("view")
    EX0, EY0, EX1, EY1 = (_vw[0], _vw[1], _vw[0] + _vw[2], _vw[1] + _vw[3]) if _vw else (0, 0, Wd, Hd)
    fails = []

    def check(name, ok, detail=""):
        if verbose:
            print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
        if not ok:
            fails.append(name)

    # population is DWELLINGS x ~5, NEVER total buildings: a town/city's shops, government
    # offices, flophouses, kura and gate furniture house no one, so counting them as housing
    # would inflate the population. Farmhouses + urban dwellings are the only residences.
    if scale in ("town", "city") and meta.get("population"):
        # a CITY's declared population (~3,000) is its URBAN castes ONLY - servants, laborers, merchants,
        # burakumin, samurai (budgets.md caste tables list ZERO farmers for a city). FARMERS do not count
        # at all: not the surrounding villagers, and not even the unusual IN-WALL agricultural district's
        # farmers - so a city's farmhouses (M["houses"]) are excluded entirely from the figure. A TOWN's
        # depicted farmhouses ARE its (partial) county farmer cohort, so they DO count there.
        urban = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS)
        dwellings = urban if scale == "city" else len(houses) + urban
        est = dwellings * HOUSEHOLD
        pop = meta["population"]
        tol = meta.get("population_tol", 0.07)   # the map should DELIVER the declared figure, not merely be in a wide band
        farm_note = "" if scale == "city" else "farmhouses + "
        check("population_consistent_with_housing", abs(est - pop) <= tol * pop,
              f"{dwellings} dwellings x{HOUSEHOLD} = ~{est} residents, but meta population is {pop} "
              f"(>{tol:.0%} off) - count ONLY dwellings ({farm_note}laborer/servant/burakumin/samurai/merchant), "
              f"never the shops, government offices, flophouses, kura, gate furniture{' or any farmhouses (city farmers are not in the ~3,000)' if scale == 'city' else ''}; "
              f"place enough dwellings to hit the declared figure")

    # ALMOST all shops front a street (commerce wants the street); POOR housing (laborer/burakumin)
    # mostly packs the block INTERIOR, reached by alleys, not the paved street frontage. (The towns
    # set the template: businesses on the frontage via s.frontage, dwellings interior via s.pack.)
    if scale in ("town", "city"):
        st_lines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])

        def on_a_street(b):
            return any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < 85 for sp in st_lines for i in range(len(sp) - 1))
        biz = [b for b in M.get("buildings", []) if b.get("kind") in BUSINESS_KINDS]
        if biz:
            off = [b for b in biz if not on_a_street(b)]
            check("businesses_front_streets", len(off) <= 0.15 * len(biz),
                  f"{len(off)}/{len(biz)} shops/merchant houses are NOT on a street - almost every business fronts a street (the more mercantile a quarter, the more streets); only dwellings fill the block interior")
        poor = [b for b in M.get("buildings", []) if b.get("kind") in ("laborer", "burakumin")]
        if poor:
            onst = [b for b in poor if on_a_street(b)]
            check("poor_housing_mostly_interior", len(onst) <= 0.5 * len(poor),
                  f"{len(onst)}/{len(poor)} laborer/burakumin dwellings sit ON a street - most poor housing jams the block INTERIOR (reached by alleys), behind the street-facing businesses")
        # surrounding farmland must be WORKED: the part of each outside field that SHOWS on the map
        # carries farmhouses at roughly the village/hamlet linear density (~12 per 1000px of field edge,
        # min ~4). Off-map field portions have their farmhouses off-screen (fine, expected), but a field
        # presenting a real on-map edge with almost no farmhouses beside it is wrong - farmers build
        # close to the fields they work. We count only IN-VIEW houses against the on-map field edge, so
        # a partially-rendered field is held to its SHOWN extent (the gap the old per-field >=2 missed).
        ADJ = 165
        FARM_LD = 7.0   # houses per 1000px of shown edge - a floor: village fields run ~4-19, the bad ones ~0
        sparse = []
        for f in fields:
            cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
            if M.get("wall") and point_in_poly(cx, cy, M["wall"]):
                continue                                   # in-wall plots are not surrounding farmland
            edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
            if edge < 120:
                continue                                   # only a tiny sliver shows - too little to require farmhouses
            nv = sum(1 for h in houses if EX0 <= h["x"] <= EX1 and EY0 <= h["y"] <= EY1
                     and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
            if nv < FARM_LD * edge / 1000:
                sparse.append((f["name"], nv, round(FARM_LD * edge / 1000, 1)))
        check("outside_fields_farmhouse_density", not sparse,
              f"shown field edge(s) with too few farmhouses beside the on-map portion (farmers build close; expect ~village density): {sparse}")
        # the IN-WALL agricultural district (the unusual city that farms inside its walls) is REAL
        # farmland too. Unlike the SURROUNDING fields above - mostly off the cropped map, so only a
        # FLOOR (7) is enforceable on their shown sliver - an in-wall field sits ENTIRELY in view, so
        # its WHOLE perimeter must read as worked: ring it DENSELY all the way round, not a sparse few
        # on one side leaving long bare edges. Held to a much higher density (the dense end of village
        # ringing). Only bites when meta(agricultural_district=True) - most cities have no in-wall fields.
        FARM_LD_INWALL = 16.0   # houses per 1000px of edge - a full, all-round ring, not the off-map floor
        if scale == "city" and meta.get("agricultural_district") and M.get("wall"):
            thin = []
            for f in fields:
                cx, cy = (f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2
                if not point_in_poly(cx, cy, M["wall"]):
                    continue                               # only the in-wall plots
                edge = onmap_field_edge(f["outline"], EX0, EY0, EX1, EY1)
                if edge < 120:
                    continue
                nv = sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
                if nv < FARM_LD_INWALL * edge / 1000:
                    thin.append((f["name"], nv, round(FARM_LD_INWALL * edge / 1000, 1)))
            check("city_interior_fields_farmhouse_density", not thin,
                  f"in-wall agricultural field(s) too sparsely farmed - an in-wall field shows its WHOLE perimeter, "
                  f"so ring it densely all the way round (no long bare edges), not a token few: {thin}")
        # housing packs DEEP, but no GIANT cluster may be cut off from circulation: a big block of
        # dwellings with no street OR alley anywhere near it has no way in or out. Deep blocks must
        # be laced with gravel alleys (s.alley) so every dwelling is reachable.
        acc = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])]

        def cut_off(b):
            return not any(seg_dist(b["x"], b["y"], ln[i], ln[i + 1]) < 95 for ln in acc for i in range(len(ln) - 1))
        iso = [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS and cut_off(b)]
        seen, biggest = set(), 0
        for i in range(len(iso)):
            if i in seen:
                continue
            stack, n = [i], 0
            seen.add(i)
            while stack:
                j = stack.pop()
                n += 1
                for k in range(len(iso)):
                    if k not in seen and abs(iso[j]["x"] - iso[k]["x"]) < 46 and abs(iso[j]["y"] - iso[k]["y"]) < 46:
                        seen.add(k)
                        stack.append(k)
            biggest = max(biggest, n)
        check("no_isolated_dwelling_cluster", biggest <= 30,
              f"a contiguous cluster of {biggest} dwellings sits >95px from any street OR alley - a giant block of houses with no way in or out; lace deep blocks with gravel alleys (s.alley) so every block is reachable")
        # an alley must EARN its length by UNIQUELY serving dwellings. A building is credited to its
        # NEAREST lane only (the one it actually fronts), exactly as empty_street_runs scores streets -
        # so a lane counts only what no other lane already reaches. This catches BOTH a lane running off
        # into a half-empty corner (a "lane to nowhere") AND a redundant lane laid beside or across one
        # that already serves the same block (a perpendicular arm the block's spine already reaches, or a
        # second lane shadowing a parallel street). Scaled to the buildings (~1 dwelling per 30px of its
        # own length), so it holds at the city's dense small-footprint grain, not a fixed town pixel gap.
        alley_blds = M.get("buildings", []) + M.get("houses", [])
        alleys = [a["pts"] for a in M.get("alleys", [])]
        other = [s["pts"] for s in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])

        def lane_dist(b, pts):
            return min(seg_dist(b["x"], b["y"], pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        uniq = [0] * len(alleys)
        for b in alley_blds:
            best_d, best_i = 60.0, None       # only buildings within a frontage band count for any lane
            for li, pts in enumerate(alleys):
                d = lane_dist(b, pts)
                if d < best_d:
                    best_d, best_i = d, li
            if best_i is None:
                continue
            if all(lane_dist(b, pts) > best_d for pts in other):   # no street/road is closer - this alley owns it
                uniq[best_i] += 1
        thin = []
        for li, pts in enumerate(alleys):
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            if uniq[li] * 30 < length:
                thin.append((pts[0], uniq[li], round(length)))
        check("alleys_serve_buildings", not thin,
              f"alley(s) that uniquely serve too few dwellings to justify their length - a lane to nowhere or a redundant lane beside/across one that already serves the block (need ~1 uniquely-served dwelling per 30px): {thin}")

    # ---- universal invariants ------------------------------------------------
    # standalone civic buildings (flophouse, granary kura) are checked for overlaps exactly like
    # houses and shops - they must not sit on a road / stream / wall / street / channel, or on
    # each other / the manor / a hall. (Merchant storehouses are NOT here: they are drawn as
    # annexes deliberately abutting their shop, so they would trip the structure-overlap test.)
    granary = M.get("granary")
    structs = houses + M.get("buildings", []) + M.get("flophouses", []) + (granary["stores"] if granary else [])
    corners = [rect_corners(s) for s in structs]
    bad = [(i, j) for i in range(len(structs)) for j in range(i + 1, len(structs))
           if math.hypot(structs[i]["x"] - structs[j]["x"], structs[i]["y"] - structs[j]["y"]) <= 110
           and sat_overlap(corners[i], corners[j])]
    check("no_structure_overlaps", not bad, f"{len(bad)} overlapping structure pair(s)")

    # no structure overlaps the magistrate's manor walls (an ellipse block undershot the corners)
    bad_m = []
    for mn in M.get("manors", []):
        mx, my, mw, mh = mn["x"], mn["y"], mn["w"], mn["h"]
        e = 4   # wall thickness
        mc = [(mx - mw / 2 - e, my - mh / 2 - e), (mx + mw / 2 + e, my - mh / 2 - e),
              (mx + mw / 2 + e, my + mh / 2 + e), (mx - mw / 2 - e, my + mh / 2 + e)]
        bad_m += [1 for sc in corners if sat_overlap(sc, mc)]
    check("no_structure_on_manor", not bad_m, f"{len(bad_m)} structure(s) overlap the manor walls")

    def rect_corners_xywh(item, e):
        cx, cy, w, h = item["x"], item["y"], item["w"], item["h"]
        return [(cx - w / 2 - e, cy - h / 2 - e), (cx + w / 2 + e, cy - h / 2 - e),
                (cx + w / 2 + e, cy + h / 2 + e), (cx - w / 2 - e, cy + h / 2 + e)]

    # no structure overlaps a religious hall (an ellipse block undershot its corners)
    bad_rel = [1 for rel in M.get("religious", []) for sc in corners
               if sat_overlap(sc, rect_corners_xywh(rel, 4))]
    check("no_structure_on_religious", not bad_rel, f"{len(bad_rel)} structure(s) overlap a religious hall")

    # no structure overlaps the gate's guard station / guardtower
    bad_g = [1 for gs in M.get("gate_structs", []) for sc in corners
             if sat_overlap(sc, rect_corners_xywh(gs, 2))]
    check("no_structure_on_gate", not bad_g, f"{len(bad_g)} structure(s) overlap the gate guard station/tower")

    # no structure overlaps a torii arch (footprint ~38x28, centerd just below the post tops)
    bad_t = [1 for t in M.get("torii", []) for sc in corners
             if sat_overlap(sc, [(t[0] - 19, t[1] - 10), (t[0] + 19, t[1] - 10), (t[0] + 19, t[1] + 18), (t[0] - 19, t[1] + 18)])]
    check("no_structure_on_torii", not bad_t, f"{len(bad_t)} structure(s) overlap a torii arch")

    # roads/streets are a GROUND layer: a gatehouse or label that legitimately sits on a road
    # must be drawn ON TOP of it (higher draw-order z), never have the road painted over it.
    road_layers = []
    if M.get("road") is not None and M.get("road_z") is not None:
        road_layers.append((M["road"], M["road_z"], M.get("road_width", 26) / 2))
    road_layers += [(st["pts"], st["z"], st["w"] / 2) for st in M.get("town_streets", []) if "z" in st]
    overlays = [("label", lab[:4], lab[4]) for lab in M.get("labels", []) if len(lab) > 4]
    overlays += [("gatehouse", (gs["x"] - gs["w"] / 2, gs["y"] - gs["h"] / 2, gs["x"] + gs["w"] / 2, gs["y"] + gs["h"] / 2), gs["z"])
                 for gs in M.get("gate_structs", []) if "z" in gs]

    def line_hits_box(poly, box, pad):
        bx0, by0, bx1, by1 = box
        for k in range(len(poly) - 1):
            (ax, ay), (bx, by) = poly[k], poly[k + 1]
            steps = max(1, int(math.hypot(bx - ax, by - ay) // 8))
            for j in range(steps + 1):
                t = j / steps
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                if bx0 - pad <= px <= bx1 + pad and by0 - pad <= py <= by1 + pad:
                    return True
        return False

    bad_z = [name for poly, rz, hw in road_layers for name, box, oz in overlays
             if rz > oz and line_hits_box(poly, box, hw)]
    check("roads_drawn_under_overlays", not bad_z, f"{len(bad_z)} road/street drawn OVER a gatehouse/label it should pass under: {sorted(set(bad_z))}")

    # LANE LAYERING: where two linear ground features cross, the WIDER renders on top (higher draw z).
    # The Imperial road is painted over the city streets it crosses, streets over the alleys they cross.
    # z is the recorded final draw position (settlement flushes road/street/alley as one ordered block).
    lanes = []
    if M.get("road") and M.get("road_z") is not None:
        lanes.append(("road", M["road"], M.get("road_width", 26), M["road_z"]))
    lanes += [("street", st["pts"], st["w"], st["z"]) for st in M.get("town_streets", []) if st.get("z") is not None]
    lanes += [("alley", a["pts"], a.get("w", 10), a["z"]) for a in M.get("alleys", []) if a.get("z") is not None]

    def lanes_cross(pi, pj):
        return any(segments_cross(pi[a], pi[a + 1], pj[b], pj[b + 1])
                   for a in range(len(pi) - 1) for b in range(len(pj) - 1))
    mislayered = []
    for i in range(len(lanes)):
        for j in range(i + 1, len(lanes)):
            ni, pi, wi, zi = lanes[i]
            nj, pj, wj, zj = lanes[j]
            if abs(wi - wj) < 1 or not lanes_cross(pi, pj):
                continue                  # same width (either order ok) or they don't cross
            wider, narrower = ((ni, zi), (nj, zj)) if wi > wj else ((nj, zj), (ni, zi))
            if wider[1] < narrower[1]:
                mislayered.append(f"{narrower[0]} over {wider[0]}")
    check("city_lanes_layered_by_width", not mislayered,
          f"a narrower lane is painted OVER a wider one it crosses (the wider lane must be on top): {sorted(set(mislayered))}")
    # and where a street/road crosses the city WALL away from a gate, it runs UNDER the rampart (the
    # wall is painted on top). A lane should only breach the wall at a gate; elsewhere the wall wins.
    wall, wall_z = M.get("wall"), M.get("wall_z")
    gates = M.get("gates") or ([M["gate"]] if M.get("gate") else [])
    if wall and wall_z is not None and len(wall) >= 3:
        ring = list(wall) + [wall[0]]
        over_wall = []
        for name, pts, w, z in lanes:
            for a in range(len(pts) - 1):
                for b in range(len(ring) - 1):
                    if segments_cross(pts[a], pts[a + 1], ring[b], ring[b + 1]):
                        xy = seg_intersect(pts[a], pts[a + 1], ring[b], ring[b + 1])
                        if xy and all(math.hypot(xy[0] - gx, xy[1] - gy) > 55 for gx, gy in gates) and z > wall_z:
                            over_wall.append(name)
        check("city_lane_under_wall", not over_wall,
              f"a street/road crosses the wall away from a gate and renders OVER it (a lane must run UNDER the rampart): {sorted(set(over_wall))}")

    # no structure overlaps the (wide) road
    road = M.get("road")
    if road:
        rw = M.get("road_width", 26) / 2 + 2     # roadbed half-width + a little

        def on_road(sc):
            if any(seg_dist(cx, cy, road[k], road[k + 1]) < rw for (cx, cy) in sc for k in range(len(road) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for (rx, ry) in road):
                return True
            return any(segments_cross(road[k], road[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(road) - 1) for e in range(4))
        bad_r = [1 for sc in corners if on_road(sc)]
        check("no_structure_on_road", not bad_r, f"{len(bad_r)} structure(s) overlap the road")

    # no structure overlaps a stream
    streams = M.get("streams", [])
    if streams:
        srw = 6   # stream half-width + a little

        def on_stream(sc, sp):
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < srw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(sp) - 1) for e in range(4))
        bad_s = [1 for sc in corners for st in streams if on_stream(sc, st["poly"])]
        check("no_structure_on_stream", not bad_s, f"{len(bad_s)} structure(s) overlap a stream")

    # no structure overlaps an irrigation channel - the SAME full-footprint test as a stream.
    # (houses_off_corridors below also touches channels, but only by house CENTER distance, so a
    # channel clipping a farmhouse's corner while its center stayed clear used to slip through.)
    channels_struct = M.get("channels", [])
    if channels_struct:
        crw = 5   # channel half-width (stroke ~4.2 -> ~2.1) + a little: a corner this close is on it

        def on_channel(sc, sp):
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < crw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(sp) - 1) for e in range(4))
        bad_c = [1 for sc in corners for c in channels_struct if on_channel(sc, c["poly"])]
        check("no_structure_on_channel", not bad_c, f"{len(bad_c)} structure(s) overlap an irrigation channel")

    # no structure overlaps the town wall (the thick rampart stroke)
    wallpts = M.get("wall")
    if wallpts:
        ww = 9   # wall half-width (stroke ~10) + a little

        def on_wall(sc):
            if any(seg_dist(cx, cy, wallpts[k], wallpts[k + 1]) < ww for (cx, cy) in sc for k in range(len(wallpts) - 1)):
                return True
            if any(point_in_poly(wx, wy, sc) for wx, wy in wallpts):
                return True
            return any(segments_cross(wallpts[k], wallpts[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(wallpts) - 1) for e in range(4))
        bad_w = [1 for sc in corners if on_wall(sc)]
        check("no_structure_on_wall", not bad_w, f"{len(bad_w)} structure(s) overlap the town wall")

    # no structure overlaps a street OR an alley (a paved lane or a gravel alley running over a
    # house is wrong) - alleys are drawn last, so a careless alley can be laid across a building
    tstreets = M.get("town_streets", [])
    lanes = tstreets + [{"pts": a["pts"], "w": a.get("w", 10)} for a in M.get("alleys", [])]
    if lanes:
        def on_street(sc, sp, hw):
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(sp) - 1) for e in range(4))
        bad_ts = [1 for sc in corners for st in lanes if on_street(sc, st["pts"], st.get("w", 24) / 2 + 2)]
        check("no_structure_on_street", not bad_ts, f"{len(bad_ts)} structure(s) overlapped by a street/alley")

    # ---- street-faced town layout: businesses front the streets (and face them); housing
    # sits back off the main commercial street. The "streets" are the town streets plus any
    # road (an unwalled town's road is its high street).
    street_lines = [st["pts"] for st in M.get("town_streets", [])]
    main_idx = next((i for i, st in enumerate(M.get("town_streets", [])) if st.get("main")), None)
    if M.get("road"):
        street_lines.append([list(p) for p in M["road"]])
        if main_idx is None:
            main_idx = len(street_lines) - 1
    if scale == "town" and street_lines and M.get("buildings"):
        def closest_on_line(px, py, sp):
            best, bd = None, 1e18
            for k in range(len(sp) - 1):
                cx, cy = seg_closest(px, py, sp[k], sp[k + 1])
                d = math.hypot(cx - px, cy - py)
                if d < bd:
                    bd, best = d, (cx, cy)
            return bd, best

        BUSINESS, HOUSING = {"shop", "merchant"}, {"laborer", "servant"}
        FRONT = 92                       # within this of a street = "fronting" it
        biz_off, off_face, house_front = [], [], []
        for b in M["buildings"]:
            kind = b["kind"]
            per = [(closest_on_line(b["x"], b["y"], sp), li) for li, sp in enumerate(street_lines)]
            (dmin, cpmin), limin = min(per, key=lambda r: r[0][0])
            if kind in BUSINESS and dmin > FRONT:
                biz_off.append(kind)
            if dmin <= FRONT and kind in (BUSINESS | HOUSING):
                th = math.radians(b.get("rot", 0))
                fx, fy = -math.sin(th), math.cos(th)              # frontage normal
                # a corner building may face any street it fronts, not only the nearest
                aligns = []
                for (d, cp), _ in per:
                    if d <= FRONT and cp:
                        dl = math.hypot(cp[0] - b["x"], cp[1] - b["y"]) or 1
                        aligns.append((fx * (cp[0] - b["x"]) + fy * (cp[1] - b["y"])) / dl)
                if aligns and max(aligns) < 0.5:                  # > 60 deg off every nearby street
                    off_face.append(kind)
            if kind in HOUSING and limin == main_idx and dmin <= FRONT:
                house_front.append(kind)
        check("businesses_front_streets", not biz_off, f"{len(biz_off)} business(es) not fronting any street")
        check("buildings_face_street", not off_face, f"{len(off_face)} street-fronting building(s) not facing any street it fronts")
        check("housing_off_main_street", not house_front, f"{len(house_front)} dwelling(s) on the main street frontage (housing belongs set back)")

    corr = ([M["lane"]] if M.get("lane") else []) + [c["poly"] for c in M["channels"]]
    onroad = sum(1 for h in houses for poly in corr
                 if any(seg_dist(h["x"], h["y"], poly[k], poly[k + 1]) < 14 for k in range(len(poly) - 1)))
    check("houses_off_corridors", onroad == 0, f"{onroad} house-on-corridor hit(s)")

    ADJ = 165
    far = [h for h in houses if h.get("role") != "headman"
           and min((poly_dist(h["x"], h["y"], f["outline"]) for f in fields), default=999) > ADJ]
    check("all_houses_field_adjacent", not far, f"{len(far)} house(s) >{ADJ}px from any field")
    def runs_off_edge(ol):
        return any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in ol)

    for f in fields:
        if runs_off_edge(f["outline"]):
            continue   # a field running off the map has its farmhouses implied off-map too
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")

    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")

    headman = next((h for h in houses if h.get("role") == "headman"), None)
    if scale == "village":
        check("village_has_headman", headman is not None, "a village must have a headman")
    else:
        # hamlets fall under the village district headman; towns are run by the magistrate
        check(f"{scale}_has_no_headman", headman is None, f"a {scale} has no peasant headman of its own")

    # religious building by settlement scale: hamlet none, village shrine, town
    # monastery, city temple
    expected_rel = {"hamlet": None, "village": "shrine", "town": "monastery", "city": "temple"}.get(scale)
    rel_kinds = set(r["kind"] for r in M.get("religious", [])) - {"small_shrine"}   # small wayside shrines are auxiliary, allowed alongside the scale's main religious building
    if expected_rel is None:
        check("religious_matches_scale", not rel_kinds, f"a {scale} should have no religious building (found {rel_kinds or 'none'})")
    else:
        check("religious_matches_scale", rel_kinds == {expected_rel},
              f"a {scale} should have only {expected_rel}(s); found {rel_kinds or 'none'}")
    # a religious building's subtitle must not RESTATE its type (the label already names it,
    # e.g. "Monastery of Tengen" needs no "(town monastery)" note)
    redundant_sub = [r.get("label") for r in M.get("religious", [])
                     if r.get("sublabel") and any(t in r["sublabel"].lower() for t in ("shrine", "monastery", "temple"))]
    check("religious_subtitle_not_redundant", not redundant_sub,
          f"religious subtitle restates the building type (already in the label): {sorted(set(redundant_sub))}")
    if headman is not None:
        hm = headman["w"] * headman["h"]
        bigger = [h for h in houses if h is not headman and h["w"] * h["h"] >= hm]
        check("headman_is_largest", not bigger, f"{len(bigger)} house(s) >= headman")

    # no two body labels overlap (title block + compass are excluded by the generator)
    labels = M.get("labels", [])
    ov = [(i, j) for i in range(len(labels)) for j in range(i + 1, len(labels))
          if min(labels[i][2], labels[j][2]) - max(labels[i][0], labels[j][0]) > 4
          and min(labels[i][3], labels[j][3]) - max(labels[i][1], labels[j][1]) > 4]
    check("no_label_overlaps", not ov, f"{len(ov)} overlapping label pair(s)")

    hill = M.get("hill")
    if hill:
        onhill = [f["name"] for f in fields if any(in_ellipse(px, py, hill) for px, py in f["outline"])]
        check("no_field_on_hill", not onhill, f"on hill: {onhill}")

    # every watercourse - irrigation channel OR natural stream - must connect what it
    # claims to: each end anchored to its pond / off-map edge / field / forest
    pond = M.get("pond")
    forest = M.get("forest")

    def anchored(pt, anchor):
        k = anchor["kind"]
        if k == "pond":
            return bool(pond) and in_ellipse(pt[0], pt[1], pond, 1.02)
        if k == "offmap":
            return min(pt[0] - EX0, EX1 - pt[0], pt[1] - EY0, EY1 - pt[1]) <= 32
        if k == "forest":
            return bool(forest) and point_in_poly(pt[0], pt[1], forest)
        if k == "stream":
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30
                       for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1))
        if k == "field":
            fo = field_by.get(anchor["name"])
            return bool(fo) and point_in_poly(pt[0], pt[1], fo["outline"]) and edge_dist(pt[0], pt[1], fo["outline"]) >= 10
        if k == "moat":
            mo = M.get("moat")
            return bool(mo) and any(seg_dist(pt[0], pt[1], mo[i], mo[i + 1]) < 34 for i in range(len(mo) - 1))
        return False

    for idx, c in enumerate(M["channels"]):
        poly, frm, to = c["poly"], c["frm"], c["to"]
        start, end = poly[0], poly[-1]
        tag = to.get("name", idx)
        check(f"channel_source_anchored[{tag}]", anchored(start, frm), f"start {start} not anchored to {frm}")
        check(f"channel_field_anchored[{tag}]", anchored(end, to), f"end {end} not anchored to {to}")
        dev = max((seg_dist(p[0], p[1], start, end) for p in poly[1:-1]), default=0)
        check(f"channel_winds_gently[{tag}]", 5 <= dev <= 50, f"deviation {dev:.0f}px (want 5-50)")
        straight = math.hypot(end[0] - start[0], end[1] - start[1])
        check(f"channel_directness[{tag}]", straight == 0 or polyline_len(poly) <= 1.6 * straight,
              f"len {polyline_len(poly):.0f} vs straight {straight:.0f}")

    # natural streams: those that declare anchors must connect them (e.g. a forest
    # brook into a pond); and NO stream may run through a farm field
    def stream_through_field(poly, outline):
        if any(point_in_poly(px, py, outline) for px, py in poly):
            return True
        n = len(outline)
        return any(segments_cross(poly[k], poly[k + 1], outline[e], outline[(e + 1) % n])
                   for k in range(len(poly) - 1) for e in range(n))

    through = []
    for idx, st in enumerate(M.get("streams", [])):
        poly, frm, to = st["poly"], st.get("frm"), st.get("to")
        if frm and to:
            check(f"stream_source_anchored[{idx}]", anchored(poly[0], frm), f"start {poly[0]} not anchored to {frm}")
            check(f"stream_end_anchored[{idx}]", anchored(poly[-1], to), f"end {poly[-1]} not anchored to {to}")
        through += [f["name"] for f in fields if stream_through_field(poly, f["outline"])]
    check("streams_avoid_fields", not through, f"stream(s) run through field(s): {sorted(set(through))}")

    # no farm field overlaps a road OR a town street (the roadbed/street band must not clip
    # a field) - the road leading into town must not run through a farm field
    roadways = []
    if road:
        roadways.append((road, M.get("road_width", 26) / 2 + 2))
    roadways += [(st["pts"], st["w"] / 2 + 2) for st in M.get("town_streets", [])]
    if roadways:
        bad_fr = []
        for f in fields:
            ol = f["outline"]
            n = len(ol)
            for poly, hw in roadways:
                if (any(seg_dist(px, py, poly[k], poly[k + 1]) < hw for px, py in ol for k in range(len(poly) - 1))
                        or any(point_in_poly(rx, ry, ol) for rx, ry in poly)
                        or any(segments_cross(poly[k], poly[k + 1], ol[e], ol[(e + 1) % n])
                               for k in range(len(poly) - 1) for e in range(n))):
                    bad_fr.append(f["name"])
                    break
        check("fields_clear_of_road", not bad_fr, f"field(s) run under a road/street: {sorted(set(bad_fr))}")

    # no field overlaps the town wall: a field may ABUT the wall but must stay on one
    # side of it (the chrysanthemum field inside the walls touches but never crosses)
    wall = M.get("wall")
    if wall:
        walled_fields = ([(f["name"], f["outline"]) for f in fields]
                         + [(f"flower[{i}]", ff["outline"]) for i, ff in enumerate(M.get("flower_fields", []))])
        bad_fw = []
        for nm, ol in walled_fields:
            n = len(ol)
            if (any(segments_cross(wall[k], wall[k + 1], ol[e], ol[(e + 1) % n])
                    for k in range(len(wall) - 1) for e in range(n))
                    or any(point_in_poly(wx, wy, ol) for wx, wy in wall)):
                bad_fw.append(nm)
        check("fields_clear_of_wall", not bad_fw, f"field(s) overlap the wall: {sorted(set(bad_fw))}")

    # EVERY fully-on-map paddy field must SHOW a source of water: a channel feeding it, or
    # the field directly abutting a stream or pond (its bank at the water). A field merely
    # NEAR water without a visible connection does not count. Fields that run off the map
    # edge are exempt (their water source may be off-map too).
    channels = M.get("channels", [])
    streams_m = M.get("streams", [])

    def watered(ol):
        if any(point_in_poly(c["poly"][-1][0], c["poly"][-1][1], ol) for c in channels):
            return True                                    # a channel ends inside it
        if any(seg_dist(px, py, sp[k], sp[k + 1]) < 18     # the field bank abuts a stream
               for st in streams_m for sp in [st["poly"]] for px, py in ol for k in range(len(sp) - 1)):
            return True
        if pond and any(in_ellipse(px, py, pond, 1.10) for px, py in ol):   # ...or the pond
            return True
        return False

    dry = [f["name"] for f in fields
           if f["kind"] == "paddy" and not runs_off_edge(f["outline"]) and not watered(f["outline"])]
    check("fields_show_water_source", not dry, f"on-map field(s) with no visible water source (channel or abutting stream/pond): {sorted(set(dry))}")

    # water flows DOWNHILL. If the map declares its slope (meta(downhill=<dir>)), every
    # channel must run with it: the source (tap on the stream/pond, poly[0]) sits uphill of
    # where it feeds the field (poly[-1]). A channel angled the other way would carry the
    # stream's water away from the field, not into it. <dir> is a cardinal name or [dx,dy]
    # vector in map coords (+y = south). Maps without the tag are exempt (slope unknown).
    downhill = meta.get("downhill")
    if downhill and channels:
        d = unit_dir(downhill)
        check("downhill_direction_valid", bool(d), f"meta(downhill={downhill!r}) is not a cardinal name or [dx,dy] vector")
        if d:
            uphill = []
            for c in channels:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]
                vx, vy = ex - sx, ey - sy
                L = math.hypot(vx, vy)
                if L > 0 and (vx * d[0] + vy * d[1]) < 0.2 * L:    # not clearly running downhill
                    uphill.append(c["to"].get("name", "?"))
            check("channels_flow_downhill", not uphill,
                  f"channel(s) not running downhill (source must be uphill of the field) for downhill={downhill}: {sorted(set(uphill))}")

    # the same flow logic applies to a city MOAT: the moat is fed by a stream entering from one
    # side (the source), so the moat water heads that-source-to-the-far-side direction (Tango's
    # feeder enters from the north, so the moat water heads SOUTH). A moat-fed irrigation channel
    # must run WITH that current - its field-end downstream of its moat-tap. A channel whose field
    # is UPSTREAM of the tap reads as water flowing from the field INTO the moat (backwards).
    moat_ring = M.get("moat")
    mfed = [c for c in channels if c.get("frm", {}).get("kind") == "moat"]
    if moat_ring and len(moat_ring) >= 3 and mfed:
        feeder = None
        for st in streams_m:
            ends = (st["poly"][0], st["poly"][-1])
            on_moat = [e for e in ends if poly_dist(e[0], e[1], moat_ring) <= 35]
            if on_moat:
                entry = on_moat[0]
                feeder = (entry, ends[1] if ends[0] == entry else ends[0])
                break
        if feeder:
            entry, origin = feeder
            dx, dy = entry[0] - origin[0], entry[1] - origin[1]      # the heading the feeder water enters on
            flow = (0, 1 if dy > 0 else -1) if abs(dy) >= abs(dx) else (1 if dx > 0 else -1, 0)   # snapped to a cardinal
            against = []
            for c in mfed:
                (sx, sy), (ex, ey) = c["poly"][0], c["poly"][-1]    # frm=moat, so poly[0] is the moat tap
                if (ex - sx) * flow[0] + (ey - sy) * flow[1] < -8:   # field clearly upstream of the tap
                    against.append(c["to"].get("name", "?"))
            check("moat_channels_flow_with_current", not against,
                  f"moat-fed channel(s) running against the moat current (field is upstream of the tap; the feeder makes the moat flow {flow}): {sorted(set(against))}")

    # large area features (forests, pastures) near a map edge must run OFF it - implying
    # they continue beyond what's drawn. Bounded farm fields are exempt.
    NEAR = 55
    area_feats = ([("forest", M["forest"])] if M.get("forest") else [])
    area_feats += [(f"forest_patch[{i}]", fp) for i, fp in enumerate(M.get("forest_patches", []))]
    area_feats += [(f"pasture[{i}]", ps) for i, ps in enumerate(M.get("pastures", []))]
    edge_bad = []
    for nm, ol in area_feats:
        xs, ys = [p[0] for p in ol], [p[1] for p in ol]
        if EX1 - NEAR <= max(xs) < EX1:
            edge_bad.append(f"{nm}:right")
        if EX0 < min(xs) <= EX0 + NEAR:
            edge_bad.append(f"{nm}:left")
        if EY1 - NEAR <= max(ys) < EY1:
            edge_bad.append(f"{nm}:bottom")
        if EY0 < min(ys) <= EY0 + NEAR:
            edge_bad.append(f"{nm}:top")
    check("edge_features_run_off_map", not edge_bad, f"edge feature(s) stop short of the edge: {edge_bad}")

    # roads and streams must run off the map edge (a stream may instead end in a pond
    # at one end; irrigation channels are exempt - they connect ponds/fields)
    EDGE = 30

    def at_edge(pt):
        return pt[0] <= EX0 + EDGE or pt[0] >= EX1 - EDGE or pt[1] <= EY0 + EDGE or pt[1] >= EY1 - EDGE

    if road:
        check("road_runs_off_edge", at_edge(road[0]) and at_edge(road[-1]),
              f"a road must reach the map edge at both ends (ends {road[0]}, {road[-1]})")
    moat_ring = M.get("moat")
    for idx, st in enumerate(M.get("streams", [])):
        e0, e1 = st["poly"][0], st["poly"][-1]
        in_pond = (lambda p: bool(pond) and in_ellipse(p[0], p[1], pond, 1.05))
        at_moat = (lambda p: bool(moat_ring) and poly_dist(p[0], p[1], moat_ring) <= 32)   # a city stream may feed the moat
        ok = all(at_edge(e) or in_pond(e) or at_moat(e) for e in (e0, e1)) and (at_edge(e0) or at_edge(e1))
        check(f"stream_runs_off_edge[{idx}]", ok, f"stream {idx} ends {e0},{e1} must run off the edge (one end may be a pond or the moat)")

    # torii (if any): clear of the shrine and spread out (universal)
    torii = M.get("torii", [])
    if torii:
        shrine = M.get("shrine")
        if shrine:
            sx, sy, sw, sh = shrine
            under = [t for t in torii if sx - 6 <= t[0] <= sx + sw + 6 and sy - 6 <= t[1] <= sy + sh + 6]
            check("torii_clear_of_shrine", not under, f"{len(under)} torii under the shrine")
        spread = all(math.hypot(torii[i][0] - torii[j][0], torii[i][1] - torii[j][1]) > 25
                     for i in range(len(torii)) for j in range(i + 1, len(torii)))
        check("torii_spread_out", spread, "torii too close together")

    # ---- village-specific expectations (from meta) ---------------------------
    abandoned = sum(1 for h in houses if h["kind"] == "abandoned")
    occupied = len(houses) - abandoned
    if meta.get("households"):
        # occupied farmhouses must portray the declared households. ~5-person homes
        # span 2-3 generations and extended families share a roof, so houses run
        # ~0.7-0.9 per household (GM: "~70 households ... at least 50 houses").
        hh = meta["households"]
        lo, hi = round(0.68 * hh), round(0.9 * hh)
        check("households_consistent", lo <= occupied <= hi,
              f"{occupied} occupied houses for ~{hh} households (expect {lo}-{hi}; +{abandoned} abandoned)")
    elif meta.get("target_houses"):
        t = meta["target_houses"]
        lo, hi = round(0.85 * t), round(1.15 * t)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect ~{t})")
    elif scale in ("village", "hamlet"):
        lo, hi = (40, 80) if scale == "village" else (10, 30)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect {lo}-{hi} for a {scale})")
    if scale == "town":
        # a town must represent its whole non-farmer population at the per-town household
        # counts documented in budgets.md (Town caste table, Families column ~= one
        # building each). Bands allow for RNG fit. Modelling calls baked into the targets:
        #  - servants (~13 households) are ALL drawn as their own dwellings: the population is
        #    counted from dwellings x5 (businesses/gatehouses house no one), so hiding most
        #    servants "inside compounds" would undercount the housing - draw the full ~13.
        #  - merchant DWELLINGS (~24) are counted on their own; shops are additional
        #    business premises (not household-gated).
        #  - samurai: ~4 resident families but a ~15-strong working platoon; show 5-10
        #    houses, the unmarried platoon barracked inside the manor (not drawn).
        bk = {}
        for b in M.get("buildings", []):
            bk[b["kind"]] = bk.get(b["kind"], 0) + 1
        farmhouses = len(houses)
        bands = {"merchant": (20, 28), "laborer": (25, 35),
                 "servant": (9, 17), "burakumin": (10, 14), "samurai": (5, 10)}
        for kind, (lo, hi) in bands.items():
            c = bk.get(kind, 0)
            check(f"town_caste_count[{kind}]", lo <= c <= hi,
                  f"{kind} buildings {c} outside budgets.md band [{lo},{hi}]")
        non_farmer_max = max((bk.get(k, 0) for k in bands), default=0)
        check("town_farmers_plurality", farmhouses >= non_farmer_max,
              f"farmhouses {farmhouses} should be the largest single group (max other {non_farmer_max})")
        check("town_has_magistrate_manor", len(M.get("manors", [])) >= 1,
              "a county-seat town must have the magistrate's manor")
        # a town has hundreds of farmers - we never show all the farmland, so at least
        # one field must run off the map edge (implying more farmland beyond what's drawn)
        off_edge = [f["name"] for f in fields if runs_off_edge(f["outline"])]
        check("town_has_field_off_edge", off_edge,
              "a town must have at least one field running off the map edge (more farmland implied)")
        # a rice-TRANSIT town (meta(granary=True)) shows a distinct tax-rice granary - a row of
        # fireproof kura where grain gathered from many counties is forwarded up the kick-up
        # chain. A standard county seat does NOT draw one: its grain sits inside the magistrate's
        # yamen, implied by the manor. Opt-in, so the default is no check (unlike the gate
        # market, amphitheater, and monasteries, which are opt-OUT defaults).
        if meta.get("granary"):
            check("town_has_granary", bool(M.get("granary")),
                  "meta(granary=True) declares a rice-transit town - it must draw a granary via s.granary(...)")
        # a noticeable MINORITY of merchant houses keep a fireproof storehouse (kura) for their
        # (often absentee) landlords' rent-rice and bulk goods - more than a token 1-2, beyond a
        # shop's ordinary inventory. Draw them with s.merchant_storehouses(...).
        check("town_has_merchant_storehouses", len(M.get("storehouses", [])) >= 3,
              f"{len(M.get('storehouses', []))} merchant storehouses - a town's merchant quarter should show several attached kura (call s.merchant_storehouses(...))")
        # a county seat is a market center: peasants from the far edge of its catchment stay
        # over on market eve in a cheap communal flophouse (kichin-yado) where travelers arrive
        # - the gate market of a walled town, the road of an unwalled one. Default-on (>= 1);
        # meta(flophouses=N) requires more (a busy hub); meta(flophouses=0) opts out.
        want_flop = meta.get("flophouses", 1)
        check("town_has_flophouse", len(M.get("flophouses", [])) >= want_flop,
              f"{len(M.get('flophouses', []))} flophouses, expected >= {want_flop} (cheap market-day lodging via s.flophouse(...); meta(flophouses=N) to change)")
        # every town has an amphitheater unless meta(amphitheater=False); for a walled town
        # it sits INSIDE the walls unless meta(amphitheater="outside")
        amph_meta = meta.get("amphitheater", True)
        amph = M.get("amphitheater")
        if amph_meta is not False:
            check("town_has_amphitheater", bool(amph),
                  "a town must have an amphitheater (set meta(amphitheater=False) to omit)")
        if amph and meta.get("walled") and amph_meta != "outside":
            w = M.get("wall") or []
            check("amphitheater_inside_wall", len(w) >= 3 and point_in_poly(amph["x"], amph["y"], w),
                  "a walled town's amphitheater belongs inside the walls (set meta(amphitheater='outside') to allow outside)")

        # a town's monasteries: by default 2, dedicated to the patron fortunes of the clan
        # whose holdings include it (meta(clan=...)). Override with an explicit list -
        # meta(monastery_fortunes=[...]) - for a town that changed hands, or a 1-monastery town.
        monks = [r for r in M.get("religious", []) if r.get("kind") == "monastery"]

        def _fortune(r):
            lab = (r.get("label") or "").strip()
            return lab.rsplit(" of ", 1)[-1].strip() if " of " in lab else lab

        declared = meta.get("monastery_fortunes")
        clan = meta.get("clan")
        if declared is None and clan:
            cf = CLAN_FORTUNES.get(clan.lower())
            check("town_clan_known", cf is not None, f"unknown clan {clan!r} - no patron fortunes")
            declared = sorted(cf) if cf else None
        check("town_declares_monasteries", declared is not None,
              "a town must declare its monasteries via meta(clan=...) or meta(monastery_fortunes=[...])")
        if declared is not None:
            check("town_monastery_count", len(monks) == len(declared),
                  f"{len(monks)} monasteries, expected {len(declared)} for {sorted(declared)}")
            got = sorted(_fortune(r) for r in monks)
            check("town_monasteries_dedicated", got == sorted(declared),
                  f"monasteries dedicated to {got}, expected {sorted(declared)}")

        # for a town whose magistrate's manor sits on a LARGE hill, two arrangement rules:
        # the manor's gate faces the town below, and the amphitheater sits at the hill's foot
        # (so the slope seats the audience)
        hill = M.get("hill")
        manor_hill = None
        if hill and hill[2] >= 150 and hill[3] >= 100:
            hcx, hcy, hrx, hry = hill
            manor_hill = next((mn for mn in M.get("manors", [])
                               if math.hypot((mn["x"] - hcx) / hrx, (mn["y"] - hcy) / hry) <= 1.0), None)
        if manor_hill:
            GATE_OUT = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
            bld = M.get("buildings", [])
            town_dir = None
            if bld:
                tvx, tvy = (sum(b["x"] for b in bld) / len(bld) - manor_hill["x"],
                            sum(b["y"] for b in bld) / len(bld) - manor_hill["y"])
                tl = math.hypot(tvx, tvy) or 1
                town_dir = (tvx / tl, tvy / tl)
                ov = GATE_OUT.get(manor_hill.get("gate_dir"), (0, 0))
                check("manor_gate_faces_town", ov[0] * town_dir[0] + ov[1] * town_dir[1] >= 0.5,
                      f"the manor's gate ({manor_hill.get('gate_dir')}) should face the town below the hill")
            if amph:
                t = math.hypot((amph["x"] - hcx) / hrx, (amph["y"] - hcy) / hry)
                fvx, fvy = amph["x"] - hcx, amph["y"] - hcy
                fl = math.hypot(fvx, fvy) or 1
                foot = unit_dir(meta.get("downhill")) or town_dir
                aligned = foot is None or (fvx / fl) * foot[0] + (fvy / fl) * foot[1] >= 0.5
                check("amphitheater_at_hill_foot", 0.85 <= t <= 1.45 and aligned,
                      "the amphitheater should sit at the foot of the hill on the downhill/town side, so the slope seats the audience")

    if scale == "town" and meta.get("walled"):
        check("walled_town_has_wall", bool(M.get("wall")) and bool(M.get("gate")),
              "a walled town must have a wall and a gate")
        w = M.get("wall") or []
        if len(w) >= 3:
            lens = [math.hypot(w[i + 1][0] - w[i][0], w[i + 1][1] - w[i][1]) for i in range(len(w) - 1)]
            # "irregular" = not a regular polygon: high spread in section lengths. A
            # coefficient of variation (stdev/mean) test, unlike a pairwise-equal test,
            # allows a wall to hug a feature with several short segments (the chrysanthemum
            # field) while still failing a lazy near-equal-sided wall.
            mean = sum(lens) / len(lens)
            cov = (sum((ln - mean) ** 2 for ln in lens) / len(lens)) ** 0.5 / mean if mean else 0
            check("wall_sections_irregular", len(lens) >= 5 and cov >= 0.25,
                  f"wall has {len(lens)} sections, length CoV {cov:.2f} (need >= 5 sections and CoV >= 0.25 for an irregular rampart)")
        # the gate-to-yamen axis: a main street must run inward from the gate
        gate = M.get("gate")
        mains = [st for st in M.get("town_streets", []) if st.get("main")]
        has_main = bool(gate) and any(min(math.hypot(p[0] - gate[0], p[1] - gate[1]) for p in st["pts"]) < 75 for st in mains)
        check("walled_town_has_main_street", has_main,
              "a walled town needs a main street running inward from the gate (the gate-to-yamen axis)")

        # no "street to nowhere": a street exists to give access to the buildings along it,
        # and is paved/worn by the traffic to and from them - so no long INSIDE-the-walls
        # stretch may be empty of buildings. (Buildings off any street are fine; that's the
        # poor who can't afford street frontage.) The map edge / off-wall approach is exempt.
        empty = empty_street_runs(M, w)
        check("streets_have_buildings", not empty,
              f"street(s) with a stretch inside the walls with no building FRONTING it (a street with no buildings would not exist - trim it or move buildings onto it): {empty}")

        # a wall is expensive: it should HUG the built-up town, not enclose large empty
        # margins. Terrain can justify some slack (a wall climbs/skirts a hill rather than
        # levelling it), so the hill counts as filled "occupancy". Flag a long contiguous
        # stretch of wall whose inside is empty of any building, feature, or terrain - that
        # length of wall would not have been built; a tighter line costs less.
        if len(w) >= 3:
            occ = [(b["x"], b["y"]) for b in M.get("buildings", []) + houses if point_in_poly(b["x"], b["y"], w)]
            for ff in M.get("flower_fields", []):
                occ += [(p[0], p[1]) for p in ff["outline"][::3]]
            occ += [(r["x"], r["y"]) for r in M.get("religious", [])] + [(mn["x"], mn["y"]) for mn in M.get("manors", [])]
            amph = M.get("amphitheater")
            if amph:
                occ.append((amph["x"], amph["y"]))
            hill = M.get("hill")

            def occ_dist(x, y):
                d = min((math.hypot(ox - x, oy - y) for ox, oy in occ), default=1e9)
                if hill:
                    hx, hy, hrx, hry = hill
                    if ((x - hx) / hrx) ** 2 + ((y - hy) / hry) ** 2 <= 1.0:
                        return 0.0   # on the hill - terrain occupancy
                    d = min(d, min(math.hypot(hx + math.cos(math.tau * k / 48) * hrx - x,
                                              hy + math.sin(math.tau * k / 48) * hry - y) for k in range(48)))
                return d

            MAXGAP, EMPTY_RUN, STEP = 140, 280, 25
            run = worst = 0
            for k in range(len(w) - 1):
                (ax, ay), (bx, by) = w[k], w[k + 1]
                for j in range(max(1, int(math.hypot(bx - ax, by - ay) // STEP))):
                    t = j / max(1, int(math.hypot(bx - ax, by - ay) // STEP))
                    if occ_dist(ax + (bx - ax) * t, ay + (by - ay) * t) > MAXGAP:
                        run += STEP
                        worst = max(worst, run)
                    else:
                        run = 0
            check("wall_hugs_the_town", worst <= EMPTY_RUN,
                  f"~{worst:.0f}px of wall runs more than {MAXGAP}px from any building or terrain (it encloses empty space - draw a tighter wall)")

        # a town monastery fronts a torii AVENUE whose number of arches is set by the open
        # approach in front of it: a grand monastery with a long clear run to the street shows
        # several arches; one wedged into a corner (the Benten monastery, hard against the west
        # wall and the Imperial field) shows a single arch. This fires ONLY for monasteries and
        # ONLY inside a wall - village SHRINES are exempt (they get 0-1 torii regardless). Each
        # torii is assigned to its nearest monastery; the approach direction is taken from the
        # monastery toward that group of torii, and the available span runs to the first street/
        # field/wall/edge (approach_span, which ignores buildings - the avenue displaces them).
        monks = [r for r in M.get("religious", []) if r.get("kind") == "monastery"]
        if monks and torii:
            PITCH = 55   # approx spacing between arches along a sando
            bad = []
            for m in monks:
                grp = [t for t in torii
                       if min(monks, key=lambda r: math.hypot(r["x"] - t[0], r["y"] - t[1])) is m]
                n = len(grp)
                if n:
                    cx, cy = sum(t[0] for t in grp) / n, sum(t[1] for t in grp) / n
                    dlen = math.hypot(cx - m["x"], cy - m["y"]) or 1.0
                    span = approach_span(m["x"], m["y"], m["h"] / 2,
                                         (cx - m["x"]) / dlen, (cy - m["y"]) / dlen, M, w, Wd, Hd)
                else:
                    span = 0.0
                lo, hi = max(1, round(span / PITCH) - 1), round(span / PITCH) + 1
                if not (lo <= n <= hi):
                    bad.append((m.get("label"), f"{n} torii", f"want {lo}-{hi}", f"~{span:.0f}px"))
            check("monastery_torii_scale_with_space", not bad,
                  f"a walled-town monastery's torii avenue should fill its approach space (a roomy approach wants several arches, a cramped one a single arch): {bad}")

        # a walled town almost always accretes a small extramural MARKET (a Chinese guan-xiang)
        # just outside its gate: the gate is a chokepoint where the rural population trades
        # without entering the walls, travellers buy services, and vendors dodge the intramural
        # tax and market regulation. So a few businesses should sit OUTSIDE the wall near the
        # gate - unless the town opts out with meta(gate_market=False) (a purely military fort,
        # or a depopulated / suppressed gate).
        if meta.get("gate_market", True):
            gate = M.get("gate")
            if gate and len(w) >= 3:
                outside_biz = [b for b in M.get("buildings", [])
                               if b.get("kind") in ("shop", "merchant")
                               and not point_in_poly(b["x"], b["y"], w)
                               and math.hypot(b["x"] - gate[0], b["y"] - gate[1]) <= 420]
                check("walled_town_has_gate_market", len(outside_biz) >= 3,
                      f"{len(outside_biz)} business(es) outside the gate - a walled town has a small gate market (guan-xiang) of a few shophouses unless meta(gate_market=False)")

    if scale == "city":
        # A PROVINCIAL CITY (budgets.md: ~2,000-4,000, avg ~3,000; 600 households - servants 120,
        # laborers 240, merchants 150, burakumin 30, samurai 60; ZERO in-city farmers). Placing
        # all 600 is unreadable, so the map shows REPRESENTATIVE neighborhoods and these checks
        # verify the required STRUCTURES + neighborhood presence, not a full per-caste headcount.
        bk = {}
        for b in M.get("buildings", []):
            bk[b.get("kind")] = bk.get(b.get("kind"), 0) + 1
        # every provincial city's interior carries the provincial government:
        check("city_has_governor_mansion", bool(M.get("governor_mansion")),
              "a provincial city must have the governor's mansion (s.governor_mansion(...))")
        mins = M.get("ministries", [])
        check("city_has_six_ministries", len(mins) == 6,
              f"{len(mins)} provincial ministry offices, expected exactly 6 (s.ministry(...))")
        rites = [m for m in mins if "rites" in (m.get("name") or "").lower()]
        check("city_has_ministry_of_rites", len(rites) == 1,
              f"{len(rites)} Ministry of Rites office(s), expected exactly 1 (sited in the temple neighborhood)")
        sam_n = bk.get("samurai", 0) + bk.get("samurai_large", 0)
        check("city_has_samurai_neighborhood", sam_n >= 8,
              f"{sam_n} samurai houses - a provincial city needs a samurai neighborhood")
        # a provincial city is ~10% samurai (~300 of ~3,000, budgets.md) - about pop/50 households.
        # Most are housed in the samurai neighborhood as individual houses; the governor's compound
        # and the extramural estates hold the rest. Require the neighborhood to depict at least ~65%
        # of that expected household count, so it is a real quarter, not a token cluster of a few.
        samurai_h = [b for b in M.get("buildings", []) if b.get("kind") in ("samurai", "samurai_large")]
        pop = meta.get("population", 0)
        if pop:
            need = round(0.65 * (0.10 * pop / HOUSEHOLD))
            check("city_samurai_housing_sufficient", len(samurai_h) >= need,
                  f"only {len(samurai_h)} samurai houses for a ~{round(0.10 * pop)}-samurai city (~{round(0.10 * pop / HOUSEHOLD)} households); "
                  f"expect >= {need} in the neighborhood (the governor's compound + extramural estates hold the rest)")
        # samurai (unlike the poor, who sit in the deep block cores) LINE their streets - many houses
        # front a street even if deeper lots sit behind. Require at least a third near a street/road.
        if samurai_h:
            slines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else [])
            near = sum(1 for b in samurai_h
                       if any(seg_dist(b["x"], b["y"], sp[i], sp[i + 1]) < 90 for sp in slines for i in range(len(sp) - 1)))
            check("city_samurai_partly_front_streets", near >= len(samurai_h) / 3,
                  f"only {near}/{len(samurai_h)} samurai houses front a street (want >= 1/3) - a samurai quarter lines its streets")
        # SAMURAI HOUSING varies in size by rank, UNLIKE a uniform cluster. budgets.md's provincial-city
        # rank table puts ~25% of resident samurai in the senior ranks (R5-7) and the rest in R1-4; so the
        # in-city neighborhood mixes a MINORITY of large houses (senior) among many small ones (junior).
        # Crucially, samurai walled ESTATES are OUTSIDE the walls (rural goshi) - the only walled samurai
        # compound inside the city is the governor's mansion - so NO manor may sit inside the wall ring.
        slarge = [b for b in M.get("buildings", []) if b.get("kind") == "samurai_large"]
        ssmall = [b for b in M.get("buildings", []) if b.get("kind") == "samurai"]
        if slarge or ssmall:
            w = M.get("wall") or []
            in_est = [m for m in M.get("manors", []) if len(w) >= 3 and point_in_poly(m["x"], m["y"], w)]
            check("city_samurai_housing_varied",
                  len(slarge) >= 3 and len(ssmall) > len(slarge) and not in_est,
                  f"samurai housing lacks size variety or has in-wall estates (large city houses={len(slarge)}, "
                  f"small={len(ssmall)}, walled estates inside the city={len(in_est)}) - senior ranks get large city "
                  f"houses, juniors small ones, and samurai walled estates sit OUTSIDE the walls (only the "
                  f"governor's mansion is walled within)")
        check("city_has_merchant_district", bk.get("merchant", 0) >= 12,
              f"{bk.get('merchant', 0)} merchant houses - a provincial city needs a merchant district")
        check("city_has_laborer_neighborhoods", bk.get("laborer", 0) >= 12,
              f"{bk.get('laborer', 0)} laborer dwellings - a provincial city needs laborer neighborhoods")
        # MERCHANT HOUSING is varied and roomy, UNLIKE the uniform, jammed laborer warren. Behind the
        # storefronts the homes mix sizes by wealth band (budgets.md: very rich -> walled ESTATES, rich
        # -> LARGE houses, the rest -> small houses) and are SPREAD OUT - more room between them than the
        # densely-packed laborers (a few denser merchant blocks are fine; the median is robust to those).
        mlarge = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_large"]
        msmall = [b for b in M.get("buildings", []) if b.get("kind") == "merchant_house"]
        mest = M.get("merchant_estates", [])
        if mlarge or msmall:                                 # a merchant district whose homes are drawn
            check("city_merchant_housing_varied", len(mest) >= 1 and len(mlarge) >= 3 and len(msmall) >= 1,
                  f"merchant housing lacks variety (walled estates={len(mest)}, large houses={len(mlarge)}, small houses={len(msmall)}) - "
                  f"a merchant quarter mixes small/average houses, LARGE (rich) houses and a few WALLED ESTATES, not one uniform size")
            homes = [(b["x"], b["y"]) for b in mlarge + msmall]
            labor = [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") == "laborer"]
            if len(homes) >= 5 and len(labor) >= 5:
                def med_nn(pts):
                    nn = sorted(min(math.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(pts) if j != i) for i, p in enumerate(pts))
                    return nn[len(nn) // 2]
                mh, lh = med_nn(homes), med_nn(labor)
                check("city_merchant_housing_spread", mh >= 1.3 * lh,
                      f"merchant homes are not more SPREAD OUT than the laborers (median neighbor gap {mh:.0f}px vs laborer {lh:.0f}px; want >= 1.3x) - "
                      f"give merchant houses more room between them; the laborer warren is the dense, uniform contrast")
        check("city_has_outside_farmland", bool([f for f in fields if runs_off_edge(f["outline"])]),
              "a city has extensive farmland outside its walls - at least one field must run off the map edge")
        # civic amenities ported up from the town tier (a city is a bigger version of the same):
        check("city_has_merchant_storehouses", len(M.get("storehouses", [])) >= 5,
              f"{len(M.get('storehouses', []))} merchant storehouses - a city's merchant district keeps fireproof kura (s.merchant_storehouses(...))")
        check("city_has_flophouse", len(M.get("flophouses", [])) >= 1,
              "a provincial city is a major market center and needs market-day lodging (s.flophouse(...))")
        check("city_has_amphitheater", bool(M.get("amphitheater")),
              "a provincial city needs an amphitheater (s.amphitheater(...))")
        # a CITY amphitheater is bigger than a town's (towns run radius ~80-82) - a provincial city
        # draws a larger crowd, so its leisure ground is ~50% larger (radius >= 92, the city baseline)
        amph = M.get("amphitheater")
        if amph:
            check("city_amphitheater_larger_than_town", amph.get("r", 0) >= 92,
                  f"the city amphitheater (radius {amph.get('r', 0)}) is no bigger than a town's - a provincial city's is larger (radius >= 92)")

        # a city ON the Imperial road LINES that road with COMMERCE (shops + traveler inns): the
        # through-road is the city's prime frontage, where caravans and travelers pass, so it must not
        # run bare. This holds for ANY city with an Imperial road, WALLED OR NOT - a city WITHOUT a road
        # has no such ribbon (its commerce stays in the market district). The road's portion running
        # THROUGH the city is judged: bounded by the WALL if there is one, else by the URBAN FOOTPRINT
        # (the bbox of the city's buildings). Scaled to that length at ~1 commercial frontage per 130px,
        # a floor that catches a bare spine.
        road = M.get("road") or []
        through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
        if through:
            wp = M.get("wall") or []
            if len(wp) >= 3:
                in_city = lambda x, y: point_in_poly(x, y, wp)        # noqa: E731
            else:
                bx = [b["x"] for b in M.get("buildings", [])] or [EX0, EX1]
                by = [b["y"] for b in M.get("buildings", [])] or [EY0, EY1]
                x0, x1, y0, y1 = min(bx) - 40, max(bx) + 40, min(by) - 40, max(by) + 40
                in_city = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1   # noqa: E731
            il = 0.0
            for i in range(len(road) - 1):
                a, b = road[i], road[i + 1]
                inside = sum(1 for t in range(11)
                             if in_city(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)) / 11
                il += math.hypot(b[0] - a[0], b[1] - a[1]) * inside
            COMMERCE = {"shop", "merchant", "inn"}
            road_comm = sum(1 for bg in M.get("buildings", [])
                            if bg.get("kind") in COMMERCE and in_city(bg["x"], bg["y"])
                            and min(seg_dist(bg["x"], bg["y"], road[k], road[k + 1]) for k in range(len(road) - 1)) <= 95)
            need = round(il / 130)
            check("city_imperial_road_has_commerce", road_comm >= need,
                  f"only {road_comm} shops/inns front the {round(il)}px of Imperial road running through the city (want >= {need}) - a "
                  f"city on a trade route lines its through-road with commerce to service travelers; don't leave the prime road frontage bare")

        if meta.get("walled"):
            w = M.get("wall") or []
            gates = M.get("gates", [])
            inwall = (lambda px, py: len(w) >= 3 and point_in_poly(px, py, w))
            check("walled_city_has_wall_and_gates", len(w) >= 3 and len(gates) >= 2,
                  f"a walled city needs a closed wall and >= 2 gates (wall={len(w)} pts, {len(gates)} gates)")
            ins = M.get("inspection_stations", [])
            no_station = [g for g in gates if not any(math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 160 for s in ins)]
            check("city_inspection_station_at_each_gate", len(gates) >= 2 and not no_station,
                  f"every city gate needs an inspection station within ~160px ({len(no_station)} gate(s) without one)")
            gstructs = M.get("gate_structs", [])
            no_guard = [g for g in gates if sum(1 for s in gstructs if math.hypot(s["x"] - g[0], s["y"] - g[1]) <= 180) < 2]
            check("city_gate_has_guardhouse", len(gates) >= 2 and not no_guard,
                  f"every city gate needs a guard house + guard tower (>= 2 gate structures within ~180px): {len(no_guard)} gate(s) short")
            buraku_in = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin" and inwall(b["x"], b["y"])]
            check("walled_city_has_burakumin_inside", len(buraku_in) >= 3,
                  f"{len(buraku_in)} burakumin inside the walls - a walled provincial city must keep >= 1 burakumin neighborhood within (they cannot be without burakumin during a siege)")
            est_out = [mn for mn in M.get("manors", []) if len(w) >= 3 and not point_in_poly(mn["x"], mn["y"], w)]
            check("city_samurai_estates_outside", 5 <= len(est_out) <= 15,
                  f"{len(est_out)} walled samurai estates outside the walls, expected 5-15 - a walled city's cramped interior pushes wealthy samurai to extramural estates they commute in from")
            areas = sorted((mn["w"] * mn["h"]) for mn in est_out)
            check("city_samurai_estates_vary_in_size", len(areas) < 2 or areas[-1] >= 1.5 * areas[0],
                  "the samurai estates should vary in size (some larger than others) - largest area >= 1.5x the smallest")
            moat = M.get("moat")
            # all city temples INSIDE the walls, and clear of the wall stroke and the moat
            rel = M.get("religious", [])
            out_rel = [r.get("label") for r in rel if not inwall(r["x"], r["y"])]
            check("city_temples_inside_walls", not out_rel,
                  f"temple(s) outside the city walls (all of a city's temples belong inside): {out_rel}")
            rel_bad = [r.get("label") for r in rel
                       if footprint_on_line(rect_corners_xywh(r, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(r, 0), moat, 13))]
            check("city_temples_clear_of_wall_moat", not rel_bad, f"temple(s) overlapping the wall or moat: {rel_bad}")
            # a TEMPLE NEIGHBORHOOD (>= 2 temples clustered together) should be dotted with a smattering of
            # small wayside SHRINES (s.small_shrine - non-residential, kind 'small_shrine'). A lone temple
            # among houses (e.g. the warrior-fortune temple in the samurai quarter) is not a neighborhood.
            temples = [r for r in rel if r.get("kind") == "temple"]
            shrines = [r for r in rel if r.get("kind") == "small_shrine"]
            clustered = [t for t in temples if any(u is not t and math.hypot(t["x"] - u["x"], t["y"] - u["y"]) < 400 for u in temples)]
            if len(clustered) >= 2:
                near = sum(1 for sh in shrines if any(math.hypot(sh["x"] - t["x"], sh["y"] - t["y"]) < 350 for t in clustered))
                check("city_temple_neighborhood_has_shrines", near >= 3,
                      f"the temple neighborhood ({len(clustered)} clustered temples) has only {near} small wayside shrine(s) - dot it with a few more (s.small_shrine)")
            # the outside samurai estates: no overlapping each other, none over the wall or moat
            est_corners = [rect_corners_xywh(mn, 0) for mn in est_out]
            est_overlap = [1 for i in range(len(est_out)) for j in range(i + 1, len(est_out)) if sat_overlap(est_corners[i], est_corners[j])]
            check("city_estates_no_overlap", not est_overlap, f"{len(est_overlap)} overlapping estate pair(s)")
            est_bad = [1 for i in range(len(est_out))
                       if footprint_on_line(est_corners[i], w, 9) or (moat and footprint_on_line(est_corners[i], moat, 13))]
            check("city_estates_clear_of_wall_moat", not est_bad, f"{len(est_bad)} estate(s) overlapping the wall or moat")
            # the WALLED MERCHANT ESTATES (their court, not just the house inside) must likewise sit clear
            # of the rampart, the moat, and any other building. (The estate's OWN inner house, centred in
            # the court, is fine; everything else - temples, compounds, other homes, other estates - is not.)
            mest = M.get("merchant_estates", [])
            mest_corners = [rect_corners_xywh(e, 0) for e in mest]
            mest_wm = [(round(mest[i]["x"]), round(mest[i]["y"])) for i in range(len(mest))
                       if footprint_on_line(mest_corners[i], w, 9) or (moat and footprint_on_line(mest_corners[i], moat, 13))]
            check("city_merchant_estates_clear_of_wall_moat", not mest_wm,
                  f"walled merchant estate(s) overlapping the city wall or moat (keep them well inside the rampart): {mest_wm}")
            civics = M.get("religious", []) + M.get("ministries", []) + ([M["governor_mansion"]] if M.get("governor_mansion") else [])
            other_struct = [rect_corners_xywh(o, 0) for o in civics] + [rect_corners(b) for b in M.get("buildings", [])]
            other_xy = [(o["x"], o["y"]) for o in civics] + [(b["x"], b["y"]) for b in M.get("buildings", [])]
            mest_bld = []
            for i in range(len(mest)):
                e = mest[i]
                for oc, (ox, oy) in zip(other_struct, other_xy):
                    if abs(ox - e["x"]) <= e["w"] / 2 and abs(oy - e["y"]) <= e["h"] / 2:
                        continue                                 # a structure centred INSIDE the court = the estate's own house
                    if sat_overlap(mest_corners[i], oc):
                        mest_bld.append((round(e["x"]), round(e["y"])))
                        break
                else:
                    for j in range(len(mest)):
                        if j != i and sat_overlap(mest_corners[i], mest_corners[j]):
                            mest_bld.append((round(e["x"]), round(e["y"])))
                            break
            check("city_merchant_estates_clear_of_buildings", not mest_bld,
                  f"walled merchant estate(s) overlapping a building (temple, compound, house, or another estate): {sorted(set(mest_bld))}")
            # a walled estate's GATE may not open INTO a building. The walls may ABUT a neighbour (very
            # common historically), but the threshold just outside the gate must front OPEN ground, not
            # a COMPOUND (temple, ministry, the yamen, or another estate court) - point the gate elsewhere.
            GDIR = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}
            compounds = [rect_corners_xywh(o, 0) for o in civics] + list(mest_corners)
            gate_bad = []
            for i in range(len(mest)):
                g = mest[i].get("gate")
                if not g:
                    continue
                ox, oy = GDIR.get(mest[i].get("gate_dir", "south"), (0, 1))
                tcx, tcy = g[0] + ox * 11, g[1] + oy * 11          # a threshold box just OUTSIDE the gate
                tw, th = (24, 22) if ox == 0 else (22, 24)
                thr = [(tcx - tw / 2, tcy - th / 2), (tcx + tw / 2, tcy - th / 2), (tcx + tw / 2, tcy + th / 2), (tcx - tw / 2, tcy + th / 2)]
                for j, cc in enumerate(compounds):
                    if j == len(civics) + i:                       # skip the estate's OWN court
                        continue
                    if sat_overlap(thr, cc):
                        gate_bad.append((round(mest[i]["x"]), round(mest[i]["y"])))
                        break
            check("city_merchant_estate_gate_clear", not gate_bad,
                  f"walled merchant estate gate(s) opening INTO a building (a temple/compound/another estate) - point the gate at open ground: {gate_bad}")
            # the government compounds (governor's mansion + ministry offices) sit inside, clear of the
            # barriers. (The governor's YAMEN is legitimately a large walled compound - a whole city block,
            # dozens of buildings inside, drawn here as walls-only - so its size is fine; it must just not
            # cross the rampart.)
            gov = M.get("governor_mansion")
            gov_items = ([gov] if gov else []) + M.get("ministries", [])
            gov_bad = [g.get("name") or g.get("label") or "governor's mansion" for g in gov_items
                       if footprint_on_line(rect_corners_xywh(g, 0), w, 9) or (moat and footprint_on_line(rect_corners_xywh(g, 0), moat, 13))]
            check("city_government_clear_of_wall_moat", not gov_bad,
                  f"government compound(s) overlapping the wall or moat: {gov_bad}")
            # the governor's mansion is the GRANDEST compound - a city-block yamen, at least as large
            # as any samurai estate and several times any single ministry office
            if gov:
                ga = gov["w"] * gov["h"]
                big_other = max([mn["w"] * mn["h"] for mn in est_out] + [3 * m["w"] * m["h"] for m in M.get("ministries", [])] + [24000])
                check("city_governor_mansion_large", ga >= big_other,
                      f"the governor's mansion ({ga:.0f}px2) must be the grandest compound - a city-block yamen at least as large as any estate and >= 3x any ministry (need >= {big_other:.0f})")
                # the ministries cluster around the yamen (the government district), threading into the
                # samurai quarter; only the Ministry of Rites sits apart, with the temples it oversees
                far_min = [m.get("name") for m in M.get("ministries", [])
                           if "rites" not in (m.get("name") or "").lower() and math.hypot(m["x"] - gov["x"], m["y"] - gov["y"]) > 480]
                check("city_ministries_cluster_at_government", not far_min,
                      f"ministry office(s) far from the governor's mansion - the ministries belong around the yamen / in the samurai quarter (only Rites sits with the temples): {far_min}")
            # a planned city's government offices FRONT its streets - the yamen sits where the main
            # streets cross and the bureaus line the avenues around it (Chinese official street /
            # jokamachi grid), so every ministry must sit on a street, not float mid-block
            st_pts = [st["pts"] for st in M.get("town_streets", [])]
            no_front = [m.get("name") for m in M.get("ministries", [])
                        if not any(seg_dist(m["x"], m["y"], sp[i], sp[i + 1]) < 85
                                   for sp in st_pts for i in range(len(sp) - 1))]
            check("city_ministries_front_a_street", not no_front,
                  f"ministry office(s) not fronting any city street - government offices line the avenues around the yamen, they do not float mid-block: {no_front}")
            # a walled city SEALS its samurai/government quarter off the commoner streets with kido
            # (wooden ward gates), not internal ramparts: full walled wards are a great-capital / Tang
            # feature, over-scaled here, so a provincial city gates the quarter's street entries instead
            on_st_kido = [k for k in M.get("kido", [])
                          if any(seg_dist(k["x"], k["y"], st["pts"][i], st["pts"][i + 1]) < st.get("w", 18) / 2 + 8
                                 for st in M.get("town_streets", []) for i in range(len(st["pts"]) - 1))]
            gated = [k for k in on_st_kido if gov and math.hypot(k["x"] - gov["x"], k["y"] - gov["y"]) < 480]
            check("city_samurai_quarter_gated", len(gated) >= 2,
                  f"a walled city seals its samurai/government quarter with kido ward gates across the streets entering it (s.kido), not walls - {len(gated)} gate(s) bar the quarter's street entries near the yamen, need >= 2")
            # ...and that ward must be SEALED: a continuous fence whose ends abut the city wall, that
            # a street pierces ONLY at a kido gate. Otherwise the gates can just be walked around, and
            # the road network connects samurai to commoner with no gate between them.
            wards = M.get("wards", [])
            kido = M.get("kido", [])
            netlines = [st["pts"] for st in M.get("town_streets", [])] + ([M["road"]] if M.get("road") else []) + [a["pts"] for a in M.get("alleys", [])]
            bad_cross, open_end = [], []
            for wd in wards:
                bnd = wd["boundary"]
                for sp in netlines:
                    for i in range(len(sp) - 1):
                        for k in range(len(bnd) - 1):
                            if segments_cross(sp[i], sp[i + 1], bnd[k], bnd[k + 1]):
                                ip = seg_intersect(sp[i], sp[i + 1], bnd[k], bnd[k + 1])
                                if ip and not any(math.hypot(g["x"] - ip[0], g["y"] - ip[1]) < 32 for g in kido):
                                    bad_cross.append((round(ip[0]), round(ip[1])))
                for e in (bnd[0], bnd[-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) > 45:
                        open_end.append((round(e[0]), round(e[1])))
            check("city_samurai_ward_sealed", bool(wards) and not bad_cross and not open_end,
                  f"the samurai/government ward is not SEALED (s.ward): wards={len(wards)}, ungated street crossings={bad_cross}, fence ends not meeting the wall={open_end} - a kido gate can be walked around unless the fence is continuous, ends at the wall, and a street pierces it only at a gate")
            # ...and the fence ends must actually TOUCH the wall - a gap (even a small one, which the
            # coarse 45px seal tolerance lets slide) means commoners can simply walk AROUND the end of
            # the fence. The end must abut the rampart within ~10px (about the wall's own half-width).
            fence_gap = []
            for wd in wards:
                bnd = wd["boundary"]
                for e in (bnd[0], bnd[-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) > 10:
                        fence_gap.append((round(e[0]), round(e[1]), "gap to the wall"))
                    elif any(math.hypot(e[0] - g[0], e[1] - g[1]) < 45 for g in gates):
                        fence_gap.append((round(e[0]), round(e[1]), "lands in a gate OPENING (the wall is cut there, so the fence meets nothing)"))
            check("city_ward_fence_meets_wall", not fence_gap,
                  f"ward-fence end(s) not abutting SOLID city wall (commoners could walk around the fence end): {fence_gap} - extend the fence to solid rampart, clear of any gate opening")
            # ...and where the fence meets the wall, the city WALL must render ON TOP (the fence runs
            # UNDER the rampart). The fence is drawn late (high z), so without a wall cap on top of the
            # junction it paints over the wall stroke. s.ward records the fence z and the wall cap it
            # lays over each end; the cap's z must be above the fence's.
            not_under = []
            for wd in wards:
                fz = wd.get("z")
                caps = wd.get("wall_caps", [])
                if fz is None:
                    continue
                for e in (wd["boundary"][0], wd["boundary"][-1]):
                    if len(w) >= 3 and edge_dist(e[0], e[1], w) <= 15 \
                            and not any(c.get("z", -1) > fz and math.hypot(c["x"] - e[0], c["y"] - e[1]) < 30 for c in caps):
                        not_under.append((round(e[0]), round(e[1])))
            check("city_ward_fence_under_wall", not not_under,
                  f"ward-fence end(s) NOT rendered under the city wall - no wall cap on top of the junction, so the fence paints over the rampart: {not_under}")
            # the extramural samurai estates all lie to the SOUTHEAST of the city
            cx, cy = sum(p[0] for p in w) / len(w), sum(p[1] for p in w) / len(w)
            not_se = [1 for mn in est_out if not (mn["x"] > cx and mn["y"] > cy)]
            check("city_estates_in_southeast", not not_se,
                  f"{len(not_se)} samurai estate(s) not to the southeast - a city's extramural estates cluster SE of it")
            # the ground circulation (streets + alleys; NOT the Imperial road, which exits at the
            # gates) must stay INSIDE the wall and clear of the moat - separate checks, since a lane
            # can poke through the rampart, the moat, or both (the elliptical wall curves in, so a
            # lane run to the block edge can spill outside even with its vertices nominally interior)
            lanes_pts = [st["pts"] for st in M.get("town_streets", [])] + [a["pts"] for a in M.get("alleys", [])]

            def crosses_ring(pts, ring, closed):
                rng = range(len(ring)) if closed else range(len(ring) - 1)
                return any(segments_cross(pts[k], pts[k + 1], ring[i], ring[(i + 1) % len(ring)])
                           for k in range(len(pts) - 1) for i in rng)
            wall_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, w, True) or any(not inwall(p[0], p[1]) for p in pts)]
            check("city_streets_clear_of_wall", not wall_hit,
                  f"{len(wall_hit)} street/alley(s) crossing the city wall (a lane running outside the rampart): {wall_hit}")
            moat = M.get("moat")
            if moat:
                moat_hit = [pts[0] for pts in lanes_pts if crosses_ring(pts, moat, False)]
                check("city_streets_clear_of_moat", not moat_hit,
                      f"{len(moat_hit)} street/alley(s) crossing the moat: {moat_hit}")
            # farm fields (in-wall plots OR the surrounding farmland) must not cut across the wall stroke
            # or the moat - the moat sits between the wall and the close-in fields, so they abut, not overlap
            fld_bad = [f["name"] for f in fields
                       if footprint_on_line(f["outline"], w, 10) or (moat and footprint_on_line(f["outline"], moat, 13))]
            check("city_fields_clear_of_wall_moat", not fld_bad, f"field(s) overlapping the city wall or moat: {fld_bad}")
            # the in-wall pond is a water source, not a moat - it must not touch the wall or moat
            pnd = M.get("pond")
            if pnd:
                pcx, pcy, prx, pry = pnd
                p_out = [(pcx + math.cos(math.tau * k / 28) * prx, pcy + math.sin(math.tau * k / 28) * pry) for k in range(28)]
                check("city_pond_clear_of_wall_moat", not (footprint_on_line(p_out, w, 9) or (moat and footprint_on_line(p_out, moat, 13))),
                      "the in-wall pond overlaps the city wall or moat")
            # internal streets must not run THROUGH the civic compounds (ministries, governor, temples,
            # gate furniture) any more than they may through ordinary buildings
            civic = M.get("ministries", []) + M.get("religious", []) + M.get("inspection_stations", []) + ([gov] if gov else [])
            civic_on_street = [c.get("name") or c.get("label") or "compound"
                               for st in M.get("town_streets", []) for c in civic
                               if footprint_on_line(rect_corners_xywh(c, 0), st["pts"], st.get("w", 24) / 2 + 2)]
            check("city_civic_clear_of_streets", not civic_on_street,
                  f"city street(s) running through a civic compound: {civic_on_street}")
            # ZONE / NEIGHBORHOOD labels must sit WITH the cluster they name: ENTIRELY on the same side
            # of the city wall as that cluster, AMONG its buildings, and not floating over a foreign field.
            # A label over the moat, a neighboring compound, or a paddy misleads the reader about what it
            # names (the "laborer neighborhoods" label drifted outside the wall, "samurai neighborhood"
            # sat over a ministry, "burakumin neighborhood" sat over a field).
            def subject_of(txt):
                t = txt.lower()
                if "estate" in t:
                    return [(m["x"], m["y"]) for m in M.get("manors", [])], 230, True
                if "agricultur" in t:   # the in-wall agricultural district, NOT the extramural farmland
                    return [c for c in ((( f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2) for f in fields) if inwall(*c)], 260, True
                if "temple" in t:
                    return [(r["x"], r["y"]) for r in M.get("religious", [])], 230, True
                for key, kinds in (("samurai", {"samurai", "samurai_large"}), ("laborer", {"laborer"}),
                                   ("burakumin", {"burakumin"}), ("merchant", {"merchant", "merchant_house", "merchant_large"})):
                    if key in t:
                        return [(b["x"], b["y"]) for b in M.get("buildings", []) if b.get("kind") in kinds], 130, False
                return [], 0, True
            bad_lab = []
            for lab in M.get("labels", []):
                if len(lab) <= 5 or not (lab[5].lower().endswith(("neighborhood", "neighborhoods", "district")) or "estates" in lab[5].lower()):
                    continue
                x0, y0, x1, y1, _z, txt = lab[:6]
                pts, reach, area_subj = subject_of(txt)
                if not pts:
                    continue                                   # nothing of that kind drawn - can't verify
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                subj_in = sum(1 for px, py in pts if inwall(px, py)) * 2 >= len(pts)
                if not all(inwall(px, py) == subj_in for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))):
                    bad_lab.append(f"{txt!r} not entirely {'inside' if subj_in else 'outside'} the wall (its cluster is)")
                elif min(math.hypot(px - cx, py - cy) for px, py in pts) > reach:
                    bad_lab.append(f"{txt!r} sits >{reach}px from any of its buildings - place it among them")
                elif not area_subj and any(point_in_poly(cx, cy, f["outline"]) for f in fields):
                    bad_lab.append(f"{txt!r} floats over a farm field, not its own houses")
            check("city_labels_placed_with_subject", not bad_lab,
                  f"neighborhood/zone label(s) misplaced relative to what they name: {bad_lab}")
            # the surrounding farmland: every OUTSIDE field (even off-edge) has farmhouses, and the
            # fields sit close to the city (cities grow up around fertile land)
            out_fields = [f for f in fields if not inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
            no_farm = [f["name"] for f in out_fields
                       if sum(1 for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ) < 2]
            check("city_outside_fields_have_farmhouses", not no_farm,
                  f"outside field(s) with < 2 farmhouses (even off-edge fields are worked by nearby villagers): {no_farm}")
            far = [f["name"] for f in out_fields if len(w) >= 3 and min(poly_dist(p[0], p[1], w) for p in f["outline"]) > 520]
            check("city_fields_close_to_city", not far,
                  f"outside field(s) too far from the city (cities grow up around fertile land, fields stay close): {far}")
            # a MOATED city irrigates several large fields from the moat
            if moat:
                chans = M.get("channels", [])
                big_out = [f for f in out_fields if (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 55000]

                def moat_fed(fo):
                    for c in chans:
                        ends = (c["poly"][0], c["poly"][-1])
                        near_moat = any(any(seg_dist(e[0], e[1], moat[i], moat[i + 1]) < 34 for i in range(len(moat) - 1)) for e in ends)
                        in_field = any(point_in_poly(e[0], e[1], fo["outline"]) for e in ends)
                        if near_moat and in_field:
                            return True
                    return False
                fed = [f["name"] for f in big_out if moat_fed(f)]
                check("city_moat_irrigates_fields", len(fed) >= 3,
                      f"{len(fed)} large outside fields fed by moat irrigation, expected >= 3 (a moated city irrigates its farmland from the moat)")
            # a gate market outside one of the gates (like a town's guan-xiang)
            biz_out = [b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant")
                       and not inwall(b["x"], b["y"]) and any(math.hypot(b["x"] - g[0], b["y"] - g[1]) <= 520 for g in gates)]
            check("city_has_gate_market", len(biz_out) >= 3,
                  f"{len(biz_out)} businesses outside a gate - a city should have a gate market (like a town's guan-xiang)")
            # market-day lodging: a flophouse INSIDE the walls, and one OUTSIDE each gate (for
            # travelers arriving from either direction, who reach the gate after it has shut)
            flops = M.get("flophouses", [])
            check("city_flophouse_inside_walls", any(inwall(fl["x"], fl["y"]) for fl in flops),
                  "a city needs market-day lodging inside the walls (a flophouse)")
            gates_wo_flop = [i for i, g in enumerate(gates)
                             if not any((not inwall(fl["x"], fl["y"])) and math.hypot(fl["x"] - g[0], fl["y"] - g[1]) <= 520 for fl in flops)]
            check("city_flophouse_outside_each_gate", not gates_wo_flop,
                  f"every city gate needs a flophouse just outside it (travelers who arrive after the gate shuts sleep there); gate(s) without one: {gates_wo_flop}")
            # a flophouse is a humble doss-house (a sen a night, on straw): inside the walls it belongs
            # in a HUMBLE quarter (the laborer section, or Tango's agrarian sector), NEVER cheek-by-jowl
            # with the nicer neighborhoods (temples, merchants, samurai), and never in or up against the
            # burakumin quarter. Only the in-wall flophouse is judged (the gate ones sit by the gate market).
            nice = [b for b in M.get("buildings", []) if b.get("kind") in ("merchant", "samurai", "samurai_large")] + M.get("religious", [])
            bura = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin"]
            inns = [b for b in M.get("buildings", []) if b.get("kind") == "inn"]
            stbl = [b for b in M.get("buildings", []) if b.get("kind") == "stables"]
            bad_flop = []
            for fl in flops:
                if not inwall(fl["x"], fl["y"]):
                    continue
                # a CARAVAN flophouse (one paired with an inn AND a stables, a gate transit cluster) is
                # exempt from the humble-quarter rule - the gate is a transit zone, not a nice neighborhood
                if (any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in inns)
                        and any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 170 for b in stbl)):
                    continue
                if any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 110 for b in nice):
                    bad_flop.append((round(fl["x"]), round(fl["y"]), "next to a temple/merchant/samurai"))
                elif any(math.hypot(b["x"] - fl["x"], b["y"] - fl["y"]) < 150 for b in bura):
                    bad_flop.append((round(fl["x"]), round(fl["y"]), "in/next to the burakumin quarter"))
            check("city_flophouse_in_humble_quarter", not bad_flop,
                  f"in-wall flophouse(s) sited in/beside a nicer or burakumin neighborhood (a doss-house belongs in the laborer/agrarian sector): {bad_flop}")
            # CARAVAN facilities: just INSIDE each gate a wagon-train needs a prominent INN and a large
            # STABLES (dozens of draft animals + crew) close to its flophouse, with OPEN GROUND around the
            # stables for the animals to be tied up / penned. Three buildings near each gate, not just one.
            caravan_bad = []
            for g in gates:
                def gnear(items, r=340):
                    return [b for b in items if inwall(b["x"], b["y"]) and math.hypot(b["x"] - g[0], b["y"] - g[1]) <= r]
                gi, gs, gf = gnear(inns), gnear(stbl), gnear(flops)
                if not (gi and gs and gf):
                    caravan_bad.append((g, f"inn={len(gi)} stables={len(gs)} flophouse={len(gf)}"))
                    continue
                crowd = sum(1 for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS
                            and math.hypot(b["x"] - gs[0]["x"], b["y"] - gs[0]["y"]) < 75)
                if crowd > 4:
                    caravan_bad.append((g, f"stables hemmed in by {crowd} dwellings (needs open ground for animals)"))
            check("city_gate_caravan_facilities", not caravan_bad,
                  f"city gate(s) lacking inside caravan facilities (a prominent inn + large stables + flophouse + open ground close to the gate): {caravan_bad}")
            # at least a couple of the samurai estates must fall (even partly) inside the rendered
            # window, so the map signals that there are several - not just one - country estates
            def _shown(m):
                hw, hh = m["w"] / 2, m["h"] / 2
                return m["x"] + hw > EX0 and m["x"] - hw < EX1 and m["y"] + hh > EY0 and m["y"] - hh < EY1
            shown_est = [m for m in M.get("manors", []) if _shown(m)]
            check("city_estates_multiple_shown", len(shown_est) >= 2,
                  f"{len(shown_est)} samurai estates fall inside the map window - show at least 2 (cropped at the edge is fine) so it reads as several, not one")
            # the Imperial-road label must sit OUTSIDE the walls (inside, the roadway is a city street)
            rl = M.get("road_label")
            if rl:
                check("city_road_label_outside_walls", not inwall(rl[0], rl[1]),
                      "the 'Imperial Road' label must sit outside the walls - inside the gates the same roadway is a city street, a city (not Imperial) responsibility")
            empty_city_streets = empty_street_runs(M, w)
            check("city_streets_have_buildings", not empty_city_streets,
                  f"city street(s) with a stretch inside the walls with no building fronting it (a street network earns its length from the buildings it serves): {empty_city_streets}")
            road = M.get("road") or []
            through = bool(road) and any(p[1] < EY0 for p in road) and any(p[1] > EY1 for p in road)
            check("city_imperial_road_through", through,
                  "the Imperial road must run N-S through a walled city - off both the top and bottom edges, via the gates")
            if not meta.get("agricultural_district"):
                inwall_fields = [f["name"] for f in fields
                                 if inwall((f["bbox"][0] + f["bbox"][2]) / 2, (f["bbox"][1] + f["bbox"][3]) / 2)]
                check("city_no_inwall_farms", not inwall_fields,
                      f"farms inside a city wall are uncharacteristic - set meta(agricultural_district=True) to allow them: {inwall_fields}")
            moat = M.get("moat")
            if moat:
                check("city_moat_surrounds_wall", len(w) >= 3 and all(point_in_poly(wx, wy, moat) for wx, wy in w),
                      "the moat must encircle the wall (every wall point inside the moat ring)")
                fed = any(any(p[0] < EX0 or p[0] > EX1 or p[1] < EY0 or p[1] > EY1 for p in (s["poly"][0], s["poly"][-1]))
                          and min(poly_dist(q[0], q[1], moat) for q in s["poly"]) <= 32
                          for s in M.get("streams", []))
                check("city_moat_fed_offmap", fed,
                      "the moat must be fed from an off-map water source (a stream from a map edge reaching the moat)")

            # the street network must be CONNECTED - one coherent grid wired to the Imperial
            # road, not isolated stubs (ported from the town "no street to nowhere" thinking).
            streets = M.get("town_streets", [])
            if streets:
                segs = [st["pts"] for st in streets] + ([M["road"]] if M.get("road") else [])
                # width of each segment's paved bed (the road counts as a street here): two streets
                # are CONNECTED only if you can walk between them, i.e. their beds actually overlap -
                # centerline gap < the sum of their half-widths. A street whose end stops even a roadbed
                # short of the next one is a SEPARATE network (you cannot step from one to the other),
                # which is exactly the laborer grid that ended 40px shy of the Imperial road. (Kido ward
                # gates do NOT break this: the street centerline runs on under the gate, uninterrupted.)
                widths = [st.get("w", 18) for st in streets] + ([M.get("road_width", 26)] if M.get("road") else [])
                parent = list(range(len(segs)))

                def find(a):
                    while parent[a] != a:
                        parent[a] = parent[parent[a]]
                        a = parent[a]
                    return a

                def beds_meet(ia, ib):   # beds overlap: segments cross, or a centerline endpoint lies
                    sa, sb = segs[ia], segs[ib]   # within the two beds' combined half-widths (+2px slack)
                    tol = widths[ia] / 2 + widths[ib] / 2 + 2
                    for i in range(len(sa) - 1):
                        for k in range(len(sb) - 1):
                            if segments_cross(sa[i], sa[i + 1], sb[k], sb[k + 1]):
                                return True
                            if (seg_dist(sa[i][0], sa[i][1], sb[k], sb[k + 1]) < tol
                                    or seg_dist(sa[i + 1][0], sa[i + 1][1], sb[k], sb[k + 1]) < tol
                                    or seg_dist(sb[k][0], sb[k][1], sa[i], sa[i + 1]) < tol
                                    or seg_dist(sb[k + 1][0], sb[k + 1][1], sa[i], sa[i + 1]) < tol):
                                return True
                    return False
                for a in range(len(segs)):
                    for b in range(a + 1, len(segs)):
                        if beds_meet(a, b):
                            parent[find(a)] = find(b)
                comps = {find(i) for i in range(len(streets))}
                check("city_streets_connected", len(comps) == 1,
                      f"the city streets form {len(comps)} disconnected groups - a street whose bed does not actually reach another's is a separate network; wire every grid to the Imperial road (extend it until the beds overlap)")
                # two streets that come ALMOST together without meeting read as a mistake - they
                # should either JOIN (cross/touch) or stay clearly apart, never leave a sliver gap
                def seg_seg_dist(a0, a1, b0, b1):
                    return min(seg_dist(a0[0], a0[1], b0, b1), seg_dist(a1[0], a1[1], b0, b1),
                               seg_dist(b0[0], b0[1], a0, a1), seg_dist(b1[0], b1[1], a0, a1))
                slines = [st["pts"] for st in streets]
                near_miss = set()
                for ia in range(len(slines)):
                    for ib in range(ia + 1, len(slines)):
                        for i in range(len(slines[ia]) - 1):
                            for k in range(len(slines[ib]) - 1):
                                if segments_cross(slines[ia][i], slines[ia][i + 1], slines[ib][k], slines[ib][k + 1]):
                                    continue
                                if 2 < seg_seg_dist(slines[ia][i], slines[ia][i + 1], slines[ib][k], slines[ib][k + 1]) < 30:
                                    near_miss.add((ia, ib))
                check("city_streets_no_near_miss", not near_miss,
                      f"city street pair(s) that come within a sliver of each other without meeting - close the gap so they join, or separate them: {sorted(near_miss)}")
                # a street that crosses another and then STOPS a little way past it leaves an ugly
                # dangling stub. Fine to cross and keep going (to the next block/edge), or to
                # terminate AT the junction (an L/T corner), but not to overshoot it by a sliver.
                stub = set()
                for ia, sa in enumerate(slines):
                    for end, nbr in ((sa[0], sa[1]), (sa[-1], sa[-2])):
                        for ib, sb in enumerate(slines):
                            if ib == ia:
                                continue
                            for k in range(len(sb) - 1):
                                if segments_cross(nbr, end, sb[k], sb[k + 1]) and 3 < seg_dist(end[0], end[1], sb[k], sb[k + 1]) < 50:
                                    stub.add((ia, ib))
                check("city_streets_no_intersection_stub", not stub,
                      f"city street(s) that cross another and then stop just past it, leaving a dangling stub - end them AT the junction or run them on: {sorted(stub)}")

            # a temple a city street runs UP TO (a street that terminates at its front) marks a
            # sacred approach - it needs torii arches on that street, just in front of the temple
            torii = M.get("torii", [])

            def pt_rect(px, py, t):
                dx = max(t["x"] - t["w"] / 2 - px, 0, px - t["x"] - t["w"] / 2)
                dy = max(t["y"] - t["h"] / 2 - py, 0, py - t["y"] - t["h"] / 2)
                return math.hypot(dx, dy)
            no_torii = []
            for t in [r for r in M.get("religious", []) if r.get("kind") == "temple"]:
                runs_up = any(min(pt_rect(e[0], e[1], t) for e in (st["pts"][0], st["pts"][-1])) < 28
                              for st in M.get("town_streets", []))
                if runs_up and not any(math.hypot(to[0] - t["x"], to[1] - t["y"]) < 95 for to in torii):
                    no_torii.append(t.get("label"))
            check("city_temple_approach_has_torii", not no_torii,
                  f"temple(s) a city street runs straight up to, with no torii arch in front: {no_torii}")
            # a torii arch stands OVER the street it spans - the street passes beneath it - so a
            # torii sitting on a street must be drawn after (higher z than) that street, not under it
            to_under = []
            for t in torii:
                for st in M.get("town_streets", []):
                    sp = st["pts"]
                    if (any(seg_dist(t[0], t[1], sp[i], sp[i + 1]) <= st.get("w", 24) / 2 + 12 for i in range(len(sp) - 1))
                            and t[2] <= st.get("z", 0)):
                        to_under.append((t[0], t[1]))
            check("city_torii_over_streets", not to_under,
                  f"torii arch(es) drawn UNDER a street they span (the street must pass beneath the arch): {to_under}")
            # no LARGE empty swath inside the walls (ported from wall_hugs_the_town). A city keeps
            # SOME open ground (drill / refuge / the road's right-of-way), so this is generous,
            # but a big contiguous region with no buildings, civic structures, fields, or pond
            # would not have been walled in.
            occ = [(b["x"], b["y"]) for b in M.get("buildings", []) + houses]
            for grp in ("manors", "ministries", "religious", "inspection_stations"):
                occ += [(o["x"], o["y"]) for o in M.get(grp, [])]
            occ += [(o["x"], o["y"]) for o in M.get("flophouses", []) + M.get("storehouses", [])]
            for one in (M.get("governor_mansion"), M.get("amphitheater")):
                if one:
                    occ.append((one["x"], one["y"]))
            field_polys = [f["outline"] for f in fields]
            pondE = M.get("pond")

            def used(x, y):
                if any((x - ox) ** 2 + (y - oy) ** 2 < 120 * 120 for ox, oy in occ):
                    return True
                if pondE and in_ellipse(x, y, pondE, 1.1):
                    return True
                return any(point_in_poly(x, y, fp) for fp in field_polys)

            STEP = 80
            empty = set()
            for ci in range(int(Wd // STEP) + 1):
                for cj in range(int(Hd // STEP) + 1):
                    x, y = ci * STEP, cj * STEP
                    if point_in_poly(x, y, w) and not used(x, y):
                        empty.add((ci, cj))
            seen, largest = set(), 0
            for cell in empty:
                if cell in seen:
                    continue
                stack, size = [cell], 0
                seen.add(cell)
                while stack:
                    pi, pj = stack.pop()
                    size += 1
                    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nb = (pi + di, pj + dj)
                        if nb in empty and nb not in seen:
                            seen.add(nb)
                            stack.append(nb)
                largest = max(largest, size)
            check("city_no_large_empty_space", largest <= 12,
                  f"a contiguous empty region of ~{largest} grid cells (~{largest * STEP * STEP // 1000}k px2) inside the walls - a city does not wall in large unused ground")

    if scale == "village":
        tf = M.get("taxfree", [])
        check("taxfree_plots_in_range", 2 <= len(tf) <= 3, f"{len(tf)} tax-free plots (law: ~2 households)")

    big_paddies = sorted([f for f in fields if f["kind"] == "paddy"
                          and (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 80000],
                         key=lambda f: -(f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]))
    if scale != "city" and len(big_paddies) >= 2:   # a city's in-wall plots / off-edge fields are not staggered common fields
        def wide(f):
            return (f["bbox"][2] - f["bbox"][0]) >= (f["bbox"][3] - f["bbox"][1])
        check("common_fields_vary_orientation", wide(big_paddies[0]) != wide(big_paddies[1]),
              "the two large common fields share an orientation")

    if meta.get("fallow_implies_abandoned"):
        for f in fields:
            if f["kind"] == "fallow":
                ab = sum(1 for h in houses if h["kind"] == "abandoned" and poly_dist(h["x"], h["y"], f["outline"]) <= ADJ)
                check(f"fallow_has_abandoned[{f['name']}]", ab >= 2, f"{ab} abandoned near {f['name']}, need 2")

    if meta.get("shrine_on_hill") and M.get("shrine") and M.get("summit") and hill:
        sx, sy, sw, sh = M["shrine"]
        sc = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
        on_hill = all(in_ellipse(px, py, hill) for px, py in sc)
        on_summit = in_ellipse(sx + sw / 2, sy + sh / 2, M["summit"])
        check("shrine_on_hill_summit", on_hill and on_summit, "shrine overhangs the hill or is off the summit")
        offhill = [t for t in torii if not in_ellipse(t[0], t[1], hill)]
        check("torii_on_hill", not offhill, f"{len(offhill)} torii off the hill")

    if "torii_expected" in meta:
        check("torii_count", len(torii) == meta["torii_expected"], f"{len(torii)} torii, expected {meta['torii_expected']}")

    if M.get("pond"):
        pcx, pcy, prx, pry = M["pond"]
        if headman is not None:
            check("pond_bigger_than_headman", math.pi * prx * pry > headman["w"] * headman["h"], "pond not larger than headman house")
        if hill:
            check("pond_clear_of_hill", not in_ellipse(pcx, pcy, hill, 1.4), "pond too close to the hill (erosion)")

    if verbose:
        print(f"\n{len(fails)} failing check(s): {fails}" if fails else "\nALL CHECKS PASSED")
    return fails


def main(path):
    return 1 if gate(load(path)) else 0


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "pool", "kikuta-village.json")
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else default))
