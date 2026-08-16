"""The comb carve: _carve cuts paddy plots between marched warp threads; _dry_fields tiles the dry-crop hem; _bund_beans lays the azemame bead accents.

Feature 110 decomposition: `_carve` is a pipeline of named stages - the supply-bank helpers
(`_supply_index`, `_clear_supply`, `_quad_in_supply`), the sector geometry helpers (`_bnd`,
`_spills_drain`, `_bank_chord`, `_above_canal`, `_root_f`), one `_carve_sector` per adjacent
thread pair (body rows -> canal-side closers -> closing rank), and the final `_hem_pass`.
Extraction is mechanical: statement order, RNG draw order, and float-op order are exactly the
monolith's, held by the byte-identity oracle (specs/110-waterfields-package/)."""

import math
import random
from collections.abc import Callable, Sequence
from typing import Any

from .banks import _TINT_MIN_APEX, dedup_ring, pointed_ring, polyline_cum, supply_bank_clearance
from .frame import BANK_MARGIN, Poly, Pt, _at_f, _f_at_u, _Frame, _miter_normals, _pip, _seg_d, _Thread
from .palette import DRY_CROPS, FLOODED, RICE_GREENS

# a supply-stroke index row: (pts, cumulative arc-length, head width, tail width, padded bbox)
_SupRow = tuple[Poly, list[float], float, float, tuple[float, float, float, float]]
_BankAt = Callable[[float], float]
_EdgeFn = Callable[[float, int, int], Pt]


def _supply_index(supply: list[dict[str, Any]] | None, g: float) -> list[_SupRow]:
    """Index the supply strokes for the bank-clearance passes (see `_carve`'s SUPPLY-SIDE BANKS note)."""
    sup_idx: list[_SupRow] = []
    for sc in supply or []:
        spts = [(float(p[0]), float(p[1])) for p in sc["pts"]]
        if len(spts) >= 2:
            _sw0, _sw1 = float(sc["w"]), float(sc.get("w_tail", sc["w"]))
            _sreach = max(_sw0, _sw1) / 2 + BANK_MARGIN * g + 2.0  # bbox prefilter: prunes only, never decides
            _sbb = (min(p[0] for p in spts) - _sreach, min(p[1] for p in spts) - _sreach, max(p[0] for p in spts) + _sreach, max(p[1] for p in spts) + _sreach)
            sup_idx.append((spts, polyline_cum(spts), _sw0, _sw1, _sbb))
    return sup_idx


def _clear_supply(x: float, y: float, hx: float, hy: float, sup_idx: list[_SupRow], g: float) -> Pt:
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


def _quad_in_supply(quad: Poly, sup_idx: list[_SupRow], g: float) -> bool:
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


def _bnd(t: _Thread, f: float, F: _Frame, dpts: Poly, bank_at: _BankAt) -> Pt:
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


def _spills_drain(pq: Pt, F: _Frame, dpts: Poly, bank_at: _BankAt) -> bool:
    """Below the collector's BANK - strict per-vertex (no plot may poke into the drain)."""
    u, f = F.to_uf(*pq)
    fd = _f_at_u(F, dpts, u)
    return fd is not None and f > fd - bank_at(u)


def _bank_chord(u0: float, u1: float, F: _Frame, dpts: Poly, bank_at: _BankAt, fd_default: float | None = None) -> tuple[float, float] | None:
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


def _above_canal(quad: Poly, F: _Frame, a_pts: Poly, a_ulo: float, a_uhi: float, g: float) -> bool:
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


def _root_f(t: _Thread, F: _Frame) -> float:
    while isinstance(t.fallback, _Thread):
        t = t.fallback
    if isinstance(t.fallback, list):
        return min(t.f0, F.to_uf(*t.fallback[0])[1])
    return t.f0


