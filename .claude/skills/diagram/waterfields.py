#!/usr/bin/env python3
"""Water-first paddy engine (warp threads) for the /diagram settlement maps.

THE INVERSION (why this module exists): fields are grown AROUND the water network, never
the other way round. The generator lays the irrigation skeleton first - one pond sluice, a
head-race, supply canals along the HIGH margins, delivery ditches dropping downhill - and
the paddy plots are carved BETWEEN those lines, so the map cannot help but communicate the
hydrology. The old approach (draw a field blob, decorate it with water) reads as random no
matter how it is tuned; see settlements.md 'Water-first fields v2' for the full grounding.

ENGINE: every plot-column boundary is a warp THREAD marched downhill in lockstep fall-steps,
clamped so threads can never cross and never pinch closer than one plot width (GAP). The
blue delivery ditch is just a thread's dug PREFIX; below it the same line continues as a
plain bund. Offtakes SPAWN from their parent thread mid-march, so they always take off
exactly on the parent's real path. Crossings and orphan ditches are impossible by
construction - the geometry is validated by how it is built, not by post-hoc repair.

SLOPE IS A KNOB, NOT A CONSTANT: everything is computed in the contour(u)/fall(f) frame
derived from `down_deg` (screen angle of the downhill direction). Kikuta is NW-high
(down_deg=45, i.e. SE); southern Lion lands slope south-to-north (down_deg=-90 -> N is a
future case); Dragon the reverse; Unicorn east-flowing. Nothing in the thread march or the
plot carve assumes SE. (The drain and the supply canals are given headings RELATIVE to
`down_deg`, so the whole system rotates together.)

Returns plain data (channels, plots, stats); the caller draws SVG via Settlement. RNG is a
LOCAL random.Random(seed) so field generation never ripples other features' placement.
"""

import math
import random
from collections.abc import Callable, Sequence
from typing import Any

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points

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

DF = 30.0  # fall step of the lockstep march (px)
GAP = 26.0  # threads never pinch closer than this - a plot must fit between them

# THE COLLECTOR'S DRAWN WIDTH at its head and at its outfall (both x grain). The akusui GATHERS the
# plots' tail-water as it crosses the low side, so it is the mirror of the supply taper - the long
# note at the `role: "drain"` channel append carries the hydraulic-vs-maintenance argument for 1.5.
# Named, rather than written twice, because `_drain_bank` has to know the same two numbers: the
# paddies' bottom bunds are laid against the ditch's EDGE, and an edge nothing can compute is an
# edge the carve draws straight through.
DRAIN_W_HEAD = 1.5
DRAIN_W_TAIL = 6.0


class _Frame:
    """Contour/fall frame for an arbitrary downhill screen angle."""

    def __init__(self, down_deg: float) -> None:
        a = math.radians(down_deg)
        self.down: float = a
        self.d: Pt = (math.cos(a), math.sin(a))  # fall unit (downhill)
        self.c: Pt = (math.sin(a), -math.cos(a))  # contour unit (90 deg left of fall)

    def to_uf(self, x: float, y: float) -> Pt:
        return (x * self.c[0] + y * self.c[1], x * self.d[0] + y * self.d[1])

    def to_xy(self, u: float, f: float) -> Pt:
        return (u * self.c[0] + f * self.d[0], u * self.c[1] + f * self.d[1])


class _Thread:
    """One plot-column boundary marched down the fall line."""

    def __init__(
        self,
        u: float,
        f: float,
        drift: float,
        ditch_f: float,
        decay: float = 110.0,
        fallback: Poly | _Thread | None = None,
    ) -> None:
        self.u0, self.f0 = u, f
        self.u = u
        self.drift = drift  # du/df at takeoff (from the ditch's dug heading)
        self.decay = decay  # fall-distance over which drift relaxes to 0
        self.ditch_f = ditch_f  # dug-ditch prefix ends at this f (plain bund below)
        self.fallback = fallback  # boundary path ABOVE the takeoff (parent canal/thread)
        self.pts: Poly = []
        self.f_end: float | None = None
        self.spawn_sub: bool = False  # set True on interior blocks that split once
        self.offtake_fs: list[float] = []  # falls at which this canal spawns offtakes

    def step(self, f: float, R: random.Random) -> float:
        k = math.exp(-max(0.0, f - self.f0) / self.decay)
        return self.u + (self.drift * k + R.uniform(-0.10, 0.10)) * DF


def _at_f(F: _Frame, pts: Poly, f: float) -> Pt:
    """Point on a fall-monotone polyline at fall f (clamped at the ends)."""
    if f <= F.to_uf(*pts[0])[1]:
        return pts[0]
    for i in range(len(pts) - 1):
        fa, fb = F.to_uf(*pts[i])[1], F.to_uf(*pts[i + 1])[1]
        if fa <= f <= fb and fb > fa:
            k = (f - fa) / (fb - fa)
            return (pts[i][0] + k * (pts[i + 1][0] - pts[i][0]), pts[i][1] + k * (pts[i + 1][1] - pts[i][1]))
    return pts[-1]


def _f_at_u(F: _Frame, pts: Poly, u: float) -> float | None:
    """Fall of a u-monotone polyline at contour coordinate u (clamped; None outside range)."""
    us = [F.to_uf(*p)[0] for p in pts]
    if not (min(us[0], us[-1]) - 20 <= u <= max(us[0], us[-1]) + 20):
        return None
    for i in range(len(pts) - 1):
        ua, ub = us[i], us[i + 1]
        if (ua <= u <= ub or ub <= u <= ua) and ub != ua:
            k = (u - ua) / (ub - ua)
            fa, fb = F.to_uf(*pts[i])[1], F.to_uf(*pts[i + 1])[1]
            return fa + k * (fb - fa)
    # off either end (within the gate slack): clamp to the NEARER end - clamping to the far
    # end returned its fall for points near the START, falsely suppressing a mid-field band
    near = pts[0] if abs(u - us[0]) <= abs(u - us[-1]) else pts[-1]
    return F.to_uf(*near)[1]


def _seg_x(a: Pt, b: Pt, c: Pt, d: Pt) -> Pt | None:
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (a[0] + t * r[0], a[1] + t * r[1])
    return None


def _drain_bank(F: _Frame, dpts: Poly, g: float) -> Callable[[float], float]:
    """Return `bank(u)`: how far ABOVE the collector's centerline, IN FALL, a paddy bund must stop.

    A paddy's low bund IS the collector's top-of-bank - the two touch - so the drawn bund line
    belongs at the EDGE of the ditch's stroke, never on its centerline. Until 2026-08-08 the carve
    held off by a flat `2 * g` everywhere, which is INSIDE the stroke over most of the collector's
    run (it widens `DRAIN_W_HEAD * g` -> `DRAIN_W_TAIL * g` downstream, so the half-width alone
    reaches `3 * g`): the field's bottom bunds were drawn under the blue ditch with the paddy fill
    poking out the far side. That is half of the GM's "the earthen bunds overlap with the drainage
    ditch" on Hoshizora - the other half was the HEM PASS laying its quads on the contour, fixed
    there.

    Two conversions, both cheap and both wrong to skip:

      - the ditch TAPERS, so the clearance has to taper with it. A constant is either inside the
        stroke at the outfall or a visible bare stripe at the head, and which one you get depends
        on the map's grain, which is the worst way for a number to be wrong.
      - fall is not perpendicular distance. The collector is fitted as `f = a + b*u`, i.e. it runs
        at atan(b) to the contour, so holding off by `c` perpendicular costs `c * hypot(1, b)` of
        FALL. The fit clamps `b` to <= 0.35, so this is <= 6% - small, but free to be exact.

    The extra `0.75 * g` is half the drawn bund stroke (`aze_w`, ~1.5 real ft), so the bund and the
    ditch ABUT at the bank rather than overlapping by half a line width."""
    uf = [F.to_uf(*p) for p in dpts]
    us = [q[0] for q in uf]
    u_lo, u_hi = min(us), max(us)
    span = (u_hi - u_lo) or 1.0
    # The fall->perpendicular conversion is taken from the LOCAL segment, not from a head-to-outfall
    # fit: the collector wanders, and the gate measures a bund against the segment it actually
    # stands on (`drain_bank_clearance`). A global slope disagrees with that by a few percent, which
    # is a fraction of a pixel - and a fraction of a pixel is exactly enough to make a bund the
    # engine laid ON the bank read as a bund inside the ditch.
    segs = []
    for i in range(len(uf) - 1):
        du = uf[i + 1][0] - uf[i][0]
        segs.append((min(uf[i][0], uf[i + 1][0]), max(uf[i][0], uf[i + 1][0]), math.hypot(1.0, abs((uf[i + 1][1] - uf[i][1]) / du) if du else 0.0)))

    def bank(u: float) -> float:
        t = max(0.0, min(1.0, (u - u_lo) / span))
        half = (DRAIN_W_HEAD + (DRAIN_W_TAIL - DRAIN_W_HEAD) * t) * g / 2
        slope = next((s for lo, hi, s in segs if lo <= u <= hi), segs[0][2] if u <= u_lo else segs[-1][2])
        return (half + BANK_MARGIN * g) * slope

    return bank


BANK_MARGIN = 0.75  # half a drawn bund stroke (aze_w is ~1.5 real ft), so bund and ditch ABUT rather than overlap


def polyline_cum(pts: Poly) -> list[float]:
    """Cumulative arc length at each vertex - hoisted so a caller testing many points against one
    collector pays for it once."""
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.dist(pts[i], pts[i + 1]))
    return cum


def drain_bank_clearance(q: Pt, dpts: Poly, dv: Pt, w0: float, w1: float, cum: list[float]) -> tuple[float, float, float, bool]:
    """How one point stands against a drainage collector: `(gap, need, lean, past)`.

    - `gap` - SIGNED perpendicular offset from the nearest segment, positive on the FIELD's side of
      the ditch (the side the fall comes from), negative once the point is across the centerline.
    - `need` - the bank: half the collector's DRAWN width at that point (it tapers `w0` -> `w1`
      along its length) plus `BANK_MARGIN`, so a bund's own stroke abuts the ditch's rather than
      overlapping it.
    - `lean` - how much clearance one unit of UP-FALL travel buys. It is ~0 for a collector running
      with the fall, where "lift it up-fall" is not a move that helps.
    - `past` - the point projects beyond the collector's head or tail. That ground drains somewhere
      else (the next fan, the map edge), so this collector does not govern it.

    ONE predicate, shared by the generator (`hem_to_bank`) and by the gate
    (`paddy_bunds_clear_the_collector`), because a placer and a checker that classify the same
    ground from two separate formulas drift apart - the trap the diagram CLAUDE.md records under
    'Placement and its check must read the SAME manifest source'."""
    off, cx, cy, arc, past, nrm = 1e9, 0.0, 0.0, 0.0, False, (0.0, 0.0)
    for i in range(len(dpts) - 1):
        ax, ay = dpts[i]
        vx, vy = dpts[i + 1][0] - ax, dpts[i + 1][1] - ay
        t = ((q[0] - ax) * vx + (q[1] - ay) * vy) / ((vx * vx + vy * vy) or 1.0)
        tc = max(0.0, min(1.0, t))
        sx, sy = ax + tc * vx, ay + tc * vy
        d = math.hypot(q[0] - sx, q[1] - sy)
        if d < off:
            off, cx, cy = d, sx, sy
            arc = cum[i] + tc * math.hypot(vx, vy)
            past = (i == 0 and t < 0.0) or (i == len(dpts) - 2 and t > 1.0)
            nl = math.hypot(vx, vy) or 1.0
            nx, ny = -vy / nl, vx / nl
            nrm = (nx, ny) if nx * dv[0] + ny * dv[1] < 0 else (-nx, -ny)  # points UP-fall, off the ditch
    gap = (q[0] - cx) * nrm[0] + (q[1] - cy) * nrm[1]
    need = (w0 + (w1 - w0) * arc / (cum[-1] or 1.0)) / 2 + BANK_MARGIN
    return gap, need, -(dv[0] * nrm[0] + dv[1] * nrm[1]), past


def supply_bank_clearance(q: Pt, pts: Poly, w0: float, w1: float, cum: list[float]) -> tuple[float, float, bool, Pt, Pt]:
    """How one point stands against a SUPPLY channel's drawn stroke: `(gap, halfw, past, foot, nrm)`.

    The supply half of `drain_bank_clearance`, and simpler for a reason: a drain-side bund is held
    off IN FALL (the hem climbs up its own column, so that verdict needs the fall geometry), while
    a supply-side bund runs ALONGSIDE its channel and is held off PERPENDICULAR - the bund is the
    channel's bank wherever the channel goes, which is also what makes the bordering bund run
    parallel to the water (GM 2026-08-15).

    - `gap` - unsigned perpendicular distance from `q` to the nearest stroke segment.
    - `halfw` - half the stroke's DRAWN width at that point (`w0` -> `w1` taper along its arc).
    - `past` - `q` projects beyond the stroke's head or tail; ground beyond the span is not
      governed by this stroke (a delivery ditch's takeoff sits on its parent canal, which governs).
    - `foot` - the nearest point on the centerline.
    - `nrm` - the nearest segment's unit normal, side arbitrary; the caller orients it.

    ONE predicate, shared by the placer (`_carve`'s `clear_supply`) and by the gate
    (`paddy_bunds_clear_the_supply_channels`), for the same reason `drain_bank_clearance` is: a
    placer and a checker that classify the same ground from two formulas drift into disagreeing
    about which side of a ditch a point is on."""
    off, foot, arc, past, nrm = 1e9, (0.0, 0.0), 0.0, False, (0.0, 1.0)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        vx, vy = pts[i + 1][0] - ax, pts[i + 1][1] - ay
        t = ((q[0] - ax) * vx + (q[1] - ay) * vy) / ((vx * vx + vy * vy) or 1.0)
        tc = max(0.0, min(1.0, t))
        sx, sy = ax + tc * vx, ay + tc * vy
        d = math.hypot(q[0] - sx, q[1] - sy)
        if d < off:
            off, foot = d, (sx, sy)
            arc = cum[i] + tc * math.hypot(vx, vy)
            past = (i == 0 and t < 0.0) or (i == len(pts) - 2 and t > 1.0)
            nl = math.hypot(vx, vy) or 1.0
            nrm = (-vy / nl, vx / nl)
    halfw = (w0 + (w1 - w0) * arc / (cum[-1] or 1.0)) / 2
    return off, halfw, past, foot, nrm


def hem_to_bank(ring: Poly, dpts: Poly, down_deg: float, w0: float, w1: float) -> Poly:
    """Lift any vertex of `ring` that lies inside the collector's drawn stroke - or past its
    centerline - up-fall onto the ditch's BANK. Returns a new ring; vertices already clear are
    returned untouched.

    `build_comb` needs none of this: it hems onto the bank BY CONSTRUCTION (see `_drain_bank`). The
    other three field engines lay their parcels against a drain they build afterwards, so they have
    no such handle, and the check that caught the comb's defect caught the same class in all three
    (2026-08-08). Each was a different flavor of the one error:

      - TERRACES: the last terrace's toe is a WIGGLY contour (amp + phase) while the collector along
        the foot is a STRAIGHT descending line, so the two cross. Tanada's toe bund - the thick
        retaining lip, drawn separately from the plots - ran ~8 px below the ditch, which is the
        defect at its most visible: a retaining wall standing in the drain.
      - RIBBON: the bands end exactly AT the foot, i.e. on the drain's centerline (measured offset
        0.00 px on every flagged vertex), so the field's bottom bund is drawn under the ditch.
      - POLDER: the collector IS the polder's bottom side, so the parcels front it directly and
        float error alone put a vertex a half-pixel past.

    This is a terminal pass rather than a construction change in three engines, and that is a
    deliberate trade: it enforces one physical invariant (a basin's wall cannot stand in the ditch)
    on geometry those engines have finished with, in the same spirit as the comb's own terminal
    thin-plot drop. The move is along the FALL, so a lifted vertex slides up its own column and the
    parcel keeps its shape."""
    dv = (math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg)))
    cum = polyline_cum(dpts)
    out: Poly = []
    for q in ring:
        gap, need, lean, past = drain_bank_clearance(q, dpts, dv, w0, w1, cum)
        if past or gap >= need or lean < 0.2:  # clear, off the collector's span, or a drain running WITH the fall
            out.append(q)
            continue
        shift = (need - gap) / lean
        out.append((round(q[0] - dv[0] * shift, 1), round(q[1] - dv[1] * shift, 1)))
    return out


