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

from settlement import Settlement, knob_rng, point_in_poly, seg_closest, seg_dist, seg_intersect, skeleton_layout  # noqa: E402
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

# LANE CLEARANCE - the no-build corridor a lane reserves, in px, and it is sized against the house
# the engine will DRAW rather than the one it tests.
#
# `_fits` checks a candidate's CENTER against a lane corridor, and it checks the farmhouse's BASE
# rect (46 x 28 ft). But a homestead's wealth variation renders the house up to ~1.33x that, so the
# drawn steading reaches ~34 px from its center where the placer assumed ~27 - and
# `houses_clear_of_lanes` measures the DRAWN corners. At the authored maps' clearance of 32 a
# well-off farmhouse's corner ended up 2.4 px from a connector track's centerline while its center
# stood a legal 34 px off. (This is the engine's known "placement tests a different footprint than
# the one drawn" debt, recorded in the skill's CLAUDE.md; it is worked around here rather than
# fixed, since fixing it re-rolls the whole pool.) 48 covers the widest drawn house plus the lane's
# own tread and a margin.
LANE_CLEARANCE = 48.0

# HOW MUCH GROUND ONE HOMESTEAD TAKES, in px at 1 ft/px - the pitch the cluster band is sized on.
# A bundle's reserved rects come to ~71 x 57 ft; the placer then keeps bundles apart by
# circumscribed circles rather than real footprints, so the effective pitch is larger again. 92 px
# per household leaves the cluster dense enough to read as a nucleus and open enough for its
# courtyards, its wells and its byres. See `seat_cluster` for what the wrong number does.
BUNDLE_PITCH = 92.0

# `build_comb`'s GRAIN, and why it is not what its own docstring prescribes.
#
# `grain` scales the carve's real-feet thresholds AND the channel widths, and the docstring says a
# map should pass `2 / ftpx` so a "too narrow to plant" test means the same real size at every
# scale - which for a 1 ft/px hamlet is 2.0. That is the principled number and it was tried. But
# EVERY authored hamlet in the pool passes the default 1.0, and the engine's downstream constants
# are calibrated against what they produce: at 2.0 the irrigation ditches come out twice as wide as
# Ikegami's, and `channel_footbridges` then lays planks too short for the water they span
# (`bridges_span_their_water`, with an abutment standing in the ditch). Matching the tier's shipped
# calibration beats matching its documentation - a scripted map should be comparable to the
# authored ones, and re-deriving the footbridge sizing is a separate job with its own pool sweep.
GRAIN = 1.0

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


def crosses_poly(a: Pt, b: Pt, poly: Sequence[Pt], samples: int = 60) -> bool:
    """Does the segment a->b pass through `poly`? Sampled rather than solved: the callers use it to
    STEER a lane away from the crop, where a sample every few pixels is ample and an exact
    segment-polygon intersection would be more code for no better answer."""
    return any(point_in_poly(a[0] + (b[0] - a[0]) * i / samples, a[1] + (b[1] - a[1]) * i / samples, list(poly)) for i in range(samples + 1))


# ---- STAGE 1: the water frame -------------------------------------------------------------------


