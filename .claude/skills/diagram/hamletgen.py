#!/usr/bin/env python3
"""SCRIPTED HAMLET GENERATION - the experiment (GM 2026-08-11).

WHAT THIS IS. A Mode B hamlet map is currently AUTHORED: a session writes a `.gen.py` by hand,
choosing the canvas, the sluice, the cluster center, the lane polylines, the pond rectangle, the
woodland patches and the windbreak belt as literal coordinates, then iterates against
`check_village.py` until the gate is green. That works, and it is slow. This module asks the GM's
question - "could a script do each of those steps instead?" - and answers it for the SIMPLEST tier,
the rice-farming hamlet, with `pool/hamlets/ikegami.gen.py` as the reference subject.

IT DOES NOT REPLACE ANYTHING. Nothing here is imported by `settlement.py`, `check_village.py`,
`waterfields.py` or any pool generator, and no existing map changes by a byte. It is additive: a
new module, its own tests, and its own demo maps under `pool/experiments/`. Delete the module and
that folder and the current method is exactly as it was.

WHAT IT IS NOT. It is not the knob engine - `Settlement.roll_village` (feature 005) already rolls a
gate-passing hamlet from a seed, and Honda and Shimizu in `pool/hamlets/` are the proof. This module
STANDS ON that work and closes the gap between what it produces and what a hand-authored map like
Ikegami contains, which is where the interesting engineering turned out to be:

  | Ikegami (authored)                 | roll_village          | here                            |
  |------------------------------------|-----------------------|---------------------------------|
  | drainage tameike at the low foot    | source pond only      | DERIVED from the drain outfall  |
  | a connector track running off-map   | none                  | DERIVED, steered clear of crops |
  | managed-woodland patches            | none                  | DERIVED by an open-ground scan  |
  | draft byres among the homesteads    | none                  | drawn                           |
  | field sized to the household count  | a hand-passed `fall`  | SOLVED for, to a real acreage   |
  | cluster with its back to the wind   | a lateral margin band | seated on the 背山面水 margin     |

THE ORDER IS THE DESIGN. `STAGES` below is the pipeline, and it is the same order a human follows
and the same order the engine's DRAW ORDER map (skill CLAUDE.md) requires - water, then the field
the water shapes, then the sink the field drains to, then the ways, then the homesteads that front
the ways, then their appurtenances, then ground cover, then the woods, then the frame. Each stage is
a module-level function of `(s, plan)`, so the sequence is readable in one place and every stage is
separately testable.

DERIVE, NEVER PIN. Every position in this module is computed from geometry that is already on the
map: the cluster from the field envelope's margins, the pond from the drain's last vertex, the
connector from the lane skeleton's gateway, the woodland from a scan of what ground is still open,
the windbreak from the houses that actually landed. That is the project's standing rule (a pinned
coordinate silently becomes false when the thing it referenced moves), and it is also what makes a
SCRIPT possible at all: a stage that reads the map can run at any size, seed or fall direction.

THE CHECKS ARE THE ORACLE, NOT A POST-HOC AUDIT. `generate()` runs `check_village.gate()` in-process
on the manifest it just built and returns the failures with the map. The GM asked whether the checks
should run per-placement or per-round: per-ROUND is right, and the reason is structural. The placer
(`Settlement._fits` and friends) already refuses an overlapping seat, so the overlap checks are a
formality that should never fire - running them after each house would cost a full gate per house to
re-prove something placement guarantees. What the gate actually catches is EMERGENT: acreage against
household count, a marsh that ended up uphill, a windbreak on the lee side, a connector that stopped
short of the edge. Those are properties of a FINISHED map, so they are checked once, on the finished
map. Where a stage can fail locally and recover (the cluster not seating every household) it retries
INSIDE the stage against the placer's own verdict, which is cheaper and more precise than a gate run.

Run it:
    python3 hamletgen.py --name Ikegami-scripted --seed 4 --households 15 --out pool/experiments/x
    python3 hamletgen.py --batch 12          # roll a whole cohort and gate every one
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:  # so the module works when run as a script from anywhere
    sys.path.insert(0, HERE)  # pragma: no cover - under pytest the skill dir is already on the path

from settlement import Settlement, knob_rng, point_in_poly, seg_closest, seg_dist, seg_intersect, segments_cross, skeleton_layout  # noqa: E402
from waterfields import build_comb  # noqa: E402

Pt = tuple[float, float]
Poly = list[Pt]

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

SQ_FT_PER_ACRE = 43560.0

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
# either side. 14 px is the smallest set-back that keeps every cohort map's tip out of the standing
# water, and it is still under a farmhouse's width, so the track visibly reaches the field.
SPUR_SETBACK = 14.0

# How much open ground a threshing yard needs to its SOUTH, in feet. A thatched roof is pitched 45
# degrees or steeper, so the 46 x 28 ft minka's ridge stands ~20 ft up; at 38N in the threshing
# month that is 21 ft of shadow at noon and 39 ft by 9am. 39 protects the 9-to-3 drying day, which
# is the one that matters - and it costs nothing in row pitch, since house depth (28) + yard depth
# (~26) + 39 already comes to about the 92 ft the cluster band was independently sized at.
SUN_CORRIDOR_FT = 39.0

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
OFFTAKE_LADDER: tuple[tuple[int, tuple[float, ...], tuple[float, ...]], ...] = (
    (11, (0.36, 0.93), ()),
    (21, (0.30, 0.62, 0.93), ()),
    (99, (0.26, 0.52, 0.78, 0.93), (0.6,)),
)

# The fall bearings a rolled hamlet may sit on: the eight compass points, in the engine's screen
# convention (0 = east, 90 = south). The GM's water-flow doctrine says the bearing is a fact about
# the REGIONAL terrain and should be reasoned from the range the settlement sits under - a script
# cannot know that, so an unpinned bearing is ROLLED and the spec always lets the GM pin the real
# one. The roll exists so a cohort varies, not because a rolled bearing is as good as a known one.
FALL_BEARINGS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)

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


# ---- the spec and the derived plan --------------------------------------------------------------


@dataclass(frozen=True)
class HamletSpec:
    """WHAT THE GM DECLARES. Everything optional is rolled from `seed`; everything given is honored.

    The split is deliberate and is the whole ergonomic claim of the experiment: the REQUIRED fields
    are the facts only a person knows (what the place is called, how big it is, and - when the
    surrounding geography is settled - which way its water runs), and everything that follows from
    those is the script's job. A spec of `HamletSpec("Ikegami", seed=4, households=15)` is a
    complete, gate-passing hamlet."""

    name: str
    seed: int
    households: int = REF_HOUSEHOLDS
    # The landscape facts. `down_deg` is the LAND's fall and `water_flow` the drainage BEARING; the
    # skill's rule is that these are two different facts and must not be derived from each other, so
    # they are two fields. A hamlet's single comb drains down its own fall, so when only one is
    # given the other follows it - that is a statement about a one-field hamlet, not a general rule.
    down_deg: float | None = None
    water_flow: float | None = None
    windward: str | None = None
    # The rolled knobs, pinnable.
    water_sink: str | None = None
    cluster_shape: str | None = None
    lane_skeleton: str | None = None
    plot_size: str | None = None
    grain_drift: int | None = None
    woodland_patches: int | None = None
    # Passed through to the engine's own knob catalog (`Settlement.pin_knob`).
    pins: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        lo, hi = HOUSEHOLD_BAND
        if not lo <= self.households <= hi:
            raise ValueError(
                f"{self.households} households is outside the hamlet band {lo}-{hi} - a smaller place is an outlying farmstead, a larger one is a village (which needs a headman, a shrine and tax-free plots this generator does not draw)"
            )
        if self.windward is not None and self.windward not in WIND_VECTORS:
            raise ValueError(f"windward {self.windward!r} is not a compass quarter: {sorted(WIND_VECTORS)}")
        if self.water_sink is not None and self.water_sink not in ("pond", "offmap"):
            raise ValueError(f"water_sink {self.water_sink!r} must be 'pond' (a tameike below the fields) or 'offmap' (the drain brook leaves the frame)")


@dataclass
class SitePlan:
    """THE DERIVED PLAN - everything decided before a single shape is drawn.

    Separating this from `build` is what makes the generator testable without rendering: `plan_site`
    is pure, so the sizing arithmetic, the knob rolls and the canvas derivation can be asserted
    directly, and a stage that misbehaves can be handed a hand-made plan."""

    spec: HamletSpec
    down_deg: float
    water_flow: float
    windward: str
    water_sink: str
    cluster_shape: str
    lane_skeleton: str
    plot_size: str
    grain_drift: int
    woodland_patches: int
    fan_aspect: float
    target_acres: float
    W: int
    H: int
    ftpx: float = 1.0
    offtakes_a: tuple[float, ...] = ()
    offtakes_b: tuple[float, ...] = ()
    # filled in by the stages as the map is built, so a later stage can read an earlier one's result
    net: dict[str, Any] = field(default_factory=dict)
    envelope: Poly = field(default_factory=list)
    sink_pond: tuple[float, float, float, float] | None = None
    sink_brook: Poly = field(default_factory=list)
    watercourses: list[tuple[Pt, Pt]] = field(default_factory=list)
    belt: Poly = field(default_factory=list)
    seat: dict[str, Any] = field(default_factory=dict)
    placed: int = 0
    acres: float = 0.0

    @property
    def fall(self) -> Pt:
        """Unit vector pointing DOWNHILL, in screen coordinates."""
        return (math.cos(math.radians(self.down_deg)), math.sin(math.radians(self.down_deg)))

    @property
    def wind(self) -> Pt:
        """Unit vector pointing at the quarter the cold wind blows FROM (so: the sheltered BACK)."""
        return WIND_VECTORS[self.windward]


def _roll(seed: int, knob: str, choices: Sequence[Any]) -> Any:
    """One deterministic, INDEPENDENT draw. Uses the engine's `knob_rng`, so a draw depends only on
    (map seed, knob name) - never on how much randomness has been drawn before it. That is the
    skill's positional-randomness rule at the knob level: adding a knob here cannot re-roll the
    others, so a cohort's earlier maps do not silently change when a later knob is added."""
    return choices[knob_rng(seed, knob).randrange(len(choices))]


