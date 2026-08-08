#!/usr/bin/env python3
"""Minami - the Fox Clan's southern provincial city, on the Hayakawa (Mode B, 1px = 3ft).

THE FOX SEAT. Minami province is the southernmost of the four Fox provinces, administered by the
NANKE lineage (l7r.md "Fox Lineages and Provinces"). The Fox are one small domain - 150,000 humans
over four provinces - so this seat is deliberately UNDER the tier average: 2,600 residents against
Tango's and Nagahara's 3,000.

EIGHT TEMPLE PRECINCTS, NOT TWO. This is the map's reason for existing. In Fox lands the question
is "which TEMPLES do X", not which merchant families: the Seven Temples hold usufruct over sections
of the Kitsune Mori, moneylending sits with Fukurokujin and Ebisu, wedding loans with Benten. So
Minami carries seven modest precincts for the seven Fortunes of Good Luck plus a slightly larger
Inari - eight compounds, every one SMALLER than the single great complex an ordinary clan's city
builds. They are scattered by TRADE rather than gathered into a rim-belt teramachi, because each is
an economic house sited where its business is. Only the THREE BONDS take a vow of celibacy, so the
rest of each precinct's clergy are hereditary householders living OUT among the laity - every
compound is ringed by its own temple families (kind "monk_house", drawn identical to laborer
houses), 48 citywide against Nagahara's 5. And eight precincts do NOT get eight graveyards: these
are economic institutions holding forest usufruct, not eight parishes, so three of them keep the
city's shared burial grounds and the other five declare graveyard=False. See
research/religion-and-death.md; the exception is declared via meta(temple_exception="fox_structure").

THE RIVER RUNS DOWN THE WEST FLANK - the mirror of Nagahara, which sits on the Hayakawa's west bank
downstream in Crab lands. Same river, same name end to end (settlements/water.md's one-name rule),
flowing north -> south out of the Kitsune Mori toward the Crab. The moat covers the three landward
faces and taps the river above and below; the cargo canal shares the moat's downstream mouth.

NO IMPERIAL ROAD. The Imperial road through Minami - the waystation-less stretch the Fox keep
warded - passes miles to the east, so the road net simply leaves the map in two directions and
nothing is labeled Imperial.

TIMBER DOWNRIVER, CHARCOAL BY CART. Fox wealth is the forest: lumber goes down the Hayakawa in
rafts, while charcoal and Kitsune-Koh incense - light and high-value - go overland. So the working
ground inside the wall is log stacking and charcoal godowns (a declared budget line, not ambient
slack), the zaimokuya's yard sits on the bank outside the river gate, and the kilns are outside
the walls entirely where fire law puts them.

PEACEFUL WALL. A minor clan shielded by the wood and the Three Man Alliance, not by fortification:
meta(wall_defense="peaceful") - the sparser Xi'an crossfire spacing, the first map in the pool to
exercise that tier.

Quarters: NE = laborer terraces; SE = the governor's ward (yamen + six ministries + samurai);
SW = burakumin downstream, with the timber and charcoal ground; NW = merchants around the dock.
"""

import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import settlement  # noqa: E402
from citybudget import BudgetLine, CityProgram, budget_to_manifest, plan_city  # noqa: E402
from settlement import Settlement, moat_swept_tap  # noqa: E402
from waterfields import AZE, BEAN_GREEN, aze_w, build_comb, hem_on_paddy, paddy_grain  # noqa: E402

PLOT_ACROSS, ROW_STEP = paddy_grain(3)

s = Settlement(3200, 2700, seed=61)

# THE POPULATION ARITHMETIC, which is not an ordinary city's (feature 016). CityProgram.population
# is the LAY population - the castes in the budgets.md table. Minami's clergy are numerous enough
# that they can no longer hide inside the population tolerance the way Nagahara's five adept-monk
# households do: 8 precincts x 6 hereditary temple families = 48 real households, 240 residents. So
# the lay figure is set 240 BELOW the declared total and the two add back up:
#     472 lay families + 48 temple families = 520 dwellings x 5 = 2,600 residents
# The declared figure is the SPEC's (FR-010), and the wall is sized to it rather than the population
# being trimmed to whatever the first layout happened to hold. An earlier pass did the latter -
# dropped the lay figure to 2,000 and pinned the old ring - which is exactly the failure mode of
# quietly building the city wrong; the shortfall it found was real, but the fix belongs in the space
# budget and therefore in the WALL (the skill's own doctrine: if the capacity report wants a resize,
# fix the budget model, not the map).
HOUSEHOLD_RESIDENTS = 5  # check_village.HOUSEHOLD - one dwelling houses a household of five
LAY_POP = 2360
TEMPLE_PRECINCTS = 8
MONK_PER_PRECINCT = 6
MONK_HOUSES = TEMPLE_PRECINCTS * MONK_PER_PRECINCT
POP = LAY_POP + MONK_HOUSES * 5

s.meta(
    water_flow=90,  # DRAINAGE BEARING: the Hayakawa runs N -> S out of the Kitsune Mori (0=E, 90=S)
    name="Minami",
    scale="city",
    walled=True,
    population=POP,
    ftpx=3,
    wall_defense="peaceful",  # a minor clan behind the wood, not behind its rampart - the sparse tier
    imperial_road=False,
    river_port=True,
    clan="Fox",
    capital_dir="northeast",
    temple_fortunes=["Benten", "Bishamon", "Daikoku", "Ebisu", "Fukurokujin", "Hotei", "Inari", "Jurojin"],
    temple_exception="fox_structure",
    # THE FOX TRADE, declared rather than tolerated (GM 2026-08-05). Minami's merchant households
    # run ~30% under the budgets.md share, and that is doctrine, not drift: the eight precincts hold
    # much of the commerce that merchant houses conduct in other clans' cities, and the households
    # that would have been merchants are the 48 hereditary temple families instead. The city's
    # POPULATION is unchanged - 472 lay families + 48 temple families = 520 dwellings = 2,600
    # residents - which is what makes the trade legitimate rather than a shortfall.
    caste_shifts={
        "merchant": (
            "Fox temples hold much of the commerce that merchant houses conduct in other clans' cities - the eight "
            "precincts lend, warehouse and broker the timber trade - so merchant households run about a third under "
            "the budgets.md share and the 48 hereditary temple families stand in their place. The city's population "
            "is unchanged at 2,600; only the caste that houses it moves."
        )
    },
)

BUDGET = plan_city(
    CityProgram(
        population=LAY_POP,
        river=True,
        temple_precincts=TEMPLE_PRECINCTS,
        # THE DRAWN PRECINCT, not just its hall compound. 3,400 px^2 priced the walled compound alone
        # (~0.70 acre) and left out everything else a precinct actually plants in the fabric, which is
        # what a wall has to enclose. Measured off this map, per precinct: hall compound block ~5,125,
        # torii approach and its stand-clear ~1,720, the caption band ~4,000 (a caption box is ~150px
        # wide and its band must clear the widest row kind's overhang on both sides - reserved in BOTH
        # registries, since rowpack honors block_polys and the _fits placers honor corridors),
        # wayside shrines ~1,790. The halls have NOT grown - only the accounting has.
        temple_precinct_px2=11_600.0,
        # NO fragmentation premium. An earlier pass measured the 431x400 ring predicting 504 in-wall
        # dwellings against 449 drawn - ~12% short - and was about to price that gap as an extras
        # line. It is gone because the shortfall was never the wall: it was top_up holding 3px off
        # every neighbor (so every fill was detached by construction) and two hand-rolled caption
        # reservations double-booking ~1,450 interior grid points. With those fixed the map packs
        # slightly BETTER than the budget predicts, so a premium here would oversize the ring.
        monk_houses_per_precinct=float(MONK_PER_PRECINCT),
        extras=(
            BudgetLine(
                "Inari precinct uplift", 1, 1_600.0, "the Inari precinct stands ~1.0 acre against its siblings' ~0.70 - the largest of the eight, still under an ordinary city's single complex"
            ),
            BudgetLine(
                "timber + charcoal working ground",
                1,
                18_100.0,
                "log stacking, sawpits and charcoal godowns inside the wall (the drawn yard is r=76px) - the storage end of the Fox forest trade; the kilns are outside by fire law",
            ),
            BudgetLine(
                "gate marshalling grounds",
                2,
                9_000.0,
                "beaten-earth hitching and wagon-train ground inside each main gate (drawn, r=38px each) - a seat on a clan road with no waystations for a day's travel either side stables the traffic itself",
            ),
            BudgetLine(
                "laneway excess over the flat circulation allowance",
                1,
                34_000.0,
                "citybudget allows a flat 7% of interior for circulation and Minami draws far more, because eight precincts sited by TRADE across the commoner quarters all have to be reached: the ring, street and roji BEDS measure 56,936 px^2 against the 43,675 allowed, and the trunk road's in-wall run adds ~21,000 more. Charged in full now, at ~34,000: the conservative 13,000 (beds only) left the map unable to seat its declared 520 dwellings AS TERRACES - a measurement of the free ground at that ring found only 23,808 px^2 of it in contiguous runs, nearly all inside the gated samurai ward where commoners do not belong. This is real ground under real lanes, unlike a caption band, which is why it belongs in the space budget and the wall follows it",
            ),
        ),
        # A CIRCULAR PLAN, and the river is why. The west flank is bounded by the Hayakawa and the
        # wharf suburb on its bank, which must stay OUTSIDE the rampart - at aspect 0.93 the west wall
        # had closed to 3px of the quay, so the city could not grow westward at all. Raising the aspect
        # spends the same interior on a rounder ring: rx falls 471 -> 462 (the wall steps BACK off the
        # bank, giving the wharf 30px) while ry rises 438 -> 462 into open country north and south.
        # A river city grows along its valley, not into its own landing.
        aspect=1.00,
        nring=20,
    ),
    canvas=(3200, 2700),
)
s.meta(budget=budget_to_manifest(BUDGET))

# THE WALL COMES FROM THE BUDGET (FR-011), never hand-picked and never pinned to a previous run's
# value. Everything laid out below - the quarter wedges, the ring road, the moat, the gates - is
# derived from RX/RY, so re-deriving the ring moves them together.
CX, CY = 1400, 1330
RX, RY = round(BUDGET.wall.rx), round(BUDGET.wall.ry)
NRING = 20
WALL = [(round(CX + RX * math.cos(-math.pi / 2 + 2 * math.pi * i / NRING)), round(CY + RY * math.sin(-math.pi / 2 + 2 * math.pi * i / NRING))) for i in range(NRING)]
NGATE, WGATE, WGATE_PT = WALL[0], WALL[15], WALL[13]

