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
from collections.abc import Sequence
from typing import Any

Pt = tuple[float, float]  # an (x, y) point in map pixels
Poly = list[Pt]  # a polyline / polygon as a list of points

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
BEAN_GREEN = '#7C9A4E'  # azemame (bund soybeans) - the beaded-bund accent

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


def _poly_area(poly: Poly) -> float:
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


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
) -> dict[str, Any]:
    """The COMB layout (the historical default - Kishu school / Chinese canal doctrine):
    the sluice's head-race forks at one division point into TWO supply canals hugging the
    high margins (canal A runs cross-slope at down-37 deg, canal B down the other margin at
    down+58 deg), delivery ditches drop downhill off them (a couple splitting once), and one
    drain collector (akusui) crosses the LOW side and leaves the map. Paddies are carved
    between the ditch threads; water cascades plot-to-plot within each block (tagoshi).

    Returns {"channels": [{pts, w, role}], "plots": [{poly, fill}], "threads", "drain",
    "envelope", "acres"} - the caller draws it (px are map px; acres assume 1px = 2ft)."""
    R = random.Random(seed)
    F = _Frame(down_deg)
    DOWN = F.down
    channels = []

    # head-race: sluice -> the division point (bunsuiguchi), straight down the fall
    hr = [sluice, (sluice[0] + 45 * F.d[0], sluice[1] + 45 * F.d[1]), (sluice[0] + 90 * F.d[0], sluice[1] + 90 * F.d[1])]
    channels.append({"pts": hr, "w": 7.0, "role": "main"})
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
    channels.append({"pts": dpts, "w": 6.0, "role": "drain"})

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
                clipped.append(hit)
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
    # size as they are tapped by branch canals" - Tabayashi 1986); ditch prefixes
    cuts = [0.0] + list(offtakes_a) + [1.0]
    for i in range(len(cuts) - 1):
        piece = [_point_along(a_pts, cuts[i] + (cuts[i + 1] - cuts[i]) * t / 6) for t in range(7)]
        channels.append({"pts": piece, "w": 6.2 - 2.2 * i / (len(cuts) - 2), "role": "main"})
    bc_cuts = sorted(F.to_uf(*e[1].pts[0])[1] if False else e[0] for e in []) if False else sorted([bc.f0] + [f for f in getattr(bc, "offtake_fs", [])] + [bc.ditch_f])
    for t in threads:
        pre = [p for p in t.pts if F.to_uf(*p)[1] <= t.ditch_f]
        if len(pre) < 2:
            continue
        if t is bc and len(bc_cuts) > 2:
            # canal B is a SUPPLY canal (role "main", like canal A) that narrows past each offtake it
            # feeds - distinct from the delivery ditches (role "branch"), which taper continuously.
            for i in range(len(bc_cuts) - 1):
                piece = [p for p in pre if bc_cuts[i] - 14 <= F.to_uf(*p)[1] <= bc_cuts[i + 1] + 14]
                if len(piece) >= 2:
                    channels.append({"pts": piece, "w": 5.6 - 1.6 * i / max(1, len(bc_cuts) - 2), "role": "main"})
        else:
            # a delivery ditch TAPERS as it descends: it sheds water into the paddies it feeds all
            # along its length, so its flow - and width - decreases from full at the canal takeoff to a
            # THREAD at the delivery point where it stops (continuously "tapped by the plots it feeds",
            # extending Tabayashi's supply-canal taper rule to the delivery ditches). w_tail marks the
            # narrow end so the gen draws it dwindling, not a blunt constant-width stub that stops dead.
            channels.append({"pts": pre, "w": 5.6 if t is bc else 4.0, "w_tail": 1.5, "role": "branch"})

    plots = _carve(R, F, threads, a_pts, dpts, W, H, plot_across, row_step)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560  # 1px=2ft -> 4 sq ft/px^2

    envelope = [p for p in a_pts] + [p for p in threads[-1].pts] + list(reversed(dpts)) + list(reversed(threads[0].pts))

    # DRY FIELDS (hatake) on the uncommanded upslope margin above the supply canal, and
    # BUND BEANS (azemame) beaded along a fraction of the paddy bunds - see settlements.md.
    dry_plots = _dry_fields(R, F, a_pts, W, H, dry_keepout, band=dry_band, furrow_spread=furrow_spread, grain_drift=grain_drift)
    dry_acres = sum(_poly_area(p["poly"]) for p in dry_plots) * 4 / 43560
    bund_beans = _bund_beans(R, plots, bean_frac)
    # furrows_vary tells the checker whether to REQUIRE neighboring dry plots to differ in row direction: a
    # gentle-valley village spreads them (the patchwork quilt, default); a STEEP/terraced village narrows the
    # spread so the rows converge back onto the contour (ridge-along-contour erosion control) and no variation
    # is required. Threshold at ~0.3 rad (~17 deg): above it the plots visibly fan, below it they read aligned.
    return {
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
) -> list[dict[str, Any]]:
    """Carve paddy plots between adjacent threads. Above a thread's takeoff the boundary
    falls back to its parent path (canal / parent ditch); below its end, to the DRAIN - so
    plots hug the canal at the top and reach the collector at the bottom, never spilling
    past either. Rows are contour-parallel bunds (the cascade steps down them)."""
    plots: list[dict[str, Any]] = []

    def bnd(t: _Thread, f: float) -> Pt:
        if f < t.f0 and t.fallback is not None:
            fb = t.fallback
            return _at_f(F, fb if isinstance(fb, list) else fb.pts, f)
        if f > F.to_uf(*t.pts[-1])[1]:
            return _at_f(F, dpts, f)
        return _at_f(F, t.pts, f)

    a_us = [F.to_uf(*p)[0] for p in a_pts]
    a_ulo, a_uhi = min(a_us), max(a_us)

    def spills_drain(pq: Pt) -> bool:
        """Below the collector - strict per-vertex (no plot may poke past the drain)."""
        u, f = F.to_uf(*pq)
        fd = _f_at_u(F, dpts, u)
        return fd is not None and f > fd - 3

    def above_canal(quad: Poly) -> bool:
        """Upslope of the supply canal - judged by the CENTROID, not the top vertices: a
        head plot's top edge sits ON the canal (fed directly through the bund), which is
        correct and must be KEPT; only a plot whose body is genuinely above the canal is
        rejected. (Per-vertex here was silently discarding every canal-touching head plot.)"""
        cx = sum(p[0] for p in quad) / 4
        cy = sum(p[1] for p in quad) / 4
        u, f = F.to_uf(cx, cy)
        if not (a_ulo - 20 < u < a_uhi + 20):
            return False
        fc = _f_at_u(F, a_pts, u)
        return fc is not None and f < fc + 4  # centroid upslope of a small berm

    def root_f(t: _Thread) -> float:
        while isinstance(t.fallback, _Thread):
            t = t.fallback
        if isinstance(t.fallback, list):
            return min(t.f0, F.to_uf(*t.fallback[0])[1])
        return t.f0

    for di in range(len(threads) - 1):
        A, B = threads[di], threads[di + 1]
        f_lo = max(root_f(A), root_f(B)) + 6
        if B.fallback is A or A.fallback is B:
            # a parent-child pair: the sector opens AT the spawn point - anchor the first
            # row there, else the row straddling the spawn has zero width and never plants
            f_lo = max(A.f0, B.f0) + 4
        f_hi0 = max(F.to_uf(*A.pts[-1])[1], F.to_uf(*B.pts[-1])[1]) - 34
        if f_hi0 - f_lo < 24:
            continue
        # measure the sector's width where BOTH boundaries are their own threads (the
        # active span) - measuring in the fallback wedge reads ~0 and degenerates nsub
        fmid = (max(A.f0, B.f0) + f_hi0) / 2
        width_mid = math.dist(bnd(A, fmid), bnd(B, fmid))
        if width_mid < 24:
            continue
        nsub = max(1, round(width_mid / plot_across))
        phase = [R.uniform(0, 6.28) for _ in range(nsub + 2)]

        def edge(  # bind loop vars (used within this iteration)
            fv: float,
            j: int,
            n: int,
            A: _Thread = A,
            B: _Thread = B,
            phase: list[float] = phase,
            nsub: int = nsub,
        ) -> Pt:
            a, b = bnd(A, fv), bnd(B, fv)
            t = j / n
            x = a[0] + t * (b[0] - a[0])
            y = a[1] + t * (b[1] - a[1])
            if 0 < j < n:  # interior bunds waver along contour
                wob = 5.0 * math.sin(fv / 70 + phase[min(j, nsub + 1)])
                x += F.c[0] * wob
                y += F.c[1] * wob
            return (x, y)

        def drain_f_at(fv: float, j_: int, n_: int) -> float:
            """Fall of the drain under the j_-th sub-bund point sampled at fall fv."""
            pu = F.to_uf(*edge(fv, j_, n_))[0]
            fd_ = _f_at_u(F, dpts, pu)
            return fd_ if fd_ is not None else fv

        f_hi = min(f_hi0, min(drain_f_at(f_hi0, j, nsub) for j in range(nsub + 1)) - 32)
        if f_hi - f_lo < 24:
            continue
        sector_start = len(plots)
        rows = [f_lo]
        f = f_lo
        while f < f_hi:
            f = min(f_hi, f + R.uniform(*row_step))
            rows.append(f)

        for k in range(len(rows) - 1):
            wk = min(math.dist(bnd(A, rows[k]), bnd(B, rows[k])), math.dist(bnd(A, rows[k + 1]), bnd(B, rows[k + 1])))
            if wk < 24:
                continue
            n = nsub if wk / nsub >= 13 else max(1, int(wk // 44))  # canal-wedge rows: local
            for j in range(n):
                quad = [edge(rows[k], j, n), edge(rows[k], j + 1, n), edge(rows[k + 1], j + 1, n), edge(rows[k + 1], j, n)]
                if math.dist(quad[0], quad[1]) < 12 or math.dist(quad[1], quad[2]) < 12:
                    continue
                if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                    continue
                if any(spills_drain(pq) for pq in quad) or above_canal(quad):
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
            fprobe = max(A.f0, B.f0) + 12  # sample where the subcolumns are spread out
            fc0 = _f_at_u(F, a_pts, F.to_uf(*edge(fprobe, j, nsub))[0])
            fc1 = _f_at_u(F, a_pts, F.to_uf(*edge(fprobe, j + 1, nsub))[0])
            if fc0 is None or fc1 is None:
                continue
            t0, t1 = fc0 + 5, fc1 + 5
            ks = [k for k in range(len(rows)) if rows[k] >= max(t0, t1) + 6]
            if not ks:
                continue
            fb = rows[ks[0]]
            if fb - min(t0, t1) > 78 or fb - max(t0, t1) < 8:
                continue  # no gap here / top boundary is not the canal
            quad = [edge(t0, j, nsub), edge(t1, j + 1, nsub), edge(fb, j + 1, nsub), edge(fb, j, nsub)]
            if math.dist(quad[0], quad[1]) < 12 or math.dist(quad[1], quad[2]) < 6:
                continue
            if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                continue
            cx = sum(pq[0] for pq in quad) / 4
            cy = sum(pq[1] for pq in quad) / 4
            if any(_pip(cx, cy, pl["poly"]) for pl in plots[sector_start:]):
                continue  # this ground already planted (fork wedges)
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
            fb0 = drain_meet(j) - 2
            fb1 = drain_meet(j + 1) - 2
            depth = max(fb0, fb1) - ftop
            if depth < 6:
                continue
            nlev = max(1, round(depth / 34))  # keep closer plots ~one row tall
            for li in range(nlev):
                fa0 = ftop + (fb0 - ftop) * li / nlev
                fa1 = ftop + (fb1 - ftop) * li / nlev
                fz0 = ftop + (fb0 - ftop) * (li + 1) / nlev
                fz1 = ftop + (fb1 - ftop) * (li + 1) / nlev
                quad = [edge(fa0, j, n), edge(fa1, j + 1, n), edge(fz1, j + 1, n), edge(fz0, j, n)]
                abuts = li == nlev - 1
                if abuts:
                    # snap the bottom vertices exactly onto the collector (drain fall at
                    # their OWN u) so the field edge lies on the ditch
                    for bi in (2, 3):
                        u_ = F.to_uf(*quad[bi])[0]
                        fdv = _f_at_u(F, dpts, u_)
                        if fdv is not None:
                            quad[bi] = F.to_xy(u_, fdv - 2)
                if math.dist(quad[0], quad[1]) < 8:
                    continue
                if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                    continue
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
            just_in = F.to_xy(u, fdr - 6)  # 6px up-fall, on the field side
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
            levels = max(1, round((fdr - 2 - top) / 38))  # tile tall gaps into ~row plots
            for li in range(levels):
                fa = top + (fdr - 2 - top) * li / levels
                fz = top + (fdr - 2 - top) * (li + 1) / levels
                quad = [F.to_xy(uu, fa), F.to_xy(uv, fa), F.to_xy(uv, fz), F.to_xy(uu, fz)]
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

    # FURROW ANGLE varies PER PLOT (a mosaic of family strips): each plot drops its ridges into the LARGEST gap
    # between the angles of its already-placed NEIGHBORS, guaranteeing separation (drives dry_plot_furrows_vary).
    HW = furrow_spread
    placed: list[tuple[float, float, float]] = []
    ADJ2 = 56**2
    prev_crop = R.choice(list(DRY_CROPS))
    berm = 8  # a thin bund holds the dry plots just ABOVE (upslope of) the canal
    for i in range(len(bounds) - 1):
        pL, pR = at(bounds[i]), at(bounds[i + 1])
        tx, ty = pR[0] - pL[0], pR[1] - pL[1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl  # unit normal to the canal
        mx, my = (pL[0] + pR[0]) / 2, (pL[1] + pR[1]) / 2
        if F.to_uf(mx + nx, my + ny)[1] > F.to_uf(mx, my)[1]:  # point it UPSLOPE (decreasing fall)
            nx, ny = -nx, -ny
        depth = R.uniform(*band)  # ragged outer edge (per-column depth)
        nrow = max(1, round(depth / 36))
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


def _bund_beans(R: random.Random, plots: list[dict[str, Any]], frac: float, spacing: float = 9.5) -> Poly:
    """AZEMAME (bund soybeans): sub-pixel at 1px=2ft, so drawn symbolically as a green BEAD
    line along a fraction of the paddy bunds. Returns bead center points; the caller draws
    small BEAN_GREEN dots. ~`frac` of plots carry beaded bunds (not every bund had beans)."""
    beans = []
    for p in plots:
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
                beans.append((round(a[0] + s * (b[0] - a[0]), 1), round(a[1] + s * (b[1] - a[1]), 1)))
    return beans


def build_terraces(
    W: float,
    H: float,
    top: Pt,
    seed: int,
    down_deg: float = 90,
    n_terraces: int = 16,
    cross_width: float = 820,
    fall: float = 1500,
) -> dict[str, Any]:
    """Contour TERRACES (梯田): stacked thin paddies following the hillside contours, stepping downhill from
    `top` (the high catchment where water enters). Each terrace is a gently curved band PERPENDICULAR to the
    fall; a supply channel runs down one flank and the stack cascades to a drain at the foot. Returns the same
    keys as `build_comb` so `Settlement.draw_comb_field` can draw it, plus `bund_lines` (the retaining-wall
    lip at each terrace's downhill edge, drawn by the gen). China-first grounding (research.md D4): the
    south-China / SE-Asia rice terrace (Yuanyang 元陽, Longsheng 龍勝) is THE field archetype for HILL ground,
    where valley-bottom paddy is impossible - the defining alternative to the comb's flat valley field."""
    R = random.Random(seed)
    dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill unit
    ux, uy = -dy, dx  # cross-slope (contour) unit
    hw = cross_width / 2
    step = fall / n_terraces
    plots: list[dict[str, Any]] = []
    bund_lines: list[Poly] = []
    samples = 14

    def contour(s: float, amp: float, phase: float) -> Poly:
        # one contour line across the slope at downhill distance s, curved by a gentle sine (organic terracing);
        # the hillside narrows slightly downhill (a natural spur), so width tapers with s
        w = hw * (1.0 - 0.12 * s / fall)
        pts: Poly = []
        for k in range(samples + 1):
            t = -1.0 + 2.0 * k / samples
            curve = amp * math.sin(phase + t * math.pi * 1.15)
            base = s + curve
            pts.append((top[0] + dx * base + ux * (t * w), top[1] + dy * base + uy * (t * w)))
        return pts

    # precompute the N+1 boundary contours ONCE (each its own gentle curve); adjacent terraces SHARE a boundary,
    # so there is no gap between them - terrace i fills between boundary i (its uphill lip) and boundary i+1
    boundaries = [contour(i * step, 16.0 + R.uniform(-4, 7), R.uniform(0, 2 * math.pi)) for i in range(n_terraces + 1)]
    for i in range(n_terraces):
        poly = [*boundaries[i], *reversed(boundaries[i + 1])]
        low = i >= n_terraces - 3  # the low terraces sit wettest - the topography, not the tint (feature 010)
        fill = FLOODED if low else R.choice(RICE_GREENS)
        plots.append({"poly": [(round(x, 1), round(y, 1)) for x, y in poly], "fill": fill, "low": low})
        bund_lines.append([(round(x, 1), round(y, 1)) for x, y in boundaries[i + 1]])  # the retaining lip at each terrace's low edge

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
    foot = contour(fall, 0.0, 0.0)
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
        {"pts": drain_pts, "role": "drain", "w": 5.0, "w_tail": 5.0},
    ]
    brook = [drain_pts[-1], (round(drain_pts[-1][0] + dx * 300, 1), round(drain_pts[-1][1] + dy * 300, 1))]  # straight downhill off-map
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
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
    vary - most module bays split into 2-3 oblong strips, a few merge into double-bay parcels, and interior
    bund nodes jitter a touch so minor bunds waver while main ditches hold their line. DELIBERATE DEPARTURE:
    parcels are drawn larger than the literal ~1-mu average (a true-scale parcel at hamlet zoom is a sliver)
    - the RELATIVE variation is the honest part; absolute size trades toward legibility, same liberty as the
    other archetypes."""
    R = random.Random(seed)
    dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))  # downhill (row) unit
    ux, uy = dy, -dx  # cross (column) unit - the grid extends to the +x/+cross side of the origin
    ox, oy = origin

    def grid(s: float, t: float) -> Pt:
        return (ox + dx * s + ux * t, oy + dy * s + uy * t)

    # jittered bund-node lattice in (s, t) space. Perimeter nodes stay PINNED so the dike and the block
    # envelope are dead straight; only interior nodes waver (minor bunds), and the jitter is small enough
    # that the main ditch lines still read straight at map scale.
    J = 6.0
    nodes: list[list[tuple[float, float]]] = [
        [(r * cell + (R.uniform(-J, J) if 0 < r < rows else 0.0), c * cell + (R.uniform(-J, J) if 0 < c < cols else 0.0)) for c in range(cols + 1)] for r in range(rows + 1)
    ]

    def lerp(a: tuple[float, float], b: tuple[float, float], f: float) -> tuple[float, float]:
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    def inset(quad: list[tuple[float, float]], g: float = 4.0) -> list[tuple[float, float]]:
        # a hairline gap = the bund between parcels. Bbox-scaling about the centroid is exact for the
        # axis-aligned case and near-exact for these gently jittered quads (all built in (s, t) space).
        s_lo, s_hi = min(p[0] for p in quad), max(p[0] for p in quad)
        t_lo, t_hi = min(p[1] for p in quad), max(p[1] for p in quad)
        cs, ct = (s_lo + s_hi) / 2, (t_lo + t_hi) / 2
        ks = max(0.0, s_hi - s_lo - 2 * g) / max(1e-9, s_hi - s_lo)
        kt = max(0.0, t_hi - t_lo - 2 * g) / max(1e-9, t_hi - t_lo)
        return [(cs + (p[0] - cs) * ks, ct + (p[1] - ct) * kt) for p in quad]

    plots: list[dict[str, Any]] = []

    def emit(quad_st: list[tuple[float, float]], r: int) -> None:
        low = r >= rows - 2  # the lowest rows of the polder (feature 010)
        poly = [grid(s, t) for s, t in inset(quad_st)]
        fill = FLOODED if low else R.choice(RICE_GREENS)
        plots.append({"poly": [(round(x, 1), round(y, 1)) for x, y in poly], "fill": fill, "low": low})

    for r in range(rows):
        c = 0
        while c < cols:
            wide = c + 1 < cols and R.random() < 0.12  # an occasional double-bay parcel (merged holding)
            c1 = c + (2 if wide else 1)
            tl, tr = nodes[r][c], nodes[r][c1]
            bl, br = nodes[r + 1][c], nodes[r + 1][c1]
            u = R.random()
            n_cuts = 0 if wide else (2 if u < 0.16 else (1 if u < 0.68 else 0))
            if n_cuts == 0:
                emit([tl, tr, br, bl], r)
            else:
                cuts = [R.uniform(0.38, 0.62)] if n_cuts == 1 else [R.uniform(0.26, 0.4), R.uniform(0.6, 0.74)]
                fs = [0.0, *cuts, 1.0]
                if R.random() < 0.5:  # cut ACROSS the fall - sub-parcels stack down the block
                    for f0, f1 in zip(fs, fs[1:], strict=False):
                        emit([lerp(tl, bl, f0), lerp(tr, br, f0), lerp(tr, br, f1), lerp(tl, bl, f1)], r)
                else:  # cut ALONG the fall - side-by-side strips
                    for f0, f1 in zip(fs, fs[1:], strict=False):
                        emit([lerp(tl, tr, f0), lerp(tl, tr, f1), lerp(bl, br, f1), lerp(bl, br, f0)], r)
            c = c1
    span_s, span_t = rows * cell, cols * cell
    envelope = [grid(0, 0), grid(0, span_t), grid(span_s, span_t), grid(span_s, 0), grid(0, 0)]
    # the supply feeder runs STRAIGHT along the high (top) edge from the sluice, so its fork sits just above the
    # block and the source->field feed (fork + a step downhill) anchors INSIDE the grid without any hairpin. The
    # drain runs along the low edge descending to the far outfall corner, then turns downhill for a smooth brook.
    flank = [grid(-12, span_t * k / 8) for k in range(5)]  # along the high edge to mid-top...
    flank.append(grid(70, span_t * 0.5))  # ...then dip INTO the block so the source->field feed anchors inside
    drain_pts = [(round(x, 1), round(y, 1)) for x, y in [grid(span_s + 12 + dx * 30 * (k / 6), span_t * k / 6) for k in range(7)]]
    drain_pts.append((round(drain_pts[-1][0] + dx * 62, 1), round(drain_pts[-1][1] + dy * 62, 1)))
    sluice = flank[0]
    channels = [
        {"pts": [(round(x, 1), round(y, 1)) for x, y in flank], "role": "main", "w": 6.0, "w_tail": 3.0},
        {"pts": drain_pts, "role": "drain", "w": 5.0, "w_tail": 5.0},
    ]
    brook = [drain_pts[-1], (round(drain_pts[-1][0] + dx * 300, 1), round(drain_pts[-1][1] + dy * 300, 1))]
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
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


def build_ribbon(
    W: float,
    H: float,
    top: Pt,
    seed: int,
    down_deg: float = 90,
    length: float = 1900,
    width: float = 300,
    n_bands: int = 24,
) -> dict[str, Any]:
    """RIBBON VALLEY (谷地田 / a narrow valley-floor strip): a long, NARROW paddy strung along a MEANDERING
    valley floor, the field archetype for a confined valley where the flat ground is only a thin winding
    ribbon beside the brook. Returns build_comb-compatible keys. China-first grounding (research.md D4): the
    valley-bottom rice ribbon of hill country - the brook runs down the center, paddy bands flank it, and the
    whole strip WANDERS with the valley (the distinguishing read against the broad comb fan or the polder)."""
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

    plots: list[dict[str, Any]] = []
    for i in range(n_bands):
        s0, s1 = i * step, (i + 1) * step
        quad = [edge(s0, -1), edge(s0, 1), edge(s1, 1), edge(s1, -1)]
        low = i >= n_bands - 3  # the lowest bands down the valley floor (feature 010)
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
        {"pts": drain_pts, "role": "drain", "w": 5.0, "w_tail": 5.0},
    ]
    brook = [drain_pts[-1], (round(drain_pts[-1][0] + dx * 300, 1), round(drain_pts[-1][1] + dy * 300, 1))]
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560
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
