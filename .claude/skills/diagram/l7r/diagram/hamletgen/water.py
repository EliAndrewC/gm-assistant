"""STAGE 1-2: the water frame, and the field the water shapes.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from l7r.diagram.settlement import Settlement, point_in_poly, seg_intersect, segments_cross
from l7r.diagram.sitegen.geom import crosses_poly, net_acres, poly_area
from l7r.diagram.waterfields import build_comb, build_polder

from .consts import FAN_ASPECTS, GRAIN, POLDER_CELL_FT, REF_CANAL_A, REF_CANAL_B, REF_FIELD_FALL, Poly, Pt
from .plan import SitePlan, _roll

# ---- STAGE 1: the water frame -------------------------------------------------------------------


def stage_water_frame(s: Settlement, plan: SitePlan) -> None:
    """Settle the drainage bearing and the land's fall BEFORE anything is placed.

    This is first because the skill says it is first, at every tier: "before a single feature is
    placed, decide the map's drainage bearing and, separately, the land's fall". Everything
    downstream reads them - which end of the fan is the head, which margin the cluster can stand on,
    which way the drain runs, where the marsh is allowed to be."""
    # THE MAP DECLARES THAT A SCRIPT MADE IT (GM 2026-08-13). Rules that the scripted path adopts
    # ahead of the hand-authored pool are gated on this tag, so a legacy map keeps its present
    # packing and starts obeying the new rule the moment it is CONVERTED - the migration enforces
    # itself instead of needing a list of exemptions that someone has to remember to prune.
    s.meta(
        generated_by="hamletgen",
        name=plan.spec.name,
        scale="hamlet",
        ftpx=plan.ftpx,
        toscale=True,
        households=plan.spec.households,
        water_flow=plan.water_flow,
        down_deg=plan.down_deg,
        windward=plan.windward,
        nucleated=True,
        field_footbridges=True,
        water_kind="stream",
    )
    s._nucleated = True
    for knob, value in plan.spec.pins.items():
        s.pin_knob(knob, value)


# ---- STAGE 2: the field the water shapes --------------------------------------------------------


def fit_field(plan: SitePlan, sluice: Pt, seed: int, plot_across: float, row_step: tuple[float, float], tolerance: float = 0.06, rounds: int = 9) -> dict[str, Any]:
    """SOLVE the comb for the acreage the household count demands, instead of guessing a fall length.

    `build_comb` takes a `field_fall` in PIXELS, and the relationship between that number and the
    acreage that comes out is not analytic - the carve drops sectors too narrow to plant, the fan's
    width follows the canal lengths, and the envelope's shape depends on where the threads clamp. An
    author picks a number, looks at the render, and adjusts; Ikegami's 1150 is such a number, and it
    lands 24% under the acreage its own docstring asks for.

    A script does not have to guess. `build_comb` is pure, deterministic and fast, so this bisects a
    single SIZE multiplier - applied to the fall length AND both canal lengths together, so the fan
    scales without changing shape - until the drawn plot area is within `tolerance` of the target.
    Returns the best net found, which is the one whose acreage is closest, not merely the last.

    The multiplier is bracketed rather than solved because acreage is monotone in it but stepwise:
    a small change can add or drop a whole plot row, so the curve has small flats and the bisection
    is on a monotone-but-lumpy function. Nine rounds resolves the multiplier to ~0.3%, far finer
    than one plot row, and costs well under a second."""
    best: tuple[tuple[bool, float], dict[str, Any]] | None = None
    # THE ASPECT IS PART OF THE SEARCH, not just a roll. A fan's legality - whether its supply canal
    # dies among the plots, whether its collector folds back on itself - depends on its SHAPE as much
    # as its size, and a roll can land on an aspect at which no size is legal. So the rolled aspect
    # is tried first and the rest follow in order; the first legal fan wins, and if none is legal the
    # closest-on-acreage is kept so the failure is a gate message rather than an exception.
    for aspect in [plan.fan_aspect] + [a for a in FAN_ASPECTS if a != plan.fan_aspect]:
        found = _fit_at_aspect(plan, sluice, seed, plot_across, row_step, aspect, tolerance, rounds)
        if best is None or found[0] < best[0]:
            best = found
        # a legal fan alone is not enough to stop the search: the supply-bank hem (2026-08-15)
        # drops the quads wedged between near-parallel channels, and on some seeds the first
        # LEGAL aspect leaves the acreage well short of the household target (cohort seed 44:
        # 11.0 against 13.0, past the 15% ratchet, with the gate itself green). Keep trying
        # aspects until one is legal AND lands the acreage; `best` already orders (illegal, err),
        # so a seed whose first legal aspect met tolerance breaks exactly where it always did and
        # every such map is byte-identical.
        if not found[0][0] and found[0][1] <= tolerance:
            break
    assert best is not None
    return best[1]


def _fit_at_aspect(plan: SitePlan, sluice: Pt, seed: int, plot_across: float, row_step: tuple[float, float], aspect: float, tolerance: float, rounds: int) -> tuple[tuple[bool, float], dict[str, Any]]:
    """`fit_field`'s bisection at ONE fan aspect. Returns ((illegal, acreage error), net)."""
    lo, hi = 0.35, 2.2
    best: tuple[tuple[bool, float], dict[str, Any]] | None = None
    for _ in range(rounds):
        k = (lo + hi) / 2.0
        net = build_comb(
            plan.W,
            plan.H,
            sluice,
            seed,
            down_deg=plan.down_deg,
            field_fall=REF_FIELD_FALL * k / aspect,
            canal_a_len=(REF_CANAL_A[0] * k * aspect, REF_CANAL_A[1] * k * aspect),
            canal_b_len=(REF_CANAL_B[0] * k * aspect, REF_CANAL_B[1] * k * aspect),
            offtakes_a=plan.offtakes_a,
            offtakes_b=plan.offtakes_b,
            plot_across=plot_across,
            row_step=row_step,
            grain_drift=plan.grain_drift,
            grain=GRAIN,
            supply_banks=True,  # bunds hem onto the supply strokes' banks (GM 2026-08-15); scripted tier only, see paddy_bunds_clear_the_supply_channels
        )
        acres = net_acres(net, plan.ftpx)
        err = abs(acres - plan.target_acres) / plan.target_acres
        # A DANGLING CANAL TAIL disqualifies a fan before its acreage is even considered. Whatever
        # supply canal runs on past its last delivery ditch has to die among the plots it waters;
        # ending outside the planted extent is runoff dying in bare ground
        # (`watercourse_ends_reach_water`). The offtake ladder keeps the tail SHORT, but whether a
        # short tail lands inside depends on how wide the fan happens to be there - so the bisection
        # picks the best fan that is legal rather than the best fan and then hoping.
        score = (tail_dangles(net) or net_bends_acutely(net), err)
        if best is None or score < best[0]:
            best = (score, net)
        if err <= tolerance and not score[0]:
            break
        if acres < plan.target_acres:
            lo = k
        else:
            hi = k
    assert best is not None
    return best