# The samurai/government ward's fence, hoisted so its ground is reserved before any pack runs. Both
# ENDS abut solid rampart - on the wall's east face between vertices 4-5, and on its south face
# between 9-10 - so the wall closes the other two sides and there is no walk-around gap. Four kido:
# two where the commoner streets pierce it, two where the ring road crosses its ends.
# These were laid out against the 431x400 ring the first budget derived. They are RING-RELATIVE
# features - the fence's two ends have to keep abutting solid rampart, the kido have to keep
# meeting the streets that pierce it - so they scale with the ring rather than being re-typed every
# time the budget re-derives it. Sizes never scale, only positions: the city spreads, it does not
# inflate (feedback: no size inflation in to-scale diagrams).
_SX, _SY = RX / 431.0, RY / 400.0


def _ring_rel(x, y):
    return (round(CX + (x - CX) * _SX), round(CY + (y - CY) * _SY))


# Design coordinates re-solved against the re-derived ring: both ends must PENETRATE solid rampart
# (they land 6px and 3px past it), and the north segment had to come ~6px south of its old line so
# it clears Bishamon's torii avenue by 14px - a fence is a continuous barrier and an arch is a
# freestanding gateway, so an arch may never stand in one.
CROSS_H = [(1120, 1150), (1670, 1150)]  # the northern E-W street, crossing the spine
MER_V = [(1200, 1090), (1200, 1330)]  # NW N-S, foot on the road
LAB_V = [(1600, 1078), (1600, 1150)]  # NE N-S, foot on the road
MAIN_E = [(1110, 1450), (1700, 1450)]  # the southern E-W street, piercing the ward fence at a kido
SW_V = [(1200, 1330), (1200, 1570)]  # SW N-S, head on the road
EAST_ST = [(1400, 1330), (1720, 1330)]  # the ward approach, piercing the fence at a kido
WARD_V = [(1650, 1330), (1650, 1450)]  # inside the ward, EAST_ST down to MAIN_E

WARD_FENCE = [_ring_rel(1829, 1293), _ring_rel(1420, 1312), _ring_rel(1420, 1666), _ring_rel(1460, 1725)]


def _fence_x_way(way):
    """Where a way CROSSES the ward fence, or None.

    A KIDO IS CENTERED ON THE ROAD IT BARS (GM 2026-07-26) - a gate that is merely near its street is
    a gate people walk around. Scaled guesses drift: when the ring was re-derived the fence's y scale
    went to 1.155 while MAIN_E stayed at y1450, which put one kido 19px off the street it was supposed
    to bar and dropped city_samurai_quarter_gated to a single gate. Solving the intersection cannot
    drift, however the ring moves."""
    for (ax, ay), (bx, by) in zip(WARD_FENCE, WARD_FENCE[1:]):
        for (cx_, cy_), (dx_, dy_) in zip(way, way[1:]):
            den = (bx - ax) * (dy_ - cy_) - (by - ay) * (dx_ - cx_)
            if abs(den) < 1e-9:
                continue
            t = ((cx_ - ax) * (dy_ - cy_) - (cy_ - ay) * (dx_ - cx_)) / den
            u = ((cx_ - ax) * (by - ay) - (cy_ - ay) * (bx - ax)) / den
            if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                return (round(ax + t * (bx - ax)), round(ay + t * (by - ay)))
    return None


# two kido on the commoner streets that pierce the fence, SOLVED onto each crossing, plus one at each
# fence end where the ring road crosses it (those ride the fence itself, so they scale with it)
KIDO_SPOTS = [p for p in (_fence_x_way(EAST_ST), _fence_x_way(MAIN_E), _ring_rel(1798, 1294), _ring_rel(1443, 1700)) if p]

s.city_wall(WALL, gates=[NGATE, WGATE], guard_east=[NGATE], water_gates=[WGATE_PT], ring_inset=22)

# ---- the Hayakawa: north -> south down the WEST flank. Points run UPSTREAM-FIRST (source before
# mouth) - both the junction tilts and the checks key on that order.
RIVER = [(806, 520), (812, 855), (818, 1190), (826, 1525), (836, 1860), (848, 2170)]
RIVER_W = s.river(RIVER)
MOAT = s.moat(WALL, gap=24, river=RIVER, river_cut=130)
RING = s.ring_road(WALL, inset=22)
s.bound = [list(p) for p in RING]

# ORDERING: the kido reservations run AFTER the ring road, because kido_reservation asks the engine
# for the seat s.ward will take and that angle follows the lane the gate bars.
for kx, ky in KIDO_SPOTS:
    s.block_polys.append(s.kido_reservation(kx, ky, WARD_FENCE))


def _qpt(i, n=48, inset=24):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return (CX + (RX - inset) * math.cos(a), CY + (RY - inset) * math.sin(a))


def _qwedge(i0, i1, n=48):
    return [(CX, CY)] + [_qpt(i, n) for i in range(i0, i1 + 1)]


s.quarter(_qwedge(0, 12), "residential")  # NE laborer terraces
s.quarter(_qwedge(12, 24), "mixed")  # SE governor's ward + samurai
s.quarter(_qwedge(24, 36), "mixed")  # SW burakumin + the timber/charcoal ground
s.quarter(_qwedge(36, 48), "mixed")  # NW merchants + the dock

s.corridors.append((WARD_FENCE, 14))


def label_ground(x, y, halfw=54, halfh=13):
    """Reserve a caption's ground BEFORE the packs run - labels are drawn LAST, so a district or
    trade-works caption that nobody reserved comes to rest on a roof (labels_clear_of_other_buildings)."""
    s.block_polys.append([(x - halfw, y - halfh), (x + halfw, y - halfh), (x + halfw, y + halfh), (x - halfw, y + halfh)])


for _lx, _ly2, _hw in ((1560, 1216, 64), (1150, 1348, 56), (1214, 1470, 42), (1668, 1314, 60), (1362, 1136, 32), (1398, 1359, 30), (1058, 1563, 34), (1256, 1669, 86)):
    label_ground(_lx, _ly2, _hw)

_LBL_DONE = 0


def reserve_caption_ground(pad=14):
    """Reserve, as a CORRIDOR, the ground under every caption emitted since the last call.

    A block poly is not enough on its own. The urban packs center-test block_polys (_fits ->
    _in_blocked looks at the candidate's CENTER only, see the skill CLAUDE.md DRAW ORDER note), so a
    wide roof whose center clears the band still comes to rest with half of itself under the text -
    which is exactly what labels_clear_of_other_buildings kept firing on. A corridor is
    distance-tested, so it keeps whole FOOTPRINTS off. Call it at each point where a phase has
    finished drawing captioned features and before the next phase packs houses around them; the
    cursor makes it idempotent."""
    global _LBL_DONE
    for _L in s.M["labels"][_LBL_DONE:]:
        _x0, _y0, _x1, _y1 = _L[0], _L[1], _L[2], _L[3]
        _mid = (_y0 + _y1) / 2
        s.corridors.append(([(_x0 - 4, _mid), (_x1 + 4, _mid)], (_y1 - _y0) + pad))
    _LBL_DONE = len(s.M["labels"])


# ---- THE through-road: down from the north gate, along the spine to the central crossroads, then
# WEST out through the river gate and over the Hayakawa bridge - one route, both ends off-map.
ROAD = [(1352, 500), (1372, 690), (1390, 840), (1400, 930), (1400, 1330), (1000, 1330), (930, 1330), (860, 1332), (700, 1338), (480, 1348), (240, 1358)]
s.road(ROAD)

s.drum_tower(1366, 1386)  # the bell-and-drum tower at the SW corner of the central crossroads

# ---- TRADE WORKS, placed early so every later pack flows around them.
s.brewery(1466, 1198)
s.dye_yard(1058, 1546)  # on the in-wall cargo canal, north of the dock basin
s.lumber_yard(
    872, 1445, label_xy=(886, 1466)
)  # the zaimokuya on the dry strip below the wharf, clear of the water but hard against its bank frontage - ~40 ft of haul ground between the yard's west edge and the log boom's mooring line, so pen and yard read as ONE works (settlement-review 2026-08-02: at 130 ft of untouched bank they read as two unrelated features). Caption hand-seated east so its box clears the pen's bank edge (it grazed by under a pixel from the default seat)
# THE LOG BOOM, a shore-fast holding pen off the yard (research/urban-features.md "The log boom").
# Fox timber comes DOWN the Hayakawa in rafts and has to be held until it is pulled out; the pen is
# the yard's waterside holding ground, anchored to the EAST bank at both ends with the raft-mats
# packed between chain and shore. It hugs the yard's own bank and takes a third of the 120 ft
# channel, leaving the fairway clear for the wharf traffic upstream - booms were barred from
# obstructing navigation, and the full-span catch boom belongs at the Fox gorge mouth upstream
# (off-map lore), never at the port. Bank on the pen's local +y side: rot 268.6 turns +y east,
# matching the bank's own lean (the centerline runs at 88.6 here). Caption on the yard side, on
# the dry strip between bank and zaimokuya. Pen head held ~15 px (45 ft) below the last wharf
# jetty (deck edge y~1391) so the jetty keeps a working berth and does not read as bolted to the
# boom (settlement-review 2026-08-02).
s.log_boom(837.7, 1458, rot=268.6, length=100, label_xy=(868, 1515))
s.oil_press(
    1622, 1268
)  # +16 east of the obvious seat: its auto-caption otherwise runs into the Temple of Bishamon's (they cleared by 0.7 px, under no_label_overlaps' 2 px estimation slack, and read as touching)
s.pawnshop(1290, 1300)  # NW merchant quarter, by the lending temples
s.bathhouses([(1416, 1180), (1250, 1424)])
s.kiln(
    640, 1180, rot=270
)  # the KILN WORKS OUTSIDE the walls on the far bank - siting confirmed sound by settlement-review 2026-07-27 (a quarter mile clear of every funerary feature, and on the far side of the trunk road from the execution ground), so only the climb bearing changed. rot=270 lays it due NORTH, uphill against meta water_flow=90
s.tanning_yard(
    866, 1840, rot=90, pits=12, water="stream"
)  # DOWNSTREAM of the moat outfall on the east bank: the re-derived ring pushed the moat to y1816, and a tanning yard's tamped ground must stay dry (pits below the waterline are just more stream)

