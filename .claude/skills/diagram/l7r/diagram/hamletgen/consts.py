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
# candidate's CENTER against the corridor and the placer passed the farmhouse's BASE rect (46 x 28
# ft), while a homestead's wealth variation renders the house up to ~1.33x that - so at 32 a
# well-off farmhouse's drawn corner ended 2.4 px from a connector track's centerline with its center
# a legal 34 px off, and `houses_clear_of_lanes` measures the DRAWN corners.
#
# THE WORKAROUND IS OVER (feature 121, 2026-08-17), and this is no longer what keeps a house off a
# lane. The bundle path now tests the rect it will DRAW against the lane's drawn tread
# (`_house_on_a_tread`), and the gate reads the same raked corners (`rect_corners`), so a seat that
# would put a wall on the trodden surface is refused on its own geometry whatever this number says.
# CORRECTNESS LIVES IN THE TREAD TEST; this constant is now only a PLACEMENT preference - how far
# out seats are offered, so houses FRONT the lane instead of crowding it.
#
# THE OLD DIAGNOSIS WAS WRONG, so do not restore it from an old copy of this comment. It said the
# drawn house "is offset from the seed point AND scaled by the wealth/length jitter - so the rect
# the placer clears is neither the size nor the position of the rect the map draws." Measured across
# pool/hamlets/inashiro.json: position and size match the drawn record to 0.0000 px. The divergence
# was the RAKE (`_house_rot`, +/-5 deg, up to 2.56 px of corner bulge) - and separately, 32 was the
# PLAIN house's arithmetic while the nucleated path jitters a minka's length to 1.35x, because a
# minka grew by adding bays along the ridge.
#
# DERIVED, at 1 ft/px: longest drawn minka 62.1 x 30.8 ft -> half-diagonal 34.7, plus the lane's own
# half-tread (a ~10 ft tread -> 5), = 39.7 -> 40. Measured on the 24-seed cohort: 22/24 at 40, with
# the same two pre-existing failures on the same two seeds as the 48 baseline - so the 8 ft this
# returns to the cluster costs nothing. (At 32 the cohort drops to 21/24: the lane checks stay
# green, but a corridor that tight re-packs the cluster into gardens and crops.)
LANE_CLEARANCE = 40.0

# HOW FAR ALONG THE FIELD OUTLINE THE CLUSTER ACTUALLY REACHES, as a multiple of the seat band's own
# lateral half-extent. ONE definition, read by `front_row` (which samples outline vertices out to
# this reach) and by `stage_seat` (which sizes the seat band). The lane skeleton is no longer sized
# over it at all - feature 128 moved every lane after the houses, so the skeleton is fitted to where
# they actually landed rather than to this predicted band.
#
# It is one definition because the two being separate numbers WAS the defect. `front_row` had 1.6
# inline and the skeleton was sized on the bare `lat`, so the lanes huddled in the middle of a
# cluster 1.6x longer than they were, and the houses at the ends had nothing near them. Measured on
# the four pool hamlets before the fix: every one of the 25 unserved farmhouses sat at a large
# offset along the cluster's LONG axis (up to 478 ft), and none at a large offset across it - a
# lateral coverage failure, not the depth failure the ledger had assumed. See
# specs/123-lane-web-and-cluster-shape/research.md R2.
CLUSTER_SPAN_FACTOR = 1.6