def offtakes_for(households: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """The delivery-ditch fractions for a hamlet of this size - see `OFFTAKE_LADDER`."""
    for ceiling, a, b in OFFTAKE_LADDER:
        if households < ceiling:
            return a, b
    return OFFTAKE_LADDER[-1][1], OFFTAKE_LADDER[-1][2]


def canvas_for(target_acres: float, ftpx: float) -> tuple[int, int]:
    """A working canvas comfortably larger than the fan it must hold.

    The canvas is NOT the map: `crop_to_content` frames the finished drawing to its hard features,
    so this only has to be big enough that `build_comb` never clamps the fan against a canvas edge
    (which truncates threads and leaves a fan with a flat, obviously-artificial side) and big enough
    to leave margin ground for the cluster, its grove and the hinterland.

    A comb fan fills roughly 40% of its own bounding box (it is a fan, not a rectangle), and the
    settlement plus its margins needs about as much ground again as the field, so the span is sized
    from the field's bbox and doubled. Erring LARGE is cheap - unused canvas is cropped away - while
    erring small is a silently mis-shaped field, so the multiplier errs high.

    IT WAS TRIED AT 1.75x and reverted. A review nitpick (fair, and still open) is that ~68% of the
    canvas is drawn and then cropped away - ink nobody sees, a 16 MB SVG, a slower render. But the
    canvas also has to hold what sits BELOW the field: `stage_sink` walks the tameike downslope from
    the drain outfall until it clears the crop, and then clamps it to the canvas. At 1.75x the clamp
    started winning, which puts the pond back on the paddy and its ditch running uphill - four
    checks failing on a third of a cohort, all from one number. Trimming the canvas needs the CROP
    to be trimmed instead, not the ground the map still uses."""
    field_px2 = target_acres * SQ_FT_PER_ACRE / (ftpx * ftpx)
    span = math.sqrt(field_px2 / 0.40)
    side = int(round(span * 2.0 / 50.0) * 50)
    return side, side


def windward_for(down_deg: float, seed: int) -> str:
    """The compass quarter the cold wind blows FROM: upslope, turned by a rolled 45 deg. See
    `WIND_TURNS` for why the wind is read off the slope instead of drawn independently."""
    bearing = (down_deg + 180.0 + float(_roll(seed, "wind_turn", WIND_TURNS))) % 360.0
    return min(WIND_VECTORS, key=lambda q: abs(((math.degrees(math.atan2(WIND_VECTORS[q][1], WIND_VECTORS[q][0])) - bearing + 180.0) % 360.0) - 180.0))


def plan_site(spec: HamletSpec) -> SitePlan:
    """Turn a spec into a fully-resolved plan. PURE - no drawing, no engine, no RNG stream."""
    down_deg = spec.down_deg if spec.down_deg is not None else float(_roll(spec.seed, "down_deg", FALL_BEARINGS))
    # A hamlet is ONE comb draining down ONE valley, so its drainage bearing IS its fall unless the
    # GM declares otherwise. Recording both separately keeps the map honest about which fact is
    # which (skill SKILL.md: "these are not the same fact and must not be derived from each other")
    # and leaves the door open for a spec that sets a channel running across the fall.
    water_flow = spec.water_flow if spec.water_flow is not None else down_deg
    windward = spec.windward or windward_for(down_deg, spec.seed)
    target_acres = spec.households * GROSS_ACRES_PER_HOUSEHOLD
    a, b = offtakes_for(spec.households)
    W, H = canvas_for(target_acres, 1.0)
    return SitePlan(
        spec=spec,
        down_deg=down_deg,
        water_flow=water_flow,
        windward=windward,
        water_sink=spec.water_sink or str(_roll(spec.seed, "water_sink", SINKS)),
        cluster_shape=spec.cluster_shape or str(_roll(spec.seed, "cluster_shape", CLUSTER_SHAPES)),
        lane_skeleton=spec.lane_skeleton or str(_roll(spec.seed, "lane_skeleton", LANE_SKELETONS)),
        plot_size=spec.plot_size or str(_roll(spec.seed, "plot_size", PLOT_SIZES)),
        grain_drift=spec.grain_drift if spec.grain_drift is not None else int(_roll(spec.seed, "grain_drift", GRAIN_DRIFTS)),
        woodland_patches=spec.woodland_patches if spec.woodland_patches is not None else int(_roll(spec.seed, "woodland_patches", (2, 3, 3, 4))),
        fan_aspect=float(_roll(spec.seed, "fan_aspect", FAN_ASPECTS)),
        target_acres=target_acres,
        W=W,
        H=H,
        offtakes_a=a,
        offtakes_b=b,
    )


# ---- geometry helpers ---------------------------------------------------------------------------


def poly_area(poly: Sequence[Pt]) -> float:
    """Absolute area of a closed polygon (the shoelace formula)."""
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2.0


def net_acres(net: Mapping[str, Any], ftpx: float) -> float:
    """The DRAWN paddy acreage of a comb net - the sum of the plot polygons actually carved.

    Deliberately measured from the plots and not from `build_comb`'s own `acres` (which assumes the
    village grain of 1 px = 2 ft and so over-reports 4x on a 1 ft/px hamlet) and not from the field
    envelope (which bows outside the plots and would count the bunds, the canals and the gaps as
    rice). The plots are what a farmer plants, so the plots are what gets counted."""
    return sum(poly_area(p["poly"]) for p in net["plots"]) * ftpx * ftpx / SQ_FT_PER_ACRE


def centroid(poly: Sequence[Pt]) -> Pt:
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def unit(vx: float, vy: float) -> Pt:
    ln = math.hypot(vx, vy) or 1.0
    return (vx / ln, vy / ln)


def crop_polys(s: Settlement) -> list[Poly]:
    """Every DRY crop plot recorded so far, read back from the manifest.

    Read back rather than carried along from `build_comb`, because `draw_comb_field` DROPS hem plots
    that landed on standing water or on another fan's rice - so the net's list and the map's list
    are not the same list, and the one that matters is what was drawn."""
    return [[(float(v[0]), float(v[1])) for v in d["poly"]] for d in s.M.get("dry_plots", [])]


def pull_clear(pt: Pt, toward: Pt, obstacles: Sequence[Poly], margin: float, step: float = 12.0, tries: int = 24) -> Pt:
    """Walk a point back toward `toward` until it is `margin` clear of every obstacle.

    Used to shape the windbreak belt around the crop. Deforming the belt is the right answer rather
    than shrinking it uniformly: a fengshui grove hugs the land it is planted on and wraps whatever
    is in its way, so a belt that bends around a hem plot reads MORE like a real grove than a
    rectangle would, and it keeps its length (the gate wants a belt that embraces the cluster, and
    a uniformly-shrunk belt stops embracing before it stops overlapping)."""
    x, y = pt
    for _ in range(tries):
        if not any(point_in_poly(x, y, list(o)) or min(seg_dist(x, y, o[i], o[(i + 1) % len(o)]) for i in range(len(o))) < margin for o in obstacles):
            return (x, y)
        ux, uy = unit(toward[0] - x, toward[1] - y)
        x, y = x + ux * step, y + uy * step
    return (x, y)


def crosses_disc(a: Pt, b: Pt, center: Pt, r: float) -> bool:
    """Does the segment a->b come within `r` of `center`? (Point-to-segment distance.)"""
    return seg_dist(center[0], center[1], a, b) < r


def crosses_poly(a: Pt, b: Pt, poly: Sequence[Pt], step: float = 8.0, cap: int = 900) -> bool:
    """Does the segment a->b pass through `poly`? Sampled rather than solved, but sampled by LENGTH.

    It used to take a fixed 60 samples whatever the segment measured, which is fine for a lane and
    useless for the thing it is mostly asked about: a connector track or a drain brook runs 4,000 px
    to the frame, so 60 samples is one every 67 px and the test steps clean over a field lobe. The
    map then ships a brook drawn through the rice with the router insisting it had checked
    (`streams_avoid_fields`). One sample every 8 px is under the width of anything it is testing
    against, and the cap keeps a stray off-canvas endpoint from turning this into a million tests."""
    ring = list(poly)
    # EXACT edge intersection first, which is what `streams_avoid_fields` and its siblings use. A
    # sampled containment test cannot see a segment that clips a thin sliver of the outline - it
    # enters and leaves between two samples, and no sample is ever strictly inside - so a brook
    # routed by sampling alone was drawn across a lobe of the rice with every point it checked
    # legitimately outside the crop. Sampling stays as the second half, because it also catches the
    # case exact-crossing cannot: a segment lying wholly INSIDE the polygon, crossing no edge.
    if any(segments_cross(a, b, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))):
        return True
    n = min(cap, max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
    return any(point_in_poly(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, ring) for i in range(n + 1))


# ---- STAGE 1: the water frame -------------------------------------------------------------------


def stage_water_frame(s: Settlement, plan: SitePlan) -> None:
    """Settle the drainage bearing and the land's fall BEFORE anything is placed.

    This is first because the skill says it is first, at every tier: "before a single feature is
    placed, decide the map's drainage bearing and, separately, the land's fall". Everything
    downstream reads them - which end of the fan is the head, which margin the cluster can stand on,
    which way the drain runs, where the marsh is allowed to be."""
    # THE MAP DECLARES THAT A SCRIPT MADE IT (GM 2026-08-13). Rules that the scripted path adopts
    # ahead of the hand-authored pool are gated on this tag, so a legacy map keeps its present
    # packing and starts obeying the new rule the moment it is CONVERTED - the migration enforces
    # itself instead of needing a list of exemptions that someone has to remember to prune.
    s.meta(
        generated_by="hamletgen",
        name=plan.spec.name,
        scale="hamlet",
        ftpx=plan.ftpx,
        toscale=True,
        households=plan.spec.households,
        water_flow=plan.water_flow,
        down_deg=plan.down_deg,
        windward=plan.windward,
        nucleated=True,
        field_footbridges=True,
        water_kind="stream",
    )
    s._nucleated = True
    for knob, value in plan.spec.pins.items():
        s.pin_knob(knob, value)


# ---- STAGE 2: the field the water shapes --------------------------------------------------------


def fit_field(plan: SitePlan, sluice: Pt, seed: int, plot_across: float, row_step: tuple[float, float], tolerance: float = 0.06, rounds: int = 9) -> dict[str, Any]:
    """SOLVE the comb for the acreage the household count demands, instead of guessing a fall length.

    `build_comb` takes a `field_fall` in PIXELS, and the relationship between that number and the
    acreage that comes out is not analytic - the carve drops sectors too narrow to plant, the fan's
    width follows the canal lengths, and the envelope's shape depends on where the threads clamp. An
    author picks a number, looks at the render, and adjusts; Ikegami's 1150 is such a number, and it
    lands 24% under the acreage its own docstring asks for.

    A script does not have to guess. `build_comb` is pure, deterministic and fast, so this bisects a
    single SIZE multiplier - applied to the fall length AND both canal lengths together, so the fan
    scales without changing shape - until the drawn plot area is within `tolerance` of the target.
    Returns the best net found, which is the one whose acreage is closest, not merely the last.

    The multiplier is bracketed rather than solved because acreage is monotone in it but stepwise:
    a small change can add or drop a whole plot row, so the curve has small flats and the bisection
    is on a monotone-but-lumpy function. Nine rounds resolves the multiplier to ~0.3%, far finer
    than one plot row, and costs well under a second."""
    best: tuple[tuple[bool, float], dict[str, Any]] | None = None
    # THE ASPECT IS PART OF THE SEARCH, not just a roll. A fan's legality - whether its supply canal
    # dies among the plots, whether its collector folds back on itself - depends on its SHAPE as much
    # as its size, and a roll can land on an aspect at which no size is legal. So the rolled aspect
    # is tried first and the rest follow in order; the first legal fan wins, and if none is legal the
    # closest-on-acreage is kept so the failure is a gate message rather than an exception.
    for aspect in [plan.fan_aspect] + [a for a in FAN_ASPECTS if a != plan.fan_aspect]:
        found = _fit_at_aspect(plan, sluice, seed, plot_across, row_step, aspect, tolerance, rounds)
        if best is None or found[0] < best[0]:
            best = found
        if not found[0][0]:
            break
    assert best is not None
    return best[1]


def _fit_at_aspect(plan: SitePlan, sluice: Pt, seed: int, plot_across: float, row_step: tuple[float, float], aspect: float, tolerance: float, rounds: int) -> tuple[tuple[bool, float], dict[str, Any]]:
    """`fit_field`'s bisection at ONE fan aspect. Returns ((illegal, acreage error), net)."""
    lo, hi = 0.35, 2.2
    best: tuple[tuple[bool, float], dict[str, Any]] | None = None
    for _ in range(rounds):
        k = (lo + hi) / 2.0
        net = build_comb(
            plan.W,
            plan.H,
            sluice,
            seed,
            down_deg=plan.down_deg,
            field_fall=REF_FIELD_FALL * k / aspect,
            canal_a_len=(REF_CANAL_A[0] * k * aspect, REF_CANAL_A[1] * k * aspect),
            canal_b_len=(REF_CANAL_B[0] * k * aspect, REF_CANAL_B[1] * k * aspect),
            offtakes_a=plan.offtakes_a,
            offtakes_b=plan.offtakes_b,
            plot_across=plot_across,
            row_step=row_step,
            grain_drift=plan.grain_drift,
            grain=GRAIN,
        )
        acres = net_acres(net, plan.ftpx)
        err = abs(acres - plan.target_acres) / plan.target_acres
        # A DANGLING CANAL TAIL disqualifies a fan before its acreage is even considered. Whatever
        # supply canal runs on past its last delivery ditch has to die among the plots it waters;
        # ending outside the planted extent is runoff dying in bare ground
        # (`watercourse_ends_reach_water`). The offtake ladder keeps the tail SHORT, but whether a
        # short tail lands inside depends on how wide the fan happens to be there - so the bisection
        # picks the best fan that is legal rather than the best fan and then hoping.
        score = (tail_dangles(net) or net_bends_acutely(net), err)
        if best is None or score < best[0]:
            best = (score, net)
        if err <= tolerance and not score[0]:
            break
        if acres < plan.target_acres:
            lo = k
        else:
            hi = k
    assert best is not None
    return best


HEAD_OFFSETS: tuple[tuple[str, float], ...] = (("head_left", -0.24), ("head_center", -0.05), ("head_center", 0.05), ("head_right", 0.24))


def head_sluice(plan: SitePlan) -> tuple[Pt, str]:
    """WHERE THE WATER REACHES THE FIELD - the intake, at the field's HIGH head.

    Gravity settles this: a comb is fed from its high end, so the sluice sits at the upslope end of
    the ground the field will occupy, and the only real freedom is WHICH point of that head margin -
    a brook coming down the left shoulder, the right, or straight into the middle.

    This is deliberately NOT the engine's `water_source_anchor`. That helper resolves the knob
    catalog's `edge_N`/`edge_W`-style positions against a canvas-relative box, so a lateral entry
    (`edge_W` on a south-falling map) lands at the box's MID-height: legal by the gravity test, but
    it leaves the fan only half the canvas to run down, and the field then saturates far under the
    acreage the household count needs. That was the first real bug in this experiment and it is the
    kind a map-by-map author never meets, because they pick the number that makes the picture work.
    Anchoring on the fall axis instead makes the intake a consequence of the slope, which is what it
    is in the world."""
    dx, dy = plan.fall
    cx, cy = plan.W / 2.0, plan.H / 2.0
    px, py = -dy, dx  # across the fall
    name, lateral = _roll(plan.spec.seed, "head_offset", HEAD_OFFSETS)
    span = float(min(plan.W, plan.H))
    return (cx - dx * span * 0.36 + px * span * lateral, cy - dy * span * 0.36 + py * span * lateral), str(name)


def tail_dangles(net: Mapping[str, Any], margin: float = 18.0) -> bool:
    """Does any supply-canal end fall outside the fan's planted extent? See `fit_field`."""
    xs = [v[0] for p in net["plots"] for v in p["poly"]]
    ys = [v[1] for p in net["plots"] for v in p["poly"]]
    if not xs:  # pragma: no cover - a fan with no plots fails long before this
        return True
    x0, y0, x1, y1 = min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
    # ONLY the supply canals ("main"), and only their FREE ends.
    #
    # Two exclusions, and both were learned by getting them wrong. The DRAIN's downstream end is
    # SUPPOSED to sit outside the crop - it is the outfall, and the brook or the tameike ditch
    # attaches to it there. And a main's UPSTREAM end is the head sluice or a junction with the
    # previous main, which is also outside the plots by construction: testing it made this return
    # True for every fan ever built, which turned the disqualifier off while leaving it looking like
    # it worked, and quietly cost five times the generation work for nothing.
    #
    # A free end is one no other main starts or ends at.
    ends = [q for c in net["channels"] if c["role"] == "main" for q in (c["pts"][0], c["pts"][-1])]
    free = [q for q in ends if sum(1 for r in ends if math.hypot(q[0] - r[0], q[1] - r[1]) < 5.0) == 1]
    return any(not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1) for q in free[1:])  # [1:] drops the head intake, which is always outside the plots


def net_bends_acutely(net: Mapping[str, Any]) -> bool:
    """Does any channel in the fan fold back through less than 90 degrees?

    `water_channels_obtuse_turns` forbids it - a dug ditch does not make a hairpin - and the fan's
    own collector occasionally produces one at a particular size. Disqualifying the candidate is far
    cheaper than trying to repair the geometry afterwards, and `fit_field` has eight other fans to
    choose from."""
    for c in net["channels"]:
        pts = c["pts"]
        for i in range(1, len(pts) - 1):
            ax_, ay_ = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx_, by_ = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax_, ay_), math.hypot(bx_, by_)
            if la >= 3 and lb >= 3 and (ax_ * bx_ + ay_ * by_) / (la * lb) < 0.0:
                return True
    return False


def feed_brook(plan: SitePlan, sluice: Pt, run: float = 420.0) -> Poly:
    """The brook coming down off the high ground to the intake, steered clear of the rice.

    It ends AT the sluice, where it becomes the head-race - it does not run on over the paddies. The
    sluice sits on the field's head margin, so the LAST stretch is legitimately against the crop and
    is not tested; everything upstream of it is, because a fan's head can carry a lobe out to one
    side and a brook coming straight down the fall line then clips it (`streams_avoid_fields`, which
    is right to object - a stream does not run through a flooded paddy). Bearings are tried outward
    from straight-upslope, so the brook stays as close to the fall line as the field allows."""
    dx, dy = plan.fall
    base = math.degrees(math.atan2(-dy, -dx))  # upslope
    for swing in sorted((10.0 * k for k in range(-7, 8)), key=abs):
        th = math.radians(base + swing)
        up = (sluice[0] + math.cos(th) * run, sluice[1] + math.sin(th) * run)
        mid = ((up[0] + sluice[0]) / 2 - math.sin(th) * 26, (up[1] + sluice[1]) / 2 + math.cos(th) * 26)
        near = (sluice[0] + math.cos(th) * 40, sluice[1] + math.sin(th) * 40)  # the last 40 px is the intake itself
        if not (crosses_poly(up, mid, plan.envelope) or crosses_poly(mid, near, plan.envelope)):
            return [up, mid, sluice]
    up = (sluice[0] - dx * run, sluice[1] - dy * run)  # pragma: no cover - a fan head never blocks all fifteen
    return [up, ((up[0] + sluice[0]) / 2 + dy * 26, (up[1] + sluice[1]) / 2 - dx * 26), sluice]  # pragma: no cover - the same unreachable fallback, one line down


def stage_field(s: Settlement, plan: SitePlan) -> None:
    """Lay the irrigation skeleton and carve the paddies between its threads.

    Second, because the water is first and the field is grown AROUND the water (the water-first
    inversion `waterfields.py` exists for). The head sluice comes from `head_sluice`, which puts the
    intake at the field's high head - gravity, not a knob."""
    dx, dy = plan.fall
    sluice, position = head_sluice(plan)
    s.M["meta"]["water_source"] = position
    s.M["meta"]["water_source_position"] = position

    across, step = s.plot_texture(plan.plot_size, "organic")
    net = fit_field(plan, sluice, plan.spec.seed, across, step)
    plan.net = net
    plan.acres = net_acres(net, plan.ftpx)

    # THE DRAIN'S CONTINUATION IS ALWAYS OURS TO DRAW. `build_comb` hands back a `brook` and
    # `draw_comb_field` draws it when it is there - straight downhill, a FIXED 520 px. Both sinks
    # need something else. A hamlet draining into its own tameike must have NO brook at all (the
    # runoff stops at the pond, and `stage_sink` supplies the ditch that reaches it). A hamlet
    # draining OFF the frame needs a brook that actually gets there, and 520 px is a constant tuned
    # against the canvases the authored maps happened to use: on a wider one the brook stops in open
    # ground and fails `stream_runs_off_edge` + `stream_end_anchored`, which is the same
    # pinned-constant failure the pond set-back had. So the brook is cleared here either way, and
    # `stage_sink` draws the off-map one at a length DERIVED from the distance to the canvas edge.
    net["brook"] = []

    plan.envelope = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]  # routed against BEFORE the field is drawn (see feed_brook)
    s.field_polys.append(list(plan.envelope))
    s.meta(dry_furrows_vary=net["furrows_vary"])
    s.M["meta"]["field_archetype"] = "valley_paddy"
    # The brook that feeds the head, running in from off-map: the visible source. It is drawn as a
    # STREAM ending AT the sluice, where it becomes the head-race - it does not run on over the
    # paddies. `draw_comb_field` then records the hairline topology channel that grounds the field's
    # water source for the gate.
    s.draw_comb_field(net, f"{plan.spec.name.lower()}-paddies", {"kind": "stream", "stream": feed_brook(plan, sluice)})
    # THE PARTS OF A DITCH THAT RUN OUTSIDE THE CROP become no-build corridors.
    #
    # `s.field_channel` registers none of its own, and inside the field envelope it does not need
    # to - the crop is blocked ground already. But a delivery ditch's tail and the collector run out
    # past the envelope onto open margin, where the placer is otherwise free to seat a homestead
    # squarely on the water (`no_structure_on_channel`). Only those stretches are reserved:
    # blanketing the whole ditch net costs the field its ring of farmhouses, because a comb's
    # deliveries run right along the margin the front row wants (`field_ringed`, three maps).
    #
    # And it goes AFTER `draw_comb_field`, which is where `M['field_ditches']` is written. Placed
    # before it, the loop had nothing to iterate and reserved nothing at all - silently, since an
    # empty loop looks exactly like a loop with nothing to do.
    for ditch in s.M.get("field_ditches", []):
        run = [(float(v[0]), float(v[1])) for v in ditch["poly"]]
        outside = [(a, b) for a, b in zip(run, run[1:], strict=False) if not point_in_poly((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, plan.envelope)]
        for a, b in outside:
            s.corridors.append(([a, b], 30.0))


# ---- STAGE 3: where the runoff goes -------------------------------------------------------------


def drain_outfall(s: Settlement, name: str) -> Pt | None:
    """The last vertex of the field's drain collector, READ BACK from the manifest.

    Read back rather than remembered, because the manifest is what the gate reads: siting the pond
    from the same record `pond_connected_to_field` will measure against is the skill's "placement and
    its check must read the SAME manifest source" rule, one level down."""
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and ditch.get("field") == name:
            pts = ditch["poly"]
            return (float(pts[-1][0]), float(pts[-1][1]))
    return None  # pragma: no cover - build_comb always emits a drain collector for a comb fan


def drain_heading(s: Settlement, name: str) -> Pt | None:
    """The direction the drain collector is running where it ends - so its continuation leaves it as
    a smooth junction rather than a hard corner."""
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and ditch.get("field") == name and len(ditch["poly"]) >= 2:
            a, b = ditch["poly"][-2], ditch["poly"][-1]
            return unit(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))
    return None  # pragma: no cover - drain_outfall found the same record a line earlier