# ---- the cargo canal: the moat's downstream corner -> water gate -> dock basin. ONE mouth on the
# river: the canal communicates with the MOAT and the moat's own outfall junction is the single
# navigation entrance (the Suzhou pattern).
CANAL = [MOAT[-2], _ring_rel(1051, 1565), _ring_rel(1128, 1572)]
s.canal(CANAL)
s.corridors.append((CANAL, 30))
s.block_polys.append(
    [
        (min(p[0] for p in CANAL) - 14, min(p[1] for p in CANAL) - 14),
        (max(p[0] for p in CANAL) + 14, min(p[1] for p in CANAL) - 14),
        (max(p[0] for p in CANAL) + 14, max(p[1] for p in CANAL) + 14),
        (min(p[0] for p in CANAL) - 14, max(p[1] for p in CANAL) + 14),
    ]
)
s.water_gate(*_ring_rel(1051, 1565), rot=152)
s.dock(*_ring_rel(1152, 1574), 54, 34)
s.label(1130, 1584, "cargo basin", 9, italic=True, color="#5A7A8C")  # else it reads as an ornamental pond; above the basin is monk_house ground
# The ring road bridges the canal just inside the wall - SOLVED by s.bridges() at the end of the
# gen, not hand-placed here. The deck used to be written out at design coordinates and went 17px
# and 39 deg adrift when the ring was re-derived, so the road ran through the water beside it
# (GM 2026-07-27; bridges_align_with_their_way).

# ---- civic amenities placed FIRST so the dense packs flow around them.
s.flophouse(1330, 806, label_below=True)  # outside the NORTH gate
s.flophouse(900, 1268)  # outside the WEST river gate, on the wharf
s.block_polys.append([(1424, 962), (1500, 962), (1500, 1080), (1424, 1080)])
s.corridors.append(([(1450, 970), (1450, 1080)], 40))
s.flophouse(1450, 972)
s.inn(1422, 1052)
s.stables(1450, 1016, rot=90)
s.farrier(1508, 1010, rot=90)
s.animal_ground(1462, 1042, r=38)
s.block_polys.append([(1004, 1176), (1136, 1176), (1136, 1320), (1004, 1320)])
s.corridors.append(([(1040, 1200), (1040, 1300)], 46))
s.flophouse(1040, 1176, label_below=True)
s.inn(1032, 1280)
s.stables(1082, 1292, rot=90)
# the river-gate stables' TIE-UP GROUND on its open (east) side. city_gate_caravan_facilities allows
# at most four dwellings within 75px of a gate stables - dozens of draft animals need somewhere to
# stand - and the merchant rows had been packing to exactly that limit, so the 2026-07-27 torii reflow
# tipped it to five without anything moving toward the stables. The north gate has s.animal_ground for
# the same job; that call CLAIMS ground for the empty-space detector but reserves none, so the pocket
# has to be blocked here, before the packs run.
s.block_polys.append([(1136, 1248), (1174, 1248), (1174, 1332), (1136, 1332)])


def grid(streets, width_ft=18):
    for st in streets:
        s.street(st, width=s.lw(width_ft))


def front(streets, kinds, width_ft=18, spacing=19, rows=2):
    for st in streets:
        s.frontage(st, list(kinds), width=s.lw(width_ft), spacing=spacing, rows=rows, rowgap=2, jitter=1, setback=s.px(14))


def alleys(lst):
    for a in lst:
        s.alley(a)


# ====================================================================== the street skeleton
# Every free end lands ON the ring bed (a clean T) rather than a sliver short of it, and every
# street meets another - one connected network wired to the through-road.
grid([CROSS_H, MAIN_E], width_ft=22)
CROSS_FRONT = True
grid([MER_V, LAB_V, SW_V, EAST_ST, WARD_V])


# block-interior roji, laid with the streets so every quarter's terraces flow around them
# The skeleton above was laid out against the 431x400 ring. The re-derived 456x424 ring adds an
# outer band the old lanes never reach, and 90 dwellings ended up further than 95px from any street
# OR alley - a warren with no way in or out (no_isolated_dwelling_cluster). These five roji lace
# that band: the southern terraces below the burakumin strips, the ward's south-east flank, the
# north gate approach, and the river-gate quarter.
def _ring_y(x, south=True):
    """The y where a vertical roji meets the ring road BED, read from the drawn ring polygon.

    Not an ellipse estimate: the ring is a 20-gon whose chords sit inside the ellipse, so an
    ellipse figure lands 3-4px past the bed and city_streets_meet_through_lanes reads that as a
    lane poking past its junction. Reading the polygon also means a re-derived wall moves every
    roji end with it instead of leaving five hand-typed numbers to re-solve."""
    _R = s.M["ring_road"]
    _R = _R["pts"] if isinstance(_R, dict) else _R
    _ys = []
    for _i in range(len(_R)):
        (_x0, _y0), (_x1, _y1) = _R[_i], _R[(_i + 1) % len(_R)]
        if (_x0 - x) * (_x1 - x) <= 0 and _x0 != _x1:
            _ys.append(_y0 + (_y1 - _y0) * (x - _x0) / (_x1 - _x0))
    return round(max(_ys) if south else min(_ys))


ALLEYS = [
    [(1120, 1124), (1120, 1330)],
    [(1490, 1014), (1490, 1150)],
    [(1640, 1150), (1640, 1230)],
    [(1300, 1330), (1300, 1606)],
    [(1372, 1596), (1372, _ring_y(1372))],
    [(1544, 1592), (1544, _ring_y(1544))],
    [(1756, 1470), (1756, _ring_y(1756))],
    [(1300, _ring_y(1300, south=False)), (1300, 1018)],
    [(1002, 1330), (1002, 1436)],
]
alleys(ALLEYS)
for _al in ALLEYS:
    s.corridors.append((_al, 8))
    (_ax0, _ay0), (_ax1, _ay1) = _al[0], _al[-1]
    _apad = 20 if _ax0 in (1544, 1756) else 8
    s.block_polys.append(
        [(min(_ax0, _ax1) - _apad, min(_ay0, _ay1) - 8), (max(_ax0, _ax1) + _apad, min(_ay0, _ay1) - 8), (max(_ax0, _ax1) + _apad, max(_ay0, _ay1) + 8), (min(_ax0, _ax1) - _apad, max(_ay0, _ay1) + 8)]
    )

for _wbox in (
    (1230, 1580, 1330, 1650),
    (1290, 1650, 1390, 1710),
    (1400, 1030, 1500, 1090),
    (1520, 1200, 1630, 1280),
    (1596, 1010, 1690, 1070),
    (1030, 1420, 1130, 1480),
    (1090, 1480, 1190, 1545),
    (1500, 950, 1600, 1010),
    (1310, 950, 1410, 1010),
    (1090, 1396, 1180, 1452),
    (958, 1412, 1030, 1500),
    (1010, 1500, 1100, 1560),
    (1290, 1630, 1400, 1720),
    (1600, 1080, 1710, 1180),
    (1360, 1700, 1460, 1780),
    (1556, 1140, 1648, 1206),
    # the SW warren south of Benten: the 2026-07-27 civic-apron widening pushed households
    # onto the one well at (1277, 1563) and took it to 27, one past city_well_density_sufficient's
    # 26. Two more probes here share the load - the engine picks whichever pocket actually fits.
    (1180, 1516, 1268, 1578),
    (1330, 1540, 1424, 1604),
):
    _ws = s.open_seat(_wbox, 18, 18, well=True)
    if _ws:
        s.well(*_ws)

# ====================================================================== THE EIGHT PRECINCTS
TW, TH = s.px(96), s.px(66)  # the seven siblings, ~0.70 acre drawn
IW, IH = s.px(118), s.px(80)  # Inari, the largest of the eight


def precinct(x, y, fortune, torii, w=TW, h=TH, primary=False, graveyard=False, label_below=True, torii_count=1):
    s.shrine_hall(x, y, f"Temple of {fortune}", w=w, h=h, kind="temple", primary=primary, graveyard=graveyard, label_below=label_below, torii=torii, torii_count=torii_count)
    _cap = s.M["labels"][-1]
    _cx0, _cy0, _cx1, _cy1 = _cap[0], _cap[1], _cap[2], _cap[3]
    _cmid = (_cy0 + _cy1) / 2
    s.block_polys.append([(_cx0 - 12, _cmid - 16), (_cx1 + 12, _cmid - 16), (_cx1 + 12, _cmid + 16), (_cx0 - 12, _cmid + 16)])
    s.corridors.append(([(_cx0 - 4, _cmid), (_cx1 + 4, _cmid)], (_cy1 - _cy0) + 12))
    # the caption's own ground, reserved BOTH ways: a block poly (which the packs center-test) and
    # a corridor (which the fills honor). "Temple of Fukurokujin" is a wide box, so the band is
    # generous - labels_clear_of_other_buildings does not forgive a roof under the text.


# --- NW: the LENDING temples, by the dock and the merchant district. Ebisu (honest commerce, the
# wharf's fortune) and Fukurokujin share the moneylending trade in Fox lands, so they sit together -
# the city's one genuine temple cluster, which is why the wayside shrines gather here.
precinct(1160, 1210, "Ebisu", [(1160, 1252)], primary=True, graveyard=True)
precinct(1310, 1206, "Fukurokujin", [(1310, 1248)], label_below=False)
for sx, sy in [(1240, 1258), (1258, 1288), (1224, 1290)]:
    s.small_shrine(sx, sy)

# --- W: BENTEN by the dock - the water fortune, and the temple that lends against a wedding
precinct(1082, 1512, "Benten", [(1082, 1548)], label_below=False)

# --- N-CENTRAL: INARI, the largest of the eight. The Fox clan's own fortune - rice and foxes - and
# the temple that keeps the Inari paddy reserve whose harvest Inari shrines buy Empire-wide.
precinct(1300, 1046, "Inari", [(1300, 1074), (1300, 1081), (1300, 1088), (1300, 1095), (1300, 1102), (1300, 1109), (1300, 1116)], w=IW, h=IH, graveyard=True, torii_count=7, label_below=False)

# --- NE: the laborer quarter's pair
precinct(1512, 1074, "Hotei", [(1512, 1116)], label_below=False)
precinct(1682, 1090, "Jurojin", [(1682, 1132)], label_below=False)
for sx, sy in [(1556, 1064), (1572, 1098), (1538, 1108)]:
    s.small_shrine(sx, sy)