def _seg_d(px: float, py: float, a: Pt, b: Pt) -> float:
    """Distance from a point to a segment (the same arithmetic several passes nest as a local
    `sd`; module-level here because _bund_beans' burial filter needs it too)."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    ll = vx * vx + vy * vy or 1.0
    t = max(0.0, min(1.0, ((px - a[0]) * vx + (py - a[1]) * vy) / ll))
    return math.hypot(px - a[0] - t * vx, py - a[1] - t * vy)


def _pip(x: float, y: float, poly: Poly) -> bool:
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


# A paddy plot's minimum THICKNESS (inradius proxy 2A/P) as a fraction of `plot_across`.
# MEASURED across the pool 2026-07-27 (do not adjust this from intuition - these are the numbers):
# a healthy plot's median thickness runs 0.25-0.39 of plot_across, and every fan has a tail running
# down to 0.000. The value is pinned to the defect it was derived from: Ubame's west comb has
# exactly EIGHT plots under 0.16, which is precisely the "~8 thin triangular slivers radiating from
# the collector vertex" a reviewer counted by eye on the render - an independent corroboration, from
# pixels, of a threshold picked from geometry.
#
# NOTE the cost, because it is not uniform: sparse town fans shed 7-8 cells, but a dense city fan can
# shed 15 of 62 (~24%) where its p25 already sits near 0.16. Every map still passes the gate,
# paddy_fan_gapless included, so the fans still read as covered - but a city fan is the place to LOOK
# if this is ever retuned, and the gate is not the eye.
_TOE_MIN_THICKNESS = 0.16


def _poly_perim(poly: Poly) -> float:
    """Perimeter of a closed polygon - the denominator of the 2A/P thickness proxy."""
    n = len(poly)
    return sum(math.hypot(poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1]) for i in range(n))


def _signed_area(poly: Poly) -> float:
    """Shoelace WITH its sign - the sign is the diagnosis. Every basin the carve lays comes out
    positively wound; one that comes back negative has had its two boundaries cross, so what is
    drawn is a bowtie, not a field. See the inverted-toe drop in `build_comb`."""
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2


def _poly_area(poly: Poly) -> float:
    return abs(_signed_area(poly))


def hem_on_paddy(quad: Poly, paddy_outline: Poly) -> bool:
    """Whether a dry hem plot REALLY overlaps a paddy fan's envelope. This is the SHARED predicate
    behind both the generators' hem filter (draw_comb_field and the city gens' comb_field drop any
    hem plot that hits a previously recorded fan) and check_village's dry_plots_clear_of_paddies
    gate, so placement and check provably classify the same geometry the same way (the same-source
    doctrine, diagram CLAUDE.md). Wet paddy and dry hatake are mutually exclusive ground - the hem
    exists BECAUSE its ground sits upslope of what the canal commands - so a dry plot on the rice
    is always a defect, never a variant. On a MULTI-FAN map each fan's hem is placed blind to the
    other fans (only hand-tuned dry_keepout circles held them apart before), which is exactly how
    Tango's fe2 hem punched into fe1's envelope (2026-07-23, 13% and 42% of two plots' area in the
    neighbor's rice) - the incident this predicate closes.

    Tolerance is built in by testing the quad SHRUNK 15% toward its centroid (~2-4px at real hem
    plot sizes - the same spirit as no_structure_on_paddy's 3px penetration rule): a hem plot
    legitimately KISSES its own fan's envelope across the berm, and two fans' margins may abut, so
    only real interpenetration counts."""
    cx = sum(p[0] for p in quad) / len(quad)
    cy = sum(p[1] for p in quad) / len(quad)
    sq = [(cx + (px - cx) * 0.85, cy + (py - cy) * 0.85) for px, py in quad]
    if _pip(cx, cy, paddy_outline) or any(_pip(px, py, paddy_outline) for px, py in sq):
        return True
    n = len(paddy_outline)
    return any(_seg_x(sq[i], sq[(i + 1) % len(sq)], paddy_outline[j], paddy_outline[(j + 1) % n]) is not None for i in range(len(sq)) for j in range(n))


def _dug_polyline(
    R: random.Random,
    F: _Frame,
    x: float,
    y: float,
    ang: float,
    length: float,
    wobble: float,
    seg: tuple[float, float],
    W: float,
    H: float,
) -> Poly:
    """A hand-dug canal: few long segments, tiny heading changes (obtuse only)."""
    pts = [(x, y)]
    trav = 0.0
    while trav < length:
        step = min(R.uniform(*seg), length - trav)
        ang += R.uniform(-wobble, wobble)
        nx, ny = x + step * math.cos(ang), y + step * math.sin(ang)
        if not (25 < nx < W - 25 and 25 < ny < H - 25):
            break
        x, y = nx, ny
        pts.append((x, y))
        trav += step
    return pts


def _point_along(pts: Poly, frac: float) -> Pt:
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    d = frac * total
    for i in range(len(pts) - 1):
        L = math.dist(pts[i], pts[i + 1])
        if d <= L:
            t = d / L
            return (pts[i][0] + t * (pts[i + 1][0] - pts[i][0]), pts[i][1] + t * (pts[i + 1][1] - pts[i][1]))
        d -= L
    return pts[-1]


def round_channel_joints(channels: list[dict[str, Any]], min_turn_deg: float = 8.0, steps: int = 6) -> None:
    """Round the bend where one drawn channel CONTINUES into the next, in place.

    A dug run is emitted as SEVERAL records so its width can taper (head-race -> main -> main ...),
    which means the run's own changes of direction fall at the SEAM between two records, where
    `settlement.fillet_polyline` - which only rounds a polyline's interior vertices - cannot reach
    them. That seam was the sharpest water on the maps: Moritono's head-race left the tameike due
    west and met the field-edge main at a mitred elbow (GM 2026-07-25). The doctrine and the
    ~2.5-channel-widths radius are documented at `settlement.fillet_polyline`; here the arc is dug
    out of BOTH records - the upstream one gives up its last stretch and carries the whole bend, the
    downstream one starts where the bend ends - because trimming only one side would leave the
    other's square tip poking out of the curve.

    Only a TRUE continuation is rounded: exactly two channels meeting, one ending and one starting.
    A node where a branch ALSO leaves is a junction, not a bend - an offtake is a notch cut in the
    bank, and the main running past it is not turning there anyway."""
    ends: dict[tuple[float, float], list[tuple[int, int]]] = {}
    for i, c in enumerate(channels):
        if len(c["pts"]) >= 2:
            for which, p in ((0, c["pts"][0]), (1, c["pts"][-1])):
                ends.setdefault((round(p[0], 1), round(p[1], 1)), []).append((i, which))
    for touch in ends.values():
        if len(touch) != 2 or {w for _, w in touch} != {0, 1}:
            continue  # a lone end, or a junction where a branch leaves: not a bend
        a_i = next(i for i, w in touch if w == 1)
        b_i = next(i for i, w in touch if w == 0)
        A, B = channels[a_i], channels[b_i]
        pv, P, nx = A["pts"][-2], A["pts"][-1], B["pts"][1]
        v0, v1 = (pv[0] - P[0], pv[1] - P[1]), (nx[0] - P[0], nx[1] - P[1])
        l0, l1 = math.hypot(*v0), math.hypot(*v1)
        if l0 < 1e-6 or l1 < 1e-6:
            continue
        cosang = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (l0 * l1)))
        if 180.0 - math.degrees(math.acos(cosang)) < min_turn_deg:
            continue  # no visible elbow to round
        w = max(A.get("w_tail", A["w"]), B["w"])
        d = min(2.5 * w, 0.35 * l0, 0.35 * l1)
        a = (P[0] + v0[0] / l0 * d, P[1] + v0[1] / l0 * d)
        b = (P[0] + v1[0] / l1 * d, P[1] + v1[1] / l1 * d)
        arc = []
        for s in range(steps + 1):
            t = s / steps
            mt = 1 - t
            arc.append((round(mt * mt * a[0] + 2 * mt * t * P[0] + t * t * b[0], 1), round(mt * mt * a[1] + 2 * mt * t * P[1] + t * t * b[1], 1)))
        A["pts"] = A["pts"][:-1] + arc  # the upstream record carries the whole bend ...
        B["pts"] = [arc[-1]] + B["pts"][1:]  # ... and the downstream one picks up where it ends


def build_comb(
    W: float,
    H: float,
    sluice: Pt,
    seed: int,
    down_deg: float = 45,
    canal_a_len: tuple[float, float] = (1250, 1450),
    canal_b_len: tuple[float, float] = (680, 800),
    offtakes_a: Sequence[float] = (0.22, 0.45, 0.68, 0.88),
    offtakes_b: Sequence[float] = (0.45, 0.8),
    plot_across: float = 48,
    row_step: tuple[float, float] = (26, 36),
    dry_keepout: Sequence[tuple[float, float, float]] = (),
    dry_band: tuple[float, float] = (70, 132),
    bean_frac: float = 0.28,
    field_fall: float | None = None,
    furrow_spread: float = 1.1,
    grain_drift: float = 0.0,
    grain: float = 1.0,
    supply_banks: bool = False,
) -> dict[str, Any]:
    """The COMB layout (the historical default - Kishu school / Chinese canal doctrine):
    the sluice's head-race forks at one division point into TWO supply canals hugging the
    high margins (canal A runs cross-slope at down-37 deg, canal B down the other margin at
    down+58 deg), delivery ditches drop downhill off them (a couple splitting once), and one
    drain collector (akusui) crosses the LOW side and leaves the map. Paddies are carved
    between the ditch threads; water cascades plot-to-plot within each block (tagoshi).

    Returns {"channels": [{pts, w, role}], "plots": [{poly, fill}], "threads", "drain",
    "envelope", "acres"} - the caller draws it (px are map px; acres assume 1px = 2ft).

    `grain` scales the PLOT-GEOMETRY thresholds in the carve (minimum sector/row/plot sizes,
    canal berms, drain set-backs, the gap-closer margins) AND the channel widths. They are
    REAL-FEET quantities that were tuned at the village grain of 1px = 2ft; the principled
    value is therefore grain = 2 / ftpx, so a "too narrow to plant" test means the same
    real-world size on every map.

    WHAT THE HAND-AUTHORED HAMLETS PASS is 1.0, not 2.0. That was recorded as a silent
    inconsistency for a long time - at 1 ft/px it makes their "too narrow to plant" thresholds
    mean half the real size they mean on a village sheet, and their irrigation ditches half the
    width - and it has now been settled by testing rather than by preference (2026-08-12).

    THE PRINCIPLED VALUE WORKS AT THIS TIER. Two obstacles used to stop it, and both are fixed.
    The first was the bridge arithmetic: wider ditches produced planks and carried-way decks whose
    abutments stood in the channel, because both paths sized a deck from a nominal width rather
    than from the water actually beneath it. `channel_footbridges` now sizes a plank to the widest
    course under it, junctions included, and `bridges()` grows a carried-way deck until its corners
    clear the crossed polyline. The second was the communal WINDBREAK: at the coarser grain the
    crop geometry shifts enough that a belt derived from the house cloud's EXTREMES could land off
    the cluster altogether on a tall narrow settlement (measured: 9 surviving clumps, 350 px from
    the nearest farmhouse). A belt sampled as a PROFILE across the wind instead of a box around the
    extremes does not have that failure mode.

    With both fixed, the scripted hamlet tier passes the principled 2.0 and a 36-map cohort gates
    clean on it (`hamletgen.py`, `GRAIN`, which carries the same reasoning).

    THE POOL'S HAND-AUTHORED HAMLETS ARE STILL AT 1.0, and moving them is a separate job rather
    than a leftover: it re-rolls every comb map in the pool and each one needs a `settlement-review`
    pass, since the change is visible (ditches at their true width, coarser minimum plots). So the
    disagreement is no longer silent - the principled value is demonstrated, the cost of adopting
    it pool-wide is named, and a hamlet gen passing 1.0 is doing so knowingly.

    Left unscaled, a city's carve dropped
    sectors, head plots, and closers that a village would have planted, leaving parchment
    holes inside the fan - the white-spots bug the villages fixed once (canal-side closers,
    the closing rank) and the cities then re-exposed at their coarser grain (2026-07-21).
    The canal/thread/drain SKELETON is deliberately NOT scaled here: its lengths arrive
    pre-scaled from the caller, and the map-edge margins (8px) are canvas facts, not feet."""
    R = random.Random(seed)
    F = _Frame(down_deg)
    DOWN = F.down
    channels = []

    # head-race: sluice -> the division point (bunsuiguchi), straight down the fall
    # (channel widths x grain throughout: the same REAL-feet channel sizes at every map scale)
    hr = [sluice, (sluice[0] + 45 * F.d[0], sluice[1] + 45 * F.d[1]), (sluice[0] + 90 * F.d[0], sluice[1] + 90 * F.d[1])]
    channels.append({"pts": hr, "w": 7.0 * grain, "role": "main"})
    fork = hr[-1]

    # supply canal A: cross-slope along the high margin, descending gently
    a_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN - math.radians(42), R.uniform(*canal_a_len), 0.045, (95, 125), W, H)
    # supply canal B: down the other margin (steeper heading, the west canal on Kikuta). Its polyline is
    # discarded - canal B is redrawn below as the `bc` boundary thread - but the call stays (its RNG draw is
    # part of the frozen stream that keeps every map byte-identical); `_`-prefixed so it reads as intentional.
    _b_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN + math.radians(58), R.uniform(*canal_b_len), 0.05, (90, 120), W, H)

    def mk(
        px: float,
        py: float,
        heading: float,
        ditch_len: float,
        decay: float = 110.0,
        fallback: Poly | _Thread | None = None,
    ) -> _Thread:
        tu, tf = F.to_uf(px, py)
        h = max(-1.2, min(1.2, heading - DOWN))
        # du/df = -tan(h): a heading LEFT of the fall line (h<0) moves u POSITIVE
        return _Thread(tu, tf, -math.tan(h), tf + ditch_len * max(0.2, math.cos(h)), decay, fallback)

    # canal B is itself the far-side boundary thread (its dug prefix IS the canal)
    bc = mk(fork[0], fork[1], DOWN + math.radians(58), R.uniform(*canal_b_len), decay=170.0)
    threads = [bc]
    # delivery ditches are MIN-SPACED: two ditches closer than ~2 plot-columns would water the same
    # ground twice (a redundant near-pair that reads as an artifact, not design), so drop the closer.
    min_gap = 2.0 * plot_across
    placed_u = [bc.u0]  # canal B is a SUPPLY canal - deliveries must not hug it either
    a_ths = []
    for frac in offtakes_a:  # delivery ditches off canal A
        bx, by = _point_along(a_pts, frac)
        tu = F.to_uf(bx, by)[0]
        if any(abs(tu - pu) < min_gap for pu in placed_u):
            continue  # redundant near-pair - skip it (keeps the net sparse)
        placed_u.append(tu)
        th = mk(bx, by, DOWN + R.uniform(-0.15, 0.1), R.uniform(420, 620), fallback=a_pts)
        a_ths.append(th)
        threads.append(th)
    for th in a_ths[1:-1]:  # only the INTERIOR (widest) blocks split once
        th.spawn_sub = True
    rb = mk(a_pts[-1][0], a_pts[-1][1], DOWN, 0, fallback=a_pts)  # far boundary (bund only)
    threads.append(rb)
    threads.sort(key=lambda t: t.u0)

    # spawn events: west-canal offtakes + mid-block subs take off ON their parent's path
    spawns: list[list[Any]] = []  # [f_at, parent_thread, heading, ditch_len, side] - heterogeneous
    bc.offtake_fs = []
    for frac in offtakes_b:
        f_at = bc.f0 + (sum(canal_b_len) / 2 * frac) * math.cos(math.radians(58))
        bc.offtake_fs.append(f_at)
        spawns.append([f_at, bc, DOWN + R.uniform(-0.2, 0.0), R.uniform(340, 560), +1])
    # a sub takes off HIGH on its parent and DIVERGES steeply (bigger heading, longer run) so the two
    # channels end up > ~2 columns apart - a real Y-junction serving a distinct sub-block, NOT two
    # ditches running adjacent for a stretch (which read as a redundant artifact, per the GM).
    for th in [t for t in threads if getattr(t, "spawn_sub", False)]:
        f_at = th.f0 + (th.ditch_f - th.f0) * R.uniform(0.24, 0.38)
        side = R.choice((-1, 1))
        spawns.append([f_at, th, DOWN + side * R.uniform(0.5, 0.66), R.uniform(300, 430), side])
    bc.ditch_f = max([e[0] for e in spawns if e[1] is bc], default=bc.f0 + 40) + 22

    # ---- the lockstep march (no thread may cross another or pinch under GAP)
    for t in threads:
        t.pts = [F.to_xy(t.u0, t.f0)]
    f = min(t.f0 for t in threads)
    # By default the field grows downhill until the threads leave the map (fills the frame to the low
    # corner, then spills off it). `field_fall` CAPS the downhill depth instead, so the field is sized
    # to the population and BOUNDED within the frame - leaving a low-side margin for the drain's outfall
    # + brook to discharge into open land (see settlements.md 'Field extent'). None = the old fill-to-edge.
    f_stop = max(F.to_uf(0, 0)[1], F.to_uf(W, 0)[1], F.to_uf(0, H)[1], F.to_uf(W, H)[1]) + 300
    if field_fall is not None:
        f_stop = min(f_stop, f + field_fall)
    while f < f_stop:
        f += DF
        for ev in [e for e in spawns if e[0] <= f]:
            spawns.remove(ev)
            _, par, head, dlen, side = ev
            px, py = par.pts[-1]
            child = mk(px, py, head, dlen, fallback=par)
            child.u0 = child.u = par.u + GAP * 0.55 * side
            child.pts = [(px, py)]
            threads.insert(threads.index(par) + (1 if side > 0 else 0), child)
        prev_u = None
        for t in threads:
            if f <= t.f0:
                continue
            nu = t.step(f, R)
            if prev_u is not None and nu < prev_u + GAP:
                nu = prev_u + GAP
            t.u = nu
            t.pts.append(F.to_xy(nu, f))
            prev_u = nu
        if all(not (-60 < F.to_xy(t.u, f)[0] < W + 60 and -60 < F.to_xy(t.u, f)[1] < H + 60) for t in threads):
            break

    # ---- DRAIN (akusui): the collector is DUG along the fields' low boundary, so its route
    # is the ENVELOPE of the delivery ditches' dug ends (each column drains just below where
    # its ditch stops) - a u-sorted polyline through (u_bot, f_bot + margin), smoothed, and
    # extended past both ends so the whole system empties off the map
    bots = []
    for t in threads:
        if t.ditch_f <= t.f0 + 10:
            continue  # bund-only boundaries have no ditch
        bot = t.pts[0]
        for p in t.pts:
            if F.to_uf(*p)[1] <= t.ditch_f:
                bot = p
        bots.append(F.to_uf(*bot))
    # A collector is dug below the DEEPEST delivery ends; shallower columns simply cascade
    # further to reach it (the prototype look the GM approved). Fit a gently-descending line
    # f = a + b*u through the ditch bottoms (b clamped so the drain always falls toward its
    # exit on the high-u side - water never runs uphill), pushed down to clear every end.
    n = len(bots)
    mu = sum(b[0] for b in bots) / n
    mf = sum(b[1] for b in bots) / n
    var = sum((b[0] - mu) ** 2 for b in bots) or 1.0
    b_fit = sum((b[0] - mu) * (b[1] - mf) for b in bots) / var
    b_fit = max(0.06, min(0.35, b_fit))
    a_fit = max(b[1] + R.uniform(32, 48) - b_fit * b[0] for b in bots)
    # the head begins AT the westmost delivery ditch's bottom (inside the field), NOT extended out to
    # the boundary thread and beyond into bare ground - a collector starts where the first field drains
    # in, and the hem pass covers any sliver at the SW corner. (This was a dangling stub before.)
    lo_u = min(b[0] for b in bots)
    hi_u = max(b[0] for b in bots) + 40  # the OUTFALL, just past the SE-most ditch bottom
    # keep the collector INSIDE the frame: lower the line if an end would dip off the map edge (a
    # delivery ditch that then reaches it simply discharges into the collector - correct hydrology)
    for uc in (lo_u, hi_u):
        yc = F.to_xy(uc, a_fit + b_fit * uc)[1]
        if yc > H - 40:
            a_fit -= (yc - (H - 40)) / max(0.35, abs(F.d[1]))
    duf = []
    u = lo_u
    while u < hi_u:
        duf.append((u, a_fit + b_fit * u + R.uniform(-6, 6)))
        u += R.uniform(120, 170)
    duf.append((hi_u, a_fit + b_fit * hi_u))  # the outfall point (drain's downhill end)
    duf.sort(key=lambda q: q[0])
    dpts = [F.to_xy(u, f) for u, f in duf]
    # the collector WIDENS downstream - the mirror of the supply taper (GM 2026-07-23): a supply
    # canal sheds water as it goes and dwindles; the akusui GATHERS the plots' tail-water as it
    # crosses the low side, so it starts as a thread at its head and carries the fan's whole
    # runoff at the outfall (duf is u-sorted with the outfall appended at hi_u, so pts[-1] is
    # the downhill end the gens anchor to the brook/moat/offmap).
    # The head is a THREAD - the same 1.5*grain the delivery ditches taper down to (GM 2026-07-25).
    # At its high end a collector is draining the toe of ONE paddy, so there is no flow there to carry:
    # the width has to come from what the ditch must BE, not from what it moves, and a hand-dug earthen
    # ditch that gets cleaned out every year needs a bottom you can put a hoe into (~1 ft) plus standing
    # side slopes, i.e. ~1.5 ft across the top. Below that it is not a maintained ditch at all, it is the
    # seasonal furrow a farmer re-cuts at each drawdown. So the hydraulic floor and the maintenance floor
    # meet exactly at the finest ditch the supply side already draws, and the drain starts there.
    channels.append({"pts": dpts, "w": DRAIN_W_HEAD * grain, "w_tail": DRAIN_W_TAIL * grain, "role": "drain"})

    # the akusui does NOT just stop: it empties at its outfall into a natural valley BROOK that
    # carries the water off the map downhill (reused by the next village downstream / rejoining the
    # river). Water IN (the pond feeder) and water OUT (this brook). BUT a brook is only added when
    # the outfall sits INSIDE the frame - if the field itself already runs to the map edge, the drain
    # discharges off-map directly (a brook grown from there would just run back through the field, as
    # the streams_avoid_fields check correctly flags). A field bounded within the frame gets the brook.
    outfall = dpts[-1]  # the drain's downhill (highest-u) end
    brook = []
    if 14 < outfall[0] < W - 14 and 14 < outfall[1] < H - 14:
        u0, f0 = F.to_uf(*outfall)
        um, fm = F.to_uf(*dpts[-2])  # the drain's EXIT heading (u/f) at the outfall
        eu, ef = u0 - um, f0 - fm
        el = math.hypot(eu, ef) or 1.0
        eu, ef = eu / el, ef / el  # unit exit heading (mostly cross-slope, slight fall)
        ou, of = u0, f0
        brook = [outfall]
        for i in range(40):
            # the brook does NOT turn a hard ~90 deg corner off the collector: it CURVES from the drain's
            # exit heading toward pure downhill over the first few steps, so the junction reads as the
            # collector turning down the valley INTO the stream (a smooth bend, not a right angle).
            w = min(1.0, i / 4.0)
            ou += (1 - w) * eu * 88 + w * R.uniform(-22, 40)
            of += (1 - w) * ef * 88 + w * R.uniform(72, 105)  # w->1 quickly: pure downhill off the map
            p = F.to_xy(ou, of)
            brook.append(p)
            if not (12 < p[0] < W - 12 and 12 < p[1] < H - 12):
                break  # ran off the map edge = the runoff sink

    drain_bank = _drain_bank(F, dpts, grain)  # the ditch's own edge, the one line the field may not cross
    for t in threads:  # clip every thread to the drain
        clipped = [t.pts[0]]
        for i in range(len(t.pts) - 1):
            a, b = t.pts[i], t.pts[i + 1]
            hit = None
            for j in range(len(dpts) - 1):
                hit = _seg_x(a, b, dpts[j], dpts[j + 1])
                if hit:
                    break
            if hit:
                # a thread ENDS AT THE COLLECTOR'S BANK, not on its centerline. `bnd` hands the
                # clipped endpoint back as a plot-boundary point for any fall at or below it, so a
                # clip on the centerline plants a paddy corner in the water - Ubame's west fan had
                # exactly one, 0.25px off the line, and it was the last thing standing between the
                # comb and a clean hem (2026-08-08). The dug PREFIX is unaffected: `ditch_f` stops
                # a couple of hundred px above this point, so the drawn blue never reaches the clip.
                hu = F.to_uf(*hit)[0]
                hf = _f_at_u(F, dpts, hu)
                clipped.append(hit if hf is None else F.to_xy(hu, hf - drain_bank(hu)))
                break
            clipped.append(b)
        t.pts = clipped

    # cascade-tail cap: a column should cascade no more than ~8-11 rows past its ditch's
    # end (the recorded norm is "a few to ~10 paddies" per string) - extend any dug ditch
    # whose tail to the collector would run longer. Only extends, never shortens; the
    # deepest ends (which set the drain fit) are already within reach of it.
    for t in threads:
        if t.ditch_f <= t.f0 + 10:
            continue
        fd_ = _f_at_u(F, dpts, F.to_uf(*t.pts[-1])[0])
        if fd_ is not None:
            t.ditch_f = min(max(t.ditch_f, fd_ - R.uniform(250, 330)), fd_ - 55)

    # ---- drawable canals: A tapers past each offtake ("main canals gradually decrease in
    # size as they are tapped by branch canals" - Tabayashi 1986), and it tapers ALL THE WAY DOWN
    # to a ditch-tail thread (1.6) at its far end (GM 2026-07-23): the supply canal sheds its whole
    # flow into the offtakes and plots along its run, so past the last offtake it carries almost
    # nothing and "slowly disappears" exactly like the delivery ditches - the old stepped 6.2 -> 4.0
    # taper left the top channel reading near-constant beside the dwindling ditches. Each piece now
    # carries w -> w_tail so the narrowing is continuous within pieces, not a stair of blunt steps.
    cuts = [0.0] + list(offtakes_a) + [1.0]
    n_a = len(cuts) - 1
    for i in range(len(cuts) - 1):
        piece = [_point_along(a_pts, cuts[i] + (cuts[i + 1] - cuts[i]) * t / 6) for t in range(7)]
        channels.append({"pts": piece, "w": (6.2 - 4.6 * i / n_a) * grain, "w_tail": (6.2 - 4.6 * (i + 1) / n_a) * grain, "role": "main"})
    bc_cuts = sorted(F.to_uf(*e[1].pts[0])[1] if False else e[0] for e in []) if False else sorted([bc.f0] + [f for f in getattr(bc, "offtake_fs", [])] + [bc.ditch_f])
    for t in threads:
        pre = [p for p in t.pts if F.to_uf(*p)[1] <= t.ditch_f]
        if len(pre) < 2:
            continue
        if t is bc and len(bc_cuts) > 2:
            # canal B is a SUPPLY canal (role "main", like canal A) that narrows past each offtake it
            # feeds - and, like A, dwindles to a ditch-tail thread at its far end (GM 2026-07-23; see
            # the canal-A taper note above).
            m_b = len(bc_cuts) - 1

            def _bc_at(ft: float, pre: Poly = pre) -> Pt | None:  # noqa: B008 - bind the loop's `pre` at definition
                """The point ON `pre` where the fall coordinate crosses `ft`, by interpolation.
                A vertex filter alone drops a whole piece when its cut window is shorter than the
                polyline's ~90-120 px vertex spacing - which is exactly the thread-tail window
                (last offtake -> ditch_f, ~22 px), so Kashikawa's arm ended in a blunt 7.2 ft cap
                where the research promises a taper to a thread (settlement-review 2026-08-16).
                Interpolating the window's endpoints makes every piece drawable regardless of
                where the dug vertices happen to fall, and the pieces meet exactly at the cuts."""
                _fs = [F.to_uf(*p)[1] for p in pre]
                for j in range(len(pre) - 1):
                    fa, fb = _fs[j], _fs[j + 1]
                    if (fa <= ft <= fb) or (fb <= ft <= fa):
                        t = 0.0 if fb == fa else (ft - fa) / (fb - fa)
                        return (pre[j][0] + (pre[j + 1][0] - pre[j][0]) * t, pre[j][1] + (pre[j + 1][1] - pre[j][1]) * t)
                # past the polyline's span: CLAMP to the nearer end rather than dropping the piece.
                # Sawada's dug arm ends a few px short of ditch_f, and returning None there cost the
                # map its thread tail while the other three drew theirs (2026-08-16).
                return pre[-1] if abs(ft - _fs[-1]) < abs(ft - _fs[0]) else pre[0]

            for i in range(len(bc_cuts) - 1):
                piece = [p for p in pre if bc_cuts[i] < F.to_uf(*p)[1] < bc_cuts[i + 1]]
                _pa, _pb = _bc_at(bc_cuts[i]), _bc_at(bc_cuts[i + 1])
                if _pa is not None:
                    piece = [_pa, *piece]
                if _pb is not None:
                    piece = [*piece, _pb]
                if len(piece) >= 2 and math.dist(piece[0], piece[-1]) > 2.0:
                    channels.append({"pts": piece, "w": (5.6 - 4.0 * i / m_b) * grain, "w_tail": (5.6 - 4.0 * (i + 1) / m_b) * grain, "role": "main"})
        elif math.hypot(pre[0][0] - fork[0], pre[0][1] - fork[1]) < 40.0:
            # a delivery must take off WELL DOWNSTREAM of the head fork. A delivery sprouting AT the
            # division point (a short canal B whose single offtake lands ~0px from the fork - Tango's
            # nw1, Hoshizora's west field) turns the clean 3-way bunsuiguchi division into a 4-way STAR
            # that reads as a crossroads, not water feeding the next channel (GM 2026-07-22). Skip drawing
            # it - the plots it shapes keep their bunds, only the blue ditch clutter at the fork goes. The
            # gap between the two offenders (0-1px) and the nearest legitimate delivery (76px) makes 40 a
            # safe cut across every scale. Gated by channels_join_not_cross_at_fork.
            continue
        else:
            # a delivery ditch TAPERS as it descends: it sheds water into the paddies it feeds all
            # along its length, so its flow - and width - decreases from full at the canal takeoff to a
            # THREAD at the delivery point where it stops (continuously "tapped by the plots it feeds",
            # extending Tabayashi's supply-canal taper rule to the delivery ditches). w_tail marks the
            # narrow end so the gen draws it dwindling, not a blunt constant-width stub that stops dead.
            channels.append({"pts": pre, "w": (5.6 if t is bc else 4.0) * grain, "w_tail": 1.5 * grain, "role": "branch"})

    # `supply_banks` hands the carve the very strokes assembled above, so the bunds hem onto the
    # banks that will actually be painted - placer and paint reading the same source. OPT-IN
    # (default False) so every legacy comb gen re-runs byte-identical; the scripted tier passes
    # True and the gate holds it there (paddy_bunds_clear_the_supply_channels, gated on
    # meta.generated_by per the migration doctrine - legacy maps inherit the rule at conversion).
    plots = _carve(
        R,
        F,
        threads,
        a_pts,
        dpts,
        W,
        H,
        plot_across,
        row_step,
        grain,
        seed,
        drain_bank,
        supply=[c for c in channels if c.get("role") != "drain"] if supply_banks else None,
    )

    envelope = [p for p in a_pts] + [p for p in threads[-1].pts] + list(reversed(dpts)) + list(reversed(threads[0].pts))

    # A BASIN IS SIMPLE AND POSITIVELY WOUND (settlement-review, 2026-08-08). At the fan's corner
    # the outer thread has been clipped at the collector, so `bnd` hands the same clamped point back
    # for every fall below it and the sector the carve is still opening no longer exists. Most of
    # what comes out there is harmless - a quad with a collapsed 4th vertex, i.e. a real triangular
    # toe parcel, which is an ordinary thing for a paddy that ran out of ground on one side. But one
    # comes out INVERTED, its winding flipped because the two boundaries crossed: on Hoshizora that
    # was a 143 ft needle, 25 ft at the base, carrying the FLOODED tint, and it read as a wedge of
    # standing water at the head of the ditch. A paddy that turned inside out is not a paddy at any
    # size, so it is dropped rather than measured - the thickness test further down cannot catch it,
    # because a bowtie can be respectably thick. The collapsed vertices are merged away first, so a
    # triangle is recorded as a triangle rather than as a quad with a 0.4px edge.
    #
    # THIS RUNS BEFORE THE WEDGE FILLER, and that ordering is load-bearing: a bowtie still COVERS
    # ground, so dropping one leaves a hole the filler has to plant. Run after it instead and
    # `paddy_fan_gapless` fires on the two city fans (nagahara fs1 8/297 bare, minami fs1 14/492).
    for pl in plots:
        _ring = pl["poly"]
        _merged = [q for i, q in enumerate(_ring) if math.dist(q, _ring[i - 1]) > 1.0]
        if len(_merged) >= 3:
            pl["poly"] = _merged
    plots[:] = [pl for pl in plots if _signed_area(pl["poly"]) > 0]

    # WEDGE FILLER (coarse grains only): even with the thresholds grain-scaled, the carve
    # leaves awkward slivers where ditch threads diverge or the closing geometry misses - and
    # a real cascade fan wasted nothing: fork wedges were terraced into small IRREGULAR
    # paddies. Sample the fan interior on the same grid paddy_fan_gapless uses, cluster the
    # bare cells, and plant a fan-aligned (u,f-frame) filler plot over each cluster. Gated to
    # grain != 1.0 ONLY for byte-stability: every village map was visually vetted gapless at
    # the 2 ft/px tuning grain, and an unconditional pass would re-roll their RNG streams.
    if grain != 1.0:
        _fill_wedges(R, F, plots, envelope, grain, channels, plot_across, row_step, a_pts, dpts)
    # THE FAN'S TOE IS A HEADLAND, NOT A ROW OF FAKE BASINS (settlement-review 2026-07-26; GM
    # 2026-07-27). Where the fan narrows to its collector vertex, the carve and the wedge filler
    # both emit cells that taper to a point - Ubame's west comb ended in ~8 acute triangles
    # radiating from the vertex, and Hoshizora shows the same. A paddy is a LEVEL BASIN: it is
    # bunded and holds standing water to a uniform depth, so a sliver that acute cannot be leveled
    # or bunded at any sane cost, and real fan and terrace systems end in a headland or simply
    # leave the odd corner unpaddied rather than pretend. Dropping them is also visually free: the
    # fan carries a base floor under the plots (`comb_base_fill`, enforced by paddy_fan_has_floor),
    # so the ground reads as the fan's own toe rather than as a hole.
    #
    # The test is the inradius proxy 2*Area/Perimeter - a THICKNESS, not an area, because an acute
    # sliver can carry a respectable area while being too narrow anywhere to hold water. Scaled to
    # `plot_across` so it means the same thing at every grain.
    _thin = [q for q in plots if _poly_perim(q["poly"]) <= 0 or 2 * _poly_area(q["poly"]) / _poly_perim(q["poly"]) < _TOE_MIN_THICKNESS * plot_across]
    if _thin:
        _drop = {id(q) for q in _thin}
        plots[:] = [q for q in plots if id(q) not in _drop]
    # THE INVARIANT, held uniformly across all four field engines: no basin's wall stands in the
    # ditch. The comb hems onto the bank BY CONSTRUCTION (see `_drain_bank`), so this pass is a
    # no-op on all but one vertex in the whole pool - and that one is worth naming, because it says
    # what the pass is really for. At Ubame's west corner the boundary thread is clipped at the
    # collector's HEAD, so `bnd` hands back the same clamped point for every fall below it and the
    # sector's closing quads come out inverted; an INTERIOR sub-bund of that degenerate sector then
    # interpolates to within 0.3px of the ditch. The real answer there is for the carve to stop
    # opening a sector whose boundary has already collapsed onto the drain, which is a change to the
    # carve's sector geometry and not to this rule - so until that is done, the corner is held to
    # the invariant here rather than left standing in the water.
    for pl in plots:
        pl["poly"] = hem_to_bank(pl["poly"], dpts, down_deg, DRAIN_W_HEAD * grain, DRAIN_W_TAIL * grain)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560  # 1px=2ft -> 4 sq ft/px^2

    # DRY FIELDS (hatake) on the uncommanded upslope margin above the supply canal, and
    # BUND BEANS (azemame) beaded along a fraction of the paddy bunds - see settlements.md.
    dry_plots = _dry_fields(R, F, a_pts, W, H, dry_keepout, band=dry_band, g=grain, furrow_spread=furrow_spread, grain_drift=grain_drift)
    if grain != 1.0:
        # the INTER-ARM FORK TRIANGLE (coarse grains only): the ground between the two supply
        # canals just below the fork is commanded by neither (it sits upslope of canal B), and
        # on a village map the scrub matrix textures it - a city map has no scrub, so it read
        # as the blank wedge the GM circled at every fan head (2026-07-21). Historically it is
        # prime dry-crop ground beside the head-race, so quilt it: a second hem band along
        # canal B's SUPPLY stretch, whose upslope normal points INTO the triangle. Village
        # maps skip this (byte-stability; their scrub already covers the same ground).
        # ...and the band spans only the stretch that BORDERS the triangle: up to bc's first
        # offtake, where the paddy bc itself commands begins. When canal B carries offtakes
        # (every scripted row since 2026-08-16), running the band to ditch_f strings hem plots
        # along ground that is now carved RICE - Cohort-41 dropped a soy plot square on the
        # paddy and its delivery ditch that way. With no offtakes the two bounds coincide.
        _bc_tri_f = min(list(getattr(bc, "offtake_fs", []) or []) + [bc.ditch_f])
        _bc_supply = [p for p in bc.pts if F.to_uf(*p)[1] <= _bc_tri_f]
        if len(_bc_supply) >= 2:
            dry_plots += _dry_fields(
                R, F, _bc_supply, W, H, dry_keepout, band=(dry_band[0] * 0.6, dry_band[1] * 0.6), g=grain, furrow_spread=furrow_spread, grain_drift=grain_drift
            )  # thinner than the a-side hem: it only needs to cover the fork triangle, and a full-depth band crowds the farmhouse ring off the fan's visible edge
    dry_acres = sum(_poly_area(p["poly"]) for p in dry_plots) * 4 / 43560
    bund_beans = _bund_beans(R, plots, bean_frac, channels=channels)
    # furrows_vary tells the checker whether to REQUIRE neighboring dry plots to differ in row direction: a
    # gentle-valley village spreads them (the patchwork quilt, default); a STEEP/terraced village narrows the
    # spread so the rows converge back onto the contour (ridge-along-contour erosion control) and no variation
    # is required. Threshold at ~0.3 rad (~17 deg): above it the plots visibly fan, below it they read aligned.
    round_channel_joints(channels)  # earthen water turns on a swept bend, not a mitred corner
    return {
        "down_deg": down_deg,  # the LOCAL fall this fan was carved to - recorded so the drainage-slope
        # checks can judge each drain against ITS OWN field rather than one map-level constant (a city
        # ringed by farmland genuinely drains several ways at once; GM 2026-07-25)
        "fork": fork,  # the bunsuiguchi division point - recorded so comb_supply_commands_both_flanks
        # can measure each flank's planted extent and drawn-supply reach FROM the point the model
        # itself divides at (placement and check reading the same source; GM 2026-08-16)
        "channels": channels,
        "plots": plots,
        "threads": threads,
        "drain": dpts,
        "brook": brook,
        "envelope": envelope,
        "acres": acres,
        "dry_plots": dry_plots,
        "dry_acres": dry_acres,
        "bund_beans": bund_beans,
        "furrows_vary": furrow_spread >= 0.3,
    }


def _fill_wedges(
    R: random.Random, F: _Frame, plots: list[dict[str, Any]], envelope: Poly, g: float, channels: list[dict[str, Any]], plot_across: float, row_step: tuple[float, float], a_pts: Poly, dpts: Poly
) -> None:
    """Plant the bare wedges _carve left inside the fan (see the call site). Grid-samples the
    envelope interior (rim inset excluded - berms and drain set-backs legitimately live there),
    clusters bare cells, and appends one fan-aligned quad per cluster, shrunk until it stands
    clear of every existing plot. Mirrors paddy_fan_gapless's geometry: inset 28*g / tol 8*g /
    step 12*g px = 56 / 6 / 24 real ft at any grain. The plot tolerance is BUND-scale (6 real
    ft): anything wider than a bund must be planted or be WATER - the recorded channels count
    as covered ground (they draw over the fan), which is what lets the tolerance stay tight
    without flagging the delivery-ditch strips between plot columns."""
    inset, tol, step = (
        8 * g,
        3 * g,
        6 * g,
    )  # rim inset is BERM-scale (16 real ft): paddies HUG their canals (the closer doctrine), so a wide "legit rim" tolerance just preserved the bare canal-head bands; step at HALF the check's grid so thin slivers cannot alias through

    dus = [F.to_uf(*q)[0] for q in dpts]
    du_lo, du_hi = min(dus), max(dus)

    def drain_f_clamped(u: float) -> float:
        """The collector's fall under u, with FLAT extensions past both ends: the command area's
        low boundary conceptually continues level beyond the drawn collector, so a low-u fork
        wedge (before the first ditch) still fills while ground below the extended line - the
        floating-diamond wart past the outfall - stays bare."""
        fd = _f_at_u(F, dpts, u)
        if fd is not None:
            return fd
        end = dpts[0] if abs(u - du_lo) < abs(u - du_hi) else dpts[-1]
        return F.to_uf(*end)[1]

    def sd(px: float, py: float, a: Pt, b: Pt) -> float:
        vx, vy = b[0] - a[0], b[1] - a[1]
        ll = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((px - a[0]) * vx + (py - a[1]) * vy) / ll))
        return math.hypot(px - a[0] - t * vx, py - a[1] - t * vy)

    boxes = [(min(q[0] for q in p["poly"]) - tol, min(q[1] for q in p["poly"]) - tol, max(q[0] for q in p["poly"]) + tol, max(q[1] for q in p["poly"]) + tol) for p in plots]

    def dist_to_plot(x: float, y: float) -> float:
        best = 1e9
        for p, (bx0, by0, bx1, by1) in zip(plots, boxes, strict=True):
            if not (bx0 - 16 * g <= x <= bx1 + 16 * g and by0 - 16 * g <= y <= by1 + 16 * g):
                continue
            poly = p["poly"]
            if _pip(x, y, poly):
                return 0.0
            best = min(best, min(sd(x, y, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))))
        return best

    def near_plot(x: float, y: float) -> bool:
        for p, (bx0, by0, bx1, by1) in zip(plots, boxes, strict=True):
            if not (bx0 <= x <= bx1 and by0 <= y <= by1):
                continue
            poly = p["poly"]
            if _pip(x, y, poly) or any(sd(x, y, poly[i], poly[(i + 1) % len(poly)]) < tol for i in range(len(poly))):
                return True
        for c in channels:
            hw = c["w"] / 2 + 3 * g
            cp = c["pts"]
            if any(sd(x, y, cp[i], cp[i + 1]) < hw for i in range(len(cp) - 1)):
                return True
        return False

    ex0, ey0 = min(q[0] for q in envelope), min(q[1] for q in envelope)
    ex1, ey1 = max(q[0] for q in envelope), max(q[1] for q in envelope)
    bare = []
    y = ey0
    while y <= ey1:
        x = ex0
        while x <= ex1:
            if (
                _pip(x, y, envelope)
                and all(sd(x, y, envelope[i], envelope[(i + 1) % len(envelope)]) > inset for i in range(len(envelope)))
                and not near_plot(x, y)
                and F.to_uf(x, y)[1] < drain_f_clamped(F.to_uf(x, y)[0]) - 3 * g
            ):
                # bounded by the COMMAND AREA, not by proximity to existing plots: bare ground
                # between the canals and the (extended) collector line is wasted commanded land
                # wherever it lies - the canal-head bands the closers miss, fork wedges, tail
                # slivers - while ground below that line is outside the fan and stays bare
                bare.append((x, y))
            x += step
        y += step

    # cluster by grid adjacency (union-find over neighbors within 1.6 steps)
    parent = list(range(len(bare)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(bare)):
        for j in range(i + 1, len(bare)):
            if math.dist(bare[i], bare[j]) <= 1.6 * step:
                parent[find(i)] = find(j)
    clusters: dict[int, list[Pt]] = {}
    for i, c in enumerate(bare):
        clusters.setdefault(find(i), []).append(c)

    def depth_in_plots(px: float, py: float) -> float:
        """How deep (px) the point sits inside any existing plot - 0 when outside all."""
        best = 0.0
        for p in plots:
            poly = p["poly"]
            if _pip(px, py, poly):
                best = max(best, min(sd(px, py, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))))
        return best

    tiles: list[tuple[float, float, float, float]] = []
    for cells in clusters.values():
        ufs = [F.to_uf(*c) for c in cells]
        ulo, uhi = min(u for u, _ in ufs) - 0.8 * step, max(u for u, _ in ufs) + 0.8 * step
        flo, fhi = min(f for _, f in ufs) - 0.8 * step, max(f for _, f in ufs) + 0.8 * step
        # tile the cluster's (u,f) box at the FAN'S OWN GRAIN: one giant filler slab would
        # dwarf the ~0.08-acre plots around it (the relative-size doctrine), so the box is
        # split into ~plot_across x row_step cells and each tile is seated on its own
        nu = max(1, round((uhi - ulo) / plot_across))
        nf = max(1, round((fhi - flo) / ((row_step[0] + row_step[1]) / 2)))
        for iu in range(nu):
            for jf in range(nf):
                tiles.append((ulo + (uhi - ulo) * iu / nu, ulo + (uhi - ulo) * (iu + 1) / nu, flo + (fhi - flo) * jf / nf, flo + (fhi - flo) * (jf + 1) / nf))
    for tulo, tuhi, tflo, tfhi in tiles:
        # a filler obeys the carve's own water bounds: its centroid never pokes past the drain
        # collector nor upslope of the supply canal (the floating-diamond wart: a tile seated in
        # the bare margin between the fan's drain edge and the smoothed outline reads as a paddy
        # with no water, hanging off the fan - exactly what spills_drain exists to forbid)
        tcu, tcf = (tulo + tuhi) / 2, (tflo + tfhi) / 2
        tcx, tcy = F.to_xy(tcu, tcf)
        if not _pip(tcx, tcy, envelope):
            continue  # the tile drifted out of the fan (cluster-box expansion can cross the rim - the floating-diamond wart)
        if tcf > drain_f_clamped(tcu) - 3 * g:
            continue  # below the (extended) collector line - outside the command area
        fd_t = _f_at_u(F, dpts, tcu)
        if fd_t is not None and tcf > fd_t - 3 * g:
            continue  # past the collector (None = no drain below this u: a low-u fork wedge, bounded by its thread instead)
        fc_t = _f_at_u(F, a_pts, tcu)
        if fc_t is not None and tcf < fc_t + 4 * g:
            continue
        quad = [F.to_xy(tulo, tflo), F.to_xy(tuhi, tflo), F.to_xy(tuhi, tfhi), F.to_xy(tulo, tfhi)]
        # shrink toward the centroid until the quad only OVERLAPS its neighbors shallowly.
        # A thin sliver is bordered by plots on BOTH sides, so demanding full clearance would
        # drop exactly the wedges this pass exists to plant - instead the filler may lap up
        # to ~12 real ft onto a neighbor: fillers append LAST, so they paint over the lapped
        # edge cleanly and the seam just reads as the bund between two plots.
        cx = sum(q[0] for q in quad) / 4
        cy = sum(q[1] for q in quad) / 4

        def touches_channel(qd: Poly) -> bool:
            """EDGE-walked at a 3 px step, not 8-point-probed (settlement-review, Sawada
            2026-08-15): two filler tiles near branch TAILS kept every corner and midpoint clear
            of the water while an edge interior dipped within a pixel of the stroke - the same
            probe-sparsity class as the carve's own vertex-only miss, fixed the same way."""
            for qi in range(4):
                qa, qb = qd[qi], qd[(qi + 1) % 4]
                for qk in range(max(1, int(math.dist(qa, qb) / 3.0)) + 1):
                    qt = qk / max(1, int(math.dist(qa, qb) / 3.0))
                    qx, qy = qa[0] + qt * (qb[0] - qa[0]), qa[1] + qt * (qb[1] - qa[1])
                    if any(any(sd(qx, qy, c["pts"][ci], c["pts"][ci + 1]) < c["w"] / 2 + 2 * g for ci in range(len(c["pts"]) - 1)) for c in channels):
                        return True
            return False

        for _ in range(12):
            probes = list(quad) + [((quad[i][0] + quad[(i + 1) % 4][0]) / 2, (quad[i][1] + quad[(i + 1) % 4][1]) / 2) for i in range(4)]
            # ... and at least one probe must stand on genuinely BARE ground (settlement-review,
            # Inashiro 2026-08-15): the shallow-lap allowance alone is satisfiable by FULL
            # containment inside a slightly-larger quad, so the shrink nested 12 fillers wholly
            # within carved paddies - a bund ring drawn inside a paddy. A filler that fills no
            # bare ground is not a filler; shrinking cannot cure containment, so it falls through
            # to the bail-out below and the sliver is left to the bunds.
            if any(depth_in_plots(px, py) == 0.0 for px, py in probes) and all(depth_in_plots(px, py) <= 6 * g for px, py in probes) and not touches_channel(quad):
                break
            quad = [(cx + (q[0] - cx) * 0.88, cy + (q[1] - cy) * 0.88) for q in quad]
        else:
            continue  # hopelessly buried - leave the sliver to the bunds
        if math.dist(quad[0], quad[1]) < 6 * g or math.dist(quad[1], quad[2]) < 6 * g:
            continue
        plots.append(
            {"poly": [(round(q[0], 1), round(q[1], 1)) for q in quad], "fill": R.choice(RICE_GREENS), "filler": True}
        )  # tagged so water-topology anchors (plot_centroid) skip synthetic rim tiles (channel_field_anchored)


def _carve(
    R: random.Random,
    F: _Frame,
    threads: list[_Thread],
    a_pts: Poly,
    dpts: Poly,
    W: float,
    H: float,
    plot_across: float,
    row_step: tuple[float, float],
    g: float = 1.0,
    seed: int = 0,
    bank: Callable[[float], float] | None = None,
    supply: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Carve paddy plots between adjacent threads. Above a thread's takeoff the boundary
    falls back to its parent path (canal / parent ditch); below its end, to the DRAIN - so
    plots hug the canal at the top and reach the collector at the bottom, never spilling
    past either. Rows step down the fall, each one wandering on its own (see `rphase` below)."""
    plots: list[dict[str, Any]] = []
    _RW = random.Random(seed ^ 0x12005)  # the row-wander stream, separate so the canal skeleton is unmoved
    # Every drain-side stop in this function measures off `bank(u)` - the ditch's own EDGE at that
    # point - rather than a flat constant, so the field hems onto the collector's BANK instead of
    # onto (and through) its drawn stroke. See `_drain_bank`. The fallback keeps `_carve` callable
    # on its own in a test without a collector width to hand.
    bank_at: Callable[[float], float] = bank if bank is not None else (lambda _u: 2.0 * g)

    # SUPPLY-SIDE BANKS (GM 2026-08-15, Inashiro: "the earth bunds which border the irrigated
    # channel ... are actually in the middle of the water instead of along the water's edge").
    # `bnd` returns thread/canal CENTERLINES, and the supply strokes (the canal pieces, the
    # delivery ditches) are drawn centered on those same lines - so without this pass the first
    # and last column's bunds, and the head wedge's boundary where `bnd` falls back onto canal A's
    # own path, run down the middle of the drawn water. The drain has hemmed onto its bank by
    # construction since 2026-08-08 (`_drain_bank`); this is the supply half of the same physical
    # rule: the bund holds the basin's water IN, the channel carries other water PAST, so the two
    # can only ABUT at the bank. Every carved corner is held off every supply stroke by the
    # stroke's local half-width (they taper) plus half a bund stroke, PERPENDICULAR to the stroke.
    # `supply=None` (the legacy default) skips all of it, so the hand-authored pool is unmoved.
    sup_idx: list[tuple[Poly, list[float], float, float, tuple[float, float, float, float]]] = []
    for sc in supply or []:
        spts = [(float(p[0]), float(p[1])) for p in sc["pts"]]
        if len(spts) >= 2:
            _sw0, _sw1 = float(sc["w"]), float(sc.get("w_tail", sc["w"]))
            _sreach = max(_sw0, _sw1) / 2 + BANK_MARGIN * g + 2.0  # bbox prefilter: prunes only, never decides
            _sbb = (min(p[0] for p in spts) - _sreach, min(p[1] for p in spts) - _sreach, max(p[0] for p in spts) + _sreach, max(p[1] for p in spts) + _sreach)
            sup_idx.append((spts, polyline_cum(spts), _sw0, _sw1, _sbb))

    def clear_supply(x: float, y: float, hx: float, hy: float) -> Pt:
        """Hold a carved corner off every supply stroke's bank. `(hx, hy)` breaks the tie for a
        point sitting exactly ON a centerline (the sector-boundary case): it points toward the
        sector's own interior, so the two sectors sharing a ditch are pushed onto opposite banks."""
        for _ in range(6):  # a corner near a takeoff can sit in two strokes; re-test until clear
            moved = False
            for spts, scum, w0, w1, sbb in sup_idx:
                if not (sbb[0] <= x <= sbb[2] and sbb[1] <= y <= sbb[3]):
                    continue
                gap, halfw, past, foot, nrm = supply_bank_clearance((x, y), spts, w0, w1, scum)
                need = halfw + BANK_MARGIN * g
                if past or gap >= need:
                    continue
                if gap > 0.5:
                    nx, ny = (x - foot[0]) / gap, (y - foot[1]) / gap
                elif hx * nrm[0] + hy * nrm[1] >= 0:
                    nx, ny = nrm
                else:
                    nx, ny = -nrm[0], -nrm[1]
                x, y = foot[0] + nx * need, foot[1] + ny * need
                moved = True
            if not moved:
                break
        return (x, y)

    def quad_in_supply(quad: Poly) -> bool:
        """A quad with a corner - or ANY point of any EDGE - still inside a supply stroke's bank
        after the push. Near a takeoff the ground between a parent channel and its child ditch is
        narrower than the two banks, so no legal corner exists there; the alternating push cannot
        resolve it, and the quad is DROPPED, the same way the toe drops its unbundable slivers:
        the fan's base floor shows and the ground reads as the junction's own margin.

        EDGES, not just vertices (settlement-review, Sawada 2026-08-15): at an acute junction a
        wedge plot can keep every corner dry while its two long edges converge THROUGH the canal
        between them - the drawn bund crosses the water with all four vertices on land. So each
        edge is walked at a 3 px step, bbox-gated so only edges near a stroke pay for it. 0.5 px
        under the placer's line keeps the drop to the genuinely unresolvable (the gate fires
        further down, at BANK_MARGIN - 0.15 over halfw)."""
        for i in range(len(quad)):
            a, b = quad[i], quad[(i + 1) % len(quad)]
            for spts, scum, w0, w1, sbb in sup_idx:
                if max(a[0], b[0]) < sbb[0] or min(a[0], b[0]) > sbb[2] or max(a[1], b[1]) < sbb[1] or min(a[1], b[1]) > sbb[3]:
                    continue
                nstep = max(1, int(math.dist(a, b) / 3.0))
                for k in range(nstep + 1):
                    t = k / nstep
                    q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
                    gap, halfw, past, _foot, _nrm = supply_bank_clearance(q, spts, w0, w1, scum)
                    if not past and gap < halfw + BANK_MARGIN * g - 0.5:
                        return True
        return False

    def bnd(t: _Thread, f: float) -> Pt:
        if f < t.f0 and t.fallback is not None:
            fb = t.fallback
            return _at_f(F, fb if isinstance(fb, list) else fb.pts, f)
        if f > F.to_uf(*t.pts[-1])[1]:
            # past its own end a boundary follows the COLLECTOR - and it follows the collector's
            # BANK, not its centerline. Without the offset the fan's side corner is planted exactly
            # on the drain head (Hoshizora's west fan did, by 1.6px) and the sector's outermost bund
            # is drawn inside the ditch it is supposed to stop at.
            pd = _at_f(F, dpts, f)
            ud, fdp = F.to_uf(*pd)
            return F.to_xy(ud, fdp - bank_at(ud))
        return _at_f(F, t.pts, f)

    a_us = [F.to_uf(*p)[0] for p in a_pts]
    a_ulo, a_uhi = min(a_us), max(a_us)

    def spills_drain(pq: Pt) -> bool:
        """Below the collector's BANK - strict per-vertex (no plot may poke into the drain)."""
        u, f = F.to_uf(*pq)
        fd = _f_at_u(F, dpts, u)
        return fd is not None and f > fd - bank_at(u)

    def bank_chord(u0: float, u1: float, fd_default: float | None = None) -> tuple[float, float] | None:
        """End falls of a STRAIGHT bund spanning u0..u1 that clears the collector's bank the whole way.

        A paddy basin has straight sides - it cannot chase the ditch's wander, and the collector
        wanders by design (its nodes carry +-6px of jitter at a 120-170px spacing, so successive
        segments differ by a few degrees). A bund pinned only at its two ends therefore cuts the
        corner at every bend and lands in the water: that is the last residue of the drain-crossing
        bunds, worth ~9 deg and one crossed segment on Hoshizora's NE pocket after the hem pass was
        squared up. So take the bank fall at each end, walk the drain's own vertices in between, and
        push the whole line up by whatever the chord falls short - the bund follows the HIGHEST
        point of the bank across its own span, which is also what a farmer laying a straight bund
        against a crooked ditch would do."""
        f0, f1 = _f_at_u(F, dpts, u0), _f_at_u(F, dpts, u1)
        f0 = fd_default if f0 is None else f0
        f1 = fd_default if f1 is None else f1
        if f0 is None or f1 is None:
            return None
        f0, f1 = f0 - bank_at(u0), f1 - bank_at(u1)
        du = u1 - u0
        if du:
            for dpt in dpts:
                uk, fk = F.to_uf(*dpt)
                if min(u0, u1) < uk < max(u0, u1):
                    lift = (f0 + (f1 - f0) * (uk - u0) / du) - (fk - bank_at(uk))
                    if lift > 0:
                        f0, f1 = f0 - lift, f1 - lift
        return f0, f1

    def above_canal(quad: Poly) -> bool:
        """Upslope of the supply canal - judged by the CENTROID, not the top vertices: a
        head plot's top edge sits ON the canal (fed directly through the bund), which is
        correct and must be KEPT; only a plot whose body is genuinely above the canal is
        rejected. (Per-vertex here was silently discarding every canal-touching head plot.)"""
        cx = sum(p[0] for p in quad) / 4
        cy = sum(p[1] for p in quad) / 4
        u, f = F.to_uf(cx, cy)
        if not (a_ulo - 20 * g < u < a_uhi + 20 * g):
            return False
        fc = _f_at_u(F, a_pts, u)
        return fc is not None and f < fc + 4 * g  # centroid upslope of a small berm

    def root_f(t: _Thread) -> float:
        while isinstance(t.fallback, _Thread):
            t = t.fallback
        if isinstance(t.fallback, list):
            return min(t.f0, F.to_uf(*t.fallback[0])[1])
        return t.f0

    for di in range(len(threads) - 1):
        A, B = threads[di], threads[di + 1]
        f_lo = max(root_f(A), root_f(B)) + 6 * g
        if B.fallback is A or A.fallback is B:
            # a parent-child pair: the sector opens AT the spawn point - anchor the first
            # row there, else the row straddling the spawn has zero width and never plants
            f_lo = max(A.f0, B.f0) + 4 * g
        f_hi0 = max(F.to_uf(*A.pts[-1])[1], F.to_uf(*B.pts[-1])[1]) - 34 * g
        if f_hi0 - f_lo < 24 * g:
            continue
        # measure the sector's width where BOTH boundaries are their own threads (the
        # active span) - measuring in the fallback wedge reads ~0 and degenerates nsub
        fmid = (max(A.f0, B.f0) + f_hi0) / 2
        width_mid = math.dist(bnd(A, fmid), bnd(B, fmid))
        if width_mid < 24 * g:
            continue
        nsub = max(1, round(width_mid / plot_across))
        phase = [R.uniform(0, 6.28) for _ in range(nsub + 2)]
        # THE ROW LINES WANDER TOO (GM 2026-07-25: "even human-made bunds won't be perfectly parallel to
        # one another"). The cross wobble above moves a point ALONG its contour, which bends the column
        # bunds; the row bunds were left running at a constant fall value, i.e. dead straight and exactly
        # parallel to one another all the way down the sector - the machine-made read the GM caught on
        # the polder, in the one place the comb still had it. So a point also shifts a little IN FALL,
        # by a profile that depends on where it sits along the row (`rphase[j]`) and on which row it is
        # (the `fv` term), so no two rows carry the same shape and the strip between them is wider at
        # one end than the other. Pinned at j=0 and j=n, exactly like the cross wobble, so the sector's
        # thread boundaries - the canals every parcel is measured off - do not move at all.
        rphase = [_RW.uniform(0, 6.28) for _ in range(nsub + 2)]
        rowamp = 0.13 * sum(row_step) / 2
        # The wander is tapered to zero at the sector's first and last row, because those two are not
        # free lines: the head row sits ON the supply canal (it takes water through bund cuts) and the
        # closing rank sits ON the drain collector. Both are pinned by the water, so only the rows
        # between them drift - which also keeps the fan's own extent exactly where the gen placed the
        # village, gardens, and label against it. `rspan` is filled in once f_hi is known below; while
        # it is degenerate the wander is simply off, so the f_hi probe itself is not perturbed.
        rspan = [f_lo, f_lo]

        def edge(  # bind loop vars (used within this iteration)
            fv: float,
            j: int,
            n: int,
            A: _Thread = A,
            B: _Thread = B,
            phase: list[float] = phase,
            nsub: int = nsub,
            rphase: list[float] = rphase,
            rowamp: float = rowamp,
            rspan: list[float] = rspan,
        ) -> Pt:
            a, b = bnd(A, fv), bnd(B, fv)
            t = j / n
            x = a[0] + t * (b[0] - a[0])
            y = a[1] + t * (b[1] - a[1])
            if 0 < j < n:  # interior bunds waver along contour...
                wob = 5.0 * math.sin(fv / 70 + phase[min(j, nsub + 1)])
                x += F.c[0] * wob
                y += F.c[1] * wob
                if rspan[1] > rspan[0]:  # ...and drift in fall, so no two rows run parallel
                    ft = max(0.0, min(1.0, (fv - rspan[0]) / (rspan[1] - rspan[0])))
                    rw = rowamp * math.sin(fv / 47 + rphase[min(j, nsub + 1)]) * math.sin(math.pi * ft)
                    x += F.d[0] * rw
                    y += F.d[1] * rw
            if sup_idx:
                # toward the sector's own interior - the tie-break side for an on-centerline point
                mx, my = (a[0] + b[0]) / 2 - x, (a[1] + b[1]) / 2 - y
                ml = math.hypot(mx, my)
                return clear_supply(x, y, mx / ml, my / ml) if ml > 1e-9 else clear_supply(x, y, F.d[0], F.d[1])
            return (x, y)

        def drain_f_at(fv: float, j_: int, n_: int) -> float:
            """Fall of the drain under the j_-th sub-bund point sampled at fall fv."""
            pu = F.to_uf(*edge(fv, j_, n_))[0]
            fd_ = _f_at_u(F, dpts, pu)
            return fd_ if fd_ is not None else fv

        f_hi = min(f_hi0, min(drain_f_at(f_hi0, j, nsub) for j in range(nsub + 1)) - 32 * g)
        if f_hi - f_lo < 24 * g:
            continue
        rspan[0], rspan[1] = f_lo, f_hi  # the row wander is live now that the sector's span is known
        sector_start = len(plots)
        rows = [f_lo]
        f = f_lo
        while f < f_hi:
            f = min(f_hi, f + R.uniform(*row_step))
            rows.append(f)

        for k in range(len(rows) - 1):
            wk = min(math.dist(bnd(A, rows[k]), bnd(B, rows[k])), math.dist(bnd(A, rows[k + 1]), bnd(B, rows[k + 1])))
            if wk < 24 * g:
                continue
            n = nsub if wk / nsub >= 13 * g else max(1, int(wk // (44 * g)))  # canal-wedge rows: local
            for j in range(n):
                quad = [edge(rows[k], j, n), edge(rows[k], j + 1, n), edge(rows[k + 1], j + 1, n), edge(rows[k + 1], j, n)]
                if math.dist(quad[0], quad[1]) < 12 * g or math.dist(quad[1], quad[2]) < 12 * g:
                    continue
                if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                    continue
                if any(spills_drain(pq) for pq in quad) or above_canal(quad) or quad_in_supply(quad):
                    continue
                # CROP: within the irrigated command area everything is RICE (paddy land was
                # too valuable for anything else - dry crops belong on ground the water cannot
                # command: above the canal / the village fringe, added in later stages; soy
                # grows on the bunds as aze-mame, not as plots). One village = one transplant
                # = one growth stage, so the field reads as ONE green. FLOODED (blue) accents
                # are reserved ENTIRELY for the closing rank (added below), which sits ON the
                # drain collector - so every blue plot literally drains into the southern ditch
                # and none can read as a stranded reservoir. The body is uniformly rice-green.
                fill = R.choice(RICE_GREENS)
                plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad], "fill": fill})

        # CANAL-SIDE closers: the head plots run up against the supply canal - only a
        # narrow berm remains. These are the plots that take water DIRECTLY from the
        # canal through bund cuts (the first link of every cascade chain); a wide bare
        # gap below a supply canal would be wasted prime land. Top edges follow the
        # canal line (sloped, like the drain closers), bottoms sit on the row grid.
        for j in range(nsub):
            fprobe = max(A.f0, B.f0) + 12 * g  # sample where the subcolumns are spread out
            fc0 = _f_at_u(F, a_pts, F.to_uf(*edge(fprobe, j, nsub))[0])
            fc1 = _f_at_u(F, a_pts, F.to_uf(*edge(fprobe, j + 1, nsub))[0])
            if fc0 is None or fc1 is None:
                continue
            t0, t1 = fc0 + 5 * g, fc1 + 5 * g
            ks = [k for k in range(len(rows)) if rows[k] >= max(t0, t1) + 6 * g]
            if not ks:
                continue
            fb = rows[ks[0]]
            _ct = (2 if g < 1.0 else 8) * g  # relaxed minima at coarse grains ONLY: village output is GM-vetted and stays byte-identical (g=1 keeps the originals)
            if fb - min(t0, t1) > 78 * g or fb - max(t0, t1) < _ct:
                continue  # no gap here / top boundary is not the canal (at coarse grain a thin FAR side is fine - the quad degrades to a wedge)
            quad = [edge(t0, j, nsub), edge(t1, j + 1, nsub), edge(fb, j + 1, nsub), edge(fb, j, nsub)]
            if math.dist(quad[0], quad[1]) < (6 if g < 1.0 else 12) * g or math.dist(quad[1], quad[2]) < (2 if g < 1.0 else 6) * g:
                continue  # min top edge 6*g at coarse grains (12*g at the vetted village grain): the city fans' narrow head sub-columns dropped 3 of nw1's 5 closers, leaving the bare canal-head band (2026-07-21)
            if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                continue
            cx = sum(pq[0] for pq in quad) / 4
            cy = sum(pq[1] for pq in quad) / 4
            if any(_pip(cx, cy, pl["poly"]) for pl in plots[sector_start:]):
                continue  # this ground already planted (fork wedges)
            if quad_in_supply(quad):
                continue  # a head closer wedged between a canal and its offtake - no bank to sit on
            plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad], "fill": R.choice(RICE_GREENS)})

        # the CLOSING rank: hem EVERY column down onto the collector, so the whole field
        # edge sits on the drain (no dry sliver between the bottom paddies and their outfall).
        # The drain is diagonal, so the triangle between the uniform last regular row and the
        # drain varies across the sector - each column is tiled to its OWN drain fall.
        n = nsub
        ftop = rows[-1]

        def drain_meet(jj: int, ftop: float = ftop, n: int = n) -> float:  # bind loop vars (used within this iteration)
            """Fall where sub-bund line jj actually meets the drain - refined, because the
            bund drifts in u as it descends so the drain fall at the top sample is wrong."""
            fd = drain_f_at(ftop, jj, n)
            for _ in range(3):
                fd2 = _f_at_u(F, dpts, F.to_uf(*edge(fd, jj, n))[0])
                if fd2 is None:
                    break
                fd = fd2
            return fd

        for j in range(n):
            fm0, fm1 = drain_meet(j), drain_meet(j + 1)  # where each sub-bund reaches the collector...
            fb0 = fm0 - bank_at(F.to_uf(*edge(fm0, j, n))[0])  # ...held off to its BANK there
            fb1 = fm1 - bank_at(F.to_uf(*edge(fm1, j + 1, n))[0])
            depth = max(fb0, fb1) - ftop
            if depth < 6 * g:
                continue
            nlev = max(1, round(depth / (34 * g)))  # keep closer plots ~one row tall
            for li in range(nlev):
                fa0 = ftop + (fb0 - ftop) * li / nlev
                fa1 = ftop + (fb1 - ftop) * li / nlev
                fz0 = ftop + (fb0 - ftop) * (li + 1) / nlev
                fz1 = ftop + (fb1 - ftop) * (li + 1) / nlev
                quad = [edge(fa0, j, n), edge(fa1, j + 1, n), edge(fz1, j + 1, n), edge(fz0, j, n)]
                abuts = li == nlev - 1
                if abuts:
                    # snap the bottom edge onto the collector's BANK so the field edge lies along
                    # the ditch - as ONE straight bund clearing the whole span (bank_chord), not
                    # two independently-snapped vertices, which cut the corner at every bend
                    u3, u2 = F.to_uf(*quad[3])[0], F.to_uf(*quad[2])[0]
                    ch = bank_chord(u3, u2)
                    if ch is not None:
                        quad[3], quad[2] = F.to_xy(u3, ch[0]), F.to_xy(u2, ch[1])
                if math.dist(quad[0], quad[1]) < 8 * g:
                    continue
                if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                    continue
                if quad_in_supply(quad):
                    continue  # a closing-rank corner wedged against a ditch tail - no bank to sit on
                # only the level whose BOTTOM edge lies on the collector floods (the wettest,
                # lowest ground); an upper split level cascades into it and stays green - so a
                # blue plot always abuts the drain
                fill = FLOODED if (abuts and R.random() < 0.45) else R.choice(RICE_GREENS)
                # `low` is the TOPOGRAPHY; `fill` is only the PICTURE. FLOODED tints a random 45% of the
                # bottom level blue for texture, so it is not the low ground - it is a sample of it. The
                # land-use overlays must key off `low`, never off the tint (feature 010).
                # The band is the bottom TWO levels, not just the one on the drain: a real valley bottom
                # has a wet backswamp with width, not a one-plot hem. Its exact extent is unrecorded, so
                # this is a CALIBRATED LIBERTY (constitution XII) - see the note in `apply_land_use`.
                plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad], "fill": fill, "low": li >= nlev - 2})

    # HEM PASS: guarantee the whole field edge meets the drain. The per-sector closers cover
    # most of it, but a straight-line drain that dips below a shallower sector can leave a
    # residual sliver. Walk the drain; wherever there is field just above a segment but a bare
    # gap down to the drain, fill it with a thin plot snapped onto the collector. Localised -
    # it only fires on an actual gap, so it never disturbs the flooded closers.
    def inside_any(px: float, py: float) -> bool:
        return any(_pip(px, py, pl["poly"]) for pl in plots)

    for i in range(len(dpts) - 1):
        da, db = dpts[i], dpts[i + 1]
        seglen = math.dist(da, db)
        for s in [x / max(1, int(seglen / 22)) for x in range(int(seglen / 22) + 1)]:
            mx = da[0] + s * (db[0] - da[0])
            my = da[1] + s * (db[1] - da[1])
            u, fdr = F.to_uf(mx, my)
            just_in = F.to_xy(u, fdr - bank_at(u) - 4)  # just up-fall of the bank, on the field side
            if not (10 < just_in[0] < W - 10 and 10 < just_in[1] < H - 10):
                continue
            if inside_any(*just_in):
                continue  # already hemmed here
            # find the field edge above (up to a deep dip below a shallow sector); only hem
            # where the field genuinely reaches down toward this stretch of drain
            top = None
            for dd in range(20, 210, 8):
                if inside_any(*F.to_xy(u, fdr - dd)):
                    top = fdr - dd
                    break
            if top is None:
                continue  # no field above (tail/outside)
            uu, uv = u - 13, u + 13
            # A HEM PLOT RUNS WITH THE DITCH, NOT ACROSS IT (GM 2026-08-08: "I would expect the
            # earthen bunds bordering the ditch to be at the same angle as it"). These quads used
            # to be laid on the CONTOUR - one constant fall for the top edge and one for the
            # bottom - while the collector is fitted as f = a + b*u and so runs at atan(b) to the
            # contour (b <= 0.35, i.e. up to ~19 deg). Over the 26px u-span of one hem quad that is
            # ~9px of fall, which is several times the ditch's own width: every hem bund therefore
            # STARTED above the drain and ENDED below it, crossing the blue line and leaving a
            # brown tick poking out into bare ground. On Hoshizora the hem covers almost the whole
            # drain-side edge (14 of 31 plots there vs 4 from the closing rank), so this WAS the
            # field's edge - the sawtooth the GM saw. Sampling the drain at uu and uv separately
            # and running BOTH edges parallel to what it does between them costs one extra lookup
            # and makes the field hem onto the collector as one clean line.
            hem_ch = bank_chord(uu, uv, fdr)
            if hem_ch is None:  # pragma: no cover - fdr is a real fall, so both ends always resolve
                continue
            b0, b1 = hem_ch
            depth = (b0 + b1) / 2 - top
            if depth < 6 * g:
                continue  # the bank already reaches the field edge - nothing to hem
            levels = max(1, round(depth / 38))  # tile tall gaps into ~row plots
            for li in range(levels):
                fa0, fa1 = b0 - depth * (levels - li) / levels, b1 - depth * (levels - li) / levels
                fz0, fz1 = b0 - depth * (levels - li - 1) / levels, b1 - depth * (levels - li - 1) / levels
                quad = [F.to_xy(uu, fa0), F.to_xy(uv, fa1), F.to_xy(uv, fz1), F.to_xy(uu, fz0)]
                # the hem pass builds its quads directly (not through `edge`), so it is the fourth
                # producer that must honor the supply banks: where a delivery ditch's TAIL comes
                # down near the collector, an unguarded hem quad laps its stroke (Sawada ring 669,
                # 2026-08-15 - found by the gate the same day the other three sites were guarded).
                # Same treatment: slide the corners onto the bank, drop what still cannot clear.
                quad = [clear_supply(q[0], q[1], F.d[0], F.d[1]) for q in quad]
                if quad_in_supply(quad):
                    continue  # no bank ground between the branch tail and the collector - leave it to the floor
                plots.append({"poly": [(round(q[0], 1), round(q[1], 1)) for q in quad], "fill": R.choice(RICE_GREENS)})
    return plots