def _sector_body_rows(
    R: random.Random,
    rows: list[float],
    nsub: int,
    edge: _EdgeFn,
    bndAB: tuple[Callable[[float], Pt], Callable[[float], Pt]],
    W: float,
    H: float,
    g: float,
    spills: Callable[[Pt], bool],
    above: Callable[[Poly], bool],
    in_supply: Callable[[Poly], bool],
    plots: list[dict[str, Any]],
) -> None:
    """The sector's BODY: one quad per row x sub-column, dropped where it degenerates or breaks a water bound."""
    bndA, bndB = bndAB
    for k in range(len(rows) - 1):
        wk = min(math.dist(bndA(rows[k]), bndB(rows[k])), math.dist(bndA(rows[k + 1]), bndB(rows[k + 1])))
        if wk < 24 * g:
            continue
        n = nsub if wk / nsub >= 13 * g else max(1, int(wk // (44 * g)))  # canal-wedge rows: local
        for j in range(n):
            quad = [edge(rows[k], j, n), edge(rows[k], j + 1, n), edge(rows[k + 1], j + 1, n), edge(rows[k + 1], j, n)]
            if math.dist(quad[0], quad[1]) < 12 * g or math.dist(quad[1], quad[2]) < 12 * g:
                continue
            if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                continue
            if any(spills(pq) for pq in quad) or above(quad) or in_supply(quad):
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


def _sector_canal_closers(
    R: random.Random,
    rows: list[float],
    nsub: int,
    edge: _EdgeFn,
    f0AB: tuple[float, float],
    F: _Frame,
    a_pts: Poly,
    W: float,
    H: float,
    g: float,
    in_supply: Callable[[Poly], bool],
    plots: list[dict[str, Any]],
    sector_start: int,
) -> None:
    """CANAL-SIDE closers: the head plots run up against the supply canal - only a
    narrow berm remains. These are the plots that take water DIRECTLY from the
    canal through bund cuts (the first link of every cascade chain); a wide bare
    gap below a supply canal would be wasted prime land. Top edges follow the
    canal line (sloped, like the drain closers), bottoms sit on the row grid."""
    for j in range(nsub):
        fprobe = max(f0AB[0], f0AB[1]) + 12 * g  # sample where the subcolumns are spread out
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
        if in_supply(quad):
            continue  # a head closer wedged between a canal and its offtake - no bank to sit on
        plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad], "fill": R.choice(RICE_GREENS)})


def _sector_closing_rank(
    R: random.Random,
    rows: list[float],
    nsub: int,
    edge: _EdgeFn,
    drain_f_at: Callable[[float, int, int], float],
    F: _Frame,
    dpts: Poly,
    bank_at: _BankAt,
    chord: Callable[[float, float], tuple[float, float] | None],
    W: float,
    H: float,
    g: float,
    in_supply: Callable[[Poly], bool],
    plots: list[dict[str, Any]],
) -> None:
    """The CLOSING rank: hem EVERY column down onto the collector, so the whole field
    edge sits on the drain (no dry sliver between the bottom paddies and their outfall).
    The drain is diagonal, so the triangle between the uniform last regular row and the
    drain varies across the sector - each column is tiled to its OWN drain fall."""
    n = nsub
    ftop = rows[-1]

    def drain_meet(jj: int, ftop: float = ftop, n: int = n) -> float:
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
                ch = chord(u3, u2)
                if ch is not None:
                    quad[3], quad[2] = F.to_xy(u3, ch[0]), F.to_xy(u2, ch[1])
            if math.dist(quad[0], quad[1]) < 8 * g:
                continue
            if any(pq[0] < 8 or pq[0] > W - 8 or pq[1] > H - 8 or pq[1] < 8 for pq in quad):
                continue
            if in_supply(quad):
                continue  # a closing-rank corner wedged against a ditch tail - no bank to sit on
            # only the level whose BOTTOM edge lies on the collector floods (the wettest,
            # lowest ground); an upper split level cascades into it and stays green - so a
            # blue plot always abuts the drain
            fill = FLOODED if (abuts and R.random() < 0.45) else R.choice(RICE_GREENS)
            if fill == FLOODED and pointed_ring(dedup_ring(quad, 1.0), _TINT_MIN_APEX):
                # A POINTED SLIVER MUST NOT WEAR THE WATER TINT (known-open ledger 2026-08-16):
                # at a fan seam the converging closing-rank sub-columns taper to needle apexes,
                # and a blue one reads as a tiny triangular pond. Demote to a rice green picked
                # by POSITION (no extra R draw, so the stream is unmoved for every other plot);
                # `low` is untouched - the tint is only the picture (feature 010). The quad is
                # DEDUPED first: the recorder merges sub-1 px collapsed edges before the ring is
                # written, and a quad with a collapsed edge carries near-90 deg corner angles
                # while its merged triangle carries the needle apex - testing the raw quad let 3
                # cohort seeds ship tinted needles the gate then caught (the split-predicate
                # trap, caught by the 48-seed sweep 2026-08-16).
                fill = RICE_GREENS[(int(abs(quad[0][0]) * 7) + int(abs(quad[0][1]) * 3)) % len(RICE_GREENS)]
            # `low` is the TOPOGRAPHY; `fill` is only the PICTURE. FLOODED tints a random 45% of the
            # bottom level blue for texture, so it is not the low ground - it is a sample of it. The
            # land-use overlays must key off `low`, never off the tint (feature 010).
            # The band is the bottom TWO levels, not just the one on the drain: a real valley bottom
            # has a wet backswamp with width, not a one-plot hem. Its exact extent is unrecorded, so
            # this is a CALIBRATED LIBERTY (constitution XII) - see the note in `apply_land_use`.
            plots.append({"poly": [(round(pq[0], 1), round(pq[1], 1)) for pq in quad], "fill": fill, "low": li >= nlev - 2})