# --- SE: BISHAMON on the LABORER side of the ward fence - the warrior fortune, but a Fox precinct is
# sited by its trade and Bishamon's is the armorers' and porters' custom, not the bushi's own chapel
# (the ward fence runs y~1304 at this x; the precinct stands ~144 ft north of it, deliberately)
precinct(1520, 1256, "Bishamon", [(1520, 1292)])

# --- SW: DAIKOKU by the timber and charcoal ground - the fortune of wealth and stores
precinct(1268, 1490, "Daikoku", [(1268, 1532)], graveyard=True)

# ---- THE SHARED BURIAL GROUNDS. Eight precincts do NOT get eight graveyards (the five above
# declare graveyard=False): they are economic institutions holding forest usufruct, not eight
# parishes, and burial ground is constrained by suitable LAND rather than by foundation count.
s.cemetery(1232, 1042, 46, 32, label="graveyard")  # Inari's
s.cemetery(1046, 1246, 42, 30, label="graveyard", label_above=True)  # Ebisu's
s.cemetery(
    1358, 1540, 42, 30, label="graveyard", label_above=True, label_xy=(1358, 1544)
)  # Daikoku's; caption ON its own plot - the third merchant strip (y1462-1506) took the ground the old above-the-plot seat needed, and every off-plot seat here lands on the packed mixed rows (a label may cover the thing it names; martial-hall precedent)
# along its own plot - centered it cleared the Temple of Daikoku caption by 2.0 px, which passes the AABB
# check and still reads as touching, because an italic's ink leans outside the box the check measures.
# Below-seat is not the answer here: the ground under this plot is solid burakumin/laborer terrace.

# ---- TEMPLE FAMILY HOUSING: 6 households per precinct, drawn identical to laborer houses. Each
# pocket is RESERVED first so the later terrace strips flow around it - competing for ground after
# the rows were laid seated only 29 of the 48 the Fox clergy program calls for.
TEMPLE_FAMILY_SEATS = [(1104, 1176), (1366, 1170), (1064, 1428), (1372, 1090), (1470, 1132), (1728, 1156), (1560, 1170), (1200, 1548)]
for _tx, _ty in TEMPLE_FAMILY_SEATS:
    s.pack((_tx - 60, _ty - 36, _tx + 60, _ty + 46), ["monk_house"] * MONK_PER_PRECINCT, step=13)  # bbox widened 2026-08-08:
    # the RNG-scope re-roll left the Ebisu precinct with a single monk house inside the old 96x68 box, and a
    # temple complex keeps 2-3 of them (city_temples_have_monk_housing). Still a precinct-sized pocket.

# ====================================================================== SE: the governor's ward
s.governor_mansion(1570, 1545, s.px(525), s.px(300), "Governor's Mansion", gate_dir="north")
# (an undocumented 216x38 block band used to sit here, spanning the mansion's width +20px and
# stopping 5px short of the north wall - the reservation for the caption the manor default hung
# ABOVE the walls. governor_mansion() seats that caption inside the court now, so the band was
# holding 1.7 acres of gate frontage blank for text that is no longer there: the settlement-review
# found 8 structures in that band against Nagahara's 17, with this street's own frontage record
# showing 30 samurai houses asked for and 5 seated. Removed 2026-08-08; the indexed civic apron
# below already covers the yamen's real standoff.)
MINS = ["Ministry of Revenue", "Ministry of Retainers", "Ministry of War", "Ministry of Works", "Ministry of Justice", "Ministry of Rites"]
MIN_POS = [(1490, 1358), (1600, 1358), (1710, 1358), (1524, 1414), (1694, 1414), (1175, 1096)]
for (mx, my), name in zip(MIN_POS, MINS, strict=True):
    s.ministry(mx, my, name, w=s.px(114), h=s.px(78))
s.mausoleum(1500, 1630, 44, 32, label="Mausoleum", gate_dir="north", label_below=True)
_CIV_I0 = len(s.block_polys)
for _m in s.M["ministries"] + [s.M["governor_mansion"]]:
    # 30px of apron, not 22. block_polys is CENTRE-tested (CLAUDE.md, "CENTRE vs FOOTPRINT"), so an
    # apron sized to the 14px office standoff alone lets a dwelling park half its width inside it: the
    # Ministry of Works ended up 13.4px from a samurai_large whose CENTRE was 5px outside the old band.
    # 30 = the 14px standoff + half the widest dwelling that packs here (~27px samurai_large).
    s.block_polys.append(
        [
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] - _m["h"] / 2 - 30),
            (_m["x"] + _m["w"] / 2 + 30, _m["y"] + _m["h"] / 2 + 30),
            (_m["x"] - _m["w"] / 2 - 30, _m["y"] + _m["h"] / 2 + 30),
        ]
    )
_CIV_I1 = len(s.block_polys)
for _m in s.M["mausoleums"]:
    s.block_polys.append(
        [
            (_m["x"] - _m["w"] / 2 - 16, _m["y"] - _m["h"] / 2 - 16),
            (_m["x"] + _m["w"] / 2 + 16, _m["y"] - _m["h"] / 2 - 16),
            (_m["x"] + _m["w"] / 2 + 16, _m["y"] + _m["h"] / 2 + 16),
            (_m["x"] - _m["w"] / 2 - 16, _m["y"] + _m["h"] / 2 + 16),
        ]
    )
s.block_polys.append([(1724, 1384), (1762, 1384), (1762, 1430), (1724, 1430)])
s.martial_hall(1700, 1500, label_xy=(1700, 1503))
s.dojos([(1452, 1394), (1786, 1444)])  # first seat nudged NORTH off the ward kido at (1421,1450): its caption ran across the gate's guard post.
# North, not east: an eastward nudge reflowed the SE burakumin rows and pushed the (1385,1617) wellhead to 27 households, one over the ceiling.
reserve_caption_ground()
front([MAIN_E], (["samurai_large"] + ["samurai"] * 2) * 10, spacing=19, rows=2)
for _y0, _x1 in ((1322, 1824), (1596, 1760), (1650, 1734)):
    s.rowpack((1462, _y0, _x1, _y0 + 40), ["samurai"] * 30, court_every=4, eave_ft=2)
# THE YAMEN'S DOMESTIC STAFF, in terraces rather than scatter. city_capacity read the SE at
# 0.48 dwellings/1000px^2 against the SW's 1.66 - the emptiest quarter in the city - and budgets.md
# puts servants among the households they serve, not in a quarter of their own: the yamen's
# runners, grooms and clerks and the samurai households' domestics live inside the ward. These go
# in as ROWPACKS on purpose. A top_up fill demands 3px of clearance from every neighbor, so every
# dwelling it seats is detached by construction and drags city_row_housing_touches DOWN; a rowpack
# lays contiguous terraces. Density added here therefore has to come from rows, not from scraps.
# The three strips are the ground the mansion, its forecourt block and the ministry aprons leave:
# the ward's west flank, its east flank below the martial hall, and the NE pocket.
s.block_polys.append([(1454, 1484), (1492, 1484), (1492, 1606), (1454, 1606)])
s.rowpack((1440, 1470, 1494, 1608), ["samurai"] * 16, court_every=4, eave_ft=2)  # west flank, between the ward fence and the yamen wall
s.rowpack(
    (1664, 1528, 1714, 1642), ["samurai"] * 40, court_every=5, eave_ft=2
)  # east flank, below the martial hall and inside the ring. SAMURAI, not the old servant/laborer terrace: the ward houses its domestics as each household's own nagaya RANGE (s.servant_ranges, below), so a servant terrace here is exactly the commoner-reading fabric the fence exists to exclude (GM 2026-08-02; city_ward_servants_housed_as_ranges)
s.rowpack((1682, 1446, 1784, 1502), ["samurai"] * 14, court_every=4, eave_ft=2)  # the NE pocket by the ministries - retainers, not domestics (y0 clear of the Ministry of Justice apron)
s.pack((1452, 1312, 1836, 1716), (["samurai"] * 3 + ["samurai_large"]) * 120, step=11, face_streets="fill")
s.label(1668, 1314, "samurai neighborhood", 10, italic=True, color="#3A352C")
s.ward("samurai", WARD_FENCE, gates=KIDO_SPOTS)

# ====================================================================== NE: the laborer quarter
s.block_polys.append([(1644, 1190), (1744, 1190), (1744, 1276), (1644, 1276)])
s.corridors.append(([(1660, 1232), (1730, 1232)], 40))
s.theater_stage(1694, 1232, w=s.px(210), h=s.px(146), rot=180, label="theater stage")
s.fire_tower(1596, 1030, label=None)
front([LAB_V], (["shop"] + ["laborer_large"] * 3) * 12, spacing=18, rows=2)

s.place_wells((1430, 980, 1790, 1300), spacing=54)
_lab = (["laborer"] * 4 + ["servant"]) * 140
for _y0 in range(946, 1140, 50):
    s.rowpack((1396, _y0, 1856, _y0 + 42), _lab, court_every=3, eave_ft=2)
for _y0 in range(971, 1140, 50):
    s.rowpack((1396, _y0, 1856, _y0 + 40), _lab, court_every=3, eave_ft=2)
for _y0 in range(1002, 1140, 25):
    s.rowpack((1408, _y0, 1804, _y0 + 22), _lab, court_every=3, eave_ft=2)
_merstrip = ["merchant_house"] * 240
for _i, _y0 in enumerate(range(1164, 1268, 52)):
    s.rowpack((1396, _y0, 1856, _y0 + 44), _merstrip if _i % 2 else _lab, court_every=3, eave_ft=2)
for _y0 in range(900, 946, 22):
    s.rowpack((1276, _y0, 1528, _y0 + 20), _lab, court_every=3, eave_ft=2)
s.rowpack((1424, 1132, 1796, 1162), _lab, court_every=3, eave_ft=2)

front([CROSS_H], (["merchant"] * 3 + ["shop"]) * 22, spacing=19, rows=2)
s.label(1560, 1216, "laborer neighborhoods", 10, italic=True, color="#5A4326")

# ====================================================================== NW: merchants + the dock
s.fire_tower(1362, 1120, label="fire tower")