HEAD_OFFSETS: tuple[tuple[str, float], ...] = (("head_left", -0.24), ("head_center", -0.05), ("head_center", 0.05), ("head_right", 0.24))


def head_sluice(plan: SitePlan) -> tuple[Pt, str]:
    """WHERE THE WATER REACHES THE FIELD - the intake, at the field's HIGH head.

    Gravity settles this: a comb is fed from its high end, so the sluice sits at the upslope end of
    the ground the field will occupy, and the only real freedom is WHICH point of that head margin -
    a brook coming down the left shoulder, the right, or straight into the middle.

    This is deliberately NOT the engine's `water_source_anchor`. That helper resolves the knob
    catalog's `edge_N`/`edge_W`-style positions against a canvas-relative box, so a lateral entry
    (`edge_W` on a south-falling map) lands at the box's MID-height: legal by the gravity test, but
    it leaves the fan only half the canvas to run down, and the field then saturates far under the
    acreage the household count needs. That was the first real bug in this experiment and it is the
    kind a map-by-map author never meets, because they pick the number that makes the picture work.
    Anchoring on the fall axis instead makes the intake a consequence of the slope, which is what it
    is in the world."""
    dx, dy = plan.fall
    cx, cy = plan.W / 2.0, plan.H / 2.0
    px, py = -dy, dx  # across the fall
    name, lateral = _roll(plan.spec.seed, "head_offset", HEAD_OFFSETS)
    span = float(min(plan.W, plan.H))
    return (cx - dx * span * 0.36 + px * span * lateral, cy - dy * span * 0.36 + py * span * lateral), str(name)


