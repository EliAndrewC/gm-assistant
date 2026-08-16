"""Shared gate helpers (geometry): Manifest, Pt, Poly, Check, load, rect_corners, _struct_rect, _box_hits_poly, ... - bodies verbatim from check_village.py (feature 024 package split; SCC-packed, see split_package.py)."""

import json
import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from settlement import _assert_not_main_tree, sat_overlap

_assert_not_main_tree(__file__)  # standalone gate runs must also happen in a session clone, never in main (CLAUDE.md "Session clones"; settlement's own import-time guard backstops this)

Manifest = dict[str, Any]  # the JSON settlement manifest the generator emits

Pt = Sequence[float]  # an (x, y) point (list from JSON, or a tuple)

Poly = Sequence[Sequence[float]]  # a polyline / polygon

Check = Callable[..., None]  # the check(name, passed, message) sink passed into the check functions


def load(path: str) -> Manifest:
    with open(path) as f:
        result: Manifest = json.load(f)
        return result


def rect_corners(h: dict[str, Any]) -> list[tuple[float, float]]:
    a = math.radians(h["rot"])
    ca, sa = math.cos(a), math.sin(a)
    w, ht = h["w"], h["h"]
    return [(h["x"] + dx * ca - dy * sa, h["y"] + dx * sa + dy * ca) for dx, dy in [(-w / 2, -ht / 2), (w / 2, -ht / 2), (w / 2, ht / 2), (-w / 2, ht / 2)]]


def _struct_rect(s: dict[str, Any]) -> dict[str, Any]:
    """Normalize a solid footprint feature to a rect for the overlap tests. Every solid feature now
    carries w/h(/rot). A LOCATION MARKER (a feature whose true footprint is sub-glyph, so it draws
    at a legibility floor - the kosatsuba; see Settlement.kosatsuba) also carries vw/vh, the box it
    actually occupies on the map: overlap is about DRAWN pixels colliding, so the marker's visual
    box is what the checks must clear, exactly as the wells' clearance uses `vr` over `r`."""
    return {"x": s["x"], "y": s["y"], "w": s.get("vw", s["w"]), "h": s.get("vh", s["h"]), "rot": s.get("rot", 0)}


def _box_hits_poly(box: tuple[float, float, float, float], poly: Poly) -> bool:
    """Whether an axis-aligned box (x0,y0,x1,y1) overlaps a polygon (corner-in, vertex-in, or edge-cross)."""
    x0, y0, x1, y1 = box
    bc = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    n = len(poly)
    return (
        any(point_in_poly(cx, cy, poly) for cx, cy in bc)
        or any(x0 <= vx <= x1 and y0 <= vy <= y1 for vx, vy in poly)
        or any(segments_cross(bc[e], bc[(e + 1) % 4], poly[k], poly[(k + 1) % n]) for e in range(4) for k in range(n))
    )


def sweep_hi(lo: float, hi: float, step: float, cap: int = 500) -> float:
    """Clamp a grid-sweep's upper bound so a MALFORMED coordinate (a stray vertex millions of px
    off the map) cannot blow the sweep up to billions of cells and make the validator appear to
    hang. A real settlement spans at most ~1,000-3,000 px (a few hundred steps at the 8px cell,
    well under `cap`), so this never truncates a valid map - but garbage input is bounded to `cap`
    steps per axis (<= 250k cells, a couple of seconds), so the check FAILS the bad manifest (via
    city_geometry_within_canvas) instead of looping forever. A validator must never hang on bad input."""
    return min(hi, lo + step * cap)


def poly_area(pts: Poly) -> float:
    """Absolute polygon area (shoelace) of a list of (x, y) vertices."""
    n = len(pts)
    s = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def convex_hull(pts: Sequence[Pt]) -> Poly:
    """Convex hull (monotone chain) of a point cloud, as a CCW vertex list. <3 unique points returns them
    as-is (a degenerate hull of zero area)."""
    ps = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(ps) < 3:
        return [(x, y) for x, y in ps]

    def cross(o: Pt, a: Pt, b: Pt) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Pt] = []
    for p in ps:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Pt] = []
    for p in reversed(ps):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def largest_empty_gap(poly: Poly, pts: Sequence[Pt], occupied: list[dict[str, Any]] | None = None, step: float = 30) -> float:
    """The radius of the largest empty pocket inside `poly`: the max over interior grid points of the
    distance to the nearest point in `pts`. A thin firebreak strip stays within a house-reach of homes
    on either side (small gap); a whole empty block has an interior point far from any house (large gap).
    This is the dead-zone signal a per-quarter density AVERAGE cannot see (a half-full quarter averages
    fine). Grid points that fall inside an `occupied` rect (a civic compound - a temple or yamen in a
    mixed quarter is built ground, not empty) are skipped, so a compound does not read as a dwelling
    dead zone. Returns 0.0 for an empty poly bbox; a large sentinel if `pts` is empty."""
    if not pts:
        return float("inf")
    occupied = occupied or []
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    worst = 0.0
    _hx, _hy = sweep_hi(min(xs), max(xs), step), sweep_hi(min(ys), max(ys), step)  # bounded: a malformed vertex cannot hang the sweep
    gx = min(xs)
    while gx <= _hx:
        gy = min(ys)
        while gy <= _hy:
            if point_in_poly(gx, gy, poly) and not any(abs(gx - r["x"]) <= r["w"] / 2 and abs(gy - r["y"]) <= r["h"] / 2 for r in occupied):
                d = min(math.hypot(gx - dx, gy - dy) for dx, dy in pts)
                if d > worst:
                    worst = d
            gy += step
        gx += step
    return worst


# ---- overlap classification registry ---------------------------------------------------------------
# Every footprint feature (a manifest key holding a list of dicts with positional geometry) must be
# classified below. The DEFAULT is "must not overlap anything": a SOLID feature joins `structs`, which
# the no_structure_* checks clear against each other and against the walls / water / roads / fields it
# should not sit on. Overlaps are OPT-IN - a feature that is meant to overlap something (a label, a
# bridge over water, a guard tower on the wall) is named in _OVERLAP_EXEMPT with its reason. The
# `every_feature_classified_for_overlap` check fires when a NEW feature key appears in none of these
# sets, forcing whoever adds it to declare its overlap behavior rather than silently skipping it.
_OVERLAP_STRUCTS = (
    "theater_stage",  # a LIST since 2026-08-10 (dict manifests normalized at gate entry)
    "houses",
    "terraces",
    "precinct_halls",
    "buildings",
    "flophouses",
    "cemeteries",
    "mausoleums",
    "cremation_grounds",
    "ossuaries",
    "ministries",
    "fire_towers",
    "drum_towers",
    "byres",
    "kosatsuba",
    # the justice works (settlements.md "Punishment spot" / "Execution ground" / "Boundary marker")
    "punishment_spots",
    "execution_grounds",
    "boundary_markers",
    # the trade works (GM 2026-07-24, settlements.md "TRADE WORKS")
    "breweries",
    "dye_yards",
    "lumber_yards",
    "oil_presses",
    "pawnshops",
    "bathhouses",
    "kilns",
    "farriers",
    "tanning_yards",
    # the charcoal district's trade works (feature 016). For OVERLAP purposes these are ordinary
    # solid premises like any other; what is special about them is a SEPARATION rule each
    # (charcoal_yard_keeps_fire_gap, refining_forge_stands_off_dwellings), which is a different
    # shape and lives in its own check rather than in this registry.
    "charcoal_yards",
    "refining_forges",
    # martial training (GM 2026-07-25): the state hall and the private dojos - solid compounds like
    # any other civic/private premises, so they overlap nothing
    "martial_halls",
    "dojos",
    # the domain capital's castle (feature 019). Recorded as a LIST precisely so this registry can
    # see it: the first cut recorded a bare dict, which this check enumerates past in silence, and
    # the Imperial road duly ran straight through the largest structure on the map with a green
    # gate. Its towers are outer-wall furniture and are solid in their own right.
    "castles",
    "castle_towers",
    # the capital's wharf granaries (feature 020): per-STORE records precisely so this registry
    # and the extractor see each kura - the legacy town M['granary'] is a bare dict special-cased
    # in solid_structs, which is the record shape feature 019 proved invisible.
    "granaries",
)