_n_est = s.merchant_estates([(1268, 1372, "north"), (1256, 1104, "east"), (1210, 1620, "east")])
_ML_SPOTS = [(1344, 1380), (1268, 1104)][_n_est - 1 :]
s.frontage([(1040, 1330), (1390, 1330)], (["merchant"] * 5 + ["shop"]) * 18, skip=ROAD, width=s.lw(26), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(46))
front([MER_V], (["merchant"] * 3 + ["shop"]) * 14, spacing=19, rows=2)
s.place_wells((1044, 1034, 1380, 1300), spacing=54)
_mer = ["merchant_house"] * 650
for _y0 in range(1036, 1148, 56):
    s.rowpack((1044, _y0, 1140, _y0 + 48), _mer, court_every=3, eave_ft=2)
    s.rowpack((1216, _y0, 1382, _y0 + 48), _mer, court_every=3, eave_ft=2)
for _y0 in range(1300, 1330, 28):
    s.rowpack((1044, _y0, 1382, _y0 + 24), _mer, court_every=3, eave_ft=2)
for _y0 in range(1150, 1320, 50):
    s.rowpack((956, _y0, 1408, _y0 + 42), _mer, court_every=3, eave_ft=2)
for _y0 in range(1092, 1140, 24):
    s.rowpack((1046, _y0, 1240, _y0 + 22), _mer, court_every=3, eave_ft=2)
for _y0 in range(1175, 1320, 50):
    s.rowpack((956, _y0, 1408, _y0 + 40), _mer, court_every=3, eave_ft=2)
for _y0 in range(1170, 1310, 25):
    s.rowpack((1020, _y0, 1398, _y0 + 22), _mer, court_every=3, eave_ft=2)
s.merchant_storehouses(8)
s.label(1150, 1348, "merchant district", 10, italic=True, color="#5A4326")

# ====================================================================== SW: burakumin + timber ground
s.fire_tower(1150, 1400, label=None)
front(
    [SW_V], (["merchant"] * 2 + ["burakumin"] + ["laborer"]) * 14, spacing=19, rows=2
)  # merchant share up one notch (GM 2026-08-02): the ward-fix left the merchant cohort 1 below its band floor and the laborers ~40 above theirs - street commerce on the cargo-basin road is the natural place for the trade
s.place_wells((1020, 1360, 1390, 1680), spacing=54)
_sw = ["merchant_house"] * 225
# THREE merchant strips, not two (GM 2026-08-02): closing the samurai ward to commoners
# (city_samurai_ward_residents_only) took back the ~9 seats the old sweeps had wrongly found
# inside the fence, and the scatter passes could not find merchant-sized daylight anywhere else -
# the cohort stalled at 82 against the ~91 band floor. The third strip runs the merchant terrace
# one band further toward the cargo basin (river-trade ground - the right side of town for
# commerce), and the mixed laborer/servant/burakumin strips start below it; the small kinds have
# band slack and re-seat themselves through the census top-ups.
for _y0 in range(1344, 1448, 52):
    s.rowpack((1004, _y0, 1404, _y0 + 44), _sw, court_every=4, eave_ft=2)
# the third strip sits BELOW the MAIN_E street corridor at y1450 (a band straddling the roadbed
# seats nothing - the corridor refuses every row), on the ground the mixed strips used to take
s.rowpack((1004, 1462, 1404, 1506), _sw, court_every=4, eave_ft=2)
_sw2 = (["laborer"] * 2 + ["servant"] * 2 + ["burakumin"]) * 45
for _y0 in range(1514, 1748, 52):
    s.rowpack((1004, _y0, 1404, _y0 + 44), _sw2, court_every=4, eave_ft=2)
for _y0 in range(1488, 1700, 52):
    s.rowpack((1022, _y0, 1396, _y0 + 42), _sw2, court_every=4, eave_ft=2)
for _y0 in range(1475, 1700, 26):
    s.rowpack((1022, _y0, 1396, _y0 + 22), _sw2, court_every=4, eave_ft=2)
# THE LAST MERCHANT SEATS, ASKED FROM THE ENGINE (GM 2026-08-02): closing the ward to commoners
# cost the cohort its ~9 wrongly-inside seats, and the strips + widened sweeps recover all but a
# few - the band floor (~91 of 520) kept missing by 1-4 across regenerations. open_seat honors
# every corridor/reservation _fits knows (skill CLAUDE.md "Ask the ENGINE where a feature fits"),
# so these seats are real; the rects are commercial ground - the strip band, the cargo-basin
# approach, the river-gate strip, and the theater pocket.
_mh_w, _mh_h = s._dims("merchant_house")
_extra_mh = 0
for _rect in ((1004, 1462, 1404, 1512), (1044, 1620, 1390, 1748), (996, 1150, 1050, 1320), (1620, 1150, 1800, 1290)):
    while _extra_mh < 7:
        _seat = s.open_seat(_rect, _mh_w, _mh_h)
        if not _seat:
            break
        s.building(_seat[0], _seat[1], _mh_w, _mh_h, "merchant_house")
        _extra_mh += 1
# Moved south with its fabric - the y1462-1506 band is the third merchant strip now. It sits 6px
# under "Temple of Daikoku" and settlement-review (2026-08-02) read that as the temple's subtitle;
# no ink touches, so only the eye catches it. It STAYS, and the reason is measured rather than
# assumed: a sweep of every 2px seat in the quarter (x1120-1380, y1532-1640) against the recorded
# 50x10 caption box finds ZERO clear of the wells and rows at even 2px - 26 households and their
# idobata saturate the ground - so every seat that breaks the stack leaves the fabric the caption
# must name (city_labels_placed_with_subject). The two captions differ in weight, color and slant,
# which is what carries them apart. Re-siting this needs the QUARTER to open up, not a nudge.
s.label(1214, 1532, "burakumin", 10, italic=True, color="#6B4F2A")
# THE TIMBER AND CHARCOAL WORKING GROUND - the declared budget line, DRAWN as its kind rather than
# left as ambient slack: beaten earth with stacking rails, in the SE of the burakumin quarter where
# the raft cargo comes up from the landing.
s.animal_ground(1256, 1672, r=76, label="timber + charcoal ground")

# ====================================================================== OUTSIDE the walls
s.bound = None
# the WHARF suburb outside the river gate. The moat is CUT along the river face, so the strip
# between the east bank and the rampart is dry working ground - the raft landing for the Fox timber.
for jy in (1236, 1312, 1388):
    s.jetty(855, jy, rot=180, length=22)  # root ~14px onto the EAST bank, running WEST into the water
QUAY = [(908, 1188), (908, 1290)]
s.frontage(QUAY, ["shop"] * 16, skip=ROAD, width=s.lw(18), spacing=19, rows=2, rowgap=2, jitter=1, setback=s.px(30))
s.label(916, 1164, "wharf", 10, italic=True, color="#5A4326")
# the river gate's own approach-stall string, and the north gate's market
# The market line IS the road: s.frontage seats a rank on EACH side of its line ~15px out, and
# skip=ROAD keeps the bed itself clear. So the two ranks straddle the approach road at ~15px -
# clear of the roadbed, inside the 28px that counts as fronting it, and exactly how a guan-xiang
# market looks. Any other offset puts one rank on the road (at 26) or one rank 49px out in the
# fields (at 34): the ranks are 31px apart and the legal band is only 14 wide.
MKT_OFF = 0
WMARKET_LINE = [(672, 1340 + MKT_OFF), (866, 1332 + MKT_OFF)]
NMARKET_LINE = [(1389 - MKT_OFF, 828), (1373 - MKT_OFF, 700), (1365 - MKT_OFF, 624)]
s.frontage(WMARKET_LINE, ["shop"] * 12, skip=ROAD, width=s.lw(22), spacing=18, rows=1, jitter=1, setback=s.px(32), fill=True)
s.frontage(NMARKET_LINE, ["shop"] * 6, skip=ROAD, width=s.lw(22), spacing=17, rows=1, jitter=1, setback=s.px(32), fill=True)
s.label(1236, 790, "gate market", 9, italic=True, color="#5A4326")

# samurai country estates: dispersed walled compounds NORTHEAST of the city, toward Otosan Uchi.
# KNOWN DEFECT, verified and deliberately NOT fixed here (settlement-review + closing bookend,
# 2026-07-27). All three compounds are invisible to a reader:
#   * (1990,1006) is PAINTED OVER by a paddy plot of comb field fne1. Verified in the ink, not the
#     manifest - the compound group is emitted at SVG char ~232k and the covering polygon at ~354k,
#     so the field wins on document order. A crop centered on the estate shows only green quilt.
#   * (2170,880) and (2340,1100) fall outside the rendered view entirely (x max 2082).
# So the "samurai estates" caption names three compounds and points at none, while check_village
# still counts all three into the samurai caste band. Nothing catches it: `manors` is an overlap
# TARGET and never a STRUCT, so field-on-manor is untested.
# WHY IT IS STILL HERE: both obvious fixes reflow the rural belt, and `farmsteads()` on the city
# path spaces house-to-house without measuring the ANNEX envelope - so any reflow drops a pair whose
# kitchen garden and neighbor's tool shed overlap by a fraction of a pixel. Moving this block after
# the comb fields (which does fix the paddy) and re-siting the estates in-frame BOTH produced
# ('gardens','farm_sheds',2235,1365), a real 0.15 px overlap the matrix rightly fails. The fix that
# holds is in the packer's annex clearance, with the regen budget to re-sweep the pool behind it.
EST = [(1990, 1006, 76, 48, "west", (2080, 1026)), (2170, 880, 84, 56, "south", (2240, 900)), (2340, 1100, 94, 62, "east", (2400, 1130))]
for ex, ey, ew, eh, gd, (_lx, _ly) in EST:
    s.manor(ex, ey, ew, eh, "", gate_dir=gd)
s.label(2010, 1070, "samurai estates", 10, italic=True, color="#3A352C")


# ====================================================================== WATER-FIRST COMB FIELDS
def _pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    ll = vx * vx + vy * vy or 1.0
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ll))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def _in_poly(x, y, poly):
    n = len(poly)
    j = n - 1
    c = False
    for i in range(n):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]):
            c = not c
        j = i
    return c