def tail_dangles(net: Mapping[str, Any], margin: float = 18.0) -> bool:
    """Does any supply-canal end fall outside the fan's planted extent? See `fit_field`."""
    xs = [v[0] for p in net["plots"] for v in p["poly"]]
    ys = [v[1] for p in net["plots"] for v in p["poly"]]
    if not xs:  # pragma: no cover - a fan with no plots fails long before this
        return True
    x0, y0, x1, y1 = min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
    # ONLY the supply canals ("main"), and only their FREE ends.
    #
    # Two exclusions, and both were learned by getting them wrong. The DRAIN's downstream end is
    # SUPPOSED to sit outside the crop - it is the outfall, and the brook or the tameike ditch
    # attaches to it there. And a main's UPSTREAM end is the head sluice or a junction with the
    # previous main, which is also outside the plots by construction: testing it made this return
    # True for every fan ever built, which turned the disqualifier off while leaving it looking like
    # it worked, and quietly cost five times the generation work for nothing.
    #
    # A free end is one no other main starts or ends at.
    ends = [q for c in net["channels"] if c["role"] == "main" for q in (c["pts"][0], c["pts"][-1])]
    free = [q for q in ends if sum(1 for r in ends if math.hypot(q[0] - r[0], q[1] - r[1]) < 5.0) == 1]
    return any(not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1) for q in free[1:])  # [1:] drops the head intake, which is always outside the plots


def net_bends_acutely(net: Mapping[str, Any]) -> bool:
    """Does any channel in the fan fold back through less than 90 degrees?

    `water_channels_obtuse_turns` forbids it - a dug ditch does not make a hairpin - and the fan's
    own collector occasionally produces one at a particular size. Disqualifying the candidate is far
    cheaper than trying to repair the geometry afterwards, and `fit_field` has eight other fans to
    choose from."""
    for c in net["channels"]:
        pts = c["pts"]
        for i in range(1, len(pts) - 1):
            ax_, ay_ = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx_, by_ = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax_, ay_), math.hypot(bx_, by_)
            if la >= 3 and lb >= 3 and (ax_ * bx_ + ay_ * by_) / (la * lb) < 0.0:
                return True
    return False


def feed_brook(plan: SitePlan, sluice: Pt, run: float = 420.0) -> Poly:
    """The brook coming down off the high ground to the intake, steered clear of the rice.

    It ends AT the sluice, where it becomes the head-race - it does not run on over the paddies. The
    sluice sits on the field's head margin, so the LAST stretch is legitimately against the crop and
    is not tested; everything upstream of it is, because a fan's head can carry a lobe out to one
    side and a brook coming straight down the fall line then clips it (`streams_avoid_fields`, which
    is right to object - a stream does not run through a flooded paddy). Bearings are tried outward
    from straight-upslope, so the brook stays as close to the fall line as the field allows."""
    dx, dy = plan.fall
    base = math.degrees(math.atan2(-dy, -dx))  # upslope
    for swing in sorted((10.0 * k for k in range(-7, 8)), key=abs):
        th = math.radians(base + swing)
        up = (sluice[0] + math.cos(th) * run, sluice[1] + math.sin(th) * run)
        mid = ((up[0] + sluice[0]) / 2 - math.sin(th) * 26, (up[1] + sluice[1]) / 2 + math.cos(th) * 26)
        near = (sluice[0] + math.cos(th) * 40, sluice[1] + math.sin(th) * 40)  # the last 40 px is the intake itself
        if not (crosses_poly(up, mid, plan.envelope) or crosses_poly(mid, near, plan.envelope)):
            return [up, mid, sluice]
    up = (sluice[0] - dx * run, sluice[1] - dy * run)  # pragma: no cover - a fan head never blocks all fifteen
    return [up, ((up[0] + sluice[0]) / 2 + dy * 26, (up[1] + sluice[1]) / 2 - dx * 26), sluice]  # pragma: no cover - the same unreachable fallback, one line down


