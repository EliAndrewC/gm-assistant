#!/usr/bin/env python3
"""Ubame - an unwalled BORDER town, the county seat of Ubame county (diagram skill, Mode B, town scale).

The third pool town, and deliberately the third COMBINATION: Hoshizora is unwalled with an Imperial
road, Hirameki is walled with none, and Ubame is unwalled with none - so the town gate runs over
geometry neither existing artifact exercises.

Ubame is the easternmost of Moriguchi province's five counties in the Daika domain (Scorpion), and
the county the road from the Kitsune Mori arrives in (l7r.md, "The Kurogi and the dynasty province
of Moriguchi"). It is a working charcoal district in its own right - its own stands of ubame oak,
its own kilns, and iron smelting that grew up around the fuel rather than the ore. It has NO WALLS,
after many centuries of peace with the Fox (GM, 2026-07-26).

THE BORDER is the map's organizing fact. The east edge IS the Fox/Scorpion line, and the county
magistracy stands on it: its east wall is the boundary, with a parley room built into that wall and
the border running across the room's floor (the Mode A plan, pool/magistracies/ubame-magistracy.svg,
which fixes this compound's orientation - a ceremonial SOUTH face to the county town and a frontier
EAST face). So the manor sits at the NORTHEAST with gate_dir="south", and the town falls away below
it. The line is drawn with s.border_line: a LINE OF LAW, overlap-exempt, because the magistracy
standing on it is the arrangement rather than a defect.

WATER AND FALL (settled before anything was placed). The mountains are NORTHEAST - confirmed against
the campaign map, where the range runs along the north and northeast flanks of the Kitsune Mori - so
the land falls NE -> SW: down_deg = water_flow = 135. The valley stream comes down off that high
ground close under the border, crosses the trunk road at a bridge, and runs away south off the
bottom edge. Both combs hang SOUTHWEST of their sluices, down-fall, which is what build_comb's frame
does at this bearing (canal A runs at down-42 deg, canal B at down+58, and the delivery ditches drop
down-fall between them) - so the stream is authored running nearly due SOUTH down the eastern side,
and the fans open away from it into the lower west. A stream angled across the fall instead would
have been quartered by its own fields.

THE TWO NUISANCE AXES DIVERGE HERE, which is most of this map's value as a test bed. Smoke goes
DOWNWIND (SE, from the default NW winter monsoon); filth goes DOWNSTREAM (S/SW, down the valley). On
Hoshizora and Hirameki those point the same way and the two rules cannot be told apart. On Ubame the
refining forge sits east and the tannery south, so the rules are shown to be genuinely independent
rather than accidentally agreeing.

THE ROAD IS A DOMAIN TRUNK ROAD, not an Imperial one (GM, 2026-07-26): the charcoal road, running
from the border west toward Shiro Daika. It is therefore UNLABELED - only Imperial roads are named
on these sheets, because an ordinary road's course is already visible - and the town draws NO
FARRIER, since a shoeing forge is earned by relay traffic (imperial_road_town_has_farrier is
correctly out of scope here; the ordinary smith stays inside the shop rows).

THE TRADE, drawn (feature 016). Two new works carry the county's declared economy:
  - the CHARCOAL YARD on the east approach, between the magistracy's tally and the town - roofed
    stacking sheds for conditioned stock, an OPEN COOLING APRON set apart for arriving loads
    (charcoal self-heats, so new stock may not go straight in with the old), and a weighing floor
    (the charcoal bale had no standard weight, so nothing leaves this yard unweighed);
  - the REFINING FORGE east and DOWNWIND - the okaji that works hill-smelted pig into wrought bar.
The KILNS AND FURNACES ARE NOT DRAWN, and that is canon rather than an omission: a kiln reduces
roughly six parts wood to one of charcoal, so the kiln goes to the wood and the furnace follows the
fuel out into the hills. What comes down to the town is finished charcoal and pig iron.

Full grounding, with the China-first research and the one disclosed divergence (Ubame follows the
Japanese two-site tatara/okaji split, not the Chinese adjacent-hearth arrangement, because dispersed
fuel forces two sites): specs/016-ubame-town/research.md and settlements/urban-features.md.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from settlement import Settlement  # noqa: E402
from waterfields import build_comb  # noqa: E402

s = Settlement(2200, 1500, seed=914)
s.meta(
    water_flow=135,  # DRAINAGE BEARING: the valley sends its water SW, off the NE mountains (0=E, 90=S)
    name="Ubame",
    scale="town",
    walled=False,  # centuries of peace with the Fox - GM, 2026-07-26
    clan="Scorpion",  # -> the two default monasteries, Benten and Jurojin (CLAN_FORTUNES)
    population=635,
    ftpx=1,
    toscale=True,
    nucleated=True,
    downhill=[-0.71, 0.71],
    down_deg=135,
    windward="NW",  # the East Asian winter monsoon; downwind is therefore SE, which is where the forge goes
    charcoal_district=True,  # feature 016 -> settlement_has_charcoal_yard
    iron_district=True,  # feature 016 -> settlement_has_refining_forge
    pond_role="drainage",
    near_ring_density="thin",  # HONEST, not a shortfall: charcoal-and-iron country in oak hills, where the fuel stands are the crop and the flat waterable ground is one narrow ribbon along the single valley stream
)  # NOTE: imperial_road is deliberately NOT declared - a domain trunk road, so no label and no farrier

BORDER_X = 2125

# ---- THE CLAN BORDER: the map's east edge. Drawn first, under everything, because the magistracy is
# sited against it and its wall stands ON it. Runs off both the top and bottom of the frame - a
# jurisdiction does not stop where the paper does.
s.border_line([(BORDER_X, -60), (BORDER_X, 1560)], label="the Fox border", label_xy=(BORDER_X - 96, 430))

# ---- terrain: the ubame-oak stand on the NE high ground (the charcoal country, whose kilns are off
# among the stands), and grazing on the dry upper margin west
s.forest_patch([(1560, -60), (2260, -60), (2260, 95), (2100, 122), (1880, 108), (1700, 60), (1600, 20)], label="ubame oak", label_xy=(1810, 40))
s.pasture([(-60, -60), (900, -60), (1000, 130), (820, 265), (300, 300), (-60, 210)], label="grazing", label_xy=(430, 140))

# ---- the trunk road (UNLABELED - not an Imperial road): in from the Fox border at the east, past
# the magistracy's south gate, then WSW across the map and off the west edge toward Shiro Daika
ROAD = [(2320, 300), (2125, 335), (1900, 400), (1600, 470), (1300, 545), (1000, 622), (700, 702), (400, 788), (100, 872), (-200, 955)]
s.road(ROAD)

# ---- WATER: the valley stream, down off the NE mountains under the border, across the trunk road at
# a bridge, and away south off the bottom edge. Authored UPSTREAM-FIRST, so the stored order IS the flow.
STREAM = [(1660, -30), (1630, 230), (1600, 470), (1560, 700), (1520, 930), (1470, 1160), (1420, 1390), (1390, 1530)]
s.stream(STREAM, frm={"kind": "offmap"}, to={"kind": "offmap"})
# a trunk road carrying a county's charcoal is bridged where it meets the stream, at ~(1600,470)
s.bridge(1600, 470, rot=-13, span=34, deck_w=26)


def topo_channel(pts, frm, to, draw_w=0.0):
    """Record a water-topology channel through `pts` (source/sink grounding + the winds/hairline
    conventions) and register its no-build corridor so the farmstead rings avoid it. Same helper as
    the other town/city gens - a bend is added on the longest segment when the path runs too
    straight, because channel_winds_gently wants a dug channel to wind 5-50px."""
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[: k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1 :])
    if draw_w:
        s.channel(pts[0], pts[-1], frm, to, width=draw_w, pts=pts)
        return
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": 2.5})
    s.corridors.append(([(px, py) for px, py in poly], 45))


def grow_poly(poly, m=8):
    """Register a dry hem plot INFLATED by ~8px: _fits tests the base house rect, but a drawn
    farmstead can exceed it (attached shed, rotation, wealth render scale) and the checks test the
    real footprint - the margin absorbs that slack so no farm building laps the hem crop."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        ln = math.hypot(dx, dy) or 1.0
        out.append((x + dx / ln * m, y + dy / ln * m))
    return out


