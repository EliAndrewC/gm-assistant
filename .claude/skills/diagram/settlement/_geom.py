"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import os
import random
from collections.abc import Callable, Mapping, Sequence
from typing import Any, SupportsIndex, cast

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points
Manifest = dict[str, Any]  # the JSON settlement manifest the generator emits


def _assert_not_main_tree(path: str | None = None) -> None:
    """Refuse to run from the MAIN /gm-assistant checkout. Main is the integration point,
    never a workspace (CLAUDE.md "Session clones"): a generator/gate/test writing into main's
    tree races with another session's mid-ritual push-to-checkout (the 2026-07-20 double-push
    post-mortem). Import-time enforcement here covers every Mode B gen, check_village.py, and
    the pytest suites, since they all import this module. GM_ASSISTANT_ALLOW_MAIN=1 overrides
    the guard: the GM sets it for a deliberate main-tree run, and the stop-work ritual's
    render-sync sets it (scoped to its one locked regen-in-main); a session never sets it by
    hand for anything else."""
    p = os.path.realpath(path if path is not None else __file__)
    if p.startswith("/gm-assistant/") and "/.clones/" not in p and os.environ.get("GM_ASSISTANT_ALLOW_MAIN") != "1":
        raise SystemExit(
            "ERROR: this ran from the MAIN /gm-assistant tree. Main is the integration point, never a workspace -\n"
            "every generator, gate, and test runs inside the session's own clone under /gm-assistant/.clones/.\n"
            "Check CLAUDE.md, section 'Session clones' (reload CLAUDE.md if it has fallen out of your context\n"
            "window) for the procedure: create or reuse .clones/<kebab-cased-session-name>, sync it in with\n"
            "'git pull origin main', and run this same command from inside that clone.\n"
            "(GM override for a deliberate main-tree run: GM_ASSISTANT_ALLOW_MAIN=1)"
        )


_assert_not_main_tree()

LAND = '#EFE3C2'
PADDY_SHADES = ['#A7C49C', '#9FBE93', '#AECBA1', '#9BBA8F', '#B4CCA6']  # rice mid-growth (green)
FLOODED_SHADES = ['#93B0A2', '#8AAB9A', '#9DBAAB', '#88A99A', '#9AB6A8']  # just-transplanted paddy (water+shoots, blue-green)
RIPE_SHADES = ['#CBBB74', '#C4B36A', '#D1C180']  # ripening rice (golden) - a few plots
RICE_GREENS = ['#A6C398', '#A2C094', '#A9C69C']  # rice at ONE stage - near-identical greens (reads uniform)

# STANDALONE plank-footbridge geometry, shared by channel_footbridges() (placement) and the
# footbridges_reach_useful_ground check in check_village.py (which duplicates these three values -
# keep them in sync). A dobashi footplank spans an ~8 ft ditch with a short landing each bank; it
# exists so field-workers can cross to the FIELD, so both banks must reach ground worth crossing to.
PLANK_ABUTMENT = 6.0  # deck = local ditch width + this SHORT abutment (GM 2026-07-22: was 15, far too long for a footplank)
PLANK_BANK_REACH = 11.0  # px past the abutment where a bank opens onto the terrain it lands on
LANDING_FT = 10.0  # a CARRIED deck runs this many REAL feet of deck onto dry ground past each
# bank (GM 2026-08-09). Researched: a bridge does not stop at the water's edge - the girder
# bears on an abutment sill set BACK from the channel edge, both because scour (the current
# undercutting the bank) must never reach the bearing and because the seat itself needs
# bearing length - so a modest timber bridge lands ~5-15 ft of deck past the water on each
# side; 10 ft is mid-band. REAL feet (convert by self.ftpx when drawing), unlike
# PLANK_ABUTMENT above, which is px and deliberately short: a dobashi footplank simply rests
# its ends on the bank (GM 2026-07-22), so footplanks do NOT take this landing.
PLANK_VILLAGE_REACH = 55.0  # a bank within this of a dwelling reaches the VILLAGE (a place worth crossing to)


# TORII AVENUE PITCH (GM 2026-07-25, after a research pass - see settlements.md 'Torii'). Rokugan's
# sando is the 1/3/7 SET of formal gateways, NOT a Fushimi-style donation row: donation rows are a
# designated-site special case here (Shinden Togashi, the Temple of Amaterasu, the Ki Rin Shrine and
# their like), so NEITHER real-world spacing regime is the model. The research found only two: a
# donation row's arches nearly touch (~0.5-1 m in the dense tunnel, "several yards" where it loosens),
# and ranked ichi/ni/san gates stand 200 m - 1.3 km apart (off the map at every settlement scale).
# Our avenues fall between, so the spacing is a house rule rather than a copied fact: arches stand
# ~20 ft apart center-to-center, and NEVER more than two rail-spans (32 ft), past which a sando reads
# as a line of isolated gates rather than one approach. The floor is the existing one arch-span
# (torii_spread_out) so they never overlap into a blob. Village avenues sit at the top of the band
# (~30 ft) by GM preference and are deliberately left alone - the cap, not the target, is the rule.
TORII_PITCH_FT = 20.0  # the usual stride: what the engine lays when it sets an avenue's pitch
TORII_PITCH_MAX_SPANS = 2.0  # the ceiling, in torii rail-spans (32 ft for a standard 16 ft arch)


def torii_halfbox(ftpx: float, span_ft: float = 16.0) -> tuple[float, float, float]:
    """True drawn half-extents (x half-width, y-up, y-down) of a `_torii` glyph at scale `ftpx`, plus a small
    stroke pad - used to FRAME torii (crop_to_content) and to verify they sit within the frame (check_village
    mirrors this function; keep the two in sync). Follows _torii's geometry: s2 = (span_ft/ftpx)/2, rail ends at
    +/-s2, rail rise s2*7/19, post drop s2*17/19. Replaces the legacy fixed x+/-19 / y-10..+18 box - the
    pre-true-scale 38px glyph (GM 2026-07-21), which over-reserved ~5x the arch's real footprint of frame margin
    (a village torii is ~8px/16ft wide, not 38px), pushing the crop out around the end of an approach avenue."""
    s2 = (span_ft / ftpx) / 2
    pad = 2.0  # rail/post stroke half-width + a hair, so the frame never clips the vermilion
    return s2 + pad, s2 * 7.0 / 19.0 + pad, s2 * 17.0 / 19.0 + pad


def _signed_area(poly: Poly) -> float:
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2


def forest_reveal_x(forest: Poly, edge: Poly | None, reveal: float, w: float) -> list[float]:
    """The x-values a canvas-filling FOREST contributes to the crop frame (mirrored by
    check_village.forest_reveal_x - keep the two in sync; the crop and the check that gates the
    crop's tightness must read the same rule from the same manifest fields).

    The wood is drawn all the way to the canvas edge, but the frame only REVEALS a shallow band of
    it past the tree line: the tree line itself plus `reveal` px of canopy behind it. Deeper in it
    is identical crowns, and a frame held open for them is wasted image (GM 2026-07-25). Without a
    recorded tree line (M['forest_edge']) the whole clamped polygon sets the frame, as it used to."""
    if not edge:
        return [min(max(p[0], 0), w) for p in forest]
    ex = [min(max(p[0], 0), w) for p in edge]
    return ex + [min(x + reveal, w) for x in ex]


def forest_frame_span(vals: Sequence[float], limit: float, other: Sequence[float]) -> tuple[float, float]:
    """One axis of the EDGE forest's frame contribution (mirrored by check_village's crop_hugs_content -
    keep the two in sync). `vals` are the wood's already-clamped values on that axis, `limit` the canvas
    size, `other` every value the REST of the content contributes there.

    A tree line that runs off BOTH ends of an axis is running ALONG it, not bounding anything: the wood
    continues past whatever frame we choose, so pinning that edge to the canvas holds the view open for
    more of the same crowns - the identical waste the reveal band already rejects on the axis the wood
    FACES (GM 2026-07-25: Moritono's north edge sat at the canvas top because the Shirin Forest, an
    east-edge wood drawn from y=-10 to y=1510, spanned the full height, while the northernmost real
    content - a well - stood 157px in; the tree line still runs off a tighter north edge, which is the
    reading we want). On such an axis the wood takes the span the rest of the content sets, so it can
    neither extend nor shrink the frame. Otherwise its own span is content, as before."""
    lo, hi = min(vals), max(vals)
    if lo <= 0 and hi >= limit and len(other):
        return max(0.0, min(other)), min(limit, max(other))
    return min(max(lo, 0.0), limit), min(max(hi, 0.0), limit)


def point_in_poly(px: float, py: float, poly: Poly) -> bool:
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


