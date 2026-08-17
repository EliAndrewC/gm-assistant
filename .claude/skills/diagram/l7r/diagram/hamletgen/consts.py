"""The researched constants that size a hamlet, each with the reasoning that fixed it.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

# Pt, Poly and SQ_FT_PER_ACRE moved to the shared sitegen package (feature 119) - they were
# never about hamlets. Re-exported here so `from .consts import Poly, Pt` keeps working inside
# this package and hamletgen's public surface is unchanged.
# The `X as X` form is not stylistic: mypy --strict turns on --no-implicit-reexport, so a
# plain `from ... import X` would NOT re-export X and every `from .consts import Poly, Pt`
# in this package would fail to type-check.
from l7r.diagram.sitegen.types import SQ_FT_PER_ACRE as SQ_FT_PER_ACRE  # noqa: F401
from l7r.diagram.sitegen.types import Poly as Poly  # noqa: F401
from l7r.diagram.sitegen.types import Pt as Pt  # noqa: F401

# ---- researched constants, each with the reasoning that fixed it -------------------------------

# GROSS PADDY PER HOUSEHOLD. Ikegami's generator states the tier's own figure: "~15 households x
# ~1.3 acres gross = ~20 acres of paddy". It is GROSS (the household's whole holding, bunds and
# access included), not the net planted area, which is why it sits above a bare subsistence ration.
# Recorded here because this is the one number that sizes the entire map: the field area sets the
# canvas, the canvas sets the crop, and the crop sets how the place reads.
#
# WORTH KNOWING, and the reason this module SOLVES for the figure instead of passing a fall length:
# Ikegami aims at ~20 acres in its docstring and its own closing line reports 15.3 - a 24% miss, and
# nothing catches it, because `field_fall` is a PIXEL length hand-tuned until the fan looked right
# and no check reads acreage. A script can close that loop (see `fit_field`), which is the clearest
# single case in this experiment of scripted beating authored on PRECISION rather than speed.
GROSS_ACRES_PER_HOUSEHOLD = 1.3


# LANE CLEARANCE - the no-build corridor a lane reserves, in px.
#
# This used to be 48 rather than the authored maps' 32, as a WORKAROUND: `_near_corridor` tests a
# candidate's CENTRE against the corridor and the placer passed the farmhouse's BASE rect (46 x 28
# ft), while a homestead's wealth variation renders the house up to ~1.33x that - so at 32 a
# well-off farmhouse's drawn corner ended 2.4 px from a connector track's centerline with its centre
# a legal 34 px off, and `houses_clear_of_lanes` measures the DRAWN corners.
#
# THE ENGINE FIXED HALF OF IT (2026-08-12): a lane now registers its drawn TREAD as well as its
# corridor, and `_fits` tests a candidate's whole footprint against the tread, so anything seated
# THROUGH `_fits` can no longer put a corner on a lane. The other half is not the corridor's size at
# all, which is why lowering this to 32 did not work: a homestead BUNDLE is seated by its own
# geometry (`_bundle_fits`), never through `_fits`, and the house inside it is offset from the seed
# point AND scaled by the wealth/length jitter - so the rect the placer clears is neither the size
# nor the position of the rect the map draws. Measured: at 32, 12 of 24 cohort maps put a farmhouse
# corner on a lane, and instrumenting one showed `_fits` was never called at the offending house's
# position with its own w/h at all. Testing the drawn house rect inside `_bundle_fits` DOES fix it
# and is the right end state, but it re-rolls four hand-authored maps and breaks Hoshigaoka's gate,
# so it is a reviewed pool job rather than a side effect (recorded in hamletgen.md, finding 2).
# Until then this stays wide enough that the drawn steading clears the tread from any seat.
LANE_CLEARANCE = 48.0

# How far off a lane's centerline a frontage seat is offered. This is a PLACEMENT decision and is
# deliberately not derived from LANE_CLEARANCE, which is the corridor rule: fronting a lane excuses
# a seat from the corridor's setback (that is what `skip` means to `_near_corridor`), so the row's
# own offset is the only thing holding the DRAWN steading off the tread. A wealthy minka renders to
# ~61 x 37 ft, a half-diagonal of ~36 px; add the lane's own half-tread and a dooryard's working
# margin. Tying this to the clearance is what made the clearance look like it had to be 48.
LANE_FRONTAGE_STANDOFF = 70.0

# How far outside the paddy's outline a field spur's tip stops. The lane is drawn 5 px wide and
# `fields_clear_of_road` allows w/2 + 2, so 8 px would clear it on paper - but the outline is a
# rolled, ragged polygon and the tip is placed against a VERTEX, whose two edges may fall away on
# either side. This is the smallest set-back that keeps every cohort map's tip out of the standing
# water, and it is still under a farmhouse's width, so the track visibly reaches the field.
#
# RE-CALIBRATED 14 -> 17 when the comb net went to TRUE SIZE (2026-08-17). Narrower channels let the
# carve plant closer to the water and `close_seams` recover more scraps, so a field's DRAWN extent
# (`vis_bbox`, which is what `fields_clear_of_road` intersects with the outline) grew - and ground a
# spur tip had legitimately occupied became rice. Seed 11 of the 24-map cohort was the one that
# tipped: its tip stood 2.7 px from an outline vertex against the check's 4.5 px allowance. Swept
# 14/16/17/18/20/22 against that seed - 14 and 16 fail, 17 is the first that clears - and 17 returns
# the whole cohort to its pre-change residue (22/24, the same two maps).
#
# THE LESSON, since this is the second knob this ladder has moved: a constant calibrated as "the
# smallest value that passes the cohort" is calibrated against a GEOMETRY, not against a principle,
# so anything that changes what the fan draws can invalidate it silently. Re-run the cohort after
# any change to channel widths, carve thresholds or the seam pass, and expect this number to move.
SPUR_SETBACK = 17.0

# How much open ground a threshing yard needs to its SOUTH, in feet. A thatched roof is pitched 45
# degrees or steeper, so the 46 x 28 ft minka's ridge stands ~20 ft up; at 38N in the threshing
# month that is 21 ft of shadow at noon and 39 ft by 9am. 39 protects the 9-to-3 drying day, which
# is the one that matters - and it costs nothing in row pitch, since house depth (28) + yard depth
# (~26) + 39 already comes to about the 92 ft the cluster band was independently sized at.
SUN_CORRIDOR_FT = 39.0

# THE FIELD ARCHETYPES this generator can draw, and why there are two rather than five. The pool's
# hamlets span five (`valley_paddy`, `polder_grid`, `mulberry_dike_fishpond`, `contour_terraces`,
# `ribbon_valley`) and they are not variations on one shape - a comb fan is grown around a head-race
# on sloping ground, a polder is a surveyed orthogonal grid diked out of standing water on flat
# ground. They share `draw_comb_field` (build_polder deliberately returns build_comb-compatible
# keys) and almost nothing else: different water entry, different drainage, a perimeter dike, and a
# village that must sit on the LANDWARD side rather than the upslope one.
#
# `mulberry_dike_fishpond` is not a third archetype here - it is an OVERLAY on the polder (see
# `MULBERRY_ELIGIBLE`), which is what it is historically too.
FIELD_ARCHETYPES = ("valley_paddy", "polder_grid")

# ...but only the proven one is ROLLED, and `polder_grid` is opt-in until it survives a COHORT.
#
# It was promoted on 2026-08-15 after sweeping 48 of 48 (8 seeds x 4 cardinal bearings, plus the
# household band's ends) and demoted the same day, because the cohort is a harder test than that
# sweep: `cohort_audit` varies HOUSEHOLDS per seed and rolls water_sink, cluster_shape and
# lane_skeleton, where the sweep pinned households at 16 and took the default rolls. Under those
# conditions the fitted cohort fell to 19 of 24. That is the cohort earning its keep exactly as it
# did three times for the valley tier - a fixed-parameter sweep is not evidence of consistency.
#
# THE BAR FOR PROMOTION is therefore a green COHORT, not a green sweep: 24/24 and 12/12 with polders
# in the mix. Rolling an archetype with open failures mixes them into the valley tier's own numbers
# and destroys the one measurement that says this process is consistent.
ROLLED_ARCHETYPES = ("valley_paddy",)

# The polder's module size, in feet, before fitting. Enokida's 110 ft cell puts a whole bay at ~1.9
# mu, a half at ~0.9 and a third at ~0.6 - which is the attested parcel range (build_polder's
# TRUE-SCALE SIZING note). `fit_polder` scales the GRID, not the cell, so the parcels keep that
# calibration whatever acreage the household count asks for.
POLDER_CELL_FT = 110.0

# HOW MUCH GROUND ONE HOMESTEAD TAKES, in px at 1 ft/px - the pitch the cluster band is sized on.
# A bundle's reserved rects come to ~71 x 57 ft; the placer then keeps bundles apart by
# circumscribed circles rather than real footprints, so the effective pitch is larger again. 92 px
# per household leaves the cluster dense enough to read as a nucleus and open enough for its
# courtyards, its wells and its byres. See `seat_cluster` for what the wrong number does.
#
# RAISED 92 -> 100 when the SUN CORRIDOR landed (2026-08-13). The pitch was calibrated before the
# rule existed, and a row now needs house depth (28) + yard (~26) + 39 ft of sun + the gaps between
# them, which comes to about 100 rather than 92. Asking the band for less than a row needs does not
# make the cluster tighter - it makes the placer spill the overflow OUTSIDE the band, which is how
# seed 18 grew a two-farm satellite 500 px off the nucleus, 777 px from the nearest water against a
# 760 px reach, with every legal well seat around it already taken by its own two courtyards.
BUNDLE_PITCH = 100.0

# How far below the drain outfall a tameike may stand before the map is better off without one.
# Calibrated against the drawn ponds: an ordinary set-back lands well under 200 px, and the case
# that motivated the limit was 575. See `stage_sink`.
POND_SETBACK_LIMIT = 300.0

# `build_comb`'s GRAIN, and why this tier passes the PRINCIPLED value rather than the pool's.
#
# `grain` scales the carve's real-feet thresholds AND the channel widths. `build_comb`'s docstring
# prescribes `2 / ftpx` so "too narrow to plant" means the same real size at every map scale - 2.0
# for a 1 ft/px hamlet - while every hand-authored hamlet in the pool passes the default 1.0, which
# at this scale means half the real size and half the ditch width. That gap was recorded as an open
# question the first time round. It is now settled by measurement.
#
# WHAT USED TO BLOCK 2.0, AND WHAT FIXED IT (2026-08-12). First the bridge arithmetic: wider
# ditches produced planks and carried-way decks whose abutments stood in the channel, because both
# paths sized a deck from a nominal width rather than from the water actually beneath them. Both
# now measure the crossed water. Second the communal WINDBREAK: at the coarser grain the crop
# shifts enough that a belt derived from the house cloud's EXTREMES lands off a tall narrow cluster
# entirely (measured: 9 clumps, 350 px from the nearest farmhouse). `belt_polygon` samples the
# windward fringe as a PROFILE in columns across the wind instead, so the belt follows the shape of
# the cluster rather than a box around it, and the failure mode is gone.
#
# So this module runs at 2.0 and its cohorts gate clean there. The POOL's hamlets stay at 1.0 until
# someone re-rolls them, which is a real job (every comb map re-rolls, each wants a
# settlement-review) rather than an oversight - `build_comb`'s docstring carries the same account.
GRAIN = 2.0

# THE HAMLET BAND (settlements.md "Scale and density"): 10-20 households, 50-100 inhabitants. Below
# 10 the place is an outlying farmstead or two rather than a hamlet; above ~20 it is a small village
# and grows the features a hamlet must not have (a headman, a shrine, tax-free plots).
HOUSEHOLD_BAND = (10, 20)

# The reference fan, at Ikegami's 15 households: the `build_comb` lengths that produced it. Every
# other size is this fan scaled by a single multiplier (see `fit_field`), so the fan's ASPECT - the
# thing that makes a comb read as a comb - is a constant of the tier and only its area varies.
REF_HOUSEHOLDS = 15
REF_FIELD_FALL = 1150.0
REF_CANAL_A = (1250.0, 1450.0)
REF_CANAL_B = (680.0, 800.0)

# ...and its ASPECT is rolled, which matters more than it sounds. `fit_field` scales the reference
# fan by one multiplier, so without this every hamlet of a given household count and fall direction
# gets the SAME fan silhouette - the review of the first draft found Inashiro's field outline was a
# byte-for-byte translation of Ikegami's, vertex for vertex, because the reference lengths ARE
# Ikegami's and its multiplier came out at 1.0. A cohort of maps that share their largest object is
# a cohort of re-skins. Trading fall length against canal length leaves the AREA alone (so the
# acreage solve is untouched) and changes the shape: a long narrow valley fan against a broad
# shallow one.
FAN_ASPECTS = (0.88, 0.95, 1.0, 1.08, 1.16)

# DELIVERY-DITCH DENSITY by household count. A comb's offtakes are how many delivery ditches drop
# off the supply canal; too many on a small fan waters the same ground twice (build_comb drops the
# redundant near-pairs itself, so an over-dense request is silently thinned - which is worse than
# asking for the right number, because the drawn net then no longer matches the declared one).
# Ikegami's 15 households run a deliberately SPARSE two-offtake net.
# ...and the LAST offtake sits near the canal's end for a reason of its own. Whatever length of
# supply canal runs on past its last delivery ditch is a TAIL, and a tail that ends outside the
# planted extent is runoff dying in bare ground (`watercourse_ends_reach_water`; the gate allows a
# tail that dies at the crop edge, which is what a real canal does - it peters out where the last
# plot it waters ends). Ikegami's authored (0.30, 0.66) leaves a third of the canal as tail and gets
# away with it because its fan happens to be wide there; across a cohort of twenty that came back as
# one dangling collector. A last offtake at ~0.88 - which is also `build_comb`'s own default - keeps
# the tail short and inside the rice.
# ...AND EVERY ROW DRAWS CANAL B (GM caught Inashiro's bare west margin 2026-08-16; researched -
# research/water.md "The head-race forks - supply commands both flanks"). A gravity canal commands
# only the ground BELOW it, and the carve plants paddy on BOTH sides of the bunsuiguchi fork - so
# the hamlet rows' old offtakes_b=() (copied from Ikegami's authored choice, now a frozen exhibit)
# left the whole canal-B flank carved as watered ground with no drawn water: the modeled net and
# the inked net disagreed, exactly the failure the paragraph above warns about. One offtake at
# ~0.55 inks the second arm partway down its margin, tapering to a thread (Minuma-dai divides its
# head into TWO margin canals; the Isawa fan's canals radiate from the fan head). Gated by
# comb_supply_commands_both_flanks.
OFFTAKE_LADDER: tuple[tuple[int, tuple[float, ...], tuple[float, ...]], ...] = (
    (11, (0.36, 0.93), (0.55,)),
    (21, (0.30, 0.62, 0.93), (0.55,)),
    (99, (0.26, 0.52, 0.78, 0.93), (0.6,)),
)

# The fall bearings a rolled hamlet may sit on: the eight compass points, in the engine's screen
# convention (0 = east, 90 = south). The GM's water-flow doctrine says the bearing is a fact about
# the REGIONAL terrain and should be reasoned from the range the settlement sits under - a script
# cannot know that, so an unpinned bearing is ROLLED and the spec always lets the GM pin the real
# one. The roll exists so a cohort varies, not because a rolled bearing is as good as a known one.
FALL_BEARINGS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
CARDINAL_BEARINGS = (0.0, 90.0, 180.0, 270.0)  # the survey grid a polder is laid to; see plan_site

# WHICH WAY THE COLD WIND COMES FROM - and why it is DERIVED from the slope rather than rolled.
#
# The engine's default is NW, the East Asian winter monsoon, and at the scale of a province that is
# the right answer. At the scale of ONE VALLEY it is not the whole answer, because the wind a
# settlement actually shelters from is the local one, and the local one follows the ground: cold air
# is dense, it pools on the high ground overnight and DRAINS DOWNHILL (the katabatic / mountain
# breeze), so in a valley the cold night wind comes off the high side. That is why the doctrine
# 背山面水 - back to the hill, face the water - shelters a settlement at all: the hill is both the
# high side AND the windward side, and they are the same fact rather than two that happen to agree.
#
# So the windward quarter is the UPSLOPE bearing, turned by a rolled 45 degrees either way (real
# terrain is not a smooth ramp and the wind follows the valley's own line, not the field's fall) and
# snapped to a compass quarter. `HamletSpec.windward` pins the regional answer when the GM knows it.
#
# THIS ALSO FIXED A REAL DEFECT, which is how it was found. Rolling the wind independently produced
# maps whose wind and slope disagreed - and the cluster is seated by BOTH (its back to the wind, its
# feet out of the wet), so on a map where they pointed opposite ways the wind term won and the
# settlement was seated at the field's drain outfall, among the drainage ditch and the tameike. That
# is three gate failures (a structure on a channel, a bridge on an oblique crossing, dwellings in
# the wet toe) with one cause: two facts about the same landscape, rolled as if they were unrelated.
WIND_TURNS = (-45.0, 0.0, 0.0, 45.0)

WIND_VECTORS: dict[str, Pt] = {
    "N": (0.0, -1.0),
    "NE": (0.7071, -0.7071),
    "E": (1.0, 0.0),
    "SE": (0.7071, 0.7071),
    "S": (0.0, 1.0),
    "SW": (-0.7071, 0.7071),
    "W": (-1.0, 0.0),
    "NW": (-0.7071, -0.7071),
}

# WHERE THE FIELD'S RUNOFF GOES. Both are ordinary; the GM's brief names both in one breath ("the
# drainage ditch feeds into a pond, though it could just as easily have run off the edge of the map
# with the understanding that that would have somewhere off map fed into a stream"). `pond` is the
# tameike reservoir at the low foot - the Ikegami case, and the one that gives the map a named
# feature; `offmap` lets the drain brook leave the frame, which is what most real valleys do.
SINKS = ("pond", "pond", "offmap")

CLUSTER_SHAPES = ("round", "round", "elongated", "crescent")
LANE_SKELETONS = ("spine", "T", "Y", "cross")
PLOT_SIZES = ("small_irregular", "medium", "medium", "large_block")
GRAIN_DRIFTS = (-8, -4, 0, 0, 4, 8)
