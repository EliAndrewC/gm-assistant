"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import hashlib
import math
import random
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ._geom import Poly, Pt, forest_frame_span, forest_reveal_x, label_aabb, point_in_poly, seg_intersect, segments_cross, torii_halfbox

if TYPE_CHECKING:
    pass

TypingRule = Callable[[Any, Mapping[str, Any]], bool]


def _always_typed(value: Any, context: Mapping[str, Any]) -> bool:
    """Default typing rule: every value is allowed (a knob with no geographic constraint)."""
    return True


def scope_seed(seed: int, name: str, key: Sequence[Any]) -> int:
    """A stable sub-seed for one RNG SCOPE - derived from (map seed, scope name, scope key) and
    nothing else, so it cannot depend on how much randomness the rest of the map has drawn.

    SHA-256 for the same reason `knob_rng` uses it: Python's `hash()` is salted per process, so a
    map keyed off it would redraw differently on every run. Float keys are rounded to 0.1 px - the
    manifest's own precision - so a key derived from geometry is stable against representation
    noise while still changing when the geometry genuinely moves."""

    def fmt(v: Any) -> str:
        return f"{round(float(v), 1):.1f}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)

    payload = f"{seed}\x00{name}\x00" + "\x00".join(fmt(v) for v in key)
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], "big")