# Urban building kinds a SAMURAI WARD refuses (Settlement.ward / Settlement.building): the commoner
# dwellings and commerce the fence exists to keep out (GM 2026-08-02, on Minami: laborer houses in
# the middle of the samurai neighborhood, on the samurai side of the fence). servant is deliberately
# absent - samurai households' live-in domestics lodge inside the ward, and the city gens interleave
# them on purpose. So is monk_house: a temple may legitimately stand inside the ward (Tango's
# Bishamon precinct - the warrior fortune beside the garrison quarter) and its clergy row belongs
# with its temple, held to it by the temple-neighborhood checks.
WARD_BARRED_KINDS = frozenset({"laborer", "laborer_large", "merchant", "merchant_house", "merchant_large", "burakumin", "shop", "inn"})


def ward_interior(fence: Poly, wall: Poly) -> Poly | None:
    """Close a ward FENCE polyline against the city wall ring: the ward's interior polygon.

    The fence's two ends abut the rampart (city_ward_fence_meets_wall holds that), so the fence
    plus the wall arc between its ends encloses the ward. Two arcs qualify; the ward is the
    SMALLER enclosed region - a ward is a quarter carved off the city, never the larger half
    (all three pool cities measure 21-25% of the walled area). Returns None when there is
    nothing to close (no wall ring / a degenerate fence) - callers skip rather than guess.
    check_village re-derives this independently for city_samurai_ward_residents_only: the check
    must not trust the engine's arithmetic."""
    if len(wall) < 3 or len(fence) < 2:
        return None
    # ARC-LENGTH closure, not nearest-VERTEX closure: a fence end abuts the rampart mid-EDGE, so
    # walking vertex indices from "the nearest vertex" can skip (or wrongly include) the vertex on
    # the far side of the junction, and the resulting polygon self-intersects - a bowtie, whose
    # shoelace area under-measures by cancellation and steals the smaller-area vote (caught by the
    # square-wall unit test). Projecting each end onto the ring and collecting the vertices whose
    # arc position lies strictly between the two junctions, in traversal order, yields a SIMPLE
    # polygon for both candidate closures, so the smaller-area rule is sound.
    ring = list(wall) + [wall[0]]
    arcs = [0.0]
    for i in range(len(ring) - 1):
        arcs.append(arcs[-1] + math.hypot(ring[i + 1][0] - ring[i][0], ring[i + 1][1] - ring[i][1]))
    perim = arcs[-1]
    if perim <= 0:
        return None

    def project(p: Pt) -> float:
        best: tuple[float, float] | None = None
        for i in range(len(ring) - 1):
            ax, ay = ring[i]
            bx, by = ring[i + 1]
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))
            qx, qy = ax + t * dx, ay + t * dy
            d = (p[0] - qx) ** 2 + (p[1] - qy) ** 2
            if best is None or d < best[0]:
                best = (d, arcs[i] + t * math.sqrt(length2))
        return 0.0 if best is None else best[1]

    def area(poly: Poly) -> float:
        a = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            a += x1 * y2 - x2 * y1
        return abs(a) / 2

    t0, t1 = project(fence[-1]), project(fence[0])
    fwd_span = (t1 - t0) % perim
    fwd = sorted(((arcs[i] - t0) % perim, wall[i]) for i in range(len(wall)))
    arc_fwd = [v for o, v in fwd if 1e-6 < o < fwd_span - 1e-6]
    back = sorted(((t0 - arcs[i]) % perim, wall[i]) for i in range(len(wall)))
    arc_back = [v for o, v in back if 1e-6 < o < (perim - fwd_span) - 1e-6]
    pa = list(fence) + arc_fwd
    pb = list(fence) + arc_back
    return pa if area(pa) <= area(pb) else pb


def seg_closest(px: float, py: float, a: Pt, b: Pt) -> Pt:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ax + t * dx, ay + t * dy


def seg_dist(px: float, py: float, a: Pt, b: Pt) -> float:
    cx, cy = seg_closest(px, py, a, b)
    return math.hypot(px - cx, py - cy)


def ring_touches(cx: float, cy: float, r: float, ring: Poly) -> bool:
    """Does a disc of radius r at (cx, cy) lap this ring - inside it, or within r of an edge?"""
    return point_in_poly(cx, cy, ring) or any(seg_dist(cx, cy, ring[i], ring[(i + 1) % len(ring)]) < r for i in range(len(ring)))


def paddy_wet_rings(M: Manifest) -> list[Poly]:
    """The rings that are a paddy field's WATER - the ground a wellhead may not stand in.

    `Settlement._well_ground_clear` (placement) and `wells_clear_of_paddies` (the verdict) both read
    this ONE function, so the siter and the check cannot disagree about where the water is - the trap
    recorded in this skill's CLAUDE.md under "Placement and its check must read the SAME manifest
    source".

    PREFER THE DRAWN PLOTS. `plot_polys` holds the individual bunded basins as they are drawn, so it
    is the ink a reader sees, and reading it leaves the fan's unplanted RIM SLACK available - which
    matters, because the smoothed `outline` is an ENVELOPE claiming more ground than the crop fills,
    and that margin is exactly where `farm_wells` seats the well of a steading boxed in by crop (see
    its fallback, and the two tests that pin it). Treating the envelope as water refuses legitimate
    margin, and on Tango's east fan it left a steading with no legal seat anywhere.

    FALL BACK TO THE OUTLINE where a field records no plots, rather than skipping that field. Only
    the three provincial cities record `plot_polys` today; all 23 rural paddy fields in the pool
    record just an outline, so a plots-only rule would silently never run on a single hamlet,
    village or town - and a check that never runs looks exactly like a check that passes (same
    CLAUDE.md). Where the plots are not recorded the fan is drawn as one wet body anyway, so its
    outline IS the edge of the water. The fallback costs nothing today: swept across the pool, no
    well on any map stands inside a paddy outline."""
    rings: list[Poly] = []
    for fl in M.get("fields") or []:
        if fl.get("kind") != "paddy":
            continue
        drawn = [r for r in ([(float(p[0]), float(p[1])) for p in q] for q in (fl.get("plot_polys") or [])) if len(r) > 2]
        if drawn:
            rings.extend(drawn)
            continue
        ring = [(float(p[0]), float(p[1])) for p in (fl.get("outline") or [])]
        if len(ring) > 2:
            rings.append(ring)
    return rings


# ---- the travelled ways, and the gate that bars one ------------------------------------------
# A kido is a gate ACROSS A WAY, so what it squares to is the way, not the fence it hangs in (GM
# 2026-07-26). These helpers are the single definition of "a road runs through here", shared by
# s.ward/s.kido (which place the gate) and check_village (which grades it), so placer and checker
# cannot drift - the same discipline as torii_wall_conflicts above.
LANE_THROUGH_TOL = 12.0  # a lane whose centerline passes within this of a gate seat runs THROUGH the gate (the kido's roofed bar is ~16px long, so a lane this near is one the bar spans)
LANE_CROSSES_MIN_DEG = (
    25.0  # ...and it must actually CROSS the fence rather than run ALONGSIDE it: a street laid parallel to the ward fence never passes through the gate, so it must not be what the gate squares to
)


def lane_runs(M: Manifest) -> list[tuple[Poly, float]]:
    """Every travelled way on the map as (polyline, bed half-width): the major/Imperial roads, the
    town streets, the gravel alleys, and the city ring road. Deliberately NOT walls, fences or
    watercourses - this answers "what could someone walk or cart along here"."""
    runs: list[tuple[Poly, float]] = []
    roads: Any = M.get("roads")
    if not roads and M.get("road"):
        roads = [{"pts": M["road"], "w": M.get("road_width", 26)}]
    for rd in roads or []:
        runs.append(([(float(p[0]), float(p[1])) for p in rd["pts"]], float(rd.get("w", 26)) / 2))
    for st in M.get("town_streets") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in st["pts"]], float(st.get("w", 18)) / 2))
    for al in M.get("alleys") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in al["pts"]], float(al.get("w", 6)) / 2))
    if M.get("ring_road"):
        runs.append(([(float(p[0]), float(p[1])) for p in M["ring_road"]], float(M.get("ring_road_width", 20)) / 2))
    return runs


