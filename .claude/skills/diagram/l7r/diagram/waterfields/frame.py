"""Layer-0 frame math for the water-first field engine: the contour(u)/fall(f) frame, warp-thread state, and pure geometry helpers (segment/polygon predicates, polyline sampling)."""

import math
import random
from collections.abc import Callable

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points

DF = 30.0  # fall step of the lockstep march (px)
GAP = 26.0  # threads never pinch closer than this - a plot must fit between them

# THE CHANNEL LADDER, IN TRUE FEET (GM 2026-08-17: "update the net to be actual size").
#
# These were multipliers-times-grain chosen by eye, and pricing them against a real irrigation duty
# found the whole net drawn 5-6x oversize - a hamlet's head-race wants ~2.5-5 ft and was drawn at 14.
# They are now TRUE WIDTHS IN FEET, converted to pixels by `chan_px`, so the comb net is to scale
# like everything else on a to-scale sheet. The research, the two independent derivations behind
# each figure, and the disclosed departures are in
# `../../../research/water.md#the-comb-net-is-drawn-at-true-size`.
#
# Sized from the ATTESTED tier ladder (a field ditch watering one paddy ~0.3 m; a distribution
# lateral ~1 m; a district main/yosui ~5 m) placed by COMMAND AREA, with a Manning/Lacey check on a
# real duty as corroboration rather than as the primary source - the attested tiers are measurements
# of real channels, while a Manning figure rests on four assumed parameters. A hamlet fan of ~8.5 ha
# sits between the lateral and the small-main tiers, which is where the head-race lands.
# The trunk, above the fork. Set to 6.0 rather than 5.0 on the tier-consistency check that
# `settlement-review` raised (2026-08-17): at 5.0 the top three tiers sat within 1 ft of each other,
# so the ONE junction where hierarchy most wants to read - the bunsuiguchi - was where it read least.
# A trunk that splits into 4.5 and 4.0 ft arms carries both, and under the width-goes-as-sqrt(Q) law
# this engine already adopts that is sqrt(4.5^2 + 4.0^2) = 6.0. This is TIER SELECTION using the law
# as a sanity check on where the trunk sits, NOT conservation-at-junctions (ruled against 2026-08-16
# - never chain drawn widths down from the source). It also has a real referent: a sluice-fed
# head-race genuinely is wider and slower than the water feeding it, ponding above the weir.
HEAD_RACE_FT = 6.0
CANAL_A_FT = (4.5, 1.5)  # the high-margin supply canal: head -> the thread it dies as
CANAL_B_FT = (4.0, 1.5)  # the far-margin arm, commanding the smaller flank
DELIVERY_FT = (2.5, 1.2)  # a delivery ditch: head at its takeoff -> the terminal field-ditch tier
DRAIN_FT = (1.2, 5.5)  # the akusui, mirrored: a thread at its head, full at the outfall. Drainage
# EXCEEDS supply at the outfall (it passes drawdown plus storm, not just the irrigation duty), which
# is why the drain's tail is wider than the head-race that fed the same ground.

# A DELIVERY IS NEVER DRAWN WIDER THAN THE CANAL FEEDING IT (settlement-review 2026-08-17: the flat
# delivery head read 7.96 px against a parent tapered to 5.73, inverting the rank read low in the
# tree - the one thing width-as-rank exists to convey). The head is capped at this fraction of the
# parent's LOCAL width at the takeoff. It binds on roughly HALF the deliveries of a hamlet fan
# (three of five on Inashiro, including the second offtake off canal A with the canal still at
# two-thirds of its head) - not merely on the last one or two, which an earlier draft of this
# comment claimed.
# This is NOT a switch to conservation-at-junctions, which the GM ruled against on 2026-08-16
# (drawn width is RANK, not discharge; do not chain widths down from the source) - it is the weaker
# and sufficient guarantee that a child reads as subordinate to its parent.
DELIVERY_PARENT_FRAC = 0.8
# A mid-block sub-ditch against the HEAD of the delivery it branches off - not that delivery's local
# width at the junction, which is what a delivery itself uses against its canal. The asymmetry is
# deliberate and was measured: at true scale a delivery is ~2.2 ft a third of the way down, so 0.75
# of its LOCAL width is 1.64 ft, which against the 1.5 px floor leaves a sub-ditch 0.14 px of room to
# taper in - and `delivery_ditches_taper` rejected exactly that on 22 of 24 cohort maps. A ditch that
# cannot taper should not be drawn claiming to.
SUB_PARENT_FRAC = 0.75

