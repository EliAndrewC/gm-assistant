"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math
import re

from l7r.diagram import settlement
from l7r.diagram.settlement import Settlement


def _town():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town")
    return s


def _crop_settlement():
    s = Settlement(2000, 1500, seed=1)
    s.meta(name="V", scale="village")
    return s


# --- NUCLEATED village: grove-less cluster, adaptive gardens, worn lanes, headman-as-farmhouse ----
def _nuc_village(seed=1):
    s = Settlement(1200, 900, seed=seed)
    s.meta(name="V", scale="village")
    s._nucleated = True
    s.field_polys.append([(640, 150), (1120, 150), (1120, 780), (640, 780)])  # a paddy to the east
    return s


def _scatter_base_points(frags):
    """The BASE coordinates of every scatter element in the given SVG fragments: tuft/reed blade
    roots (the x1,y1 each blade grows from - the exact point _sparse tested) and dot/patch centers
    (cx,cy). Blade TIPS (x2,y2) may lean a few px past the base, so assertions run on bases."""

    pts = []
    for fr in frags:
        pts += [(float(a), float(b)) for a, b in re.findall(r'x1="(-?[\d.]+)" y1="(-?[\d.]+)"', fr)]
        pts += [(float(a), float(b)) for a, b in re.findall(r'cx="(-?[\d.]+)" cy="(-?[\d.]+)"', fr)]
    return pts


def _yard_glyphs(s, yards=None):
    """Every drawn well / trough cluster / hitching rail on the map as (label, quad) - built with
    the SAME shared builders the placement and the check both use (settlement.wellhead_quad etc.),
    so these tests measure the drawn extents rather than a test-local guess at them."""
    out = [(f"well@{w['x']:.0f},{w['y']:.0f}", settlement.wellhead_quad(w)) for w in s.M.get("wells", [])]
    for i, yd in enumerate(yards if yards is not None else s.M.get("stable_yards", [])):
        if yd.get("troughs_box"):
            out.append((f"troughs@yard{i}", settlement.trough_quad(yd["troughs_box"])))
        for rl in yd.get("rails", []) or []:
            out.append((f"rail@{rl['x']:.0f},{rl['y']:.0f}", settlement.rail_quad(rl)))
    return out


def _assert_no_glyph_overlaps(s, yards=None):
    g = _yard_glyphs(s, yards)
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            assert not settlement.sat_overlap(g[i][1], g[j][1]), f"{g[i][0]} overlaps {g[j][0]}"


def _torii_city(**kw):
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple of Ebisu", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560)], **kw)
    return s


def _walled_city(fence=((300, 700), (900, 700))):
    # a city with ONE wall already drawn (a ward fence), so the torii placement can see it
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.ward("samurai", list(fence), gates=[])
    return s


def _byre_village():
    s = _crop_settlement()
    hs = [{"x": 300 + i * 170, "y": 350, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.6 - 0.1 * i} for i in range(5)]
    s.M["houses"] = hs
    for h in hs:
        s.placed.append((h["x"], h["y"], h["w"], h["h"]))
    return s, hs


_IDX_POLY = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]


# --- fragmented dooryard gardens: _garden_beds picks single / flanking / stacked / side-by-side --------
def _pos_where(pred):
    """The first (x, y) on a deterministic sweep whose position-hash lands in the wanted branch."""
    for i in range(4000):
        x, y = 100 + i * 0.7, 200 + (i * 1.3) % 500
        if pred(x, y):
            return x, y
    raise AssertionError("no position matched the predicate")  # pragma: no cover


def _village():
    s = Settlement(600, 600, seed=3)
    s.meta(name="V", scale="village")
    return s


def _city():
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    return s


def _hamlet_with_field(down_deg):
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="H", scale="hamlet", down_deg=down_deg)
    s.field_polys.append([(400, 400), (600, 400), (600, 600), (400, 600)])  # a paddy centered at (500,500)
    return s


def _caption_size(lab: list) -> float:
    # _record_label's box is len(text) * size * 0.55 wide, so the drawn size reads straight back
    # off the record - and reading it that way is the point: these tests pin what the MAP shows.
    return round((lab[2] - lab[0]) / (len(lab[5]) * 0.55), 1)  # 1dp: the record itself is rounded to 0.1px