CLUSTER_ROW_SPAN = {"round": 1.2, "crescent": 1.6, "elongated": 2.6, "split": 1.6}
"""How far the FRONT ROW wraps along the field outline, per rolled `cluster_shape`, as a multiple of
the seat band's own half-length.

The band aspect (`CLUSTER_BAND_ASPECT`) was not enough on its own, and the measurement says why:
with the band alone, Kashikawa declared `elongated` and DREW 1.2:1, because the row wraps 1.6x past
the band in every direction and the lane-frontage pass then fills behind it. A declaration that does
not describe the drawing is the exact failure the old stamping guard existed to prevent, so binding
the shape at the band and declaring it unconditionally without this would have reintroduced it in a
worse form - the knob would read as honored on every map while changing almost nothing.

So the shape governs the ROW's reach too: a round hamlet keeps its row short and packs depth behind
it, an elongated one strings along the margin. Crescent keeps 1.6, the value every map used before,
so a crescent map is unchanged. `ways.py` keeps reading the plain `CLUSTER_SPAN_FACTOR` for the lane
frame - that frame spans the houses that actually landed, which is a different question."""

# THE NO-BUILD CORRIDOR OF A WEB LANE, in feet - deliberately much tighter than LANE_CLEARANCE.
#
# LANE_CLEARANCE (40) is derived for a lane the homesteads FRONT: it is the drawn minka's
# half-diagonal plus the lane's own half-tread, so the steading clears the way it faces. A web lane
# is the other kind: the research describes the lateral ones as "colonized as semi private space by
# the adjoining house", which is a way people build right up against. Holding 40 ft off both verges
# of every web lane reserved the middle of the cluster and pushed the houses out - measured on the
# four pool hamlets, the long axis grew 51%, 58%, 15% and 97%. This is the lane's own half-tread
# plus a hand's breadth: enough that a wall is not drawn ON the tread, and no more.
WEB_CLEARANCE = 28.0

# THE LEAST ROOM BETWEEN TWO STEADINGS A WEB LANE WILL THREAD, in feet. `web_cuts` only cuts where a
# gap is at least this wide, so a lane is placed where one can actually be walked rather than driven
# through a wall and left to the clipper to sort out. Three feet of tread plus a hand's breadth on
# each side, doubled for the two neighbors: a person with a carrying pole, which is the traffic these
# lanes were for (see settlements/ways.md - the vehicle to picture is the wheelbarrow and the
# shoulder-pole porter, never a cart).
#
# NOTE ON WEB_CLEARANCE ABOVE, because the number moved twice and the reason changed with it. While
# the web was laid BEFORE the houses, a wide corridor was ruinous - it reserved the middle of the
# cluster and the placer shoved the houses out, growing the four pool hamlets' long axes by 15-97%.
# Laid AFTER them (see `stage_web`) the corridor no longer competes with a single farmhouse, because
# every farmhouse is already seated; all it still governs is what `stage_appurtenances` puts down
# NEXT - byres, sheds, wells. At 12 those were landing on the tread and `features_do_not_overlap`
# fired on 7 of 24 cohort seeds. 28 holds a byre off the way while staying well under the 40 ft a
# fronting lane reserves, which is the distinction the two constants exist to keep.

# HOW FAR A WEB LANE'S CENTERLINE STAYS OFF THE SETTLEMENT'S OWN FABRIC, in feet.
#
# It has to clear the overlap MATRIX, not just the drawing, and the matrix is less forgiving than it
# looks: it sizes EVERY lane at 6 ft wide whatever the record says (`_MX_LINE_W`), so a 3 px web
# tread is judged as a 3 ft half-width; and a dooryard garden records both a `poly` and a rect, with
# the rect running up to ~2.3 ft proud of the poly. At 6 ft of margin that leaves well under a foot
# of true clearance, and `features_do_not_overlap` fired on `lanes` vs `gardens` across the cohort.
# It was 9 while the fabric list carried only a garden's `poly`. Now that `_homestead_polys` records
# the RECT as well, the discrepancy is covered by the geometry instead of by the margin, and 9 was
# doing a second job it should not have been: `MIN_WEB_GAP` says a 16 ft gap between two steadings is
# walkable, while a 9 ft margin needs 18 - so the cut solver offered gaps the router could not
# thread, and a house sat 296 ft from any way with no route found at all. The two are now derived
# from each other and cannot contradict again.
WEB_FABRIC_GAP = 7.0