def edge_run(plan: SitePlan, frm: Pt) -> float:
    """Distance from `frm` to the canvas edge along the fall - how far a watercourse has to run to
    leave the map from here."""
    dx, dy = plan.fall
    spans = []
    if abs(dx) > 1e-6:
        spans.append(((plan.W if dx > 0 else 0.0) - frm[0]) / dx)
    if abs(dy) > 1e-6:
        spans.append(((plan.H if dy > 0 else 0.0) - frm[1]) / dy)
    return max(0.0, min(spans)) if spans else 0.0  # pragma: no cover - the fall is never the zero vector


def pond_clear_of_crop(plan: SitePlan, center: Pt, prx: float, pry: float) -> bool:
    """The two tests `pond_clear_of_field` makes, on the same envelope: no rim point inside the crop,
    no crop vertex inside the pond."""
    env = list(plan.envelope)
    rim = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
    if any(point_in_poly(center[0] + prx * ux, center[1] + pry * uy, env) for ux, uy in rim):
        return False
    return not any(((v[0] - center[0]) / prx) ** 2 + ((v[1] - center[1]) / pry) ** 2 <= 1.0 for v in env)


def pond_setback(plan: SitePlan, out: Pt, prx: float, pry: float, step: float = 14.0, limit: float = 900.0) -> float:
    """How far DOWNSLOPE of the drain outfall the pond must stand to clear the crop entirely.

    Walks outward in small steps and returns the first distance at which no rim point of the ellipse
    falls inside the field envelope and no envelope vertex falls inside the ellipse - the same two
    tests `pond_clear_of_field` makes, run against the same envelope, so the siting and the check
    cannot disagree (the skill's "adjudicate against the gate, never a re-statement of it" rule, in
    its cheap form: the predicate is copied from the check and measured on the same manifest
    geometry). A 12 px cushion past the first clear position keeps it off the line."""
    dx, dy = plan.fall
    env = list(plan.envelope)
    rim = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
    d = pry + 46.0  # never closer than a rim's worth below the outfall, whatever the geometry says
    while d <= limit:
        cx, cy = out[0] + dx * d, out[1] + dy * d
        clear = not any(point_in_poly(cx + prx * ux, cy + pry * uy, env) for ux, uy in rim)
        if clear:
            clear = not any(((v[0] - cx) / prx) ** 2 + ((v[1] - cy) / pry) ** 2 <= 1.0 for v in env)
        if clear:
            return d + 12.0
        d += step
    return limit  # pragma: no cover - a fan is never 900px deep past its own outfall