def stage_polder(s: Settlement, plan: SitePlan) -> None:
    """The POLDER field: a surveyed orthogonal grid diked out of standing water on flat ground.

    Not a variation on the comb - the opposite of it. A comb is grown around a head-race running down
    a slope and its shape follows the water; a polder is a planned block whose water enters at a
    corner, rings the module in a perimeter feeder, and drains to the low corner. `build_polder`
    returns `build_comb`-compatible keys on purpose, so `draw_comb_field` draws either.

    The SOURCE is a header reservoir OUTSIDE the dike above the high corner, charged through a sluice
    in the dike - not a brook running in over the crop, which is what a valley hamlet has."""
    net = fit_polder(plan, plan.spec.seed)
    plan.net = net
    plan.acres = net_acres(net, plan.ftpx)
    plan.envelope = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]
    s.field_polys.append(list(plan.envelope))
    s.meta(dry_furrows_vary=False)
    s.M["meta"]["field_archetype"] = "polder_grid"
    s.M["meta"]["water_source"] = "reservoir"
    s.M["meta"]["water_source_position"] = "corner_high"
    # THE HEADER RESERVOIR sits OUTSIDE the dike, above the block's high end, on the fall axis -
    # derived from the drawn envelope rather than offset from a corner, because which corner is
    # "high" depends on the bearing. It is the wild water the inlet sluice draws from.
    env = plan.envelope
    prx, pry = 82.0, 54.0
    # SEATED AT THE DIKE'S OWN INLET SLUICE, pushed straight out from the block. `build_polder` says
    # where the dike is cut for water (`dike_sluices`), and the reservoir is the body that sluice
    # draws from - so the link between them is the short square one Enokida draws, not a diagonal
    # across the block's whole head. Two earlier tries measured only in the fall frame: one blended
    # the high corner with the centroid and put the pond INSIDE the crop; the next centered it across
    # the block's head, and the inlet channel then ran so far that its field end dangled short of
    # the envelope (`watercourse_ends_reach_water`). The sluice is the anchor both ends agree on.
    # SEATED ON THE LINE THROUGH THE RING'S HEAD. `draw_comb_field` runs the inlet channel from the
    # pond to `net["sluice"]`, and `build_polder` puts the perimeter feeder's own head up to 70 px
    # away from that sluice, just outside the planted extent - so the ring's head dangled in bare
    # ground with the inlet water stopping short of it (`watercourse_ends_reach_water`, which is
    # right: an on-map main end outside the crop must JOIN a watercourse). Snapping the sluice onto
    # the head was tried and is worse - it drags the channel's mouth across the grid and puts a
    # farmstead on it. Placing the POND on the far side of the head, along the head->sluice line,
    # leaves the channel running straight THROUGH the head on its way in: the ring is charged where
    # it begins, which is what the sluice gate does, and nothing else moves.
    # THE RESERVOIR ANSWERS THREE RULES AT ONCE, and seating it against fewer than three is what
    # made this oscillate. It must sit OUTSIDE the crop (`pond_clear_of_field`), close enough to the
    # ring canal's head that the inlet channel is a short square run rather than a diagonal across
    # the block, and UPHILL of the field, because the source of an irrigation system has to be above
    # what it waters (`channels_flow_downhill`). Earlier versions had two of the three: seating it on
    # the head-to-sluice line satisfied the first two and let the fall push it downhill; backing it
    # off along that same line to clear the crop then dragged it further from the head.
    #
    # So: start at the ring's head and walk UPHILL - straight against the fall, which is the one
    # direction that cannot make the feed run backwards - until the rim is clear of the envelope.
    sluice = net.get("sluice")
    main = next((ch for ch in net.get("channels", []) if ch.get("role") == "main" and len(ch.get("pts") or []) >= 2), None)
    # THE ANCHOR IS THE MAIN'S LAST POINT, because that is the one `draw_comb_field` draws the inlet
    # from (`fork = net["channels"][0]["pts"][-1]`). Choosing the end nearest the SLUICE instead put
    # the reservoir uphill of one end of the ring while the channel was drawn from the other, so the
    # inlet ran diagonally across the head and the far end dangled with nothing joining it
    # (`watercourse_ends_reach_water`, 5 cohort maps). Same point, or the two disagree.
    if main is not None and sluice is not None:
        anchor: Pt = (float(main["pts"][-1][0]), float(main["pts"][-1][1]))
    else:  # pragma: no cover - build_polder always returns a main feeder and a sluice
        anchor = (net.get("dike_sluices") or [(min(p[0] for p in env), sum(p[1] for p in env) / len(env))])[0]
    ux, uy = -plan.fall[0], -plan.fall[1]  # uphill
    pond = (anchor[0] + ux * (pry + 30.0), anchor[1] + uy * (pry + 30.0), prx, pry)
    for _ in range(60):
        rim = [(pond[0] + pond[2] * math.cos(a), pond[1] + pond[3] * math.sin(a)) for a in (k * math.pi / 8 for k in range(16))]
        if not any(point_in_poly(q[0], q[1], plan.envelope) for q in rim):
            break
        pond = (pond[0] + ux * 12.0, pond[1] + uy * 12.0, pond[2], pond[3])
    # `join_head=True`: a polder's ring canal ENDS on the block's corner, outside the planted
    # extent, so the inlet must visibly meet it or the ring reads as dangling
    # (`watercourse_ends_reach_water`). A comb's head-race ends among its own plots and needs no
    # such junction, which is why this is the polder's flag rather than the engine's default.
    s.draw_comb_field(net, f"{plan.spec.name.lower()}-polder", {"kind": "pond", "pond": pond}, join_head=True)
    plan.sink_pond = None
    # THE PERIMETER DIKE - the defining polder feature, and the reason a polder is a polder: an
    # irregular hand-piled earthwork band following the water edge in organic bends (fish-scale
    # polder, 鱼鳞圩). Drawn HERE, before the village, so it sits UNDER the houses that line it.
    # ...gapped WHEREVER a channel actually crosses it, not only at the two sluices `build_polder`
    # names. A dug gap is what lets water through an earthwork; anywhere else the dike would be
    # drawn straight over a running channel (`polder_dike_gapped_at_sluices`).
    ring = list(plan.envelope)
    gaps = list(net.get("dike_sluices") or [])
    for ch in net.get("channels", []):
        pts = ch["pts"]
        for i in range(len(pts) - 1):
            for k in range(len(ring)):
                a, b = ring[k], ring[(k + 1) % len(ring)]
                if segments_cross(tuple(pts[i]), tuple(pts[i + 1]), a, b):
                    hit = seg_intersect(tuple(pts[i]), tuple(pts[i + 1]), a, b)
                    if hit is not None and not any(math.hypot(hit[0] - g[0], hit[1] - g[1]) < 30 for g in gaps):
                        gaps.append(
                            hit
                        )  # pragma: no cover - no polder seed yet runs a channel through its dike away from the two sluices `build_polder` names; the guard stays because its laterals can, and an ungapped crossing draws the earthwork over running water
    # ...and UNLABELLED on this tier. `perimeter_dike` captions itself 8 px above the band it picks,
    # and the band is not in the crop's hard set (`_CROP_HARD`), so on some bearings that caption
    # lands outside the frame (`labels_within_image`, seen at down_deg=270). Adding `dikes` to the
    # crop set was tried: the band then holds the frame open past the content and every bearing
    # fails `crop_hugs_content` instead, and Enokida and Kuwabata both move. A perimeter dike is not
    # a feature a reader needs named - it is the most legible thing on a polder sheet - so the
    # scripted tier draws it without a caption rather than framing slack around a word.
    s.perimeter_dike(ring, seed=plan.spec.seed ^ 0x6D, gaps=gaps, label="")
    # ...and the ditch runs OUTSIDE the crop become no-build corridors, exactly as on the valley
    # path. `field_channel` registers none of its own because inside the envelope the crop already
    # blocks building - but a polder's RING CANAL hugs the envelope's edge and its outer stretches
    # lie on the open margin where the village stands, so a farmstead landed squarely on the water
    # (`no_structure_on_channel`, 1 of 12 cardinal polders). The same loop the valley path runs, and
    # like that one it must come AFTER the field is drawn, since `M["field_ditches"]` is written
    # there - placed before it, the loop iterates nothing and reserves nothing, silently.
    # A SEGMENT IS RESERVED UNLESS IT LIES WHOLLY INSIDE THE CROP - tested at both ENDS, not at the
    # midpoint. A ditch segment that straddles the envelope has its midpoint inside, so a midpoint
    # test reserves nothing while half the segment runs out onto the margin where the village is;
    # that is where the last byre came to rest, with the ring canal's vertex landing inside its
    # drawn quad (measured: channel vertex (2301.0, 1864.6) inside a byre spanning 2294-2310 x
    # 1862-1873). The crop already blocks building for the part that IS inside, so reserving a
    # straddling segment costs nothing and closes the gap the midpoint left open.
    # ...over `channels` AS WELL as `field_ditches`. The polder's ring and laterals are field
    # ditches, but the inlet link and the topology hairline `draw_comb_field` records live in
    # `M["channels"]` - and it was one of THOSE that the last byre sat on, its vertex 3.4 px from
    # the byre's center. Reserving one list and not the other is the same shape as a check that
    # reads one manifest key and not its sibling: the ground does not care which list the water
    # was written to.
    for ditch in list(s.M.get("field_ditches", [])) + list(s.M.get("channels", [])):
        run = [(float(v[0]), float(v[1])) for v in ditch["poly"]]
        for a, b in zip(run, run[1:], strict=False):
            if not (point_in_poly(a[0], a[1], plan.envelope) and point_in_poly(b[0], b[1], plan.envelope)):
                s.corridors.append(([a, b], 30.0))