# HOW FAR A TRACK KEEPS OFF A STEADING, as opposed to how far the WEB does (feature 128).
#
# `WEB_FABRIC_GAP` is 7 px because an alley IS the residual gap between two plots - it threads
# between them and is barely wider than the space it occupies. A connector or a field spur is a
# different animal: it runs PAST the settlement rather than through it, and it has no business
# hugging a wall.
#
# 16 px is derived, not chosen. The gate counts a house-on-corridor hit at
# `seg_dist(house_center, lane) < 14` (`houses_off_corridors`), and a clip measures to the FOOTPRINT
# rather than the center - so a 7 px clip left the center 14-17 px out and 3 of the reference
# hamlet's 15 houses failed. 16 px to the footprint puts the center comfortably past 14 with the
# margin coming from the house's own half-extent.
#
# NOT LARGER, and feature 126 recorded why: it clipped its skeleton arms at 20 px, which demands a
# 40 px clear corridor between two steadings that a packed cluster does not have, so arms were
# clipped out of existence entirely. A track only needs to reach the cluster's edge, not thread it.
TRACK_FABRIC_GAP = 16.0

# A FOOTPATH IS NOT A LANE, and it may squeeze where a lane may not. This is the clearance for the
# path from an outlying steading's door to the nearest way - the thing the sources describe as
# "colonized as semi private space by the adjoining house", i.e. the residual room between two
# plots, walked in single file. It still clears the overlap matrix's 3 ft half-tread with room over,
# but it lets a path thread a gap a back lane could not, which is the difference between a house
# being reached and a house being 296 ft from anything with no route at all.
# 4 ft, and the number is doing real work at the margin. The overlap matrix sizes every lane at 6 ft
# wide whatever its record says, so 3 ft is the hard floor and this is 3 plus a hand's breadth; the
# drawn tread is 3 px, so the ink clears a wall by better than two of its own widths. At 5 a hemmed-in
# farmstead on cohort seed 41 had no route to the network at all, at any target - the gaps between
# its neighbors' plots were simply narrower than a lane-and-two-margins. A footpath is the one way on
# the map that is walked in single file, and this is the width that says so.
FOOTPATH_FABRIC_GAP = 4.0

# HOW FAR A WEB LANE STAYS OFF THE CROP, THE TOE AND THE MARSH, in feet.
#
# The skeleton's arms are clipped at 20, which is right for them: they are 5-6 px cart ways and they
# are laid before anything else, so there is no cost to being generous. A web lane is 3 px and is
# threading ground that is already full, and 20 was not a rule, it was a copied default - the gate's
# own bar is `fields_clear_of_road`, which allows w/2 + 2, i.e. about 3.5 ft for a tread this narrow.
# Measured cost of the copied 20: a farmstead 251 ft from its nearest neighbor had NO route to the
# network at all, not because any single obstacle blocked it but because the crop, the toe and the
# marsh each took 20 ft off the same corridor and closed it between them. 8 keeps better than double
# the gate's bar while leaving a path somewhere to go. It also matches the doctrine: a real farm
# track runs on the baulk between plots, not twenty feet clear of the rice.
WEB_HARD_GAP = 8.0

# HOW CLOSE TWO WAYS MAY RUN BEFORE A READER SEES ONE WAY DRAWN TWICE, in feet.
#
# This is a LEGIBILITY number, not a clearance: `MIN_WEB_GAP` says what a lane can squeeze through,
# and using it here was a category error that let a back lane share a corridor with the connector -
# median 14.6 ft apart, 91% of its length within 30 ft - without the shadow test firing once. A
# review read the pair as "a long thin scissors with a drafting overlap". 30 ft is a third of a
# bundle pitch: far enough apart that the eye separates them at fit zoom.
WEB_SHADOW_FT = 30.0

MIN_WEB_GAP = 2.0 * WEB_FABRIC_GAP + 4.0  # 18 ft: both neighbors' clearance, plus the tread between them