def stage_sink(s: Settlement, plan: SitePlan) -> None:
    """The tameike the field drains into - DERIVED from the drain, never placed by hand.

    A reservoir below the fields is sited by one fact: it must sit clear of the paddies and low
    enough that the drain reaches it downhill. So it goes a fixed set-back DOWNSLOPE of the drain's
    own outfall, wherever that outfall landed, and the drainage ditch is drawn from the outfall to
    the pond's center so the two are visibly joined. Both scale with the map: a bigger hamlet drains
    more water into a bigger pond.

    `water_sink="offmap"` draws nothing here - the drain's brook (kept in `stage_field`) already
    carries the runoff off the frame, which is what most valleys do and what the GM's brief allows."""
    name = f"{plan.spec.name.lower()}-paddies"
    out = drain_outfall(s, name)
    if out is None:  # pragma: no cover - build_comb always emits a drain collector for a comb fan
        return
    dx, dy = plan.fall
    if plan.water_sink != "pond":
        # OFF THE FRAME: the collector's brook runs on downhill and leaves the map, to join a stream
        # or another farm's drain somewhere the map does not have to care about. Its LENGTH is
        # derived per bearing below - the distance from the junction to the canvas edge along the
        # heading actually taken - because a fixed length only works on the canvas it was tuned for,
        # and a length derived for the FALL is wrong for any other bearing the search tries.
        heading = drain_heading(s, name) or (dx, dy)
        # THE ROUTE IS CHOSEN AS A WHOLE - junction and exit together.
        #
        # The brook leaves the collector at a junction point and then runs downhill off the frame.
        # The junction sits on the BISECTOR of the drain's heading and the chosen exit, so the brook
        # turns through half the angle twice rather than all of it once, and half of any angle is
        # obtuse (`water_channels_obtuse_turns`; a ditch does not fold back on itself). It TURNS WITH
        # THE BEARING for a reason learned the hard way: pinned to the fall line it was identical for
        # every candidate, so when that one leg crossed the crop all nine bearings failed alike and
        # the sweep dropped through to an untested straight line - the exact defect the sweep exists
        # to prevent, chosen deliberately.
        #
        # "Straight downhill" is right on most fans and wrong on the ones whose toe is concave, where
        # the exit clips back across the rice - so the bearing swings off the fall until the route is
        # clear, nearest first. A brook does follow the fall; the swing is small, and the alternative
        # is a watercourse drawn through a paddy.
        #
        # The junction leg is exempt from the crop test exactly when the GATE exempts it, on the same
        # test: `streams_avoid_fields` trims leading vertices that are INSIDE the field outline, so a
        # leg whose start is outside gets measured in full. Anything looser skips the one leg that
        # was crossing - a 35%-along start was tried, and the crossing was in the first 35%.
        # THE BROOK STARTS WHERE THE GATE WILL TRIM IT. `streams_avoid_fields` drops leading vertices
        # that are strictly INSIDE the field outline, which is how it exempts the anchored end - but a
        # collector whose outfall lands exactly ON the outline (within rounding) is neither in nor
        # out, so nothing is trimmed and every route from it reads as crossing the crop. There is no
        # bearing that fixes that; the start is the problem. Backing up the drain until the point is
        # genuinely inside costs nothing - the brook is the drain's own continuation, so it still
        # touches the collector at its end - and it lets the exemption do its job.
        for back_off in (0.0, 12.0, 24.0, 40.0, 60.0):
            cand = (out[0] - heading[0] * back_off, out[1] - heading[1] * back_off)
            if point_in_poly(cand[0], cand[1], plan.envelope):
                out = cand
                break
        exit_deg = math.degrees(math.atan2(dy, dx))
        anchored = point_in_poly(out[0], out[1], plan.envelope)
        best: tuple[int, Poly] | None = None
        # ...and the junction's DISTANCE from the outfall is searched too. At a fixed 70 px the
        # junction can sit inside a lobe of the fan that the collector runs past, so every bearing
        # crosses on its first leg and the best available route is still a bad one. Letting the brook
        # run a little further before it turns is what gets it clear, and it is what a brook does.
        # Ordered SWING-major and capped at +/-54 deg: `drainage_junction_smooth` wants the brook to
        # leave the collector without a kink, so a wide swing bought to clear a lobe costs more than
        # it saves. Try the nearest bearings at every junction distance before widening the angle.
        # Bearings are tried around the FALL first and then around the DRAIN'S OWN HEADING. A brook
        # continuing along the collector's line before it turns downhill is both perfectly smooth at
        # the junction (turn = 0) and already clear of the rice, since the collector is - which is the
        # combination a fan whose toe wraps a lobe cannot get any other way.
        head_deg = math.degrees(math.atan2(heading[1], heading[0]))
        for base_deg, swing, jd in ((bd, sw, j) for sw in (0, 12, -12, 24, -24, 38, -38, 54, -54) for bd in (exit_deg, head_deg) for j in (70.0, 110.0, 160.0, 230.0)):
            th = math.radians(base_deg + swing)
            bis = unit(heading[0] + math.cos(th), heading[1] + math.sin(th))
            mid = (out[0] + bis[0] * jd, out[1] + bis[1] * jd)
            # the run is measured along THIS bearing, not along the fall: a ray sized for the fall
            # and fired on another heading either stops on the map or sweeps far past it
            spans = [
                ((plan.W if math.cos(th) > 0 else 0.0) - mid[0]) / math.cos(th) if abs(math.cos(th)) > 1e-6 else 1e9,
                ((plan.H if math.sin(th) > 0 else 0.0) - mid[1]) / math.sin(th) if abs(math.sin(th)) > 1e-6 else 1e9,
            ]
            run_here = max(120.0, min(spans)) + 260.0
            end = (mid[0] + math.cos(th) * run_here, mid[1] + math.sin(th) * run_here)
            # THE JUNCTION ANGLE IS SCORED, not left to the ordering. `drainage_junction_smooth`
            # wants under 65 degrees between the drain's own heading and the brook's first leg, and
            # the crop and the angle pull against each other on a fan whose collector runs past a
            # lobe: clearing the rice wants a wide swing, the smooth junction wants a narrow one.
            # Scoring both together picks a route that satisfies both when one exists, instead of
            # ping-ponging between two rules each satisfied at the other's expense.
            turn = math.degrees(math.acos(max(-1.0, min(1.0, heading[0] * bis[0] + heading[1] * bis[1]))))
            bad = int(point_in_poly(mid[0], mid[1], plan.envelope)) + int(crosses_poly(mid, end, plan.envelope))
            bad += int(not anchored and crosses_poly(out, mid, plan.envelope))
            bad += int(turn > 55.0)
            if bad == 0:
                s.stream([out, mid, end], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)  # s.stream reserves its own corridor
                plan.sink_brook = [out, mid, end]
                return
            if best is None or bad < best[0]:  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
                best = (bad, [out, mid, end])  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        assert (
            best is not None
        )  # ...and if none is clean, the LEAST-BAD route, never an untested one  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        s.stream(
            best[1], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8
        )  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        plan.sink_brook = list(best[1])  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        return  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
    # Sized to the settlement: a tameike serving ~15 households reads at roughly Ikegami's 116x74 px
    # (~230 x 150 ft), and the radius scales with the square root of the households it waters, since
    # a reservoir's job is a VOLUME and its depth does not grow with the hamlet.
    grow = math.sqrt(plan.spec.households / REF_HOUSEHOLDS)
    prx, pry = 116.0 * grow, 74.0 * grow
    # THE SET-BACK IS SOLVED, NOT PICKED. `pond_clear_of_field` wants the whole ellipse outside the
    # field envelope, and the drain's outfall is not reliably outside it - a comb's envelope bows out
    # around the collector, so on some fans the outfall sits well inside the outline. Ikegami's
    # authored constant (rim + 46 px below the outfall) is true for Ikegami's fan and false for
    # others, which is exactly the failure mode the project's "derive, don't pin" rule names. So the
    # pond walks DOWNSLOPE from the outfall until its rim is genuinely clear, and stops at the first
    # position that is - the nearest legal seat, so the ditch between field and pond stays a ditch.
    back = pond_setback(plan, out, prx, pry)
    if back > POND_SETBACK_LIMIT:
        # NO ROOM FOR A RESERVOIR HERE, so the field drains off the frame instead.
        #
        # `pond_setback` walks downslope until the pond's rim clears the crop, and on a fan whose
        # toe reaches well past its own drain outfall that can be most of a canvas - at which point
        # the pond is a hard crop feature stranded in open scrub, holding the map's frame open by
        # hundreds of px for its own sake (`crop_not_held_open_by_one_feature` caught one 575 px
        # proud). A tameike is dug just below the fields it collects; one a quarter mile out is not
        # a tameike, it is a lake. Falling back to the off-map brook is the honest reading of the
        # same geometry, and the GM's brief names both sinks as equally ordinary.
        plan.water_sink = "offmap"  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
        stage_sink(s, plan)  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
        return  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
    pcx, pcy = out[0] + dx * back, out[1] + dy * back
    clamped = (max(prx + 20.0, min(plan.W - prx - 20.0, pcx)), max(pry + 20.0, min(plan.H - pry - 20.0, pcy)))
    if math.hypot(clamped[0] - pcx, clamped[1] - pcy) > 1.0 or not pond_clear_of_crop(plan, clamped, prx, pry):
        # THE CLAMP UNDOES THE SOLVE, so a clamped pond is no pond. `pond_setback` walks the tameike
        # downslope until its rim clears the crop; the clamp then pulls it back onto the canvas - and
        # straight back onto the rice it had just cleared (`pond_clear_of_field`). The reservoir has
        # nowhere to go on this map, which is the same finding as a set-back over the limit, so it
        # takes the same answer: the field drains off the frame instead.
        plan.water_sink = "offmap"
        stage_sink(s, plan)
        return
    pcx, pcy = clamped
    s.pond(pcx, pcy, prx, pry)
    plan.sink_pond = (pcx, pcy, prx, pry)
    s.M["meta"]["pond_role"] = "drainage"
    # The drainage ditch, bowed slightly off the straight line so it reads as dug earth rather than
    # a ruled connector (the gate's `channel_winds_gently` wants the same thing). Drawn in the BASE
    # water block, not the late one: the pond's fill has to paint OVER the ditch's mouth where it
    # overshoots the rim, and a late stroke composites above the fill instead
    # (`pond_fill_covers_channel_mouths`).
    bow = min(10.0, 0.08 * math.hypot(pcx - out[0], pcy - out[1]))  # a fixed 10 px bow on a SHORT run is an
    # acute hairpin (`water_channels_obtuse_turns`); proportional keeps the turn obtuse at any length
    mid = ((out[0] + pcx) / 2 - dy * bow, (out[1] + pcy) / 2 + dx * bow)
    ditch: Poly = [out, mid, (pcx, pcy)]
    s.field_channel(ditch, "#7C9EB0", 2.5, 2.5)
    s.M["channels"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in ditch], "frm": {"kind": "drain"}, "to": {"kind": "pond"}, "w": 2.5})
    # RESERVE IT AS A NO-BUILD CORRIDOR. `s.channel` and `s.stream` register one; `s.field_channel`
    # does not - which is fine for the comb's own ditches, because they run inside a field envelope
    # that is blocked ground already, and wrong for this one, which runs OUT of the field across
    # open margin where the placer is free to seat a homestead on it (`no_structure_on_channel`).
    s.corridors.append((list(ditch), 33.0))
    # A reedy fringe rims the shore - the shallow margin of any standing water.
    ring: Poly = [(pcx + (prx + 44) * math.cos(a), pcy + (pry + 44) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
    s.marsh(ring, role="pond_fringe")
    # No building on the water.
    s.block_polys.append([(pcx - prx - 10, pcy - pry - 10), (pcx + prx + 10, pcy - pry - 10), (pcx + prx + 10, pcy + pry + 10), (pcx - prx - 10, pcy + pry + 10)])


# ---- STAGE 4: seating the settlement, and its ways ----------------------------------------------


def below_drain(pt: Pt, drain: Poly, dx: float, dy: float, band: float = 150.0) -> bool:
    """Is `pt` on the WET side of the drain collector, within a toe band of it?

    The same question `dwellings_above_field_drain` asks of every dwelling, asked before the
    dwellings exist. Reading the check's own predicate rather than approximating it with "downhill
    of the field centroid" is the point: an aggregate cannot stand in for a distributed thing, and
    the drain is a LINE across the low side, not a point."""
    near = min(range(len(drain) - 1), key=lambda i: seg_dist(pt[0], pt[1], drain[i], drain[i + 1]))
    d = seg_dist(pt[0], pt[1], drain[near], drain[near + 1])
    proj = seg_closest(pt[0], pt[1], drain[near], drain[near + 1])
    return (pt[0] - proj[0]) * dx + (pt[1] - proj[1]) * dy > 18.0 and d <= band


def back_fouled(anchor: Pt, out: Pt, dep: float, dry_plots: Sequence[Poly], reach: float = 2.6, samples: int = 7) -> float:
    """What fraction of the ground BEHIND a candidate margin is already cropland.

    Samples a fan of points running out from the anchor along its outward normal, over the depth the
    cluster plus its windbreak will occupy. Returns 0.0 for a clear back and 1.0 for one entirely
    under the hem."""
    if not dry_plots:
        return 0.0
    ax, ay = -out[1], out[0]
    hit = 0
    total = 0
    for i in range(samples):
        t = (i + 0.5) / samples
        for lat in (-0.5, 0.0, 0.5):
            px = anchor[0] + out[0] * dep * reach * t + ax * dep * lat
            py = anchor[1] + out[1] * dep * reach * t + ay * dep * lat
            total += 1
            hit += any(point_in_poly(px, py, list(poly)) for poly in dry_plots)
    return hit / total


def seat_cluster(plan: SitePlan, dry_plots: Sequence[Poly] = (), drain: Poly | None = None, toe: Poly | None = None) -> dict[str, Any]:
    """WHERE THE HOUSES GO - the one derivation that decides how the whole map reads.

    背山面水, "back to the hill, face the water": a farming settlement stands with its back to the
    high, cold, windward side and its face to the field and its water. That is not decoration, it is
    the reason the windbreak grove has a side to be on, and it is what Ikegami's own docstring cites.
    So the cluster is seated on the field-envelope margin whose OUTWARD NORMAL best points into the
    wind, tie-broken toward the UPSLOPE end - which is also where the gate needs the dwellings to be
    (`dwellings_above_field_drain`: the ground below the drainage line is the wettest in the valley
    and is not building ground).

    Scoring every margin point of the DRAWN envelope, rather than picking a compass corner, is what
    makes this survive a field that came out a different shape: the seat follows the fan.

    Returns the seat frame - a center, an ALONG-the-margin unit, an AWAY-from-the-field unit, and
    the band's half-extents - which the lanes, the house seeds, the connector and the windbreak all
    work in, so every one of them lands correctly at any fall direction."""
    env = plan.envelope
    cen = centroid(env)
    dx, dy = plan.fall
    wx, wy = plan.wind
    # A band sized from the household count x the ground a homestead ACTUALLY takes.
    #
    # THE PITCH IS THE WHOLE THING, and getting it wrong is silent. `roll_village` sizes its band at
    # a 56 px pitch per household, which is the FARMHOUSE - but the to-scale tiers do not place a
    # farmhouse, they place a BUNDLE: house (46 x 28 ft) plus its threshing yard below and its
    # dooryard garden beside, ~71 x 57 ft of reserved ground, and the placer keeps bundles apart by
    # circumscribed circles rather than real footprints, which costs up to another ~2x in spacing
    # (the engine's documented collision-circle debt). 56 px per household therefore asks a band to
    # hold about three times what fits in it.
    #
    # The symptom is NOT a shortfall, which is what makes it worth writing down: the retry loop
    # widens the band until the houses do fit, so the count comes out right and the cluster ends up
    # packed absolutely solid. Then the wells have nowhere to go - 702 candidate seats offered,
    # every one refused, `open_seat` finding nothing anywhere in the cluster - and the map fails
    # `settlement_has_wells` for a reason that looks nothing like its cause. Sizing the band from
    # the bundle leaves the courtyards a well can stand in.
    dep = max(112.0, min(math.sqrt(plan.spec.households * (BUNDLE_PITCH**2) / (3.0 * math.pi)), 300.0))
    lat = max(240.0, min(plan.spec.households * (BUNDLE_PITCH**2) / (math.pi * dep), 1100.0))

    best: tuple[float, Pt, Pt] | None = None
    n = len(env)
    for i in range(n):
        ax, ay = env[i]
        bx, by = env[(i + 1) % n]
        mid = ((ax + bx) / 2.0, (ay + by) / 2.0)
        # THE EDGE'S OWN NORMAL, turned to face away from the field - not the ray from the field's
        # middle. A comb fan is NOT CONVEX: it has concave shoulders where the carve stops short,
        # and on those edges "away from the centroid" points straight back INTO the rice. Seeding a
        # cluster there put ten households on the paddy, where every candidate footprint was refused
        # by the crop keep-out and only four houses of a declared ten ever landed (seed 11). The
        # centroid ray is a plausible-looking approximation of an outward normal that is simply
        # wrong for the one shape this generator always draws.
        nx, ny = unit(-(by - ay), bx - ax)
        if (nx * (mid[0] - cen[0]) + ny * (mid[1] - cen[1])) < 0:
            nx, ny = -nx, -ny  # flip to the outward side (winding-independent)
        rel = ((mid[0] - cen[0]), (mid[1] - cen[1]))
        # ...and belt-and-braces: the BAND ITSELF must stand on open ground. An edge normal can
        # still graze a lobe of the fan a little further along, and a check is cheaper than a theory.
        if any(point_in_poly(mid[0] + nx * d - ny * lat * t, mid[1] + ny * d + nx * lat * t, env) for d in (dep * 0.5, dep + 34.0, dep * 2.0) for t in (-0.6, 0.0, 0.6)):
            continue
        # HARD 1: never below the DRAIN. The ground under the drainage line is the wettest in the
        # valley - reed marsh, the tameike, the low reclaimed paddy - and it is not building ground
        # (`dwellings_above_field_drain` says exactly this). Excluded rather than scored down: a
        # soft penalty lets a strong enough wind score pull the settlement into the bog.
        #
        # Measured against the DRAIN POLYLINE, not against the field's middle. "Above the middle"
        # was tried first and was much too strict - it is the dry HEM that hems the upslope margin,
        # so banning the downslope half leaves only the hem to build on, and the whole cohort came
        # back with its lanes and its grove standing in the hatake plots. The wet toe is a thin band
        # along one edge; the buildable ground is the two flanks, which is where Ikegami's cluster
        # sits and where this now puts it.
        if drain is not None and below_drain(mid, drain, dx, dy):
            continue
        # HARD 2: there must be clear ground BEHIND the margin. The settlement is a band and its
        # windbreak is a belt behind that - together most of a cluster's depth again - so a margin
        # is only usable if the ground it backs onto is free of crop. Testing the anchor POINT is
        # not enough (that was the first attempt): a point can stand clear of the hem while the belt
        # that goes 250 px behind it lands squarely in the plots.
        if back_fouled(mid, (nx, ny), dep, dry_plots) > 0.30:
            continue
        # HARD 3: the band has to FIT ON THE CANVAS. A margin near the canvas edge seats its band
        # centre outside it - and `_fits` refuses every candidate beyond `s.bound`, so the cluster
        # simply does not get built: seed 106 seated 7 farmhouses of a declared 15, with the band's
        # centre 56 px off the east edge. The map is not wrong, the seat is; another margin will do.
        seat_c = (mid[0] + nx * (dep + 12.0), mid[1] + ny * (dep + 12.0))
        if not (lat * 0.5 <= seat_c[0] <= plan.W - lat * 0.5 and lat * 0.5 <= seat_c[1] <= plan.H - lat * 0.5):
            continue
        # HARD 4: THE CLUSTER IS NOT BUILT ON THE WET TOE (GM 2026-08-12). `hinterland` lays reed
        # marsh across everything below the crop's low point, and on a crescent cluster hugging the
        # fan's toe the seat landed INSIDE that band - so the settlement's own lanes started in the
        # marsh and no amount of routing could save them (3 of 36 cohort maps). No reeds are drawn
        # on the houses, because the scatter skips the settlement halo, but the ground is still
        # marsh and the map says so. This is the same instinct as HARD 1 one step further out: you
        # do not build in the bog, and you do not build where the bog is either.
        if toe and (point_in_poly(seat_c[0], seat_c[1], toe) or point_in_poly(mid[0], mid[1], toe)):
            continue
        # 1.0 x facing the wind (the back), 0.8 x being upslope. Both express the same siting
        # instinct from two directions, and weighting the wind slightly higher keeps the windbreak
        # unambiguously behind the houses even on a map whose fall and wind nearly oppose.
        score = 1.0 * (nx * wx + ny * wy) - 0.8 * unit(*rel)[0] * dx - 0.8 * unit(*rel)[1] * dy
        # ...MINUS the dry hem. The upslope margin is contested ground: the comb's dry (hatake)
        # plots hem the high side along the supply canal, and they are cropland - a settlement
        # seated on top of them puts its windbreak's canopy in the crop (`groves_clear_of_dry_plots`)
        # and its farmsteads on the plots (`structures_clear_of_dry_plots`). So a margin that is
        # already hemmed scores down, in proportion to how close the hem is, and the seat slides
        # around the field to the free shoulder. Nothing here says WHICH shoulder - the geometry
        # does, which is why this works on a fan that came out a different shape.
        if dry_plots:
            hem = min(min(seg_dist(mid[0], mid[1], p[i], p[(i + 1) % len(p)]) for i in range(len(p))) for p in dry_plots)
            score -= 1.6 * max(0.0, 1.0 - hem / (2.0 * dep))
            score -= 2.5 * back_fouled(mid, (nx, ny), dep, dry_plots)
        if best is None or score > best[0]:
            best = (score, mid, (nx, ny))
    if best is None:  # pragma: no cover - a fan always leaves one buildable flank; belt and braces
        raise ValueError("no field margin is clear of the drain and the dry hem - the fan has no buildable flank")
    _, anchor, out = best
    along = (-out[1], out[0])
    # THE BAND'S NEAR EDGE HUGS THE FIELD. The standoff is the front row's own depth and no more:
    # `field_ringed` wants at least five farmhouses within 165 px of the field outline, and every
    # pixel of standoff comes off that count twice over, because the band is seeded across its whole
    # depth rather than packed against its near face. At 34 px of standoff three cohort maps rang
    # their field with four houses; at 12 the same maps ring it comfortably, and the front row still
    # fronts the paddy across its lane rather than standing in the rice.
    cx = anchor[0] + out[0] * (dep + 12.0)
    cy = anchor[1] + out[1] * (dep + 12.0)
    return {"cx": cx, "cy": cy, "along": along, "out": out, "lat": lat, "dep": dep, "anchor": anchor}


def stage_ways(s: Settlement, plan: SitePlan) -> None:
    """The lanes, laid BEFORE the houses because a lane is a no-build corridor the homesteads front.

    Three kinds, and each is derived from something already on the map:
      - the cluster's internal SKELETON (`skeleton_layout`, rolled), laid in the seat frame so it
        runs along the margin whatever direction the margin faces;
      - a SPUR from the skeleton to the nearest point of the field, because the reason these houses
        are here is the field and there must be a way to walk to it;
      - the CONNECTOR, the trodden track that leaves for the wider world. It starts at the
        skeleton's own gateway (the downslope exit the layout defines) and runs to the map edge, its
        bearing swung away from the crop until it clears - a track goes around a paddy, not through
        it. `connector_lane_runs_off_edge` requires it to actually reach the frame; the reason it
        must is that a path stopping mid-landscape reads as a dead end."""
    drain = None
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and len(ditch["poly"]) >= 2:
            drain = [(float(v[0]), float(v[1])) for v in ditch["poly"]]
            break
    # EVERY watercourse on the map, not just the field's own ditches. The ways are routed to meet
    # water squarely and to keep their decks off the crop, and that is only as good as the list they
    # are handed: the STREAMS - the feed brook coming down to the intake, the drain brook leaving
    # the frame - are drawn in the two stages before this one and were missing from it, so a track
    # could cross one at a slant and `bridges_span_their_water` would fail on a deck too short for
    # the water beneath it.
    # ...and the DRAWN lines, not only the recorded ones. `field_channel` fillets its polyline before
    # drawing it (`fillet_polyline`, so a mitred corner does not spike), and it is the drawn line a
    # bridge gets placed on - so routing against the recorded one can send a way across a ditch at a
    # slant the router never saw. Same rule as the connector's own bow: measure what is drawn.
    plan.watercourses = [
        ((float(a[0]), float(a[1])), (float(b[0]), float(b[1])))
        for rec in list(s.M.get("field_ditches", [])) + list(s.M.get("channels", [])) + list(s.M.get("streams", []))
        for a, b in zip(rec["poly"], rec["poly"][1:], strict=False)
    ] + [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
    seat = seat_cluster(plan, dry_plots=crop_polys(s), drain=drain, toe=s.toe_band() or None)
    plan.seat = seat
    # THE SITE'S BACK IS THE WINDWARD SIDE, and where the two disagree the site wins.
    #
    # The wind is derived from the slope (cold air drains off the high ground) and the cluster is
    # seated partly by it - back to the hill, face to the water. But the seat has hard constraints
    # the wind does not: not below the drain, not on the hem, not off the canvas. When those rule
    # out every wind-facing margin, the settlement ends up with its back to the FIELD, and a belt
    # placed on the declared windward side is then planted in the rice - where `village_grove`
    # throws away almost every clump and the map fails both windbreak checks with a grove of eight
    # trees. Re-reading the exposure off the seat is the self-consistent answer and the true one: a
    # settlement's sheltered side is the side it actually turns its back to, and this map is
    # declaring which quarter that is. A GM who knows the region's real prevailing wind pins it on
    # the spec, and then the seat search is what bends instead.
    if plan.wind[0] * seat["out"][0] + plan.wind[1] * seat["out"][1] < 0.34:  # more than ~70 deg apart
        plan.windward = min(WIND_VECTORS, key=lambda q: -(WIND_VECTORS[q][0] * seat["out"][0] + WIND_VECTORS[q][1] * seat["out"][1]))
        s.M["meta"]["windward"] = plan.windward
    ax, ay = seat["along"]
    ox, oy = seat["out"]
    cx, cy = seat["cx"], seat["cy"]

    crops = crop_polys(s)

    def to_screen(p: Pt) -> Pt:
        """Seat frame (along the margin, away from the field) -> screen."""
        return (cx + ax * p[0] + ox * p[1], cy + ay * p[0] + oy * p[1])

    toe_now = s.toe_band() or None
    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, seat["lat"], seat["dep"])
    for lane_pts in layout["lanes"]:
        # ...pulled back out of any hem plot the arm would otherwise reach into. The skeleton is
        # sized from the household count, so on a cluster seated tight against the hem a `cross`
        # crossbar can overrun into the barley - and a lane may touch a plot's edge but never cross
        # its interior. Shortening the arm is the honest fix: the lane simply ends where the crop
        # starts, which is what a village lane does.
        # The arms are clipped at WATER as well as at crop. A cluster's internal lanes serve the
        # houses; they have no business crossing a ditch, and a lane that does gets a deck from
        # `s.bridges()` sized for the angle it happens to meet the water at - which on a slant comes
        # up short (`bridges_span_their_water`). The spur and the connector are the ways that leave,
        # and they are routed to meet water squarely; an arm just stops at the bank.
        # ...clipped against the DRAWN water lines as well as the recorded ones: `field_channel`
        # fillets its polyline before drawing it, and a bridge is decked on what was drawn.
        drawn_water = [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
        # ...and the WET TOE is clipped against like any other ground a lane may not cross, not just
        # trimmed at the ends: `trim_off_marsh` walks an END back, which is the right move for a way
        # that pokes into the reeds, but an arm whose MIDDLE runs through them needs the truncation
        # its own docstring points at. An arm ends where the marsh begins - that is what a lane does.
        arm = clip_to_clear([to_screen((p[0], p[1])) for p in lane_pts], [*crops, *([toe_now] if toe_now else [])], 20.0, lines=list(plan.watercourses) + drawn_water)
        arm = s.trim_off_marsh(arm)  # ...and off the pond's reed fringe, which is already drawn by now
        if len(arm) >= 2:
            s.lane(arm, width=5, clearance=LANE_CLEARANCE, worn=True)
    s.M["meta"]["lane_skeleton"] = plan.lane_skeleton

    # the SPUR to the field: from the middle of the cluster to the nearest envelope point THE TRACK
    # CAN ACTUALLY REACH. Nearest-by-distance alone routes the path straight over the dry hem when
    # the hem lies between cluster and paddy - and a trodden path crosses no row crops
    # (`lanes_clear_of_dry_plots`; a real farm track runs on the baulk between plots, or round the
    # hem). So candidates are ordered by distance and the first one whose straight run is clear of
    # every hem plot wins; if none is, the nearest is used and the gate says so rather than the map
    # quietly shipping a lane through the barley.
    start = to_screen((0.0, 0.0))
    cen = centroid(plan.envelope)
    brook_segs = [(plan.sink_brook[i], plan.sink_brook[i + 1]) for i in range(len(plan.sink_brook) - 1)]

    def spur_path(target: Pt) -> Poly:
        # THE TIP STOPS OUTSIDE THE FIELD, measured on the LOCAL edge normal (GM 2026-08-12:
        # "Inashiro has village paths overlapping with rice paddies"). It used to pull back 8 px
        # along the SEAT's outward normal, which is one fixed direction for the whole map - so at a
        # target vertex whose own outline runs a different way, the pull-back was sideways and the
        # tip finished 28 px INSIDE the envelope, a track ending in the standing water. The normal
        # is taken from the two outline edges meeting at the target and oriented away from the
        # field's centroid, and the set-back covers the lane's own half-width plus the tolerance
        # `fields_clear_of_road` allows. A path stops AT the bund; the last few feet are the baulk.
        env = plan.envelope
        k = min(range(len(env)), key=lambda i2: math.hypot(env[i2][0] - target[0], env[i2][1] - target[1]))
        nx, ny = 0.0, 0.0
        for a2, b2 in ((env[k - 1], env[k]), (env[k], env[(k + 1) % len(env)])):
            ex, ey = unit(-(b2[1] - a2[1]), b2[0] - a2[0])
            nx, ny = nx + ex, ny + ey
        nx, ny = unit(nx, ny)
        if nx * (target[0] - cen[0]) + ny * (target[1] - cen[1]) < 0:
            nx, ny = -nx, -ny
        edge = (target[0] + nx * SPUR_SETBACK, target[1] + ny * SPUR_SETBACK)
        return [start, ((cx + edge[0]) / 2 + ax * 14, (cy + edge[1]) / 2 + ay * 14), edge]

    # ...and again the candidate is the DRAWN path, bow and all - see `path_is_clear`.
    spur = min(
        (spur_path(q) for q in sorted(plan.envelope, key=lambda v: math.hypot(v[0] - cx, v[1] - cy))),
        key=lambda p: (path_violations(p, crops, plan.sink_pond, brook_segs, plan.watercourses), polyline_len(p)),
    )
    s.lane(s.trim_off_marsh(clip_to_clear(spur, [*crops, *([toe_now] if toe_now else [])], 12.0)), width=5, clearance=LANE_CLEARANCE, worn=True)

    # the CONNECTOR, out to the frame
    # ...and the gate the connector starts FROM must itself be out of the crop. The skeleton's
    # gateway is a point in the seat frame, so on a cluster that sits against a concave stretch of
    # the fan it can land INSIDE the field envelope - and the connector then starts in the rice and
    # crosses the outline twice on its way out (Inashiro, GM 2026-08-12).
    gate = push_out_of(plan.envelope, to_screen((float(layout["gateway"][0]), float(layout["gateway"][1]))), SPUR_SETBACK)
    # THE TRACK LEAVES CLEAR OF THE WET TOE (GM 2026-08-12: "there's supposed to be a rule that
    # paths don't pass through marshland"). The marsh is not drawn until `stage_hinterland`, long
    # after this, so the router asks the ENGINE where it will be - `toe_band` is the same derivation
    # `hinterland()` lays the reeds on, factored out precisely so the two cannot disagree. With the
    # band in the obstacle list every straight-downslope bearing scores as a violation and the sweep
    # settles on a contour-following one, which is what a real valley track does anyway: roads run
    # ALONG the valley, they do not dive into the swamp at its foot.
    # ...and the wet ground is EVERY marsh, not just the toe band: the pond's reed fringe is drawn
    # back in `stage_sink`, before this, and a cohort sweep found ways ending in it on two maps.
    toe = s.toe_band()
    drawn_wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    track = connector_track(plan, gate, avoid=[list(plan.envelope), *crops], wet=([toe] if toe else []) + drawn_wet)
    s.lane(route_around(plan.envelope, track, SPUR_SETBACK), width=6, clearance=LANE_CLEARANCE, worn=True, connector=True)


def push_out_of(poly: Poly, p: Pt, margin: float) -> Pt:
    """Move `p` OUTSIDE `poly` by `margin`, on the normal of the outline EDGE nearest to it.

    Shared by the field spur's tip and the connector's route, which had the same defect for the same
    reason: both were pushed clear along one fixed map-wide direction (the seat's outward normal),
    which is only the right way out where the outline happens to run across it - so a spur tip
    finished 28 px inside the standing water. Projecting onto the nearest EDGE (not the nearest
    VERTEX - a point deep inside a lobe can have its nearest vertex right round the far side, and
    stepping out from there is a detour, not a fix) puts the way exactly where a track meeting a
    field goes: on the bund, just outside the crop. A point already clear is returned untouched, so
    this never drags a way back in."""
    ring = list(poly)
    n = len(ring)
    best: tuple[float, Pt, Pt, Pt] | None = None
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        q = seg_closest(p[0], p[1], a, b)
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        if best is None or d < best[0]:
            best = (d, q, a, b)
    assert best is not None  # a ring always has an edge
    d, q, a, b = best
    inside = point_in_poly(p[0], p[1], ring)
    if not inside and d > margin:
        return p
    nx, ny = unit(-(b[1] - a[1]), b[0] - a[0])
    cen = centroid(poly)
    if nx * (q[0] - cen[0]) + ny * (q[1] - cen[1]) < 0:
        nx, ny = -nx, -ny
    return (q[0] + nx * margin, q[1] + ny * margin)


def route_around(poly: Poly, path: Poly, margin: float, rounds: int = 6) -> Poly:
    """Bend a drawn way OUT of `poly` by walking its outline round the obstruction.

    `connector_track` sweeps forty bearings and keeps the LEAST-BAD when none is clean, which is the
    right call for a track that has to reach the frame somehow - but least-bad can still mean a leg
    cutting straight across a lobe of the fan, which is what the GM saw on Inashiro (2026-08-12).

    A track meeting a field GOES ROUND IT, and that is what this does literally: where a leg enters
    the outline at one edge and leaves at another, the outline's own vertices between those two
    edges are spliced in (the shorter way round), each stepped `margin` clear on its local normal.
    An earlier version inserted ONE waypoint at the mean of the crossings and re-ran; it converged a
    few pixels per round and ran out of rounds still crossing, because a point pushed off the middle
    of a lobe lands right beside the leg it came from. Following the boundary is both the correct
    detour and the one a farmer walks."""
    ring = list(poly)
    n = len(ring)
    out = [push_out_of(poly, q, margin) for q in path]
    for _ in range(rounds):
        redo: Poly = []
        cut = False
        for i in range(len(out) - 1):
            redo.append(out[i])
            a, b = out[i], out[i + 1]
            hits = [(k, h) for k in range(n) if segments_cross(a, b, ring[k], ring[(k + 1) % n]) and (h := seg_intersect(a, b, ring[k], ring[(k + 1) % n])) is not None]
            if len(hits) < 2:
                if (
                    hits
                ):  # pragma: no cover - a leg from outside to outside crosses a closed ring an EVEN number of times, so this is the guard for a leg grazing a vertex; no cohort map has produced one
                    redo.append(push_out_of(poly, hits[0][1], margin))
                    cut = True
                continue
            hits.sort(key=lambda kh: math.hypot(kh[1][0] - a[0], kh[1][1] - a[1]))
            k0, k1 = hits[0][0], hits[-1][0]
            fwd = [(k0 + 1 + t) % n for t in range((k1 - k0) % n)]
            bwd = [(k0 - t) % n for t in range((k0 - k1) % n)]
            way = fwd if len(fwd) <= len(bwd) else bwd
            redo += [push_out_of(poly, ring[t], margin) for t in way]
            cut = True
        redo.append(out[-1])
        out = redo
        if not cut:
            break
    return out


def clip_to_clear(pts: Poly, obstacles: Sequence[Poly], margin: float, step: float = 8.0, lines: Sequence[tuple[Pt, Pt]] = (), line_margin: float = 14.0) -> Poly:
    """Shorten a polyline so it stops before the first ground it may not cross.

    Used on the cluster's lane arms. Dragging an offending VERTEX back toward the cluster was tried
    first and is not reliable: a vertex deep inside a large hem plot may not escape in the steps
    allowed, and it distorts the skeleton on the way. Truncating is both simpler and more honest -
    the lane ends where the crop begins, which is what a village lane does. Always returns at least
    a two-point line so the caller still has a lane."""
    if not obstacles and not lines:
        return pts

    def fouled(q: Pt) -> bool:
        if any(seg_dist(q[0], q[1], a, b) < line_margin for a, b in lines):
            return True
        return any(point_in_poly(q[0], q[1], list(o)) or min(seg_dist(q[0], q[1], o[j], o[(j + 1) % len(o)]) for j in range(len(o))) < margin for o in obstacles)

    out: Poly = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        run = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(run / step))
        last = a
        for k in range(1, n + 1):
            q = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            if fouled(q):
                # NOTHING is returned if the surviving run is too short to be a lane. The first
                # version fell back to the ORIGINAL first segment here, which meant a lane blocked
                # immediately was drawn in full, unclipped - a fallback that does the opposite of
                # the function's job. A skeleton arm with nowhere to go is not drawn at all.
                trimmed = out + [last]
                return trimmed if polyline_len(trimmed) >= 70.0 else []
            last = q
        out.append(b)
    return out


def polyline_len(pts: Poly) -> float:
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def connector_track(plan: SitePlan, start: Pt, avoid: Sequence[Poly] = (), reach: float = 4000.0, wet: Sequence[Poly] = ()) -> Poly:
    """The track from the settlement's gateway to the map edge, steered clear of the crop.

    Bearings are tried outward from "away from the field, leaning downslope" - the direction a real
    track leaves by, since the wider world is downstream and the paddy is not walkable - and the
    first that reaches the frame without crossing the field envelope wins. Sweeping alternate sides
    at growing angles keeps the chosen bearing as close to the ideal as the geometry allows instead
    of jumping to whatever happens to be clear.

    The track is drawn PAST the canvas edge, not up to it: the gate wants an endpoint at the frame,
    and the crop is set later from the hard features, so a track that overshoots is trimmed by the
    viewBox while one that stops short reads as a dead end."""
    dx, dy = plan.fall
    ox, oy = plan.seat["out"]
    base = math.degrees(math.atan2(0.55 * oy + 0.85 * dy, 0.55 * ox + 0.85 * dx))
    # ...and clear of the POND. A track skirting the tameike ends up crossing the short drainage
    # ditch between field and pond at a very shallow angle, and an oblique crossing needs a much
    # longer deck than a square one - `bridges_span_their_water` caught exactly that, with an
    # abutment standing in the water. Steering around the pond removes the crossing instead of
    # widening the bridge, which is also what a real track does: you ford or bridge a ditch where it
    # is narrow and square, not where it fans into a reservoir.
    pond = plan.sink_pond
    brook = [(plan.sink_brook[i], plan.sink_brook[i + 1]) for i in range(len(plan.sink_brook) - 1)]
    waters = plan.watercourses
    # A FINE sweep, nearest bearing first. Sixteen coarse tries were enough when the only obstacle
    # was the field; with the pond and the drain brook added, a whole quadrant can be closed and a
    # coarse sweep steps straight over the gap between them - which drops through to the fallback,
    # and the fallback ignores every constraint. Forty bearings is a few hundred point tests.
    # The gateway can itself stand on hem ground when the cluster's back is partly hemmed, and a
    # start point inside a crop makes EVERY bearing fail - which is how the fallback below came to
    # fire at all. Step it clear first.
    start = pull_clear(start, (plan.seat["cx"], plan.seat["cy"]), avoid or [plan.envelope], 12.0)
    best: tuple[tuple[int, int], Poly] | None = None
    for swing in sorted((9.0 * k for k in range(-20, 21)), key=abs):
        theta = math.radians(base + swing)
        # THE CANDIDATE IS THE PATH THAT WILL BE DRAWN, not the straight line to its endpoint. A
        # foot track wanders, so the drawn polyline bows ~40 px either side of the bearing - and
        # testing the CHORD while drawing the BOW is how a track ended up crossing a hem plot and a
        # drainage ditch on maps whose straight line cleared both. (The skill's dev notes state the
        # rule in the label-probe case: a probe must measure what the check will measure. It applies
        # to routing just as squarely.)
        px, py = -math.sin(theta), math.cos(theta)
        path: Poly = [
            start,
            (start[0] + math.cos(theta) * reach * 0.18 + px * 34, start[1] + math.sin(theta) * reach * 0.18 + py * 34),
            (start[0] + math.cos(theta) * reach * 0.44 - px * 46, start[1] + math.sin(theta) * reach * 0.44 - py * 46),
            (start[0] + math.cos(theta) * reach, start[1] + math.sin(theta) * reach),
        ]
        # WET GROUND OUTRANKS EVERYTHING ELSE (GM 2026-08-12). The toe marsh is a contour band
        # spanning the whole canvas below the crop, so on a map whose cluster sits in a pocket of
        # the fan NO bearing is clean of both - and a single violation count lets one crop clip
        # outweigh a thousand feet of swamp. Scoring them separately, wet first, makes the sweep
        # leave along the contour and exit the frame ABOVE the marsh, which is what a real valley
        # road does; whatever crop it then clips is bent round afterwards by `route_around`, which
        # the marsh has no equivalent of because a track through a marsh cannot be nudged dry.
        soaked = sum(path_violations(path, [w], None, ()) for w in wet)  # the WET POLYGON only - pond and brook are scored once, below
        violations = path_violations(path, avoid or [plan.envelope], pond, brook, waters)
        if soaked == 0 and violations == 0:
            return path
        if best is None or (soaked, violations) < best[0]:
            best = ((soaked, violations), path)
    # NO CLEAN BEARING: take the LEAST-BAD one rather than a fixed escape route.
    #
    # This used to return `start` plus a ray straight away from the field, and that fallback is what
    # actually shipped the defect: it consulted nothing, so on any map where the sweep came up empty
    # the connector was drawn through the hem and across the drainage ditch, failing three checks at
    # once. A fallback that ignores the constraints is worse than no fallback, because it looks like
    # a decision. Scoring every candidate and keeping the best means a hard map degrades by one
    # crossing instead of by everything.
    assert best is not None
    return best[1]


def path_violations(path: Poly, avoid: Sequence[Poly], pond: tuple[float, float, float, float] | None, brook: Sequence[tuple[Pt, Pt]], waters: Sequence[tuple[Pt, Pt]] = ()) -> int:
    """How many segments of a drawn way foul the crop, the pond or the drain brook (0 = clear).

    A COUNT rather than a boolean, so a caller with no clean option can still take the least-bad one.

    The pond and the brook are avoided outright rather than bridged: a way meeting water at a
    shallow angle needs a far longer deck than a square crossing, and `bridges_span_their_water`
    measures the deck the engine actually drew. Going around removes the crossing entirely, which
    is also what a real track does - you ford a ditch where it is narrow and square."""
    bad = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if (
            (pond is not None and crosses_disc(a, b, (pond[0], pond[1]), max(pond[2], pond[3]) + 80.0))
            or any(seg_intersect(a, b, p, q) is not None for p, q in brook)
            or any(crosses_poly(a, b, poly) for poly in avoid)
            or any(shallow_crossing(a, b, p, q) for p, q in waters)
            or any(crossing_lands_on_crop(a, b, p, q, avoid) for p, q in waters)
        ):
            bad += 1
    # ...and a way may not bridge TWICE within a deck's length. `s.bridges()` decks every crossing
    # it finds, so a way cutting two ditches a few tens of px apart gets two decks drawn on top of
    # each other - which `features_do_not_overlap` reads as a ('bridges', 'bridges') pair, and which
    # is a drawing error rather than a siting one. Crossing further along, where the ditches have
    # separated, is what a track does anyway.
    hits = [x for i in range(len(path) - 1) for p, q in waters if (x := seg_intersect(path[i], path[i + 1], p, q)) is not None]
    bad += sum(1 for i, u in enumerate(hits) for v in hits[i + 1 :] if math.hypot(u[0] - v[0], u[1] - v[1]) < 46.0)
    return bad


def crossing_lands_on_crop(a: Pt, b: Pt, p: Pt, q: Pt, crops: Sequence[Poly], pad: float = 14.0) -> bool:
    """Does the way a->b meet the watercourse p->q at a point standing on cropland?

    A crossing gets a DECK, and a deck laid on a hem plot is a bridge across the barley
    (`features_do_not_overlap` reports it as a dry_plots/bridges pair). The way is free to cross the
    same ditch a little further along where the crop stops - which is where the bund is anyway."""
    hit = seg_intersect(a, b, p, q)
    if hit is None:
        return False
    return any(point_in_poly(hit[0], hit[1], list(c)) or min(seg_dist(hit[0], hit[1], c[i], c[(i + 1) % len(c)]) for i in range(len(c))) < pad for c in crops)


def shallow_crossing(a: Pt, b: Pt, p: Pt, q: Pt, limit_deg: float = 42.0) -> bool:
    """Does the way a->b cross the watercourse p->q at a SHALLOW angle?

    A way is allowed to cross an irrigation ditch - that is what a plank or a small timber bridge is
    for, and forbidding it outright would cut the field spur off from the field. What it may not do
    is cross at a slant: an oblique crossing needs a deck of (width + deck_w x |cos|) / sin plus a
    landing each side, so `bridges_span_their_water` fails it with an abutment standing in the
    water. Steering the way to meet the ditch square is the fix a farmer would recognize."""
    if seg_intersect(a, b, p, q) is None:
        return False
    ux, uy = unit(b[0] - a[0], b[1] - a[1])
    vx, vy = unit(q[0] - p[0], q[1] - p[1])
    return abs(math.degrees(math.asin(max(-1.0, min(1.0, ux * vy - uy * vx))))) < limit_deg


# ---- STAGE 5: the homesteads --------------------------------------------------------------------


def front_row(plan: SitePlan, count: int, standoff: float = 46.0) -> list[Pt]:
    """Seats for the row of homesteads that FRONTS the field, offset from the field OUTLINE itself.

    Offsetting from the cluster band's straight near face is not the same thing and is not good
    enough: the outline curves away from the band, so a row laid along the face can sit 32 px from
    the field at its middle and 300 px from it at its ends, and `field_ringed` (five farmhouses
    within 165 px of the outline) then fails on a map whose cluster is plainly beside its paddy.
    Following the outline also draws better - a farming hamlet's front row bends with the field edge
    the way a real one does, rather than ruling a straight line across a curved margin."""
    env = plan.envelope
    cen = centroid(env)
    seat = plan.seat
    ax, ay = seat["along"]
    # the stretch of outline this cluster fronts: everything within the band's lateral reach
    # The row spans 1.6x the band's own length along the outline. Confined to `lat` exactly, all its
    # candidates come off one short arc - and if that arc happens to be blocked (crop up to the bund,
    # a delivery ditch's corridor, the field spur), the whole row is refused together and the field
    # ends up ringed by four houses instead of five. Wrapping further round the field costs nothing:
    # a seat too far along is dropped by the caller's own band test.
    span = [(i, p) for i, p in enumerate(env) if abs((p[0] - seat["anchor"][0]) * ax + (p[1] - seat["anchor"][1]) * ay) <= seat["lat"] * 1.6]
    if len(span) < 2:  # pragma: no cover - a band always spans several outline vertices
        return []
    span.sort(key=lambda ip: (ip[1][0] - seat["anchor"][0]) * ax + (ip[1][1] - seat["anchor"][1]) * ay)
    out: list[Pt] = []
    for k in range(count):
        idx = span[min(len(span) - 1, round(k * (len(span) - 1) / max(1, count - 1)))][0]
        a, b = env[idx], env[(idx + 1) % len(env)]
        nx, ny = unit(-(b[1] - a[1]), b[0] - a[0])
        if nx * (a[0] - cen[0]) + ny * (a[1] - cen[1]) < 0:
            nx, ny = -nx, -ny
        out.append((a[0] + nx * standoff, a[1] + ny * standoff))
    return out


def lane_frontage(s: Settlement, seat: Mapping[str, Any], step: float = 86.0) -> list[Pt]:
    """Candidate seats along BOTH verges of every internal lane, just outside its no-build corridor.

    Ordered from the cluster's center outward, so the lanes fill from their busy end. The connector
    is skipped: it is the track OUT of the settlement, and lining it with farmhouses would string the
    hamlet along the road instead of nucleating it (that is the `linear` settlement form, a
    different archetype)."""
    out: list[Pt] = []
    off = LANE_FRONTAGE_STANDOFF
    for lane in s.M.get("lanes", []):
        if lane.get("connector"):
            continue
        pts = lane["pts"]
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            run = math.hypot(x1 - x0, y1 - y0)
            nx, ny = unit(-(y1 - y0), x1 - x0)
            k = 1
            while k * step < run:
                px, py = x0 + (x1 - x0) * (k * step / run), y0 + (y1 - y0) * (k * step / run)
                out += [(px + nx * off, py + ny * off), (px - nx * off, py - ny * off)]
                k += 1
    return sorted(out, key=lambda q: math.hypot(q[0] - seat["cx"], q[1] - seat["cy"]))


def stage_homesteads(s: Settlement, plan: SitePlan) -> None:
    """Seat every declared household, and KNOW whether it worked.

    `households_consistent` wants the occupied farmhouses within 0.85-1.05x the declared households -
    a to-scale map depicts essentially every household - so a hamlet that declares 15 and seats 12
    fails, and the authored maps deal with that by tuning a hand-written candidate loop until the
    number comes out. The script instead asks the placer, which is the only thing that actually knows
    whether a seat is free: it draws candidates from the rolled cluster shape and, if the quota is
    still short, GROWS the band and draws more, up to a cap.

    Growing rather than re-rolling is deliberate. A retry with a different seed would re-roll the
    whole map to fix a local shortfall - the expensive, whack-a-mole loop the skill's dev notes warn
    about. Widening the band changes only the ground the candidates come from, so the houses already
    seated stay exactly where they are and the map converges instead of churning."""
    # A YARD KEEPS ITS SUN (GM 2026-08-13; researched in research/homesteads.md, "The threshing
    # yard's sun"). 39 ft is the 9-to-3 drying window at 38N in the 10th month for a minka's ~20 ft
    # ridge; the noon figure is 21. The engine's rule is opt-in and this is where the scripted tier
    # opts in - the hand-authored maps keep their packing until they are converted.
    s.sun_corridor(SUN_CORRIDOR_FT)
    seat = plan.seat
    ax, ay = seat["along"]
    ox, oy = seat["out"]
    rng = random.Random((plan.spec.seed * 2654435761) & 0xFFFFFFFF)
    placed = 0
    lat, dep = seat["lat"], seat["dep"]

    # THE FRONT ROW GOES DOWN FIRST, along the band's field-facing face. A cluster seeded only by
    # its SHAPE fills its whole depth evenly, and on a small hamlet that can leave the field ringed
    # by four houses where `field_ringed` wants five - the map then reads as a settlement that
    # happens to be near a paddy rather than one that works it. Seating a row against the margin
    # first is also just what a farming hamlet looks like: the houses front the field they farm, and
    # the back rows fill in behind them.
    # (no quota guard here: the row is capped at 8 seats and the tier's floor is 10 households, so
    # the front row alone can never meet the ask)
    # TWO passes at two standoffs. `field_ringed` wants five farmhouses within 165 px of the field
    # outline, and a single row of eight candidates at one standoff can land four when the near
    # ground is awkward - the placer refuses a bundle that laps a bund or a ditch, and every refusal
    # is a house that ends up in the back rows instead. Offering the same row again a little further
    # out costs nothing when the first pass filled it and rescues the ring when it did not.
    # EVERY SEAT MUST LIE IN THE BAND. The front row follows the field OUTLINE and the frontage rows
    # follow the lanes, and both can wander well past the cluster on a long fan - which produced a
    # nucleated hamlet with three or four farmsteads strung hundreds of px down the margin. That is
    # a form defect on its own (a nucleus is supposed to read as a nucleus), and it was ALSO the
    # cause of three separate gate failures: a windbreak sized off the furthest house became a green
    # blanket, a copse over the full house bbox left the map no blank ground, and a stray farm past
    # the last well tripped `settlement_dwellings_watered`. Fixing the seats fixes all of it at the
    # source, which is why the percentile guards elsewhere are belt-and-braces rather than the cure.
    bound = 1.15 * math.hypot(lat, dep)

    def in_band(q: Pt) -> bool:
        return math.hypot(q[0] - seat["cx"], q[1] - seat["cy"]) <= bound

    # THREE standoffs, not two. `field_ringed` wants five farmhouses within 165 px of the field
    # outline and the placer refuses any bundle that laps a bund or a ditch, so a single ring of
    # candidates can land four on awkward ground. Each extra pass is free when the earlier one
    # filled the row.
    # The FRONT ROW is allowed a little further out than the rest - a house hugging the field is
    # part of the settlement wherever the band's nominal circle happens to fall, and `field_ringed`
    # wants five of them within 165 px of the outline.
    # Standoffs run out to 150 px, which is still inside `field_ringed`'s 165 px band. The near
    # ground is often the busiest on the map - crop up to the bund, the collector's out-of-crop
    # stretches with their corridors, the field spur - so a row that stops at 92 px can land four
    # houses where five are wanted while perfectly good ground sits at 120. A farmhouse 150 px from
    # its paddy is still a farmhouse on its paddy.
    for standoff in (46.0, 56.0, 66.0, 78.0, 92.0, 110.0, 130.0, 150.0):
        if placed >= plan.spec.households:
            break  # pragma: no cover - the ask-met guards. The row rarely fills a whole hamlet by itself on real ground, but eight standoffs x twelve seats CAN offer more than the households asked for, and a row that overshoots fails households_consistent
        for fx, fy in front_row(plan, min(plan.spec.households, 12), standoff=standoff):
            if placed >= plan.spec.households:
                break  # pragma: no cover - the ask-met guards. The row rarely fills a whole hamlet by itself on real ground, but eight standoffs x twelve seats CAN offer more than the households asked for, and a row that overshoots fails households_consistent
            if math.hypot(fx - seat["cx"], fy - seat["cy"]) <= bound * 1.3 and s.try_place(fx, fy, "plain"):
                placed += 1
    # ...then rows FLANKING the lanes, before any shape fill. A lane exists to be fronted, and a
    # cluster seeded only by its shape leaves them running across empty middle: the review of the
    # first draft measured a median house-to-lane distance of 94 ft against Ikegami's 55, with one
    # lane dead-ending in open ground and no house at its end. Offering the placer seats at exactly
    # the corridor's edge is what puts the doors on the street.
    for lx, ly in lane_frontage(s, seat):
        if placed >= plan.spec.households:
            break
        if in_band((lx, ly)) and s.try_place(lx, ly, "plain"):
            placed += 1
    for attempt in range(4):
        if placed >= plan.spec.households:
            break
        # each round widens the band a little (and reaches a little further back from the field)
        wlat, wdep = lat * (1.0 + 0.22 * attempt), dep * (1.0 + 0.16 * attempt)
        want = plan.spec.households * 6 + 30
        for lx, ly in s.cluster_seeds(plan.cluster_shape, 0.0, 0.0, wlat, wdep, want, rng, record=(attempt == 0)):
            if placed >= plan.spec.households:
                break
            # THE CLOUD LEANS TOWARD THE FIELD. `cluster_seeds` returns a shape symmetric about the
            # band's middle, which spreads a hamlet's houses as far behind the settlement as in front
            # of it - and the ground in FRONT is the ground that matters: `field_ringed` wants five
            # farmhouses within 165 px of the outline, and on a map whose near margin is largely crop
            # and ditch corridor only four of them land there. Compressing the away-from-field
            # coordinate pulls the whole cloud a quarter closer without changing its shape or count,
            # which is also how a farming hamlet really sits - the houses crowd the fields they work
            # and thin out behind.
            ly = -wdep + (ly + wdep) * 0.75
            if s.try_place(seat["cx"] + ax * lx + ox * ly, seat["cy"] + ay * lx + oy * ly, "plain"):
                placed += 1
    plan.placed = s.farmsteads()


# ---- STAGE 6: what stands among the houses ------------------------------------------------------


def stage_appurtenances(s: Settlement, plan: SitePlan) -> None:
    """Communal wells and shared draft byres, dropped into the courtyards the homesteads left.

    AFTER the houses (they slot into the gaps the final layout produced, which is a thing only the
    finished layout knows) and BEFORE the grove (whose canopy then skips them). Both are sized off
    the houses that actually landed, not off the declared household count: a byre is roughly one per
    four or five households, and the wells cover the cluster's real extent."""
    houses = s.M.get("houses", [])
    if not houses:  # pragma: no cover - a hamlet with no houses fails the gate long before here
        return
    place_wells(s, plan, houses)
    s.draft_byres(fraction=0.22, gap=60)


def well_target(households: int) -> int:
    """How many communal draw-wells a hamlet of this size keeps.

    `wells_sized_to_population` wants 2-20 households per well at hamlet scale (the setting's
    deliberate prosperity liberty runs generous wells), so the band for 12 households is 1 to 6.
    One per ~6 households sits mid-band and matches what the authored hamlets draw - a couple of
    shared wells among the courtyards, not one per farm and not one for the whole place."""
    return max(1, min(6, round(households / 6.0)))


def place_wells(s: Settlement, plan: SitePlan, houses: Sequence[Mapping[str, Any]]) -> int:
    """Seat the communal wells INSIDE the house cloud, not on a box around it.

    The engine's `place_wells` sweeps a grid over a bbox, which is right for a town's street blocks
    and wrong for a loose farm cluster: the bbox corners are open ground, so a well lands past the
    outermost homestead and, being a hard crop feature with a 16 px extent, drags the map's frame
    out after it and leaves a band of empty scrub on that side
    (`crop_not_held_open_by_one_feature`). Insetting the bbox was tried first and is not the fix -
    it starves an elongated cluster of wells entirely, because the inset box no longer holds a grid
    cell (`settlement_has_wells`, seed 3).

    So the seats are derived from the HOUSES: a candidate must have several homesteads around it and
    none too far, which is what "among the dwellings" means, and the innermost candidates are tried
    first. `well_at` gives the engine's own verdict on each - it refuses a seat on a lane, a crop, a
    footprint or too near another well - so nothing here restates a placement rule."""
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    ccx, ccy = sum(xs) / len(xs), sum(ys) / len(ys)
    want = well_target(plan.spec.households)
    placed: list[Pt] = []
    # A RELAXATION LADDER, not a single rule. The tight neighborhood test is right for a compact
    # cluster and impossible for a stretched one: an `elongated` cluster strung along a margin has
    # no point with three homesteads inside 190 px, so the strict pass found nothing at all and the
    # map shipped with no well (seeds 3 and 12). A settlement WITHOUT a well is a much worse map
    # than one whose well sits a little wide, so the test loosens until it finds seats. It never
    # loosens into "anywhere": every seat still has to be nearer a house than the crop.
    # Only the THIRD-nearest distance relaxes - the "is this in a neighborhood" test. The distance to
    # the NEAREST house stays tight, because `wells_among_dwellings` is a 95 px gap verdict against
    # the served building's edge: a well 220 px from its closest farmhouse is standing in the fields
    # by any measure, and relaxing that rung traded one failure for another.
    # The last rung also serves a PAIR. Every rung above asks for three homesteads around a seat,
    # which is the right shape for a nucleus and leaves a two-farm satellite with no well of its own
    # - and then the coverage pass cannot rescue it either, because the ground among two farms is
    # their own courtyards. Seed 18 stranded exactly that: a pair 500 px off the cluster, 760 and
    # 777 px from the nearest well, with all 118 legal-neighbourhood probes around them refused.
    # Two households sharing a draw-well is an ordinary thing; three is not a threshold nature knows.
    for third, nearest, want_near in ((190.0, 105.0, 3), (300.0, 110.0, 3), (520.0, 112.0, 3), (520.0, 112.0, 2)):
        if len(placed) >= want:
            break
        seats: list[tuple[float, float, float]] = []
        step = 22.0
        y = min(ys)
        while y <= max(ys):
            x = min(xs)
            while x <= max(xs):
                near = sorted(math.hypot(x - h["x"], y - h["y"]) for h in houses)
                if len(near) >= want_near and near[want_near - 1] <= third and near[0] <= nearest:
                    seats.append((math.hypot(x - ccx, y - ccy), x, y))
                x += step
            y += step
        for _, x, y in sorted(seats):
            if len(placed) >= want:
                break
            if any(math.hypot(x - px, y - py) < 170.0 for px, py in placed):
                continue  # `wells_not_clustered`: shared wells serve separate courtyards
            if s.well_at(x, y):
                placed.append((x, y))
    # ...then a COVERAGE pass. `settlement_dwellings_watered` gives every dwelling ~760 real feet to
    # the nearest well, channel, pond or stream - generous, and still not automatic once a cluster is
    # sized from the real bundle pitch and runs 700+ px along its margin: a single well at one end
    # leaves the far end dry. So any house still out of reach gets a well sought beside it.
    reach = 760.0 / max(plan.ftpx, 0.01)
    for h in houses:
        if any(math.hypot(h["x"] - px, h["y"] - py) <= reach for px, py in placed):
            continue
        # A RING PROBE, spiraling out from the house, asking `well_at` directly.
        #
        # AND EVERY CANDIDATE MUST STILL STAND AMONG THE DWELLINGS - near SOME house, not necessarily
        # the one being rescued. `wells_among_dwellings` is a 95 px edge-gap verdict against the
        # served building, and this probe used to take the first seat `well_at` allowed at any radius
        # out to 340. That was harmless while nothing reached this branch, and stopped being harmless
        # the moment the sun corridor (2026-08-13) spread a cluster enough to strand a household:
        # seed 18 seated a well 161 px from its nearest dwelling. Capping the RADIUS was the obvious
        # fix and the wrong one - it just traded the failure for `settlement_dwellings_watered`,
        # leaving the household dry. The honest constraint is the one the check states: a well may
        # be dug well away from the farm it rescues, as long as it is in somebody's courtyard.
        #
        # `open_seat` was tried here first and is the wrong tool: it optimizes a seat over a
        # RECTANGLE - furthest from what it is told to clear, ties toward the center - and it
        # returned None at every radius from 60 to 430 px around a stranded farmstead that had a
        # perfectly legal spot 40 px to its east. What this needs is not the best seat in a region
        # but ANY seat near THIS house, so it asks the question that way round, and it asks it of
        # `well_at`, which is the call that actually places a well.
        spot = None  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
        for radius in range(40, 340, 20):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
            for bearing in range(0, 360, 20):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                cand = (
                    h["x"] + math.cos(math.radians(bearing)) * radius,
                    h["y"] + math.sin(math.radians(bearing)) * radius,
                )  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if not (
                    min(xs) <= cand[0] <= max(xs) and min(ys) <= cand[1] <= max(ys)
                ):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # a rescue well still sits INSIDE the house cloud. A wellhead is a hard crop  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # feature with a 16 px extent, so one seated past the outermost homestead drags  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # the frame out after it (`crop_not_held_open_by_one_feature`) - the same reason  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # the grid above is laid over the cloud rather than a box grown around it.  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    continue  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if not any(math.hypot(cand[0] - hh2["x"], cand[1] - hh2["y"]) <= 95.0 for hh2 in houses):  # pragma: no cover - the rescue's among-the-dwellings floor
                    continue  # pragma: no cover - centre distance <= 95 is strictly inside the check's 95 px EDGE gap
                if any(
                    math.hypot(cand[0] - px, cand[1] - py) < 110.0 for px, py in placed
                ):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    continue  # `wells_not_clustered`: shared wells serve separate courtyards  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if s.well_at(cand[0], cand[1]):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    spot = cand  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    break  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
            if spot is not None:  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                placed.append(spot)  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                break  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
    if not placed:
        # LAST RESORT: ask the engine. A settlement with NO well fails the gate outright, and by
        # this point the lattice has been refused everywhere - which means the courtyards are full,
        # not that there is no room. `open_seat` runs the engine's own `_fits` over the ground and
        # returns the best clear spot or None, which is the documented answer to "this pocket needs
        # one more X" and finds seats a hand-rolled scan misses (the skill's dev notes: a manifest
        # scan cannot predict `_fits`).
        spot = s.open_seat(
            (min(xs), min(ys), max(xs), max(ys)), 16.0, 16.0, well=True
        )  # pragma: no cover - reached only when the lattice above found NOTHING, which the bundle-pitch fix made rare; a settlement with no well fails the gate outright, so the branch stays
        if spot is not None and s.well_at(spot[0], spot[1]):  # pragma: no cover - the last-resort seat; unreached since the bundle-pitch fix left the courtyards open
            placed.append(spot)
    return len(placed)


# ---- STAGE 7: the ground between everything ------------------------------------------------------


def stage_hinterland(s: Settlement, plan: SitePlan) -> None:
    """The non-arable ground: reed marsh at the wet toe, cut-over scrub everywhere else.

    One engine call, because the engine already knows the doctrine (China-first: the south-China rice
    hills were stripped for fuel and timber over centuries, so the DOMINANT cover past the fields is
    scrub, not forest). It runs after the structures so the scatter skips them, and before the woods
    so the woodland patches draw on top of the scrub they stand in."""
    s.hinterland()


def open_ground_patches(s: Settlement, plan: SitePlan, count: int, size: float = 250.0) -> list[Poly]:
    """Find `count` patches of ground still open enough for a managed woodland - by SCANNING.

    Woodland (coppice, bamboo, tung-oil - the "economic forest") is a few discrete patches on the
    higher, farther ground, set back from the sun-needing crops by the scrub between. Ikegami places
    three by hand. The script cannot hand-place, so it scans a coarse lattice over the canvas and
    scores each candidate square on the two things that actually decide the answer:

      - it must be CLEAR of the crops by a real margin, and clear by MORE on the crop's sunny side,
        because a canopy south of a field shades it (this mirrors `woodland_clear_of_crops`, whose
        set-back is bigger to the south for exactly that reason);
      - it must be clear of the settlement, its lanes, its grove and its water.

    Among the candidates that qualify it prefers the ones furthest from the crop and highest up the
    slope, and it keeps them apart from each other so three patches read as three woods rather than
    one ragged mass. This is the stage that most obviously could not be done by pinning coordinates:
    "where is there still room" is a question about the map as it stands at that moment."""
    dx, dy = plan.fall
    keep: list[tuple[float, float, float]] = []  # (x, y, radius) of everything to stay clear of
    for h in s.M.get("houses", []):
        keep.append((h["x"], h["y"], 150.0))
    for wl in s.M.get("wells", []):
        keep.append((wl["x"], wl["y"], 90.0))
    pond = s.M.get("pond")
    if pond:
        keep.append((pond[0], pond[1], max(pond[2], pond[3]) + 120.0))
    lanes: list[tuple[Poly, float]] = [(ln["pts"], 70.0) for ln in s.M.get("lanes", [])]
    # THE COPPICE IS A DISTINCT WOOD from the fengshui grove, and must not merge into it
    # (`woodland_clear_of_grove`, which measures to each grove CLUMP, not to the belt outline - so a
    # patch merely touching the belt's edge already fails). Both groves count: the windbreak belt
    # behind the cluster, and the copse scattered through the gaps among the houses, whose footprint
    # is the house bbox. The margin is generous because a clump's drawn canopy overhangs its
    # recorded radius, and because two woods that nearly touch read as one ragged mass anyway.
    # Kept clear by RECTANGLE, not by a circle around the bounding box. A belt is a long thin band
    # and a cluster is usually longer than it is deep, so a circle sized to the LONG side leaves the
    # short side hugely over-reserved while a circle sized any tighter under-covers the ends - and
    # the ends are exactly where a patch slips in and merges with the grove.
    keep_rects: list[tuple[float, float, float, float]] = [title_pocket(s, plan)]
    if plan.belt:
        keep_rects.append((min(p[0] for p in plan.belt) - 110.0, min(p[1] for p in plan.belt) - 110.0, max(p[0] for p in plan.belt) + 110.0, max(p[1] for p in plan.belt) + 110.0))
    hxs = [h["x"] for h in s.M.get("houses", [])]
    hys = [h["y"] for h in s.M.get("houses", [])]
    if hxs:  # the copse's ground, which is the house cloud
        keep_rects.append((min(hxs) - 110.0, min(hys) - 110.0, max(hxs) + 110.0, max(hys) + 110.0))
    streams: list[tuple[Poly, float]] = [(st["poly"], 60.0) for st in s.M.get("streams", [])]
    crops: list[Poly] = [list(plan.envelope)] + [[(float(v[0]), float(v[1])) for v in d["poly"]] for d in s.M.get("dry_plots", [])]
    _hx = [h["x"] for h in s.M.get("houses", [])] or [plan.W / 2]
    _hy = [h["y"] for h in s.M.get("houses", [])] or [plan.H / 2]
    ccx, ccy = sum(_hx) / len(_hx), sum(_hy) / len(_hy)

    # THE PATCHES MUST NOT STRETCH THE FRAME. `crop_to_content` frames the map to its HARD features,
    # and a woodland patch is one - so a patch parked in a far corner of the working canvas drags the
    # crop out with it, leaving a band of empty scrub on one side and (worse) putting the map edge
    # beyond the reach of the drain brook, which then no longer runs off the frame. That is three
    # gate failures from one badly-sited wood: `crop_not_held_open_by_one_feature`,
    # `stream_runs_off_edge` and `stream_end_anchored`. So the scan is confined to the ground the
    # map already occupies, expanded by a margin - a coppice stands on the settlement's own high
    # ground, not a quarter mile out in nowhere.
    x0, y0, x1, y1 = content_box(s, plan, pad=210.0)
    half = size / 2.0
    step = 90.0
    chosen: list[Poly] = []
    scored: list[tuple[float, float, float]] = []
    y = max(half + 40.0, y0)
    while y <= min(plan.H - half - 40.0, y1):
        x = max(half + 40.0, x0)
        while x <= min(plan.W - half - 40.0, x1):
            gap = _clear_gap((x, y), half, crops, dy)
            if (
                gap is not None
                and not any(math.hypot(x - kx, y - ky) < kr + half for kx, ky, kr in keep)
                and not any(rx0 - half < x < rx1 + half and ry0 - half < y < ry1 + half for rx0, ry0, rx1, ry1 in keep_rects)
                and not any(_near_line((x, y), half, pts, pad) for pts, pad in lanes + streams)
            ):
                # PREFER THE NEAREST QUALIFYING GROUND, leaning upslope. The first version of this
                # maximized distance from the crop instead, which sounds right and is wrong twice
                # over: it drove every patch to the canvas's far upslope margin, where the dedupe
                # radius strung them out along one line at identical height, and then the crop -
                # which frames to the HARD features and lets commons bleed off-frame - cut three of
                # the four off the sheet entirely. A settlement's coppice is walked to daily for
                # fuel and fodder; it stands on the back slope behind the houses, as close as the
                # crop set-back allows. The keep-outs above are what make it far ENOUGH.
                upslope = -((x - ccx) * dx + (y - ccy) * dy)
                scored.append((-math.hypot(x - ccx, y - ccy) + 0.35 * upslope, x, y))
            x += step
        y += step
    for _, x, y in sorted(scored, reverse=True):
        if len(chosen) >= count:
            break
        if any(math.hypot(x - c[0][0] - half, y - c[0][1] - half) < size * 1.5 for c in chosen):
            continue
        chosen.append([(x - half, y - half), (x + half, y - half), (x + half, y + half), (x - half, y + half)])
    return chosen


def content_box(s: Settlement, plan: SitePlan, pad: float = 0.0) -> tuple[float, float, float, float]:
    """The bounding box of everything the crop will frame to - the field, its hem, the homesteads and
    the pond - grown by `pad`. Read from the manifest, so it tracks whatever actually got drawn."""
    xs: list[float] = [p[0] for p in plan.envelope]
    ys: list[float] = [p[1] for p in plan.envelope]
    for d in s.M.get("dry_plots", []):
        xs += [float(v[0]) for v in d["poly"]]
        ys += [float(v[1]) for v in d["poly"]]
    for h in s.M.get("houses", []):
        xs.append(h["x"])
        ys.append(h["y"])
    pond = s.M.get("pond")
    if pond:
        xs += [pond[0] - pond[2], pond[0] + pond[2]]
        ys += [pond[1] - pond[3], pond[1] + pond[3]]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def title_pocket(s: Settlement, plan: SitePlan, w: float = 300.0, h: float = 190.0) -> tuple[float, float, float, float]:
    """Ground held back so the map has somewhere to put its NAME.

    `title()` scans the framed window for a box clearing every feature and falls back to a corner
    overlap when there is none - and on a hamlet the blank ground is a short list: the field takes
    the middle, the hem the high margin, the marsh the whole low toe, the cluster and its grove one
    flank. That leaves the lateral corners, which is exactly where the coppice scan wants to go
    (`open_ground_patches` prefers the nearest qualifying ground). Both cannot have them.

    So one corner of the map's content is reserved before the coppice is sited. The corner chosen is
    the one furthest from the field's middle AND from the houses - the emptiest quarter of the sheet,
    which is where a reader would expect the cartouche anyway. It is a reservation, not a placement:
    `title()` still does its own search and may well sit somewhere else."""
    x0, y0, x1, y1 = content_box(s, plan, pad=30.0)
    # ASK THE ENGINE WHICH GROUND IS ACTUALLY BLANK, rather than assuming a corner is.
    #
    # `_blank_label_spot` is the same scan `title()` will run, so this reserves ground the title can
    # really use. Picking "the corner furthest from the field and the houses" was tried first and is
    # not the same thing: on the reference map that corner already held the reed marsh - which IS a
    # title obstacle, being a distinct wet surface rather than sparse ground cover - so the pocket
    # was reserved over ground the title could never have taken, the coppice went somewhere else for
    # nothing, and the title still landed on the fallback corner. Reserving what is blank NOW works
    # because this runs after the water, the crops, the houses and the hinterland and before the
    # only two things left that could fill it (the coppice and the grove).
    spot = s._blank_label_spot(x0, y0, x1 - x0, y1 - y0, w, h)
    if spot is None:  # pragma: no cover - the map is already too full to title; nothing to reserve
        return (x0, y0, x0, y0)
    return (spot[0], spot[1], spot[0] + w, spot[1] + h)


def _clear_gap(center: Pt, half: float, crops: Sequence[Poly], fall_y: float) -> float | None:
    """Distance from a candidate square to the nearest crop, or None if it is too close.

    The set-back is 80 px normally and 180 px when the square sits on the crop's SUNNY side (south,
    in screen terms) - the shading case. `woodland_clear_of_crops` uses 1 : 2.5-ish set-backs for the
    same reason; this is deliberately a little more generous than the check, so a patch that passes
    here passes there with room to spare rather than sitting on the line."""
    cx, cy = center
    best = 1e9
    for crop in crops:
        d = min(seg_dist(cx, cy, crop[i], crop[(i + 1) % len(crop)]) for i in range(len(crop))) - half
        if point_in_poly(cx, cy, list(crop)):
            return None
        south_of = cy - half > max(p[1] for p in crop) - 40 and min(p[0] for p in crop) - half < cx < max(p[0] for p in crop) + half
        if d < (180.0 if south_of else 80.0):
            return None
        best = min(best, d)
    return None if best >= 1e9 else best


def _near_line(center: Pt, half: float, pts: Sequence[Pt], pad: float) -> bool:
    cx, cy = center
    return any(seg_dist(cx, cy, pts[i], pts[i + 1]) < half + pad for i in range(len(pts) - 1))


def stage_woodland(s: Settlement, plan: SitePlan) -> None:
    """A few managed-woodland patches on the high, far ground - the green EXCEPTION to the scrub.

    The windbreak belt is COMPUTED here, before the scan, and only DRAWN in the next stage. That
    split exists because the two woods must not merge: `woodland_clear_of_grove` requires a coppice
    patch to keep off every clump of the fengshui grove, or the two read as one indistinct green
    mass. The scan therefore has to know where the belt is going, but the belt has to be DRAWN late
    so its per-crown filter sees every structure already standing (the engine's DRAW ORDER rule).
    Computing early and drawing late satisfies both."""
    plan.belt = belt_polygon(s, plan)
    for patch in open_ground_patches(s, plan, plan.woodland_patches):
        s.commons(patch, role="woodland")


def stage_windbreak(s: Settlement, plan: SitePlan) -> None:
    """The communal fengshui belt behind the cluster, shaped to the houses that actually landed.

    A nucleated settlement shelters behind ONE grove rather than per-house belts, and the belt must
    do two things the gate measures: stand on the WINDWARD side of the house centroid, and EMBRACE
    the cluster (a substantial belt within 150 px of a farmhouse - "far corner masses alone are
    decoration"). Both fall out of deriving it from the houses: the belt is a band offset into the
    wind from the cluster's own centroid, spanning the cluster's width across the wind, ragged along
    its edges because a grove hugs the land and is not a ruled wall. A copse scatter then fills the
    leafy gaps among the homes.

    Drawn LATE, after the ground cover and the woods, so its per-crown filter sees every structure
    already standing and no tree is drawn on a roof."""
    if not plan.belt:  # pragma: no cover - stage_woodland always computes it first
        return
    s.village_grove(plan.belt, role="windbreak")
    # The COPSE fills the leafy gaps AMONG the homes, over the house cloud. That is only reasonable
    # ground because `stage_homesteads` now bounds every seat to the cluster band: over a cloud with
    # a strewn farmstead in it, this became a scatter across 1,446 x 1,244 px - a wood over the whole
    # settlement rather than a copse among the houses, and every clump an obstacle the map's own
    # title could then find no room around (`title_clear_of_features`).
    houses = s.M.get("houses", [])
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    pad = 16.0
    s.village_grove([(min(xs) - pad, min(ys) - pad), (max(xs) + pad, min(ys) - pad), (max(xs) + pad, max(ys) + pad), (min(xs) - pad, max(ys) + pad)], role="copse", dense=False)


def belt_polygon(s: Settlement, plan: SitePlan) -> Poly:
    """The windbreak belt's footprint - a band FOLLOWING the cluster's windward fringe.

    The belt used to be a straight band standing off the single windward-most house, its length set
    by the widest cross-wind pair. That is right for a round cluster and wrong for every other
    shape: on a tall narrow settlement under a diagonal wind it put the belt 350 px clear of the
    nearest farmhouse and nearly square, and `village_grove`'s own filters then threw most of its
    clumps away - nine survived. A belt that shelters nothing fails
    `village_windbreak_embraces_cluster` and `village_windbreak_scales_with_cluster` together, and
    both are right to fail it.

    So the near face is sampled ACROSS the wind and, in each column, sits just behind whichever
    house is furthest upwind THERE. The result hugs the settlement's windward profile whatever its
    shape - which is what a back-village grove does, being planted where the houses are - and stays
    a band of constant depth, so `village_grove` still fills it as a belt rather than a blob."""
    houses = s.M.get("houses", [])
    if len(houses) < 3:  # pragma: no cover - fewer houses than this fails the gate first
        return []
    wx, wy = plan.wind
    px, py = -wy, wx  # across the wind
    ccx, ccy = sum(h["x"] for h in houses) / len(houses), sum(h["y"] for h in houses) / len(houses)
    uv = [(((h["x"] - ccx) * wx + (h["y"] - ccy) * wy), ((h["x"] - ccx) * px + (h["y"] - ccy) * py)) for h in houses]
    v_lo, v_hi = min(v for _u, v in uv), max(v for _u, v in uv)
    COLS = 7
    half = (v_hi - v_lo) / 2 + 90.0  # a shoulder past the outermost house at each end
    v_mid = (v_lo + v_hi) / 2
    rng = random.Random((plan.spec.seed * 7919) & 0xFFFFFFFF)

    def rag(q: Pt, amp: float = 13.0) -> Pt:
        return (q[0] + rng.uniform(-amp, amp), q[1] + rng.uniform(-amp, amp))

    # NO COLUMN FALLS BEHIND THE MEDIAN HOUSE. Following the profile is right, but on a cluster
    # that is long ACROSS the wind the flank columns' own frontrunner sits well downwind of the
    # middle ones, so the band bows back around the settlement and its centroid can land level with
    # (or behind) the house cloud - which is exactly what `village_windbreak_on_windward_side`
    # measures, and it fired on two cohort maps with a belt that looked fine in every other check.
    # Flooring each column at the cluster's MEDIAN u keeps the belt following the fringe where the
    # fringe leads it, and keeps the whole band on the windward half where a back-village grove
    # belongs. The median, not the mean: one house pushed far upwind should not drag the wall out.
    u_sorted = sorted(u for u, _v in uv)
    u_floor = u_sorted[len(u_sorted) // 2]

    def profile(span_f: float) -> list[tuple[float, float]]:
        """(v, u) of the windward fringe, sampled in columns across the wind."""
        cols: list[tuple[float, float]] = []
        for k in range(COLS + 1):
            v = v_mid + half * span_f * (-1.0 + 2.0 * k / COLS)
            width = half * span_f / COLS + 40.0
            near = [u for u, vv in uv if abs(vv - v) <= width]
            if not near:  # a column with no house of its own leans on the whole cluster's fringe
                near = [max(u for u, _v in uv) - 40.0]
            cols.append((v, max(max(near), u_floor)))
        return cols

    # ~110 px deep - a real wind wall, not a hedge. The 24 px stand-off is set by
    # `village_windbreak_embraces_cluster`, which wants a clump within 150 px of a farmhouse: the
    # clump grid starts some way inside the polygon, so a 42 px face measured 160 px to the nearest
    # tree.
    crops: list[Poly] = [list(plan.envelope), *crop_polys(s)]

    def band(span_f: float, back: float) -> Poly:
        cols = profile(span_f)
        # 36 px, not 24. `village_grove` filters clumps against every structure and crop, and it
        # filters the near face hardest - so a belt whose POLYGON sits clearly windward can still
        # have its DRAWN clumps average back onto the cluster's own line, which is what
        # `village_windbreak_on_windward_side` measures (Kashikawa: polygon centroid +137, drawn
        # centroid -5). The extra 12 px comes out of the 150 px embrace budget and leaves plenty.
        near = [rag((ccx + wx * (u + 36.0 + back) + px * v, ccy + wy * (u + 36.0 + back) + py * v)) for v, u in cols]
        far = [rag((ccx + wx * (u + 146.0 + back) + px * v, ccy + wy * (u + 146.0 + back) + py * v)) for v, u in reversed(cols)]
        return near + far

    def fouled(poly: Poly) -> bool:
        return any(point_in_poly(q[0], q[1], list(c)) or min(seg_dist(q[0], q[1], c[i2], c[(i2 + 1) % len(c)]) for i2 in range(len(c))) < 20.0 for q in poly for c in crops)

    # THE LADDER STANDS BACK BEFORE IT SHRINKS. Both moves get the belt off the crop, but they cost
    # different things: standing back spends the embrace budget (a clump within 150 px of a
    # farmhouse, and the belt starts 24 px behind the fringe, so there is room), while shrinking
    # spends the SIZE budget (canopy worth 40% of the roof area it shelters, which a belt trimmed to
    # half its length cannot meet). Shrinking first cost both checks on two cohort maps.
    belt = band(1.0, 0.0)
    for span_f, back in ((1.0, 0.0), (1.0, 22.0), (1.0, 44.0), (0.88, 44.0), (0.74, 60.0), (0.6, 60.0)):
        belt = band(span_f, back)
        if not fouled(belt):
            break
    return [(max(6.0, min(plan.W - 6.0, bx)), max(6.0, min(plan.H - 6.0, by))) for bx, by in belt]


# ---- STAGE 8: crossings, the board, and the frame ------------------------------------------------


def stage_crossings(s: Settlement, plan: SitePlan) -> None:
    """Bridges where a way crosses water, and plank footbridges over the long irrigation ditches.

    After every way and every watercourse, because a crossing added later leaves an unbridged one -
    the engine's own `bridges()` docstring says so and the `roads_bridge_water` check enforces it."""
    s.bridges()
    if s.M.get("field_ditches"):
        s.channel_footbridges(spacing=300)


def stage_notice(s: Settlement, plan: SitePlan) -> None:
    """The official notice board, on a lane verge at the busiest node.

    EVERY settlement tier posts the state's standing law, hamlets included - the ofuregaki circulars
    reached the peasantry through this board, read out by the one required-literate person (a
    hamlet's senior farmer, answering to the village headman). `place_kosatsuba` sites it itself,
    deterministically, from the same route records the validator reads.

    It runs BEFORE the ground cover and the woods, not with the framing, because it needs a clear
    verge and it competes for the same ground the scrub scatter and the grove clumps take. Sited
    after them it silently found nowhere to go on one cohort map in six and the gate reported a
    hamlet with no notice board - a failure of ORDER, not of siting."""
    spot = s.place_kosatsuba()
    # ...AND IT MUST STAND WHERE THE FRAME WILL KEEP IT. `place_kosatsuba` maximises passing traffic
    # (dwellings within ~260 px) along the whole way network, and a lane ARM that runs past the
    # cluster still sees the whole cluster from its far end - so on a held-out cohort hamlet the
    # board landed 87 px north of the northernmost farmhouse, on a stretch of lane serving nobody.
    # `crop_to_content` frames the HARD features and deliberately ignores linear runners like lanes,
    # so the board and its caption fell outside the sheet (`labels_within_image`). Adding the board
    # to the crop's hard set was tried and is worse: it then holds the frame open by itself, which is
    # what `crop_not_held_open_by_one_feature` exists to stop. The board belongs among the houses it
    # is read by, so if the engine's traffic score sends it outside them, re-seat it on the nearest
    # verge that is inside the cloud.
    hs = s.M.get("houses", [])
    if spot is not None and hs:
        hx0, hx1 = min(h["x"] for h in hs), max(h["x"] for h in hs)
        hy0, hy1 = min(h["y"] for h in hs), max(h["y"] for h in hs)
        if not (hx0 - 30 <= spot[0] <= hx1 + 30 and hy0 - 30 <= spot[1] <= hy1 + 30):
            board = s.M["kosatsuba"].pop()
            # ...and its CAPTION with it. `kosatsuba` records the board and calls `self.label`, so
            # popping only the board leaves an orphan "notice board" caption sitting where the board
            # used to be - which is the very label the frame could not hold, still failing
            # `labels_within_image` after the board itself had moved.
            for _li in range(len(s.M.get("labels", [])) - 1, -1, -1):
                if len(s.M["labels"][_li]) > 5 and s.M["labels"][_li][5] == "notice board":
                    s.M["labels"].pop(_li)
                    break
            best: tuple[float, float, float, float] | None = None
            for lane in s.M.get("lanes", []):
                if lane.get("connector"):
                    continue
                pts = lane["pts"]
                for i in range(len(pts) - 1):
                    (ax, ay), (bx, by) = pts[i], pts[i + 1]
                    seg = math.hypot(bx - ax, by - ay) or 1.0
                    ux, uy = -(by - ay) / seg, (bx - ax) / seg
                    rot = math.degrees(math.atan2(by - ay, bx - ax))
                    for t in range(int(seg // 12) + 1):
                        mx, my = ax + (bx - ax) * (t * 12 / seg), ay + (by - ay) * (t * 12 / seg)
                        for side in (1.0, -1.0):
                            cx2, cy2 = mx + ux * 16.0 * side, my + uy * 16.0 * side
                            if not (hx0 <= cx2 <= hx1 and hy0 <= cy2 <= hy1):
                                continue
                            if not s._fits(cx2, cy2, 14.0, 8.0, corridors=False):
                                continue
                            busy = sum(1 for h in hs if math.hypot(cx2 - h["x"], cy2 - h["y"]) < 260)
                            if best is None or -busy < best[0]:
                                best = (-busy, cx2, cy2, rot)
            if best is not None:
                s.kosatsuba(best[1], best[2], rot=best[3])
            else:  # pragma: no cover - no verge inside the cloud takes a board; keep the engine's seat rather than none
                s.M["kosatsuba"].append(board)


def stage_frame(s: Settlement, plan: SitePlan) -> None:
    """The crop, then the title.

    In that order: the title searches the FRAMED window for blank space to sit in, so the frame has
    to exist first."""
    # The margin leaves the TITLE somewhere to stand: `title()` scans the framed window for a box
    # that clears every feature and falls back to a corner overlap when the map is too full, which
    # `title_clear_of_features` then fails. But it is bounded above as well as below - `crop_hugs_
    # content` allows at most 56 px of view past the frame-setting content, because a band whose
    # only extra is open ground is wasted image. 64 was tried and fails all twelve. 48 is the most
    # air the frame will give the title.
    s.crop_to_content(margin=48)
    s.title(plan.spec.name)


# THE PIPELINE. Read top to bottom: this is the generator.
STAGES = (
    stage_water_frame,
    stage_field,
    stage_sink,
    stage_ways,
    stage_homesteads,
    stage_appurtenances,
    stage_notice,
    stage_hinterland,
    stage_woodland,
    stage_windbreak,
    stage_crossings,
    stage_frame,
)


# ---- driving it ---------------------------------------------------------------------------------


@dataclass
class Report:
    """What one generated hamlet came out as - the row of the cohort table."""

    plan: SitePlan
    failures: list[str]
    path: str | None = None

    @property
    def ok(self) -> bool:
        return not self.failures

    def line(self) -> str:
        p = self.plan
        return (
            f"{p.spec.name:<18} seed={p.spec.seed:<4} hh={p.placed}/{p.spec.households:<3} "
            f"acres={p.acres:5.1f}/{p.target_acres:5.1f} fall={int(p.down_deg):<4} wind={p.windward:<3} "
            f"sink={p.water_sink:<7} {p.cluster_shape[:9]:<10} {p.lane_skeleton:<6} "
            f"{'OK' if self.ok else 'FAIL: ' + ', '.join(self.failures[:4])}"
        )


def build(plan: SitePlan) -> Settlement:
    """Run every stage, in order, against a fresh `Settlement`."""
    s = Settlement(W=plan.W, H=plan.H, seed=plan.spec.seed)
    for stage in STAGES:
        stage(s, plan)
    return s


def generate(spec: HamletSpec, out_base: str | None = None, render: bool = True) -> Report:
    """Build a hamlet, FINISH it, gate it, and report. Writes svg/png/json when `out_base` is given.

    THE MANIFEST IS NOT COMPLETE UNTIL `finish()` RUNS, and that cost an hour of chasing a phantom
    defect. `finish` is not just "write the file": it flushes the deferred tree canopies, seats the
    deferred captions, and splices the shared water block - which is where a pond's fill records the
    draw position `pond_fill_covers_channel_mouths` reads. Gating the in-memory manifest before that
    reported a broken pond on every map with a pond, and the maps were fine. So the finish always
    runs; a cohort member with nowhere to go finishes into a scratch directory and is thrown away.

    The gate then runs IN-PROCESS on that finished manifest, which is what makes it cheap to roll a
    dozen hamlets and ask how many of them are actually correct."""
    import tempfile

    from check_village import gate

    plan = plan_site(spec)
    s = build(plan)
    if out_base is not None:
        s.finish(out_base, render=render)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            s.finish(os.path.join(tmp, "scratch"), render=False)
    return Report(plan=plan, failures=sorted(gate(s.M)), path=out_base)


def cohort(count: int, first_seed: int = 1, households: int | None = None) -> list[Report]:
    """Roll `count` hamlets from consecutive seeds and gate every one.

    This is the experiment's actual evidence. A generator that produces ONE good map has shown that
    a person can drive it to a good map; a generator that produces a cohort of correct maps from
    seeds nobody looked at has shown that the SCRIPT is doing the work."""
    out = []
    for i in range(count):
        seed = first_seed + i
        hh = households if households is not None else 10 + (seed * 7) % 11
        out.append(generate(HamletSpec(name=f"Cohort-{seed:02d}", seed=seed, households=hh), out_base=None))
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a Rokugani rice hamlet from a seed, and gate it.")
    ap.add_argument("--name", default="Hamlet")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--households", type=int, default=REF_HOUSEHOLDS)
    ap.add_argument("--down-deg", type=float, default=None)
    ap.add_argument("--sink", choices=("pond", "offmap"), default=None)
    ap.add_argument("--windward", default=None)
    ap.add_argument("--out", default=None, help="write <out>.svg/.png/.json")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--batch", type=int, default=0, help="roll N hamlets from consecutive seeds and gate them all")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.batch:
        reports = cohort(args.batch, first_seed=args.seed)
        for r in reports:
            print(r.line())
        good = sum(1 for r in reports if r.ok)
        print(f"\n{good}/{len(reports)} passed the full gate")
        return 0 if good == len(reports) else 1

    report = generate(
        HamletSpec(name=args.name, seed=args.seed, households=args.households, down_deg=args.down_deg, water_sink=args.sink, windward=args.windward),
        out_base=args.out,
        render=not args.no_render,
    )
    print(report.line())
    for f in report.failures:
        print("  FAIL", f)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
