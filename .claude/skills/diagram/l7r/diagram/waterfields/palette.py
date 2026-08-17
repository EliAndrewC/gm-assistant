"""Layer-0 palette and parcels: paddy/crop colors, the real-feet paddy-cell calibration (paddy_grain), aze width, organic dry-crop parcel outlines."""

import math
import random

from .frame import Poly, Pt

# ---- PADDY CELL SIZE (the real-feet calibration; GM 2026-07-22) --------------------------------
# One DRAWN plot is a single leveled, diked paddy cell - and because a paddy must hold water at an
# EVEN depth, that cell is physically small. This is the researched real-world target for it, so the
# same real size renders at every map scale instead of being hand-set in pixels per map (which made
# an identical px grain read as 4x different real area between a 1 ft/px hamlet and a 2 ft/px village).
#
# WHY 0.05 acre (~200 m2, ~47 ft square) - China-first, Japan corroborating:
#   - Francesca Bray, The Rice Economies: a leveled paddy "twenty yards square [~0.083 acre / 335 m2]
#     would be considered large" - that is the CEILING for one cell, typical valley cells smaller.
#   - J.L. Buck, Land Utilization in China (16,786 farms, 1929-33): avg ~0.06 ha (0.15 ac) OWNERSHIP
#     plots - but a plot subdivides into several leveled cells on any slope, so the cell sits below it.
#   - Japanese se (畝) = 100 m2 (0.025 ac) is the small-paddy unit (floor); tan (段, ~0.245 ac) is a
#     TAX/allotment unit, not one leveled field.
#   0.05 ac sits mid-band (above the se floor, well under Bray's ceiling) and keeps a drawn plot ~1.7x
#   the 46x28 ft (1,288 ft2) farmhouse glyph, so a paddy still visibly outsizes a farmhouse.
# DELIBERATELY NOT applied to hamlets/towns: they already render ~0.034-0.057 ac (in-band); only the
# villages (~0.13 ac, over Bray's ceiling) and cities (~0.08 ac, at it) ran large and are pulled down.
# The population/household invariant is untouched: this subdivides the SAME field envelope into more,
# smaller cells - total paddy area, farmhouse rings, and the household count are all unchanged. See
# settlements.md 'Paddy cell size'.
PADDY_CELL_ACRES = 0.05


def paddy_grain(ftpx: float, target_acres: float = PADDY_CELL_ACRES, aspect: float = 0.66, spread: float = 0.16) -> tuple[float, tuple[float, float]]:
    """`(plot_across, row_step)` in PIXELS that carve a ~`target_acres` leveled cell at this map's `ftpx`.
    Derived as target_area / ftpx^2 (a real-feet target, so every scale matches), split into an
    across-canal x along-canal cell of the given `aspect` (= along/across; 0.66 is the mild
    across-elongation the GM-vetted village paddies already read as). `row_step` is (min, max) at
    +/-`spread` around the along mean, carrying the organic row variation. This is THE paddy-size
    calibration lever - one real-feet target in, consistent paddy size out, replacing hand-set px."""
    target_px2 = target_acres * 43560.0 / (ftpx * ftpx)
    across = math.sqrt(target_px2 / aspect)
    along = aspect * across
    return round(across, 1), (round(along * (1 - spread), 1), round(along * (1 + spread), 1))


# A rice field is ONE crop at ONE transplant/growth stage, so its body is a UNIFORM green - the plot-to-plot
# shade jitter denoted nothing (it was only anti-flatness texture), and the GM asked for it uniform. The bund
# network + footpaths carry the structure, not color. Kept as a 3-element list of the SAME value so R.choice
# consumes the RNG stream IDENTICALLY to the old 3-shade version - the field geometry + the meaningful FLOODED
# drain-plots stay byte-for-byte unchanged; only the body color goes uniform. (The MEANINGFUL colors remain:
# FLOODED blue-green for the low plots that sit on the drain, and RIPE_GOLD, when a map uses it.)
_RICE_GREEN = '#A6C398'
RICE_GREENS = [_RICE_GREEN, _RICE_GREEN, _RICE_GREEN]
FLOODED = '#93B7AC'
RIPE_GOLD = '#C9BA79'
BUND = '#C2A772'
# AZE: the paddy plot-boundary stroke, split from BUND (GM 2026-07-24). BUND stays the broad
# exposed-earth AREA fill (perimeter dikes, dike-top house pads - true-width earthworks); AZE is
# the LINE between paddies: the puddled-mud ridge (aze / tiangeng) re-plastered each spring
# (azenuri) to seal the basin. A plain aze ran ~1-2 ft wide and ~1 ft high (walking bunds,
# azemichi, 2-5 ft), so AZE_FT below draws it near TRUE scale instead of the old 1.7-2.6 px
# tan (~3-5 ft at village grain) - a dark line stays legible at half the width where the light
# tan needed inflation. The hue is the GM's pick from a 5-color ladder rendered on Hoshigaoka
# (2026-07-24): red-leaning dark mud, chosen over the lighter chestnut #7A5230 that reads more
# nameably "brown" at hairline width - at map view this dark a line blends toward black against
# the rice green, and the GM preferred that weight. Accuracy
# is deliberately mixed: the color is honest for SPRING (fresh azenuri mud); by high summer -
# the season the paddy surfaces depict - real bunds green over with grass and azemame and all
# but vanish, so a dark visible bund network is a stylization that keeps the field structure
# readable. See settlements.md 'Paddy plot grain'.
AZE = '#6E4520'
AZE_FT = 1.5  # drawn aze width in real feet; convert at the map's ftpx, floored for raster visibility