def way_beds(M: Manifest) -> list[tuple[Poly, float]]:
    """Every DRAWN way BED as (polyline, half-width): `lane_runs` (roads, town streets, alleys, the
    ring road) PLUS the village/hamlet lane network (`lane`, `lanes`), which lane_runs does not carry.

    This is the AVOIDANCE list for a verge-hugging feature - the notice board and the punishment
    ground, which both site themselves on a frontage and both deliberately bypass the lane CORRIDOR
    (a house setback: homesteads must not crowd the tread, while a board that everyone passes is the
    whole institution). Bypassing the corridor must not mean standing in the roadbed, so each siter
    still tests every bed - and it must be EVERY bed, not merely the ones it sampled candidates
    from: a spot offset from street A can land on alley B, and each siter had built its own partial
    list (the board's omitted town_streets and alleys, the punishment ground's omitted alleys and
    the ring road), so a seat clipping an alley was proposed rather than refused and had to be
    hand-sited (Tango, reported by another session 2026-07-27). The gate caught it after the fact -
    the overlap matrix forbids SOLID x WAY - so this closes the PLACEMENT half of the same rule.
    """
    runs = lane_runs(M)
    if M.get("lane"):
        runs.append(([(float(p[0]), float(p[1])) for p in M["lane"]], 4.0))
    for ln in M.get("lanes") or []:
        runs.append(([(float(p[0]), float(p[1])) for p in ln["pts"]], float(ln.get("w", 8)) / 2))
    return runs


def stroke_quads(pts: Sequence[Any], hw: float) -> list[Poly]:
    """One quad per segment of a polyline at half-width `hw` - a linear feature as real polygons, so
    a caller can SAT-test against it instead of measuring to sample points (a corner-distance test
    misses a line passing through the MIDDLE of a box, which is exactly the ward-fence-through-the-
    guard-box case it was hiding)."""
    quads: list[Poly] = []
    for i in range(len(pts) - 1):
        ax, ay = float(pts[i][0]), float(pts[i][1])
        bx, by = float(pts[i + 1][0]), float(pts[i + 1][1])
        ln = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / ln * hw, (bx - ax) / ln * hw
        quads.append([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    return quads


def lane_through_gate(M: Manifest, x: float, y: float, fence_deg: float) -> tuple[float, float] | None:
    """The travelled way a ward gate seated at (x, y) BARS, as (tangent degrees, bed half-width), or
    None if the gate stands in open fence with no lane through it. `fence_deg` is the local fence
    tangent, used only to reject a lane running ALONGSIDE the fence (which the gate does not bar).
    The nearest true crossing wins where several lanes are close."""
    best: tuple[float, float, float] | None = None
    for pts, half in lane_runs(M):
        for i in range(len(pts) - 1):
            d = seg_dist(x, y, pts[i], pts[i + 1])
            if d > LANE_THROUGH_TOL:
                continue
            a = math.degrees(math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0]))
            if abs(((a - fence_deg + 90.0) % 180.0) - 90.0) < LANE_CROSSES_MIN_DEG:
                continue  # runs alongside the fence, not through the gate
            if best is None or d < best[0]:
                best = (d, a, half)
    return None if best is None else (best[1], best[2])


def kido_bar_deg(lane_deg: float, fence_deg: float) -> float:
    """The angle a ward gate's roofed bar takes: SQUARE TO THE LANE it bars. Returned as the
    representative nearest the fence direction, so the guard box's ward-interior flank (which s.ward
    resolves against the bar's local +y) keeps the same sense whichever way the fence was drawn."""
    return fence_deg + (((lane_deg + 90.0) - fence_deg + 90.0) % 180.0 - 90.0)


def box_gap(a: Sequence[float], b: Sequence[float]) -> float:
    """Clear separation between two axis-aligned boxes (x0, y0, x1, y1) - 0 when they touch or
    overlap. The single measure behind the label standoff ladder below AND behind the gate's
    `label_hugs_its_referent`, so placer and checker agree by construction."""
    dx = max(0.0, b[0] - a[2], a[0] - b[2])
    dy = max(0.0, b[1] - a[3], a[1] - b[3])
    return math.hypot(dx, dy)


# ---- LABEL STANDOFF LADDER (GM 2026-07-26) ----------------------------------------------------
# The label doctrine was "empty ground wins" (see settlements/presentation.md), scored by
# `_label_hits` - a COUNT of the footprints a candidate box would cover. Overlaps were the only
# term, so every clear candidate tied at zero and the winner fell out of generation order: a
# caption could float 50+px out in bare ground and score exactly as well as one tucked against the
# thing it names. Tango showed both halves of the failure at once - "Imperial Road" sat 55px off
# the roadway, and "gate market" 42px east of its stall rows, ending up nearer the execution
# ground than the market it labels. The fix is a SECOND term: among candidates that cover nothing,
# the NEAREST wins, searched over a ladder of standoffs instead of at one hand-guessed distance.
#
# WHY THESE ARE PIXELS AND NOT FEET (the usual unit in this engine): this is a LEGIBILITY rule,
# and label type does not scale with the map grain - captions are 9-14px at 1, 2 and 3 ft/px
# alike - so the air a caption needs to read as "beside, but not touching" is a constant number of
# pixels at every scale. Expressed in feet it would be 5 ft at hamlet grain and 15 ft in a city,
# which is exactly backwards.
LABEL_MIN_AIR = 5.0  # clear air between a caption's box and its subject's. Calibrated to the
#                      hand-tuned captions already in the engine, which this must not visibly
#                      change: a size-9 label drawn at `y + h/2 + 11` puts its glyph top 3.8px
#                      below the subject's edge, and one at `y - h/2 - 9` its descender 6.75px
#                      above - so ~5px is the house standoff, arrived at by eye over many maps.
LABEL_AIR_STEP = 6.0  # ladder rung: fine enough to find a slot between crowded features, coarse
#                      enough that nine rungs still reach past a dense frontage band.
LABEL_AIR_RINGS = 9  # ~53px of reach. Past that a caption has lost its subject anyway, so the
#                      placer stops searching and takes the least-covered seat it found.
LABEL_AIR_CAP = 3.0  # x font size - how far a placed caption may END UP from its subject before
#                      `label_hugs_its_referent` calls it adrift. A BACKSTOP, not the mechanism:
#                      the ladder does the real work, and this only catches a caption that ran the
#                      whole ladder and still landed nowhere near its subject. Calibrated against
#                      the Tango numbers: it fires on the two captions the GM caught (55px on a
#                      12px "Imperial Road", 42px on a 10px "gate market") and passes the tightest
#                      seat the ladder can actually find for that road caption (29px - Tango's
#                      north roadway is flanked by market stalls the whole length of the segment,
#                      so 29px IS the nearest clear ground, and a cap that failed it would be
#                      demanding a placement no map can make).

# A CAPTION IS SIZED BY ITS GLYPH, NOT BY THE INSTITUTION'S IMPORTANCE (GM 2026-08-08). Both of
# these used to be set by rank - a temple and a governor outrank a ministry office, so their
# captions were bigger - and on the rendered maps that read as a mistake rather than a hierarchy:
# a city temple hall is 96-140 real ft and a ministry office is 114-140, the same size class, yet
# "Temple of Benten" at 13pt was set 44% larger per character than "Ministry of Rites" standing a
# few hundred px away - so the temple neighborhood read as shouting rather than as ranked. The rank
# still shows, in COLOR (temple red, ministry violet) and in weight, which is where it belongs.
HALL_CAPTION_FS = 9.0  # every religious hall's caption - city temple, town monastery, village
#                        shrine - at the ministry's size. The village case has the same defect and
#                        the same cure: Kikuta's 88x60 ft "Shrine to Benten" was set at the same
#                        13pt beside 9-11pt neighbors on a map whose other glyphs are half the
#                        size. Read by `_hall_caption_y` too, which must measure the box
#                        `shrine_hall` will actually draw.
GOVERNOR_CAPTION_FS = 11.0  # the yamen's caption, ~20% down from the manor default of 14 so it
#                             fits INSIDE the empty court with air on both sides: at 11pt
#                             "Governor's Mansion" measures 123px in the render font against the
#                             145px-wide mansions of Tango and Nagahara, i.e. ~11px (~33 real ft)
#                             off each wall. At 14 it measured 157px and would not fit at all.


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    def ccw(p: Pt, q: Pt, r: Pt) -> bool:
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])

    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


# ---------------------------------------------------------------------------------------------
# A TORII STANDS CLEAR OF EVERY WALL (GM 2026-07-25, caught on Nagahara: the seventh arch of the
# Ebisu sando stood in the samurai ward fence). WHY: a torii is a FREESTANDING gateway - two posts
# in open ground that carry no load and close nothing, marking the threshold of sacred ground. A
# wall is its opposite: a continuous barrier whose whole purpose is that you cannot walk through
# it. So an arch drawn ON a wall run is impossible construction twice over - the posts stand inside
# the palisade, and the "gateway" opens onto a barrier. Where a way genuinely pierces a wall the
# opening is a GATE STRUCTURE (the city gate, a ward kido), never an arch. A torii over an ordinary
# street or lane stays legitimate: a sando arch spans its road, and a road is not a barrier.
#
# The rule is enforced from BOTH ends, because either feature may be drawn first (see CLAUDE.md
# "DRAW ORDER"): _torii refuses a seat standing in a wall already drawn (and shrine_hall shortens
# its avenue to fit rather than fail), while every wall-drawing method re-asks the question once
# its own run is on the page. check_village's torii_clear_of_walls is the manifest-level backstop,
# and all three read the SAME wall_runs() / torii_wall_conflicts() below.