def furrows(poly, color, theta):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    fcx, fcy = sum(xs) / len(xs), sum(ys) / len(ys)
    diag = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    dx, dy = math.cos(theta), math.sin(theta)
    nx, ny = -dy, dx
    cid = s._cid("dry")
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in poly)
    g = [f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath>', f'<g clip-path="url(#{cid})">']
    t = -diag / 2
    while t <= diag / 2:
        mx, my = fcx + nx * t, fcy + ny * t
        g.append(f'<line x1="{mx - dx * diag / 2:.1f}" y1="{my - dy * diag / 2:.1f}" x2="{mx + dx * diag / 2:.1f}" y2="{my + dy * diag / 2:.1f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        t += 5
    g.append('</g>')
    s.add(''.join(g))


def comb_field(name, sluice, down_deg, seed, field_fall, canal_a, canal_b, offtakes_a, offtakes_b=(), dry_band=(47, 88), avoid=(), dry_keepout=()):
    net = build_comb(
        3200,
        2700,
        sluice,
        seed,
        down_deg=down_deg,
        field_fall=field_fall,
        canal_a_len=canal_a,
        canal_b_len=canal_b,
        offtakes_a=offtakes_a,
        offtakes_b=offtakes_b,
        plot_across=PLOT_ACROSS,
        row_step=ROW_STEP,
        dry_band=dry_band,
        dry_keepout=dry_keepout,
        grain=2 / 3,
    )
    env = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append([(p[0], p[1]) for p in env])
    s.comb_base_fill(net, name, color="#CDB78C", full_envelope=True)
    _prior = [fld["outline"] for fld in s.M["fields"] if fld.get("kind") == "paddy"]
    for dp in net["dry_plots"]:
        if any(_pt_seg(x, y, ln[i][0], ln[i][1], ln[i + 1][0], ln[i + 1][1]) < 16 for ln in avoid for (x, y) in dp["poly"] for i in range(len(ln) - 1)):
            continue
        if any(hem_on_paddy(dp["poly"], _pol) for _pol in _prior):
            continue
        s.dry_polys.append(dp["poly"])
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in dp["poly"])
        s.add(f'<polygon points="{pts}" fill="{dp["fill"]}" stroke="#A98C58" stroke-width="1.4" stroke-linejoin="round"/>')
        furrows(dp["poly"], dp["furrow"], dp["theta"])
        s.M["dry_plots"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in dp["poly"]], "crop": dp["crop"], "theta": round(dp["theta"], 3)})
    for p in net["plots"]:
        pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in p["poly"])
        s.add(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{AZE}" stroke-width="{aze_w(s.ftpx):.2f}" stroke-linejoin="round"/>')
    s.bund_junctions(net["plots"], name)
    beads = ''.join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="{BEAN_GREEN}"/>' for x, y in net["bund_beans"])
    s.add(f'<g opacity="0.85">{beads}</g>')
    for c in sorted(net["channels"], key=lambda c: -c["w"]):
        s.field_channel(c["pts"], '#7C9EB0' if c["role"] == "drain" else '#6C9CBE', c["w"], c.get("w_tail", c["w"]), late=True)
    exs = [p[0] for p in env]
    eys = [p[1] for p in env]
    pvx = [v[0] for p in net["plots"] for v in p["poly"]]
    pvy = [v[1] for p in net["plots"] for v in p["poly"]]
    s.M["fields"].append(
        {
            "name": name,
            "kind": "paddy",
            "down_deg": down_deg,
            "outline": [[x, y] for x, y in env],
            "bbox": [min(exs), min(eys), max(exs), max(eys)],
            "vis_bbox": [min(pvx), min(pvy), max(pvx), max(pvy)],
            "plot_polys": [[[round(v[0], 1), round(v[1], 1)] for v in p["poly"]] for p in net["plots"]],
        }
    )
    for c in net["channels"]:
        s.M["field_ditches"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in c["pts"]], "role": c["role"], "field": name, "w": round(c["w"], 1), "w_tail": round(c.get("w_tail", c["w"]), 1)})
    return net, env, (round(sum(exs) / len(exs), 1), round(sum(eys) / len(eys), 1))


def plot_centroid(net, key, inset=0.15):
    cens = [(sum(v[0] for v in p["poly"]) / len(p["poly"]), sum(v[1] for v in p["poly"]) / len(p["poly"])) for p in net["plots"] if not p.get("filler")]
    cx, cy = key(cens)
    mx = sum(c[0] for c in cens) / len(cens)
    my = sum(c[1] for c in cens) / len(cens)
    return (round(cx + inset * (mx - cx), 1), round(cy + inset * (my - cy), 1))


def topo_channel(pts, frm, to, draw_w=0.0, col='#7C9EB0'):
    ax, ay = pts[0]
    bx, by = pts[-1]
    chord = math.hypot(bx - ax, by - ay) or 1.0
    dev = max(abs((py - ay) * (bx - ax) - (px - ax) * (by - ay)) / chord for px, py in pts[1:-1]) if len(pts) > 2 else 0.0
    if dev < 6:
        k = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        mx, my = (pts[k][0] + pts[k + 1][0]) / 2, (pts[k][1] + pts[k + 1][1]) / 2
        pts = list(pts[: k + 1]) + [(mx - 12 * (by - ay) / chord, my + 12 * (bx - ax) / chord)] + list(pts[k + 1 :])
    poly = [[round(px, 1), round(py, 1)] for px, py in pts]
    s.M["channels"].append({"poly": poly, "frm": frm, "to": to, "w": draw_w or 2.5, "drawn": bool(draw_w)})
    s.corridors.append(([(px, py) for px, py in poly], 33))
    if draw_w:
        s.field_channel([(px, py) for px, py in poly], col, draw_w, draw_w)


# the moat-fed combs on the three LANDWARD faces (the river face is the wharf's dry working ground)
# down_deg points AWAY from the wall on each face - a fan falls down the slope the moat sits on
# top of, so a bearing aimed back at the city grows the paddy over the rampart and the streets.
MOAT_FARMS = [
    ("fse1", (1740, 1660), 55, 21, 185, (165, 215), (100, 135), (0.35, 0.7)),  # SE face, falling SE - downstream of its own tap
    ("fne1", (1790, 1120), 345, 22, 180, (160, 210), (95, 130), (0.4, 0.75)),  # NE face, falling NNE
    ("fe1", (1900, 1450), 10, 38, 185, (165, 215), (100, 135), (0.4, 0.78)),  # E face, falling E
    ("fs1", (1420, 1800), 85, 39, 185, (155, 200), (95, 130), (0.4, 0.75)),  # S face, falling S
    ("fsw1", (1210, 1852), 120, 44, 175, (150, 195), (92, 125), (0.4, 0.75)),  # SW face, falling SSW - east of the Hayakawa, clear of the re-derived ring's outfall
]
for nm, tap, dd, sd, ff, ca, cb, oa in MOAT_FARMS:
    mp = min(MOAT, key=lambda p: (p[0] - tap[0]) ** 2 + (p[1] - tap[1]) ** 2)
    _ol = math.hypot(mp[0] - CX, mp[1] - CY) or 1.0
    sl = (round(mp[0] + 30 * (mp[0] - CX) / _ol), round(mp[1] + 30 * (mp[1] - CY) / _ol))
    _mfl = s.M["moat_flow"]
    mp = moat_swept_tap(MOAT, _mfl["inlet"], _mfl["outlet"], sl, mp)
    s.field_channel([mp, sl], '#9CB4C8', 7, 7)
    s.sluice_gate(sl[0], sl[1], rot=math.degrees(math.atan2(sl[1] - mp[1], sl[0] - mp[0])) + 90)
    _net, _env, _cen = comb_field(nm, sl, dd, sd, ff, ca, cb, oa, avoid=(MOAT,))
    _pd = plot_centroid(_net, lambda cs: max(cs, key=lambda pc: pc[1]))
    _pd = (round(0.80 * _pd[0] + 0.20 * _cen[0], 1), round(0.80 * _pd[1] + 0.20 * _cen[1], 1))
    topo_channel([(mp[0], mp[1]), sl, _pd], {"kind": "moat"}, {"kind": "field", "name": nm})
    _dr = next(c["pts"] for c in _net["channels"] if c["role"] == "drain")
    topo_channel([tuple(_dr[-2]), tuple(_dr[-1])], {"kind": "drain", "name": nm}, {"kind": "offmap"})
    s.ring(('poly', _env), 26, 15, ["plain"])
    s.ring(('poly', _env), 20, 40, ["plain"])

# the FAR-BANK fan, tapped straight off the Hayakawa - the paddy country running on west beyond the
# frame (city_has_outside_farmland wants at least one field off the map edge).
_netw, ENV_FW, _cw = comb_field("fw1", (660, 940), 190, 43, 190, (170, 220), (105, 140), (0.4, 0.75), avoid=(MOAT,))
_pw = plot_centroid(_netw, lambda cs: max(cs, key=lambda c: c[0]))
topo_channel([(810, 920), (660, 940), _pw], {"kind": "river"}, {"kind": "field", "name": "fw1"})
s.field_channel([(810, 920), (660, 940)], '#9CB4C8', 7, 7)
s.sluice_gate(660, 940, rot=math.degrees(math.atan2(20, -150)) + 90)
_drw = next(c["pts"] for c in _netw["channels"] if c["role"] == "drain")
_dwx, _dwy = _drw[-1]
topo_channel([(_dwx, _dwy), (200, _dwy + 40)], {"kind": "drain", "name": "fw1"}, {"kind": "offmap"}, draw_w=4.0)
s.ring(('poly', ENV_FW), 24, 15, ["plain"])
s.ring(('poly', ENV_FW), 18, 40, ["plain"])
s.ring(('poly', ENV_FW), 30, 15, ["plain"])
s.ring(('poly', ENV_FW), 22, 26, ["plain"])

# THE DEAD CROSS THE RIVER: the funerary complex on the far bank, DOWNSTREAM of the city and south
# of the bridge road. The moat's water set-back leaves no dry landward fringe, and bearing the dead
# over the water suits the geography of the afterlife. Burial set-back: the Hayakawa is a wide
# stream, so a burial ground's corners sit >= 160px off its centerline (cremation is exempt at 30).
s.cemetery(600, 1700, 92, 66, parish=False, label="common burial ground")
s.cremation_ground(604, 1800)
s.ossuary(596, 1614)

s.boundary_marker(
    658, 1354, label_xy=(620, 1366)
)  # ON the west road verge, where the road leaves clean ground (seat from site_justice.py); caption pulled west off a gate-market stall at (682.7,1359.2)
s.execution_ground(
    556, 1378, rot=6
)  # caption BELOW (clear waste ground): angled captions (GM 2026-08-02) tilt this caption 6 deg with its ground, and from the above-seat its right end dipped into the boundary stone's caption band (no_label_overlaps)

s.bridges()
s.farmsteads()
s.farm_wells()


