"""The non-comb field builders: build_polder (dike-and-drain reclamation), build_terraces (contour terraces), build_ribbon (valley ribbon paddies)."""

import math
import random
from collections.abc import Callable
from typing import Any

from .banks import hem_to_bank, round_channel_joints
from .frame import Poly, Pt, _poly_area
from .palette import FLOODED, PADDY_CELL_ACRES, RICE_GREENS, organic_parcel

_RING = 18.0  # the inner-toe ring-canal corridor width in (s, t) px (see _polder_lattice's RING note)


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
    span_s, span_t = rows * cell, cols * cell

    grid, nodes, tt, ss = _polder_lattice(R, seed, origin, (dx, dy), (ux, uy), rows, cols, cell, span_s, span_t, edge_wander, mosaic, line_wander)
    plots = _polder_parcels(R, seed, grid, nodes, rows, cols, cell, gap, split_gap, parcel_mix, organic)
    envelope = _polder_envelope(grid, span_s, span_t)
    sides_st, fi, di, sluice = _polder_ring(R, grid, span_s, span_t)
    channels, brook, dike_sluices, floor, out_t = _polder_channels(grid, sides_st, nodes, rows, cols, tt, span_s, span_t, fi, di)
    _drn = _polder_close(plots, channels, sides_st, grid, down_deg)
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


_GridFn = Callable[[float, float], Pt]


def _polder_lattice(
    R: random.Random,
    seed: int,
    origin: Pt,
    d_unit: tuple[float, float],
    u_unit: tuple[float, float],
    rows: int,
    cols: int,
    cell: float,
    span_s: float,
    span_t: float,
    edge_wander: float,
    mosaic: float,
    line_wander: float,
) -> tuple[_GridFn, list[list[tuple[float, float]]], Callable[[int], float], Callable[[int], float]]:
    """The (s, t) -> xy warp and the jittered bund-node lattice - the coordinate system every
    other polder stage places through."""
    dx, dy = d_unit
    ux, uy = u_unit
    ox, oy = origin

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
    t_step = (span_t - 2 * _RING) / cols
    s_step = (span_s - 2 * _RING) / rows

    def tt(c: int) -> float:
        return _RING + c * t_step

    def ss(r: int) -> float:
        return _RING + r * s_step

    # MOSAIC knob (GM 2026-07-22, researched): the 圩田 lower-Yangtze polder was a SURVEYED rectilinear grid,
    # but the Pearl-delta 桑基魚塘 dike-pond accreted household-by-household (挖塘培基) into a MOSAIC of varied
    # ponds fitted around MEANDERING interior creeks - scholarship describes the historical landscape as
    # "mosaic-like constructed ponds with meandering natural river systems, [with] the boundary between
    # constructed and natural blurred" (research 2026-07-22; settlements.md 'Polder mosaic vs grid'). `mosaic`
    # (0 = the clean surveyed grid, the default) displaces the INTERIOR bund-node lattice by a smooth
    # CORRELATED field, tapered to 0 at the pinned perimeter so the envelope + dike stay put: neighboring
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
    # to its own section of dike - which means every interior line keeps exactly its neighbors' shape
    # and the spacing between two bunds never changes. Real fragmented tenure does not look like that: a
    # bund is laid by eye between two points, by a different household in a different decade, so
    # neighboring lines drift, converge, and open out again, and the strip between them is wider at one
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
    return grid, nodes, tt, ss


def _polder_parcels(
    R: random.Random,
    seed: int,
    grid: _GridFn,
    nodes: list[list[tuple[float, float]]],
    rows: int,
    cols: int,
    cell: float,
    gap: tuple[float, float],
    split_gap: float | None,
    parcel_mix: tuple[float, float, float],
    organic: tuple[float, float],
) -> list[dict[str, Any]]:
    """The parcel fabric: walk the module bays, split/merge per the mix, inset each quad by its
    bund/corridor gaps, soften with the organic pass, and emit the plot records."""

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
        # cap the edge bow so two neighbors can never bow into contact: each side of a shared bund may
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
    return plots


def _polder_envelope(grid: _GridFn, span_s: float, span_t: float) -> Poly:
    """Densify the envelope so the edge-wander CURVATURE is carried into the drawn field, the perimeter dike
    that follows it, and the recorded outline - 4 bare corners would read as straight edges between them."""
    _ecorn = [(0.0, 0.0), (0.0, span_t), (span_s, span_t), (span_s, 0.0)]
    envelope = []
    for _i in range(4):
        _ea, _eb = _ecorn[_i], _ecorn[(_i + 1) % 4]
        for _k in range(12):
            envelope.append(grid(_ea[0] + (_eb[0] - _ea[0]) * _k / 12, _ea[1] + (_eb[1] - _ea[1]) * _k / 12))
    envelope.append(envelope[0])
    return envelope