def _dry_fields(
    R: random.Random,
    F: _Frame,
    a_pts: Poly,
    W: float,
    H: float,
    keepout: Sequence[tuple[float, float, float]],
    plot: float = 46,
    band: tuple[float, float] = (70, 132),
    g: float = 1.0,
    furrow_spread: float = 1.1,
    grain_drift: float = 0.0,
) -> list[dict[str, Any]]:
    """DRY FIELDS (hatake) on the UPSLOPE margin the irrigation cannot command - the band just ABOVE the
    supply canal. Grain and pulses (barley/wheat, millet, buckwheat, field soy) in an irregular PATCHWORK of
    ridge-cultivated plots. Crop is assigned per-PLOT (not per-column) with spatial coherence - historical
    holdings were fragmented, so adjacent small plots carry different crops. To scale (1px=2ft): plot outlines
    are real, furrows stylised.

    The plots are RECTANGLES laid out AGAINST THE CANAL THEY BORDER - one edge runs ALONG the supply canal,
    the other PERPENDICULAR to it, extending upslope. They are NOT oriented to the paddy's fall grid (that gave
    a pronounced ~43deg shear, since the canal runs diagonally to the fall). Because the base edge rides the
    canal itself, adjacent plots ABUT continuously along it (no shear, no steps); only the UPSLOPE (outer) edge
    is ragged - a per-column depth. The base dips slightly BELOW the canal so it tucks under the paddy (drawn
    after). `band` = (min, max) upslope depth in px: a THIN fringe (default) for a water-rich valley floor.

    FURROWS run along the CONTOUR (perpendicular to the fall), the traditional ridge-along-contour that dams
    rain and checks runoff - so the furrow direction is the contour heading, varied per plot; `theta` per plot."""
    plots = []
    plot = plot * g  # the along-canal parcel width and the 36px row depth below are REAL-FEET
    # quantities tuned at the village grain (1px = 2ft; ~1 mu strips per Buck) - unscaled at a
    # coarser grain every hem parcel doubled in area, dry cells dwarfing the rice plots beside
    # them ("a number of pixels, not a number of feet" - the GM's catch, 2026-07-21; gated by
    # dry_plots_to_scale)
    theta0 = math.atan2(F.c[1], F.c[0]) + math.radians(grain_drift)  # contour heading (ridges follow it), drifted off the fall-line by the grain_drift knob (feature 005)

    def blocked(x: float, y: float) -> bool:
        return any((x - cx) ** 2 + (y - cy) ** 2 < rr * rr for (cx, cy, rr) in keepout)

    # tile the plots ALONG the canal by ARC-LENGTH (shared boundaries -> a contiguous margin), jittered widths
    seglen = [math.dist(a_pts[i], a_pts[i + 1]) for i in range(len(a_pts) - 1)]
    total = sum(seglen)

    def at(s: float) -> Pt:  # point on the canal polyline at arc-length s
        acc = 0.0
        for i, sl in enumerate(seglen):
            if acc + sl >= s or i == len(seglen) - 1:
                t = (s - acc) / sl if sl else 0.0
                ax, ay = a_pts[i]
                bx, by = a_pts[i + 1]
                return (ax + (bx - ax) * t, ay + (by - ay) * t)
            acc += sl
        return a_pts[-1]  # unreachable for a real (non-empty) canal; satisfies the type

    bounds = [0.0]
    while bounds[-1] < total - plot * 0.6:
        bounds.append(bounds[-1] + plot * R.uniform(0.9, 1.25))
    bounds[-1] = total
    if g != 1.0 and len(bounds) >= 2 and bounds[-1] - bounds[-2] > 1.35 * plot:
        # the snap-to-total stretch can hand the END cell up to ~1.85 plot widths (a ~0.38-acre
        # slab at city grain - the largest-parcel outlier, 2026-07-21); split it. Coarse grains
        # only: the vetted village maps carry the same (milder, in-band) artifact byte-stably.
        bounds.insert(-1, (bounds[-1] + bounds[-2]) / 2)

    # FURROW ANGLE varies PER PLOT (a mosaic of family strips): each plot drops its ridges into the LARGEST gap
    # between the angles of its already-placed NEIGHBORS, guaranteeing separation (drives dry_plot_furrows_vary).
    HW = furrow_spread
    placed: list[tuple[float, float, float]] = []
    ADJ2 = (
        56**2
    )  # the furrow-variety neighborhood stays UNSCALED: dry_plot_furrows_vary judges adjacency at this px radius on every map, and a generator that varies over a WIDER circle than the check demands is safely conservative
    prev_crop = R.choice(list(DRY_CROPS))
    berm = 8 * g  # a thin bund holds the dry plots just ABOVE (upslope of) the canal (grain-scaled: 8px was 16 real ft at the village grain; unscaled it left a 24 ft bare stripe on the city maps)
    for i in range(len(bounds) - 1):
        pL, pR = at(bounds[i]), at(bounds[i + 1])
        tx, ty = pR[0] - pL[0], pR[1] - pL[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl  # unit normal to the canal
        mx, my = (pL[0] + pR[0]) / 2, (pL[1] + pR[1]) / 2
        if F.to_uf(mx + nx, my + ny)[1] > F.to_uf(mx, my)[1]:  # point it UPSLOPE (decreasing fall)
            nx, ny = -nx, -ny
        depth = R.uniform(*band)  # ragged outer edge (per-column depth)
        nrow = max(1, round(depth / (36 * g)))
        for k in range(nrow):
            # per-plot crop with coherence: usually keep the last crop (holdings cluster), sometimes switch
            if R.random() < 0.45:
                prev_crop = R.choice(list(DRY_CROPS))
            crop = prev_crop
            fill, furrow = DRY_CROPS[crop]
            # PERPENDICULAR offset from the canal (both edges UPSLOPE of it): near = canal side, far = upslope.
            # The whole plot stays on the DRY side - it never dips across the canal onto the wet paddy.
            o_near = berm + depth * k / nrow
            o_far = berm + depth * (k + 1) / nrow
            quad = [(pL[0] + nx * o_far, pL[1] + ny * o_far), (pR[0] + nx * o_far, pR[1] + ny * o_far), (pR[0] + nx * o_near, pR[1] + ny * o_near), (pL[0] + nx * o_near, pL[1] + ny * o_near)]
            cx = sum(p[0] for p in quad) / 4
            cy = sum(p[1] for p in quad) / 4
            if any(p[0] < 12 or p[0] > W - 12 or p[1] < 12 or p[1] > H - 12 for p in quad):
                continue
            if blocked(cx, cy):
                continue
            lo, hi = theta0 - HW, theta0 + HW  # furrows stay within HW rad of the contour
            nb = sorted(min(hi, max(lo, t)) for (px, py, t) in placed if (cx - px) ** 2 + (cy - py) ** 2 < ADJ2)
            edges = [lo] + nb + [hi]
            gi = max(range(len(edges) - 1), key=lambda j: edges[j + 1] - edges[j])  # the widest gap between neighbors
            theta = min(hi, max(lo, (edges[gi] + edges[gi + 1]) / 2 + R.uniform(-0.03, 0.03)))
            placed.append((cx, cy, theta))
            plots.append({"poly": [(round(p[0], 1), round(p[1], 1)) for p in quad], "crop": crop, "fill": fill, "furrow": furrow, "theta": round(theta, 3)})
    return plots


def _bund_beans(R: random.Random, plots: list[dict[str, Any]], frac: float, spacing: float = 9.5, tol: float = 1.0, channels: list[dict[str, Any]] | None = None) -> Poly:
    """AZEMAME (bund soybeans): sub-pixel at 1px=2ft, so drawn symbolically as a green BEAD
    line along a fraction of the paddy bunds. Returns bead center points; the caller draws
    small BEAN_GREEN dots. ~`frac` of plots carry beaded bunds (not every bund had beans).

    A bead is DROPPED when a plot drawn LATER than its host buries it deeper than `tol` px
    (GM 2026-08-15, on Inashiro: green dots scattered mid-paddy). `_fill_wedges`' fillers
    deliberately lap up to ~12 real ft onto a neighbor and paint last - the lapped stretch of
    the neighbor's bund stroke is not visible ground on the finished map, so a bead line laid
    along it surfaces as dots floating in the filler's water. Beads must land on the bunds the
    finished paint actually shows, so each bead is tested against the plots that paint after
    its host and dropped when buried. `tol` is bead-scale rather than bund-scale: a bead
    within ~its own 1.4px drawn radius of the burying plot's edge still reads as sitting on
    that plot's seam. The gate mirrors this at double the tolerance (bund_beans_on_bunds), so
    a bead this filter allows cannot false-fire there through manifest rounding. The filter
    runs after all draws from R, so dropping beads never ripples the RNG stream.

    `channels` extends the same honesty to the ditch net (GM 2026-08-15, second pass): the net's
    strokes draw LATE - over every plot and bead - so a bead within a stroke's local half-width
    (tapering w -> w_tail along the run) + tol is buried under water paint and dropped. Pond
    burial is filtered at the draw site (draw_comb_field), where the pond geometry lives."""
    beans = []
    boxes = [(min(q[0] for q in p["poly"]), min(q[1] for q in p["poly"]), max(q[0] for q in p["poly"]), max(q[1] for q in p["poly"])) for p in plots]

    def buried(x: float, y: float, host: int) -> bool:
        for j in range(host + 1, len(plots)):
            bx0, by0, bx1, by1 = boxes[j]
            if not (bx0 - tol <= x <= bx1 + tol and by0 - tol <= y <= by1 + tol):
                continue
            poly = plots[j]["poly"]
            if _pip(x, y, poly) and min(_seg_d(x, y, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))) > tol:
                return True
        return False

    chans = []
    for c in channels or []:
        cpts = c["pts"]
        if len(cpts) < 2:
            continue
        cum = polyline_cum(cpts)
        pad = max(c["w"], c.get("w_tail", c["w"])) / 2 + tol
        cbox = (min(q[0] for q in cpts) - pad, min(q[1] for q in cpts) - pad, max(q[0] for q in cpts) + pad, max(q[1] for q in cpts) + pad)
        chans.append((cpts, cum, cum[-1] or 1.0, c["w"], c.get("w_tail", c["w"]), cbox))

    def wet(x: float, y: float) -> bool:
        for cpts, cum, tot, w0, w1, (bx0, by0, bx1, by1) in chans:
            if not (bx0 <= x <= bx1 and by0 <= y <= by1):
                continue
            for i in range(len(cpts) - 1):
                # taper measured at the segment head - within one segment it moves less than tol
                if _seg_d(x, y, cpts[i], cpts[i + 1]) < (w0 + (w1 - w0) * cum[i] / tot) / 2 + tol:
                    return True
        return False

    for pi, p in enumerate(plots):
        if R.random() > frac:
            continue
        poly = p["poly"]
        order = list(range(len(poly)))
        R.shuffle(order)
        for ei in order[: R.randint(1, 2)]:
            a = poly[ei]
            b = poly[(ei + 1) % len(poly)]
            nd = int(math.dist(a, b) / spacing)
            for t in range(1, nd):
                s = t / nd
                bx, by = round(a[0] + s * (b[0] - a[0]), 1), round(a[1] + s * (b[1] - a[1]), 1)
                if not buried(bx, by, pi) and not wet(bx, by):
                    beans.append((bx, by))
    return beans


