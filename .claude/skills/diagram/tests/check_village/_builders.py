"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import json
import math

from l7r.diagram import check_village

WALL = [[50, 50], [950, 50], [950, 950], [50, 950]]  # a simple square enclosure


def f(M):
    return set(check_village.gate(M, verbose=False))


def bldg(x, y, kind="merchant", rot=0, w=40, h=28, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "rot": rot, "kind": kind, **kw}


# ---- fixture builders -------------------------------------------------------------------------
# Every test below hands `gate()` a hand-built manifest containing only the keys ITS check reads.
# That is the right shape for a focused test, but it has a recurring tax: a feature record is often
# required to carry a key some OTHER check indexes unconditionally (a threshing yard's "of", a
# grove's "face"), and omitting it does not fail the test you are writing - it raises a KeyError
# from an unrelated check, which costs a fix-and-rerun cycle to diagnose. These builders carry the
# required keys so new tests do not rediscover them one crash at a time; pass **kw to override
# anything. `test_fixture_builders_survive_every_check` is the guarantee that they stay complete.
def manifest(**over):
    """A minimally-valid manifest: sane meta plus whatever feature lists the test supplies."""
    M = {"meta": {"scale": "village", "ftpx": 1, "W": 1000, "H": 1000}}
    M.update(over)
    return M


def house(x, y, kind="plain", rot=0, w=46, h=28, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "rot": rot, "kind": kind, **kw}


def yard(x, y, of=None, w=36, h=26, **kw):
    """A threshing yard. `of` (the house it belongs to) is indexed unconditionally - the omission
    that motivated these builders."""
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "of": list(of or (x, y)), **kw}


def garden(x, y, of=None, w=22, h=24, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "of": list(of or (x, y)), **kw}


def well(x, y, r=8, vr=12, **kw):
    """A wellhead. `r` is the clearance radius, `vr` the DRAWN head - checks use vr for overlap."""
    return {"x": x, "y": y, "r": r, "vr": vr, **kw}


def grove(x, y, of=None, w=40, h=30, face=(0, -1), **kw):
    """One arm of a per-house yashikirin belt."""
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "of": list(of or (x, y)), "face": list(face), **kw}