# `shrines` duplicates the primary religious halls (shrine_hall records both), so it rides along with
# `religious`; both are halls that structs must AVOID, gated by no_structure_on_religious.
_OVERLAP_TARGETS = ("manors", "religious", "shrines", "gate_structs", "docks")

_OVERLAP_LINEAR = (
    "fields",
    "fallow_patches",
    "flower_fields",
    "streams",
    "channels",
    "town_streets",
    "alleys",
    "lanes",
    "wards",
    "ponds",
    "pastures",
    "forests",
    "commons",
    "dry_plots",
    "marshes",
    "canals",
    "roads",
    "crescent_ponds",
    "towpaths",
    "quays",  # the revetted bank face at a wharf - a LINE feature, classified WAY like the towpath
    "aqueducts",
)  # linear / area features structs avoid (canals = the cargo canal; roads = the multi-road list, same ground the single M['road'] covers; crescent_ponds = the fengshui 半月塘 focal pond, reserved as a placement keep-out so the cluster packs around it; towpaths = the riverbank haulage path and aqueducts = the open supply cut, both feature 020 - ground a structure must keep off)

_OVERLAP_EXEMPT = {
    "drawn_channels": "z-order record of the drawn field-channel strokes (post-clip geometry + stroke widths w0/w1 + bedz), not a placement feature: the strokes duplicate the field_ditches/channels ground the structs already avoid, and their mouths deliberately touch the pond/moat/stream they join (pond_fill_covers_channel_mouths and water_channels_join_not_cross read this record - it is the only source that says what was actually stroked, and how wide)",
    "storehouses": "merchant kura drawn as an annex deliberately abutting its shop",
    "borders": "a drawn CLAN/jurisdictional border is a LINE OF LAW, not a physical object - it has no footprint (no w/h), reserves no ground and blocks nothing. Being overlapped is the POINT: a frontier magistracy stands its wall ON the line so the border runs across the parley-room floor (the Mode A ubame-magistracy sheet), and the period PHYSICAL marker - an earthen mound, as at the Nanbu-Date boundary - is deliberately NOT what this draws, precisely because a mound would be a structure everything then had to stay clear of",
    "farm_sheds": "a farmstead's grain-storehouse kura drawn as an annex abutting its own farmhouse's back wall (farm_sheds_attached verifies the attachment)",
    "threshing_yards": "a farmstead's threshing/drying yard drawn as an annex abutting its own farmhouse",
    "gardens": "a farmstead's dooryard kitchen garden drawn as a plot abutting its own farmhouse",
    "groves": "a farmstead's windbreak grove (yashikirin) drawn as a clump abutting the windward side of its own farmhouse",
    "merchant_estates": "a walled court AROUND an inner building that is itself an overlap-checked struct",
    "wells": "a small well-head dropped into the open gaps between dwellings (its nominal footprint may kiss a dense-city building)",
    "wall_towers": "guard towers stand ON the city wall - an intentional overlap - and clear of the interior",
    "bridges": "a bridge spans a stream/moat to carry a road over it (intentional water + road overlap)",
    "kido": "a ward gate sits ON the ward fence at the point a lane passes through it",
    "inspection_stations": "an inspection post sited AT the city gate, part of the gate complex (overlaps the gate furniture)",
    "water_gates": "the shuimen arch stands ON the city wall over its canal - intentional, like the kido on its fence",
    "sluice_gates": "the field-channel intake/outfall board sits ON its channel at a water-to-water handoff (moat/river tap -> comb canal, drain -> culvert) - the control structure IS the junction",
    "jetties": "planked mooring fingers running out over the river water, like bridge decks",
    "log_booms": "a cabled chain of floating logs holding rafted timber against the bank - it FLOATS on the river, so overlapping the water is the whole point, exactly as a jetty deck does",
    "field_ditches": "in-field irrigation ditches (main/laterals/drain) - water lines drawn ON the paddy, validated by water_channels_obtuse_turns + field_ditches_terminate, not solid structures",
    "village_groves": "the COMMUNAL fengshui windbreak (back-village belt / water-mouth cluster / bamboo copses) - vegetation drawn LAST in open ground at the cluster margins; a copse may abut a house, validated by the village_windbreak_* checks",
    "districts": "declarative fabric districts (feature 021), the quarter overlay's sibling - named pack regions validated by capital_districts_declared / capital_rank_gradient, never drawn",
    "precincts": "a sovereign-temple precinct RESERVATION (feature 021) - a region record like a district; its drawn content is precinct_halls, which carry their own classes",
    "quarters": "declarative zoning overlays (feature 006), not solid structures - they intentionally contain buildings and are validated by the city_quarters_* / per-quarter density checks",
    "mills": "a water mill (水磨) focal feature drawn BESIDE its watercourse with the wheel dipping into the drain/stream - an intentional water-adjacency like a bridge/jetty; reserved in open ground (self.placed) so it does not overlap dwellings",
    "field_ponds": "feature 012: a low-pocket pond sunk INTO one paddy plot, the field tiling around it - drawn ON the paddy like field_ditches, validated by paddy_features_match_archetype + field_ponds_sunk_into_one_plot",
    "field_rocks": "feature 012: a bedrock outcrop the terrace risers wrap around, drawn ON the paddy - validated by paddy_features_match_archetype (bedrock archetypes only)",
    "field_graves": "feature 012: a rare in-field grave island (calibrated liberty) the flat paddy tiles around, drawn ON the paddy - validated by paddy_features_match_archetype",
    "clearings": "swept-ground records (the shrine keidai / torii sando collar / grave collar), not drawn features at all - they carry the cover-ordinal bookkeeping for scatter_respects_swept_clearings and deliberately CONTAIN their sacred/funerary feature",
    "stable_yards": "the gate stables' beaten-earth working yard (s._stable_yard) - a feathered ground scatter (hitching rails, trough, dung heaps, litter; no animal glyphs - the maps render no humans or animals) that deliberately SURROUNDS its stables and fills the open pocket; a ground record, not a keep-clear structure (validated by stables_have_yards). `troughs` counts the watering point's troughs and `troughs_at` records the cluster center, which must hug a wellhead (validated by stable_troughs_beside_well); `troughs_box` and `rails` record the furniture's DRAWN extents, which must not intersect each other or any wellhead (wells_troughs_rails_clear_of_each_other)",
    "dikes": "the reclaimed-polder PERIMETER dike earthwork band (s.perimeter_dike) - a walked, lived-on planted bank the village lines and the feeder/drain channels + footbridges cross by design; a broad ground feature, not a keep-clear structure (validated by polder_dike_is_earthwork)",
}