def build_terraces(
    W: float,
    H: float,
    top: Pt,
    seed: int,
    down_deg: float = 90,
    n_terraces: int = 32,
    cross_width: float = 820,
    fall: float = 1500,
    ftpx: float = 1.0,
    cell_acres: float = PADDY_CELL_ACRES,
) -> dict[str, Any]:
    """Contour TERRACES (梯田): stacked thin paddies following the hillside contours, stepping downhill from
    `top` (the high catchment where water enters). Each terrace step is a gently curved band PERPENDICULAR to
    the fall, itself SPLIT ALONG THE CONTOUR into individual leveled cells; a supply channel runs down one
    flank and the stack cascades to a drain at the foot. Returns the same keys as `build_comb` so
    `Settlement.draw_comb_field` can draw it, plus `bund_lines` (the retaining-wall lip at each terrace's
    downhill edge, drawn by the gen). China-first grounding (research.md D4): the south-China / SE-Asia rice
    terrace (Yuanyang 元陽, Longsheng 龍勝) is THE field archetype for HILL ground.

    CELL SIZE (GM 2026-07-22): a terrace step is a ROW of SEPARATE small leveled paddies of varying size, NOT
    one field-wide band - a terrace paddy is a leveled cell like any other and the leveled-cell principle
    (water held even) makes it SMALL. Grounding: at Longsheng the LARGEST terrace is 0.62 mu (~0.10 acre) and
    most are far smaller (some hold three rice plants), 15,862 terraces in one village. So each step is split
    along the contour into cells of ~`cell_acres` (the universal PADDY_CELL_ACRES target, derived at this
    map's `ftpx`), and `n_terraces` is set so the step DEPTH stays shallow enough that a cell reads wider than
    deep (a terrace runs long along the contour, short down the fall). See settlements.md 'Paddy cell size'."""
    R = random.Random(seed)
    dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill unit
    ux, uy = -dy, dx  # cross-slope (contour) unit
    hw = cross_width / 2
    step = fall / n_terraces
    plots: list[dict[str, Any]] = []
    bund_lines: list[Poly] = []

    def contour_pt(s: float, amp: float, phase: float, t: float) -> Pt:
        # a point on the contour at downhill distance s and cross-slope parameter t in [-1, 1], curved by a
        # gentle sine (organic terracing); the hillside narrows slightly downhill (a spur), width tapers with s
        w = hw * (1.0 - 0.12 * s / fall)
        base = s + amp * math.sin(phase + t * math.pi * 1.15)
        return (top[0] + dx * base + ux * (t * w), top[1] + dy * base + uy * (t * w))

    def contour(s: float, amp: float, phase: float, n: int = 14) -> Poly:
        return [contour_pt(s, amp, phase, -1.0 + 2.0 * k / n) for k in range(n + 1)]

    # per-boundary curve params (adjacent terraces SHARE a boundary, so there is no gap between them)
    b_par = [(16.0 + R.uniform(-4, 7), R.uniform(0, 2 * math.pi)) for _ in range(n_terraces + 1)]
    # cell width along the contour, from the real-feet cell target and the step DEPTH (converted at ftpx):
    # a cell is cell_acres = cell_across x step, so cell_across = area / step (floored so a shallow step still
    # yields a sane count)
    cell_across = max(24.0, cell_acres * 43560.0 / (ftpx * ftpx) / step)
    for i in range(n_terraces):
        a_up, p_up = b_par[i]
        a_lo, p_lo = b_par[i + 1]
        s_up, s_lo = i * step, (i + 1) * step
        w_lo = hw * (1.0 - 0.12 * s_lo / fall)
        ncell = max(3, round(2 * w_lo / cell_across))  # this step's cell count, from its (tapered) width
        # split points across the contour (t in [-1, 1]); interior positions JITTERED so terraces vary in size
        ts = [-1.0] + [(-1.0 + 2.0 * k / ncell) + R.uniform(-0.7, 0.7) / ncell for k in range(1, ncell)] + [1.0]
        low = i >= n_terraces - 3  # the low terraces sit wettest - the topography, not the tint (feature 010)
        for k in range(ncell):
            t0, t1 = ts[k], ts[k + 1]
            poly = [contour_pt(s_up, a_up, p_up, t0), contour_pt(s_up, a_up, p_up, t1), contour_pt(s_lo, a_lo, p_lo, t1), contour_pt(s_lo, a_lo, p_lo, t0)]
            fill = FLOODED if low else R.choice(RICE_GREENS)
            plots.append({"poly": [(round(x, 1), round(y, 1)) for x, y in poly], "fill": fill, "low": low})
        bund_lines.append([(round(x, 1), round(y, 1)) for x, y in contour(s_lo, a_lo, p_lo)])  # the retaining lip at each terrace's low edge (full contour)

    # envelope: the two flank edges + the top and bottom contours (the outer boundary of the whole stack)
    top_c = contour(0.0, 22.0, 0.0)
    bot_c = contour(fall, 22.0, 0.0)
    envelope = [*top_c, *reversed(bot_c), top_c[0]]
    # a supply canal runs DOWN the high (t=-1) flank, then TURNS INTO the field foot (so its tail sits inside the
    # terraces and the source->field feed anchors); a drain collects along the foot and DESCENDS to the low-flank
    # outfall (so it flows downhill); a brook carries the drain off-map continuing the drain's own heading.
    # a gentle diagonal supply: from the sluice (high-west shoulder) descending toward the field-center foot, so
    # its fork sits INSIDE the terraces (the source->field feed anchors) with no hairpin turn
    n_sup = 8
    flank = []
    for k in range(n_sup + 1):
        f = k / n_sup
        s_pos = fall * 0.9 * f
        lat = -hw * 0.92 * (1.0 - f * 0.8)  # from the west flank toward the center as it descends
        flank.append((top[0] + dx * s_pos + ux * lat, top[1] + dy * s_pos + uy * lat))
    # the drain is a STRAIGHT descending collector along the foot (a straight amp=0 contour, not the wiggly
    # terrace bottom - following the sine would hairpin), sloping steadily to the low-flank outfall, then turning
    # downhill so the brook continues without an acute bend
    foot = contour(fall, 0.0, 0.0)  # (drain widens downstream below - the collector gathers; GM 2026-07-23)
    fe, fw = foot[0], foot[-1]  # east / west foot ends
    n_d = 8
    drain_pts = []
    for k in range(n_d + 1):
        f = k / n_d
        x = fe[0] + (fw[0] - fe[0]) * f + dx * 40 * f
        y = fe[1] + (fw[1] - fe[1]) * f + dy * 40 * f
        drain_pts.append((round(x, 1), round(y, 1)))
    drain_pts.append((round(drain_pts[-1][0] + dx * 66, 1), round(drain_pts[-1][1] + dy * 66, 1)))  # the outfall TURNS DOWNHILL
    sluice = flank[0]
    channels = [
        {"pts": [(round(x, 1), round(y, 1)) for x, y in flank], "role": "main", "w": 6.0, "w_tail": 3.0},
        {"pts": drain_pts, "role": "drain", "w": 1.5, "w_tail": 5.0},  # gathers fe -> fw: a THREAD at its head (see build_comb's drain), full at the low-flank outfall
    ]
    brook = [drain_pts[-1], (round(drain_pts[-1][0] + dx * 300, 1), round(drain_pts[-1][1] + dy * 300, 1))]  # straight downhill off-map
    # the toe stops at the ditch's BANK: the last terrace's low edge is a WIGGLY contour and the
    # collector along the foot is a STRAIGHT descending line, so they cross unless held apart. The
    # retaining LIP goes through the same pass - it is the thick brown line a reader actually sees,
    # and on Tanada it was the one standing in the drain (see `hem_to_bank`).
    for p in plots:
        p["poly"] = hem_to_bank(p["poly"], drain_pts, down_deg, 1.5, 5.0)
    bund_lines = [hem_to_bank(bl, drain_pts, down_deg, 1.5, 5.0) for bl in bund_lines]
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
    round_channel_joints(channels)  # earthen water turns on a swept bend, not a mitred corner
    return {
        "channels": channels,
        "plots": plots,
        "threads": [],
        "drain": drain_pts,
        "brook": brook,
        "envelope": [(round(x, 1), round(y, 1)) for x, y in envelope],
        "acres": acres,
        "dry_plots": [],
        "dry_acres": 0.0,
        "bund_beans": [],
        "bund_lines": bund_lines,
        "furrows_vary": False,
        "sluice": (round(sluice[0], 1), round(sluice[1], 1)),
    }