# THE VISIBILITY FLOOR, and the one place map SCALE enters the ladder. True widths are honest at
# hamlet/village resolution (1-2 ft/px) and vanish above it: at a provincial city's 3 ft/px the
# terminal tier is 0.4 px, i.e. not a line at all. So a stroke is drawn at its true width or this
# floor, whichever is larger - the coarser the sheet, the more of the ladder collapses onto it,
# which is the honest form of the "minimum-visibility floor" the stroke convention in
# `../../../settlements/water.md` already sanctions.
#
# 1.5, AND 1.2 WAS TRIED AND REVERTED (2026-08-17) - the number is load-bearing on the carve, not
# just on legibility. `settlement-review` noted that 1.5 COLLIDES with `aze_w`, which at hamlet grain
# is also exactly 1.5 px: the finest water tier is drawn at precisely the paddy bund's stroke width
# and separated from the brown lattice it runs among only by hue. 1.2 fixes that and is also truer
# (1.2 ft IS the field-ditch tier, ~0.3-0.37 m, so at hamlet scale the floor would bind on nothing).
#
# But the floor feeds `supply_bank_clearance`, so lowering it moves every bund that hems a supply
# stroke, and `close_seams` then welds a different set of scraps. Measured on the 24-seed cohort,
# with the change isolated by reverting this line alone: **1.2 costs seeds 19 and 22 to
# `paddy_plot_seams_shared` (22/24 -> 20/24); at 1.5 they pass.** A cosmetic ambiguity is not worth
# two broken maps, so the collision stands as recorded-and-accepted rather than fixed.
#
# IF IT IS EVER WORTH CLOSING, the lever is the OTHER side: `AZE_FT` is 1.5 by its own research
# (a plain aze ran ~1-2 ft), so there is room to take the BUND to 1.3 and leave the water alone -
# which changes only a stroke width and touches no clearance. That was not attempted here.
MIN_CHANNEL_PX = 1.5

# THE CANAL BERM: bare ground between a supply canal's BANK and the dry-crop hem above it, in feet.
# Measured from the bank, never from the centerline - the hem's stand-off used to be a flat `8 * g`
# from the canal's CENTERLINE, which is a pinned number wearing a derived one's clothes: it did not
# move when the net went to true size, so the water inside it shrank threefold while the bare stripe
# GREW (12.3 -> 14.8 px median on Inashiro, identical before and after - settlement-review
# 2026-08-17). A berm defined by its relationship to a bank has to be derived from that bank.
#
# 5.0 ft is the spoil bank plus standing room: GB50288 puts a lateral/farm canal's embankment TOP at
# not less than 1 m, and a canal wants a walkable side for the annual dredging that keeps it flowing.
# The old effective figure was ~10 ft of bare ground, which was never chosen - it is what 16 ft from
# the centerline left once a 12.4 px canal was subtracted, i.e. an artifact of the inflation.
CANAL_BERM_FT = 5.0

# A FARMER STEPS OVER A DITCH THIS NARROW RATHER THAN DECKING IT (settlement-review 2026-08-17).
# The footplank rule used to be about LENGTH only - any ditch over ~140 px got a plank about midway -
# which was harmless while the net was 5-6x oversize and absurd the moment it went to true size:
# eight of Inashiro's fifteen planks were decking water 1.7-2.3 ft wide, with 3-4 ft abutments each
# side. A plank bridge is a real object a household builds and maintains; nobody builds one over
# something they can stride across. 3 ft is about that stride, and it lands cleanly in the gap the
# measured pool leaves - the delivery ditches carry 1.8-2.5 ft and the supply canals 3.0-4.5, so the
# rule separates "step over it" from "lay a board" without cutting through either group.
FOOTPLANK_MIN_FT = 3.0