def aze_w(ftpx: float) -> float:
    """Paddy bund stroke width in px at this map's scale: AZE_FT real feet, floored at 0.5 px
    so the city scale (3 ft/px) keeps a faint-but-present line instead of vanishing."""
    return max(AZE_FT / ftpx, 0.5)


BEAN_GREEN = '#2F6B35'  # azemame (bund soybeans) - the beaded-bund accent. Deep PINE green
# (GM 2026-08-15): the old olive #7C9A4E sat between the rice green and the bund brown and read as
# neither - the beads were nearly invisible at map zoom. A glyph rendering convention, not botany
# (real soybean foliage is lighter): dark enough to punch against the pale rice, green enough to
# still read as a plant against the near-black bund stroke. Picked from a 3-color ladder rendered
# on Inashiro (hunter #355E3B grayed out, forest #1F4A28 read as black).


# HAND-PILED EARTHWORK IS NEVER RULED (GM 2026-07-24). A farmer building a rectangular basin out of
# puddled mud INTENDS four straight sides and a right angle at each corner, and gets neither. Two
# separate physical reasons, and both are worth drawing:
#   - CORNERS ROUND. A right angle in soft earth cannot stand: the apex is the thinnest, least
#     supported point of the ridge, it slumps under its own weight and under every rain, and it is
#     the one spot on the bund that every person, ox, and carrying-pole cuts across rather than
#     walking to the point. Re-plastering (azenuri) each spring restores the ridge, not the geometry,
#     so the corner converges on a walked-and-slumped curve of a few feet' radius. This is the same
#     argument `Settlement._rounded_pond` already makes for the dug fish ponds - it applies to every
#     earthwork the farmers piled, not just the ones holding fish.
#   - EDGES WANDER. A bund is paced and eyeballed between two corners, re-cut a little differently
#     every year as parcels are split, sold, and re-plastered, so a "straight" 100 ft run bows by a
#     foot or two. It is straight in intent and to the eye at a distance, not to the ruler.
# The dead-straight, sharp-cornered cell is the machine-cut signature of 20th-century consolidation
# (Japan's 1963 hojo seibi), the same anachronism `polder_parcels_vary` and `polder_edges_wander`
# already guard at the fabric and block scale - this is that same rule at the level of the single
# parcel outline. Teeth: `polder_parcels_are_organic`. See settlements.md 'Polder fifth pass'.
def organic_parcel(
    poly: Poly,
    rng: random.Random,
    fillet: float,
    bow: float,
    bow_cap: float,
    arc: int = 5,
    bows: int = 3,
) -> Poly:
    """Soften a ruled parcel quad into a hand-piled one: fillet every corner with a quadratic bezier
    of jittered reach (`fillet` px, the walked-and-slumped corner radius) and bow each straight run
    by a half-sine of amplitude `bow` x its length, capped at `bow_cap` px. Returns a SAMPLED polygon
    (not a path), so every downstream consumer - the manifest record, the point-in-poly checks, the
    dike-pond overlay - keeps working on an ordinary polygon; `arc`/`bows` set the sampling density.

    `bow_cap` is the caller's guarantee that two neighbouring parcels cannot bow into each other: it
    must leave a positive gap given the inset the caller applied, or the drawn bunds would touch."""
    n = len(poly)
    if n < 3:
        return list(poly)

    def toward(frm: Pt, to: Pt, dist: float) -> Pt:
        vx, vy = to[0] - frm[0], to[1] - frm[1]
        ln = math.hypot(vx, vy) or 1.0
        dd = min(dist, ln * 0.42)  # never eat more than the edge can spare, so slivers stay valid
        return (frm[0] + vx / ln * dd, frm[1] + vy / ln * dd)

    reach: list[float] = []  # each corner's own (smaller) leg, which sets how much its arc may be roughed
    a_in: Poly = []  # the point on the INCOMING edge where corner i's fillet starts
    b_out: Poly = []  # ...and on the outgoing edge where it ends
    for i in range(n):
        # Reach is drawn INDEPENDENTLY for the two legs of each corner, not once per corner: a corner
        # slumps toward whichever side is walked, loaded, or under-plastered, so the curve runs further
        # down one bund than the other. A single symmetric reach per corner is what makes a filleted
        # rectangle read as a drawn-on border-radius instead of as earth.
        #
        # The SPREAD is the whole point (GM 2026-07-25, on the first version: "it just kind of looks
        # like you put a circle at each intersection, which actually makes it look less natural").
        # A tight band of reaches gives every corner the same radius, so four parcels rounding away
        # from one junction cut a clean disc out of it, and a repeated identical mark reads as a stamp
        # - MORE machine-made than the sharp corner it replaced. The physical truth is that corners
        # differ enormously: the one on the walked side is worn to a broad sweep while the one behind
        # a neighbour's bund keeps almost its full angle for years. So the reach is drawn from a WIDE
        # triangular distribution - a long tail up to ~2.2x, a floor near 0.12x that leaves a corner
        # all but square - and the arc itself is roughed below, since a mathematically clean curve is
        # the other half of what reads as stamped.
        ra, rb = fillet * rng.triangular(0.12, 2.2, 0.7), fillet * rng.triangular(0.12, 2.2, 0.7)
        reach.append(min(ra, rb))
        a_in.append(toward(poly[i], poly[(i - 1) % n], ra))
        b_out.append(toward(poly[i], poly[(i + 1) % n], rb))
    out: Poly = []
    for i in range(n):
        # roughness scales with THIS corner's own reach, never the global fillet: on a corner drawn
        # nearly square the arc spans under a pixel, and a fixed-size wobble there is bigger than the
        # arc itself - the samples scatter instead of curving, folding the outline back on itself into
        # spikes (measured: turns of 180 degrees, and a visible burr on the render)
        rough = reach[i] * 0.18  # the arc is a slumped mud shoulder, not a drafted curve
        # Sample density follows the SIZE of the arc. A corner drawn nearly square spans a fraction of
        # a pixel; cutting that into six samples puts them 0.2 px apart, where the roughness above (or
        # plain float noise) reverses the direction of travel and the outline grows a burr. So a big
        # sweep gets the full sampling and a tight corner gets a single midpoint - which is also the
        # honest record of what it is, a corner that never really rounded.
        steps = max(1, min(arc, int(reach[i] * 0.8)))
        for k in range(steps + 1):  # the corner arc: a_in[i] -> control poly[i] -> b_out[i]
            f = k / steps
            w0, w1, w2 = (1 - f) ** 2, 2 * (1 - f) * f, f * f
            jx = rough * rng.uniform(-1, 1) * math.sin(math.pi * f)  # pinned at both ends so the arc still meets its runs
            jy = rough * rng.uniform(-1, 1) * math.sin(math.pi * f)
            out.append((w0 * a_in[i][0] + w1 * poly[i][0] + w2 * b_out[i][0] + jx, w0 * a_in[i][1] + w1 * poly[i][1] + w2 * b_out[i][1] + jy))
        p0, p1 = b_out[i], a_in[(i + 1) % n]  # the straight run to the next corner - it WANDERS, not bows
        ex, ey = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(ex, ey) or 1.0
        # ...and the run's wander is likewise bounded by the run's OWN length. With a long fillet tail
        # the straight part between two corners can be a stub a pixel long, and a wander sized for a
        # 100 ft bund applied across it is another way to fold the outline into a spike.
        amp = min(bow * ln, bow_cap, ln * 0.1)
        for k in range(1, bows + 1):
            f = k / (bows + 1)
            # each sample offsets independently, so the run reads as re-cut-by-eye rather than as one
            # clean arc; the sin() taper still pins both ends on the fillet so the corners meet exactly
            d = amp * rng.uniform(-1.0, 1.0) * math.sin(math.pi * f)
            out.append((p0[0] + ex * f - ey / ln * d, p0[1] + ey * f + ex / ln * d))
    return out


# DRY-FIELD (hatake) crops on ground the irrigation cannot command - the upslope margin
# above the supply canal. Each: fill + furrow-line color (dry crops are ridge-cultivated).
DRY_CROPS = {
    "barley": ("#CDB86A", "#B49E52"),  # mugi - tan-gold
    "millet": ("#C6A64A", "#AD8C36"),  # awa/kibi - ochre
    "buckwheat": ("#D3C2A6", "#C69C86"),  # soba - pale, reddish stems
    "soy": ("#A9B36A", "#8E9A50"),  # daizu as a field crop - soybean green
}