def build_polder(
    W: float,
    H: float,
    origin: Pt,
    seed: int,
    down_deg: float = 90,
    rows: int = 11,
    cols: int = 6,
    cell: float = 150,
    parcel_mix: tuple[float, float, float] = (0.52, 0.16, 0.12),
    gap: tuple[float, float] = (1.5, 4.0),
    split_gap: float | None = None,
    edge_wander: float = 0.0,
    mosaic: float = 0.0,
    line_wander: float = 0.10,
    organic: tuple[float, float] = (0.05, 0.02),
) -> dict[str, Any]:
    """POLDER GRID (圩田 wei-tian / reclaimed-marsh grid): a rectilinear block of paddies on flat reclaimed
    low ground, an orthogonal ditch-grid module inside a perimeter dike. Returns build_comb-compatible keys
    so `Settlement.draw_comb_field` draws it. China-first grounding (research.md D4): the wei-tian polder of
    the lower-Yangtze lake plains (Taihu / Dongting) is THE field archetype for LOW reclaimed ground -
    orthogonal, surveyed, big-block, the planned opposite of the old organic comb; water enters a corner, a
    perimeter feeder rings the block, and it drains to the low corner.

    PARCEL FABRIC (researched + source-verified 2026-07-21; drives `polder_parcels_vary`). The surveyed
    chessboard was the CANAL GRID, not the parcels: Northern Song sources describe the Taihu tangpu 塘浦
    polder lattice at kilometer scale (canals every 5-10 li), but inside it private tenure fragmented land
    continuously - mid-Qing Jiangnan farms averaged ~10 mu scattered over several parcels, and Buck's
    pre-mechanization survey (1929-33) found a mean parcel of ~600 m2 (~1 mu), roughly rectangular where it
    fronted a straight ditch and irregular elsewhere. Household-by-household dike-pond digging (挖塘培基,
    research.md D2) likewise yields a patchwork accreted over centuries, never 66 identical cells. Fields of
    one uniform machine-sized rectangle are a 20th-century consolidation look (Japan's 1963 hojo seibi 30m x
    100m standard; PRC land-consolidation campaigns). SO: the ditch-grid MODULE stays straight and uniform
    (that part was genuinely surveyed, and the perimeter dike is dead straight), while the parcels inside it
    vary - most module bays split into 2-3 oblong strips, a few merge into double-bay parcels (ALONG the
    fall, so parcels never cross a lateral), and interior bund nodes jitter a touch so minor bunds waver
    while main ditches hold their line.

    TRUE-SCALE SIZING (GM directive 2026-07-21: no legibility inflation - these maps are perfectly to
    scale, 1 px = 1 ft at hamlet scale; sizes verified by research the same day):
    - RICE polder (`parcel_mix` default (0.52, 0.16, 0.12)): target mean parcel ~1 mu (~600 m2 ~6,460
      sq ft; Buck 1929-33: 0.34 ha over 5.6 plots), common range ~0.2-3 mu, square to ~1:3 oblong. A
      ~110 ft module hits this: whole bay ~1.9 mu, halves ~0.9 mu, thirds ~0.6 mu, rare merges ~3.7 mu.
      `gap` default (1.5, 4.0): between-row gaps 3 px (~1 m walking bund, attested 20-50 cm + stroke) and
      8 px column corridors carrying the 3.2 px lateral (a bang 浜 field ditch + spoil banks, ~2.4 m).
      A GAP IS ONLY AS WIDE AS WHAT RUNS IN IT (`split_gap`, GM 2026-07-24): `gap[1]` is the width of a
      DITCH corridor, so it belongs only on the module column lines, where a lateral actually runs. The
      lines INSIDE a bay - where a holding was split into side-by-side strips - carry no ditch, just a
      walking bund, so they take `split_gap` (default `gap[0]`, the same 3 ft the row-edge bunds get).
      Drawing them at the corridor width put a bare 8 ft strip between two strips of one holding, which
      is both wider than any attested plain aze and a promise of water that is not there.
    - DIKE-POND (mulberry_dike_fishpond archetype): traditional ponds were 0.4-0.6 ha (6-9 mu) oblong
      rectangles, dikes 6-10 m wide (Ruddle & Zhong / FAO; CAVEAT: earliest well-attested sizes are
      Republican-to-1980s surveys of the traditional landscape, not Ming/Qing documents). A ~160 ft
      module with merge-heavy mix (e.g. (0.10, 0.0, 0.60)) yields mostly 160x320 ft (~0.48 ha, 1:2)
      ponds with square ~2.4-mu minority ponds, and `gap` ~(11, 11) draws ~22 ft (~6.7 m) mulberry dikes.
    - The per-parcel ditch FRONTAGE (every basin on a jing/bang ditch; polder_parcels_front_water) is
      qualitatively well-attested; the exact lateral spacing is a REASONED RECONSTRUCTION (one lateral
      per module line, so no basin sits farther than a basin-width from water) - no published pre-modern
      metric spacing was found."""
    R = random.Random(seed)
    dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill (row) unit
    ux, uy = dy, -dx  # cross (column) unit - the grid extends to the +x/+cross side of the origin
    ox, oy = origin
    span_s, span_t = rows * cell, cols * cell

    # EDGE WANDER (GM 2026-07-22): a hand-dug polder is NOT a machine-perfect axis-aligned rectangle - its
    # dikes follow the old water edge, so they run at a slight ANGLE and gently CHANGE direction with the
    # ground (the 'fish-scale polder' 鱼鳞圩 read; a dead-straight right-angled block is the post-1949
    # industrial shape). `edge_wander` (0 = the old dead-straight block) drives a SEPARABLE low-frequency
    # deformation of the whole (s, t) grid: cwarp(s) shifts every contour-row in the CROSS direction (so all
    # N-S dikes AND every interior column line share it and stay parallel while the block bends), fwarp(t)
    # shifts every column in the FALL direction (E-W dikes + row lines, likewise). The linear term is an
    # overall tilt (the dikes are not axis-perfect); the sines are the topology-following bends. Because
    # EVERY point - envelope, parcels, ring canal, laterals, and the dike that follows the envelope - is
    # placed through grid(), the whole polder warps as ONE coherent piece and each field edge stays parallel
    # to its dike section (research 2026-07-22, settlements.md 'Polder edge wander'). Phases come from a
    # SEPARATE rng so the main draw stream (and every edge_wander=0 map) stays byte-identical.
    Rw = random.Random(seed ^ 0x5EED)
    ac = af = cell * 0.9 * edge_wander  # cross / fall wander amplitude (~a module at edge_wander ~ 1)
    tilt_s, tilt_t = Rw.uniform(-1, 1) * 0.05 * edge_wander, Rw.uniform(-1, 1) * 0.05 * edge_wander
    cp1, cp2 = Rw.uniform(0, math.tau), Rw.uniform(0, math.tau)  # cross-warp phases
    fp1, fp2 = Rw.uniform(0, math.tau), Rw.uniform(0, math.tau)  # fall-warp phases

    def cwarp(s: float) -> float:
        z = s / max(1.0, span_s)
        return tilt_s * s + ac * (0.6 * math.sin(math.tau * 0.8 * z + cp1) + 0.4 * math.sin(math.tau * 1.7 * z + cp2))

    def fwarp(t: float) -> float:
        z = t / max(1.0, span_t)
        return tilt_t * t + af * (0.6 * math.sin(math.tau * 0.7 * z + fp1) + 0.4 * math.sin(math.tau * 1.6 * z + fp2))

    def grid(s: float, t: float) -> Pt:
        cs, fs = cwarp(s), fwarp(t)
        return (ox + dx * (s + fs) + ux * (t + cs), oy + dy * (s + fs) + uy * (t + cs))

    # jittered bund-node lattice in (s, t) space. Perimeter nodes stay PINNED so the block envelope is
    # straight; only interior nodes waver (minor bunds). A narrow RING corridor (~14 px ~14 ft) is reserved
    # inside the dike on ALL FOUR sides for the polder's INNER RING CANAL (圩内河, "一河围田 / one river
    # surrounds the field"): the trunk distribution+collection channel runs a ring on the INSIDE toe of the
    # perimeter dike, on the field side - outside the dike is the wild lake/creek the dike holds back, so no
    # channel runs out there, and water crosses the dike ONLY at gated sluices (斗门) at the inlet + outfall
    # (research 2026-07-22, settlements.md 'Polder ring canal'). So the parcel lattice is inset to
    # [ring, span-ring] on BOTH axes and the ring canal runs in the margins just inside the dike; the
    # envelope keeps the full span (the dike's inner face sits on it).
    J = 6.0
    RING = 18.0
    t_step = (span_t - 2 * RING) / cols
    s_step = (span_s - 2 * RING) / rows

    def tt(c: int) -> float:
        return RING + c * t_step

    def ss(r: int) -> float:
        return RING + r * s_step

    # MOSAIC knob (GM 2026-07-22, researched): the 圩田 lower-Yangtze polder was a SURVEYED rectilinear grid,
    # but the Pearl-delta 桑基魚塘 dike-pond accreted household-by-household (挖塘培基) into a MOSAIC of varied
    # ponds fitted around MEANDERING interior creeks - scholarship describes the historical landscape as
    # "mosaic-like constructed ponds with meandering natural river systems, [with] the boundary between
    # constructed and natural blurred" (research 2026-07-22; settlements.md 'Polder mosaic vs grid'). `mosaic`
    # (0 = the clean surveyed grid, the default) displaces the INTERIOR bund-node lattice by a smooth
    # CORRELATED field, tapered to 0 at the pinned perimeter so the envelope + dike stay put: neighbouring
    # nodes move together, so the lattice lines stay continuous but BEND - the interior laterals become
    # meandering creeks and the parcels skew to trapezoids. Both are historically-grounded looks, so the knob
    # makes two same-type polders read differently (map variety). The displacement draws from a SEPARATE rng
    # so the main plot/fill stream - and every mosaic=0 map - stays byte-identical.
    Rm = random.Random(seed ^ 0x3059)
    _mph = [Rm.uniform(0, math.tau) for _ in range(4)]
    _mamp = mosaic * cell * 0.32

    def mdisp(r: int, c: int) -> tuple[float, float]:
        if mosaic <= 0 or not (0 < r < rows) or not (0 < c < cols):
            return (0.0, 0.0)  # the perimeter stays pinned; parcels never leave the envelope
        zr, zc = r / rows, c / cols
        taper = math.sin(math.pi * zr) * math.sin(math.pi * zc)
        ds = _mamp * taper * (math.sin(math.tau * 1.3 * zr + _mph[0]) + 0.6 * math.sin(math.tau * 2.1 * zc + _mph[1]))
        dt = _mamp * taper * (math.sin(math.tau * 1.1 * zc + _mph[2]) + 0.6 * math.sin(math.tau * 1.9 * zr + _mph[3]))
        return (ds, dt)

    # EVERY BUND LINE WANDERS ON ITS OWN (GM 2026-07-25: "even human-made bunds won't be perfectly
    # parallel to one another in the way that these are depicted"). This is the root of the machine-made
    # read, and it outranks the corner treatment: `edge_wander` and `mosaic` both warp the lattice
    # COHERENTLY - they bend the block as one piece, on purpose, so that each field edge stays parallel
    # to its own section of dike - which means every interior line keeps exactly its neighbours' shape
    # and the spacing between two bunds never changes. Real fragmented tenure does not look like that: a
    # bund is laid by eye between two points, by a different household in a different decade, so
    # neighbouring lines drift, converge, and open out again, and the strip between them is wider at one
    # end than the other. So each row line and each column line gets its OWN low-frequency profile,
    # amplitude and phase drawn per line. Because a node is shared by its row and its column, the
    # lattice stays consistent - lines still meet, parcels are still quads, the laterals that follow the
    # column nodes just meander with them. Each profile is tapered to zero at both ends of its line and
    # suppressed entirely on the four boundary lines, so the envelope, the perimeter dike, and the ring
    # canal are untouched. Drawn from a separate rng, so `line_wander=0` reproduces the old lattice.
    RW = random.Random(seed ^ 0x11FE)
    _lwa = line_wander * cell
    _rowp = [(RW.uniform(0.35, 1.0) * _lwa * RW.choice((-1.0, 1.0)), RW.uniform(0, math.tau), RW.uniform(0.9, 2.3)) for _ in range(rows + 1)]
    _colp = [(RW.uniform(0.35, 1.0) * _lwa * RW.choice((-1.0, 1.0)), RW.uniform(0, math.tau), RW.uniform(0.9, 2.3)) for _ in range(cols + 1)]

    def lwander(r: int, c: int) -> tuple[float, float]:
        ds = dt = 0.0
        if 0 < r < rows and cols:
            amp, ph, k = _rowp[r]
            u = c / cols
            ds = amp * math.sin(math.pi * u) * math.sin(ph + k * math.pi * u)
        if 0 < c < cols and rows:
            amp, ph, k = _colp[c]
            u = r / rows
            dt = amp * math.sin(math.pi * u) * math.sin(ph + k * math.pi * u)
        return (ds, dt)

    def _node(r: int, c: int) -> tuple[float, float]:
        js = R.uniform(-J, J) if 0 < r < rows else 0.0  # draw order (s then t) matches the old lattice exactly
        jt = R.uniform(-J, J) if 0 < c < cols else 0.0
        md = mdisp(r, c)
        lw = lwander(r, c)
        return (ss(r) + js + md[0] + lw[0], tt(c) + jt + md[1] + lw[1])

    nodes: list[list[tuple[float, float]]] = [[_node(r, c) for c in range(cols + 1)] for r in range(rows + 1)]

    def lerp(a: tuple[float, float], b: tuple[float, float], f: float) -> tuple[float, float]:
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    g_s, g_t = gap  # (row-edge bund gap, column-edge ditch-corridor gap) - see TRUE-SCALE SIZING above
    g_x = g_s if split_gap is None else split_gap  # intra-bay split line: a walking bund, no ditch

    def inset(quad: list[tuple[float, float]], gt_lo: float, gt_hi: float) -> list[tuple[float, float]]:
        # the gap = the bund / mulberry dike between parcels (and the ditch corridor on column edges).
        # Bbox-scaling about the centroid is exact for the axis-aligned case and near-exact for these
        # gently jittered quads (all built in (s, t) space). The two CROSS-direction gaps are passed in
        # per parcel, because a bay's outer edges sit on the module column lines (ditch corridors) while
        # a side-by-side split inside it does not - see `split_gap` in TRUE-SCALE SIZING above.
        s_lo, s_hi = min(p[0] for p in quad), max(p[0] for p in quad)
        t_lo, t_hi = min(p[1] for p in quad), max(p[1] for p in quad)
        cs = (s_lo + s_hi) / 2
        ks = max(0.0, s_hi - s_lo - 2 * g_s) / max(1e-9, s_hi - s_lo)
        kt = max(0.0, t_hi - t_lo - gt_lo - gt_hi) / max(1e-9, t_hi - t_lo)
        return [(cs + (p[0] - cs) * ks, t_lo + gt_lo + (p[1] - t_lo) * kt) for p in quad]

    # The organic pass draws from its OWN rng so that adding it left every parcel CORNER byte-identical
    # (the main stream R still drives the lattice jitter, splits, merges, and ring waver in the same
    # order it always did) - only the outline between those corners softens.
    RO = random.Random(seed ^ 0x0BA5E)
    o_fillet, o_bow = organic
    plots: list[dict[str, Any]] = []

    def emit(quad_st: list[tuple[float, float]], r: int, gt_lo: float = -1.0, gt_hi: float = -1.0) -> None:
        low = r >= rows - 2  # the lowest rows of the polder (feature 010)
        gt_lo, gt_hi = (g_t if gt_lo < 0 else gt_lo), (g_t if gt_hi < 0 else gt_hi)
        quad = [grid(s, t) for s, t in inset(quad_st, gt_lo, gt_hi)]
        # cap the edge bow so two neighbours can never bow into contact: each side of a shared bund may
        # eat at most half of what the insets opened, less a 1 px hairline the drawn aze strokes keep
        cap = max(0.0, min(g_s, gt_lo, gt_hi) - 0.5)
        poly = organic_parcel(quad, RO, fillet=o_fillet * cell, bow=o_bow, bow_cap=cap)
        fill = FLOODED if low else R.choice(RICE_GREENS)
        plots.append({"poly": [(round(x, 1), round(y, 1)) for x, y in poly], "quad": [(round(x, 1), round(y, 1)) for x, y in quad], "fill": fill, "low": low})

    p_split2, p_split3, p_merge = parcel_mix
    for c in range(cols):
        r = 0
        while r < rows:
            # an occasional double-bay parcel (merged holding). Merges run ALONG the fall (never across a
            # column line) so the lateral ditches on the column lines never cut through a parcel, and never
            # straddle the low-band boundary so the `low` flag stays a whole-parcel truth.
            tall = r + 1 < rows and ((r + 1 >= rows - 2) == (r >= rows - 2)) and R.random() < p_merge
            r1 = r + (2 if tall else 1)
            tl, tr = nodes[r][c], nodes[r][c + 1]
            bl, br = nodes[r1][c], nodes[r1][c + 1]
            u = R.random()
            n_cuts = 0 if tall else (2 if u < p_split3 else (1 if u < p_split3 + p_split2 else 0))
            if n_cuts == 0:
                emit([tl, tr, br, bl], r)
            else:
                cuts = [R.uniform(0.38, 0.62)] if n_cuts == 1 else [R.uniform(0.26, 0.4), R.uniform(0.6, 0.74)]
                fs = [0.0, *cuts, 1.0]
                if R.random() < 0.5:  # cut ACROSS the fall - sub-parcels stack down the block
                    # every cross-fall line (module row edge or intra-bay cut alike) is a plain walking
                    # bund at g_s, so these need no per-parcel gap override
                    for f0, f1 in zip(fs, fs[1:], strict=False):
                        emit([lerp(tl, bl, f0), lerp(tr, br, f0), lerp(tr, br, f1), lerp(tl, bl, f1)], r)
                else:  # cut ALONG the fall - side-by-side strips
                    # only the OUTER two edges sit on module column lines (where a lateral runs); the
                    # cuts between the strips are bunds, so they take the narrow `g_x` gap
                    for k, (f0, f1) in enumerate(zip(fs, fs[1:], strict=False)):
                        emit([lerp(tl, tr, f0), lerp(tl, tr, f1), lerp(bl, br, f1), lerp(bl, br, f0)], r, g_t if k == 0 else g_x, g_t if f1 == 1.0 else g_x)
            r = r1
    # densify the envelope so the edge-wander CURVATURE is carried into the drawn field, the perimeter dike
    # that follows it, and the recorded outline - 4 bare corners would read as straight edges between them
    _ecorn = [(0.0, 0.0), (0.0, span_t), (span_s, span_t), (span_s, 0.0)]
    envelope = []
    for _i in range(4):
        _ea, _eb = _ecorn[_i], _ecorn[(_i + 1) % 4]
        for _k in range(12):
            envelope.append(grid(_ea[0] + (_eb[0] - _ea[0]) * _k / 12, _ea[1] + (_eb[1] - _ea[1]) * _k / 12))
    envelope.append(envelope[0])
    # THE WATER NETWORK IS A CONNECTED INNER RING CANAL (researched 2026-07-22; GM-flagged the old feeder,
    # which ran at s=-12 / s=span+12 - OUTSIDE the envelope, so once the dike became a wide earthwork band
    # the trunk canal sat buried IN the dike). The correct polder hydrology: the trunk canal rings the block
    # on the INSIDE toe of the dike (圩内河, "one river surrounds the field") - feeder along the high inner
    # toe, drain along the low inner toe, a toe ditch down each side inner toe - and water crosses the dike
    # ONLY at gated sluices (the pond inlet at the high corner + the brook outfall at the low corner). The
    # ring runs in the ~14 px inner-toe margin (s or t = RING*0.5) just inside the envelope, so it never
    # overlaps the dike. The trunk line is organized-but-organic: long runs that read straight-ish, GENTLY
    # WAVY (a surveyed dug canal wavers with terrain and repair; crescent/bow trunk forms are attested) with
    # rounded corners, NOT a hard 90-degree CAD grid - the finer laterals (following the jittered bund lines)
    # are visibly crookeder. Feeder -> laterals -> drain stays one connected system; every parcel fronts one.
    fi, di = RING * 0.5, span_s - RING * 0.5  # feeder / drain inner-toe s-lines
    phf = R.uniform(0, math.tau)

    def waver(pts_st: list[tuple[float, float]], along: str, amp: float, ph: float) -> list[tuple[float, float]]:
        # Gently wave a trunk run: offset the CROSS coord by a low-freq sine so the canal is not dead
        # straight - TAPERED to zero at both ends of the run, so each side still starts and finishes
        # exactly on the fillet endpoints it continues from. Untapered, the sine displaced a side's
        # first/last point by up to `amp` off its neighbour's fillet end, opening a small kink at each
        # ring corner (up to 3.7px on Kuwabata - enough for the toe collector's tip to leave the drawn
        # band of the trunk it joins). The ring canal is a CLOSED loop; its corners must actually close.
        out = []
        m2 = max(1, len(pts_st) - 1)
        for i, (s, t) in enumerate(pts_st):
            w = amp * math.sin(math.pi * i / m2) * math.sin(ph + 2.2 * math.pi * i / m2)
            out.append((s + w, t) if along == "t" else (s, t + w))
        return out

    # FILLETED CORNERS (research 2026-07-22): an earthen canal EASES its bends - a hard 90-degree interior
    # corner scours the outer bank and silts the inner, so FAO sets a minimum bend radius of tens of times
    # the width; a polder corner can't honor the full ideal but it gets a generous FILLET, never a right
    # angle. So the ring is a rounded rectangle: each corner is a quadratic-bezier fillet of reach `cr`.
    cr = RING * 0.9
    corners = [(fi, fi), (fi, span_t - fi), (di, span_t - fi), (di, fi)]  # NW, NE, SE, SW (clockwise)

    def _u(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        vx, vy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(vx, vy) or 1.0
        return (vx / ln, vy / ln)

    def _bz(a: tuple[float, float], c: tuple[float, float], b: tuple[float, float], f: float) -> tuple[float, float]:
        return ((1 - f) ** 2 * a[0] + 2 * (1 - f) * f * c[0] + f * f * b[0], (1 - f) ** 2 * a[1] + 2 * (1 - f) * f * c[1] + f * f * b[1])

    sides_st: list[list[tuple[float, float]]] = []  # side i runs corner[i] -> corner[i+1], its fillet AT corner[i+1] included
    for i in range(4):
        c0, c1, c2 = corners[i], corners[(i + 1) % 4], corners[(i + 2) % 4]
        d0, d1 = _u(c0, c1), _u(c1, c2)
        a0 = (c0[0] + d0[0] * cr, c0[1] + d0[1] * cr)  # this side begins after corner[i]'s fillet
        a1 = (c1[0] - d0[0] * cr, c1[1] - d0[1] * cr)  # ...its straight part ends before corner[i+1]'s fillet
        run = [(a0[0] + (a1[0] - a0[0]) * k / 6, a0[1] + (a1[1] - a0[1]) * k / 6) for k in range(7)]
        run = waver(run, "s" if abs(d0[0]) > abs(d0[1]) else "t", 3.5, phf + i * 1.7)  # gentle waver
        b1 = (c1[0] + d1[0] * cr, c1[1] + d1[1] * cr)  # the fillet arc a1 -> corner[i+1] -> next side's start
        sides_st.append(run + [_bz(a1, c1, b1, k / 6) for k in range(1, 7)])

    def _mk(pts_st: list[tuple[float, float]], role: str, w: float, wt: float) -> dict[str, Any]:
        return {"pts": [(round(x, 1), round(y, 1)) for x, y in [grid(s, t) for s, t in pts_st]], "role": role, "w": w, "w_tail": wt}

    # The ring is a CLOSED loop (feeder top + two toe sides + drain bottom), all 4 corners FILLETED. The
    # INLET is the source->field hairline itself: draw_comb_field draws it from the pond to channels[0]'s far
    # end, so the feeder is recorded NW-END-LAST (reversed) - the hairline then crosses the dike from the pond
    # straight onto the feeder's NW corner (the north inlet sluice), no dangling stub. The OUTFALL is the brook,
    # which taps the MIDDLE of the drain (far from either drain endpoint, so it reads as a mid-run offtake, not
    # a hard corner) and runs off-map south through the dike (the south sluice).
    # the feeder is recorded NW-end-last, then extended with a short INLET STUB up through the dike to the
    # pond rim - a visible sluice channel so the pond plainly charges the ring (the source->field hairline
    # anchors at the stub's far end for the topology)
    # the inlet stub angles up toward the NW corner (t -> fi), not straight out at constant t: under
    # edge_wander a constant-t stub met the feeder at a ~90 deg bend that the warp tipped past 90 into an
    # acute turn (water_channels_obtuse_turns); heading toward the corner keeps the feeder->stub bend obtuse.
    feeder_rev = [*reversed(sides_st[0]), (-52.0, fi)]
    sluice = grid(fi, fi)  # the nominal NW inlet corner

    # `seg` tags each ring side so footbridge placement is side-aware (research 2026-07-22: crossings cluster
    # on the SETTLEMENT side, not all four): e_toe is the settlement (east) side, the rest are unsettled.
    def _seg(pts_st: list[tuple[float, float]], role: str, w: float, wt: float, seg: str) -> dict[str, Any]:
        d = _mk(pts_st, role, w, wt)
        d["seg"] = seg
        return d

    channels = [
        _seg(feeder_rev, "main", 5.0, 4.0, "feeder"),  # feeder (top), NW-end LAST so the source->field hairline anchors at the pond side
        _seg(sides_st[1], "lateral", 3.4, 3.0, "e_toe"),  # east toe collector (the SETTLEMENT side)
        _seg(sides_st[2], "drain", 5.0, 5.0, "drain"),  # bottom = drain collector (cross-slope)
        _seg(sides_st[3], "lateral", 3.4, 3.0, "w_toe"),  # west toe collector
    ]

    def _s_on_side(side_st: list[tuple[float, float]], tq: float) -> float:
        # the s-coordinate where a ring side (mostly t-monotone) crosses cross-coord tq - the POSITION
        # GUESS for a lateral's end, so it meets the feeder/drain at roughly its own column line rather
        # than wherever the nearest-point projection below would slide it.
        for i in range(len(side_st) - 1):
            ta, tb = side_st[i][1], side_st[i + 1][1]
            if (ta <= tq <= tb or tb <= tq <= ta) and tb != ta:
                k = (tq - ta) / (tb - ta)
                return side_st[i][0] + k * (side_st[i + 1][0] - side_st[i][0])
        return side_st[0][0] if abs(tq - side_st[0][1]) < abs(tq - side_st[-1][1]) else side_st[-1][0]

    # SNAP the lateral ends onto the feeder (top) + drain (bottom) centerlines so each lateral FEEDS the
    # trunk at a clean T instead of poking a stub past it. The snap must happen in DRAWN (xy) space, not
    # in (s, t): grid() is a NONLINEAR warp (edge_wander's cwarp/fwarp, plus mosaic), so a point sitting
    # exactly on the straight st-space chord between two trunk vertices maps a few px OFF the straight
    # xy-space segment the trunk is actually drawn along. That residual is why Enokida's laterals still
    # crossed the ring and stuck ~2-5 px past it, reading as a 4-way intersection rather than a junction
    # (GM 2026-07-24; the earlier st-space-only fix, GM 2026-07-22, removed the gross stubs but not this).
    # So: take _s_on_side as the position guess, map to xy, then project the tip onto the trunk's own
    # drawn polyline - exact whatever the warp does. Gated by water_channels_join_not_cross.
    feeder_xy = [grid(s, t) for s, t in sides_st[0]]
    drain_xy = [grid(s, t) for s, t in sides_st[2]]

    def _onto(pt: Pt, poly: list[Pt]) -> Pt:
        """The closest point on a drawn polyline - snaps a lateral's tip onto the trunk centerline."""
        best, bd = pt, float("inf")
        for i in range(len(poly) - 1):
            (ax, ay), (bx, by) = poly[i], poly[i + 1]
            dx, dy = bx - ax, by - ay
            ln = dx * dx + dy * dy
            k = 0.0 if ln == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / ln))
            cand = (ax + k * dx, ay + k * dy)
            dist = math.hypot(pt[0] - cand[0], pt[1] - cand[1])
            if dist < bd:
                best, bd = cand, dist
        return best

    for c in range(1, cols):  # the laterals, one per interior column line, feeder (top) -> drain (bottom)
        tc = tt(c)
        lat_pts = [(_s_on_side(sides_st[0], tc), tc), *[nodes[r][c] for r in range(rows + 1)], (_s_on_side(sides_st[2], tc), tc)]
        lat_xy = [grid(s, t) for s, t in lat_pts]
        lat_xy[0], lat_xy[-1] = _onto(lat_xy[0], feeder_xy), _onto(lat_xy[-1], drain_xy)
        d = {"pts": [(round(x, 1), round(y, 1)) for x, y in lat_xy], "role": "lateral", "w": 3.2, "w_tail": 2.4, "seg": "lateral"}
        channels.append(d)
    out_t = span_t * 0.5  # the outfall taps the drain at mid-south and runs off-map downhill
    brook_start, brook_dir = grid(di, out_t), grid(di + 40, out_t)
    brook = [(round(brook_start[0], 1), round(brook_start[1], 1)), (round(brook_dir[0], 1), round(brook_dir[1], 1))]
    # WHERE THE WATER CROSSES THE DIKE: the inlet sluice (top edge, at the feeder's NW corner) and the outfall
    # sluice (bottom edge, at the drain's mid-south tap). The gen hands these to perimeter_dike so the dike is
    # NOTCHED (a dug gap) there instead of the channel running OVER the top of the earthwork bank (GM 2026-07-22).
    dike_sluices = [grid(0.0, fi + cr), grid(span_s, out_t)]
    # THE FIELD FLOOR (the green greenery) is the INTERIOR of the ring canal - the outermost irrigated
    # channels - NOT the dike-boundary envelope (GM 2026-07-22). Under edge_wander the ring wavers, and a
    # separate envelope rectangle drifted in and out of it; concatenating the 4 ring sides gives the closed
    # inner-toe loop, so the green is bounded exactly by the ring and the canal draws on top of it.
    floor = [grid(s, t) for s, t in (sides_st[0] + sides_st[1] + sides_st[2] + sides_st[3])]
    # THE PARCELS STOP AT THE COLLECTOR'S BANK. `hem_to_bank`'s own docstring names this engine as
    # one of the three that need the pass - "the collector IS the polder's bottom side, so the
    # parcels front it directly and float error alone put a vertex a half-pixel past" - and the call
    # was simply never made here, only in the comb, the terraces and the ribbon. It surfaced on a
    # scripted polder (2026-08-13): 6 bund vertices drawn inside the drain's stroke on 2 of 12 grid
    # shapes, a bund laid under the ditch. The pass only LIFTS vertices that breach, so a grid whose
    # parcels already clear the bank is returned untouched - Enokida and Kuwabata are byte-identical.
    _drn = [(round(x, 1), round(y, 1)) for x, y in [grid(s, t) for s, t in sides_st[2]]]
    # ...at the collector's OWN widths. The first version passed the terraces' 1.5 -> 5.0 taper,
    # copied from the call above it, and this drain is 5.0 throughout - so the pass under-lifted
    # along most of its run and the bunds it was added to clear stayed in the stroke. The widths a
    # lift measures against have to be the widths the ditch is drawn at, which are the ones recorded
    # on its own channel.
    # A RING THAT CLOSES ON A SHORT STUB MAKES AN ACUTE TURN, and water does not (2026-08-15).
    # The perimeter feeder is built by walking the block's sides, so on some edge-wander draws its
    # last vertex lands a short way back ALONG the run it just made - measured on a scripted polder:
    # ...(2093,1958) -> (2059,1838) -> (2120,1837), a 61 px stub doubling back at 75 degrees, which
    # `water_channels_obtuse_turns` reads (correctly) as impossible topology. A trailing stub carries
    # no water anywhere the run has not already been, so it is dropped rather than swept: rounding it
    # would keep the hairpin and merely soften its corner.
    for _c in channels:
        _pts = _c.get("pts") or []
        while len(_pts) >= 3:
            _a, _b, _cc = _pts[-3], _pts[-2], _pts[-1]
            _v1 = (_a[0] - _b[0], _a[1] - _b[1])
            _v2 = (_cc[0] - _b[0], _cc[1] - _b[1])
            _n1 = math.hypot(*_v1) or 1.0
            _n2 = math.hypot(*_v2) or 1.0
            _ang = math.degrees(math.acos(max(-1.0, min(1.0, (_v1[0] * _v2[0] + _v1[1] * _v2[1]) / (_n1 * _n2)))))
            # 90 EXACTLY, which is the check's own boundary ("ACUTE (<90 deg)") rather than a
            # margin of my choosing. Enokida's ring closes on a trailing turn of precisely 90.0 - a
            # right-angle corner, which is what a surveyed block does and which the check allows -
            # and a 95 degree threshold trimmed it, moving a shipped map for nothing.
            if _ang >= 90.0 or _n2 > 0.75 * _n1:
                break
            _pts.pop()
        _c["pts"] = _pts
    _dw = next((float(_c.get("w", 5.0)) for _c in channels if _c.get("role") == "drain"), 5.0)
    _dwt = next((float(_c.get("w_tail", _dw)) for _c in channels if _c.get("role") == "drain"), _dw)
    for _p in plots:
        _p["poly"] = hem_to_bank(_p["poly"], _drn, down_deg, _dw, _dwt)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
    round_channel_joints(channels)  # earthen water turns on a swept bend, not a mitred corner
    return {
        "channels": channels,
        "plots": plots,
        "threads": [],
        "drain": _drn,
        "brook": brook,
        "envelope": [(round(x, 1), round(y, 1)) for x, y in envelope],
        "acres": acres,
        "dry_plots": [],
        "dry_acres": 0.0,
        "bund_beans": [],
        "furrows_vary": False,
        "sluice": (round(sluice[0], 1), round(sluice[1], 1)),
        "dike_sluices": [(round(x, 1), round(y, 1)) for x, y in dike_sluices],
        "floor": [(round(x, 1), round(y, 1)) for x, y in floor],
    }