# THE REACH A FARMHOUSE IS ENTITLED TO: every house center must be within this of some drawn way
# (`farmhouses_reach_a_way`). It is BUNDLE_PITCH, deliberately and by reference rather than by
# repetition - the ground one homestead occupies is exactly the distance at which a lane passes your
# own plot or your neighbor's, which is what the sources mean by a lateral "colonized as semi-private
# space by the adjoining house". The same number sets the web's lane spacing, so the requirement and
# the geometry that satisfies it cannot drift apart.
#
# Grounding: research/homesteads.md, "Is every farmhouse reached by a lane, and in what FORM?" - the
# record is decisive that a house in a nucleated cluster IS reached by a way. The previous 90 ft in
# `lanes_reach_something` was flagged in future-work/ as a number nobody had justified; this one is
# derived from a researched constant instead of chosen to make today's maps pass.
WEB_REACH_FT = 100.0  # == BUNDLE_PITCH; asserted in tests rather than imported, since BUNDLE_PITCH is defined below

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
# A bundle's reserved rects come to ~71 x 57 ft. 92 px per household leaves the cluster dense enough
# to read as a nucleus and open enough for its courtyards, its wells and its byres. See
# `seat_cluster` for what the wrong number does.
#
# ASKED vs ACHIEVED - do NOT lower this to "recover" the difference (feature 121, 2026-08-17). This
# comment used to run the two together: the placer keeps bundles apart by circumscribed circles
# rather than real footprints, "so the effective pitch is larger again". True, and it is the
# ACHIEVED pitch that the circle inflates, not this number. Retiring the circle closes that gap by
# itself - the cluster lands at the pitch it asks for instead of overshooting it.
#
# THIS NUMBER IS HISTORICALLY GROUNDED, which is why it survives the fix unchanged: the spacing of
# farmsteads in a nucleated wet-rice village is set by the THRESHING YARD'S SUN, not by how tightly
# buildings can be packed. Rice dries on the niwa, so a yard needs clear ground to its south; a
# kayabuki thatch must be pitched 45 deg or steeper to shed rain, putting the ridge ~20 ft up, and
# at 38N in the 10th month that throws 39 ft of shadow by 9am. Lowering the asked pitch would put
# houses inside each other's drying shadow - a defect against the rule, arriving disguised as a
# density win. (research/homesteads.md, "The threshing yard's sun"; specs/121 research.md D2.)
#
# THE HONEST WAY TO GET MORE DENSITY HERE is what real yashiki lots did: STAGGER east-west rather
# than space rows further apart.
#
# THAT IS NOW DONE, and this comment used to end "the placer is free to; nothing asks it to yet",
# which was stale and cost feature 126 a user story before anyone read the placer instead of the
# comment. Three mechanisms already deliver it, and re-deriving a fourth would be a second
# implementation of a rule the checker owns:
#   - `_sun_corridor_ok` keeps SUN_CORRIDOR_FT (39) of open ground SOUTH of every threshing yard,
#     in BOTH directions between neighbors, and `yards_unshaded_by_neighbors` gates it;
#   - `_yard_sun_conflict` and `_garden_shaded` extend the same rule to groves and dooryard gardens;
#   - feature 121 retired the circumscribed-circle spacing for real rotated footprints, and
#     `_house_too_near_a_neighbor` is an eave-drip rule of a couple of feet, not a sun rule.
# So THIS number is a ROW-PLANNING pitch and nothing else: nothing pays 100 ft east-west. See
# specs/126-derived-lanes-and-form/research.md R8.
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