def vgrove(poly, role="windbreak", clumps=None, r=14, **kw):
    """A communal fengshui grove: an outline plus the clump centers actually drawn in it."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return {
        "x": sum(xs) / len(xs),
        "y": sum(ys) / len(ys),
        "w": max(xs) - min(xs),
        "h": max(ys) - min(ys),
        "rot": 0,
        "role": role,
        "r": r,
        "poly": [list(p) for p in poly],
        "clumps": [list(c) for c in (clumps if clumps is not None else [(sum(xs) / len(xs), sum(ys) / len(ys))])],
        **kw,
    }


# ---- channels_flow_downhill: a channel running uphill against the declared slope -----------
def _channel(start, end):
    return {"poly": [start, end], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}}


# ---- channels_join_streams_at_confluence (a drain culvert reaches INTO the receiving bed) ----
def _sink_channel(end):
    return {"poly": [[end[0] - 60, end[1] - 40], end], "frm": {"kind": "drain"}, "to": {"kind": "stream"}}


# ---- drainage flows downhill (matches meta.down_deg); a COLLECTOR may run cross-slope, but not uphill ----
def _drain(poly, stream=None):
    M = {"meta": {"down_deg": 45}, "field_ditches": [{"poly": poly, "role": "drain", "field": "f"}]}
    if stream:
        M["streams"] = [{"poly": stream, "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}]
    return M


# a bunsuiguchi head fork: 3 SUPPLY (main) ditches meet at (100,100) - the head-race in + two supply canals out
_FORK_MAINS = [
    {"poly": [[60, 60], [100, 100]], "role": "main", "field": "f"},
    {"poly": [[100, 100], [160, 100]], "role": "main", "field": "f"},
    {"poly": [[100, 100], [100, 160]], "role": "main", "field": "f"},
]


def _dryplot(x, theta):
    # a full ~40x36 parcel (one corner nipped): the furrows-vary adjacency radius now derives from the
    # plots' own mean size (1.25x side length, capped 50px), so the fixture plots must be REAL parcels -
    # the old sliver trapezoid (~790px^2) read as sub-30px plots whose radius no longer paired them
    return {"poly": [[x, 300], [x + 40, 300], [x + 40, 336], [x + 4, 336]], "theta": theta, "crop": "barley"}


# ---- paddy_bunds_clear_the_collector: a paddy's low bund is the ditch's BANK, never drawn
# through it (GM 2026-08-08, Hoshizora). down_deg=45 -> fall is SE, and the collector below runs
# along the contour on the line x + y = 1000, so a vertex with x + y > 1000 is past its centerline.
def _hem_M(ring, name="f", **fld):
    return {
        "meta": {"scale": "village", "down_deg": 45, "W": 1200, "H": 1200},
        "fields": [{**_field(name, 200, 200, 900, 900), "drain_hem": [ring], **fld}],
        "field_ditches": [{"poly": [[300, 700], [700, 300]], "role": "drain", "field": name, "w": 1.5, "w_tail": 6.0}],
    }


# ---- paddy_bunds_clear_the_supply_channels: a paddy's canal-side bund is the SUPPLY channel's
# bank, never drawn down the middle of the water (GM 2026-08-15, Inashiro). Scripted maps only
# (meta.generated_by - the migration doctrine; legacy comb maps inherit the rule at conversion).
# The ditch below runs straight down x=500 at 8px drawn width, so the gate's line is
# halfw + BANK_MARGIN - 0.15 = 4.6px and a vertex nearer x=500 than that is inside the stroke.
def _sup_M(ring, role="main", gen="hamletgen", ditch=None, name="f"):
    M = {
        "meta": {"scale": "hamlet", "down_deg": 90, "W": 1200, "H": 1200},
        "fields": [{**_field(name, 200, 200, 900, 900), "plot_rings": [ring]}],
        "field_ditches": [ditch or {"poly": [[500, 200], [500, 800]], "role": role, "field": name, "w": 8.0, "w_tail": 8.0}],
    }
    if gen:
        M["meta"]["generated_by"] = gen
    return M


_FIELD_400 = {"name": "f", "kind": "paddy", "outline": [[300, 300], [500, 300], [500, 500], [300, 500]], "bbox": [300, 300, 500, 500], "vis_bbox": [300, 300, 500, 500]}
_POND_FEED = {"poly": [[400, 400], [450, 450]], "frm": {"kind": "pond"}, "to": {"kind": "field", "name": "f"}, "w": 2.5}


# ---- town_monasteries_dedicated: wrong patron fortunes for the clan ------------------------
def _monastery(fortune):
    return {"kind": "monastery", "label": f"Monastery of {fortune}", "x": 0, "y": 0, "w": 10, "h": 10}


# ---- the on_<feature> overlap helpers: a structure that CONTAINS a feature vertex
# (point_in_poly path) and one the feature CROSSES (segments_cross path) ---------------------
FEAT = [[100, 500], [500, 500], [900, 500]]


def _feature_overlap(meta_extra, key, value, extra=None):
    A = bldg(500, 500, w=200, h=200)  # the feature's (500,500) vertex sits inside A (point_in_poly path)
    B = bldg(300, 500, w=16, h=300)  # the feature crosses B's edge (segments_cross path)
    C = bldg(200, 500, w=40, h=8)  # C's corner sits right on the feature (seg_dist path)
    M = {"meta": {"scale": "town", **meta_extra}, "buildings": [A, B, C], key: value}
    if extra:
        M.update(extra)
    return f(M)


# ---- field/water/channel FAIL branches ----------------------------------------------------
def _field(name, x0, y0, x1, y1):
    return {"name": name, "kind": "paddy", "bbox": [x0, y0, x1, y1], "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


# ---- field_supply_visibly_sourced: an undrawn supply conduit whose comb origin dangles -------
# (Tango fs3, GM 2026-07-24: the recorded tap sat on a stream vertex but nothing was DRAWN
# between stream and comb, so the main canal's head hung in open ground short of the bank)
def _supply_M(main_head, drawn_channels=None, drawn=False):
    # a stream along y=100 (w 9), a paddy at (300,300)-(600,600), one main ditch into it whose
    # head is `main_head`, and an undrawn supply conduit recorded stream -> field
    return {
        "meta": {"scale": "town", "W": 1000, "H": 1000},
        "streams": [{"poly": [[100, 100], [800, 100]], "w": 9}],
        "fields": [_field("x", 300, 300, 600, 600)],
        "field_ditches": [{"poly": [main_head, [450, 320], [460, 400]], "role": "main", "field": "x", "w": 4}],
        "channels": [{"poly": [[440, 104], [445, 180], main_head], "frm": {"kind": "stream"}, "to": {"kind": "field", "name": "x"}, "w": 2.5, "drawn": drawn}],
        "drawn_channels": drawn_channels or [],
    }


# ---- watercourses join, they do not cross (GM 2026-07-24, Enokida's polder laterals) --------
def _tips_M(lateral):
    # a paddy ringed by a horizontal main (top) and drain (bottom), both w 5 -> band half-width
    # 2.5, with one lateral spanning them; `lateral` is the lateral's polyline
    return {
        "meta": {"scale": "hamlet", "W": 400, "H": 400},
        "fields": [_field("x", 0, 0, 300, 300)],
        "field_ditches": [
            {"poly": [[0, 100], [300, 100]], "role": "main", "field": "x", "w": 5, "w_tail": 5},
            {"poly": [[0, 250], [300, 250]], "role": "drain", "field": "x", "w": 5, "w_tail": 5},
            {"poly": lateral, "role": "lateral", "field": "x", "w": 3.2, "w_tail": 2.4},
        ],
    }


def _cross_M(*strokes):
    return {"meta": {"scale": "hamlet", "W": 400, "H": 400}, "drawn_channels": [dict(s) for s in strokes]}


# ---- water-width ladder: ditch < creek < moat, with honest gaps ---------------------------
# Real wet-rice water systems are a tiered hierarchy (~2-4x per tier); the rendered map log-
# compresses that but must keep the ordering. A ditch is the thinnest line; a creek clearly
# beats it; the city moat dwarfs it and out-widths every natural stream (a feeder may equal it).
_CHAN = [[100, 100], [110, 120], [120, 140]]
_STRM = [[400, 100], [400, 300]]


# ---- dooryard kitchen garden: every farmstead has a saien on a sunny side -------------------
# Each fixture trips ONE garden check: the work yard was universal and so was the kitchen garden,
# so the gate enforces a garden per farmhouse, smaller than the house, on a sunny (not north) side,
# on dry ground, abutting only its own house.
def _farmhouse(x, y):
    return {"x": x, "y": y, "w": 44, "h": 29, "kind": "plain", "rot": 0}


# ---- SOFT ADVISORY: crop-limiting relocatable singleton ----
# a village that crops to content, with a pond stuck far EAST (sole east feature) and empty room between the
# NW houses and the SE paddy to move it into -> moving that one pond would crop the image much smaller
_POND_OUTLIER = {
    "meta": {"scale": "village", "view": [0, 0, 1400, 1000]},
    "houses": [{"x": 200, "y": 200, "w": 60, "h": 40, "rot": 0, "kind": "plain"}],
    "fields": [{"name": "f", "kind": "paddy", "vis_bbox": [600, 500, 1000, 900], "bbox": [600, 500, 1000, 900], "outline": [[600, 500], [1000, 500], [1000, 900], [600, 900]]}],
    "pond": [1300, 400, 90, 60],
}


# ---- SOFT ADVISORY: a SHRINE + its churchyard GRAVEYARD move as one relocatable GROUP ----
# The Hikari-no-Sato case: a village Bishamon shrine and the graveyard it is responsible for both sit at the
# far SW corner, so together they hold the S crop edge out. Removing the shrine ALONE leaves the graveyard
# pinning that edge (and vice versa) -> neither reads as a relocatable singleton; only weighed TOGETHER does
# the precinct free the corner, letting the image crop much smaller. The `shrines`/`religious` mirror pair,
# the cemetery, and the ablution well all move as one unit.
_SHRINE_GRAVEYARD_GROUP = {
    "meta": {"scale": "village", "view": [0, 0, 1400, 1200]},
    "houses": [{"x": 300, "y": 250, "w": 60, "h": 40, "rot": 0, "kind": "plain"}],
    "fields": [{"name": "f", "kind": "paddy", "vis_bbox": [500, 300, 1000, 700], "bbox": [500, 300, 1000, 700], "outline": [[500, 300], [1000, 300], [1000, 700], [500, 700]]}],
    "religious": [{"kind": "shrine", "x": 300, "y": 1050, "w": 90, "h": 60}],
    "shrines": [{"x": 300, "y": 1050, "w": 90, "h": 60}],
    "cemeteries": [{"x": 300, "y": 940, "w": 80, "h": 70, "rot": 0}],
    "wells": [{"x": 380, "y": 1050, "r": 8}],
}


def _grove(x, y, ofx, ofy, w=30, h=24):
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "of": [ofx, ofy], "face": [-1, -1]}


def _nuc_grid(n=12):
    return [_farmhouse(300 + 40 * (i % 6), 400 + 40 * (i // 6)) for i in range(n)]


def _nuc_village_M(houses, vgroves=None, **extra):
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses}
    if vgroves is not None:
        M["village_groves"] = vgroves
    M.update(extra)
    return M


def _nuc_with_windbreak():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx - 160, "y": ccy - 160, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # NW back grove
    return houses, ccx, ccy, _nuc_village_M(houses, wb)


def _big_grove(x, y, ofx, ofy):
    return _grove(x, y, ofx, ofy, w=44, h=34)  # area 1496 vs a 44x29=1276 house -> ~1.17x (substantial)


_CITY_WALL = [[100, 100], [900, 100], [900, 900], [100, 900]]  # a closed square wall


# ---- provincial-city checks (scale="city"); tango.gen.py is the passing integration ---------
WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # a closed city ring


def _city_with_samurai(label_box):
    sam = [bldg(400, 400, kind="samurai"), bldg(440, 400, kind="samurai"), bldg(420, 440, kind="samurai")]
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": sam, "labels": [label_box]}


def _merchant_city(buildings, estates=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if estates is not None:
        M["merchant_estates"] = estates
    return M


def _samurai_varied_city(buildings, manors=None):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if manors is not None:
        M["manors"] = manors
    return M


def _agri_city(houses, agri=True):
    # a city with an in-wall AGRICULTURAL field (the unusual jokamachi that farms inside the walls)
    field = {"name": "nw1", "kind": "paddy", "bbox": [350, 350, 550, 550], "outline": [[350, 350], [550, 350], [550, 550], [350, 550]]}  # ~800px perimeter, all in-wall
    hs = [{"kind": "plain", "rot": 0, "w": 18, "h": 12, **h} for h in houses]
    return {"meta": {"scale": "city", "walled": True, "agricultural_district": agri, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [field], "houses": hs}


def _road_city(buildings, road=True):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "buildings": buildings}
    if road:
        M["road"] = [[500, -40], [500, 500], [500, 1040]]  # runs off both edges, through the walls
    return M


def _unwalled_road_city(buildings):
    # an UNWALLED city: no wall, so the road's through-extent is the urban footprint (the building bbox)
    spread = [bldg(300 + i * 60, 250, kind="laborer") for i in range(8)] + [bldg(300 + i * 60, 750, kind="laborer") for i in range(8)]  # housing spanning the road on both sides
    return {"meta": {"scale": "city", "W": 1000, "H": 1000}, "gates": [], "road": [[500, -40], [500, 500], [500, 1040]], "buildings": spread + buildings}


# --- city_lanes_meet_when_aligned (two lanes heading at each other should connect) ---
def _lanes(streets=None, alleys=None, **extra):
    M = {}
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    if alleys is not None:
        M["alleys"] = [{"pts": p} for p in alleys]
    M.update(extra)
    return M


# --- city_lanes_reach_ward_gates (lanes at a neighborhood wall extend to it and end at a gate) ---
def _ward_lane(alleys=None, streets=None, fence=None, gov=(500, 640), **extra):
    M = {"wards": [{"boundary": fence or [[300, 500], [700, 500]]}]}  # a horizontal ward fence at y500
    if gov:
        M["governor_mansion"] = {"x": gov[0], "y": gov[1]}  # interior anchor, SOUTH of the fence
    if alleys is not None:
        M["alleys"] = [{"pts": p} for p in alleys]
    if streets is not None:
        M["town_streets"] = [{"pts": p, "w": 18} for p in streets]
    M.update(extra)
    return M


# --- city_lane_under_wall / city_lanes_under_ward_fences (lanes render UNDER walls) ---
def _walled(streets=None, alleys=None, **extra):
    M = {"meta": {"scale": "city"}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]], "wall_z": 10, "gates": [[500, 200]]}
    if streets is not None:
        M["town_streets"] = streets
    if alleys is not None:
        M["alleys"] = alleys
    M.update(extra)
    return M


# ---- a caption naming a LINEAR feature runs ALONG it (GM 2026-08-08) --------------------------
# The label records below carry the road caption's own shape: a box centered on `road_label`'s x
# and straddling its baseline, which is how the check finds the record without matching on text.
def _road_map(road, tilt=None):
    lab = [1157.0, 122.0, 1243.0, 134.6, 1, "Imperial Road", [1187, 87, 1213, 113]]
    M = {"meta": {}, "road": road, "road_label": [1200, 130], "labels": [lab if tilt is None else [*lab, tilt]]}
    return M


# --- city_caste_counts_in_band (the caste MIX, not just the total, matches budgets.md) ---
def _caste_city(**counts):
    blds = []
    for kind, n in counts.items():
        blds += [bldg(300 + i * 10, 300 + (i % 5) * 10, kind=kind) for i in range(n)]
    return {"meta": {"scale": "city", "population": 300}, "buildings": blds}  # ~60 households


# --- wall guard towers, ring road, streets reaching the ring road (fortification) ---
def _fort_city(**extra):
    M = {"meta": {"scale": "city", "walled": True}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]]}
    M.update(extra)
    return M


# ---- the ward gate's FULL DRAWN FOOTPRINT in the overlap matrix (GM 2026-07-27) ----
# "in general we always want overlap checks to use full footprints". A kido carries no w/h, so
# matrix_extents skipped it silently and the gate was invisible to every matrix check in BOTH
# directions - a notice board came to rest on Nagahara's guard box with the gate green.
def _gate_parts(x=400, y=500):
    """A ward gate's recorded geometry: the roofed bar on the fence line, the guard box beside it."""
    roof = [[x - 15, y - 7], [x + 15, y - 7], [x + 15, y + 7], [x - 15, y + 7]]
    guard = [[x - 30, y + 12], [x - 15, y + 12], [x - 15, y + 28], [x - 30, y + 28]]
    return {"x": x, "y": y, "rot": 0, "bbox": [x - 30, y - 7, x + 15, y + 28], "guard": guard, "parts": [roof, guard]}