def _rect_ring(x: float, y: float, w: float, h: float, rot: float = 0.0) -> Poly:
    """The closed corner ring of a (possibly rotated) w x h rect centered at (x, y)."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts: Poly = [(x + dx * c - dy * s, y + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return pts + [pts[0]]


def sat_overlap(p: Sequence[Sequence[float]], q: Sequence[Sequence[float]]) -> bool:
    """Do two CONVEX polygons overlap? (separating-axis test; touching edges do not count.)"""
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


def label_tilt(rot: float) -> float:
    """The angle a caption takes to lie ALIGNED with the feature it names when that feature is
    drawn at `rot` degrees (GM 2026-08-02: an angled building's label carries the building's own
    tilt - "caravan inn" runs along its rot=-16 inn, not as level text beside a diagonal glyph).
    Folded mod 90 into [-45, 45): the text aligns with whichever of the building's two edge
    families lies nearer the horizontal, so a caption never tilts past 45 degrees (legibility),
    and a SQUARE-rotated building (0/90/180/270) keeps its level caption EXACTLY as before - the
    fold is what keeps every level caption in the pool byte-stable. Rounded to 0.1 degree (the
    grain the glyph transforms use); float noise under half that grain snaps level."""
    t = (rot + 45.0) % 90.0 - 45.0
    return 0.0 if abs(t) < 0.05 else round(t, 1)


def linear_tilt_full(rot: float) -> float:
    """The GM's 2026-08-09 EXTENSION of the linear-caption rule: a LINE subject's caption may
    carry its FULL tilt, past linear_tilt's 45-degree go-level clamp - the cartographic
    along-feature convention (a river's name lies along the river at whatever bearing the river
    runs). Opt-in per call site (label(full_tilt=True)): the clamp stays the default, so every
    existing road caption in the pool - including Hoshizora's level "Imperial Road", the ruling
    that set the clamp - is byte-identical. Normalized to [-90, 90) so a bearing and its reverse
    caption identically and the text never renders upside down."""
    t = (rot + 90.0) % 180.0 - 90.0
    return round(t, 1) if abs(t) >= 0.05 else 0.0


def linear_tilt(rot: float) -> float:
    """The caption tilt for a LINEAR subject - a road, a street, a row of shopfronts laid along
    one (GM 2026-08-08: Hoshizora's "Imperial Road" and "merchant houses & shops" read level
    beside a roadbed running at -27 degrees). A line has ONE axis, not a building's two edge
    families, so this CLAMPS where `label_tilt` FOLDS, and the two must never be swapped:

    - The angle is normalized to [-90, 90) - a bearing and its reverse describe the same line,
      so a road stored SW-to-NE and the same road stored NE-to-SW caption identically.
    - Past 45 degrees the caption goes LEVEL rather than tilting. That is the GM's own rule for
      a north-south road ("it is reasonable to have the label still read left-to-right"), and it
      generalizes: text steeper than 45 degrees is hard to read, and unlike a building there is
      no second edge family to fall back on - a near-vertical road's cross direction is not an
      axis of anything drawn. Folding a 72-degree road (Nagahara's Imperial approach) to -18
      would tilt the caption to match NOTHING on the map, which is worse than level.

    The 45-degree cutoff is therefore a discontinuity by design: a 44-degree road tilts, a
    46-degree one does not. It never shows WITHIN a map (a caption names one stretch of one
    road), and legibility is the thing being protected at the boundary either way."""
    t = (rot + 90.0) % 180.0 - 90.0  # (-90, 90]: a line has no direction, only an axis
    return 0.0 if abs(t) < 0.05 or abs(t) > 45.0 else round(t, 1)


def label_quad(L: Sequence[Any]) -> Poly:
    """The drawn corner ring of a recorded label. Elements [0..3] are the caption's UNROTATED box
    (what `_record_label` has always written); a TILTED caption (element [7], degrees - see
    `label_tilt`) is that box rotated about its own center, exactly the SVG transform `label()`
    emits, so a check reads the true glyph run straight off the record. A level record returns
    its plain corners."""
    x0, y0, x1, y1 = float(L[0]), float(L[1]), float(L[2]), float(L[3])
    cs: Poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    t = float(L[7]) if len(L) > 7 and L[7] else 0.0
    if not t:
        return cs
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ca, sa = math.cos(math.radians(t)), math.sin(math.radians(t))
    return [(cx + (qx - cx) * ca - (qy - cy) * sa, cy + (qx - cx) * sa + (qy - cy) * ca) for qx, qy in cs]


def label_aabb(L: Sequence[Any]) -> tuple[float, float, float, float]:
    """A recorded label's axis-aligned bounds - what the CONTAINMENT consumers (frame clipping,
    the crop's must-include list, blocker lists, the title search) test. Identical to elements
    [0..3] for a level record; for a tilted one it is the rotated quad's AABB - the honest
    'ground this text can reach'."""
    q = label_quad(L)
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    return (min(xs), min(ys), max(xs), max(ys))


def tilt_caption_seat(x: float, y: float, rot: float, tilt: float, half_w: float, half_h: float, gap: float, above: bool = False) -> Pt:
    """Where a caption hangs off a TILTED footprint: the standard 'centered under the lower edge'
    seat every glyph uses, computed in the footprint's own frame and rotated with it (`above`
    flips to the upper edge). Which local half-extent lies perpendicular to the caption's
    baseline depends on which edge family `label_tilt` folded onto - a rot=150 works reads along
    its LONG side (half_h below the baseline) where a rot=102 yard reads along its SHORT one
    (half_w) - so both halves are passed and the fold decides."""
    perp = half_h if round((rot - tilt) / 90.0) % 2 == 0 else half_w
    a = math.radians(tilt)
    d = (perp + gap) * (-1.0 if above else 1.0)
    return (x - math.sin(a) * d, y + math.cos(a) * d)


# --- STABLE-YARD GLYPH EXTENTS: wells, trough clusters, hitching rails ------------------------
# These three MUST NOT OVERLAP ONE ANOTHER (GM 2026-07-25). The motivating defect was Nagahara's
# flophouse yard, which drew a hitching rail straight ACROSS a wellhead and then stacked the trough
# cluster on both: three glyphs piled on one spot, where the reader can no longer tell which is
# which, and the layout it implies is nonsense - you cannot draw water through a rail, and no yard
# ties its animals across its own draw-point. They collide because they are placed at three
# different moments (wells long before the yard, then the rails, then the cluster), so each stage
# has to test the DRAWN extent of everything already on the map.
#
# The builders below are the ONE definition of each glyph's drawn extent, shared by the placement
# in `_stable_yard` and by the `wells_troughs_rails_clear_of_each_other` check that gates it - the
# placement-and-check-read-the-same-data doctrine (see settlements.md "PLANK BRIDGES"): change what
# gets drawn and both sides move together instead of drifting into disagreement. `grow` inflates a
# quad by the placement's slack; the CHECK always passes 0, so a map that only just satisfies the
# check was in fact placed with room to spare.
YARD_GLYPH_SLACK = 2.0  # px (~6 real ft at city scale) of placement slack over the check's strict no-overlap floor


def wellhead_quad(w: Mapping[str, Any], grow: float = 0.0) -> Poly:
    """A wellhead's drawn extent: the well-house ROOF square (the curb and shaft draw inside it)."""
    e = w.get("vr", 4.0) + grow
    return [(w["x"] - e, w["y"] - e), (w["x"] + e, w["y"] - e), (w["x"] + e, w["y"] + e), (w["x"] - e, w["y"] + e)]


def trough_quad(box: Sequence[float], grow: float = 0.0) -> Poly:
    """A watering point's drawn extent: the stacked trough rects' full envelope - a stable-yard
    record's `troughs_box`, not one trough."""
    return [(box[0] - grow, box[1] - grow), (box[2] + grow, box[1] - grow), (box[2] + grow, box[3] + grow), (box[0] - grow, box[3] + grow)]


def tower_quad(t: Mapping[str, Any], grow: float = 0.0) -> Poly:
    """A wall tower's drawn footprint: its `w` x `h` mamian rect turned onto the wall's local
    tangent (`rot`). The default 38 x 38 is the pre-to-scale mamian, for a legacy record."""
    hw_, hh_ = t.get("w", 38) / 2 + grow, t.get("h", 38) / 2 + grow
    a = math.radians(t.get("rot", 0))
    ca, sa = math.cos(a), math.sin(a)
    return [(t["x"] + dx * ca - dy * sa, t["y"] + dx * sa + dy * ca) for dx, dy in ((-hw_, -hh_), (hw_, -hh_), (hw_, hh_), (-hw_, hh_))]