CLUSTER_BAND_ASPECT = {"round": 2.2, "crescent": 3.0, "elongated": 5.0, "split": 3.0}
"""How long the cluster BAND is against how deep, per rolled `cluster_shape`.

THE KNOB WAS DEAD UNTIL THIS TABLE EXISTED (2026-08-19). `cluster_shape` is rolled per settlement
and printed in every cohort-audit header, and it fed exactly one thing: `cluster_seeds`, the CLOUD
pass, which runs only for households the front rows do not seat. Census: on all 48 cohort seeds and
all four pool hamlets the rows plus lane frontage seat EVERY house, the cloud never runs, and
`meta.cluster_shape` is stamped on none of them - so round, elongated and crescent all drew the
same 3:1 band. A peer session found it while retracting a result that had blamed the knob for a
placement failure; the knob could not have caused anything, because nothing read it.

The band is where the shape has to bind, because the band is what the front rows are seated along.
Area is HELD (`households * BUNDLE_PITCH^2`, the ground a homestead actually takes), so only the
ratio moves and no settlement gains or loses room by its shape. The 3.0 that was hardcoded here is
kept as the crescent/split value, so a crescent map is byte-identical to what it drew before and the
change is visible only where it should be.

Depth floors at 112 px, so a small round hamlet reads well under its band figure and a small
elongated one is pushed toward 2.5:1 rather than 5:1 - the floor is a real minimum (a band shallower
than that cannot hold a homestead bundle and its yard), and letting it compress the extremes is
honester than pretending a 10-household string can be five times longer than it is deep.

ROUND'S BAND IS 2.2/1.2, AND WHAT IT BUYS IS HONESTY RATHER THAN ROUNDNESS. Say the limit plainly: on
the rotation-aware measure, round rolls draw a MEAN 2.48 aspect against a 2.0 ceiling, so `round` is
declared on 5 of 21 cohort rolls and recorded `cluster_shape_unhonored` on the rest. The knob does not
make a round hamlet round; it reports truthfully that most of them are not.

That is a smaller claim than an earlier version of this docstring made, and the earlier one was wrong
for an instructive reason: it rested on the AXIS-ALIGNED aspect, which cannot see a diagonal band (see
`cluster_aspect`). Measured on the honest metric across the full 48, the trade is:

    2.2/1.2 -> 43/48, ZERO regressions, round honored  5/21, mean 2.48   <- shipped
    1.5/0.9 -> 42/48, ONE regression (seed 34), honored 12/21, mean 1.86
    1.2/0.8 -> 38/48, four regressions,          honored 20/21, mean 1.50

**THE WALL IS `lane_ends_front_different_houses` (0611), AND IT IS CORRECT.** The session that owns it
ruled on this exact question: two lane ends within 60 ft pointing within 25 degrees are a fork serving
one steading, so a cluster tight enough to produce that is too tight. Do not weaken 0611 to buy a
rounder cluster; Principle XIII forbids shipping the regression anyway.

WHAT THIS MEANS ARCHITECTURALLY, and it is the finding worth more than the number: at hamlet scale the
LANE SKELETON AND FRONTAGE dominate cluster shape, and the band aspect is a weak lever pulling against
them. The front rows and `lane_frontage` seat every household on 47 of 48 seeds, along a margin whose
bearing the field chose - so the cluster's proportion is mostly a consequence of the field edge, not of
this table. A genuinely round hamlet needs the SKELETON to be shape-aware (a T laid compactly rather
than spread), which is untried for SHAPE - note that it was tried and falsified for REACH, which is a
different question. That, not a smaller number here, is the next real lever."""