# ====================================================================== the dwelling top-up
# REFUSALS ARE REMEMBERED ACROSS CALLS (2026-08-08). The sweep below is run over the same ground
# many times over - each caste's regions three times, then again by fill_exactly - on a fixed 5x6
# px lattice, so 64.6% of this gen's 511,519 candidate evaluations were re-refusals of a seat an
# earlier pass had already refused. SeatMemo (settlement.py) skips those, and asserts the
# append-only invariant that makes skipping them sound rather than assuming it. Output-preserving:
# the manifest is byte-identical across the change.
_SEATS = settlement.SeatMemo(s)


def top_up(kind, region, need, count_kinds=None):
    _SEATS.sync()
    kinds = set(count_kinds or (kind,))
    have = sum(1 for b in s.M["buildings"] if b["kind"] in kinds)
    w_, h_ = s._dims(kind)
    gov = s.M.get("governor_mansion")
    civ = [(m["x"], m["y"], m["w"], m["h"]) for m in s.M.get("ministries", [])]
    if gov:
        civ.append((gov["x"], gov["y"], gov["w"], gov["h"]))
    labs = [tuple(lb[:4]) for lb in s.M.get("labels", [])]
    # INDEXED (2026-08-04): ok() ran this list per candidate - ~50 labels x ~500k candidates - which
    # was the single hottest thing in this gen. Labels do not move during a top-up, so the grid is
    # built once; the pad is conservative (the longer half-dimension), and the exact overlap test
    # below is unchanged, so it can only narrow what that test sees.
    lab_grid = settlement.boxed_grid([(lb, *lb) for lb in labs])
    lab_pad = max(w_, h_) / 2 + 2
    stab = [(b["x"], b["y"]) for b in s.M.get("buildings", []) if b.get("kind") == "stables"]

    def ok(gx, gy):
        if not _in_poly(gx, gy, WALL):
            return False
        if any(abs(gx - cx) <= (cw + w_) / 2 + 27 and abs(gy - cy) <= (ch + h_) / 2 + 27 for cx, cy, cw, ch in civ):
            return False
        if any((gx - sx) ** 2 + (gy - sy) ** 2 < 85**2 for sx, sy in stab):
            return False
        return not any(
            min(x1_, gx + w_ / 2 + 2) - max(x0_, gx - w_ / 2 - 2) > 0 and min(y1_, gy + h_ / 2 + 2) - max(y0_, gy - h_ / 2 - 2) > 0 for (x0_, y0_, x1_, y1_), *_ in lab_grid.near(gx, gy, lab_pad)
        )

    def exact_clear(gx, gy, gap=3.0):
        if s._in_blocked(gx, gy) or s._near_corridor(gx, gy):
            return False
        if s.bound and not _in_poly(gx, gy, s.bound):
            return False
        if any(abs(gx - w2["x"]) < 26 and abs(gy - w2["y"]) < 26 for w2 in s.M.get("wells", [])):
            return False
        if not all(abs(gx - px) >= (w_ + pw) / 2 + gap or abs(gy - py) >= (h_ + ph) / 2 + gap for (px, py, pw, ph) in s.placed):
            return False
        for o in itertools.chain(s.M["buildings"], s.M["houses"]):  # chained, not concatenated: the + built a ~700-entry list per candidate
            if "w" not in o or abs(gx - o["x"]) > 42 or abs(gy - o["y"]) > 42:
                continue
            oth = math.radians(o.get("rot", 0))
            oc, os_ = abs(math.cos(oth)), abs(math.sin(oth))
            if abs(gx - o["x"]) < (w_ + oc * o["w"] + os_ * o["h"]) / 2 + gap and abs(gy - o["y"]) < (h_ + os_ * o["w"] + oc * o["h"]) / 2 + gap:
                return False
        return True

    def door_clear(gx, gy, rot):
        dc = (7.0 / 3) * 1.15
        th = math.radians(rot)
        ux, uy = -math.sin(th), math.cos(th)
        vx, vy = -uy, ux
        fx, fy = gx + ux * h_ / 2, gy + uy * h_ / 2
        rr = math.hypot(w_, h_) / 2 + dc + 2
        for o in itertools.chain(s.M["buildings"], s.M["houses"]):  # chained, not concatenated: the + built a ~700-entry list per candidate
            if "w" not in o:
                continue
            if math.hypot(o["x"] - gx, o["y"] - gy) > rr + math.hypot(o["w"], o["h"]) / 2:
                continue
            oth = math.radians(o.get("rot", 0))
            c_, sn = math.cos(oth), math.sin(oth)
            corners = [
                (o["x"] + c_ * dx - sn * dy, o["y"] + sn * dx + c_ * dy) for dx, dy in ((-o["w"] / 2, -o["h"] / 2), (o["w"] / 2, -o["h"] / 2), (o["w"] / 2, o["h"] / 2), (-o["w"] / 2, o["h"] / 2))
            ]
            for d_ in (0.8, dc * 0.55, dc):
                for t_ in (-0.3 * w_, 0.0, 0.3 * w_):
                    if _in_poly(fx + ux * d_ + vx * t_, fy + uy * d_ + vy * t_, corners):
                        return False
        return True

    x0, y0, x1, y1 = region
    for pad in (7, 4, "exact", "tight"):
        # the refusal set for THIS kind at THIS tightness, hoisted out of the scan. The key names
        # the footprint as well as the kind, so it cannot outlive a re-dimensioned kind.
        dead = _SEATS.level(kind, w_, h_, pad)
        gy = y0
        while gy <= y1 and have < need:
            gx = x0
            while gx <= x1 and have < need:
                if (gx, gy) not in dead:
                    orot = None
                    if ok(gx, gy) and (exact_clear(gx, gy, 2.4 if pad == "tight" else 3.0) if pad in ("exact", "tight") else s._fits(gx, gy, w_ + pad, h_ + pad)):
                        orot = next((r_ for r_ in (0.0, 180.0) if door_clear(gx, gy, r_)), None)
                    if orot is None:
                        dead.add((gx, gy))
                    else:
                        s.building(gx, gy, w_, h_, kind, orot)
                        have += 1
                gx += 5
            gy += 6
        if have >= need:
            break
    return have


DWELL = ("laborer", "laborer_large", "servant", "burakumin", "merchant", "merchant_house", "merchant_large", "samurai", "samurai_large", "monk_house")


def _dwell_count():
    return sum(1 for b in s.M["buildings"] if b["kind"] in DWELL)


# civic aprons, PHASE 2: the pack is done, so the ministry/yamen aprons drop 30 -> 16 and the
# axis-aligned fills (whose own ok() enforces a 15px AABB office gap) may claim the tight bands.
# Replaced IN PLACE, index for index - the _poly_bboxes cache invalidates on list LENGTH only.
for _ci, _m in zip(range(_CIV_I0, _CIV_I1), s.M["ministries"] + [s.M["governor_mansion"]], strict=True):
    s.block_polys[_ci] = [
        (_m["x"] - _m["w"] / 2 - 28, _m["y"] - _m["h"] / 2 - 28),
        (_m["x"] + _m["w"] / 2 + 28, _m["y"] - _m["h"] / 2 - 28),
        (_m["x"] + _m["w"] / 2 + 28, _m["y"] + _m["h"] / 2 + 28),
        (_m["x"] - _m["w"] / 2 - 28, _m["y"] + _m["h"] / 2 + 28),
    ]

NE_Q = (1424, 968, 1790, 1258)
NW_Q = (1030, 1030, 1386, 1312)
SW_Q = (1044, 1366, 1386, 1660)
SE_Q = (1452, 1312, 1836, 1716)

_MERCH = ("merchant", "merchant_house", "merchant_large")
_LAB = ("laborer", "laborer_large")
# the wealthier 'master' cohort FIRST, into gaps the plain fill would otherwise claim (budgets.md
# puts ~12.5% of laborers in larger homes; city_laborer_housing_varied wants 6-20%)
# tight draw-point passes for the courts the gate names as over the ~26-household cap. BEFORE
# the fills, so each reserves its court rather than arriving to find the ground taken.
for _wr in (
    (1610, 1080, 1710, 1180),
    (1530, 1190, 1630, 1290),
    (1280, 1215, 1380, 1315),
    (1015, 1405, 1115, 1505),
    (1215, 1610, 1315, 1700),
    (1425, 1010, 1466, 1100),
    (1500, 960, 1640, 1070),
    (1000, 1400, 1140, 1520),
    (1200, 1500, 1350, 1620),
    (1240, 1590, 1380, 1700),
    (1360, 960, 1470, 1070),
    (1500, 1180, 1650, 1300),
):
    _wseat = s.open_seat(_wr, 18, 18, well=True)
    if _wseat:
        s.well(*_wseat)
top_up("samurai_large", SE_Q, 6)
top_up("laborer_large", NE_Q, 18)
top_up("laborer_large", SW_Q, 24)
# then each caste to its budgets.md target across every quarter that can hold it
for _kind, _regions, _target, _ck in (
    ("samurai", (SE_Q,), 40, ("samurai", "samurai_large")),
    ("merchant_house", (NW_Q, SW_Q), 94, _MERCH),
    ("burakumin", (SW_Q,), 26, ("burakumin",)),
    ("laborer", (NE_Q, SW_Q, NW_Q), 150, _LAB),
    ("servant", (NW_Q, NE_Q, SW_Q, SE_Q), 76, ("servant",)),
):
    for _region in _regions:
        if sum(1 for b in s.M["buildings"] if b["kind"] in _ck) >= _target:
            break
        top_up(_kind, _region, _target, count_kinds=_ck)
# the temple families, wherever a precinct's own pack could not seat all six
for _tx, _ty in [(1104, 1176), (1366, 1170), (1064, 1428), (1372, 1090), (1470, 1132), (1728, 1156), (1560, 1170), (1330, 1444)]:
    top_up("monk_house", (_tx - 60, _ty - 46, _tx + 60, _ty + 54), 48)
