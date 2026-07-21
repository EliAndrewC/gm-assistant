#!/usr/bin/env python3
"""Hoshizora - an unwalled town (diagram skill, Mode B, town scale).

A county seat of ~1,200 people / ~238 households. Per budgets.md the population is
~65% farmers, plus merchants (~24 hh), laborers (~29), servants (~13), burakumin
(~12), and samurai (~4: the magistrate and staff). The map represents ALL of these
(scaled down - others off-map - but every caste present and farmers the plurality):
a rural farm zone NW around a stream, a dense urban core of merchant/laborer/servant
buildings along the Imperial Road, the Magistrate's walled manor + samurai houses SW,
the segregated burakumin neighborhood NE, a theater stage by the monastery, barns ringed by hayfield/grazing
pasture SE, and a small forest. Unwalled.

WATER (the water-first comb doctrine, settlements.md "Water-first fields v2"): the
stream is the valley watercourse, crossing the map NE -> SW roughly parallel to the
Imperial Road; the land falls with it (downhill/down_deg = 115, SSW - high NE corner,
low SW corner). The farm zone is a single build_comb fan WEDGED between the stream
(NW) and the road (SE): its sluice sits ON the stream bank (a weir diverts the water
straight into the head-race), the head-race forks into supply canals, tapering
delivery ditches drop down-slope, and the drain
collector empties into a small drainage tameike at the low road-bend corner
(pond_role="drainage", the akagahara pattern). The NE pocket is the west TIP of a
second comb running off the east edge - fed by a brook off the high ground NE,
draining off-map east. This replaced the retired legacy paddy_field quilts (45-deg
multicolor patchwork with no in-field water), which this map originally used.

COMB GRAIN (historical grounding - recorded so the numbers aren't re-derived): at the
town scale (1 px = 1 ft) plot_across=58 with row_step=(52,72) carves ~58 x 62 ft
bunded paddies, ~0.08 acre - the mid premodern range, and the scale-audit
relationship still holds (one plot visibly outsizes the 46x28 ft farmhouses beside
it). The old quilt figure of 66 px (~0.1 acre) is NOT reused: build_comb spaces
delivery ditches at 2x plot_across, and that 132 px floor skips every offtake on the
short canals a town-scale comb runs - the comb degenerates to a ditchless sliver.
58 keeps the plot in the historical band AND lets the delivery net develop.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from settlement import Settlement  # noqa: E402
from waterfields import build_comb  # noqa: E402

s = Settlement(2000, 1300, seed=386)
# EXCEPTION to the default 2-monasteries-per-town rule: Hoshizora is a quiet interior county
# seat in a historically uncontested area, and really has only the ONE town monastery (to
# Bishamon). Declared explicitly via monastery_fortunes so the gate knows it is intentional.
# downhill=[-0.42, 0.91] / down_deg=115: the land falls SSW, obliquely along the stream and
# the Imperial Road (both descend toward the low SW corner); every channel + drain runs with it.
s.meta(
    name="Hoshizora",
    scale="town",
    walled=False,
    torii_expected=1,
    monastery_fortunes=["Bishamon"],
    population=680,
    ftpx=1,
    toscale=True,
    nucleated=True,
    downhill=[-0.42, 0.91],
    down_deg=115,
    pond_role="drainage",
)  # residents DEPICTED (dwellings x5); urban housing full, most farms off-map - a slice of the ~1,200 county (the nucleated to-scale farm rows pack ~135 dwellings around the combs). ftpx=1: the GM's town scale, 1px=1ft

# ---- terrain: a small forest (SE corner) and two grazing pastures, all running OFF
# the map edge (larger than drawn)
s.forest_patch([(1660, 950), (1860, 915), (2060, 1000), (2060, 1360), (1720, 1360), (1620, 1120)])
# southern hayfield - expanded up toward the barns, off the bottom edge
s.pasture([(900, 1010), (1180, 1000), (1290, 900), (1540, 900), (1600, 1110), (1490, 1360), (910, 1360), (860, 1190)], label="hayfields & grazing", amp=32, label_xy=(1090, 1190))
# northern hayfield - the whole upland strip along the top edge, extended WEST over the high
# dry ground NW of the stream (hay country above the weir), off the top edge, with hay barns
s.pasture([(250, -50), (1660, -50), (1660, 240), (1060, 240), (700, 160), (250, 140)], label="hayfields", label_xy=(1300, 150))
for bx, by in [(1180, 140), (1420, 110), (1560, 185)]:
    s.building(bx, by, 84, 56, "barn")

# ---- the Imperial Road (SW -> NE spine), running off both edges
ROAD = [(-162, 1306), (140, 1130), (620, 850), (1100, 580), (1560, 350), (1900, 170), (2209, 6)]
s.road(ROAD, label="Imperial Road")

# ---- WATER + FARMLAND: water-first combs (see docstring). The stream runs NE -> SW between
# the hay upland (NW) and the farm wedge (SE), roughly parallel to the road, off the west edge.
s.stream([(-15, 640), (230, 500), (470, 360), (700, 210), (880, -15)])


def topo_channel(pts, frm, to, draw_w=0.0):
    """Record a water-topology channel through `pts` (source/sink grounding + the winds/hairline
    conventions) and register its no-build corridor so the farmstead rings avoid it. A bend is
    added on the longest segment when the path runs too straight (channel_winds_gently wants a
    dug channel to wind 5-50px). Pass draw_w to also draw it (a visible culvert/runoff ditch);
    zero = topology only. Same helper as the provincial-city gens."""
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[: k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1 :])
    if draw_w:
        # a DRAWN culvert goes through s.channel: recorded + drawn in the shared water group at
        # the standard bed hue, so its mouth MERGES into the receiving stream/pond like any
        # confluence (a flat field_channel stroke butt-joints against the bank - GM, 2026-07)
        s.channel(pts[0], pts[-1], frm, to, width=draw_w, pts=pts)
        return
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": 2.5})
    s.corridors.append(([(px, py) for px, py in poly], 45))  # 45 half-width: a 44x28 farmhouse corner stays off the water even center-placed at the corridor edge
    if draw_w:
        s.field_channel([(px, py) for px, py in poly], '#7C9EB0', draw_w, draw_w)


# THE MAIN COMB ("hoshizora-west"): the wedge between stream and road. Its SLUICE sits on the
# stream's east bank (a weir on the stream, ~25px off the centerline - within the 30px anchor
# band, so the engine's hairline source channel grounds to the stream; a detached leat is NOT
# an option, since every drawn stream must run off a map edge). Seed 1 lands the fan clear of
# the stream (NW), the road (SE), the monastery/funerary block (SW) and the laborers' quarter
# (NE) - the acceptance sweep that chose it tested all four clearances. (A denser-offtake
# variant was tried and reverted: its bigger fan displaced the merchant residences and the
# farm rings - the map is packed tightly enough that the comb's exact footprint is load-bearing.)
netA = build_comb(
    2000,
    1300,
    (558, 322),
    1,
    down_deg=115,
    field_fall=250,
    canal_a_len=(240, 280),
    canal_b_len=(70, 100),
    offtakes_a=(0.4, 0.8),
    offtakes_b=(0.5,),
    plot_across=58,
    row_step=(52, 72),
    dry_band=(22, 38),
)
netA["brook"] = []  # no auto-brook (it would shoot into the town); the runoff's real sink is the tameike
ENV_A = s.draw_comb_field(netA, "hoshizora-west", {"kind": "stream"})  # no polyline: the map's stream IS the source
# the WEIR: the head-race's visible intake, drawn from the sluice's perpendicular FOOT on the
# stream centerline (the same confluence point draw_comb_field snaps the recorded hairline's
# start to); _clip_to_stream trims this drawn mouth onto the bank edge so it joins the current
# without crossing it. Drawing only - the snapped hairline carries the manifest topology.
s.field_channel([(549.1, 308.4), (558, 322)], '#6C9CBE', 7, 7)
s.field_polys.append([(x, y) for x, y in ENV_A])
s.corridors.append(([(p[0], p[1]) for p in s.M["channels"][-1]["poly"]], 45))  # keep farmsteads off the hairline feed


def grow_poly(poly, m=8):
    # register hem plots INFLATED by ~8px: _fits tests the base house rect, but a drawn farmstead
    # can exceed it (attached shed, rotation, wealth render scale), and the checks test the real
    # footprint - the margin absorbs that slack so no farm building ever laps the hem crop
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1.0
        out.append((x + dx / ln * m, y + dy / ln * m))
    return out


for _dp in netA["dry_plots"]:
    s.dry_polys.append(grow_poly(_dp["poly"]))  # footprint-aware: houses/yards/sheds stay OFF the hem crop
# the DRAINAGE TAMEIKE at the low road-bend corner: the collector's outfall empties into it
# (pond_role="drainage" - a reservoir BELOW the field). Sited in the low pocket between the
# flophouse, the road bend, and the manor - the only low ground the town leaves open, which
# is exactly where a real tameike sits.
_drainA = [c for c in netA["channels"] if c["role"] == "drain"][0]["pts"]
_outA = _drainA[-1]
POND = (430, 895, 44, 26)
s.pond(*POND)
# reed fringe on the NORTH arc of the rim only (+16): the Imperial Road bends past the south
# side, and a road never runs through marshland (roads_clear_of_marsh)
_pring = [(POND[0] + (POND[2] + 16) * math.cos(a), POND[1] + (POND[3] + 16) * math.sin(a)) for a in [i * math.pi / 8 for i in range(8, 17)]]
s.marsh(_pring, role="pond_fringe")
s.block_polys.append(
    [
        (POND[0] - POND[2] - 34, POND[1] - POND[3] - 34),
        (POND[0] + POND[2] + 34, POND[1] - POND[3] - 34),
        (POND[0] + POND[2] + 34, POND[1] + POND[3] + 34),
        (POND[0] - POND[2] - 34, POND[1] + POND[3] + 34),
    ]
)  # wide pad: block_polys tests centers, so the pad must absorb a house half-footprint
topo_channel([_outA, ((_outA[0] + POND[0]) / 2, (_outA[1] + POND[1]) / 2 + 14), (POND[0], POND[1])], {"kind": "drain"}, {"kind": "pond"}, draw_w=2.5)

# THE NE POCKET COMB ("hoshizora-ne"): the west TIP of a larger field running off the east
# edge (a town map shows a slice of the county's farmland). Fed by a brook off the high
# ground NE (off-map); its drain collector discharges off-map east (the sink stub below
# carries the topology, angled SSE so it still runs downhill).
netE = build_comb(
    2300, 1300, (2010, 570), 6, down_deg=115, field_fall=145, canal_a_len=(280, 320), canal_b_len=(55, 75), offtakes_a=(0.55, 0.95), offtakes_b=(), plot_across=58, row_step=(52, 72), dry_band=(18, 30)
)
netE["brook"] = []  # the drain already leaves the map east; no brook
ENV_E = s.draw_comb_field(netE, "hoshizora-ne", {"kind": "stream", "stream": [(2012, 470), (2004, 522), (2010, 570)]})
s.field_polys.append([(x, y) for x, y in ENV_E])
s.corridors.append(([(p[0], p[1]) for p in s.M["channels"][-1]["poly"]], 45))
for _dp in netE["dry_plots"]:
    s.dry_polys.append(grow_poly(_dp["poly"]))
_drainE = [c for c in netE["channels"] if c["role"] == "drain"][0]["pts"]
_onmapE = [p for p in _drainE if p[0] < 1995][-1]
# sink stub angled SSE (mostly along the fall) so channels_flow_downhill holds; ends off-map east
topo_channel([_onmapE, (2010, _onmapE[1] + 95)], {"kind": "drain"}, {"kind": "offmap"})

# ---- the Shrine to Bishamon, by the stream
# a town's religious building is a monastery (not a village shrine), with a torii in front
s.shrine_hall(215, 800, "Monastery of Bishamon", w=132, h=86, kind="monastery", primary=True, torii=[(215, 892)], label_below=True)

# ---- the Magistrate's walled manor (county seat) - walls only; its interior
# (hall, stables, etc.) is the subject of a separate Mode A diagram. TILTED (rot=-30) so its front
# wall runs PARALLEL to the Imperial Road, which crosses NW-to-NE just past this SW edge; the gate
# (north side) opens onto that road. The tilted footprint reshuffles the dense town's seeded packs,
# which is why this map's seed (386) was chosen - it lands the depicted population back on its mark.
s.manor(500, 1120, 250, 180, "Magistrate's Manor", gate_dir="north", rot=-30)

# the market flophouse (kichin-yado) just off the road on the SW approach, where peasants
# traveling in for market day arrive - they sleep on straw for a sen a night. (Nudged west of
# its old spot to clear the drainage tameike at the road bend.)
s.flophouse(300, 920)

# ---- the THEATER STAGE - a roofed performance stage + open viewing ground - in the Bishamon monastery's
# precinct (just south of it), the festival/troupe venue belonging to the temple. A quiet county seat, so
# a modest stage. The barns sit in the grazing pasture (SE).
s.theater_stage(200, 990, w=120, h=84, rot=180, label="theater stage")  # rot=180: the monastery is NORTH, so the stage faces north (its viewing ground opens toward the hall, the audience between)
s.building(1080, 1110, 88, 58, "barn")
s.building(1330, 1150, 84, 56, "barn")
s.label(1200, 1058, "barns", 10, italic=True)

# ---- urban core, sized to the town's documented non-farmer households (budgets.md):
# ~24 merchant houses, ~14 shops, ~29 laborer dwellings, ~5 standalone servants. The
# BUSINESSES front the Imperial Road (the high street), each facing the roadbed; the
# laborers' and servants' housing sits back off the road, behind the shopfronts.
ROAD_CORE = [(470, 945), (760, 760), (1060, 600), (1360, 450), (1700, 278)]
s.frontage(ROAD_CORE, (["merchant"] * 3 + ["shop"]) * 11, width=26, setback=16, spacing=48, rows=2, skip=ROAD)
s.label(972, 586, "merchant houses & shops", 11, italic=True, color="#5A4326")
# a MINORITY of the wealthy keep larger RESIDENCES (budgets.md town wealth tiers): a few VERY-RICH / RICH
# merchants in big homes DIRECTLY BEHIND the storefronts (the merchant family lives over/behind its own
# shop), ahead of the laborer warren set further back. Derived from the ACTUAL shop positions (not fixed
# coords), so each home is behind the band and parallel to its shop under ANY seed; placed BEFORE the packs,
# which then flow AROUND them. The ~3 MASTER (rich) laborers get larger dwellings at the edge of the warren.
s.merchant_residences(4)
for lx, ly in [(1328, 235), (740, 298), (1445, 745)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")
# a fixed plain laborer dwelling at the warren's east edge - the packs saturate one short of
# the budgets.md band, so this one is pinned (stable across the packs' RNG)
s.building(1625, 1000, *s._dims("laborer"), "laborer")
# laborers' and servants' housing, set back off the road behind the shopfronts (NW and SE)
s.pack((680, 190, 1150, 395), ["laborer"] * 11, step=40)  # laborers at the budgets.md band floor (25 total with the SE pack + the 3 masters) so the depicted farmer cohort stays the plurality
s.pack((1165, 700, 1600, 925), ["servant"] * 16 + ["laborer"] * 14, step=40)
s.label(1010, 224, "laborers' dwellings", 10, italic=True, color="#5A4326")  # the set-back is self-evident on the map (annotations explain the unusual, not the universal)

# ---- the segregated burakumin neighborhood (NE edge). Set back a full 74+ ft behind the
# road frontage: the aligned-behind-storefronts rule treats any dwelling 15-74 ft directly
# behind a shop as row housing that must lie parallel, and this quarter is its own cluster,
# not part of the shopfront rows. (Shifted up ~80px from its old spot so the NE pocket comb
# below it has room for its head.)
s.pack((1725, 395, 2005, 600), ["burakumin"] * 16, step=42)
s.label(1855, 382, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")

# ---- samurai houses, around the magistrate's manor (SW); their servants live within
# the manor/samurai compounds, not as separate huts
s.pack((620, 1010, 920, 1295), ["samurai"] * 10, step=54)
s.label(770, 1268, "samurai houses", 11, italic=True)  # over the cluster - kept above the bottom image edge (canvas H=1300)

# a noticeable minority of merchant houses keep a fireproof kura (the absentee landlords'
# rent-rice / bulk goods), drawn AFTER the businesses exist
s.merchant_storehouses(6)

s._nucleated = True  # town-fringe farms pack in tight mutually-sheltering rows (the NUCLEATED
# homestead bundle: house + south threshing yard + adaptive sunny garden + reserved north kura;
# no per-farm grove - a nucleus shelters itself, per settlements.md 'Settlement form')

# funerary ground BEHIND the monastery, placed BEFORE the farm rings (the to-scale homestead
# bundles reserve yard+garden+grove footprints, so the graveyard must already be an obstacle
# they pack around): the parish graveyard (Buddhist danka) against the BACK of the hall, the
# cremation ground (monk-run, burakumin assistants) on the marginal western edge beyond it -
# both behind the hall so no one walks past the pyre to reach the monastery.
s.cemetery(215, 705, 110, 80, label="graveyard", label_above=True)
s.cremation_ground(85, 810, label_above=True)
# keep-out ring around the crematory: town_has_cremation_ground demands >120 ft clear of every
# dwelling, so no farm bundle may pack into that radius (blocked BEFORE the rings run).
# Centered a touch WEST of the crematory so the ring covers the full 120 ft on every side
# while leaving the monastery center (215,800) outside it - the ring must not swallow the
# monastery's own ablution-well spot (remote_shrine_has_own_well).
s.block_polys.append([(72 + 136 * math.cos(a), 815 + 136 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]])
# ...and a small block on the road-frontage corner SE of the comb: the shopfronts there stand
# ROTATED along the diagonal road, and the bundle packer's axis-aligned placed-rect test cannot
# see a rotated corner - one farm kept packing into a shop's swung corner (no_structure_overlaps)
s.block_polys.append([(615, 855), (835, 855), (835, 940), (615, 940)])
# ...and a thin strip between the burakumin quarter and the NE comb's head: a bundle packed
# there stands hard against the quarter's door row (city_house_doors_unblocked)
s.block_polys.append([(1720, 590), (2010, 590), (2010, 665), (1720, 665)])

# ---- farmhouses: the town's farmer majority (still the largest single group), ringed
# several-deep around the comb envelopes - generously, since each needs room for its
# threshing yard (some get dropped). Dense rings so the shown field edges read WORKED
# (outside_fields_farmhouse_density wants ~village density along the on-map edge).
for bb, rings in ((('poly', ENV_A), [(48, 14), (42, 40), (34, 66), (28, 92), (22, 118), (16, 144)]), (('poly', ENV_E), [(28, 14), (24, 40), (20, 66), (16, 92)])):
    for n, gap in rings:
        s.ring(bb, n, gap, ["plain"])


# CULL THE WET TOE: the rings surround the whole envelope, but the ground DOWNSLOPE of each
# drain collector is the wettest in the valley - not building ground (dwellings_above_field_drain;
# the same rule the dispersed hamlets follow). Drop every ring house that landed below a drain.
def cull_wet_toe(drain_pts, margin=-5):  # negative: safety band, _solve_homestead may nudge a farm ~20px after the cull
    # operates on the PENDING farmstead reservations (ring/try_place queue them; farmsteads()
    # only draws them later - M["houses"] is still empty here)
    dux, duy = math.cos(math.radians(115)), math.sin(math.radians(115))
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
            d = math.hypot(h["x"] - px, h["y"] - py)
            at_end = (i == 0 and tt <= 0.001) or (i == len(drain_pts) - 2 and tt >= 0.999)
            if best is None or d < best[0]:
                best = (d, px, py, at_end)
        _d, px, py, at_end = best
        if not at_end and (h["x"] - px) * dux + (h["y"] - py) * duy > margin:
            continue  # clearly on the wet (downslope) side of the collector - no farm here
        keep.append(h)
    s._pending_farmsteads[:] = keep


cull_wet_toe(_drainA)
cull_wet_toe(_drainE)

# HAND-PLACED farmsteads on the dry margins the random rings under-serve: a row on the stream's
# NW bank (farms working the west comb across footbridges - the dry high bank is exactly where
# they build), and the west flank of the NE pocket (between the servants' quarter and the
# forest). try_place runs the same homestead-fit solve as the rings, so a spot that cannot host
# its yard+garden is simply dropped.
for fx, fy in [
    (405, 315),
    (475, 282),
    (545, 250),
    (340, 355),
    (585, 218),
    (270, 400),
    (700, 430),
    (706, 500),
    (712, 570),
    (718, 640),
    (438, 248),
    (368, 290),
    (300, 345),
    (1590, 800),
    (575, 795),
    (640, 755),
    (1665, 700),
    (1668, 775),
    (1682, 850),
    (1600, 740),
    (1612, 660),
    (1640, 880),
]:
    s.try_place(fx, fy, "plain")

# a caravan INN + STABLES on the Imperial Road through-route, with open ground beside the stables as a
# pasture for the wagon-train animals (oxen, horses) - like a provincial city's gate caravan facilities,
# but a county town needs only the ONE; it FRONTS the Imperial Road on the quiet SW approach (caravans pull up to it)
s.inn(276, 1116, rot=150)
s.stables(276, 1202, rot=150)


# draw the farmhouses, each with its threshing/drying yard (universal); LAST so every obstacle is known
s.farmsteads()

# the COMMUNAL WINDBREAK (后龙林 back-village grove): a nucleated cluster shelters behind ONE
# village-scale belt on its high WINDWARD (NW) edge instead of per-farm groves - the band runs
# along the top-left upland margin OUTSIDE the farm rows (clumps auto-skip any house/yard/
# garden, so the belt must lie on genuinely open ground to actually render)
s.village_grove([(12, 165), (95, 148), (185, 158), (240, 175), (250, 240), (245, 330), (180, 350), (95, 330), (14, 320)], role="windbreak")
# ...and the leafy scatter: bamboo + dooryard fruit filling the OPEN gaps through the whole
# farm belt (clumps skip every house/yard/garden/paddy, settling into the bare ground between
# homes - the greenery the per-farm groves used to carry)
# ...shaped AROUND the comb + its hem (a copse fills gaps between homes, not the crop)
s.village_grove([(20, 120), (700, 120), (690, 250), (360, 285), (20, 310)], role="copse", dense=False)
s.village_grove([(20, 330), (180, 365), (130, 545), (20, 520)], role="copse", dense=False)
s.village_grove([(700, 270), (780, 330), (795, 690), (715, 640)], role="copse", dense=False)
s.village_grove([(1600, 620), (1740, 645), (1735, 935), (1620, 925)], role="copse", dense=False)

# communal WELLS among the FINAL dwellings (placed after farmsteads so they sit among the houses)
s.place_wells((60, 30, 1980, 1270), spacing=220, near=100)  # grid widened to reach the off-edge fields' farms (top + NE pocket)
# the Bishamon monastery sits apart from the houses, so it keeps its OWN ablution well
# (remote_shrine_has_own_well) - placed BY HAND at the proven spot SW of the hall: the crematory
# keep-out block makes shrine_well's automatic ring search reject every candidate, but the block
# only steers FARM placement; a wellhead here is clear of the hall, the torii, and the graveyard
s.well(167, 883)

s.title("Hoshizora")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "hoshizora")))