CLUSTER_DRAWN_ASPECT = {"round": (1.0, 2.0), "crescent": (1.9, 4.2), "elongated": (2.8, 12.0), "split": (1.9, 4.2)}
"""What the FINISHED cluster's long:short ratio must fall inside for a rolled shape to be declared.

THIS IS NOT `CLUSTER_BAND_ASPECT`, AND CONFLATING THE TWO WAS A BUG (caught 2026-08-19, in the sweep
that chose the round value). The band aspect is a MECHANISM parameter - the proportions of the seat
band the front rows are laid along. The drawn aspect is an OBSERVABLE - the bounding box of where the
houses actually ended up. They are not the same quantity and they do not even track each other
closely: at `CLUSTER_BAND_ASPECT["round"] = 2.2` the five swept seeds drew 1.01, 1.07, 1.17, 1.76 and
2.21, because the front row wraps and the rows stack, so a 2.2:1 band routinely yields a ~1:1 cluster.

The first honesty guard compared the drawn aspect directly against the band parameter and passed only
because its tolerance was wide enough to swallow the mismatch - one seed sat 1.19 outside a 1.2
tolerance and was declared honored on what was effectively a rounding accident. That is this
project's most-repeated defect wearing yet another hat: A CHECK AND THE THING IT CHECKS MEASURING
DIFFERENT QUANTITIES. So the guard now tests the observable against these ranges, which are stated in
the observable's own units and can be read off a finished map with a ruler.

ROUND'S CEILING IS 2.0, AND IT COMES FROM THE HAND-AUTHORED MAPS rather than from taste. Those 19 are
frozen exhibits drawn by eye before any of this machinery existed, so they are the only visual ground
truth the project has for what a word means. Measured on the rotation-aware aspect, the ones a reviewer
reads as a round clump sit at **1.24 / 1.29 / 1.38 / 1.80** (moritono, honda, ikegami, shimizu) and the
ones read as a string sit at **2.42 / 3.52 / 3.72 / 4.26** (tanada, kuwabata, enokida, yatsuda). The gap
between 1.80 and 2.42 is where the word changes, so 2.0 sits in it.

The first cut of this table said 2.4, which was calibrated against the AXIS-ALIGNED measure and is
inside the string band on the honest one - so it would have honored `round` on clusters that plainly
read as ribbons. The ceiling and the measure had to be fixed together; fixing either alone leaves the
rule wrong.

The ranges are wide on purpose. They are not a target the generator aims at; they are the band inside
which a reader looking at the sheet would agree with the word. `round` tops out at 2.4 because past
that a clump reads as a string; `crescent` starts at 1.9 and `elongated` at 2.8, overlapping
deliberately, because the difference between those two at the margin is the CURVE of the band and not
its ratio, and this rule is not the place to adjudicate curvature. The upper bound of 12.0 on
`elongated` is a sanity rail, not a shape statement.

Kept in step with the gate's own copy in `check_village/segments_04c_groves_and_shading.py` by
`tests/hamletgen/test_cluster_shape.py` - the gate may not import the generator, so the table is
duplicated, and a duplicated table with no pin is a table that drifts."""
LANE_SKELETONS = ("spine", "T", "Y", "cross")
# The two attested forms of making every house reachable. NOT weighted: the research supports both
# equally, so an even roll is the honest one, and the two read differently enough at a glance
# (a laid-out double row vs. a grown spine-and-alleys) to be worth a full half of the cohort each.
LANE_WEBS = ("alleys", "back_lane")
# THE SETTLEMENT FORM - which KIND of settlement this is, not merely what shape its cluster takes.
# Three forms, and the roll is DELIBERATELY flatter than real-world frequency would be. Read that
# sentence twice before re-weighting this tuple, because the departure is the decision.
#
# What the research supports (research/homesteads.md, "Does a hamlet have to be NUCLEATED at all?"):
#   - nucleated  - the default across wet-rice East Asia, because paddy is too valuable to build on,
#                  so households cluster on whatever ground will not grow rice. The access rule
#                  (`farmhouses_reach_a_way`) is decisive for THIS form and no other.
#   - dispersed  - the Tonami plain's 7,000 farmhouses over 220 km2, each in its own kainyo grove.
#                  Arises where an alluvial fan drains too well for paddy, so water control is
#                  per-holding and the farmer lives on the holding. Our comb field IS such a fan.
#   - linear     - the row village: farmsteads either side of a through-track, each holding behind
#                  its own house. Weakest-attested of the three in the English-language record, so
#                  it draws least - but not so rarely that the cohort stops exercising it.
#
# THE DEPARTURE, recorded per the project's calibrated-liberty rule: in the real world nucleated
# would dominate far more heavily than 50% - Tonami is famous precisely BECAUSE dispersal is
# regionally unusual. These maps exist to be told apart at a glance ("settlements which are within
# historical norms while being as different from one another as is justifiable"), and each form here
# is individually inside the norms; it is the FREQUENCY that is flattened, which is the liberty a
# DEGREE-along-a-continuum may take. Weighting to true frequency would make two of the three forms
# vanishingly rare, untested by the cohort, and pointless to have built.
# HOW FAR A NON-NUCLEATED FARMHOUSE MAY STAND FROM ITS FIELD, in px.
#
# MIRRORS THE GATE, deliberately and by the same number. `all_houses_field_adjacent` (segment 0232)
# has two branches: a NUCLEATED cluster is allowed `ADJ + 2 * span` - the cluster's own diameter of
# slack, because a nucleus legitimately has a back rank - while every other form gets a flat `ADJ`
# of 165 px with no allowance at all. That asymmetry is right, and it is the research rather than
# the checker talking: a Tonami farmstead stands in the MIDDLE of its own holding, and a row
# village's fields lie directly behind each house, so neither form has a back rank to excuse.
#
# The placer needs the same figure because it is the placer that decides. Left to the cloud pass,
# dispersed and linear maps put houses a median 164 and 208 px out (against the baseline's 144 and
# 145) and failed the check - which was the generator being wrong about the form, not the check
# being wrong about the map.
FIELD_ADJ_PX = 165.0

