"""build_comb - the water-first comb field builder (pond sluice, head-race, supply canals, delivery-ditch threads, carved paddies)."""

import math
import random
from collections.abc import Callable, Sequence
from typing import Any

from .banks import _TOE_MIN_APEX, _TOE_MIN_AREA, _TOE_MIN_THICKNESS, cell_area, dedup_ring, floor_overhang, hem_to_bank, pointed_ring, round_channel_joints
from .carve import _bund_beans, _carve, _dry_fields
from .frame import (
    CANAL_A_FT,
    CANAL_B_FT,
    DELIVERY_FT,
    DELIVERY_PARENT_FRAC,
    DF,
    DRAIN_FT,
    GAP,
    HEAD_RACE_FT,
    SUB_PARENT_FRAC,
    Poly,
    Pt,
    _drain_bank,
    _dug_polyline,
    _f_at_u,
    _Frame,
    _point_along,
    _poly_area,
    _poly_perim,
    _seg_x,
    _signed_area,
    _Thread,
    chan_px,
)
from .seams import close_seams


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
    channels: list[dict[str, Any]] = []

    fork, a_pts = _comb_skeleton(R, F, DOWN, sluice, canal_a_len, canal_b_len, W, H, grain, channels)
    threads, bc, spawns = _comb_threads(R, F, DOWN, fork, a_pts, canal_b_len, offtakes_a, offtakes_b, plot_across)
    # ---- the lockstep march (no thread may cross another or pinch under GAP)
    _comb_march(R, F, DOWN, threads, spawns, W, H, field_fall)
    dpts = _comb_drain(R, F, threads, W, H, grain, channels)
    brook = _comb_brook(R, F, dpts, W, H)

    drain_bank = _drain_bank(F, dpts, grain)  # the ditch's own edge, the one line the field may not cross
    _comb_clip_and_cap(R, F, threads, dpts, drain_bank)
    _comb_canal_pieces(F, threads, bc, a_pts, offtakes_a, fork, grain, channels)

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

    envelope = _comb_floor_and_winding(plots, threads, a_pts, dpts, F)

    _comb_toe_and_hem(plots, dpts, down_deg, plot_across, row_step, grain)
    # Sweep the channel bends BEFORE the seam pass, not after: rounding a joint moves the drawn
    # water sideways by a few px, and `close_seams` holds its new basins off the water it is shown.
    # Called last (as it was) the pass reconciled the fan against a course the map does not draw,
    # and 9 basins came out with a bund inside a swept branch bend - placement and its check must
    # read the same source, and the source is what will actually be painted.
    round_channel_joints(channels)  # earthen water turns on a swept bend, not a mitred corner
    # SEAM CLOSING, LAST. The carve leaves awkward ground wherever ditch threads diverge, the
    # closing geometry misses, or a guard drops a quad - and a real cascade fan wasted nothing:
    # fork wedges were terraced into small IRREGULAR paddies, and the odd unplantable scrap was
    # simply taken into the basin beside it rather than walled off on its own. `close_seams` does
    # exactly that, so every square foot inside the command area ends up planted, water, or
    # outside the fan, and every bund is SHARED with whatever lies across it (its module docstring
    # carries the research and the defect it replaced; the gate is `paddy_plot_seams_shared`).
    #
    # It runs AFTER `_comb_toe_and_hem` on purpose: the toe pass drops slivers too acute to bund
    # and re-hems every bund onto the drain bank, both of which open fresh bare ground - anything
    # reconciling the fan before it would have its work undone. Ungated: the hand-authored pool is
    # FROZEN since 2026-08-16, so a new rule no longer needs a byte-stability escape (the retired
    # `grain != 1.0` gate on the old wedge filler was exactly that).
    close_seams(R, F, plots, envelope, grain, channels, plot_across, row_step, a_pts, dpts, drain_bank)
    acres = sum(_poly_area(p["poly"]) for p in plots) * 4 / 43560  # 1px=2ft -> 4 sq ft/px^2

    dry_plots, dry_acres, bund_beans = _comb_dry_and_beans(R, F, a_pts, bc, plots, channels, W, H, dry_keepout, dry_band, bean_frac, grain, furrow_spread, grain_drift)
    # furrows_vary tells the checker whether to REQUIRE neighboring dry plots to differ in row direction: a
    # gentle-valley village spreads them (the patchwork quilt, default); a STEEP/terraced village narrows the
    # spread so the rows converge back onto the contour (ridge-along-contour erosion control) and no variation
    # is required. Threshold at ~0.3 rad (~17 deg): above it the plots visibly fan, below it they read aligned.
    return {
        "down_deg": down_deg,  # the LOCAL fall this fan was carved to - recorded so the drainage-slope
        # checks can judge each drain against ITS OWN field rather than one map-level constant (a city
        # ringed by farmland genuinely drains several ways at once; GM 2026-07-25)
        "fork": fork,  # the bunsuiguchi division point - recorded so comb_supply_commands_both_flanks
        # can measure each flank's planted extent and drawn-supply reach FROM the point the model
        # itself divides at (placement and check reading the same source; GM 2026-08-16)
        # THE DESIGN CELL this fan was carved to, recorded so `paddy_basins_are_worth_their_bund`
        # judges each basin against the reference the PLACER used rather than one it re-derives.
        # It cannot be re-derived from `meta.ftpx`: `plot_texture` scales the target per map
        # (small_irregular 0.72x, medium 1.0x, large_block 1.35x, strip long-and-narrow), so a gate
        # computing `paddy_grain(ftpx)` for itself would hold a textured fan to a cell it never
        # aimed at.
        "cell": cell_area(plot_across, row_step),
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


def _comb_toe_and_hem(plots: list[dict[str, Any]], dpts: Poly, down_deg: float, plot_across: float, row_step: tuple[float, float], grain: float) -> None:
    """The fan's toe discipline: drop unbundable slivers, then hold every bund off the drain."""
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
    # TWO INDEPENDENT WAYS TO BE UNBUNDABLE, and a plot only has to fail one.
    #
    # THICKNESS - the inradius proxy 2*Area/Perimeter, not an area, because an acute sliver can
    # carry a respectable area while being too narrow anywhere to hold water. Scaled to
    # `plot_across` so it means the same thing at every grain.
    #
    # APEX - added 2026-08-17 on the GM's realism ruling, because thickness alone let the fan-toe
    # SUNBURST through. A needle that is LONG passes the inradius test while still tapering to a
    # point: Inashiro carried eight to ten bunds 130-254 ft long converging on a ~10 ft stretch of
    # collector bank at 7.5-14.3 deg, and the last yards of a wedge that acute are an aze on each
    # side with no floor between them. The radial convergence itself is authentic and is NOT what
    # this drops - a cascade fan genuinely narrows to its outfall, and narrow strips are real
    # (Shiroyone Senmaida, the Cordilleras); what no real basin does is taper to zero. `_TOE_MIN_APEX`
    # carries the calibration and the arithmetic.
    #
    # DROPPING IS THE WHOLE FIX, because `close_seams` runs after this and absorbs the ground into
    # the basin beside it - which is exactly what its own research says a real fan did with an
    # unplantable scrap ("taken into the basin beside it rather than walled off on its own"). So
    # the toe pass does not need to truncate a corner or leave bare floor: it says which rings are
    # not basins, and the seam pass re-plants what that frees. Do NOT move this after `close_seams`
    # - that would open bare ground nothing reconciles, and fight `paddy_plot_seams_shared`.
    # HEM FIRST, THEN JUDGE - the order matters and it was wrong until 2026-08-17. The drop used to
    # run before the hem, so it judged a ring that the very next loop rewrote: `hem_to_bank` pulls
    # vertices onto the drain bank, and pulling one vertex of an already-tapering plot onto the bank
    # SHARPENS its apex. Six of Inashiro's needles were made by the hem, in a row along the
    # collector at y~1521, and no amount of dropping beforehand could reach them. Judge the geometry
    # that actually gets recorded. (Same rule as "placement and its check must read the SAME
    # source", one level down: here both were the same code, reading two different moments.)
    #
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
        pl["poly"] = hem_to_bank(pl["poly"], dpts, down_deg, chan_px(DRAIN_FT[0], grain), chan_px(DRAIN_FT[1], grain))
    # THREE WAYS TO BE UNBUNDABLE, and they are genuinely independent measurements - each constant's
    # own comment in `banks.py` says what it is answering. Thinness catches the sliver too narrow to
    # hold water anywhere; the apex catches the long wedge that is workable through its middle and a
    # needle at its tip; AREA catches the fragment that is neither - a boundary offcut with honest
    # angles and honest width that is simply not worth a perimeter of aze when the basin beside it
    # can take it in. The GM read that third one off a hamlet sheet as "a few very small triangles"
    # (2026-08-17), which is what a clipped corner of the lattice looks like: the triangularity is
    # the symptom and the size is the cause, so the rule is written on size.
    _cell = cell_area(plot_across, row_step)
    _thin = [
        q
        for q in plots
        if _poly_perim(q["poly"]) <= 0
        or 2 * _poly_area(q["poly"]) / _poly_perim(q["poly"]) < _TOE_MIN_THICKNESS * plot_across
        or _poly_area(q["poly"]) < _TOE_MIN_AREA * _cell
        or pointed_ring(dedup_ring([(float(_p[0]), float(_p[1])) for _p in q["poly"]], 1.0), _TOE_MIN_APEX)
    ]
    if _thin:
        _drop = {id(q) for q in _thin}
        plots[:] = [q for q in plots if id(q) not in _drop]


def _canal_ft(tier: tuple[float, float], i: int, n: int) -> float:
    """A supply canal's TRUE width in feet at cut `i` of `n` - Tabayashi's taper, in real units.

    The canal sheds flow into each offtake it passes, so it steps down at every cut and dies as a
    thread past the last one. Shared by the drawing pass and by `_comb_threads`, which needs the
    parent's width AT a takeoff to size the delivery leaving there (`DELIVERY_PARENT_FRAC`); the
    two used to be one formula written out and one written nowhere, which is how a delivery came to
    be drawn wider than the canal feeding it."""
    return tier[0] - (tier[0] - tier[1]) * i / n


def _mk_thread(
    F: _Frame,
    DOWN: float,
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


def _comb_skeleton(
    R: random.Random, F: _Frame, DOWN: float, sluice: Pt, canal_a_len: tuple[float, float], canal_b_len: tuple[float, float], W: float, H: float, grain: float, channels: list[dict[str, Any]]
) -> tuple[Pt, Poly]:
    """The water skeleton's head: head-race to the division point, then canal A's dug polyline
    (canal B's is drawn and discarded - its RNG draw is part of the frozen stream)."""
    # head-race: sluice -> the division point (bunsuiguchi), straight down the fall.
    # Every width below goes through `chan_px`, which converts a TRUE width in feet to pixels at
    # this map's scale (and floors it at the visibility minimum) - so the net is to scale, and the
    # same real channel is the same real size on every sheet that draws it.
    hr = [sluice, (sluice[0] + 45 * F.d[0], sluice[1] + 45 * F.d[1]), (sluice[0] + 90 * F.d[0], sluice[1] + 90 * F.d[1])]
    channels.append({"pts": hr, "w": chan_px(HEAD_RACE_FT, grain), "role": "main"})
    fork = hr[-1]

    # supply canal A: cross-slope along the high margin, descending gently
    a_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN - math.radians(42), R.uniform(*canal_a_len), 0.045, (95, 125), W, H)
    # supply canal B: down the other margin (steeper heading, the west canal on Kikuta). Its polyline is
    # discarded - canal B is redrawn below as the `bc` boundary thread - but the call stays (its RNG draw is
    # part of the frozen stream that keeps every map byte-identical); `_`-prefixed so it reads as intentional.
    _b_pts = _dug_polyline(R, F, fork[0], fork[1], DOWN + math.radians(58), R.uniform(*canal_b_len), 0.05, (90, 120), W, H)
    return fork, a_pts


def _comb_threads(
    R: random.Random,
    F: _Frame,
    DOWN: float,
    fork: Pt,
    a_pts: Poly,
    canal_b_len: tuple[float, float],
    offtakes_a: Sequence[float],
    offtakes_b: Sequence[float],
    plot_across: float,
) -> tuple[list[_Thread], _Thread, list[list[Any]]]:
    """Boundary + delivery threads off the two canals, and the spawn events for mid-march offtakes."""
    # canal B is itself the far-side boundary thread (its dug prefix IS the canal)
    bc = _mk_thread(F, DOWN, fork[0], fork[1], DOWN + math.radians(58), R.uniform(*canal_b_len), decay=170.0)
    bc.head_ft = CANAL_B_FT[0]  # bc is a SUPPLY canal, not a delivery - it carries its own tier
    threads = [bc]
    # delivery ditches are MIN-SPACED: two ditches closer than ~2 plot-columns would water the same
    # ground twice (a redundant near-pair that reads as an artifact, not design), so drop the closer.
    min_gap = 2.0 * plot_across
    placed_u = [bc.u0]  # canal B is a SUPPLY canal - deliveries must not hug it either
    a_ths = []
    # canal A is cut at every offtake, so offtake j leaves where the canal has already stepped down
    # to cut j+1 of its len(offtakes_a)+1 pieces - the same profile `_comb_canal_pieces` draws.
    n_a_cuts = len(offtakes_a) + 1
    for j, frac in enumerate(offtakes_a):  # delivery ditches off canal A
        bx, by = _point_along(a_pts, frac)
        tu = F.to_uf(bx, by)[0]
        if any(abs(tu - pu) < min_gap for pu in placed_u):
            continue  # redundant near-pair - skip it (keeps the net sparse)
        placed_u.append(tu)
        th = _mk_thread(F, DOWN, bx, by, DOWN + R.uniform(-0.15, 0.1), R.uniform(420, 620), fallback=a_pts)
        th.head_ft = min(DELIVERY_FT[0], _canal_ft(CANAL_A_FT, j + 1, n_a_cuts) * DELIVERY_PARENT_FRAC)
        a_ths.append(th)
        threads.append(th)
    for th in a_ths[1:-1]:  # only the INTERIOR (widest) blocks split once
        th.spawn_sub = True
    rb = _mk_thread(F, DOWN, a_pts[-1][0], a_pts[-1][1], DOWN, 0, fallback=a_pts)  # far boundary (bund only)
    threads.append(rb)
    threads.sort(key=lambda t: t.u0)

    # spawn events: west-canal offtakes + mid-block subs take off ON their parent's path
    spawns: list[list[Any]] = []  # [f_at, parent_thread, heading, ditch_len, side, head_ft] - heterogeneous
    bc.offtake_fs = []
    n_b_cuts = len(offtakes_b) + 1
    for j, frac in enumerate(offtakes_b):
        f_at = bc.f0 + (sum(canal_b_len) / 2 * frac) * math.cos(math.radians(58))
        bc.offtake_fs.append(f_at)
        head_ft = min(DELIVERY_FT[0], _canal_ft(CANAL_B_FT, j + 1, n_b_cuts) * DELIVERY_PARENT_FRAC)
        spawns.append([f_at, bc, DOWN + R.uniform(-0.2, 0.0), R.uniform(340, 560), +1, head_ft])
    # a sub takes off HIGH on its parent and DIVERGES steeply (bigger heading, longer run) so the two
    # channels end up > ~2 columns apart - a real Y-junction serving a distinct sub-block, NOT two
    # ditches running adjacent for a stretch (which read as a redundant artifact, per the GM).
    for th in [t for t in threads if getattr(t, "spawn_sub", False)]:
        f_at = th.f0 + (th.ditch_f - th.f0) * R.uniform(0.24, 0.38)
        side = R.choice((-1, 1))
        # A sub-ditch is sized against its parent's HEAD, deliberately - not its local width there.
        # `settlement-review` (2026-08-17) flagged the divergence between this and the docs, which
        # said LOCAL, and the docs have been corrected to match rather than the other way round,
        # because the local version was TRIED and is worse: at true scale a delivery's local width a
        # third of the way down is ~2.2 ft, so 0.75 of it is 1.64 - against a 1.5 px floor, a
        # sub-ditch with 0.14 px of room to taper in. `delivery_ditches_taper` (w_tail < 0.85*w)
        # correctly rejected that on 22 of 24 cohort maps: a ditch that cannot taper should not be
        # drawn claiming to. Sizing off the head keeps the sub a real tier below its parent while
        # leaving it somewhere to dwindle to.
        spawns.append([f_at, th, DOWN + side * R.uniform(0.5, 0.66), R.uniform(300, 430), side, th.head_ft * SUB_PARENT_FRAC])
    bc.ditch_f = max([e[0] for e in spawns if e[1] is bc], default=bc.f0 + 40) + 22
    return threads, bc, spawns


def _comb_march(R: random.Random, F: _Frame, DOWN: float, threads: list[_Thread], spawns: list[list[Any]], W: float, H: float, field_fall: float | None) -> None:
    """The lockstep march (no thread may cross another or pinch under GAP), spawning children mid-march."""
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
            _, par, head, dlen, side, head_ft = ev
            px, py = par.pts[-1]
            child = _mk_thread(F, DOWN, px, py, head, dlen, fallback=par)
            child.head_ft = head_ft  # sized against its parent's local width, never wider than it
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


def _comb_drain(R: random.Random, F: _Frame, threads: list[_Thread], W: float, H: float, grain: float, channels: list[dict[str, Any]]) -> Poly:
    """DRAIN (akusui): the collector is DUG along the fields' low boundary, so its route
    is the ENVELOPE of the delivery ditches' dug ends (each column drains just below where
    its ditch stops) - a u-sorted polyline through (u_bot, f_bot + margin), smoothed, and
    extended past both ends so the whole system empties off the map."""
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
    channels.append({"pts": dpts, "w": chan_px(DRAIN_FT[0], grain), "w_tail": chan_px(DRAIN_FT[1], grain), "role": "drain"})
    return dpts


def _comb_brook(R: random.Random, F: _Frame, dpts: Poly, W: float, H: float) -> Poly:
    """The akusui does NOT just stop: it empties at its outfall into a natural valley BROOK that
    carries the water off the map downhill (reused by the next village downstream / rejoining the
    river). Water IN (the pond feeder) and water OUT (this brook). BUT a brook is only added when
    the outfall sits INSIDE the frame - if the field itself already runs to the map edge, the drain
    discharges off-map directly (a brook grown from there would just run back through the field, as
    the streams_avoid_fields check correctly flags). A field bounded within the frame gets the brook."""
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
    return brook


def _comb_clip_and_cap(R: random.Random, F: _Frame, threads: list[_Thread], dpts: Poly, drain_bank: Callable[[float], float]) -> None:
    """Clip every thread to the drain's BANK, then cap each column's cascade tail."""
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


def _comb_canal_pieces(F: _Frame, threads: list[_Thread], bc: _Thread, a_pts: Poly, offtakes_a: Sequence[float], fork: Pt, grain: float, channels: list[dict[str, Any]]) -> None:
    """Drawable canals: A tapers past each offtake ("main canals gradually decrease in
    size as they are tapped by branch canals" - Tabayashi 1986), and it tapers ALL THE WAY DOWN
    to a ditch-tail thread (1.6) at its far end (GM 2026-07-23): the supply canal sheds its whole
    flow into the offtakes and plots along its run, so past the last offtake it carries almost
    nothing and "slowly disappears" exactly like the delivery ditches - the old stepped 6.2 -> 4.0
    taper left the top channel reading near-constant beside the dwindling ditches. Each piece now
    carries w -> w_tail so the narrowing is continuous within pieces, not a stair of blunt steps."""
    cuts = [0.0] + list(offtakes_a) + [1.0]
    n_a = len(cuts) - 1
    for i in range(len(cuts) - 1):
        piece = [_point_along(a_pts, cuts[i] + (cuts[i + 1] - cuts[i]) * t / 6) for t in range(7)]
        channels.append({"pts": piece, "w": chan_px(_canal_ft(CANAL_A_FT, i, n_a), grain), "w_tail": chan_px(_canal_ft(CANAL_A_FT, i + 1, n_a), grain), "role": "main"})
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
                    channels.append({"pts": piece, "w": chan_px(_canal_ft(CANAL_B_FT, i, m_b), grain), "w_tail": chan_px(_canal_ft(CANAL_B_FT, i + 1, m_b), grain), "role": "main"})
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
            # `head_ft` was capped against the parent's LOCAL width where this ditch takes off, so a
            # delivery can never be drawn wider than the canal feeding it (DELIVERY_PARENT_FRAC).
            channels.append({"pts": pre, "w": chan_px(t.head_ft, grain), "w_tail": chan_px(DELIVERY_FT[1], grain), "role": "branch"})


def _comb_floor_and_winding(plots: list[dict[str, Any]], threads: list[_Thread], a_pts: Poly, dpts: Poly, F: _Frame) -> Poly:
    """The fan's envelope, its floor trimmed to the command area, and the bowtie drop."""
    envelope = [p for p in a_pts] + [p for p in threads[-1].pts] + list(reversed(dpts)) + list(reversed(threads[0].pts))

    # TRIM THE FLOOR TO THE COMMAND AREA (known-open ledger 2026-08-16, Mizuguchi's SE needle -
    # and the same class on all four live hamlets: 0.7-1.8% of floor area, measured with no plot
    # vertex more than 0.8 px past the line). Where the collector stops short of the outer
    # threads, the raw ring closes across ground down-fall of the (flat-extended) drain line -
    # ground that cannot drain and is never planted (the wedge filler refuses it by the same
    # extension rule), so it renders as bare field color: a dead needle hanging off the fan.
    # Pull every vertex past the line back up-fall onto it. `floor_overhang` is the shared
    # predicate the gate reads too (comb_floor_ends_at_the_collector); the 0.5 px floor keeps
    # already-clear vertices byte-identical - the envelope's low edge IS the drain polyline, and
    # a float round-trip must not dirty it.
    _fo = floor_overhang(envelope, dpts, math.degrees(F.down))
    envelope = [(p[0] - o * F.d[0], p[1] - o * F.d[1]) if o > 0.5 else p for p, o in zip(envelope, _fo, strict=True)]
    # ...then merge the near-duplicate vertices the clamp deposits where the cut meets the old
    # boundary (merged-roll review 2026-08-16, Kashikawa: ~12 points with reversals in a ~5 px
    # span at the trim corner) - data hygiene for every later consumer of the ring.
    envelope = dedup_ring(envelope, 1.0)

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
    return envelope


def _comb_dry_and_beans(
    R: random.Random,
    F: _Frame,
    a_pts: Poly,
    bc: _Thread,
    plots: list[dict[str, Any]],
    channels: list[dict[str, Any]],
    W: float,
    H: float,
    dry_keepout: Sequence[tuple[float, float, float]],
    dry_band: tuple[float, float],
    bean_frac: float,
    grain: float,
    furrow_spread: float,
    grain_drift: float,
) -> tuple[list[dict[str, Any]], float, Poly]:
    """DRY FIELDS (hatake) on the uncommanded upslope margin above the supply canal, and
    BUND BEANS (azemame) beaded along a fraction of the paddy bunds - see settlements.md."""
    # The hem's stand-off is derived from the SUPPLY strokes' drawn banks (`CANAL_BERM_FT`), so the
    # drawn channels have to be in hand - they are, because this pass runs after `_comb_canal_pieces`
    # and after `round_channel_joints`, i.e. against the geometry that will actually be painted.
    _supply_strokes = [c for c in channels if c.get("role") != "drain"]
    dry_plots = _dry_fields(R, F, a_pts, W, H, dry_keepout, band=dry_band, g=grain, furrow_spread=furrow_spread, grain_drift=grain_drift, supply=_supply_strokes)
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
                R, F, _bc_supply, W, H, dry_keepout, band=(dry_band[0] * 0.6, dry_band[1] * 0.6), g=grain, furrow_spread=furrow_spread, grain_drift=grain_drift, supply=_supply_strokes
            )  # thinner than the a-side hem: it only needs to cover the fork triangle, and a full-depth band crowds the farmhouse ring off the fan's visible edge
    dry_acres = sum(_poly_area(p["poly"]) for p in dry_plots) * 4 / 43560
    bund_beans = _bund_beans(R, plots, bean_frac, channels=channels)
    return dry_plots, dry_acres, bund_beans