# THE MAIN COMB ("ubame-west"): the farm zone below the road, opening SOUTHWEST off a weir on the
# stream's west bank. The sluice sits ~20px off the centerline, inside the anchor band.
netA = build_comb(
    2200,
    1500,
    (1535, 730),
    3,
    down_deg=135,
    field_fall=300,
    canal_a_len=(250, 300),
    canal_b_len=(80, 110),
    offtakes_a=(0.4, 0.8),
    offtakes_b=(0.5,),
    plot_across=58,
    row_step=(52, 72),
    dry_band=(22, 38),
)
netA["brook"] = []  # the runoff's sink is the drainage tameike, not a brook back into the town
ENV_A = s.draw_comb_field(netA, "ubame-west", {"kind": "stream"})
# the WEIR: the head-race's visible intake, tapping the stream UPSTREAM of the sluice so it runs
# down-fall. Its mouth is snapped ONTO the stream centerline - an intake joins its stream at a
# CONFLUENCE, never dying in the grass beside the bank (channels_join_streams_at_confluence).
topo_channel([(1562, 690), (1535, 730)], {"kind": "stream"}, {"kind": "ditch"}, draw_w=2.5)
s.field_polys.append([(x, y) for x, y in ENV_A])
s.corridors.append(([(p[0], p[1]) for p in s.M["channels"][-1]["poly"]], 45))
for _dp in netA["dry_plots"]:
    s.dry_polys.append(grow_poly(_dp["poly"]))