_DIAMOND = [[500, 200], [800, 500], [500, 800], [200, 500]]  # a wall whose edges run at 45 deg


def _ring_towers(step, wall=None):
    # evenly-spaced towers walking the WALLSQ perimeter at `step` px - a dense enough ring
    import math as _m

    w = wall or WALLSQ
    ring = list(w) + [w[0]]
    seglens = [_m.hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]) for i in range(len(ring) - 1)]
    out = []
    for i in range(len(ring) - 1):
        n = max(1, int(seglens[i] / step))
        for j in range(n):
            t = j / n
            out.append({"x": ring[i][0] + (ring[i + 1][0] - ring[i][0]) * t, "y": ring[i][1] + (ring[i + 1][1] - ring[i][1]) * t})
    return out


def _gate_furn(rot, wall=None, gates=None):
    return _fort_city(
        wall=wall or WALLSQ,
        gates=gates or [[500, 200], [500, 800]],
        gate_structs=[{"x": 420, "y": 256, "w": 66, "h": 44, "rot": rot, "kind": "guardhouse", "z": 1}, {"x": 360, "y": 256, "w": 60, "h": 44, "rot": rot, "kind": "inspection", "z": 1}],
    )


_RING = [[240, 240], [760, 240], [760, 760], [240, 760], [240, 240]]


def _ring_city(streets, **extra):
    return _fort_city(ring_road=_RING, ring_road_width=15, town_streets=[{"pts": p, "w": 18} for p in streets], **extra)


# --- ring_road_kept_clear (no building/civic/field footprint overlaps the ring road bed) ---
def _on_ring_bldg():  # a 40px dwelling straddling the west ring leg (x=240)
    return {"kind": "samurai", "x": 240, "y": 500, "w": 40, "h": 40, "rot": 0}


def _temple_city(religious):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "religious": religious}


def _n_temples(n):
    return [{"kind": "temple", "x": 200 + 60 * i, "y": 400, "w": 80, "h": 60, "rot": 0, "label": f"Temple of X{i}"} for i in range(n)]


def _estate_city(estates, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "merchant_estates": estates}
    M.update(extra)
    return M


def _ward_city(boundary):
    return {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "wards": [{"name": "x", "boundary": boundary}]}


def _moat_city(channel_poly):
    # square moat fed by a stream entering its NORTH edge from off the top -> the moat flows SOUTH
    return {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": [[320, 320], [680, 320], [680, 680], [320, 680]],
        "moat": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "streams": [{"poly": [[500, 40], [500, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "moat"}}],
        "channels": [{"poly": channel_poly, "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}}],
        "gates": [[500, 300], [500, 700]],
    }


def _street_city(streets, **extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "town_streets": streets}
    M.update(extra)
    return M


def _caravan_city(**extra):
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200]]}
    M.update(extra)
    return M


# ---- theater_stage_clear: the stage footprint overlaps NOTHING (the Hirameki-on-the-wall bug) ----------
_STAGE = {"x": 500, "y": 500, "w": 150, "h": 105, "rot": 0}


# --- labels_clear_of_other_buildings (a label may cover only the thing it names) ---
def _bldg(kind, x=500, y=500, w=40, h=30):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h, "rot": 0}


def _lbl_city(**extra):
    M = {"meta": {"scale": "city"}, "labels": [[480, 490, 520, 510, 1, "flophouse"]]}
    M.update(extra)
    return M


# --- the check also runs at TOWN scale (the monastery/graveyard cross-overlap the GM hit) ---
def _lbl_town(label_text, **extra):
    M = {"meta": {"scale": "town"}, "labels": [[480, 490, 520, 510, 1, label_text]]}
    M.update(extra)
    return M


# --- city wells: water access + block-interior placement ---
def _well_city(**extra):
    M = {"meta": {"scale": "city"}, "wells": [{"x": 500, "y": 500, "r": 8}]}
    M.update(extra)
    return M


def _warren(nwells):
    # 30 laborer dwellings in a tight cluster, served by `nwells` wells spread across it
    blds = [{"kind": "laborer", "x": 500 + (i % 6) * 15, "y": 500 + (i // 6) * 15, "w": 14, "h": 10, "rot": 0} for i in range(30)]
    wells = [{"x": 500 + i * (75 // max(1, nwells - 1) if nwells > 1 else 0), "y": 530, "r": 8} for i in range(nwells)]
    return {"meta": {"scale": "city"}, "buildings": blds, "wells": wells}


def _es_pocket_city(**extra):
    # a densely housed city with ONE deliberate bare pocket (~230x120px, the Tango north-gate
    # shape): houses on a 60px lattice except x 510-690 / y 400-520
    houses = [{"kind": "laborer", "x": x, "y": y, "w": 30, "h": 22, "rot": 0} for x in range(150, 850, 60) for y in range(150, 850, 60) if not (500 <= x <= 700 and 400 <= y <= 520)]
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100], [500, 900]],
        "buildings": houses,
    }
    M.update(extra)
    return M


def _farrier_map(fx, fy, sx=200, sy=200, scale="town", **meta_kw):
    meta = {"scale": scale, "W": 1000, "H": 1000, "ftpx": 1}
    meta.update(meta_kw)
    return {
        "meta": meta,
        "buildings": [{"x": sx, "y": sy, "w": 92, "h": 44, "kind": "stables", "rot": 0}],
        "farriers": [{"x": fx, "y": fy, "w": 28, "h": 38, "rot": 0, "label": "farrier"}],
    }


_MOAT = [[160, 160], [840, 160], [840, 840], [160, 840], [160, 160]]  # encircles WALLSQ (200-800)


def _feeder_city(stream_w):
    return {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "moat": _MOAT,
        "moat_width": 22,
        "streams": [{"poly": [[80, 500], [165, 500]], "frm": None, "to": None, "w": stream_w}],
    }


def _drain_city(streams):
    # a closed-moat city (no river); off-map = x<0 / x>1000 (EX0=0, EX1=W for a viewBox-less manifest)
    return {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "moat": _MOAT,
        "moat_width": 22,
        "streams": streams,
    }


_MOAT_FEEDER = {"poly": [[-20, 500], [165, 500]], "frm": None, "to": None, "w": 22}  # off-map W -> moat W rim
_MOAT_OUTFALL = {"poly": [[835, 500], [1020, 500]], "frm": None, "to": None, "w": 22}  # moat E rim -> off-map E (opposite the feeder)


# --- settlement wells (town/village/hamlet water access) ---
def _rural(scale, houses, wells, **extra):
    M = {"meta": {"scale": scale}, "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses], "wells": [{"x": x, "y": y, "r": 8} for (x, y) in wells]}
    M.update(extra)
    return M


def _well_size_city(vr):
    # two 44px farmhouses with a well of drawn radius `vr` beside them
    return {
        "meta": {"scale": "village"},
        "houses": [{"x": 300, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"}, {"x": 344, "y": 300, "w": 44, "h": 29, "rot": 0, "kind": "plain"}],
        "wells": [{"x": 322, "y": 300, "r": 8, "vr": vr}],
    }


# --- bridges where a road crosses water ---
def _bridge_map(bridges):
    # a country road (E-W) crossing a stream (N-S) at (500, 500); `bridges` is the recorded list
    return {"meta": {"scale": "village", "W": 1000, "H": 1000}, "road": [[100, 500], [900, 500]], "streams": [{"poly": [[500, 100], [500, 900]], "frm": None, "to": None, "w": 9}], "bridges": bridges}


# --- a bridge must lie ON its crossing and run ALONG the way it carries ---
def _skew_bridge_map(**kw):
    # the E-W road crosses the N-S stream at (500, 500); the deck under test is `bridges[0]`
    M = _bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}])
    M["bridges"][0].update(kw)
    return M


def _footbridge_map(bridges, footbridges=True):
    return {
        "meta": {"scale": "village", **({"field_footbridges": True} if footbridges else {})},
        # a field STRADDLING the main ditch, so the ditch is PLANKABLE (cultivation both banks) and thus
        # warrants a plank - a margin ditch with nothing to cross to is exempt (see the plankable-gate test)
        "fields": [{"name": "p", "kind": "paddy", "outline": [[50, 130], [850, 130], [850, 270], [50, 270]], "bbox": [50, 130, 850, 270]}],
        "field_ditches": [
            {"poly": [[100, 200], [800, 200]], "w": 5, "role": "main", "field": "p"},
            {"poly": [[100, 600], [180, 600]], "w": 4, "role": "branch", "field": "p"},
        ],  # short stub -> below min, skipped
        "bridges": bridges,
    }


# ---- shrine_avenue_fronts_the_hall: a village sando's innermost arch sits at the hall's threshold ----------
def _shrine_avenue(hall_x, torii_y0):
    return {
        "meta": {"scale": "village", "ftpx": 2},
        "religious": [{"x": hall_x, "y": 400, "w": 30, "h": 24, "kind": "shrine", "rot": 0}],
        "torii": [[400, torii_y0 + i * 15, i] for i in range(3)],  # a 3-arch sando marching S
    }


# --- harvest processing (per-farmstead threshing/drying yards) ---
_PADDY_SQ = [[400, 400], [600, 400], [600, 600], [400, 600]]


def _harvest(houses, yards, fields=None):
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in houses],
        "wells": [{"x": x, "y": y, "r": 8, "vr": 11.9} for (x, y) in houses],  # a well by each house so the water checks pass
        "threshing_yards": yards,
    }
    if fields:
        M["fields"] = fields
    return M


def _yard(of, dx=44, dy=0, w=32, h=20):
    # a small yard beside the farmhouse at `of`, recording its parent farmhouse center
    return {"x": of[0] + dx, "y": of[1] + dy, "w": w, "h": h, "rot": 0, "of": [of[0], of[1]]}


_SIX = [(300, 300), (380, 300), (460, 300), (540, 300), (620, 300), (700, 300)]  # the work yard is UNIVERSAL: need all 6


# --- waterways merge at crossings (confluence layering) ---
def _confluence(ch_bedz):
    # a stream (bed+sheen) crossed by a channel; ch_bedz is the channel's bed draw position
    return {
        "meta": {"scale": "village"},
        "streams": [{"poly": [[100, 500], [900, 500]], "frm": None, "to": None, "w": 9, "bedz": 10, "sheenz": 20}],
        "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "bedz": ch_bedz}],
    }


# --- the dead (cemeteries) ---
_MON = [{"kind": "monastery", "x": 500, "y": 500, "w": 120, "h": 80}]
_SHR = [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]


def _dead(scale, cems, religious=None):
    M = {"meta": {"scale": scale}, "cemeteries": cems}
    if religious is not None:
        M["religious"] = religious
    return M


# --- the full city funerary geography ---
def _city_dead(**kw):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # inside = 200..800
    d = dict(
        cems=[(300, 300), (700, 300), (100, 100)],  # 2 inside + 1 outside
        temples=[(320, 320, "A", True), (680, 320, "B", True)],
        maus=[(520, 520)],
        crem=[(100, 900)],
        oss=[(140, 900)],
        gov=(500, 500),
        shrines=[],
    )
    d.update(kw)

    def _cem(c):
        x, y = c[0], c[1]
        if len(c) >= 4:
            w, h = c[2], c[3]
        else:  # outside cemeteries default bigger than inside
            outside = not (200 < x < 800 and 200 < y < 800)
            w, h = (104, 74) if outside else (70, 50)
        parish = c[4] if len(c) >= 5 else True
        return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "parish": parish}

    return {
        "meta": {"scale": "city"},
        "wall": WALLSQ,
        "cemeteries": [_cem(c) for c in d["cems"]],
        "mausoleums": [{"x": x, "y": y, "w": 74, "h": 58, "rot": 0} for (x, y) in d["maus"]],
        "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in d["crem"]],
        "ossuaries": [{"x": x, "y": y, "w": 92, "h": 60, "rot": 0} for (x, y) in d["oss"]],
        "religious": [{"kind": "temple", "x": tx, "y": ty, "w": 80, "h": 60, "label": lbl, "graveyard": gv} for (tx, ty, lbl, gv) in d["temples"]]
        + [{"kind": "small_shrine", "x": sx, "y": sy, "w": 30, "h": 24} for (sx, sy) in d["shrines"]],
        "governor_mansion": {"x": d["gov"][0], "y": d["gov"][1], "w": 120, "h": 90} if d["gov"] else None,
    }