# ---- label classification registry (GM 2026-07-26) --------------------------------------------
# The sibling of _OVERLAP_STRUCTS, for the OTHER thing a new feature has to be protected from: a
# CAPTION landing on it. labels_clear_of_other_buildings used to build its victim list from ~22
# hand-written manifest keys, which is the same bug the keep-clear contract retired - and it had
# already fallen behind twice over. When the martial hall went in, `martial_halls` and `dojos` had
# to be remembered into it; a day later the execution-ground feature landed and `punishment_spots`,
# `execution_grounds` and `boundary_markers` were not in it either, so a foreign caption could sit
# squarely on an execution ground with the gate green.
#
# Now every solid feature is classified here exactly once. The GROUP name is what a caption must
# NAME to be allowed to cover the feature - and because the group name is the caption word, that
# permission is derived rather than hand-listed too (see _label_allows).
_LABEL_GROUP = {
    "quays": "quay",
    "theater_stage": "theater",
    "granaries": "granary",
    "terraces": "terrace",
    "flophouses": "flophouse",
    "log_booms": "log boom",
    "religious": "temple",
    "precinct_halls": "temple",
    "ministries": "ministry",
    "governor_mansion": "governor",
    "gate_structs": "gate",
    "merchant_estates": "merchant",
    "manors": "estate",
    "cemeteries": "cemetery",
    "mausoleums": "mausoleum",
    "cremation_grounds": "cremation",
    "ossuaries": "ossuary",
    "breweries": "brewery",
    "dye_yards": "dye works",
    "lumber_yards": "lumber yard",
    "oil_presses": "oil press",
    "pawnshops": "pawnshop",
    "bathhouses": "bathhouse",
    "kilns": "kiln",
    "farriers": "farrier",
    "tanning_yards": "tanning yard",
    "charcoal_yards": "charcoal yard",
    "refining_forges": "refining forge",
    "drum_towers": "drum tower",
    "martial_halls": "martial hall",
    "castles": "castle",
    "castle_towers": "castle",
    "dojos": "dojo",
    "fire_towers": "fire tower",
    "kosatsuba": "notice board",
    "punishment_spots": "punishment ground",
    "execution_grounds": "execution ground",
    "boundary_markers": "boundary marker",
    "houses": "farmhouse",
    # a WELLHEAD is a drawn glyph a caption can bury, but it is _OVERLAP_EXEMPT (a well may kiss a
    # dense-city building), so it fell outside the classification ratchet - which iterates the
    # overlap registry - and a caption on a wellhead was invisible. Found by settlement-review 2026-07-26.
    "wells": "well",
    # THE SAME HOLE, ONE CLASS OVER (settlement-review 2026-07-27). The ratchet at
    # `labels_cover_every_feature` iterates the overlap registry, and `matrix_extents` SKIPS the
    # permissive classes outright - so every key registered "FIXTURE" is invisible to it and can go
    # unclassified for labels for ever. On Minami that let two captions ("punishment ground" and a
    # "dojo") be drawn straight through a ward kido's guard post, each biting a notch out of its
    # outline so a clean square rendered as two disconnected corners, with the gate fully green.
    # A kido and a dock are both solid drawn glyphs a caption can bury, so both are victims here.
    # (A concurrent session has since moved `kido` off the POINT FIXTURE row - it always had a
    # footprint - which fixes its overlap handling but not this: label classification is a separate
    # registry, and an unclassified key stays invisible to captions whatever its overlap class.)
    "kido": "ward gate",
    "docks": "dock",
    # a TORII ARCH, likewise (GM 2026-07-27: an arch must "never be covered by the 'temple of X'
    # label"). Its group word appears in no caption any map draws, so NOTHING may cover an arch -
    # correct, because a sando's whole legibility is the ROW it makes, and a caption laid across it
    # breaks the row into unrelated marks. The commonest offender was the hall's OWN caption, which
    # wants the same ground the approach does. See the torii branch in the victim builder: an arch is
    # recorded as a bare [x, y, z] triple, so the registry loop cannot pick it up on its own.
    "torii": "torii",
}

# STILL UNCLASSIFIED, and known to be (2026-07-27): the other six FIXTURE keys - `bridges`,
# `water_gates`, `sluice_gates`, `inspection_stations`, `jetties`, `wall_towers`. They are drawn
# glyphs a caption could bury exactly like the two above, and nothing will tell us when one does,
# because the ratchet cannot reach the permissive classes. Left open deliberately rather than
# half-closed: adding them is one line each, but each may fire on a finished map in the pool, and
# that is a fix to make with the regen budget to see it through - not a line to add blind.
# `buildings` is the one key whose group is not fixed: each record carries its own `kind`, and _grp
# folds those kinds into groups (samurai_large -> samurai, and so on).
_LABEL_BY_KIND = ("buildings",)

_LABEL_EXEMPT = {
    "districts": "a declared district is a REGION overlay like a quarter - it draws nothing, so there is nothing under it for a caption to bury",
    "precincts": "a reservation region, never drawn - the halls inside it are the drawn features",
    "borders": "a jurisdictional line has no footprint to protect - there is nothing under it to be buried by a caption, and its own caption is drawn in the top layer so no ground feature can paint over it",
    "byres": "a draft-ox byre is an ANNEX abutting its own farmhouse (draft_byres places it against the wall), so it shares the house's ground and any caption cleared for the house is cleared for it",
}

_LABEL_CLASSIFIED = set(_LABEL_GROUP) | set(_LABEL_BY_KIND) | set(_LABEL_EXEMPT)

_LABEL_GROUPS = frozenset(_LABEL_GROUP.values())