def rail_quad(rl: Mapping[str, Any], grow: float = 0.0) -> Poly:
    """A hitching rail's drawn extent: its `len` along the tangent by the posts' `reach` to either
    side. The POSTS are the glyph's real width - the bare rail line is a hairline nobody reads."""
    h, e = rl["len"] / 2 + grow, rl.get("reach", 2.4) + grow
    tx, ty = rl["tx"], rl["ty"]
    return [(rl["x"] + tx * sh * h - ty * se * e, rl["y"] + ty * sh * h + tx * se * e) for sh, se in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def wall_runs(M: Manifest) -> list[tuple[str, Poly, float]]:
    """Every WALL on a settlement map as (label, polyline, half-width px): the city rampart, each
    ward fence (plus the short wall-stroke caps where it abuts the rampart), and the perimeter of
    every walled compound - manor, governor's mansion, merchant estate, mausoleum. The half-widths
    are the DRAWN stroke half-widths (city_wall's 11 px rampart, ward's 5 px fence and 11 px cap,
    each compound's recorded wall_w), so the test is against the ink actually on the page."""
    runs: list[tuple[str, Poly, float]] = []
    ring = M.get("wall")
    if ring:
        pts: Poly = [(float(p[0]), float(p[1])) for p in ring]
        runs.append(("the city wall", pts + [pts[0]], 5.5))
    for wd in M.get("wards", []):
        runs.append((f"the {wd.get('name', 'ward')} ward fence", [(float(p[0]), float(p[1])) for p in wd["boundary"]], 2.5))
        for cap in wd.get("wall_caps", []):
            runs.append(("a ward fence wall-cap", [(float(p[0]), float(p[1])) for p in cap.get("pts", [])], 5.5))
    walled: list[tuple[str, Any]] = [(lbl, c) for lbl, key in (("a manor wall", "manors"), ("a merchant estate wall", "merchant_estates"), ("a mausoleum wall", "mausoleums")) for c in M.get(key, [])]
    if M.get("governor_mansion"):
        walled.append(("the governor's mansion wall", M["governor_mansion"]))
    for lbl, c in walled:
        if not all(k in c for k in ("x", "y", "w", "h")):
            continue  # a synthetic fixture compound recorded for some other check's sake carries no footprint to wall
        runs.append((lbl, _rect_ring(c["x"], c["y"], c["w"], c["h"], float(c.get("rot", 0) or 0)), float(c.get("wall_w", 2.0)) / 2))
    return [(lbl, p, half) for lbl, p, half in runs if len(p) >= 2]


def _box_hits_run(box: tuple[float, float, float, float], pts: Poly, half: float) -> bool:
    """Does an axis-aligned box (x0, y0, x1, y1) reach a polyline drawn `2 * half` px thick? The
    wall's stroke is a THICK line, so the box must clear its EDGE, not its centerline - and a run
    that merely ends inside the box (crossing no edge) counts too."""
    x0, y0, x1, y1 = box
    edges = (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)))
    for i in range(len(pts) - 1):
        a, b = (pts[i][0], pts[i][1]), (pts[i + 1][0], pts[i + 1][1])
        if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
            return True
        for e0, e1 in edges:
            if segments_cross(a, b, e0, e1):
                return True
            if min(seg_dist(a[0], a[1], e0, e1), seg_dist(b[0], b[1], e0, e1), seg_dist(e0[0], e0[1], a, b), seg_dist(e1[0], e1[1], a, b)) < half:
                return True
    return False


def torii_seat_on_wall(M: Manifest, tx: float, ty: float, ftpx: float, runs: list[tuple[str, Poly, float]] | None = None) -> str | None:
    """The label of the wall an arch seated at (tx, ty) would stand in, or None if it stands clear.
    Asked of ONE candidate seat before it is drawn; `runs` caches wall_runs(M) across a sweep. The
    arch's extent is torii_halfbox - the same true-scale glyph box the crop and frame checks use."""
    txh, tyu, tyd = torii_halfbox(ftpx)
    for lbl, pts, half in wall_runs(M) if runs is None else runs:
        if _box_hits_run((tx - txh, ty - tyu, tx + txh, ty + tyd), pts, half):
            return lbl
    return None


def torii_wall_conflicts(M: Manifest) -> list[tuple[float, float, str]]:
    """Every recorded arch standing in a wall, as [(x, y, wall label), ...] - the whole-manifest
    form of torii_seat_on_wall, shared by the engine's post-draw guards and by check_village."""
    ftpx = float(M.get("meta", {}).get("ftpx", 1) or 1)
    runs = wall_runs(M)
    bad = []
    for t in M.get("torii") or []:
        lbl = torii_seat_on_wall(M, float(t[0]), float(t[1]), ftpx, runs)
        if lbl:
            bad.append((round(float(t[0]), 1), round(float(t[1]), 1), lbl))
    return bad


def _union_area(rects: Any) -> float:
    """Total area covered by a set of axis-aligned rects (x0, y0, x1, y1), counting overlap ONCE. The grove's
    belt arms abut at the windward corner, so summing their areas double-counts it; the honest grove footprint
    is the union. Few small rects, so a coordinate-compression sweep is ample."""
    rects = [r for r in rects if r[2] > r[0] and r[3] > r[1]]
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    area = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        spans = sorted((r[1], r[3]) for r in rects if r[0] <= x0 and r[2] >= x1)
        cy = -1e18
        covered = 0.0
        for y0, y1 in spans:
            if y1 <= cy:
                continue
            covered += y1 - max(y0, cy)
            cy = y1
        area += (x1 - x0) * covered
    return area


