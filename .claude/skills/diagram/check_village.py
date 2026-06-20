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


DEFAULT_MANIFEST = {
    "houses": [], "fields": [], "fallow_patches": [], "channels": [], "lane": [],
    "taxfree": [], "torii": [], "shrines": [], "manors": [], "streams": [],
    "buildings": [], "pastures": [], "forest_patches": [], "religious": [],
    "flower_fields": [], "labels": [], "town_streets": [], "gate_structs": [],
    "pond": None, "hill": None, "summit": None, "shrine": None, "forest": None,
    "road": None, "wall": None, "gate": None, "amphitheater": None, "meta": {},
}


def gate(M, verbose=True):
    """Run every check over a manifest dict M and return the list of FAILED check names.
    verbose prints the PASS/FAIL lines. Pass a synthetic M to unit-test a single check."""
    # tolerate sparse synthetic manifests (unit tests build only the keys a check needs)
    M = {**DEFAULT_MANIFEST, **M}
    meta = M.get("meta", {})
    houses, fields = M["houses"], M["fields"]
    field_by = {f["name"]: f for f in fields}
    Wd, Hd = meta.get("W", 1820), meta.get("H", 1180)
    fails = []

    def check(name, ok, detail=""):
        if verbose:
            print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -> " + detail))
        if not ok:
            fails.append(name)

    # ---- universal invariants ------------------------------------------------
    structs = houses + M.get("buildings", [])     # farmhouses AND urban buildings
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

    # no structure overlaps a torii arch (footprint ~38x28, centred just below the post tops)
    bad_t = [1 for (tx, ty) in M.get("torii", []) for sc in corners
             if sat_overlap(sc, [(tx - 19, ty - 10), (tx + 19, ty - 10), (tx + 19, ty + 18), (tx - 19, ty + 18)])]
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

    # no structure overlaps a town street (the gate-to-yamen avenue or a cross lane)
    tstreets = M.get("town_streets", [])
    if tstreets:
        def on_street(sc, sp, hw):
            if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
                return True
            if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
                return True
            return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % 4])
                       for k in range(len(sp) - 1) for e in range(4))
        bad_ts = [1 for sc in corners for st in tstreets if on_street(sc, st["pts"], st.get("w", 24) / 2 + 2)]
        check("no_structure_on_street", not bad_ts, f"{len(bad_ts)} structure(s) overlap a town street")

    # ---- street-faced town layout: businesses front the streets (and face them); housing
    # sits back off the main commercial street. The "streets" are the town streets plus any
    # road (an unwalled town's road is its high street).
    street_lines = [st["pts"] for st in M.get("town_streets", [])]
    main_idx = next((i for i, st in enumerate(M.get("town_streets", [])) if st.get("main")), None)
    if M.get("road"):
        street_lines.append([list(p) for p in M["road"]])
        if main_idx is None:
            main_idx = len(street_lines) - 1
    if street_lines and M.get("buildings"):
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
        return any(p[0] < 0 or p[0] > Wd or p[1] < 0 or p[1] > Hd for p in ol)

    for f in fields:
        if runs_off_edge(f["outline"]):
            continue   # a field running off the map has its farmhouses implied off-map too
        ring = [h for h in houses if poly_dist(h["x"], h["y"], f["outline"]) <= ADJ]
        area = (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1])
        need = 5 if area > 80000 else 3
        check(f"field_ringed[{f['name']}]", len(ring) >= need, f"{len(ring)} houses, need {need}")

    not_south = [h for h in houses if h["w"] < h["h"] or abs(h["rot"]) > 12]
    check("houses_face_south", not not_south, f"{len(not_south)} house(s) not south-facing")

    scale = meta.get("scale", "village")
    headman = next((h for h in houses if h.get("role") == "headman"), None)
    if scale == "village":
        check("village_has_headman", headman is not None, "a village must have a headman")
    else:
        # hamlets fall under the village district headman; towns are run by the magistrate
        check(f"{scale}_has_no_headman", headman is None, f"a {scale} has no peasant headman of its own")

    # religious building by settlement scale: hamlet none, village shrine, town
    # monastery, city temple
    expected_rel = {"hamlet": None, "village": "shrine", "town": "monastery", "city": "temple"}.get(scale)
    rel_kinds = set(r["kind"] for r in M.get("religious", []))
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
            return min(pt[0], Wd - pt[0], pt[1], Hd - pt[1]) <= 32
        if k == "forest":
            return bool(forest) and point_in_poly(pt[0], pt[1], forest)
        if k == "stream":
            return any(seg_dist(pt[0], pt[1], sp[i], sp[i + 1]) < 30
                       for st in M.get("streams", []) for sp in [st["poly"]] for i in range(len(sp) - 1))
        if k == "field":
            fo = field_by.get(anchor["name"])
            return bool(fo) and point_in_poly(pt[0], pt[1], fo["outline"]) and edge_dist(pt[0], pt[1], fo["outline"]) >= 10
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

    # large area features (forests, pastures) near a map edge must run OFF it - implying
    # they continue beyond what's drawn. Bounded farm fields are exempt.
    NEAR = 55
    area_feats = ([("forest", M["forest"])] if M.get("forest") else [])
    area_feats += [(f"forest_patch[{i}]", fp) for i, fp in enumerate(M.get("forest_patches", []))]
    area_feats += [(f"pasture[{i}]", ps) for i, ps in enumerate(M.get("pastures", []))]
    edge_bad = []
    for nm, ol in area_feats:
        xs, ys = [p[0] for p in ol], [p[1] for p in ol]
        if Wd - NEAR <= max(xs) < Wd:
            edge_bad.append(f"{nm}:right")
        if 0 < min(xs) <= NEAR:
            edge_bad.append(f"{nm}:left")
        if Hd - NEAR <= max(ys) < Hd:
            edge_bad.append(f"{nm}:bottom")
        if 0 < min(ys) <= NEAR:
            edge_bad.append(f"{nm}:top")
    check("edge_features_run_off_map", not edge_bad, f"edge feature(s) stop short of the edge: {edge_bad}")

    # roads and streams must run off the map edge (a stream may instead end in a pond
    # at one end; irrigation channels are exempt - they connect ponds/fields)
    EDGE = 30

    def at_edge(pt):
        return pt[0] <= EDGE or pt[0] >= Wd - EDGE or pt[1] <= EDGE or pt[1] >= Hd - EDGE

    if road:
        check("road_runs_off_edge", at_edge(road[0]) and at_edge(road[-1]),
              f"a road must reach the map edge at both ends (ends {road[0]}, {road[-1]})")
    for idx, st in enumerate(M.get("streams", [])):
        e0, e1 = st["poly"][0], st["poly"][-1]
        in_pond = (lambda p: bool(pond) and in_ellipse(p[0], p[1], pond, 1.05))
        ok = all(at_edge(e) or in_pond(e) for e in (e0, e1)) and (at_edge(e0) or at_edge(e1))
        check(f"stream_runs_off_edge[{idx}]", ok, f"stream {idx} ends {e0},{e1} must run off the edge (one end may be a pond)")

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
        #  - servants (~13 households) are mostly attached to samurai/merchant compounds;
        #    only the ~5 "miscellaneous" households stand alone, so the rest aren't drawn.
        #  - merchant DWELLINGS (~24) are counted on their own; shops are additional
        #    business premises (not household-gated).
        #  - samurai: ~4 resident families but a ~15-strong working platoon; show 5-10
        #    houses, the unmarried platoon barracked inside the manor (not drawn).
        bk = {}
        for b in M.get("buildings", []):
            bk[b["kind"]] = bk.get(b["kind"], 0) + 1
        farmhouses = len(houses)
        bands = {"merchant": (20, 28), "laborer": (25, 33),
                 "servant": (3, 7), "burakumin": (10, 14), "samurai": (5, 10)}
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

    if meta.get("walled"):
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
        # poor who can't afford street frontage.) The map edge / off-wall approach is exempt
        # (the main street legitimately runs out to elsewhere).
        if M.get("town_streets") and len(w) >= 3:
            blds = M.get("buildings", []) + houses
            lines = [st["pts"] for st in M["town_streets"]]
            FRONT, COVER, MAXGAP, STEP = 95, 105, 130, 25
            # A building only SERVES the street it actually fronts - its nearest street,
            # within the frontage band. A building near a perpendicular cross-street fronts
            # THAT one, not the lane it happens to sit beside, so it can't paper over an
            # empty stub on the lane.
            fronts = {}
            for b in blds:
                best, bi = FRONT, None
                for i, sp in enumerate(lines):
                    for k in range(len(sp) - 1):
                        dd = seg_dist(b["x"], b["y"], sp[k], sp[k + 1])
                        if dd < best:
                            best, bi = dd, i
                if bi is not None:
                    fronts.setdefault(bi, []).append(b)
            empty = []
            for si, st in enumerate(M["town_streets"]):
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
                if worst > MAXGAP:
                    empty.append(("main" if st.get("main") else f"@{pts[0]}", worst))
            check("streets_have_buildings", not empty,
                  f"street(s) with a stretch > {MAXGAP}px inside the walls with no building FRONTING it (a street with no buildings would not exist - trim it or move buildings onto it): {empty}")

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
