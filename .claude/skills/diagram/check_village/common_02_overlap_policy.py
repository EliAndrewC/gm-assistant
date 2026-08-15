"""Shared gate helpers (overlap policy): matrix_violations, check_ring_road_clear, matrix_extents, GridIndex, forest_reveal_x, torii_halfbox, FOREST_REVEAL_FT, CANOPY_STRUCT_KEYS, ... - bodies verbatim from check_village.py (feature 024 package split; SCC-packed, see split_package.py)."""

import math
from collections.abc import Callable, Mapping
from typing import Any

from settlement import sat_overlap

from .common_01_geometry import (
    _MATRIX_PARENT_FIELD,
    _MATRIX_PERMISSIVE,
    _MX_FIXTURE_BOX,
    _MX_LINE_W,
    _OVERLAP_STRUCTS,
    OVERLAP_CLASS,
    Check,
    Manifest,
    Poly,
    _mx_rect,
    _mx_same,
    _mx_stroke,
    _struct_rect,
    matrix_policy,
    point_in_poly,
    poly_dist,
    rect_corners,
    seg_dist,
    segments_cross,
    solid_structs,
)


def matrix_violations(M: Mapping[str, Any]) -> list[tuple[str, str, float, float]]:
    """Every FORBIDDEN overlap on the map, as (key_a, key_b, x, y).

    The conditional permissions live here rather than in `matrix_policy`, because each depends on
    the two RECORDS rather than on their classes alone: an annex may lie on its own parent (and only
    its own), two annexes of one household may abut, a supply channel may reach the field it feeds,
    and a trade work's private well stands inside its own court."""
    ext = matrix_extents(M)
    if not ext:
        return []  # pragma: no cover - every real map draws something
    priv = {(round(w_["x"], 1), round(w_["y"], 1)) for w_ in M.get("wells", []) or [] if w_.get("private")}
    polys = [p for _k, p, _i, _pa in ext]
    boxes = [(min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)) for p in polys]
    # CLAMP THE INDEX BOX TO THE CANVAS. GridIndex.add inserts under every cell an item's bbox
    # touches, so one feature reaching far off-map costs a dict entry per 120 px in BOTH axes. A
    # malformed map is not hypothetical - `city_geometry_within_canvas` is checked with a fixture
    # planting a wall vertex at 9,000,000 on a 3,200 px canvas, which is ~5.6 BILLION cells and
    # gigabytes of RAM (found the hard way, 2026-07-26: the run had to be killed by hand). The index
    # only PRUNES - every surviving pair is still tested against the real polygons - so clamping the
    # indexed extent changes no verdict for anything actually on the map. Two features BOTH off the
    # canvas may no longer be compared, which is the right division of labour: geometry that is not
    # on the map is `city_geometry_within_canvas`'s business, not the overlap matrix's.
    _mx_w = float(M.get("meta", {}).get("W") or 4000)
    _mx_h = float(M.get("meta", {}).get("H") or 4000)

    def _mx_clamp(b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        return (max(b[0], -_mx_w), max(b[1], -_mx_h), min(b[2], _mx_w * 2), min(b[3], _mx_h * 2))

    # Clamp for BOTH insert and query: `near_rect` walks the cells of the box it is GIVEN, so
    # querying with the unclamped extent costs exactly as much as inserting with it did.
    cboxes = [_mx_clamp(b) for b in boxes]
    gi = GridIndex(120)
    for idx, cb in enumerate(cboxes):
        if cb[2] < cb[0] or cb[3] < cb[1]:
            continue  # wholly off the canvas - nothing on the map can meet it
        gi.add(cb[0], cb[1], cb[2], cb[3], idx)
    seen: set[tuple[int, int]] = set()
    out: list[tuple[str, str, float, float]] = []
    for i, (ki, _pi, idi, pari) in enumerate(ext):
        del _pi
        bi = boxes[i]
        cbi = cboxes[i]
        if cbi[2] < cbi[0] or cbi[3] < cbi[1]:
            continue
        for j in gi.near_rect(*cbi):
            if j <= i or (i, j) in seen:
                continue
            seen.add((i, j))
            kj, _pj, idj, parj = ext[j]
            del _pj
            if matrix_policy(ki, kj):
                continue
            bj = boxes[j]
            if bi[2] < bj[0] or bi[0] > bj[2] or bi[3] < bj[1] or bi[1] > bj[3]:
                continue
            if _mx_same(pari, idj) or _mx_same(parj, idi):
                continue  # an annex on its OWN parent
            if OVERLAP_CLASS.get(ki) == "ANNEX" and OVERLAP_CLASS.get(kj) == "ANNEX" and _mx_same(pari, parj):
                continue  # two annexes of one household
            if "wells" in (ki, kj) and ((idi in priv) or (idj in priv)):
                continue  # a trade work's own private well, inside its own court
            if sat_overlap(polys[i], polys[j]):
                cx = sum(q[0] for q in polys[i]) / len(polys[i])
                cy = sum(q[1] for q in polys[i]) / len(polys[i])
                out.append((ki, kj, round(cx), round(cy)))
    return out


def check_ring_road_clear(M: Mapping[str, Any], check: Any) -> None:
    """THE RING ROAD IS A CLEAR PATROL ROAD - it must run clear of EVERY solid footprint and of
    fields. The gate guard houses / inspection stations / towers DO sit along it (wall furniture -
    `gate_structs` and `wall_towers` are overlap TARGETS and EXEMPT respectively, so the registry
    leaves them out), and a ward fence may cross it only at a gated kido. Overlap = the ring's BED
    passes through a footprint. Reads the REGISTRY, never a hand list (GM 2026-07-25).

    FACTORED OUT of the scale=="city" block (GM 2026-08-09, 'estates should not overlap with the
    ring-road'): a CAPITAL has a ring road too, and this check living only under scale=="city"
    meant four lineage estates could stand on the capital's patrol road with a green gate - the
    check never RAN there, which looks exactly like passing. Two gaps stacked: the scope, and the
    victim list - `manors` and `religious` are overlap TARGETS (protected FROM structs by the
    matrix), but nothing about being a target keeps a compound off the patrol road, so both ride
    along here explicitly."""
    ring_rd = M.get("ring_road")
    if not ring_rd:
        return
    rbed = (M.get("ring_road_width", 15) - 6) / 2

    def _rfoot(it: dict[str, Any]) -> list[tuple[float, float]]:
        if "rot" in it:
            return rect_corners(it)
        rhw, rhh = it["w"] / 2, it["h"] / 2
        return [(it["x"] - rhw, it["y"] - rhh), (it["x"] + rhw, it["y"] - rhh), (it["x"] + rhw, it["y"] + rhh), (it["x"] - rhw, it["y"] + rhh)]

    # ...except an official NOTICE BOARD inside a GATE PRECINCT. A kosatsuba is street furniture,
    # not a compound: a ~12x5 ft post-and-roof board that must stand within ~60 real ft of a road
    # where people pass (kosatsuba_by_the_road), which at a gate means the same crowded verge the
    # guard house, inspection station and towers already line. Scoped to the precinct on purpose -
    # a board out on an open stretch of patrol lane is still a defect.
    rr_gates = [g for g in (M.get("gates") or [])] + ([M["gate"]] if M.get("gate") else [])

    def _rr_exempt(it: dict[str, Any]) -> bool:
        return it.get("label") in (None, "notice board") and "vw" in it and any(math.hypot(it["x"] - g[0], it["y"] - g[1]) < 130 for g in rr_gates)

    on_ring = [
        it.get("name") or it.get("label") or it.get("kind") or "compound" for it in solid_structs(M, "religious", "manors") if footprint_on_line(_rfoot(it), ring_rd, rbed) and not _rr_exempt(it)
    ]
    on_ring += ["field:" + f["name"] for f in M.get("fields", []) if footprint_on_line(f["outline"], ring_rd, rbed)]
    check(
        "ring_road_kept_clear",
        not on_ring,
        f"the ring road must run CLEAR of buildings/civic compounds/fields (only the gate guard houses, inspection stations, towers and gated ward fences may sit on it): {sorted(set(on_ring))}",
    )


def matrix_extents(M: Mapping[str, Any]) -> list[tuple[str, list[tuple[float, float]], Any, Any]]:
    """Every DRAWN extent as (key, polygon, own_id, parent_id).

    DRAWN, not recorded. Several features store an ENVELOPE far larger than the ink inside it - a
    paddy field's smoothed `outline` bows well outside its plots, a grove's `poly` is a belt outline
    whose ink is its clumps, a commons `poly` surrounds a sparse grass scatter. A survey that
    compared envelopes reported 101 overlapping pairs pool-wide, roughly half of them artifacts of
    exactly that; a matrix built on envelopes would inherit those, cry wolf, and be switched off.
    So this reads what is actually inked, and permissive classes are not extracted at all.
    """
    out: list[tuple[str, list[tuple[float, float]], Any, Any]] = []
    for k, cls in OVERLAP_CLASS.items():
        if cls in _MATRIX_PERMISSIVE:
            continue
        rec = M.get(k)
        recs: list[Any] = [rec] if isinstance(rec, dict) and "x" in rec else (rec if isinstance(rec, list) else [])
        pfield = _MATRIX_PARENT_FIELD.get(k)
        if k == "wards":
            # the fence LINE at a hair's width: a fence is thin, and a generous stroke would
            # manufacture defects out of houses that merely front it
            for wd in recs:
                for q in _mx_stroke(wd.get("boundary") or [], 2.5):
                    out.append((k, q, None, None))
        elif k == "kido":
            # THE FULL DRAWN FOOTPRINT, AND IT IS TWO DIFFERENT THINGS (GM 2026-07-27: "in general
            # we always want overlap checks to use full footprints"). A ward gate is a roofed bar +
            # two posts + a guard box standing off to ONE flank, so no single centred w/h rect
            # describes it - and, carrying no w/h at all, it fell through every branch here and was
            # extracted as NOTHING. Classified, mounted, and completely invisible: a notice board
            # came to rest squarely on Nagahara's guard box with the gate green. That is the failure
            # _FIXTURE_MOUNTS was written to end, one level down - a mount list cannot help a
            # feature the extractor never reaches.
            #
            # The parts are then NOT interchangeable. The gateway (roof + posts) is a genuine
            # FIXTURE on the fence: the gate IS the opening, so it may stand on the ward line and on
            # the way it bars. The GUARD BOX is a small building on the verge beside it, and rides
            # no such permission - it is extracted as `kido_guard_box`, classed SOLID, so the matrix
            # forbids it against the fence, the roadbed and everything built. The GM's second
            # observation, same day: "ward gates seem to sometimes overlap with neighborhood walls".
            # They did - on oblique crossings, where the box sits along the lane and the fence does
            # not - and both cases were invisible because the whole gate rode the gateway's mount.
            #
            # `parts` is each drawn rect's ROTATED corner quad, recorded by the glyph itself, so
            # this is the ink and not a bounding box (the record also keeps `bbox`, which for a gate
            # at 45 degrees claims ~2x the ground the gate covers). All parts share ONE object id,
            # carried as both own-id and parent-id, so the existing annex-on-its-own-parent test
            # stops the pieces of one gate accusing each other; the key-tagged 3-tuple cannot
            # collide with another key's 2-tuple (x, y) id, so it excuses nothing but its own glyph.
            for o_ in recs:
                oid = (k, round(float(o_.get("x", 0)), 1), round(float(o_.get("y", 0)), 1))
                gq = [(round(float(q[0]), 1), round(float(q[1]), 1)) for q in (o_.get("guard") or [])]
                for qd in o_.get("parts") or []:
                    if len(qd) > 2:
                        poly = [(float(q[0]), float(q[1])) for q in qd]
                        is_guard = gq and [(round(a, 1), round(b, 1)) for a, b in poly] == gq
                        out.append(("kido_guard_box" if is_guard else k, poly, oid, oid))
        elif k in _MX_FIXTURE_BOX:
            # fixtures record their extent in their own vocabulary (a bridge stores span x deck-w, a
            # jetty a length, a sluice nothing at all), so each says how to read its drawn box
            for o_ in recs:
                bw, bh = _MX_FIXTURE_BOX[k](o_)
                out.append((k, _mx_rect({"x": o_["x"], "y": o_["y"], "w": bw, "h": bh, "rot": o_.get("rot", 0)}), (round(o_["x"], 1), round(o_["y"], 1)), None))
        elif k == "wells":
            for w_ in recs:
                r_ = float(w_.get("vr") or w_.get("r") or 8.0)
                out.append((k, [(w_["x"] + r_ * math.cos(i * math.pi / 6), w_["y"] + r_ * math.sin(i * math.pi / 6)) for i in range(12)], (round(w_["x"], 1), round(w_["y"], 1)), None))
        elif k == "pond":
            p_ = M.get("pond")
            if p_:
                out.append((k, [(p_[0] + p_[2] * math.cos(a_), p_[1] + p_[3] * math.sin(a_)) for a_ in [i * math.pi / 8 for i in range(16)]], None, None))
        elif k in ("road", "moat", "ring_road", "wall", "lane"):
            _w = {"road": float(M.get("road_width") or 26.0), "moat": float(M.get("moat_width") or 22.0), "ring_road": 20.0, "wall": 10.0, "lane": 6.0}[k]
            for q in _mx_stroke(M.get(k) or [], _w / 2):
                out.append((k, q, None, None))
        elif k == "torii":
            hw_, up_, dn_ = torii_halfbox(float(M.get("meta", {}).get("ftpx") or 1))
            for t_ in recs:
                if isinstance(t_, (list, tuple)) and len(t_) >= 2:
                    tx_, ty_ = float(t_[0]), float(t_[1])
                    out.append((k, [(tx_ - hw_, ty_ - up_), (tx_ + hw_, ty_ - up_), (tx_ + hw_, ty_ + dn_), (tx_ - hw_, ty_ + dn_)], None, None))
        elif k in _MX_LINE_W:
            for r2_ in recs:
                pl2 = r2_.get("poly") or r2_.get("pts")
                if not pl2:
                    continue  # pragma: no cover - defensive: every linear record carries a path
                par = r2_.get(pfield) if pfield else None
                for q in _mx_stroke(pl2, float(r2_.get("w") or _MX_LINE_W[k]) / 2):
                    out.append((k, q, None, par))
        else:
            for o_ in recs:
                if not isinstance(o_, dict):
                    continue  # pragma: no cover - defensive: classified keys store dicts
                par = o_.get(pfield) if pfield else None
                pid = tuple(par) if isinstance(par, list) else par
                if "x" in o_ and (o_.get("w") or o_.get("vw")):
                    out.append((k, _mx_rect(o_), (round(o_["x"], 1), round(o_["y"], 1)), pid))
                elif len(o_.get("poly") or o_.get("outline") or ()) > 2:
                    # POLYGON-ONLY records - a dry hatake plot stores `poly`/`crop`/`theta` and no
                    # x/w at all. An earlier cut of this extractor required x+w and so skipped every
                    # one of them SILENTLY, which made the very defect this feature exists to catch
                    # (a dry crop plot in a watercourse) disappear from its own dry run. A feature
                    # that is never extracted looks exactly like a feature with nothing wrong.
                    # `outline` is the same shape under another name (a flower bed's ring), and it
                    # cost exactly that silence until 2026-07-27.
                    out.append((k, [(q[0], q[1]) for q in (o_.get("poly") or o_["outline"])], None, pid))
    return out


class GridIndex:
    """A uniform-grid spatial index for the "what is near here?" queries several checks make
    THOUSANDS of times against the same features. Each item is inserted under every cell its
    influence bbox touches; a query returns only the items in the queried cell(s), which is a
    superset of the true neighbors, so the caller still runs its exact test - the index prunes,
    it never decides.

    WHY (profiled 2026-07-25, after a feature spent an hour and the gate was suspected): the
    naive form is a full scan per query, and two checks were doing exactly that.
    `city_fan_heads_quilted` tested each of ~3,000 canal-side sample points against EVERY plot
    polygon and ditch on the map - 14M segment-distance calls, ~58% of Tango's 17s gate.
    `structures_clear_of_trees` tested every structure against every drawn crown - 1,049 x 7,440
    on Tango. Both are point-vs-local-geometry questions, so pruning to the local cell is a pure
    constant-factor win with identical verdicts (the gate's whole regression corpus is replayed
    against the pre-index results to prove that).

    Cell size is the one tuning knob: too small wastes memory on cell lists, too large stops
    pruning. Pick it near the size of the features being indexed."""

    __slots__ = ("cell", "bins")

    def __init__(self, cell: float) -> None:
        self.cell = max(float(cell), 1.0)
        self.bins: dict[tuple[int, int], list[Any]] = {}

    def add(self, x0: float, y0: float, x1: float, y1: float, payload: Any) -> None:
        """Index `payload` under every cell its influence bbox touches."""
        c = self.cell
        for gx in range(int(x0 // c), int(x1 // c) + 1):
            for gy in range(int(y0 // c), int(y1 // c) + 1):
                self.bins.setdefault((gx, gy), []).append(payload)

    def near(self, x: float, y: float) -> list[Any]:
        """Candidates whose influence bbox may reach (x, y). Empty list when nothing is close."""
        return self.bins.get((int(x // self.cell), int(y // self.cell)), [])

    def near_rect(self, x0: float, y0: float, x1: float, y1: float) -> list[Any]:
        """Candidates near any part of a rect, de-duplicated by identity (an item spanning several
        of the queried cells is returned once)."""
        c = self.cell
        seen: dict[int, Any] = {}
        for gx in range(int(x0 // c), int(x1 // c) + 1):
            for gy in range(int(y0 // c), int(y1 // c) + 1):
                for it in self.bins.get((gx, gy), ()):
                    seen[id(it)] = it
        return list(seen.values())


def forest_reveal_x(forest: Poly, edge: Any, reveal: float, w: float) -> list[float]:
    """Mirror of settlement.forest_reveal_x (keep in sync): the x-values a canvas-filling FOREST
    contributes to the frame. The wood is drawn to the canvas edge, but the crop reveals only the
    tree line plus `reveal` px of canopy behind it - deeper in it is identical crowns, and holding
    the frame open for them is wasted image. This is the crop rule, so crop_hugs_content (which
    gates how tight the crop is) has to measure by exactly the same rule."""
    if not edge:
        return [min(max(p[0], 0), w) for p in forest]
    ex = [min(max(p[0], 0), w) for p in edge]
    return ex + [min(x + reveal, w) for x in ex]


def torii_halfbox(ftpx: float, span_ft: float = 16.0) -> tuple[float, float, float]:
    """Mirror of settlement.torii_halfbox (keep in sync): the true drawn half-extents (x half-width, y-up,
    y-down) of a torii glyph at scale `ftpx`, plus a small stroke pad. Replaces the legacy fixed x+/-19 /
    y-10..+18 box (the pre-true-scale 38px glyph, ~5x oversized), used to check torii sit within the frame."""
    s2 = (span_ft / ftpx) / 2
    pad = 2.0
    return s2 + pad, s2 * 7.0 / 19.0 + pad, s2 * 17.0 / 19.0 + pad


# STANDALONE plank-footbridge usefulness (mirrors settlement.PLANK_BANK_REACH / PLANK_VILLAGE_REACH /
# PLANK_ABUTMENT - keep in sync). A footplank is worth building only if BOTH banks reach ground someone
# walks to; the placement engine (channel_footbridges) enforces it, these checks re-verify from the manifest.
FOREST_REVEAL_FT = 110.0  # mirrors settlement.FOREST_REVEAL_FT - how deep the crop reveals a canvas-filling wood

# Mirrors settlement._CANOPY_STRUCT_KEYS (keep in sync): every ROOFED structure a tree may not be drawn on.
CANOPY_STRUCT_KEYS = (
    "houses",
    "buildings",
    "storehouses",
    "flophouses",
    "byres",
    "farm_sheds",
    "religious",
    "shrines",
    "manors",
    "ministries",
    "inspection_stations",
    "merchant_estates",
    "fire_towers",
    "drum_towers",
    "breweries",
    "pawnshops",
    "bathhouses",
    "oil_presses",
    "kilns",
    "farriers",
    "mausoleums",
    "gate_structs",
    "wall_towers",
    "martial_halls",
    "dojos",
)

# Martial training in a provincial city (GM 2026-07-25). The first two mirror
# settlement.DOJO_SAMURAI_FRAC / DOJO_PER_SAMURAI - keep in sync, they are the roll the gate holds
# the map to. RANGE_FT is the kyudo standard 28 m shot (92 ft), rounded down to the ~90 ft clear
# lane the Mode A azuchi already uses. QUARTER_PX is "in or against the samurai neighborhood" at the
# city rung (3 ft/px -> ~780 real ft, about a quarter's width), not a precise siting rule.
DOJO_SAMURAI_FRAC = 0.10

DOJO_PER_SAMURAI = 200

DOJO_RANGE_FT = 90.0

DOJO_QUARTER_PX = 260.0

FOOT_ABUTMENT = 6.0  # deck = local ditch width + this abutment (settlement.PLANK_ABUTMENT)

FOOT_BANK_REACH = 11.0  # px past the abutment where a bank opens onto the terrain it lands on

FOOT_VILLAGE_REACH = 55.0  # a bank within this of a dwelling reaches the village (a place worth crossing to)


def _footbridge_useful_ground(M: Manifest) -> Any:
    """Return good(x, y) -> True when (x, y) sits on ground a field-worker walks TO: cultivated field
    (wet paddy / dry crop), the village (a dwelling within reach), or a walked polder dike. A plank whose
    far bank fails this opens onto reed marsh / scrub / off-map and connects the fields to nowhere."""
    crop = [f["outline"] for f in M.get("fields", []) if f.get("outline")]
    crop += [d["poly"] for d in M.get("dry_plots", [])]
    dikes = [dk["outline"] for dk in M.get("dikes", []) if dk.get("outline")]
    houses = M.get("houses", [])

    def good(x: float, y: float) -> bool:
        return any(point_in_poly(x, y, p) for p in crop) or any(point_in_poly(x, y, p) for p in dikes) or any((x - h["x"]) ** 2 + (y - h["y"]) ** 2 < FOOT_VILLAGE_REACH**2 for h in houses)

    return good


def _ditch_plankable(pts: Poly, w: float, good: Any) -> bool:
    """True if some point along the ditch has USEFUL ground (per `good`) on BOTH banks - i.e. it separates
    two places worth crossing between, so it warrants a footplank. A MARGIN/toe ditch (cultivation on one
    side, marsh/scrub on the other for its whole run) is not plankable and needs no plank (GM 2026-07-22)."""
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg)  # always >= FB_MIN at the one call site (the long-ditch loop pre-filters by length)
    reach = (w + FOOT_ABUTMENT) / 2 + FOOT_BANK_REACH
    step = max(8.0, total / 40)
    s = 0.0
    while s <= total:
        acc = 0.0
        for i, sl in enumerate(seg):
            if acc + sl >= s or i == len(seg) - 1:
                fr = (s - acc) / sl if sl else 0.0
                ax, ay = pts[i]
                bx, by = pts[i + 1]
                px, py = ax + (bx - ax) * fr, ay + (by - ay) * fr
                a = math.radians(math.degrees(math.atan2(by - ay, bx - ax)) + 90.0)  # deck axis, across the ditch
                ux, uy = math.cos(a), math.sin(a)
                if good(px + ux * reach, py + uy * reach) and good(px - ux * reach, py - uy * reach):
                    return True
                break
            acc += sl
        s += step
    return False


def poly_gap(a: Poly, b: Poly) -> float:
    """Minimum distance between two polygons; 0.0 if they overlap, touch, or one contains the other."""
    na, nb = len(a), len(b)
    if any(point_in_poly(x, y, b) for x, y in a) or any(point_in_poly(x, y, a) for x, y in b):
        return 0.0
    if any(segments_cross(a[i], a[(i + 1) % na], b[j], b[(j + 1) % nb]) for i in range(na) for j in range(nb)):
        return 0.0
    return min(min(poly_dist(x, y, b) for x, y in a), min(poly_dist(x, y, a) for x, y in b))


def check_theater_stage(M: Manifest, check: Check) -> None:
    """The theater stage's siting. It BELONGS to a temple/monastery precinct (a temple OPERA STAGE / shrine
    NOH stage), the audience gathering in the open ground between stage and hall, the stage FACING the hall:
    (1) `theater_stage_clear` - the stage + its viewing ground sit in CLEAR ground, overlapping NOTHING (no
        wall, moat, road, street/alley, watercourse, building, compound, grave, field, or pond). Unlike a
        packed dwelling it is not auto-checked by the generic overlap pass, so this is its dedicated guard.
    (2) `theater_stage_by_temple` - ADJACENT to a religious hall (center within ~260px of the nearest one).
    (3) `theater_stage_faces_temple` - its viewing ground OPENS TOWARD that hall (the stage faces it). The
        glyph's open side is local +y, so after `rot` it points (-sin, cos); that aligns with the hall."""
    ts_raw = M.get("theater_stage")
    # LIST since 2026-08-10 (the singleton write clobbered a second stage); old manifests carry a dict
    ts_all = ts_raw if isinstance(ts_raw, list) else ([ts_raw] if ts_raw else [])
    if not ts_all:
        return
    ts_hits: list[str] = []
    ts_far: list[str] = []
    ts_back: list[str] = []
    for ts in ts_all:
        _theater_one_stage(M, ts, ts_hits, ts_far, ts_back)
    check(
        "theater_stage_clear",
        not ts_hits,
        f"theater stage footprint(s) overlap {sorted(set(ts_hits))[:6]} - the stage and its viewing ground "
        f"must sit in CLEAR ground, touching nothing (no wall, moat, road, street/alley, watercourse, "
        f"building, compound, grave, field, or pond)",
    )
    if M.get("religious"):
        check(
            "theater_stage_by_temple",
            not ts_far,
            f"monzen theater stage(s) far from every temple/monastery: {ts_far[:3]} (want <= 260px) - a temple/shrine "
            f"performance stage sits ADJACENT to a religious hall with the viewing ground between them "
            f"(a commercial quarter theater takes kind='machi' and owes no hall)",
        )
        check(
            "theater_stage_faces_temple",
            not ts_back,
            f"monzen theater stage(s) whose viewing ground does not OPEN toward the temple: {ts_back[:3]} (alignment "
            f"want >= 0.5) - the stage faces the hall with the audience between; set `rot` so the ground opens "
            f"toward the temple (the stage's back is the side AWAY from the audience)",
        )


def _theater_one_stage(M: Manifest, ts: dict[str, Any], ts_hits: list[str], ts_far: list[str], ts_back: list[str]) -> None:
    """One stage's share of check_theater_stage: clear-ground hits for every stage; the temple
    adjacency/facing verdicts only for a MONZEN (temple) stage - kind='machi' is the commercial
    quarter theater and sits in the fabric, not at a hall."""
    # (1) CLEAR: build the full footprint (the viewing ground PLUS the roofed stage straddling its north edge)
    w, h = ts["w"], ts["h"]
    sh = h * 0.26
    cyl, fh = -sh * 0.25, h + sh * 0.5
    thr = math.radians(ts.get("rot", 0))
    ca, sa = math.cos(thr), math.sin(thr)
    sc = [(ts["x"] + dx * ca - dy * sa, ts["y"] + dx * sa + dy * ca) for dx, dy in ((-w / 2, cyl - fh / 2), (w / 2, cyl - fh / 2), (w / 2, cyl + fh / 2), (-w / 2, cyl + fh / 2))]
    hits = []
    lines = []  # linear barriers (name, polyline, half-width)
    if M.get("wall"):
        lines.append(("the wall", M["wall"], 9))
    if M.get("moat"):
        lines.append(("the moat", M["moat"], M.get("moat_width", 26) / 2 + 4))
    if M.get("road"):
        lines.append(("a road", M["road"], M.get("road_width", 26) / 2))
    if M.get("ring_road"):
        lines.append(("the ring road", M["ring_road"], M.get("ring_road_width", 15) / 2))
    lines += [("a street", st["pts"], st.get("w", 18) / 2) for st in M.get("town_streets", [])]
    lines += [("an alley", a["pts"], a.get("w", 10) / 2) for a in M.get("alleys", [])]
    lines += [("a stream", s["poly"], s.get("w", 9) / 2) for s in M.get("streams", [])]
    lines += [("a channel", c["poly"], c.get("w", 2.5) / 2 + 2) for c in M.get("channels", [])]
    lines += [("the canal", c["poly"], c.get("w", 12) / 2 + 2) for c in M.get("canals", [])]
    for nm, pts, hw in lines:
        if len(pts) >= 2 and footprint_on_line(sc, pts, hw):
            hits.append(nm)
    granary = M.get("granary")  # solid features (buildings, compounds, graves)
    solids = (
        [s for k in _OVERLAP_STRUCTS if k != "theater_stage" for s in M.get(k, [])]  # a stage is not its own obstacle; stage-vs-stage is the generic matrix's business now
        + M.get("manors", [])
        + M.get("religious", [])
        + M.get("shrines", [])
        + M.get("gate_structs", [])
        + M.get("storehouses", [])
        + M.get("merchant_estates", [])
        + M.get("threshing_yards", [])
        + M.get("gardens", [])
        + M.get("inspection_stations", [])
        + (granary["stores"] if granary else [])
    )
    if M.get("governor_mansion"):
        solids.append(M["governor_mansion"])
    for r in solids:
        if abs(r["x"] - ts["x"]) + abs(r["y"] - ts["y"]) <= 440 and sat_overlap(sc, rect_corners(_struct_rect(r))):
            hits.append(f"a {r.get('kind', 'building')}")
    for fkey in ("fields", "fallow_patches", "flower_fields"):  # areas: paddies/fields and the pond
        for fld in M.get(fkey, []):
            ol = fld["outline"]
            if any(point_in_poly(px, py, ol) for px, py in sc) or any(point_in_poly(vx, vy, sc) for vx, vy in ol):
                hits.append("a field")
                break
    pond = M.get("pond")
    if pond and (
        point_in_poly(pond[0], pond[1], sc)  # pond engulfed by the stage, OR a stage corner in the pond
        or any(((px - pond[0]) / (pond[2] + 6)) ** 2 + ((py - pond[1]) / (pond[3] + 6)) ** 2 <= 1.0 for px, py in sc)
    ):
        hits.append("the pond")
    ts_hits += hits
    halls = M.get("religious", [])
    if not halls:
        return
    # EVERY stage faces a temple (GM 2026-08-10). A `machi` kind was briefly exempted here on
    # the research finding that a capital's entertainment district is commercial - but the
    # SETTING rule is older and governs: a Rokugani stage belongs to a hall and opens toward it,
    # whoever pays for the troupe. The kind still records which doctrine sited the stage; it no
    # longer excuses the facing.
    nearest = min(halls, key=lambda h: math.hypot(ts["x"] - h["x"], ts["y"] - h["y"]))
    near = math.hypot(ts["x"] - nearest["x"], ts["y"] - nearest["y"])
    if near > 260:
        ts_far.append(f"({round(ts['x'])},{round(ts['y'])}) {round(near)}px out")
    th = math.radians(ts.get("rot", 0))
    ox, oy = -math.sin(th), math.cos(th)  # the viewing ground's open direction (toward the audience/temple)
    dx, dy = nearest["x"] - ts["x"], nearest["y"] - ts["y"]
    d = math.hypot(dx, dy) or 1.0
    facing = (ox * dx + oy * dy) / d
    if facing < 0.5:
        ts_back.append(f"({round(ts['x'])},{round(ts['y'])}) alignment {facing:.2f}")


def check_fire_features(M: Manifest, check: Check) -> None:
    """Geometry of the fire-watch towers (hinomi-yagura) a walled town or a city draws. Scale-agnostic:
    the PRESENCE/count checks live in the scale blocks; this validates whatever is drawn, so it is a
    no-op for a settlement that has none. WHY (a dense, enclosed wooden core needs a fire-watch over
    its rooftops, manned by the magistrate's watch): settlements.md 'Fire towers'."""
    towers = M.get("fire_towers", [])
    # A tower's WATCH RADIUS: the visual neighborhood of rooftops one hinomi-yagura usefully covers.
    # Both clauses below share it - a tower more than one radius from any dwelling watches nothing,
    # and two towers within one radius of EACH OTHER watch the same rooftops twice.
    WATCH = 230
    COMMON = {"laborer", "laborer_large", "servant", "merchant", "merchant_house", "merchant_large", "shop"}
    SAM = {"samurai", "samurai_large"}
    dwell = [(b["x"], b["y"], b.get("kind")) for b in M.get("buildings", []) if b.get("kind") in COMMON | SAM]
    if towers and dwell:
        misplaced = []
        for t in towers:
            near = sorted(dwell, key=lambda d: math.hypot(d[0] - t["x"], d[1] - t["y"]))[:3]
            nearest = math.hypot(near[0][0] - t["x"], near[0][1] - t["y"])
            sam = sum(1 for d in near if d[2] in SAM)
            if nearest > WATCH or sam * 2 > len(near):  # isolated, or sitting in the samurai quarter
                misplaced.append((round(t["x"]), round(t["y"])))
        check("fire_tower_in_commoner_quarter", not misplaced, f"fire tower(s) {misplaced} sit isolated or in the samurai quarter - a hinomi-yagura watches the dense COMMONER rooftops")
    # a fire tower stands in the dense built-up core, never ON cultivated ground: a hinomi-yagura on a
    # paddy (or the in-wall chrysanthemum field / a fallow patch) is nonsense, and an in-wall agricultural
    # district puts a real field right where a tower might land. (There is no blanket no_structure_on_field
    # - farmhouses legitimately ring the fields - so the towers carry their own field-clearance check.)
    fields = [f["outline"] for f in M.get("fields", [])] + [f["outline"] for f in M.get("fallow_patches", [])] + [f["outline"] for f in M.get("flower_fields", [])]
    if towers and fields:
        on_field = []
        for t in towers:
            rc = rect_corners(_struct_rect(t))
            for ol in fields:
                n = len(ol)
                if any(point_in_poly(cx, cy, ol) for cx, cy in rc) or any(segments_cross(rc[i], rc[(i + 1) % 4], ol[e], ol[(e + 1) % n]) for i in range(4) for e in range(n)):
                    on_field.append((round(t["x"]), round(t["y"])))
                    break
        check("fire_tower_clear_of_fields", not on_field, f"fire tower(s) {on_field} sit on a field - a hinomi-yagura stands in the dense urban core, never on a paddy or planting")
    # MULTIPLE TOWERS DISPERSE. A settlement dense/populous enough to warrant a second tower gets it
    # to watch a DIFFERENT quarter's rooftops: historically the fire-watch was parcelled out per
    # neighborhood (in Edo each machi block-group kept its own hinomi-yagura, and the shogunate's
    # official watch stations were likewise distributed one to a district), so towers were spread
    # across the city, never bunched. Two towers inside one watch radius of each other duplicate
    # coverage while some other dense quarter goes unwatched - the second tower accomplishes nothing.
    # WHY: settlements.md "Fire towers".
    if len(towers) >= 2:
        bunched = [((round(a["x"]), round(a["y"])), (round(b["x"]), round(b["y"]))) for i, a in enumerate(towers) for b in towers[i + 1 :] if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < WATCH]
        check(
            "fire_towers_dispersed",
            not bunched,
            f"fire tower pair(s) {bunched} stand within one watch radius ({WATCH} px) of each other - a second "
            f"hinomi-yagura exists to watch a DIFFERENT quarter's rooftops; spread them across the settlement",
        )
    # EACH TOWER STANDS AMID THE DISTRICT IT WATCHES. Dispersal alone is not enough: two towers a
    # comfortable distance apart can still both sit in the SAME QUADRANT, leaving the dense commoner
    # quarter across the city unwatched (Tango's original pair both stood NW of center while the NE
    # laborer warren - the city's biggest rooftop mass - had no watch). Historically the watch was
    # parcelled by district, every commoner roof belonging to SOME tower's watch, and the tower stood
    # amid its blocks (it watched outward over rooftops on all sides, not a district it sat at the far
    # edge of). So: assign every commoner dwelling to its NEAREST tower - that partition IS the de
    # facto watch districting the drawn towers imply - and each tower must stand near its district's
    # center of mass: offset <= max(0.9 x the district's RMS radius, one WATCH radius). A tower parked
    # in the wrong quadrant inherits the whole far side of the city as its "district" and lands far
    # off that centroid, which is exactly the failure. Inside the walls only, when walled - the
    # extramural gate-market rows are not part of the enclosed core the towers exist for.
    # WHY: settlements.md "Fire towers".
    wallp = M.get("wall")
    core = [d for d in dwell if d[2] not in SAM and (not wallp or point_in_poly(d[0], d[1], wallp))]
    if len(towers) >= 2 and core:
        offside = []
        for ti, t in enumerate(towers):
            g = [d for d in core if ti == min(range(len(towers)), key=lambda j: math.hypot(d[0] - towers[j]["x"], d[1] - towers[j]["y"]))]
            if not g:
                continue
            gx, gy = sum(d[0] for d in g) / len(g), sum(d[1] for d in g) / len(g)
            rms = math.sqrt(sum((d[0] - gx) ** 2 + (d[1] - gy) ** 2 for d in g) / len(g))
            off = math.hypot(t["x"] - gx, t["y"] - gy)
            if off > max(0.9 * rms, WATCH):
                offside.append((round(t["x"]), round(t["y"]), round(off), round(rms)))
        check(
            "fire_tower_amid_its_district",
            not offside,
            f"fire tower(s) {offside} (x, y, offset, district rms) stand far off the center of the rooftop "
            f"district they are nearest to - the towers are bunched in one part of the city while a dense "
            f"commoner quarter goes unwatched; put one tower AMID each major commoner quarter",
        )
    # A TOWER KEEPS A SMALL STANDOFF FROM ITS NEIGHBORS (>= 5 px of daylight). The blanket
    # no_structure_overlaps SAT test only catches true footprint intersection, so a tower butted
    # flush against a house passes it while READING as a collision: the drawn glyph's roof cap
    # overhangs the recorded frame by ~2px a side, and an open braced-timber tower needs its
    # footing and ladder clear of the neighboring eaves anyway (it stands on a seam, not in a
    # party-wall row). GM rule: at least 5 px between a fire tower and any neighboring building.
    STANDOFF = 5
    if towers:
        neigh = [s for k in _OVERLAP_STRUCTS if k != "fire_towers" for s in M.get(k, [])]
        crowded = []
        for t in towers:
            tc = rect_corners(_struct_rect(t))
            for s in neigh:
                sc = rect_corners(_struct_rect(s))
                if math.hypot(t["x"] - s["x"], t["y"] - s["y"]) > 160:  # cheap prefilter
                    continue
                gap = min(min(seg_dist(px, py, sc[i], sc[(i + 1) % 4]) for px, py in tc for i in range(4)), min(seg_dist(px, py, tc[i], tc[(i + 1) % 4]) for px, py in sc for i in range(4)))
                if sat_overlap(tc, sc) or gap < STANDOFF:
                    crowded.append((round(t["x"]), round(t["y"]), round(gap, 1)))
                    break
        check(
            "fire_tower_standoff",
            not crowded,
            f"fire tower(s) {crowded} (x, y, gap px) stand within {STANDOFF} px of a neighboring building - "
            f"the open braced frame (and its overhanging roof cap) needs a little daylight around its footing; "
            f"nudge the tower onto clearer ground",
        )
    # A TOWER NEVER STANDS ON A WELLHEAD. Wells are overlap-EXEMPT (a wellhead's nominal footprint
    # may kiss a dense-city building - see _OVERLAP_EXEMPT), so neither the blanket
    # no_structure_overlaps pass nor fire_tower_standoff above (which walks _OVERLAP_STRUCTS only)
    # guards a tower dropped onto a well. But that exemption is about houses ringing a tenement
    # court closely - a fire tower must not ride it: its braced footing would stand in the well
    # court blocking the shared draw-point, and the two glyphs read as a plain collision. Same
    # 5 px daylight rule as fire_tower_standoff; circle (the well's clearance disc, radius r,
    # as in wells_clear_of_shrine_and_torii) vs the tower's rect.
    wells = M.get("wells", [])
    if towers and wells:
        on_well = []
        for t in towers:
            hw, hh = t["w"] / 2, t["h"] / 2
            for wl in wells:
                ddx = wl["x"] - t["x"] - max(-hw, min(hw, wl["x"] - t["x"]))
                ddy = wl["y"] - t["y"] - max(-hh, min(hh, wl["y"] - t["y"]))
                if math.hypot(ddx, ddy) < wl["r"] + STANDOFF:
                    on_well.append((round(t["x"]), round(t["y"])))
                    break
        check(
            "fire_tower_clear_of_wells",
            not on_well,
            f"fire tower(s) {on_well} stand on (or within {STANDOFF} px of) a wellhead - a hinomi-yagura's footing must not block a quarter's shared draw-point; nudge the tower off the well court",
        )
    # ... and clear of GRAVEYARDS (GM, 2026-07): a watch-tower's braced footing planted among
    # the graves reads as a plain collision - the dead get the same daylight as the living
    cems = M.get("cemeteries", [])
    if towers and cems:
        on_grave = []
        for t in towers:
            tc = rect_corners({"x": t["x"], "y": t["y"], "w": t["w"] + 2 * STANDOFF, "h": t["h"] + 2 * STANDOFF, "rot": 0})
            for cm in cems:
                if sat_overlap(tc, rect_corners({"x": cm["x"], "y": cm["y"], "w": cm["w"], "h": cm["h"], "rot": 0})):
                    on_grave.append((round(t["x"]), round(t["y"])))
                    break
        check("fire_tower_clear_of_graveyards", not on_grave, f"fire tower(s) {on_grave} stand on (or within {STANDOFF} px of) a graveyard - move the watch-tower off the burial ground")


def water_setback(width: float) -> float:
    """The set-back a BURIAL ground keeps from the EDGE of open water, scaling with the waterway's
    width: even a narrow STREAM floods graves out, so the floor is a solid ~75px; a moat (the heaviest
    watercourse, ~26px wide -> ~130px) more still, a river or canal most. A burial ground by big water
    floods out, so the bigger the watercourse the further back the dead must lie. (Thin irrigation
    channels are not open water and are not checked at all.)"""
    return max(75, min(140, 5.0 * width))


def _ward_interior(fence: Any, wall: Any) -> Any:
    """Close a samurai-ward FENCE polyline against the city wall ring: the ward's interior polygon.

    The fence's ends abut the rampart (city_ward_fence_meets_wall holds that), so the fence plus
    the wall arc between its ends encloses the ward. Two arcs qualify; the ward is the SMALLER
    enclosed region - a ward is a quarter carved off the city, never the larger half (all three
    pool cities measure 21-25% of the walled area). None when there is nothing to close (no wall
    ring / a degenerate fence) - the caller skips rather than guesses. Deliberately independent of
    settlement.ward_interior: the check must not trust the arithmetic of the engine it grades."""
    if not wall or len(wall) < 3 or not fence or len(fence) < 2:
        return None
    # ARC-LENGTH closure, not nearest-VERTEX closure: a fence end abuts the rampart mid-EDGE, so
    # walking vertex indices from "the nearest vertex" can skip (or wrongly include) the vertex on
    # the far side of the junction, and the resulting polygon self-intersects - a bowtie, whose
    # shoelace area under-measures by cancellation and steals the smaller-area vote (caught by the
    # square-wall unit test). Projecting each end onto the ring and collecting the vertices whose
    # arc position lies strictly between the two junctions, in traversal order, yields a SIMPLE
    # polygon for both candidate closures, so the smaller-area rule is sound.
    ring = list(wall) + [wall[0]]
    arcs = [0.0]
    for i in range(len(ring) - 1):
        arcs.append(arcs[-1] + math.hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]))
    perim = arcs[-1]
    if perim <= 0:
        return None

    def project(p: Any) -> float:
        best: tuple[float, float] | None = None
        for i in range(len(ring) - 1):
            ax, ay = ring[i]
            bx, by = ring[i + 1]
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))
            qx, qy = ax + t * dx, ay + t * dy
            d = (p[0] - qx) ** 2 + (p[1] - qy) ** 2
            if best is None or d < best[0]:
                best = (d, arcs[i] + t * math.sqrt(length2))
        return 0.0 if best is None else best[1]

    def area(poly: Any) -> float:
        a = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            a += x1 * y2 - x2 * y1
        return abs(a) / 2

    t0, t1 = project(fence[-1]), project(fence[0])
    fwd_span = (t1 - t0) % perim
    fwd = sorted(((arcs[i] - t0) % perim, wall[i]) for i in range(len(wall)))
    arc_fwd = [v for o, v in fwd if 1e-6 < o < fwd_span - 1e-6]
    back = sorted(((t0 - arcs[i]) % perim, wall[i]) for i in range(len(wall)))
    arc_back = [v for o, v in back if 1e-6 < o < (perim - fwd_span) - 1e-6]
    pa = list(fence) + arc_fwd
    pb = list(fence) + arc_back
    return pa if area(pa) <= area(pb) else pb


def edge_dist(px: float, py: float, poly: Poly) -> float:
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def in_ellipse(px: float, py: float, e: Any, scale: float = 1.0) -> bool:
    cx, cy, rx, ry = e
    return bool(((px - cx) / (rx * scale)) ** 2 + ((py - cy) / (ry * scale)) ** 2 <= 1.0)


def polyline_len(poly: Poly) -> float:
    return sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))


def clip_poly_rect(poly: Poly, x0: float, y0: float, x1: float, y1: float) -> list[Any]:
    """Sutherland-Hodgman clip of a polygon to an axis rect; returns the clipped polygon (may be []).
    Used to find how much of an off-edge field actually shows inside the rendered map window."""

    def cl(pts: list[Any], ins: Callable[[Any], bool], isc: Callable[[Any, Any], tuple[float, float]]) -> list[Any]:
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            ia, ib = ins(a), ins(b)
            if ia:
                out.append(a)
            if ia != ib:
                out.append(isc(a, b))
        return out

    p: list[Any] = list(poly)
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


def onmap_field_edge(poly: Poly, x0: float, y0: float, x1: float, y1: float, eps: float = 8) -> float:
    """Length of a field's REAL boundary lying inside the map rect - EXCLUDING the segments that run
    along the rect edge (those are the off-map cut, where the field's farmhouses are off-screen).
    This is the on-map field frontage that ought to carry farmhouses."""
    cp = clip_poly_rect(poly, x0, y0, x1, y1)
    if len(cp) < 2:
        return 0.0
    total = 0.0
    for i in range(len(cp)):
        a, b = cp[i], cp[(i + 1) % len(cp)]
        on_rect = (
            (abs(a[0] - x0) < eps and abs(b[0] - x0) < eps)
            or (abs(a[0] - x1) < eps and abs(b[0] - x1) < eps)
            or (abs(a[1] - y0) < eps and abs(b[1] - y0) < eps)
            or (abs(a[1] - y1) < eps and abs(b[1] - y1) < eps)
        )
        if not on_rect:
            total += math.hypot(b[0] - a[0], b[1] - a[1])
    return total


def kido_quads(kd: Mapping[str, Any]) -> list[Poly]:
    """A ward gate's drawn footprint as its TRUE (rotated) parts - the roofed bar, its two posts and
    the guard box. Falls back to the axis-aligned `bbox` for a legacy manifest that never recorded
    the parts. Use this, not `bbox`, for any keep-clear rule: once a kido turns onto the lane it
    bars, its AABB can be half again the size of the glyph and reads as overlapping neighbors the
    gate plainly clears (Nagahara's SW gate at 115 degrees, GM 2026-07-26)."""
    parts = kd.get("parts")
    if parts:
        return [[(float(c[0]), float(c[1])) for c in q] for q in parts]
    bb = kd.get("bbox")
    if not bb:
        return []
    return [[(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3])]]


def footprint_on_line(sc: Poly, sp: Poly, hw: float) -> bool:
    """True if closed polygon sc overlaps polyline sp within half-width hw - a corner near a
    segment, a polyline vertex inside the polygon, or an edge crossing. sc may be a 4-corner
    building footprint OR a field outline. Used to test a footprint/field against a barrier
    (city wall stroke, moat)."""
    if any(seg_dist(cx, cy, sp[k], sp[k + 1]) < hw for (cx, cy) in sc for k in range(len(sp) - 1)):
        return True
    if any(point_in_poly(rx, ry, sc) for rx, ry in sp):
        return True
    return any(segments_cross(sp[k], sp[k + 1], sc[e], sc[(e + 1) % len(sc)]) for k in range(len(sp) - 1) for e in range(len(sc)))