def knob_rng(seed: int, knob_name: str) -> random.Random:
    """A per-knob INDEPENDENT, deterministic RNG. Derives a stable sub-seed from (map seed, knob
    name) with SHA-256 - Python's built-in hash() is salted per process (PYTHONHASHSEED), so it
    cannot give cross-run determinism - so each knob draws independently of the others and a given
    (seed, knob) pair always yields the same draw. Returns its OWN Random instance and never disturbs
    the global random state the generators seed positionally."""
    digest = hashlib.sha256(f"{seed}\x00{knob_name}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class Knob:
    """One named degree of village-layout variation: a discrete value_space, a default, and a
    typing_rule(value, context) predicate that excludes values historically invalid for the stated
    geography / already-resolved knobs. `roll` draws deterministically and independently from the
    typing-filtered space."""

    def __init__(self, name: str, value_space: Sequence[Any], default: Any, typing_rule: TypingRule | None = None) -> None:
        self.name = name
        self.value_space: list[Any] = list(value_space)
        self.default = default
        self.typing_rule: TypingRule = typing_rule if typing_rule is not None else _always_typed

    def allowed(self, context: Mapping[str, Any]) -> list[Any]:
        """value_space filtered to the values whose typing_rule holds in this context."""
        return [v for v in self.value_space if self.typing_rule(v, context)]

    def roll(self, seed: int, context: Mapping[str, Any]) -> Any:
        """A deterministic, independent draw from the typing-filtered value space. An empty filtered
        space is a spec error (loud), never a silent fallback (contract C2)."""
        pool = self.allowed(context)
        if not pool:
            raise ValueError(f"knob {self.name!r}: no value in {self.value_space} satisfies its typing rule for context {dict(context)!r}")
        return pool[knob_rng(seed, self.name).randrange(len(pool))]


KNOBS: dict[str, Knob] = {}


def register_knob(knob: Knob) -> Knob:
    """Register a knob in the global catalog (last registration per name wins). Returns the knob so
    a module can write `X = register_knob(Knob(...))`."""
    KNOBS[knob.name] = knob
    return knob


def resolve_knob(name: str, seed: int, context: Mapping[str, Any], pinned: Mapping[str, Any], *, do_roll: bool = True) -> Any:
    """Resolve one registered knob. Order (data-model.md): pinned -> rolled -> default. A pinned value
    that is not in the value_space, or that violates the typing_rule, is a loud error - never silently
    drawn (contract C3). With do_roll=False an unpinned knob falls straight to its default (a map that
    opts out of rolling this knob)."""
    knob = KNOBS[name]
    if pinned.get(name) is not None:
        val = pinned[name]
        if val not in knob.value_space:
            raise ValueError(f"knob {name!r}: pinned value {val!r} is not in its value space {knob.value_space}")
        if not knob.typing_rule(val, context):
            raise ValueError(f"knob {name!r}: pinned value {val!r} violates its typing rule for context {dict(context)!r}")
        return val
    if do_roll:
        return knob.roll(seed, context)
    return knob.default


# ---- Family-A knob catalog (feature 005, US1): the within-archetype layout knobs --------------
# Registered at import so a spec can pin or roll them. Value spaces + typing rules follow data-model.md
# D2 / research.md D2 (China-first). Each typing rule reads the village's stated geography from the
# resolution `context` (water_kind, field_origin, scale, ...) and excludes values that would be
# historically incoherent there, so an INDEPENDENT per-knob roll still lands on a coherent village.


def _lane_skeleton_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A 'waterside' lane skeleton needs water running ALONG the cluster (a stream/canal beside it), not
    merely a valley-head pond uphill - so it is allowed only for a stream-fed village or one that
    explicitly declares a waterside/canal site."""
    if v == "waterside":
        return ctx.get("water_kind") == "stream" or bool(ctx.get("waterside_site"))
    return True


def _water_source_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """Stream 'edge_*' entry points need a stream source; the pond positions (corner/mid_margin/chain)
    need a pond. Gravity feed (source uphill of the field intake) is a PLACEMENT concern enforced when
    the source is drawn, not a value exclusion here."""
    if v.startswith("edge_"):
        return ctx.get("water_kind") == "stream"
    return ctx.get("water_kind") != "stream"


# The two attested ways of making every house in a nucleated cluster reachable. Defined up here
# rather than beside `web_cuts` because the knob catalog below registers against it at import.
LANE_WEBS = ("alleys", "back_lane")


def _cluster_shape_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A 'split' cluster needs room for two hamlets to read separately - a village/town, not a hamlet."""
    return v != "split" or ctx.get("scale") in ("village", "town")


def _plot_regularity_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A rectilinear 'grid' bund pattern implies a planned/surveyed field (a reclamation or allotment
    context), not an organically-grown old one - so it is excluded unless the field origin is planned."""
    return v != "grid" or ctx.get("field_origin") == "planned"


def _field_archetype_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """The FIELD terrain archetype must match the village's stated terrain (research.md D4, China-first):
    contour_terraces need HILL/upland ground; polder_grid needs LOW reclaimed/coastal-delta ground; a
    ribbon_valley needs a narrow valley floor; a mulberry_dike_fishpond is the Pearl-delta low-wet system.
    valley_paddy (the comb default) fits any ordinary valley-bottom terrain. Terrain is read from
    `ctx['terrain']` when the spec declares it; absent a declaration, only valley_paddy is coherent."""
    terrain = ctx.get("terrain")
    need = {"valley_paddy": None, "contour_terraces": "hill", "polder_grid": "low", "ribbon_valley": "narrow_valley", "mulberry_dike_fishpond": "low"}
    req = need.get(v)
    return req is None or terrain == req


def _toward(frm: Pt, to: Pt, dist: float) -> Pt:
    """A point `dist` along the way from `frm` to `to`, never past 45% of the run - so a fillet leg
    piled onto a short plot edge still leaves that edge with a middle."""
    vx, vy = to[0] - frm[0], to[1] - frm[1]
    ln = math.hypot(vx, vy) or 1.0
    dd = min(dist, ln * 0.45)
    return (frm[0] + vx / ln * dd, frm[1] + vy / ln * dd)


def _centroid(poly: Sequence[Pt]) -> list[float]:
    """Rounded centroid of a plot polygon - the identity a land-use record and a wet-plot record share."""
    return [round(sum(p[0] for p in poly) / len(poly), 1), round(sum(p[1] for p in poly) / len(poly), 1)]


def _sharp_corners(poly: Sequence[Pt]) -> int:
    """How many vertices of a closed outline turn through more than 60 degrees - i.e. how many corners
    are still essentially square. A ruled quad scores 4. Counting them, rather than taking the SHARPEST
    turn, is what survives the rule getting more honest: once corner reach is drawn from a wide spread
    some corners legitimately stay near-square (the one behind a neighbor's bund never gets walked),
    so a max is a statistic about the single least-rounded corner on the parcel and says nothing about
    the parcel. The count does: it separates 'a few corners never rounded' from 'nothing rounded'."""
    n = len(poly)
    hard = 0
    for i in range(n):
        ax, ay = poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1]
        bx, by = poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la < 1e-9 or lb < 1e-9:
            continue  # a duplicate vertex turns through no angle at all
        hard += math.degrees(math.acos(max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb))))) > 60.0
    return hard


def _land_use_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """A LAND-USE overlay must suit the setting: mulberry_fishpond + lotus are wet/valley uses fine on ordinary
    paddy land; a tea_fringe needs some hill/terrace margin (`ctx['terrain']` hill, or a terrace archetype) to
    sit on. 'none' (plain rice) is always valid.

    WHY EVERY VALUE HERE IS A *PERMANENT* USE, never a rotation (GM, 2026-07): an overlay recolors SOME plots
    while the rest stay standing rice, so it may only hold crops that genuinely coexist with rice in the same
    season. A dike-pond, a lotus paddy and a hill tea garden are permanent installations - the plot is given
    over to them all year, so the plot next door can be rice. RAPE (油菜) was tried here and REMOVED: rice and
    rape are the two halves of one ROTATION in the SAME plot (rice transplanted May-June and harvested
    Sep-Oct; rape sown into the drained stubble Oct-Nov, flowering Mar-Apr, off by May), so they are never
    both standing. Mixing them at ANY fraction depicts two seasons at once. What varies between households is
    only whether a plot is double-cropped at all, and that shows up in the SPRING picture as yellow rape
    against BARE stubble / standing water - never against green rice. Rape therefore belongs on a future
    seasonal axis (a whole-field state), not on this per-plot land-use axis. Do not re-add it here."""
    if v in ("none", "mulberry_fishpond", "lotus"):
        return True
    return ctx.get("terrain") == "hill" or ctx.get("field_archetype") == "contour_terraces"  # tea_fringe


def _settlement_form_ok(v: Any, ctx: Mapping[str, Any]) -> bool:
    """The SETTLEMENT FORM must suit the site: nucleated/linear/dispersed fit anywhere, but a WATER-TOWN (houses
    fronting a canal) needs a canal - and per GM setting canon artificial transport canals are a LION-lands
    feature, not the Empire-wide default (see the diagram SKILL.md China-first note), so water_town is excluded
    unless the map declares Lion lands or a canal (`ctx['clan']=='Lion'` or `ctx['canal']`)."""
    if v in ("nucleated", "linear", "dispersed"):
        return True
    if v == "dike_top":  # a dike-top line stands ON a polder's perimeter dike, so it needs LOW reclaimed ground
        return ctx.get("terrain") == "low"
    return ctx.get("clan") == "Lion" or bool(ctx.get("canal"))  # water_town


register_knob(Knob("settlement_form", ["nucleated", "linear", "dispersed", "water_town", "dike_top"], default="nucleated", typing_rule=_settlement_form_ok))
register_knob(Knob("field_archetype", ["valley_paddy", "contour_terraces", "polder_grid", "ribbon_valley", "mulberry_dike_fishpond"], default="valley_paddy", typing_rule=_field_archetype_ok))
register_knob(Knob("land_use_overlay", ["none", "mulberry_fishpond", "lotus", "tea_fringe"], default="none", typing_rule=_land_use_ok))
register_knob(Knob("cluster_position", ["high_margin", "flank", "mid_margin", "valley_mouth", "valley_head", "on_rise"], default="high_margin"))
register_knob(Knob("cluster_shape", ["round", "elongated", "crescent", "split"], default="round", typing_rule=_cluster_shape_ok))
register_knob(Knob("lane_web", list(LANE_WEBS), default="alleys"))
register_knob(Knob("lane_skeleton", ["spine", "T", "Y", "cross", "waterside"], default="spine", typing_rule=_lane_skeleton_ok))
register_knob(
    Knob(
        "water_source_position",
        ["corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain", "edge_N", "edge_E", "edge_S", "edge_W"],
        default="corner_NW",
        typing_rule=_water_source_ok,
    )
)
register_knob(Knob("plot_size", ["small_irregular", "medium", "large_block", "strip"], default="medium"))
register_knob(Knob("plot_regularity", ["organic", "grid"], default="organic", typing_rule=_plot_regularity_ok))
register_knob(Knob("grain_drift", [-12, -8, -4, 0, 4, 8, 12], default=0))  # degrees of paddy-grain drift off the fall-line


LANE_SKELETONS = ("spine", "T", "Y", "cross", "waterside")


def web_cuts(coords: Sequence[float], reach: float, gap: float) -> list[float]:
    """WHERE TO CUT A LANE THROUGH A ROW OF HOUSES so every one of them is within `reach` of a way.

    Pure 1-D, and that is what makes it serve both forms of the lane web off one implementation:
    for `alleys` the coordinates are the houses' positions ALONG the field margin and each cut
    becomes a lateral running back through the cluster; for `back_lane` they are the houses'
    STANDOFFS from the field and each cut becomes a lane running the length of the settlement,
    behind a rank. Same problem, same answer, turned ninety degrees.

    THE CUT GOES IN A GAP, NEVER THROUGH A HOUSE. `gap` is the least room a lane needs between two
    neighbors; among the gaps that qualify within reach ahead of an uncovered house, the widest wins,
    because the widest gap is the one a lane fits down without crowding either steading. That is
    also how these ways came to exist - the sources describe the lateral ones as "colonised as semi
    private space by the adjoining house", which is a lane that IS the leftover room between two
    plots rather than a corridor set aside before anyone built.

    Fewest cuts that do the job, greedily: walk the houses in order, skip any already within reach of
    the last cut, and when one is not, place the next cut as far ahead as it can go while still
    covering that house. Minimal matters - a hamlet threaded with a lane between every pair of houses
    is a hairball, not a settlement, and an earlier version of this feature drew 34 internal lanes on
    a 19-house map.

    Falls back to `reach * 0.5` ahead when no gap in the window is wide enough: a lane there will be
    broken up by whatever it runs into, which is the honest outcome, and is preferable to leaving a
    house unreachable because its neighbors are packed tight."""
    xs = sorted(float(c) for c in coords)
    if not xs:
        return []
    gaps = [((xs[k + 1] - xs[k]), (xs[k] + xs[k + 1]) / 2.0, xs[k]) for k in range(len(xs) - 1)]
    cuts: list[float] = []
    for x in xs:
        if cuts and abs(x - cuts[-1]) <= reach:
            continue
        # The candidate must still COVER x. Filtering on the gap's left edge alone is not the same
        # test and lets the widest gap in the window sit beyond reach of the very house that
        # triggered the cut - measured: houses at 0/95/190/300/410/505/600/700 with reach 100 left
        # the one at 505 a full 145 away, because a 100 ft gap starting at 600 outranked a 95 ft gap
        # starting at 505. The midpoint is where the lane actually goes, so the midpoint is what has
        # to be within reach.
        window = [(w, mid) for w, mid, left in gaps if x <= left and mid <= x + reach and w >= gap]
        cuts.append(max(window)[1] if window else x + reach * 0.5)
    return cuts


def skeleton_layout(kind: str, cx: float, cy: float, ex: float, ey: float) -> dict[str, Any]:
    """Pure geometry for a nucleated cluster's internal lane skeleton. Given the cluster center (cx, cy)
    and its half-extents (ex horizontal, ey vertical, in px), returns the lane polylines plus the two
    DERIVED focal points a village reads by: the headman compound (the grandest house, at the skeleton's
    prime spot) and the gateway (the downslope exit where the connector track leaves and the tutelary
    shrine sits). Screen frame: -y = upslope/back (the high, dry 背 side), +y = downslope toward the
    field; +x = toward the field flank. The headman lands at a DIFFERENT spot per skeleton (never a fixed
    offset), which is the whole point - it is why two same-water villages stop sharing a headman position.
    Grounding (research.md D2): a nucleated village's lanes followed its site - a spine along a ridge, a T
    where a spur met the field track, a Y where two approaches merged, a cross at a small market node, a
    waterside lane in a stream village - and the headman sat at that skeleton's focal point, not a pixel."""
    top, bot = cy - ey, cy + ey
    if kind == "spine":  # one lane along the margin; headman at the high HEAD, gateway at the low foot
        lanes = [[(cx, top), (cx, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, top + ey * 0.12), "gateway": (cx, bot)}
    if kind == "T":  # spine + an upper crossbar toward the field; headman at the T-junction
        cj = cy - ey * 0.4
        lanes = [[(cx, top), (cx, bot)], [(cx - ex, cj), (cx + ex, cj)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, cj), "gateway": (cx, bot)}
    if kind == "Y":  # two approaches merging into one downslope stem; headman at the fork
        fy = cy + ey * 0.2
        lanes = [[(cx - ex * 0.7, top), (cx, fy)], [(cx + ex * 0.7, top), (cx, fy)], [(cx, fy), (cx, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx, fy), "gateway": (cx, bot)}
    if kind == "cross":  # two crossing lanes at a small market node; headman in an adjacent quadrant
        lanes = [[(cx, top), (cx, bot)], [(cx - ex, cy), (cx + ex, cy)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx - ex * 0.4, cy - ey * 0.22), "gateway": (cx, bot), "market": (cx, cy)}
    if kind == "waterside":  # a lane hugging the water flank; headman fronting the water
        lanes = [[(cx - ex, top), (cx - ex, bot)]]
        return {"kind": kind, "lanes": lanes, "headman": (cx - ex, cy), "gateway": (cx - ex, bot)}
    raise ValueError(f"unknown lane_skeleton {kind!r}; expected one of {LANE_SKELETONS}")


TORII_WEIGHTS = {
    # TORII COUNT DISTRIBUTIONS (GM 2026-07-21): counts are NUMEROLOGICAL - 1, 3, or 7 only (7 is even
    # more potent in Rokugan than in the real world). Weights per settlement tier; the richer the tier,
    # the deeper the accumulated patronage (torii are DONATED votive gates - see settlements.md 'Torii'
    # for the historical grounding and the deliberate Rokugan liberties). "capital" is recorded ahead of
    # need - no capital-city maps exist yet.
    "village": ((1, 0.60), (3, 0.30), (7, 0.10)),
    "town": ((1, 0.30), (3, 0.60), (7, 0.10)),
    "city": ((1, 0.30), (3, 0.40), (7, 0.30)),
    "capital": ((1, 0.10), (3, 0.60), (7, 0.30)),
}


def roll_torii_count(scale: str, rng: random.Random) -> int:
    """Roll a hall's torii count for the tier: always 1, 3, or 7 (torii_count_canonical gates it),
    weighted by TORII_WEIGHTS. Unknown scales roll the village column (the conservative tier)."""
    weights = TORII_WEIGHTS.get(scale, TORII_WEIGHTS["village"])
    x = rng.random()
    acc = 0.0
    for count, wt in weights:
        acc += wt
        if x < acc:
            return count
    return weights[-1][0]


MERCHANT_ESTATE_WEIGHTS: dict[str, tuple[tuple[int, float], ...]] = {
    # CAPITAL (021, the counts table): 48 rich families against the provincial 12 - the
    # walled-estate privilege lands on ~4-8 of them, weighted to the middle of that band
    "capital": ((4, 0.15), (5, 0.25), (6, 0.3), (7, 0.2), (8, 0.1)),
    # WALLED MERCHANT COMPOUND COUNT DISTRIBUTION (GM 2026-07-23). A gated compound is a PRIVILEGE
    # that must be explicitly GRANTED to a merchant family, not a purchase: this mirrors the
    # Edo-period system of individually granted merchant rights and privileges - an audience with
    # the daimyo at the New Year's celebration, permission to carry a persistent surname across
    # generations despite not being samurai (myoji gomen), and the like. So even most VERY rich
    # merchants do not have one: they can afford the wall, but lack the legal standing to build it.
    # A provincial city holds ~12 very-rich merchant families (budgets.md, 2% of ~3,000), of whom
    # only 1-3 hold the grant - rolled 30% / 40% / 30% per city, seeded on the map seed (the same
    # deterministic re-roll pattern as TORII_WEIGHTS above). "capital" is left to be added when
    # capital maps exist, like the torii table did for its tiers.
    "city": ((1, 0.30), (2, 0.40), (3, 0.30)),
}


def roll_merchant_estate_count(scale: str, rng: random.Random) -> int:
    """Roll how many walled merchant compounds a settlement carries, weighted by
    MERCHANT_ESTATE_WEIGHTS - see that table for the granted-privilege reasoning. Scales without
    a column (villages, towns today) do not roll; callers hand-place there."""
    weights = MERCHANT_ESTATE_WEIGHTS[scale]
    x = rng.random()
    acc = 0.0
    for count, wt in weights:
        acc += wt
        if x < acc:
            return count
    return weights[-1][0]


# WALL DEFENSE POSTURE (GM 2026-07-22): a walled city's guard-tower coverage is TUNABLE per city
# (meta wall_defense=), because how heavily a wall is towered reflects its history and threat exposure -
# a border city that has repelled sieges packs its towers to the aimed-lethal-bowshot spacing so every
# stretch of the wall base is under crossfire from >=2 towers; a city that has known centuries of peace
# runs the sparser Xi'an spacing. Each tier maps to (effective arrow range in FEET, minimum towers that
# must cover every wall point within that range). The historical grounding (侧射 flanking fire; Shen Kuo's
# 11th-c. 矢石相及; Xi'an 120 m / Pingyao ~55 m mamian spacing at a ~60 m aimed-lethal bowshot) is in
# settlements.md. Gated by city_wall_tower_coverage; used to set the mural-tower spacing in city_wall.
WALL_DEFENSE = {
    # tier          (arrow_range_ft, min_towers)  placement spacing = range if min==2 else 2*range
    "siege": (197.0, 2),  # border / besieged city: aimed-lethal bowshot (60 m), >=2 towers EVERYWHERE (Pingyao-dense)
    "garrison": (328.0, 2),  # garrisoned interior city: full war-bow reach (100 m), >=2 towers everywhere
    "peaceful": (197.0, 1),  # long-peaceful city: Xi'an crossfire - spacing <= 2x60 m, so >=1 flanking tower within aimed-lethal range everywhere (midpoints get 2)
}


KOSATSUBA_MARKER_MIN_PX = 11.0
# Long-axis floor in px for the DRAWN notice-board glyph (see Settlement.kosatsuba). 11 px is the
# size the true 12x5 ft frame already draws itself at 1 ft/px - the hamlet/town tiers, where the
# board has always read fine - so the floor is calibrated to "as legible as it is on a town map",
# not to a number picked for the city. It lands the city marker (11x4.6 px at 3 ft/px) just above
# the city wellhead glyph (~8 px), which is the smallest thing on a city map that reliably reads.


PUNISHMENT_SPOT_FT = (30.0, 12.0)  # the cangue frame + post + kneeling stone, true size at every tier
BOUNDARY_MARKER_FT = 3.0  # a real roadside dosojin stone (drawn as a marker - see BOUNDARY_MARKER_MIN_PX)


#: The scales that draw as a WALLED URBAN RING at the city grain. A domain capital is a bigger
#: city, not a different kind of thing: it wants the same execution-ground sizing, the same
#: in-wall grove suppression, the same street widths and the same walled-ring paddy handling. So
#: the tier predicates are WIDENED rather than forked (feature 019) - the opposite of what
#: citybudget does for the BUDGET, and for the opposite reason: there a shared path risked
#: repricing shipped cities, here the shared behavior is simply the correct behavior and
#: duplicating it would fork the drawing vocabulary.
CITY_TIER_SCALES = ("city", "capital")


def execution_ground_ft(scale: str) -> tuple[float, float]:
    """Tier footprint of an execution ground in REAL FEET, scaled down from the Suzugamori anchor
    (74 x 16.2 m serving Edo) by execution volume - see settlements.md "Execution ground".

    SHARED DATA, deliberately: Settlement.execution_ground draws from this, and site_justice.py
    sizes its trial placements from it, so a tool proposing a seat can never disagree with the
    engine about how big the thing it is seating actually is."""
    return (100.0, 60.0) if scale in CITY_TIER_SCALES else (60.0, 60.0)


BOUNDARY_MARKER_MIN_PX = 7.0
# Long-axis floor in px for the DRAWN dosojin stone (see Settlement.boundary_marker). A real
# roadside boundary stone is ~3 ft, which draws 3 px at town grain and 1 px at city grain - sub-glyph
# at EVERY tier, so this is a location marker in the wells' sense, never a size claim. 7 px is below
# the wellhead glyph (~8 px) on purpose: the stone should read as the smallest deliberate mark on the
# map, because that is what it is.

BOUNDARY_STONE_CLEAR_FT = 60.0
# Minimum real feet of open ground between a dosojin and the nearest dwelling on an UNWALLED map,
# enforced by execution_ground_past_the_boundary_marker. Where there is a rampart the wall settles
# "outside" instead and this does not apply.
#
# WHY 60 AND NOT THE 120 THE POLLUTION RULES USE. The stone is a MARKER, not a polluting
# installation: it says where the road leaves clean ground, and a real one stands at the village
# edge rather than a bowshot past it. What it must not do is stand AMONG the houses, so the figure
# is the same "legible band of open ground" the burakumin seam asks for - several times the ~10-30
# ft that dwellings inside a quarter pack at, so the gap reads as a gap rather than as a wide lane.
# The first draft of the rule reused the 120 ft pollution separation for the sake of having one
# number; that squeezed the stone between its own floor and the ground it bounds into a ~25 ft band
# on Hoshizora, which is how a borrowed constant announces itself (GM, 2026-07-27).

EXECUTION_GROUND_DEAD_CLEAR_FT = 400.0
# Minimum real feet between an execution ground and any funerary feature (cemetery, cremation ground,
# ossuary, mausoleum), enforced by execution_ground_clear_of_the_dead.
#
# THIS NUMBER IS A MAP-LEGIBILITY FLOOR, NOT A HISTORICAL MEASUREMENT, and saying so is the
# disclosure Principle XII's calibrated-liberty clause requires. In reality the two were not
# separated by feet at all: the executed went into a pit AT the execution ground (Kozukappara's
# burials were haphazard enough that a memorial hall was founded beside it in 1667 for exactly that
# reason), while the community's own dead went to temple graveyards elsewhere in the city entirely -
# typically a different road out of town, often a mile off. Our maps are a few thousand feet across
# and cannot hold that, so we compress it and keep the RELATIVE ordering honest instead: the
# execution ground is always the further-out, more polluted of the two. 150 ft is one band above the
# project's existing pollution constant (the cremation ground and tanning yard demand 120 ft clear of
# dwellings) because 120 ft separates polluted ground from CLEAN ground, whereas two polluted grounds
# at that spacing read as one precinct - which is the exact conflation this rule exists to prevent.
#
# RAISED 150 -> 400 by the Principle XII artifact review (2026-07-25), which is exactly the kind of
# thing that review exists to catch: Nagahara's ground passed the 150 ft rule at 225 ft and STILL
# read, in the rendered PNG, as part of the burial cluster next door. 150 ft was derived by analogy
# to the dwelling-separation constant; 400 ft is derived from the picture - it is the distance at
# which, at the coarsest grain we draw (3 ft/px, so 133 px), the two grounds are unmistakably two
# places. The automated check proved internal consistency and the number was still wrong; only
# looking at the artifact could show that.
# WHY (full): settlements.md "Execution ground".

KIDO_TOWER_KEEPCLEAR = 62.0
# px of rampart kept tower-free around a `tower_skip` spot - where a ward FENCE meets the city wall
# (its kido ward-gate stands there; a mamian's footprint would collide the junction). Placement
# refuses towers inside this band (city_wall's even-fill), so the coverage check EXEMPTS curtain
# points inside it too (the check-keep-outs-mirror-placement-keep-outs doctrine, same as the
# water-gate exemption): the junction is a manned chokepoint, not open curtain - and demanding
# 2-tower coverage of it forced the remediation pass to seat a DOUBLED tower right outside the
# band (the Tango/Nagahara adjacent-tower artifacts, GM 2026-07-23, wall_towers_evenly_spaced).


def wall_tower_spacing_px(scale_px_per_ft: float, tier: str) -> float:
    """Max mural-tower spacing (px) that satisfies a wall_defense tier: the arrow range for a >=2 tier
    (so a point at any tower has a neighbor within range), or twice it for the >=1 Xi'an tier. Unknown
    tiers fall back to 'garrison' (the moderate middle). `scale_px_per_ft` is 1/ftpx."""
    rng_ft, mincov = WALL_DEFENSE.get(tier, WALL_DEFENSE["garrison"])
    return (rng_ft if mincov == 2 else 2 * rng_ft) * scale_px_per_ft


def bridge_carried_ways(M: Any) -> list[tuple[Any, float]]:
    """Every WAY a bridge may have to carry, as (points, width). THE SINGLE SOURCE for both sides.

    WHY THIS IS A SHARED FUNCTION AND NOT TWO MATCHING LISTS (feature 020). The generator's
    `bridges()` and the validator's `roads_bridge_water` used to build these sets separately, and
    both omitted the same three things - `M["roads"]` (every road but the Imperial one), the river,
    and a castle's own moat. So they agreed perfectly and were both wrong, and four of six crossings
    on the first capital were unbridged with a green gate. The skill's rule that "placement and its
    check must read the SAME manifest source" is what guarantees they cannot disagree; this is the
    case that shows it guarantees AGREEMENT, not CORRECTNESS. Re-adding the missing keys on both
    sides would have reproduced exactly the same silent symmetry the next time a key was added, so
    the sets are derived ONCE, here, and consumed by both."""
    carried: list[tuple[Any, float]] = []
    if M.get("road"):
        carried.append((M["road"], M.get("road_width", 26)))
    for rd in M.get("roads", []):  # every OTHER trunk road - the omission that left two gates unbridged
        carried.append((rd["pts"], rd.get("w", 26)))
    if M.get("ring_road"):
        carried.append((M["ring_road"], M.get("ring_road_width", 8)))
    for st in M.get("town_streets", []):
        carried.append((st["pts"], st["w"]))
    for ln in M.get("lanes", []):
        carried.append((ln["pts"], ln.get("w", 6)))
    return carried


def bridge_crossed_waters(M: Any) -> list[tuple[Any, float]]:
    """Every WATERCOURSE a way may have to be carried over, as (points, width). See
    `bridge_carried_ways` for why both sides read this one function."""
    waters: list[tuple[Any, float]] = []
    for s in M.get("streams", []):
        waters.append((s["poly"], s.get("w", 9)))
    for c in M.get("channels", []):
        if c.get("drawn", True):  # an UNDRAWN channel is a buried conduit - no seam on the ground to bridge
            waters.append((c["poly"], c.get("w", 4.2)))
    for d in M.get("field_ditches", []):
        waters.append((d["poly"], d.get("w", 4.2)))
    for cn in M.get("canals", []):
        waters.append((cn["poly"], cn.get("w", 12)))
    if M.get("moat"):
        waters.append((M["moat"], M.get("moat_width", 22)))
    riv = M.get("river")  # the trunk river - a road crossing one was NEVER bridged, anywhere in the pool
    # s.river records "pts" (the "poly" spelling never occurs in a real manifest, so a branch
    # reading only it is a check that never runs). The river also rides in M["streams"], so this
    # entry can duplicate that one - harmless, because bridge() keeps one deck per crossing.
    if isinstance(riv, dict) and (riv.get("pts") or riv.get("poly")):
        waters.append((riv.get("pts") or riv["poly"], riv.get("w", 40)))
    for c2 in M.get("castles", []):  # a castle's OWN moat is water like any other
        if c2.get("moat"):
            waters.append((c2["moat"], c2.get("moat_width", 26)))
    for aq in M.get("aqueducts", []):  # an open supply cut is a seam on the ground like any channel
        waters.append((aq["poly"], aq.get("w", 8)))
    return waters


def machi_mouths(M: Any) -> list[tuple[float, float]]:
    """Every point where a town street ENTERS a machi-kind district - the ward mouths the kido
    mesh bars at night (research 021 item 6: Edo's machi-kido, Qing's zhalan; ward_style
    "mesh" has NO ward walls - the block's own gate closes its mouth). THE SINGLE SOURCE for
    both the placer (Settlement.kido_mesh) and the validator (kido_close_the_machi_mouths),
    same doctrine as bridge_carried_ways. Out-wall suburb districts are skipped: the gate
    wards live outside the curfew mesh (their bar is the city gate itself). Mouths within
    40px collapse to one (a street grazing a district corner is one entry, not two)."""
    wall = M.get("wall")
    out: list[tuple[float, float]] = []
    for d in M.get("districts", []):
        if d.get("kind") != "machi":
            continue
        poly = d["poly"]
        if wall:
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            if not point_in_poly(cx, cy, wall):
                continue
        ring = [tuple(p) for p in poly] + [tuple(poly[0])]
        for st in M.get("town_streets", []):
            pts = st["pts"]
            for i in range(len(pts) - 1):
                for j in range(len(ring) - 1):
                    if not segments_cross(tuple(pts[i]), tuple(pts[i + 1]), ring[j], ring[j + 1]):
                        continue
                    xpt = seg_intersect(tuple(pts[i]), tuple(pts[i + 1]), ring[j], ring[j + 1])
                    if xpt is not None and not any(math.hypot(xpt[0] - ox, xpt[1] - oy) < 40 for ox, oy in out):
                        out.append((xpt[0], xpt[1]))
    return out


def moat_current_at(ring: Any, inlet: Pt, outlet: Pt, pt: Pt) -> tuple[float, float] | None:
    """The moat's flow direction at `pt`: the ring tangent pointing the way water travels toward the
    outlet along the arc `pt` sits on.

    A ring has NO single downstream side - water entering the inlet runs BOTH ways round to the
    outlet - so "the moat's current" is only ever a local quantity. SHARED between the generators
    (which sweep an offtake throat and land a drain culvert with it) and check_village's
    `moat_junctions_swept_with_the_current` (which judges the result), because a check that
    re-derives what the generator computed drifts from it.

    The tangent is the chord between the vertex's two NEIGHBORS, not the forward segment: taking the
    forward segment alone tilts every reading by about half the vertex's turn angle, consistently
    enough (~8-9 deg on these rings) to misclassify a square tap as upstream-facing."""
    n = len(ring)
    if n < 3:
        return None

    def ix(q: Pt) -> int:
        return min(range(n), key=lambda k: math.hypot(ring[k][0] - q[0], ring[k][1] - q[1]))

    i_in, i_out, it = ix(inlet), ix(outlet), ix(pt)
    step = 1 if (it - i_in) % n <= (i_out - i_in) % n else -1
    a, b = ring[(it - step) % n], ring[(it + step) % n]
    vx, vy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(vx, vy)
    return None if L == 0 else (vx / L, vy / L)


def _below_drain(x: float, y: float, drain: Any, fx: float, fy: float, berth: float = 26.0) -> bool:
    """Is (x, y) downslope of the drain COLLECTOR? Measured to the NEAREST POINT on the drain
    polyline and projected along the fall - which is what the check does. A global cut along the
    fall axis is not the same thing and lets a farmstead sit in the toe where the drain bends."""
    best = (float("inf"), drain[0])
    for k in range(len(drain) - 1):
        ax, ay = drain[k]
        bx, by = drain[k + 1]
        dx, dy = bx - ax, by - ay
        ll = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ll))
        px_, py_ = ax + t * dx, ay + t * dy
        d = math.hypot(x - px_, y - py_)
        if d < best[0]:
            best = (d, (px_, py_))
    nx, ny = best[1]
    return bool((x - nx) * fx + (y - ny) * fy > -berth)


def _seg_point(pt: Pt, a: Pt, b: Pt) -> Pt:
    """The point on segment a-b nearest `pt` - so a tap is DERIVED from the watercourse rather than
    eyeballed beside it (every hand-picked tap in the capital's first ring stood on dry ground)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / ll))
    return (a[0] + t * dx, a[1] + t * dy)


def _poly_centroid(poly: Poly) -> Pt:
    return (sum(q[0] for q in poly) / len(poly), sum(q[1] for q in poly) / len(poly))


def moat_swept_tap(ring: Any, inlet: Pt, outlet: Pt, other: Pt, near: Pt, want_deg: float = 50.0, max_back: float = 220.0, arriving: bool = False) -> Pt:
    """The rim point an offtake should leave from so its throat is SWEPT DOWNSTREAM into the sluice.

    Canal practice: an offtake leaves its parent at an ACUTE angle pointing downstream - best
    alignment 0 deg separating out in transition, with the studied optimum for water and sediment at
    15-45 deg, explicitly "30 or 45 instead of 90". A square tap sheds sediment into its own mouth
    and, on the page, says nothing about which way the water runs.

    Only the MOAT-SIDE end moves. The sluice stays exactly where it is, so the comb field it feeds
    does not shift by a pixel; the throat simply becomes a diagonal from a point further upstream.
    Walks upstream by ARC LENGTH, not by vertex: a vertex step on these rings is ~140 px against a
    ~30 px throat, which overshoots past the target into a channel running nearly parallel to the
    rim. The wanted offset is a fraction of an edge (~36 px for a 30 px throat at 40 deg), so the
    walk samples every few px and takes the FIRST point that is swept enough - the nearest such
    point, keeping the tap close to the field it feeds."""
    n = len(ring)
    if n < 3:
        return near

    def ix(q: Pt) -> int:
        return min(range(n), key=lambda k: math.hypot(ring[k][0] - q[0], ring[k][1] - q[1]))

    i0, i_in, i_out = ix(near), ix(inlet), ix(outlet)
    step = 1 if (i0 - i_in) % n <= (i_out - i_in) % n else -1  # +1 where travel runs with the index
    # An OFFTAKE leaves the ring, so its rim end walks UPSTREAM and the throat (other - cand) then
    # runs with the current. A DRAIN arrives, so its landing walks DOWNSTREAM and the arriving
    # segment (cand - other) runs with the current. Same geometry, mirrored.
    if arriving:
        step = -step
        max_back = min(max_back, 90.0)  # a culvert landing must stay NEAR its drain's tail: walk too
        # far and the culvert's sink end ends up closer to the drain's HEAD than its tail, which flips
        # the outfall attribution drain_flows_downhill depends on (Nagahara's fnn2 did exactly this).

    def sweep(p: Pt) -> float:
        cur = moat_current_at(ring, inlet, outlet, p)
        vx, vy = (p[0] - other[0], p[1] - other[1]) if arriving else (other[0] - p[0], other[1] - p[1])
        L = math.hypot(vx, vy)
        if cur is None or L == 0:
            return 999.0
        return math.degrees(math.acos(max(-1.0, min(1.0, (vx * cur[0] + vy * cur[1]) / L))))

    best, best_ang, walked, cur_i = near, sweep(near), 0.0, i0
    while walked < max_back:
        a, b = ring[cur_i % n], ring[(cur_i - step) % n]  # the edge running UPSTREAM from here
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if seg == 0:
            cur_i -= step
            continue
        t = 0.0
        while t < seg and walked < max_back:
            t, walked = t + 5.0, walked + 5.0
            f = min(1.0, t / seg)
            cand = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            ang = sweep(cand)
            if ang < best_ang:
                best, best_ang = cand, ang
            if ang <= want_deg:
                return (round(cand[0], 1), round(cand[1], 1))
        cur_i -= step
    return (round(best[0], 1), round(best[1], 1))


def crop_boxes(M: Any, city: bool, ftpx: float, W: float, H: float) -> list[tuple[float, float, float, float, str]]:
    """Every feature that SETS the render frame, as labeled boxes (x0, x1, y0, y1, what).

    SINGLE SOURCE OF TRUTH, shared by `crop_to_content` / `crop_city` - which reduce it to a
    bounding box - and by check_village's `crop_not_held_open_by_one_feature`, which asks the
    opposite question: WHICH feature is setting each edge, and is it out there on its own?
    Keeping one list is what stops the crop and the check that gates it from drifting apart
    (the recurring engine trap recorded in the dev-loop doc: placement and its check must read
    the same manifest source). The two crops take DIFFERENT sets by design - a city frames on
    its moat ring, satellites and labels while its paddy fans and farmhouses clip at the edge -
    so the `city` flag selects which."""
    from .core import Settlement  # lazy: runtime class-attr read, import cycle otherwise

    out: list[tuple[float, float, float, float, str]] = []

    def add(o: Any, k: str, i: int) -> None:
        # some area keys (forest_patches, pastures) record a RAW POLYGON, not a dict - they are
        # drawn ground and set the frame like any other area
        if not isinstance(o, dict):
            xs = [p[0] for p in o]
            ys = [p[1] for p in o]
            out.append((min(xs), max(xs), min(ys), max(ys), f"{k}[{i}]"))
            return
        lab = f"{k}[{i}]" + (f" '{o.get('label')}'" if o.get("label") else "")
        # `outline` counts as well as `poly` (2026-08-13). A record whose ring is called `outline` -
        # a perimeter dike is the one in this list - matched none of these branches and was extracted
        # as NOTHING, so it could not hold the frame however carefully it was classified. Exactly the
        # trap this skill's notes record for the OVERLAP extractor ("a feature the extractor never
        # reaches is invisible in both directions no matter how carefully it is classified"), one
        # extractor over: adding the key to _CROP_HARD changed nothing until this line changed too.
        _ring = o.get("poly") or o.get("outline")
        if _ring:
            xs = [p[0] for p in _ring]
            ys = [p[1] for p in _ring]
            out.append((min(xs), max(xs), min(ys), max(ys), lab))
        elif "r" in o:  # a well records {x, y, r} - no poly, no w/h
            out.append((o["x"] - o["r"], o["x"] + o["r"], o["y"] - o["r"], o["y"] + o["r"], lab))
        elif "w" in o and "h" in o:
            out.append((o["x"] - o["w"] / 2, o["x"] + o["w"] / 2, o["y"] - o["h"] / 2, o["y"] + o["h"] / 2, lab))

    if city:
        wallp = M.get("wall")
        for k in Settlement._CROP_CITY:
            for i, o in enumerate(M.get(k, [])):
                if k == "buildings" and o.get("kind") == "shop" and wallp and not point_in_poly(o["x"], o["y"], wallp):
                    continue  # the extramural gate-market / wharf stall STRING clips at the edge (the slice doctrine)
                add(o, k, i)
        for mp_ in M.get("moat") or []:  # the city itself (moat encloses the wall)
            out.append((mp_[0], mp_[0], mp_[1], mp_[1], "moat"))
        for i, lb in enumerate(M.get("labels", [])):  # placed label boxes: [x0, y0, x1, y1, z, text(, ref, tilt)] - label_aabb reads tilted records too
            _la = label_aabb(lb)
            out.append((_la[0], _la[2], _la[1], _la[3], f"label {lb[5]!r}" if len(lb) > 5 else f"labels[{i}]"))
        return out
    for k in Settlement._CROP_HARD:
        for i, o in enumerate(M.get(k, [])):
            add(o, k, i)
    _txh, _tyu, _tyd = torii_halfbox(ftpx)  # a torii ARCH is a visible structure and must be framed
    for i, t in enumerate(M.get("torii", [])):
        out.append((t[0] - _txh, t[0] + _txh, t[1] - _tyu, t[1] + _tyd, f"torii[{i}]"))
    for fd in M.get("fields", []):  # the field's VISIBLE extent, NOT its house-blocking envelope tail
        vb = fd.get("vis_bbox")
        if vb:
            out.append((vb[0], vb[2], vb[1], vb[3], f"field {fd.get('name')}"))
        else:
            xs = [p[0] for p in fd["outline"]]
            ys = [p[1] for p in fd["outline"]]
            out.append((min(xs), max(xs), min(ys), max(ys), f"field {fd.get('name')}"))
    if M.get("pond"):
        cx, cy, rx, ry = M["pond"]
        out.append((cx - rx, cx + rx, cy - ry, cy + ry, "pond"))
    if M.get("forest"):  # a big EDGE feature: revealed a band deep on the axis it FACES, and not
        fpts = M["forest"]  # frame-setting at all on the axis it RUNS ALONG (see forest_frame_span)
        fxs = forest_reveal_x(fpts, M.get("forest_edge"), Settlement.FOREST_REVEAL_FT / ftpx, W)
        fys = [min(max(p[1], 0), H) for p in fpts]
        x0, x1 = forest_frame_span(fxs, W, [v for b in out for v in (b[0], b[1])])
        y0, y1 = forest_frame_span(fys, H, [v for b in out for v in (b[2], b[3])])
        out.append((x0, x1, y0, y1, "forest"))
    return out