def _water_grave(water):
    M = {"meta": {"scale": "village"}, "cemeteries": [{"x": 300, "y": 300, "w": 60, "h": 44, "rot": 0, "parish": True}]}
    M.update(water)
    return M


_PADDY = {"name": "a", "kind": "paddy", "bbox": [300, 330, 500, 500], "outline": [[300, 330], [500, 330], [500, 500], [300, 500]]}


def _city_estates(gate_dirs):
    WALLSQ = [[200, 200], [800, 200], [800, 800], [200, 800]]  # estates sit OUTSIDE, to the SE
    return {
        "meta": {"scale": "city", "walled": True},
        "wall": WALLSQ,
        "manors": [{"x": 900 + (i % 3) * 220, "y": 900 + (i // 3) * 220, "w": 120, "h": 90, "gate_dir": gd} for i, gd in enumerate(gate_dirs)],
    }


# --- town_has_caravan_inn -------------------------------------------------------------------------
def _town_caravan(inn=True, stables=True, walled=False, inn_xy=(500, 500), st_xy=(500, 560)):
    M = {"meta": {"scale": "town", "walled": walled}, "houses": [], "fields": [], "buildings": []}
    if inn:
        M["buildings"].append({"x": inn_xy[0], "y": inn_xy[1], "w": 66, "h": 48, "kind": "inn", "rot": 0})
    if stables:
        M["buildings"].append({"x": st_xy[0], "y": st_xy[1], "w": 92, "h": 44, "kind": "stables", "rot": 0})
    if walled:
        M["wall"] = [[100, 100], [2000, 100], [2000, 2000], [100, 2000]]
    return M


# --- town merchant/laborer house-size variety -----------------------------------------------------
def _town_housing(m_large, l_large, m_small=12, l_small=22):
    b = []
    for i in range(m_small):
        b.append(bldg(120 + i * 60, 120, "merchant"))
    for i in range(m_large):
        b.append(bldg(120 + i * 100, 240, "merchant_large", w=86, h=60))
    for i in range(l_small):
        b.append(bldg(120 + i * 50, 360, "laborer"))
    for i in range(l_large):
        b.append(bldg(120 + i * 70, 480, "laborer_large", w=50, h=34))
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "buildings": b}


# --- merchant_residences_behind_businesses (road-fronted towns: shops -> homes -> gap -> laborers) -
# A vertical trunk road at x=100; droad = |x - 100|. Shops front it, merchant homes sit behind, then
# the laborer warren further back with a gap.
def _town_behind(res_x=230, lab_x=300):
    b = []
    for i in range(7):
        b.append(bldg(150, 100 + i * 60, "shop"))  # businesses at droad ~50
    for i in range(3):
        b.append(bldg(res_x, 150 + i * 80, "merchant_large", w=86, h=60))  # merchant residences
    for i in range(6):
        b.append(bldg(lab_x, 120 + i * 50, "laborer"))  # laborer warren
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


# --- housing_aligned_behind_storefronts (a home tucked behind a shop lies parallel to it) ----------
# A vertical trunk road at x=100; along = y, droad = |x - 100|. Shops front it (rot 0); a home is
# "directly behind" a shop when it shares the shop's along-road position and sits one building deeper.
def _town_align(home_rot=0, home_x=200, home_y=280, with_shops=True):
    b = []
    if with_shops:
        for i in range(7):
            b.append(bldg(140, 100 + i * 60, "shop", rot=0))  # storefronts at droad 40
    b.append(bldg(home_x, home_y, "merchant_large", rot=home_rot, w=86, h=60))
    return {"meta": {"scale": "town"}, "houses": [], "fields": [], "road": [[100, 0], [100, 1000]], "road_width": 26, "buildings": b}


def _maus_ward(ward_walls, maus_cy=1556):
    # a mausoleum (gate west) whose NORTH wall (y0 = cy-20) runs along a ward fence at y=1535,
    # inside a city wall - "ward_walls" records the sides the compound yielded to the fence
    return {
        "meta": {"scale": "city", "walled": True},
        "wall": [[100, 100], [3000, 100], [3000, 2500], [100, 2500]],
        "wards": [{"name": "samurai", "boundary": [[1620, 1535], [2401, 1535]], "z": 5}],
        "mausoleums": [{"x": 2246, "y": maus_cy, "w": 54, "h": 40, "rot": 0, "gate_dir": "west", "ward_walls": ward_walls}],
    }


def _town_manor(gate_dir, rot=0, road=None):
    # a magistrate manor at (300,300); the "town" (houses) is to the SE at ~(950,933)
    M = {
        "meta": {"scale": "town"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for x, y in [(900, 900), (1000, 900), (950, 1000)]],
        "manors": [{"x": 300, "y": 300, "w": 120, "h": 90, "rot": rot, "gate_dir": gate_dir, "gate": [300, 300]}],
    }
    if road:
        M["road"] = road
    return M


def _crem_cem(crem_xy, cem_xy, walled=False):
    M = {
        "meta": {"scale": "town"},
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}],
    }
    if walled:
        M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    return M


def _crem_road(crem_xy, cem_xy):
    # a cremation ground + an adjacent external cemetery, beside a main road along y=200
    return {
        "meta": {"scale": "town"},
        "road": [[100, 200], [900, 200]],
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": cem_xy[0], "y": cem_xy[1], "w": 100, "h": 72, "rot": 0, "parish": True}],
    }


def _crem_temple(crem_xy, mon_xy=(300, 500)):
    # a monastery + a cremation ground (with an adjacent cemetery), beside a main road along y=200.
    # The monastery at y=500 sits 300px back from the road; "behind" it means >= 260px back.
    return {
        "meta": {"scale": "town"},
        "road": [[100, 200], [900, 200]],
        "religious": [{"x": mon_xy[0], "y": mon_xy[1], "w": 132, "h": 86, "rot": 0, "kind": "monastery"}],
        "cremation_grounds": [{"x": crem_xy[0], "y": crem_xy[1], "w": 116, "h": 80, "rot": 0}],
        "cemeteries": [{"x": crem_xy[0], "y": crem_xy[1] + 110, "w": 100, "h": 72, "rot": 0, "parish": True}],
    }


def _town_dead(crem, dwell=((300, 300),)):
    return {
        "meta": {"scale": "town"},
        "houses": [{"x": x, "y": y, "w": 40, "h": 28, "rot": 0, "kind": "plain"} for (x, y) in dwell],
        "cemeteries": [{"x": 300, "y": 360, "w": 70, "h": 50, "rot": 0}],
        "religious": [{"kind": "monastery", "x": 300, "y": 300, "w": 80, "h": 60, "label": "M", "graveyard": True}],
        "cremation_grounds": [{"x": x, "y": y, "w": 116, "h": 80, "rot": 0} for (x, y) in crem],
    }


# ---- fire-watch towers (hinomi-yagura) & fire-break plazas (hiyokechi/hirokoji) ----