def stage_water_frame(s: Settlement, plan: SitePlan) -> None:
    """Settle the drainage bearing and the land's fall BEFORE anything is placed.

    This is first because the skill says it is first, at every tier: "before a single feature is
    placed, decide the map's drainage bearing and, separately, the land's fall". Everything
    downstream reads them - which end of the fan is the head, which margin the cluster can stand on,
    which way the drain runs, where the marsh is allowed to be."""
    s.meta(
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

    plan.envelope = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append(list(plan.envelope))
    s.meta(dry_furrows_vary=net["furrows_vary"])
    s.M["meta"]["field_archetype"] = "valley_paddy"
    # The brook that feeds the head, running in from off-map: the visible source. It is drawn as a
    # STREAM ending AT the sluice, where it becomes the head-race - it does not run on over the
    # paddies. `draw_comb_field` then records the hairline topology channel that grounds the field's
    # water source for the gate.
    up = (sluice[0] - dx * 420, sluice[1] - dy * 420)
    s.draw_comb_field(net, f"{plan.spec.name.lower()}-paddies", {"kind": "stream", "stream": [up, ((up[0] + sluice[0]) / 2 + dy * 26, (up[1] + sluice[1]) / 2 - dx * 26), sluice]})
    # REGISTER THE DRY HEM AS CROPLAND, which `draw_comb_field` does NOT do - and this is worth
    # knowing about, because it is a defect in the shared engine rather than in this module.
    #
    # The engine keeps two registries for cropland. `block_polys` is the no-build list; `dry_polys`
    # is the one the GROVE, the LANE and the threshing-yard filters read to keep trees and tracks
    # out of the hatake strips. `draw_comb_field` appends the hem to `block_polys` only, so a map
    # built through it has hem plots that stop a house but do not stop a tree - and every
    # hand-authored comb gen in the pool (hoshigaoka, ueda, hikari, hoshizora, hirameki, ubame)
    # compensates with its own `s.dry_polys.append(...)` line, which is exactly the shape of bug the
    # skill's dev notes call out: placement and its check reading DIFFERENT sources. Honda and
    # Shimizu, the two maps that already roll from a seed, pass only because their clusters happen
    # to sit away from the hem; a seat that hugs it, as several of this module's cohort do, fails
    # `groves_clear_of_dry_plots` and `lanes_clear_of_dry_plots` at once.
    #
    # Registered here, from the MANIFEST (what was actually drawn - `draw_comb_field` drops hem
    # plots that landed on water or on another fan's rice, so the net's list is not the map's list).
    for poly in crop_polys(s):
        s.dry_polys.append(poly)


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
        # derived - the distance from the outfall to the canvas edge along the fall, plus a margin -
        # because a fixed length only works on the canvas it was tuned for.
        run = edge_run(plan, out) + 260.0
        heading = drain_heading(s, name) or (dx, dy)
        # The junction leg runs on the BISECTOR of the drain's heading and the fall, so the brook
        # turns through half the angle twice instead of all of it once - and half of any angle is
        # obtuse. Leaving on the drain's own heading and then turning downhill makes ONE turn of the
        # full angle, which on a collector running well across the fall is an acute hairpin
        # (`water_channels_obtuse_turns`; a ditch does not fold back on itself).
        bis = unit(heading[0] + dx, heading[1] + dy)
        mid = (out[0] + bis[0] * 70.0, out[1] + bis[1] * 70.0)  # a smooth junction off the collector,
        # ...THEN downhill and out. "Straight downhill" is right on most fans and wrong on the ones
        # whose toe is concave, where the exit line clips back across the rice
        # (`streams_avoid_fields`) - so the exit bearing is swung off the fall until it is clear of
        # the crop, nearest bearing first, exactly the way the connector track is steered. A brook
        # DOES follow the fall; the swing is small, and the alternative is a watercourse drawn
        # through a paddy.
        exit_deg = math.degrees(math.atan2(dy, dx))
        for swing in (0, 12, -12, 24, -24, 38, -38, 54, -54):
            th = math.radians(exit_deg + swing)
            end = (mid[0] + math.cos(th) * run, mid[1] + math.sin(th) * run)
            if not (crosses_poly(out, mid, plan.envelope) or crosses_poly(mid, end, plan.envelope)):
                s.stream([out, mid, end], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)
                plan.sink_brook = [out, mid, end]
                return
        s.stream([out, mid, (mid[0] + dx * run, mid[1] + dy * run)], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)  # pragma: no cover - a fan toe never blocks all nine bearings
        plan.sink_brook = [out, mid, (mid[0] + dx * run, mid[1] + dy * run)]
        return
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
    pcx, pcy = out[0] + dx * back, out[1] + dy * back
    pcx = max(prx + 20.0, min(plan.W - prx - 20.0, pcx))
    pcy = max(pry + 20.0, min(plan.H - pry - 20.0, pcy))
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


def seat_cluster(plan: SitePlan, dry_plots: Sequence[Poly] = (), drain: Poly | None = None) -> dict[str, Any]:
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
    plan.watercourses = [
        ((float(a[0]), float(a[1])), (float(b[0]), float(b[1])))
        for rec in list(s.M.get("field_ditches", [])) + list(s.M.get("channels", []))
        for a, b in zip(rec["poly"], rec["poly"][1:], strict=False)
    ]
    seat = seat_cluster(plan, dry_plots=crop_polys(s), drain=drain)
    plan.seat = seat
    ax, ay = seat["along"]
    ox, oy = seat["out"]
    cx, cy = seat["cx"], seat["cy"]

    crops = crop_polys(s)

    def to_screen(p: Pt) -> Pt:
        """Seat frame (along the margin, away from the field) -> screen."""
        return (cx + ax * p[0] + ox * p[1], cy + ay * p[0] + oy * p[1])

    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, seat["lat"], seat["dep"])
    for lane_pts in layout["lanes"]:
        # ...pulled back out of any hem plot the arm would otherwise reach into. The skeleton is
        # sized from the household count, so on a cluster seated tight against the hem a `cross`
        # crossbar can overrun into the barley - and a lane may touch a plot's edge but never cross
        # its interior. Shortening the arm is the honest fix: the lane simply ends where the crop
        # starts, which is what a village lane does.
        arm = clip_to_clear([to_screen((p[0], p[1])) for p in lane_pts], crops, 20.0)
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
    brook_segs = [(plan.sink_brook[i], plan.sink_brook[i + 1]) for i in range(len(plan.sink_brook) - 1)]

    def spur_path(target: Pt) -> Poly:
        edge = (target[0] - ox * 8.0, target[1] - oy * 8.0)
        return [start, ((cx + edge[0]) / 2 + ax * 14, (cy + edge[1]) / 2 + ay * 14), edge]

    # ...and again the candidate is the DRAWN path, bow and all - see `path_is_clear`.
    spur = min(
        (spur_path(q) for q in sorted(plan.envelope, key=lambda v: math.hypot(v[0] - cx, v[1] - cy))),
        key=lambda p: (path_violations(p, crops, plan.sink_pond, brook_segs, plan.watercourses), polyline_len(p)),
    )
    s.lane(spur, width=5, clearance=LANE_CLEARANCE, worn=True)

    # the CONNECTOR, out to the frame
    gate = to_screen((float(layout["gateway"][0]), float(layout["gateway"][1])))
    s.lane(connector_track(plan, gate, avoid=[list(plan.envelope), *crops]), width=6, clearance=LANE_CLEARANCE, worn=True, connector=True)