def _carve_sector(
    R: random.Random,
    RW: random.Random,
    F: _Frame,
    A: _Thread,
    B: _Thread,
    a_pts: Poly,
    dpts: Poly,
    W: float,
    H: float,
    plot_across: float,
    row_step: tuple[float, float],
    g: float,
    bank_at: _BankAt,
    sup_idx: list[_SupRow],
    a_ulo: float,
    a_uhi: float,
    plots: list[dict[str, Any]],
) -> None:
    """One sector - the ground between adjacent threads A and B: geometry gates, the wander
    profiles, then body rows -> canal-side closers -> closing rank (each its own stage)."""
    f_lo = max(_root_f(A, F), _root_f(B, F)) + 6 * g
    if B.fallback is A or A.fallback is B:
        # a parent-child pair: the sector opens AT the spawn point - anchor the first
        # row there, else the row straddling the spawn has zero width and never plants
        f_lo = max(A.f0, B.f0) + 4 * g
    f_hi0 = max(F.to_uf(*A.pts[-1])[1], F.to_uf(*B.pts[-1])[1]) - 34 * g
    if f_hi0 - f_lo < 24 * g:
        return
    # measure the sector's width where BOTH boundaries are their own threads (the
    # active span) - measuring in the fallback wedge reads ~0 and degenerates nsub
    fmid = (max(A.f0, B.f0) + f_hi0) / 2
    width_mid = math.dist(_bnd(A, fmid, F, dpts, bank_at), _bnd(B, fmid, F, dpts, bank_at))
    if width_mid < 24 * g:
        return
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
    rphase = [RW.uniform(0, 6.28) for _ in range(nsub + 2)]
    rowamp = 0.13 * sum(row_step) / 2
    # The wander is tapered to zero at the sector's first and last row, because those two are not
    # free lines: the head row sits ON the supply canal (it takes water through bund cuts) and the
    # closing rank sits ON the drain collector. Both are pinned by the water, so only the rows
    # between them drift - which also keeps the fan's own extent exactly where the gen placed the
    # village, gardens, and label against it. `rspan` is filled in once f_hi is known below; while
    # it is degenerate the wander is simply off, so the f_hi probe itself is not perturbed.
    rspan = [f_lo, f_lo]

    def edge(fv: float, j: int, n: int) -> Pt:
        a, b = _bnd(A, fv, F, dpts, bank_at), _bnd(B, fv, F, dpts, bank_at)
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
            return _clear_supply(x, y, mx / ml, my / ml, sup_idx, g) if ml > 1e-9 else _clear_supply(x, y, F.d[0], F.d[1], sup_idx, g)
        return (x, y)

    def drain_f_at(fv: float, j_: int, n_: int) -> float:
        """Fall of the drain under the j_-th sub-bund point sampled at fall fv."""
        pu = F.to_uf(*edge(fv, j_, n_))[0]
        fd_ = _f_at_u(F, dpts, pu)
        return fd_ if fd_ is not None else fv

    f_hi = min(f_hi0, min(drain_f_at(f_hi0, j, nsub) for j in range(nsub + 1)) - 32 * g)
    if f_hi - f_lo < 24 * g:
        return
    rspan[0], rspan[1] = f_lo, f_hi  # the row wander is live now that the sector's span is known
    sector_start = len(plots)
    rows = [f_lo]
    f = f_lo
    while f < f_hi:
        f = min(f_hi, f + R.uniform(*row_step))
        rows.append(f)

    def spills(pq: Pt) -> bool:
        return _spills_drain(pq, F, dpts, bank_at)

    def above(quad: Poly) -> bool:
        return _above_canal(quad, F, a_pts, a_ulo, a_uhi, g)

    def in_supply(quad: Poly) -> bool:
        return _quad_in_supply(quad, sup_idx, g)

    def chord(u0: float, u1: float) -> tuple[float, float] | None:
        return _bank_chord(u0, u1, F, dpts, bank_at)

    bndAB = (lambda fv: _bnd(A, fv, F, dpts, bank_at), lambda fv: _bnd(B, fv, F, dpts, bank_at))
    _sector_body_rows(R, rows, nsub, edge, bndAB, W, H, g, spills, above, in_supply, plots)
    _sector_canal_closers(R, rows, nsub, edge, (A.f0, B.f0), F, a_pts, W, H, g, in_supply, plots, sector_start)
    _sector_closing_rank(R, rows, nsub, edge, drain_f_at, F, dpts, bank_at, chord, W, H, g, in_supply, plots)