def _tower(x, y):
    return {"x": x, "y": y, "w": 26, "h": 26, "rot": 0}


# ---- the official notice board (kosatsuba) ----


def _kosatsuba(x, y):
    return {"x": x, "y": y, "w": 12, "h": 5, "rot": 0}


def _block(cx, cy, kind="laborer", n=4, step=30):
    return [bldg(cx + i * step, cy + j * step, kind) for i in range(n) for j in range(n)]


# ---- gardens_unshaded_from_east: nudge an E-side garden S of a shading tree WHERE POSSIBLE ----
# a house with its garden on the E, a NEIGHBOR grove hard against the garden's east, open ground to the S
_EAST_SHADE = {
    "meta": {"scale": "village"},
    "houses": [{"x": 300, "y": 300, "w": 23, "h": 14, "rot": 0, "kind": "plain"}],
    "gardens": [{"x": 320, "y": 300, "w": 10, "h": 11, "rot": 0, "of": [300, 300]}],
    "groves": [{"x": 340, "y": 300, "w": 16, "h": 24, "rot": 0, "of": [380, 300], "face": [-1, 0]}],
}


# ---- city_capacity: the wall-sizing space-budget analysis --------------------------------
# These pin the four verdicts, the ASCII interior map (each cell-class branch), and the
# _rects skip for a footprint-less item. city_capacity is called directly (it is analysis,
# not a gate check) - the gate wrapper only surfaces its too_small/too_big verdict via
# city_wall_sized_to_population.
def _diamond_city(pop, dwellings=0, **extra):
    # a diamond wall so the bbox corners fall OUTSIDE the polygon (covers the "outside" cell
    # branch); 400px across -> ~160000px^2 interior.
    wall = [[200, 0], [400, 200], [200, 400], [0, 200]]
    houses = [bldg(200 + (i % 20) * 3, 200 + (i // 20) * 3, "laborer", w=3, h=3) for i in range(dwellings)]
    M = {"meta": {"scale": "city", "population": pop}, "wall": wall, "buildings": houses}
    M.update(extra)
    return M


# ---- feature 006: in-wall population + extramural commoners ------------------------------
_CITY_WALL_SMALL = [[200, 200], [800, 200], [800, 800], [200, 800]]  # 600x600 box


def _pop_city(buildings, population=100, **extra):
    M = {"meta": {"scale": "city", "population": population}, "wall": _CITY_WALL_SMALL, "buildings": buildings}
    M.update(extra)
    return M


# ---- feature 006: declared quarters, per-quarter density, civic-open, reserve-cap ---------
def _qcity(quarters, buildings=None, **extra):
    M = {"meta": {"scale": "city"}, "wall": _CITY_WALL_SMALL, "quarters": quarters, "buildings": buildings or []}
    M.update(extra)
    return M


_FULL_Q = [[200, 200], [800, 200], [800, 800], [200, 800]]  # a quarter covering the whole interior


def _dwell_grid(x0, x1, y0, y1, n, kind="laborer"):
    return [bldg(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * j / (n - 1), kind) for i in range(n) for j in range(n)]


def _ward006(**extra):
    # a walled city with a sealed rectangular ward whose fence ends abut the wall
    wall = _CITY_WALL_SMALL
    bnd = [[200, 500], [500, 500], [500, 700], [200, 700]]  # a fence with ends on the W wall (x=200)
    M = {
        "meta": {"scale": "city", "walled": True},
        "wall": wall,
        "gates": [[500, 200]],
        "wards": [{"name": "samurai", "boundary": bnd, "z": 10}],
        "kido": [{"x": 500, "y": 600, "horizontal": False, "bbox": [490, 590, 510, 610]}],
    }
    M.update(extra)
    return M


# ---- Pool-level twin-detector (feature 005) -----------------------------------------------------
# The cross-map check that mechanically guards the distinctiveness goal: two same-down_deg villages must
# differ on >= TWIN_MIN_DIFF of the 7 structural axes, or they read as copies (the Kikuta/Hoshigaoka twin).


def _tv(**over):
    """A minimal village manifest with the fields twin_axes reads; `over` merges (meta merges nested)."""
    M = {
        "meta": {"scale": "village", "down_deg": 45},
        "houses": [
            {"x": 380, "y": 620, "role": "plain"},
            {"x": 420, "y": 700, "role": "plain"},
            {"x": 400, "y": 560, "role": "headman"},
            {"x": 440, "y": 660, "role": "plain"},
        ],
        "fields": [{"bbox": [566, 313, 2122, 1392]}],
        "pond": [420, 210, 145, 92],
        "dry_plots": [{"theta": -0.8}, {"theta": -0.9}, {"theta": -0.7}],
    }
    for k, v in over.items():
        if k == "meta":
            M["meta"] = {**M["meta"], **v}
        else:
            M[k] = v
    return M


# ---- feature 009: the wall must match the declared space budget -----------------------------
def _budget_city(budget=None):
    # a walled city whose square wall encloses 600x600 = 360,000 px^2
    M = {"meta": {"scale": "city", "walled": True}, "wall": [[200, 200], [800, 200], [800, 800], [200, 800]]}
    if budget is not None:
        M["meta"]["budget"] = budget
    return M


# ---- doors face open ground + rows max 2-deep (GM feedback 2026-07-18) ----------------------
# The door glyph draws on a building's local +h/2 side (settlement.building), so the door's
# world position/direction derive from x,y,w,h,rot alone. At rot=0 the door faces +y (down).
def _door_city(buildings, scale="city"):
    return {"meta": {"scale": scale, "ftpx": 3}, "wall": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]], "buildings": buildings}


# ---- merchant-estate walls clear of water + fire towers (GM feedback 2026-07-19) ------------
def _mest_city(**extra):
    M = {"meta": {"scale": "city"}, "merchant_estates": [{"x": 500, "y": 500, "w": 62.0, "h": 46.0, "gate": [500, 523.0], "gate_dir": "south"}]}
    M.update(extra)
    return M


# ---- to-scale gates/walls + funerary features (GM feedback 2026-07-19) ----------------------
def _scaled_city(**extra):
    M = {"meta": {"scale": "city", "ftpx": 3}}
    M.update(extra)
    return M


def _paddy_field_rec(name="p1", x0=300, y0=300, x1=700, y1=700):
    ol = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    return {"name": name, "kind": "paddy", "outline": ol, "bbox": [x0, y0, x1, y1], "vis_bbox": [x0, y0, x1, y1]}


# ---- drain_ends_reach_water (a collector's free end never dangles in bare ground) ----
def _drain_ditch(pts, field="f1"):
    return {"poly": pts, "role": "drain", "field": field, "w": 6, "w_tail": 6}


# ---- the town-scale audit batch (GM 2026-07): checks adapted from the city suite ----
def _dw(x, y, kind):
    return {"x": x, "y": y, "w": 30, "h": 20, "kind": kind, "rot": 0}


def _thin_belt_cluster(**extra):
    # 12 farmhouses behind a belt that NESTLES and carries 12 clumps (so the embrace test is satisfied)
    # but whose crowns are small - the shape a too-thin belt takes: present, adjacent, and no wall.
    houses = [{"x": 500 + i * 30, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0} for i in range(12)]
    belt = {"x": 620, "y": 430, "w": 300, "h": 20, "role": "windbreak", "r": 6, "clumps": [[500 + j * 26, 430] for j in range(12)]}
    return {"meta": {"scale": "village", "nucleated": True}, "houses": houses, "village_groves": [belt], **extra}


# ---- near_ring_paddy_dominant (feature 014): a wet-rice county seat's flat near ring is PADDY, not dryland
# grain. Paddy cells (kind="paddy" fields) must dominate dry-grain cells (dry_plots crop != garden) in the
# near-ring band, scaled by tier. Gardens are the legitimate near-town dry use, not counted against.
def _paddy_f(x0, y0, x1, y1, name="p"):
    return {"name": name, "kind": "paddy", "outline": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "bbox": [x0, y0, x1, y1]}


# ---- inwall_drains_gated_at_cutoff: the Tango bare outfall (GM 2026-07-23) -------------------
# A walled city's in-wall drain leaves through an UNDERGROUND culvert (an undrawn drain->moat
# conduit); the visible ditch must be trimmed back clear of the patrol ring road and wear a
# sluice_gate glyph at the cut - otherwise it reads as unfinished linework running into the road.
_IW_WALL = [[50, 50], [950, 50], [950, 950], [50, 950]]
_IW_RING = [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]]


def _iw_manifest(conduit_start, stroke=None, gates=(), drawn=False):
    return {
        "meta": {"scale": "town", "W": 1000, "H": 1000},
        "wall": _IW_WALL,
        "ring_road": _IW_RING,
        "ring_road_width": 8,
        "channels": [{"poly": [conduit_start, [200, 250], [60, 300]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 2.5, "drawn": drawn}],
        "drawn_channels": [{"pts": stroke, "late": True, "bedz": 5}] if stroke else [],
        "sluice_gates": [{"x": g[0], "y": g[1], "rot": 0, "z": 1} for g in gates],
    }


# ---- tanning yards (GM 2026-07-24) ---------------------------------------------------------
# Water, not settlement size, is the gate: tanning soaks hides for 1-2 weeks, so the yard must
# abut a watercourse; the stench keeps it outside the walls and off the ordinary houses; and the
# burakumin's OWN houses are exempt from that separation, because living on the ground they work
# is what the segregated quarter IS.
def _ty_map(**over):
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1},
        "streams": [{"poly": [[500, 100], [500, 900]], "w": 8, "flow": "forward", "flow_deg": 90.0, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}],
        "buildings": [bldg(200, 200, kind="burakumin"), bldg(240, 200, kind="burakumin")],
        # rot 90 lays the yard along the vertical stream: the shared fixture must be a LEGAL
        # yard, or every test in this family quietly carries tanning_yard_square_to_its_water
        "tanning_yards": [{"x": 466, "y": 500, "w": 58, "h": 41, "rot": 90, "label": "tanning yard"}],
    }
    M.update(over)
    return M