def _polder_ring(R: random.Random, grid: _GridFn, span_s: float, span_t: float) -> tuple[list[list[tuple[float, float]]], float, float, Pt]:
    """THE WATER NETWORK IS A CONNECTED INNER RING CANAL (researched 2026-07-22; GM-flagged the old feeder,
    which ran at s=-12 / s=span+12 - OUTSIDE the envelope, so once the dike became a wide earthwork band
    the trunk canal sat buried IN the dike). The correct polder hydrology: the trunk canal rings the block
    on the INSIDE toe of the dike (圩内河, "one river surrounds the field") - feeder along the high inner
    toe, drain along the low inner toe, a toe ditch down each side inner toe - and water crosses the dike
    ONLY at gated sluices (the pond inlet at the high corner + the brook outfall at the low corner). The
    ring runs in the ~14 px inner-toe margin (s or t = RING*0.5) just inside the envelope, so it never
    overlaps the dike. The trunk line is organized-but-organic: long runs that read straight-ish, GENTLY
    WAVY (a surveyed dug canal wavers with terrain and repair; crescent/bow trunk forms are attested) with
    rounded corners, NOT a hard 90-degree CAD grid - the finer laterals (following the jittered bund lines)
    are visibly crookeder. Feeder -> laterals -> drain stays one connected system; every parcel fronts one."""
    fi, di = _RING * 0.5, span_s - _RING * 0.5  # feeder / drain inner-toe s-lines
    phf = R.uniform(0, math.tau)

    def waver(pts_st: list[tuple[float, float]], along: str, amp: float, ph: float) -> list[tuple[float, float]]:
        # Gently wave a trunk run: offset the CROSS coord by a low-freq sine so the canal is not dead
        # straight - TAPERED to zero at both ends of the run, so each side still starts and finishes
        # exactly on the fillet endpoints it continues from. Untapered, the sine displaced a side's
        # first/last point by up to `amp` off its neighbor's fillet end, opening a small kink at each
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
    cr = _RING * 0.9
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

    sluice = grid(fi, fi)  # the nominal NW inlet corner
    return sides_st, fi, di, sluice


def _polder_channels(
    grid: _GridFn,
    sides_st: list[list[tuple[float, float]]],
    nodes: list[list[tuple[float, float]]],
    rows: int,
    cols: int,
    tt: Callable[[int], float],
    span_s: float,
    span_t: float,
    fi: float,
    di: float,
) -> tuple[list[dict[str, Any]], list[Pt], list[Pt], list[Pt], float]:
    """The ring is a CLOSED loop (feeder top + two toe sides + drain bottom), all 4 corners FILLETED. The
    INLET is the source->field hairline itself: draw_comb_field draws it from the pond to channels[0]'s far
    end, so the feeder is recorded NW-END-LAST (reversed) - the hairline then crosses the dike from the pond
    straight onto the feeder's NW corner (the north inlet sluice), no dangling stub. The OUTFALL is the brook,
    which taps the MIDDLE of the drain (far from either drain endpoint, so it reads as a mid-run offtake, not
    a hard corner) and runs off-map south through the dike (the south sluice)."""

    def _mk(pts_st: list[tuple[float, float]], role: str, w: float, wt: float) -> dict[str, Any]:
        return {"pts": [(round(x, 1), round(y, 1)) for x, y in [grid(s, t) for s, t in pts_st]], "role": role, "w": w, "w_tail": wt}

    # the feeder is recorded NW-end-last, then extended with a short INLET STUB up through the dike to the
    # pond rim - a visible sluice channel so the pond plainly charges the ring (the source->field hairline
    # anchors at the stub's far end for the topology)
    # the inlet stub angles up toward the NW corner (t -> fi), not straight out at constant t: under
    # edge_wander a constant-t stub met the feeder at a ~90 deg bend that the warp tipped past 90 into an
    # acute turn (water_channels_obtuse_turns); heading toward the corner keeps the feeder->stub bend obtuse.
    feeder_rev = [*reversed(sides_st[0]), (-52.0, fi)]

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
    cr = _RING * 0.9
    dike_sluices = [grid(0.0, fi + cr), grid(span_s, out_t)]
    # THE FIELD FLOOR (the green greenery) is the INTERIOR of the ring canal - the outermost irrigated
    # channels - NOT the dike-boundary envelope (GM 2026-07-22). Under edge_wander the ring wavers, and a
    # separate envelope rectangle drifted in and out of it; concatenating the 4 ring sides gives the closed
    # inner-toe loop, so the green is bounded exactly by the ring and the canal draws on top of it.
    floor = [grid(s, t) for s, t in (sides_st[0] + sides_st[1] + sides_st[2] + sides_st[3])]
    return channels, brook, dike_sluices, floor, out_t


def _polder_close(plots: list[dict[str, Any]], channels: list[dict[str, Any]], sides_st: list[list[tuple[float, float]]], grid: _GridFn, down_deg: float) -> Poly:
    """Close-out: trim trailing acute stubs off every channel, then lift the parcels onto the
    collector's bank."""
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
    return _drn


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