# THE SOUTHEAST COMB ("ubame-south"): the head of a larger field running OFF the south edge - a town
# map shows a slice of the county's farmland. Fed by its own brook off the high ground east.
netB = build_comb(
    2200,
    1760,
    (1760, 1120),
    8,
    down_deg=85,  # LOCAL fall, not the map's: this spur below the town falls nearly due SOUTH rather than following the valley's SW trend. Verisimilitude, not uniformity - and it is what makes the two combs read as different ground (common_fields_vary_orientation wants one WIDE field and one TALL one, which is what a valley-floor fan and a south-facing spur actually look like)
    field_fall=280,
    canal_a_len=(340, 380),
    canal_b_len=(60, 90),
    offtakes_a=(0.5, 0.9),
    offtakes_b=(),
    plot_across=58,
    row_step=(52, 72),
    dry_band=(18, 30),
)
netB["brook"] = []
ENV_B = s.draw_comb_field(netB, "ubame-south", {"kind": "stream", "stream": [(2270, 990), (2020, 1050), (1760, 1120)]})
s.field_polys.append([(x, y) for x, y in ENV_B])
s.corridors.append(([(p[0], p[1]) for p in s.M["channels"][-1]["poly"]], 45))
for _dp in netB["dry_plots"]:
    s.dry_polys.append(grow_poly(_dp["poly"]))
_drainB = [c for c in netB["channels"] if c["role"] == "drain"][0]["pts"]
# the SE comb's collector must reach a sink - water never just stops (watercourse_ends_reach_water).
# At this fall it usually leaves the frame under its own steam; carry it out only if it does not.
_onmapB = ([p for p in _drainB if p[1] < 1495] or [_drainB[0]])[-1]
topo_channel([_onmapB, (_onmapB[0] - 30, _onmapB[1] + 55), (_onmapB[0] - 70, 1560)], {"kind": "drain", "name": "ubame-south"}, {"kind": "offmap"})

# the DRAINAGE TAMEIKE at the west comb's low toe - a reservoir BELOW the field (pond_role="drainage")
_drainA = [c for c in netA["channels"] if c["role"] == "drain"][0]["pts"]
_outA = _drainA[-1]
POND = (1235, 1285, 46, 27)
s.pond(*POND)
_pring = [(POND[0] + (POND[2] + 16) * math.cos(a), POND[1] + (POND[3] + 16) * math.sin(a)) for a in [i * math.pi / 8 for i in range(4, 13)]]
s.marsh(_pring, role="pond_fringe")
s.block_polys.append(
    [
        (POND[0] - POND[2] - 34, POND[1] - POND[3] - 34),
        (POND[0] + POND[2] + 34, POND[1] - POND[3] - 34),
        (POND[0] + POND[2] + 34, POND[1] + POND[3] + 34),
        (POND[0] - POND[2] - 34, POND[1] + POND[3] + 34),
    ]
)
topo_channel([_outA, ((_outA[0] + POND[0]) / 2, (_outA[1] + POND[1]) / 2 + 14), (POND[0], POND[1])], {"kind": "drain", "name": "ubame-west"}, {"kind": "pond"}, draw_w=2.5)

# ---- the MAGISTRATE'S MANOR at the NORTHEAST, its EAST WALL ON THE BORDER. Walls only - the
# interior (hearing court, parley room, tally shed, sealed charcoal store) is the Mode A sheet
# pool/magistracies/ubame-magistracy.svg. gate_dir="south": that sheet gives the compound a
# ceremonial south face to the county town and a frontier east face, and the south gate opens onto
# the trunk road running past it.
s.manor(BORDER_X - 145, 240, 290, 200, "Magistrate's Manor", gate_dir="south", label_xy=(1958, 112))  # 290x200 ft = the envelope on pool/magistracies/ubame-magistracy.svg; centered so the east wall stands ON the border