def clip_to_clear(pts: Poly, obstacles: Sequence[Poly], margin: float, step: float = 8.0) -> Poly:
    """Shorten a polyline so it stops before the first ground it may not cross.

    Used on the cluster's lane arms. Dragging an offending VERTEX back toward the cluster was tried
    first and is not reliable: a vertex deep inside a large hem plot may not escape in the steps
    allowed, and it distorts the skeleton on the way. Truncating is both simpler and more honest -
    the lane ends where the crop begins, which is what a village lane does. Always returns at least
    a two-point line so the caller still has a lane."""
    if not obstacles:
        return pts

    def fouled(q: Pt) -> bool:
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


def connector_track(plan: SitePlan, start: Pt, avoid: Sequence[Poly] = (), reach: float = 4000.0) -> Poly:
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
    best: tuple[int, Poly] | None = None
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
        violations = path_violations(path, avoid or [plan.envelope], pond, brook, waters)
        if violations == 0:
            return path
        if best is None or violations < best[0]:
            best = (violations, path)
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
        ):
            bad += 1
    return bad


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
    span = [(i, p) for i, p in enumerate(env) if abs((p[0] - seat["anchor"][0]) * ax + (p[1] - seat["anchor"][1]) * ay) <= seat["lat"]]
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
    off = LANE_CLEARANCE + 22.0  # the DRAWN bundle exceeds the rect the placer tests, so leave the frontage row real daylight
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
    for fx, fy in front_row(plan, min(plan.spec.households, 8)):
        if placed >= plan.spec.households:
            break
        if s.try_place(fx, fy, "plain"):
            placed += 1
    # ...then rows FLANKING the lanes, before any shape fill. A lane exists to be fronted, and a
    # cluster seeded only by its shape leaves them running across empty middle: the review of the
    # first draft measured a median house-to-lane distance of 94 ft against Ikegami's 55, with one
    # lane dead-ending in open ground and no house at its end. Offering the placer seats at exactly
    # the corridor's edge is what puts the doors on the street.
    for lx, ly in lane_frontage(s, seat):
        if placed >= plan.spec.households:
            break
        if s.try_place(lx, ly, "plain"):
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
    for third, nearest in ((190.0, 105.0), (300.0, 110.0), (520.0, 112.0)):
        if len(placed) >= want:
            break
        seats: list[tuple[float, float, float]] = []
        step = 22.0
        y = min(ys)
        while y <= max(ys):
            x = min(xs)
            while x <= max(xs):
                near = sorted(math.hypot(x - h["x"], y - h["y"]) for h in houses)
                if len(near) >= 3 and near[2] <= third and near[0] <= nearest:
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
        for radius in (60.0, 90.0, 130.0, 190.0, 260.0):
            spot = s.open_seat((h["x"] - radius, h["y"] - radius, h["x"] + radius, h["y"] + radius), 16.0, 16.0, well=True)
            if spot is not None and not any(math.hypot(spot[0] - px, spot[1] - py) < 130.0 for px, py in placed) and s.well_at(spot[0], spot[1]):
                placed.append(spot)
                break
    if not placed:
        # LAST RESORT: ask the engine. A settlement with NO well fails the gate outright, and by
        # this point the lattice has been refused everywhere - which means the courtyards are full,
        # not that there is no room. `open_seat` runs the engine's own `_fits` over the ground and
        # returns the best clear spot or None, which is the documented answer to "this pocket needs
        # one more X" and finds seats a hand-rolled scan misses (the skill's dev notes: a manifest
        # scan cannot predict `_fits`).
        spot = s.open_seat((min(xs), min(ys), max(xs), max(ys)), 16.0, 16.0, well=True)
        if spot is not None and s.well_at(spot[0], spot[1]):
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
    if plan.belt:
        bx0, by0 = min(p[0] for p in plan.belt), min(p[1] for p in plan.belt)
        bx1, by1 = max(p[0] for p in plan.belt), max(p[1] for p in plan.belt)
        keep.append(((bx0 + bx1) / 2, (by0 + by1) / 2, max(bx1 - bx0, by1 - by0) / 2 + 110.0))
    hxs = [h["x"] for h in s.M.get("houses", [])]
    hys = [h["y"] for h in s.M.get("houses", [])]
    if hxs:  # the copse's ground
        keep.append(((min(hxs) + max(hxs)) / 2, (min(hys) + max(hys)) / 2, max(max(hxs) - min(hxs), max(hys) - min(hys)) / 2 + 110.0))
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
            if gap is not None and not any(math.hypot(x - kx, y - ky) < kr + half for kx, ky, kr in keep) and not any(_near_line((x, y), half, pts, pad) for pts, pad in lanes + streams):
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
    houses = s.M.get("houses", [])
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    pad = 16.0
    s.village_grove(
        [(min(xs) - pad, min(ys) - pad), (max(xs) + pad, min(ys) - pad), (max(xs) + pad, max(ys) + pad), (min(xs) - pad, max(ys) + pad)],
        role="copse",
        dense=False,
    )