# ---- s.quarter: first-class zoned regions (feature 006) -----------------------------------
def _zoned_city():  # was a second '_city' shadowing the line-1665 helper (seed 1 vs 3) - renamed 2026-07-24, now gated by scripts/check-duplicate-defs.py
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="C", scale="city", walled=True, population=3000, ftpx=3)
    return s


def _shoelace(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2


def _estate_settlement():
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="E", scale="city", ftpx=3, down_deg=90)
    return s


def _inwall_settlement():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="town", ftpx=1)
    s.M["ring_road"] = [[100, 100], [900, 100], [900, 900], [100, 900], [100, 100]]
    s.M["ring_road_width"] = 8
    s.M["moat"] = [[60, 60], [940, 60], [940, 940], [60, 940]]
    return s


def _max_turn_deg(pts):
    """The sharpest direction change anywhere along a polyline, in degrees."""
    worst = 0.0
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        v0, v1 = (ax - bx, ay - by), (cx - bx, cy - by)
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-9 or l1 < 1e-9:
            continue
        cosang = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (l0 * l1)))
        worst = max(worst, 180.0 - math.degrees(math.acos(cosang)))
    return worst


# ---- the LABEL STANDOFF LADDER (GM 2026-07-26) ------------------------------------------------
# The rule under test is "among seats that cover nothing, the NEAREST to the subject wins" - the
# term the old overlap-count-only scorer was missing, which let a caption float in empty ground.
def _ladder_map():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="L", scale="town")
    return s


# --- a neighborhood wall JOINS the city wall (GM 2026-07-27, Minami) ----------------------------
def _walled(gates=()):
    s = Settlement(1000, 1000, seed=1)
    s.city_wall([(200, 200), (800, 200), (800, 800), (200, 800)], gates=gates)
    return s


def _ward_city_with_samurai(*houses):
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="W", scale="city", ftpx=3)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    for x, y, kind, rot in houses:
        s.building(x, y, *s._dims(kind), kind, rot)
    s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])
    return s


# ---------------------------------------------------------------- SeatMemo (the top-up refusal memo)
# Its whole value rests on ONE property: a seat refused once stays refused, because the registries
# the scan reads only ever grow. These tests hold both halves - that it remembers while the map
# only grows, and that it FORGETS the moment anything could have freed ground. Getting the second
# half wrong is silent under-population, which is the failure this engine has already paid for
# twice (see the Indexed docstring), so each way the invariant can break gets its own case.


def _memo_city():
    s = _town()
    s.M.setdefault("buildings", [])
    return s, settlement.SeatMemo(s)


# ---- THE DAIMYO'S CASTLE (feature 019) -------------------------------------------------------
#
# The castle is drawn WALLS-ONLY with a deliberately empty court, so the tests that matter most
# are the negative ones: nothing may be recorded as a building inside it, ever.


def _castle_map(**kw):
    s = settlement.Settlement(3200, 2700, seed=3)
    s.meta(name="Cap", scale="capital", ftpx=3, walled=True)
    rec = s.castle(1600, 1300, 850, 700, **kw)
    return s, rec


# ---- feature 020: the capital's ground-reserving layer ----------------------------------------


def _cap020():
    s = settlement.Settlement(1400, 1400, seed=9)
    s.meta(name="C", scale="capital", ftpx=3, walled=True)
    return s


def _plank_bed(bend=False):
    """A minimal map with one long ditch, cultivated ground on both banks, and (optionally) a sharp
    bend in the ditch - enough for channel_footbridges to want a plank and have to choose where."""
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="Plank", scale="hamlet", ftpx=1, toscale=True, households=12, down_deg=90, water_flow=90, field_footbridges=True)
    pts = [[200.0, 700.0], [700.0, 700.0], [720.0, 660.0], [1200.0, 700.0]] if bend else [[200.0, 700.0], [1200.0, 700.0]]
    s.M["field_ditches"].append({"poly": pts, "role": "branch", "field": "plank-paddies", "w": 4.0, "w_tail": 4.0})
    # cultivated ground on BOTH banks, so every point along it reaches useful ground
    for y0, y1 in ((520.0, 690.0), (710.0, 880.0)):
        s.M["fields"].append(
            {"name": f"plank-{y0:.0f}", "kind": "paddy", "outline": [[150.0, y0], [1250.0, y0], [1250.0, y1], [150.0, y1]], "bbox": [150.0, y0, 1250.0, y1], "vis_bbox": [150.0, y0, 1250.0, y1]}
        )
    return s