# ---- the two monasteries: Scorpion's patron fortunes, Benten and Jurojin
s.shrine_hall(430, 1180, "Monastery of Benten", w=132, h=86, kind="monastery", primary=True, torii=[(430, 1248), (430, 1278)], label_below=True)
s.shrine_hall(1230, 300, "Monastery of Jurojin", w=118, h=78, kind="monastery", torii=[(1230, 362), (1230, 392)], label_below=True)

# ---- the THEATER STAGE in the Benten precinct, EAST of the hall with its viewing ground opening
# WEST toward it (rot=90) - the audience gathers between stage and hall
s.theater_stage(640, 1180, w=120, h=84, rot=90, label="theater stage")

# ---- funerary ground BEHIND the Benten monastery (south of it, away from the road), placed BEFORE
# the packs and the farm rings: the to-scale homestead bundles reserve yard+garden footprints, so
# the graveyard must already be an obstacle everything else packs around. Nobody walks past the pyre
# to reach the monastery (cremation_ground_not_between_temple_and_road).
s.cemetery(560, 1340, 104, 72, label="graveyard", label_above=True)
s.cremation_ground(705, 1412, label_above=True)
s.ossuary(800, 1452)
# keep-out ring around the crematory: town_has_cremation_ground demands >120 ft clear of every dwelling
s.block_polys.append([(705 + 145 * math.cos(a), 1412 + 145 * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]])
# the Jurojin monastery keeps its own small parish burial ground behind the hall, and - standing
# apart from the housing on the upper ground - its own ablution well (remote_shrine_has_own_well)
s.cemetery(1230, 200, 84, 56, label="graveyard", label_above=True)

# reserve both torii avenues BEFORE the packs: an arch is a structure like any other, and the
# warren would otherwise seat a dwelling on one (no_structure_on_torii)
for _tx, _ty in ((430, 1263), (1230, 377)):
    s.block_polys.append([(_tx - 58, _ty - 46), (_tx + 58, _ty - 46), (_tx + 58, _ty + 46), (_tx - 58, _ty + 46)])

# ---- the market flophouse off the road where peasants coming in for market day arrive
s.flophouse(800, 800)

# ================= THE CHARCOAL AND IRON FRONT (feature 016) =================
# THE CHARCOAL YARD on the east approach, between the magistracy's tally and the town core - the
# Kurogi wholesalers' store for what comes down from the county's own kilns and in across the border
# from the Fox. rot=-17 lays its ROAD SIDE (local -y) against the roadbed, the same square-to-your-
# frontage convention the tanning yard follows for its bank. It stands ALONE by design: the 30 ft
# fire gap is the rule, not a packing accident - a charcoal stack self-heats and can ignite with
# nobody watching it - which is why nothing is packed against it.
s.charcoal_yard(1830, 560, rot=-17, sheds=2)
s.block_polys.append([(1710, 480), (1955, 480), (1955, 645), (1710, 645)])

# THE REFINING FORGE (okaji), east and DOWNWIND of the housing - the works that turns pig iron
# smelted out at the fuel into wrought bar. Kept off the dwellings by the 60 ft standoff: an open
# charcoal hearth under a forced blast throws sparks, noise and smoke all season.
s.refining_forge(1855, 800, rot=0)
s.block_polys.append([(1740, 700), (1975, 700), (1975, 905), (1740, 905)])

# ---- the TANNING YARD, downstream on the valley stream below every intake - the burakumin trade on
# marginal bank ground. rot follows the BANK's own bearing there (the yard is a working frontage, so
# its water side must lie along the water, not square to the map). Its 120 ft stench keep-out is
# registered BEFORE the farm rings, so the steadings pack around it instead of crowding it.
s.tanning_yard(1395, 1300, rot=102, pits=4, water="stream")
s.block_polys.append([(1395 + 155 * math.cos(a), 1300 + 155 * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]])