def _hem_pass(
    R: random.Random,
    F: _Frame,
    dpts: Poly,
    W: float,
    H: float,
    g: float,
    bank_at: _BankAt,
    sup_idx: list[_SupRow],
    plots: list[dict[str, Any]],
) -> None:
    """HEM PASS: guarantee the whole field edge meets the drain. The per-sector closers cover
    most of it, but a straight-line drain that dips below a shallower sector can leave a
    residual sliver. Walk the drain; wherever there is field just above a segment but a bare
    gap down to the drain, fill it with a thin plot snapped onto the collector. Localised -
    it only fires on an actual gap, so it never disturbs the flooded closers."""

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
            hem_ch = _bank_chord(uu, uv, F, dpts, bank_at, fdr)
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
                quad = [_clear_supply(q[0], q[1], F.d[0], F.d[1], sup_idx, g) for q in quad]
                if _quad_in_supply(quad, sup_idx, g):
                    continue  # no bank ground between the branch tail and the collector - leave it to the floor
                plots.append({"poly": [(round(q[0], 1), round(q[1], 1)) for q in quad], "fill": R.choice(RICE_GREENS)})


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
    past either. Rows step down the fall, each one wandering on its own (see `rphase` in
    `_carve_sector`)."""
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
    sup_idx = _supply_index(supply, g)

    a_us = [F.to_uf(*p)[0] for p in a_pts]
    a_ulo, a_uhi = min(a_us), max(a_us)

    for di in range(len(threads) - 1):
        _carve_sector(R, _RW, F, threads[di], threads[di + 1], a_pts, dpts, W, H, plot_across, row_step, g, bank_at, sup_idx, a_ulo, a_uhi, plots)

    _hem_pass(R, F, dpts, W, H, g, bank_at, sup_idx, plots)
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
    a pronounced ~43deg shear, since the canal runs diagonally to the fall). The base edge rides the canal
    itself, and each shared boundary point is offset along ONE mitred normal (`_miter_normals`), so adjacent
    columns share every seam as a single straight line - no gap wedge or lap where the canal bends. Only the
    UPSLOPE (outer) edge is ragged - a per-column depth, stepping along the shared seam lines. The base dips
    slightly BELOW the canal so it tucks under the paddy (drawn after). `band` = (min, max) upslope depth in
    px: a THIN fringe (default) for a water-rich valley floor.

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
    bpts = [at(b) for b in bounds]
    bnorm = _miter_normals(bpts, F)  # ONE shared upslope normal per boundary point - see its WHY
    for i in range(len(bounds) - 1):
        pL, pR = bpts[i], bpts[i + 1]
        (nLx, nLy), (nRx, nRy) = bnorm[i], bnorm[i + 1]
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
            quad = [(pL[0] + nLx * o_far, pL[1] + nLy * o_far), (pR[0] + nRx * o_far, pR[1] + nRy * o_far), (pR[0] + nRx * o_near, pR[1] + nRy * o_near), (pL[0] + nLx * o_near, pL[1] + nLy * o_near)]
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
