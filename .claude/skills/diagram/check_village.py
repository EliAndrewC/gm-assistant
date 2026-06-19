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


def edge_dist(px, py, poly):
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def in_ellipse(px, py, e, scale=1.0):
    cx, cy, rx, ry = e
    return ((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0


def polyline_len(poly):
    return sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))


def main(path):
    M = load(path)
    meta = M.get("meta", {})
    houses, fields = M["houses"], M["fields"]
    field_by = {f["name"]: f for f in fields}
    Wd, Hd = meta.get("W", 1820), meta.get("H", 1180)
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -> " + detail))
        if not ok:
            fails.append(name)

    # ---- universal invariants ------------------------------------------------
    corners = [rect_corners(h) for h in houses]
    bad = [(i, j) for i in range(len(houses)) for j in range(i + 1, len(houses))
           if math.hypot(houses[i]["x"] - houses[j]["x"], houses[i]["y"] - houses[j]["y"]) <= 90
           and sat_overlap(corners[i], corners[j])]
    check("no_house_overlaps", not bad, f"{len(bad)} overlapping pair(s)")

    corr = ([M["lane"]] if M.get("lane") else []) + [c["poly"] for c in M["channels"]]
    onroad = sum(1 for h in houses for poly in corr
                 if any(seg_dist(h["x"], h["y"], poly[k], poly[k + 1]) < 14 for k in range(len(poly) - 1)))
    check("houses_off_corridors", onroad == 0, f"{onroad} house-on-corridor hit(s)")

    ADJ = 165
    far = [h for h in houses if h.get("role") != "headman"
           and min((poly_dist(h["x"], h["y"], f["outline"]) for f in fields), default=999) > ADJ]
    check("all_houses_field_adjacent", not far, f"{len(far)} house(s) >{ADJ}px from any field")
    for f in fields:
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")

    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")

    headman = next((h for h in houses if h.get("role") == "headman"), None)
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

    # channels: each anchored at BOTH ends and gently winding (universal)
    pond = M.get("pond")
    for idx, c in enumerate(M["channels"]):
        poly, frm, to = c["poly"], c["frm"], c["to"]
        start, end = poly[0], poly[-1]
        tag = to.get("name", idx)

        def anchored(pt, anchor):
            k = anchor["kind"]
            if k == "pond":
                return bool(pond) and in_ellipse(pt[0], pt[1], pond, 1.02)
            if k == "offmap":
                return min(pt[0], Wd - pt[0], pt[1], Hd - pt[1]) <= 32
            if k == "field":
                fo = field_by.get(anchor["name"])
                return bool(fo) and point_in_poly(pt[0], pt[1], fo["outline"]) and edge_dist(pt[0], pt[1], fo["outline"]) >= 10
            return False
        check(f"channel_source_anchored[{tag}]", anchored(start, frm), f"start {start} not anchored to {frm}")
        check(f"channel_field_anchored[{tag}]", anchored(end, to), f"end {end} not anchored to {to}")
        dev = max((seg_dist(p[0], p[1], start, end) for p in poly[1:-1]), default=0)
        check(f"channel_winds_gently[{tag}]", 5 <= dev <= 50, f"deviation {dev:.0f}px (want 5-50)")
        straight = math.hypot(end[0] - start[0], end[1] - start[1])
        check(f"channel_directness[{tag}]", straight == 0 or polyline_len(poly) <= 1.6 * straight,
              f"len {polyline_len(poly):.0f} vs straight {straight:.0f}")

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
    scale = meta.get("scale", "village")
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
    else:
        lo, hi = (40, 80) if scale == "village" else (10, 30)
        check("house_count_in_range", lo <= len(houses) <= hi, f"{len(houses)} houses (expect {lo}-{hi} for a {scale})")

    if scale == "village":
        tf = M.get("taxfree", [])
        check("taxfree_plots_in_range", 2 <= len(tf) <= 3, f"{len(tf)} tax-free plots (law: ~2 households)")

    big_paddies = sorted([f for f in fields if f["kind"] == "paddy"
                          and (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]) > 80000],
                         key=lambda f: -(f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]))
    if len(big_paddies) >= 2:
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

    print(f"\n{len(fails)} failing check(s): {fails}" if fails else "\nALL CHECKS PASSED")
    return 1 if fails else 0


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "pool", "kikuta-village.json")
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else default))