# ============================ THE OVERLAP MATRIX (feature 017) ============================
# WHY THIS EXISTS (GM 2026-07-26). `_OVERLAP_STRUCTS` models **structure x hazard** - a building
# against a road, wall, stream, torii. It has no notion of **ground x ground**, which is where
# `dry_plots x water` lives, so a dry crop field could sit in a stream with the gate fully green
# while a manor on a road got its own bespoke check. The GM's words: "it's like playing whack-a-mole
# where every time we make a new map, I see a few more things which have never happened to overlap
# before but now they do... I'd like to make sure our automated checks aren't just individually
# listing 'X cannot overlap with Y, N cannot overlap with M'."
#
# So: every geometric key gets ONE CLASS and a class-by-class policy decides every pair at once.
# FORBIDDEN BY DEFAULT; every permission carries its reason. Adding a feature is one line here.
OVERLAP_CLASS: dict[str, str] = {
    # --- TESTED CLASSES -------------------------------------------------------------------------
    # SOLID - an exclusive built footprint
    **{
        k: "SOLID"
        for k in (
            "houses",
            "terraces",
            "precinct_halls",
            "buildings",
            "flophouses",
            "manors",
            "religious",
            "shrines",
            "ministries",
            "merchant_estates",
            "cemeteries",
            "cremation_grounds",
            "ossuaries",
            "mausoleums",
            "fire_towers",
            "drum_towers",
            "martial_halls",
            "dojos",
            # the castle and its outer-wall towers (feature 019). SOLID like any other walled
            # compound: nothing may be built on the works, and no way may run through them.
            "castles",
            "castle_towers",
            "kosatsuba",
            "punishment_spots",
            "execution_grounds",
            "boundary_markers",
            "theater_stage",
            "wells",
            "breweries",
            "dye_yards",
            "lumber_yards",
            "oil_presses",
            "pawnshops",
            "bathhouses",
            "kilns",
            "farriers",
            "tanning_yards",
            "charcoal_yards",
            "refining_forges",
            # the capital's wharf granaries (feature 020) - kura rows, one record per store
            "granaries",
        )
    },
    # A ward gate's GUARD BOX is a small building on the verge beside the gateway, not part of the
    # opening: it is SOLID and rides none of the gate's fence/roadbed mounts (see matrix_extents,
    # which splits it out of `kido`). Not a manifest key - it is extracted from the gate's own
    # `parts` - so nothing reads M['kido_guard_box'] and the classification ratchet never sees it.
    "kido_guard_box": "SOLID",
    # The rampart and the torii arches are SOLID: things must keep off them. All of these were
    # UNCLASSIFIED until 2026-07-26 because the ratchet inspected only keys whose records are lists
    # of DICTS - a wall is a bare list of points, a torii a bare [x, y, z] triple - and a ratchet
    # that enumerates one record shape has exactly the blindness this feature exists to abolish.
    # `lane` (singular) is the same plural/singular trap that had already hidden `marshes` and `roads`.
    **{k: "SOLID" for k in ("wall", "torii")},
    # GROUND - cultivated / engineered ground worked AS A SURFACE: anything standing in it ruins it
    **{k: "GROUND" for k in ("dry_plots", "flower_fields", "fallow_patches")},
    # PADDY is GROUND in principle but RECONSTRUCTED in practice: a plot's polygon is not stored, so
    # its extent is rebuilt from recorded spans as an oriented bounding box (see matrix_extents).
    # That is good enough to reason with and NOT good enough to accuse another feature with, so
    # paddy is permissive HERE and the precise paddy rules stay authoritative -
    # harvest_yards_clear_of_paddies, structures_clear_of_dry_plots, streams_avoid_fields,
    # tanning_yard_clear_of_fields and fields_clear_of_road all test real geometry.
    "fields": "PADDY_RECONSTRUCTED",
    # `aqueducts` is WATER (feature 020): the open supply cut is a seam on the ground exactly like
    # a channel, and the shared crossing source (bridge_crossed_waters) already demands a deck of
    # any way over it. `towpaths` is a WAY: a beaten path things keep off, however unlike a road
    # it is drawn.
    **{k: "WATER" for k in ("streams", "channels", "field_ditches", "canals", "pond", "moat", "aqueducts")},
    **{k: "WAY" for k in ("road", "roads", "town_streets", "alleys", "lanes", "towpaths", "quays")},
    # ANNEX - belongs to a named parent and abuts IT (and nothing else)
    **{k: "ANNEX" for k in ("gardens", "threshing_yards", "farm_sheds", "storehouses", "byres")},
    # --- PERMISSIVE CLASSES (never tested; each row below records WHY) ---------------------------
    **{k: "COVER" for k in ("commons", "pastures", "marsh", "marshes")},
    "quarters": "OVERLAY",
    "districts": "OVERLAY",
    "precincts": "OVERLAY",
    # A WARD IS NOT A QUARTER. A quarter is a zoning word; a ward is a walled enclosure whose FENCE
    # is a physical barrier everything except its own kido must stand clear of. Classed OVERLAY it was
    # never extracted, which is why a guard station, a notice board and an oil press all came to rest
    # on Minami's ward fence with a green gate. Extracted as the STROKE of its boundary (the fence
    # line), not as its interior - the interior does contain features, by definition.
    "wards": "BARRIER",
    # a caravan yard is beaten WORKING GROUND, like grazing: its rails, troughs and litter stand on
    # it by design, and that is what the yard IS
    **{k: "COVER" for k in ("stable_yards",)},
    # FIXTURE - a control structure deliberately built ON another feature, where the overlap is the
    # whole point. Reasons, carried over from the older _OVERLAP_EXEMPT entries:
    #   bridges             span water to carry a way over it
    #   kido                a ward gate sits ON the ward fence where a lane passes through
    #   water_gates         the shuimen arch stands ON the city wall over its canal
    #   sluice_gates        the intake/outfall board sits ON its channel - the control structure IS the junction
    #   inspection_stations an inspection post is part of the gate complex it stands in
    #   jetties             planked mooring fingers run out OVER the river
    #   wall_towers         guard towers stand ON the wall
    #   docks               a landing stands at the waterline by definition
    #   gate_structs        the guard station and tower ARE the gate complex, standing on wall and road
    #   log_booms           a cabled log pen floats ON the river it holds timber in
    **{k: "FIXTURE" for k in ("bridges", "kido", "water_gates", "sluice_gates", "inspection_stations", "jetties", "wall_towers", "docks", "gate_structs", "log_booms")},
    # RECORD - bookkeeping geometry that duplicates ground already classified elsewhere, or an
    # in-field flourish drawn ON the paddy by design (feature 012). Never tested.
    #   drawn_channels  a z-order record of the drawn field-channel strokes; the ground it covers is
    #                   the field_ditches/channels the matrix already reasons about
    #   field_ponds / field_rocks / field_graves / crescent_ponds
    #                   a pocket pond, bedrock outcrop, grave island or crescent pond sunk INTO one
    #                   paddy plot, the field tiling around it - the overlap is the feature
    #   borders         a drawn jurisdictional line is a LINE OF LAW, not a physical object
    **{k: "RECORD" for k in ("drawn_channels", "field_ponds", "field_rocks", "field_graves", "crescent_ponds", "borders", "forest_edge", "lane")},
    # the intramural patrol strip has its OWN precise rule (ring_road_kept_clear), which knows the
    # real bed width and which frontages may legitimately stand against it; the matrix defers
    **{k: "RING_ROAD" for k in ("ring_road",)},
    **{k: "VEGETATION" for k in ("village_groves", "groves", "forest", "tree_stands", "tree_crowns")},
}