def belt_polygon(s: Settlement, plan: SitePlan) -> Poly:
    """The windbreak belt's footprint, derived from the houses that actually landed."""
    houses = s.M.get("houses", [])
    if len(houses) < 3:  # pragma: no cover - fewer houses than this fails the gate first
        return []
    wx, wy = plan.wind
    px, py = -wy, wx  # across the wind
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    ccx, ccy = sum(xs) / len(xs), sum(ys) / len(ys)
    reach = max((h["x"] - ccx) * wx + (h["y"] - ccy) * wy for h in houses)
    span = max(abs((h["x"] - ccx) * px + (h["y"] - ccy) * py) for h in houses) + 90.0
    rng = random.Random((plan.spec.seed * 7919) & 0xFFFFFFFF)

    def rag(p: Pt, amp: float = 13.0) -> Pt:
        return (p[0] + rng.uniform(-amp, amp), p[1] + rng.uniform(-amp, amp))

    # the belt's near face sits just behind the windward fringe of the houses (inside the 150 px
    # embrace band), and it is ~110 px deep - a real wind wall, not a hedge
    near = reach + 42.0
    far = near + 110.0
    crops: list[Poly] = [list(plan.envelope), *crop_polys(s)]
    belt: Poly = []
    steps = 7
    for i in range(steps + 1):  # the near face, swept across the wind
        t = -1.0 + 2.0 * i / steps
        belt.append(rag((ccx + wx * near + px * span * t, ccy + wy * near + py * span * t)))
    for i in range(steps + 1):  # ...and back along the far face
        t = 1.0 - 2.0 * i / steps
        belt.append(rag((ccx + wx * far + px * span * t, ccy + wy * far + py * span * t)))
    # bend the belt around any cropland it would otherwise stand in (see `pull_clear`)
    belt = [pull_clear(p, (ccx, ccy), crops, 34.0) for p in belt]
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
    s.place_kosatsuba()


def stage_frame(s: Settlement, plan: SitePlan) -> None:
    """The crop, then the title.

    In that order: the title searches the FRAMED window for blank space to sit in, so the frame has
    to exist first."""
    # The margin leaves the TITLE somewhere to stand. `title()` scans the framed window for a box
    # that clears every feature and falls back to a corner overlap when the map is too full - which
    # `title_clear_of_features` then fails. A tight crop on a sheet that is nearly all field is
    # exactly that case, and a few px of margin is the cheapest cure.
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
