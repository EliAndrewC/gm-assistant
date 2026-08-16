"""Layer-0 frame math for the water-first field engine: the contour(u)/fall(f) frame, warp-thread state, and pure geometry helpers (segment/polygon predicates, polyline sampling)."""

import math
import random
from collections.abc import Callable

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points

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


def taper_w(w0: float, w1: float, t: float) -> float:
    """The drawn width of a tapering channel a fraction `t` along its run (0 = head, 1 = tail).

    THE WIDTH SQUARED IS WHAT RUNS LINEARLY, not the width - because a channel's width goes as the
    SQUARE ROOT of the discharge it carries, and the discharge is what changes linearly along one of
    these runs. (why: `../research/water.md#a-channel-taper-is-a-square-root-not-a-straight-line`)

    Both halves of that are load-bearing, so neither is a free choice:

      - *Width goes as sqrt(Q).* This is the regime relation the water-width ladder in
        `../settlements/water.md` has always asserted ("channel width scales with the square-root of
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
    which is what "the water is leaving it" is supposed to look like. MEASURED IN THE INK on
    Inashiro's five 8.0 -> 3.0 ft delivery ditches - the MEDIAN drawn width of the piece covering
    each of the tenths 0.10 / 0.25 / 0.50 / 0.75 / 0.90 of the run: **7.7 / 7.0 / 6.1 / 4.8 / 3.7
    px**, against the straight line's 7.5 / 6.8 / 5.5 / 4.3 / 3.5. So it holds ~6 ft at mid-run
    where the old law had already given up half of its 5 ft of narrowing.

    A piece carries the law at its OWN midpoint, so the ink brackets the continuous law rather than
    sitting on it, and the SPREAD widens where the segments are coarse: the five ditches agree
    within ~0.1 px at the first four tenths but span 3.46 to 4.13 px at 0.90 against the law's 3.81.
    Quote the median and that spread, never a single tight figure.

    Those are drawn widths, not formula values, and the distinction has now bitten this docstring
    TWICE. It first carried the formula's numbers while `field_channel` still sampled the law by
    vertex index, so the ink was 4.6 px at mid-run and the claim here was false on its own example
    map; the correction then quoted the formula's 7.1 at the 0.25 tenth where the ink's median is
    7.0 (both caught by settlement-review, 2026-08-17). **Re-measure in the SVG. Do not compute
    these from the rule this docstring is describing.** `taper_pieces` in `banks.py` carries the
    arc-parameterization half of the story, and the bound between its piecewise ink and the
    continuous law the bank clearances evaluate.

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
        half = taper_w(DRAIN_W_HEAD * g, DRAIN_W_TAIL * g, t) / 2
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