# A permissive class may be overlapped by anything, and is never extracted. The reason matters as
# much as the fact - these are the rows that stop the matrix crying wolf.
_MATRIX_PERMISSIVE = {
    # the GM's own example, and the distinction the whole design turns on
    "COVER": "permissive ground cover - grazing, pasture and scrub describe what the ground IS, not an object occupying it, so a well, a house or a field built on it is the normal case and the cover simply stops there (contrast GROUND, which is worked as a surface and is ruined by anything standing in it)",
    "OVERLAY": "a declarative zoning overlay (a QUARTER) CONTAINS features by definition - it describes what a district is for, not an object standing in it",
    # Deliberately out of scope rather than unclassified: canopy-vs-structure is already governed
    # precisely by the keep-clear/canopy contract (Settlement._CANOPY_STRUCT_KEYS + the ratchet added
    # in feature 016), which tests recorded CROWNS and knows which grounds a bough may legitimately
    # overhang. Re-deciding that here would duplicate proven machinery and risk two verdicts on one
    # question. Vegetation records are also envelopes (a `forest` is a stand outline, a grove a belt
    # outline) whose ink lives in `tree_crowns` - see the drawn-extent rule in matrix_extents.
    "VEGETATION": "canopy overlap is governed by the canopy keep-out contract, which tests recorded crowns; the matrix does not re-decide it",
    "RING_ROAD": "the intramural patrol strip is governed precisely by ring_road_kept_clear, which knows its real bed width; the matrix does not re-decide it",
    "RECORD": "bookkeeping geometry or an in-field flourish drawn ON its own paddy by design - not ground the matrix reasons about",
    "PADDY_RECONSTRUCTED": "a paddy plot's extent is reconstructed from recorded spans rather than stored, so it is an approximation - the precise paddy checks (harvest_yards_clear_of_paddies, structures_clear_of_dry_plots, streams_avoid_fields, tanning_yard_clear_of_fields) test real geometry and remain authoritative",
}

# WHAT EACH FIXTURE IS MOUNTED ON (GM 2026-07-26). FIXTURE used to be a PERMISSIVE class, which had
# two compounding effects: `matrix_extents` skips permissive classes entirely, so all ten fixture keys
# were never extracted and therefore invisible to every matrix check in BOTH directions; and
# `matrix_policy` returned a permission whenever either side was a fixture, so anything could sit on
# one. In Minami that hid 56 solid built objects - 4 bridges, 4 ward gates, 24 wall towers, 10 gate
# structures, 6 sluice gates, 3 jetties, 2 inspection stations, 1 dock - and it is how the map came to
# carry TWO overlapping bridges over the same crossing, a guard station on the ward fence and an oil
# press across a ward gate, all with a green gate.
#
# "The overlap is the whole point" is true only OF THE THING THE FIXTURE IS BUILT ON. A bridge is
# built on water and on the way it carries; it is not built on another bridge, and a ward gate is not
# built on an oil press. So each fixture names its mounts - CLASSES or specific KEYS - and may overlap
# nothing else, including another fixture of its own kind. Entries are deliberately MINIMAL: a
# genuine adjacency the sweep surfaces should be added here with its reason, not pre-permitted.
_FIXTURE_MOUNTS: dict[str, frozenset[str]] = {
    "bridges": frozenset(
        {"WATER", "WAY", "wall", "water_gates"}
    ),  # spans the water to carry the way over it - and a bridge on a moated approach lands ON the rampart at its water gate, which is the crossing the wall is pierced for. `water_gates` was added 2026-07-27 with Nagahara's ring-road canal deck: the ring runs a fixed inset inside the rampart, so where a cargo canal enters through a shuimen the ring necessarily crosses it a few paces INSIDE the arch (Nagahara 39 real ft), and the gate structure's own apron and the deck share that ground - the Suzhou pattern, where the wall road crosses each canal on a bridge at the water gate. Shortening the deck does not separate them (checked: even a bare-abutment span still lands inside the gate footprint), which is what says this is an adjacency rather than a drawing error
    "docks": frozenset({"WATER", "WAY"}),  # a landing stands at the waterline, reached from the quay
    "jetties": frozenset({"WATER"}),  # planked mooring fingers run out OVER the river
    "log_booms": frozenset({"WATER"}),  # a cabled log pen floats ON the river it holds timber in
    "sluice_gates": frozenset({"WATER"}),  # the intake/outfall board IS the water-to-water junction
    "water_gates": frozenset(
        {"WATER", "wall"}
    ),  # the shuimen arch stands over its canal AND on the city wall - the wall IS a matrix feature now (classified SOLID for feature 017), so the mount it always had must be stated
    "kido": frozenset({"WAY", "wards"}),  # a ward gate sits ON the ward fence where a lane passes through
    "gate_structs": frozenset({"WAY", "wall"}),  # the guard station and tower ARE the city gate complex, standing on the wall and the road - both mounts now stated, since `wall` is classified
    "inspection_stations": frozenset({"WAY", "gate_structs"}),  # an inspection post is part of the gate complex it stands in
    # A tower stands ON the rampart. That mount is now EXPLICIT: `wall` was unclassified when these
    # entries were written ("which the matrix does not model"), and classifying it SOLID turned every
    # tower, gate complex, water gate and moat bridge in the pool into a violation of a rule they had
    # always satisfied. The lesson is that a mount list written against an unclassified neighbor is
    # silently incomplete - it records only the mounts the matrix could see at the time. The moat and its irrigation taps run at the
    # rampart's foot by construction (Tango's moat-fed channel passes under the tower line), and the
    # tower is elevated above them, so water is a legitimate mount; anything SOLID against a tower is
    # still a defect.
    "wall_towers": frozenset({"WATER", "wall"}),
}

_MATRIX_SAME_CLASS_OK = {
    "WATER": "watercourses meet at confluences",
    "WAY": "ways meet at junctions",
    # two annexes of the SAME parent (a farmhouse's yard, garden, shed and grove arms) abut one
    # another as a matter of course; the parent-scope test below is what keeps them honest, since an
    # annex touching a DIFFERENT household's annex is still a defect
    "ANNEX": None,
}

# same-KEY permissions: records of one kind that legitimately touch each other
_MATRIX_SAME_KEY_OK = {
    "wall": "consecutive rampart segments meet at every corner - the wall is one continuous work, drawn as a chain of strokes",
    "torii": "the arches of one approach avenue are a series along the sando, spaced by design",
    "wards": "consecutive segments of ONE fence share their corner - the extractor strokes a polyline into one quad per segment, so neighbors always meet. Two DIFFERENT wards' fences crossing is a real defect and is caught by city_ward_fence_clear_of_structures' own ward-x-ward test",
    "dry_plots": "adjacent hatake plots in one quilt abut and share their headlands, exactly as paddy plots share bunds",
    "fields": "paddy plots in one fan abut and share their bunds - and a plot's extent is reconstructed from recorded spans, not a stored polygon, so the reconstruction slightly overstates an irregular plot",
}

_MATRIX_ALLOWED_PAIRS: dict[frozenset[str], str] = {
    frozenset({"WATER", "WAY"}): "a way crosses water at a bridge; unbridged crossings are gated separately by roads_bridge_watercourses",
    frozenset(
        {"WAY", "BARRIER"}
    ): "a way PIERCES a ward fence - that is what a kido is for. The rule that matters is not whether a street crosses the fence but whether every crossing has a gate, and that is held by city_samurai_ward_sealed + city_kido_on_ward_fence, which fire on an ungated crossing",
}