# ROLLED TO NUCLEATED ONLY, FOR NOW - and the weights above are what to restore, not to re-derive.
#
# Feature 126 built everything the other two forms need: the research (research/homesteads.md), the
# knob, the form-conditional access checks, the corrected field-adjacency branch, and per-form
# seating. What it did NOT build is a per-house GROVE that behaves. That path had never been
# exercised by the scripted tier - it was written for hand-authored dispersed maps - and switching
# it on surfaces four latent defects at once, measured on the in-gate ratchet seeds:
#
#   seed 42 (linear):    groves_clear_of_lanes, groves_on_windward_side, gardens_unshaded_from_east
#   seed 43 (dispersed): groves_clear_of_structures, structures_clear_of_trees (groves over byres),
#                        gardens_unshaded_from_east, and 12 of 14 households seated
#
# MECHANISM, as far as it was traced: a yashikirin is part of the BUNDLE and is planted at seat
# time, but it is tested only by `_rect_blocked` (keep-out polygons). It is not tested against lane
# treads, against byres seated later in `stage_appurtenances`, or for the garden's morning sun. Two
# fixes were tried and MEASURED NOT TO HELP, so do not repeat them: adding `groves` to the lane
# fabric in `_homestead_polys`, and giving the grove rects the house's own `_house_on_a_tread` test.
# Both are kept because they are correct in themselves; neither moved the ratchet.
#
# SKETCH for the follow-up: the grove needs the same treatment the HOUSE already has - a
# footprint-level fit test covering treads, later-seated fixtures and the east-sun rule - which
# probably means groves stop being seated with the bundle and become a deferred pass after the
# appurtenances, in the same way canopies are already deferred to the flush.
#
# Until then the generator emits only the form it can draw correctly. This is a WEIGHTS change and
# nothing else: every other part of the knob is live and tested, so restoring the line below is the
# whole of turning the other forms back on.
SETTLEMENT_FORMS = ("nucleated",)
_SETTLEMENT_FORMS_WHEN_GROVES_WORK = ("nucleated", "nucleated", "nucleated", "nucleated", "nucleated", "dispersed", "dispersed", "dispersed", "linear", "linear")

PLOT_SIZES = ("small_irregular", "medium", "medium", "large_block")
GRAIN_DRIFTS = (-8, -4, 0, 0, 4, 8)
