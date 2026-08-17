"""The spec a caller writes, and the site plan derived from it.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from l7r.diagram.settlement import knob_rng

from .consts import (
    CARDINAL_BEARINGS,
    CLUSTER_SHAPES,
    FALL_BEARINGS,
    FAN_ASPECTS,
    FIELD_ARCHETYPES,
    GRAIN_DRIFTS,
    GROSS_ACRES_PER_HOUSEHOLD,
    HOUSEHOLD_BAND,
    LANE_SKELETONS,
    OFFTAKE_LADDER,
    PLOT_SIZES,
    REF_HOUSEHOLDS,
    ROLLED_ARCHETYPES,
    SINKS,
    SQ_FT_PER_ACRE,
    WIND_TURNS,
    WIND_VECTORS,
    Poly,
    Pt,
)

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
    field_archetype: str | None = None
    plot_size: str | None = None
    grain_drift: int | None = None
    woodland_patches: int | None = None
    # Passed through to the engine's own knob catalog (`Settlement.pin_knob`).
    pins: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.field_archetype is not None and self.field_archetype not in FIELD_ARCHETYPES:
            raise ValueError(f"field_archetype {self.field_archetype!r} is not one this generator draws: {sorted(FIELD_ARCHETYPES)}")
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
    field_archetype: str
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
    # A POLDER IS LAID TO THE CARDINAL SURVEY GRID, so its fall is rolled from the four cardinals
    # rather than the eight compass points. This is not a workaround for `polder_fills_its_bbox`
    # (which a diagonal block fails, correctly - a rotated rectangle cannot fill an axis-aligned
    # bbox): it is what the archetype IS. A wei-tian polder is a SURVEYED orthogonal module diked
    # out of standing water, and the survey runs with the cardinal directions; the organic comb fan,
    # which follows its own water down whatever slope it finds, is the one that sits on a diagonal.
    # A GM who pins `down_deg` is still honoured - the pin is a fact about that place.
    _archetype = spec.field_archetype or str(_roll(spec.seed, "field_archetype", ROLLED_ARCHETYPES))
    _falls = CARDINAL_BEARINGS if _archetype == "polder_grid" else FALL_BEARINGS
    down_deg = spec.down_deg if spec.down_deg is not None else float(_roll(spec.seed, "down_deg", _falls))
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
        field_archetype=_archetype,
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