# ---- urban core: the businesses front the trunk road (the high street), each facing the roadbed;
# the housing sits back behind the shopfronts. Counts per budgets.md - ~24 merchant houses, ~14
# shops, ~29 laborer dwellings, ~5 standalone servants, ~12 burakumin, 5-10 samurai.
ROAD_CORE = [(1500, 490), (1180, 573), (860, 655), (540, 740), (260, 820)]
s.frontage(ROAD_CORE, (["merchant"] * 3 + ["shop"]) * 13, width=26, setback=16, spacing=48, rows=2, skip=ROAD, fill=True)
s.label(1010, 512, "merchant houses & shops", 11, italic=True, color="#5A4326")
s.merchant_residences(3)
# the ~3 MASTER (rich) laborers get larger dwellings at the edge of the warren
for lx, ly in [(268, 1060), (700, 1030), (960, 405)]:
    s.building(lx, ly, *s._dims("laborer_large"), "laborer_large")
# the laborers' and servants' warren, set FURTHER back than the merchant residences with a clear
# radial gap between the two bands (merchant_residences_behind_businesses)
s.pack((300, 960, 780, 1180), ["laborer"] * 16 + ["servant"] * 12, step=40, fill=True)
s.pack((520, 300, 1150, 470), ["laborer"] * 12 + ["servant"] * 8, step=40, fill=True)
s.label(520, 942, "laborers' dwellings", 10, italic=True, color="#5A4326")

# ---- the segregated burakumin quarter, at the low southwest - the downstream corner, which is also
# the outcast side the execution ground lies past
s.pack((90, 1250, 380, 1470), ["burakumin"] * 14, step=42, fill=True)
s.label(235, 1228, "burakumin neighborhood", 11, italic=True, color="#6B4F2A")

# ---- samurai houses west of the magistrate's manor, north of the road and clear of the oak stand
s.building(1700, 300, *s._dims("samurai_large"), "samurai_large")
s.building(1520, 260, *s._dims("samurai_large"), "samurai_large")
s.pack((1420, 215, 1790, 370), ["samurai"] * 8, step=54, fill=True)
s.label(1600, 198, "samurai houses", 11, italic=True)

s.merchant_storehouses(6)

s._nucleated = True  # town-fringe farms pack in tight mutually-sheltering rows; no per-farm groves

# ---- the JUSTICE WORKS. The execution ground goes on the WEST road out, past the burakumin quarter
# - the outcast side - and emphatically NOT on the eastern frontier approach, which is the road the
# Fox delegation arrives by. That is a deliberate siting call, not an accident of the rules: a county
# does not conduct its executions at the gate its neighbor's envoys ride through. A county of ~7,000
# reaches the formal channel about once a decade, so this is bare, unfenced, weedy ground.
s.boundary_marker(247, 807)  # seat proposed and adjudicated by site_justice.py against check_village.gate() - the hand-picked one stood inside a merchant house
s.execution_ground(125, 975, rot=-16)

# a no-build band along the road's south verge through the core: the outer farm ring reached up
# into the shop rows, where a bundle's kitchen garden lapped a storefront (gardens_clear_of_structures)
s.block_polys.append([(880, 600), (1560, 435), (1600, 600), (930, 762)])

# ---- farmhouses: the farmer majority, ringed several-deep around the comb envelopes
for bb, rings in ((("poly", ENV_A), [(48, 14), (42, 40), (34, 66), (26, 92)]), (("poly", ENV_B), [(26, 14), (22, 40), (18, 66)])):
    for n, gap in rings:
        s.ring(bb, n, gap, ["plain"])


def cull_wet_toe(drain_pts, margin=-5):
    """Drop every pending ring farmstead that landed DOWNSLOPE of a drain collector - the wettest
    ground in the valley, and not building ground (dwellings_above_field_drain)."""
    dux, duy = math.cos(math.radians(135)), math.sin(math.radians(135))
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
            continue
        keep.append(h)
    s._pending_farmsteads[:] = keep


cull_wet_toe(_drainA)

# a caravan INN + STABLES fronting the trunk road on the quiet west approach, with open ground beside
# the stables for the wagon-train animals. NO farrier: this is a domain road, not an Imperial relay.
s.inn(170, 768, rot=-16)
s.stables(112, 686, rot=-16)

s.farmsteads()
s.farm_wells()

s.place_wells((60, 30, 2140, 1470), spacing=210, near=82)

# NEAR-RING FARMLAND. A county seat sits in the middle of its best land and the near ring is worked
# hardest - but Ubame's is genuinely THIN, and that is the county's character rather than a shortfall:
# this is charcoal-and-iron country in oak hills, where the fuel stands are the crop and the flat
# waterable ground is a narrow ribbon along the one valley stream. So the paddy takes that ribbon
# (near_ring_paddy places a basin ONLY where water actually reaches, never conjuring hydrology) and
# the dry hatake/garden quilt takes the drier western margins.
s.near_ring_paddy((1130, 260, 2110, 1465), seed=5)
s.near_ring_cropland((60, 250, 760, 1470), seed=7)
s.near_ring_cropland((700, 1140, 1300, 1480), seed=11)  # the garden band south of the town, below the warren
s.near_ring_cropland((150, 180, 1150, 560), seed=13)  # the upper dry margin north of the road