def worth_planking(w_px: float, w_tail_px: float, ftpx: float) -> bool:
    """Is this ditch wide enough anywhere to be worth a plank rather than a stride?

    ONE predicate, called by the placer (`channel_footbridges`) and by the gate
    (`long_ditches_have_a_footbridge`), because a ditch the placer declines to deck and the check
    still demands a deck on is the classic disagreement this engine keeps rediscovering.

    TWO SCOPES, and both are needed. Pass the ditch's HEAD and TAIL and this answers "is this ditch
    worth a crossing ANYWHERE" - which is the question the gate asks, since it demands one plank per
    long ditch. Pass the same value twice and it answers "is the water wide enough HERE", which is
    what the placer must ask at each candidate seat: a tapering run can qualify on its head and still
    put a board over 2.4 ft if the seat is chosen by arc fraction alone, which is what shipped and
    what a review caught (2026-08-17). The placer now tests both - the ditch to decide whether to
    look at all, then each seat as it slides - so the board lands where the water earns it."""
    return max(w_px, w_tail_px) * ftpx >= FOOTPLANK_MIN_FT


def chan_px(ft: float, grain: float) -> float:
    """A channel's DRAWN width in pixels, from its true width in feet.

    `grain` is defined as `2 / ftpx` (see `build_comb`'s docstring and `hamletgen.consts.GRAIN`), so
    `ft * grain / 2` is `ft / ftpx` - the true width in pixels at this map's scale. Written through
    grain rather than taking `ftpx` directly because grain is what every caller already threads
    down, and inventing a second scale parameter is how the two drift apart.

    The floor is applied to each END of a taper independently, because it is a floor on the DRAWN
    stroke, not on the taper: a run whose true head clears the floor and whose true tail does not
    should still narrow, just less far than the truth would take it."""
    return max(MIN_CHANNEL_PX, ft * grain / 2.0)