# per-KEY-PAIR permissions for genuine one-offs the class policy is too coarse to express
_MATRIX_ALLOWED_KEYS: dict[frozenset[str], str] = {
    frozenset(
        {"quays", "jetties"}
    ): "a jetty SPRINGS FROM the quay face - the faced bank is the working surface the stage projects out of, so they meet by construction (research/cities/river-cities.md: the pier exists for REACH where the bank shelves too gently, and it starts at the revetment)",
    **{
        frozenset(
            {"wall", w}
        ): "a way or a watercourse passes THROUGH the rampart at its gate or water gate - that opening is the point of a gate, and no_structure_on_wall still governs anything BUILT on the rampart"
        for w in ("road", "roads", "town_streets", "alleys", "lanes", "canals", "channels", "streams", "moat")
    },
    frozenset(
        {"castles", "castle_towers"}
    ): "a yagura STANDS ON the rampart it defends - a corner tower projecting from the enceinte IS the form of the thing, exactly as a mural tower sits on the city wall. The castle's works may still not be built on by anything else: both keys stay SOLID against every other feature, and the ways are held off by the same matrix that caught the Imperial road running through this castle in the first place",
    **{frozenset({"torii", w}): "a torii STANDS OVER its approach - an arch spanning the sando is the whole form of the thing" for w in ("road", "roads", "town_streets", "alleys", "lanes")},
    frozenset({"religious", "shrines"}): "shrine_hall records one hall under BOTH keys - these are the same object, not two",
    frozenset(
        {"wards", "wall"}
    ): "a ward fence ENDS at the rampart - city_ward_fence_meets_wall demands exactly that, so commoners cannot walk around it. The same adjacency was already stated for {wards, wall_towers}; it needed stating for the wall ITSELF once `wall` was classified SOLID. (The route is held by city_ward_fence_meets_wall + city_samurai_ward_sealed, so this cannot excuse a fence running along INSIDE the rampart.)",
    frozenset(
        {"wards", "wall_towers"}
    ): "a ward fence ENDS at the rampart - that is exactly what city_ward_fence_meets_wall demands, so commoners cannot walk around it - and a wall tower stands ON the rampart. A fence end butting into a tower's footprint IS the fence reaching solid wall. (Its route is held by city_ward_fence_meets_wall and city_samurai_ward_sealed, so this cannot excuse a fence wandering through a tower mid-span.)",
    frozenset(
        {"gate_structs", "wall_towers"}
    ): "a city gate's own TOWER is recorded under both keys - identical x/y/w/h/rot, the same object rather than two (verified on Minami: tower(1323,902) w17h10 appears in each list). The same duplicate-record case as religious x shrines",
    frozenset(
        {"castles", "bridges"}
    ): "a deck carries the approach avenue over the castle's OWN moat - the moat ring is part of the castles record, so the deck that the shared crossing source (feature 020) DEMANDS there necessarily overlaps it. The deck lies on the water, not the works; the ways themselves are still held off the castle by the matrix that caught the Imperial road running through it",
    frozenset(
        {"castle_towers", "bridges"}
    ): "the ote-mon's moat deck lands at the gate tower's foot - a castle bridge ENDS at its gate, so the deck's landing margin may kiss the tower footprint, exactly as a city gate's bridge lands in its gate complex",
    frozenset(
        {"channels", "dry_plots"}
    ): "a supply canal hugs the fan's HIGH DRY MARGIN by design (the comb doctrine), and the dry hem IS that margin - a plot may be crossed by the irrigation that serves it. A NATURAL watercourse is a different matter and stays forbidden: dry_plots x streams is the defect this whole feature was opened for",
    frozenset(
        {"kosatsuba", "lanes"}
    ): "the notice board hugs the roadside BY DESIGN - place_kosatsuba deliberately bypasses the lane corridor's no-build clearance, which is a house setback, because a board that everyone passes is the whole institution (settlements/urban-features.md, 'Notice board')",
    frozenset({"buildings", "merchant_estates"}): "a merchant estate is a walled COURT drawn around an inner building that is itself a checked struct",
    frozenset(
        {"wall", "flower_fields"}
    ): "an ornamental bed laid FLUSH against the inside of the town wall - s.flower_field's `flat_west` flag exists for exactly that (it straightens the edge so it can run against the rampart), so the bed's straight face meeting the wall's drawn stroke is the feature working, not a defect. Anything BUILT on the rampart is still governed by no_structure_on_wall; this permits planting, which occupies no rampart",
}

# A record naming its PARENT may overlap that parent and nothing else - strictly stronger than the
# blanket per-pair exemptions this replaces, because an annex on somebody ELSE's building stays a defect.
# manifest lists that carry coordinates but are NOT drawn ground the matrix reasons about
# Manifest lists carrying coordinates that are NOT drawn ground. `gates` is a list of GAP POSITIONS
# in the wall (the furniture in the gap is `gate_structs`); `wall_tower_keepclears` is a reservation,
# not ink; `forest_edge` is an envelope whose ink is `tree_crowns` and is classified RECORD above.
_MX_NOT_GEOMETRY = frozenset({"labels", "tree_crowns", "wet_plots", "bund_junctions", "footbridges", "knobs", "clearings", "gates", "wall_tower_keepclears"})

_MATRIX_PARENT_FIELD = {
    "gardens": "of",
    "threshing_yards": "of",
    "farm_sheds": "of",
    "byres": "of",
    "storehouses": "of",
    "field_ditches": "field",  # a field's own irrigation, drawn ON it by design
}


def matrix_policy(ka: str, kb: str) -> str | None:
    """The reason this pair may overlap, or None if FORBIDDEN. Unclassified keys abstain here and
    are reported by the ratchet check instead. ANNEX x ANNEX resolves to None here on purpose: the
    permission is conditional on a SHARED PARENT, which only the caller can test."""
    ca, cb = OVERLAP_CLASS.get(ka), OVERLAP_CLASS.get(kb)
    if ca is None or cb is None:
        return "unclassified"
    # A FIXTURE may overlap ONLY what it declares itself mounted on (_FIXTURE_MOUNTS), by class or by
    # key - never anything else, and never another fixture unless that key is named. This replaces a
    # blanket permissive class that made ten keys invisible; see that registry's comment.
    pk_first = _MATRIX_ALLOWED_KEYS.get(frozenset({ka, kb}))
    if pk_first:
        return pk_first
    if "FIXTURE" in (ca, cb):
        for fk, ok, oc in ((ka, kb, cb), (kb, ka, ca)):
            if OVERLAP_CLASS.get(fk) != "FIXTURE":
                continue
            mounts = _FIXTURE_MOUNTS.get(fk, frozenset())
            if ok in mounts or oc in mounts:
                return f"{fk} is mounted on {ok} by design"
        return None
    for cls, why in _MATRIX_PERMISSIVE.items():
        if cls in (ca, cb):
            return why
    if ka == kb and ka in _MATRIX_SAME_KEY_OK:
        return _MATRIX_SAME_KEY_OK[ka]
    if ca == cb:
        return _MATRIX_SAME_CLASS_OK.get(ca)
    return _MATRIX_ALLOWED_PAIRS.get(frozenset({ca, cb}))


def _mx_same(a: Any, b: Any) -> bool:
    """Does a parent reference point at this record? Tolerant, because a parent is stored as a
    rounded coordinate pair and the child's own id is rounded independently."""
    if a is None or b is None:
        return False
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == 2 and len(b) == 2:
        return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1])) <= 1.5
    return bool(a == b)