# GRID FILLS before the scattered sweeps. s.pack lays on a fixed step, so its houses come to rest
# in ranks that touch their neighbors; top_up's per-candidate clearance sweep cannot (it keeps 3px
# of daylight by construction), and half the commoner fabric was arriving that way
# (city_row_housing_touches). Pack first, scatter only into what is left.
# s.bound is restored to the ring for the fills: s.pack does NOT test the wall, and without it
# a dozen commoner houses came to rest outside the rampart (city_commoner_dwellings_inside_walls).
s.bound = [list(p) for p in RING]
reserve_caption_ground()
s.pack(NE_Q, (["laborer"] * 4 + ["servant"]) * 60, step=13, face_streets="fill")
s.pack(NW_Q, (["merchant_house"] * 4 + ["merchant"]) * 55, step=13, face_streets="fill")
s.pack(SW_Q, (["laborer"] * 3 + ["servant"] * 2 + ["burakumin"]) * 55, step=13, face_streets="fill")
s.pack(SE_Q, (["samurai"] * 3 + ["samurai_large"]) * 30, step=12, face_streets="fill")
# THE WARD'S SERVANT HOUSING - each household's own nagaya, not a servant quarter. Runs here, with
# every ward samurai house finally placed and s.ward long since drawn, and BEFORE fill_exactly, so
# the exact-population pass can top the servant count up in the commoner quarters afterwards.
# (The old `s.pack(SE_Q, ["servant"] * 90)` stood here; the engine now refuses a freestanding
# servant inside a ward outright, so it would place nothing.)
# HOUSEHOLDS FIRST, then their ranges - in that order, and never the reverse. The ward was the
# city's emptiest quarter (0.48 dwellings/1000px^2 against the SW's 1.66) and the samurai cohort
# sits well inside its band, so the honest way to close the exact-population figure is MORE SAMURAI
# HOUSEHOLDS here, each arriving with its own servant range, rather than commoner fill the fence
# exists to keep out. The ranges go LAST because a house seated after them can come to rest across
# a range's doorway - top_up only clears its OWN door, not its neighbors'.
top_up("samurai", SE_Q, 64, count_kinds=("samurai", "samurai_large"))  # 64 = the caste ceiling (1.3 x 10% x 520) less the three extramural estates
s.servant_ranges()

# whole-interior sweeps: the per-quarter regions leave ground stranded at their seams, and the
# budget promises 520 dwellings, so the last passes are limited by the ground and nothing else.
ALL_Q = (1032, 980, 1800, 1690)
# The ward is closed to commoners now (city_samurai_ward_residents_only), which cost the merchant
# cohort the ~9 seats the old sweeps had WRONGLY found inside the fence - and ALL_Q stops at
# y=1690 / x=1032, so the south band inside the ring and the river-gate strip were never scanned
# for replacement seats. MERCHANTS FIRST into that wider window, ahead of the laborer/servant
# sweeps: the small kinds seat almost anywhere, the big merchant footprint is the one that runs
# out of ground (post-ward-fix it stalled at 81 of the ~91 band floor).
WIDE_Q = (962, 980, 1836, 1758)
top_up("merchant_house", WIDE_Q, 94, count_kinds=_MERCH)
top_up("merchant_house", ALL_Q, 94, count_kinds=_MERCH)
top_up("laborer", ALL_Q, 150, count_kinds=_LAB)
top_up("servant", ALL_Q, 76)
top_up("samurai", SE_Q, 40, count_kinds=("samurai", "samurai_large"))
top_up("burakumin", SW_Q, 26)
for _pass in range(3):
    for _rg in (NW_Q, SW_Q, NE_Q, ALL_Q, WIDE_Q):
        top_up("merchant_house", _rg, 94, count_kinds=_MERCH)
    for _rg in (NE_Q, NW_Q, SW_Q, SE_Q, ALL_Q):
        top_up("laborer", _rg, 150, count_kinds=_LAB)
    for _rg in (NW_Q, NE_Q, SW_Q, SE_Q, ALL_Q):
        top_up("servant", _rg, 76)

# ====================================================================== EXACTLY the declared figure
# population_consistent_with_housing allows NO band any more (GM 2026-07-26): a declared population is
# a promise about what the map CONTAINS, so the arithmetic has to close exactly - POP / HOUSEHOLD
# dwellings, not "within 7%". This drives the count to the target and never past it: each pass asks a
# caste for exactly the shortfall, and top_up stops the moment that caste's tally reaches the figure
# asked, so it cannot overshoot. Order matters - the castes with the smallest footprint go first,
# because they are the ones that still fit once the quarters are full. If the ground genuinely cannot
# take them the loop stalls and the CHECK fails, which is the correct outcome: the answer is a bigger
# wall from the budget, never a smaller declared figure.
TARGET_DWELLINGS = POP // HOUSEHOLD_RESIDENTS


def fill_exactly(target):
    order = (
        ("servant", ALL_Q, ("servant",)),
        ("laborer", ALL_Q, _LAB),
        ("merchant_house", WIDE_Q, _MERCH),
        ("burakumin", SW_Q, ("burakumin",)),
        ("samurai", SE_Q, ("samurai", "samurai_large")),
    )
    # count what the CHECK counts (its dwelling set includes monk_house); Minami's DWELL happens to
    # match, but stating it here keeps the three cities' fills identical
    _CHECKED = ("laborer", "laborer_large", "servant", "burakumin", "samurai", "samurai_large", "merchant", "merchant_house", "merchant_large", "monk_house")

    def _dw_all():
        return sum(1 for b in s.M["buildings"] if b["kind"] in _CHECKED)

    # RESPECT THE CASTE CEILINGS. Filling smallest-footprint-first is what makes the last seats
    # findable, but unchecked it pushes one caste past its +/-30% band (Tango's servants went to 159
    # against a 156 ceiling). Each caste is asked for no more than its ceiling; the loop then moves to
    # the next. The ceiling counts what city_caste_counts_in_band counts - walled estates and manors
    # included - so the two cannot disagree.
    _FRAC = {"servant": 0.20, "laborer": 0.40, "merchant_house": 0.25, "burakumin": 0.05, "samurai": 0.10}
    _EXTRA = {"merchant_house": len(s.M.get("merchant_estates", []) or []), "samurai": len(s.M.get("manors", []) or [])}
    for _ in range(30):
        if _dw_all() >= target:
            return
        moved = False
        for _k, _rg, _ck in order:
            short = target - _dw_all()
            if short <= 0:
                break
            _have = sum(1 for b in s.M["buildings"] if b["kind"] in _ck)
            _ceil = int(1.3 * _FRAC[_k] * target) - _EXTRA.get(_k, 0)
            if _have >= _ceil:
                continue
            _n0 = _dw_all()
            top_up(_k, _rg, min(_have + short, _ceil), count_kinds=_ck)
            moved = moved or _dw_all() > _n0
        if not moved:
            return  # the ground is full - the gate says so, loudly


fill_exactly(TARGET_DWELLINGS)

for _mx, _my in _ML_SPOTS:
    s.building(_mx, _my, *s._dims("merchant_large"), "merchant_large")

# THE LAST SEATS, asked from the engine rather than from a grid. fill_exactly scans on a fixed
# 5x6 px lattice, so a gap that is real but off-lattice is invisible to it - and after the ward
# stopped taking commoner fill, the map came to rest ONE dwelling under its declared 520. open_seat
# asks _fits itself at the finest step and returns the best clear seat, which is how the well
# passes already find ground the sweeps miss (skill CLAUDE.md, "Ask the ENGINE where a feature
# fits"). Smallest kind first, because at this point only a small footprint can still land.
_sv_w, _sv_h = s._dims("servant")
for _rect in (SW_Q, NE_Q, NW_Q, WIDE_Q, ALL_Q):
    while _dwell_count() < TARGET_DWELLINGS:
        _seat = s.open_seat(_rect, _sv_w, _sv_h)
        if not _seat or not s.building(_seat[0], _seat[1], _sv_w, _sv_h, "servant", 0.0):
            break
    if _dwell_count() >= TARGET_DWELLINGS:
        break

# FINE global well pass: after every dwelling is placed, drop wells into the nearest clear COURT.
s.place_wells((1424, 968, 1730, 1250), spacing=42, near=48)
s.place_wells(NW_Q, spacing=42, near=48)
s.place_wells(SW_Q, spacing=42, near=48)
s.place_wells((1440, 960, 1720, 1240), spacing=46, near=48)
s.place_wells((1020, 1020, 1382, 1300), spacing=46, near=48)
s.place_wells((1020, 1370, 1382, 1670), spacing=46, near=48)
for _wr in (
    (1030, 1000, 1390, 1320),
    (1420, 990, 1800, 1300),
    (1030, 1340, 1390, 1690),
    (1010, 1400, 1130, 1520),
    (1260, 1440, 1380, 1620),
    (1370, 1000, 1490, 1110),
    (1040, 1420, 1180, 1560),
    (1240, 1500, 1380, 1640),
    (1400, 1010, 1520, 1120),
    (1280, 1220, 1380, 1310),
    (1090, 1470, 1200, 1560),
    (1210, 1610, 1320, 1700),
    (1380, 1020, 1480, 1100),
    (1300, 1230, 1400, 1320),
    (1020, 1420, 1120, 1500),
    (1240, 1520, 1340, 1610),
    (1220, 1620, 1330, 1700),
    (1390, 1030, 1470, 1090),
):
    s.place_wells(_wr, spacing=38, near=46)
for _wr in ((1100, 1200, 1400, 1320), (1200, 1350, 1400, 1450), (1440, 1180, 1560, 1270), (1080, 1220, 1240, 1320), (1260, 1220, 1400, 1320)):
    s.place_wells(_wr, spacing=34, near=44)
s.place_wells(
    (1220, 1500, 1400, 1620), spacing=30, near=44
)  # the SE-of-burakumin pocket: the ward-fix reshuffle pushed its (1378,1572) head to 27-29 households, over the 26 ceiling - tighter spacing seats a second head
s.place_wells((1540, 1000, 1700, 1100), spacing=30, near=42)  # the north laborer terraces outgrew the (1605,1047) head

s.crop_city(margin=30, west=70)
s.title("Minami")

# ===== THE OFFICIAL NOTICE BOARDS - a city draws the SET: the principal board at the central
# market node plus one on every main gate's approach. Only ONE carries the label.
s.kosatsuba(1398, 1348, rot=90)
s.kosatsuba(1384, 974, rot=78, label=None)  # the north gate's board, on the road verge inside
s.kosatsuba(1016, 1348, rot=0, label=None)  # the river gate's board

s.place_punishment_spot(label_xy=(1270, 1454))  # the auto-caption sat 106 px east of its own spot AND across the ward kido at (1421,1450)

HERE = os.path.dirname(os.path.abspath(__file__))
nb = {}
for b in s.M["buildings"]:
    nb[b["kind"]] = nb.get(b["kind"], 0) + 1
print("farmhouses:", len(s.M["houses"]), "| buildings:", nb, "| total urban:", sum(nb.values()), "| dwellings:", _dwell_count(), "| finish:", s.finish(os.path.join(HERE, "minami")))