def taper_w(w0: float, w1: float, t: float) -> float:
    """The drawn width of a tapering channel a fraction `t` along its run (0 = head, 1 = tail).

    THE WIDTH SQUARED IS WHAT RUNS LINEARLY, not the width - because a channel's width goes as the
    SQUARE ROOT of the discharge it carries, and the discharge is what changes linearly along one of
    these runs. (why: `../../../research/water.md#a-channel-taper-is-a-square-root-not-a-straight-line`)

    Both halves of that are load-bearing, so neither is a free choice:

      - *Width goes as sqrt(Q).* This is the regime relation the water-width ladder in
        `../../../settlements/water.md` has always asserted ("channel width scales with the square-root of
        the command-area flow it carries"), and it is Lacey's canal result, P = 4.75 * sqrt(Q) - the
        standard design equation for exactly this kind of unlined earthen channel.
      - *Q runs linearly.* A delivery ditch sheds its water through a `mizuguchi` per plot into a row
        of near-equal paddies, so it loses roughly the same flow per unit length; a collector gathers
        its tail-water the same way. Uniform shedding over the run IS Q linear in `t`.

    Interpolating the WIDTH linearly - which is what every one of these call sites used to do -
    quietly asserts Q proportional to w, a different and wrong law, and it looks wrong in the way the
    GM caught (2026-08-17): the stroke thins almost imperceptibly for its whole length and then stops
    dead at a still-substantial width. Under the true law a delivery ditch holds most of its working
    width while it still has most of its water to deliver, then dwindles hard over the last stretch -
    which is what "the water is leaving it" is supposed to look like.

    THAT PROFILE IS DATA, NOT A VISIBLE GRADIENT, and saying so is part of the rule. Since the net
    went to true size a delivery ditch sheds one pixel over five hundred (0.20 px per 100 px, against
    0.93 before), so the shape below is correct and unreadable at once. The GM asked directly, was
    given x1.5 and x2 legibility multipliers with the gradients priced, and chose true size
    (2026-08-17). Do NOT widen these strokes to make the taper show - the numbers and the reasoning
    are in `../../../research/water.md#what-drawing-at-true-size-left-open`.

    **THE WORKED EXAMPLE LIVES IN A TEST, NOT HERE** -
    `test_the_delivery_taper_holds_then_dwindles` asserts the SHAPE this paragraph promises (wider
    than a straight line at every interior point; more of the drop in the back half than the front;
    the floor reached only at the tail) against the shipped tier constants. That is deliberate and
    it is the third attempt at this paragraph. Twice it carried magnitudes in prose and twice they
    went false without anything failing: first the formula's numbers while `field_channel` was still
    sampling by vertex index, so the real ink was 4.6 px at mid-run; then a re-measured set that the
    true-size ladder invalidated the same day, leaving this docstring describing 8.0 -> 3.0 ft
    ditches on a map whose ditches are 2.5 -> 1.2. **A number in a docstring is not falsifiable by
    any gate; a number in a test is.** So state the shape here, assert it there, and if you need a
    magnitude, measure the SVG - never compute it from the rule this docstring is describing.

    `taper_pieces` in `banks.py` carries the arc-parameterization half of the story, and the bound
    between its piecewise ink and the continuous law the bank clearances evaluate.

    NOT a taper to nothing: `w1` is a real tier, not zero. See the same research anchor for why the
    finest channel we DRAW stops at the terminal-lateral width instead of vanishing to a point.

    ONE helper, called by every site that needs a local width - the drawn stroke, the two bank
    clearances the gate shares, the seam buffer, the carve's burial filter, and the channel keep-out
    corridor. A taper law re-derived per call site is the "one measurement, not several" trap in the
    diagram CLAUDE.md: the bunds are laid against the bank this returns and the checks read the same
    number, so two formulas here means a bund drawn inside the water."""
    return math.sqrt(max(0.0, w0 * w0 + (w1 * w1 - w0 * w0) * t))


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
        # This ditch's TRUE head width in feet, set by whoever creates it from the width of the
        # channel it takes off from (see DELIVERY_PARENT_FRAC). Defaulted rather than left unset so
        # a thread that reaches the drawing pass by some other route still has an honest width.
        self.head_ft: float = DELIVERY_FT[0]

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
    run (it widens `chan_px(DRAIN_FT[0], g)` -> `chan_px(DRAIN_FT[1], g)` downstream, so the half-width alone
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
        half = taper_w(chan_px(DRAIN_FT[0], g), chan_px(DRAIN_FT[1], g), t) / 2
        slope = next((s for lo, hi, s in segs if lo <= u <= hi), segs[0][2] if u <= u_lo else segs[-1][2])
        return (half + BANK_MARGIN * g) * slope

    return bank


BANK_MARGIN = 0.75  # half a drawn bund stroke (aze_w is ~1.5 real ft), so bund and ditch ABUT rather than overlap


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


def _miter_normals(bpts: Poly, F: _Frame) -> list[Pt]:
    """Per-BOUNDARY upslope offset normals for hem columns tiled along the boundary points `bpts`:
    each interior boundary gets the mitred average of its two chords' upslope normals, scaled by
    1/cos(half-bend) - the stroked-polyline miter join, so the offset band keeps its true upslope
    depth at the seam (capped at 2x for a degenerate hairpin; a 180-degree fold, where no shared
    offset direction exists, falls back to the outgoing chord's normal). The two end boundaries
    take their single chord's normal unscaled.

    WHY (GM 2026-08-16, Inashiro): _dry_fields used to offset each column along its OWN chord's
    normal, so both quads at a shared boundary point pushed that point in slightly different
    directions wherever the canal bent - a wedge of bare ground on a convex bend, a lap on a
    concave one, ~bend-angle x depth px wide at the ragged edge (the worst Inashiro pair lapped
    245 sq ft; 7 pairs overlapped outright, and every scripted hamlet had some). Offsetting each
    boundary point along ONE shared vector makes every seam a single straight line both quads lie
    on - gated by dry_plot_seams_shared."""
    cn: list[Pt] = []
    for i in range(len(bpts) - 1):
        tx, ty = bpts[i + 1][0] - bpts[i][0], bpts[i + 1][1] - bpts[i][1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl  # unit normal to this chord
        mx, my = (bpts[i][0] + bpts[i + 1][0]) / 2, (bpts[i][1] + bpts[i + 1][1]) / 2
        if F.to_uf(mx + nx, my + ny)[1] > F.to_uf(mx, my)[1]:  # point it UPSLOPE (decreasing fall)
            nx, ny = -nx, -ny
        cn.append((nx, ny))
    out: list[Pt] = [cn[0]]
    for k in range(1, len(cn)):
        sx, sy = cn[k - 1][0] + cn[k][0], cn[k - 1][1] + cn[k][1]
        sl = math.hypot(sx, sy)
        if sl < 1e-9:  # 180-degree fold: opposite chord normals cancel
            out.append(cn[k])
            continue
        ux, uy = sx / sl, sy / sl
        scale = 1.0 / max(0.5, ux * cn[k][0] + uy * cn[k][1])  # 1/cos(half-bend), miter-limited at 2x
        out.append((ux * scale, uy * scale))
    out.append(cn[-1])
    return out
