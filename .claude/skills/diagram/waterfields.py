#!/usr/bin/env python3
"""Water-first paddy engine (warp threads) for the /diagram settlement maps.

THE INVERSION (why this module exists): fields are grown AROUND the water network, never
the other way round. The generator lays the irrigation skeleton first - one pond sluice, a
head-race, supply canals along the HIGH margins, delivery ditches dropping downhill - and
the paddy plots are carved BETWEEN those lines, so the map cannot help but communicate the
hydrology. The old approach (draw a field blob, decorate it with water) reads as random no
matter how it is tuned; see SKILL.md 'Water-first fields v2' for the full grounding.

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

# A rice field is ONE crop at ONE transplant/growth stage, so its body is a UNIFORM green - the plot-to-plot
# shade jitter denoted nothing (it was only anti-flatness texture), and the GM asked for it uniform. The bund
# network + footpaths carry the structure, not colour. Kept as a 3-element list of the SAME value so R.choice
# consumes the RNG stream IDENTICALLY to the old 3-shade version - the field geometry + the meaningful FLOODED
# drain-plots stay byte-for-byte unchanged; only the body colour goes uniform. (The MEANINGFUL colours remain:
# FLOODED blue-green for the low plots that sit on the drain, and RIPE_GOLD, when a map uses it.)
_RICE_GREEN = '#A6C398'
RICE_GREENS = [_RICE_GREEN, _RICE_GREEN, _RICE_GREEN]
FLOODED = '#93B7AC'
RIPE_GOLD = '#C9BA79'
BUND = '#C2A772'
BEAN_GREEN = '#7C9A4E'        # azemame (bund soybeans) - the beaded-bund accent

# DRY-FIELD (hatake) crops on ground the irrigation cannot command - the upslope margin
# above the supply canal. Each: fill + furrow-line colour (dry crops are ridge-cultivated).
DRY_CROPS = {
    "barley": ("#CDB86A", "#B49E52"),      # mugi - tan-gold
    "millet": ("#C6A64A", "#AD8C36"),      # awa/kibi - ochre
    "buckwheat": ("#D3C2A6", "#C69C86"),   # soba - pale, reddish stems
    "soy": ("#A9B36A", "#8E9A50"),         # daizu as a field crop - soybean green
}

DF = 30.0        # fall step of the lockstep march (px)
GAP = 26.0       # threads never pinch closer than this - a plot must fit between them


class _Frame:
    """Contour/fall frame for an arbitrary downhill screen angle."""

    def __init__(self, down_deg):
        a = math.radians(down_deg)
        self.down = a
        self.d = (math.cos(a), math.sin(a))          # fall unit (downhill)
        self.c = (math.sin(a), -math.cos(a))         # contour unit (90 deg left of fall)

    def to_uf(self, x, y):
        return (x * self.c[0] + y * self.c[1], x * self.d[0] + y * self.d[1])

    def to_xy(self, u, f):
        return (u * self.c[0] + f * self.d[0], u * self.c[1] + f * self.d[1])


class _Thread:
    """One plot-column boundary marched down the fall line."""

    def __init__(self, u, f, drift, ditch_f, decay=110.0, fallback=None):
        self.u0, self.f0 = u, f
        self.u = u
        self.drift = drift              # du/df at takeoff (from the ditch's dug heading)
        self.decay = decay              # fall-distance over which drift relaxes to 0
        self.ditch_f = ditch_f          # dug-ditch prefix ends at this f (plain bund below)
        self.fallback = fallback        # boundary path ABOVE the takeoff (parent canal/thread)
        self.pts = []
        self.f_end = None

    def step(self, f, R):
        k = math.exp(-max(0.0, f - self.f0) / self.decay)
        return self.u + (self.drift * k + R.uniform(-0.10, 0.10)) * DF


def _at_f(F, pts, f):
    """Point on a fall-monotone polyline at fall f (clamped at the ends)."""
    if f <= F.to_uf(*pts[0])[1]:
        return pts[0]
    for i in range(len(pts) - 1):
        fa, fb = F.to_uf(*pts[i])[1], F.to_uf(*pts[i + 1])[1]
        if fa <= f <= fb and fb > fa:
            k = (f - fa) / (fb - fa)
            return (pts[i][0] + k * (pts[i + 1][0] - pts[i][0]),
                    pts[i][1] + k * (pts[i + 1][1] - pts[i][1]))
    return pts[-1]


def _f_at_u(F, pts, u):
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


def _seg_x(a, b, c, d):
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


def _pip(x, y, poly):
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


def _poly_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


def _dug_polyline(R, F, x, y, ang, length, wobble, seg, W, H):
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


def _point_along(pts, frac):
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    d = frac * total
    for i in range(len(pts) - 1):
        L = math.dist(pts[i], pts[i + 1])
        if d <= L:
            t = d / L
            return (pts[i][0] + t * (pts[i + 1][0] - pts[i][0]),
                    pts[i][1] + t * (pts[i + 1][1] - pts[i][1]))
        d -= L
    return pts[-1]


def build_comb(W, H, sluice, seed, down_deg=45,
               canal_a_len=(1250, 1450), canal_b_len=(680, 800),
               offtakes_a=(0.22, 0.45, 0.68, 0.88), offtakes_b=(0.45, 0.8),
               plot_across=48, row_step=(26, 36), dry_keepout=(), dry_band=(70, 132),
               bean_frac=0.28, field_fall=None, furrow_spread=1.1):
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
    hr = [sluice,
          (sluice[0] + 45 * F.d[0], sluice[1] + 45 * F.d[1]),
          (sluice[0] + 90 * F.d[0], sluice[1] + 90 * F.d[1])]
    channels.append({"pts": hr, "w": 7.0, "role": "main"})
    fork = hr[-1]

    # supply canal A: cross-slope along the high margin, descending gently
    a_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN - math.radians(42),
                          R.uniform(*canal_a_len), 0.045, (95, 125), W, H)
    # supply canal B: down the other margin (steeper heading, the west canal on Kikuta)
    b_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN + math.radians(58),
                          R.uniform(*canal_b_len), 0.05, (90, 120), W, H)

    def mk(px, py, heading, ditch_len, decay=110.0, fallback=None):
        tu, tf = F.to_uf(px, py)
        h = max(-1.2, min(1.2, heading - DOWN))
        # du/df = -tan(h): a heading LEFT of the fall line (h<0) moves u POSITIVE
        return _Thread(tu, tf, -math.tan(h), tf + ditch_len * max(0.2, math.cos(h)),
                       decay, fallback)

    # canal B is itself the far-side boundary thread (its dug prefix IS the canal)
    bc = mk(fork[0], fork[1], DOWN + math.radians(58), R.uniform(*canal_b_len), decay=170.0)
    threads = [bc]
    # delivery ditches are MIN-SPACED: two ditches closer than ~2 plot-columns would water the same
    # ground twice (a redundant near-pair that reads as an artifact, not design), so drop the closer.
    min_gap = 2.0 * plot_across
    placed_u = [bc.u0]                           # canal B is a SUPPLY canal - deliveries must not hug it either
    a_ths = []
    for frac in offtakes_a:                      # delivery ditches off canal A
        bx, by = _point_along(a_pts, frac)
        tu = F.to_uf(bx, by)[0]
        if any(abs(tu - pu) < min_gap for pu in placed_u):
            continue                             # redundant near-pair - skip it (keeps the net sparse)
        placed_u.append(tu)
        th = mk(bx, by, DOWN + R.uniform(-0.15, 0.1), R.uniform(420, 620), fallback=a_pts)
        a_ths.append(th)
        threads.append(th)
    for th in a_ths[1:-1]:                        # only the INTERIOR (widest) blocks split once
        th.spawn_sub = True
    rb = mk(a_pts[-1][0], a_pts[-1][1], DOWN, 0, fallback=a_pts)   # far boundary (bund only)
    threads.append(rb)
    threads.sort(key=lambda t: t.u0)

    # spawn events: west-canal offtakes + mid-block subs take off ON their parent's path
    spawns = []
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
    # + brook to discharge into open land (see SKILL.md 'Field extent'). None = the old fill-to-edge.
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
        if all(not (-60 < F.to_xy(t.u, f)[0] < W + 60 and -60 < F.to_xy(t.u, f)[1] < H + 60)
               for t in threads):
            break

    # ---- DRAIN (akusui): the collector is DUG along the fields' low boundary, so its route
    # is the ENVELOPE of the delivery ditches' dug ends (each column drains just below where
    # its ditch stops) - a u-sorted polyline through (u_bot, f_bot + margin), smoothed, and
    # extended past both ends so the whole system empties off the map
    bots = []
    for t in threads:
        if t.ditch_f <= t.f0 + 10:
            continue                                     # bund-only boundaries have no ditch
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
    hi_u = max(b[0] for b in bots) + 40                  # the OUTFALL, just past the SE-most ditch bottom
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
    duf.append((hi_u, a_fit + b_fit * hi_u))             # the outfall point (drain's downhill end)
    duf.sort(key=lambda q: q[0])
    dpts = [F.to_xy(u, f) for u, f in duf]
    channels.append({"pts": dpts, "w": 6.0, "role": "drain"})

    # the akusui does NOT just stop: it empties at its outfall into a natural valley BROOK that
    # carries the water off the map downhill (reused by the next village downstream / rejoining the
    # river). Water IN (the pond feeder) and water OUT (this brook). BUT a brook is only added when
    # the outfall sits INSIDE the frame - if the field itself already runs to the map edge, the drain
    # discharges off-map directly (a brook grown from there would just run back through the field, as
    # the streams_avoid_fields check correctly flags). A field bounded within the frame gets the brook.
    outfall = dpts[-1]                                   # the drain's downhill (highest-u) end
    brook = []
    if 14 < outfall[0] < W - 14 and 14 < outfall[1] < H - 14:
        u0, f0 = F.to_uf(*outfall)
        um, fm = F.to_uf(*dpts[-2])                      # the drain's EXIT heading (u/f) at the outfall
        eu, ef = u0 - um, f0 - fm
        el = math.hypot(eu, ef) or 1.0
        eu, ef = eu / el, ef / el                        # unit exit heading (mostly cross-slope, slight fall)
        ou, of = u0, f0
        brook = [outfall]
        for i in range(40):
            # the brook does NOT turn a hard ~90 deg corner off the collector: it CURVES from the drain's
            # exit heading toward pure downhill over the first few steps, so the junction reads as the
            # collector turning down the valley INTO the stream (a smooth bend, not a right angle).
            w = min(1.0, i / 4.0)
            ou += (1 - w) * eu * 88 + w * R.uniform(-22, 40)
            of += (1 - w) * ef * 88 + w * R.uniform(72, 105)   # w->1 quickly: pure downhill off the map
            p = F.to_xy(ou, of)
            brook.append(p)
            if not (12 < p[0] < W - 12 and 12 < p[1] < H - 12):
                break                                    # ran off the map edge = the runoff sink

    for t in threads:                                    # clip every thread to the drain
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
    bc_cuts = sorted(F.to_uf(*e[1].pts[0])[1] if False else e[0]
                     for e in [] ) if False else sorted(
        [bc.f0] + [f for f in getattr(bc, "offtake_fs", [])] + [bc.ditch_f])
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
                    channels.append({"pts": piece,
                                     "w": 5.6 - 1.6 * i / max(1, len(bc_cuts) - 2),
                                     "role": "main"})
        else:
            # a delivery ditch TAPERS as it descends: it sheds water into the paddies it feeds all
            # along its length, so its flow - and width - decreases from full at the canal takeoff to a
            # THREAD at the delivery point where it stops (continuously "tapped by the plots it feeds",
            # extending Tabayashi's supply-canal taper rule to the delivery ditches). w_tail marks the
            # narrow end so the gen draws it dwindling, not a blunt constant-width stub that stops dead.
            channels.append({"pts": pre, "w": 5.6 if t is bc else 4.0, "w_tail": 1.5, "role": "branch"})

    plots = _carve(R, F, threads, a_pts, dpts, W, H, plot_across, row_step)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560   # 1px=2ft -> 4 sq ft/px^2

    envelope = ([p for p in a_pts] + [p for p in threads[-1].pts] +
                list(reversed(dpts)) + list(reversed(threads[0].pts)))

    # DRY FIELDS (hatake) on the uncommanded upslope margin above the supply canal, and
    # BUND BEANS (azemame) beaded along a fraction of the paddy bunds - see SKILL.md.
    dry_plots = _dry_fields(R, F, a_pts, W, H, dry_keepout, band=dry_band, furrow_spread=furrow_spread)
    dry_acres = sum(_poly_area(p["poly"]) for p in dry_plots) * 4 / 43560
    bund_beans = _bund_beans(R, plots, bean_frac)
    # furrows_vary tells the checker whether to REQUIRE neighbouring dry plots to differ in row direction: a
    # gentle-valley village spreads them (the patchwork quilt, default); a STEEP/terraced village narrows the
    # spread so the rows converge back onto the contour (ridge-along-contour erosion control) and no variation
    # is required. Threshold at ~0.3 rad (~17 deg): above it the plots visibly fan, below it they read aligned.
    return {"channels": channels, "plots": plots, "threads": threads, "drain": dpts,
            "brook": brook, "envelope": envelope, "acres": acres, "dry_plots": dry_plots,
            "dry_acres": dry_acres, "bund_beans": bund_beans, "furrows_vary": furrow_spread >= 0.3}


def _carve(R, F, threads, a_pts, dpts, W, H, plot_across, row_step):
    """Carve paddy plots between adjacent threads. Above a thread's takeoff the boundary
    falls back to its parent path (canal / parent ditch); below its end, to the DRAIN - so
    plots hug the canal at the top and reach the collector at the bottom, never spilling
    past either. Rows are contour-parallel bunds (the cascade steps down them)."""
    plots = []

    def bnd(t, f):
        if f < t.f0 and t.fallback is not None:
            fb = t.fallback
            return _at_f(F, fb if isinstance(fb, list) else fb.pts, f)
        if f > F.to_uf(*t.pts[-1])[1]:
            return _at_f(F, dpts, f)
        return _at_f(F, t.pts, f)

    a_us = [F.to_uf(*p)[0] for p in a_pts]
    a_ulo, a_uhi = min(a_us), max(a_us)

    def spills_drain(pq):
        """Below the collector - strict per-vertex (no plot may poke past the drain)."""
        u, f = F.to_uf(*pq)
        fd = _f_at_u(F, dpts, u)
        return fd is not None and f > fd - 3

    def above_canal(quad):
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
        return fc is not None and f < fc + 4                 # centroid upslope of a small berm

    def root_f(t):
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

        def edge(fv, j, n):
            a, b = bnd(A, fv), bnd(B, fv)
            t = j / n
            x = a[0] + t * (b[0] - a[0])
            y = a[1] + t * (b[1] - a[1])
            if 0 < j < n:                                # interior bunds waver along contour
                wob = 5.0 * math.sin(fv / 70 + phase[min(j, nsub + 1)])
                x += F.c[0] * wob
                y += F.c[1] * wob
            return (x, y)

        def drain_f_at(fv, j_, n_):
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
            wk = min(math.dist(bnd(A, rows[k]), bnd(B, rows[k])),
                     math.dist(bnd(A, rows[k + 1]), bnd(B, rows[k + 1])))
            if wk < 24:
                continue
            n = nsub if wk / nsub >= 13 else max(1, int(wk // 44))   # canal-wedge rows: local
            for j in range(n):
                quad = [edge(rows[k], j, n), edge(rows[k], j + 1, n),
                        edge(rows[k + 1], j + 1, n), edge(rows[k + 1], j, n)]
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
                plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad],
                              "fill": fill})

        # CANAL-SIDE closers: the head plots run up against the supply canal - only a
        # narrow berm remains. These are the plots that take water DIRECTLY from the
        # canal through bund cuts (the first link of every cascade chain); a wide bare
        # gap below a supply canal would be wasted prime land. Top edges follow the
        # canal line (sloped, like the drain closers), bottoms sit on the row grid.
        for j in range(nsub):
            fprobe = max(A.f0, B.f0) + 12       # sample where the subcolumns are spread out
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
                continue                    # no gap here / top boundary is not the canal
            quad = [edge(t0, j, nsub), edge(t1, j + 1, nsub),
                    edge(fb, j + 1, nsub), edge(fb, j, nsub)]
            if math.dist(quad[0], quad[1]) < 12 or math.dist(quad[1], quad[2]) < 6:
                continue
            if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                continue
            cx = sum(pq[0] for pq in quad) / 4
            cy = sum(pq[1] for pq in quad) / 4
            if any(_pip(cx, cy, pl["poly"]) for pl in plots[sector_start:]):
                continue                        # this ground already planted (fork wedges)
            plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad],
                          "fill": R.choice(RICE_GREENS)})

        # the CLOSING rank: hem EVERY column down onto the collector, so the whole field
        # edge sits on the drain (no dry sliver between the bottom paddies and their outfall).
        # The drain is diagonal, so the triangle between the uniform last regular row and the
        # drain varies across the sector - each column is tiled to its OWN drain fall.
        n = nsub
        ftop = rows[-1]

        def drain_meet(jj):
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
            nlev = max(1, round(depth / 34))             # keep closer plots ~one row tall
            for li in range(nlev):
                fa0 = ftop + (fb0 - ftop) * li / nlev
                fa1 = ftop + (fb1 - ftop) * li / nlev
                fz0 = ftop + (fb0 - ftop) * (li + 1) / nlev
                fz1 = ftop + (fb1 - ftop) * (li + 1) / nlev
                quad = [edge(fa0, j, n), edge(fa1, j + 1, n),
                        edge(fz1, j + 1, n), edge(fz0, j, n)]
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
                plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad],
                              "fill": fill})

    # HEM PASS: guarantee the whole field edge meets the drain. The per-sector closers cover
    # most of it, but a straight-line drain that dips below a shallower sector can leave a
    # residual sliver. Walk the drain; wherever there is field just above a segment but a bare
    # gap down to the drain, fill it with a thin plot snapped onto the collector. Localised -
    # it only fires on an actual gap, so it never disturbs the flooded closers.
    def inside_any(px, py):
        return any(_pip(px, py, pl["poly"]) for pl in plots)

    for i in range(len(dpts) - 1):
        da, db = dpts[i], dpts[i + 1]
        seglen = math.dist(da, db)
        for s in [x / max(1, int(seglen / 22)) for x in range(int(seglen / 22) + 1)]:
            mx = da[0] + s * (db[0] - da[0])
            my = da[1] + s * (db[1] - da[1])
            u, fdr = F.to_uf(mx, my)
            just_in = F.to_xy(u, fdr - 6)                    # 6px up-fall, on the field side
            if not (10 < just_in[0] < W - 10 and 10 < just_in[1] < H - 10):
                continue
            if inside_any(*just_in):
                continue                                     # already hemmed here
            # find the field edge above (up to a deep dip below a shallow sector); only hem
            # where the field genuinely reaches down toward this stretch of drain
            top = None
            for dd in range(20, 210, 8):
                if inside_any(*F.to_xy(u, fdr - dd)):
                    top = fdr - dd
                    break
            if top is None:
                continue                                     # no field above (tail/outside)
            uu, uv = u - 13, u + 13
            levels = max(1, round((fdr - 2 - top) / 38))     # tile tall gaps into ~row plots
            for li in range(levels):
                fa = top + (fdr - 2 - top) * li / levels
                fz = top + (fdr - 2 - top) * (li + 1) / levels
                quad = [F.to_xy(uu, fa), F.to_xy(uv, fa), F.to_xy(uv, fz), F.to_xy(uu, fz)]
                plots.append({"poly": [(round(q[0], 1), round(q[1], 1)) for q in quad],
                              "fill": R.choice(RICE_GREENS)})
    return plots


def _dry_fields(R, F, a_pts, W, H, keepout, plot=46, band=(70, 132), furrow_spread=1.1):
    """DRY FIELDS (hatake) on the UPSLOPE margin the irrigation cannot command - the band
    just ABOVE the supply canal (lower fall). Grain and pulses (barley/wheat, millet,
    buckwheat, field soy) in an irregular PATCHWORK of ridge-cultivated plots. Crop is
    assigned per-PLOT (not per-column) with spatial coherence - historical holdings were
    fragmented, so adjacent small plots carry different crops, clustering rather than forming
    clean full-height ribbons. To scale (1px=2ft): plot outlines are real, furrows stylised.

    Columns share JITTERED boundaries (each interior boundary is drawn once and used by both
    neighbours) so the dry plots ABUT into a contiguous cultivated margin rather than floating
    as separated lozenges; their canal-side edges hug the canal continuously (bottom edge
    follows the canal fall), and only the UPSLOPE (top) edge is ragged - a per-column depth.
    `band` = (min, max) upslope depth in px: a THIN fringe (default) for a water-rich valley
    floor where dry land is scarce; widen it for a drier / hill-flanked village.

    FURROWS run along the CONTOUR (perpendicular to the fall), the traditional Japanese
    ridge-along-contour that dams rain and checks soil runoff (GIAHS drainage practice) - so
    the furrow direction is the contour heading, NOT random. Returned as `theta` per plot."""
    plots = []
    us = sorted(F.to_uf(*p)[0] for p in a_pts)
    ulo, uhi = us[0], us[-1]
    theta0 = math.atan2(F.c[1], F.c[0])                    # contour heading (ridges follow it)

    def blocked(x, y):
        return any((x - cx) ** 2 + (y - cy) ** 2 < rr * rr for (cx, cy, rr) in keepout)

    # shared column boundaries across the whole margin; endpoints pinned, interiors jittered
    bounds = [ulo]
    while bounds[-1] < uhi - plot * 0.6:
        bounds.append(bounds[-1] + plot * R.uniform(0.9, 1.25))
    bounds[-1] = uhi
    jit = [0.0] + [R.uniform(-5, 5) for _ in bounds[1:-1]] + [0.0]

    # FURROW ANGLE varies PER PLOT: fragmented dry-field holdings were a mosaic of family strips, each plowed
    # to its OWN orientation, so adjacent plots run their ridges different ways (the patchwork-quilt look).
    # Ridge-along-contour is a STEEP-slope erosion measure; on a GENTLE valley margin it is not forced, so the
    # furrows spread up to ~HW rad either side of the contour (never straight down-slope). Each plot drops its
    # furrows into the LARGEST gap between the angles of its already-placed NEIGHBOURS, guaranteeing a real
    # separation from every one of them (drives dry_plot_furrows_vary). Uses ONE R draw per plot (a small
    # jitter), exactly as the old contour code did, so the plot GEOMETRY is unchanged - only the angles vary.
    # `furrow_spread` (HW) is the KNOB: the default (~1.1 rad) gives the gentle-valley patchwork; a SMALL value
    # narrows the fan back onto the contour for a STEEP/terraced village (ridge-along-contour erosion control),
    # in which case the plots read aligned and dry_plot_furrows_vary is not required (build_comb flags it).
    HW = furrow_spread
    placed = []                                            # (cx, cy, theta) of dry plots already given an angle
    ADJ2 = 56 ** 2                                         # neighbour guard radius^2 (>= the check's, so it is a superset)
    prev_crop = R.choice(list(DRY_CROPS))
    for i in range(len(bounds) - 1):
        uL, uR = bounds[i] + jit[i], bounds[i + 1] + jit[i + 1]
        fcL, fcR = _f_at_u(F, a_pts, uL), _f_at_u(F, a_pts, uR)
        if fcL is None or fcR is None:
            continue
        depth = R.uniform(*band)                           # ragged top edge (per-column depth)
        berm = 12                                          # a thin bund above the canal
        nrow = max(1, round(depth / 36))
        for k in range(nrow):
            # per-plot crop with coherence: usually keep the last crop (holdings cluster),
            # sometimes switch - a fragmented mosaic, not a clean single-crop ribbon
            if R.random() < 0.45:
                prev_crop = R.choice(list(DRY_CROPS))
            crop = prev_crop
            fill, furrow = DRY_CROPS[crop]
            # near = canal side (larger f); far = upslope (smaller f). Both L and R edges are
            # anchored to their own canal fall so the whole bottom edge rides the canal line.
            fL_near = fcL - berm - depth * k / nrow
            fR_near = fcR - berm - depth * k / nrow
            fL_far = fcL - berm - depth * (k + 1) / nrow
            fR_far = fcR - berm - depth * (k + 1) / nrow
            quad = [F.to_xy(uL, fL_far), F.to_xy(uR, fR_far),
                    F.to_xy(uR, fR_near), F.to_xy(uL, fL_near)]
            cx = sum(p[0] for p in quad) / 4
            cy = sum(p[1] for p in quad) / 4
            if any(p[0] < 12 or p[0] > W - 12 or p[1] < 12 or p[1] > H - 12 for p in quad):
                continue
            if blocked(cx, cy):
                continue
            lo, hi = theta0 - HW, theta0 + HW              # furrows stay within HW rad of the contour
            nb = sorted(min(hi, max(lo, t)) for (px, py, t) in placed
                        if (cx - px) ** 2 + (cy - py) ** 2 < ADJ2)
            edges = [lo] + nb + [hi]
            gi = max(range(len(edges) - 1), key=lambda j: edges[j + 1] - edges[j])   # the widest gap between neighbours
            theta = min(hi, max(lo, (edges[gi] + edges[gi + 1]) / 2 + R.uniform(-0.03, 0.03)))
            placed.append((cx, cy, theta))
            plots.append({"poly": [(round(p[0], 1), round(p[1], 1)) for p in quad],
                          "crop": crop, "fill": fill, "furrow": furrow, "theta": round(theta, 3)})
    return plots


def _bund_beans(R, plots, frac, spacing=9.5):
    """AZEMAME (bund soybeans): sub-pixel at 1px=2ft, so drawn symbolically as a green BEAD
    line along a fraction of the paddy bunds. Returns bead centre points; the caller draws
    small BEAN_GREEN dots. ~`frac` of plots carry beaded bunds (not every bund had beans)."""
    beans = []
    for p in plots:
        if R.random() > frac:
            continue
        poly = p["poly"]
        order = list(range(len(poly)))
        R.shuffle(order)
        for ei in order[:R.randint(1, 2)]:
            a = poly[ei]
            b = poly[(ei + 1) % len(poly)]
            nd = int(math.dist(a, b) / spacing)
            for t in range(1, nd):
                s = t / nd
                beans.append((round(a[0] + s * (b[0] - a[0]), 1),
                              round(a[1] + s * (b[1] - a[1]), 1)))
    return beans