# ---- and the yard runs WITH its bank (GM 2026-07-26) ----------------------------------------
# A diagonal stream takes a diagonal yard: the pit rank and the staking frames share one edge of
# water, so a yard left square to the map on a slanted bank puts one corner in the stream and
# strands the far end of the rank inland. The reference bank is any course within the on-water
# reach - measured to the BANK, not the centerline - so a yard at a confluence may follow either.
_TY_DIAG = [[400, 300], [600, 600]]  # bearing 56.3


# ---- water flow direction (GM 2026-07-24) --------------------------------------------------
def _wf_map(**over):
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1, "down_deg": 90, "water_flow": 90},
        "streams": [{"poly": [[500, 100], [500, 900]], "w": 8, "flow": "forward", "flow_deg": 90.0}],
    }
    M.update(over)
    return M


# ---- crop_not_held_open_by_one_feature (GM 2026-07-25) --------------------------------------
def _crop_map(**over):
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1, "W": 1200, "H": 1400},
        "buildings": [bldg(500, 500), bldg(540, 500), bldg(520, 480)],
    }
    M.update(over)
    return M


# ---- per-field drainage slope (GM 2026-07-25) -----------------------------------------------
def _drain_map(**over):
    M = {
        "meta": {"scale": "village", "ftpx": 2, "down_deg": 90, "W": 1200, "H": 1400},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[200, 200], [900, 200], [900, 900], [200, 900]], "bbox": [200, 200, 900, 900], "vis_bbox": [200, 200, 900, 900]}],
        # a collector running straight DOWN a 90 deg (south) fall - what the check exists to catch
        "field_ditches": [{"role": "drain", "field": "f1", "poly": [[400, 300], [430, 800]], "w": 1.5}],
    }
    M.update(over)
    return M


# ---- settlement_declares_a_land_fall (GM 2026-07-25) ----------------------------------------
def _fall_map(**over):
    M = {
        "meta": {"scale": "town", "walled": False, "ftpx": 1, "W": 1200, "H": 1200},
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 100], [500, 100], [500, 500], [100, 500]], "bbox": [100, 100, 500, 500], "vis_bbox": [100, 100, 500, 500]}],
    }
    M.update(over)
    return M


_MOAT_RING = [[400, 300], [700, 300], [700, 700], [400, 700], [400, 300]]


def _moat_map(**over):
    M = {
        "meta": {"scale": "city", "walled": True, "ftpx": 3, "W": 3200, "H": 2700, "down_deg": 90},
        "wall": [[450, 350], [650, 350], [650, 650], [450, 650]],
        "moat": _MOAT_RING,
        "moat_flow": {"inlet": [400, 300], "outlet": [700, 700]},  # enters NW, leaves SE -> heads south
        "fields": [{"name": "fs", "kind": "paddy", "outline": [[300, 800], [600, 800], [600, 1000], [300, 1000]], "bbox": [300, 800, 600, 1000], "vis_bbox": [300, 800, 600, 1000]}],
        "channels": [{"poly": [[500, 700], [480, 900]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "fs"}, "w": 2.5}],
    }
    M.update(over)
    return M


# ---- moat junctions swept with the current (GM 2026-07-25) ----------------------------------
# sampled every 50px: a 4-vertex square is too coarse for a mid-edge tap, since the nearest-vertex
# tangent then picks up the wrong edge entirely
_MJ_RING = [[x, 300] for x in range(400, 700, 50)] + [[700, y] for y in range(300, 700, 50)] + [[x, 700] for x in range(700, 400, -50)] + [[400, y] for y in range(700, 300, -50)] + [[400, 300]]
_MJ_FLOW = {"inlet": [400, 300], "outlet": [700, 700]}  # enters NW, leaves SE


def _mj_map(chan):
    return {
        "meta": {"scale": "city", "walled": True, "ftpx": 3, "W": 3200, "H": 2700, "down_deg": 90},
        "wall": [[450, 350], [650, 350], [650, 650], [450, 650]],
        "moat": _MJ_RING,
        "moat_flow": _MJ_FLOW,
        "fields": [{"name": "f1", "kind": "paddy", "outline": [[100, 800], [400, 800], [400, 1000], [100, 1000]], "bbox": [100, 800, 400, 1000], "vis_bbox": [100, 800, 400, 1000], "down_deg": 90}],
        "channels": [chan],
    }


# ---- the justice works (feature 015) ----------------------------------------------------------
# Two institutions sited by OPPOSITE logics: the punishment ground lives on the town's foot
# traffic, the execution ground lives outside the settlement past the boundary stone and clear of
# the community's dead. Each fixture below breaks exactly one of those rules.
def pspot(x, y, rot=0, w=30, h=12, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "rot": rot, "label": "punishment ground", **kw}


def exground(x, y, rot=0, w=60, h=60, screened=False, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "rot": rot, "screened": screened, "label": "execution ground", **kw}


def bstone(x, y, rot=0, w=3, h=3, vw=7, vh=7, **kw):
    return {"x": x, "y": y, "w": w, "h": h, "vw": vw, "vh": vh, "rot": rot, "label": "boundary stone", **kw}


def _justice_town(**over):
    """A town that PASSES every justice check: a core around x=500 on an east-west road, the
    punishment ground on the town's frontage, the burakumin quarter east of the core, the boundary
    stone beyond it, and the execution ground beyond that - clear of the burial ground.

    The stone sits 160 ft past the outcast quarter, not 100: this is an UNWALLED town, so the stone
    answers to the same ~120 ft "past the built edge" clearance the ground does, and the quarter's
    huts are dwellings like any other."""
    M = {
        "meta": {"scale": "town", "ftpx": 1, "W": 2000, "H": 2000},
        "road": [[100, 1000], [1900, 1000]],
        "houses": [house(440 + 30 * i, 940) for i in range(6)],
        "buildings": [bldg(1000, 1010, kind="burakumin")],
        "punishment_spots": [pspot(520, 1020)],
        "boundary_markers": [bstone(1160, 1010)],
        "execution_grounds": [exground(1500, 1060)],
        "cemeteries": [{"x": 1500, "y": 500, "w": 100, "h": 80, "rot": 0, "parish": False}],
    }
    M.update(over)
    return M


def _martial_city(pop=3000, halls=1, dojos=1, roll=None, range_ft=100.0, hall_xy=(400, 500), dojo_xy=(460, 500), sam_xy=(430, 520)):
    """A minimal provincial city carrying the martial-training program (GM 2026-07-25)."""
    meta = {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True, "population": pop}
    if roll is not None:
        meta["dojo_roll"] = roll
    return {
        "meta": meta,
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100]],
        "buildings": [bldg(sam_xy[0] + 20 * i, sam_xy[1], kind="samurai") for i in range(10)],
        "martial_halls": [{"x": hall_xy[0], "y": hall_xy[1], "w": 43.3, "h": 33.3, "rot": 0, "label": "martial hall", "range_ft": range_ft} for _ in range(halls)],
        "dojos": [{"x": dojo_xy[0] + 40 * i, "y": dojo_xy[1], "w": 25.3, "h": 14.7, "rot": 0, "label": "dojo"} for i in range(dojos)],
    }


# ---- THE KEEP-CLEAR CONTRACT (GM 2026-07-25) --------------------------------------------------
# _OVERLAP_STRUCTS is a PROMISE: "this feature is solid, and must not overlap anything." The
# promise is only worth as much as the checks that actually read the registry, and the recurring
# way it breaks is a keep-clear check that hand-lists its own manifest keys and quietly falls
# behind - which looks exactly like a passing check. The martial hall is the worked example: it
# was correctly registered, correctly cleared of all thirteen no_structure_on_* hazards, and sat
# squarely on Tango's ring road with a green gate, because ring_road_kept_clear was reading eight
# keys nobody had updated. The GM found it by eye. That is the failure mode this test retires.
#
# It plants ONE instance of EVERY registered key squarely on EVERY hazard and demands the hazard's
# own check fire. So a new map feature cannot be added without either being gated everywhere or
# failing HERE, with both the key and the hazard named. Adding a hazard to the table below extends
# the contract to every existing feature at once.
_SOLID_EXTRAS = {
    "houses": {"kind": "plain"},
    "buildings": {"kind": "laborer"},
    "ministries": {"name": "Ministry of War"},
    "kosatsuba": {"vw": 11.0, "vh": 4.6, "label": "notice board"},
    "martial_halls": {"label": "martial hall", "range_ft": 100.0},
    "dojos": {"label": "dojo"},
    "breweries": {"label": "brewery"},
    "dye_yards": {"label": "dye works"},
    "lumber_yards": {"label": "lumber yard"},
    "oil_presses": {"label": "oil press"},
    "pawnshops": {"label": "pawnshop"},
    "bathhouses": {"label": "bathhouse"},
    "kilns": {"label": "kiln"},
    "farriers": {"label": "farrier"},
    "tanning_yards": {"label": "tanning yard"},
    "fire_towers": {"label": "fire tower"},
    "drum_towers": {"label": "drum tower"},
}