# COMMONS SCRUB on the bare outskirts only - the built-up EDGE, never the town's own floor
s.commons([(-40, 1030), (104, 1044), (96, 1180), (-40, 1168)], role="grazing")
s.commons([(-40, 460), (58, 474), (52, 600), (-40, 590)], role="grazing")
s.commons([(-40, 1330), (70, 1342), (64, 1470), (-40, 1462)], role="grazing")
s.commons([(1060, -40), (1620, -40), (1640, 165), (1080, 175)], role="grazing")
s.commons([(1900, 450), (2160, 460), (2152, 600), (1908, 590)], role="grazing")
s.commons([(1950, 650), (2160, 660), (2152, 850), (1958, 840)], role="grazing")
s.commons([(1750, 900), (2050, 910), (2042, 1050), (1758, 1040)], role="grazing")
s.commons([(1600, 0), (1850, 10), (1842, 200), (1608, 190)], role="grazing")
s.commons([(150, 300), (330, 310), (322, 580), (158, 570)], role="grazing")
s.commons([(900, 1200), (1150, 1210), (1142, 1400), (908, 1390)], role="grazing")
s.commons([(680, 1160), (900, 1169), (893, 1340), (687, 1331)], role="grazing")
s.commons([(1160, 1360), (1440, 1369), (1433, 1500), (1167, 1491)], role="grazing")
s.commons([(2040, 880), (2110, 889), (2104, 1120), (2047, 1111)], role="grazing")
s.commons([(960, 0), (1120, 9), (1113, 240), (967, 231)], role="grazing")
s.commons([(1120, 1080), (1400, 1089), (1393, 1220), (1127, 1211)], role="grazing")
s.commons([(-40, 200), (120, 214), (112, 400), (-40, 388)], role="grazing")

# the COMMUNAL WINDBREAK on the high WINDWARD (NW) margin of the FARM cluster - a nucleated cluster
# shelters behind ONE village-scale belt rather than per-farm groves, and the belt must NESTLE
# against the cluster's windward fringe (village_windbreak_embraces_cluster), not sit off in a corner
s.village_grove([(1002, 618), (1108, 662), (1092, 828), (1046, 1000), (1002, 1152), (922, 1160), (908, 1000), (922, 830), (944, 662)], role="windbreak")
# ...and the leafy scatter filling the OPEN gaps through the farm belt
s.village_grove([(1080, 1290), (1220, 1400), (1140, 1470), (1010, 1400)], role="copse", dense=False)
s.village_grove([(1620, 1000), (1730, 1015), (1715, 1120), (1605, 1105)], role="copse", dense=False)

# ===== FIRE DEFENSE: deliberately NO fire-watch tower. The hinomi-yagura belongs to a dense ENCLOSED
# wooden core; an unwalled county seat at detached village grain has field-gaps for natural breaks,
# and a real jin'ya town kept fire bells, stored water and fireproof kura instead. Same call as
# Hoshizora. WHY: settlements/towns.md "Fire towers".

# ===== THE NOTICE BOARD (kosatsuba) and THE PUNISHMENT GROUND, both AUTO-SITED. These two are
# siblings: each is placed by FOOT TRAFFIC, so each wants the engine's own verge probe rather than a
# hand-picked rect. (A hand rect was tried here first and failed exactly as the docstring warns -
# open_seat ties toward the rect's CENTER, which is the open ground behind the frontage, precisely
# where a display installation must not be.) The board deliberately does NOT default to the manor
# gate: this manor sits at the settlement EDGE by design, which is where the fewest feet pass.
# The punishment ground carries no board of its own - the crime rides on the cangue, and the
# standing law is already posted a few paces off.
_kb = None
for _krect in ((980, 640, 1330, 720), (600, 720, 980, 800), (1450, 470, 1700, 545), (240, 840, 620, 920)):
    _kb = s.open_seat(_krect, 96, 44)
    if _kb:
        break
assert _kb, "no road verge with room for the notice board and its caption"
s.kosatsuba(_kb[0], _kb[1], rot=-14)
s.place_punishment_spot()

s.title("Ubame")

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| finish:", s.finish(os.path.join(HERE, "ubame")))