def fit_polder(plan: SitePlan, seed: int, tolerance: float = 0.06, rounds: int = 9) -> dict[str, Any]:
    """SOLVE the polder grid for the acreage the household count demands - the flat-ground sibling of
    `fit_field`, and it bisects the same way for the same reason.

    What it scales is the GRID (how many modules), never the module: `build_polder`'s cell size is
    calibrated so a whole bay is ~1.9 mu, a half ~0.9 and a third ~0.6, which is the attested parcel
    range, and stretching the cell to hit an acreage would silently move every parcel out of it. A
    polder grows by taking in more of the marsh, not by drawing bigger fields.

    The block keeps a ~1.8:1 tall aspect (Enokida's 15x8 is 1.9), which is what a wei-tian module
    looks like when it is diked out along a shore rather than around a bay."""
    # THE ORIGIN IS DERIVED, NOT PINNED. `build_polder` grows its grid from the HIGH corner along the
    # fall and across it, so a fixed corner only works for one fall bearing - at down_deg=0 the same
    # corner sends the block off the top of the canvas, which is exactly what the first version did
    # (bunds at y=-124, the drain outfall at y=-407, water running visibly backwards). Centring the
    # block and stepping back half its extent along each axis puts it on the canvas at any bearing,
    # and it has to be recomputed per candidate because the bisection changes the extent.
    dx, dy = plan.fall
    ux, uy = -dy, dx  # across the fall
    cellpx = POLDER_CELL_FT / plan.ftpx
    lo, hi = 6, 44
    best: dict[str, Any] | None = None
    for _ in range(rounds):
        rows = (lo + hi) // 2
        cols = max(4, int(round(rows * 0.55)))
        along, across = rows * cellpx, cols * cellpx
        cx, cy = plan.W / 2.0, plan.H / 2.0
        origin = (cx - dx * along / 2 - ux * across / 2, cy - dy * along / 2 - uy * across / 2)
        # EDGE WANDER IS FITTED TO THE BLOCK, not fixed at Enokida's 0.5. `polder_fills_its_bbox`
        # wants the outline to cover >= 82% of its bbox - the archetype's teeth, since a polder
        # reads as a SURVEYED rectangle rather than an organic field - and the wander's wobble is a
        # fixed size in cells, so on a small block it eats a much larger share of the bbox: measured,
        # a 9x5 grid fills 79% at wander 0.5 where Enokida's 15x8 clears the bar comfortably. So the
        # wander is walked down until the block reads as surveyed, keeping as much of the
        # hand-piled, fish-scale irregularity as the archetype can carry at that size.
        net = None
        for wander in (0.5, 0.4, 0.3, 0.2, 0.12):
            net = build_polder(plan.W, plan.H, origin, seed, down_deg=plan.down_deg, rows=rows, cols=cols, cell=cellpx, edge_wander=wander)
            _env = [(float(a), float(b)) for a, b in net["envelope"]]
            _xs = [q[0] for q in _env]
            _ys = [q[1] for q in _env]
            _bb = max(1.0, (max(_xs) - min(_xs)) * (max(_ys) - min(_ys)))
            if poly_area(_env) / _bb >= 0.86:  # 0.82 is the rule; the margin absorbs the drawn outline's rounding
                break
        assert net is not None
        got = net_acres(net, plan.ftpx)
        best = net
        if abs(got - plan.target_acres) / plan.target_acres <= tolerance:
            break
        if got < plan.target_acres:
            lo = rows + 1
        else:
            hi = rows - 1
        if lo > hi:
            break  # pragma: no cover - the bisection exhausts its bracket without meeting tolerance; every seed tried lands inside 6% within the rounds allowed, and the guard is what stops a runaway if a future cell size widens the gap between grid steps
    assert best is not None
    return best