def solid(key, x, y, w=18.0, h=14.0):
    """One record of manifest key `key`, planted at (x, y). Mirrors the per-key fields the checks
    index unconditionally, the same job the fixture builders above do for houses and yards."""
    return {"x": x, "y": y, "w": w, "h": h, "rot": 0, **_SOLID_EXTRAS.get(key, {})}


_HAZ_META = {"scale": "city", "ftpx": 3, "W": 1000, "H": 1000, "walled": True, "population": 3000}


def _haz_base():
    """A walled-city shell every hazard shares. It carries a wall + gate + ring road because the
    city checks index them unconditionally; the hazards that are not under test sit far from
    (500, 500), so only the one being exercised is under the planted struct."""
    return {
        "meta": dict(_HAZ_META),
        "wall": WALL,
        "gates": [[50, 500]],
        "gate": [50, 500],
        "ring_road": [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]],
        "ring_road_width": 15,
    }


# (name, the check that must fire, where the struct goes, the hazard geometry laid under it, keys
# the rule DELIBERATELY does not govern). Most rows plant the struct ON the hazard, which is the
# overlap contract; the last row plants it a few px AWAY, because a CLEARANCE rule is the other
# shape a keep-clear rule comes in - and it broke in exactly the same way, with
# city_government_offices_dont_abut never having seen the martial hall or the dojo, so both shipped
# inside its 14px standoff.
_HAZARDS = (
    ("the town wall", "no_structure_on_wall", (500, 50), lambda: {}, ()),
    ("the moat", "no_structure_on_moat", (500, 500), lambda: {"moat": [[400, 500], [600, 500]], "moat_width": 22}, ()),
    ("the road", "no_structure_on_road", (500, 500), lambda: {"road": [[400, 500], [600, 500]], "road_width": 26}, ()),
    ("a street", "no_structure_on_street", (500, 500), lambda: {"town_streets": [{"pts": [[400, 500], [600, 500]], "w": 24}]}, ()),
    ("a stream", "no_structure_on_stream", (500, 500), lambda: {"streams": [{"poly": [[400, 500], [600, 500]], "w": 12}]}, ()),
    ("an irrigation channel", "no_structure_on_channel", (500, 500), lambda: {"channels": [{"poly": [[400, 500], [600, 500]], "w": 10, "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}]}, ()),
    ("the cargo canal", "no_structure_on_canal", (500, 500), lambda: {"canals": [{"poly": [[400, 500], [600, 500]], "w": 20}]}, ()),
    ("the pond", "no_structure_on_pond", (500, 500), lambda: {"pond": [500, 500, 60, 40]}, ()),
    ("the manor walls", "no_structure_on_manor", (500, 500), lambda: {"manors": [{"x": 500, "y": 500, "w": 80, "h": 60, "rot": 0}]}, ()),
    ("a religious hall", "no_structure_on_religious", (500, 500), lambda: {"religious": [{"x": 500, "y": 500, "w": 60, "h": 40, "kind": "temple", "label": "Temple of Bishamon"}]}, ()),
    ("the gate furniture", "no_structure_on_gate", (500, 500), lambda: {"gate_structs": [{"x": 500, "y": 500, "w": 30, "h": 16, "rot": 0, "kind": "guardhouse"}]}, ()),
    ("a torii arch", "no_structure_on_torii", (500, 500), lambda: {"torii": [[500, 500, 10]]}, ()),
    ("another structure", "no_structure_overlaps", (500, 500), lambda: {"flophouses": [{"x": 500, "y": 500, "w": 30, "h": 22, "rot": 0, "label": "flophouse"}]}, ()),
    ("the ring road", "ring_road_kept_clear", (500, 500), lambda: {"ring_road": [[400, 500], [600, 500]], "ring_road_width": 15}, ()),
    (
        "a government office's 14px standoff",
        "city_government_offices_dont_abut",
        (500, 528),  # 6px of daylight from the ministry below - inside the 14px the rule demands
        lambda: {"ministries": [{"x": 500, "y": 500, "w": 44, "h": 30, "name": "Ministry of War"}]},
        ("cemeteries", "mausoleums", "cremation_grounds", "ossuaries"),  # the documented funerary exclusion
    ),
)


def _label_map(caption, key, **extra):
    """A city carrying one solid feature at (500, 500) with `caption` written across it."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True, "population": 3000},
        "wall": WALL,
        "gates": [[500, 50]],
        "labels": [[470, 492, 530, 508, 1, caption]],
    }
    M[key] = [solid(key, 500, 500)]
    M.update(extra)
    return M


# ---- feature 016: the charcoal district's trade works ------------------------------------------
def _fuel_map(**over):
    """A town carrying one charcoal yard at (500, 500) on otherwise empty ground."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000})
    M["charcoal_yards"] = [{"x": 500, "y": 500, "w": 88, "h": 58, "rot": 0, "label": "charcoal yard", "sheds": 2, "apron": [-26, 12, 30, 20]}]
    M.update(over)
    return M


def _forge_map(fx=500.0, fy=500.0, homes=(), windward="NW"):
    """A town carrying one refining forge, plus whatever dwellings the test supplies."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000, "windward": windward})
    M["refining_forges"] = [{"x": fx, "y": fy, "w": 74, "h": 48, "rot": 0, "label": "refining forge", "hearths": 2}]
    M["houses"] = [house(hx, hy) for hx, hy in homes]
    return M


def _kiln_map(quarters=((500.0, 570.0),), body=(500.0, 470.0), ftpx=1, rot=0.0, **over):
    """A town carrying one kiln WORKS at (500, 500): a 140x120 ft ground, the 46x16 ft kiln body
    at `body`, and a 28x18 ft cottage at each of `quarters`."""
    M = manifest(meta={"scale": "town", "ftpx": ftpx, "W": 1000, "H": 1000})
    rec = {"x": 500.0, "y": 500.0, "w": 140.0, "h": 120.0, "rot": rot, "label": "kiln works", "quarters": [[qx, qy, 28.0, 18.0, rot] for qx, qy in quarters]}
    if body is not None:
        rec["body"] = [body[0], body[1], 46.0, 16.0, rot]
    M["kilns"] = [rec]
    M.update(over)
    return M


# ---- feature 017: the overlap matrix -------------------------------------------------------------
def _mx_map(**over):
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1200, "H": 1200, "name": "Nowhere", "down_deg": 90})
    M.update(over)
    return M


# ---- the tanning yard shares the quarter's SIDE (GM 2026-07-27) ---------------------------------
# Distance is deliberately NOT the test - a walled city keeps its quarter in-wall at the margin
# while the works go out to the water, and Nagahara's legal yard stands ~1,390 ft from its quarter.
# What the rule forbids is the yard facing the OPPOSITE way out of town, which routes the tanners'
# daily carcass haul back through the whole settlement. The "why" is in settlements/urban-features.md.


def _side_map(bur, others, **over):
    """The shared tanning fixture plus real NON-burakumin dwellings, which is what gives the
    settlement a center for the quarter to have a side OF. Yard and stream are _ty_map's, so the
    rest of the tanning family stays satisfied and only the bearing varies."""
    M = _ty_map(buildings=[bldg(x, y, kind="burakumin") for x, y in bur] + [bldg(x, y) for x, y in others])
    M.update(over)
    return M


# ---- the waiver hatch, and the two checks that keep it honest -----------------------------------

_WHY = "The Emperor lies southeast, so that quarter is claimed by the governor's yamen and the samurai estates, and the irrigation taps force the tanning ground to the south regardless."


def _waived_map(waivers):
    M = _side_map([(200, 200), (240, 200)], [(360, 620), (360, 620)])
    M["meta"] = {**M["meta"], "waivers": waivers}
    return M


# ---- THE FOOTPRINT-VS-CENTER RATCHET ------------------------------------------------------------
# Every gap VERDICT reads true footprints, never a center and never a circumscribed radius. That was
# a rule in a document once and it did not hold: three conventions coexisted in check_village.py and
# two of them shipped live defects (a boundary stone among the shops, an execution ground 105 ft from
# a laborer's wall, a burakumin quarter with a 5 ft seam, a cremation ground ~50 ft from a farmhouse).
# So the rule is a test instead, in the shape that already worked for the keep-clear contract.
#
# THE CONSTRUCTION. Each entry plants two features at exactly the offset where the two conventions
# DISAGREE - close enough that the footprints violate the rule, far enough that the centers do not
# (or the reverse, where the old approximation's error ran the other way) - and pins which verdict is
# right. Numbers are derived from the recorded sizes and the rule's own limit, so an entry says what
# it means rather than carrying a magic offset. A check that quietly reverts to centers fails here by
# name; one that reverts to half-diagonals fails the entries whose rects are elongated.
#
# TEETH, VERIFIED (2026-07-27), because 100% coverage proves nothing about a ratchet: reverting the
# helper to raw center distance breaks exactly the first three entries, and reverting it to
# circumscribed radii breaks exactly the other three. The two halves are complementary by design -
# either convention coming back fails this test by name.
def _ratchet_execution_ground(dx):
    return _justice_town(houses=[house(440 + 30 * i, 940) for i in range(6)] + [house(1500 + dx, 1060)])


def _ratchet_cremation(dx):
    return manifest(meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000}, cremation_grounds=[{"x": 500, "y": 500, "w": 116, "h": 80, "rot": 0}], houses=[house(500 + dx, 500)])


def _ratchet_burakumin(dx):
    return manifest(meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000}, buildings=[bldg(500, 500, kind="burakumin", w=38, h=26), bldg(500 + dx, 500, kind="laborer", w=34, h=24)])


def _ratchet_dead(dy):
    # An ELONGATED burial ground, measured along its SHORT axis: half-extent 20, but max(w,h)/2 = 100.
    # This is the entry that fails if anyone puts the circumscribed radius back.
    return _justice_town(cemeteries=[{"x": 1500, "y": 1060 + dy, "w": 200, "h": 40, "rot": 0, "parish": False}])


def _ratchet_well(dy):
    return manifest(meta={"scale": "village", "ftpx": 1}, buildings=[bldg(500, 500, kind="merchant", w=200, h=40)], wells=[well(500, 500 + dy)])


def _ratchet_shed(dx):
    return manifest(meta={"scale": "village", "ftpx": 1}, houses=[house(500, 500)], farm_sheds=[{"x": 500 + dx, "y": 500, "w": 20, "h": 14, "rot": 0}])


def _ratchet_tannery(dx):
    return manifest(
        meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000},
        tanning_yards=[{"x": 500, "y": 500, "w": 58, "h": 41, "rot": 0, "pits": 8, "water": "stream"}],
        houses=[house(500 + dx, 500)],
        buildings=[bldg(300, 300, kind="burakumin")],
    )


def _ratchet_charcoal(dx):
    return manifest(
        meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000, "charcoal_district": True},
        charcoal_yards=[{"x": 500, "y": 500, "w": 70, "h": 50, "rot": 0, "sheds": 2, "apron": [480, 540, 40, 30]}],
        buildings=[bldg(500 + dx, 500, kind="merchant")],
    )


def _ratchet_forge(dx):
    return manifest(
        meta={"scale": "town", "ftpx": 1, "W": 2000, "H": 2000, "iron_district": True},
        refining_forges=[{"x": 500, "y": 500, "w": 46, "h": 30, "rot": 0}],
        houses=[house(500 + dx, 500)],
    )


_GAP_RATCHET = (
    # (check, build, offset, must_fire, why this offset is the disagreement point)
    ("execution_ground_outside_the_settlement", _ratchet_execution_ground, 121, True, "centers 121 px apart clears the 120 px rule; the two walls are only 68 px apart"),
    ("town_has_cremation_ground", _ratchet_cremation, 121, True, "a 116 px wide pyre 121 px from a house CENTER stands 40 px from its wall"),
    ("burakumin_quarter_segregated", _ratchet_burakumin, 61, True, "61 px between centers is 25 px of open ground - less than half the 60 px seam"),
    ("execution_ground_clear_of_the_dead", _ratchet_dead, 460, False, "410 px of true daylight, which the old max(w,h)/2 radius scored as 330 and wrongly failed"),
    ("wells_among_dwellings", _ratchet_well, 190, True, "158 px from the hall's wall - the half-diagonal of a 200x40 hall scored it as 88 and wrongly passed"),
    ("farm_sheds_attached", _ratchet_shed, 48, True, "15 px of daylight is not 'attached'; two half-diagonals scored it as 48 against a 49 px threshold"),
    # The trade works. The first two were already exact (feature 016 wrote its own footprint helper);
    # the tannery was NOT, and the 2026-07-27 sweep missed it because its center test compared a
    # record against an unpacked tuple. All three are pinned now so none can drift back.
    ("tanning_yard_clear_of_dwellings", _ratchet_tannery, 121, True, "a 58 px wide yard 121 px from a house CENTER stands 69 px from its wall, against a 120 ft rule"),
    ("charcoal_yard_keeps_fire_gap", _ratchet_charcoal, 31, True, "31 px between centers is under a 70 px yard's own half-width - the walls overlap"),
    ("refining_forge_stands_off_dwellings", _ratchet_forge, 61, True, "61 px between centers leaves 15 px of daylight against a 60 ft standoff"),
)


# --- city_ward_fence_joins_wall_not_crosses (a neighborhood wall ENDS at the rampart) -----------
def _ward_wall(boundary, **extra):
    """A ward fence against the square WALL enclosure, with the engine's recorded stroke widths."""
    return manifest(wall=WALL, wall_stroke=11.0, wards=[{"boundary": boundary, "stroke": 5.0}], **extra)


def _ward_residents_city(*bldgs):
    # a samurai ward carved off the SE corner of the square wall; interior = (400..950, 400..950).
    # The residents-only check lives in the walled-CITY block, so the meta must say so.
    M = manifest(wall=WALL, wall_stroke=11.0, gates=[[500, 50], [500, 950]], wards=[{"name": "samurai", "boundary": [[400, 945], [400, 400], [945, 400]], "stroke": 5.0}], buildings=list(bldgs))
    M["meta"].update(scale="city", walled=True)
    return M


def _ward_servant_city(*bldgs):
    M = _ward_residents_city(*bldgs)
    M["buildings"] = list(bldgs)
    return M


# ---- the DOMAIN-CAPITAL tier is sized budget-first too (feature 018) --------------------------


def _capital_manifest(interior_frac=1.0, budget=True, scale="capital"):
    """A capital manifest whose wall encloses `interior_frac` of its declared required interior.
    The wall is a square of the right area, which is all either check reads."""
    required = 1_000_000.0
    side = math.sqrt(required * interior_frac)
    M = manifest(meta={"scale": scale, "ftpx": 3, "W": 4000, "H": 4000}, wall=[[0, 0], [side, 0], [side, side], [0, side]])
    if budget:
        M["meta"]["budget"] = {"required_interior_px2": required}
    return M


# ---- feature 020: the capital's ground-reserving layer ----------------------------------------

_CAP_GOV_CHECKS = (
    "capital_has_six_ministries",
    "capital_chancellery_meets_in_the_castle",
    "capital_has_domain_school",
    "capital_castle_has_approach_avenue",
    "capital_ministries_front_the_avenue",
    "capital_school_on_the_axis",
    "capital_government_offices_dont_abut",
    "capital_declares_lineages",
    "capital_lineage_compounds_labeled",
    "capital_ruling_lineage_seat_is_the_castle",
    "capital_lineage_bands_visibly_distinct",
)


def _cap_gov():
    """A capital with a castle, its approach avenue, a full government ward and four lineage
    compounds - everything the feature-020 government checks read. The 1000x1000 square wall
    comes from _capital_manifest; the avenue runs from the castle's south gate to the trunk road."""
    M = _capital_manifest()
    M["meta"]["lineages"] = {"hazama": "grand", "utsuro": "grand", "kurogi": "estate", "yodo": "house"}
    M["meta"]["ruling_lineage"] = "daika"
    M["gates"] = [[500, 1000], [0, 500]]
    M["castles"] = [{"x": 500, "y": 250, "w": 220, "h": 160, "rot": 0, "gate": [500, 330], "label": "Castle"}]
    M["roads"] = [{"pts": [[500, 340], [500, 700]], "w": 30}, {"pts": [[500, 700], [500, 1000]], "w": 26}]
    mins = []
    for i, nm in enumerate(("Rites", "Revenue", "Retainers")):
        mins.append({"x": 435, "y": 400 + 100 * i, "w": 75, "h": 50, "name": f"Ministry of {nm}"})
    for i, nm in enumerate(("War", "Works", "Justice")):
        mins.append({"x": 565, "y": 400 + 100 * i, "w": 75, "h": 50, "name": f"Ministry of {nm}"})
    mins.append({"x": 565, "y": 800, "w": 70, "h": 48, "name": "Domain School"})
    M["ministries"] = mins

    def _lin(x, y, w, h, name):
        return {"x": x, "y": y, "w": w, "h": h, "rot": 0, "label": f"{name.title()} Estate", "lineage": name, "gate": [x, y + h / 2], "gate_dir": "south", "ward_walls": [], "gate_w": 8, "wall_w": 2}

    M["manors"] = [_lin(150, 200, 150, 118, "hazama"), _lin(850, 200, 145, 115, "utsuro"), _lin(150, 450, 110, 85, "kurogi"), _lin(850, 450, 75, 60, "yodo")]
    return M


def _cap_water():
    """A capital with a river past its east flank, an aqueduct from an upstream intake to the
    east gate, and no road on the bank - the feature-020 waterfront checks' fixture."""
    M = _capital_manifest()
    M["gates"] = [[1000, 500]]
    M["river"] = {"pts": [[1200, 0], [1200, 1000]], "w": 40}
    M["streams"] = [{"poly": [[1200, 0], [1200, 1000]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "w": 40}]
    M["aqueducts"] = [{"poly": [[1175, 200], [1100, 300], [1030, 480]], "w": 8, "intake": [1175, 200], "to": [1030, 480]}]
    return M


def _water_map(**kw):
    M = {"meta": {"scale": "town"}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 20}]}
    M.update(kw)
    return M


# ---- feature 022: the gate registry and targeted execution --------------------------------------
# Red-first (Principle X): written against the legacy monolithic gate() where all four MUST fail;
# the 022 registry driver turns them green.


def _feature_022_manifest():
    return json.loads(json.dumps(manifest()))  # deep copy - the gate shares nested values


# ---- bund_beans_on_bunds: an azemame bead sits on a bund the finished paint SHOWS - never
# floating in a later-drawn plot's water (GM 2026-08-15, Inashiro: "random green dots ...
# scattered in the middle of flooded rice patties"). The wedge fillers lap their neighbors on
# purpose and paint LAST, so the lapped stretch of the neighbor's bund stroke is buried under
# their fill; a bead line laid there must be dropped by the placer and caught by the gate.
def _bb_M(beads, rings):
    return manifest(fields=[{**_field("f", 100, 100, 900, 900), "plot_rings": rings, "bund_beans": beads}])


_BB_HOST = [[200, 200], [400, 200], [400, 400], [200, 400]]  # painted first
_BB_FILLER = [[300, 150], [500, 150], [500, 450], [300, 450]]  # painted last, laps the host's east bund
