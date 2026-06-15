#!/usr/bin/env python3
"""Automated checks for a Mode B settlement-map manifest (diagram skill).

Reads the JSON manifest the generator emits and asserts the testable Mode B
rules. Exit 0 if all pass, 1 otherwise. The skill's plain-English / persona
review still applies on top of this gate - this only covers what a script can
judge by geometry.
"""
import json
import math
import os
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
    """True if two convex polygons intersect (separating-axis theorem)."""
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


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


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


def in_ellipse(px, py, e, scale=1.0):
    cx, cy, rx, ry = e
    return ((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0


def polyline_len(poly):
    return sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))


def edge_dist(px, py, poly):
    """Distance to the nearest edge of a polygon, regardless of inside/outside."""
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def main(path):
    M = load(path)
    houses, fields = M["houses"], M["fields"]
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -> " + detail))
        if not ok:
            fails.append(name)

    # 1 - no farmhouse overlaps (rotated-rect SAT)
    corners = [rect_corners(h) for h in houses]
    bad = []
    for i in range(len(houses)):
        for j in range(i + 1, len(houses)):
            if math.hypot(houses[i]["x"] - houses[j]["x"], houses[i]["y"] - houses[j]["y"]) > 90:
                continue
            if sat_overlap(corners[i], corners[j]):
                bad.append((i, j))
    check("no_house_overlaps", not bad, f"{len(bad)} overlapping pair(s)")

    # 2 - nothing built on a lane or irrigation channel
    corr = [M["lane"]] + [c["poly"] for c in M["channels"]]
    onroad = sum(1 for h in houses for poly in corr
                 if any(seg_dist(h["x"], h["y"], poly[k], poly[k + 1]) < 14 for k in range(len(poly) - 1)))
    check("houses_off_corridors", onroad == 0, f"{onroad} house-on-corridor hit(s)")

    # 3 - all houses field-adjacent; every field ringed; fallow fields ring abandoned houses
    ADJ = 165
    far = [h for h in houses if h.get("role") != "headman"
           and min(poly_dist(h["x"], h["y"], f["outline"]) for f in fields) > ADJ]
    check("all_houses_field_adjacent", not far, f"{len(far)} house(s) >{ADJ}px from any field")
    for f in fields:
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")
        if f["kind"] == "fallow":
            ab = sum(1 for h in ring if h["kind"] == "abandoned")
            check(f"fallow_has_abandoned[{f['name']}]", ab >= 2, f"{ab} abandoned, need 2")

    # 4 - no cultivation on the hill
    hill = M["hill"]
    onhill = [f["name"] for f in fields if any(in_ellipse(px, py, hill) for px, py in f["outline"])]
    check("no_field_on_hill", not onhill, f"on hill: {onhill}")

    # 5 - shrine doesn't overhang the hill and sits on the summit
    sx, sy, sw, sh = M["shrine"]
    scorners = [(sx, sy), (sx + sw, sy), (sx + sw, sy + sh), (sx, sy + sh)]
    on_hill = all(in_ellipse(px, py, hill) for px, py in scorners)
    on_summit = in_ellipse(sx + sw / 2, sy + sh / 2, M["summit"])
    check("shrine_on_hill_summit", on_hill and on_summit, "shrine overhangs the hill or is off the summit")

    # 6 - pond larger than the headman's house, and set back from the hill
    pcx, pcy, prx, pry = M["pond"]
    headman = next((h for h in houses if h.get("role") == "headman"), None)
    check("pond_bigger_than_headman", headman is not None and math.pi * prx * pry > headman["w"] * headman["h"], "pond not larger than headman house")
    check("pond_clear_of_hill", not in_ellipse(pcx, pcy, hill, 1.4), "pond too close to the hill (erosion)")

    # 7 - irrigation reasonably direct (channel <= 1.5x straight pond->entry)
    for c in M["channels"]:
        poly = c["poly"]
        straight = math.hypot(poly[-1][0] - pcx, poly[-1][1] - pcy)
        check(f"channel_directness[{c['target']}]", straight == 0 or polyline_len(poly) <= 1.5 * straight,
              f"len {polyline_len(poly):.0f} vs straight {straight:.0f}")

    # 8 - house count plausible for an average village (40-100 households)
    check("house_count_in_range", 40 <= len(houses) <= 80, f"{len(houses)} houses")

    # 9 - the country monk's tax-free allocation is law-bounded (~2 households = 2-3 plots)
    tf = M.get("taxfree", [])
    check("taxfree_plots_in_range", 2 <= len(tf) <= 3, f"{len(tf)} tax-free plots (law: ~2 households)")

    # 10 - the headman's house is the largest in the village
    if headman is not None:
        hm_area = headman["w"] * headman["h"]
        bigger = [h for h in houses if h is not headman and h["w"] * h["h"] >= hm_area]
        check("headman_is_largest", not bigger, f"{len(bigger)} house(s) >= headman")

    # 11 - houses face south (long axis E-W, no large rotation)
    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")

    # 12 - the two largest common (paddy) fields differ in orientation
    paddies = sorted([f for f in fields if f["kind"] == "paddy"],
                     key=lambda f: -(f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]))[:2]

    def wide(f):
        return (f["bbox"][2] - f["bbox"][0]) >= (f["bbox"][3] - f["bbox"][1])
    check("common_fields_vary_orientation", len(paddies) < 2 or wide(paddies[0]) != wide(paddies[1]),
          "the two large common fields share an orientation")

    # 13 - torii: 7 of them, none hidden under the shrine, all on the hill, spread out
    torii = M.get("torii", [])
    sx, sy, sw, sh = M["shrine"]
    under = [t for t in torii if sx - 6 <= t[0] <= sx + sw + 6 and sy - 6 <= t[1] <= sy + sh + 6]
    offhill = [t for t in torii if not in_ellipse(t[0], t[1], hill)]
    spread = all(math.hypot(torii[i][0] - torii[j][0], torii[i][1] - torii[j][1]) > 25
                 for i in range(len(torii)) for j in range(i + 1, len(torii)))
    check("torii_count_7", len(torii) == 7, f"{len(torii)} torii")
    check("torii_clear_of_shrine", not under, f"{len(under)} torii under the shrine")
    check("torii_on_hill", not offhill, f"{len(offhill)} torii off the hill")
    check("torii_spread_out", spread, "torii too close together")

    # 14 - irrigation channels actually connect pond->field and wind gently (not straight)
    pond = M["pond"]
    field_by = {f["name"]: f for f in fields}
    for c in M["channels"]:
        poly, tgt = c["poly"], c["target"]
        start, end = poly[0], poly[-1]
        check(f"channel_connects_pond[{tgt}]", in_ellipse(start[0], start[1], pond),
              f"start {start} is not inside the pond")
        f = field_by.get(tgt)
        # "connects" means the channel reaches INTO the field (a margin inside the outline),
        # not merely touching the edge where the field is still brown bund margin
        inside = bool(f) and point_in_poly(end[0], end[1], f["outline"])
        margin = edge_dist(end[0], end[1], f["outline"]) if f else 0
        reaches_in = inside and margin >= 10
        detail = (f"end {end} is outside the {tgt} field" if not inside
                  else f"end only {margin:.0f}px inside the {tgt} field (want >=10)")
        check(f"channel_connects_field[{tgt}]", reaches_in, detail)
        dev = max((seg_dist(p[0], p[1], start, end) for p in poly[1:-1]), default=0)
        check(f"channel_winds_gently[{tgt}]", 5 <= dev <= 50, f"max deviation {dev:.0f}px (want a gentle 5-50)")

    print(f"\n{len(fails)} failing check(s): {fails}" if fails else "\nALL CHECKS PASSED")
    return 1 if fails else 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "pool", "kikuta-village.json")
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else default))