def stage_field(s: Settlement, plan: SitePlan) -> None:
    """Lay the irrigation skeleton and carve the paddies between its threads.

    Second, because the water is first and the field is grown AROUND the water (the water-first
    inversion `waterfields.py` exists for). The head sluice comes from `head_sluice`, which puts the
    intake at the field's high head - gravity, not a knob."""
    if plan.field_archetype == "polder_grid":
        stage_polder(s, plan)
        return
    dx, dy = plan.fall
    sluice, position = head_sluice(plan)
    s.M["meta"]["water_source"] = position
    s.M["meta"]["water_source_position"] = position

    across, step = s.plot_texture(plan.plot_size, "organic")
    net = fit_field(plan, sluice, plan.spec.seed, across, step)
    plan.net = net
    plan.acres = net_acres(net, plan.ftpx)

    # THE DRAIN'S CONTINUATION IS ALWAYS OURS TO DRAW. `build_comb` hands back a `brook` and
    # `draw_comb_field` draws it when it is there - straight downhill, a FIXED 520 px. Both sinks
    # need something else. A hamlet draining into its own tameike must have NO brook at all (the
    # runoff stops at the pond, and `stage_sink` supplies the ditch that reaches it). A hamlet
    # draining OFF the frame needs a brook that actually gets there, and 520 px is a constant tuned
    # against the canvases the authored maps happened to use: on a wider one the brook stops in open
    # ground and fails `stream_runs_off_edge` + `stream_end_anchored`, which is the same
    # pinned-constant failure the pond set-back had. So the brook is cleared here either way, and
    # `stage_sink` draws the off-map one at a length DERIVED from the distance to the canvas edge.
    net["brook"] = []

    plan.envelope = [(round(x, 1), round(y, 1)) for x, y in net["envelope"]]  # routed against BEFORE the field is drawn (see feed_brook)
    s.field_polys.append(list(plan.envelope))
    s.meta(dry_furrows_vary=net["furrows_vary"])
    s.M["meta"]["field_archetype"] = "valley_paddy"
    # The brook that feeds the head, running in from off-map: the visible source. It is drawn as a
    # STREAM ending AT the sluice, where it becomes the head-race - it does not run on over the
    # paddies. `draw_comb_field` then records the hairline topology channel that grounds the field's
    # water source for the gate.
    s.draw_comb_field(net, f"{plan.spec.name.lower()}-paddies", {"kind": "stream", "stream": feed_brook(plan, sluice)})
    # THE PARTS OF A DITCH THAT RUN OUTSIDE THE CROP become no-build corridors.
    #
    # `s.field_channel` registers none of its own, and inside the field envelope it does not need
    # to - the crop is blocked ground already. But a delivery ditch's tail and the collector run out
    # past the envelope onto open margin, where the placer is otherwise free to seat a homestead
    # squarely on the water (`no_structure_on_channel`). Only those stretches are reserved:
    # blanketing the whole ditch net costs the field its ring of farmhouses, because a comb's
    # deliveries run right along the margin the front row wants (`field_ringed`, three maps).
    #
    # And it goes AFTER `draw_comb_field`, which is where `M['field_ditches']` is written. Placed
    # before it, the loop had nothing to iterate and reserved nothing at all - silently, since an
    # empty loop looks exactly like a loop with nothing to do.
    for ditch in s.M.get("field_ditches", []):
        run = [(float(v[0]), float(v[1])) for v in ditch["poly"]]
        outside = [(a, b) for a, b in zip(run, run[1:], strict=False) if not point_in_poly((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, plan.envelope)]
        for a, b in outside:
            s.corridors.append(([a, b], 30.0))