# THE OUTSTANDING LIST (2026-07-26). Real defects the matrix found on its first pool-wide run,
# itemized BY MAP AND COORDINATE so the gate can be green while they are worked down. This is
# deliberately NOT a blanket grandfather list: every class PAIR is classified (that was the point of
# the feature), these are individual map defects, and because each entry names a position a NEW
# defect of the same kind is still caught. Every line here is work owed, not a permission.
_MATRIX_OUTSTANDING: dict[str, dict[tuple[str, str], int]] = {
    # Keyed by (map, PAIR) with a COUNT - not by coordinate, which proved brittle to regeneration.
    # Every line is WORK OWED, not a permission.
    #
    # 2026-07-26 final: the matrix found 11 defects across 6 maps on its first pool run, and ALL
    # ELEVEN are now fixed. What is left belongs to another session.
    #
    # (Minami's five were recorded here while it was another session's work in progress; all five are
    # fixed and the entry is gone. A line left here after its defect is fixed does not just rot - it
    # TOLERATES that many real defects on that map for ever after, which is why the guard below now
    # fails on one.)
}


def _mx_rect(o: Mapping[str, Any]) -> list[tuple[float, float]]:
    """A record's DRAWN box: `vw`/`vh` where a marker draws above its true size, else w/h."""
    hw = float(o.get("vw", o.get("w", 0))) / 2
    hh = float(o.get("vh", o.get("h", 0))) / 2
    th = math.radians(float(o.get("rot") or 0.0))
    c, s_ = math.cos(th), math.sin(th)
    return [(o["x"] + dx * c - dy * s_, o["y"] + dx * s_ + dy * c) for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def _mx_stroke(pts: Sequence[Any], hw: float) -> list[list[tuple[float, float]]]:
    """One quad per segment of a linear feature at its TRUE half-width - never the ink width, since a
    hairline stroke floor draws a 1 ft ditch 4 px wide and that slop must not manufacture a defect."""
    quads: list[list[tuple[float, float]]] = []
    for i in range(len(pts) - 1):
        ax, ay = float(pts[i][0]), float(pts[i][1])
        bx, by = float(pts[i + 1][0]), float(pts[i + 1][1])
        ln = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / ln * hw, (bx - ax) / ln * hw
        quads.append([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    return quads


# a fixture's DRAWN box, in its own record's vocabulary (see matrix_extents)
_MX_FIXTURE_BOX: dict[str, Any] = {
    "bridges": lambda o: (float(o["span"]), float(o["w"])),  # the deck: span along the way, deck width across
    "jetties": lambda o: (float(o["len"]), 6.4),  # the planked finger, at the width the glyph draws
    "sluice_gates": lambda o: (11.0, 11.0),  # the board and its cheeks - a small square control structure
}

_MX_LINE_W = {"streams": 9.0, "channels": 2.5, "field_ditches": 1.5, "canals": 14.0, "town_streets": 20.0, "alleys": 6.0, "lanes": 6.0, "roads": 26.0, "towpaths": 2.4, "aqueducts": 4.0, "quays": 3.4}

_OVERLAP_SINGLETONS = ("governor_mansion",)  # solid footprints the manifest stores as ONE dict, not a list

_OVERLAP_CLASSIFIED = set(_OVERLAP_STRUCTS) | set(_OVERLAP_TARGETS) | set(_OVERLAP_LINEAR) | set(_OVERLAP_EXEMPT)


def solid_structs(M: Mapping[str, Any], *extra: str, exclude: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """EVERY solid footprint on the map, read from the _OVERLAP_STRUCTS registry.

    WHY THIS EXISTS (GM 2026-07-25). The `no_structure_on_*` battery has always been registry-driven:
    it builds its rects from _OVERLAP_STRUCTS, so classifying a new feature there - which
    `every_feature_classified_for_overlap` already FORCES - wires it into all thirteen hazards at
    once (wall, moat, road, street, stream, channel, canal, pond, manor, religious hall, gate
    furniture, torii, and every other structure). But a handful of keep-clear checks predate that
    battery and hand-listed their own keys instead, so each new feature had to be remembered into
    each of them - and a forgotten one looks exactly like a passing check.

    That is precisely how the martial hall came to sit on Tango's ring road with a green gate: the
    hall was correctly classified in _OVERLAP_STRUCTS and correctly cleared of all thirteen battery
    hazards, but `ring_road_kept_clear` was reading its own list of eight keys that nobody had
    updated. The fix is not to remember harder - it is for every keep-clear check to read the SAME
    registry, which is what this helper is for, and for `test_every_solid_struct_is_gated_off_every_hazard`
    to prove that each registered key really does trip each hazard's check.

    `extra` names _OVERLAP_TARGETS keys a particular hazard must ALSO keep clear of - "religious"
    for the ring road (a temple may not stand on the patrol lane), which is not in _OVERLAP_STRUCTS
    because halls are what structs avoid rather than structs themselves. `exclude` drops keys a
    particular rule deliberately does not govern; use it only with a stated reason at the call site,
    since a silent omission is the exact bug this helper exists to prevent. Records without a drawn
    footprint are skipped, so a caller can pass a key whose dicts are positional-only."""
    out = [s for k in _OVERLAP_STRUCTS + extra if k not in exclude for s in (M.get(k) or [])]
    out += [M[k] for k in _OVERLAP_SINGLETONS if k not in exclude and M.get(k)]
    if M.get("granary") and "granary" not in exclude:
        out += M["granary"]["stores"]
    return [s for s in out if isinstance(s, dict) and "x" in s and "w" in s]


def seg_closest(px: float, py: float, a: Pt, b: Pt) -> tuple[float, float]:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px: float, py: float, a: Pt, b: Pt) -> float:
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


def pt_to_rect(px: float, py: float, rect: dict[str, Any]) -> float:
    """Shortest distance from a point to a (possibly rotated) rectangle footprint; 0 if the point is inside.
    Un-rotates the point into the rect's local frame, clamps to the half-extents, and measures the overhang."""
    a = math.radians(rect.get("rot", 0))
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = px - rect["x"], py - rect["y"]
    lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca  # local coords (rect axis-aligned here)
    ox = max(abs(lx) - rect["w"] / 2, 0.0)
    oy = max(abs(ly) - rect["h"] / 2, 0.0)
    return math.hypot(ox, oy)


def seg_to_rect_dist(a: Pt, b: Pt, rect: dict[str, Any]) -> float:
    """Shortest distance between segment a-b and a (possibly rotated) rectangle; 0 if they touch/cross. Needed
    where a thin corridor can thread THROUGH a wide footprint BETWEEN its corners - corner-sampling misses that.
    Standard convex result: 0 on intersection, else min(endpoint-to-rect, rect-corner-to-segment)."""
    corners = rect_corners(rect)
    for i in range(4):
        if segments_cross(a, b, corners[i], corners[(i + 1) % 4]):
            return 0.0
    if pt_to_rect(a[0], a[1], rect) == 0 or pt_to_rect(b[0], b[1], rect) == 0:
        return 0.0
    return min(min(pt_to_rect(a[0], a[1], rect), pt_to_rect(b[0], b[1], rect)), min(seg_dist(cx, cy, a, b) for cx, cy in corners))


# the 2 patron fortunes of each Great Clan - a town defaults to one monastery for each
# The recognized justifications for a city carrying MORE than two major temples
# (settlements/religion-and-death.md). A fixed vocabulary rather than free text: the doctrine
# enumerates the exceptions, so an unrecognized reason must FAIL rather than pass by virtue of
# being non-empty - otherwise the declaration stops meaning anything and becomes a rubber stamp.
#   large         - an especially large city
#   pious         - a pilgrimage destination (the monzen-machi inversion)
#   changed_hands - kept the old ruler's temple after passing between clans (Tango)
#   fox_structure - the Fox seven-temple structure: many modest precincts, each an economic house
#                   holding forest usufruct, rather than two great complexes (Minami; l7r.md
#                   "Fox Temples", research/religion-and-death.md)
TEMPLE_EXCEPTIONS = {"large", "pious", "changed_hands", "fox_structure"}

CLAN_FORTUNES = {
    "crab": {"Bishamon", "Ebisu"},
    "crane": {"Benten", "Daikoku"},
    "dragon": {"Hotei", "Ebisu"},
    "lion": {"Bishamon", "Daikoku"},
    "phoenix": {"Fukurokujin", "Hotei"},
    "scorpion": {"Benten", "Jurojin"},
    "unicorn": {"Fukurokujin", "Jurojin"},
}


def unit_dir(spec: Any) -> tuple[float, float] | None:
    """A cardinal name or [dx,dy] vector -> a unit vector in map coords (+y=south). None if bad."""
    DIRS = {
        "north": (0, -1),
        "south": (0, 1),
        "east": (1, 0),
        "west": (-1, 0),
        "northeast": (0.7071, -0.7071),
        "northwest": (-0.7071, -0.7071),
        "southeast": (0.7071, 0.7071),
        "southwest": (-0.7071, 0.7071),
    }
    if spec is None:
        return None
    if isinstance(spec, str):
        return DIRS.get(spec.lower())
    dl = math.hypot(spec[0], spec[1]) or 1
    return (spec[0] / dl, spec[1] / dl)


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def ccw(p: Pt, q: Pt, r: Pt) -> bool:
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> tuple[float, float] | None:
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def point_in_poly(px: float, py: float, poly: Any) -> bool:
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def poly_dist(px: float, py: float, poly: Poly) -> float:
    if point_in_poly(px, py, poly):
        return 0.0
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def kiln_quarters(k: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A kiln works' own cottages as footprint records, ROTATION INCLUDED.

    One helper rather than two call sites unpacking the list by index, because they had already
    drifted apart once in spirit: `kiln_keeps_fire_gap` and `wells_among_dwellings` both rebuilt the
    record inline and both dropped the rotation, so a works drawn at rot=270 was adjudicated as a
    box at the right place with the wrong orientation (Tango's 69 ft fire gap measured 62 ft). Same
    lesson as `solid_structs` one level down: a record that two checks unpack by hand is a record
    that will be unpacked differently by the third.

    A record with only four elements predates the rotation and is read as rot=0 - which is what
    every kiln works was before the maps started passing `rot` on 2026-07-27."""
    return [{"x": q[0], "y": q[1], "w": q[2], "h": q[3], "rot": (q[4] if len(q) > 4 else 0.0)} for q in k.get("quarters", []) or []]


def edge_gap(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    """The TRUE gap in px between two rotated footprints - the distance you could measure on the
    ground between the nearest points of two buildings. 0.0 if they overlap or touch.

    THE ONE MEASUREMENT ANY GAP VERDICT USES (GM, 2026-07-26). Before this there were THREE
    conventions in the file for the same question, and all three were wrong in different ways:

      - raw center-to-center (`math.hypot(a["x"] - b["x"], ...)`) understates the real clearance by
        the sum of both half-extents, so a rule promising 120 ft delivered as little as ~60 at town
        scale. Two live defects shipped this way: an execution ground and a boundary stone both
        sited inside the line they were supposed to be outside of.
      - the circumscribed radius (`0.5 * math.hypot(w, h)`) is the half-DIAGONAL, which exceeds the
        true half-extent by up to 41% on a square and more on an elongated rect;
      - `max(w, h) / 2` is the same error, differently sized.

    And the approximations' error FLIPS SIGN with the rule: subtracting too much makes a
    "must be far" rule strict and a "must be near" rule lenient, so they cannot even be reasoned
    about as a uniform safety margin. Since the closest pair of two convex polygons is always a
    vertex of one against an edge of the other, the exact answer costs a few `poly_dist` calls -
    there was never a reason to approximate it.

    Centers remain correct for CLASSIFICATION ("which ward is this in" - a building belongs to one
    ward, not 0.6 of one), for ASSOCIATION/REACH whose tolerance dwarfs the footprints, and for
    PREFILTERS. See the dev-loop doc, "Centers, footprints, and aggregates"."""
    da, db = _gap_disc(a), _gap_disc(b)
    if da is not None and db is not None:
        return max(0.0, math.hypot(da[0] - db[0], da[1] - db[1]) - da[2] - db[2])
    if da is not None:
        return max(0.0, poly_dist(da[0], da[1], rect_corners(_struct_rect(dict(b)))) - da[2])
    if db is not None:
        return max(0.0, poly_dist(db[0], db[1], rect_corners(_struct_rect(dict(a)))) - db[2])
    ca, cb = rect_corners(_struct_rect(dict(a))), rect_corners(_struct_rect(dict(b)))
    if sat_overlap(ca, cb):
        return 0.0
    return min(min(poly_dist(px, py, cb) for px, py in ca), min(poly_dist(px, py, ca) for px, py in cb))


def _gap_disc(o: Mapping[str, Any]) -> tuple[float, float, float] | None:
    """(x, y, radius) if this feature is drawn as a DISC rather than a rect, else None.

    A wellhead is the case: it records `r` (clearance) and `vr` (the drawn head) and carries no
    w/h at all, so treating every feature as a rect is not merely imprecise here, it raises
    KeyError. Found the hard way on 2026-07-27, and the way it was found is worth more than the
    bug: a crashing gate prints no FAIL lines, so a pool scan that greps for FAIL read the crash
    as CLEAN - the file's own "a check that never RUNS looks exactly like a check that passes",
    committed by the person who had just written it down. Scan for the exit code, not for FAIL.

    `vr` over `r` for the same reason `_struct_rect` prefers vw/vh: a clearance rule is about the
    ink on the map, and the drawn head is what a reader sees."""
    if "w" in o:
        return None
    return float(o["x"]), float(o["y"]), float(o.get("vr", o.get("r", 0.0)))


def _gap_reach(o: Mapping[str, Any]) -> float:
    """A circumscribed radius for the pair prefilter - deliberately generous (see within_edge_gap)."""
    d = _gap_disc(o)
    return d[2] if d is not None else math.hypot(o.get("vw", o["w"]), o.get("vh", o["h"])) / 2


def within_edge_gap(a: Mapping[str, Any], b: Mapping[str, Any], lim: float) -> bool:
    """Is the true gap between two footprints at most `lim` px? Center-distance prefiltered, so a
    check may ask it of every pair on a city without the exact test running on all of them - the
    index-prunes-never-decides rule applied to a pair test. The prefilter uses circumscribed radii
    deliberately: over-estimating an extent can only admit a pair the exact test then rejects."""
    if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) > lim + _gap_reach(a) + _gap_reach(b):
        return False
    return edge_gap(a, b) <= lim