def build_ribbon(
    W: float,
    H: float,
    top: Pt,
    seed: int,
    down_deg: float = 90,
    length: float = 1900,
    width: float = 300,
    n_bands: int = 48,
    ftpx: float = 1.0,
    cell_acres: float = PADDY_CELL_ACRES,
) -> dict[str, Any]:
    """RIBBON VALLEY (谷地田 / a narrow valley-floor strip): a long, NARROW paddy strung along a MEANDERING
    valley floor, the field archetype for a confined valley where the flat ground is only a thin winding
    ribbon beside the brook. Returns build_comb-compatible keys. China-first grounding (research.md D4): the
    valley-bottom rice ribbon of hill country - the brook runs down the center, paddy bands flank it, and the
    whole strip WANDERS with the valley (the distinguishing read against the broad comb fan or the polder).

    CELL SIZE (GM 2026-07-22): the valley floor steps down in cross-bunds AND is split across its width into
    individual leveled cells - a ribbon paddy is a leveled cell like any other (the same small ~`cell_acres`
    as a comb or terrace paddy; a hill valley floor cannot hold one field-wide sheet level over any slope).
    `n_bands` sets the cross-bund (down-valley) step and the width is split into cells of that target, derived
    at this map's `ftpx`. See settlements.md 'Paddy cell size'."""
    R = random.Random(seed)
    dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
    ux, uy = dy, -dx
    hw = width / 2
    step = length / n_bands
    amp = width * 0.62  # how far the valley meanders laterally
    wl = length / 2.4  # meander wavelength
    ph = R.uniform(0, 2 * math.pi)

    def cline(s: float) -> float:  # lateral offset of the valley center at downhill s (the meander)
        return amp * math.sin(ph + s / wl * 2 * math.pi)

    def edge(s: float, side: float) -> Pt:
        lat = cline(s) + side * hw * (0.9 + 0.2 * math.sin(s / 90.0))
        return (top[0] + dx * s + ux * lat, top[1] + dy * s + uy * lat)

    # each down-valley band is split ACROSS the width into cells of ~cell_acres (cell_across = area / step),
    # so the ribbon reads as a chain of small leveled paddies, not one long field-wide sheet
    cell_across = max(24.0, cell_acres * 43560.0 / (ftpx * ftpx) / step)
    plots: list[dict[str, Any]] = []
    for i in range(n_bands):
        s0, s1 = i * step, (i + 1) * step
        ncell = max(2, round(width / cell_across))  # cells across this band
        sides = [-1.0] + [(-1.0 + 2.0 * k / ncell) + R.uniform(-0.6, 0.6) / ncell for k in range(1, ncell)] + [1.0]
        low = i >= n_bands - 3  # the lowest bands down the valley floor (feature 010)
        for j in range(ncell):
            c0, c1 = sides[j], sides[j + 1]
            quad = [edge(s0, c0), edge(s0, c1), edge(s1, c1), edge(s1, c0)]
            fill = FLOODED if low else R.choice(RICE_GREENS)
            plots.append({"poly": [(round(x, 1), round(y, 1)) for x, y in quad], "fill": fill, "low": low})
    left = [edge(i * step, -1) for i in range(n_bands + 1)]
    right = [edge(i * step, 1) for i in range(n_bands + 1)]
    envelope = [*left, *reversed(right), left[0]]
    # the valley BROOK runs down the meandering center (the source: a stream, entering at the high end); a drain
    # continues it off-map at the foot. Supply is the brook itself, so the 'main' ditch traces the centerline.
    center = [(top[0] + dx * (i * step) + ux * cline(i * step), top[1] + dy * (i * step) + uy * cline(i * step)) for i in range(n_bands + 1)]
    flank = [
        (round(x, 1), round(y, 1)) for x, y in center[: n_bands // 2 + 1]
    ]  # the upper valley brook is the supply reach; its fork sits mid-valley so the source->field feed anchors INSIDE the ribbon
    # a short CROSS-SLOPE collector across the ribbon at the foot (perpendicular to the fall), then a downhill
    # outfall so the brook leaves smoothly (a valley ribbon still gathers its tail-water in a cross drain)
    foot = center[-1]
    drain_pts = [
        (round(foot[0] - ux * hw * 0.9, 1), round(foot[1] - uy * hw * 0.9, 1)),
        (round(foot[0], 1), round(foot[1], 1)),
        (round(foot[0] + ux * hw * 0.9, 1), round(foot[1] + uy * hw * 0.9, 1)),
    ]
    drain_pts.append((round(drain_pts[-1][0] + dx * 60, 1), round(drain_pts[-1][1] + dy * 60, 1)))
    sluice = flank[0]
    channels = [
        {"pts": flank, "role": "main", "w": 5.0, "w_tail": 3.0},
        {
            "pts": drain_pts,
            "role": "drain",
            "w": 1.5,
            "w_tail": 5.0,
        },  # gathers across the foot into the outfall at its FAR end (drain_pts runs near flank -> center -> far flank -> downhill stub, and the brook leaves from that stub), so the taper is monotone like every other collector: a thread where it starts, full where it discharges. (An older comment here claimed the outfall was central and the width therefore constant - the geometry above says otherwise.)
    ]
    brook = [drain_pts[-1], (round(drain_pts[-1][0] + dx * 300, 1), round(drain_pts[-1][1] + dy * 300, 1))]
    # the ribbon's bands end AT the foot, i.e. on the cross-drain's centerline - so its bottom bund
    # was drawn under the ditch. Hold the last band off to the bank (see `hem_to_bank`).
    for p in plots:
        p["poly"] = hem_to_bank(p["poly"], drain_pts, down_deg, 1.5, 5.0)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
    round_channel_joints(channels)  # earthen water turns on a swept bend, not a mitred corner
    return {
        "channels": channels,
        "plots": plots,
        "threads": [],
        "drain": drain_pts,
        "brook": brook,
        "envelope": [(round(x, 1), round(y, 1)) for x, y in envelope],
        "acres": acres,
        "dry_plots": [],
        "dry_acres": 0.0,
        "bund_beans": [],
        "furrows_vary": False,
        "sluice": (round(sluice[0], 1), round(sluice[1], 1)),
    }