def seg_intersect(a: Pt, b: Pt, c: Pt, d: Pt) -> Pt | None:
    """The (x, y) where segments ab and cd cross, or None if parallel. Call only when they cross."""
    den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
    if abs(den) < 1e-9:
        return None
    t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def edge_dist(px: float, py: float, poly: Poly) -> float:
    return min(seg_dist(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def boxed_polys(polys: Any, pad: float = 0.0) -> list[tuple[Poly, float, float, float, float]]:
    """Each polygon paired with its bounding box, expanded by `pad`, computed ONCE. Feed the result
    to `boxed_hit` - which is where the why is written down."""
    out: list[tuple[Poly, float, float, float, float]] = []
    for poly in polys:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        out.append((poly, min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))
    return out


def boxed_hit(px: float, py: float, boxed: Any, edge_pad: float = 0.0) -> bool:
    """Is (px, py) inside any pre-boxed polygon - or within `edge_pad` of one's edge?

    PREFILTER family (this skill's CLAUDE.md, "Centers, footprints, and aggregates"): the bbox
    PRUNES, the exact `point_in_poly` / `edge_dist` still DECIDES. The verdict is therefore
    identical to a bare scan, which is what lets the whole pool regenerate byte-identical when a
    caller switches over - and is why this is a prefilter rather than the forbidden "coarsen it"
    (CLAUDE.md, "When a check is slow, INDEX it - do not coarsen it").

    WHY IT EXISTS: the ground-cover scatters test every field poly, block poly and clearing PER
    SCATTER POINT, and a marshy village pushes hundreds of thousands of points through them -
    Kikuta burned 24.6M `point_in_poly` calls, 93% of its whole gen (profiled 2026-08-03). The
    PLACEMENT path had had this treatment for months (`_in_blocked`, via `_poly_bboxes`); the
    scatter path never got it. Build the boxes with the SAME pad you pass as `edge_pad`, or the
    prefilter can reject a point the edge test would have wanted."""
    return any(bx0 <= px <= bx1 and by0 <= py <= by1 and (point_in_poly(px, py, poly) or (edge_pad > 0 and edge_dist(px, py, poly) < edge_pad)) for poly, bx0, by0, bx1, by1 in boxed)


def boxed_segs(corridors: Any) -> list[tuple[Pt, Pt, float, float, float, float, float]]:
    """Every corridor segment with its clearance-expanded bbox, flattened and computed ONCE - the
    polyline companion of `boxed_polys`. Feed to `boxed_seg_hit`."""
    out: list[tuple[Pt, Pt, float, float, float, float, float]] = []
    for pl, hw in corridors:
        for i in range(len(pl) - 1):
            a, b = pl[i], pl[i + 1]
            out.append((a, b, hw, min(a[0], b[0]) - hw, min(a[1], b[1]) - hw, max(a[0], b[0]) + hw, max(a[1], b[1]) + hw))
    return out


def boxed_seg_hit(px: float, py: float, segs: Any) -> bool:
    """Is (px, py) within its clearance of any pre-boxed corridor segment? Prefilter family exactly
    as `boxed_hit` - and the same shape `_near_corridor` already uses on the placement side."""
    return any(bx0 <= px <= bx1 and by0 <= py <= by1 and seg_dist(px, py, a, b) < hw for a, b, hw, bx0, by0, bx1, by1 in segs)


class Indexed(list):  # type: ignore[type-arg]
    """A no-build registry that carries a VERSION, so an index built from it can be invalidated by
    the data itself rather than by a guess about the data.

    WHY NOT A CACHE KEY. Two attempts in this engine at "is my cached index still valid?" failed,
    both SILENTLY, both on 2026-08-03: an incremental index over `placed` missed the two sites that
    REBIND it to a filtered copy (Minami and Nagahara lost every garden), and a record-count
    fingerprint for the well grids missed an in-place replacement of a same-LENGTH ring (a wellhead
    cleared to stand in a paddy). Length, object identity and record counts are all guesses about
    CONTENT. A version the list bumps itself is not a guess - mutating is the only way content
    changes, and every mutator bumps.

    The cache lives on the list too (`cache`), keyed by consumer, so an index physically cannot be
    read against a different list than it was built from. That covers the one non-append pattern in
    the engine: `farm_wells` swaps `field_polys` for an empty list and swaps the ORIGINAL OBJECT
    back, which an identity- or length-keyed cache gets wrong and this cannot.

    `test_indexed_overrides_every_mutating_list_method` is the ratchet: it enumerates `list`'s
    mutators by introspection and fails if one is not overridden here, so a Python version adding a
    mutating method cannot open a silent staleness hole."""

    __slots__ = ("appends", "cache", "version")

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.version = 0
        self.appends = 0  # bumped ONLY by append/extend - see indexed_grid for why that distinction pays
        self.cache: dict[str, tuple[int, int, int, Any]] = {}

    def _bump(self) -> None:
        self.version += 1

    def append(self, item: Any) -> None:
        self.appends += 1
        self._bump()
        super().append(item)

    def extend(self, items: Any) -> None:
        self.appends += 1
        self._bump()
        super().extend(items)

    def insert(self, i: SupportsIndex, item: Any) -> None:
        self._bump()
        super().insert(i, item)

    def remove(self, item: Any) -> None:
        self._bump()
        super().remove(item)

    def pop(self, i: SupportsIndex = -1) -> Any:
        self._bump()
        return super().pop(i)

    def clear(self) -> None:
        self._bump()
        super().clear()

    def sort(self, **kw: Any) -> None:
        self._bump()
        super().sort(**kw)

    def reverse(self) -> None:
        self._bump()
        super().reverse()

    def __setitem__(self, i: Any, v: Any) -> None:
        self._bump()
        super().__setitem__(i, v)

    def __delitem__(self, i: Any) -> None:
        self._bump()
        super().__delitem__(i)

    def __iadd__(self, other: Any) -> Any:  # type: ignore[misc]  # same as __imul__ below: mypy checks this against list.__add__, which an in-place op on a subclass cannot satisfy; the override exists so `reg += xs` bumps the version
        self._bump()
        return super().__iadd__(other)

    def __imul__(self, n: Any) -> Any:  # type: ignore[misc]  # mypy compares __imul__ against list.__mul__, which cannot hold for an in-place op on a subclass; the override exists so `reg *= n` still bumps the version rather than silently invalidating an index
        self._bump()
        return super().__imul__(n)


def indexed_grid(lst: Any, key: str, build: Callable[[Any], PointGrid], add: Callable[[PointGrid, Any], None] | None = None) -> PointGrid:
    """The PointGrid `build` makes from `lst`, cached ON `lst` under `key` until `lst` mutates.

    A plain list (one a caller rebound out from under us) is handled by simply building fresh every
    time: slower, never wrong. That fallback is the whole reason this is safe to use on registries
    whose mutation pattern might change later."""
    if not isinstance(lst, Indexed):
        return build(lst)
    hit = lst.cache.get(key)
    if hit is not None:
        version, appends, count, grid = hit
        if version == lst.version:
            return cast(PointGrid, grid)
        # EVERY change since was an append (the version moved exactly as far as the append counter),
        # so the index is not stale - it is merely SHORT, and appending to a grid is exact. This is
        # what keeps an accreting registry cheap: `placed` grows ~1,000 times per city map with
        # queries interleaved, and rebuilding all of it per append would cost more than the scan
        # being replaced.
        if add is not None and lst.version - version == lst.appends - appends:
            add(cast(PointGrid, grid), lst[count:])
            lst.cache[key] = (lst.version, lst.appends, len(lst), grid)
            return cast(PointGrid, grid)
    fresh = build(lst)
    lst.cache[key] = (lst.version, lst.appends, len(lst), fresh)
    return fresh


class SeatMemo:
    """The lattice positions a generator's dwelling top-up has already REFUSED, so a later pass
    over the same ground does not pay for the same refusal a second time.

    WHY IT EXISTS (2026-08-08). Minami's top-up evaluated **511,519 candidate positions** at ~46us
    each - effectively the whole of that gen's 21s, and 2.2x its sibling cities - and **64.6% of
    those visits were RE-visits of a position an earlier pass had already refused at the same
    tightness**. The caller sweeps each caste's regions three times over and then again in
    `fill_exactly`, always on the same fixed 5x6 px lattice, so a target the ground cannot meet
    rescans the identical positions from scratch every time. Merchant houses alone: 295,400 visits,
    20 placements. The per-candidate work was already indexed to the floor by the 2026-08-03/04
    passes, so the only remaining lever was the candidate COUNT.

    IT IS A MINAMI TOOL, AND THAT IS MEASURED, NOT ASSUMED. The same memo was wired into Nagahara
    and Tango and both got SLOWER (9.56 -> 10.29s and 9.71 -> 10.19s): their re-visit share is
    **3.1% and 0.0%**, so every candidate paid the lookup and almost none of them saved a test.
    Minami is the outlier because the Fox eight-temple doctrine puts 8 precincts and 48 monk houses
    inside its walls, its residential packs seat nothing (`PACK SHORTFALL ... 0/300`), and its
    merchant target is unmeetable - which is what produces the repeated whole-region rescans. Do
    not wire this into a gen without measuring that gen's re-visit share first; below roughly a
    third it is a pessimization.

    THE INVARIANT IT RESTS ON. A refusal can only turn into a placement if some obstacle
    DISAPPEARS. Through a top-up phase every registry those tests read - `placed`, `block_polys`,
    `corridors`, `grove_rects`, `hard_polys`, and the manifest's buildings / houses / wells /
    labels - is only ever appended to, and `bound` only ever TIGHTENS (None -> the wall ring). So a
    refused position stays refused, skipping it changes nothing, and the maps regenerate
    byte-identical. That byte-identity is the real proof; everything below is what keeps it true.

    IT CHECKS THE INVARIANT RATHER THAN ASSUMING IT, because this engine has been burned twice by
    a memo that guessed (see `Indexed`: an incremental index over `placed` missed the two sites
    that REBIND it to a filtered copy, and Minami and Nagahara silently lost every garden).
    `sync()` compares a witness per registry and CLEARS everything unless it grew append-only:

    - an `Indexed` registry is exact - `version` moving exactly as far as `appends` means every
      change since was an append or extend, the same test `indexed_grid` uses to keep its grids;
    - a plain list is witnessed by identity + length, so a rebind or a truncation is caught (an
      in-place edit of an existing record is not, and nothing in a top-up phase does that);
    - `bound` may go from None to a ring - that only ADDS a constraint - but never the reverse.

    A violation costs the SPEEDUP, never the map: the memo forgets and the scan does the work
    again. That is the failure mode to preserve in anything built on this.

    THE LOOKUP HAS TO BE CHEAP, because it runs on every candidate including the ones it does NOT
    save - and the sibling cities above are what that costs when it is not worth paying. `level()`
    hands out the refusal set for one (seat, tightness) so the caller hoists that part of the key
    out of its two nested while loops and pays one small tuple and one set probe per candidate."""

    __slots__ = ("_levels", "_s", "_witness")

    def __init__(self, s: Any) -> None:
        self._s = s
        self._levels: dict[Any, set[Any]] = {}
        self._witness: dict[str, Any] = self._snapshot()

    def _snapshot(self) -> dict[str, Any]:
        """(identity, length, version, appends) per registry. version/appends are None for a plain
        list, where length is the only witness available. `bound` is None until a gen sets it."""
        s = self._s
        w: dict[str, Any] = {}
        for name, v in list(vars(s).items()):
            if isinstance(v, list):
                w["s." + name] = (id(v), len(v), getattr(v, "version", None), getattr(v, "appends", None))
        for key, v in s.M.items():
            if isinstance(v, list):
                w["M." + key] = (id(v), len(v), None, None)
        w["bound"] = None if s.bound is None else (id(s.bound), len(s.bound), None, None)
        return w

    @staticmethod
    def _grew(before: dict[str, Any], after: dict[str, Any]) -> bool:
        """Did every registry we had a witness for grow APPEND-ONLY? A registry that appeared since
        is new keep-out ground, which only ever refuses more, so it needs no witness of its own."""
        for name, was in before.items():
            if was is None:
                continue  # only `bound` is ever None, and unset -> set is a TIGHTENING
            now = after.get(name)
            if now is None or now[0] != was[0] or now[1] < was[1]:
                return False  # registry gone, rebound, or shorter: ground may have been freed
            if was[2] is not None and now[2] - was[2] != now[3] - was[3]:
                return False  # an Indexed registry changed by something that was not an append
        return True

    def sync(self) -> None:
        """Call once at the top of each top-up call - and ONLY there, never mid-scan, because a set
        `level()` already handed out goes on being written to. Re-takes the witness, and forgets
        every refusal if the map did anything but grow since the last one."""
        now = self._snapshot()
        if not self._grew(self._witness, now):
            self._levels.clear()
        self._witness = now

    def level(self, *key: Any) -> set[Any]:
        """The set of (x, y) already refused for one kind of seat at one tightness. `key` must name
        everything the verdict depends on beyond the position itself - the kind AND the footprint
        it was measured at, and the pass's padding - or one pass's refusals will silence another's.
        The caller tests and records positions in it directly; that is the whole hot path."""
        return self._levels.setdefault(key, set())


def boxed_grid(boxed: Any) -> PointGrid:
    """A PointGrid over already-boxed items, for a caller that builds its keep-outs ONCE per region
    and then queries them per scatter point. `boxed_hit`/`boxed_seg_hit` accept the narrowed list
    `near` returns, so switching a linear prefilter to an index is a two-line change at the call
    site and the exact tests underneath are untouched."""
    grid = PointGrid()
    grid.extend(boxed)
    return grid


class PointGrid:
    """A uniform-grid spatial index for POINT queries against many static extents.

    PREFILTER family, like `boxed_hit` one level up: the grid narrows the CANDIDATE LIST, the
    caller's exact test still DECIDES, so verdicts match a linear scan exactly - which is what lets
    the pool regenerate byte-identical when a caller switches over.

    WHY IT EXISTS. A bbox prefilter drops the cost per item but still visits EVERY item, and some
    of this engine's per-candidate scans are long: Minami's well siting probes ~133k seats against
    ~580 watercourse segments plus 927 paddy rings (~123M box comparisons, 74% of that gen), and
    `_fits` measures every candidate against every building already standing. `check_village.py`
    solved exactly this on the CHECKING side with `GridIndex` (whole-pool gate 34.1s -> 11.8s); the
    GENERATOR side had no equivalent until 2026-08-03.

    Items are `(payload..., x0, y0, x1, y1)` - the box is the LAST FOUR fields, the shape
    `boxed_polys` and `boxed_segs` already produce. Filing is INCREMENTAL (`extend` appends), which
    is exact for an append-only registry like `Settlement.placed`, so a growing list is indexed as
    it grows instead of rebuilt.

    A GRID BOX IS A COST, SO IT IS CLAMPED - the lesson recorded in this skill's CLAUDE.md, learned
    when a negative fixture's 9,000,000px vertex asked the checker's index for ~5.6 billion cells
    and the gate ate gigabytes. An item spanning more than `_MAX_SPAN` cells on either axis is
    filed as OVERSIZED and returned by every query. That makes a wild coordinate cheap rather than
    unbounded, and it cannot change a verdict: an oversized item is simply never pruned."""

    __slots__ = ("buckets", "cell", "n", "oversized")
    _MAX_SPAN = 64  # cells per axis before an item is oversized (64 * 128px = 8,192px - wider than any canvas we draw)

    def __init__(self, cell: float = 128.0) -> None:
        self.cell = cell
        self.buckets: dict[tuple[int, int], list[Any]] = {}
        self.oversized: list[Any] = []
        self.n = 0  # items filed so far - an append-only source hands in only the tail

    def extend(self, items: Any) -> None:
        c = self.cell
        for item in items:
            self.n += 1
            i0, j0 = int(item[-4] // c), int(item[-3] // c)
            i1, j1 = int(item[-2] // c), int(item[-1] // c)
            if i1 - i0 > self._MAX_SPAN or j1 - j0 > self._MAX_SPAN:
                self.oversized.append(item)
                continue
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    self.buckets.setdefault((i, j), []).append(item)

    def near(self, px: float, py: float, pad: float = 0.0) -> Any:
        """Every filed item whose box comes within `pad` of (px, py) - plus, harmlessly, some that
        do not, and possibly the same item twice (an item spanning several queried cells). It never
        OMITS one that does, which is the only property the callers' exactness rests on."""
        c = self.cell
        i0, j0 = int((px - pad) // c), int((py - pad) // c)
        i1, j1 = int((px + pad) // c), int((py + pad) // c)
        if i0 == i1 and j0 == j1 and not self.oversized:  # the common case - one cell, no copy
            return self.buckets.get((i0, j0)) or ()
        out: list[Any] = list(self.oversized)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                bucket = self.buckets.get((i, j))
                if bucket:
                    out.extend(bucket)
        return out


# A village runs ~200-500 inhabitants, averaging ~350 (budgets.md). The spread is deliberately NOT a bell
# curve - the tails are only modestly rarer than the mode - so a generated village varies widely in size while
# still clustering on 350. Households = population / 5 (the "dwellings x5" rule). Weights sum to 100.
_VILLAGE_POP_DIST = ((200, 10), (250, 10), (300, 15), (350, 30), (400, 15), (450, 10), (500, 10))


# Ground one HOMESTEAD BUNDLE takes, in real feet, used to size a nucleated cluster's band. The
# bundle's reserved rects come to ~71 x 57 ft; `_fits` then spaces bundles by circumscribed circles
# rather than real footprints, so the effective pitch is larger again. See `roll_village`, which
# explains what the wrong number does and why it does not fail as a shortfall.
BUNDLE_PITCH_FT = 92.0

# How far a CARRIED-WAY deck's corner must stand back from the water it spans, in real feet - the
# floor `bridges_span_their_water` applies to anything that is not a standalone footplank. A real
# abutment sill sits back from the channel edge so scour cannot undercut the bearing.
CARRIED_LANDING_FLOOR_FT = 6.0


def village_population(rng: random.Random) -> int:
    """Draw a village population (200-500, mode 350) from the weighted distribution, using the passed
    random.Random so the draw is DETERMINISTIC from the map seed. Returns the integer population."""
    return rng.choices([p for p, _ in _VILLAGE_POP_DIST], weights=[w for _, w in _VILLAGE_POP_DIST])[0]


def fillet_polyline(pts: Poly, radius: float, steps: int = 6, min_turn_deg: float = 8.0) -> Poly:
    """Round every interior corner of a drawn watercourse, returning a densified polyline (so callers
    keep building plain `M ... L ...` paths and the taper/piece machinery is unaffected).

    WHY (GM 2026-07-25): flowing water in an EARTHEN channel has no mitred corners. A dug ditch that
    changes direction does it on a swept bend, because a sharp corner scours on the outside and silts
    on the inside until the water has rounded it itself - the maintenance crew re-digs the bend, not
    the corner. Sharp corners belong to masonry (a stone-lined aqueduct, a sluice box, a revetted
    canal), and nothing at village/town scale in this setting is lined: these are hand-dug earth
    ditches with grass banks. HOW BIG: an alluvial channel's bend radius runs ~2-3 channel widths
    (Leopold & Wolman's meander geometry), and a dug farm ditch's bend is no tighter, so callers pass
    ~2.5x the drawn width and the bend scales with the ditch instead of being a fixed drawing quirk -
    a big head-race sweeps, a thin lateral turns tight, both at the same real ratio.

    `radius` is the target cut-back along each leg, capped at 35% of either adjacent segment, so two
    neighboring corners can never eat the segment between them (0.35 + 0.35 < 1) and a short offtake
    stub keeps its shape. Corners gentler than `min_turn_deg` are left alone - there is no visible
    elbow to round, and rounding them would only add points."""
    if len(pts) < 3 or radius <= 0:
        return [(float(x), float(y)) for x, y in pts]
    out: Poly = [(float(pts[0][0]), float(pts[0][1]))]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v0, v1 = (p0[0] - p1[0], p0[1] - p1[1]), (p2[0] - p1[0], p2[1] - p1[1])
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-6 or l1 < 1e-6:
            continue  # a repeated vertex bends nothing
        cosang = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (l0 * l1)))
        if 180.0 - math.degrees(math.acos(cosang)) < min_turn_deg:
            out.append((float(p1[0]), float(p1[1])))
            continue
        d = min(radius, 0.35 * l0, 0.35 * l1)
        a = (p1[0] + v0[0] / l0 * d, p1[1] + v0[1] / l0 * d)
        b = (p1[0] + v1[0] / l1 * d, p1[1] + v1[1] / l1 * d)
        for s in range(steps + 1):  # quadratic bend, the corner itself as the control point
            t = s / steps
            mt = 1 - t
            out.append((mt * mt * a[0] + 2 * mt * t * p1[0] + t * t * b[0], mt * mt * a[1] + 2 * mt * t * p1[1] + t * t * b[1]))
    out.append((float(pts[-1][0]), float(pts[-1][1])))
    return out


def smooth_closed(pts: Poly) -> str:
    n = len(pts)
    d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    return d + 'Z'


def smooth_points(pts: Poly, steps: int = 10) -> Poly:
    """Sample the rendered (Catmull-Rom) boundary so the manifest matches what's
    drawn - the curve bows inward of the raw vertices (a hard-won lesson)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        for s in range(steps):
            t = s / steps
            mt = 1 - t
            x = mt**3 * p1[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * p2[0]
            y = mt**3 * p1[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * p2[1]
            out.append((round(x, 1), round(y, 1)))
    return out


def region_blocked(quad: Poly, circles: Sequence[tuple[float, float, float]], halo: Sequence[tuple[float, float, float]], lines: Sequence[tuple[Any, float]], polys: Sequence[Poly]) -> bool:
    """Does a cell REGION meet any keep-out? Circles by distance-to-region, stroked lines by
    segment-to-region, polygons by containment-or-crossing.

    Factored out of near_ring_cropland so it can be tested directly: the bug it exists to stop is a
    keep-out that sits against the middle of a cell EDGE, touching neither the cell's center nor any
    of its corners, which is how a wellhead ended up 1 px inside a hatake plot with every sample
    point clear."""
    if any(point_quad_dist(cx, cy, quad) < r for cx, cy, r in circles):
        return True
    if any(point_quad_dist(cx, cy, quad) < r for cx, cy, r in halo):
        return True
    if any(quad_hits_seg(quad, pl[i], pl[i + 1], hw) for pl, hw in lines for i in range(len(pl) - 1)):
        return True
    return any(quad_hits_poly(quad, gp) for gp in polys)


def quad_hits_poly(quad: Poly, poly: Poly) -> bool:
    """Does a convex cell REGION meet an arbitrary polygon? Containment either way, plus edge
    crossings - so a polygon threading between the cell's sample points is still caught."""
    if any(point_in_poly(qx, qy, poly) for qx, qy in quad):
        return True
    if any(point_in_poly(px, py, quad) for px, py in poly):
        return True
    for i in range(len(quad)):
        a, b = quad[i], quad[(i + 1) % len(quad)]
        for j in range(len(poly)):
            c, d = poly[j], poly[(j + 1) % len(poly)]
            if segments_cross(a, b, c, d):
                return True
    return False


def point_quad_dist(px: float, py: float, quad: Poly) -> float:
    """Distance from a point to a convex cell region; 0 inside it."""
    if point_in_poly(px, py, quad):
        return 0.0
    return min(seg_dist(px, py, quad[i], quad[(i + 1) % len(quad)]) for i in range(len(quad)))


def quad_hits_seg(quad: Poly, a: Pt, b: Pt, hw: float) -> bool:
    """Does a stroked line (segment + half-width) meet a cell region? Tests the SEGMENT against the
    cell's edges, not just its corners - a ditch crossing the middle of a cell touches no corner."""
    if point_quad_dist(a[0], a[1], quad) < hw or point_quad_dist(b[0], b[1], quad) < hw:
        return True
    for i in range(len(quad)):
        c, d = quad[i], quad[(i + 1) % len(quad)]
        if segments_cross(a, b, c, d):
            return True
        if seg_dist(c[0], c[1], a, b) < hw or seg_dist(d[0], d[1], a, b) < hw:
            return True
    return False


def rot_rect(cx: float, cy: float, w: float, h: float, deg: float = 0.0) -> Poly:
    """The four corners of a (possibly rotated) footprint - the shape most placement tests want."""
    th = math.radians(deg or 0.0)
    c, sn = math.cos(th), math.sin(th)
    return [(cx + dx * c - dy * sn, cy + dx * sn + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def poly_gap(p: Poly, q: Poly) -> float:
    """The true gap in px between two convex quads - 0.0 if they overlap or touch.

    For two non-intersecting convex polygons the closest approach always involves a vertex of one
    and an edge of the other, so the four vertex-to-edge minima are exact, not an approximation."""
    if rects_overlap(p, q):
        return 0.0
    best = 1e18
    for a, b in ((p, q), (q, p)):
        for vx, vy in a:
            for i in range(len(b)):
                best = min(best, seg_dist(vx, vy, b[i], b[(i + 1) % len(b)]))
    return best


def _aabb_gap(p: Poly, q: Poly) -> float:
    """The gap between two quads' AXIS-ALIGNED bounds - 0 where the bounds meet or overlap.

    Deliberately the coarse measure, because it is the one `city_government_offices_dont_abut`
    uses: that check reads AABBs, so a placement probe that guards the same standoff has to read
    AABBs too or the two disagree exactly where a feature is drawn at an angle."""
    ax0, ay0, ax1, ay1 = min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)
    bx0, by0, bx1, by1 = min(x for x, _ in q), min(y for _, y in q), max(x for x, _ in q), max(y for _, y in q)
    return math.hypot(max(0.0, ax0 - bx1, bx0 - ax1), max(0.0, ay0 - by1, by0 - ay1))


def rects_overlap(p: Poly, q: Poly) -> bool:
    """Separating-axis overlap for two convex quads (corner lists)."""
    for poly in (p, q):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = -(y2 - y1), (x2 - x1)
            pa = [nx * x + ny * y for x, y in p]
            qa = [nx * x + ny * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


def organic_bbox(bbox: Any, amp: float, flat_edges: tuple[int, ...] = ()) -> Poly:
    """Semi-rectangular core with lobes (outgrowths) and bays (indentations).
    Edges listed in flat_edges (0=N, 1=E, 2=S, 3=W) are kept straight - e.g. a field
    that must run flush against a town wall flattens the abutting edge."""
    x0, y0, x1, y1 = bbox
    edges = [((x0, y0), (x1, y0), (0, -1)), ((x1, y0), (x1, y1), (1, 0)), ((x1, y1), (x0, y1), (0, 1)), ((x0, y1), (x0, y0), (-1, 0))]
    pts = []
    for ei, (sa, sb, (nx, ny)) in enumerate(edges):
        for i in range(4):
            t = i / 4
            bx, by = sa[0] + (sb[0] - sa[0]) * t, sa[1] + (sb[1] - sa[1]) * t
            off = random.uniform(-amp * 0.5, amp)
            jt = random.uniform(-amp * 0.18, amp * 0.18)  # consume RNG even when flat, to keep placement aligned
            if ei in flat_edges:
                pts.append((bx, by))
                continue
            if i == 0:
                off *= 0.35
            pts.append((bx + nx * off + jt, by + ny * off + jt))
    return pts


def organic_poly(base: Poly, amp: float) -> Poly:
    """Organic-ize an arbitrary base polygon (handles concave shapes like a V):
    densify each edge and jitter the samples; smoothing rounds it."""
    pts = []
    n = len(base)
    for i in range(n):
        ax, ay = base[i]
        bx, by = base[(i + 1) % n]
        segs = max(1, int(math.hypot(bx - ax, by - ay) / 150))
        for s in range(segs):
            t = s / segs
            pts.append((ax + (bx - ax) * t + random.uniform(-amp, amp) * 0.5, ay + (by - ay) * t + random.uniform(-amp, amp) * 0.5))
    return pts


def winding(start: Pt, end: Pt, amp: float = 15, n: int = 2) -> Poly:
    """A gently winding path from start to end (a shallow S, not a straight line)."""
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(float(sx), float(sy))]
    for k in range(1, n + 1):
        t = k / (n + 1)
        off = amp * (1 if k % 2 else -1)
        pts.append((round(sx + dx * t + nx * off, 1), round(sy + dy * t + ny * off, 1)))
    pts.append((float(ex), float(ey)))
    return pts
