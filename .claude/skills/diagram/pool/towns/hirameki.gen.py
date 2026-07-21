#!/usr/bin/env python3
"""Hirameki - a WALLED border town (diagram skill, Mode B, town scale).

A county seat of ~1,200 (per budgets.md), drawn TO SCALE at the GM's town scale, 1px = 1ft
(the scale-ladder pass: the old bscale 0.82 grain implied ~1.3 ft/px and made this the one
town out of step with the others). Historically a Chinese walled county seat / Japanese
jokamachi keeps the urban castes - merchants, artisans, LABORERS, servants, and samurai -
INSIDE the walls, zoned around the magistrate's hilltop citadel; only the farmland/farmhouses,
the segregated burakumin neighborhood, and a small guan-xiang gate-market lie outside. The
surrounding farmers retreat inside during a raid. The hill's steep back defends the north
flank; the Imperial chrysanthemum field abuts the inside of the west rampart.

WATER (the water-first comb doctrine, settlements.md "Water-first fields v2"; this replaced
the retired legacy paddy_field quilts this map originally used): the land falls SOUTH
(downhill="south" / down_deg=90), and every field is a build_comb fan with a real source and
a real sink:

- w1 (NW, outside the wall): fed by its OWN hill brook off the north edge, fully diverted at
  the sluice (the akagahara pattern); MIRRORED chirality so its drain collector descends WEST
  and empties back into the west stream through a short culvert.
- w2 (W, running off the west edge): fed by a brook in from the west edge; its collector
  discharges off-map west.
- e1 (NE, between wall and east stream): fed by its own hill brook off the north edge;
  collector culverts east into the east stream.
- e2 (E, below e1): fed by CASCADE - a drawn connector carries e1's surplus from its drain
  down into e2's head (tagoshi between fields, one shared component tracing to e1's brook);
  collector culverts east into the east stream.
- every culvert mouth reaches the receiving stream's CENTERLINE (stream_at_y), so the join is
  a real confluence (channels_join_streams_at_confluence); _clip_to_stream trims the drawn bed
  back onto the bank edge so the mouth covers the bank stroke without crossing the current.
- s1 (S of the gate, running off the bottom edge): the west stream itself BENDS southeast
  below w2 and is swallowed whole at s1's sluice (a stream diverted into an irrigation head,
  the sanctioned brook-into-channel ending); the comb runs off the bottom edge and its
  collector discharges off-map south.

COMB GRAIN (historical grounding, same numbers as Hoshizora - recorded so they aren't
re-derived): at 1 px = 1 ft, plot_across=58 with row_step=(52,72) carves ~58 x 62 ft bunded
paddies, ~0.08 acre - the mid premodern range, one plot still visibly outsizing the 46x28 ft
farmhouses (the scale-audit relationship). The old quilt figure of 66 px is NOT reused:
build_comb spaces delivery ditches at 2x plot_across, and that 132 px floor skips every
offtake on the short canals a town-scale comb runs - 58 keeps the plot in the historical
band AND lets the delivery net develop.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from settlement import Settlement  # noqa: E402
from waterfields import build_comb  # noqa: E402

s = Settlement(2600, 2000, seed=77)
# downhill is SOUTH: the hill/manor sit in the north, so the land falls away southward and
# the streams flow north-to-south; irrigation channels must run downhill (tap upstream/north
# of where they feed each field)
# Clan: LION (current holder) - its patron fortunes are Bishamon + Daikoku. But Hirameki
# CHANGED HANDS during the Lion/Crane war, so its monasteries are special (override): the
# main one is to Bishamon (Lion's), and a much smaller, older one to Benten (Crane's) sits
# on the far side of town - a relic of Crane rule. Hence monastery_fortunes is set explicitly.
s.meta(
    name="Hirameki",
    scale="town",
    walled=True,
    torii_expected=5,
    downhill="south",
    down_deg=90,
    clan="Lion",
    monastery_fortunes=["Bishamon", "Benten"],
    population=820,
    ftpx=1,
    toscale=True,
    nucleated=True,
)  # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county. ftpx=1 -> bscale 1.0

# ---- OUTSIDE the walls: the two valley streams. The WEST stream now BENDS southeast below
# the w2 field and runs to the s1 comb's sluice, where a weir swallows it whole into the
# irrigation head (its lower course IS s1's water supply). The EAST stream runs through.
WS = [(250, -10), (175, 470), (255, 940), (160, 1400), (300, 1620), (560, 1680), (700, 1700)]
ES = [(2430, -10), (2390, 560), (2460, 1100), (2400, 2010)]
s.stream(WS)
s.stream(ES)


def topo_channel(pts, frm, to, draw_w=0.0):
    """Record a water-topology channel through `pts` (source/sink grounding + the winds/hairline
    conventions) and register its no-build corridor so the farmstead rings avoid it. A bend is
    added on the longest segment when the path runs too straight (channel_winds_gently wants a
    dug channel to wind 5-50px). Pass draw_w to also draw it (a visible culvert/runoff ditch);
    zero = topology only. Same helper as the provincial-city gens and Hoshizora."""
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        b = max(6.0, min(12.0, 0.28 * chord))  # bend scaled to the chord: a short stub keeps directness (<=1.6x)
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[: k + 1]) + [(mx - b * (by - ay) / chord, my + b * (bx - ax) / chord)] + list(pts[k + 1 :])
    if draw_w:
        # a DRAWN culvert goes through s.channel: recorded + drawn in the shared water group at
        # the standard bed hue, so its mouth MERGES into the receiving stream/pond like any
        # confluence (a flat field_channel stroke butt-joints against the bank - GM, 2026-07)
        s.channel(pts[0], pts[-1], frm, to, width=draw_w, pts=pts)
        return
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": 2.5})
    s.corridors.append(([(px, py) for px, py in poly], 45))


def grow_poly(poly, m=7):
    # register hem plots INFLATED by ~7px (= the grove check's B margin, so engine and check agree): _fits tests the base house rect, but a drawn
    # farmstead can exceed it (attached shed, rotation), and the checks test the real
    # footprint - the margin absorbs that slack (same helper as Hoshizora)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1.0
        out.append((x + dx / ln * m, y + dy / ln * m))
    return out


def mirror_comb(net, mx):
    """Flip a build_comb net's CHIRALITY about the vertical line x=mx (the sluice x). For a
    south fall (down_deg=90) the mirrored fall is unchanged, so this purely swaps which flank
    carries the wide canal-A fan and where the drain descends - real combs came in both hands
    (same rationale as Tango's mirror_ym, about a vertical axis instead)."""

    def m(pts):
        return [(2 * mx - x, y) for x, y in pts]

    net["envelope"] = m(net["envelope"])
    for p in net["plots"]:
        p["poly"] = m(p["poly"])
    for dp in net["dry_plots"]:
        dp["poly"] = m(dp["poly"])
        dp["theta"] = math.pi - dp["theta"]  # a furrow heading mirrors with the frame
    for c in net["channels"]:
        c["pts"] = m(c["pts"])
    net["bund_beans"] = m(net["bund_beans"])
    if net["brook"]:
        net["brook"] = m(net["brook"])
    return net


def stream_at_y(poly, y):
    """The stream centerline's point at height y (the valley streams run essentially N -> S, so
    the first segment crossing y gives the confluence point a culvert mouth should reach)."""
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        if (ay - y) * (by - y) <= 0 and ay != by:
            return (ax + (bx - ax) * (y - ay) / (by - ay), y)
    return poly[-1]


def toe_block(drain_pts, depth=250, slack=6):
    # a no-build BLOCK over the wet toe below a drain collector: unlike the post-hoc cull, a
    # block poly is honored by placement AND by the homestead-solve nudges, so a farm can never
    # end up nudged into the toe after the cull has run
    top = [(x, y + slack) for x, y in drain_pts]
    bot = [(x, y + depth) for x, y in reversed(drain_pts)]
    s.block_polys.append(top + bot)


def comb(name, net, source):
    """Draw + register one comb: envelope CLAMPED to the planting, then into field_polys, hem
    plots (grown) into dry_polys, the hairline feed's corridor registered. Returns (envelope,
    drain polyline). The clamp: a pinched flank's boundary thread can wander ~150px past the
    last carved plot (a phantom flap with no crop under it - field_outline_matches_planting
    fails, and w2's flap even swallowed the stream); the envelope is manifest geometry only
    (the render is the plots themselves), so clamping it to the plots' bbox +40px is safe."""
    pv = [v for p in net["plots"] for v in p["poly"]]
    env = net["envelope"]
    px0, py0, px1, py1 = min(v[0] for v in pv), min(v[1] for v in pv), max(v[0] for v in pv), max(v[1] for v in pv)
    ex0, ey0, ex1, ey1 = min(p[0] for p in env), min(p[1] for p in env), max(p[0] for p in env), max(p[1] for p in env)
    x0 = px0 - 40 if px0 - ex0 > 55 else ex0  # clamp ONLY a flapping side (>55px past the crop);
    y0 = py0 - 40 if py0 - ey0 > 55 else ey0  # faithful sides keep the exact outline so gardens/
    x1 = px1 + 40 if ex1 - px1 > 55 else ex1  # groves near the head stay fenced by it
    y1 = py1 + 40 if ey1 - py1 > 55 else ey1
    net["envelope"] = [(min(max(x, x0), x1), min(max(y, y0), y1)) for x, y in env]
    env = s.draw_comb_field(net, name, source)
    s.field_polys.append([(x, y) for x, y in env])
    if source.get("kind") != "cascade":
        s.corridors.append(([(p[0], p[1]) for p in s.M["channels"][-1]["poly"]], 45))
    for dp in net["dry_plots"]:
        s.dry_polys.append(grow_poly(dp["poly"]))
    # no-build corridors over the comb's own canals/ditches: the boundary canals RUN ON the
    # envelope edge, so a farmstead abutting the field would otherwise drop its garden/yard
    # right on the ditch stroke (gardens_clear_of_channels)
    for c in net["channels"]:
        s.corridors.append(([(p[0], p[1]) for p in c["pts"]], 26))
    return env, [c for c in net["channels"] if c["role"] == "drain"][0]["pts"]


# ---- the five combs (seeds/params from the acceptance sweeps: clear of streams/wall/roads,
# drain outfalls landing on their sinks, the two LARGEST fields differing in orientation -
# e1 WIDE vs s1 TALL - for common_fields_vary_orientation)
# w1: MIRRORED, own hill brook off the N edge, collector culverts west into the stream
netW1 = mirror_comb(
    build_comb(
        2600,
        2000,
        (420, 330),
        14,
        down_deg=90,
        field_fall=310,
        canal_a_len=(210, 250),
        canal_b_len=(60, 80),
        offtakes_a=(0.55, 0.95),
        offtakes_b=(),
        plot_across=58,
        row_step=(52, 72),
        dry_band=(36, 64),
    ),
    420,
)
netW1["brook"] = []
ENV_W1, DR_W1 = comb("hirameki-w1", netW1, {"kind": "stream", "stream": [(430, -12), (426, 150), (420, 330)]})
toe_block(DR_W1)
topo_channel([DR_W1[-1], stream_at_y(WS, DR_W1[-1][1] + 16)], {"kind": "drain"}, {"kind": "stream"}, draw_w=2.5)

# w2: MIRRORED, fed by a brook in from the west edge, collector discharges off-map west
netW2 = mirror_comb(
    build_comb(
        2600,
        2000,
        (60, 920),
        2,
        down_deg=90,
        field_fall=250,
        canal_a_len=(210, 250),
        canal_b_len=(60, 80),
        offtakes_a=(0.55, 0.95),
        offtakes_b=(),
        plot_across=58,
        row_step=(52, 72),
        dry_band=(36, 64),
    ),
    60,
)
netW2["brook"] = []
# the on-map plots stop well west of the canal net here (most of w2 is off-map), so a delivery
# tail can overshoot the planted edge into bare ground - trim every branch to the crop
_w2_pmax = max(v[0] for p in netW2["plots"] for v in p["poly"])
_w2_pminy = min(v[1] for p in netW2["plots"] for v in p["poly"])
for _c in netW2["channels"]:
    if _c["role"] == "branch":
        _trimmed = [p for p in _c["pts"] if p[0] <= _w2_pmax + 6]
        if len(_trimmed) >= 2:
            _c["pts"] = _trimmed
        if _c["pts"][-1][1] < _w2_pminy - 4:
            # a tail stopping ABOVE the crop dangles in bare ground - bend it straight down-fall
            # into the plot head so the delivery visibly reaches the rice it waters
            _c["pts"] = list(_c["pts"]) + [(_c["pts"][-1][0], _w2_pminy + 4)]
ENV_W2, DR_W2 = comb("hirameki-w2", netW2, {"kind": "stream", "stream": [(-12, 856), (24, 886), (60, 920)]})
toe_block(DR_W2)


def _drain_at_x(dr, x):
    for i in range(len(dr) - 1):
        (ax, ay), (bx, by) = dr[i], dr[i + 1]
        if (ax - x) * (bx - x) <= 0 and ax != bx:
            t = (x - ax) / (bx - ax)
            return (x, ay + (by - ay) * t)
    return dr[-1]


_onW2 = _drain_at_x(DR_W2, 35)
topo_channel([_onW2, (-14, _onW2[1] + 22)], {"kind": "drain"}, {"kind": "offmap"})
# the collector's EAST end would otherwise dangle mid-air beside the stream: a short relief
# culvert tees the excess back into the stream at a proper confluence
topo_channel([DR_W2[0], (stream_at_y(WS, DR_W2[0][1] + 17))], {"kind": "drain"}, {"kind": "stream"}, draw_w=2.5)

# e1: default chirality, own hill brook off the N edge, collector culverts east into the stream
netE1 = build_comb(
    2600, 2000, (2130, 330), 47, down_deg=90, field_fall=390, canal_a_len=(240, 280), canal_b_len=(60, 80), offtakes_a=(0.55, 0.95), offtakes_b=(), plot_across=58, row_step=(52, 72), dry_band=(36, 64)
)  # fall 390: decisively TALL, so the two LARGEST fields (this one + the WIDE w1) differ for common_fields_vary_orientation
netE1["brook"] = []
ENV_E1, DR_E1 = comb("hirameki-e1", netE1, {"kind": "stream", "stream": [(2140, -12), (2136, 160), (2130, 330)]})
toe_block(DR_E1, depth=140)  # shallower: e2's head needs its worked margin below
topo_channel([DR_E1[-1], stream_at_y(ES, DR_E1[-1][1] + 40)], {"kind": "drain"}, {"kind": "stream"}, draw_w=2.5)

# e2: CASCADE-fed from e1 (the connector below carries the source topology), collector
# culverts east into the stream
netE2 = build_comb(
    2600, 2000, (2170, 930), 14, down_deg=90, field_fall=230, canal_a_len=(260, 300), canal_b_len=(60, 80), offtakes_a=(0.55, 0.95), offtakes_b=(), plot_across=58, row_step=(52, 72), dry_band=(18, 30)
)
netE2["brook"] = []
# cascade-fed: no sluice exists, so the auto head-race would dangle with a free top end
# (GM: "channels just ending"). Shorten it to a short THROAT above the fork; the cascade
# connector below runs through the throat's top, so the water visibly arrives there.
netE2["channels"][0]["pts"] = [(2170, 1000), (2170, 1020)]
ENV_E2, DR_E2 = comb("hirameki-e2", netE2, {"kind": "cascade"})
toe_block(DR_E2)
# the cascade connector: e1's drain outfall -> a gentle diagonal culvert -> just past e2's
# FORK. The end sits 15px inside the e2 planting (the to=field anchor + fields_show_water_
# source) AND within the 16px union tolerance of e2's head-race, so the two combs' ditch
# nets join into one component that traces to e1's brook (field_ditches_reach_source_and_sink).
# ...routed THROUGH the throat's top (2170,1000), so the shortened head-race visibly receives
# the cascade water, then diving into the fan for the to=field anchor
topo_channel(
    [DR_E1[-1], (2262, 930), (2170, 1000), (2174, 1062)],
    {"kind": "drain"},
    {"kind": "field", "name": "hirameki-e2"},
    draw_w=2.5,
)
topo_channel([DR_E2[-1], stream_at_y(ES, DR_E2[-1][1] + 22)], {"kind": "drain"}, {"kind": "stream"}, draw_w=2.5)

# s1: the rerouted west stream ends AT this sluice (fully diverted); runs off the bottom edge
netS1 = build_comb(
    2600, 2150, (700, 1700), 1, down_deg=90, field_fall=430, canal_a_len=(190, 220), canal_b_len=(70, 90), offtakes_a=(0.55, 0.95), offtakes_b=(), plot_across=58, row_step=(52, 72), dry_band=(36, 64)
)
netS1["brook"] = []
ENV_S1, DR_S1 = comb("hirameki-s1", netS1, {"kind": "stream"})  # no polyline: the west stream IS the source
_onS1 = DR_S1[0]
topo_channel([_onS1, (_onS1[0] + 12, _onS1[1] + 30)], {"kind": "drain"}, {"kind": "offmap"})

# ---- the hill (north) with the Magistrate's Manor on top (the citadel)
sx, sy = s.hill(1300, 480, 560, 360, steep=True)
s.manor(1300, 415, 360, 216, "Magistrate's Manor", gate_dir="south")  # gate faces the town below

# ---- the irregular rampart (anchored to the hill, climbing both flanks); the gate is
# south; the west face is a straight run the chrysanthemum field abuts flush
# the S/SE/E faces hug the built core (the monastery + laborer quarters) rather than
# enclosing empty corner space - a tighter line is cheaper to build (wall_hugs_the_town).
# The ring is the pre-rescale ring scaled ~1.22x about the hill anchor (1300,500): the same
# real wall, drawn at 1 ft/px instead of the old ~1.3 ft/px grain.
# NW face tucks IN toward the Benten pocket (two segments instead of one long diagonal):
# the straight line left a ~325 ft empty run beyond the hill base (wall_hugs_the_town)
WALL = [
    (930, 500),
    (860, 700),
    (700, 940),
    (560, 1060),
    (560, 1525),
    (665, 1610),
    (1055, 1647),
    (1300, 1720),
    (1545, 1647),
    (1910, 1525),
    (1925, 1160),
    (1855, 940),
    (1790, 500),
]  # east face pulled to ~140 ft of the Bishamon precinct (wall_hugs_the_town)
s.wall(WALL, gate=(1300, 1720))
s.label(1300, 1780, "front gate (guard station + tower)", 11, italic=True, color="#3A352C")

# ---- INSIDE: chrysanthemum field (abuts west wall), monastery, the zoned urban core
CHRYS = (567, 1134, 788, 1476)  # the Imperial chrysanthemum field (x0, y0, x1, y1)
s.flower_field(CHRYS, "chrysanthemum field", amp=8, flat_west=True)
# main town monastery (to Bishamon, the Lion patron), on the east side. It has a long, clear
# approach south to the market cross-street, so it fronts a proper torii AVENUE (sando) of
# several arches rather than a single gate (monastery_torii_scale_with_space).
s.shrine_hall(1750, 1050, "Monastery of Bishamon", w=150, h=98, kind="monastery", primary=True, torii=[(1750, 1174), (1750, 1235), (1750, 1296), (1750, 1357)])
# the older, much smaller Benten monastery (Crane patron) on the OPPOSITE (west) side, inside
# the walls - a relic of the town's time under Crane rule. It is wedged hard against the west
# rampart and the Imperial chrysanthemum field, so there is room for only a SINGLE torii arch.
s.shrine_hall(700, 1010, "Monastery of Benten", w=60, h=40, kind="monastery", primary=False, torii=[(700, 1073)])

# street plan: the gate-to-yamen main avenue + a market cross-street (both fully built up).
# The laborer/servant quarters behind them are accessed off the cross-street and otherwise
# sit as deep tenement blocks with no street frontage (the poor can't afford it) - no
# speculative back-lanes that would dead-end empty, per `streets_have_buildings`.
MAIN = [(1300, 2020), (1300, 1788), (1300, 1470), (1300, 1160), (1300, 960)]  # runs out the gate, off the edge
# The market cross-street must start EAST of the Imperial chrysanthemum field: a public street
# cannot be cut through the protected Imperial planting. This is HIRAMEKI-SPECIFIC (it is the
# only town with a flower field inside its walls), so it stays a per-map invariant rather than
# a general check in check_village.py - hence the local assertion below, which fires on every
# regeneration if a future edit drifts the cross-street back over the field.
CROSS = [(849, 1400), (1300, 1388), (1837, 1403)]
assert CROSS[0][0] >= CHRYS[2] + 30, "market cross-street must start clear of the chrysanthemum field"
s.street(MAIN, width=28, main=True, label="main street")
s.street(CROSS, width=22)

# the town's THEATER STAGE - a roofed performance stage facing an open viewing ground - sited in the Benten
# monastery's precinct, just EAST of it (the NW diagonal rampart hems the ground directly north of Benten),
# facing WEST (rot=90) so its viewing ground opens toward the Benten hall, the audience gathered between
s.theater_stage(856, 1010, rot=90, label="theater stage")

# Big fixed-position buildings go DOWN FIRST, before the packs - the packs' _fits() then flows the small
# houses AROUND them (a pack placed first fills these spots and the big building lands on a house). The
# caravan INN + STABLES just inside the front gate (a county town needs the one; a walled town keeps it
# inside the rampart, fronting the main street, open ground by the stables for the wagon-train animals):
s.inn(1372, 1139, rot=90)  # tight to the main street: no room for a shop row in front (town_has_caravan_inn)
s.stables(1520, 1139)
# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH / RICH
# merchants in big homes near the commercial core, and the ~3 MASTER (rich) laborers in larger dwellings
# among the tenements - the rest live small (the house-size variety a county town shows, like a city).
for mx, my in [(975, 1169), (1840, 1315), (1034, 1557), (1422, 1600)]:
    s.building(mx, my, *s._dims("merchant_large"), "merchant_large")
for lx, ly in [(963, 1295), (1146, 1295), (1556, 1295)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")
# two pinned plain laborer dwellings on the strip between the main-street backs and the east
# warren - the packs saturate just short of the budgets.md band floor (stable across pack RNG)
s.building(1418, 1265, *s._dims("laborer"), "laborer")
s.building(1418, 1350, *s._dims("laborer"), "laborer")

# samurai neighborhood: lining the manor's approach, below the hill
s.pack((861, 964, 1764, 1183), ["samurai"] * 9, step=70)
s.label(1030, 950, "samurai neighborhood", 11, italic=True)

# merchants + shops FRONT the main avenue and the market cross-street (facing them)
s.frontage(MAIN, (["merchant"] * 3 + ["shop"]) * 6, width=28, spacing=56, rows=2)
s.frontage(CROSS, (["merchant"] * 2 + ["shop"]) * 6, width=22, spacing=56, rows=2)
# the laborers' and servants' dwellings fill the blocks flanking the core - those next to
# the cross-street face it; the rest are deep tenement blocks with no street frontage
s.pack((540, 1200, 1130, 1600), ["servant"] * 13 + ["laborer"] * 13, step=44, face_streets="fill")
s.pack((1450, 1200, 1880, 1540), ["laborer"] * 17, step=44, face_streets="fill")
s.label(1300, 1505, "merchant houses & shops", 10, italic=True, color="#5A4326")
s.label(800, 1560, "laborers' & servants' tenements", 9, italic=True, color="#5A4326")

# ---- OUTSIDE: a small guan-xiang gate-market, the segregated burakumin neighborhood, farm rings
s.pack((1080, 1810, 1540, 1980), ["merchant"] * 6 + ["shop"] * 6, step=52, face_streets=True)
s.label(1120, 1795, "gate market", 10, italic=True, color="#5A4326")
# the market flophouse (kichin-yado), OUTSIDE the gate beside the gate market: far-traveling
# peasants who reach the town after the gate shuts at dusk sleep here for a sen before market day
s.flophouse(1720, 1880)
s.pack((2120, 1690, 2340, 1960), ["burakumin"] * 14, step=46)
s.label(2230, 1680, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")
# a noticeable minority of merchant houses keep a fireproof kura (rent-rice / bulk goods of the
# absentee landlords whose tenants farm the surrounding land), drawn AFTER the businesses exist
s.merchant_storehouses(6)

s._nucleated = True  # town-fringe farms pack in tight mutually-sheltering rows (the NUCLEATED
# homestead bundle: house + south threshing yard + adaptive sunny garden + reserved north kura;
# no per-farm grove - same conversion as Hoshizora, settlements.md 'Settlement form')

# funerary complex BEFORE the rings (bundle appurtenances reserve real footprints and must pack
# around it): the intramural parish graveyard by the Bishamon monastery, the MAIN extramural
# common burial ground, and the adjoining cremation ground (monk-run, burakumin assistants)
s.cemetery(1840, 1160, 88, 62, label="graveyard", label_above=True)
s.cemetery(2080, 1420, 120, 88, label="common burial ground")
s.cremation_ground(2100, 1513)
# keep-out ring: town_has_cremation_ground demands the crematory stay >120 ft from every dwelling
s.block_polys.append([(2100 + 132 * math.cos(a), 1513 + 132 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]])

# ---- farmhouses: ringed around the comb envelopes, densely (outside_fields_farmhouse_density
# wants ~village density along each shown edge; many attempts get dropped by the homestead solve)
for bb, rings in (
    (('poly', ENV_W1), [(15, 12), (12, 52), (9, 96)]),
    (('poly', ENV_W2), [(13, 12), (10, 52)]),
    (('poly', ENV_E1), [(15, 12), (12, 52), (9, 96)]),
    (('poly', ENV_E2), [(11, 12), (9, 52), (7, 96)]),
    (('poly', ENV_S1), [(14, 12), (12, 52), (9, 96)]),
):
    for n, gap in rings:
        s.ring(bb, n, gap, ["plain"])


# CULL THE WET TOE: drop every ring house that landed downslope of a drain collector (the
# wettest ground in the valley - dwellings_above_field_drain; same helper as Hoshizora)
def cull_wet_toe(drain_pts, margin=-5):
    keep = []
    for h in s._pending_farmsteads:
        best = None
        for i in range(len(drain_pts) - 1):
            ax, ay = drain_pts[i]
            bx, by = drain_pts[i + 1]
            vx, vy = bx - ax, by - ay
            ll = vx * vx + vy * vy or 1.0
            tt = max(0.0, min(1.0, ((h["x"] - ax) * vx + (h["y"] - ay) * vy) / ll))
            px, py = ax + vx * tt, ay + vy * tt
            at_end = (i == 0 and tt <= 0.001) or (i == len(drain_pts) - 2 and tt >= 0.999)
            if best is None or math.hypot(h["x"] - px, h["y"] - py) < best[0]:
                best = (math.hypot(h["x"] - px, h["y"] - py), px, py, at_end)
        _d, px, py, at_end = best
        if not at_end and _d <= 290 and h["y"] - py > margin:  # the check's 240 ft toe band + ~50px homestead-nudge slack
            continue
        keep.append(h)
    s._pending_farmsteads[:] = keep


for _dr in (DR_W1, DR_W2, DR_E1, DR_E2, DR_S1):
    cull_wet_toe(_dr)

# HAND-PLACED farmsteads on the strip between w2 and the stream (the rings mostly fall
# off-map west, and the shown east edge must still read worked); rejects are dropped free
for fx, fy in [
    (150, 972),
    (192, 1030),
    (196, 1105),
    (188, 1180),
    (95, 845),
    (60, 1150),
    (1932, 975),
    (1962, 1052),
    (1972, 1345),
    (1974, 1206),
    (2408, 1066),
    (2394, 1248),
    (2382, 1372),
    (1966, 1390),
    (2394, 1264),
]:  # + e2's flank pockets (scanned placeable ground; shown-edge density)
    s.try_place(fx, fy, "plain")

# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()


# communal WELLS among the dwellings (placed after them, in the open gaps); households share these, the
# rest draw from the irrigation channels/streams. Placed AFTER farmsteads() so the FINAL house set
# is known: the threshing pass abandons the odd over-crowded farmhouse, and a well must never be left
# stranded beside one that is no longer there (wells_among_dwellings).
s.place_wells((80, 300, 2500, 1975), spacing=250, near=90)
# the set-apart Benten monastery (west, far from the houses) keeps its OWN ablution well (remote_shrine_has_own_well)
s.shrine_well(700, 1010)
# the Bishamon monastery also sits apart from the dwellings at the to-scale spacing
s.shrine_well(1750, 1050)

# the COMMUNAL WINDBREAK (后龙林): the nucleated farm rows shelter behind belt lobes on the high
# WINDWARD (NW) upland above the w1 comb - two lobes flanking its feeder brook so no canopy
# stands over the water. (The matching belt above e1 sits NE of the all-farms centroid, so it is
# recorded as a leafy copse instead - the windward check wants role='windbreak' only NW.) Copse
# scatter then fills the open gaps between homes on strips shaped AROUND the fields and their
# hems. All AFTER the wells, so the canopy keep-out sees every wellhead.
# The real FOREST mass sits on the open upland CORNERS (the strips beside the farm rows are
# mostly full of homesteads, so clumps there thin to a scatter): two windward lobes in the NW
# corner flanking the west stream, and two matching lobes in the NE corner flanking e1's
# feeder brook (recorded as dense copse - they sit NE of the all-farms centroid, and the
# windward check reserves role='windbreak' for the NW side).
s.village_grove([(30, 70), (165, 55), (185, 140), (160, 225), (60, 235), (28, 160)], role="windbreak")
s.village_grove([(275, 60), (385, 70), (392, 200), (360, 280), (285, 265), (262, 150)], role="windbreak")
# ...and the NESTLING bands: the doctrine belt "nestles against and EMBRACES the cluster"
# (settlements.md) - each farm cluster gets a band hugging its windward (N/NW) fringe, wide
# enough to reach open ground so the clumps take (a band drawn only over the packed rows
# thins to scatter). The corner masses above are the wood; these bands are the wind wall.
s.village_grove([(238, 205), (396, 198), (398, 348), (240, 352)], role="windbreak")
s.village_grove([(452, 198), (626, 192), (628, 342), (454, 345)], role="windbreak")
s.village_grove([(1960, 70), (2095, 60), (2100, 215), (1975, 235)], role="copse")
s.village_grove([(2175, 55), (2350, 65), (2360, 210), (2280, 255), (2180, 225)], role="copse")
s.village_grove([(1978, 240), (2098, 232), (2100, 345), (1980, 350)], role="copse")
s.village_grove([(2172, 228), (2352, 222), (2356, 342), (2176, 345)], role="copse")
s.village_grove([(64, 795), (228, 788), (232, 858), (66, 862)], role="windbreak")
s.village_grove([(260, 380), (700, 362), (700, 415), (260, 430)], role="copse", dense=False)
s.village_grove([(640, 430), (700, 430), (700, 860), (640, 860)], role="copse", dense=False)
s.village_grove([(1940, 420), (1985, 420), (1985, 1300), (1940, 1300)], role="copse", dense=False)
s.village_grove([(1990, 835), (2190, 835), (2190, 995), (1990, 995)], role="copse", dense=False)
s.village_grove([(380, 1740), (458, 1745), (455, 1975), (380, 1975)], role="copse", dense=False)
s.village_grove([(890, 1745), (1040, 1740), (1045, 1975), (895, 1975)], role="copse", dense=False)
# ...and the SOUTHEASTERN quadrant's own wood (GM: the s1/e2 farm rows had no windbreak trees):
# a real windbreak lobe on the open SW corner (the rerouted stream bent away from it, leaving
# clear ground beside s1's western rows), a copse lobe on the open ground between the gate
# market and the burakumin quarter, and a small copse behind e2's southeastern farms
s.village_grove([(35, 1725), (200, 1710), (225, 1800), (190, 1955), (60, 1965), (30, 1850)], role="windbreak")
s.village_grove([(372, 1708), (548, 1712), (546, 1762), (374, 1760)], role="copse")
s.village_grove([(720, 1716), (880, 1712), (882, 1764), (722, 1766)], role="copse")
s.village_grove([(1800, 1700), (2050, 1690), (2060, 1800), (1900, 1830), (1795, 1790)], role="copse")
s.village_grove([(2290, 1350), (2378, 1345), (2382, 1462), (2295, 1470)], role="copse")

# ===== FIRE DEFENSE: a watch-tower =====
# Placed LAST, on a cleared seam the dense town already leaves between its building clusters - so it
# perturbs nothing and stands on an ACTUAL gap. A FIRE-WATCH TOWER (hinomi-yagura, the magistrate's
# bell-watch) stands in the tenement warren, watching its packed rooftops. WHY: settlements.md "Fire towers".
s.fire_tower(1560, 1608, label="fire-watch tower")  # SE warren fringe inside the rampart - the manifest-scanned clearest seam (61px to the nearest roof, 32 to the wall)

s.title("Hirameki")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hirameki")))
